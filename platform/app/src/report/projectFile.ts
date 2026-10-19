// The .evsient project file: a zip the planner keeps, from which the same results can be rebuilt
// on any device. project.json lists a SHA-256 for every other member, so a damaged or edited file
// is refused with a plain reason instead of being half-read.
//
//   project.json          ProjectManifest
//   inputs/table.json     the uploaded table, every cell as text (TableInput)
//   inputs/mapping.json   field -> column, null for "not in this file"
//   inputs/details.json   source details (AcceptDetails)
//   inputs/public_data.json  public values the planner accepted, with their sources (only when
//                         there are any; the file is then evsient-project/2, otherwise /1)
//   inputs/your_columns.json  the file's columns the model does not read, with each site's values,
//                         never scored (only when there are any; the file is then evsient-project/3)
//   results/...           every file the engine wrote for the last run (engine.outputFiles())

import { strFromU8, strToU8, unzipSync, zipSync, type Zippable } from 'fflate';
import { version as appVersion } from '../../package.json';
import { getEngine } from '../engine/client';
import { PROTOCOL_VERSION, type AcceptDetails, type FieldFill, type TableInput } from '../engine/protocol';
import { projectName } from '../lib/projectName';
import { fullMapping, useSession } from '../state/store';
import type { CarriedColumns } from '../results/carried';
import {
  PROJECT_SCHEMA, PROJECT_SCHEMA_V1, PROJECT_SCHEMA_V3, PROJECT_SCHEMAS, type ProjectManifest, type ProjectSnapshot,
} from './projectTypes';

export const PROJECT_EXTENSION = '.evsient';
const MAX_PROJECT_BYTES = 100 * 1024 * 1024;
const MAX_UNZIPPED_BYTES = 400 * 1024 * 1024;

async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', bytes as Uint8Array<ArrayBuffer>);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

const json = (value: unknown) => strToU8(JSON.stringify(value, null, 2) + '\n');

