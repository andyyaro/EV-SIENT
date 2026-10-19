// Your Index: the planner's own weighted sum of their confirmed columns (docs/FLEXIBLE_ANALYSIS.md
// section 3). This file holds the shapes the engine returns and the builder's small rules: which
// columns can be scored and why not, the default value function for a column, and the exclusion
// rules the planner writes as rows, turned into the JsonLogic keep conditions the engine runs.
// The engine checks and computes everything; nothing here scores a site.

import type { ColumnEntry, ColumnRole, Direction, IndexRefusal, IndexResult, IndexSpec } from '../engine/protocol';

export const NOT_OFFICIAL = 'Your index, not the EV-SIENT readiness score';

// ---------- the engine's answers, field for field (src/fcf_m2/flex/index.py) ----------

export interface IndexDriver {
  column: string; weight: number; value: number; points: number; max: number; absent: boolean; raw: string | null;
}

export interface IndexSite {
  siteId: string;
  name: string | null;
  score: number;
  bounds: { worst: number; best: number };
  completeness: number;
  missing: string[];
  drivers: IndexDriver[];
  rank?: number;
  robustness?: { rankLow: number; rankHigh: number; topShare: number; neverTopK: boolean };
  /** Unranked sites: why. */
  reason?: string;
}

export interface IndexExcluded {
  siteId: string;
  name: string | null;
  reasons: { screen: number; reason: string; missing: string[] }[];
}

export interface IndexRankChange {
  above: string; below: string; gap: number; tied: boolean; shareAhead: number | null; sentences: string[];
}

export interface IndexGate {
  id: string;
  level: 'block' | 'warn' | 'strong';
  message: string;
  columns: string[];
  numbers: Record<string, unknown>;
}

export interface IndexFormulaRow {
  column: string; direction: Direction; directionWords: string; weight: number; weightGiven: number;
  value: IndexSpec['criteria'][number]['value']; describe: string; coverage: number; indexCorrelation: number | null;
}

export interface IndexSummary {
  sites: number; excluded: number; unranked: number; ranked: number; withMissing: number; k: number;
  disclosure: string; note: string;
}

export interface IndexRobustness {
  draws: number; spread: number; seed: number; ordinalSpread: number; k: number; ordinalMapsNudged: string[]; method: string;
}

export interface ComparisonRow {
  siteId: string; name: string | null; indexRank: number; readinessRank: number; indexScore: number; readinessScore: number; shift: number;
}

export interface IndexComparison {
  official: false; name: string; badge: string; n: number; spearman: number | null;
  sites: ComparisonRow[]; disagreements: ComparisonRow[]; notInReadiness: string[]; notInIndex: string[];
}

/** IndexResult with the parts the screen reads typed. */
export interface IndexOutcome {
  official: false;
  name: string;
  badge: string;
  refused: boolean;
  refusals: IndexRefusal[];
  spec: IndexSpec | null;
  formula: IndexFormulaRow[];
  summary: IndexSummary | null;
  sites: IndexSite[];
  unranked: IndexSite[];
  excluded: IndexExcluded[];
  rankChanges: IndexRankChange[];
  robustness: IndexRobustness | null;
  gatesChecked: string[];
  gates: IndexGate[];
  comparison?: IndexComparison;
}

export const outcome = (r: IndexResult) => r as unknown as IndexOutcome;

// ---------- the spec ----------

export type Kind = 'linear' | 'threshold' | 'target' | 'ordinal';
export type Criterion = IndexSpec['criteria'][number];

export const DEFAULT_ROBUSTNESS = { draws: 2000, spread: 0.25, seed: 1 };
export const MIN_COVERAGE = 0.65;

export function newSpec(name: string): IndexSpec {
  return {
    pack: 'evsient-custom-index', packVersion: '1.0.0', name, criteria: [], screens: [],
    missing: 'no_credit', minCoverage: MIN_COVERAGE, robustness: { ...DEFAULT_ROBUSTNESS },
  };
}

/** A name not already taken: "My Index", "My Index 2", ... */
export function freeName(base: string, specs: IndexSpec[]): string {
  const taken = new Set(specs.map((s) => s.name.trim()));
  if (!taken.has(base)) return base;
  for (let i = 2; ; i++) if (!taken.has(`${base} ${i}`)) return `${base} ${i}`;
}

