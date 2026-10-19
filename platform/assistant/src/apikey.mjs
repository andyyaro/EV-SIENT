// An API key held in memory for a model provider (the Claude API or OpenAI). handler.mjs reads
// it at cold start and every 15 minutes (SSM Parameter Store or Secrets Manager). The key is
// never logged, never put in an error message and never returned to a viewer.

/** An error naming only what failed: never the key, never the store's message. */
function failure(name) {
  return Object.assign(new Error(`API key: ${name}`), { name });
}

/**
 * The API key, read through `read` (handler.mjs: SSM GetParameter, or Secrets Manager
 * GetSecretValue) and kept in memory. refresh() reads it again and says whether there is one;
 * any failure forgets the key, so the assistant refuses (fails closed) until a later refresh
 * succeeds. A read that returns nothing, or something that is not a key, counts as no key.
 */
export function keySource(read) {
  let key = null;
  return {
    get: () => key,
    async refresh() {
      try {
        const v = String((await read()) ?? '').trim();
        key = /^[\x21-\x7e]{20,400}$/.test(v) ? v : null;
      } catch (e) {
        key = null;
        throw failure(e?.name && /^[A-Za-z]{1,60}$/.test(e.name) ? e.name : 'KeyReadError');
      }
      return key !== null;
    },
  };
}
