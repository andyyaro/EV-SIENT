// The spend ledger: concurrent reservations never pass a cap, a reached cap refuses, settling
// replaces a reservation with the actual cost, and the DynamoDB translation says the same thing.
import test from 'node:test';
import assert from 'node:assert/strict';
import { CapReached, createLedger, nextDayStart, nextMonthStart, USD } from '../src/ledger.mjs';
import { ConditionFailed, memoryStore, toTransactItems } from '../src/store.mjs';
import { actualMicros, PRICES, worstCaseMicros } from '../src/pricing.mjs';

const NOW = new Date('2026-10-18T12:00:00Z');
const CAPS = { monthMicros: 5 * USD, dayMicros: 0.35 * USD, deeperMonthMicros: 1 * USD };

/** A store whose every call waits a random moment, so many writers interleave. */
const jittery = () => memoryStore({ delay: () => new Promise((r) => setTimeout(r, Math.floor(Math.random() * 3))) });

test('200 concurrent reservations never commit more than the cap', async () => {
  const store = jittery();
  const ledger = createLedger(store, { monthMicros: 1000, dayMicros: 1000, deeperMonthMicros: 1000 });
  const amounts = Array.from({ length: 200 }, (_, i) => 7 + (i % 13));
  const results = await Promise.allSettled(amounts.map((a) => ledger.reserve(a, { now: NOW })));
  const granted = results.filter((r) => r.status === 'fulfilled').map((r) => r.value.amount);
  const refused = results.filter((r) => r.status === 'rejected');
  const committed = store.items.get('ledger#month#2026-10').committed;
  assert.equal(committed, granted.reduce((a, b) => a + b, 0));
  assert.ok(committed <= 1000, `committed ${committed}`);
  assert.ok(committed > 1000 - 20, 'the cap is used nearly in full');
  assert.ok(refused.length > 0);
  for (const r of refused) assert.ok(r.reason instanceof CapReached, String(r.reason));
});

test('concurrent reservations and settlements together stay within the cap', async () => {
  const store = jittery();
  const ledger = createLedger(store, { monthMicros: 5000, dayMicros: 5000, deeperMonthMicros: 5000 });
  let maxSeen = 0;
  await Promise.all(Array.from({ length: 300 }, async (_, i) => {
    try {
      const r = await ledger.reserve(100, { now: NOW });
      maxSeen = Math.max(maxSeen, store.items.get('ledger#month#2026-10').committed);
      await ledger.settle(r, i % 3 === 0 ? 100 : 20 + (i % 50));
    } catch (e) {
      if (!(e instanceof CapReached)) throw e;
    }
  }));
  const m = store.items.get('ledger#month#2026-10');
  assert.ok(maxSeen <= 5000);
  assert.ok(m.committed <= 5000);
  assert.equal(m.committed, m.spent, 'once everything settles, committed equals spent');
});

test('the month cap: reached means refused, with the start of next month', async () => {
  const ledger = createLedger(memoryStore(), { monthMicros: 300, dayMicros: 10_000, deeperMonthMicros: 300 });
  await ledger.reserve(200, { now: NOW });
  await ledger.reserve(100, { now: NOW });
  await assert.rejects(ledger.reserve(1, { now: NOW }), (e) => e instanceof CapReached && e.scope === 'month' && e.until.getTime() === nextMonthStart(NOW).getTime());
  const s = await ledger.status(NOW, 1);
  assert.equal(s.monthReached, true);
  assert.equal(s.usedShare, 1);
  // A new month starts fresh.
  const next = new Date('2026-11-01T00:00:01Z');
  await ledger.reserve(100, { now: next });
  assert.equal((await ledger.status(next, 1)).monthReached, false);
});

test('a call dearer than a whole cap is refused without writing', async () => {
  const store = memoryStore();
  const ledger = createLedger(store, { monthMicros: 100, dayMicros: 50, deeperMonthMicros: 10 });
  await assert.rejects(ledger.reserve(101, { now: NOW }), (e) => e.scope === 'month');
  await assert.rejects(ledger.reserve(51, { now: NOW }), (e) => e.scope === 'day');
  await assert.rejects(ledger.reserve(11, { now: NOW, deeper: true }), (e) => e.scope === 'deeper');
  assert.equal(store.items.size, 0);
});

