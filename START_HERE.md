# Start Here

This is the shortest path for understanding and reproducing the project.

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

The model is for early planning support only and does not replace official review, engineering review, utility review, permitting, procurement, or stakeholder confirmation.

## Current active workflow

The active Phase 2 prototype is V2 on this branch:

```text
v2-expansion-planning
```

Read these first:

```text
docs/ACTIVE_DOCS_INDEX.md
docs/REVIEWER_GUIDE.md
docs/V2_CURRENT_WORKFLOW_GUIDE.md
docs/REPO_MAP.md
src/README.md
tableau/README.md
```

## Main public visual artifact

The main public-facing visual artifact is the interactive Tableau workbook:

[Open the EV Charging Site Readiness Workbook](https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite)

Tableau Public opens the workbook through one starting worksheet URL. Use the visible sheet tabs on the Tableau Public page to move between the readiness ranking, candidate maps, port-growth planning view, review-burden views, profile sensitivity views, port-sizing scenarios, utilization simulation, and action decision quadrant.

Local packaged workbook:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

Tableau documentation:

```text
tableau/README.md
```

Static PNG charts are still generated for reproducibility, GitHub previews, and the technical deliverable package, but they are no longer the main public-facing visual layer.

## Quickest V2 run

From the repository root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make setup
make run-v2
make check-v2
```

Useful follow-up checks:

```bash
make tableau-exports
make links
make status
```

Equivalent full review command:

```bash
make review
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
```

A healthy run should show:

```text
Status: PASSED
Copied files: 35/35
Synced files: 35/35
```

## What to open first

For public-facing review, open the Tableau workbook first:

```text
https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite
```

For technical reproducibility review, after a successful V2 run, open these generated package outputs first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

The package folder is the cleanest technical review folder because it collects the most important V2 outputs into one place.

## Main V2 input files

```text
data/inputs/real_sites_v2.csv
data/inputs/v2_port_sizing_scenarios.csv
```

`real_sites_v2.csv` is the active candidate-site dataset. `v2_port_sizing_scenarios.csv` controls the port-sizing stress-test assumptions.

## Main V2 decision table

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
port-sizing scenario sensitivity
right-sizing validation
major review flags
```

## Stable V1 workflow

Use `main` only when reproducing the stable V1 baseline workflow.

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

## Simple project map

| File | Purpose |
|---|---|
| [tableau/README.md](tableau/README.md) | Tableau workbook link, refresh notes, and workbook contents. |
| [docs/ACTIVE_DOCS_INDEX.md](docs/ACTIVE_DOCS_INDEX.md) | Clean index of active reviewer-facing docs. |
| [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md) | Best first guide for someone reviewing the repo. |
| [docs/V2_CURRENT_WORKFLOW_GUIDE.md](docs/V2_CURRENT_WORKFLOW_GUIDE.md) | Main V2 workflow guide. |
| [docs/REPO_MAP.md](docs/REPO_MAP.md) | Fuller repository map. |
| [src/README.md](src/README.md) | Script-by-script index. |
| [docs/checkpoints/README.md](docs/checkpoints/README.md) | Checkpoint and history index. |
| [src/run_v2.py](src/run_v2.py) | Runs the full 24-step V2 workflow. |
| [src/check_outputs_v2.py](src/check_outputs_v2.py) | Checks V2 generated outputs and package sync. |
| [src/build_tableau_exports.py](src/build_tableau_exports.py) | Regenerates Tableau-ready CSV inputs. |
| [src/ev_charger_model.py](src/ev_charger_model.py) | Main scoring and right-sizing model. |

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
