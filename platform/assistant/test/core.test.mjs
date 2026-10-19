// The proxy's request handling with a fake model and the memory store: refusals before the
// model, streaming, settling, the rate limits, and never a 403 or 404.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssistant } from '../src/core.mjs';
import { configFromEnv } from '../src/config.mjs';
import { createLedger, USD } from '../src/ledger.mjs';
import { addressPrefix, countQuestion, DEFAULT_LIMITS, loadSalt, RateLimited, viewerAddress, visitorHash } from '../src/limits.mjs';
import { memoryStore } from '../src/store.mjs';
import { actualMicros } from '../src/pricing.mjs';
import { SYSTEM_PROMPT } from '../src/prompt.mjs';

const NOW = new Date('2026-10-18T12:00:00Z');
const SESSION = 'session-0123456789abcdef';

function config(over = {}) {
  return {
    ...configFromEnv({ ASSISTANT_ENABLED: 'true' }),
    ...over,
  };
}

/** A fake Bedrock stream: the events Anthropic's Messages stream sends. */
function fakeModel({ text = 'The demand part is 45% of the score.', usage = { input_tokens: 3000, output_tokens: 40 }, failAt = null, errorName = 'ModelStreamErrorException' } = {}) {
  const calls = [];
  return {
    calls,
    async *stream(req) {
      calls.push(req);
      if (failAt === 'before') throw Object.assign(new Error('x'), { name: errorName });
      yield { type: 'message_start', message: { usage: { input_tokens: usage.input_tokens, output_tokens: 1 } } };
      yield { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } };
      for (const part of text.match(/.{1,8}/gs) ?? []) yield { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: part } };
      if (failAt === 'middle') throw Object.assign(new Error('x'), { name: errorName });
      yield { type: 'content_block_stop', index: 0 };
      yield { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: { output_tokens: usage.output_tokens } };
      yield { type: 'message_stop', 'amazon-bedrock-invocationMetrics': { inputTokenCount: usage.input_tokens, outputTokenCount: usage.output_tokens } };
    },
  };
}

function setup({ cfg = config(), model = fakeModel(), store = memoryStore(), caps } = {}) {
  const ledger = createLedger(store, caps ?? { monthMicros: cfg.monthMicros, dayMicros: cfg.dayMicros, deeperMonthMicros: cfg.deeperMonthMicros });
  const a = createAssistant(cfg, { store, ledger, model, now: () => NOW });
  return { a, store, ledger, model };
}

/** Call the handler and collect what it sends. */
async function call(a, { method = 'POST', path = '/api/assistant/ask', body, headers = { 'cloudfront-viewer-address': '203.0.113.7:4431' } } = {}) {
  const out = { status: null, headers: null, chunks: [], ended: false };
  await a.handle({ method, path, headers, body: typeof body === 'string' ? body : JSON.stringify(body) }, {
    start(status, h) { out.status = status; out.headers = h; },
    write(t) { out.chunks.push(t); },
    end() { out.ended = true; },
  });
  const text = out.chunks.join('');
  out.json = () => JSON.parse(text);
  out.lines = () => text.split('\n').filter(Boolean).map((l) => JSON.parse(l));
  return out;
}

const ask = (over = {}) => ({
  v: 1, session: SESSION, question: 'What does the demand part measure?', history: [],
  context: { app: { step: 'results', hasRun: true, engine: 'real', rows: 360, columns: 31 } }, ...over,
});

test('an answer streams as NDJSON: meta, text, done; and the ledger settles to the actual cost', async () => {
  const { a, store, model } = setup();
  const r = await call(a, { body: ask() });
  assert.equal(r.status, 200);
  assert.match(r.headers['content-type'], /ndjson/);
  assert.equal(r.ended, true);
  const lines = r.lines();
  assert.equal(lines[0].t, 'meta');
  assert.ok(lines[0].methodNumbers.includes(45));
  assert.equal(lines.filter((l) => l.t === 'text').map((l) => l.v).join(''), 'The demand part is 45% of the score.');
  assert.deepEqual(lines.at(-1), { t: 'done', stop: 'end_turn' });
  const m = store.items.get('ledger#month#2026-10');
  assert.equal(m.committed, actualMicros('haiku', { input_tokens: 3000, output_tokens: 40 }));
  assert.equal(m.spent, m.committed);
  assert.equal(m.calls, 1);
  // The request Bedrock received.
  const sent = model.calls[0];
  assert.equal(sent.modelId, 'global.anthropic.claude-haiku-5-5');
  assert.equal(sent.body.anthropic_version, 'bedrock-2023-05-31');
  assert.equal(sent.body.max_tokens, 1200);
  assert.deepEqual(sent.body.thinking, { type: 'disabled' });
  assert.equal(sent.body.system[0].text, SYSTEM_PROMPT);
  assert.match(sent.body.messages.at(-1).content[0].text, /<question>\nWhat does the demand part measure\?\n<\/question>/);
});

