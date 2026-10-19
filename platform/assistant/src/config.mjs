// The proxy's settings, read from the environment the CloudFormation template sets
// (platform/assistant/template.yaml). Kept apart from handler.mjs so tests can read it.
// Anything malformed throws, and the handler then refuses every question (fails closed).

import { USD } from './ledger.mjs';
import { DEFAULT_LIMITS, DEFAULT_LOCAL } from './limits.mjs';
import { priceForModel } from './pricing.mjs';

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
 * The price row comes from the model ID. MODEL_PRICE may still be set, but only to the same
 * row: a mismatch means someone meant a different model, so the proxy refuses to start.
 */
function price(env, name, modelId) {
  const derived = priceForModel(modelId);
  if (env[name] && env[name] !== derived) throw new Error(`${name} is ${env[name]} but ${modelId} is priced as ${derived}`);
  return derived;
}

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

/**
 * Extra request fields, from an allow-list only: switching thinking off or to adaptive, the
 * effort level, and the temperature. Anything else (cache_control, tools, metadata, betas, a
 * second system prompt) is refused, so configuration cannot change what a call may cost or see.
 */
function extra(env, name, fallback) {
  const raw = env[name];
  const v = raw ? JSON.parse(raw) : fallback;
  if (!isObject(v)) throw new Error(`${name} must be a JSON object`);
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

const MODEL_ID = /^(global|us|eu|apac|jp|au)\.anthropic\.[a-z0-9-]+(:\d+)?$/;

function modelId(v, name) {
  if (!MODEL_ID.test(v)) throw new Error(`${name} must be a cross-Region inference profile ID such as global.anthropic.claude-haiku-5-5`);
  return v;
}

export function configFromEnv(env = process.env) {
  const deeperId = env.DEEPER_MODEL_ID ?? '';
  const standardId = modelId(env.MODEL_ID || 'global.anthropic.claude-haiku-5-5', 'MODEL_ID');
  return {
    enabled: env.ASSISTANT_ENABLED === 'true',
    monthMicros: dollars(env, 'MONTHLY_CAP_USD', 5),
    dayMicros: dollars(env, 'DAILY_CAP_USD', 0.35),
    deeperMonthMicros: dollars(env, 'DEEPER_MONTHLY_CAP_USD', 1),
    // One visitor's (address prefix's) share of a day, so one person cannot use the day's cap.
    visitorDayMicros: dollars(env, 'ADDRESS_DAILY_CAP_USD', 0.05),
    model: {
      id: standardId,
      price: price(env, 'MODEL_PRICE', standardId),
      maxTokens: whole(env, 'MAX_TOKENS', 1200, 64, 4000),
      // Haiku 5.5 accepts thinking switched off at its default effort. output_config (effort) is
      // left out by default because Bedrock's acceptance of it is not confirmed; add it here
      // through MODEL_EXTRA_JSON once a test call shows it works.
      extra: extra(env, 'MODEL_EXTRA_JSON', { thinking: { type: 'disabled' } }),
    },
    deeper: deeperId ? {
      id: modelId(deeperId, 'DEEPER_MODEL_ID'),
      price: price(env, 'DEEPER_MODEL_PRICE', deeperId),
      maxTokens: whole(env, 'DEEPER_MAX_TOKENS', 2000, 64, 8000),
      // Sonnet 5.5 refuses thinking switched off, so nothing is set by default.
      extra: extra(env, 'DEEPER_EXTRA_JSON', {}),
    } : null,
    limits: {
      perAddressHour: whole(env, 'LIMIT_PER_ADDRESS_HOUR', DEFAULT_LIMITS.perAddressHour, 1, 10_000),
      perAddressDay: whole(env, 'LIMIT_PER_ADDRESS_DAY', DEFAULT_LIMITS.perAddressDay, 1, 100_000),
      perSessionDay: whole(env, 'LIMIT_PER_SESSION_DAY', DEFAULT_LIMITS.perSessionDay, 1, 100_000),
      globalMinute: whole(env, 'LIMIT_GLOBAL_MINUTE', DEFAULT_LIMITS.globalMinute, 1, 10_000),
    },
    local: DEFAULT_LOCAL,
    // How long one instance reuses a status answer, and the data retention check.
    statusCacheMs: whole(env, 'STATUS_CACHE_MS', 30_000, 0, 300_000),
    retentionCheckMs: whole(env, 'RETENTION_CHECK_MS', 15 * 60_000, 60_000, 24 * 3600_000),
    timeoutMs: whole(env, 'MODEL_TIMEOUT_MS', 45_000, 1000, 55_000),
  };
}