test('the day cap refuses until tomorrow; the month cap is untouched by it', async () => {
  const ledger = createLedger(memoryStore(), { monthMicros: 10_000, dayMicros: 300, deeperMonthMicros: 300 });
  await ledger.reserve(300, { now: NOW });
  await assert.rejects(ledger.reserve(1, { now: NOW }), (e) => e.scope === 'day' && e.until.getTime() === nextDayStart(NOW).getTime());
  const s = await ledger.status(NOW, 1);
  assert.equal(s.dayReached, true);
  assert.equal(s.monthReached, false);
  await ledger.reserve(300, { now: new Date('2026-10-19T00:00:00Z') });
});

test('the deeper sub-cap refuses deeper answers only', async () => {
  const ledger = createLedger(memoryStore(), { monthMicros: 10_000, dayMicros: 10_000, deeperMonthMicros: 500 });
  await ledger.reserve(400, { now: NOW, deeper: true });
  await assert.rejects(ledger.reserve(200, { now: NOW, deeper: true }), (e) => e.scope === 'deeper');
  await ledger.reserve(200, { now: NOW });
});

test('settle replaces the reservation with the actual cost and counts the call', async () => {
  const store = memoryStore();
  const ledger = createLedger(store, CAPS);
  const r = await ledger.reserve(10_000, { now: NOW });
  await ledger.settle(r, 1_234);
  const m = store.items.get('ledger#month#2026-10');
  const d = store.items.get('ledger#day#2026-10-18');
  assert.deepEqual({ committed: m.committed, spent: m.spent, calls: m.calls }, { committed: 1_234, spent: 1_234, calls: 1 });
  assert.deepEqual({ committed: d.committed, spent: d.spent }, { committed: 1_234, spent: 1_234 });
  // An unsettled reservation stays counted: the ledger overstates, never understates.
  await ledger.reserve(5_000, { now: NOW });
  assert.equal(store.items.get('ledger#month#2026-10').committed, 6_234);
  await assert.rejects(ledger.settle(r, -1));
  await assert.rejects(ledger.settle(r, 1.5));
});

test('any store error reaches the caller, which refuses', async () => {
  const broken = { write: async () => { throw new Error('network'); }, read: async () => { throw new Error('network'); }, putNew: async () => false };
  const ledger = createLedger(broken, CAPS);
  await assert.rejects(ledger.reserve(10, { now: NOW }), /network/);
  await assert.rejects(ledger.status(NOW, 1), /network/);
});

test('caps must be whole micro-dollars', () => {
  assert.throws(() => createLedger(memoryStore(), { monthMicros: 1.5, dayMicros: 1, deeperMonthMicros: 1 }));
  assert.throws(() => createLedger(memoryStore(), { monthMicros: -1, dayMicros: 1, deeperMonthMicros: 1 }));
});

test('the DynamoDB transaction carries the same additions and conditions', () => {
  const items = toTransactItems([
    { key: 'ledger#month#2026-10', add: { committed: 42, deeperCommitted: 42 }, atMost: { committed: 958, deeperCommitted: 100 }, ttl: 123 },
    { key: 'ledger#day#2026-10-18', add: { committed: -5, spent: 7 } },
  ], 'tbl');
  const [a, b] = items.map((i) => i.Update);
  assert.equal(a.TableName, 'tbl');
  assert.deepEqual(a.Key, { pk: { S: 'ledger#month#2026-10' } });
  assert.equal(a.UpdateExpression, 'ADD #a0 :a0, #a1 :a1 SET #ttl = if_not_exists(#ttl, :ttl)');
  assert.equal(a.ConditionExpression, '(attribute_not_exists(#c0) OR #c0 <= :c0) AND (attribute_not_exists(#c1) OR #c1 <= :c1)');
  assert.deepEqual(a.ExpressionAttributeNames, { '#a0': 'committed', '#a1': 'deeperCommitted', '#ttl': 'expiresAt', '#c0': 'committed', '#c1': 'deeperCommitted' });
  assert.deepEqual(a.ExpressionAttributeValues, { ':a0': { N: '42' }, ':a1': { N: '42' }, ':ttl': { N: '123' }, ':c0': { N: '958' }, ':c1': { N: '100' } });
  assert.equal(b.UpdateExpression, 'ADD #a0 :a0, #a1 :a1');
  assert.equal(b.ConditionExpression, undefined);
  assert.deepEqual(b.ExpressionAttributeValues, { ':a0': { N: '-5' }, ':a1': { N: '7' } });
});