/** A file name for the download: the project's name, made safe for every file system. */
export function projectFileName(name: string): string {
  const safe = name.normalize('NFKD').replace(/[^\w.-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80) || 'evsient-project';
  return `${safe}${PROJECT_EXTENSION}`;
}

export async function buildProjectFile(): Promise<Blob> {
  const s = useSession.getState();
  if (!s.table || !s.proposal || !s.run) throw new Error('Run the model before saving a project file.');
  const engine = getEngine();
  const outputs = await engine.outputFiles();

  const members: Record<string, Uint8Array> = {
    'inputs/table.json': json(s.table),
    'inputs/mapping.json': json(fullMapping(s)),
    'inputs/details.json': json(s.details),
  };
  if (s.publicFills.length) members['inputs/public_data.json'] = json({ fills: s.publicFills });
  if (s.carried) members['inputs/your_columns.json'] = json({ note: 'Columns from the planner\'s file that the model does not read. Kept with each site and never scored.', ...s.carried });
  for (const [path, text] of Object.entries(outputs.files)) {
    // Engine paths are "results/..." and "inputs/..." (the accepted cohort); all of them live under results/.
    const clean = path.replace(/^\/+/, '');
    members[clean.startsWith('results/') ? clean : `results/${clean}`] = strToU8(text);
  }

  const hashes: Record<string, string> = {};
  for (const [path, bytes] of Object.entries(members)) hashes[path] = await sha256(bytes);

  const b = s.boot;
  const info = b.status === 'ready' ? b.info : null;
  const manifest: ProjectManifest = {
    schema: s.carried ? PROJECT_SCHEMA_V3 : s.publicFills.length ? PROJECT_SCHEMA : PROJECT_SCHEMA_V1,
    name: projectName(s.details, s.table.fileName),
    savedAt: new Date().toISOString(),
    app: { version: appVersion },
    engine: { version: info?.engine.version ?? 'unknown', sha256: info?.engine.sha256 ?? '', protocol: info?.protocol ?? PROTOCOL_VERSION },
    runtime: { pyodide: info?.pyodide ?? 'unknown', python: info?.python ?? 'unknown' },
    asOf: s.run.asOf,
    runId: s.run.runId,
    members: hashes,
  };

  const zip: Zippable = { 'project.json': json(manifest) };
  for (const [path, bytes] of Object.entries(members)) zip[path] = bytes;
  const out = zipSync(zip, { level: 6 });
  return new Blob([out as Uint8Array<ArrayBuffer>], { type: 'application/zip' });
}

class ProjectFileError extends Error {
  constructor(message: string) { super(message); this.name = 'ProjectFileError'; }
}

const isRecord = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const isStringArray = (v: unknown): v is string[] => Array.isArray(v) && v.every((x) => typeof x === 'string');

function parseMember<T>(files: Record<string, Uint8Array>, path: string): T {
  const bytes = files[path];
  if (!bytes) throw new ProjectFileError(`This project file is missing ${path}, so it cannot be opened.`);
  try {
    return JSON.parse(strFromU8(bytes)) as T;
  } catch {
    throw new ProjectFileError(`${path} in this project file cannot be read, so it cannot be opened.`);
  }
}

export async function readProjectFile(file: File): Promise<ProjectSnapshot> {
  const broken = `${file.name} is not an EV-SIENT project file, or it is damaged. Project files end in ${PROJECT_EXTENSION} and are saved from the Report step.`;
  if (file.size > MAX_PROJECT_BYTES) throw new ProjectFileError(`${file.name} is too large to be a project file.`);
  let files: Record<string, Uint8Array>;
  try {
    let total = 0;
    files = unzipSync(new Uint8Array(await file.arrayBuffer()), {
      filter: (f) => {
        total += f.originalSize;
        if (total > MAX_UNZIPPED_BYTES) throw new ProjectFileError(`${file.name} unpacks to more than ${MAX_UNZIPPED_BYTES / 1024 / 1024} MB, which is too large to be a project file.`);
        return !f.name.startsWith('__MACOSX/') && !f.name.endsWith('/');
      },
    });
  } catch (e) {
    if (e instanceof ProjectFileError) throw e;
    throw new ProjectFileError(broken);
  }
  if (!files['project.json']) throw new ProjectFileError(broken);

  const manifest = parseMember<ProjectManifest>(files, 'project.json');
  if (!isRecord(manifest) || !(PROJECT_SCHEMAS as readonly unknown[]).includes(manifest.schema)) {
    const found = isRecord(manifest) && typeof manifest.schema === 'string' ? ` (it says ${manifest.schema})` : '';
    throw new ProjectFileError(`This project file was saved in a format this planner does not read${found}. It reads ${PROJECT_SCHEMAS.slice(0, -1).join(', ')} and ${PROJECT_SCHEMAS[PROJECT_SCHEMAS.length - 1]}.`);
  }
  if (!isRecord(manifest.members) || typeof manifest.asOf !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(manifest.asOf)) {
    throw new ProjectFileError(broken);
  }

  // Every listed member must be present and unchanged; nothing may be added that is not listed.
  for (const [path, expected] of Object.entries(manifest.members)) {
    const bytes = files[path];
    if (!bytes) throw new ProjectFileError(`This project file is missing ${path}, so it cannot be opened.`);
    if ((await sha256(bytes)) !== expected) {
      throw new ProjectFileError(`${path} in this project file has been changed since it was saved, so it cannot be trusted. Open the original file, or start a new project from your spreadsheet.`);
    }
  }
  for (const path of Object.keys(files)) {
    if (path !== 'project.json' && !(path in manifest.members)) {
      throw new ProjectFileError(`This project file contains ${path}, which was not part of it when it was saved, so it cannot be trusted.`);
    }
  }

  const table = parseMember<TableInput>(files, 'inputs/table.json');
  if (!isRecord(table) || typeof table.fileName !== 'string' || !isStringArray(table.columns)
    || !Array.isArray(table.rows) || !table.rows.every(isStringArray)) {
    throw new ProjectFileError('The table in this project file is not in the expected shape, so it cannot be opened.');
  }
  const mapping = parseMember<Record<string, string | null>>(files, 'inputs/mapping.json');
  if (!isRecord(mapping) || !Object.values(mapping).every((v) => v === null || typeof v === 'string')) {
    throw new ProjectFileError('The column matches in this project file are not in the expected shape, so it cannot be opened.');
  }
  const details = parseMember<AcceptDetails>(files, 'inputs/details.json');
  if (!isRecord(details) || !Object.values(details).every((v) => v === undefined || typeof v === 'string')) {
    throw new ProjectFileError('The source details in this project file are not in the expected shape, so it cannot be opened.');
  }
  const snapshot: ProjectSnapshot = { manifest, table, mapping, details };
  if (files['inputs/public_data.json']) {
    const publicData = parseMember<{ fills: FieldFill[] }>(files, 'inputs/public_data.json');
    const isFill = (f: unknown) => isRecord(f) && typeof f.field === 'string' && isRecord(f.source)
      && isRecord(f.values) && Object.values(f.values).every((v) => typeof v === 'number');
    if (!isRecord(publicData) || !Array.isArray(publicData.fills) || !publicData.fills.every(isFill)) {
      throw new ProjectFileError('The public data values in this project file are not in the expected shape, so it cannot be opened.');
    }
    snapshot.publicData = publicData;
  }
  if (files['inputs/your_columns.json']) {
    const carried = parseMember<CarriedColumns>(files, 'inputs/your_columns.json');
    const isColumn = (c: unknown) => isRecord(c) && typeof c.name === 'string' && typeof c.numeric === 'boolean';
    const ok = isRecord(carried) && Array.isArray(carried.columns) && carried.columns.length > 0 && carried.columns.every(isColumn)
      && isRecord(carried.values) && Object.values(carried.values).every((v) => isStringArray(v) && v.length === carried.columns.length);
    if (!ok) throw new ProjectFileError('Your Columns in this project file are not in the expected shape, so it cannot be opened.');
    snapshot.carried = {
      columns: carried.columns.map((c) => ({ name: c.name, numeric: c.numeric, ...(typeof c.grouped === 'boolean' ? { grouped: c.grouped } : {}) })),
      values: carried.values,
    };
  }
  return snapshot;
}
