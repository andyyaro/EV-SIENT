# Start Here

This file is the shortest path for understanding and reproducing the project.

## What this project does

This project compares public EV charging candidate sites in Fairfax City and Prince William County.

It helps answer:

```text
Which sites look most promising?
How many charging ports should be installed now?
How many ports should be planned for 2035 and 2050?
Which sites need better data or technical review?
What should happen next for each site?
Do the port recommendations remain stable under alternate demand and charging assumptions?
```

The model is for early planning support only and does not replace official review or site confirmation.

## Current active workflow

The active Phase 2 prototype is V2 on this branch:

```text
v2-expansion-planning
```

Read the V2 landing page first:

```text
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

## Quickest V2 run

From the repository root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

A successful V2 run should end with:

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, the port-sizing scenario analysis is present, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.
```

A healthy package build should show:

```text
Copied files: 35/35
Synced files: 35/35
```

## V2 files to open first

After a successful V2 run, open these first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
data/outputs/deliverable_package_v2/reports/v2_baseline_comparison.md
```

The package folder is the cleanest review folder because it collects the most important V2 outputs into one place.

## Stable V1 workflow

Use `main` only when reproducing the stable V1 baseline workflow.

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

For a stricter step-by-step reproduction check, use [REPRODUCIBILITY_CHECKLIST.md](REPRODUCIBILITY_CHECKLIST.md).

## Python version

Use Python 3.10 or newer.

Python 3.11 is the tested version used by the GitHub Actions workflow.

## Main V2 input files

```text
data/inputs/real_sites_v2.csv
data/inputs/v2_port_sizing_scenarios.csv
```

`real_sites_v2.csv` is the active candidate-site dataset. `v2_port_sizing_scenarios.csv` controls the port-sizing stress-test assumptions.

## Main V2 output file

```text
data/outputs/v2_executive_site_summary.csv
```

This file combines:

```text
site ranking
readiness score
data confidence
electrical-risk screening
right-sizing recommendation
port-use simulation
right-sizing validation
major review flags
```

## Port-sizing scenario outputs

```text
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
```

This layer stress-tests whether the port recommendations remain reasonable under alternate charging-duration, charging-window, peak-demand, and future-demand assumptions.

## Main V2 visual outputs

```text
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
docs/assets/charts/v2_site_decision_map_readme.png
```

The README decision map includes all 12 candidate site callout tags. Generated Matplotlib chart text uses the shared Times New Roman style.

## Simple project map

| File | Purpose |
|---|---|
| [docs/V2_CURRENT_WORKFLOW_GUIDE.md](docs/V2_CURRENT_WORKFLOW_GUIDE.md) | Main V2 workflow guide. |
| [docs/V2_STABLE_WORKFLOW_CHECKPOINT.md](docs/V2_STABLE_WORKFLOW_CHECKPOINT.md) | Stable V2 milestone summary. |
| [docs/V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md](docs/V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md) | Port-sizing scenario checkpoint. |
| [src/run_v2.py](src/run_v2.py) | Runs the full 24-step V2 workflow. |
| [src/check_outputs_v2.py](src/check_outputs_v2.py) | Checks V2 generated outputs and package sync. |
| [src/run_port_sizing_scenario_analysis.py](src/run_port_sizing_scenario_analysis.py) | Runs the port-sizing scenario analysis. |
| [src/build_v2_deliverable_package.py](src/build_v2_deliverable_package.py) | Builds the clean V2 deliverable package. |
| [src/compare_v2_to_baseline.py](src/compare_v2_to_baseline.py) | Compares current V2 outputs to the saved baseline. |
| [src/ev_charger_model.py](src/ev_charger_model.py) | Main scoring and right-sizing model. |
| [src/run_all.py](src/run_all.py) | Runs the stable V1 workflow. |

For more detail, read [docs/REPO_MAP.md](docs/REPO_MAP.md).

## Main result right now

The current V2 model run identifies:

```text
FFX002 — City of Fairfax Regional Library
```

as the strongest current public candidate.

The strongest current Prince William County library candidate is:

```text
PWC006 — Bull Run Library
```

The current port-sizing scenario result is:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

## Important rule

Use the results to decide what site data, stakeholder confirmation, and technical review should happen next.
