// The public data hub (platform/hub/, DEC-025): county packs of public data the app reads to
// propose values for fields a planner's file does not have.
//
// Only this origin's /hub/ files are fetched, and only after the planner asks. latest.json is
// the one file read without the cache; it names the release manifest and its SHA-256, and the
// manifest names every other file with its own. A file that does not match is refused, never
// read. Nothing about the planner's file is sent: the requests name counties, never sites.

import { distanceToRingsMi, haversineMi, packsFor, pointInRings, propose, type Place, type Proposed } from './compute';
import type { HubCoverage, HubLatest, HubManifest, PackRow } from './types';

const HUB_URL = new URL('hub/', new URL(import.meta.env.BASE_URL, location.origin)).href;

export interface HubSite {
  siteId: string;
  lat: number | null;
  lon: number | null;
}

export interface HubLookup {
  manifest: HubManifest;
  /** field -> site ID -> the proposed value or the reason there is none. */
  proposals: Record<string, Record<string, Proposed>>;
  /** Counties whose packs were read, by name. */
  counties: string[];
  bytes: number;
}

export interface HubProgress {
  done: number;
  total: number;
}

const hex = (buf: ArrayBuffer) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

async function fetchBytes(key: string, init?: RequestInit): Promise<ArrayBuffer> {
  const res = await fetch(HUB_URL + key, init);
  if (!res.ok) throw new Error(`The public data hub did not answer for ${key} (HTTP ${res.status}). Try again later.`);
  return res.arrayBuffer();
}

/** A hub file, refused unless its SHA-256 is the one the release lists. */
async function fetchChecked(key: string, sha256: string): Promise<ArrayBuffer> {
  const buf = await fetchBytes(key);
  if (hex(await crypto.subtle.digest('SHA-256', buf)) !== sha256) {
    throw new Error(`The public data file ${key} does not match its published checksum, so it was not used.`);
  }
  return buf;
}

const json = <T>(buf: ArrayBuffer) => JSON.parse(new TextDecoder().decode(buf)) as T;

async function readPack(buf: ArrayBuffer): Promise<PackRow[]> {
  // Loaded only when a planner looks up public data, so the first screens never wait for it.
  const { parquetReadObjects } = await import('hyparquet');
  return (await parquetReadObjects({ file: buf })) as unknown as PackRow[];
}

/** Every proposal for these sites and fields, from the current hub release. */
export async function lookUp(sites: HubSite[], fields: string[], onProgress?: (p: HubProgress) => void): Promise<HubLookup> {
  const latest = json<HubLatest>(await fetchBytes('latest.json', { cache: 'no-cache' }));
  const manifest = json<HubManifest>(await fetchChecked(latest.manifest, latest.manifestSha256));
  if (manifest.hubVersion !== latest.hubVersion) throw new Error('The public data hub is part way through an update. Try again in a minute.');
  const coverage = json<HubCoverage>(await fetchChecked(manifest.coverage.key, manifest.coverage.sha256));
  let bytes = manifest.coverage.bytes;

  const places = new Map<string, Place>();
  const needed = new Set<string>();
  for (const s of sites) {
    const place: Place = { lat: s.lat, lon: s.lon };
    if (s.lat != null && s.lon != null) {
      place.inside = pointInRings(s.lon, s.lat, coverage.rings);
      if (place.inside) {
        place.edgeMiles = distanceToRingsMi(s.lon, s.lat, coverage.rings);
        for (const key of packsFor(manifest, s.lat, s.lon)) needed.add(key);
      }
    }
    places.set(s.siteId, place);
  }

  const byKey = new Map(manifest.packs.map((p) => [p.key, p]));
  const rows = new Map<string, PackRow[]>();
  const keys = [...needed];
  onProgress?.({ done: 0, total: keys.length });
  for (const [i, key] of keys.entries()) {
    const pack = byKey.get(key)!;
    rows.set(key, await readPack(await fetchChecked(key, pack.sha256)));
    bytes += pack.bytes;
    onProgress?.({ done: i + 1, total: keys.length });
  }

  const wanted = fields.filter((f) => manifest.fields[f]);
  const widest = Math.max(0, ...wanted.map((f) => manifest.fields[f].radiusMiles));
  const proposals: Record<string, Record<string, Proposed>> = Object.fromEntries(wanted.map((f) => [f, {}]));
  for (const s of sites) {
    const place = places.get(s.siteId)!;
    // Narrowed once per site to the widest circle; propose() measures each field's own radius.
    const near = place.inside && s.lat != null && s.lon != null
      ? packsFor(manifest, s.lat, s.lon).flatMap((k) => rows.get(k) ?? []).filter((r) => haversineMi(s.lat!, s.lon!, r.lat, r.lon) <= widest)
      : [];
    for (const f of wanted) proposals[f][s.siteId] = propose(manifest.fields[f], coverage.name, place, near);
  }
  return { manifest, proposals, counties: keys.map((k) => byKey.get(k)!.name).sort(), bytes };
}
