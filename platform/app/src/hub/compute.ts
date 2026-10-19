// Works out a public value for one site from the hub's county packs, the way the release manifest
// says (its `fields`). Pure functions, no fetching: hub.ts loads the packs, this reads them.
//
// Distances are great-circle miles on the same sphere platform/hub/hubbuild/geo.py uses, so a
// radius means the same thing here as when the packs were built. A value is only proposed when
// the packs hold everything inside the circle; otherwise the site gets a reason instead, and a
// reason is never turned into a zero.

import type { HubField, HubManifest, PackRow } from './types';

const EARTH_RADIUS_MI = 3958.7613;
const MI_PER_DEGREE = (EARTH_RADIUS_MI * Math.PI) / 180;
const rad = (d: number) => (d * Math.PI) / 180;

export function haversineMi(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const p1 = rad(lat1), p2 = rad(lat2);
  const a = Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(rad(lon2 - lon1) / 2) ** 2;
  return 2 * EARTH_RADIUS_MI * Math.asin(Math.sqrt(Math.min(1, Math.max(0, a))));
}

/** Even-odd rule over every ring, so islands count and holes do not. Rings are [lon, lat] pairs. */
export function pointInRings(lon: number, lat: number, rings: number[][][]): boolean {
  let inside = false;
  for (const ring of rings) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      if ((yi > lat) !== (yj > lat) && lon < xi + ((lat - yi) * (xj - xi)) / (yj - yi)) inside = !inside;
    }
  }
  return inside;
}

/** Miles from a point to the nearest edge of any ring, in a flat frame around the point. */
export function distanceToRingsMi(lon: number, lat: number, rings: number[][][]): number {
  const k = Math.cos(rad(lat));
  let best = Infinity;
  for (const ring of rings) {
    for (let i = 0; i + 1 < ring.length; i++) {
      const ax = (ring[i][0] - lon) * k, ay = ring[i][1] - lat;
      const dx = (ring[i + 1][0] - lon) * k - ax, dy = ring[i + 1][1] - lat - ay;
      const len2 = dx * dx + dy * dy;
      const t = len2 > 0 ? Math.min(1, Math.max(0, -(ax * dx + ay * dy) / len2)) : 0;
      const px = ax + t * dx, py = ay + t * dy;
      best = Math.min(best, px * px + py * py);
    }
  }
  return Math.sqrt(best) * MI_PER_DEGREE;
}

/** Whether a site lies within `miles` of a pack's bounding box [west, south, east, north]. */
export function nearBox(lat: number, lon: number, bbox: number[], miles: number): boolean {
  // 1% slack covers the gap between degrees and great-circle miles at these distances.
  const dLat = (miles * 1.01) / MI_PER_DEGREE;
  const top = Math.min(89, Math.max(Math.abs(bbox[1]), Math.abs(bbox[3])) + dLat);
  const dLon = (miles * 1.01) / (MI_PER_DEGREE * Math.cos(rad(top)));
  return lon >= bbox[0] - dLon && lon <= bbox[2] + dLon && lat >= bbox[1] - dLat && lat <= bbox[3] + dLat;
}

/** The packs a site needs: every county pack within the widest radius of the site. */
export function packsFor(manifest: HubManifest, lat: number, lon: number): string[] {
  const widest = Math.max(...Object.values(manifest.fields).map((f) => f.radiusMiles));
  return manifest.packs.filter((p) => nearBox(lat, lon, p.bbox, widest)).map((p) => p.key);
}

export type Proposed = { value: number } | { reason: string };

export interface Place {
  lat: number | null;
  lon: number | null;
  /** Inside the hub's coverage, and how far from its edge; worked out once per site. */
  inside?: boolean;
  edgeMiles?: number;
}

const miles = (r: number) => (r === 1 ? '1 mile' : `${r} miles`);

/** One field's value at one site, or the reason there is none. `rows` are the site's packs, merged. */
export function propose(field: HubField, coverageName: string, place: Place, rows: PackRow[]): Proposed {
  const { lat, lon } = place;
  if (lat == null || lon == null) return { reason: 'No usable latitude and longitude in your file.' };
  if (!place.inside) return { reason: `Outside the area this hub covers so far: ${coverageName}.` };
  if (field.requiresFullCircle && (place.edgeMiles ?? 0) < field.radiusMiles) {
    const what = field.aggregate === 'sum' ? 'the total would be too low' : 'the average would leave out part of the area';
    return { reason: `Within ${miles(field.radiusMiles)} of the edge of the area this hub covers, and the hub has nothing beyond it, so ${what}.` };
  }
  const near: PackRow[] = [];
  const seen = new Set<string>();
  for (const r of rows) {
    if (r.kind !== field.rowKind || seen.has(r.id)) continue;
    if (haversineMi(lat, lon, r.lat, r.lon) <= field.radiusMiles) { near.push(r); seen.add(r.id); }
  }
  const scale = 10 ** field.decimals;
  const round = (v: number) => Math.round(v * scale) / scale;
  if (field.aggregate === 'sum') {
    let total = 0;
    for (const r of near) {
      const v = r[field.column];
      if (v == null) return { reason: `Part of the area within ${miles(field.radiusMiles)} has no value in the hub, so no total is proposed.` };
      total += v;
    }
    return { value: round(total) };
  }
  // A weighted mean, e.g. a vulnerability rank averaged by households.
  let weight = 0, sum = 0, unranked = 0;
  for (const r of near) {
    const w = field.weight ? (r[field.weight] ?? 0) : 1;
    if (w <= 0) continue;
    const v = r[field.column];
    if (v == null) { unranked += w; continue; }
    weight += w; sum += v * w;
  }
  if (unranked > 0) return { reason: `Some homes within ${miles(field.radiusMiles)} have no value in the hub, so no average is proposed.` };
  if (weight <= 0) return { reason: `No households within ${miles(field.radiusMiles)}, so there is nothing to average.` };
  return { value: round(sum / weight) };
}
