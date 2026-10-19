// Bedrock's account data retention mode in this Region, read when an instance starts and now and
// then after (core.mjs). The assistant answers only while it reads "none".
//
// The call is a signed GET of https://bedrock.<region>.amazonaws.com/data-retention (the API
// behind `aws bedrock get-account-data-retention`). It is signed here with Signature Version 4
// using the function's own credentials, because the AWS SDK that ships with the Lambda runtime
// may predate this API. The role allows bedrock:GetAccountDataRetention only.

import { createHash, createHmac } from 'node:crypto';

const hex = (data) => createHash('sha256').update(data).digest('hex');
const hmac = (key, data) => createHmac('sha256', key).update(data).digest();

/**
 * Signature Version 4 headers for a request with an empty body.
 * creds: { accessKeyId, secretAccessKey, sessionToken? }
 */
export function signV4({ method, host, path, query = '', region, service, creds, date = new Date() }) {
  const amzDate = date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const day = amzDate.slice(0, 8);
  const headers = { host, 'x-amz-date': amzDate };
  if (creds.sessionToken) headers['x-amz-security-token'] = creds.sessionToken;
  const names = Object.keys(headers).sort();
  const canonical = [
    method, path, query,
    names.map((n) => `${n}:${String(headers[n]).trim()}\n`).join(''),
    names.join(';'),
    hex(''),
  ].join('\n');
  const scope = `${day}/${region}/${service}/aws4_request`;
  const toSign = ['AWS4-HMAC-SHA256', amzDate, scope, hex(canonical)].join('\n');
  const key = hmac(hmac(hmac(hmac(`AWS4${creds.secretAccessKey}`, day), region), service), 'aws4_request');
  const signature = createHmac('sha256', key).update(toSign).digest('hex');
  return {
    ...headers,
    authorization: `AWS4-HMAC-SHA256 Credential=${creds.accessKeyId}/${scope}, SignedHeaders=${names.join(';')}, Signature=${signature}`,
  };
}

/** The retention mode ("none", "default", ...), or throws. */
export async function readRetentionMode(region, env = process.env, fetchFn = fetch) {
  const creds = { accessKeyId: env.AWS_ACCESS_KEY_ID, secretAccessKey: env.AWS_SECRET_ACCESS_KEY, sessionToken: env.AWS_SESSION_TOKEN };
  if (!region || !creds.accessKeyId || !creds.secretAccessKey) throw new Error('no region or credentials');
  const host = `bedrock.${region}.amazonaws.com`;
  const headers = signV4({ method: 'GET', host, path: '/data-retention', region, service: 'bedrock', creds });
  delete headers.host;
  const r = await fetchFn(`https://${host}/data-retention`, { method: 'GET', headers, signal: AbortSignal.timeout(5000) });
  if (!r.ok) throw Object.assign(new Error(`retention check ${r.status}`), { name: `Http${r.status}` });
  const body = await r.json();
  return String(body.mode ?? '');
}
