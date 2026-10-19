// Plain words for the column dictionary. They only name what the engine said; every reading,
// count and proposal comes from the engine (src/fcf_m2/flex/dictionary.py).

import type { ColumnEntry, ColumnRole, Direction } from '../engine/protocol';
import { plural } from '../lib/fieldText';

export const ROLE_ORDER: ColumnRole[] = [
  'identifier', 'name', 'category', 'ordinal', 'flag', 'count', 'measure', 'score', 'percentage',
  'money', 'date', 'year', 'latitude', 'longitude', 'address', 'text', 'unknown',
];

export const ROLE_LABEL: Record<ColumnRole, string> = {
  identifier: 'ID', name: 'Name', category: 'Category', ordinal: 'Ordered Levels', flag: 'Yes or No',
  count: 'Count', measure: 'Measurement', score: 'Score on a Scale', percentage: 'Percentage', money: 'Money',
  date: 'Date', year: 'Year', latitude: 'Latitude', longitude: 'Longitude', address: 'Address',
  text: 'Free Text', unknown: 'Unknown',
};

export const ROLE_HINT: Record<ColumnRole, string> = {
  identifier: 'A code that names one site, such as a site ID.',
  name: 'A name for each row, such as a site or partner name.',
  category: 'Groups with no order, such as a city or a site type.',
  ordinal: 'Levels in an order, such as Low, Moderate and High.',
  flag: 'Yes or no, sometimes with other states.',
  count: 'Whole numbers of things, such as visits or people.',
  measure: 'Numbers with a unit, such as kW or square metres.',
  score: 'Numbers on a fixed scale, such as 0 to 100.',
  percentage: 'A share, written as a percentage.',
  money: 'An amount of money in one currency.',
  date: 'A calendar date.',
  year: 'A calendar year.',
  latitude: 'Latitude in decimal degrees.',
  longitude: 'Longitude in decimal degrees.',
  address: 'A street address or postcode.',
  text: 'Notes or comments, read as words only.',
  unknown: 'Not yet known. The cells are kept as written.',
};

/** Roles for which higher or lower can be better (the engine's _DIRECTIONAL). */
const DIRECTIONAL = new Set<ColumnRole>(['ordinal', 'flag', 'count', 'measure', 'score', 'percentage', 'money', 'year', 'date']);
/** Roles that carry a unit (the engine's _UNIT_ROLES). */
const UNIT_ROLES = new Set<ColumnRole>(['measure', 'money', 'percentage', 'count']);
/** Roles read through a list of values (the engine's _CATEGORICAL). */
const LISTED = new Set<ColumnRole>(['category', 'ordinal', 'flag']);

export const canRank = (role: ColumnRole) => DIRECTIONAL.has(role);
export const hasUnit = (role: ColumnRole) => UNIT_ROLES.has(role);

/**
 * The kinds this screen can switch a column to. A kind read through a list of values needs that
 * list (and, for ordered levels, its order), which this screen does not edit yet, so those are
 * offered only where the entry already has what they need.
 */
export function roleChoices(entry: ColumnEntry): ColumnRole[] {
  const current = entry['evsient:role'];
  const listed = Array.isArray(entry.categories) && entry.categories.length > 0;
  return ROLE_ORDER.filter((role) => {
    if (role === current) return true;
    if (!LISTED.has(role)) return true;
    if (!listed) return false;
    if (role === 'ordinal') return entry.categoriesOrdered === true;
    return true;
  });
}

export const DIRECTION_LABEL: Record<Direction, string> = {
  higher_better: 'Higher Is Better', lower_better: 'Lower Is Better', neither: 'Not Ranked',
};

const DIRECTION_WORDS: Record<Direction, string> = {
  higher_better: 'higher is better', lower_better: 'lower is better', neither: 'not ranked (neither is better)',
};

export const directionWords = (d: Direction) => DIRECTION_WORDS[d];

/** What "higher" means for this kind of column, so the choice is concrete. */
export function higherMeans(entry: ColumnEntry, role: ColumnRole): string {
  if (role === 'flag') return 'For a yes or no column, higher means yes.';
  if (role === 'ordinal') {
    const levels = (entry.categories ?? []).map(String);
    return levels.length ? `Higher means later in the order ${levels.join(' < ')}.` : 'Higher means later in the order of levels.';
  }
  if (role === 'date' || role === 'year') return 'Higher means later.';
  return 'Higher means a larger number.';
}

