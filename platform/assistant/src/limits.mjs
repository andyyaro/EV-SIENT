// Request limits, in two layers.
//
// 1. In memory, per function instance, before anything touches DynamoDB: a token bucket for
//    everyone and one per viewer address. A flood is refused here for the price of a Lambda
//    invocation of a few milliseconds, with no database write. Each instance keeps its own
//    buckets, so the totals scale with the number of instances (at most the function's
//    concurrency).
// 2. In DynamoDB, shared by all instances: per address per hour and per day, per session per
//    day, and everyone per minute. Each is one conditional update (one write unit), checked in
//    turn and stopping at the first refusal, the visitor's own limits first so one visitor's
//    refused requests do not use up everyone's minute.
//
// A visitor is the network address CloudFront saw, hashed with a secret salt (never stored as
// it is), and the browser's random session ID. Counters expire on their own (DynamoDB time to
// live). Like the ledger, any error refuses.

import { createHmac, randomBytes } from 'node:crypto';
import { ConditionFailed } from './store.mjs';

export const DEFAULT_LIMITS = Object.freeze({
  perAddressHour: 12,
  perAddressDay: 30,
  perSessionDay: 30,
  globalMinute: 20,
});

/** Per instance, in memory: capacity (burst) and refill per minute. */
export const DEFAULT_LOCAL = Object.freeze({
  askGlobal: { capacity: 4, perMinute: 3 },
  askAddress: { capacity: 3, perMinute: 1 },
  statusAddress: { capacity: 10, perMinute: 10 },
  addresses: 5000,
});

/** The shared, conservative bucket for requests that arrive without CloudFront's address. */
export const NO_ADDRESS = 'no-viewer-address';

export class RateLimited extends Error {
  constructor(scope, until) {
    super(`${scope} rate limit reached`);
    this.name = 'RateLimited';
    this.scope = scope; // 'everyone' | 'hour' | 'day'
    this.until = until;
  }
}

/**
 * The viewer's address as CloudFront saw it, from CloudFront-Viewer-Address ("ip:port"), which
 * the origin request policy adds and a viewer cannot set. X-Forwarded-For is not used: its
 * entries can come from the viewer. Without the header, every such request shares one
 * conservative bucket (NO_ADDRESS), and the caller logs it.
 */
export function viewerAddress(headers) {
  const h = Object.fromEntries(Object.entries(headers ?? {}).map(([k, v]) => [k.toLowerCase(), String(v)]));
  const cf = (h['cloudfront-viewer-address'] ?? '').trim();
  if (!cf) return NO_ADDRESS;
  const i = cf.lastIndexOf(':');
  const ip = i > 0 ? cf.slice(0, i).replace(/^\[|\]$/g, '') : cf;
  return /^[0-9a-fA-F:.]{2,45}$/.test(ip) ? ip : NO_ADDRESS;
}

/**
 * An address prefix, so one office (or one phone moving between addresses in a block) counts as
 * one visitor: the /24 of IPv4, the /56 of IPv6.
 */
export function addressPrefix(ip) {
  if (ip === NO_ADDRESS) return NO_ADDRESS;
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
  return NO_ADDRESS;
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

// ---------------------------------------------------------------- in memory

/** A token bucket: `capacity` requests at once, refilled at `perMinute`. */
export class TokenBucket {
  constructor({ capacity, perMinute }, nowMs) {
    this.capacity = capacity;
    this.perMs = perMinute / 60_000;
    this.tokens = capacity;
    this.at = nowMs;
  }

  take(nowMs) {
    this.tokens = Math.min(this.capacity, this.tokens + Math.max(0, nowMs - this.at) * this.perMs);
    this.at = nowMs;
    if (this.tokens < 1) return false;
    this.tokens -= 1;
    return true;
  }

  /** When the next token arrives. */
  nextMs(nowMs) {
    return nowMs + Math.ceil(Math.max(0, 1 - this.tokens) / this.perMs);
  }
}

/**
 * The instance's buckets. `check(kind, address, nowMs)` returns null when allowed, or
 * { scope, until } when refused. Per-address buckets are kept for the most recent
 * `addresses` addresses (least recently used dropped first).
 */
export function localLimiter(local = DEFAULT_LOCAL, startMs = Date.now()) {
  const global = new TokenBucket(local.askGlobal, startMs);
  const maps = { ask: new Map(), status: new Map() };
  const settings = { ask: local.askAddress, status: local.statusAddress };
  function bucketFor(kind, address, nowMs) {
    const map = maps[kind];
    let b = map.get(address);
    if (b) map.delete(address);
    else b = new TokenBucket(settings[kind], nowMs);
    map.set(address, b);
    if (map.size > local.addresses) map.delete(map.keys().next().value);
    return b;
  }
  return {
    check(kind, address, nowMs = Date.now()) {
      const mine = bucketFor(kind, addressPrefix(address), nowMs);
      if (!mine.take(nowMs)) return { scope: 'hour', until: new Date(mine.nextMs(nowMs)) };
      if (kind === 'ask' && !global.take(nowMs)) return { scope: 'everyone', until: new Date(global.nextMs(nowMs)) };
      return null;
    },
    size(kind) { return maps[kind].size; },
  };
}

// ---------------------------------------------------------------- in DynamoDB

const pad = (n) => String(n).padStart(2, '0');

/** Count one question against every shared limit, or throw RateLimited naming the first passed. */
export async function countQuestion(store, { visitor, session, now = new Date(), limits = DEFAULT_LIMITS }) {
  const y = now.getUTCFullYear();
  const day = `${y}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}`;
  const hour = `${day}${pad(now.getUTCHours())}`;
  const minute = `${hour}${pad(now.getUTCMinutes())}`;
  const t = Math.floor(now.getTime() / 1000);
  const nextHour = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate(), now.getUTCHours() + 1));
  const nextDay = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate() + 1));
  const nextMinute = new Date(Date.UTC(y, now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes() + 1));
  const checks = [
    { scope: 'hour', until: nextHour, op: { key: `rate#addr#${visitor}#${hour}`, add: { n: 1 }, atMost: { n: limits.perAddressHour - 1 }, ttl: t + 2 * 3600 } },
    { scope: 'day', until: nextDay, op: { key: `rate#addr#${visitor}#${day}`, add: { n: 1 }, atMost: { n: limits.perAddressDay - 1 }, ttl: t + 2 * 86400 } },
    { scope: 'day', until: nextDay, op: { key: `rate#session#${session}#${day}`, add: { n: 1 }, atMost: { n: limits.perSessionDay - 1 }, ttl: t + 2 * 86400 } },
    { scope: 'everyone', until: nextMinute, op: { key: `rate#all#${minute}`, add: { n: 1 }, atMost: { n: limits.globalMinute - 1 }, ttl: t + 3600 } },
  ];
  for (const c of checks) {
    try {
      await store.update(c.op);
    } catch (e) {
      if (e instanceof ConditionFailed) throw new RateLimited(c.scope, c.until);
      throw e;
    }
  }
}
