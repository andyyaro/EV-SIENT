/*
 * ChargeReady NOVA — 3D Site Explorer
 *
 * Renders every candidate site from the readiness model onto a real-world 3D
 * globe, with click-to-inspect scoring, side-by-side comparison, and proposed
 * infrastructure models placed at each site's actual coordinates.
 *
 * Data contract: web/data/sites.geojson, written by `python -m fcf3d.build_sites`.
 * Models:        web/models/<SITE_ID>.glb, written by `python -m fcf3d.build_models`.
 */

/* global Cesium */

// ---------------------------------------------------------------- constants

const NOVA_HOME = { lon: -77.34, lat: 38.72, height: 42000 };

const TIER_COLOR = {
  1: '#16b48b',   // Tier 1 — advance
  2: '#d9a23e',   // Tier 2 — refine / high-review
  3: '#7b8494',   // Tier 3 — monitor
  4: '#d9534f',   // special-use
  9: '#7b8494',
};

const SUBSCORE_WEIGHTS = {
  demand_subscore: 0.45,
  feasibility_subscore: 0.30,
  safety_subscore: 0.15,
  equity_subscore: 0.10,
};

const MAX_PINS = 4;

// ------------------------------------------------------------------- state

const state = {
  viewer: null,
  sites: [],
  byId: new Map(),
  entities: new Map(),        // site_id -> marker entity
  models: new Map(),          // site_id -> model entity
  placement: new Map(),       // site_id -> {heading, east, north, height}
  selected: null,
  pinned: [],
  mode: 'terrain',
  hasToken: false,
  layers: { photoreal: null, osmBuildings: null },
  showBuilds: true,
  showLabels: true,
};

// --------------------------------------------------------------- utilities

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (v, d = 1) => (v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(d));
const usd = (v) => (v == null ? '—' : '$' + Math.round(v).toLocaleString());
const int = (v) => (v == null ? '—' : Math.round(v).toLocaleString());

function tierClass(t) { return 't' + (t || 9); }

// localStorage is not available in every embedding context; degrade quietly.
const store = {
  get(k) { try { return window.localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { window.localStorage.setItem(k, v); } catch { /* ignore */ } },
};

function toast(msg, ms = 2600) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add('hidden'), ms);
}

// ------------------------------------------------------------- data loading

async function loadManifest() {
  // The manifest states which model mode produced this payload, and its horizon
  // vocabulary. It shipped with the build from the beginning and nothing ever read it,
  // so the strongest provenance statement in the tree was never shown to anyone.
  // Failure here is non-fatal: the viewer degrades to saying the mode is unknown, which
  // is honest, rather than silently implying the numbers are canonical.
  try {
    const res = await fetch('data/manifest.json', { cache: 'no-cache' });
    if (res.ok) return await res.json();
  } catch { /* fall through */ }
  return null;
}

function renderModeBadge(manifest) {
  const el = document.getElementById('modeBadge');
  if (!el) return;

  if (!manifest || !manifest.mode) {
    el.className = 'mode-badge is-legacy';
    el.innerHTML =
      '<span class="mode-label"><span class="mode-dot"></span>Data mode unknown</span>';
    el.title = 'data/manifest.json could not be read, so this viewer cannot confirm ' +
               'which model mode produced these numbers. Treat them as unverified.';
    return;
  }

  const canonical = manifest.mode_is_canonical === true;
  const horizons = Array.isArray(manifest.horizons) ? manifest.horizons.join(' · ') : '';
  el.className = 'mode-badge ' + (canonical ? 'is-canonical' : 'is-legacy');
  el.innerHTML =
    `<span class="mode-label"><span class="mode-dot"></span>` +
    `${canonical ? '' : 'SUPERSEDED — '}${esc(manifest.mode)}</span>` +
    (horizons ? `<span style="opacity:.75;font-weight:500">${esc(horizons)}</span>` : '') +
    ` <button class="mode-why" type="button" aria-label="What this mode means">what's this?</button>`;

  const note = manifest.mode_note ||
    'No description of this mode was recorded in the manifest.';
  el.title = note;
  const why = el.querySelector('.mode-why');
  if (why) why.addEventListener('click', () => window.alert(note));
}

async function loadSites() {
  // Preferred: fetch the GeoJSON. Falls back to the inlined copy so the app
  // also runs straight off the filesystem with no web server.
  try {
    const res = await fetch('data/sites.geojson', { cache: 'no-cache' });
    if (res.ok) return await res.json();
  } catch { /* fall through */ }

  if (window.__FCF_SITES__) return window.__FCF_SITES__;

  try {
    await import('./data/sites.inline.js');
    if (window.__FCF_SITES__) return window.__FCF_SITES__;
  } catch { /* fall through */ }

  throw new Error(
    'Could not load data/sites.geojson. Run `make data`, then serve this ' +
    'directory (python -m http.server 8080) rather than opening the file directly.'
  );
}

