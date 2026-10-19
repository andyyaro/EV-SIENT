// Prices in US dollars per million tokens, for Claude 5.5 models through Amazon Bedrock's global
// cross-Region inference profiles. The AWS Price List of 12 October 2026 bills the global profile
// at the same rates as Anthropic's list; geographic and in-Region profiles cost 10% more, and
// Haiku prompts over 100,000 tokens cost five times as much. The proxy never sends a prompt that
// large (LIMITS.bodyBytes keeps every request far below it).
//
// The ledger works in micro-dollars (whole numbers), so sums never drift. If AWS changes a price,
// change it here and redeploy: the ledger only ever spends from this table.

export const PRICES = Object.freeze({
  haiku: { input: 0.10, cacheWrite: 0.125, cacheRead: 0.01, output: 0.50 },
  sonnet: { input: 2.00, cacheWrite: 2.50, cacheRead: 0.10, output: 10.00 },
});

/** Micro-dollars for `tokens` at `perMillion` dollars per million tokens, rounded up. */
export function micros(tokens, perMillion) {
  return Math.ceil(tokens * perMillion);
}

/**
 * Bedrock offers no token counting for these models, so a call is reserved from its size in
 * bytes. English text and JSON run at about 4 bytes a token; a byte-level tokenizer never makes
 * more than one token per byte, so 1 byte a token is the true worst case and the reservation is
 * never short. At the request size limit that is under one US cent of input.
 */
export const BYTES_PER_TOKEN_WORST = 1;

export function estimateTokens(bytes) {
  return Math.ceil(bytes / BYTES_PER_TOKEN_WORST);
}

/**
 * The most one call can cost: every input token priced as a cache write (the dearest input
 * rate), plus every output token the call may produce.
 */
export function worstCaseMicros(model, inputBytes, maxTokens) {
  const p = PRICES[model];
  if (!p) throw new Error(`no price for model ${model}`);
  return micros(estimateTokens(inputBytes), Math.max(p.input, p.cacheWrite)) + micros(maxTokens, p.output);
}

/** What a call actually cost, from the usage Bedrock reports. */
export function actualMicros(model, usage) {
  const p = PRICES[model];
  if (!p) throw new Error(`no price for model ${model}`);
  const n = (v) => (Number.isFinite(v) && v > 0 ? v : 0);
  return micros(n(usage.input_tokens), p.input)
    + micros(n(usage.cache_creation_input_tokens), p.cacheWrite)
    + micros(n(usage.cache_read_input_tokens), p.cacheRead)
    + micros(n(usage.output_tokens), p.output);
}
