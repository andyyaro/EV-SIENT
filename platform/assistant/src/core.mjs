// The assistant proxy's request handling, with no AWS in it: the store (DynamoDB or memory),
// the model (Bedrock or a test double) and the data retention check are passed in.
// handler.mjs wires the real ones.
//
// Routes (CloudFront sends /api/assistant/* here; the path is matched on its end so a prefix
// change in CloudFront does not matter):
//   GET  .../status   whether the assistant can answer now, and if not, until when
//   POST .../ask      one question; the answer streams back as NDJSON lines
//
// Status codes avoid 403 and 404, because the app's distribution turns those into its 404 page.
//
// Every refusal happens before the model is called, cheapest first: the size, this instance's
// in-memory buckets (no database call), the shape (validate.mjs), switched off, data retention
// not confirmed as none, a cap this instance already knows is reached (no database call), the
// shared rate limits (limits.mjs), and the spend ledger (ledger.mjs). Any error in the limits,
// the ledger or the retention check refuses the call (fail closed). Nothing here logs or
// stores the question, the answer or the shared results.
//
// What the server enforces is the shape and the limits: closed objects, rounded numbers,
// sanitised labels, sizes and spend. It cannot tell whether a label is really a column header,
// so what the content is (no cells, names or coordinates) rests on the browser's payload
// builder (platform/app/src/assistant/payload.ts).

import { Invalid, LIMITS, validateAsk } from './validate.mjs';
import { CapReached } from './ledger.mjs';
import { countQuestion, localLimiter, loadSalt, NO_ADDRESS, RateLimited, viewerAddress, visitorHash } from './limits.mjs';
import { actualMicros, worstCaseMicros } from './pricing.mjs';
import { buildBody, buildMessages, methodNumbers, SYSTEM_PROMPT } from './prompt.mjs';

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
const STREAM_HEADERS = { 'content-type': 'application/x-ndjson; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' };

/** The plain words the panel shows for each refusal. */
export const WORDS = {
  off: 'The assistant is switched off. Everything else in the planner keeps working.',
  unavailable: 'The assistant is not available right now. Everything else in the planner keeps working.',
  month: "The assistant has reached this month's limit. Everything else in the planner keeps working.",
  day: "The assistant has reached today's limit. Everything else in the planner keeps working.",
  visitor: "You have used today's share of the assistant. Ask again tomorrow. Everything else in the planner keeps working.",
  deeper: "Deeper answers have reached this month's limit. Ask without a deeper answer instead.",
  deeperOff: 'Deeper answers are not available.',
  busy: 'The assistant is busy. Wait a minute and ask again.',
  rateHour: 'You have asked a lot of questions this hour. Wait a while and ask again.',
  rateDay: 'You have asked as many questions as one visitor can today. Ask again tomorrow.',
  ledger: 'The assistant cannot check its spending limit right now, so it is not answering. Try again later.',
  invalid: 'The planner sent something the assistant does not accept, so nothing was sent to the model.',
  tooLarge: 'This question and what it shares are too large to send. Share fewer columns or start a new conversation.',
  model: 'The assistant could not answer just now. Try again in a minute.',
};

/** Bedrock errors that reject a request before any model work, so nothing is billed. */
const REFUSED_UNBILLED = new Set([
  'ValidationException', 'AccessDeniedException', 'ResourceNotFoundException', 'ThrottlingException',
  'ServiceQuotaExceededException', 'ModelNotReadyException', 'ServiceUnavailableException',
]);

function log(level, event, fields = {}) {
  // Metadata only: never the question, the answer, the shared results or an address.
  console[level === 'warn' ? 'warn' : 'log'](JSON.stringify({ level, event, ...fields }));
}

