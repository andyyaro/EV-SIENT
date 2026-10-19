// The planner's column dictionary (docs/FLEXIBLE_ANALYSIS.md section 1) as the app keeps it: the
// engine's Table Schema, plus the labels the planner gives their columns. The engine holds the
// entries; the session keeps the confirmed schema so the project file can carry it, and an opened
// project gives it back to the engine with columnsRestore.
//
// Kept apart from state/store.ts so the store only gains a field and a few lines. These helpers
// are the only code here that calls the engine, as the store's actions do for everything else.

import { getEngine } from '../engine/client';
import type { ColumnChange, ColumnEntry, ColumnsResult } from '../engine/protocol';
import { useSession } from '../state/store';

/** What the session and the project file keep. */
export interface ColumnDictionary {
  /** The engine's Frictionless v2 Table Schema, as it last returned it. */
  tableSchema: Record<string, unknown>;
  /** column name -> the planner's own label for it. Display only; the file is never changed. */
  labels: Record<string, string>;
}

/** inputs/column_dictionary.json in the project file. */
export const DICTIONARY_MEMBER = 'inputs/column_dictionary.json';

export const MAX_LABEL = 80;

const isRecord = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** The engine's message as a sentence the planner reads. */
export function engineMessage(e: unknown): string {
  const text = message(e).trim();
  if (!text) return 'Something went wrong reading your columns.';
  const s = text[0].toUpperCase() + text.slice(1);
  return /[.!?]$/.test(s) ? s : `${s}.`;
}

/** Whether any entry has been confirmed by the planner. Only then is the dictionary worth keeping. */
export function anyConfirmed(entries: ColumnEntry[]): boolean {
  return entries.some((e) => e['evsient:provenance'] === 'confirmed_by_user');
}

function keepLabels(labels: Record<string, string>, entries: ColumnEntry[]): Record<string, string> {
  const names = new Set(entries.map((e) => e.name));
  return Object.fromEntries(Object.entries(labels).filter(([name]) => names.has(name)));
}

/** The dictionary for the uploaded file, as the engine has it now (proposed the first time). */
export async function loadColumns(): Promise<ColumnsResult> {
  return getEngine().columns();
}

/**
 * Send the planner's changes and keep the result. Labels change only after the engine accepts the
 * rest, so a refused change leaves everything as it was.
 */
export async function confirmColumns(changes: ColumnChange[], labels: Record<string, string>): Promise<ColumnsResult> {
  const result = await getEngine().columnsConfirm(changes);
  const before = useSession.getState().columnDictionary?.labels ?? {};
  const merged = { ...before };
  for (const [name, label] of Object.entries(labels)) {
    const clean = label.trim().slice(0, MAX_LABEL);
    if (clean && clean !== name) merged[name] = clean;
    else delete merged[name];
  }
  useSession.setState({
    columnDictionary: anyConfirmed(result.entries)
      ? { tableSchema: result.tableSchema, labels: keepLabels(merged, result.entries) }
      : null,
  });
  return result;
}

// ---------- the project file ----------

/** The schema with each label written as the field's Frictionless `title`. */
export function schemaWithLabels(dictionary: ColumnDictionary): Record<string, unknown> {
  const fields = Array.isArray(dictionary.tableSchema.fields) ? dictionary.tableSchema.fields : [];
  return {
    ...dictionary.tableSchema,
    fields: fields.map((f) => {
      if (!isRecord(f) || typeof f.name !== 'string') return f;
      const { title: _old, ...rest } = f;
      const label = dictionary.labels[f.name];
      return label ? { ...rest, title: label } : rest;
    }),
  };
}

/**
 * What the project file stores. Asked of the engine again first, so the record of which model
 * field each column fills follows the mapping the planner saved; the session's copy otherwise.
 */
export async function columnsForProject(dictionary: ColumnDictionary): Promise<Record<string, unknown>> {
  try {
    const now = await getEngine().columns();
    if (anyConfirmed(now.entries)) return schemaWithLabels({ tableSchema: now.tableSchema, labels: dictionary.labels });
  } catch { /* the session's copy is the planner's last confirmed dictionary */ }
  return schemaWithLabels(dictionary);
}

/** Read inputs/column_dictionary.json, or say why it cannot be. Labels come back from `title`. */
export function parseSavedColumns(value: unknown): ColumnDictionary | null {
  if (!isRecord(value) || !Array.isArray(value.fields) || !value.fields.every((f) => isRecord(f) && typeof f.name === 'string')) {
    return null;
  }
  const labels: Record<string, string> = {};
  const fields = (value.fields as Record<string, unknown>[]).map((f) => {
    const { title, ...rest } = f;
    if (typeof title === 'string' && title.trim()) labels[f.name as string] = title.trim().slice(0, MAX_LABEL);
    return rest;
  });
  return { tableSchema: { ...value, fields }, labels };
}

/**
 * Give a saved dictionary back to the engine for the reopened file. A dictionary the engine cannot
 * read again is kept as saved, so saving the project again does not lose it, and the planner is told.
 */
export async function restoreColumns(saved: ColumnDictionary | undefined): Promise<{ dictionary: ColumnDictionary | null; note: string }> {
  if (!saved) return { dictionary: null, note: '' };
  try {
    const result = await getEngine().columnsRestore(saved.tableSchema);
    return { dictionary: { tableSchema: result.tableSchema, labels: keepLabels(saved.labels, result.entries) }, note: '' };
  } catch (e) {
    return {
      dictionary: saved,
      note: ` Your column choices were kept in the project but could not be read again here: ${engineMessage(e)}`,
    };
  }
}
