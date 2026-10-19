// Explore's words. The findings themselves are the engine's sentences (src/fcf_m2/flex/explore.py
// fills them from fixed templates); this file only names the measures, kinds and roles and formats
// the numbers. Nothing here may say that one column changes another: describe, never explain.

import type { ExploreCard, ExploreResult } from '../engine/protocol';

const whole = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const two = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const int = (n: number) => whole.format(n);
export const num2 = (n: number) => two.format(n).replace(/^-/, '−');

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${whole.format(n)} ${n === 1 ? one : many}`;
}

/** The adjusted significance in words a planner can read: very small values are not spelled out. */
export function qText(q: number | null): string {
  if (q === null || !Number.isFinite(q)) return 'Not tested on its own';
  if (q < 0.001) return 'below 0.001';
  return q < 0.01 ? q.toFixed(3) : q.toFixed(2);
}

/** Each strength measure: its short name, and what 0 and 1 mean on its own scale. */
export const MEASURES: Record<string, { name: string; what: string; signed: boolean }> = {
  spearman_rho: {
    name: 'Rank correlation (rho)', signed: true,
    what: 'How closely the two columns rise and fall together across sites. 0 is no pattern; 1 is in perfect step.',
  },
  cliffs_delta: {
    name: "Cliff's delta", signed: true,
    what: 'How often a site in one group has a higher value than a site in the other. 0 is no difference; 1 is every time.',
  },
  epsilon_squared: {
    name: 'Epsilon squared', signed: false,
    what: 'How much of the spread in values lines up with the groups. 0 is none; 1 is all of it.',
  },
  cramers_v: {
    name: "Cramer's V", signed: false,
    what: 'How strongly the two sets of groups go together. 0 is not at all; 1 is completely.',
  },
};

export function measure(name: string) {
  return MEASURES[name] ?? { name: name.replace(/_/g, ' '), what: '', signed: false };
}

/** The strength as drawn: the size of the effect from 0 to 1, with its 95% interval on that scale. */
export function strength(effect: NonNullable<ExploreCard['effect']>): { value: number; low: number | null; high: number | null } {
  const clamp = (x: number) => Math.max(0, Math.min(1, x));
  const flip = effect.value < 0;
  const v = Math.abs(effect.value);
  if (effect.low === null || effect.high === null) return { value: clamp(v), low: null, high: null };
  const lo = flip ? -effect.high : effect.low;
  const hi = flip ? -effect.low : effect.high;
  return { value: clamp(v), low: clamp(lo), high: clamp(hi) };
}

export type PatternKind = 'association' | 'group' | 'missingness' | 'within' | string;

export const KIND_LABEL: Record<string, string> = {
  association: 'Two Columns Together',
  group: 'Differs by Group',
  missingness: 'Missing Values',
};

export function kindLabel(card: ExploreCard): string {
  if (card.kind === 'association' && card.effect?.name === 'cramers_v') return 'Groups Together';
  return KIND_LABEL[card.kind] ?? 'Pattern';
}

const ROLE_WORDS: Record<string, string> = {
  identifier: 'Site ID', name: 'Name', category: 'Groups', ordinal: 'Ordered levels', flag: 'Yes or no',
  count: 'Count', measure: 'Measurement', score: 'Score', percentage: 'Percentage', money: 'Money',
  date: 'Date', year: 'Year', latitude: 'Latitude', longitude: 'Longitude', address: 'Address',
  text: 'Free text', unknown: 'Not yet described',
};

export const roleWords = (role: string) => ROLE_WORDS[role] ?? role;

/** Column name to the readable label the engine gave it (in its summaries). */
export function labelsOf(result: ExploreResult | null): Record<string, string> {
  const out: Record<string, string> = {};
  const summaries = (result?.summaries ?? []) as { column?: string; label?: string }[];
  for (const s of summaries) if (s.column) out[s.column] = s.label || s.column;
  return out;
}

/** What a pattern compares, in words: "Heat Risk and Service Population". */
export function comparedText(card: ExploreCard, labels: Record<string, string>): string {
  const [a, b] = card.columns.map((c) => labels[c] ?? c);
  if (card.kind === 'missingness') return `Gaps in ${a} across ${b} groups`;
  if (card.kind === 'group') return `${b} across ${a} groups`;
  return b ? `${a} and ${b}` : a;
}

/** The plain statement every Explore surface carries. */
export const NOT_THE_SCORE = 'Your data, exploratory. Not part of the EV-SIENT readiness score.';
