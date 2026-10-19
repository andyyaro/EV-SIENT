// Your Columns: every column of the planner's file that is not matched to a field the model reads.
// They are kept with each site by its exact site ID and shown as the planner wrote them, always
// labelled Not in the Score. Display data only: nothing here reaches the engine, and the only
// things worked out from them are the order, filter and map colours the planner asks for.

import type { TableInput } from '../engine/protocol';

export const NOT_IN_SCORE = 'Not in the score';

export interface CarriedColumn {
  name: string;
  /** Every value in the column that is not blank reads as a plain number. */
  numeric: boolean;
  /** A numeric column with a value of 10,000 or more: its numbers are shown with thousands commas. */
  grouped?: boolean;
}

export interface CarriedColumns {
  columns: CarriedColumn[];
  /** Site ID, as the engine reads it (the cell without surrounding spaces) -> one value per column, as written. */
  values: Record<string, string[]>;
}

/**
 * A plain number as a planner types one: an optional sign, digits with or without thousands
 * commas, an optional decimal part. A leading zero ("007", a ZIP code) is an identifier, not a
 * number, so a column holding one is shown as text and never reformatted.
 */
const NUMBER = /^[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?$/;

export function carriedNumber(text: string): number | null {
  const t = text.trim();
  if (!t || !/\d/.test(t) || !NUMBER.test(t) || /^[-+]?0\d/.test(t)) return null;
  const n = Number(t.replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

/** The columns the model does not read, and each site's values in them. Null when there are none. */
export function carriedFrom(table: TableInput | null, mapping: Record<string, string | null> | undefined): CarriedColumns | null {
  if (!table || !mapping) return null;
  const idColumn = mapping.site_id;
  const at = idColumn ? table.columns.indexOf(idColumn) : -1;
  if (at < 0) return null;
  const used = new Set(Object.values(mapping).filter((c): c is string => !!c));
  const keep = table.columns.map((name, i) => ({ name, i })).filter((c) => !used.has(c.name));
  if (!keep.length) return null;
  const values: Record<string, string[]> = {};
  for (const row of table.rows) {
    const id = (row[at] ?? '').trim();
    // A blank or repeated ID is a Must Fix row the model never runs, so it has nothing to carry.
    if (!id || id in values) continue;
    values[id] = keep.map((c) => row[c.i] ?? '');
  }
  const columns = keep.map((c, k) => {
    const filled = Object.values(values).map((v) => v[k]).filter((v) => v.trim() !== '');
    const numeric = filled.length > 0 && filled.every((v) => carriedNumber(v) !== null);
    const grouped = numeric && filled.some((v) => Math.abs(carriedNumber(v)!) >= 10_000);
    return { name: c.name.trim() ? c.name : `Column ${c.i + 1}`, numeric, grouped };
  });
  return { columns, values };
}

/** One site's value in one column, as written ('' when blank or when the site has none). */
export function carriedText(c: CarriedColumns, siteId: string, column: number): string {
  return (c.values[siteId]?.[column] ?? '').trim();
}

/**
 * A value for display. Text is shown as written. A number keeps the decimals it was written
 * with, and gains thousands commas only in a column that reaches 10,000, so a year stays 2028
 * and one column is never half with commas and half without.
 */
export function showCarried(col: CarriedColumn, text: string): string {
  const t = text.trim();
  if (!t) return 'Blank';
  if (!col.numeric) return t;
  const n = carriedNumber(t);
  if (n === null) return t;
  const decimals = t.includes('.') ? t.length - t.indexOf('.') - 1 : 0;
  return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals, useGrouping: col.grouped ?? Math.abs(n) >= 10_000 });
}

export function columnIndex(c: CarriedColumns | null, name: string): number {
  return c ? c.columns.findIndex((x) => x.name === name) : -1;
}

/** Compare two sites by one column: numbers by value, text in natural order, blanks last either way. */
export function compareCarried(c: CarriedColumns, column: number, a: string, b: string, dir: 1 | -1): number {
  const x = carriedText(c, a, column), y = carriedText(c, b, column);
  if (!x || !y) return !x && !y ? 0 : !x ? 1 : -1;
  if (c.columns[column].numeric) return dir * ((carriedNumber(x) ?? 0) - (carriedNumber(y) ?? 0));
  return dir * x.localeCompare(y, 'en', { numeric: true, sensitivity: 'base' });
}

export type CarriedFilter =
  | { column: string; kind: 'text'; contains: string }
  | { column: string; kind: 'range'; min: string; max: string };

/** Whether a site passes the filter. An empty filter passes every site. */
export function passesFilter(c: CarriedColumns, f: CarriedFilter | null, siteId: string): boolean {
  if (!f) return true;
  const k = columnIndex(c, f.column);
  if (k < 0) return true;
  const text = carriedText(c, siteId, k);
  if (f.kind === 'text') {
    const want = f.contains.trim().toLowerCase();
    return !want || text.toLowerCase().includes(want);
  }
  const min = f.min.trim() === '' ? null : Number(f.min);
  const max = f.max.trim() === '' ? null : Number(f.max);
  if (min === null && max === null) return true;
  const n = carriedNumber(text);
  if (n === null) return false;
  return (min === null || !Number.isFinite(min) || n >= min) && (max === null || !Number.isFinite(max) || n <= max);
}

// ---------- Map colours ----------
// Sequential: one hue, light to dark, in five equal steps. Categories: up to eight hues in a fixed
// order, the rest as Other. Both palettes are dataviz reference steps, validated for colour vision
// deficiency; each marker also keeps its rank number and the legend names every colour.

const SEQUENTIAL = ['#b7d3f6', '#6da7ec', '#2a78d6', '#1c5cab', '#0d366b'];
const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'];
export const OTHER_COLOUR = '#8e8e93';
export const BLANK_COLOUR = '#d1d1d6';

export interface LegendItem { colour: string; label: string; count: number }
export interface MarkerColours { byId: Map<string, string>; legend: LegendItem[]; kind: 'range' | 'category' }

/** Text that reads on a marker of this colour: black on light fills, white on dark ones. */
export function inkOn(hex: string): string {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.3 ? '#000000' : '#ffffff';
}

export function markerColours(c: CarriedColumns, name: string, siteIds: string[]): MarkerColours | null {
  const k = columnIndex(c, name);
  if (k < 0) return null;
  const col = c.columns[k];
  const byId = new Map<string, string>();
  const blank = siteIds.filter((id) => !carriedText(c, id, k));
  const blankItem = (): LegendItem[] => (blank.length ? [{ colour: BLANK_COLOUR, label: 'Blank', count: blank.length }] : []);
  for (const id of blank) byId.set(id, BLANK_COLOUR);
  if (col.numeric) {
    const nums = siteIds.map((id) => [id, carriedNumber(carriedText(c, id, k))] as const).filter((x): x is [string, number] => x[1] !== null);
    if (!nums.length) return { byId, legend: blankItem(), kind: 'range' };
    const lo = Math.min(...nums.map((x) => x[1])), hi = Math.max(...nums.map((x) => x[1]));
    const steps = lo === hi ? 1 : SEQUENTIAL.length;
    const width = (hi - lo) / steps;
    const counts = new Array(steps).fill(0);
    for (const [id, n] of nums) {
      const bin = steps === 1 ? 0 : Math.min(steps - 1, Math.floor((n - lo) / width));
      counts[bin]++;
      byId.set(id, steps === 1 ? SEQUENTIAL[2] : SEQUENTIAL[bin]);
    }
    const digits = Math.max(0, ...nums.map(([id]) => {
      const t = carriedText(c, id, k);
      return t.includes('.') ? t.length - t.indexOf('.') - 1 : 0;
    }));
    const show = (n: number) => n.toLocaleString('en-US', { maximumFractionDigits: Math.max(digits, width < 1 ? 2 : 0), useGrouping: Math.abs(n) >= 10_000 });
    const legend: LegendItem[] = counts.map((count, i) => ({
      colour: steps === 1 ? SEQUENTIAL[2] : SEQUENTIAL[i],
      label: steps === 1 ? show(lo) : `${show(lo + i * width)} to ${show(i === steps - 1 ? hi : lo + (i + 1) * width)}`,
      count,
    }));
    return { byId, legend: [...legend, ...blankItem()], kind: 'range' };
  }
  const tally = new Map<string, number>();
  for (const id of siteIds) {
    const t = carriedText(c, id, k);
    if (t) tally.set(t, (tally.get(t) ?? 0) + 1);
  }
  // The most common values get the hues; ties in the order they first appear in the file.
  const order = [...tally.entries()].sort((a, b) => b[1] - a[1]);
  const named = order.length > CATEGORICAL.length ? order.slice(0, CATEGORICAL.length - 1) : order;
  const colourOf = new Map(named.map(([v], i) => [v, CATEGORICAL[i]]));
  let other = 0;
  for (const id of siteIds) {
    const t = carriedText(c, id, k);
    if (!t) continue;
    const colour = colourOf.get(t);
    if (colour) byId.set(id, colour);
    else { byId.set(id, OTHER_COLOUR); other++; }
  }
  const legend: LegendItem[] = named.map(([v, count], i) => ({ colour: CATEGORICAL[i], label: v, count }));
  if (other) legend.push({ colour: OTHER_COLOUR, label: `Other (${order.length - named.length} values)`, count: other });
  return { byId, legend: [...legend, ...blankItem()], kind: 'category' };
}