test('a model failure mid-answer keeps the whole reservation; a refusal before it costs nothing', async () => {
  {
    const { a, store } = setup({ model: fakeModel({ failAt: 'middle' }) });
    const r = await call(a, { body: ask() });
    assert.equal(r.status, 200);
    assert.equal(r.lines().at(-1).t, 'error');
    const m = store.items.get('ledger#month#2026-10');
    assert.ok(m.committed > actualMicros('haiku', { input_tokens: 3000, output_tokens: 40 }), 'reservation kept');
    assert.equal(m.spent, m.committed);
  }
  {
    const { a, store } = setup({ model: fakeModel({ failAt: 'before', errorName: 'ValidationException' }) });
    const r = await call(a, { body: ask() });
    assert.equal(r.lines().at(-1).t, 'error');
    assert.equal(store.items.get('ledger#month#2026-10').committed, 0);
  }
  {
    // An unknown failure before the first event (a timeout, say) is assumed billed.
    const { a, store } = setup({ model: fakeModel({ failAt: 'before', errorName: 'AbortError' }) });
    await call(a, { body: ask() });
    assert.ok(store.items.get('ledger#month#2026-10').committed > 0);
  }
});

test("the month's cap reached: refused before the model, with the plain message", async () => {
  const model = fakeModel();
  const cfg = config({ monthMicros: 3000, dayMicros: 3000 });
  const { a, store } = setup({ cfg, model });
  store.items.set('ledger#month#2026-10', { committed: 2990 });
  const r = await call(a, { body: ask() });
  assert.equal(r.status, 503);
  const body = r.json();
  assert.equal(body.error, 'cap');
  assert.equal(body.scope, 'month');
  assert.equal(body.resumes, '2026-11-01T00:00:00.000Z');
  assert.equal(body.message, "The assistant has reached this month's limit. Everything else in the planner keeps working.");
  assert.equal(model.calls.length, 0);
  const s = await call(a, { method: 'GET', path: '/api/assistant/status' });
  assert.equal(s.status, 200);
  assert.equal(s.json().state, 'paused');
  assert.equal(s.json().scope, 'month');
});

test('status when available, and when the ledger cannot be read', async () => {
  const { a } = setup();
  const s = (await call(a, { method: 'GET', path: '/api/assistant/status' })).json();
  assert.equal(s.state, 'available');
  assert.equal(s.deeper, false);
  const broken = { read: async () => { throw new Error('down'); }, write: async () => { throw new Error('down'); }, putNew: async () => false };
  const b = setup({ store: broken }).a;
  assert.equal((await call(b, { method: 'GET', path: '/api/assistant/status' })).json().state, 'paused');
  const r = await call(b, { body: ask() });
  assert.equal(r.status, 503);
  assert.equal(r.json().error, 'ledger');
});

test('switched off, invalid, too large, deeper unavailable: refused before the model', async () => {
  const model = fakeModel();
  const off = setup({ cfg: config({ enabled: false }), model }).a;
  assert.equal((await call(off, { body: ask() })).status, 503);
  assert.equal((await call(off, { method: 'GET', path: '/api/assistant/status' })).json().state, 'off');
  const { a } = setup({ model });
  const bad = await call(a, { body: ask({ context: { app: { step: 'results', hasRun: true, engine: 'real' }, shared: { rows: [['FC-1']] } } }) });
  assert.equal(bad.status, 400);
  assert.equal(bad.json().error, 'invalid');
  assert.equal((await call(a, { body: 'not json' })).status, 400);
  assert.equal((await call(a, { body: 'x'.repeat(70_000) })).status, 413);
  assert.equal((await call(a, { body: ask({ deeper: true }) })).json().error, 'deeper_off');
  assert.equal(model.calls.length, 0);
});

