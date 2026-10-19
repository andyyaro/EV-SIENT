// The data retention check (M7): the Signature Version 4 signer against AWS's published test
// vector, and the call itself against a fake fetch. Nothing here reaches AWS.

import test from 'node:test';
import assert from 'node:assert/strict';

import { readRetentionMode, retentionIsNone, signV4 } from '../src/retention.mjs';

// AWS's "get-vanilla" case from the Signature Version 4 test suite.
const VANILLA = {
  method: 'GET', host: 'example.amazonaws.com', path: '/', region: 'us-east-1', service: 'service',
  creds: { accessKeyId: 'AKIDEXAMPLE', secretAccessKey: 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY' },
  date: new Date('2015-08-30T12:36:00Z'),
};

test('signV4 matches the AWS get-vanilla test vector', () => {
  const h = signV4(VANILLA);
  assert.equal(h['x-amz-date'], '20150830T123600Z');
  assert.equal(h.authorization,
    'AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20150830/us-east-1/service/aws4_request, SignedHeaders=host;x-amz-date, '
    + 'Signature=5fa00fa31553b73ebf1942676e86291e8372ff2a2260956d9b8aae1d763fbf31');
});

test('signV4 signs the session token when there is one', () => {
  const h = signV4({ ...VANILLA, creds: { ...VANILLA.creds, sessionToken: 'token' } });
  assert.equal(h['x-amz-security-token'], 'token');
  assert.match(h.authorization, /SignedHeaders=host;x-amz-date;x-amz-security-token,/);
});

const ENV = { AWS_ACCESS_KEY_ID: 'AKIDEXAMPLE', AWS_SECRET_ACCESS_KEY: 'secret', AWS_SESSION_TOKEN: 'token' };

test('readRetentionMode makes one signed GET to the Region\'s Bedrock endpoint', async () => {
  const seen = [];
  const fetchFn = async (url, init) => { seen.push({ url, init }); return { ok: true, status: 200, json: async () => ({ mode: 'none' }) }; };
  assert.equal(await readRetentionMode('us-east-1', ENV, fetchFn), 'none');
  assert.equal(seen.length, 1);
  assert.equal(seen[0].url, 'https://bedrock.us-east-1.amazonaws.com/data-retention');
  assert.equal(seen[0].init.method, 'GET');
  assert.match(seen[0].init.headers.authorization, /Credential=AKIDEXAMPLE\/\d{8}\/us-east-1\/bedrock\/aws4_request/);
  assert.equal(seen[0].init.headers['x-amz-security-token'], 'token');
  assert.equal(seen[0].init.headers.host, undefined, 'fetch sets the host itself');
});

test('readRetentionMode throws on an error response or without credentials', async () => {
  const denied = async () => ({ ok: false, status: 403, json: async () => ({}) });
  await assert.rejects(readRetentionMode('us-east-1', ENV, denied), /403/);
  let called = false;
  const spy = async () => { called = true; return { ok: true, json: async () => ({ mode: 'none' }) }; };
  await assert.rejects(readRetentionMode('us-east-1', {}, spy));
  await assert.rejects(readRetentionMode('', ENV, spy));
  assert.equal(called, false);
  assert.equal(await readRetentionMode('us-east-1', ENV, async () => ({ ok: true, json: async () => ({ mode: 'default' }) })), 'default');
  assert.equal(await readRetentionMode('us-east-1', ENV, async () => ({ ok: true, json: async () => ({}) })), '');
});

test('retentionIsNone: Bedrock is ready only while the mode reads none', async () => {
  assert.equal(await retentionIsNone(async () => 'none')(), true);
  for (const mode of ['default', 'provider_data_share', 'inherit', '', 'NONE']) assert.equal(await retentionIsNone(async () => mode)(), false, mode);
  await assert.rejects(retentionIsNone(async () => { throw new Error('down'); })());
});
