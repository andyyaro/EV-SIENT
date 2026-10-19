// The real engine: Pyodide plus fcf_m2 in a module Web Worker (./engine.worker.ts), reached
// through Comlink. The worker speaks browser_api's JSON strings; this side parses them.
//
// cancel() ends the worker outright (Python cannot be interrupted mid-run) and the next call
// starts a fresh one. The engine's session dies with it, so the last uploaded table and the
// planner's mapping and accepted public values are replayed into the new worker before a call
// that needs them.

import * as Comlink from 'comlink';
import type {
  AcceptDetails, AcceptResult, ColumnChange, ColumnsResult, ExploreOptions, ExploreResult,
  IndexResult, IndexSpec, IndexValidation, BootProgress, CheckResult, EngineClient, Explanation, FieldCatalog,
  FillRequest, OutputFiles, Proposal, ProvenanceRecord, ProvenanceRequest, RemapRequest, RunOptions,
  RunResult, RuntimeInfo, StabilityOptions, StabilityResult, TableInput,
} from './protocol';
import { EngineError } from './protocol';
import type { EngineWorkerApi } from './engine.worker';

interface Live {
  worker: Worker;
  api: Comlink.Remote<EngineWorkerApi>;
  booted: Promise<RuntimeInfo> | null;
  /** Session state the worker holds; false after a fresh start until replayed. */
  hasSession: boolean;
}

export function createWorkerEngine(): EngineClient {
  let live: Live | null = null;
  let onProgress: ((p: BootProgress) => void) | undefined;
  let lastTable: string | null = null;
  let lastRemap: string | null = null;
  let lastFill: string | null = null;
  /** The confirmed column dictionary as a Table Schema, replayed into a fresh worker. */
  let lastColumns: string | null = null;
  const pending = new Set<(e: unknown) => void>();

  function spawn(): Live {
    const worker = new Worker(new URL('./engine.worker.ts', import.meta.url), { type: 'module', name: 'evsient-engine' });
    return { worker, api: Comlink.wrap<EngineWorkerApi>(worker), booted: null, hasSession: false };
  }

  /** Runs `fn`, rejecting it at once if cancel() ends the worker under it. */
  function guarded<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      pending.add(reject);
      fn().then(resolve, (e) => reject(translate(e))).finally(() => pending.delete(reject));
    });
  }

  // Comlink rebuilds a thrown Error with its name and message, so an EngineError keeps its kind.
  function translate(e: unknown): unknown {
    if (e instanceof Error && e.name === 'EngineError') return new EngineError(e.message);
    return e;
  }

  function boot(): Promise<RuntimeInfo> {
    if (!live) live = spawn();
    const current = live;
    if (!current.booted) {
      const progress = Comlink.proxy((p: BootProgress) => onProgress?.(p));
      current.booted = guarded(() => current.api.boot(progress)).then((json) => JSON.parse(json) as RuntimeInfo);
      current.booted.catch(() => { if (live === current) { current.worker.terminate(); live = null; } });
    }
    return current.booted;
  }

  /** The booted worker, with the planner's file and mapping back in place when `session`. */
  async function ready(session: boolean): Promise<Live> {
    await boot();
    const current = live!;
    if (session && !current.hasSession && lastTable) {
      await guarded(() => current.api.propose(lastTable!));
      if (lastRemap) await guarded(() => current.api.remap(lastRemap!));
      if (lastFill) await guarded(() => current.api.fill(lastFill!));
      if (lastColumns) await guarded(() => current.api.columns_restore(lastColumns!));
      current.hasSession = true;
    }
    return current;
  }

  async function call<T>(session: boolean, fn: (api: Comlink.Remote<EngineWorkerApi>) => Promise<string>): Promise<T> {
    const current = await ready(session);
    return JSON.parse(await guarded(() => fn(current.api))) as T;
  }

  return {
    kind: 'worker',
    boot(progress) {
      onProgress = progress;
      return boot();
    },
    fields: () => call<FieldCatalog>(false, (api) => api.fields()),
    async reset() {
      lastTable = lastRemap = lastFill = lastColumns = null;
      await call(false, (api) => api.reset());
    },
    async propose(table: TableInput) {
      const json = JSON.stringify(table);
      const result = await call<Proposal>(false, (api) => api.propose(json));
      lastTable = json;
      lastRemap = lastFill = lastColumns = null;
      if (live) live.hasSession = true;
      return result;
    },
    async remap(request: RemapRequest) {
      const json = JSON.stringify(request);
      const result = await call<Proposal>(true, (api) => api.remap(json));
      lastRemap = json;
      lastFill = null;
      return result;
    },
    check: () => call<CheckResult>(true, (api) => api.check()),
    async fill(request: FillRequest) {
      const json = JSON.stringify(request);
      const result = await call<CheckResult>(true, (api) => api.fill(json));
      lastFill = request.fills.length ? json : null;
      return result;
    },
    accept: (details: AcceptDetails) => call<AcceptResult>(true, (api) => api.accept(JSON.stringify(details ?? {}))),
    run: (options?: RunOptions) => call<RunResult>(true, (api) => api.run(JSON.stringify(options ?? {}))),
    explain: (siteId: string) => call<Explanation>(true, (api) => api.explain(siteId)),
    stability: (options?: StabilityOptions) => call<StabilityResult>(true, (api) => api.stability(JSON.stringify(options ?? {}))),
    provenance: (cell: ProvenanceRequest) => call<ProvenanceRecord>(true, (api) => api.provenance(JSON.stringify(cell))),
    outputFiles: () => call<OutputFiles>(true, (api) => api.output_files()),
    async columns() {
      const result = await call<ColumnsResult>(true, (api) => api.columns());
      lastColumns = JSON.stringify(result.tableSchema);
      return result;
    },
    async columnsConfirm(changes: ColumnChange[]) {
      const result = await call<ColumnsResult>(true, (api) => api.columns_confirm(JSON.stringify({ changes })));
      lastColumns = JSON.stringify(result.tableSchema);
      return result;
    },
    async columnsRestore(tableSchema: Record<string, unknown>) {
      const result = await call<ColumnsResult>(true, (api) => api.columns_restore(JSON.stringify(tableSchema)));
      lastColumns = JSON.stringify(result.tableSchema);
      return result;
    },
    explore: (options?: ExploreOptions) => call<ExploreResult>(true, (api) => api.explore(JSON.stringify(options ?? {}))),
    indexValidate: (spec: IndexSpec) => call<IndexValidation>(true, (api) => api.index_validate(JSON.stringify(spec))),
    indexRun: (spec: IndexSpec, options?: { populationColumn?: string }) =>
      call<IndexResult>(true, (api) => api.index_run(JSON.stringify({ spec, options: options ?? {} }))),
    cancel() {
      if (!live) return;
      live.worker.terminate();
      live = null;
      const stopped = new DOMException('The run was stopped.', 'AbortError');
      for (const reject of pending) reject(stopped);
      pending.clear();
    },
  };
}