/** The direction the engine proposes, from its evidence. A proposal only: never applied unasked. */
export function suggestedDirection(entry: ColumnEntry): { direction: Direction; because: string } | null {
  const item = entry['evsient:evidence'].find((e) => e.signal === 'direction' && e.direction);
  return item?.direction ? { direction: item.direction, because: sentence(item.text) } : null;
}

export function sentence(text: string): string {
  const t = text.trim();
  if (!t) return t;
  const s = t[0].toUpperCase() + t.slice(1);
  return /[.!?]$/.test(s) ? s : `${s}.`;
}

const TYPE_WORDS: Record<string, string> = {
  string: 'text', number: 'numbers', integer: 'whole numbers', date: 'dates', year: 'years', boolean: 'yes or no', any: 'as written',
};

export const typeWords = (type: string) => TYPE_WORDS[type] ?? type;

const num = (v: unknown) => (typeof v === 'number' ? v.toLocaleString('en-US') : String(v));

export function rangeText(range: [number, number] | null | undefined): string | null {
  return range ? `${num(range[0])} to ${num(range[1])}` : null;
}

/** How many cells were read, in one line. */
export function cellsText(entry: ColumnEntry): string {
  const r = entry['evsient:reading'];
  if (!r) return 'Not read again yet.';
  const parts = [`${r.read.toLocaleString('en-US')} of ${plural(r.cells, 'cell')} read`];
  if (r.missing) parts.push(`${r.missing.toLocaleString('en-US')} missing`);
  if (r.unreadable) parts.push(`${r.unreadable.toLocaleString('en-US')} not read`);
  return `${parts.join(', ')}.`;
}

const PROBLEM_KINDS = new Set(['unreadable', 'ambiguous', 'sentinel', 'outOfRange', 'notWhole', 'extra']);

/** The reading problems for a column, each a sentence. Empty when the cells read cleanly. */
export function readingProblems(entry: ColumnEntry): string[] {
  const out: string[] = [];
  if (entry['evsient:agreement'] === 'conflict') {
    out.push('The header and the values say different things. Check the kind of column.');
  }
  const r = entry['evsient:reading'];
  if (!r) return out;
  for (const p of r.patterns) {
    if (!p.kind || !PROBLEM_KINDS.has(p.kind)) continue;
    const shown = p.pattern === '' ? 'An empty cell' : `"${p.pattern}"`;
    out.push(`${shown} (${plural(p.count, 'cell')}): ${p.readAs.replace(/\.$/, '')}.`);
  }
  return out;
}

/** Patterns the planner can mark as missing: likely no-data codes, and a yes or no column's other states. */
export function missingCandidates(entry: ColumnEntry): { pattern: string; count: number }[] {
  const r = entry['evsient:reading'];
  if (!r) return [];
  const already = new Set(entry.missingValues ?? []);
  return r.patterns
    .filter((p) => (p.kind === 'sentinel' || p.kind === 'extra') && p.pattern !== '' && !already.has(p.pattern))
    .map((p) => ({ pattern: p.pattern, count: p.count }));
}

/** Whether some cells were left unread because the decimal mark or the date order is undecided. */
export function hasAmbiguous(entry: ColumnEntry): boolean {
  return !!entry['evsient:reading']?.patterns.some((p) => p.kind === 'ambiguous');
}

export const DECIMAL_LABEL: Record<'.' | ',', string> = { '.': 'A Point (1.5)', ',': 'A Comma (1,5)' };
export const DATE_ORDER_LABEL: Record<string, string> = {
  '%Y-%m-%d': 'Year, Month, Day (2026-10-18)', '%d/%m/%Y': 'Day, Month, Year (18/10/2026)', '%m/%d/%Y': 'Month, Day, Year (10/18/2026)',
};

/** "Low, Moderate, High" for a column read through a list of values, shortened past six. */
export function valuesText(entry: ColumnEntry): string | null {
  const values = (entry.categories ?? []).map(String);
  if (!values.length) return null;
  const join = entry.categoriesOrdered ? ' < ' : ', ';
  return values.length > 6 ? `${values.slice(0, 6).join(join)} and ${values.length - 6} more` : values.join(join);
}

/** The engine's note of patterns past its cap, in either of the shapes it has used. */
export function notShownText(value: unknown): string | null {
  if (typeof value === 'number' && value > 0) return `${plural(value, 'more pattern')} not listed.`;
  if (value && typeof value === 'object' && 'patterns' in value) {
    const v = value as { patterns: number; cells?: number };
    return `${plural(v.patterns, 'more pattern')}${typeof v.cells === 'number' ? ` (${plural(v.cells, 'cell')})` : ''} not listed.`;
  }
  return null;
}