/** Each criterion's share of the index: its weight over the sum of the weights. */
export function shares(spec: IndexSpec): number[] {
  const total = spec.criteria.reduce((a, c) => a + (Number.isFinite(c.weight) && c.weight > 0 ? c.weight : 0), 0);
  return spec.criteria.map((c) => (total > 0 && c.weight > 0 ? c.weight / total : 0));
}

// ---------- which columns can be scored ----------

const NUMERIC_ROLES: ReadonlySet<ColumnRole> = new Set(['count', 'measure', 'score', 'percentage', 'money', 'year', 'flag']);
const LABEL_ROLES: ReadonlySet<ColumnRole> = new Set(['ordinal', 'category']);

export const ROLE_WORDS: Record<ColumnRole, string> = {
  identifier: 'Identifier', name: 'Name', category: 'Categories', ordinal: 'Ordered levels', flag: 'Yes or no',
  count: 'Count', measure: 'Measure', score: 'Score', percentage: 'Percentage', money: 'Money', date: 'Date',
  year: 'Year', latitude: 'Latitude', longitude: 'Longitude', address: 'Address', text: 'Free text', unknown: 'Not yet known',
};

export const DIRECTION_WORDS: Record<Direction, string> = {
  higher_better: 'Higher is better', lower_better: 'Lower is better', neither: 'Neither is better',
};

export const role = (e: ColumnEntry) => e['evsient:role'];
export const confirmedDirection = (e: ColumnEntry): Direction | null =>
  e['evsient:provenance'] === 'confirmed_by_user' ? e['evsient:direction'] : null;

export const isNumeric = (e: ColumnEntry) => NUMERIC_ROLES.has(role(e));
export const isLabels = (e: ColumnEntry) => LABEL_ROLES.has(role(e));

/** The directions the planner may confirm for a column, or none when it has no order at all. */
export function directionsFor(e: ColumnEntry): Direction[] {
  if (NUMERIC_ROLES.has(role(e)) || role(e) === 'ordinal') return ['higher_better', 'lower_better', 'neither'];
  if (role(e) === 'category') return ['neither'];
  return [];
}

/** The direction the dictionary's evidence proposes, if any (a proposal only, never applied). */
export function proposedDirection(e: ColumnEntry): Direction | null {
  return e['evsient:evidence'].find((x) => x.signal === 'direction' && x.direction)?.direction ?? null;
}

export type Scorable =
  | { ok: true; direction: Direction; kinds: Kind[] }
  | { ok: false; why: string; needsDirection: boolean };

/** Whether a column can go into the index now, and if not, why, in the planner's words. */
export function scorable(e: ColumnEntry): Scorable {
  const r = role(e);
  if (r === 'date') return { ok: false, why: 'Dates cannot be scored yet. A year column can.', needsDirection: false };
  if (!NUMERIC_ROLES.has(r) && !LABEL_ROLES.has(r)) {
    const what: Partial<Record<ColumnRole, string>> = {
      identifier: 'It identifies each site, so no value is better than another.',
      name: 'It names each site, so no value is better than another.',
      address: 'It is an address, so no value is better than another.',
      latitude: 'It is a coordinate, which says where a site is, not how good it is.',
      longitude: 'It is a coordinate, which says where a site is, not how good it is.',
      text: 'It is free text, which has no order to score.',
      unknown: 'The planner has not said what this column holds yet.',
    };
    return { ok: false, why: what[r] ?? 'This kind of column cannot be scored.', needsDirection: false };
  }
  const reading = e['evsient:reading'];
  if (reading && reading.read === 0) return { ok: false, why: 'None of its cells could be read as values.', needsDirection: false };
  const direction = confirmedDirection(e);
  if (!direction) {
    return {
      ok: false,
      why: r === 'category'
        ? 'Its categories have no order. Confirm that neither direction is better, then give each category a value.'
        : 'Its direction is not confirmed yet: say whether higher or lower is better.',
      needsDirection: true,
    };
  }
  if (LABEL_ROLES.has(r)) return { ok: true, direction, kinds: ['ordinal'] };
  return { ok: true, direction, kinds: direction === 'neither' ? ['target'] : ['linear', 'threshold'] };
}

