// The message protocol between the app and the engine (platform/PROTOCOL.md).
// Every shape here is what src/fcf_m2/browser_api.py returns, field for field. Python is the
// source of truth: change it there first, then here, and bump PROTOCOL_VERSION in both.

export const PROTOCOL_VERSION = 2;

export type Severity = 'refusal' | 'warning' | 'note';

export interface Finding {
  severity: Severity;
  field: string;
  explain: string;
  detail: string;
}

export interface EngineInfo {
  protocol: number;
  python: string;
  platform: string;
  packages: Record<string, string>;
}

/** What the worker adds about itself when it starts. */
export interface RuntimeInfo extends EngineInfo {
  pyodide: string;
  engine: { version: string; sha256: string };
  timingsMs: { runtime: number; packages: number; engine: number };
}

export type FieldKind = 'number' | 'flag' | 'coordinate' | 'text';

export interface FieldInfo {
  name: string;
  label: string;
  unit: string;
  what: string;
  if_missing: string;
  group: string;
  groupLabel: string;
  kind: FieldKind;
  scored: boolean;
  required: boolean;
}

export interface FieldCatalog {
  fields: FieldInfo[];
  groups: Record<string, string>;
}

/** The uploaded table. Every cell is the text the planner typed: nothing is re-typed in JS. */
export interface TableInput {
  fileName: string;
  sheet?: string;
  columns: string[];
  rows: string[][];
}

export interface ColumnSummary {
  name: string;
  samples: string[];
  blank: number;
  distinct: number;
}

/** Matched: exact or chosen by the planner. Check: a guess or a unit conversion to confirm. */
export type MatchStatus = 'matched' | 'check' | 'unmatched';

export interface Proposal {
  rowCount: number;
  columns: ColumnSummary[];
  /** canonical field -> supplied column */
  mapping: Record<string, string>;
  /** canonical field -> multiplier applied to reach the model's unit */
  conversions: Record<string, number>;
  matchScore: Record<string, number>;
  status: Record<string, MatchStatus>;
  /** canonical field -> cells the field cannot read (scored as absent); only fields with some */
  unreadable?: Record<string, number>;
  absent: string[];
  findings: Finding[];
  refused: boolean;
  completeness: number;
  summary: string;
}

export interface RemapRequest {
  /** The WHOLE mapping as the planner wants it; null means "not in this file". */
  mapping: Record<string, string | null>;
}

export type RowStatus = 'ready' | 'missing' | 'must_fix';

export interface CheckRow {
  /** File row number; the header is row 1. */
  row: number;
  siteId: string;
  siteName: string;
  status: RowStatus;
  mustFix: string[];
  /** Scored fields that are blank or unreadable in this row (scored as absent, never defaulted). */
  missing: string[];
  /** Fields filled at this site from public data the planner accepted (no longer missing). */
  filled: string[];
  /** The site's coordinates as the model reads them; null when not supplied or not usable. */
  lat: number | null;
  lon: number | null;
}

/** Where a public value came from. Written beside every filled value, in the cohort and the report. */
export interface FillSource {
  hubVersion: string;
  /** Hub dataset id, e.g. "lodes-wac-va". */
  dataset: string;
  title: string;
  vintage: string;
  /** YYYY-MM-DD: the date data confidence ages the value from. */
  sourceDate: string;
  licence: string;
  /** One sentence: how the value was worked out. */
  method: string;
  url?: string;
}

/** Public values for one field, by site ID, as the planner accepted them. */
export interface FieldFill {
  field: string;
  values: Record<string, number>;
  source: FillSource;
}

export interface FillRequest {
  /** The WHOLE set the planner wants; an empty list removes every public value. */
  fills: FieldFill[];
}

export interface CheckResult {
  rows: CheckRow[];
  refusals: Finding[];
  counts: { total: number; ready: number; missing: number; mustFix: number; located: number };
  /** Scored fields this file does not have at all. */
  absentFromFile: string[];
  publicFill: {
    /** Fields public data may fill: a site's surroundings, never the site itself. */
    fields: string[];
    /** field -> number of sites filled */
    filled: Record<string, number>;
    sources: Record<string, FillSource>;
  };
}

export interface AcceptDetails {
  jurisdiction?: string;
  sourceOrg?: string;
  /** YYYY-MM-DD, or empty for "unstated" (which costs confidence). */
  sourceDate?: string;
  reviewer?: string;
}

export interface LedgerEntry {
  canonical_field: string;
  action: string;
  reason: string;
  detail: string;
}

export interface AcceptResult {
  siteCount: number;
  ledger: LedgerEntry[];
  summary: string;
  /** Cells filled from public data. */
  publicCells: number;
}

export interface RunOptions {
  /** YYYY-MM-DD the data confidence is judged on. Defaults to today. */
  asOf?: string;
}

export type ConfidenceLevel = 'High' | 'Medium' | 'Low';

