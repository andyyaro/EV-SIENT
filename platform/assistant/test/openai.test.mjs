// The OpenAI Responses API adapter (src/openai.mjs): the events it reads and what it turns them
// into, the request it makes, its errors, the usage it reports and the key read from the
// secret. A fake fetch stands in for the API; nothing here reaches OpenAI or AWS.
import test from 'node:test';
import assert from 'node:assert/strict';
import { keyFromSecretString, openaiModel, RESPONSES_URL, usageFromOpenAI } from '../src/openai.mjs';

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

const USAGE = { input_tokens: 2500, input_tokens_details: { cached_tokens: 500 }, output_tokens: 300, output_tokens_details: { reasoning_tokens: 120 }, total_tokens: 2800 };
const EVENTS = [
  { type: 'response.created', sequence_number: 0, response: { id: 'resp_1', status: 'in_progress', usage: null } },
  { type: 'response.in_progress', sequence_number: 1, response: { id: 'resp_1', status: 'in_progress' } },
  { type: 'response.output_item.added', sequence_number: 2, output_index: 0, item: { type: 'message' } },
  { type: 'response.content_part.added', sequence_number: 3, output_index: 0, content_index: 0, part: { type: 'output_text', text: '' } },
  { type: 'response.output_text.delta', sequence_number: 4, output_index: 0, content_index: 0, delta: 'caf\u00e9 ' },
  { type: 'response.output_text.delta', sequence_number: 5, output_index: 0, content_index: 0, delta: '\u{1F600} done' },
  { type: 'response.output_text.done', sequence_number: 6, output_index: 0, content_index: 0, text: 'caf\u00e9 \u{1F600} done' },
  { type: 'response.completed', sequence_number: 7, response: { id: 'resp_1', status: 'completed', usage: USAGE } },
];
const wire = (events, eol = '\n') => events.map((d) => `event: ${d.type}${eol}data: ${JSON.stringify(d)}${eol}${eol}`).join('');

const EXPECTED = [
  { type: 'message_start', message: { usage: {} } },
  { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: 'caf\u00e9 ' } },
  { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: '\u{1F600} done' } },
  { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: { input_tokens: 2000, cache_creation_input_tokens: 0, cache_read_input_tokens: 500, output_tokens: 300 } },
  { type: 'message_stop' },
];

const KEY = 'fake-openai-TEST-ONLY-not-a-real-key-000000';
const BODY = { model: 'gpt-5.4-mini', stream: true, store: false, instructions: 'S', input: [{ role: 'user', content: 'Q' }], max_output_tokens: 1200 };

function fakeFetch({ status = 200, text = wire(EVENTS), sizes = [11], error } = {}) {
  const seen = [];
  const fn = async (url, init) => {
    seen.push({ url, init });
    if (error) throw error;
    const bytes = new TextEncoder().encode(text);
    return { ok: status >= 200 && status < 300, status, body: chunksOf(bytes, sizes), json: async () => JSON.parse(text) };
  };
  fn.seen = seen;
  return fn;
}
const run = (fetchFn, over = {}) => collect(openaiModel({ getKey: () => KEY, fetchFn }).stream({ modelId: 'gpt-5.4-mini', body: BODY, ...over }));

test('stream: the same events however the bytes are split, and with any line ending', async () => {
  for (const eol of ['\n', '\r\n', '\r']) {
    const bytes = new TextEncoder().encode(wire(EVENTS, eol));
    // From 1 byte (splits every multi-byte character and every CRLF) upwards.
    for (const sizes of [[1], [2], [3], [5], [7, 1, 13], [64], [bytes.length]]) {
      const fetchFn = async () => ({ ok: true, status: 200, body: chunksOf(bytes, sizes) });
      assert.deepEqual(await run(fetchFn), EXPECTED, `${JSON.stringify(eol)} ${sizes}`);
    }
  }
});

test('stream: events without an event line, a [DONE] marker and unknown events are handled', async () => {
  const text = EVENTS.map((d) => `data: ${JSON.stringify(d)}\n\n`).join('') + 'data: [DONE]\n\n';
  assert.deepEqual(await run(fakeFetch({ text })), EXPECTED);
  // Nothing after response.completed is read.
  const after = wire([...EVENTS, { type: 'response.output_text.delta', delta: 'late' }]);
  assert.deepEqual(await run(fakeFetch({ text: after })), EXPECTED);
  // A refusal is shown as the answer's text.
  const refusal = wire([EVENTS[0], { type: 'response.refusal.delta', delta: 'I cannot help with that.' }, EVENTS.at(-1)]);
  assert.equal((await run(fakeFetch({ text: refusal })))[1].delta.text, 'I cannot help with that.');
});

