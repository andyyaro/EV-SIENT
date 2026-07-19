# Migrating from the V1/V2 prototype to Milestone 2 V3

[← docs index](README.md)

This repository previously carried the V1 prototype on `main` and the V2 model on the
`v2-expansion-planning` branch. The Milestone 2 V3 restructure replaces the working
tree with one canonical codebase. **Nothing was lost:** full history is intact, the
pre-restructure state is preserved on branch `archive/pre-milestone2-v3-20260719` and
tag `pre-milestone2-v3-20260719`, and the accepted V2 results remain reproducible from
this codebase's `legacy_v2` mode (golden-tested).

## What changed

| Area | V1/V2 (before) | V3 (now) |
|---|---|---|
| Package | loose scripts in `src/` (`run_all.py`, `run_v2.py`, 25-step subprocess chain) | installable package `src/fcf_m2/` with one orchestrator (`fcf_m2.workflow`) |
| Horizons | 2035/2050 labels (Python), 2026–2046 (Excel), Now/2035/2050 (MATLAB) — three truths | one canonical set: 2026 baseline + **2036/2046/2056**, identical in every artifact |
| Scoring | cohort-relative min-max (adding a site changed every score) | fixed benchmark anchors (`data/anchors/anchor_set_v1.json`), cohort-independent; legacy behavior retained in `legacy_v2` mode |
| Data confidence | note-keyword heuristics ("official" +5) | typed field-level provenance (`data/provenance/`); prose cannot change scores |
| Waits | steady-state Erlang-C only | + peak-window Erlang + seeded discrete-event simulation (P10/P50/P90) |
| Economics / emissions | none | lifecycle NPC (staged/overbuild/defer) + net CO2e with sourced factor |
| Cross-model | hand-built MATLAB adapter CSV (port mismatches) | generated adapter from the validated contract; `capacity_basis` on every row |
| Tests | output checkers only | 80-test pytest suite incl. golden legacy fixtures; CI coverage gate |
| GIS | live TIGER/basemap downloads (failed offline) | cached, filtered boundary GeoJSON — fully offline |

## Old commands → new commands

| Task | V2 command | V3 command |
|---|---|---|
| Full run | `python src/run_v2.py` | `make run-v3` (or `python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run`) |
| Legacy-equivalent run | `python src/run_v2.py` | `make run-legacy` |
| Output checks | `python src/check_outputs_v2.py` + `compare_v2_to_baseline.py` | `make test` (golden tests) + `./scripts/verify.sh` |
| Tableau inputs | `python src/build_tableau_exports.py` | contract-derived CSVs in `dashboard/tableau/patch_package/` |
| Docs of steps | hand-maintained (drifted) | `make docs` (generated from the step manifest) |

## Old paths → new paths

| Old | New |
|---|---|
| `src/*.py` (V2 scripts) | `src/fcf_m2/*.py` (modules) — legacy scripts remain in history and on the archive branch |
| `data/inputs/real_sites_v2.csv` (V2 branch) | `data/inputs/real_sites_v2.csv` (unchanged content) |
| `data/outputs/v2_*.csv` | `data/outputs/` (gitignored; regenerated) — frozen goldens in `tests/` |
| `tableau/EV_Charging_Site_Readiness_Workbook.twbx` | not carried (unverifiable without Tableau Desktop); recipe in `dashboard/tableau/` |
| MATLAB `file1_phase2/*.m` | `matlab/src/*.m` (merged, rewritten); originals archived in `matlab/legacy_archive/` |

## Legacy results vs V3 results

`legacy_v2` mode reproduces the accepted baseline **bit-for-bit** (FFX002 top at 58.8;
25 starter / 48 pathway ports; identical per-site scores, ranks, and strategies —
asserted by `tests/test_legacy_golden.py` against frozen fixtures).

`milestone2_v3` anchor scores differ from legacy scores *by design* (fixed anchors
compress cohort extremes). Every rank change is explained in the generated
`scoring_migration_report.csv` of a V3 run. The accepted port/pathway structure
(25/48) is deliberately retained pending a documented re-baselining decision. Growth
multipliers (2036: 1.9/2.6 · 2046: 3.0/4.5 · 2056: 4.0/6.0, stress ×1.15) are
provisional planning conventions, not calibrated forecasts.

## Known breaking changes

1. The V2 script entry points (`run_v2.py`, `check_outputs_v2.py`, …) no longer exist
   in the working tree — use the archive branch to run them verbatim.
2. Outputs are no longer committed; regenerate locally (`make run-v3`).
3. The 2035/2050 column names are replaced by horizon-year columns in the contract.
4. The hand-built MATLAB adapter CSV is gone; regenerating the contract regenerates
   the adapter (`data/outputs/v3_run/matlab_scenarios.csv`, tracked copy at
   `matlab/data/canonical/matlab_scenarios.csv`).

## How to reproduce each behavior

- **Legacy:** `make run-legacy` (this codebase) — or check out
  `archive/pre-milestone2-v3-20260719` / branch `v2-expansion-planning` for the
  original scripts.
- **V3:** `make run-v3 && make validate`.
