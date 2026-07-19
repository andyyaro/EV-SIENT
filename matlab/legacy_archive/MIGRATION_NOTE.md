# Migration Note - Legacy Scripts to the V3 `src/` Pipeline (ML-02)

Date: 2026-07-19 (static authoring; no MATLAB execution - see `../EXECUTION_STATUS.md`)

## What is in this folder

Byte-identical reference copies of the two legacy scripts from the pre-V3
legacy MATLAB workspace (`file1_phase2/`, preserved in the archive branch
`archive/pre-milestone2-v3-20260719`):

| File | Role in the legacy repo |
|---|---|
| `build_and_run_site_grid_behavior_model.m` | The documented "starter" script (matches the legacy `README.txt`) |
| `untitled.m` | The diverged copy that actually generated the committed professional PNGs and the animated GIF |

The originals remain **unchanged** in the pre-V3 archive branch for
provenance. Nothing in this archive is on the MATLAB path and nothing here
is executed by the V3 pipeline.

## Why two scripts existed (verified hypothesis H13)

`untitled.m` carries the *same header docstring* as
`build_and_run_site_grid_behavior_model.m` - it began as a copy and then
diverged. Line-by-line comparison (Report 13, H13 CONFIRMED) shows the core
math is identical in both; `untitled.m` **added**:

- a professional multi-tile plot pipeline (`tiledlayout`, styled axes,
  overload shading, summary bars, result annotation),
- an interactive `uifigure` dashboard with a time slider and play button,
- an animated GIF exporter (`createLoadAnimation`),
- a figure save pipeline (`exportgraphics` into `outputs/`),
- a CSV path fallback (`data/` subfolder) and a friendlier
  site-not-found error listing available sites.

That left **two sources of truth**: edits to the model math landed in one
file only, and the committed visuals were produced by the undocumented copy.

## How the merge was done

Both scripts were merged into a single parameterized pipeline under
`../src/`, decomposed by responsibility instead of duplicated as
monoliths:

| Legacy local function (both scripts) | V3 replacement | Change |
|---|---|---|
| `loadScenario` | `src/loadScenarios.m` | Reads the canonical auto-generated CSV; validates columns; filters by `site_id` (never name); horizons read from data (ML-06); fail-closed on missing `capacity_basis` |
| `makeProfiles` | `src/makeSessionProfiles.m` | Session-based demand (sessions/day, dwell consumed, energy per session, efficiency, diversity) replaces the ports x 19.2 kW Gaussian (H1/H2/H5); legacy shape retained only as an explicitly labeled `legacy_gaussian` continuity mode |
| capacity line inside `makeProfiles` | `src/capacityGuard.m` | Controlled `capacity_basis` vocabulary; fail-closed feasibility gate; mandatory placeholder banner (H3) |
| managed clamp inside `makeProfiles` | `src/managedCharging.m` | Three strategies: `unmanaged`, legacy `clamp` (preserved for comparison), and the new `energy_aware` deferral scheduler with per-vehicle energy/deadline accounting (H4) |
| (absent) | `src/electricalEconomics.m` | Efficiency/power-factor/service check/demand-charge economics; costs only when a tariff is supplied (ML-11 / H6) |
| top-level script body | `src/runScenario.m` | Single-scenario end-to-end pipeline, no hard-coded site/year (H9) |
| `runAllYearsAfter` loop | `src/run_all_scenarios.m` | Full batch over all sites x horizons x cases with results table, manifest, SHA-256 hashes (ML-08/ML-12); replaces the hard-coded `["Now","2035","2050"]` loop (H7) |
| `plotScenario`, `plotYearComparison`, styling helpers | `src/plotScenario.m` | Professional figure retained; **adds mandatory capacity-basis label, placeholder banner, and source/date footer** |
| `buildModel` | `src/buildSimulinkModel.m` | Build-once (never delete/rebuild - reverses H8), version-stamped, parameters externalized to a data dictionary + `.mat`; explicitly illustrative, not load-bearing |
| `createDashboard`, `createLoadAnimation` | *not migrated* | Presentation-only features (Report 13: "adds motion, not information"); can be reintroduced on demand against the V3 result structs |

## Behavioral differences to be aware of

1. **The default EV request is no longer ports x charger kW.** The
   session-based profile is the authoritative demand model. Use
   `makeSessionProfiles(..., "Mode", "legacy_gaussian")` only for visual
   continuity with the Phase 2 PNGs, and say so in the caption.
2. **Capacity may legitimately be undefined.** The canonical CSV ships
   with empty `service_capacity_kW`/`spare_capacity_kW` and
   `capacity_basis=placeholder` on all 120 rows. Capacity-limited
   strategies refuse to run without an explicit, labeled assumed value.
3. **No feasibility claims.** `capacityGuard` errors in feasibility mode
   for every current row - by design, until verified capacity data lands.
4. **The Simulink model is optional.** All metrics come from base MATLAB.
