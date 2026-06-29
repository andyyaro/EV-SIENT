# Repository Map

This file explains the main parts of the repo without making you read every file.

## Start files

- [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md) — clean index of active reviewer-facing docs
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md) — main landing page for the active V2 workflow
- [START_HERE.md](../START_HERE.md) — shortest project entry point
- [REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md) — step-by-step local reproduction checklist
- [README.md](../README.md) — project overview
- [tableau/README.md](../tableau/README.md) — Tableau workbook, public link, and refresh instructions
- [checkpoints/README.md](checkpoints/README.md) — checkpoint and history index

## Main folders

- [src/](../src/) — Python scripts
- [data/inputs/](../data/inputs/) — input datasets
- [data/config/](../data/config/) — scoring, checker, and output manifest configuration
- [data/source_extracts/](../data/source_extracts/) — source extracts and source notes
- [data/baselines/](../data/baselines/) — committed baseline snapshots
- [data/outputs/](../data/outputs/) — generated local outputs ignored by Git
- `data/outputs/tableau/` — generated Tableau CSV inputs ignored by Git
- `data/demo/` — generated local-only synthetic demo outputs; this folder may not exist until demo mode is run
- [docs/](../docs/) — active documentation and project notes
- [docs/checkpoints/](checkpoints/) — checkpoint/history notes moved out of the active-docs path
- [tableau/](../tableau/) — packaged Tableau workbook and Tableau documentation


## Public website and user-facing assistant docs

The public website is documented at:

```text
docs/PUBLIC_WEBSITE_STATUS.md
```

The assistant-readable branch should contain public-safe project context, not private deployment or operations internals.

User-facing assistant docs:

```text
docs/AI_ASSISTANT_USER_GUIDE.md
docs/MODEL_LIMITATIONS.md
```

These files help the AI Assistant answer project-scope and limitation questions without relying on private deployment documentation.

## Website source files

The inspected V2 branch is primarily the model/reproducibility source of truth. Deployed website HTML files may be maintained separately from this branch unless intentionally added later.

Do not add private deployment notes, credentials, exact internal resource identifiers, or production-only operational files to this assistant-readable branch unless they are explicitly redacted and intended for project-facing use.

## Active V2 workflow

Run the active V2 workflow and Tableau export validation with:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make setup
make full-v2-tableau
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

The V2 runner has 24 steps and generates the active Phase 2 prototype outputs and the clean package at:

```text
data/outputs/deliverable_package_v2/
```

A healthy V2 package reports:

```text
Copied files: 35/35
Synced files: 35/35
```

A healthy Tableau export check reports:

```text
TABLEAU EXPORT CHECK
--------------------
Status: PASSED
Checked exports: 15/15
Candidate sites represented: 12/12
Exact export set, required columns, row counts, numeric fields, and site coverage are valid.
```

## Public visual layer

The main public-facing visual artifact is Tableau:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
tableau/README.md
```

Static PNG charts remain generated support outputs for reproducibility, GitHub previews, and the technical deliverable package.

## Stable V1 workflow

Run the stable V1 workflow with:

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
```

The V1 package is created at:

```text
data/outputs/deliverable_package/
```

## Main V2 scripts

| File | Purpose |
|---|---|
| [src/run_v2.py](../src/run_v2.py) | Runs the full active 24-step V2 workflow. |
| [src/check_outputs_v2.py](../src/check_outputs_v2.py) | Checks V2 outputs, required files, scenario layer, package, manifest, baseline comparison, and all 12 candidate sites. |
| [src/build_tableau_exports.py](../src/build_tableau_exports.py) | Regenerates the 15 Tableau-ready CSV inputs from current V2 outputs. |
| [src/check_tableau_exports.py](../src/check_tableau_exports.py) | Validates the exact Tableau export file set, schemas, row counts, numeric fields, and 12-site coverage. |
| [src/build_v2_deliverable_package.py](../src/build_v2_deliverable_package.py) | Builds the clean 35-file V2 deliverable package. |
| [src/build_v2_executive_summary.py](../src/build_v2_executive_summary.py) | Builds the V2 executive site summary table and report. |
| [src/run_electrical_risk_scenarios.py](../src/run_electrical_risk_scenarios.py) | Runs V2 electrical-feasibility scenario screening. |
| [src/run_right_sizing_scenarios.py](../src/run_right_sizing_scenarios.py) | Builds near-term, 2035, and 2050 port recommendations. |
| [src/run_port_utilization_simulation.py](../src/run_port_utilization_simulation.py) | Runs the simple V2 port-use simulation. |
| [src/run_port_sizing_scenario_analysis.py](../src/run_port_sizing_scenario_analysis.py) | Stress-tests port recommendations under alternate charging and demand assumptions. |
| [src/validate_right_sizing_with_simulation.py](../src/validate_right_sizing_with_simulation.py) | Compares right-sizing recommendations with port-use simulation results. |
| [src/generate_run_summary_v2.py](../src/generate_run_summary_v2.py) | Generates the V2 run summary. |
| [src/write_v2_workflow_success_marker.py](../src/write_v2_workflow_success_marker.py) | Writes the V2 workflow manifest. |
| [src/compare_v2_to_baseline.py](../src/compare_v2_to_baseline.py) | Compares stable V2 outputs against the V2 baseline snapshot. |

## Shared / V1 scripts