// --------------------------------------------------------------- pin canvas

function pinCanvas(rank, colour, selected) {
  const dpr = 2, w = 34, h = 44;
  const c = document.createElement('canvas');
  c.width = w * dpr; c.height = h * dpr;
  const g = c.getContext('2d');
  g.scale(dpr, dpr);

  g.beginPath();
  g.moveTo(w / 2, h);
  g.bezierCurveTo(w / 2 - 5, h - 12, 1.5, h - 17, 1.5, h - 27);
  g.arc(w / 2, h - 27, w / 2 - 1.5, Math.PI, 0);
  g.bezierCurveTo(w - 1.5, h - 17, w / 2 + 5, h - 12, w / 2, h);
  g.closePath();

  g.fillStyle = colour;
  g.shadowColor = 'rgba(0,0,0,.55)';
  g.shadowBlur = 7; g.shadowOffsetY = 2;
  g.fill();
  g.shadowColor = 'transparent';

  g.lineWidth = selected ? 2.5 : 1.2;
  g.strokeStyle = selected ? '#ffffff' : 'rgba(0,0,0,.35)';
  g.stroke();

  g.fillStyle = '#06140f';
  g.font = '600 14px ui-monospace, Menlo, monospace';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(String(rank), w / 2, h - 27);

  return c;
}

// ------------------------------------------------------------ viewer setup

async function initViewer(token) {
  if (token) Cesium.Ion.defaultAccessToken = token;
  state.hasToken = Boolean(token);

  const osm = new Cesium.OpenStreetMapImageryProvider({
    url: 'https://tile.openstreetmap.org/',
  });

  const viewer = new Cesium.Viewer('cesiumContainer', {
    baseLayer: new Cesium.ImageryLayer(osm),
    baseLayerPicker: false,
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    animation: false,
    timeline: false,
    fullscreenButton: false,
    infoBox: false,
    selectionIndicator: false,
    shadows: true,
    contextOptions: { webgl: { powerPreference: 'high-performance' } },
  });

  viewer.scene.globe.enableLighting = false;
  viewer.scene.globe.depthTestAgainstTerrain = true;
  viewer.scene.skyAtmosphere.show = true;
  viewer.scene.fog.enabled = true;
  viewer.scene.screenSpaceCameraController.enableCollisionDetection = true;

  state.viewer = viewer;

  // ion-only layers are created lazily on first use
  if (!state.hasToken) {
    document.querySelectorAll('#basemapSeg button').forEach((b) => {
      if (b.dataset.mode !== 'flat') b.disabled = true;
    });
    setMode('flat', { silent: true });
  }

  return viewer;
}

async function setMode(mode, opts = {}) {
  const viewer = state.viewer;
  if (!viewer) return;

  if (mode !== 'flat' && !state.hasToken) {
    toast('That base map needs a Cesium ion token. Reload and add one to enable it.');
    return;
  }

  document.querySelectorAll('#basemapSeg button')
    .forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
  state.mode = mode;

  if (state.layers.photoreal) state.layers.photoreal.show = false;
  if (state.layers.osmBuildings) state.layers.osmBuildings.show = false;
  viewer.scene.globe.show = true;

  try {
    if (mode === 'photoreal') {
      if (!state.layers.photoreal) {
        state.layers.photoreal = await Cesium.createGooglePhotorealistic3DTileset();
        viewer.scene.primitives.add(state.layers.photoreal);
      }
      state.layers.photoreal.show = true;
      // Photorealistic tiles include the ground; the ellipsoid underneath
      // would z-fight with it.
      viewer.scene.globe.show = false;
      viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
    } else if (mode === 'terrain') {
      viewer.terrainProvider = await Cesium.createWorldTerrainAsync({
        requestVertexNormals: true,
      });
      if (!state.layers.osmBuildings) {
        state.layers.osmBuildings = await Cesium.createOsmBuildingsAsync();
        viewer.scene.primitives.add(state.layers.osmBuildings);
      }
      state.layers.osmBuildings.show = true;
    } else {
      viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
    }
  } catch (err) {
    console.error(err);
    toast('Base map failed to load: ' + err.message);
  }

  if (!opts.silent) toast(`Base map: ${mode}`);
}

// ------------------------------------------------------------ site plotting

function placementFor(id) {
  if (!state.placement.has(id)) {
    const p = state.byId.get(id).properties.asset || {};
    state.placement.set(id, {
      heading: p.heading_deg ?? 0,
      east: p.offset_east_m ?? 0,
      north: p.offset_north_m ?? 0,
      height: 0,
    });
  }
  return state.placement.get(id);
}

