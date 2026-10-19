// The proxy's request handling with a fake model and the memory store: refusals before the
// model, streaming, settling, the rate limits, and never a 403 or 404.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssistant, mergeUsage, WORDS } from '../src/core.mjs';
import { configFromEnv } from '../src/config.mjs';
import { createLedger, USD } from '../src/ledger.mjs';
import { addressPrefix, countQuestion, DEFAULT_LIMITS, DEFAULT_LOCAL, loadSalt, localLimiter, NO_ADDRESS, RateLimited, TokenBucket, viewerAddress, visitorHash } from '../src/limits.mjs';
import { memoryStore } from '../src/store.mjs';
import { actualMicros, priceForModel, PRICES, worstCaseMicros } from '../src/pricing.mjs';
import { SYSTEM_PROMPT } from '../src/prompt.mjs';
import { readRetentionMode, signV4 } from '../src/retention.mjs';

const NOW = new Date('2026-10-18T12:00:00Z');
const SESSION = 'session-0123456789abcdef';

/** Local buckets wide open, so tests of the shared limits and the ledger are not cut short. */
const OPEN_LOCAL = { askGlobal: { capacity: 1e6, perMinute: 1e6 }, askAddress: { capacity: 1e6, perMinute: 1e6 }, statusAddress: { capacity: 1e6, perMinute: 1e6 }, addresses: 5000 };

function config(over = {}) {
  return {
    ...configFromEnv({ ASSISTANT_ENABLED: 'true' }),
    local: OPEN_LOCAL,
    statusCacheMs: 0,
    ...over,
  };
}

/**
 * A fake Bedrock stream: the events Anthropic's Messages stream sends. `delta` and `metrics`
 * are the output counts in message_delta and in the invocation metrics; null leaves one out.
 */
function fakeModel({ text = 'The demand part is 45% of the score.', usage = { input_tokens: 3000, output_tokens: 40 }, delta, metrics, failAt = null, errorName = 'ModelStreamErrorException' } = {}) {
  const calls = [];
  const deltaUsage = delta === undefined ? { output_tokens: usage.output_tokens } : delta;
  const invocation = metrics === undefined ? { inputTokenCount: usage.input_tokens, outputTokenCount: usage.output_tokens } : metrics;
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
      yield { type: 'message_delta', delta: { stop_reason: 'end_turn' }, ...(deltaUsage ? { usage: deltaUsage } : {}) };
      yield { type: 'message_stop', ...(invocation ? { 'amazon-bedrock-invocationMetrics': invocation } : {}) };
    },
  };
}

