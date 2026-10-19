// One planner session: the steps, what each has produced, and where the planner is.
// Screens read from here and call these actions; only the actions talk to the engine.

import { create } from 'zustand';
import { getEngine } from '../engine/client';
import type {
  AcceptDetails, AcceptResult, BootProgress, CheckResult, FieldCatalog, FieldFill, MatchStatus, Proposal, RunOptions,
  RunResult, RuntimeInfo, TableInput,
} from '../engine/protocol';
import type { HubLookup, HubProgress } from '../hub/hub';
import { carriedFrom, type CarriedColumns, type CarriedFilter } from '../results/carried';
import type { ProjectSnapshot } from '../report/projectTypes';
import { restoreColumns, type ColumnDictionary } from '../columns/dictionary';

export type StepKey = 'start' | 'upload' | 'map' | 'check' | 'fill' | 'run' | 'results' | 'report' | 'explore';

export const STEPS: { key: StepKey; label: string; icon: string; short: string }[] = [
  { key: 'start', label: 'Start', short: 'Start', icon: 'house' },
  { key: 'upload', label: 'Upload', short: 'Upload', icon: 'square.and.arrow.up' },
  { key: 'map', label: 'Map Columns', short: 'Map', icon: 'list.bullet' },
  { key: 'check', label: 'Check', short: 'Check', icon: 'checkmark.circle' },
  { key: 'fill', label: 'Public Data', short: 'Data', icon: 'globe' },
  { key: 'run', label: 'Run', short: 'Run', icon: 'play.fill' },
  { key: 'results', label: 'Results', short: 'Results', icon: 'chart.bar' },
  { key: 'explore', label: 'Explore', short: 'Explore', icon: 'magnifyingglass' },
  { key: 'report', label: 'Report', short: 'Report', icon: 'doc' },
];

/** The one configuration the engine runs today. Other presets need engine changes first. */
export const CONFIGURATION = "Balanced (the study's weights)";

export type BootState =
  | { status: 'idle' }
  | { status: 'booting'; progress: BootProgress }
  | { status: 'ready'; info: RuntimeInfo }
  | { status: 'error'; message: string };

export interface Session {
  step: StepKey;
  boot: BootState;
  fields: FieldCatalog | null;
  table: TableInput | null;
  proposal: Proposal | null;
  check: CheckResult | null;
  details: AcceptDetails;
  accepted: AcceptResult | null;
  run: RunResult | null;
  /** Set when an input changed after the last run: results are shown as Out of Date. */
  staleReason: string | null;
  busy: null | 'propose' | 'remap' | 'check' | 'hub' | 'fill' | 'accept' | 'run' | 'restore';
  error: string | null;
  /** A plain status message for the planner (not an error), shown once and dismissible. */
  notice: string | null;
  selectedSiteId: string | null;
  /** Up to three site IDs to compare side by side. */
  compare: string[];
  /** field -> column the planner confirmed (Confirm, Accept All Matched, choosing it, a reused or restored mapping). */
  confirmed: Record<string, string>;
  /** field -> column the engine guessed at upload and asked the planner to check. */
  guessed: Record<string, string>;
  /** What the public data hub proposed, once the planner asked (DEC-025). Never sent anywhere. */
  hub: HubLookup | null;
  hubProgress: HubProgress | null;
  /** field -> the planner's answer to the hub's proposal. Only 'use' reaches the engine. */
  publicChoice: Record<string, 'use' | 'skip'>;
  /** The public values the engine holds now, exactly as last sent to it. */
  publicFills: FieldFill[];
  /** The file's columns the model does not read, kept with the last run's sites (never scored). */
  carried: CarriedColumns | null;
  /** How Results shows them: the table's extra columns, its order and filter, the map's colours. */
  yourColumns: YourColumnsView;
  /** The planner's confirmed column dictionary and labels (src/columns), saved in the project file. */
  columnDictionary: ColumnDictionary | null;
}

export interface YourColumnsView {
  shown: string[];
  /** null is rank order. */
  sort: { column: string; dir: 1 | -1 } | null;
  filter: CarriedFilter | null;
  mapColour: string | null;
}

