// OpenAI's Responses API, called directly: one streaming POST to /v1/responses with fetch, and
// the server-sent events parsed by sse.mjs, so the function needs no SDK and no new dependency.
// This is the same API, model and key the earlier site assistant (infra/assistant) uses.
//
// The Responses events are translated here into the events core.mjs already reads (the
// Anthropic Messages events Bedrock and the Claude API stream), so the ledger settles every
// provider the same way:
//   the first event                 -> message_start (the call has started)
//   response.output_text.delta      -> content_block_delta (text)
//   response.completed / incomplete -> message_delta with the final usage, then message_stop
//   response.failed, error          -> an error; the caller keeps the whole reservation
// A stream that ends without response.completed or response.incomplete, or whose final usage
// has no output count, gives core.mjs no final count, so it keeps the whole reservation (S2).
//
// No retries: a failed call is reported once and the planner asks again. The request is aborted
// when the proxy's timeout fires or the viewer goes away (the signal core.mjs passes). The API
// key is sent only in the Authorization header and is never logged, never put in an error
// message and never returned.

import { parseSse } from './sse.mjs';

export const RESPONSES_URL = 'https://api.openai.com/v1/responses';

/** An error from the call. `unbilled` is true when the API refused the request outright. */
function failure(name, extra = {}) {
  return Object.assign(new Error(`OpenAI API: ${name}`), { name, ...extra });
}

/** An error code or type from the API, if it is a plain identifier; never free text. */
function code(...values) {
  for (const v of values) {
    const s = String(v ?? '');
    if (/^[A-Za-z_]{1,40}$/.test(s)) return s;
  }
  return '';
}

/**
 * OpenAI's usage in the shape core.mjs settles: input_tokens there counts cached tokens too, so
 * they are split out and priced at the cached rate. output_tokens includes reasoning tokens,
 * which OpenAI bills as output. Without both counts there is no usable final count: null.
 */
export function usageFromOpenAI(u) {
  if (!u || !Number.isFinite(u.input_tokens) || !Number.isFinite(u.output_tokens)) return null;
  const input = Math.max(0, u.input_tokens);
  const c = u.input_tokens_details?.cached_tokens;
  const cached = Number.isFinite(c) ? Math.min(Math.max(0, c), input) : 0;
  return {
    input_tokens: input - cached,
    cache_creation_input_tokens: 0,
    cache_read_input_tokens: cached,
    output_tokens: Math.max(0, u.output_tokens),
  };
}

/** Why an incomplete response stopped, in the words the panel already knows. */
function stopReason(type, response) {
  if (type === 'response.completed') return 'end_turn';
  const reason = response?.incomplete_details?.reason;
  if (reason === 'max_output_tokens') return 'max_tokens';
  if (reason === 'content_filter') return 'refusal';
  return 'incomplete';
}

/**
 * The Responses API as a model for core.mjs: stream({ modelId, body, signal }) yields the
 * translated events. `body` is sent exactly as built (prompt.mjs puts the model, stream: true
 * and store: false in it). getKey() returns the current key or null.
 */
export function openaiModel({ getKey, fetchFn = fetch, url = RESPONSES_URL }) {
  return {
    async *stream({ modelId, body, signal }) {
      const key = getKey();
      if (!key) throw failure('NoApiKey', { unbilled: true });
      if (body.model !== modelId || body.stream !== true || body.store !== false) throw failure('BadRequestBody', { unbilled: true });
      let r;
      try {
        r = await fetchFn(url, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            accept: 'text/event-stream',
            authorization: `Bearer ${key}`,
          },
          body: JSON.stringify(body),
          signal,
        });
      } catch (e) {
        // No response at all (network, timeout, aborted): whether the API started work is not
        // known, so the caller keeps the reservation.
        throw failure(e?.name === 'AbortError' || e?.name === 'TimeoutError' ? 'AbortError' : 'NetworkError');
      }
      if (!r.ok) {
        // Refused before any model work (bad request, bad key, rate limit, no quota): unbilled.
        let name = '';
        try {
          const err = (await r.json())?.error;
          name = code(err?.code, err?.type);
        } catch { /* not JSON */ }
        throw failure(name || `http_${r.status}`, { unbilled: true, status: r.status });
      }
      if (!r.body) throw failure('NoBody');
      let started = false;
      for await (const { data } of parseSse(r.body)) {
        if (data === '[DONE]') break;
        let ev;
        try { ev = JSON.parse(data); } catch { throw failure('BadEvent'); }
        const type = ev?.type;
        if (type === 'error') throw failure(code(ev.code, ev.error?.code, ev.error?.type) || 'error');
        if (type === 'response.failed') throw failure(code(ev.response?.error?.code) || 'response_failed');
        if (!started) {
          started = true;
          yield { type: 'message_start', message: { usage: {} } };
        }
        if ((type === 'response.output_text.delta' || type === 'response.refusal.delta') && typeof ev.delta === 'string') {
          yield { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: ev.delta } };
        } else if (type === 'response.completed' || type === 'response.incomplete') {
          const usage = usageFromOpenAI(ev.response?.usage);
          yield { type: 'message_delta', delta: { stop_reason: stopReason(type, ev.response) }, ...(usage ? { usage } : {}) };
          yield { type: 'message_stop' };
          return;
        }
      }
    },
  };
}

/**
 * The OpenAI key from a Secrets Manager secret string: a JSON object with the key in `field`
 * (OPENAI_API_KEY, as the earlier assistant stores it). Other fields in the secret are ignored
 * and never kept. A secret that is not JSON is an error named only by kind, so no part of it
 * can reach a log.
 */
export function keyFromSecretString(secretString, field = 'OPENAI_API_KEY') {
  if (typeof secretString !== 'string' || !secretString) return null;
  let parsed;
  try { parsed = JSON.parse(secretString); } catch { throw failure('SecretNotJson'); }
  const v = parsed && typeof parsed === 'object' ? parsed[field] : null;
  return typeof v === 'string' ? v : null;
}
