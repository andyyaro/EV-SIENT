# EV Charger Site-Readiness and Right-Sizing Prototype

![Model Pipeline Check](https://github.com/andyyaro/Future-City-Fellowship-/actions/workflows/model-check.yml/badge.svg)

This repository contains a Python planning-support prototype for comparing public EV charging candidate sites in Fairfax City and Prince William County.

The model evaluates sites using demand, implementation feasibility, site review, equity, and charger right-sizing signals. It supports early planning only; it is not a construction, procurement, or approval tool.

## Clean repository structure

```text
src/                  Python scripts
src/run_all.py
src/check_outputs.py
src/compare_to_baseline.py
src/create_baseline_snapshot.py
src/generate_run_summary.py
src/generate_results_interpretation.py
src/build_deliverable_package.py
src/ev_charger_model.py
src/validate_site_data.py
src/add_action_matrix.py
src/run_sensitivity_analysis.py
src/run_profile_analysis.py
src/plot_readiness_score_chart.py
src/plot_data_confidence_chart.py
src/plot_profile_rank_stability.py
src/plot_profile_score_heatmap.py
src/build_osm_amenities.py
src/plot_site_map.py

data/inputs/           Main input datasets
data/config/           Model configuration and output-check rules
data/baselines/        Curated benchmark snapshots
data/source_extracts/  Small model-ready source extracts
data/raw_exports/      Notes about raw exports not committed to the repo
data/outputs/          Generated local outputs; ignored by Git

docs/                  Project documentation and reporting files
requirements.txt       Python package list
README.md              Start here
```

## Install requirements

```bash
pip install -r requirements.txt
```

The project currently uses:

```text
pandas
numpy
matplotlib
```

## Main workflow

Run the full local workflow from the repository root:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```

`src/run_all.py` runs the validator, readiness/right-sizing model, action matrix, readiness chart, data confidence chart, sensitivity analysis, scoring profile analysis, profile visuals, readiness map, Markdown run summary, generated results interpretation, and output checks.

The package builder checks for `data/outputs/workflow_success.json`, which is written only after the full workflow passes. This helps avoid packaging stale outputs after a failed or partial run.

Manual step order:

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/add_action_matrix.py
python src/plot_readiness_score_chart.py
python src/plot_data_confidence_chart.py
python src/run_sensitivity_analysis.py
python src/run_profile_analysis.py
python src/plot_profile_rank_stability.py
python src/plot_profile_score_heatmap.py
python src/plot_site_map.py
python src/generate_run_summary.py
python src/generate_results_interpretation.py
python src/check_outputs.py
python src/build_deliverable_package.py
```

Optional amenities POI workflow:

```bash
python src/build_osm_amenities.py
```

## Main generated outputs

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/action_matrix.md
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/profile_results.csv
data/outputs/profile_rank_summary.csv
data/outputs/profile_comparison.md
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/baseline_comparison.csv
data/outputs/baseline_comparison.md
data/outputs/workflow_success.json
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/deliverable_package/
```

`site_results.csv` includes readiness, confidence, and action-matrix outputs:

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is

action_label = what to do next
```

More detail:

```text
docs/DATA_CONFIDENCE_SCORE.md
data/outputs/action_matrix.md
```

## Scoring profile analysis

`src/run_profile_analysis.py` tests whether rankings change when different planning priorities are emphasized.

Current profiles:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

Recommended profile visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

This is the main presentation visual because it is easiest to explain: the x-axis shows scoring profiles, the y-axis shows rank, and a flat line at `#1` means the site remains the top candidate across all profiles.

Supporting profile visual:

```text
data/outputs/charts/profile_score_heatmap.png
```

The heatmap remains available for people who want to see the actual score/rank values in each profile.

## Deliverable package

Build the local shareable package with:

```bash
python src/build_deliverable_package.py
```

Default package folder:

```text
data/outputs/deliverable_package/
```

The package includes charts, dynamic run outputs, key CSV tables, reporting documents, a package README, and a package manifest.

## Current candidate sites

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Current planning interpretation

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC002 — High-review candidate because of garage context
PWC004 — Tier 2 / strongest current PWC public-library candidate under future/reopened planning assumptions
PWC001 — Tier 3 / lower priority under current assumptions
PWC003 — Low public-priority / special-use because public access is limited
```

## Documentation guide

```text
docs/PROJECT_STATUS.md
docs/MODEL_FINDINGS_BRIEF.md
docs/MODEL_FINDINGS_REPORT.md
docs/PRESENTATION_OUTLINE.md
docs/RESULTS_INTERPRETATION.md
docs/READINESS_MAP_GUIDE.md
docs/DATA_CONFIDENCE_SCORE.md
docs/SITE_SCREENING_CHECKLIST.md
docs/ADDING_NEW_SITES_GUIDE.md
docs/STAKEHOLDER_DATA_REQUEST.md
docs/METHODOLOGY.md
docs/DATA_DICTIONARY.md
docs/DATA_SOURCES.md
docs/PROJECT_DECISIONS_LOG.md
```

Latest generated interpretation:

```text
data/outputs/results_interpretation.md
```

## Important limitation

The prototype is useful for transparent early planning, but any real project decision must be checked with the appropriate site owner, technical reviewers, permitting offices, and procurement process.
