# `src/` - the Python model (`fcf_m2`)

[← repository root](../README.md)

One package, one model, two modes (`legacy_v2` bit-exact baseline, `milestone2_v3`
canonical horizons). Installed editable via `make setup` from the repo root.

| Module | Responsibility |
|---|---|
| `config.py` | Every result-changing constant, with provenance labels; the two mode names |
| `scoring.py` | Readiness scoring: legacy cohort min-max and V3 fixed anchors (`data/anchors/`) |
| `queueing.py` | Legacy-exact Erlang-C screen and port chooser |
| `peak_wait.py` | Peak-window Erlang + seeded discrete-event simulation (P10/P50/P90 waits) |
| `right_sizing.py` | Starter-vs-pathway logic; legacy 2035/2050 and canonical 2026/2036/2046/2056 |
| `demand.py` | Demand-model status (`synthetic_uncalibrated`) + observed-data calibration with refusal logic |
| `confidence.py` | Typed field-level data confidence (prose cannot change scores) |
| `economics.py` | Lifecycle NPC: staged vs overbuild vs defer; avoided cost; low/base/high |
| `emissions.py` | Net avoided CO2e (sourced grid factor + vintage) and avoided-EVSE metric |
| `standards.py` | Per-site standards register (adopted vs latest editions; conditional standards excluded) |
| `triggers.py` | Proposed equity-aware expansion-trigger policy with explainable rule traces |
| `contract.py` | Contract build + validation (rules RT-01..RT-10, JSON Schema, hash chain) |
| `contract_v2.py`, `contract_v3.py` | Contract v2 (additive observed-data fields) and v3, the authoritative output since DEC-027 |
| `stability.py` | Score breakdown and rank stability: one-weight sweeps, 2,000 random weightings, the unconfirmed-capacity range |
| `intake.py` | Reads a jurisdiction's own file and never silently improves it (DEC-021, DEC-023) |
| `provenance.py` | Resolves any displayed number to its full lineage |
| `browser_api.py` | The planner's door into the engine: JSON in, JSON out, run unmodified in the browser under Pyodide (DEC-024) |
| `flex/` | Flexible analysis of a visitor's own columns: `dictionary.py`, `explore.py`, `index.py` (`docs/FLEXIBLE_ANALYSIS.md`) |
| `server.py`, `launcher.py` | The desktop tier's local server and launcher |
| `matlab_adapter.py` | Generates the MATLAB input CSV from the contract (`capacity_basis` on every row) |
| `visuals.py` / `gis_offline.py` | Footer-enforced charts; fully offline site map from cached boundaries |
| `workflow.py` | Orchestrator + the single step manifest that generates `docs/WORKFLOW_STEPS.md` |

Run: `python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run`
Outputs land in `data/outputs/` (gitignored; regenerate at will). Verified by the repository's `tests/` suite and `scripts/verify.sh` - **neither of which
is part of the public installer**, which ships the model and the surfaces it can build
rather than the harness that checks them.

Limitations that ship with the code: demand uncalibrated, capacity placeholder at all
sites, screening-class costs - see the root README's Known limitations.
