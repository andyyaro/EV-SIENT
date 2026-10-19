// The .evsient project file: a zip the planner owns, from which the same results can be rebuilt.
// Written by report/projectFile.ts (Results workstream), read back by the Start screen and
// restored by the store's restoreProject action (Steps workstream).

import type { AcceptDetails, FieldFill, IndexSpec, TableInput } from '../engine/protocol';
import type { CarriedColumns } from '../results/carried';
import type { ColumnDictionary } from '../columns/dictionary';

/** Written when the file has columns the model does not read (Your Columns), saved with the project. */
export const PROJECT_SCHEMA_V3 = 'evsient-project/3';
/** Written when the project uses public data and has no Your Columns. */
export const PROJECT_SCHEMA = 'evsient-project/2';
/** Otherwise /1, so older planners still open it. */
export const PROJECT_SCHEMA_V1 = 'evsient-project/1';
export const PROJECT_SCHEMAS = [PROJECT_SCHEMA_V1, PROJECT_SCHEMA, PROJECT_SCHEMA_V3] as const;

/** project.json inside the zip. */
export interface ProjectManifest {
  schema: (typeof PROJECT_SCHEMAS)[number];
  name: string;
  savedAt: string;
  app: { version: string };
  engine: { version: string; sha256: string; protocol: number };
  runtime: { pyodide: string; python: string };
  /** The date data confidence was judged on, so a re-run scores the same. */
  asOf: string;
  runId: string | null;
  /** SHA-256 of every other member, by path. */
  members: Record<string, string>;
}

/** Everything needed to rebuild the session: replay upload -> remap -> check -> accept -> run. */
export interface ProjectSnapshot {
  manifest: ProjectManifest;
  table: TableInput;
  mapping: Record<string, string | null>;
  details: AcceptDetails;
  /** inputs/public_data.json: the public values the planner accepted, with their sources (DEC-025). */
  publicData?: { fills: FieldFill[] };
  /** inputs/your_columns.json: the file's columns the model does not read, by site ID (evsient-project/3). */
  carried?: CarriedColumns;
  /**
   * inputs/column_dictionary.json: the planner's confirmed column dictionary as a Frictionless Table
   * Schema, labels as each field's `title`. Optional in any version: a planner that does not know it
   * opens the project without it.
   */
  columns?: ColumnDictionary;
  /** inputs/your_index.json: the planner's own index settings (Your Index). Never official; any schema may carry it. */
  yourIndex?: { specs: IndexSpec[]; active: number };
}
