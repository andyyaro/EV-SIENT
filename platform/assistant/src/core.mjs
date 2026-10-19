// The assistant proxy's request handling, with no AWS in it: the store (DynamoDB or memory)
// and the model (Bedrock or a test double) are passed in. handler.mjs wires the real ones.
//
// Routes (CloudFront sends /api/assistant/* here; the path is matched on its end so a prefix
// change in CloudFront does not matter):
//   GET  .../status   whether the assistant can answer now, and if not, until when
//   POST .../ask      one question; the answer streams back as NDJSON lines
//
// Status codes avoid 403 and 404, because the app's distribution turns those into its 404 page.
//
// Every refusal happens before the model is called: size, shape (validate.mjs), switched off,
// rate limits (limits.mjs), and the spend ledger (ledger.mjs). Any error in the limits or the
// ledger refuses the call (fail closed). Nothing here logs or stores the question, the answer
// or the shared results.

import { Invalid, LIMITS, validateAsk } from './validate.mjs';
import { CapReached } from './ledger.mjs';
import { countQuestion, loadSalt, RateLimited, viewerAddress, visitorHash } from './limits.mjs';
import { actualMicros, worstCaseMicros } from './pricing.mjs';
import { buildBody, buildMessages, methodNumbers, SYSTEM_PROMPT } from './prompt.mjs';

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
const STREAM_HEADERS = { 'content-type': 'application/x-ndjson; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' };

/** The plain words the panel shows for each refusal. */
const WORDS = {
  off: 'The assistant is switched off. Everything else in the planner keeps working.',
  month: "The assistant has reached this month's limit. Everything else in the planner keeps working.",
  day: "The assistant has reached today's limit. Everything else in the planner keeps working.",
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

/**
 * config: {
 *   enabled, monthMicros, dayMicros, deeperMonthMicros,
 *   model: { id, price, maxTokens, extra },        // the standard model
 *   deeper: { id, price, maxTokens, extra } | null, // optional, under its own sub-cap
 *   limits, timeoutMs
 * }
 * deps: { store, ledger, model: { stream({ modelId, body, signal }) -> AsyncIterable<event> }, now }
 */
export function createAssistant(config, deps) {
  const now = deps.now ?? (() => new Date());
  const numbers = methodNumbers();

  async function status() {
    if (!config.enabled) return { v: 1, state: 'off', message: WORDS.off };
    try {
      const probe = worstCaseMicros(config.model.price, Buffer.byteLength(SYSTEM_PROMPT) + 2000, config.model.maxTokens);
      const s = await deps.ledger.status(now(), probe);
      const usedShare = Math.round(s.usedShare * 10) / 10;
      if (s.monthReached) return { v: 1, state: 'paused', scope: 'month', resumes: s.monthResumes.toISOString(), usedShare, message: WORDS.month };
      if (s.dayReached) return { v: 1, state: 'paused', scope: 'day', resumes: s.dayResumes.toISOString(), usedShare, message: WORDS.day };
      return { v: 1, state: 'available', usedShare, deeper: !!config.deeper, limits: { questionChars: LIMITS.questionChars, historyTurns: LIMITS.historyTurns } };
    } catch (e) {
      log('warn', 'status_ledger_error', { error: e?.name });
      return { v: 1, state: 'paused', scope: 'ledger', message: WORDS.ledger };
    }
  }

  /**
   * Handle one request. `req`: { method, path, headers, body (string, already decoded) }.
   * `res`: { start(status, headers), write(text), end() }.
   */
  async function handle(req, res) {
    const send = (status, payload) => { res.start(status, JSON_HEADERS); res.write(JSON.stringify(payload)); res.end(); };
    const path = (req.path ?? '').replace(/\/+$/, '');
    if (path.endsWith('/status')) {
      if (req.method !== 'GET') return send(405, { error: 'method' });
      return send(200, await status());
    }
    if (!path.endsWith('/ask')) return send(400, { error: 'path' });
    if (req.method !== 'POST') return send(405, { error: 'method' });

    const raw = req.body ?? '';
    if (Buffer.byteLength(raw) > LIMITS.bodyBytes) return send(413, { error: 'too_large', message: WORDS.tooLarge });
    let body;
    try {
      body = validateAsk(JSON.parse(raw));
    } catch (e) {
      const why = e instanceof Invalid ? e.message : 'not JSON';
      log('warn', 'invalid', { why: e instanceof Invalid ? e.path : 'json' });
      return send(400, { error: 'invalid', message: WORDS.invalid, detail: why });
    }
    if (!config.enabled) return send(503, { error: 'off', message: WORDS.off });
    const deeper = body.deeper === true;
    const model = deeper ? config.deeper : config.model;
    if (!model) return send(400, { error: 'deeper_off', message: WORDS.deeperOff });

    const at = now();
    try {
      const salt = await loadSalt(deps.store);
      await countQuestion(deps.store, { visitor: visitorHash(salt, viewerAddress(req.headers)), session: body.session, now: at, limits: config.limits });
    } catch (e) {
      if (e instanceof RateLimited) return send(429, { error: 'rate', scope: e.scope, resumes: e.until.toISOString(), message: { everyone: WORDS.busy, hour: WORDS.rateHour, day: WORDS.rateDay }[e.scope] ?? WORDS.busy });
      log('warn', 'limits_error', { error: e?.name });
      return send(503, { error: 'ledger', message: WORDS.ledger });
    }

    const requestBody = buildBody({ messages: buildMessages(body), maxTokens: model.maxTokens, extra: model.extra });
    const bytes = Buffer.byteLength(JSON.stringify(requestBody));
    const worst = worstCaseMicros(model.price, bytes, model.maxTokens);
    let reservation;
    try {
      reservation = await deps.ledger.reserve(worst, { now: at, deeper });
    } catch (e) {
      if (e instanceof CapReached) {
        log('warn', 'cap_reached', { scope: e.scope });
        return send(503, { error: 'cap', scope: e.scope, resumes: e.until.toISOString(), message: WORDS[e.scope] });
      }
      log('warn', 'ledger_error', { error: e?.name });
      return send(503, { error: 'ledger', message: WORDS.ledger });
    }

    // From here the call is paid for: whatever happens, settle.
    const usage = {};
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
          if (ev.usage) Object.assign(usage, ev.usage);
          if (ev.delta?.stop_reason) stop = ev.delta.stop_reason;
        } else if (ev.type === 'message_stop') {
          complete = true;
          const m = ev['amazon-bedrock-invocationMetrics'];
          if (m && usage.input_tokens === undefined) {
            usage.input_tokens = m.inputTokenCount;
            usage.output_tokens = m.outputTokenCount;
          }
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

    // Settle. A call Bedrock refused outright cost nothing; one that broke off, timed out or
    // failed in any other way keeps its whole reservation (the ledger may overstate, never
    // understate).
    let actual = reservation.amount;
    if (refusedBeforeStart) actual = 0;
    else if (complete && usage.output_tokens !== undefined) actual = actualMicros(model.price, usage);
    try {
      await deps.ledger.settle(reservation, actual);
    } catch (e) {
      log('warn', 'settle_error', { error: e?.name });
    }
    log('info', 'answered', { model: model.price, reserved: reservation.amount, actual, stop });
  }

  return { handle, status };
}
