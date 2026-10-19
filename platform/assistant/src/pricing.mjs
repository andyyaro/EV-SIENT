// Prices in US dollars per million tokens, keyed by provider and model.
//
// openai: OpenAI's API, standard tier list prices from developers.openai.com/api/docs/pricing
//   (read 19 October 2026): gpt-5.4-mini $0.75 input, $0.075 cached input, $4.50 output.
//   OpenAI has no cache write charge, so cacheWrite is the input price. Regional processing
//   (data residency) endpoints cost 10% more; the proxy calls api.openai.com, not one of them.
//   Verify against OpenAI's current price list before each deploy.
// anthropic: Anthropic's Claude API, list prices from platform.claude.com/docs/en/about-claude/
//   pricing (read 19 October 2026). Cache writes are the 5-minute rate; Sonnet 5.5 cache reads
//   are 0.05 times input ($0.10). Haiku prompts over 100,000 tokens cost five times as much.
// bedrock: Amazon Bedrock's global cross-Region inference profiles. The AWS Price List of
//   12 October 2026 bills them at Anthropic's list rates; the Sonnet cache read is kept at
//   $0.20 as the security review set it (the ledger may overstate, never understate).
//   Geographic and in-Region profiles cost 10% more.
// The proxy never sends a prompt anywhere near 100,000 tokens (LIMITS.bodyBytes is 32 KB).
//
// The ledger works in micro-dollars (whole numbers), so sums never drift. If a price changes,
// change it here and redeploy: the ledger only ever spends from this table.

export const PRICES = Object.freeze({
  'openai:gpt-5.4-mini': { input: 0.75, cacheWrite: 0.75, cacheRead: 0.075, output: 4.50 },
  'anthropic:haiku': { input: 0.10, cacheWrite: 0.125, cacheRead: 0.01, output: 0.50 },
  'anthropic:sonnet': { input: 2.00, cacheWrite: 2.50, cacheRead: 0.10, output: 10.00 },
  'bedrock:haiku': { input: 0.10, cacheWrite: 0.125, cacheRead: 0.01, output: 0.50 },
  'bedrock:sonnet': { input: 2.00, cacheWrite: 2.50, cacheRead: 0.20, output: 10.00 },
});

export const PROVIDERS = ['openai', 'anthropic', 'bedrock'];

/**
 * The price row for a model, from the provider and the model ID, so a model can never be billed
 * at another's rates or another provider's. Only the IDs below are known; anything else is
 * refused (configFromEnv then refuses to start). An ID under the wrong provider (a Bedrock
 * profile ID under anthropic, say) is refused too.
 */
const MODEL_PRICES = {
  openai: [
    [/^gpt-5\.4-mini$/, 'gpt-5.4-mini'],
  ],
  anthropic: [
    [/^claude-haiku-5-5$/, 'haiku'],
    [/^claude-sonnet-5-5$/, 'sonnet'],
  ],
  bedrock: [
    [/^global\.anthropic\.claude-haiku-5-5$/, 'haiku'],
    [/^global\.anthropic\.claude-sonnet-5-5$/, 'sonnet'],
  ],
};

/** The price key ("openai:gpt-5.4-mini", "anthropic:haiku") for a model ID under a provider, or throws. */
export function priceForModel(modelId, provider = 'bedrock') {
  const hit = (MODEL_PRICES[provider] ?? []).find(([re]) => re.test(String(modelId)));
  if (!hit) throw new Error(`no price is known for model ${modelId} on ${provider}`);
  return `${provider}:${hit[1]}`;
}

/** Micro-dollars for `tokens` at `perMillion` dollars per million tokens, rounded up. */
export function micros(tokens, perMillion) {
  return Math.ceil(tokens * perMillion);
}

/**
 * No token count is asked for before a call (Bedrock offers none for these models), so a call
 * is reserved from its size in bytes. English text and JSON run at about 4 bytes a token; a
 * byte-level tokenizer never makes more than one token per byte, so 1 byte a token is the true
 * worst case and the reservation is never short. At the request size limit that is about three
 * US cents of input with gpt-5.4-mini, and under one cent with Haiku 5.5.
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

/** What a call actually cost, from the usage the provider reports. */
export function actualMicros(model, usage) {
  const p = PRICES[model];
  if (!p) throw new Error(`no price for model ${model}`);
  const n = (v) => (Number.isFinite(v) && v > 0 ? v : 0);
  return micros(n(usage.input_tokens), p.input)
    + micros(n(usage.cache_creation_input_tokens), p.cacheWrite)
    + micros(n(usage.cache_read_input_tokens), p.cacheRead)
    + micros(n(usage.output_tokens), p.output);
}
