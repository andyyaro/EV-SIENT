// The public data hub's published shapes (platform/hub/README.md). The builder writes them; the
// app only reads them. Python (platform/hub/hubbuild/) is the source of truth.

export interface HubLatest {
  schema: string;
  hubVersion: string;
  /** Key of the release manifest, relative to /hub/. */
  manifest: string;
  manifestSha256: string;
  published: string;
}

/** How one model field is worked out from the packs. */
export interface HubField {
  column: PackColumn;
  rowKind: 'block' | 'station';
  aggregate: 'sum' | 'weighted_mean';
  weight?: PackColumn;
  radiusMiles: number;
  decimals: number;
  /** Offered only when the whole circle lies inside the coverage area. */
  requiresFullCircle: boolean;
  /** The dataset named as the value's source. */
  primary: string;
  datasets: string[];
  sourceLabel: string;
  method: string;
  vintage: string;
  sourceDate: string;
  licence: string;
}

export interface HubDataset {
  dataset: string;
  title: string;
  publisher: string;
  vintage: string;
  licence: string;
  licenceUrl: string;
  landing: string;
  url: string;
  sourceDate: string;
}

export interface HubPack {
  county: string;
  name: string;
  key: string;
  sha256: string;
  bytes: number;
  rows: { block: number; station: number };
  /** [west, south, east, north] of the pack's points. */
  bbox: number[];
}

export interface HubManifest {
  schema: string;
  hubVersion: string;
  builtUtc: string;
  coverage: { name: string; stateFips: string; key: string; sha256: string; bytes: number; bbox: number[] };
  licences: { key: string; sha256: string; bytes: number };
  datasets: Record<string, HubDataset>;
  fields: Record<string, HubField>;
  /** Fields the hub does not fill yet -> why, in plain words. */
  notYet: Record<string, string>;
  packs: HubPack[];
}

export interface HubCoverage {
  schema: string;
  name: string;
  bbox: number[];
  /** Rings of [lon, lat]. */
  rings: number[][][];
}

export type PackColumn = 'households' | 'jobs' | 'svi' | 'l2_ports' | 'dcfc_ports';

export type PackRow = { kind: 'block' | 'station'; id: string; lat: number; lon: number } & Record<PackColumn, number | null>;
