// Engine reads the Results and Report screens share: one site's explanation, every site's
// explanations, and the run's output files, each fetched once per run and kept in memory.
// Also small readers for the output files the screens quote (cohort, manifest, scenario table).

import { useEffect, useState } from 'react';
import { getEngine } from '../engine/client';
import type { Explanation, OutputFiles, RunResult } from '../engine/protocol';

const explainCache = new Map<string, Promise<Explanation>>();
const filesCache = new Map<string, Promise<OutputFiles>>();

export function fetchExplain(runId: string, siteId: string): Promise<Explanation> {
  const key = `${runId}\u0000${siteId}`;
  let p = explainCache.get(key);
  if (!p) {
    p = getEngine().explain(siteId);
    p.catch(() => explainCache.delete(key));
    explainCache.set(key, p);
  }
  return p;
}

export function fetchOutputFiles(runId: string): Promise<OutputFiles> {
  let p = filesCache.get(runId);
  if (!p) {
    p = getEngine().outputFiles();
    p.catch(() => filesCache.delete(runId));
    filesCache.set(runId, p);
  }
  return p;
}

export type Loadable<T> = { status: 'loading' } | { status: 'ready'; value: T } | { status: 'error'; message: string };

function useLoad<T>(key: string | null, load: () => Promise<T>): Loadable<T> {
  const [state, setState] = useState<{ key: string | null; value: Loadable<T> }>({ key: null, value: { status: 'loading' } });
  useEffect(() => {
    if (!key) return;
    let live = true;
    load().then(
      (value) => { if (live) setState({ key, value: { status: 'ready', value } }); },
      (e: unknown) => { if (live) setState({ key, value: { status: 'error', message: e instanceof Error ? e.message : String(e) } }); },
    );
    return () => { live = false; };
  }, [key]);
  return state.key === key ? state.value : { status: 'loading' };
}

export function useExplain(run: RunResult | null, siteId: string | null): Loadable<Explanation> {
  const key = run && siteId ? `${run.runId}\u0000${siteId}` : null;
  return useLoad(key, () => fetchExplain(run!.runId, siteId!));
}

/** Every site's explanation, in rank order. Requested one at a time: the worker answers in turn. */
export function useAllExplains(run: RunResult | null): Loadable<Explanation[]> {
  return useLoad(run ? `${run.runId}\u0000all` : null, async () => {
    const out: Explanation[] = [];
    for (const s of run!.sites) out.push(await fetchExplain(run!.runId, s.siteId));
    return out;
  });
}

export function useOutputFiles(run: RunResult | null): Loadable<OutputFiles> {
  return useLoad(run ? run.runId : null, () => fetchOutputFiles(run!.runId));
}

// ---------- Readers for the output files ----------

/** RFC 4180 CSV: quoted fields, doubled quotes, CRLF or LF. */
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { cell += '"'; i++; } else quoted = false;
      } else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter((r) => r.length > 1 || r[0] !== '');
  if (!head) return [];
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}

function json<T>(files: OutputFiles | null, path: string): T | null {
  const text = files?.files[path];
  if (!text) return null;
  try { return JSON.parse(text) as T; } catch { return null; }
}

export interface Cohort {
  cohort_id?: string;
  jurisdiction?: string;
  source_date?: string;
  source_org?: string;
  source_file?: string;
  source_sha256?: string;
  accepted_utc?: string;
}

export interface Manifest {
  contract_version?: string;
  model_version?: string;
  run_id?: string;
  generated_utc?: string;
  inputs?: Record<string, string>;
  tables?: Record<string, string>;
  grid_factor?: { source?: string; value_lb_per_mwh?: number; vintage?: string };
  conventions?: { baseline_year?: number; horizons?: number[]; cases?: string[]; discount_rate_real?: number };
}

export interface Assumptions {
  energy_per_session_kwh?: { value?: number; label?: string };
  demand_model?: { status?: string; provenance?: string };
  economics?: { tariff_usd_per_kwh?: number; discount_rate_real?: number; hardware_usd_per_port?: number; provenance?: string };
  emissions?: { grid_factor_value?: number; grid_factor_units?: string; grid_factor_source?: string; grid_factor_vintage?: string };
  growth_multipliers?: Record<string, number>;
  growth_provenance?: string;
  trigger_policy?: { policy_status?: string; utilization_threshold?: number; wait_threshold_min?: number };
  capacity?: string;
}

export const readCohort = (f: OutputFiles | null) => json<Cohort>(f, 'inputs/cohort.json');
export const readManifest = (f: OutputFiles | null) => json<Manifest>(f, 'results/contract/contract_manifest.json');
export const readAssumptions = (f: OutputFiles | null) => json<Assumptions>(f, 'results/contract/assumptions.json');

/** One public dataset the planner accepted values from (inputs/public_data_fills.csv, DEC-025). */
export interface PublicSource {
  title: string;
  vintage: string;
  sourceDate: string;
  licence: string;
  hubVersion: string;
  fields: string[];
  cells: number;
}

/** The public values in this run, grouped by the dataset they came from. Empty when there are none. */
export function readPublicSources(files: OutputFiles | null): PublicSource[] {
  const text = files?.files['inputs/public_data_fills.csv'];
  if (!text) return [];
  const out = new Map<string, PublicSource>();
  for (const r of parseCsv(text)) {
    const key = `${r.hub_version}\u0000${r.dataset}`;
    let s = out.get(key);
    if (!s) {
      s = { title: r.title ?? '', vintage: r.vintage ?? '', sourceDate: r.source_date ?? '', licence: r.licence ?? '', hubVersion: r.hub_version ?? '', fields: [], cells: 0 };
      out.set(key, s);
    }
    if (!s.fields.includes(r.field)) s.fields.push(r.field);
    s.cells++;
  }
  return [...out.values()];
}

export interface CapacityEvidence {
  basis: string;
  source: string;
  confidence: string;
}

/** Each site's capacity evidence as the contract's scenario table states it (its first row per site). */
export function readCapacity(files: OutputFiles | null): Map<string, CapacityEvidence> {
  const out = new Map<string, CapacityEvidence>();
  const text = files?.files['results/contract/scenario_table.csv'];
  if (!text) return out;
  for (const r of parseCsv(text)) {
    if (!out.has(r.site_id)) {
      out.set(r.site_id, { basis: r.capacity_basis ?? '', source: r.capacity_source ?? '', confidence: r.capacity_confidence ?? '' });
    }
  }
  return out;
}

/** The four rungs of the capacity-evidence ladder, strongest first, and which engine bases sit on each. */
export const CAPACITY_LADDER: { key: string; label: string; bases: string[] }[] = [
  { key: 'utility', label: 'Utility Confirmed', bases: ['verified_utility'] },
  { key: 'survey', label: 'On-Site Survey', bases: ['verified_facility', 'engineering_estimate'] },
  { key: 'hosting', label: 'Hosting-Capacity Map', bases: [] },
  { key: 'proxy', label: 'Proxy or Unknown', bases: ['planning_proxy', 'placeholder', 'unknown', ''] },
];

export function ladderRung(basis: string): number {
  const i = CAPACITY_LADDER.findIndex((r) => r.bases.includes(basis));
  return i < 0 ? CAPACITY_LADDER.length - 1 : i;
}