test('never 403 or 404: unknown paths are 400, wrong methods 405', async () => {
  const { a } = setup();
  assert.equal((await call(a, { method: 'GET', path: '/api/assistant/secret' })).status, 400);
  assert.equal((await call(a, { method: 'GET', path: '/api/assistant/ask' })).status, 405);
  assert.equal((await call(a, { method: 'POST', path: '/api/assistant/status', body: '' })).status, 405);
  assert.equal((await call(a, { method: 'GET', path: '/api/assistant/status/' })).status, 200);
});

test('a deeper answer uses the deeper model under its own sub-cap', async () => {
  const cfg = configFromEnv({ ASSISTANT_ENABLED: 'true', DEEPER_MODEL_ID: 'global.anthropic.claude-sonnet-5-5' });
  const model = fakeModel();
  const { a, store } = setup({ cfg, model });
  const r = await call(a, { body: ask({ deeper: true }) });
  assert.equal(r.status, 200);
  assert.equal(model.calls[0].modelId, 'global.anthropic.claude-sonnet-5-5');
  assert.equal(model.calls[0].body.thinking, undefined, 'Sonnet 5.5 refuses thinking switched off');
  assert.equal(store.items.get('ledger#month#2026-10').deeperCommitted, actualMicros('sonnet', { input_tokens: 3000, output_tokens: 40 }));
});

test('rate limits: per address per hour, then everyone per minute', async () => {
  const model = fakeModel();
  const cfg = config({ limits: { ...DEFAULT_LIMITS, perAddressHour: 2, globalMinute: 3 } });
  const { a } = setup({ cfg, model });
  assert.equal((await call(a, { body: ask() })).status, 200);
  assert.equal((await call(a, { body: ask() })).status, 200);
  const third = await call(a, { body: ask() });
  assert.equal(third.status, 429);
  assert.equal(third.json().scope, 'hour');
  assert.equal(third.json().resumes, '2026-10-18T13:00:00.000Z');
  // Another visitor in the same /24 is the same visitor.
  assert.equal((await call(a, { body: ask(), headers: { 'cloudfront-viewer-address': '203.0.113.200:1' } })).status, 429);
  // A refused request counts nothing (all limits are one transaction), so a different address
  // gets the minute's third answer, and the fourth is refused for everyone.
  assert.equal((await call(a, { body: ask(), headers: { 'cloudfront-viewer-address': '198.51.100.1:1' } })).status, 200);
  const fourth = await call(a, { body: ask(), headers: { 'cloudfront-viewer-address': '192.0.2.1:1' } });
  assert.equal(fourth.status, 429);
  assert.equal(fourth.json().scope, 'everyone');
  assert.equal(model.calls.length, 3);
});

test('limits: per session per day, and the salt is created once', async () => {
  const store = memoryStore();
  const salt = await loadSalt(store);
  assert.equal(await loadSalt(store), salt);
  const limits = { ...DEFAULT_LIMITS, perSessionDay: 2, perAddressHour: 100, perAddressDay: 100, globalMinute: 100 };
  for (let i = 0; i < 2; i += 1) await countQuestion(store, { visitor: `v${i}`, session: SESSION, now: NOW, limits });
  await assert.rejects(countQuestion(store, { visitor: 'v9', session: SESSION, now: NOW, limits }), (e) => e instanceof RateLimited && e.scope === 'day');
  // Concurrent salts: everyone ends with the same one.
  const s2 = memoryStore({ delay: () => new Promise((r) => setTimeout(r, Math.random() * 3)) });
  const salts = await Promise.all(Array.from({ length: 20 }, () => loadSalt(s2)));
  assert.equal(new Set(salts).size, 1);
});