export const KIND_WORDS: Record<Kind, string> = {
  linear: 'Straight Line', threshold: 'Cut-Offs', target: 'Target Value', ordinal: 'Value for Each Level',
};

const num = (v: unknown): number | undefined => (typeof v === 'number' && Number.isFinite(v) ? v : undefined);

/** The lowest and highest values the dictionary read in the column, when it is numeric. */
export function observedRange(e: ColumnEntry): { min: number; max: number } | null {
  const r = e['evsient:reading'];
  const min = num(r?.min), max = num(r?.max);
  if (role(e) === 'flag') return { min: 0, max: 1 };
  return min !== undefined && max !== undefined ? { min, max } : null;
}

/** The column's levels as text, lowest first (ordinal) or as the dictionary lists them (category). */
export const levels = (e: ColumnEntry): string[] => (e.categories ?? []).map(String);

/** A value function for a kind, starting from the column's observed range or levels. */
export function defaultValue(e: ColumnEntry, kind: Kind, direction: Direction): Criterion['value'] {
  const range = observedRange(e);
  if (kind === 'linear') return { kind };
  if (kind === 'threshold') {
    if (!range) return { kind };
    return direction === 'lower_better' ? { kind, worst: range.max, best: range.min } : { kind, worst: range.min, best: range.max };
  }
  if (kind === 'target') {
    if (!range) return { kind };
    return { kind, low: range.min, target: round((range.min + range.max) / 2), high: range.max };
  }
  const names = levels(e);
  const map: Record<string, number> = {};
  names.forEach((name, i) => {
    const up = names.length > 1 ? i / (names.length - 1) : 1;
    map[name] = role(e) === 'ordinal' && direction !== 'neither' ? round(direction === 'higher_better' ? up : 1 - up) : 0.5;
  });
  return { kind, map };
}

const round = (x: number) => Math.round(x * 100) / 100;

export function newCriterion(e: ColumnEntry): Criterion | null {
  const s = scorable(e);
  if (!s.ok) return null;
  return { column: e.name, direction: s.direction, weight: 10, value: defaultValue(e, s.kinds[0], s.direction) };
}

// ---------- exclusion rules ----------

/** One rule as the planner writes it: leave out a site when column op value. */
export type RuleOp = 'lt' | 'le' | 'gt' | 'ge' | 'eq' | 'ne' | 'in' | 'missing';

export interface Rule {
  column: string;
  op: RuleOp;
  /** A number for lt..ge on a numeric column; a label (or 1 / 0 for a flag) for eq and ne; labels for in. */
  value: string | number | (string | number)[] | null;
}

export const OP_WORDS: Record<RuleOp, string> = {
  lt: 'is below', le: 'is at most', gt: 'is above', ge: 'is at least', eq: 'is', ne: 'is not', in: 'is one of', missing: 'has no value',
};

export function opsFor(e: ColumnEntry | undefined): RuleOp[] {
  if (!e) return ['missing'];
  if (role(e) === 'flag') return ['eq', 'ne', 'missing'];
  if (isNumeric(e)) return ['lt', 'le', 'gt', 'ge', 'eq', 'ne', 'missing'];
  return ['eq', 'ne', 'in', 'missing'];
}

/** Whether a site with no value for the rule's column is left out by it, as the engine reads the rule. */
export const missingLeftOut = (op: RuleOp) => op !== 'eq' && op !== 'in';

const KEEP: Partial<Record<RuleOp, string>> = { lt: '>=', le: '>', gt: '<=', ge: '<', eq: '!=', ne: '==' };
const FROM_KEEP: Record<string, RuleOp> = { '>=': 'lt', '>': 'le', '<=': 'gt', '<': 'ge', '!=': 'eq', '==': 'ne' };

/** Whether a rule is finished enough to run. */
export function ruleComplete(r: Rule): boolean {
  if (!r.column) return false;
  if (r.op === 'missing') return true;
  if (r.op === 'in') return Array.isArray(r.value) && r.value.length > 0;
  if (r.value === null || r.value === '' || Array.isArray(r.value)) return false;
  return r.op === 'eq' || r.op === 'ne' ? true : typeof r.value === 'number' && Number.isFinite(r.value);
}

