// Reads the planner's spreadsheet in the browser with SheetJS Community Edition, before the engine
// sees it. Every cell is kept as the text the planner sees: CSV text is never parsed into numbers
// or dates (read option raw: true), and Excel cells are taken as their formatted text
// (sheet_to_json raw: false). The engine reads the text the same way the command line does.

import type { TableInput } from '../engine/protocol';

export const LIMITS = { bytes: 20 * 1024 * 1024, rows: 5000, columns: 200 };

const TEXT_TYPES = ['csv', 'tsv', 'txt'];
const BOOK_TYPES = ['xlsx', 'xlsm', 'xls', 'ods'];
export const ACCEPT = '.csv,.tsv,.txt,.xlsx,.xlsm,.xls,.ods,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,application/vnd.oasis.opendocument.spreadsheet';

export interface ParsedSheet {
  name: string;
  /** Every row as text, trailing empty rows and columns removed, each row padded to the same width. */
  cells: string[][];
  /** True when the sheet has more rows than the planner reads; only the first rows were read. */
  truncated: boolean;
  /** Rows in the sheet, when it was truncated. */
  totalRows: number;
}

export interface ParsedFile {
  fileName: string;
  size: number;
  kind: 'text' | 'book';
  sheets: ParsedSheet[];
}

export class ParseError extends Error {
  constructor(message: string) { super(message); this.name = 'ParseError'; }
}

const fmtInt = (n: number) => n.toLocaleString('en-US');

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** "A", "B", ... "Z", "AA": the spreadsheet's own column letters, for messages. */
export function columnLetter(index: number): string {
  let n = index + 1;
  let out = '';
  while (n > 0) { const r = (n - 1) % 26; out = String.fromCharCode(65 + r) + out; n = Math.floor((n - 1) / 26); }
  return out;
}

const isBlank = (v: string) => v.trim() === '';

function decodeText(buffer: ArrayBuffer): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer);
  } catch {
    // Not UTF-8: spreadsheets saved from older Excel on Windows are usually Windows-1252.
    return new TextDecoder('windows-1252').decode(buffer);
  }
}

function tidy(rows: unknown[][]): string[][] {
  const text = rows.map((r) => (Array.isArray(r) ? r : []).map((v) => (v == null ? '' : String(v))));
  while (text.length && text[text.length - 1].every(isBlank)) text.pop();
  let width = 0;
  for (const r of text) {
    for (let j = r.length - 1; j >= 0; j--) if (!isBlank(r[j])) { width = Math.max(width, j + 1); break; }
  }
  return text.map((r) => { const row = r.slice(0, width); while (row.length < width) row.push(''); return row; });
}

export async function parseFile(file: File): Promise<ParsedFile> {
  const ext = (file.name.split('.').pop() ?? '').toLowerCase();
  const isText = TEXT_TYPES.includes(ext);
  if (!isText && !BOOK_TYPES.includes(ext)) {
    throw new ParseError(`${file.name} is not a spreadsheet this planner can read. Use a CSV, XLSX, XLS or ODS file.`);
  }
  if (file.size > LIMITS.bytes) {
    throw new ParseError(`${file.name} is ${formatBytes(file.size)}. The planner reads files up to ${formatBytes(LIMITS.bytes)}. Remove columns or rows you do not need and try again.`);
  }
  if (file.size === 0) throw new ParseError(`${file.name} is empty.`);

  const XLSX = await import('xlsx');
  const buffer = await file.arrayBuffer();
  const readRows = LIMITS.rows + 100; // header rows and blank rows above the table, with room to spare
  let book;
  try {
    book = isText
      ? XLSX.read(decodeText(buffer), { type: 'string', raw: true, dense: true, sheetRows: readRows })
      : XLSX.read(new Uint8Array(buffer), { type: 'array', dense: true, sheetRows: readRows, cellFormula: false, cellHTML: false });
  } catch (e) {
    const why = e instanceof Error && /password|encrypt/i.test(e.message)
      ? 'It is protected with a password. Save an unprotected copy and try again.'
      : 'It may be damaged, or saved in a format that only looks like a spreadsheet. Open it in your spreadsheet app, save it again as CSV or XLSX, and try again.';
    throw new ParseError(`${file.name} could not be read. ${why}`);
  }

  const sheets: ParsedSheet[] = book.SheetNames.map((name) => {
    const ws = book.Sheets[name];
    const rows = XLSX.utils.sheet_to_json<unknown[]>(ws, { header: 1, raw: false, defval: '', blankrows: true });
    let totalRows = rows.length;
    const full = (ws as Record<string, unknown>)['!fullref'];
    if (typeof full === 'string') totalRows = XLSX.utils.decode_range(full).e.r + 1;
    return { name, cells: tidy(rows), truncated: totalRows > readRows, totalRows };
  });
  if (!sheets.some((s) => s.cells.length)) throw new ParseError(`${file.name} has no values in it.`);
  return { fileName: file.name, size: file.size, kind: isText ? 'text' : 'book', sheets };
}