/** Bedrock's usage, merged from the stream events and the invocation metrics, field by field. */
export function mergeUsage(stream, metrics) {
  const n = (v) => (Number.isFinite(v) && v > 0 ? v : 0);
  const m = metrics ?? {};
  return {
    input_tokens: Math.max(n(stream.input_tokens), n(m.inputTokenCount)),
    cache_creation_input_tokens: Math.max(n(stream.cache_creation_input_tokens), n(m.cacheWriteInputTokenCount)),
    cache_read_input_tokens: Math.max(n(stream.cache_read_input_tokens), n(m.cacheReadInputTokenCount)),
    output_tokens: Math.max(n(stream.output_tokens), n(m.outputTokenCount)),
  };
}

/**
 * config: {
 *   enabled, monthMicros, dayMicros, deeperMonthMicros, visitorDayMicros,
 *   model: { id, price, maxTokens, extra },        // the standard model
 *   deeper: { id, price, maxTokens, extra } | null, // optional, under its own sub-cap
 *   limits, local, statusCacheMs, retentionCheckMs, timeoutMs
 * }
 * deps: {
 *   store, ledger, now,
 *   model: { stream({ modelId, body, signal }) -> AsyncIterable<event> },
 *   retention: () => Promise<string>   // Bedrock's account data retention mode in this Region
 * }
 */
