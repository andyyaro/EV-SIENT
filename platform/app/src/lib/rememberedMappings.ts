// Column choices remembered on this device, by the file's header signature, so a planner who
// uploads next month's version of the same spreadsheet does not match columns twice.
// Only header names and the fields chosen for them are stored: never a cell value.

const KEY = 'evsient.columnChoices.v1';
const MAX_ENTRIES = 20;

export interface RememberedMapping {
  headers: string[];
  mapping: Record<string, string | null>;
  savedAt: string;
}

type Store = Record<string, RememberedMapping>;

/** FNV-1a over the header names in order: a short key, not a secret. */
export function headerSignature(headers: string[]): string {
  let h = 0x811c9dc5;
  const s = headers.join('\u001f');
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return (h >>> 0).toString(16).padStart(8, '0');
}

function load(): Store {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === 'object' ? (parsed as Store) : {};
  } catch {
    return {};
  }
}

function save(store: Store): void {
  try { localStorage.setItem(KEY, JSON.stringify(store)); } catch { /* storage off or full: nothing is remembered */ }
}

const sameHeaders = (a: string[], b: string[]) => a.length === b.length && a.every((x, i) => x === b[i]);

export function recall(headers: string[]): RememberedMapping | null {
  const entry = load()[headerSignature(headers)];
  if (!entry || !Array.isArray(entry.headers) || !sameHeaders(entry.headers, headers)) return null;
  const known = new Set(headers);
  // Only choices that still name a column in this file.
  const mapping: Record<string, string | null> = {};
  for (const [field, column] of Object.entries(entry.mapping ?? {})) {
    if (column === null || (typeof column === 'string' && known.has(column))) mapping[field] = column;
  }
  return { ...entry, mapping };
}

export function remember(headers: string[], mapping: Record<string, string | null>): void {
  const store = load();
  store[headerSignature(headers)] = { headers: [...headers], mapping: { ...mapping }, savedAt: new Date().toISOString() };
  const keys = Object.keys(store).sort((a, b) => (store[b].savedAt ?? '').localeCompare(store[a].savedAt ?? ''));
  for (const k of keys.slice(MAX_ENTRIES)) delete store[k];
  save(store);
}

export function forget(headers: string[]): void {
  const store = load();
  delete store[headerSignature(headers)];
  save(store);
}
