// The proxy's settings, read from the environment the CloudFormation template sets
// (platform/assistant/template.yaml). Kept apart from handler.mjs so tests can read it.
// Anything malformed throws, and the handler then refuses every question (fails closed).

import { USD } from './ledger.mjs';
import { DEFAULT_LIMITS } from './limits.mjs';
import { PRICES } from './pricing.mjs';

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

function price(env, name, fallback) {
  const v = env[name] || fallback;
  if (!Object.prototype.hasOwnProperty.call(PRICES, v)) throw new Error(`${name} must be one of ${Object.keys(PRICES).join(', ')}`);
  return v;
}

/** Extra request fields; never allowed to replace the ones the proxy sets itself. */
function extra(env, name, fallback) {
  const raw = env[name];
  const v = raw ? JSON.parse(raw) : fallback;
  if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error(`${name} must be a JSON object`);
  for (const k of ['messages', 'system', 'max_tokens', 'anthropic_version', 'tools', 'tool_choice']) {
    if (k in v) throw new Error(`${name} may not set ${k}`);
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
  return {
    enabled: env.ASSISTANT_ENABLED === 'true',
    monthMicros: dollars(env, 'MONTHLY_CAP_USD', 5),
    dayMicros: dollars(env, 'DAILY_CAP_USD', 0.35),
    deeperMonthMicros: dollars(env, 'DEEPER_MONTHLY_CAP_USD', 1),
    model: {
      id: modelId(env.MODEL_ID || 'global.anthropic.claude-haiku-5-5', 'MODEL_ID'),
      price: price(env, 'MODEL_PRICE', 'haiku'),
      maxTokens: whole(env, 'MAX_TOKENS', 1200, 64, 4000),
      // Haiku 5.5 accepts thinking switched off at its default effort. output_config (effort) is
      // left out by default because Bedrock's acceptance of it is not confirmed; add it here
      // through MODEL_EXTRA_JSON once a test call shows it works.
      extra: extra(env, 'MODEL_EXTRA_JSON', { thinking: { type: 'disabled' } }),
    },
    deeper: deeperId ? {
      id: modelId(deeperId, 'DEEPER_MODEL_ID'),
      price: price(env, 'DEEPER_MODEL_PRICE', 'sonnet'),
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
    timeoutMs: whole(env, 'MODEL_TIMEOUT_MS', 45_000, 1000, 55_000),
  };
}
