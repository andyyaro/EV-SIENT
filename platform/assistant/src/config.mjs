// The proxy's settings, read from the environment the CloudFormation template sets
// (platform/assistant/template.yaml). Kept apart from handler.mjs so tests can read it.
// Anything malformed throws, and the handler then refuses every question (fails closed).

import { USD } from './ledger.mjs';
import { DEFAULT_LIMITS, DEFAULT_LOCAL } from './limits.mjs';
import { priceForModel, PROVIDERS } from './pricing.mjs';

function dollars(env, name, fallback) {
  const v = Number(env[name] ?? fallback);
  if (!Number.isFinite(v) || v < 0) throw new Error(`${name} must be a number of dollars`);
  return Math.round(v * USD);
}

function whole(env, name, fallback, min, max) {
  const v = Number(env[name] ?? fallback);
  if (!Number.isInteger(v) || v < min || v > max) throw new Error(`${name} must be a whole number from ${min} to ${max}`);
  return v;
}

/**
 * The price row comes from the provider and the model ID. MODEL_PRICE may still be set, as the
 * model ("gpt-5.4-mini", "haiku") or the full key ("openai:gpt-5.4-mini"), but only to the
 * same row: a mismatch means someone meant a different model or provider, so the proxy refuses
 * to start.
 */
function price(env, name, modelId, provider) {
  const derived = priceForModel(modelId, provider);
  const given = env[name];
  if (given && given !== derived && `${provider}:${given}` !== derived) {
    throw new Error(`${name} is ${given} but ${modelId} on ${provider} is priced as ${derived}`);
  }
  return derived;
}

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

/**
 * Extra request fields, from an allow-list only. Claude (Claude API or Bedrock): switching
 * thinking off or to adaptive, the effort level, and the temperature. OpenAI: the reasoning
 * effort and the text verbosity. Anything else (tools, metadata, cache settings, a second
 * system prompt, storing the response, the output limit) is refused, so configuration cannot
 * change what a call may cost or see. The output limit is MAX_TOKENS, because the reservation
 * is worked out from it.
 */
function extra(env, name, fallback, provider) {
  const raw = env[name];
  const v = raw ? JSON.parse(raw) : fallback;
  if (!isObject(v)) throw new Error(`${name} must be a JSON object`);
  if (provider === 'openai') return openaiExtra(v, name);
  for (const [k, x] of Object.entries(v)) {
    if (k === 'thinking') {
      if (!isObject(x) || Object.keys(x).length !== 1 || !['disabled', 'adaptive'].includes(x.type)) {
        throw new Error(`${name}.thinking must be {"type":"disabled"} or {"type":"adaptive"}`);
      }
    } else if (k === 'output_config') {
      if (!isObject(x) || Object.keys(x).length !== 1 || !['low', 'medium', 'high'].includes(x.effort)) {
        throw new Error(`${name}.output_config must be {"effort":"low"|"medium"|"high"}`);
      }
    } else if (k === 'temperature') {
      if (typeof x !== 'number' || !(x >= 0 && x <= 1)) throw new Error(`${name}.temperature must be from 0 to 1`);
    } else {
      throw new Error(`${name} may not set ${k}`);
    }
  }
  return v;
}

function openaiExtra(v, name) {
  for (const [k, x] of Object.entries(v)) {
    if (k === 'reasoning') {
      if (!isObject(x) || Object.keys(x).length !== 1 || !['none', 'minimal', 'low', 'medium', 'high'].includes(x.effort)) {
        throw new Error(`${name}.reasoning must be {"effort":"none"|"minimal"|"low"|"medium"|"high"}`);
      }
    } else if (k === 'text') {
      if (!isObject(x) || Object.keys(x).length !== 1 || !['low', 'medium', 'high'].includes(x.verbosity)) {
        throw new Error(`${name}.text must be {"verbosity":"low"|"medium"|"high"}`);
      }
    } else if (k === 'max_output_tokens') {
      throw new Error(`${name} may not set max_output_tokens: set MAX_TOKENS, which the reservation is worked out from`);
    } else {
      throw new Error(`${name} may not set ${k}`);
    }
  }
  return v;
}

// Model IDs as each provider names them: OpenAI's, Bedrock's cross-Region inference profiles,
// and the Claude API's own IDs.
const MODEL_ID = {
  openai: /^gpt-[a-z0-9.-]+$/,
  bedrock: /^(global|us|eu|apac|jp|au)\.anthropic\.[a-z0-9-]+(:\d+)?$/,
  anthropic: /^claude-[a-z0-9-]+$/,
};
const DEFAULT_MODEL = { openai: 'gpt-5.4-mini', bedrock: 'global.anthropic.claude-haiku-5-5', anthropic: 'claude-haiku-5-5' };
export const DEFAULT_KEY_PARAMETER = '/evsient/assistant/anthropic-api-key';
// The earlier site assistant's secret (infra/assistant), a JSON object holding OPENAI_API_KEY,
// in us-east-1. The proxy reads it across Regions by name.
export const DEFAULT_OPENAI_SECRET = 'future-city-assistant-secrets';
export const DEFAULT_OPENAI_SECRET_REGION = 'us-east-1';

