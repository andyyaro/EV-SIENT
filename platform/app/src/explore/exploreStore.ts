// Explore's own state, kept apart from the planner session (state/store.ts) so the readiness
// steps never depend on it. The engine computes every number: this file asks for the column
// dictionary and the scan, remembers which dictionary the scan used, and forgets both when the
// planner's file changes.

import { create } from 'zustand';
import { getEngine } from '../engine/client';
import type { ColumnEntry, ExploreResult, TableInput } from '../engine/protocol';
import { useSession } from '../state/store';

export type ExploreStatus = 'idle' | 'busy' | 'done' | 'error' | 'unavailable';

interface ExploreState {
  status: ExploreStatus;
  result: ExploreResult | null;
  /** The dictionary entries the scan read, for labels, roles and what is confirmed. */
  entries: ColumnEntry[];
  /** True when the column dictionary changed after the scan: the patterns are out of date. */
  changed: boolean;
  error: string | null;
  /** Run the scan on the file and dictionary the engine holds now. */
  scan(): Promise<void>;
  /** Ask the engine for the dictionary again and mark the scan out of date if it changed. */
  compareDictionary(): Promise<void>;
}

/** The stand-in engine's refusal (engine/mock.ts): it never reads the planner's own columns. */
const REAL_ONLY = 'Your columns are read with the real engine only.';

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** The dictionary as the engine reads it, without the reading report (which never changes alone). */
function dictionaryKey(entries: ColumnEntry[]): string {
  return JSON.stringify(entries.map((e) => {
    const { ['evsient:reading']: _reading, ['evsient:evidence']: _evidence, ...rest } = e;
    return rest;
  }));
}

/** The file the current scan belongs to; any other file means start again. */
let scannedTable: TableInput | null = null;
let scannedKey: string | null = null;
/** Bumped whenever the file changes, so an answer for an older file is dropped. */
let generation = 0;

async function engineReady(): Promise<void> {
  const session = useSession.getState();
  await session.bootEngine();
  const boot = useSession.getState().boot;
  if (boot.status === 'error') throw new Error(boot.message);
}

export const useExplore = create<ExploreState>((set, get) => ({
  status: 'idle',
  result: null,
  entries: [],
  changed: false,
  error: null,

  async scan() {
    const table = useSession.getState().table;
    if (!table || get().status === 'busy') return;
    const engine = getEngine();
    if (engine.kind === 'mock') { set({ status: 'unavailable', result: null, error: null }); return; }
    const gen = generation;
    set({ status: 'busy', error: null });
    try {
      await engineReady();
      const columns = await engine.columns();
      const result = await engine.explore({});
      if (gen !== generation) return;
      scannedTable = table;
      scannedKey = dictionaryKey(columns.entries);
      set({ status: 'done', result, entries: columns.entries, changed: false });
    } catch (e) {
      if (gen !== generation) return;
      const text = message(e);
      if (text === REAL_ONLY) set({ status: 'unavailable', result: null, error: null });
      else set({ status: 'error', error: text });
    }
  },

  async compareDictionary() {
    if (get().status !== 'done' || scannedKey === null) return;
    const gen = generation;
    try {
      const columns = await getEngine().columns();
      if (gen !== generation) return;
      if (dictionaryKey(columns.entries) !== scannedKey) set({ changed: true });
    } catch { /* the scan on screen stays; Check Again reports any problem */ }
  },
}));

/** Whether the scan on screen is for the file the planner has open now. */
export function scanIsForCurrentFile(): boolean {
  return scannedTable !== null && scannedTable === useSession.getState().table;
}

// A different file (or a new project) makes the patterns meaningless: forget them.
useSession.subscribe((now, before) => {
  if (now.table === before.table) return;
  generation++;
  scannedTable = null;
  scannedKey = null;
  useExplore.setState({ status: 'idle', result: null, entries: [], changed: false, error: null });
});
