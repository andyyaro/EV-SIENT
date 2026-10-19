// The Claude API adapter (src/anthropic.mjs): the server-sent events parser, the request it
// makes, its errors, and the API key holder. A fake fetch stands in for the API; nothing here
// reaches Anthropic.
import test from 'node:test';
import assert from 'node:assert/strict';
import { ANTHROPIC_VERSION, anthropicModel, keySource, MESSAGES_URL, parseSse } from '../src/anthropic.mjs';

async function collect(iter) {
  const out = [];
  for await (const x of iter) out.push(x);
  return out;
}
async function* chunksOf(bytes, sizes) {
  let i = 0;
  let k = 0;
  while (i < bytes.length) {
    const n = sizes[k % sizes.length];
    yield bytes.slice(i, i + n);
    i += n;
    k += 1;
  }
}

const STREAM = [
  'event: message_start',
  'data: {"type":"message_start","message":{"usage":{"input_tokens":25,"output_tokens":1}}}',
  '',
  ': a comment line',
  'event: ping',
  'data: {"type": "ping"}',
  '',
  'event: content_block_delta',
  'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"caf\u00e9 \u{1F600}"}}',
  '',
  'event: message_delta',
  'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":15}}',
  '',
  'event: message_stop',
  'data: {"type":"message_stop"}',
  '',
  '',
];

test('SSE: events are the same however the bytes are split, and with any line ending', async () => {
  const expected = [
    { event: 'message_start', data: '{"type":"message_start","message":{"usage":{"input_tokens":25,"output_tokens":1}}}' },
    { event: 'ping', data: '{"type": "ping"}' },
    { event: 'content_block_delta', data: '{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"caf\u00e9 \u{1F600}"}}' },
    { event: 'message_delta', data: '{"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":15}}' },
    { event: 'message_stop', data: '{"type":"message_stop"}' },
  ];
  for (const eol of ['\n', '\r\n', '\r']) {
    const bytes = new TextEncoder().encode(STREAM.join(eol));
    // Every chunk size from 1 byte (splits every multi-byte character and every CRLF) upwards.
    for (const sizes of [[1], [2], [3], [5], [7, 1, 13], [64], [bytes.length]]) {
      assert.deepEqual(await collect(parseSse(chunksOf(bytes, sizes))), expected, `${JSON.stringify(eol)} ${sizes}`);
    }
  }
});

test('SSE: data lines join, comments and unknown fields are ignored, the last event needs no blank line', async () => {
  const text = 'event: a\ndata: one\ndata:two\nid: 7\nretry: 10\n: note\n\ndata: {"x":1}';
  assert.deepEqual(await collect(parseSse([text])), [
    { event: 'a', data: 'one\ntwo' },
    { event: 'message', data: '{"x":1}' },
  ]);
  assert.deepEqual(await collect(parseSse(['\n\n: only comments\n\n'])), []);
});

const KEY = 'fake-anthropic-TEST-ONLY-not-a-real-key-000000';
const BODY = { model: 'claude-haiku-5-5', stream: true, max_tokens: 1200, system: [{ type: 'text', text: 'S' }], messages: [{ role: 'user', content: [{ type: 'text', text: 'Q' }] }] };

function fakeFetch({ status = 200, text = STREAM.join('\n'), error } = {}) {
  const seen = [];
  const fn = async (url, init) => {
    seen.push({ url, init });
    if (error) throw error;
    const bytes = new TextEncoder().encode(text);
    return {
      ok: status >= 200 && status < 300, status,
      body: chunksOf(bytes, [11]),
      json: async () => JSON.parse(text),
    };
  };
  fn.seen = seen;
  return fn;
}

test('the request: one POST with the key, the version header and the body exactly as built', async () => {
  const fetchFn = fakeFetch();
  const signal = new AbortController().signal;
  const model = anthropicModel({ getKey: () => KEY, fetchFn });
  const events = await collect(model.stream({ modelId: 'claude-haiku-5-5', body: BODY, signal }));
  assert.equal(fetchFn.seen.length, 1, 'no retries');
  const { url, init } = fetchFn.seen[0];
  assert.equal(url, MESSAGES_URL);
  assert.equal(url, 'https://api.anthropic.com/v1/messages');
  assert.equal(init.method, 'POST');
  assert.equal(init.headers['x-api-key'], KEY);
  assert.equal(init.headers['anthropic-version'], ANTHROPIC_VERSION);
  assert.equal(ANTHROPIC_VERSION, '2023-06-01');
  assert.equal(init.headers['content-type'], 'application/json');
  assert.equal(init.body, JSON.stringify(BODY));
  assert.equal(init.signal, signal, 'the timeout and disconnect signal reach fetch');
  assert.deepEqual(events.map((e) => e.type), ['message_start', 'content_block_delta', 'message_delta', 'message_stop'], 'pings dropped');
  assert.equal(events[1].delta.text, 'caf\u00e9 \u{1F600}');
});

