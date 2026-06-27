# Source Script Index

This folder contains the Python scripts for the EV charging site-readiness and right-sizing prototype.

Use this file to find the right script without reading every file.

## Start here

| Script | Purpose |
|---|---|
| `run_v2.py` | Runs the full active V2 model workflow from scoring through deliverable package creation. |
| `check_outputs_v2.py` | Verifies the active V2 outputs, package sync, baseline comparison, scenario layer, and site coverage. |
| `build_tableau_exports.py` | Regenerates Tableau-ready CSV inputs from current V2 outputs. |
| `ev_charger_model.py` | Core scoring and right-sizing model shared by V1 and V2. |

Recommended model run from the repository root:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Recommended Tableau export refresh after the model run:

```bash
python src/build_tableau_exports.py
```

Equivalent Makefile workflow:

```bash
make full-v2-tableau
```

## Public visual layer

The main public-facing visual artifact is the Tableau workbook, not the static PNG chart set.

| File | Purpose |
|---|---|
| `build_tableau_exports.py` | Builds generated CSV inputs under `data/outputs/tableau/` for the packaged Tableau workbook. |
| `../tableau/EV_Charging_Site_Readiness_Workbook.twbx` | Packaged Tableau workbook. |
| `../tableau/README.md` | Tableau workbook documentation, refresh instructions, and Tableau Public link. |

Generated Tableau CSVs are ignored by Git by default. Regenerate them locally from current V2 outputs instead of editing them by hand.

## Active V2 orchestration

| Script | Purpose |
|---|---|
| `run_v2.py` | Main active model workflow runner. This is the safest entry point for V2 model outputs. |
| `check_outputs_v2.py` | Main active output checker. Run this after every V2 workflow run. |
| `write_v2_workflow_success_marker.py` | Writes the workflow success marker and expected-output manifest result. |
| `compare_v2_to_baseline.py` | Compares current V2 outputs against the committed V2 baseline snapshot. |
| `build_v2_deliverable_package.py` | Copies selected V2 results into the clean reviewer package. |

## V2 analysis layers

| Script | Purpose |
|---|---|
| `build_v2_executive_summary.py` | Creates the executive decision table and report. |
| `run_electrical_risk_scenarios.py` | Screens electrical-feasibility and review-risk scenarios. |
| `run_right_sizing_scenarios.py` | Creates near-term, 2035, and 2050 right-sizing recommendations. |
| `run_port_utilization_simulation.py` | Runs simple port-use simulation using demand and session assumptions. |
| `run_port_sizing_scenario_analysis.py` | Stress-tests port recommendations under alternate demand and charging assumptions. |
| `validate_right_sizing_with_simulation.py` | Compares right-sizing recommendations with simulation results. |
| `generate_run_summary_v2.py` | Generates a high-level V2 run summary. |

## Public-data upgrade helpers

| Script | Purpose |
|---|---|
| `build_v2_public_data_upgrades.py` | Builds public-data upgrade recommendations and related review outputs. |
| `check_v2_public_data_upgrade_inputs.py` | Checks inputs for public-data upgrade work. |
| `check_v2_next_batch_readiness.py` | Checks whether next-batch candidate-site data is ready. |
| `triage_v2_candidate_backlog.py` | Helps triage future candidate sites. |
| `build_afdc_ev_supply_counts.py` | Builds EV supply counts from AFDC-style source extracts. |

## Static chart and map support outputs

Static PNG charts are still generated for reproducibility, GitHub previews, and the technical deliverable package. They are no longer the main public-facing visual layer; Tableau is.

| Script | Purpose |
|---|---|
| `plot_readiness_score_chart.py` | Creates readiness score PNG charts for generated-output review. |
| `plot_data_confidence_chart.py` | Creates data-confidence PNG charts for generated-output review. |
| `plot_profile_score_heatmap.py` | Creates scoring-profile PNG heatmaps for generated-output review. |
| `plot_profile_rank_stability.py` | Creates profile rank-stability PNG charts for generated-output review. |
| `plot_site_map.py` | Creates the standard site-readiness PNG map. |
| `plot_site_decision_map.py` | Creates the V2 GIS decision PNG map. |
| `plot_site_decision_map_all_labels.py` | Creates the README/report decision-map PNG variant with all site labels. |
| `chart_style.py` | Shared chart styling helpers. |
| `check_chart_font.py` | Checks chart font availability. |

## Shared and V1 scripts

| Script | Purpose |
|---|---|
| `run_all.py` | Runs the stable V1 workflow. |
| `check_outputs.py` | Checks V1 generated outputs. |
| `build_deliverable_package.py` | Builds the V1 deliverable package. |
| `validate_site_data.py` | Validates candidate-site input data. |
| `add_action_matrix.py` | Adds next-action labels to model outputs. |
| `run_sensitivity_analysis.py` | Runs demand/cost sensitivity analysis. |
| `run_profile_analysis.py` | Runs scoring-profile analysis. |
| `generate_results_interpretation.py` | Generates interpretation text for results. |
| `generate_demo_sites.py` | Creates synthetic demo candidate sites. |
| `run_demo.py` | Runs the synthetic demo workflow. |

## Import safety rule

Avoid moving scripts unless you update all of these together:

```text
imports
src/run_v2.py
src/build_tableau_exports.py
GitHub Actions workflows
Makefile
documentation links
reproducibility commands
baseline/package checks
Tableau workbook refresh instructions
```

For now, the repo is optimized for a beginner-friendly flat script layout, with this README acting as the navigation layer.