function setup({ cfg = config(), model = fakeModel(), store = memoryStore(), caps, retention = async () => 'none', clock = { t: NOW } } = {}) {
  const ledger = createLedger(store, caps ?? { monthMicros: cfg.monthMicros, dayMicros: cfg.dayMicros, deeperMonthMicros: cfg.deeperMonthMicros, visitorDayMicros: cfg.visitorDayMicros });
  const a = createAssistant(cfg, { store, ledger, model, retention, now: () => clock.t });
  return { a, store, ledger, model, clock };
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
  assert.equal((await call(a, { body: 'x'.repeat(32 * 1024 + 1) })).status, 413, 'the body limit is 32 KB');
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
  // The visitor's own limits are checked first, so their refused requests never reach the
  // minute's shared counter: a different address gets the minute's third answer, and the
  // fourth is refused for everyone.
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

test('addresses: CloudFront only, never X-Forwarded-For; hashed by prefix (M1)', () => {
  assert.equal(viewerAddress({ 'CloudFront-Viewer-Address': '203.0.113.7:443' }), '203.0.113.7');
  assert.equal(viewerAddress({ 'cloudfront-viewer-address': '[2001:db8::1]:443' }), '2001:db8::1');
  assert.equal(viewerAddress({ 'cloudfront-viewer-address': '2001:db8::1:443' }), '2001:db8::1');
  assert.equal(viewerAddress({ 'x-forwarded-for': '1.2.3.4, 198.51.100.9' }), NO_ADDRESS, 'a viewer can write X-Forwarded-For');
  assert.equal(viewerAddress({ 'cloudfront-viewer-address': 'not an address:1' }), NO_ADDRESS);
  assert.equal(viewerAddress({}), NO_ADDRESS);
  assert.equal(addressPrefix(NO_ADDRESS), NO_ADDRESS);
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
  assert.equal(c.visitorDayMicros, 0.05 * USD);
  assert.equal(c.statusCacheMs, 30_000);
  assert.deepEqual(c.local, DEFAULT_LOCAL);
});

test('S3: the price row comes from the model ID, and a mismatch refuses to start', () => {
  assert.equal(priceForModel('global.anthropic.claude-haiku-5-5'), 'haiku');
  assert.equal(priceForModel('global.anthropic.claude-sonnet-5-5'), 'sonnet');
  assert.throws(() => priceForModel('global.anthropic.claude-opus-5-5'));
  assert.throws(() => priceForModel('global.anthropic.claude-haiku-5-5-preview'));
  assert.equal(configFromEnv({ MODEL_ID: 'global.anthropic.claude-sonnet-5-5' }).model.price, 'sonnet', 'derived, not the default haiku');
  assert.equal(configFromEnv({ MODEL_PRICE: 'haiku' }).model.price, 'haiku', 'a matching MODEL_PRICE is accepted');
  assert.throws(() => configFromEnv({ MODEL_ID: 'global.anthropic.claude-sonnet-5-5', MODEL_PRICE: 'haiku' }), /priced as sonnet/);
  assert.throws(() => configFromEnv({ MODEL_ID: 'global.anthropic.claude-opus-5-5' }), /no price/);
  assert.throws(() => configFromEnv({ DEEPER_MODEL_ID: 'global.anthropic.claude-sonnet-5-5', DEEPER_MODEL_PRICE: 'haiku' }));
  assert.equal(configFromEnv({ DEEPER_MODEL_ID: 'global.anthropic.claude-sonnet-5-5' }).deeper.price, 'sonnet');
  // Sonnet 5.5's cache read price (M2).
  assert.equal(PRICES.sonnet.cacheRead, 0.20);
});

test('S3: MODEL_EXTRA_JSON accepts allow-listed keys only', () => {
  const ok = [
    '{"thinking":{"type":"disabled"}}',
    '{"thinking":{"type":"adaptive"},"output_config":{"effort":"low"}}',
    '{"temperature":0.2}',
    '{}',
  ];
  for (const v of ok) assert.doesNotThrow(() => configFromEnv({ MODEL_EXTRA_JSON: v }), v);
  const refused = [
    '{"cache_control":{"type":"ephemeral"}}',
    '{"tools":[]}',
    '{"tool_choice":{"type":"any"}}',
    '{"metadata":{"user_id":"x"}}',
    '{"anthropic_beta":["x"]}',
    '{"max_tokens":64000}',
    '{"messages":[]}',
    '{"thinking":{"type":"enabled","budget_tokens":30000}}',
    '{"thinking":{"type":"adaptive","budget_tokens":1}}',
    '{"output_config":{"effort":"max"}}',
    '{"output_config":{"effort":"low","format":{}}}',
    '{"temperature":2}',
    '{"temperature":"0.5"}',
    'null',
  ];
  for (const v of refused) {
    assert.throws(() => configFromEnv({ MODEL_EXTRA_JSON: v }), undefined, v);
    assert.throws(() => configFromEnv({ DEEPER_MODEL_ID: 'global.anthropic.claude-sonnet-5-5', DEEPER_EXTRA_JSON: v }), undefined, v);
  }
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

// ---------------------------------------------------------------- security review fixes

const storeCalls = (store) => Object.values(store.calls).reduce((a, b) => a + b, 0);
const from = (ip) => ({ 'cloudfront-viewer-address': `${ip}:443` });

function capture(fn) {
  const seen = [];
  const orig = { log: console.log, warn: console.warn };
  console.log = (...x) => seen.push(x.join(' '));
  console.warn = (...x) => seen.push(x.join(' '));
  return Promise.resolve().then(fn).finally(() => Object.assign(console, orig)).then(() => seen);
}

test('S1: the token bucket refills by the minute and the address map stays bounded', () => {
  const b = new TokenBucket({ capacity: 2, perMinute: 1 }, 0);
  assert.equal(b.take(0), true);
  assert.equal(b.take(0), true);
  assert.equal(b.take(1000), false);
  assert.equal(b.nextMs(1000), 60_000);
  assert.equal(b.take(60_000), true);
  const l = localLimiter({ ...DEFAULT_LOCAL, addresses: 3 }, 0);
  for (let i = 0; i < 50; i += 1) l.check('ask', `198.51.${i}.1`, 0);
  assert.equal(l.size('ask'), 3);
});

test('S1: a flood from one address is refused in memory, with no database call', async () => {
  const model = fakeModel();
  const { a, store } = setup({ cfg: config({ local: DEFAULT_LOCAL }), model });
  for (let i = 0; i < DEFAULT_LOCAL.askAddress.capacity; i += 1) assert.equal((await call(a, { body: ask() })).status, 200);
  const before = storeCalls(store);
  const seen = await capture(async () => {
    for (let i = 0; i < 200; i += 1) {
      const r = await call(a, { body: i % 2 ? ask() : 'not json' });
      assert.equal(r.status, 429);
      assert.equal(r.json().scope, 'hour');
    }
  });
  assert.equal(storeCalls(store), before, 'no DynamoDB read or write for a refused request');
  assert.equal(model.calls.length, DEFAULT_LOCAL.askAddress.capacity);
  assert.equal(seen.filter((l) => l.includes('local_refusal')).length, 1, 'refusals are logged once a minute, with a count');
  // Another address in the same /24 shares the bucket.
  assert.equal((await call(a, { body: ask(), headers: from('203.0.113.250') })).status, 429);
});

test('S1: everyone together is limited per instance, also before any database call', async () => {
  const { a, store } = setup({ cfg: config({ local: DEFAULT_LOCAL }) });
  for (let i = 0; i < DEFAULT_LOCAL.askGlobal.capacity; i += 1) assert.equal((await call(a, { body: ask(), headers: from(`198.51.${i}.1`) })).status, 200);
  const before = storeCalls(store);
  const r = await call(a, { body: ask(), headers: from('192.0.2.1') });
  assert.equal(r.status, 429);
  assert.equal(r.json().scope, 'everyone');
  assert.equal(storeCalls(store), before);
});

test('S1: /status is served from memory for 30 seconds and limited per address', async () => {
  const clock = { t: NOW };
  let checks = 0;
  const { a, store } = setup({ cfg: config({ local: DEFAULT_LOCAL, statusCacheMs: 30_000 }), clock, retention: async () => { checks += 1; return 'none'; } });
  const status = (ip) => call(a, { method: 'GET', path: '/api/assistant/status', headers: from(ip) });
  assert.equal((await status('198.51.100.1')).json().state, 'available');
  const reads = store.calls.read;
  for (let i = 0; i < 50; i += 1) assert.equal((await status(`192.0.${i}.9`)).status, 200);
  assert.equal(store.calls.read, reads, 'cached: no ledger read within 30 seconds');
  clock.t = new Date(NOW.getTime() + 31_000);
  await status('198.51.100.1');
  assert.ok(store.calls.read > reads, 'read again after 30 seconds');
  assert.equal(checks, 1, 'the retention mode is cached longer than the status');
  // One address: the bucket's capacity, then refused without reading anything.
  const one = '203.0.113.5';
  let ok = 0;
  for (let i = 0; i < 30; i += 1) if ((await status(one)).status === 200) ok += 1;
  assert.equal(ok, DEFAULT_LOCAL.statusAddress.capacity);
  assert.equal(store.calls.write + store.calls.update, 0, 'status never writes');
});

test('S1: a cap this instance has seen refuses later questions without DynamoDB', async () => {
  const model = fakeModel();
  const { a, store } = setup({ cfg: config({ monthMicros: 3000, dayMicros: 3000 }), model });
  store.items.set('ledger#month#2026-10', { committed: 2990 });
  assert.equal((await call(a, { body: ask() })).json().scope, 'month');
  const before = storeCalls(store);
  const r = await call(a, { body: ask(), headers: from('198.51.100.1') });
  assert.equal(r.status, 503);
  assert.equal(r.json().scope, 'month');
  assert.equal(r.json().resumes, '2026-11-01T00:00:00.000Z');
  assert.equal(storeCalls(store), before);
  assert.equal(model.calls.length, 0);
});

test('S2: settles at the larger of the stream and the invocation metrics, field by field', async () => {
  const expected = actualMicros('haiku', { input_tokens: 3000, output_tokens: 1200 });
  assert.equal(expected, 900);
  {
    // The stream says 40 output tokens, the metrics 1200: the ledger takes 1200.
    const model = fakeModel({ usage: { input_tokens: 3000, output_tokens: 40 }, metrics: { inputTokenCount: 3000, outputTokenCount: 1200 } });
    const { a, store } = setup({ model });
    await call(a, { body: ask() });
    assert.equal(store.items.get('ledger#month#2026-10').committed, expected);
  }
  {
    // And the other way round.
    const model = fakeModel({ usage: { input_tokens: 3000, output_tokens: 1200 }, metrics: { inputTokenCount: 2000, outputTokenCount: 40 } });
    const { a, store } = setup({ model });
    await call(a, { body: ask() });
    assert.equal(store.items.get('ledger#month#2026-10').committed, expected);
  }
  {
    // A final count from the metrics alone is enough.
    const model = fakeModel({ delta: null, metrics: { inputTokenCount: 3000, outputTokenCount: 1200 } });
    const { a, store } = setup({ model });
    await call(a, { body: ask() });
    assert.equal(store.items.get('ledger#month#2026-10').committed, expected);
  }
  assert.deepEqual(mergeUsage({ input_tokens: 3000, output_tokens: 40, cache_read_input_tokens: 5 }, { inputTokenCount: 10, outputTokenCount: 1200, cacheWriteInputTokenCount: 7 }), {
    input_tokens: 3000, cache_creation_input_tokens: 7, cache_read_input_tokens: 5, output_tokens: 1200,
  });
});

test('S2: with no final output count, the whole reservation is kept', async () => {
  const model = fakeModel({ delta: null, metrics: null });
  const { a, store } = setup({ model });
  const r = await call(a, { body: ask() });
  assert.equal(r.lines().at(-1).t, 'done');
  const m = store.items.get('ledger#month#2026-10');
  assert.ok(m.committed > 900, 'not settled from the opening count');
  assert.equal(m.committed, m.spent);
  // The reservation is the worst case for the request that was sent.
  const sent = Buffer.byteLength(JSON.stringify(model.calls[0].body));
  assert.equal(m.committed, worstCaseMicros('haiku', sent, 1200));
});

test('S4: one visitor cannot use more than their daily share', async () => {
  const model = fakeModel();
  const cfg = config();
  const { a, store } = setup({ cfg, model });
  assert.equal(cfg.visitorDayMicros, 50_000);
  assert.equal((await call(a, { body: ask() })).status, 200);
  const visitor = visitorHash(await loadSalt(store), '203.0.113.7');
  const key = `ledger#visitor#${visitor}#2026-10-18`;
  assert.equal(store.items.get(key).committed, actualMicros('haiku', { input_tokens: 3000, output_tokens: 40 }), 'settled to the actual cost');
  store.items.set(key, { committed: 49_000, spent: 49_000 });
  let r;
  const seen = await capture(async () => { r = await call(a, { body: ask() }); });
  assert.equal(r.status, 503);
  assert.equal(r.json().scope, 'visitor');
  assert.equal(r.json().resumes, '2026-10-19T00:00:00.000Z');
  assert.equal(r.json().message, WORDS.visitor);
  assert.ok(seen.some((l) => l.includes('"visitor_limit"')));
  assert.ok(!seen.some((l) => l.includes('"cap_reached"')), 'the cap alarm is not raised by one visitor');
  // Remembered: refused again without DynamoDB; another visitor is still answered.
  const before = storeCalls(store);
  assert.equal((await call(a, { body: ask() })).json().scope, 'visitor');
  assert.equal(storeCalls(store), before);
  assert.equal((await call(a, { body: ask(), headers: from('198.51.100.1') })).status, 200);
  assert.equal(model.calls.length, 2);
});

test('S4: the limits are lower: 30 a day per address, and the body at most 32 KB', () => {
  assert.equal(DEFAULT_LIMITS.perAddressDay, 30);
  assert.ok(DEFAULT_LIMITS.perAddressHour <= DEFAULT_LIMITS.perAddressDay);
  // At 32 KB plus the system prompt, one Haiku question reserves well under a cent, so the
  // visitor's share is at least eight full-size questions.
  const worst = worstCaseMicros('haiku', 32 * 1024 + Buffer.byteLength(SYSTEM_PROMPT) + 2000, 1200);
  assert.ok(worst < 0.01 * USD, `worst case ${worst}`);
  assert.ok(configFromEnv({}).visitorDayMicros / worst >= 8);
});

test('M1: requests without CloudFront\'s address share one conservative bucket and are counted', async () => {
  const { a, store } = setup({ cfg: config({ local: DEFAULT_LOCAL }) });
  let statuses = [];
  const seen = await capture(async () => {
    for (let i = 0; i < 6; i += 1) {
      statuses.push((await call(a, { body: ask(), headers: { 'x-forwarded-for': `198.51.100.${i}` } })).status);
    }
  });
  assert.deepEqual(statuses, [200, 200, 200, 429, 429, 429], 'different X-Forwarded-For values do not get separate buckets');
  assert.equal(seen.filter((l) => l.includes('"no_viewer_address"')).length, 1);
  // The shared limits count them under one visitor too.
  const salt = await loadSalt(store);
  const hour = `rate#addr#${visitorHash(salt, NO_ADDRESS)}#2026101812`;
  assert.equal(store.items.get(hour).n, 3);
});

test('M7: data retention must read "none", or nothing is sent to the model', async () => {
  for (const retention of [async () => 'default', async () => 'provider_data_share', async () => { throw new Error('down'); }, undefined]) {
    const model = fakeModel();
    const store = memoryStore();
    const cfg = config();
    const ledger = createLedger(store, { monthMicros: cfg.monthMicros, dayMicros: cfg.dayMicros, deeperMonthMicros: cfg.deeperMonthMicros, visitorDayMicros: cfg.visitorDayMicros });
    const a = createAssistant(cfg, { store, ledger, model, retention, now: () => NOW });
    let r;
    await capture(async () => { await a.warm(); r = await call(a, { body: ask() }); });
    assert.equal(r.status, 503);
    assert.equal(r.json().error, 'unavailable');
    assert.equal(model.calls.length, 0);
    assert.equal(storeCalls(store), 0, 'refused before the rate limits and the ledger');
    const s = (await call(a, { method: 'GET', path: '/api/assistant/status' })).json();
    assert.equal(s.state, 'paused');
    assert.equal(s.scope, 'unavailable');
  }
});

test('M7: a failed retention check is retried after a minute; a good one is reused', async () => {
  const clock = { t: NOW };
  let mode = 'default';
  let checks = 0;
  const { a, model } = setup({ clock, retention: async () => { checks += 1; return mode; } });
  await capture(() => a.warm());
  assert.equal(checks, 1);
  mode = 'none';
  assert.equal((await call(a, { body: ask() })).status, 503, 'still the cached refusal');
  clock.t = new Date(NOW.getTime() + 61_000);
  assert.equal((await call(a, { body: ask() })).status, 200);
  assert.equal((await call(a, { body: ask() })).status, 200);
  assert.equal(checks, 2);
  mode = 'default';
  clock.t = new Date(NOW.getTime() + 61_000 + 15 * 60_000 + 1);
  await capture(async () => assert.equal((await call(a, { body: ask() })).status, 503));
  assert.equal(model.calls.length, 2);
});
