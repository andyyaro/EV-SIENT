# Legacy Baseline Verification (frozen 2026-07-19)

Reproduced on disposable copies of the V1 and V2 legacy code in the pre-publication implementation workspace, using a dedicated legacy virtual environment (Python 3.14.6; unpinned legacy requirements + GIS extras). The full run logs (`legacy_v1_run.log`, `legacy_v2_run.log`) were retained in that workspace and are not tracked in this repository; the output hashes below are.

## Python V1 (`Future-City-Fellowship--main`)
- `src/run_all.py` completed; `src/check_outputs.py`: **Result: PASSED** ("Current outputs are valid, and the baseline comparison report was generated"); sanity check PASSED.

## Python V2 (`Future-City-Fellowship--2-expansion-planning`)
- `src/run_v2.py`: all 25 steps completed (exit 0), including GIS decision map (online TIGER + basemap download).
- `src/check_outputs_v2.py`: **Status: PASSED** (all outputs present, 12/12 sites, package hash-synced).
- `src/compare_v2_to_baseline.py`: all guardrail comparisons **PASS**.
- `src/build_tableau_exports.py` + `src/check_tableau_exports.py`: **15/15 exports, 12/12 sites, PASSED**.

## Headline metrics — all match expected values exactly
| Check | Expected | Reproduced |
|---|---|---|
| Sites | 12 | 12 |
| Top site | FFX002 ≈58.8 | FFX002 City of Fairfax Regional Library 58.8 (Medium confidence) |
| High-confidence sites | 0 | 0 |
| Starter ports | 25 | 25 |
| Future-ready pathway ports | 48 | 48 |
| 2035 base / 2035 high / 2050 base / 2050 high | 35 / 44 / 44 / 54 | 35 / 44 / 44 / 54 |
| Data-quality findings | 38 REVIEW + 12 INFO | 38 REVIEW + 12 INFO |
| Tableau exports | 15 | 15 |
| Deliverable package files | 35 | 35 |

## Offline behavior
- First full run required internet (TIGER county boundary + basemap tiles downloaded at runtime).
- A subsequent run of `plot_site_decision_map.py` with all HTTP(S) proxies pointed at a dead port **succeeded**, because the boundary zip was already cached in `data/` and basemap failures degrade gracefully after tile cache warm-up. Cold offline environments still fail — confirming the PY-06 finding that the fix is shipping cached boundaries + a documented offline mode.

## MATLAB/Simulink (`MATLAB-SIMULINK--main-2`)
- **No MATLAB installation available in this environment. No simulation was executed and none is claimed.**
- Static inspection only (scripts, CSVs, committed PNG/GIF outputs). Executable `.slx` verification is **blocked**; exact commands for a licensed runner are provided in `matlab/RUN_ON_LICENSED_MATLAB.md`.

## Output hash freeze
- `v1_output_hashes.txt` (14 files), `v2_output_hashes.txt` (71 files) — SHA-256 of all CSV/JSON/MD outputs from the reproduced runs.
