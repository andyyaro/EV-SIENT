# Start Here

This file is the shortest path for understanding and reproducing the project.

## What this project does

This project compares public EV charging candidate sites in Fairfax City and Prince William County.

It helps answer:

```text
Which sites look most promising?
Which sites need better data?
What should we do next for each site?
```

The model is for early planning support only. It does not replace utility, engineering, permitting, accessibility, fire/AHJ, procurement, or stakeholder review.

## Quickest way to run everything

From the repository root:

```bash
git pull --rebase origin main
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## What success looks like

A successful run should show:

```text
Sanity check: PASSED
Baseline comparison: COMPLETED
Missing files: 0
```

The output summary should also show `OK` for the main generated files.

## Files to open first

Open these in this order:

```text
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/action_matrix.md
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/site_readiness_map.png
```

## Most important input file

```text
data/inputs/real_sites_v1.csv
```

This is the main candidate-site dataset.

## Most important output file

```text
data/outputs/site_results.csv
```

This file contains the main model results, including:

```text
readiness_score
data_confidence_score
action_label
recommended_ports_now
recommendation_tier
```

## Simple project map

```text
src/run_all.py                  Run the full workflow
src/ev_charger_model.py         Main scoring and right-sizing model
src/add_action_matrix.py        Adds next-action labels
src/check_outputs.py            Checks that outputs are valid
src/build_deliverable_package.py Builds the shareable package
```

For more detail, read:

```text
docs/REPO_MAP.md
```

## Main result right now

The current model run identifies `FFX002 — City of Fairfax Regional Library` as the strongest current candidate.

The result is stable across the base model, sensitivity analysis, and scoring-profile analysis.

## Important rule

Do not treat a high score as permission to build.

Use the results to decide what site data, stakeholder confirmation, and technical review should happen next.
