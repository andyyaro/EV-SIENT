// Anthropic's Claude API, called directly: one streaming POST to /v1/messages with fetch, and
// the server-sent events parsed here, so the function needs no SDK and no new dependency.
//
// The events are the same Anthropic Messages events Bedrock streams (message_start,
// content_block_delta, message_delta, message_stop), so core.mjs reads both alike. No retries:
// a failed call is reported once and the planner asks again. The request is aborted when the
// proxy's timeout fires or the viewer goes away (the signal core.mjs passes).
//
// The API key comes from SSM Parameter Store (handler.mjs reads it at cold start and every 15
// minutes through keySource in apikey.mjs). It is sent only in the x-api-key header and is
// never logged, never put in an error message and never returned.

import { parseSse } from './sse.mjs';

export { keySource } from './apikey.mjs';
export { parseSse };

export const MESSAGES_URL = 'https://api.anthropic.com/v1/messages';
export const ANTHROPIC_VERSION = '2023-06-01';

/** An error from the call. `unbilled` is true when the API refused the request outright. */
function failure(name, extra = {}) {
  return Object.assign(new Error(`Claude API: ${name}`), { name, ...extra });
}

/**
 * The Claude API as a model for core.mjs: stream({ modelId, body, signal }) yields the parsed
 * Messages events. `body` is sent exactly as built (prompt.mjs puts the model and stream: true
 * in it). getKey() returns the current key or null.
 */
export function anthropicModel({ getKey, fetchFn = fetch, url = MESSAGES_URL }) {
  return {
    async *stream({ modelId, body, signal }) {
      const key = getKey();
      if (!key) throw failure('NoApiKey', { unbilled: true });
      if (body.model !== modelId || body.stream !== true) throw failure('BadRequestBody', { unbilled: true });
      let r;
      try {
        r = await fetchFn(url, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            accept: 'text/event-stream',
            'anthropic-version': ANTHROPIC_VERSION,
            'x-api-key': key,
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
        // Refused before any model work (bad request, auth, rate limit, overloaded): unbilled.
        let type = '';
        try { type = String((await r.json())?.error?.type ?? ''); } catch { /* not JSON */ }
        throw failure(/^[a-z_]{1,40}$/.test(type) ? type : `http_${r.status}`, { unbilled: true, status: r.status });
      }
      if (!r.body) throw failure('NoBody');
      for await (const { event, data } of parseSse(r.body)) {
        if (event === 'ping') continue;
        let ev;
        try { ev = JSON.parse(data); } catch { throw failure('BadEvent'); }
        if (event === 'error' || ev?.type === 'error') {
          const type = String(ev?.error?.type ?? 'error');
          throw failure(/^[a-z_]{1,40}$/.test(type) ? type : 'error');
        }
        yield ev;
      }
    },
  };
}