/** Offset a lon/lat by metres east/north, then return a Cartesian3. */
function offsetPosition(lon, lat, pl) {
  const mPerDegLat = 111132.92;
  const mPerDegLon = 111412.84 * Math.cos(Cesium.Math.toRadians(lat));
  return Cesium.Cartesian3.fromDegrees(
    lon + pl.east / mPerDegLon,
    lat + pl.north / mPerDegLat,
    pl.height,
  );
}

function plotSites() {
  const viewer = state.viewer;

  for (const f of state.sites) {
    const p = f.properties;
    const [lon, lat] = f.geometry.coordinates;
    const colour = TIER_COLOR[p.tier_key] || TIER_COLOR[9];

    // --- marker ---
    const marker = viewer.entities.add({
      id: `pin_${p.site_id}`,
      name: p.site_name,
      position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
      billboard: {
        image: pinCanvas(p.model_rank, colour, false),
        width: 34, height: 44,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        scaleByDistance: new Cesium.NearFarScalar(300, 1.15, 40000, 0.55),
      },
      label: {
        text: p.site_name,
        font: '500 12px ui-sans-serif, -apple-system, Segoe UI, sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.fromCssColorString('#0c0e11'),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0, 8),
        verticalOrigin: Cesium.VerticalOrigin.TOP,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 22000),
        translucencyByDistance: new Cesium.NearFarScalar(8000, 1.0, 22000, 0.0),
      },
      properties: { siteId: p.site_id },
    });
    state.entities.set(p.site_id, marker);

    // --- proposed build model, positioned from the live placement state ---
    const pl = placementFor(p.site_id);
    const model = viewer.entities.add({
      id: `build_${p.site_id}`,
      position: new Cesium.CallbackProperty(
        () => offsetPosition(lon, lat, placementFor(p.site_id)), false),
      orientation: new Cesium.CallbackProperty(() => {
        const cur = placementFor(p.site_id);
        return Cesium.Transforms.headingPitchRollQuaternion(
          offsetPosition(lon, lat, cur),
          new Cesium.HeadingPitchRoll(Cesium.Math.toRadians(cur.heading), 0, 0),
        );
      }, false),
      model: {
        uri: `models/${p.site_id}.glb`,
        minimumPixelSize: 0,
        maximumScale: 200,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        silhouetteColor: Cesium.Color.fromCssColorString(colour),
        silhouetteSize: 0,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 6000),
        shadows: Cesium.ShadowMode.ENABLED,
      },
      properties: { siteId: p.site_id },
      show: state.showBuilds,
    });
    state.models.set(p.site_id, model);
    void pl;
  }
}

// ------------------------------------------------------------ selection UX

function select(id, opts = {}) {
  if (state.selected && state.entities.has(state.selected)) {
    const prev = state.byId.get(state.selected).properties;
    state.entities.get(state.selected).billboard.image =
      pinCanvas(prev.model_rank, TIER_COLOR[prev.tier_key] || TIER_COLOR[9], false);
    const pm = state.models.get(state.selected);
    if (pm) pm.model.silhouetteSize = 0;
  }

  state.selected = id;
  if (!id) { $('#panel').classList.add('hidden'); renderList(); return; }

  const p = state.byId.get(id).properties;
  state.entities.get(id).billboard.image =
    pinCanvas(p.model_rank, TIER_COLOR[p.tier_key] || TIER_COLOR[9], true);
  const m = state.models.get(id);
  if (m) m.model.silhouetteSize = 2.0;

  renderPanel(p);
  renderList();

  if (opts.fly !== false) flyTo(id);
}

function flyTo(id) {
  const f = state.byId.get(id);
  const [lon, lat] = f.geometry.coordinates;
  state.viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(lon, lat - 0.0016, 240),
    orientation: {
      heading: Cesium.Math.toRadians(0),
      pitch: Cesium.Math.toRadians(-32),
      roll: 0,
    },
    duration: 2.0,
  });
}

function flyHome() {
  state.viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(NOVA_HOME.lon, NOVA_HOME.lat - 0.28, NOVA_HOME.height),
    orientation: { heading: 0, pitch: Cesium.Math.toRadians(-52), roll: 0 },
    duration: 2.2,
  });
}

// --------------------------------------------------------------- left rail

function visibleSites() {
  const j = $('#filterJurisdiction').value;
  const sortKey = $('#sortBy').value;
  let list = state.sites.filter((f) => !j || f.properties.jurisdiction === j);

  list = [...list].sort((a, b) => {
    const pa = a.properties, pb = b.properties;
    if (sortKey === 'model_rank') return pa.model_rank - pb.model_rank;
    if (sortKey.endsWith('_subscore')) {
      return (pb.subscores[sortKey] ?? 0) - (pa.subscores[sortKey] ?? 0);
    }
    return (pb[sortKey] ?? 0) - (pa[sortKey] ?? 0);
  });
  return list;
}

