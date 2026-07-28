# ChargeReady NOVA — 3D Site Explorer

A Google Earth–style 3D viewer for the Future City Fellowship's Public EV
Charging Site-Readiness and Right-Sizing Model. Real terrain, real buildings,
all 12 scored candidate sites, click-to-inspect rankings, side-by-side
comparison, and proposed charging infrastructure placed on the actual parking
lots.

```bash
make setup && make explorer && make explorer-serve
```

---

## The architectural call

**Yes, Claude Code can drive Blender.** Blender has a complete Python API
(`bpy`), runs fully headless (`blender --background --python script.py`), and
the Blender Foundation now ships an official MCP server that exposes that API
to an LLM client.

**But Blender should not be the map.** It is a modelling and rendering
application. It has no terrain streaming, no level-of-detail tiling, no
geographic coordinate system, no click-to-inspect UI layer, and no web
delivery story. Building an interactive planning tool inside it means
reimplementing a GIS engine — and then handing stakeholders a `.blend` file
and a 4 GB install instead of a URL.

So the split is:

| Layer | Tool | Why |
|---|---|---|
| Globe, terrain, buildings, imagery | **CesiumJS** | Purpose-built for streaming georeferenced 3D at planetary scale. Apache-2.0. |
| Photorealistic context | **Google Photorealistic 3D Tiles** | Literally Google Earth's mesh, 2,500+ cities, streamed through Cesium ion. |
| Proposed infrastructure assets | **Blender → glTF** | Best-in-class modelling, scriptable, exports the format Cesium consumes. |
| GIS processing & data contract | **Python** | Joins the model outputs into one georeferenced record per site. |
| Automation across all three | **Claude Code** | Writes and maintains the Python, the `bpy` scripts, and the CesiumJS app. |

Blender produces glTF. Cesium places it at a latitude and longitude. Neither
does the other's job.

---

## What's here

```
fcf3d/
  build_sites.py     model CSVs  → web/data/sites.geojson
  geometry.py        parametric infrastructure massing (zero dependencies)
  glb.py             glTF 2.0 writer — the pipeline runs without Blender
  build_models.py    CLI; routes to glb.py or to Blender
blender/
  build_assets.py    headless bpy asset factory (production fidelity)
web/
  index.html         CesiumJS viewer
  app.js             globe, markers, panels, comparison, placement editor
  style.css
  data/              generated
  models/            generated — one GLB per site
tests/
  test_pipeline.py   46 tests
```

### Data pipeline

`build_sites.py` is read-only on the Fellowship repo. It joins seven frozen
model tables on `site_id` and emits one GeoJSON Feature per candidate site
carrying rank, readiness score, all four subscores, recommendation tier,
confidence bands, right-sizing trajectory, electrical risk with rank
sensitivity, queueing results, lifecycle scenarios, avoided-overbuild
economics, coordinate provenance, and the outstanding data gaps.

**It also explains the ranking.** `DRIVERS` mirrors the exact weights in
`fcf_m2/scoring.py`, so every site's score decomposes into per-driver point
contributions:

> City of Fairfax Regional Library ranks #2 at 51.8.
> Earned: equity gap index +6.60 pts, distance to electrical service +5.62 pts, install cost +5.53 pts.
> Forgone: spare electrical capacity −10.50 pts, jobs within 1 mi −4.92 pts, households within 1 mi −4.75 pts.

Those numbers sum back to 51.8 exactly, for all 12 sites. (This example previously
quoted 58.8 and rank #1 — those are `legacy_v2` figures, and the shipped viewer
data is `milestone2_v3`. A worked example that does not match the artifact it
documents is a defect, not a rounding.)
`test_attribution_reproduces_model_score` fails the build if anyone reweights
the model without updating the map — so the viewer can never quietly tell
planners a story the model never told.

### Asset pipeline

`geometry.py` holds one parametric spec for a proposed site build: ADA-width
stalls first, energised stalls in the model's recommended `ports_now` count,
translucent amber stalls for the pathway capacity the model says to *reserve*
but not energise, dispensers serving stall pairs, a canopy on columns, a power
cabinet, and a pad-mount transformer set back behind the aisle.

Two consumers read that one spec:

- `glb.py` writes it straight to glTF with no dependencies, so CI and
  teammates without Blender can still build and test the whole pipeline.
- `blender/build_assets.py` renders it with bevels, real PBR materials, named
  collections, and an optional `.blend` you can open and art-direct by hand.

They cannot drift, because there is only one geometry definition.

### The viewer

- **Three base map modes.** *Photoreal* streams Google's 3D mesh. *Terrain*
  uses Cesium World Terrain plus OSM building footprints. *Flat* needs no
  credentials at all and still gives you every site, score, and proposed build.
- **Click any pin** for a five-tab panel: Overview, Score (with the driver
  decomposition), Right-sizing, Risk & gaps, Place.
- **Pin up to four sites** and open a side-by-side table across 22 metrics,
  with the best value in each numeric row highlighted.
- **Placement editor.** Nudge heading, east/north offset, and height until the
  massing sits on the parking area you'd actually use, then copy the placement
  JSON back into `sites.geojson` to make it permanent.
- Right-click a site in the rail to pin it. `Esc` closes, `c` pins the
  selection.

---

## Setup

> **Corrected 2026-07-28.** This section previously named `make all`, `make serve`,
> `make candidates`, `make doctor`, `make models-blender` and an `FCF_REPO` variable.
> **None of them exist in this repository's Makefile** — they are from the explorer's original
> standalone repo, before it was integrated here, and `FCF_REPO` is unnecessary now that the
> explorer lives inside the model repository. The real targets are below.