test('stream: an incomplete response reports why it stopped, with its usage', async () => {
  const incomplete = (reason) => wire([...EVENTS.slice(0, 5), { type: 'response.incomplete', response: { status: 'incomplete', incomplete_details: { reason }, usage: USAGE } }]);
  for (const [reason, stop] of [['max_output_tokens', 'max_tokens'], ['content_filter', 'refusal'], ['steered', 'incomplete'], [undefined, 'incomplete']]) {
    const got = await run(fakeFetch({ text: incomplete(reason) }));
    assert.deepEqual(got.at(-2), { type: 'message_delta', delta: { stop_reason: stop }, usage: EXPECTED[3].usage }, String(reason));
    assert.deepEqual(got.at(-1), { type: 'message_stop' });
  }
});

test('usage: cached tokens are split out; anything missing gives no final count', () => {
  assert.deepEqual(usageFromOpenAI(USAGE), { input_tokens: 2000, cache_creation_input_tokens: 0, cache_read_input_tokens: 500, output_tokens: 300 });
  assert.deepEqual(usageFromOpenAI({ input_tokens: 100, output_tokens: 5 }), { input_tokens: 100, cache_creation_input_tokens: 0, cache_read_input_tokens: 0, output_tokens: 5 });
  // A cached count larger than the input is capped; a negative one is ignored.
  assert.equal(usageFromOpenAI({ input_tokens: 100, input_tokens_details: { cached_tokens: 900 }, output_tokens: 5 }).cache_read_input_tokens, 100);
  assert.equal(usageFromOpenAI({ input_tokens: 100, input_tokens_details: { cached_tokens: -9 }, output_tokens: 5 }).input_tokens, 100);
  for (const u of [null, undefined, {}, { input_tokens: 100 }, { output_tokens: 5 }, { input_tokens: '100', output_tokens: 5 }, { input_tokens: 100, output_tokens: null }]) {
    assert.equal(usageFromOpenAI(u), null, JSON.stringify(u));
  }
  // So a response.completed without usage yields a message_delta with no usage at all.
  const done = { ...EVENTS.at(-1), response: { status: 'completed', usage: null } };
  return run(fakeFetch({ text: wire([...EVENTS.slice(0, -1), done]) })).then((got) => {
    assert.deepEqual(got.at(-2), { type: 'message_delta', delta: { stop_reason: 'end_turn' } });
  });
});

test('the request: one POST with the key as a bearer token and the body exactly as built', async () => {
  const fetchFn = fakeFetch();
  const signal = new AbortController().signal;
  await run(fetchFn, { signal });
  assert.equal(fetchFn.seen.length, 1, 'no retries');
  const { url, init } = fetchFn.seen[0];
  assert.equal(url, RESPONSES_URL);
  assert.equal(url, 'https://api.openai.com/v1/responses');
  assert.equal(init.method, 'POST');
  assert.equal(init.headers.authorization, `Bearer ${KEY}`);
  assert.equal(init.headers['content-type'], 'application/json');
  assert.equal(init.body, JSON.stringify(BODY));
  assert.equal(init.signal, signal, 'the timeout and disconnect signal reach fetch');
});

test('errors: no key, or a body that is not the one checked, is refused before any call', async () => {
  for (const getKey of [() => null, () => '']) {
    const fetchFn = fakeFetch();
    await assert.rejects(collect(openaiModel({ getKey, fetchFn }).stream({ modelId: 'gpt-5.4-mini', body: BODY })), (e) => e.name === 'NoApiKey' && e.unbilled === true);
    assert.equal(fetchFn.seen.length, 0);
  }
  const fetchFn = fakeFetch();
  const model = openaiModel({ getKey: () => KEY, fetchFn });
  for (const [modelId, body] of [['gpt-5.4', BODY], ['gpt-5.4-mini', { ...BODY, stream: false }], ['gpt-5.4-mini', { ...BODY, store: true }], ['gpt-5.4-mini', { ...BODY, store: undefined }]]) {
    await assert.rejects(collect(model.stream({ modelId, body })), (e) => e.name === 'BadRequestBody' && e.unbilled === true);
  }
  assert.equal(fetchFn.seen.length, 0);
});

