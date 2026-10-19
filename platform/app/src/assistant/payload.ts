// What may leave the tab for the assistant (docs/FLEXIBLE_ANALYSIS.md section 5), and the
// builder that makes it. The server (platform/assistant/src/validate.mjs) checks the same rules
// and refuses anything else, so a change here needs the same change there; the tests in
// platform/assistant/test/payload.test.mjs run this file's output through the server's check.
//
// Three tiers:
//   Always        where the planner is and the file's shape (step, rows, columns).
//   With consent  per column: header, dictionary role, unit, direction and declared scale, the
//                 share of blanks, a bucket of distinct values, rounded 10th, 50th and 90th
//                 percentiles (never the smallest or largest value), category labels with
//                 counts (groups under 10 never sent); results the engine computed (sites per
//                 tier, Explore patterns, the planner's index settings and gates); one site's
//                 driver breakdown, renamed "Site A".
//   Never         rows, cells, sample values, site names, IDs, addresses, coordinates, free
//                 text, per-site values of carried columns, the file name. Nothing below puts
//                 them in the payload: the file name is never read at all, and cells are read
//                 only to count blanks, distinct values, percentiles and category sizes.
//
// Only type imports here, so Node runs this file as it is in the tests.

import type { ColumnEntry, Explanation, ExploreResult, IndexResult, RunResult, TableInput } from '../engine/protocol';

export const LIMITS = {
  labelChars: 64,
  columns: 80,
  categoriesPerColumn: 20,
  /** Groups smaller than this are never sent, as label or count. */
  minGroup: 10,
  /** Percentiles need at least this many readable values. */
  minValues: 10,
  cards: 12,
  cardColumns: 4,
  criteria: 20,
  refusals: 20,
  tiers: 8,
  drivers: 40,
  questionChars: 1000,
  assistantChars: 4000,
  historyTurns: 14,
  /** The server's request size limit; the oldest turns are dropped to stay under it. */
  bodyBytes: 32 * 1024,
  /** Room kept for the question and the request's own fields. */
  questionBytes: 4 * 1024,
} as const;

export type Role =
  | 'identifier' | 'name' | 'category' | 'ordinal' | 'flag' | 'count' | 'measure' | 'score' | 'percentage'
  | 'money' | 'date' | 'year' | 'latitude' | 'longitude' | 'address' | 'text' | 'unknown';

/** Only the header, role and blank share travel for these: their values identify places or people. */
export const HEADER_ONLY_ROLES: readonly Role[] = ['identifier', 'name', 'latitude', 'longitude', 'address', 'text', 'date', 'unknown'];
export const CATEGORY_ROLES: readonly Role[] = ['category', 'ordinal', 'flag'];
export const NUMERIC_ROLES: readonly Role[] = ['count', 'measure', 'score', 'percentage', 'money', 'year'];
export const ROLES: readonly Role[] = [...HEADER_ONLY_ROLES, ...CATEGORY_ROLES, ...NUMERIC_ROLES];

/**
 * Header words that mark a column as identifying whatever role it was given, so a column called
 * "latitude" or "site name" marked as a measure or category still sends only its header. A
 * guard against a wrong role, not a replacement for one. The server holds the same list.
 */
export const SENSITIVE_HEADER_WORDS: readonly string[] = [
  'id', 'ids', 'uuid', 'guid', 'key', 'name', 'names', 'lat', 'latitude', 'lon', 'lng', 'long', 'longitude',
  'coord', 'coords', 'coordinate', 'coordinates', 'geometry', 'geom', 'wkt', 'geojson', 'easting', 'northing',
  'address', 'addr', 'street', 'postcode', 'postal', 'zip', 'zipcode', 'email', 'phone', 'tel', 'contact',
  'note', 'notes', 'comment', 'comments', 'description', 'remarks', 'owner', 'parcel', 'apn',
  'x', 'y', 'pointx', 'pointy', 'xcoord', 'ycoord', 'gps', 'location', 'loc', 'geo', 'geopoint', 'fid', 'oid',
  'objectid', 'sitename', 'siteid', 'latdd', 'londd', 'lngdd', 'mail', 'mobile', 'fax', 'dob', 'birth', 'ssn',
  'passport', 'plate', 'vin', 'ip',
];
/** Word endings and beginnings that mark the same: site_id, siteid, sitename, latdd, lon_wgs84. */
export const SENSITIVE_HEADER_SUFFIXES: readonly string[] = ['id', 'name', 'address', 'zip', 'postcode', 'phone', 'email'];
export const SENSITIVE_HEADER_PREFIXES: readonly string[] = ['lat', 'lon', 'lng'];