function modelId(v, name, provider) {
  if (!MODEL_ID[provider].test(v)) throw new Error(`${name} must be a model ID for ${provider}, such as ${DEFAULT_MODEL[provider]}`);
  return v;
}

/** Which service answers: OpenAI (the default), Anthropic's Claude API or Amazon Bedrock. */
function providerOf(env) {
  const p = env.PROVIDER || 'openai';
  if (!PROVIDERS.includes(p)) throw new Error(`PROVIDER must be one of ${PROVIDERS.join(', ')}`);
  return p;
}

export function configFromEnv(env = process.env) {
  const provider = providerOf(env);
  const deeperId = env.DEEPER_MODEL_ID ?? '';
  const standardId = modelId(env.MODEL_ID || DEFAULT_MODEL[provider], 'MODEL_ID', provider);
  const keyParameter = env.ANTHROPIC_KEY_PARAMETER || DEFAULT_KEY_PARAMETER;
  if (!/^\/[A-Za-z0-9/_.-]{1,500}$/.test(keyParameter)) throw new Error('ANTHROPIC_KEY_PARAMETER must be a parameter name starting with /');
  const secretId = env.OPENAI_SECRET_ID || DEFAULT_OPENAI_SECRET;
  if (!/^[A-Za-z0-9/_+=.@-]{1,512}$/.test(secretId)) throw new Error('OPENAI_SECRET_ID must be a secret name');
  const secretRegion = env.OPENAI_SECRET_REGION || DEFAULT_OPENAI_SECRET_REGION;
  if (!/^[a-z]{2}(-[a-z]+)+-\d$/.test(secretRegion)) throw new Error('OPENAI_SECRET_REGION must be an AWS Region');
  return {
    enabled: env.ASSISTANT_ENABLED === 'true',
    provider,
    // The SSM parameter holding the Claude API key (anthropic only). Its value is never logged.
    keyParameter: provider === 'anthropic' ? keyParameter : null,
    // The Secrets Manager secret holding the OpenAI key (openai only), by name and Region.
    openaiSecret: provider === 'openai' ? { id: secretId, region: secretRegion } : null,
    monthMicros: dollars(env, 'MONTHLY_CAP_USD', 5),
    dayMicros: dollars(env, 'DAILY_CAP_USD', 0.35),
    deeperMonthMicros: dollars(env, 'DEEPER_MONTHLY_CAP_USD', 1),
    // One visitor's (address prefix's) share of a day, so one person cannot use the day's cap.
    visitorDayMicros: dollars(env, 'ADDRESS_DAILY_CAP_USD', 0.05),
    model: {
      id: standardId,
      price: price(env, 'MODEL_PRICE', standardId, provider),
      maxTokens: whole(env, 'MAX_TOKENS', 1200, 64, 4000),
      // Haiku 5.5 accepts thinking switched off at effort high or below, and its default effort
      // is medium. output_config (effort) is left out by default; add it through
      // MODEL_EXTRA_JSON once a test call shows it works. OpenAI: nothing extra by default, as
      // the earlier assistant sends.
      extra: extra(env, 'MODEL_EXTRA_JSON', provider === 'openai' ? {} : { thinking: { type: 'disabled' } }, provider),
    },
    deeper: deeperId ? {
      id: modelId(deeperId, 'DEEPER_MODEL_ID', provider),
      price: price(env, 'DEEPER_MODEL_PRICE', deeperId, provider),
      maxTokens: whole(env, 'DEEPER_MAX_TOKENS', 2000, 64, 8000),
      // Sonnet 5.5 refuses thinking switched off, so nothing is set by default.
      extra: extra(env, 'DEEPER_EXTRA_JSON', {}, provider),
    } : null,
    limits: {
      perAddressHour: whole(env, 'LIMIT_PER_ADDRESS_HOUR', DEFAULT_LIMITS.perAddressHour, 1, 10_000),
      perAddressDay: whole(env, 'LIMIT_PER_ADDRESS_DAY', DEFAULT_LIMITS.perAddressDay, 1, 100_000),
      perSessionDay: whole(env, 'LIMIT_PER_SESSION_DAY', DEFAULT_LIMITS.perSessionDay, 1, 100_000),
      globalMinute: whole(env, 'LIMIT_GLOBAL_MINUTE', DEFAULT_LIMITS.globalMinute, 1, 10_000),
    },
    local: DEFAULT_LOCAL,
    // How long one instance reuses a status answer, and a passed provider check (Bedrock's data
    // retention mode, or the API key read from Secrets Manager or SSM).
    statusCacheMs: whole(env, 'STATUS_CACHE_MS', 30_000, 0, 300_000),
    readyCheckMs: whole(env, 'READY_CHECK_MS', 15 * 60_000, 60_000, 24 * 3600_000),
    timeoutMs: whole(env, 'MODEL_TIMEOUT_MS', 45_000, 1000, 55_000),
  };
}
