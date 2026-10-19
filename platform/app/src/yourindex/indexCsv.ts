// Your index as a table, for the .csv download and the Excel workbook's own sheet. Every heading
// says it is the planner's own index, so a copied column is never mistaken for the readiness score.

import { slug, today } from '../results/format';
import type { IndexOutcome, IndexSite } from './model';

type Cell = string | number | null;

const YOURS = '(Your Index, Not Official)';

/** The heading row and one row per site: ranked, then not ranked, then left out by a rule. */
export function indexRows(r: IndexOutcome): { head: string[]; rows: Cell[][] } {
  const columns = r.formula.map((f) => f.column);
  const head = [
    'Index Name', 'Status', `Rank ${YOURS}`, 'Site ID', 'Site Name', `Points out of 100 ${YOURS}`, 'Best Case Points',
    'Share of Columns With a Value', 'Rank Band Low (5th percentile)', 'Rank Band High (95th percentile)',
    `Share of Runs in the Top ${r.summary?.k ?? ''}`, 'Columns With No Value', 'Reason Not Ranked or Left Out',
    ...columns.flatMap((c) => [`${c}: value as written`, `${c}: credit 0 to 1`, `${c}: points`]),
  ];
  const site = (s: IndexSite, status: string, reason: string | null): Cell[] => {
    const by = new Map(s.drivers.map((d) => [d.column, d]));
    return [
      r.name, status, s.rank ?? null, s.siteId, s.name, s.score, s.bounds.best, s.completeness,
      s.robustness?.rankLow ?? null, s.robustness?.rankHigh ?? null, s.robustness?.topShare ?? null,
      s.missing.join('; '), reason,
      ...columns.flatMap((c) => {
        const d = by.get(c);
        return d ? [d.raw, d.absent ? null : d.value, d.points] : [null, null, null];
      }),
    ];
  };
  const blank = (n: number) => Array.from({ length: n }, () => null as Cell);
  const rows: Cell[][] = [
    ...r.sites.map((s) => site(s, 'Ranked', null)),
    ...r.unranked.map((s) => site(s, 'Not ranked', s.reason ?? null)),
    ...r.excluded.map((x): Cell[] => [
      r.name, 'Left out by a rule', null, x.siteId, x.name, null, null, null, null, null, null,
      [...new Set(x.reasons.flatMap((w) => w.missing))].join('; '), x.reasons.map((w) => w.reason).join('; '),
      ...blank(columns.length * 3),
    ]),
  ];
  return { head, rows };
}

/** A spreadsheet must not read a cell as a formula: text starting with = + - @ gets a leading apostrophe. */
function csvCell(v: Cell): string {
  if (v === null || v === undefined) return '';
  let s = typeof v === 'number' ? (Number.isFinite(v) ? String(v) : '') : v;
  if (typeof v === 'string' && /^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function indexCsv(r: IndexOutcome, place: string): { blob: Blob; name: string } {
  const { head, rows } = indexRows(r);
  const lines = [head.map(csvCell).join(','), ...rows.map((row) => row.map(csvCell).join(','))];
  // A byte-order mark so Excel reads the file as UTF-8.
  return {
    blob: new Blob(['﻿' + lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' }),
    name: `${slug(place) || 'ev-sient'}-your-index-${slug(r.name) || 'index'}-${today()}.csv`,
  };
}
