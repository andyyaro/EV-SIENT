// What the report is built from: the run, every site's explanation, the run's output files, the
// runtime that produced them and the planner's source details. Gathered once, read by the report
// document and every download.

import type {
  AcceptDetails, Explanation, FieldCatalog, OutputFiles, RunResult, RuntimeInfo, TableInput,
} from '../engine/protocol';
import {
  readAssumptions, readCapacity, readCohort, readManifest, readPublicSources, type CapacityEvidence, type PublicSource,
} from '../results/data';
import { projectName } from '../lib/projectName';
import type { CarriedColumns } from '../results/carried';
import { slug, today } from '../results/format';

export interface ReportModel {
  run: RunResult;
  explains: Map<string, Explanation>;
  files: OutputFiles;
  info: RuntimeInfo | null;
  details: AcceptDetails;
  fields: FieldCatalog | null;
  table: TableInput | null;
  /** The file's columns the model does not read, shown in their own section. Never scored. */
  carried: CarriedColumns | null;
  cohort: ReturnType<typeof readCohort>;
  manifest: ReturnType<typeof readManifest>;
  assumptions: ReturnType<typeof readAssumptions>;
  capacity: Map<string, CapacityEvidence>;
  /** Public datasets the planner accepted values from, if any. */
  publicSources: PublicSource[];
  /** The jurisdiction or project name shown on the cover. */
  place: string;
}

export function buildModel(args: {
  run: RunResult; explains: Explanation[]; files: OutputFiles; info: RuntimeInfo | null;
  details: AcceptDetails; fields: FieldCatalog | null; table: TableInput | null; carried: CarriedColumns | null;
}): ReportModel {
  const cohort = readCohort(args.files);
  const place = projectName(args.details, args.table?.fileName);
  return {
    ...args,
    explains: new Map(args.explains.map((e) => [e.siteId, e])),
    cohort,
    manifest: readManifest(args.files),
    assumptions: readAssumptions(args.files),
    capacity: readCapacity(args.files),
    publicSources: readPublicSources(args.files),
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
