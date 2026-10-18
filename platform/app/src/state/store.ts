// One planner session: the steps, what each has produced, and where the planner is.
// Screens read from here and call these actions; only the actions talk to the engine.

import { create } from 'zustand';
import { getEngine } from '../engine/client';
import type {
  AcceptDetails, AcceptResult, BootProgress, CheckResult, FieldCatalog, Proposal, RunResult,
  RuntimeInfo, TableInput,
} from '../engine/protocol';

export type StepKey = 'start' | 'upload' | 'map' | 'check' | 'run' | 'results' | 'report';

export const STEPS: { key: StepKey; label: string; icon: string; short: string }[] = [
  { key: 'start', label: 'Start', short: 'Start', icon: 'house' },
  { key: 'upload', label: 'Upload', short: 'Upload', icon: 'square.and.arrow.up' },
  { key: 'map', label: 'Map Columns', short: 'Map', icon: 'list.bullet' },
  { key: 'check', label: 'Check', short: 'Check', icon: 'checkmark.circle' },
  { key: 'run', label: 'Run', short: 'Run', icon: 'play.fill' },
  { key: 'results', label: 'Results', short: 'Results', icon: 'chart.bar' },
  { key: 'report', label: 'Report', short: 'Report', icon: 'doc' },
];

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
  busy: null | 'propose' | 'remap' | 'check' | 'accept' | 'run';
  error: string | null;
  selectedSiteId: string | null;
  /** Up to three site IDs to compare side by side. */
  compare: string[];
}

interface Actions {
  go(step: StepKey): void;
  bootEngine(): Promise<void>;
  loadTable(table: TableInput): Promise<void>;
  remap(mapping: Record<string, string | null>): Promise<void>;
  runCheck(): Promise<void>;
  setDetails(details: AcceptDetails): void;
  runModel(): Promise<void>;
  cancelRun(): void;
  selectSite(siteId: string | null): void;
  toggleCompare(siteId: string): void;
  clearError(): void;
  newProject(): Promise<void>;
}

const initial: Omit<Session, 'boot' | 'fields'> = {
  step: 'start', table: null, proposal: null, check: null, details: {}, accepted: null, run: null,
  staleReason: null, busy: null, error: null, selectedSiteId: null, compare: [],
};

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** Whether a step can be opened yet, and if not, why, in the planner's words. */
export function stepGate(s: Session, step: StepKey): { open: boolean; reason?: string } {
  switch (step) {
    case 'start':
    case 'upload':
      return { open: true };
    case 'map':
      return s.proposal ? { open: true } : { open: false, reason: 'Upload a file first.' };
    case 'check':
      return s.proposal ? { open: true } : { open: false, reason: 'Upload a file first.' };
    case 'run':
      if (!s.check) return { open: false, reason: 'Check the file first.' };
      if (s.check.counts.mustFix > 0 || s.proposal?.refused) return { open: false, reason: 'Fix the items marked Must Fix first.' };
      return { open: true };
    case 'results':
    case 'report':
      return s.run ? { open: true } : { open: false, reason: 'Run the model first.' };
  }
}

export function unresolvedMatches(p: Proposal | null): string[] {
  return p ? Object.entries(p.status).filter(([, v]) => v === 'check').map(([k]) => k) : [];
}

function readHash(): StepKey | null {
  const key = location.hash.replace(/^#\/?/, '') as StepKey;
  return STEPS.some((s) => s.key === key) ? key : null;
}

export const useSession = create<Session & Actions>((set, get) => {
  const fail = (e: unknown) => set({ error: message(e), busy: null });
  const markStale = (reason: string) => { if (get().run) set({ staleReason: reason }); };

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

    async bootEngine() {
      const b = get().boot.status;
      if (b === 'booting' || b === 'ready') return;
      const engine = getEngine();
      set({ boot: { status: 'booting', progress: { stage: 'runtime', fraction: 0, message: 'Preparing the model on this device' } } });
      try {
        const info = await engine.boot((progress) => set({ boot: { status: 'booting', progress } }));
        const fields = await engine.fields();
        set({ boot: { status: 'ready', info }, fields });
      } catch (e) {
        set({ boot: { status: 'error', message: message(e) } });
      }
    },

    async loadTable(table) {
      set({ busy: 'propose', error: null });
      try {
        await get().bootEngine();
        const proposal = await getEngine().propose(table);
        markStale('You uploaded a different file.');
        set({ table, proposal, check: null, accepted: null, busy: null });
      } catch (e) { fail(e); }
    },

    async remap(mapping) {
      set({ busy: 'remap', error: null });
      try {
        const proposal = await getEngine().remap({ mapping });
        markStale('You changed how columns are matched.');
        set({ proposal, check: null, accepted: null, busy: null });
      } catch (e) { fail(e); }
    },

    async runCheck() {
      set({ busy: 'check', error: null });
      try { set({ check: await getEngine().check(), busy: null }); } catch (e) { fail(e); }
    },

    setDetails(details) {
      markStale('You changed the source details.');
      set({ details: { ...get().details, ...details }, accepted: null });
    },

    async runModel() {
      set({ busy: 'accept', error: null });
      try {
        const engine = getEngine();
        const accepted = await engine.accept(get().details);
        set({ accepted, busy: 'run' });
        const run = await engine.run({ asOf: new Date().toISOString().slice(0, 10) });
        set({ run, staleReason: null, busy: null, selectedSiteId: run.sites[0]?.siteId ?? null, compare: [] });
      } catch (e) { fail(e); }
    },

    cancelRun() {
      getEngine().cancel();
      set({ busy: null, boot: { status: 'idle' }, accepted: null });
    },

    selectSite(siteId) { set({ selectedSiteId: siteId }); },

    toggleCompare(siteId) {
      const c = get().compare;
      if (c.includes(siteId)) set({ compare: c.filter((x) => x !== siteId) });
      else if (c.length < 3) set({ compare: [...c, siteId] });
    },

    clearError() { set({ error: null }); },

    async newProject() {
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
