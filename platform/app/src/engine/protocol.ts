// The message protocol between the app and the engine (platform/PROTOCOL.md).
// Every shape here is what src/fcf_m2/browser_api.py returns, field for field. Python is the
// source of truth: change it there first, then here, and bump PROTOCOL_VERSION in both.

export const PROTOCOL_VERSION = 1;

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
}

export interface CheckResult {
  rows: CheckRow[];
  refusals: Finding[];
  counts: { total: number; ready: number; missing: number; mustFix: number; located: number };
  /** Scored fields this file does not have at all. */
  absentFromFile: string[];
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
export interface EngineClient {
  readonly kind: 'worker' | 'mock';
  boot(onProgress?: (p: BootProgress) => void): Promise<RuntimeInfo>;
  fields(): Promise<FieldCatalog>;
  reset(): Promise<void>;
  propose(table: TableInput): Promise<Proposal>;
  remap(request: RemapRequest): Promise<Proposal>;
  check(): Promise<CheckResult>;
  accept(details: AcceptDetails): Promise<AcceptResult>;
  run(options?: RunOptions): Promise<RunResult>;
  explain(siteId: string): Promise<Explanation>;
  outputFiles(): Promise<OutputFiles>;
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
