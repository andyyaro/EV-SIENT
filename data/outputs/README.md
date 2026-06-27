# Generated Outputs

This folder is for files created when the scripts run locally.

Generated outputs are ignored by Git so local runs do not clutter `git status`.

## Active V2 generated outputs

The active V2 workflow is run with:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Main V2 output files:

```text
v2_site_results.csv
v2_action_matrix.md
v2_data_quality_report.csv
v2_sensitivity_results.csv
v2_sensitivity_summary.csv
v2_profile_results.csv
v2_profile_rank_summary.csv
v2_profile_comparison.md
v2_electrical_scenario_results.csv
v2_electrical_risk_summary.csv
v2_electrical_feasibility_report.md
v2_right_sizing_scenarios.csv
v2_right_sizing_report.md
v2_port_utilization_simulation.csv
v2_port_utilization_simulation_report.md
v2_port_sizing_scenario_results.csv
v2_port_sizing_scenario_summary.csv
v2_port_sizing_scenario_report.md
v2_right_sizing_validation.csv
v2_right_sizing_validation_report.md
v2_executive_site_summary.csv
v2_executive_site_summary.md
v2_results_interpretation.md
v2_run_summary.md
v2_baseline_comparison.json
v2_baseline_comparison.md
v2_workflow_success.json
```

The main V2 executive table is:

```text
v2_executive_site_summary.csv
```

It combines ranking, readiness score, data confidence, electrical risk, right-sizing, port-use simulation, port-sizing scenario sensitivity, right-sizing validation, and review flags.

Key scenario-sensitivity fields in the executive table:

```text
scenario_max_min_ports_2050_high
scenario_future_capacity_gap
scenario_sensitivity_level
scenario_stress_note
```

The main V2 port-sizing scenario outputs are:

```text
v2_port_sizing_scenario_results.csv
v2_port_sizing_scenario_summary.csv
v2_port_sizing_scenario_report.md
```

These stress-test port recommendations under alternate charging-duration, charging-window, peak-demand, and future-demand assumptions.

## Active V2 chart outputs

Important V2 charts:

```text
charts/v2_readiness_score_chart.png
charts/v2_polished_readiness_score_chart.png
charts/v2_data_confidence_chart.png
charts/v2_profile_score_heatmap.png
charts/v2_profile_rank_stability_chart.png
charts/v2_site_readiness_map.png
charts/v2_site_decision_map.png
charts/v2_site_decision_map_readme.png
charts/v2_port_utilization_simulation.png
charts/v2_port_sizing_scenario_heatmap.png
charts/v2/utilization_vs_ports_<site>.png
```

Generated Matplotlib chart text uses the shared Times New Roman style.

The README decision-map asset is copied to:

```text
../../docs/assets/charts/v2_site_decision_map_readme.png
```

The output checker verifies that this committed README asset matches the generated README decision-map chart.

## V2 deliverable package

The V2 workflow creates a clean local review folder:

```text
deliverable_package_v2/
```

Package structure:

```text
deliverable_package_v2/README.md
deliverable_package_v2/package_manifest.json
deliverable_package_v2/inputs/
deliverable_package_v2/reports/
deliverable_package_v2/tables/
deliverable_package_v2/charts/
deliverable_package_v2/manifests/
```

Start with:

```text
deliverable_package_v2/README.md
deliverable_package_v2/charts/v2_site_decision_map.png
deliverable_package_v2/charts/v2_site_decision_map_readme.png
deliverable_package_v2/reports/v2_executive_site_summary.md
deliverable_package_v2/tables/v2_executive_site_summary.csv
deliverable_package_v2/reports/v2_right_sizing_validation_report.md
deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
deliverable_package_v2/reports/v2_run_summary.md
deliverable_package_v2/reports/v2_baseline_comparison.md
```

The V2 package builder uses a clean rebuild by default, so stale copied files are removed before the package is recreated.

A healthy package has:

```text
Copied files: 35/35
Synced files: 35/35
```

The package manifest stores SHA-256 hashes for each source output and copied package file.

## Stable V1 generated outputs

The stable V1 workflow is run with:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```

Main V1 output files:

```text
data_quality_report.csv
site_results.csv
action_matrix.md
sensitivity_results.csv
sensitivity_summary.csv
readiness_score_chart.png
profile_results.csv
profile_rank_summary.csv
profile_comparison.md
model_run_summary.md
results_interpretation.md
baseline_comparison.csv
baseline_comparison.md
workflow_success.json
```

`site_results.csv` includes readiness, confidence, and action-matrix fields.

```text
readiness_score = how promising the site looks

data_confidence_score = how complete/confirmed the current input data is

action_label = what to do next
```

## Stable V1 chart outputs

```text
charts/readiness_score_chart.png
charts/data_confidence_chart.png
charts/profile_rank_stability_chart.png
charts/profile_score_heatmap.png
charts/site_readiness_map.png
charts/utilization_vs_ports_<site>.png
```

## Stable V1 deliverable package

The V1 package builder creates:

```text
deliverable_package/
```

## Optional OSM amenities outputs

```text
amenities_osm_summary_0_5mi.csv
amenities_osm_pois_0_5mi.csv
```

## Regenerate outputs

From the repository root, regenerate V2 outputs with:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
```

Regenerate V1 outputs with:

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
```

<!-- TABLEAU_OUTPUTS_START -->
## Tableau generated outputs

Tableau-ready CSV exports are generated under:

`data/outputs/tableau/`

These files are created by:

`python src/build_tableau_exports.py`

They are generated inputs for the packaged Tableau workbook and are ignored by Git by default.

The committed Tableau artifact is:

`tableau/EV_Charging_Site_Readiness_Workbook.twbx`

The committed export logic is:

`src/build_tableau_exports.py`

Do not manually edit the generated Tableau CSVs. Regenerate them from the model outputs instead.
<!-- TABLEAU_OUTPUTS_END -->