const noView: YourColumnsView = { shown: [], sort: null, filter: null, mapColour: null };

interface Actions {
  go(step: StepKey): void;
  bootEngine(): Promise<void>;
  loadTable(table: TableInput): Promise<void>;
  remap(mapping: Record<string, string | null>): Promise<void>;
  /** Set one field's column (or null, "not in this file") and send the WHOLE mapping. Returns the field the column was moved from, if any. */
  chooseColumn(field: string, column: string | null): Promise<string | null>;
  confirmMatch(field: string): void;
  /** Confirm every suggested match still marked Check This Match. */
  confirmAll(): void;
  /** Use a whole remembered mapping, as the planner's own choice. */
  applyMapping(mapping: Record<string, string | null>): Promise<void>;
  runCheck(): Promise<void>;
  setDetails(details: AcceptDetails): void;
  /** Fetch the hub's packs for these sites and work out its proposals. Only on the planner's request. */
  lookUpPublicData(): Promise<void>;
  /** Use or skip the hub's values for one field; sends the WHOLE set the planner now uses. */
  choosePublicData(field: string, choice: 'use' | 'skip'): Promise<void>;
  runModel(options?: RunOptions): Promise<void>;
  cancelRun(): void;
  restoreProject(snapshot: ProjectSnapshot): Promise<void>;
  selectSite(siteId: string | null): void;
  toggleCompare(siteId: string): void;
  setYourColumns(view: Partial<YourColumnsView>): void;
  clearError(): void;
  clearNotice(): void;
  newProject(): Promise<void>;
}

const initial: Omit<Session, 'boot' | 'fields'> = {
  step: 'start', table: null, proposal: null, check: null, details: {}, accepted: null, run: null,
  staleReason: null, busy: null, error: null, notice: null, selectedSiteId: null, compare: [],
  confirmed: {}, guessed: {}, hub: null, hubProgress: null, publicChoice: {}, publicFills: [],
  carried: null, yourColumns: noView,
  columnDictionary: null,
};

/** The view kept across runs, less any column the new run no longer carries. */
function keepView(view: YourColumnsView, carried: CarriedColumns | null): YourColumnsView {
  const has = new Set(carried?.columns.map((c) => c.name) ?? []);
  return {
    shown: view.shown.filter((c) => has.has(c)),
    sort: view.sort && has.has(view.sort.column) ? view.sort : null,
    filter: view.filter && has.has(view.filter.column) ? view.filter : null,
    mapColour: view.mapColour && has.has(view.mapColour) ? view.mapColour : null,
  };
}

/** Everything public data adds, cleared whenever the file or its column matches change. */
const noPublicData = { hub: null, hubProgress: null, publicChoice: {}, publicFills: [] };

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** Today in the planner's own time zone, as YYYY-MM-DD. */
export const today = () => new Date().toLocaleDateString('en-CA');

/** Every field the model reads, in the engine's order. */
export function fieldNames(s: Pick<Session, 'fields' | 'proposal'>): string[] {
  if (s.fields) return s.fields.fields.map((f) => f.name);
  return s.proposal ? Object.keys(s.proposal.status) : [];
}

/** The whole mapping as the planner has it now: every field, null where it is not in this file. */
export function fullMapping(s: Pick<Session, 'fields' | 'proposal'>): Record<string, string | null> {
  const out: Record<string, string | null> = {};
  for (const name of fieldNames(s)) out[name] = s.proposal?.mapping[name] ?? null;
  return out;
}

/**
 * Matched / Check This Match / Not Matched, as the planner sees it. The engine marks a guess or a
 * unit conversion "check" after upload; after any change it reports every chosen pair as matched,
 * so the app keeps its own record of what the planner has actually confirmed.
 */
export function matchStatus(s: Pick<Session, 'proposal' | 'confirmed' | 'guessed'>, field: string): MatchStatus {
  const column = s.proposal?.mapping[field];
  if (!column) return 'unmatched';
  if (s.confirmed[field] === column) return 'matched';
  if (s.proposal?.conversions[field] != null) return 'check';
  if (s.guessed[field] === column) return 'check';
  if (s.proposal?.status[field] === 'check') return 'check';
  return 'matched';
}

