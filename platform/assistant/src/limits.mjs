// Per-visitor and global request limits, counted in the same store as the ledger.
//
// A visitor is the network address CloudFront saw (hashed with a secret salt, never stored as
// it is) and the browser's random session ID. Limits are counted per hour and per day; one
// global per-minute limit stops a flood from many addresses before it reaches the model. The
// counters expire on their own (DynamoDB time to live). Like the ledger, any error refuses.

import { createHmac, randomBytes } from 'node:crypto';
import { ConditionFailed } from './store.mjs';

export const DEFAULT_LIMITS = Object.freeze({
  perAddressHour: 20,
  perAddressDay: 60,
  perSessionDay: 40,
  globalMinute: 30,
});

export class RateLimited extends Error {
  constructor(scope, until) {
    super(`${scope} rate limit reached`);
    this.name = 'RateLimited';
    this.scope = scope;
    this.until = until;
  }
}

/**
 * The viewer's address as CloudFront saw it. CloudFront-Viewer-Address ("ip:port") is added by
 * the origin request policy; otherwise the last X-Forwarded-For entry is the one CloudFront
 * appended (anything before it was sent by the viewer and is not trusted).
 */
export function viewerAddress(headers) {
  const h = Object.fromEntries(Object.entries(headers ?? {}).map(([k, v]) => [k.toLowerCase(), String(v)]));
  const cf = h['cloudfront-viewer-address'];
  if (cf) {
    const i = cf.lastIndexOf(':');
    return i > 0 ? cf.slice(0, i).replace(/^\[|\]$/g, '') : cf;
  }
  const xff = (h['x-forwarded-for'] ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  return xff.length ? xff[xff.length - 1] : 'unknown';
}

/**
 * An address prefix, so one office (or one phone moving between addresses in a block) counts as
 * one visitor: the /24 of IPv4, the /56 of IPv6.
 */
export function addressPrefix(ip) {
  if (/^\d+\.\d+\.\d+\.\d+$/.test(ip)) return ip.split('.').slice(0, 3).join('.') + '.0/24';
  if (ip.includes(':')) {
    const parts = ip.split('::');
    const head = parts[0].split(':').filter(Boolean);
    const tail = parts.length > 1 ? parts[1].split(':').filter(Boolean) : [];
    const full = [...head, ...Array(Math.max(0, 8 - head.length - tail.length)).fill('0'), ...tail];
    const groups = full.slice(0, 4).map((g) => g.padStart(4, '0'));
    groups[3] = groups[3].slice(0, 2) + '00';
    return groups.join(':') + '::/56';
  }
  return 'unknown';
}

/** The salt that keeps hashed addresses from being reversed by trying every address. */
export async function loadSalt(store) {
  const first = await store.read('config#salt');
  if (first?.salt) return first.salt;
  await store.putNew('config#salt', { salt: newSalt() });
  const item = await store.read('config#salt');
  if (item?.salt) return item.salt;
  throw new Error('no salt');
}

export function newSalt() { return randomBytes(32).toString('hex'); }

export function visitorHash(salt, ip) {
  return createHmac('sha256', salt).update(addressPrefix(ip)).digest('hex').slice(0, 32);
}

const pad = (n) => String(n).padStart(2, '0');

/** Count one question against every limit, or throw RateLimited naming the first one passed. */
export async function countQuestion(store, { visitor, session, now = new Date(), limits = DEFAULT_LIMITS }) {
  const y = now.getUTCFullYear();
  const day = `${y}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}`;
  const hour = `${day}${pad(now.getUTCHours())}`;
  const minute = `${hour}${pad(now.getUTCMinutes())}`;
  const t = Math.floor(now.getTime() / 1000);
  const nextHour = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate(), now.getUTCHours() + 1));
  const nextDay = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate() + 1));
  const nextMinute = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes() + 1));
  const ops = [
    { scope: 'everyone', until: nextMinute, op: { key: `rate#all#${minute}`, add: { n: 1 }, atMost: { n: limits.globalMinute - 1 }, ttl: t + 3600 } },
    { scope: 'hour', until: nextHour, op: { key: `rate#addr#${visitor}#${hour}`, add: { n: 1 }, atMost: { n: limits.perAddressHour - 1 }, ttl: t + 2 * 3600 } },
    { scope: 'day', until: nextDay, op: { key: `rate#addr#${visitor}#${day}`, add: { n: 1 }, atMost: { n: limits.perAddressDay - 1 }, ttl: t + 2 * 86400 } },
    { scope: 'day', until: nextDay, op: { key: `rate#session#${session}#${day}`, add: { n: 1 }, atMost: { n: limits.perSessionDay - 1 }, ttl: t + 2 * 86400 } },
  ];
  try {
    await store.write(ops.map((o) => o.op));
  } catch (e) {
    if (e instanceof ConditionFailed) {
      const hit = ops[e.index] ?? ops[0];
      throw new RateLimited(hit.scope, hit.until);
    }
    throw e;
  }
}
