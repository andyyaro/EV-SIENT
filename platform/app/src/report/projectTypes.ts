// The .evsient project file: a zip the planner owns, from which the same results can be rebuilt.
// Written by report/projectFile.ts (Results workstream), read back by the Start screen and
// restored by the store's restoreProject action (Steps workstream).

import type { AcceptDetails, TableInput } from '../engine/protocol';

export const PROJECT_SCHEMA = 'evsient-project/1';

/** project.json inside the zip. */
export interface ProjectManifest {
  schema: typeof PROJECT_SCHEMA;
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
}