function renderList() {
  const list = visibleSites();
  const ol = $('#siteList');
  ol.innerHTML = '';
  $('#siteCount').textContent = list.length;

  for (const f of list) {
    const p = f.properties;
    const colour = TIER_COLOR[p.tier_key] || TIER_COLOR[9];
    const li = el('li');
    if (p.site_id === state.selected) li.classList.add('selected');

    const rank = el('div', 'rank', String(p.model_rank));
    rank.style.background = colour;

    const mid = el('div');
    mid.appendChild(el('div', 's-name', esc(p.site_name)));
    mid.appendChild(el('div', 's-meta',
      `${esc(p.site_type)} · ${esc(p.city)} · ${p.ports_now}→${p.ports_2050} ports`));

    const sc = el('div', 's-score', `${num(p.readiness_score, 1)}<small>SCORE</small>`);
    sc.style.color = colour;

    li.append(rank, mid, sc);
    li.onclick = () => select(p.site_id);
    li.oncontextmenu = (e) => { e.preventDefault(); togglePin(p.site_id); };
    li.title = `${p.recommendation_tier}\nRight-click to pin for comparison`;
    ol.appendChild(li);
  }
}

// ------------------------------------------------------------ detail panel

function subscoreBlock(p) {
  return Object.entries(SUBSCORE_WEIGHTS).map(([key, w]) => {
    const v = p.subscores[key] ?? 0;
    const label = p.subscore_labels?.[key] ?? key;
    const contribution = v * w;
    return `
      <div class="sub">
        <div class="lab">
          <span>${esc(label)} <span class="wt">×${w.toFixed(2)}</span></span>
          <b>${num(v, 1)} <span class="wt">→ ${num(contribution, 1)} pts</span></b>
        </div>
        <div class="bar"><i style="width:${Math.max(0, Math.min(100, v))}%;background:${TIER_COLOR[p.tier_key]}"></i></div>
      </div>`;
  }).join('');
}

function driverList(items, kind) {
  if (!items?.length) return '<p class="callout">Nothing flagged at this threshold.</p>';
  return '<ul class="drivers">' + items.map((d) => {
    if (d.note) {
      return `<li><span class="d-name">${esc(d.driver)}</span>
        <span class="d-pts neg">flag</span>
        <span class="d-sub">${esc(d.note)}</span></li>`;
    }
    const pts = kind === 'pos' ? d.points_earned : d.points_forgone;
    const sign = kind === 'pos' ? '+' : '−';
    return `<li>
      <span class="d-name">${esc(d.driver)}</span>
      <span class="d-pts ${kind}">${sign}${num(pts, 2)} pts</span>
      <span class="d-sub">${esc(d.subscore_label)} · ${esc(d.raw_display ?? '')}${
        d.raw_display ? ' · ' : ''}${Math.round((d.effective ?? 0) * 100)}% of available${
        d.lower_is_better ? ' · lower is better' : ''}</span>
    </li>`;
  }).join('') + '</ul>';
}

