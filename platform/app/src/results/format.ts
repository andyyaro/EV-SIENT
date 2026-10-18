// Display helpers shared by Results and Report. They format the engine's numbers and name its
// codes in the planner's words; none of them computes a score.

import type { ConfidenceLevel, SiteResult } from '../engine/protocol';

const nf = (o: Intl.NumberFormatOptions) => new Intl.NumberFormat('en-US', o);
const one = nf({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
const two = nf({ minimumFractionDigits: 2, maximumFractionDigits: 2 });
const whole = nf({ maximumFractionDigits: 0 });
const usd = nf({ style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const pct = nf({ style: 'percent', maximumFractionDigits: 0 });
const signed = nf({ minimumFractionDigits: 1, maximumFractionDigits: 1, signDisplay: 'always' });

const ok = (v: number | null | undefined): v is number => typeof v === 'number' && Number.isFinite(v);

export const NOT_RECORDED = 'Not recorded';

export const fmt = {
  score: (v: number | null | undefined) => (ok(v) ? one.format(v) : NOT_RECORDED),
  one: (v: number | null | undefined) => (ok(v) ? one.format(v) : NOT_RECORDED),
  two: (v: number | null | undefined) => (ok(v) ? two.format(v) : NOT_RECORDED),
  points: (v: number | null | undefined) => (ok(v) ? one.format(v) : NOT_RECORDED),
  signed: (v: number | null | undefined) => (ok(v) ? signed.format(v) : NOT_RECORDED),
  int: (v: number | null | undefined) => (ok(v) ? whole.format(v) : NOT_RECORDED),
  usd: (v: number | null | undefined) => (ok(v) ? usd.format(v) : NOT_RECORDED),
  pct: (v: number | null | undefined) => (ok(v) ? pct.format(v) : NOT_RECORDED),
  weight: (v: number | null | undefined) => (ok(v) ? pct.format(v) : NOT_RECORDED),
  minutes: (v: number | null | undefined) => (ok(v) ? `${one.format(v)} min` : NOT_RECORDED),
  ports: (v: number | null | undefined) => (ok(v) ? `${whole.format(v)} ${v === 1 ? 'port' : 'ports'}` : NOT_RECORDED),
};

export { ok as isNumber };

/** The tier's key for the shape marks in shell.css, from the engine's own tier text. */
export type TierKey = 'tier1' | 'tier2' | 'tier3' | 'high-review' | 'special' | 'other';

export function tierKey(tier: string): TierKey {
  const t = tier.toLowerCase();
  if (t.startsWith('tier 1')) return 'tier1';
  if (t.startsWith('tier 2')) return 'tier2';
  if (t.startsWith('tier 3')) return 'tier3';
  if (t.startsWith('high-review')) return 'high-review';
  if (t.includes('special-use') || t.startsWith('low public-priority')) return 'special';
  return 'other';
}

const TIER_SHORT: Record<TierKey, string> = {
  tier1: 'Tier 1', tier2: 'Tier 2', tier3: 'Tier 3', 'high-review': 'High Review', special: 'Special Use', other: 'Other',
};

export function tierShort(tier: string): string {
  const k = tierKey(tier);
  return k === 'other' ? tier : TIER_SHORT[k];
}

/** The engine's tier text with its hyphen separator read as a colon: "Tier 2: promising candidate, refine data". */
export function tierLong(tier: string): string {
  return tier.replace(/\s+-\s+/, ': ');
}

export const TIER_ORDER: TierKey[] = ['tier1', 'high-review', 'tier2', 'tier3', 'special', 'other'];

export const CONFIDENCE_CUTOFFS = 'High is 75 or more of 100, Medium 50 to 74.9, Low below 50.';

export function confidenceText(s: SiteResult): string {
  const { level, score } = s.confidence;
  if (!level) return NOT_RECORDED;
  return ok(score) ? `${level} (${one.format(score)})` : level;
}

export function confidenceLevel(level: ConfidenceLevel | null): string {
  return level ?? NOT_RECORDED;
}

/** Scenario case codes in words. */
export function caseLabel(c: string): string {
  const map: Record<string, string> = {
    baseline: 'Baseline', base: 'Base', high: 'High Growth', stress_combined: 'Combined Stress',
  };
  return map[c] ?? sentence(c);
}

/** An engine code such as "starter_install_with_expandable_design" read as words. */
export function sentence(code: string): string {
  const s = code.replace(/_/g, ' ').trim();
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

export function siteTypeLabel(t: string): string {
  return sentence(t || 'unspecified');
}

export const SUBSCORE_LABELS: Record<string, string> = {
  demand: 'Demand', feasibility: 'Feasibility', safety: 'Safety', equity: 'Equity',
};

export function subscoreLabel(key: string): string {
  const k = key.replace(/_subscore$/, '');
  return SUBSCORE_LABELS[k] ?? sentence(k);
}

export const SUBSCORE_KEYS = ['demand', 'feasibility', 'safety', 'equity'] as const;

/** Today's local date as YYYY-MM-DD, for file names. */
export function today(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** A file-name-safe slug. */
export function slug(s: string): string {
  return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
}

export function dateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(d) + ' UTC';
}

export function longDate(ymd: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(ymd);
  if (!m) return ymd;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'long', timeZone: 'UTC' }).format(d);
}

/** "A, B and C" */
export function andList(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${whole.format(n)} ${n === 1 ? one : many}`;
}