/**
 * Whether a header names an identifying column. Split into words at anything not a letter or
 * digit and at case changes; each word, and all of them run together, is checked against the
 * list, the endings and the beginnings. Errs towards sharing less. Exactly the server's rule.
 */
function headerWords(header: string): string[] {
  const words = header.normalize('NFKC').replace(/([a-z0-9])([A-Z])/g, '$1 $2').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
  return words.length > 1 ? [...words, words.join('')] : words;
}

export function sensitiveHeader(header: string): boolean {
  // The header as written and as it travels (hidden characters removed), so a hidden character
  // can neither split a word apart nor run two together unseen.
  const raw = String(header ?? '');
  const candidates = [...headerWords(raw), ...headerWords(sanitizeLabel(raw)), ...headerWords(raw.replace(HIDDEN, ''))];
  return candidates.some((w) => SENSITIVE_HEADER_WORDS.includes(w)
    || SENSITIVE_HEADER_SUFFIXES.some((s) => w.endsWith(s))
    || SENSITIVE_HEADER_PREFIXES.some((p) => w.startsWith(p)));
}

export type Cardinality = 'one value' | '2 to 5' | '6 to 20' | '21 to 100' | 'over 100';

export function cardinality(distinct: number): Cardinality {
  if (distinct <= 1) return 'one value';
  if (distinct <= 5) return '2 to 5';
  if (distinct <= 20) return '6 to 20';
  if (distinct <= 100) return '21 to 100';
  return 'over 100';
}

// Removed outright: default-ignorable code points (zero-width characters, variation selectors,
// U+034F, the Hangul fillers, bidirectional controls, tag characters), format characters, the
// braille blank U+2800 and U+FFFC. Turned into spaces: controls, private use, surrogates,
// unassigned, line and paragraph separators. The same classes as the server.
const HIDDEN = /[\p{Default_Ignorable_Code_Point}\p{Cf}\u034f\u115f\u1160\u3164\uffa0\ufe00-\ufe0f\u{E0100}-\u{E01EF}\u2800\ufffc]/gu;
const SPACING = /[\p{Cc}\p{Co}\p{Cs}\p{Cn}\u2028\u2029]/gu;
const LEADING_FORMULA = /^[\s=+\-@]+/u;

/**
 * A header or label as it may travel: no invisible characters, single spaces, no leading
 * = + - @, no [[ ]], < > or backticks, at most 64 characters. Exactly the server's rule.
 */