function scenarioTable(p) {
  if (!p.scenarios?.length) return '<p class="callout">No scenario rows for this site.</p>';
  const rows = p.scenarios.map((s) => `
    <tr>
      <td class="txt">${esc(s.horizon_year)} ${esc(s.scenario_name ?? '')}</td>
      <td>${int(s.ports_active)}</td>
      <td>${num(s.utilization * 100, 1)}%</td>
      <td>${num(s.peak_wait_minutes, 1)}</td>
      <td>${usd(s.lifecycle_cost_npv_usd)}</td>
    </tr>`).join('');
  return `<table class="grid">
    <thead><tr><th>Horizon</th><th>Ports</th><th>Util</th><th>Peak wait</th><th>NPV</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function placementEditor(p) {
  const pl = placementFor(p.site_id);
  return `
    <h4 class="sec">Place the proposed build</h4>
    <p class="callout">Nudge the massing onto the actual parking area you'd
    use. Copy the placement back into <span class="mono">sites.geojson</span>
    → <span class="mono">properties.asset</span> to make it permanent.</p>
    <div class="placer" style="margin-top:11px">
      <div class="row">
        <label>Heading</label>
        <input type="range" id="plHeading" min="0" max="359" step="1" value="${pl.heading}">
        <output id="outHeading">${pl.heading}°</output>
      </div>
      <div class="row">
        <label>East</label>
        <input type="range" id="plEast" min="-120" max="120" step="1" value="${pl.east}">
        <output id="outEast">${pl.east} m</output>
      </div>
      <div class="row">
        <label>North</label>
        <input type="range" id="plNorth" min="-120" max="120" step="1" value="${pl.north}">
        <output id="outNorth">${pl.north} m</output>
      </div>
      <div class="row">
        <label>Height</label>
        <input type="range" id="plHeight" min="-15" max="30" step="0.5" value="${pl.height}">
        <output id="outHeight">${pl.height} m</output>
      </div>
    </div>
    <div style="display:flex;gap:7px;margin-top:11px">
      <button class="ghost" id="btnCopyPlacement" style="flex:1">Copy placement JSON</button>
      <button class="ghost" id="btnResetPlacement">Reset</button>
    </div>`;
}

function renderPanel(p) {
  const colour = TIER_COLOR[p.tier_key] || TIER_COLOR[9];
  const el_ = $('#panelBody');

  el_.innerHTML = `
    <div class="p-head">
      <div class="eyebrow">${esc(p.site_id)} · RANK ${p.model_rank} OF ${state.sites.length}</div>
      <h3>${esc(p.site_name)}</h3>
      <div class="addr">${esc(p.address ?? '')}, ${esc(p.city ?? '')} ${esc(p.zip ?? '')}</div>
      <div class="tierbar">
        <span class="chip ${tierClass(p.tier_key)}">${esc(p.recommendation_tier)}</span>
        <span class="chip">${esc(p.readiness_band)}</span>
        <span class="chip">${esc(p.confidence_band)}</span>
        ${p.ahj_review_flag ? '<span class="chip warn">AHJ review</span>' : ''}
      </div>
    </div>

    <nav class="tabs">
      <button data-tab="overview" class="active">Overview</button>
      <button data-tab="score">Score</button>
      <button data-tab="sizing">Right-sizing</button>
      <button data-tab="risk">Risk &amp; gaps</button>
      <button data-tab="place">Place</button>
    </nav>

    <div class="tab-body" data-body="overview">
      <div class="bigscore">
        <b style="color:${colour}">${num(p.readiness_score, 1)}</b>
        <span>readiness score · ${p.readiness_score_pct}% of portfolio range</span>
      </div>
      <div class="bar"><i style="width:${p.readiness_score_pct}%;background:${colour}"></i></div>

      <h4 class="sec">Recommended action</h4>
      <p class="callout"><strong>${esc(p.action_label)}</strong><br>${esc(p.action_detail)}</p>

      <h4 class="sec">Why it ranks here</h4>
      <p style="font-size:12px;color:var(--ink-2);line-height:1.55">${esc(p.priority_reason)}</p>

      <h4 class="sec">At a glance</h4>
      <dl class="kv">
        <dt>Site type</dt><dd>${esc(p.site_type)}</dd>
        <dt>Public access</dt><dd>${p.public_access ? 'Yes' : 'No'}</dd>
        <dt>Parking spaces</dt><dd>${int(p.parking_spaces)}</dd>
        <dt>Expected sessions/day</dt><dd>${num(p.expected_sessions_day, 2)}</dd>
        <dt>Estimated utilisation</dt><dd>${num((p.estimated_utilization ?? 0) * 100, 1)}%</dd>
        <dt>Mean wait</dt><dd>${num(p.mean_wait_min, 2)} min</dd>
        <dt>Install cost (screening)</dt><dd>${usd(p.install_cost_est_usd)}</dd>
      </dl>

      ${p.coordinate_provenance ? `
      <h4 class="sec">Coordinate provenance</h4>
      <p style="font-size:11.5px;color:var(--ink-3);line-height:1.5">
        ${esc(p.coordinate_provenance.source_quality)} —
        ${esc(p.coordinate_provenance.source_dataset)}<br>
        <em>${esc(p.coordinate_provenance.source_owner)}</em>
      </p>` : ''}
    </div>

    <div class="tab-body hidden" data-body="score">
      <h4 class="sec">Subscores → readiness</h4>
      ${subscoreBlock(p)}
      <p style="font-size:11px;color:var(--ink-3);font-family:var(--mono)">
        Σ contributions = ${num(p.score_reconstructed, 1)} = readiness score ✓
      </p>

      <h4 class="sec">Strengths — points earned</h4>
      ${driverList(p.strengths, 'pos')}

      <h4 class="sec">Constraints — points forgone</h4>
      ${driverList(p.constraints, 'neg')}
    </div>

    <div class="tab-body hidden" data-body="sizing">
      <h4 class="sec">Port trajectory</h4>
      <dl class="kv">
        <dt>Install now</dt><dd>${int(p.ports_now)}</dd>
        <dt>2035 (base / high)</dt><dd>${int(p.right_sizing?.ports_2035_base)} / ${int(p.right_sizing?.ports_2035_high)}</dd>
        <dt>2050 (base / high)</dt><dd>${int(p.right_sizing?.ports_2050_base)} / ${int(p.right_sizing?.ports_2050_high)}</dd>
        <dt>Pathway capacity to build</dt><dd>${int(p.right_sizing?.future_ready_capacity)}</dd>
        <dt>Site capacity cap</dt><dd>${int(p.right_sizing?.site_capacity_cap)}</dd>
      </dl>
      ${p.right_sizing?.right_sizing_reason ? `
        <h4 class="sec">Strategy</h4>
        <p class="callout">${esc(p.right_sizing.right_sizing_reason)}</p>` : ''}

      ${p.avoided_overbuild ? `
        <h4 class="sec">Avoided overbuild (2026)</h4>
        <dl class="kv">
          <dt>Ports kept as pathway-only</dt><dd>${int(p.avoided_overbuild.avoided_active_evse_ports)}</dd>
          <dt>Avoided network fees</dt><dd>${usd(p.avoided_overbuild.avoided_network_fee_usd_yr)}/yr</dd>
        </dl>` : ''}

      <h4 class="sec">Scenarios</h4>
      ${scenarioTable(p)}
    </div>

    <div class="tab-body hidden" data-body="risk">
      ${p.electrical ? `
        <h4 class="sec">Electrical risk — ${esc(p.electrical.risk_level)}</h4>
        <p class="callout ${p.electrical.risk_level === 'high' ? 'risk' : 'warn'}">
          ${p.electrical.risk_reason.map(esc).join('<br>')}
        </p>
        <dl class="kv" style="margin-top:11px">
          <dt>Rank — optimistic</dt><dd>${int(p.electrical.rank_optimistic)}</dd>
          <dt>Rank — expected</dt><dd>${int(p.electrical.rank_expected)}</dd>
          <dt>Rank — conservative</dt><dd>${int(p.electrical.rank_conservative)}</dd>
          <dt>Worst-case rank change</dt><dd>${int(p.electrical.worst_case_rank_change)}</dd>
        </dl>` : ''}

      ${p.review_reasons?.length ? `
        <h4 class="sec">AHJ review triggers</h4>
        <ul class="notes">${p.review_reasons.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}

      <h4 class="sec">Data confidence — ${esc(p.data_confidence_level)} (${num(p.data_confidence_score, 0)})</h4>
      <p style="font-size:11.5px;color:var(--ink-3);line-height:1.5">${esc(p.data_confidence_reason)}</p>

      <h4 class="sec">Data needed next</h4>
      <ul class="notes">${(p.data_needed_next ?? []).map((d) => `<li>${esc(d)}</li>`).join('')}</ul>
    </div>

    <div class="tab-body hidden" data-body="place">
      <h4 class="sec">Proposed build</h4>
      <dl class="kv">
        <dt>Energised ports</dt><dd>${int(p.asset?.ports)}</dd>
        <dt>Pathway stalls (reserved)</dt><dd>${int((p.asset?.pathway_ports ?? 0) - (p.asset?.ports ?? 0))}</dd>
        <dt>Model</dt><dd>models/${esc(p.site_id)}.glb</dd>
      </dl>
      ${placementEditor(p)}
    </div>

    <div class="p-actions">
      <button class="primary" id="btnFly">Fly to site</button>
      <button class="ghost" id="btnPin">${state.pinned.includes(p.site_id) ? 'Unpin' : 'Pin to compare'}</button>
    </div>`;

  $('#panel').classList.remove('hidden');
  $('#panel').scrollTop = 0;
  wirePanel(p);
}

function wirePanel(p) {
  $('#panelBody').querySelectorAll('.tabs button').forEach((btn) => {
    btn.onclick = () => {
      $('#panelBody').querySelectorAll('.tabs button')
        .forEach((b) => b.classList.toggle('active', b === btn));
      $('#panelBody').querySelectorAll('.tab-body').forEach((b) =>
        b.classList.toggle('hidden', b.dataset.body !== btn.dataset.tab));
    };
  });

  $('#btnFly').onclick = () => flyTo(p.site_id);
  $('#btnPin').onclick = () => { togglePin(p.site_id); renderPanel(p); };

  const bind = (input, output, key, suffix) => {
    const i = $(input);
    if (!i) return;
    i.oninput = () => {
      const pl = placementFor(p.site_id);
      pl[key] = parseFloat(i.value);
      $(output).textContent = i.value + suffix;
    };
  };
  bind('#plHeading', '#outHeading', 'heading', '°');
  bind('#plEast', '#outEast', 'east', ' m');
  bind('#plNorth', '#outNorth', 'north', ' m');
  bind('#plHeight', '#outHeight', 'height', ' m');

  const copy = $('#btnCopyPlacement');
  if (copy) {
    copy.onclick = async () => {
      const pl = placementFor(p.site_id);
      const json = JSON.stringify({
        site_id: p.site_id,
        asset: {
          model: 'evse_canopy',
          heading_deg: pl.heading,
          offset_east_m: pl.east,
          offset_north_m: pl.north,
          height_offset_m: pl.height,
          ports: p.asset?.ports,
          pathway_ports: p.asset?.pathway_ports,
        },
      }, null, 2);
      try {
        await navigator.clipboard.writeText(json);
        toast('Placement JSON copied to clipboard');
      } catch {
        console.log(json);
        toast('Clipboard blocked — placement JSON logged to console');
      }
    };
  }

  const reset = $('#btnResetPlacement');
  if (reset) {
    reset.onclick = () => {
      state.placement.delete(p.site_id);
      renderPanel(p);
      toast('Placement reset');
    };
  }
}

// ------------------------------------------------------------- comparison

function togglePin(id) {
  const i = state.pinned.indexOf(id);
  if (i >= 0) state.pinned.splice(i, 1);
  else if (state.pinned.length >= MAX_PINS) { toast(`Pin limit is ${MAX_PINS} sites`); return; }
  else state.pinned.push(id);
  renderTray();
}

function renderTray() {
  const tray = $('#tray');
  if (!state.pinned.length) { tray.classList.add('hidden'); return; }
  tray.classList.remove('hidden');

  const chips = $('#trayChips');
  chips.innerHTML = '';
  for (const id of state.pinned) {
    const p = state.byId.get(id).properties;
    const chip = el('div', 'pinchip',
      `<b style="color:${TIER_COLOR[p.tier_key]}">#${p.model_rank}</b>
       <span>${esc(p.site_name)}</span>`);
    const x = el('button', null, '×');
    x.onclick = () => togglePin(id);
    chip.appendChild(x);
    chips.appendChild(chip);
  }
  $('#trayHint').textContent = `${state.pinned.length} of ${MAX_PINS} pinned`;
}

const COMPARE_ROWS = [
  ['Model rank', (p) => '#' + p.model_rank],
  ['Readiness score', (p) => num(p.readiness_score, 1)],
  ['Recommendation tier', (p) => p.recommendation_tier, true],
  ['Recommended action', (p) => p.action_label, true],
  ['Demand', (p) => num(p.subscores.demand_subscore, 1)],
  ['Feasibility', (p) => num(p.subscores.feasibility_subscore, 1)],
  ['Safety', (p) => num(p.subscores.safety_subscore, 1)],
  ['Equity', (p) => num(p.subscores.equity_subscore, 1)],
  ['Data confidence', (p) => `${p.data_confidence_level} (${num(p.data_confidence_score, 0)})`, true],
  ['Electrical risk', (p) => p.electrical?.risk_level ?? '—', true],
  ['Worst-case rank change', (p) => int(p.electrical?.worst_case_rank_change)],
  ['Ports now', (p) => int(p.ports_now)],
  ['Ports 2035 (base)', (p) => int(p.right_sizing?.ports_2035_base)],
  ['Ports 2050 (base)', (p) => int(p.right_sizing?.ports_2050_base)],
  ['Pathway capacity', (p) => int(p.right_sizing?.future_ready_capacity)],
  ['Sessions/day', (p) => num(p.expected_sessions_day, 2)],
  ['Utilisation', (p) => num((p.estimated_utilization ?? 0) * 100, 1) + '%'],
  ['Mean wait (min)', (p) => num(p.mean_wait_min, 2)],
  ['Install cost (screening)', (p) => usd(p.install_cost_est_usd)],
  ['Parking spaces', (p) => int(p.parking_spaces)],
  ['Top strength', (p) => p.strengths?.[0]?.driver ?? '—', true],
  ['Largest constraint', (p) => p.constraints?.find((c) => c.points_forgone)?.driver ?? '—', true],
];

function openCompare() {
  if (state.pinned.length < 2) { toast('Pin at least two sites to compare'); return; }
  const sites = state.pinned.map((id) => state.byId.get(id).properties);

  const head = sites.map((p) => `<th style="color:${TIER_COLOR[p.tier_key]}">${esc(p.site_name)}</th>`).join('');
  const body = COMPARE_ROWS.map(([label, fn, isText]) => {
    const vals = sites.map((p) => fn(p));
    // highlight the best numeric value in the row
    const nums = vals.map((v) => parseFloat(String(v).replace(/[^0-9.\-]/g, '')));
    const best = isText ? -1 : nums.indexOf(Math.max(...nums.filter((n) => !Number.isNaN(n))));
    return `<tr><th>${esc(label)}</th>${vals.map((v, i) =>
      `<td class="${isText ? 'txt' : ''}"${i === best && !isText ? ' style="color:var(--accent);font-weight:600"' : ''}>${esc(v)}</td>`).join('')}</tr>`;
  }).join('');

  $('#modalBody').innerHTML = `
    <h3>Side-by-side comparison</h3>
    <p class="sub-t">${sites.length} candidate sites · green marks the highest value in each numeric row</p>
    <table class="grid"><thead><tr><th>Metric</th>${head}</tr></thead><tbody>${body}</tbody></table>
    <p class="sub-t" style="margin-top:18px">
      Screening-class planning estimates. Electrical service capacity is
      unconfirmed for every site pending utility and facility review — treat
      feasibility subscores as provisional.
    </p>`;
  $('#modal').classList.remove('hidden');
}

// ------------------------------------------------------------------- wiring

function wireGlobal() {
  document.querySelectorAll('#basemapSeg button').forEach((b) => {
    b.onclick = () => setMode(b.dataset.mode);
  });

  $('#toggleBuilds').onchange = (e) => {
    state.showBuilds = e.target.checked;
    state.models.forEach((m) => { m.show = state.showBuilds; });
  };
  $('#toggleLabels').onchange = (e) => {
    state.showLabels = e.target.checked;
    state.entities.forEach((m) => { m.label.show = state.showLabels; });
  };

  $('#btnReset').onclick = () => { select(null); flyHome(); };
  $('#panelClose').onclick = () => select(null);
  $('#filterJurisdiction').onchange = renderList;
  $('#sortBy').onchange = renderList;
  $('#btnCompare').onclick = openCompare;
  $('#btnClearTray').onclick = () => { state.pinned = []; renderTray(); };
  $('#modalClose').onclick = () => $('#modal').classList.add('hidden');
  $('#modal').onclick = (e) => { if (e.target.id === 'modal') $('#modal').classList.add('hidden'); };

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (!$('#modal').classList.contains('hidden')) $('#modal').classList.add('hidden');
      else select(null);
    }
    if (e.key === 'c' && state.selected) togglePin(state.selected);
  });

  const handler = new Cesium.ScreenSpaceEventHandler(state.viewer.scene.canvas);
  handler.setInputAction((click) => {
    const picked = state.viewer.scene.pick(click.position);
    const id = picked?.id?.properties?.siteId?.getValue?.() ?? picked?.id?.properties?.siteId;
    if (id) select(String(id), { fly: false });
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

  handler.setInputAction((click) => {
    const picked = state.viewer.scene.pick(click.position);
    const id = picked?.id?.properties?.siteId?.getValue?.() ?? picked?.id?.properties?.siteId;
    if (id) select(String(id), { fly: true });
  }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
}

// ---------------------------------------------------------------- bootstrap

async function start(token) {
  await initViewer(token);

  let data;
  try {
    data = await loadSites();
  } catch (err) {
    toast(err.message, 12000);
    console.error(err);
    return;
  }

  state.sites = data.features;
  state.sites.forEach((f) => state.byId.set(f.properties.site_id, f));

  plotSites();
  renderList();
  wireGlobal();
  flyHome();

  const meta = data.metadata ?? {};
  const manifest = await loadManifest();
  renderModeBadge(manifest);

  // Standing caveats. Each one appears in the reports, and the viewer used to carry only
  // two of the four: the 0-of-12 confidence statement and the massing disclaimer were
  // absent entirely. A 3D render is the most persuasive surface this project has, so it
  // is the last place that should be quiet about what the data cannot support.
  $('#railFoot').innerHTML =
    `${meta.site_count ?? state.sites.length} sites · schema ${esc(meta.schema_version ?? '—')}` +
    (manifest && manifest.mode ? ` · mode ${esc(manifest.mode)}` : '') + `<br>` +
    `<ul class="standing-caveats">` +
      `<li><strong>Screening-class only.</strong> Not an engineering, permitting, or procurement tool.</li>` +
      `<li><strong>0 of 12 sites reach High data confidence.</strong></li>` +
      `<li><strong>Electrical capacity is a labeled placeholder at 12 of 12 sites</strong>, pending utility and facility confirmation.</li>` +
      `<li><strong>The massing is not a design.</strong> Volumes are illustrative placement studies, not proposed structures.</li>` +
    `</ul>`;

  if (state.hasToken) setMode('terrain', { silent: true });
}

(function boot() {
  const saved = store.get('fcf3d.ionToken');
  if (saved) { start(saved); return; }

  const gate = $('#tokenGate');
  gate.classList.remove('hidden');
  $('#tokenSave').onclick = () => {
    const t = $('#tokenInput').value.trim();
    if (!t) { toast('Paste a token, or continue without one'); return; }
    store.set('fcf3d.ionToken', t);
    gate.classList.add('hidden');
    start(t);
  };
  $('#tokenSkip').onclick = () => { gate.classList.add('hidden'); start(null); };
})();
