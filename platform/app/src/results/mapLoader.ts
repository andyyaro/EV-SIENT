// MapLibre GL, loaded only after the planner chooses Show Map. Its worker is a same-origin module
// file bundled by Vite (setWorkerUrl), so the map needs no blob: worker and no CDN.

import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

maplibregl.setWorkerUrl(new URL(workerUrl, location.href).href);

export { maplibregl };

/** OpenFreeMap's styles: Positron for light, Dark for dark. */
export function styleUrl(dark: boolean): string {
  return dark ? 'https://tiles.openfreemap.org/styles/dark' : 'https://tiles.openfreemap.org/styles/positron';
}