export function createAssistant(config, deps) {
  const now = deps.now ?? (() => new Date());
  const numbers = methodNumbers();
  const local = localLimiter(config.local, now().getTime());
  const caches = {
    salt: null,
    status: null, // { value, until }
    retention: null, // { ok, until }
    caps: new Map(), // 'month' | 'day' | 'deeper' -> Date
    visitorCaps: new Map(), // visitor hash -> Date
  };
  const tallies = new Map(); // event -> { count, since }

  /** Log an event that can come in floods at most once a minute per instance, with a count. */
  function tally(event, fields = {}) {
    const t = now().getTime();
    const s = tallies.get(event) ?? { count: 0, since: t, logged: 0 };
    s.count += 1;
    tallies.set(event, s);
    if (t - s.logged >= 60_000) {
      log('warn', event, { ...fields, count: s.count, sinceMs: t - s.since });
      tallies.set(event, { count: 0, since: t, logged: t });
    }
  }

  /** Whether Bedrock data retention is "none" here; checked now and then, never assumed. */
  async function retentionOk() {
    const t = now().getTime();
    if (caches.retention && t < caches.retention.until) return caches.retention.ok;
    let ok = false;
    try {
      ok = (await deps.retention?.()) === 'none';
      if (!ok) log('warn', 'retention_not_none');
    } catch (e) {
      log('warn', 'retention_check_error', { error: e?.name });
    }
    caches.retention = { ok, until: t + (ok ? config.retentionCheckMs ?? 900_000 : 60_000) };
    return ok;
  }

  function knownCap(visitor, deeper, at) {
    for (const scope of deeper ? ['month', 'day', 'deeper'] : ['month', 'day']) {
      const until = caches.caps.get(scope);
      if (until && at < until) return { scope, until };
    }
    const v = visitor && caches.visitorCaps.get(visitor);
    if (v && at < v) return { scope: 'visitor', until: v };
    return null;
  }

  function rememberCap(e, visitor) {
    if (e.scope === 'visitor') {
      caches.visitorCaps.set(visitor, e.until);
      if (caches.visitorCaps.size > 5000) caches.visitorCaps.delete(caches.visitorCaps.keys().next().value);
    } else {
      caches.caps.set(e.scope, e.until);
    }
    caches.status = null;
  }

  async function status() {
    if (!config.enabled) return { v: 1, state: 'off', message: WORDS.off };
    const t = now();
    if (caches.status && t.getTime() < caches.status.until) return caches.status.value;
    let value;
    if (!(await retentionOk())) {
      value = { v: 1, state: 'paused', scope: 'unavailable', message: WORDS.unavailable };
    } else {
      try {
        const probe = worstCaseMicros(config.model.price, Buffer.byteLength(SYSTEM_PROMPT) + 2000, config.model.maxTokens);
        const s = await deps.ledger.status(t, probe);
        const usedShare = Math.round(s.usedShare * 10) / 10;
        if (s.monthReached) value = { v: 1, state: 'paused', scope: 'month', resumes: s.monthResumes.toISOString(), usedShare, message: WORDS.month };
        else if (s.dayReached) value = { v: 1, state: 'paused', scope: 'day', resumes: s.dayResumes.toISOString(), usedShare, message: WORDS.day };
        else value = { v: 1, state: 'available', usedShare, deeper: !!config.deeper, limits: { questionChars: LIMITS.questionChars, historyTurns: LIMITS.historyTurns, bodyBytes: LIMITS.bodyBytes } };
      } catch (e) {
        log('warn', 'status_ledger_error', { error: e?.name });
        value = { v: 1, state: 'paused', scope: 'ledger', message: WORDS.ledger };
      }
    }
    caches.status = { value, until: t.getTime() + (config.statusCacheMs ?? 30_000) };
    return value;
  }

  /**
   * Handle one request. `req`: { method, path, headers, body (string, already decoded) }.
   * `res`: { start(status, headers), write(text), end() }.
   */
  async function handle(req, res) {
    const send = (status, payload) => { res.start(status, JSON_HEADERS); res.write(JSON.stringify(payload)); res.end(); };
    const rateWords = { everyone: WORDS.busy, hour: WORDS.rateHour, day: WORDS.rateDay };
    const path = (req.path ?? '').replace(/\/+$/, '');
    const isStatus = path.endsWith('/status');
    if (!isStatus && !path.endsWith('/ask')) return send(400, { error: 'path' });
    if (req.method !== (isStatus ? 'GET' : 'POST')) return send(405, { error: 'method' });

    // The viewer's address, from CloudFront only. Without it (a misconfigured behaviour), all
    // such requests share one conservative bucket, and the metric filter counts the log line.
    const address = viewerAddress(req.headers);
    if (address === NO_ADDRESS) tally('no_viewer_address');

    // This instance's buckets: no database call for a refused request.
    const refusal = local.check(isStatus ? 'status' : 'ask', address, now().getTime());
    if (refusal) {
      tally('local_refusal', { scope: refusal.scope });
      return send(429, { error: 'rate', scope: refusal.scope, resumes: refusal.until.toISOString(), message: rateWords[refusal.scope] });
    }
    if (isStatus) return send(200, await status());

    const raw = req.body ?? '';
    if (Buffer.byteLength(raw) > LIMITS.bodyBytes) return send(413, { error: 'too_large', message: WORDS.tooLarge });
    let body;
    try {
      body = validateAsk(JSON.parse(raw));
    } catch (e) {
      const why = e instanceof Invalid ? e.message : 'not JSON';
      tally('invalid', { why: e instanceof Invalid ? e.path : 'json' });
      return send(400, { error: 'invalid', message: WORDS.invalid, detail: why });
    }
    if (!config.enabled) return send(503, { error: 'off', message: WORDS.off });
    const deeper = body.deeper === true;
    const model = deeper ? config.deeper : config.model;
    if (!model) return send(400, { error: 'deeper_off', message: WORDS.deeperOff });
    if (!(await retentionOk())) return send(503, { error: 'unavailable', message: WORDS.unavailable });

    const at = now();
    let visitor;
    try {
      caches.salt ??= await loadSalt(deps.store);
      visitor = visitorHash(caches.salt, address);
    } catch (e) {
      log('warn', 'limits_error', { error: e?.name });
      return send(503, { error: 'ledger', message: WORDS.ledger });
    }
    const known = knownCap(visitor, deeper, at);
    if (known) {
      tally('cap_known', { scope: known.scope });
      return send(503, { error: 'cap', scope: known.scope, resumes: known.until.toISOString(), message: WORDS[known.scope] });
    }
    try {
      await countQuestion(deps.store, { visitor, session: body.session, now: at, limits: config.limits });
    } catch (e) {
      if (e instanceof RateLimited) return send(429, { error: 'rate', scope: e.scope, resumes: e.until.toISOString(), message: rateWords[e.scope] ?? WORDS.busy });
      log('warn', 'limits_error', { error: e?.name });
      return send(503, { error: 'ledger', message: WORDS.ledger });
    }

    const requestBody = buildBody({ messages: buildMessages(body), maxTokens: model.maxTokens, extra: model.extra });
    const bytes = Buffer.byteLength(JSON.stringify(requestBody));
    const worst = worstCaseMicros(model.price, bytes, model.maxTokens);
    let reservation;
    try {
      reservation = await deps.ledger.reserve(worst, { now: at, deeper, visitor });
    } catch (e) {
      if (e instanceof CapReached) {
        log('warn', e.scope === 'visitor' ? 'visitor_limit' : 'cap_reached', { scope: e.scope });
        rememberCap(e, visitor);
        return send(503, { error: 'cap', scope: e.scope, resumes: e.until.toISOString(), message: WORDS[e.scope] });
      }
      log('warn', 'ledger_error', { error: e?.name });
      return send(503, { error: 'ledger', message: WORDS.ledger });
    }

    // From here the call is paid for: whatever happens, settle.
    const usage = {};
    let metrics = null;
    let finalOutput = false;
    let started = false;
    let complete = false;
    let stop = null;
    let refusedBeforeStart = false;
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), config.timeoutMs ?? 45_000);
    res.start(200, STREAM_HEADERS);
    res.write(JSON.stringify({ t: 'meta', methodNumbers: numbers, deeper }) + '\n');
    try {
      for await (const ev of deps.model.stream({ modelId: model.id, body: requestBody, signal: abort.signal })) {
        if (ev.type === 'message_start') {
          started = true;
          Object.assign(usage, ev.message?.usage ?? {});
        } else if (ev.type === 'content_block_delta' && ev.delta?.type === 'text_delta' && typeof ev.delta.text === 'string') {
          res.write(JSON.stringify({ t: 'text', v: ev.delta.text }) + '\n');
        } else if (ev.type === 'message_delta') {
          if (ev.usage) {
            Object.assign(usage, ev.usage);
            if (Number.isFinite(ev.usage.output_tokens)) finalOutput = true;
          }
          if (ev.delta?.stop_reason) stop = ev.delta.stop_reason;
        } else if (ev.type === 'message_stop') {
          complete = true;
          metrics = ev['amazon-bedrock-invocationMetrics'] ?? null;
          if (Number.isFinite(metrics?.outputTokenCount)) finalOutput = true;
        }
      }
      res.write(JSON.stringify({ t: 'done', stop: stop ?? (complete ? 'end_turn' : 'incomplete') }) + '\n');
    } catch (e) {
      log('warn', 'model_error', { error: e?.name, started });
      refusedBeforeStart = !started && REFUSED_UNBILLED.has(e?.name);
      res.write(JSON.stringify({ t: 'error', error: 'model', message: WORDS.model }) + '\n');
    } finally {
      clearTimeout(timer);
      res.end();
    }

    // Settle. A call Bedrock refused outright cost nothing. A complete call with a final output
    // count costs the larger of what the stream and the invocation metrics report, field by
    // field. Anything else (broke off, timed out, no final count) keeps its whole reservation:
    // the ledger may overstate, never understate.
    let actual = reservation.amount;
    if (refusedBeforeStart) actual = 0;
    else if (complete && finalOutput) actual = actualMicros(model.price, mergeUsage(usage, metrics));
    try {
      await deps.ledger.settle(reservation, actual);
    } catch (e) {
      log('warn', 'settle_error', { error: e?.name });
    }
    log('info', 'answered', { model: model.price, reserved: reservation.amount, actual, stop });
  }

  /** Read the retention mode as the instance starts (cold start), so the first answer waits on nothing new. */
  async function warm() { await retentionOk(); }

  return { handle, status, warm };
}