| File | Purpose |
|---|---|
| [src/ev_charger_model.py](../src/ev_charger_model.py) | Main readiness and right-sizing model used by V1 and V2. |
| [src/validate_site_data.py](../src/validate_site_data.py) | Checks input data. |
| [src/add_action_matrix.py](../src/add_action_matrix.py) | Adds next-action labels. |
| [src/run_sensitivity_analysis.py](../src/run_sensitivity_analysis.py) | Tests rankings under alternate demand/cost assumptions. |
| [src/run_profile_analysis.py](../src/run_profile_analysis.py) | Tests rankings under alternate scoring-priority profiles. |
| [src/plot_readiness_score_chart.py](../src/plot_readiness_score_chart.py) | Creates readiness score charts. |
| [src/plot_data_confidence_chart.py](../src/plot_data_confidence_chart.py) | Creates data-confidence charts. |
| [src/plot_profile_score_heatmap.py](../src/plot_profile_score_heatmap.py) | Creates profile score heatmaps. |
| [src/plot_profile_rank_stability.py](../src/plot_profile_rank_stability.py) | Creates profile rank-stability charts. |
| [src/plot_site_map.py](../src/plot_site_map.py) | Creates candidate-site readiness maps. |
| [src/run_all.py](../src/run_all.py) | Runs the stable V1 workflow. |
| [src/check_outputs.py](../src/check_outputs.py) | Checks V1 generated outputs. |
| [src/build_deliverable_package.py](../src/build_deliverable_package.py) | Builds the V1 shareable package. |
| [src/run_demo.py](../src/run_demo.py) | Runs a synthetic larger-site demo workflow. |
| [src/generate_demo_sites.py](../src/generate_demo_sites.py) | Creates synthetic demo candidate sites. |

## Main input and config files

| File | Purpose |
|---|---|
| [data/inputs/real_sites_v2.csv](../data/inputs/real_sites_v2.csv) | Active V2 candidate-site input dataset. |
| [data/inputs/v2_port_sizing_scenarios.csv](../data/inputs/v2_port_sizing_scenarios.csv) | V2 port-sizing scenario assumptions. |
| [data/inputs/real_sites_v1.csv](../data/inputs/real_sites_v1.csv) | Stable V1 candidate-site input dataset. |
| [data/inputs/new_sites_template.csv](../data/inputs/new_sites_template.csv) | Template for new candidate sites. |
| [data/config/scoring_profiles.csv](../data/config/scoring_profiles.csv) | Scoring-priority profiles. |
| [data/baselines/v2_baseline_snapshot.json](../data/baselines/v2_baseline_snapshot.json) | V2 baseline snapshot for comparison. |

## Main V2 generated outputs

Important V2 output files include:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_action_matrix.md
data/outputs/v2_data_quality_report.csv
data/outputs/v2_sensitivity_summary.csv
data/outputs/v2_profile_results.csv
data/outputs/v2_profile_rank_summary.csv
data/outputs/v2_profile_comparison.md
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_electrical_feasibility_report.md
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_right_sizing_report.md
data/outputs/v2_port_utilization_simulation.csv
data/outputs/v2_port_utilization_simulation_report.md
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/v2_right_sizing_validation.csv
data/outputs/v2_right_sizing_validation_report.md
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
data/outputs/v2_results_interpretation.md
data/outputs/v2_run_summary.md
data/outputs/v2_baseline_comparison.md
data/outputs/v2_workflow_success.json
```

Important Tableau generated outputs include:

```text
data/outputs/tableau/tableau_site_readiness.csv
data/outputs/tableau/tableau_site_map.csv
data/outputs/tableau/tableau_map_points.csv
data/outputs/tableau/tableau_port_growth.csv
data/outputs/tableau/tableau_review_burden.csv
data/outputs/tableau/tableau_review_burden_map.csv
data/outputs/tableau/tableau_profile_score_heatmap.csv
data/outputs/tableau/tableau_profile_subscore_heatmap.csv
data/outputs/tableau/tableau_profile_rank_stability.csv
data/outputs/tableau/tableau_data_confidence.csv
data/outputs/tableau/tableau_data_quality_issues.csv
data/outputs/tableau/tableau_port_sizing_scenario_heatmap.csv
data/outputs/tableau/tableau_port_utilization_simulation.csv
data/outputs/tableau/tableau_action_recommendation_matrix.csv
data/outputs/tableau/tableau_action_decision_quadrant_clean.csv
```

Important support chart files include:

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_utilization_simulation.png
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
```

## Deliverable packages

| Folder | Purpose |
|---|---|
| `data/outputs/deliverable_package_v2/` | Clean active V2 review package. |
| `data/outputs/deliverable_package/` | Stable V1 review package. |

The V2 package contains:

```text
README.md
package_manifest.json
inputs/
reports/
tables/
charts/
manifests/
```

## Documentation organization

| Folder or file | Purpose |
|---|---|
| [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md) | Clean active-docs index for reviewers. |
| [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) | Main reviewer guide. |
| [REPO_MAP.md](REPO_MAP.md) | This repository map. |
| [checkpoints/README.md](checkpoints/README.md) | Checkpoint/history index. |
| [checkpoints/](checkpoints/) | Moved implementation history and milestone notes. |

## Demo mode for larger tests

For a full 50-site synthetic test, use:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

This generates demo data, validates it, runs the model, adds action labels, runs sensitivity analysis, runs scoring-profile analysis, creates scalable visuals, and writes a demo summary.

See [DEMO_MODE_GUIDE.md](DEMO_MODE_GUIDE.md).

## Recommended V2 reading path

1. [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md)
2. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
3. [../tableau/README.md](../tableau/README.md)
4. `data/outputs/deliverable_package_v2/README.md`
5. `data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md`
6. `data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md`
7. `data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md`
8. `data/outputs/deliverable_package_v2/reports/v2_run_summary.md`