export function pendingMatches(s: Pick<Session, 'fields' | 'proposal' | 'confirmed' | 'guessed'>): string[] {
  return fieldNames(s).filter((f) => matchStatus(s, f) === 'check');
}

/**
 * The sites that could take a public value, by field: every site for a field the file does not
 * have, otherwise the sites whose cell is empty (and those already filled from public data).
 */
export function publicNeeds(s: Pick<Session, 'check'>): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  const check = s.check;
  if (!check) return out;
  const absent = new Set(check.absentFromFile);
  for (const field of check.publicFill.fields) {
    const sites = check.rows
      .filter((r) => r.siteId && (absent.has(field) || r.missing.includes(field) || r.filled.includes(field)))
      .map((r) => r.siteId);
    if (sites.length) out[field] = sites;
  }
  return out;
}

/** The fills the engine should hold for these choices: each used field's proposed values, with their source. */
export function fillsFor(s: Pick<Session, 'check' | 'hub'>, choice: Record<string, 'use' | 'skip'>): FieldFill[] {
  const hub = s.hub;
  if (!hub) return [];
  const needs = publicNeeds(s);
  const out: FieldFill[] = [];
  for (const [field, answer] of Object.entries(choice)) {
    const spec = hub.manifest.fields[field];
    const proposed = hub.proposals[field];
    if (answer !== 'use' || !spec || !proposed) continue;
    const values: Record<string, number> = {};
    for (const siteId of needs[field] ?? []) {
      const p = proposed[siteId];
      if (p && 'value' in p) values[siteId] = p.value;
    }
    if (!Object.keys(values).length) continue;
    const data = hub.manifest.datasets[spec.primary];
    out.push({
      field, values,
      source: {
        hubVersion: hub.manifest.hubVersion, dataset: spec.primary, title: data?.title ?? spec.sourceLabel,
        vintage: spec.vintage, sourceDate: spec.sourceDate, licence: spec.licence, method: spec.method,
        url: data?.landing,
      },
    });
  }
  return out;
}

/** Whether a step can be opened yet, and if not, why, in the planner's words. */
export function stepGate(s: Session, step: StepKey): { open: boolean; reason?: string } {
  switch (step) {
    case 'start':
    case 'upload':
      return { open: true };
    case 'map':
      return s.proposal ? { open: true } : { open: false, reason: 'Upload a file first.' };
    case 'check': {
      if (!s.proposal) return { open: false, reason: 'Upload a file first.' };
      const n = pendingMatches(s).length;
      return n ? { open: false, reason: `Confirm or change the ${n === 1 ? 'match' : `${n} matches`} marked Check This Match first.` } : { open: true };
    }
    case 'fill':
    case 'run': {
      const before = stepGate(s, 'check');
      if (!before.open) return before;
      if (!s.check) return { open: false, reason: 'Check the file first.' };
      if (s.check.counts.mustFix > 0 || s.proposal?.refused) return { open: false, reason: 'Fix the items marked Must Fix first.' };
      return { open: true };
    }
    case 'results':
    case 'report':
      return s.run ? { open: true } : { open: false, reason: 'Run the model first.' };
    case 'explore':
      // Explore reads the uploaded file's own columns; it needs no run and no confirmed directions.
      return s.proposal ? { open: true } : { open: false, reason: 'Upload a file first.' };
  }
}

/** Whether the planner has finished a step, for the step list's Done mark. */
export function stepDone(s: Session, step: StepKey): boolean {
  switch (step) {
    case 'start': return !!s.table;
    case 'upload': return !!s.proposal && !s.proposal.refused;
    case 'map': return !!s.proposal && pendingMatches(s).length === 0 && !!s.check;
    case 'check': return !!s.check && s.check.counts.mustFix === 0 && !s.proposal?.refused;
    case 'fill': return s.publicFills.length > 0 || Object.keys(s.publicChoice).length > 0;
    case 'run': return !!s.run && !s.staleReason;
    default: return false;
  }
}