/** The engine keeps a site when its rule is true, so a rule that leaves sites out is written as its opposite. */
export function ruleLogic(r: Rule): unknown {
  const v = { var: r.column };
  if (r.op === 'missing') return { '!': [{ missing: [r.column] }] };
  if (r.op === 'in') return { '!': [{ in: [v, r.value] }] };
  return { [KEEP[r.op]!]: [v, r.value] };
}

const said = (x: unknown) => (typeof x === 'number' ? fmtNumber(x) : String(x));

export function ruleReason(r: Rule, e: ColumnEntry | undefined): string {
  const value = (x: string | number) => (e && role(e) === 'flag' ? (Number(x) === 1 ? 'Yes' : 'No') : said(x));
  if (r.op === 'missing') return `${r.column} has no value`;
  if (r.op === 'in') return `${r.column} is one of ${(r.value as (string | number)[]).map(value).join(', ')}`;
  return `${r.column} ${OP_WORDS[r.op]} ${value(r.value as string | number)}`;
}

/** Read back a rule this screen wrote; any other JsonLogic is kept as it is and shown in words only. */
export function ruleFrom(logic: unknown): Rule | null {
  if (!logic || typeof logic !== 'object' || Array.isArray(logic)) return null;
  const [op, args] = Object.entries(logic as Record<string, unknown>)[0] ?? [];
  const col = (x: unknown) => (x && typeof x === 'object' && !Array.isArray(x) && typeof (x as { var?: unknown }).var === 'string' ? (x as { var: string }).var : null);
  if (op === '!' && Array.isArray(args) && args.length === 1 && args[0] && typeof args[0] === 'object') {
    const inner = args[0] as Record<string, unknown>;
    if (Array.isArray(inner.missing) && inner.missing.length === 1 && typeof inner.missing[0] === 'string') {
      return { column: inner.missing[0], op: 'missing', value: null };
    }
    if (Array.isArray(inner.in) && inner.in.length === 2 && col(inner.in[0]) && Array.isArray(inner.in[1])) {
      return { column: col(inner.in[0])!, op: 'in', value: inner.in[1] as (string | number)[] };
    }
    return null;
  }
  if (op && op in FROM_KEEP && Array.isArray(args) && args.length === 2 && col(args[0])) {
    const value = args[1];
    if (typeof value !== 'string' && typeof value !== 'number') return null;
    return { column: col(args[0])!, op: FROM_KEEP[op], value };
  }
  return null;
}

// ---------- words and numbers ----------

const n2 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const n1 = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const p0 = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 0 });
const p1 = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 });

export const fmtNumber = (x: number) => n2.format(x);
export const fmtPoints = (x: number) => n1.format(x);
export const fmtShare = (x: number) => p0.format(x);
/** A share to one decimal place, for normalised weights where 33% and 33.3% differ. */
export const fmtShareFine = (x: number) => p1.format(x);

/** How steady a rank is across the weight draws, from its 5th to 95th percentile. */
export function steadiness(low: number, high: number): { word: string; key: 'fixed' | 'steady' | 'moves' } {
  const spread = high - low;
  if (spread === 0) return { word: 'Fixed', key: 'fixed' };
  if (spread <= 2) return { word: 'Steady', key: 'steady' };
  return { word: 'Moves', key: 'moves' };
}

/** A few sentences that state the index in words and numbers. */
export function formulaWords(r: IndexOutcome): string[] {
  const rows = r.formula;
  const parts = rows.map((f) => `${fmtShareFine(f.weight)} ${f.column}`);
  return [
    `${r.name} = ${parts.join(' + ')}, each column's credit (0 to 1) times its weight, out of 100 points.`,
    ...rows.map((f) => `${f.describe.replace(/\.$/, '')} (${f.directionWords}; ${f.column} has a value at ${fmtShare(f.coverage)} of the sites scored).`),
  ];
}

export const siteLabel = (s: { siteId: string; name: string | null }) => s.name || s.siteId;

/** The engine refuses with a message whose first words say the real engine is needed. */
export const REAL_ONLY_TEXT = 'Your columns are read with the real engine only.';
