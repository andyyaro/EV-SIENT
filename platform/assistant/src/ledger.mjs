// The spend ledger: the assistant's hard cap on model spend, and it fails closed.
//
// Before every model call the proxy reserves the most that call could cost (pricing.mjs), on
// condition that the month's and the day's committed spend stay within their caps. After the
// call it settles: the reservation is replaced by what the call actually cost. A reservation
// that is never settled (the function crashed or timed out mid-answer) stays counted, so the
// ledger can only overstate spend, never understate it. Any error reading or writing the ledger
// refuses the call. The ledger records amounts and counts only, never any text.
//
// Items (one DynamoDB table, key `pk`):
//   ledger#month#2026-10     committed, spent, calls, deeperCommitted
//   ledger#day#2026-10-18    committed, spent
//   ledger#visitor#<hash>#2026-10-18   committed, spent (one visitor's share of a day)
// Amounts are micro-dollars (1 = $0.000001).

import { ConditionFailed } from './store.mjs';

export const USD = 1_000_000;

export function monthKey(now) { return now.toISOString().slice(0, 7); }
export function dayKey(now) { return now.toISOString().slice(0, 10); }

/** The first moment of next month (UTC), when a monthly pause ends. */
export function nextMonthStart(now) {
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1));
}

/** The first moment of tomorrow (UTC), when a daily pause ends. */
export function nextDayStart(now) {
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
}

const epoch = (d) => Math.floor(d.getTime() / 1000);

export class CapReached extends Error {
  constructor(scope, until) {
    super(`${scope} limit reached`);
    this.name = 'CapReached';
    this.scope = scope; // 'month' | 'day' | 'deeper' | 'visitor'
    this.until = until; // Date
  }
}

/**
 * caps: { monthMicros, dayMicros, deeperMonthMicros, visitorDayMicros? } (whole micro-dollars).
 * Returns { reserve, settle, status }.
 */
export function createLedger(store, caps) {
  for (const [k, v] of Object.entries(caps)) {
    if (!Number.isInteger(v) || v < 0) throw new Error(`ledger cap ${k} must be a whole number of micro-dollars`);
  }

  /**
   * Reserve `amount` micro-dollars for one call. Throws CapReached when any cap would be passed,
   * and lets any other error through (the caller refuses the call on any error).
   */
  async function reserve(amount, { now = new Date(), deeper = false, visitor = null } = {}) {
    if (!Number.isInteger(amount) || amount <= 0) throw new Error('a reservation must be a positive whole number of micro-dollars');
    const month = `ledger#month#${monthKey(now)}`;
    const day = `ledger#day#${dayKey(now)}`;
    const untilMonth = nextMonthStart(now);
    const untilDay = nextDayStart(now);
    // A call dearer than a whole cap can never fit; refuse without writing.
    if (amount > caps.monthMicros) throw new CapReached('month', untilMonth);
    if (amount > caps.dayMicros) throw new CapReached('day', untilDay);
    if (deeper && amount > caps.deeperMonthMicros) throw new CapReached('deeper', untilMonth);
    const perVisitor = visitor && caps.visitorDayMicros !== undefined;
    if (perVisitor && amount > caps.visitorDayMicros) throw new CapReached('visitor', untilDay);
    const monthOp = {
      key: month,
      add: { committed: amount, ...(deeper ? { deeperCommitted: amount } : {}) },
      atMost: { committed: caps.monthMicros - amount, ...(deeper ? { deeperCommitted: caps.deeperMonthMicros - amount } : {}) },
      ttl: epoch(untilMonth) + 400 * 86400,
    };
    const dayOp = { key: day, add: { committed: amount }, atMost: { committed: caps.dayMicros - amount }, ttl: epoch(untilDay) + 40 * 86400 };
    const visitorKey = perVisitor ? `ledger#visitor#${visitor}#${dayKey(now)}` : null;
    const ops = [monthOp, dayOp];
    if (visitorKey) {
      ops.push({ key: visitorKey, add: { committed: amount }, atMost: { committed: caps.visitorDayMicros - amount }, ttl: epoch(untilDay) + 2 * 86400 });
    }
    try {
      await store.write(ops);
    } catch (e) {
      if (e instanceof ConditionFailed) {
        if (e.index === 1) throw new CapReached('day', untilDay);
        if (e.index === 2) throw new CapReached('visitor', untilDay);
        // The month operation carries both month conditions; tell them apart by reading back.
        if (deeper) {
          const m = await store.read(month).catch(() => null);
          if (m && (m.committed ?? 0) + amount <= caps.monthMicros) throw new CapReached('deeper', untilMonth);
        }
        throw new CapReached('month', untilMonth);
      }
      throw e;
    }
    return { month, day, visitor: visitorKey, amount, deeper };
  }

  /** Replace a reservation with what the call cost. Never conditional: spend already happened. */
  async function settle(reservation, actual) {
    if (!Number.isInteger(actual) || actual < 0) throw new Error('actual spend must be a whole number of micro-dollars');
    const delta = actual - reservation.amount;
    const ops = [
      { key: reservation.month, add: { committed: delta, spent: actual, calls: 1, ...(reservation.deeper ? { deeperCommitted: delta } : {}) } },
      { key: reservation.day, add: { committed: delta, spent: actual } },
    ];
    if (reservation.visitor) ops.push({ key: reservation.visitor, add: { committed: delta, spent: actual } });
    await store.write(ops);
  }

  /** What the panel shows: whether the month's cap is reached and roughly how much is used. */
  async function status(now = new Date(), probeMicros = 0) {
    const m = (await store.read(`ledger#month#${monthKey(now)}`)) ?? {};
    const d = (await store.read(`ledger#day#${dayKey(now)}`)) ?? {};
    const committed = m.committed ?? 0;
    const monthLeft = caps.monthMicros - committed;
    const dayLeft = caps.dayMicros - (d.committed ?? 0);
    return {
      month: monthKey(now),
      usedShare: caps.monthMicros ? Math.min(1, Math.max(0, committed / caps.monthMicros)) : 1,
      monthReached: monthLeft < Math.max(1, probeMicros),
      dayReached: dayLeft < Math.max(1, probeMicros),
      monthResumes: nextMonthStart(now),
      dayResumes: nextDayStart(now),
    };
  }

  return { reserve, settle, status };
}
