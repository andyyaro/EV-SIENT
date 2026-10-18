// What the report is built from: the run, every site's explanation, the run's output files, the
// runtime that produced them and the planner's source details. Gathered once, read by the report
// document and every download.

import type {
  AcceptDetails, Explanation, FieldCatalog, OutputFiles, RunResult, RuntimeInfo, TableInput,
} from '../engine/protocol';
import { readAssumptions, readCapacity, readCohort, readManifest, type CapacityEvidence } from '../results/data';
import { slug, today } from '../results/format';

export interface ReportModel {
  run: RunResult;
  explains: Map<string, Explanation>;
  files: OutputFiles;
  info: RuntimeInfo | null;
  details: AcceptDetails;
  fields: FieldCatalog | null;
  table: TableInput | null;
  cohort: ReturnType<typeof readCohort>;
  manifest: ReturnType<typeof readManifest>;
  assumptions: ReturnType<typeof readAssumptions>;
  capacity: Map<string, CapacityEvidence>;
  /** The jurisdiction or project name shown on the cover. */
  place: string;
}

export function buildModel(args: {
  run: RunResult; explains: Explanation[]; files: OutputFiles; info: RuntimeInfo | null;
  details: AcceptDetails; fields: FieldCatalog | null; table: TableInput | null;
}): ReportModel {
  const cohort = readCohort(args.files);
  const stem = args.table?.fileName.replace(/\.[^.]+$/, '') ?? '';
  const place = args.details.jurisdiction?.trim() || cohort?.jurisdiction?.replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) || stem || 'EV-SIENT Project';
  return {
    ...args,
    explains: new Map(args.explains.map((e) => [e.siteId, e])),
    cohort,
    manifest: readManifest(args.files),
    assumptions: readAssumptions(args.files),
    capacity: readCapacity(args.files),
    place,
  };
}

/** e.g. "example-city-ev-sient-report-2026-10-18.html" */
export function fileName(m: ReportModel, what: string, ext: string): string {
  return `${slug(m.place) || 'ev-sient'}-${what}-${today()}.${ext}`;
}

export function fieldLabel(m: ReportModel, name: string): string {
  return m.fields?.fields.find((f) => f.name === name)?.label ?? name.replace(/_/g, ' ');
}

export function groupLabel(m: ReportModel, group: string): string {
  return m.fields?.groups[group] ?? group.replace(/_/g, ' ');
}
