// Lambda entry point: a function URL in RESPONSE_STREAM mode, reached only through CloudFront
// with origin access control (the URL's AuthType is AWS_IAM, so a direct call is refused by
// Lambda before this code runs). Configuration comes from environment variables set by
// platform/assistant/template.yaml; there are no secrets.
//
// `awslambda` is a global the Node.js runtime provides for response streaming.

/* global awslambda */
import { createAssistant } from './core.mjs';
import { configFromEnv } from './config.mjs';
import { createLedger } from './ledger.mjs';
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

let ready = null;
async function assistant() {
  if (!ready) {
    ready = (async () => {
      const config = configFromEnv();
      const region = process.env.AWS_REGION;
      const store = await dynamoStore(process.env.TABLE_NAME, region);
      const ledger = createLedger(store, { monthMicros: config.monthMicros, dayMicros: config.dayMicros, deeperMonthMicros: config.deeperMonthMicros });
      return createAssistant(config, { store, ledger, model: await bedrockModel(region) });
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
