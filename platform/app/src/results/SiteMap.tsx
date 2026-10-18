// The sites on a basemap, numbered by rank. Nothing loads until the planner chooses Show Map:
// the basemap comes from OpenFreeMap, which then sees the area being viewed (never the file).
// The ranked table is the full accessible equivalent; each marker is also a button.

import { useEffect, useRef, useState } from 'react';
import type { Map as MlMap, Marker } from 'maplibre-gl';
import { Icon } from '../components/Icon';
import type { SiteResult } from '../engine/protocol';
import { isNumber } from './format';

interface Props {
  sites: SiteResult[];
  selectedId: string | null;
  onSelect(siteId: string): void;
}

const isDark = () => (document.documentElement.getAttribute('data-theme') ?? '').startsWith('dark')
  || (!document.documentElement.hasAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);

export function SiteMap({ sites, selectedId, onSelect }: Props) {
  const [shown, setShown] = useState(false);
  const located = sites.filter((s) => isNumber(s.lat) && isNumber(s.lon));
  const missing = sites.filter((s) => !(isNumber(s.lat) && isNumber(s.lon)));

  return (
    <section className="rs-map" aria-labelledby="rs-map-title">
      <div className="rs-map__head">
        <h3 className="rs-map__title" id="rs-map-title">Site Map</h3>
        {shown && <span className="rs-map__note">Numbers are ranks. The table lists the same sites.</span>}
      </div>
      {!shown ? (
        <div className="rs-map__gate">
          <span className="rs-map__glyph" aria-hidden="true"><Icon name="map" size={28} strokeWidth={1.6} /></span>
          <p className="rs-map__privacy">
            Showing the map contacts OpenFreeMap for the basemap and shares the area being viewed, never your file or results.
          </p>
          <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus hig-pressable" onClick={() => setShown(true)} disabled={!located.length}>
            <Icon name="map" size={18} /><span className="hig-button__label">Show Map</span>
          </button>
          {!located.length && <p className="footnote">No site has coordinates, so there is nothing to map.</p>}
        </div>
      ) : (
        <MapCanvas sites={located} selectedId={selectedId} onSelect={onSelect} />
      )}
      {missing.length > 0 && (
        <p className="footnote rs-map__missing">
          Not on the map (no coordinates): {missing.map((s) => `${s.rank}. ${s.name}`).join(', ')}.
        </p>
      )}
    </section>
  );
}

function MapCanvas({ sites, selectedId, onSelect }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const markers = useRef(new Map<string, { marker: Marker; el: HTMLButtonElement }>());
  const select = useRef(onSelect);
  select.current = onSelect;
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    let observer: MutationObserver | null = null;
    const markerMap = markers.current;
    import('./mapLoader').then(({ maplibregl, styleUrl }) => {
      if (cancelled || !box.current) return;
      let dark = isDark();
      const map = new maplibregl.Map({
        container: box.current,
        style: styleUrl(dark),
        attributionControl: { compact: true },
        cooperativeGestures: true,
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
        maxZoom: 18,
      });
      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      map.keyboard.enable();
      map.getCanvas().setAttribute('aria-label', 'Basemap. Use the arrow keys to pan and plus or minus to zoom; the site markers follow as buttons.');
      const bounds = new maplibregl.LngLatBounds();
      for (const s of sites) {
        const el = document.createElement('button');
        el.type = 'button';
        el.className = 'rs-marker';
        el.textContent = String(s.rank);
        el.setAttribute('aria-label', `Rank ${s.rank}: ${s.name}`);
        el.addEventListener('click', (e) => { e.stopPropagation(); select.current(s.siteId); });
        const marker = new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([s.lon!, s.lat!]).addTo(map);
        markerMap.set(s.siteId, { marker, el });
        bounds.extend([s.lon!, s.lat!]);
      }
      if (sites.length === 1) map.jumpTo({ center: [sites[0].lon!, sites[0].lat!], zoom: 13 });
      else map.fitBounds(bounds, { padding: 56, maxZoom: 14, duration: 0 });
      map.on('load', () => { if (!cancelled) setStatus('ready'); });
      map.on('error', (e: unknown) => {
        if (cancelled) return;
        const msg = (e as { error?: Error }).error?.message ?? '';
        if (!map.loaded()) { setStatus('error'); setError(msg); }
      });
      observer = new MutationObserver(() => {
        const next = isDark();
        if (next !== dark) { dark = next; map.setStyle(styleUrl(dark)); }
      });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }).catch((e: unknown) => {
      if (!cancelled) { setStatus('error'); setError(e instanceof Error ? e.message : String(e)); }
    });
    return () => {
      cancelled = true;
      observer?.disconnect();
      markerMap.forEach(({ marker }) => marker.remove());
      markerMap.clear();
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // The map is built once per set of sites; selection is applied below.
  }, [sites.map((s) => s.siteId).join('|')]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    markers.current.forEach(({ el, marker }, id) => {
      const on = id === selectedId;
      el.classList.toggle('is-selected', on);
      if (on) el.setAttribute('aria-current', 'true'); else el.removeAttribute('aria-current');
      marker.getElement().style.zIndex = on ? '2' : '1';
    });
    const map = mapRef.current;
    const hit = selectedId ? markers.current.get(selectedId) : undefined;
    if (map && hit) {
      const p = map.project(hit.marker.getLngLat());
      const c = map.getContainer();
      if (p.x < 24 || p.y < 24 || p.x > c.clientWidth - 24 || p.y > c.clientHeight - 24) {
        map.easeTo({ center: hit.marker.getLngLat(), duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 400 });
      }
    }
  }, [selectedId, status]);

  return (
    <div className="rs-map__frame">
      <div className="rs-map__canvas" ref={box} />
      {status === 'loading' && <p className="rs-map__status" role="status">Loading the map</p>}
      {status === 'error' && (
        <p className="rs-map__status rs-map__status--error" role="alert">
          The basemap could not load{error ? ` (${error})` : ''}. The table above still lists every site.
        </p>
      )}
    </div>
  );
}
