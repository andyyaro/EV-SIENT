// Wording helpers. They only rename things for the planner (a field's code name becomes its label);
// they never change what the engine said.

import type { FieldCatalog, FieldInfo, Finding } from '../engine/protocol';

export function fieldLabel(catalog: FieldCatalog | null, name: string): string {
  if (name === 'lat/lon') return 'Latitude and Longitude';
  return catalog?.fields.find((f) => f.name === name)?.label ?? name;
}

export function fieldInfo(catalog: FieldCatalog | null, name: string): FieldInfo | undefined {
  return catalog?.fields.find((f) => f.name === name);
}

/** The engine's sentence with each field's code name replaced by its label. */
export function plainText(catalog: FieldCatalog | null, text: string): string {
  if (!catalog) return text;
  let out = text.replace(/\blat\/lon\b/g, 'Latitude and Longitude');
  // Longest names first, so "lat" never eats part of a longer name.
  const names = catalog.fields.map((f) => f.name).sort((a, b) => b.length - a.length);
  for (const name of names) {
    const label = fieldLabel(catalog, name);
    out = out.replace(new RegExp(`(^|[^A-Za-z0-9_])${name}(?![A-Za-z0-9_])`, 'g'), `$1${label}`);
  }
  return out;
}

/** "the file is refused" -> "The file is refused" */
export function sentence(text: string): string {
  const t = text.trim();
  if (!t) return t;
  const s = t[0].toUpperCase() + t.slice(1);
  return /[.!?]$/.test(s) ? s : `${s}.`;
}

/** What to do about a refusal, by the field it is about. Fixed guidance; the reason is the engine's. */
export function refusalFix(finding: Finding): string {
  if (finding.field === 'site_id') {
    if (/no column/i.test(finding.explain)) return 'In Map Columns, choose the column that holds a site ID for each row. If your file has none, add a column with a unique ID for each site and upload it again.';
    if (/unique|repeats/i.test(finding.explain)) return 'Give each row its own site ID in your spreadsheet and upload it again. The Check step lists the rows that share one.';
    return 'Fill in a site ID for every row in your spreadsheet and upload it again. The Check step lists the rows without one.';
  }
  if (finding.field === 'lat/lon') {
    return 'Export the coordinates from your mapping software as latitude and longitude in decimal degrees (WGS84) and upload the file again. Or, in Map Columns, set Latitude and Longitude to Not in This File to run without the map.';
  }
  return 'Correct this in your spreadsheet and upload it again.';
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${n.toLocaleString('en-US')} ${n === 1 ? one : many}`;
}

export function listWords(items: string[]): string {
  if (items.length <= 1) return items.join('');
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}