test('errors: no key and a mismatched body are refused before any call', async () => {
  for (const getKey of [() => null, () => '']) {
    const fetchFn = fakeFetch();
    const model = anthropicModel({ getKey, fetchFn });
    await assert.rejects(collect(model.stream({ modelId: 'claude-haiku-5-5', body: BODY })), (e) => e.name === 'NoApiKey' && e.unbilled === true);
    assert.equal(fetchFn.seen.length, 0);
  }
  const fetchFn = fakeFetch();
  const model = anthropicModel({ getKey: () => KEY, fetchFn });
  await assert.rejects(collect(model.stream({ modelId: 'claude-sonnet-5-5', body: BODY })), (e) => e.unbilled === true);
  await assert.rejects(collect(model.stream({ modelId: 'claude-haiku-5-5', body: { ...BODY, stream: false } })), (e) => e.unbilled === true);
  assert.equal(fetchFn.seen.length, 0);
});

test('errors: an HTTP error is unbilled and named by its type; a stream error event is not', async () => {
  const cases = [
    [400, '{"type":"error","error":{"type":"invalid_request_error","message":"bad"}}', 'invalid_request_error'],
    [401, '{"type":"error","error":{"type":"authentication_error","message":"x"}}', 'authentication_error'],
    [429, '{"type":"error","error":{"type":"rate_limit_error","message":"x"}}', 'rate_limit_error'],
    [529, '{"type":"error","error":{"type":"overloaded_error","message":"x"}}', 'overloaded_error'],
    [502, '<html>bad gateway</html>', 'http_502'],
    [400, '{"type":"error","error":{"type":"Weird Type With Spaces <script>"}}', 'http_400'],
  ];
  for (const [status, text, name] of cases) {
    const model = anthropicModel({ getKey: () => KEY, fetchFn: fakeFetch({ status, text }) });
    await assert.rejects(collect(model.stream({ modelId: 'claude-haiku-5-5', body: BODY })), (e) => {
      assert.equal(e.name, name);
      assert.equal(e.unbilled, true);
      assert.equal(e.status, status);
      assert.doesNotMatch(`${e.message} ${e.stack}`, /TEST-ONLY/, 'the key never appears in an error');
      return true;
    });
  }
  // Mid-stream: an error event after the answer started; not marked unbilled.
  const text = [...STREAM.slice(0, 3), 'event: error', 'data: {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}', '', ''].join('\n');
  const model = anthropicModel({ getKey: () => KEY, fetchFn: fakeFetch({ text }) });
  const got = [];
  await assert.rejects((async () => { for await (const e of model.stream({ modelId: 'claude-haiku-5-5', body: BODY })) got.push(e); })(),
    (e) => e.name === 'overloaded_error' && e.unbilled === undefined);
  assert.deepEqual(got.map((e) => e.type), ['message_start']);
  // Malformed event data, and no response at all.
  const bad = anthropicModel({ getKey: () => KEY, fetchFn: fakeFetch({ text: 'event: message_start\ndata: {not json\n\n' }) });
  await assert.rejects(collect(bad.stream({ modelId: 'claude-haiku-5-5', body: BODY })), (e) => e.name === 'BadEvent');
  const down = anthropicModel({ getKey: () => KEY, fetchFn: fakeFetch({ error: new TypeError('fetch failed') }) });
  await assert.rejects(collect(down.stream({ modelId: 'claude-haiku-5-5', body: BODY })), (e) => e.name === 'NetworkError' && !e.unbilled);
  const aborted = anthropicModel({ getKey: () => KEY, fetchFn: fakeFetch({ error: Object.assign(new Error('a'), { name: 'AbortError' }) }) });
  await assert.rejects(collect(aborted.stream({ modelId: 'claude-haiku-5-5', body: BODY })), (e) => e.name === 'AbortError' && !e.unbilled);
});

test('keySource: holds the key in memory, refreshes on demand, forgets it on any failure', async () => {
  let value = `  ${KEY}\n`;
  let fail = false;
  let reads = 0;
  const k = keySource(async () => { reads += 1; if (fail) throw Object.assign(new Error(`denied ${KEY}`), { name: 'AccessDeniedException' }); return value; });
  assert.equal(k.get(), null, 'nothing before the first read');
  assert.equal(await k.refresh(), true);
  assert.equal(k.get(), KEY, 'trimmed');
  fail = true;
  await assert.rejects(k.refresh(), (e) => e.name === 'AccessDeniedException' && !e.message.includes(KEY) && !String(e.stack).includes('TEST-ONLY'));
  assert.equal(k.get(), null, 'fails closed');
  fail = false;
  for (const v of [null, '', 'short', 'has space inside the key value 0000000', 'x'.repeat(401)]) {
    value = v;
    assert.equal(await k.refresh(), false, JSON.stringify(v));
    assert.equal(k.get(), null);
  }
  value = KEY;
  assert.equal(await k.refresh(), true);
  assert.equal(reads, 8);
});