test('addresses: CloudFront first, the last forwarded entry otherwise, hashed by prefix', () => {
  assert.equal(viewerAddress({ 'CloudFront-Viewer-Address': '203.0.113.7:443' }), '203.0.113.7');
  assert.equal(viewerAddress({ 'cloudfront-viewer-address': '[2001:db8::1]:443' }), '2001:db8::1');
  assert.equal(viewerAddress({ 'cloudfront-viewer-address': '2001:db8::1:443' }), '2001:db8::1');
  assert.equal(viewerAddress({ 'x-forwarded-for': '1.2.3.4, 198.51.100.9' }), '198.51.100.9');
  assert.equal(viewerAddress({}), 'unknown');
  assert.equal(addressPrefix('203.0.113.7'), '203.0.113.0/24');
  assert.equal(addressPrefix('2001:db8:abcd:12ff::1'), '2001:0db8:abcd:1200::/56');
  assert.equal(visitorHash('s', '203.0.113.7'), visitorHash('s', '203.0.113.99'));
  assert.notEqual(visitorHash('s', '203.0.113.7'), visitorHash('t', '203.0.113.7'));
  assert.doesNotMatch(visitorHash('s', '203.0.113.7'), /203/);
});

test('logs carry metadata only, never the question or the shared results', async () => {
  const { a } = setup();
  const seen = [];
  const orig = { log: console.log, warn: console.warn };
  console.log = (...x) => seen.push(x.join(' '));
  console.warn = (...x) => seen.push(x.join(' '));
  try {
    await call(a, { body: ask({ question: 'SECRET-QUESTION-TEXT' }) });
    await call(a, { body: ask({ question: 'SECRET-QUESTION-TEXT', context: { app: { step: 'nope', hasRun: true, engine: 'real' } } }) });
  } finally {
    Object.assign(console, orig);
  }
  assert.ok(seen.length >= 2);
  for (const line of seen) {
    assert.doesNotMatch(line, /SECRET-QUESTION-TEXT|203\.0\.113/);
  }
});

test('configuration: defaults, and anything malformed refuses to start', () => {
  const c = configFromEnv({ ASSISTANT_ENABLED: 'true' });
  assert.equal(c.monthMicros, 5 * USD);
  assert.equal(c.dayMicros, 0.35 * USD);
  assert.equal(c.deeper, null);
  assert.equal(configFromEnv({}).enabled, false, 'off unless switched on');
  assert.throws(() => configFromEnv({ MONTHLY_CAP_USD: 'five' }));
  assert.throws(() => configFromEnv({ MODEL_PRICE: 'opus' }));
  assert.throws(() => configFromEnv({ MAX_TOKENS: '100000' }));
  assert.throws(() => configFromEnv({ MODEL_ID: 'anthropic.claude-haiku-5-5' }), /inference profile/);
  assert.throws(() => configFromEnv({ MODEL_EXTRA_JSON: '{"system":"x"}' }));
  assert.throws(() => configFromEnv({ MODEL_EXTRA_JSON: '[1]' }));
  assert.equal(configFromEnv({ MONTHLY_CAP_USD: '0' }).monthMicros, 0);
});

test('the Lambda entry point refuses with a 503 when it cannot start (bad configuration)', async () => {
  let meta = null;
  const written = [];
  globalThis.awslambda = {
    streamifyResponse: (fn) => fn,
    HttpResponseStream: { from: (s, m) => { meta = m; return s; } },
  };
  const saved = process.env.MODEL_PRICE;
  process.env.MODEL_PRICE = 'not-a-model';
  const quiet = console.warn;
  console.warn = () => {};
  try {
    const { handler } = await import('../src/index.mjs');
    await handler({ rawPath: '/api/assistant/status', requestContext: { http: { method: 'GET' } }, headers: {} }, { write: (t) => written.push(t), end: () => {} });
  } finally {
    console.warn = quiet;
    if (saved === undefined) delete process.env.MODEL_PRICE; else process.env.MODEL_PRICE = saved;
  }
  assert.equal(meta.statusCode, 503);
  assert.equal(JSON.parse(written.join('')).error, 'unavailable');
});

test('a cap of zero refuses every question', async () => {
  const cfg = configFromEnv({ ASSISTANT_ENABLED: 'true', MONTHLY_CAP_USD: '0' });
  const model = fakeModel();
  const { a } = setup({ cfg, model });
  const r = await call(a, { body: ask() });
  assert.equal(r.status, 503);
  assert.equal(r.json().scope, 'month');
  assert.equal(model.calls.length, 0);
  assert.equal((await call(a, { method: 'GET', path: '/api/assistant/status' })).json().state, 'paused');
});