export interface SiteResult {
  siteId: string;
  name: string;
  type: string;
  lat: number | null;
  lon: number | null;
  rank: number;
  score: number;
  /** The engine's tier text, e.g. "Tier 2 - promising candidate, refine data". */
  tier: string;
  subscores: { demand: number; feasibility: number; safety: number; equity: number };
  confidence: { score: number | null; level: ConfidenceLevel | null; breakdown: Record<string, number> };
  portsNow: number | null;
  pathwayPorts: number | null;
  capacityCap: number | null;
  plan: string | null;
  expectedSessionsDay: number | null;
  utilization: number | null;
  meanWaitMin: number | null;
  installCostUsd: number | null;
  electricalRisk: string | null;
  absentFields: string[];
}

export interface HorizonRow {
  siteId: string;
  year: number;
  case: string;
  portsActive: number;
  portsPathway: number;
  capacityCap: number;
  strategy: string;
}

export interface RunResult {
  runId: string;
  generatedAt: string;
  asOf: string;
  mode: string;
  elapsedSec: number;
  totals: { sites: number; starterPorts2026: number; pathwayPorts: number; highConfidenceSites: number };
  /** The engine's one-line statement of what these numbers are and are not. Always shown. */
  claims: string;
  defaults: string[];
  notes: string[];
  costsWithheld: string[];
  subscoreWeights: Record<string, number>;
  sites: SiteResult[];
  horizons: HorizonRow[];
}

export interface Driver {
  key: string;
  label: string;
  subscore: 'demand' | 'feasibility' | 'safety' | 'equity';
  /** Share of the whole score this driver can carry (subscore weight x driver weight). */
  weight: number;
  /** 0..1 after "lower is better" inversion; 0 when nobody recorded the value. */
  credit: number;
  inverted: boolean;
  /** Readiness points this driver adds. The drivers sum to the score. */
  points: number;
  /** Points at full credit. */
  max: number;
  absent: boolean;
  inputs: string[];
}

export interface Explanation {
  siteId: string;
  name: string;
  score: number;
  rank: number;
  /** 1, or 0.65 when the site is not recorded as open to the public (demand counted at 65%). */
  accessAdjustment: number;
  subscores: { key: string; label: string; weight: number; value: number; points: number; max: number }[];
  drivers: Driver[];
}

/** One cell of the run's contract scenario table, e.g. ports_active at 2036 in "base". */
export interface ProvenanceRequest {
  siteId: string;
  horizonYear: number;
  scenario: string;
  column: string;
}

/** provenance.resolve()'s record for one cell, resolved when asked (never precomputed). */
export interface ProvenanceRecord {
  value: number | string | boolean | null;
  column: string;
  table: string;
  row_key: { site_id: string; horizon_year: number; scenario_name: string };
  contract_version: string;
  model_version: string;
  model_mode: string;
  run_id: string;
  generated_at: string;
  engine: string;
  table_sha256: string;
  source_id: string;
  source_date: string;
  assumption_flag: string;
  data_confidence: string;
  capacity_basis: string;
  /** Caveat texts, in full. */
  caveats: string[];
  consumer_rules: string[];
  field_provenance: {
    field_group: string; source_class: string; verification_status: string; source_org: string;
    source_date: string; reviewer: string; assumption_type: string; unresolved: boolean;
  } | null;
  notes: string;
}

export interface OutputFiles {
  /** "results/..." and "inputs/..." paths -> file text */
  files: Record<string, string>;
}

export type BootStage = 'runtime' | 'packages' | 'engine' | 'ready';

export interface BootProgress {
  stage: BootStage;
  /** 0..1 across the whole boot */
  fraction: number;
  /** Plain words for the status line. */
  message: string;
}

/** What the app calls. The worker client and the sample-data stand-in both implement it. */
// ---------- the planner's own columns (docs/FLEXIBLE_ANALYSIS.md) ----------
// The shapes below are the contract's; Python (src/fcf_m2/flex/) is the source of truth.

export type ColumnRole =
  | 'identifier' | 'name' | 'category' | 'ordinal' | 'flag' | 'count' | 'measure' | 'score'
  | 'percentage' | 'money' | 'date' | 'year' | 'latitude' | 'longitude' | 'address' | 'text' | 'unknown';
export type Direction = 'higher_better' | 'lower_better' | 'neither';

export interface ColumnEvidence { signal: string; match?: string; text: string; direction?: Direction }

export interface ReadingPattern { pattern: string; readAs: string; count: number; kind?: string }

export interface ColumnReading {
  cells: number; read: number; missing: number; unreadable: number; ambiguous: number;
  decimalSeparator: '.' | ',' | null;
  patterns: ReadingPattern[];
  patternsNotShown?: number;
  sentinels: { value: string; count: number }[] | string[];
  outOfRange?: number; notWhole?: number; distinct?: number;
  min?: number | string | null; max?: number | string | null;
}

