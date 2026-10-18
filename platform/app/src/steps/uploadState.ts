// The file being read on the Upload step: the parsed workbook, the chosen sheet and heading row.
// It lives in memory only (never in storage) and is shared with Start, which sends the Example City
// sample through exactly the same path.

import { create } from 'zustand';
import {
  buildTable, defaultHeaderRow, defaultSheet, parseFile, type ParsedFile, type TableBuild,
} from '../lib/parseTable';
import { useSession } from '../state/store';

export const SAMPLE_URL = '/samples/example-city.csv';
export const TEMPLATE_URL = '/samples/template.csv';

interface UploadState {
  parsed: ParsedFile | null;
  sheet: number;
  headerRow: number;
  build: TableBuild | null;
  /** True for the Example City sample, which is invented data. */
  sample: boolean;
  reading: boolean;
  readError: string | null;
  /** The planner asked to choose a different file: show the drop zone even though a table is loaded. */
  replacing: boolean;
  ingest(file: File, options?: { sample?: boolean }): Promise<void>;
  loadSample(): Promise<void>;
  chooseSheet(index: number): Promise<void>;
  chooseHeaderRow(row: number): Promise<void>;
  /** Forget the file being read; by default also show the drop zone over a loaded table. */
  clear(replacing?: boolean): void;
  cancelReplace(): void;
}

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

export const useUpload = create<UploadState>((set, get) => {
  async function rebuild(parsed: ParsedFile, sheet: number, headerRow: number) {
    const build = buildTable(parsed, sheet, headerRow);
    set({ sheet, headerRow, build });
    if (build.table) await useSession.getState().loadTable(build.table);
  }

  return {
    parsed: null, sheet: 0, headerRow: 0, build: null, sample: false, reading: false, readError: null, replacing: false,

    async ingest(file, options) {
      set({ reading: true, readError: null });
      try {
        const parsed = await parseFile(file);
        const sheet = defaultSheet(parsed);
        set({ parsed, sample: !!options?.sample, reading: false, replacing: false });
        await rebuild(parsed, sheet, defaultHeaderRow(parsed.sheets[sheet]));
      } catch (e) {
        set({ reading: false, readError: message(e) });
      }
    },

    async loadSample() {
      set({ reading: true, readError: null });
      try {
        const response = await fetch(SAMPLE_URL);
        if (!response.ok) throw new Error('The Example City sample could not be loaded. Check your connection and try again.');
        const blob = await response.blob();
        await get().ingest(new File([blob], 'example-city.csv', { type: 'text/csv' }), { sample: true });
      } catch (e) {
        set({ reading: false, readError: message(e) });
      }
    },

    async chooseSheet(index) {
      const { parsed } = get();
      if (!parsed) return;
      await rebuild(parsed, index, defaultHeaderRow(parsed.sheets[index]));
    },

    async chooseHeaderRow(row) {
      const { parsed, sheet } = get();
      if (!parsed) return;
      await rebuild(parsed, sheet, row);
    },

    clear(replacing = true) { set({ parsed: null, build: null, sample: false, readError: null, sheet: 0, headerRow: 0, replacing }); },
    cancelReplace() { set({ replacing: false, readError: null }); },
  };
});
