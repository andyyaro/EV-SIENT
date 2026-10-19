// The Report screen's downloads. Each is built on the device from the engine's outputs and handed
// to the browser as a file; nothing is uploaded.

import * as Comlink from 'comlink';
import { strToU8, zipSync } from 'fflate';
import type { SiteResult } from '../engine/protocol';
import { carriedNumber, carriedText, type CarriedColumns } from '../results/carried';
import { SUBSCORE_KEYS, subscoreLabel } from '../results/format';
import type { PdfWorkerApi } from './pdf.worker';
import { reportBlocks } from './reportBlocks';
import { fileName, groupLabel, type ReportModel } from './reportModel';
import { standaloneCss } from './reportTheme';
import { indexRows } from '../yourindex/indexCsv';

export function saveBlob(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

/** The report as one self-contained, light .html file: the preview's markup with its CSS inlined. */
export function reportHtml(m: ReportModel, article: HTMLElement): { blob: Blob; name: string } {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="generator" content="EV-SIENT Planner">
<title>${esc(`EV Charging Site Readiness Report: ${m.place}`)}</title>
<style>
${standaloneCss}
</style>
</head>
<body>
${article.outerHTML}
</body>
</html>
`;
  return { blob: new Blob([html], { type: 'text/html;charset=utf-8' }), name: fileName(m, 'ev-sient-report', 'html') };
}

// ---------- PDF and Word ----------
// Both are built from the rendered report (reportBlocks.ts). Their libraries load only when asked
// for: the PDF maker in a worker (pdf.worker.ts, about 7 MB once), Word's in its own chunk.

let pdfMaker: { worker: Worker; api: Comlink.Remote<PdfWorkerApi>; failed: Promise<never> } | null = null;

function startPdfMaker() {
  const worker = new Worker(new URL('./pdf.worker.ts', import.meta.url), { type: 'module', name: 'evsient-pdf' });
  // A worker that cannot load reports only an error event; turn it into a rejection.
  const failed = new Promise<never>((_, reject) => {
    worker.addEventListener('error', (e) => reject(new Error(e.message || 'The PDF maker could not be loaded.')));
  });
  failed.catch(() => undefined);
  return { worker, api: Comlink.wrap<PdfWorkerApi>(worker), failed };
}

export async function reportPdf(m: ReportModel, article: HTMLElement): Promise<{ blob: Blob; name: string }> {
  const json = JSON.stringify(reportBlocks(m, article));
  pdfMaker ??= startPdfMaker();
  const maker = pdfMaker;
  try {
    const bytes = await Promise.race([maker.api.pdf(json), maker.failed]);
    return { blob: new Blob([bytes as Uint8Array<ArrayBuffer>], { type: 'application/pdf' }), name: fileName(m, 'ev-sient-report', 'pdf') };
  } catch (e) {
    // Start afresh next time rather than reuse a worker in an unknown state.
    maker.worker.terminate();
    if (pdfMaker === maker) pdfMaker = null;
    throw e;
  }
}

export async function reportDocx(m: ReportModel, article: HTMLElement): Promise<{ blob: Blob; name: string }> {
  const blocks = reportBlocks(m, article);
  const { docxBlob } = await import('./docxReport');
  return { blob: await docxBlob(blocks), name: fileName(m, 'ev-sient-report', 'docx') };
}

// ---------- Table rows shared by CSV and Excel ----------

type Cell = string | number | null;

interface Col { title: string; value(s: SiteResult): Cell }

const SITE_COLUMNS: Col[] = [
  { title: 'Rank', value: (s) => s.rank },
  { title: 'Site ID', value: (s) => s.siteId },
  { title: 'Site Name', value: (s) => s.name },
  { title: 'Site Type', value: (s) => s.type },
  { title: 'Readiness Score', value: (s) => s.score },
  { title: 'Tier', value: (s) => s.tier },
  ...SUBSCORE_KEYS.map((k): Col => ({ title: `${subscoreLabel(k)} Subscore`, value: (s) => s.subscores[k] })),
  { title: 'Data Confidence Score', value: (s) => s.confidence.score },
  { title: 'Data Confidence Level', value: (s) => s.confidence.level },
  { title: 'Ports Now', value: (s) => s.portsNow },
  { title: 'Pathway Ports', value: (s) => s.pathwayPorts },
  { title: 'Capacity Cap', value: (s) => s.capacityCap },
  { title: 'Port Plan', value: (s) => s.plan },
  { title: 'Expected Sessions per Day', value: (s) => s.expectedSessionsDay },
  { title: 'Utilization', value: (s) => s.utilization },
  { title: 'Mean Wait (min)', value: (s) => s.meanWaitMin },
  { title: 'Install Cost (USD, screening)', value: (s) => s.installCostUsd },
  { title: 'Electrical Risk', value: (s) => s.electricalRisk },
  { title: 'Latitude', value: (s) => s.lat },
  { title: 'Longitude', value: (s) => s.lon },
  { title: 'Fields Not Recorded', value: (s) => s.absentFields.join('; ') },
];

/** A spreadsheet must not read a cell as a formula: text starting with = + - @ gets a leading apostrophe. */
function csvCell(v: Cell): string {
  if (v === null || v === undefined) return '';
  let s = typeof v === 'number' ? (Number.isFinite(v) ? String(v) : '') : v;
  if (typeof v === 'string' && /^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/**
 * Your Columns, after the model's: each heading says it is the planner's column and not in the
 * score, and each value is the text the planner wrote.
 */
export const yourColumnTitle = (name: string) => `Your column (not in the score): ${name}`;

function yourColumns(c: CarriedColumns | null, asNumbers: boolean): Col[] {
  if (!c) return [];
  return c.columns.map((col, k): Col => ({
    title: yourColumnTitle(col.name),
    value: (s) => {
      const text = carriedText(c, s.siteId, k);
      if (!text) return null;
      return asNumbers && col.numeric ? carriedNumber(text) : text;
    },
  }));
}

export function sitesCsv(m: ReportModel): { blob: Blob; name: string } {
  const columns = [...SITE_COLUMNS, ...yourColumns(m.carried, false)];
  const lines = [columns.map((c) => csvCell(c.title)).join(',')];
  for (const s of m.run.sites) lines.push(columns.map((c) => csvCell(c.value(s))).join(','));
  // A byte-order mark so Excel reads the file as UTF-8.
  return { blob: new Blob(['﻿' + lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' }), name: fileName(m, 'ranked-sites', 'csv') };
}

export async function workbook(m: ReportModel): Promise<{ blob: Blob; name: string }> {
  const { default: writeXlsxFile } = await import('write-excel-file/browser');
  type XCell = { value: string | number; type?: StringConstructor | NumberConstructor; fontWeight?: 'bold'; wrap?: boolean } | null;
  const cell = (v: Cell): XCell => {
    if (v === null || v === undefined || (typeof v === 'number' && !Number.isFinite(v))) return null;
    return typeof v === 'number' ? { value: v, type: Number } : { value: v, type: String };
  };
  const head = (t: string): XCell => ({ value: t, type: String, fontWeight: 'bold', wrap: true });

  const sites = [SITE_COLUMNS.map((c) => head(c.title)), ...m.run.sites.map((s) => SITE_COLUMNS.map((c) => cell(c.value(s))))];

  const byId = new Map(m.run.sites.map((s) => [s.siteId, s]));
  const scenarioHead = ['Site ID', 'Site Name', 'Year', 'Scenario', 'Ports Active', 'Pathway Ports', 'Capacity Cap', 'Strategy'];
  const scenarios = [
    scenarioHead.map(head),
    ...m.run.horizons.map((h) => [h.siteId, byId.get(h.siteId)?.name ?? '', h.year, h.case, h.portsActive, h.portsPathway, h.capacityCap, h.strategy].map(cell)),
  ];

  const groups = [...new Set(m.run.sites.flatMap((s) => Object.keys(s.confidence.breakdown)))];
  const confidence = [
    ['Site ID', 'Site Name', 'Confidence Score', 'Confidence Level', ...groups.map((g) => groupLabel(m, g))].map(head),
    ...m.run.sites.map((s) => [s.siteId, s.name, s.confidence.score, s.confidence.level, ...groups.map((g) => s.confidence.breakdown[g] ?? null)].map(cell)),
  ];

  // Your Columns on their own sheet, so the Sites sheet holds only the model's numbers.
  const id: Col[] = [SITE_COLUMNS[0], SITE_COLUMNS[1], SITE_COLUMNS[2]];
  const yours = [...id, ...yourColumns(m.carried, true)];
  const yourSheet = m.carried ? [
    [head(`Columns from your file that the model does not read. Not in the score: shown as you wrote them, never used to rank.`)],
    yours.map((c) => head(c.title)),
    ...m.run.sites.map((s) => yours.map((c) => cell(c.value(s)))),
  ] : null;

  // The planner's own index on its own sheet, its heading saying it is not the readiness score.
  const index = m.index ? indexRows(m.index) : null;
  const indexSheet = index ? [
    [head(`Your index, not the EV-SIENT readiness score: ${m.index!.name}. Built by the planner from their own columns; never used by the readiness model.`)],
    index.head.map(head),
    ...index.rows.map((row) => row.map(cell)),
  ] : null;

  const widths = (n: number, first = 14) => Array.from({ length: n }, (_, i) => ({ width: i < 3 ? first + (i === 2 ? 14 : 0) : 14 }));
  const blob = await writeXlsxFile([
    { data: sites, sheet: 'Sites', columns: widths(SITE_COLUMNS.length), stickyRowsCount: 1 },
    { data: scenarios, sheet: 'Scenarios', columns: widths(scenarioHead.length), stickyRowsCount: 1 },
    { data: confidence, sheet: 'Data Confidence', columns: widths(groups.length + 4), stickyRowsCount: 1 },
    ...(yourSheet ? [{ data: yourSheet, sheet: 'Your Columns (Not in the Score)', columns: widths(yours.length), stickyRowsCount: 2 }] : []),
    ...(indexSheet ? [{ data: indexSheet, sheet: 'Your Index (Not Official)', columns: widths(index!.head.length), stickyRowsCount: 2 }] : []),
  ] as Parameters<typeof writeXlsxFile>[0]).toBlob();
  return { blob, name: fileName(m, 'ev-sient-results', 'xlsx') };
}

export async function outputsZip(m: ReportModel): Promise<{ blob: Blob; name: string }> {
  const members: Record<string, Uint8Array> = {};
  for (const [path, text] of Object.entries(m.files.files)) members[path.replace(/^\/+/, '')] = strToU8(text);
  const bytes = zipSync(members, { level: 6 });
  return { blob: new Blob([bytes as Uint8Array<ArrayBuffer>], { type: 'application/zip' }), name: fileName(m, 'model-outputs', 'zip') };
}