/** One column of the planner's file, as the dictionary reads it (contract section 1). */
export interface ColumnEntry {
  name: string;
  type: string;
  categories?: string[];
  categoriesOrdered?: boolean;
  missingValues?: string[];
  'evsient:role': ColumnRole;
  'evsient:unit': string | null;
  'evsient:range': [number, number] | null;
  'evsient:direction': Direction | null;
  'evsient:modelField': string | null;
  'evsient:evidence': ColumnEvidence[];
  'evsient:agreement': 'agree' | 'conflict' | 'unknown';
  'evsient:provenance': 'inferred' | 'confirmed_by_user';
  'evsient:reading'?: ColumnReading;
  [key: string]: unknown;
}

export interface ColumnsResult {
  entries: ColumnEntry[];
  /** The dictionary as a Frictionless v2 Table Schema, for the project file. */
  tableSchema: Record<string, unknown>;
}

/** One change the planner makes to a column; any subset of the keys (contract section 1). */
export interface ColumnChange {
  column: string;
  role?: ColumnRole;
  unit?: string | null;
  direction?: Direction | null;
  categories?: string[];
  missingValues?: string[];
  range?: [number, number] | null;
  decimalSeparator?: '.' | ',';
  dateFormat?: string;
  confirm?: boolean;
}

/** Explore's answer (contract section 2). Cards describe; nothing here ranks a site. */
export interface ExploreCard {
  id: string;
  kind: string;
  columns: string[];
  sentence: string;
  effect: { name: string; value: number; low: number | null; high: number | null } | null;
  n: number;
  q: number | null;
  reliability: string;
  stratum: string | null;
  chart: Record<string, unknown> | null;
  siteIds: string[];
  footer: string;
  [key: string]: unknown;
}

export interface ExploreResult {
  checked: number;
  passed: number;
  fdr: number;
  minGroup: number;
  health: Record<string, unknown>;
  cards: ExploreCard[];
  [key: string]: unknown;
}

export interface ExploreOptions {
  fdr?: number; minGroup?: number; seed?: number; stratum?: string | null;
  asOf?: string; staleYears?: number; paretoColumns?: string[];
}

/** The planner's own index settings, shaped as a pack (contract section 3). */
export interface IndexSpec {
  pack: 'evsient-custom-index';
  packVersion: string;
  name: string;
  criteria: {
    column: string;
    direction: Direction;
    weight: number;
    value: Record<string, unknown> & { kind: 'linear' | 'threshold' | 'target' | 'ordinal' };
  }[];
  screens: { logic: unknown; reason: string }[];
  missing: 'no_credit';
  minCoverage: number;
  robustness?: { draws: number; spread: number; seed: number };
}

export interface IndexValidation { ok: boolean; refusals: string[]; [key: string]: unknown }

/** The planner's own index (contract section 3). Never official, never on the readiness scale. */
export interface IndexResult {
  official: false;
  name: string;
  badge: string;
  refused: boolean;
  refusals: string[];
  spec: IndexSpec;
  formula: unknown;
  summary: Record<string, unknown>;
  sites: Record<string, unknown>[];
  unranked: Record<string, unknown>[];
  excluded: Record<string, unknown>[];
  rankChanges: unknown[];
  robustness: Record<string, unknown>;
  gatesChecked: unknown;
  comparison?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface EngineClient {
  readonly kind: 'worker' | 'mock';
  boot(onProgress?: (p: BootProgress) => void): Promise<RuntimeInfo>;
  fields(): Promise<FieldCatalog>;
  reset(): Promise<void>;
  propose(table: TableInput): Promise<Proposal>;
  remap(request: RemapRequest): Promise<Proposal>;
  check(): Promise<CheckResult>;
  /** Record the public values the planner accepted; answers with the check again. */
  fill(request: FillRequest): Promise<CheckResult>;
  accept(details: AcceptDetails): Promise<AcceptResult>;
  run(options?: RunOptions): Promise<RunResult>;
  explain(siteId: string): Promise<Explanation>;
  provenance(cell: ProvenanceRequest): Promise<ProvenanceRecord>;
  outputFiles(): Promise<OutputFiles>;
  /** The column dictionary for the uploaded file: proposed the first time, then as confirmed. */
  columns(): Promise<ColumnsResult>;
  columnsConfirm(changes: ColumnChange[]): Promise<ColumnsResult>;
  /** A dictionary saved in a project file, read again against the reopened file. */
  columnsRestore(tableSchema: Record<string, unknown>): Promise<ColumnsResult>;
  explore(options?: ExploreOptions): Promise<ExploreResult>;
  indexValidate(spec: IndexSpec): Promise<IndexValidation>;
  indexRun(spec: IndexSpec, options?: { populationColumn?: string }): Promise<IndexResult>;
  /** Stops a run in progress by ending the worker; the next call starts a fresh one. */
  cancel(): void;
}

/** Errors the engine raises for the planner (ValueError in Python) carry this name. */
export class EngineError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EngineError';
  }
}