export function sanitizeLabel(raw: unknown): string {
  let s = String(raw ?? '');
  for (let i = 0, prev: string | null = null; i < 4 && s !== prev; i += 1) {
    prev = s;
    s = s.normalize('NFKC').replace(HIDDEN, '').replace(SPACING, ' ');
  }
  s = s.replace(/\[\[|\]\]/g, ' ').replace(/[<>`]/g, ' ');
  s = s.replace(/\s+/gu, ' ').trim();
  let before: string;
  do { before = s; s = s.replace(LEADING_FORMULA, ''); } while (s !== before);
  if ([...s].length > LIMITS.labelChars) s = [...s].slice(0, LIMITS.labelChars).join('').trim();
  return s;
}

/** x rounded to `digits` significant figures. */
export function roundSig(x: number, digits: number): number {
  if (!Number.isFinite(x) || x === 0) return x === 0 ? 0 : x;
  return Number(x.toPrecision(digits));
}

/** A share from 0 to 1, rounded to 2 decimal places. */
export function roundShare(x: number): number {
  return Math.round(Math.min(1, Math.max(0, x)) * 100) / 100;
}

/** A short machine word as the server accepts it, or null. */
export function slug(raw: unknown): string | null {
  const s = String(raw ?? '').toLowerCase().replace(/[^a-z0-9_-]+/g, '_').replace(/^[^a-z]+/, '').slice(0, 40);
  return /^[a-z][a-z0-9_-]{0,39}$/.test(s) ? s : null;
}

// ---------------------------------------------------------------- the payload's shape

type Direction = 'higher_better' | 'lower_better' | 'neither';
type Kind = 'linear' | 'threshold' | 'target' | 'ordinal';
type Part = 'demand' | 'feasibility' | 'safety' | 'equity';

export interface AppState {
  step: string;
  hasRun: boolean;
  engine: 'real' | 'stand-in';
  rows?: number;
  columns?: number;
}

export interface SharedColumn {
  header: string;
  role: Role;
  blankShare: number;
  distinct: Cardinality;
  unit?: string;
  direction?: Direction;
  scale?: [number, number];
  p10?: number;
  p50?: number;
  p90?: number;
  categories?: { label: string; count: number }[];
  hiddenCategories?: number;
}

export interface ExploreCardShared {
  kind: string;
  columns: string[];
  n: number;
  reliability: string;
  effect?: { name: string; value: number; low?: number; high?: number };
  q?: number;
}

export interface Shared {
  columns?: SharedColumn[];
  readiness?: { sites: number; tiers: { tier: string; count: number }[]; highConfidence?: number; starterPorts?: number; pathwayPorts?: number };
  explore?: { checked: number; passed: number; cards: ExploreCardShared[] };
  index?: { criteria: { column: string; direction: Direction; weight: number; kind: Kind }[]; refused: boolean; refusals?: string[]; ranked?: number; unranked?: number };
  site?: { label: 'Site A'; score: number; confidence?: 'High' | 'Medium' | 'Low'; drivers: { label: string; part: Part; points: number; max: number; missing: boolean }[] };
}

export interface Context { app: AppState; shared?: Shared }

/** What the planner chose to include, in the consent step. */
export interface ShareChoice {
  columns: boolean;
  readiness: boolean;
  explore: boolean;
  index: boolean;
  /** One site's breakdown (the explanation passed in), renamed Site A. */
  site: boolean;
  /** Column names (as in the file) the planner withheld. */
  withheld: string[];
}

export interface PayloadInputs {
  step: string;
  engine: 'real' | 'stand-in';
  table: TableInput | null;
  entries: ColumnEntry[] | null;
  run: RunResult | null;
  explore: ExploreResult | null;
  index: IndexResult | null;
  /** The explanation of the one site the planner asked about, if any. */
  site: Explanation | null;
  /** That site's confidence level, from the run. */
  siteConfidence?: 'High' | 'Medium' | 'Low' | null;
}

// ---------------------------------------------------------------- always

export function buildAppState(i: Pick<PayloadInputs, 'step' | 'engine' | 'table' | 'run'>): AppState {
  const app: AppState = { step: i.step, hasRun: !!i.run, engine: i.engine };
  if (i.table) { app.rows = i.table.rows.length; app.columns = i.table.columns.length; }
  return app;
}

// ---------------------------------------------------------------- with consent

const DIRECTIONS: readonly string[] = ['higher_better', 'lower_better', 'neither'];
const KINDS: readonly string[] = ['linear', 'threshold', 'target', 'ordinal'];
const PARTS: readonly string[] = ['demand', 'feasibility', 'safety', 'equity'];

const isRole = (r: unknown): r is Role => typeof r === 'string' && (ROLES as readonly string[]).includes(r);
const isDirection = (d: unknown): d is Direction => typeof d === 'string' && DIRECTIONS.includes(d);
const whole = (x: unknown): number | undefined => (typeof x === 'number' && Number.isFinite(x) && x >= 0 ? Math.round(x) : undefined);
const finite = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x);

/** A cell read as a number the way the dictionary reads the column, or null. */
export function readNumber(cell: string, decimal: '.' | ',' | null | undefined): number | null {
  let t = cell.trim().replace(/[\s$€£%]/g, '');
  if (!t) return null;
  t = decimal === ',' ? t.replace(/\./g, '').replace(',', '.') : t.replace(/,/g, '');
  if (!/^-?\d+(\.\d+)?$/.test(t)) return null;
  const v = Number(t);
  return Number.isFinite(v) ? v : null;
}

/** The q-th quantile (0..1) of sorted values, by linear interpolation between ranks. */
export function quantile(sorted: number[], q: number): number {
  const at = (sorted.length - 1) * q;
  const lo = Math.floor(at);
  const hi = Math.ceil(at);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (at - lo);
}

function column(table: TableInput, index: number, entry: ColumnEntry | undefined): SharedColumn {
  const header = sanitizeLabel(table.columns[index]) || `Column ${index + 1}`;
  const role: Role = entry && isRole(entry['evsient:role']) ? entry['evsient:role'] : 'unknown';
  const cells = table.rows.map((r) => String(r[index] ?? '').trim());
  const filled = cells.filter((c) => c !== '');
  const counts = new Map<string, number>();
  for (const c of filled) counts.set(c, (counts.get(c) ?? 0) + 1);
  const out: SharedColumn = {
    header, role,
    blankShare: roundShare(cells.length ? (cells.length - filled.length) / cells.length : 0),
    distinct: cardinality(counts.size),
  };
  // Without a dictionary entry nothing says what the values are, so only the header travels;
  // the same for identifying roles and headers that name identifying columns.
  if (!entry || HEADER_ONLY_ROLES.includes(role) || sensitiveHeader(String(table.columns[index] ?? '')) || sensitiveHeader(header)) return out;

  const unit = entry['evsient:unit'] ? sanitizeLabel(entry['evsient:unit']) : '';
  if (unit) out.unit = unit;
  const direction = entry['evsient:direction'];
  if (isDirection(direction)) out.direction = direction;
  // The declared scale comes from the header or the unit (a 1 to 5 score, a percentage), never
  // from the values, so it says nothing about the smallest or largest cell.
  const range = entry['evsient:range'];
  if (Array.isArray(range) && range.length === 2 && finite(range[0]) && finite(range[1])) out.scale = [roundSig(range[0], 3), roundSig(range[1], 3)];

  if (NUMERIC_ROLES.includes(role)) {
    const decimal = entry['evsient:reading']?.decimalSeparator;
    const values = filled.map((c) => readNumber(c, decimal)).filter((v): v is number => v !== null).sort((a, b) => a - b);
    if (values.length >= LIMITS.minValues) {
      out.p10 = roundSig(quantile(values, 0.1), 2);
      out.p50 = roundSig(quantile(values, 0.5), 2);
      out.p90 = roundSig(quantile(values, 0.9), 2);
    }
  }
  if (CATEGORY_ROLES.includes(role)) {
    const big = [...counts.entries()]
      .filter(([, n]) => n >= LIMITS.minGroup)
      .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
    const shown = big
      .map(([label, count]) => ({ label: sanitizeLabel(label), count }))
      .filter((g) => g.label !== '')
      .slice(0, LIMITS.categoriesPerColumn);
    out.categories = shown;
    out.hiddenCategories = counts.size - shown.length;
  }
  return out;
}

function readiness(run: RunResult): NonNullable<Shared['readiness']> {
  const byTier = new Map<string, number>();
  for (const s of run.sites) {
    const tier = sanitizeLabel(s.tier) || 'No tier';
    byTier.set(tier, (byTier.get(tier) ?? 0) + 1);
  }
  const out: NonNullable<Shared['readiness']> = {
    sites: run.sites.length,
    tiers: [...byTier.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1)).slice(0, LIMITS.tiers).map(([tier, count]) => ({ tier, count })),
  };
  const hc = whole(run.totals?.highConfidenceSites);
  const sp = whole(run.totals?.starterPorts2026);
  const pp = whole(run.totals?.pathwayPorts);
  if (hc !== undefined) out.highConfidence = hc;
  if (sp !== undefined) out.starterPorts = sp;
  if (pp !== undefined) out.pathwayPorts = pp;
  return out;
}

function explore(result: ExploreResult, withheld: Set<string>): NonNullable<Shared['explore']> {
  const cards: ExploreCardShared[] = [];
  for (const c of result.cards ?? []) {
    if (cards.length >= LIMITS.cards) break;
    const cols = Array.isArray(c.columns) ? c.columns : [];
    if (cols.some((name) => withheld.has(name)) || cols.length > LIMITS.cardColumns) continue;
    const kind = slug(c.kind);
    const reliability = slug(c.reliability);
    const headers = cols.map((name) => sanitizeLabel(name));
    if (!kind || !reliability || headers.some((h) => !h)) continue;
    // The card's sentence and footer are not sent: they are written from the file and can carry
    // category text that was never checked for group size. Its site IDs are never sent.
    const card: ExploreCardShared = { kind, columns: headers, n: whole(c.n) ?? 0, reliability };
    if (finite(c.q)) card.q = roundSig(c.q, 2);
    const e = c.effect;
    const effectName = e ? slug(e.name) : null;
    if (e && effectName && finite(e.value)) {
      card.effect = { name: effectName, value: roundSig(e.value, 3) };
      if (finite(e.low)) card.effect.low = roundSig(e.low, 3);
      if (finite(e.high)) card.effect.high = roundSig(e.high, 3);
    }
    cards.push(card);
  }
  return { checked: whole(result.checked) ?? 0, passed: whole(result.passed) ?? 0, cards };
}

function index(result: IndexResult, withheld: Set<string>): NonNullable<Shared['index']> {
  const criteria: NonNullable<Shared['index']>['criteria'] = [];
  for (const c of result.spec?.criteria ?? []) {
    if (criteria.length >= LIMITS.criteria || withheld.has(c.column)) continue;
    const column = sanitizeLabel(c.column);
    const kind = c.value?.kind;
    if (!column || !isDirection(c.direction) || !finite(c.weight) || !KINDS.includes(kind)) continue;
    criteria.push({ column, direction: c.direction, weight: roundSig(c.weight, 3), kind });
  }
  // The index's name is the planner's own free text, so it is not sent.
  const out: NonNullable<Shared['index']> = { criteria, refused: !!result.refused };
  const refusals = (result.refusals ?? []).map((r) => slug(r.code)).filter((r): r is string => !!r).slice(0, LIMITS.refusals);
  if (refusals.length) out.refusals = refusals;
  if (Array.isArray(result.sites)) out.ranked = result.sites.length;
  if (Array.isArray(result.unranked)) out.unranked = result.unranked.length;
  return out;
}

function site(x: Explanation, confidence: PayloadInputs['siteConfidence']): NonNullable<Shared['site']> {
  const drivers: NonNullable<Shared['site']>['drivers'] = [];
  for (const d of x.drivers ?? []) {
    if (drivers.length >= LIMITS.drivers) break;
    const label = sanitizeLabel(d.label);
    if (!label || !PARTS.includes(d.subscore) || !finite(d.points) || !finite(d.max)) continue;
    drivers.push({ label, part: d.subscore, points: roundSig(d.points, 3), max: roundSig(d.max, 3), missing: !!d.absent });
  }
  // Never the site's ID, name, rank or inputs: only its score and how the drivers add up to it.
  const out: NonNullable<Shared['site']> = { label: 'Site A', score: roundSig(x.score, 3), drivers };
  if (confidence === 'High' || confidence === 'Medium' || confidence === 'Low') out.confidence = confidence;
  return out;
}

/** The consented tier, built from what the engine computed and the planner chose. */
export function buildShared(i: PayloadInputs, choice: ShareChoice): Shared | undefined {
  const withheld = new Set(choice.withheld);
  const shared: Shared = {};
  const table = i.table;
  if (choice.columns && table) {
    const cols: SharedColumn[] = [];
    table.columns.forEach((name, n) => {
      if (withheld.has(name) || cols.length >= LIMITS.columns) return;
      cols.push(column(table, n, i.entries?.find((e) => e.name === name)));
    });
    if (cols.length) shared.columns = cols;
  }
  if (choice.readiness && i.run) shared.readiness = readiness(i.run);
  if (choice.explore && i.explore) shared.explore = explore(i.explore, withheld);
  if (choice.index && i.index) shared.index = index(i.index, withheld);
  if (choice.site && i.site && finite(i.site.score)) shared.site = site(i.site, i.siteConfidence);
  return Object.keys(shared).length ? shared : undefined;
}

/** Everything the next question would carry besides its own words. */
export function buildContext(i: PayloadInputs, choice: ShareChoice | null): Context {
  const app = buildAppState(i);
  const shared = choice ? buildShared(i, choice) : undefined;
  return shared ? { app, shared } : { app };
}

const bytes = (v: unknown) => new TextEncoder().encode(JSON.stringify(v)).length;

/** Whether a context leaves room in a request for a question (the consent step checks this). */
export function contextFits(context: Context): boolean {
  return bytes(context) <= LIMITS.bodyBytes - LIMITS.questionBytes;
}

interface Turnish { role: string; text: string }

/**
 * The request with the oldest turns of the conversation dropped, a question and its answer at
 * a time, until it fits the server's size limit; null when it does not fit even with none.
 */
export function fitRequest<T extends { history: Turnish[] }>(body: T): T | null {
  let history = body.history.slice(-LIMITS.historyTurns);
  if (history.length % 2) history = history.slice(1);
  for (;;) {
    const candidate = { ...body, history };
    if (bytes(candidate) <= LIMITS.bodyBytes) return candidate;
    if (!history.length) return null;
    history = history.slice(2);
  }
}