function readHash(): StepKey | null {
  const key = location.hash.replace(/^#\/?/, '') as StepKey;
  return STEPS.some((s) => s.key === key) ? key : null;
}

export const useSession = create<Session & Actions>((set, get) => {
  const fail = (e: unknown) => set({ error: message(e), busy: null });
  const markStale = (reason: string) => { if (get().run) set({ staleReason: reason }); };
  let bootPromise: Promise<void> | null = null;
  /** Bumped by Cancel and New Project, so an answer that arrives afterwards is ignored. */
  let generation = 0;

  async function ensureBooted(): Promise<void> {
    await get().bootEngine();
    const b = get().boot;
    if (b.status === 'error') throw new Error(b.message);
  }

  /**
   * Before any call that needs the planner's file. After Cancel the worker is gone; the engine
   * client starts a fresh one and gives it the last file and mapping again by itself, so all the
   * store has to do is boot it.
   */
  const ensureEngineSession = ensureBooted;

  return {
    ...initial,
    boot: { status: 'idle' },
    fields: null,

    go(step) {
      const gate = stepGate(get(), step);
      if (!gate.open) return;
      set({ step, error: null });
      if (readHash() !== step) history.pushState(null, '', `#/${step}`);
      window.scrollTo({ top: 0 });
    },

    bootEngine() {
      const b = get().boot.status;
      if (b === 'ready') return Promise.resolve();
      if (b === 'booting' && bootPromise) return bootPromise;
      const engine = getEngine();
      set({ boot: { status: 'booting', progress: { stage: 'runtime', fraction: 0, message: 'Preparing the model on this device' } } });
      bootPromise = (async () => {
        try {
          const info = await engine.boot((progress) => set({ boot: { status: 'booting', progress } }));
          const fields = await engine.fields();
          set({ boot: { status: 'ready', info }, fields });
        } catch (e) {
          set({ boot: { status: 'error', message: message(e) } });
        } finally {
          bootPromise = null;
        }
      })();
      return bootPromise;
    },

    async loadTable(table) {
      const gen = generation;
      set({ busy: 'propose', error: null });
      try {
        await ensureBooted();
        const engine = getEngine();
        const proposal = await engine.propose(table);
        // The file's own summary needs the row check (how many rows have a location), so it runs now.
        const check = await engine.check();
        if (gen !== generation) return;
        const guessed: Record<string, string> = {};
        for (const [field, status] of Object.entries(proposal.status)) {
          if (status === 'check' && proposal.mapping[field]) guessed[field] = proposal.mapping[field];
        }
        markStale('You uploaded a different file.');
        set({ table, proposal, check, guessed, confirmed: {}, accepted: null, busy: null, ...noPublicData, columnDictionary: null });
      } catch (e) { if (gen === generation) fail(e); }
    },

    async remap(mapping) {
      const gen = generation;
      set({ busy: 'remap', error: null });
      try {
        await ensureEngineSession();
        const proposal = await getEngine().remap({ mapping });
        if (gen !== generation) return;
        markStale('You changed how columns are matched.');
        // The engine forgets public values on a new mapping (a filled field may now be in the file).
        set({ proposal, check: null, accepted: null, busy: null, ...noPublicData });
      } catch (e) { if (gen === generation) fail(e); }
    },

    async chooseColumn(field, column) {
      const s = get();
      const mapping = fullMapping(s);
      let movedFrom: string | null = null;
      if (column) {
        for (const [f, c] of Object.entries(mapping)) {
          if (f !== field && c === column) { mapping[f] = null; movedFrom = f; }
        }
      }
      mapping[field] = column;
      await get().remap(mapping);
      const after = get();
      if (after.error || !after.proposal) return null;
      const confirmed = { ...after.confirmed };
      // Choosing a column is a confirmation, unless the engine now converts its units: the planner
      // is shown the conversion and asked to confirm that separately.
      if (column && after.proposal.conversions[field] == null) confirmed[field] = column;
      else delete confirmed[field];
      if (movedFrom) delete confirmed[movedFrom];
      set({ confirmed });
      return movedFrom;
    },

    confirmMatch(field) {
      const s = get();
      const column = s.proposal?.mapping[field];
      if (!column) return;
      set({ confirmed: { ...s.confirmed, [field]: column } });
    },

    confirmAll() {
      const s = get();
      const confirmed = { ...s.confirmed };
      for (const field of pendingMatches(s)) {
        const column = s.proposal?.mapping[field];
        if (column) confirmed[field] = column;
      }
      set({ confirmed });
    },

    async applyMapping(mapping) {
      const s = get();
      const whole = { ...fullMapping(s), ...mapping };
      await get().remap(whole);
      const after = get();
      if (after.error || !after.proposal) return;
      const confirmed: Record<string, string> = {};
      for (const [f, c] of Object.entries(after.proposal.mapping)) confirmed[f] = c;
      set({ confirmed });
    },

    async runCheck() {
      const gen = generation;
      set({ busy: 'check', error: null });
      try {
        await ensureEngineSession();
        const check = await getEngine().check();
        if (gen === generation) set({ check, busy: null });
      } catch (e) { if (gen === generation) fail(e); }
    },

    setDetails(details) {
      const before = get().details;
      const next = { ...before, ...details };
      const changed = (Object.keys(details) as (keyof AcceptDetails)[]).some((k) => (before[k] ?? '') !== (next[k] ?? ''));
      if (!changed) return;
      markStale('You changed the source details.');
      set({ details: next, accepted: null });
    },

    async lookUpPublicData() {
      const gen = generation;
      const s = get();
      if (!s.check) return;
      const needs = publicNeeds(s);
      const wanted = new Set(Object.values(needs).flat());
      // Only sites that could take a value are looked up, so only their counties are fetched.
      const sites = s.check.rows.filter((r) => wanted.has(r.siteId)).map((r) => ({ siteId: r.siteId, lat: r.lat, lon: r.lon }));
      set({ busy: 'hub', error: null, hubProgress: null });
      try {
        const { lookUp } = await import('../hub/hub');
        const hub = await lookUp(sites, Object.keys(needs), (hubProgress) => { if (gen === generation) set({ hubProgress }); });
        if (gen !== generation) return;
        // Values kept from an older hub release (an opened project) are set aside, never swapped
        // for the new release's: the planner chooses again, field by field.
        const older = get().publicFills.filter((f) => f.source.hubVersion !== hub.manifest.hubVersion);
        if (!older.length) { set({ hub, hubProgress: null, busy: null }); return; }
        const kept = get().publicFills.filter((f) => !older.includes(f));
        const publicChoice = { ...get().publicChoice };
        for (const f of older) delete publicChoice[f.field];
        set({ busy: 'fill' });
        const check = await getEngine().fill({ fills: kept });
        if (gen !== generation) return;
        markStale('Public values from an older hub release were set aside.');
        set({
          hub, check, publicChoice, publicFills: kept, accepted: null, hubProgress: null, busy: null,
          notice: `The values from public data release ${older[0].source.hubVersion} were set aside. Choose again for release ${hub.manifest.hubVersion}.`,
        });
      } catch (e) { if (gen === generation) { set({ hubProgress: null }); fail(e); } }
    },

    async choosePublicData(field, choice) {
      const gen = generation;
      const s = get();
      const publicChoice = { ...s.publicChoice, [field]: choice };
      const fills = fillsFor(s, publicChoice);
      if (JSON.stringify(fills) === JSON.stringify(s.publicFills)) { set({ publicChoice }); return; }
      set({ busy: 'fill', error: null });
      try {
        await ensureEngineSession();
        const check = await getEngine().fill({ fills });
        if (gen !== generation) return;
        markStale('You changed which public values are used.');
        set({ check, publicChoice, publicFills: fills, accepted: null, busy: null });
      } catch (e) { if (gen === generation) fail(e); }
    },

    async runModel(options) {
      const gen = generation;
      set({ busy: 'accept', error: null });
      try {
        await ensureEngineSession();
        const engine = getEngine();
        const accepted = await engine.accept(get().details);
        if (gen !== generation) return;
        set({ accepted, busy: 'run' });
        const run = await engine.run({ asOf: options?.asOf ?? today() });
        if (gen !== generation) return;
        // Taken with the mapping the run used, so a later change in Map Columns leaves these results alone.
        const s = get();
        const carried = carriedFrom(s.table, s.proposal?.mapping);
        set({
          run, carried, yourColumns: keepView(s.yourColumns, carried), staleReason: null, busy: null,
          selectedSiteId: run.sites[0]?.siteId ?? null, compare: [],
        });
      } catch (e) { if (gen === generation) fail(e); }
    },

    cancelRun() {
      generation++;
      getEngine().cancel();
      bootPromise = null;
      // The worker is gone with everything it held; the next call starts a fresh one, which the
      // engine client gives the file and mapping again. The previous run, if any, stays on screen.
      set({ busy: null, boot: { status: 'idle' }, accepted: null, notice: 'The run was cancelled. Nothing was changed.' });
    },

    async restoreProject(snapshot) {
      const gen = ++generation;
      set({ ...initial, busy: 'restore' });
      try {
        await ensureBooted();
        const engine = getEngine();
        try { await engine.reset(); } catch { /* a fresh session either way */ }
        await engine.propose(snapshot.table);
        const proposal = await engine.remap({ mapping: snapshot.mapping });
        // Public values are restored as they were saved, with their sources; the hub is not asked again.
        const publicFills = snapshot.publicData?.fills ?? [];
        const check = publicFills.length ? await engine.fill({ fills: publicFills }) : await engine.check();
        if (gen !== generation) return;
        const confirmed: Record<string, string> = { ...proposal.mapping };
        const publicChoice = Object.fromEntries(publicFills.map((f) => [f.field, 'use' as const]));
        set({ table: snapshot.table, proposal, check, confirmed, guessed: {}, details: { ...snapshot.details }, publicFills, publicChoice });
        // The planner's column dictionary, read again against the reopened file (src/columns).
        const columns = await restoreColumns(snapshot.columns);
        if (gen !== generation) return;
        set({ columnDictionary: columns.dictionary });
        if (proposal.refused || check.counts.mustFix > 0) {
          set({ busy: null, notice: 'This project file was opened, but its file has items marked Must Fix, so the model was not run.' });
          get().go('check');
          return;
        }
        const accepted = await engine.accept(snapshot.details);
        if (gen !== generation) return;
        set({ accepted, busy: 'run' });
        const run = await engine.run({ asOf: snapshot.manifest.asOf });
        if (gen !== generation) return;
        const b = get().boot;
        const nowVersion = b.status === 'ready' ? b.info.engine.version : '';
        const savedVersion = snapshot.manifest.engine.version;
        const versionNote = nowVersion && savedVersion && nowVersion !== savedVersion
          ? ` It was saved with model version ${savedVersion} and re-run with version ${nowVersion}, so some figures may differ.`
          : '';
        // An older project file has no saved columns; they are read again from its table.
        const carried = snapshot.carried ?? carriedFrom(snapshot.table, proposal.mapping);
        set({
          run, carried, staleReason: null, busy: null, selectedSiteId: run.sites[0]?.siteId ?? null, compare: [],
          notice: `Opened ${snapshot.manifest.name}. The model was run again on this device, with data confidence judged as of ${snapshot.manifest.asOf}.${versionNote}${columns.note}`,
        });
        get().go('results');
      } catch (e) { if (gen === generation) fail(e); }
    },

    selectSite(siteId) { set({ selectedSiteId: siteId }); },

    toggleCompare(siteId) {
      const c = get().compare;
      if (c.includes(siteId)) set({ compare: c.filter((x) => x !== siteId) });
      else if (c.length < 3) set({ compare: [...c, siteId] });
    },

    setYourColumns(view) { set({ yourColumns: { ...get().yourColumns, ...view } }); },

    clearError() { set({ error: null }); },
    clearNotice() { set({ notice: null }); },

    async newProject() {
      generation++;
      try { if (get().boot.status === 'ready') await getEngine().reset(); } catch { /* a fresh session either way */ }
      set({ ...initial });
      history.pushState(null, '', '#/start');
    },
  };
});

// Back and forward buttons move between steps the planner has already opened.
window.addEventListener('popstate', () => {
  const key = readHash();
  if (key && stepGate(useSession.getState(), key).open) useSession.setState({ step: key });
});
const first = readHash();
if (first && first !== 'start') history.replaceState(null, '', '#/start');