/** The sheet with the most rows: a notes or cover sheet usually comes first but is short. */
export function defaultSheet(parsed: ParsedFile): number {
  let best = 0;
  parsed.sheets.forEach((s, i) => { if (s.cells.length > parsed.sheets[best].cells.length) best = i; });
  return best;
}

/** The first row with any value in it: where most files keep their headings. */
export function defaultHeaderRow(sheet: ParsedSheet): number {
  const i = sheet.cells.findIndex((r) => r.some((v) => !isBlank(v)));
  return i < 0 ? 0 : i;
}

export interface TableBuild {
  table: TableInput | null;
  /** Reasons the table cannot be sent to the model yet, in the planner's words. */
  problems: string[];
  /** Rows below the headings with nothing in any cell; they are left out and the planner is told. */
  skippedBlankRows: number;
  /** Columns with no heading and no values; they are left out. */
  skippedBlankColumns: number;
}

export function buildTable(parsed: ParsedFile, sheetIndex: number, headerRow: number): TableBuild {
  const sheet = parsed.sheets[sheetIndex];
  const problems: string[] = [];
  const empty = { table: null, problems, skippedBlankRows: 0, skippedBlankColumns: 0 };
  if (!sheet || !sheet.cells.length) {
    problems.push(sheet ? `The sheet "${sheet.name}" has no values in it. Choose another sheet.` : 'Choose a sheet.');
    return empty;
  }
  if (sheet.truncated) {
    problems.push(`The sheet "${sheet.name}" has ${fmtInt(sheet.totalRows)} rows. The planner reads up to ${fmtInt(LIMITS.rows)} sites at a time. Split the file into parts and run each part.`);
    return empty;
  }
  const header = sheet.cells[headerRow] ?? [];
  const body = sheet.cells.slice(headerRow + 1);
  const keep: number[] = [];
  let skippedBlankColumns = 0;
  const unnamed: string[] = [];
  header.forEach((name, j) => {
    if (!isBlank(name)) { keep.push(j); return; }
    if (body.some((r) => !isBlank(r[j] ?? ''))) unnamed.push(columnLetter(j));
    else skippedBlankColumns++;
  });
  if (unnamed.length) {
    const which = unnamed.length === 1 ? `Column ${unnamed[0]} has` : `Columns ${unnamed.slice(0, -1).join(', ')} and ${unnamed[unnamed.length - 1]} have`;
    problems.push(`${which} values but no heading in row ${headerRow + 1}. If the headings are in a lower row, choose it under Headings Are in. Otherwise add ${unnamed.length === 1 ? 'a heading' : 'headings'} in your spreadsheet and upload it again.`);
  }
  const columns = keep.map((j) => header[j]);
  const seen = new Map<string, number>();
  for (const c of columns) seen.set(c, (seen.get(c) ?? 0) + 1);
  for (const [c, n] of seen) {
    if (n > 1) problems.push(`${n} columns are named "${c}". Give each column its own heading in your spreadsheet and upload it again.`);
  }
  if (columns.length > LIMITS.columns) {
    problems.push(`This sheet has ${fmtInt(columns.length)} columns. The planner reads up to ${fmtInt(LIMITS.columns)}. Remove the columns you do not need and upload it again.`);
  }
  let skippedBlankRows = 0;
  const rows: string[][] = [];
  for (const r of body) {
    if (r.every(isBlank)) { skippedBlankRows++; continue; }
    rows.push(keep.map((j) => r[j] ?? ''));
  }
  if (!rows.length) problems.push(`There are no rows of sites below the headings in row ${headerRow + 1}. Choose a different heading row or sheet.`);
  if (rows.length > LIMITS.rows) {
    problems.push(`This sheet has ${fmtInt(rows.length)} rows of sites. The planner reads up to ${fmtInt(LIMITS.rows)} at a time. Split the file into parts and run each part.`);
  }
  if (problems.length) return { ...empty, skippedBlankRows, skippedBlankColumns };
  const table: TableInput = { fileName: parsed.fileName, columns, rows };
  if (parsed.kind === 'book') table.sheet = sheet.name;
  return { table, problems, skippedBlankRows, skippedBlankColumns };
}
