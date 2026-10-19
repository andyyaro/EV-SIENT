// Lambda entry point: a function URL in RESPONSE_STREAM mode, reached only through CloudFront
// with origin access control (the URL's AuthType is AWS_IAM, so a direct call is refused by
// Lambda before this code runs). Configuration comes from environment variables set by
// platform/assistant/template.yaml.
//
// PROVIDER picks who answers:
//   openai     OpenAI's Responses API (openai.mjs), the default. The API key is the
//              OPENAI_API_KEY field of the Secrets Manager secret the earlier site assistant uses
//              (us-east-1, read across Regions by name), read at cold start and every 15
//              minutes, kept in memory only and never logged. Without it the assistant is
//              unavailable (fails closed).
//   anthropic  Anthropic's Claude API (anthropic.mjs). The API key is a SecureString in SSM
//              Parameter Store, read at cold start and every 15 minutes, kept in memory only and
//              never logged. Without it the assistant is unavailable (fails closed).
//   bedrock    Claude on Amazon Bedrock through a global inference profile. Answers only while
//              Bedrock's data retention in this Region reads "none" (retention.mjs).
//
// `awslambda` is a global the Node.js runtime provides for response streaming.

/* global awslambda */
import { anthropicModel } from './anthropic.mjs';
import { keySource } from './apikey.mjs';
import { createAssistant } from './core.mjs';
import { configFromEnv } from './config.mjs';
import { createLedger } from './ledger.mjs';
import { keyFromSecretString, openaiModel } from './openai.mjs';
import { readRetentionMode, retentionIsNone } from './retention.mjs';
import { dynamoStore } from './store.mjs';

/** Bedrock's streaming Messages call, yielding the Anthropic stream events one by one. */
async function bedrockModel(region) {
  const br = await import('@aws-sdk/client-bedrock-runtime');
  const client = new br.BedrockRuntimeClient({ region, maxAttempts: 1 });
  const decoder = new TextDecoder();
  return {
    async *stream({ modelId, body, signal }) {
      const out = await client.send(new br.InvokeModelWithResponseStreamCommand({
        modelId, contentType: 'application/json', accept: 'application/json', body: JSON.stringify(body),
      }), { abortSignal: signal });
      for await (const part of out.body) {
        if (part.chunk?.bytes) yield JSON.parse(decoder.decode(part.chunk.bytes));
        else {
          const err = Object.values(part).find((v) => v && typeof v === 'object' && v.message);
          if (err) throw Object.assign(new Error('model stream error'), { name: Object.keys(part)[0] });
        }
      }
    },
  };
}

/** The Claude API key from SSM Parameter Store (SecureString, decrypted by SSM). */
async function ssmKeyReader(region, name) {
  const ssm = await import('@aws-sdk/client-ssm');
  const client = new ssm.SSMClient({ region, maxAttempts: 1 });
  return async () => {
    const out = await client.send(new ssm.GetParameterCommand({ Name: name, WithDecryption: true }),
      { abortSignal: AbortSignal.timeout(5000) });
    return out.Parameter?.Value ?? null;
  };
}

/**
 * The OpenAI key from the Secrets Manager secret, in the secret's own Region. Only the
 * OPENAI_API_KEY field is returned; the rest of the secret is dropped at once.
 */
async function secretKeyReader({ id, region }) {
  const sm = await import('@aws-sdk/client-secrets-manager');
  const client = new sm.SecretsManagerClient({ region, maxAttempts: 1 });
  return async () => {
    const out = await client.send(new sm.GetSecretValueCommand({ SecretId: id }),
      { abortSignal: AbortSignal.timeout(5000) });
    return keyFromSecretString(out.SecretString);
  };
}

/** The model and the provider check for the configured provider. */
async function provider(config, region) {
  if (config.provider === 'bedrock') {
    return { model: await bedrockModel(region), ready: retentionIsNone(() => readRetentionMode(region)) };
  }
  if (config.provider === 'openai') {
    const key = keySource(await secretKeyReader(config.openaiSecret));
    return { model: openaiModel({ getKey: key.get }), ready: key.refresh };
  }
  const key = keySource(await ssmKeyReader(region, config.keyParameter));
  return { model: anthropicModel({ getKey: key.get }), ready: key.refresh };
}

let ready = null;
async function assistant() {
  if (!ready) {
    ready = (async () => {
      const config = configFromEnv();
      const region = process.env.AWS_REGION;
      const store = await dynamoStore(process.env.TABLE_NAME, region);
      const ledger = createLedger(store, { monthMicros: config.monthMicros, dayMicros: config.dayMicros, deeperMonthMicros: config.deeperMonthMicros, visitorDayMicros: config.visitorDayMicros });
      const a = createAssistant(config, { store, ledger, ...(await provider(config, region)) });
      await a.warm();
      return a;
    })().catch((e) => { ready = null; throw e; });
  }
  return ready;
}

export const handler = awslambda.streamifyResponse(async (event, responseStream) => {
  let stream = responseStream;
  let begun = false;
  let ended = false;
  const res = {
    start(statusCode, headers) { begun = true; stream = awslambda.HttpResponseStream.from(responseStream, { statusCode, headers }); },
    write(text) { stream.write(text); },
    end() { if (!ended) { ended = true; stream.end(); } },
    // The viewer went away (CloudFront closed the connection) before the answer finished.
    onClose(fn) {
      const once = () => { if (!ended) fn(); };
      responseStream.on?.('close', once);
      responseStream.on?.('error', once);
    },
  };
  try {
    const a = await assistant();
    const raw = event.body ?? '';
    await a.handle({
      method: event.requestContext?.http?.method,
      path: event.rawPath,
      headers: event.headers ?? {},
      body: event.isBase64Encoded ? Buffer.from(raw, 'base64').toString('utf8') : raw,
    }, res);
  } catch (e) {
    // Configuration or start-up failure: refuse, as every other failure does.
    console.warn(JSON.stringify({ level: 'warn', event: 'unhandled_error', error: e?.name }));
    if (begun) { res.end(); return; }
    res.start(503, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
    res.write(JSON.stringify({ error: 'unavailable', message: 'The assistant is not available right now. Everything else in the planner keeps working.' }));
    res.end();
  }
});