```bash
make setup            # creates venv/, installs deps
make explorer         # build the viewer payload in the canonical milestone2_v3 mode
make explorer-serve   # build, then serve it on http://127.0.0.1:8080
```

Two further targets exist: `make explorer-legacy` builds the payload in `legacy_v2` mode, and
`make explorer-vendor` downloads CesiumJS locally so the viewer runs with no CDN.
All of them run from the **repository root**, not from `explorer/`.

`make setup` builds a local `venv/` and the Makefile picks it up automatically
from then on — no `pip install` into system Python, which recent macOS and
Homebrew Pythons refuse anyway.

There is nothing to point at any more. The old `make candidates`, `make doctor` and the
`FCF_REPO` variable existed because the explorer used to live in its own repository and had to
be told where the model was. It now lives **inside** the model repository, so the paths are
just relative and those helpers are gone.

`make explorer-serve` builds and serves. Open <http://localhost:8080>.

### Cesium ion token (optional but worth it)

Terrain, OSM buildings, and Google Photorealistic 3D Tiles all stream through
Cesium ion. Get a free token at <https://cesium.com/ion> → Access Tokens, and
paste it into the gate on first load. It is stored in your browser only.

Photorealistic 3D Tiles are included with a Cesium ion account and cover 2,500+
cities — Fairfax, Manassas, and Woodbridge are all in coverage. Google requires
that its logo and the data attribution stay visible; the app leaves Cesium's
credit widget in place, so don't remove it.

Without a token the viewer runs in *Flat* mode on OpenStreetMap imagery. Every
score, comparison, and proposed build still works.

### Blender assets (optional — NOT WIRED UP IN THIS REPOSITORY)

> **Corrected 2026-07-28.** This section documented `make models-blender`, which **this
> repository's Makefile does not define**. The underlying `--blender` route in
> `src/fcf3d/build_models.py` is also broken: it builds the script path
> `src/blender/build_assets.py`, and that file does not exist — the ETL moved into `src/`
> during integration and the sibling `blender/` directory did not follow it. The real script
> is still at `explorer/blender/build_assets.py`.
>
> The twelve GLB models shipped with the viewer are produced by the **procedural** route, which
> works and is gated (`3d: all 12 GLB models are well-formed glTF 2.0`). The higher-fidelity
> Blender route is a documented intention, not a working path. The notes below are kept because
> they are the design record for anyone who wires it up.

Or interactively, with the official MCP server
(<https://www.blender.org/lab/mcp-server/>, Blender 5.1+): install the add-on,
point your LLM client at the server, and art-direct the canopy by conversation.
Note Blender's own warning — the MCP server executes generated Python inside
your live session with no sandbox, so use a scratch scene.

For batch generation prefer `blender --background --python`. It is
deterministic, reviewable in a diff, and runs in CI. Keep MCP for exploration.

---

## Extending it

### Higher-fidelity site context

Photorealistic 3D Tiles give you the parking lots as they exist today, which is
usually enough for siting conversations. If you need survey-grade local data:

| Need | Source | Tool |
|---|---|---|
| Bare-earth elevation | USGS 3DEP (1 m lidar DEM, national) | `py3dep`, or GDAL → `cesium-terrain-builder` → quantized-mesh |
| Virginia lidar & imagery | VGIN / Virginia LiDAR portal | same |
| Parcel boundaries | Fairfax County GIS Open Data; PWC GIS | `geopandas` → GeoJSON, drape as a Cesium `GeoJsonDataSource` |
| Building footprints + height | Microsoft US Building Footprints, or OSM | `geopandas` → extruded polygons, or tile to 3D Tiles |
| Existing chargers | AFDC Station Locator API | already in the model; plot as a second entity layer |

Anything you tile yourself becomes a `Cesium3DTileset` and drops into the same
scene alongside Google's mesh. `py3dtiles` and Cesium ion's upload API both
handle the tiling.

### Ideas that fit the existing shape

- Time slider driving `ports_active` across the 2026 → 2036 → 2050 horizons,
  animating the pathway stalls energising.
- Utility service-drop lines drawn from each site to its nearest feeder once
  Dominion confirms capacity, colour-coded by the electrical risk level
  already in the data.
- An equity choropleth from the ACS-derived index, draped on terrain under
  the pins.
- Export the current camera + selection as a shareable URL for the Fellowship
  presentation.

---

## Honest limits

- **Screening-class only.** Every number is a planning estimate. Electrical
  service capacity is unconfirmed for all 12 sites pending utility and
  facility review, which is why the feasibility subscore is the largest source
  of forgone points almost everywhere.
- **The massing is not a design.** Stall and canopy dimensions follow common
  US surface-lot practice for a siting conversation. ADA stall provision uses
  a screening rule of thumb — confirm against the AHJ's adopted accessibility
  code before it informs anything real.
- **Placement offsets are eyeballed.** The default drops the massing on the
  site's official coordinate, which is usually a building centroid, not a
  parking area. Use the placement editor and commit the result.
- **Photorealistic tiles are a snapshot.** Google's mesh has a capture date;
  recent construction won't appear.

---

## Licence & attribution

CesiumJS is Apache-2.0. Google Photorealistic 3D Tiles are governed by the
Google Maps Platform Terms of Service and require visible brand and data
attribution. OpenStreetMap imagery and building data are ODbL. Blender is
GPL — that covers the application, not the glTF it exports.