test('errors: an HTTP error is unbilled and named by its code; stream errors are not unbilled', async () => {
  const cases = [
    [400, { error: { message: 'bad', type: 'invalid_request_error', param: 'x', code: null } }, 'invalid_request_error'],
    [401, { error: { message: 'Incorrect API key provided: fake-openai-TEST-ONLY', type: 'invalid_request_error', code: 'invalid_api_key' } }, 'invalid_api_key'],
    [429, { error: { message: 'x', type: 'insufficient_quota', code: 'insufficient_quota' } }, 'insufficient_quota'],
    [429, { error: { message: 'x', type: 'requests', code: 'rate_limit_exceeded' } }, 'rate_limit_exceeded'],
    [400, { error: { message: 'x', type: 'Weird Type <script>', code: 'has spaces' } }, 'http_400'],
    [502, null, 'http_502'],
  ];
  for (const [status, json, name] of cases) {
    const text = json ? JSON.stringify(json) : '<html>bad gateway</html>';
    await assert.rejects(run(fakeFetch({ status, text })), (e) => {
      assert.equal(e.name, name);
      assert.equal(e.unbilled, true);
      assert.equal(e.status, status);
      assert.doesNotMatch(`${e.message} ${e.stack}`, /TEST-ONLY/, 'neither the key nor the API message reaches an error');
      return true;
    });
  }
  // Mid-stream: an error event, and a failed response, after the answer started.
  for (const [ev, name] of [
    [{ type: 'error', code: 'server_error', message: 'x', param: null }, 'server_error'],
    [{ type: 'error', code: null, message: 'x' }, 'error'],
    [{ type: 'response.failed', response: { status: 'failed', error: { code: 'server_error', message: 'x' } } }, 'server_error'],
    [{ type: 'response.failed', response: { status: 'failed', error: null } }, 'response_failed'],
  ]) {
    const got = [];
    const model = openaiModel({ getKey: () => KEY, fetchFn: fakeFetch({ text: wire([...EVENTS.slice(0, 5), ev]) }) });
    await assert.rejects((async () => { for await (const e of model.stream({ modelId: 'gpt-5.4-mini', body: BODY })) got.push(e); })(),
      (e) => e.name === name && e.unbilled === undefined);
    assert.deepEqual(got.map((e) => e.type), ['message_start', 'content_block_delta'], name);
  }
  // Malformed event data, no body, and no response at all.
  await assert.rejects(run(fakeFetch({ text: 'event: response.created\ndata: {not json\n\n' })), (e) => e.name === 'BadEvent');
  await assert.rejects(run(async () => ({ ok: true, status: 200, body: null })), (e) => e.name === 'NoBody' && !e.unbilled);
  await assert.rejects(run(fakeFetch({ error: new TypeError('fetch failed') })), (e) => e.name === 'NetworkError' && !e.unbilled);
  await assert.rejects(run(fakeFetch({ error: Object.assign(new Error('a'), { name: 'AbortError' }) })), (e) => e.name === 'AbortError' && !e.unbilled);
  await assert.rejects(run(fakeFetch({ error: Object.assign(new Error('a'), { name: 'TimeoutError' }) })), (e) => e.name === 'AbortError' && !e.unbilled);
});

test('the secret: only OPENAI_API_KEY is taken from it, and a bad secret never reaches an error', () => {
  assert.equal(keyFromSecretString(JSON.stringify({ OPENAI_API_KEY: KEY, GITHUB_TOKEN: 'github_pat_x' })), KEY);
  for (const v of [undefined, null, '', JSON.stringify({ GITHUB_TOKEN: 'x' }), JSON.stringify({ OPENAI_API_KEY: 5 }), 'null', '[]', '"sk"']) {
    assert.equal(keyFromSecretString(v), null, String(v));
  }
  assert.throws(() => keyFromSecretString(`{"OPENAI_API_KEY": "${KEY}"`), (e) => {
    assert.equal(e.name, 'SecretNotJson');
    assert.doesNotMatch(`${e.message} ${e.stack}`, /TEST-ONLY/);
    return true;
  });
});