test('the memory store is all or nothing', async () => {
  const store = memoryStore();
  await store.write([{ key: 'a', add: { n: 5 } }]);
  await assert.rejects(store.write([{ key: 'b', add: { n: 1 } }, { key: 'a', add: { n: 1 }, atMost: { n: 4 } }]), (e) => e instanceof ConditionFailed && e.index === 1);
  assert.equal(store.items.has('b'), false);
  assert.equal(store.items.get('a').n, 5);
});

test('prices: worst case covers any actual use of the same request', () => {
  for (const model of Object.keys(PRICES)) {
    const bytes = 20_000;
    const max = 1200;
    const worst = worstCaseMicros(model, bytes, max);
    // The dearest real outcome: every byte a token, all written to cache, full output.
    const actual = actualMicros(model, { input_tokens: 0, cache_creation_input_tokens: bytes, cache_read_input_tokens: 0, output_tokens: max });
    assert.ok(worst >= actual, `${model}: ${worst} < ${actual}`);
    const plain = actualMicros(model, { input_tokens: bytes, output_tokens: max });
    assert.ok(worst >= plain);
  }
  // Haiku at the request size limit (32 KB plus the system prompt): well under a cent.
  assert.ok(worstCaseMicros('haiku', 32 * 1024 + 12_000, 1200) < 0.0065 * USD);
  assert.throws(() => worstCaseMicros('nope', 1, 1));
  // Every input field counts at its own price (M2: Sonnet cache reads at $0.20 a million).
  assert.equal(actualMicros('sonnet', { cache_read_input_tokens: 1_000_000 }), 0.20 * USD);
});

test('S4: one visitor has a daily share; reaching it refuses them only, and writes nothing', async () => {
  const store = jittery();
  const ledger = createLedger(store, { ...CAPS, visitorDayMicros: 0.05 * USD });
  const amounts = Array.from({ length: 60 }, () => 1_000);
  const results = await Promise.allSettled(amounts.map((a) => ledger.reserve(a, { now: NOW, visitor: 'v1' })));
  const granted = results.filter((r) => r.status === 'fulfilled').length;
  assert.equal(granted, 50, 'exactly the share, even when the requests race');
  for (const r of results.filter((x) => x.status === 'rejected')) {
    assert.equal(r.reason.scope, 'visitor');
    assert.equal(r.reason.until.toISOString(), '2026-10-19T00:00:00.000Z');
  }
  assert.equal(store.items.get('ledger#visitor#v1#2026-10-18').committed, 50_000);
  assert.equal(store.items.get('ledger#day#2026-10-18').committed, 50_000, 'refused reservations wrote nothing');
  // Another visitor is unaffected, and a call dearer than a whole share is refused up front.
  await ledger.reserve(1_000, { now: NOW, visitor: 'v2' });
  await assert.rejects(ledger.reserve(50_001, { now: NOW, visitor: 'v3' }), (e) => e.scope === 'visitor');
  assert.equal(store.items.get('ledger#visitor#v3#2026-10-18'), undefined);
  // Tomorrow is a new day.
  await ledger.reserve(1_000, { now: new Date('2026-10-19T00:00:01Z'), visitor: 'v1' });
});

test('S4: settling adjusts the visitor share too', async () => {
  const store = memoryStore();
  const ledger = createLedger(store, { ...CAPS, visitorDayMicros: 0.05 * USD });
  const r = await ledger.reserve(6_000, { now: NOW, visitor: 'v1' });
  assert.equal(r.visitor, 'ledger#visitor#v1#2026-10-18');
  await ledger.settle(r, 900);
  const v = store.items.get(r.visitor);
  assert.deepEqual({ committed: v.committed, spent: v.spent }, { committed: 900, spent: 900 });
  assert.equal(v.expiresAt, Date.UTC(2026, 9, 21) / 1000, 'the share expires on its own, two days after the day ends');
  // Without a share configured nothing per visitor is written.
  const plain = createLedger(store, CAPS);
  const p = await plain.reserve(100, { now: NOW, visitor: 'v9' });
  assert.equal(p.visitor, null);
});
