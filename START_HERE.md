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
```

The model is for early planning support only. It does not replace utility, engineering, permitting, accessibility, fire/AHJ, procurement, or stakeholder review.

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
Status: PASSED
All expected V2 outputs are present and all 12 V2 candidate sites are represented in the main output tables.
```

## V2 files to open first

After a successful V2 run, open these first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
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

## Main V2 input file

```text
data/inputs/real_sites_v2.csv
```

This is the active V2 candidate-site dataset.

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

## Simple project map

| File | Purpose |
|---|---|
| [docs/V2_CURRENT_WORKFLOW_GUIDE.md](docs/V2_CURRENT_WORKFLOW_GUIDE.md) | Main V2 workflow guide. |
| [src/run_v2.py](src/run_v2.py) | Runs the full V2 workflow. |
| [src/check_outputs_v2.py](src/check_outputs_v2.py) | Checks V2 generated outputs. |
| [src/build_v2_deliverable_package.py](src/build_v2_deliverable_package.py) | Builds the clean V2 deliverable package. |
| [src/ev_charger_model.py](src/ev_charger_model.py) | Main scoring and right-sizing model. |
| [src/run_all.py](src/run_all.py) | Runs the stable V1 workflow. |

For more detail, read [docs/REPO_MAP.md](docs/REPO_MAP.md).

## Main result right now

The current V2 model run identifies:

```text
FFX002 — City of Fairfax Regional Library
```

as the strongest current public candidate.

## Important rule

Do not treat a high score as permission to build.

Use the results to decide what site data, stakeholder confirmation, and technical review should happen next.
