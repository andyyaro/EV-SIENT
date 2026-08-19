# 3D Site Explorer - architectural constraints

*Folded into the repository's documentation during the V4 program's Phase 3, from the
standalone explorer project's own `CLAUDE.md`. These constraints are binding on
`src/fcf3d/` and `explorer/`, and the ones marked **gated** are enforced by
`scripts/verify.sh` and CI rather than left to memory.*

## Enforcement status

| Constraint | Enforced by |
|---|---|
| The map never re-runs or re-implements the model | `tests/test_explorer_drift.py` - the explorer **imports** `fcf_m2.scoring`'s weights rather than copying them |
| Attribution reproduces the model's own score, in **both** modes | `tests/test_explorer_pipeline.py::test_attribution_reproduces_model_score`, now running by default instead of skipping |
| `geometry.py` keeps zero third-party dependencies (Blender imports it directly) | `tests/test_explorer_pipeline.py` |
| A field name never carries a horizon its data does not have | `tests/test_explorer_drift.py::test_canonical_mode_never_emits_a_retired_horizon` **gated** |
| The active data mode is visible, not implied | `manifest.json` carries `mode`, `mode_note`, `mode_is_canonical` **gated** |
| `sites.geojson` is strict RFC 7946, 12 sites, Northern Virginia | `verify.sh` 3D gate **gated** |
| All 12 GLBs are well-formed glTF 2.0 | `verify.sh` 3D gate **gated** |
| Committed web artifacts match a fresh build | `tests/test_explorer_drift.py::TestCommittedArtifacts` **gated** |
| No unpinned CDN reference | `scripts/check_cdn_pins.py` **gated**, with a CesiumJS >= 1.124 floor |
| Cesium ion token is runtime-only, browser-only, never committed | `scripts/secret_scan.py` **gated** |

---

*What follows is the original constraints document, preserved as written.*

# CLAUDE.md - ChargeReady NOVA 3D Site Explorer

Project instructions for Claude Code. Read this before touching anything.

## What this is

A 3D geospatial viewer for the Future City Fellowship's Public EV Charging
Site-Readiness and Right-Sizing Model. It plots every scored candidate site on
a real-world globe, lets planners inspect and compare rankings, and places
proposed charging infrastructure massing at each site's actual coordinates.

## Architecture - and the one rule that matters

**Blender authors. Cesium delivers. Python glues.**

```
frozen model outputs (CSV)
        │
        ├── fcf3d/build_sites.py ──► web/data/sites.geojson   ← the data contract
        │
        └── fcf3d/build_models.py ─► web/models/<SITE>.glb    ← the 3D assets
                  │                        ▲
                  └── blender/build_assets.py (optional, higher fidelity)
                                           │
                              web/index.html + app.js (CesiumJS)
```

Blender is **never** the viewer. It is an offline asset factory that emits
glTF. If a task starts with "make Blender show the map interactively," that is
the wrong shape - redirect it into the Cesium layer.

## Layout

| Path | Role |
|---|---|
| `fcf3d/build_sites.py` | ETL. Joins model CSVs → GeoJSON. **Read-only on the source repo.** |
| `fcf3d/geometry.py` | Parametric infrastructure massing. Single source of truth. |
| `fcf3d/glb.py` | Dependency-free glTF 2.0 writer (the no-Blender path). |
| `fcf3d/build_models.py` | CLI; routes to `glb.py` or Blender. |
| `blender/build_assets.py` | Headless `bpy` asset builder. Only importable inside Blender. |
| `web/` | CesiumJS app. Static - no build step, no bundler. |
| `tests/test_pipeline.py` | 46 tests. Must stay green. |

## Non-negotiables

1. **Never re-run or re-implement the scoring model here.** This repo is a
   *projection* of frozen outputs. If a number looks wrong, fix it upstream in
   `fcf_m2`, re-freeze, and re-run `make data`.

2. **`SUBSCORE_WEIGHTS` and `DRIVERS` in `build_sites.py` mirror
   `fcf_m2/scoring.py`.** They exist so the map can explain *why* a site ranks
   where it does using the model's own arithmetic.
   `test_attribution_reproduces_model_score` guards this. If you change either
   file, run the tests - a silent drift means the map tells planners a story
   the model never told.

3. **`geometry.py` has zero dependencies and must stay that way.** Blender's
   bundled Python imports it directly; anything exotic breaks the Blender path.

4. **Keep the disclaimer visible.** Every surface says screening-class
   planning estimates, not engineering. Electrical service capacity is
   unconfirmed for all 12 sites. Do not let UI polish imply more certainty
   than the data supports.

5. **No secrets in the repo.** The Cesium ion token is entered at runtime and
   held in the browser only.

## Common tasks

```bash
make all                       # rebuild data + models
make serve                     # build, then http://localhost:8080
make test                      # 46 tests
make models-blender BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
```

Re-point at a different model run:

```bash
make data FCF_REPO=/path/to/Future-City-Fellowship
```

## Adding a field to the map

1. Add it to the properties dict in `build_sites.py::build()`.
2. Add a key assertion to `test_all_expected_keys_present`.
3. Render it in `app.js::renderPanel()` and, if comparable, add a row to
   `COMPARE_ROWS`.
4. `make data && make test`.

## Changing the proposed-build geometry

Edit `fcf3d/geometry.py` only. Both output paths read from it, so they stay in
sync automatically. Add a test to the geometry section - the existing ones
check ADA stall provision, canopy clearance, pathway-stall translucency, and
the ENU→glTF axis conversion.

## MCP servers worth connecting

- **Blender MCP** (`blender.org/lab/mcp-server`, official; Blender 5.1+) -
  for interactive art direction of the assets. It executes generated Python
  inside a live Blender session with no sandbox, so run it against a scratch
  scene, not a file you care about.
- **Filesystem / Git** - normal repo work.

For batch asset generation prefer `blender --background --python`, not MCP.
It is deterministic, reviewable, and runs in CI.

## Style

- Python: 3.11+, type hints, module docstrings that say *why*.
- JS: plain ES modules, no framework, no bundler. Keep it that way.
- Comments explain intent and constraints, not syntax.
