## Generated documents and artifacts from the model run

When the V2 workflow is reproduced successfully, the model writes a set of generated outputs under:

```text
data/outputs/
```

These outputs are not all the same type. Some are human-readable Markdown reports, some are CSV tables, some are JSON manifests, some are chart images, and some are Tableau-ready CSV exports.

### Human-readable Markdown reports

These are the main generated documents to open and read after running the model:

```text
data/outputs/v2_executive_site_summary.md
data/outputs/v2_results_interpretation.md
data/outputs/v2_run_summary.md
data/outputs/v2_action_matrix.md
data/outputs/v2_profile_comparison.md
data/outputs/v2_electrical_feasibility_report.md
data/outputs/v2_right_sizing_report.md
data/outputs/v2_port_utilization_simulation_report.md
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/v2_right_sizing_validation_report.md
data/outputs/v2_baseline_comparison.md
```

What each report is for:

```text
v2_executive_site_summary.md
High-level site summary for reviewing candidate sites, ranks, readiness, recommendation tiers, and planning notes.

v2_results_interpretation.md
Narrative interpretation of the model results and what the output patterns mean.

v2_run_summary.md
Summary of the completed run, including workflow status and key generated outputs.

v2_action_matrix.md
Action-oriented recommendation matrix for interpreting next steps by site.

v2_profile_comparison.md
Comparison of scenario/profile results and how site rankings change across scoring profiles.

v2_electrical_feasibility_report.md
Electrical feasibility and risk-screening narrative.

v2_right_sizing_report.md
Right-sizing report describing recommended charger/port planning implications.

v2_port_utilization_simulation_report.md
Report explaining simulated port utilization and operational pressure.

v2_port_sizing_scenario_report.md
Report summarizing port-sizing scenario results across different planning assumptions.

v2_right_sizing_validation_report.md
Validation report comparing right-sizing recommendations against utilization and scenario outputs.

v2_baseline_comparison.md
Markdown summary comparing current V2 outputs against the stored V2 baseline snapshot.
```

### Generated CSV tables

These are the main generated table outputs:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_data_quality_report.csv
data/outputs/v2_sensitivity_results.csv
data/outputs/v2_sensitivity_summary.csv
data/outputs/v2_profile_results.csv
data/outputs/v2_profile_rank_summary.csv
data/outputs/v2_electrical_scenario_results.csv
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_port_utilization_simulation.csv
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_right_sizing_validation.csv
data/outputs/v2_executive_site_summary.csv
```

What the most important CSV files are for:

```text
v2_site_results.csv
Core model output table with site-level scores, rankings, and recommendation fields.

v2_executive_site_summary.csv
Clean executive summary table for review, reporting, and dashboard use.

v2_data_quality_report.csv
Data completeness and confidence checks by site and field.

v2_sensitivity_results.csv
Site results under different scoring-weight sensitivity cases.

v2_sensitivity_summary.csv
Summary of how stable or unstable each site is across sensitivity cases.

v2_profile_results.csv
Scenario/profile-level scoring results.

v2_profile_rank_summary.csv
Rank-stability summary across scoring profiles.

v2_electrical_scenario_results.csv
Electrical feasibility results under different electrical/capacity scenarios.

v2_electrical_risk_summary.csv
Summary of electrical risk indicators by site.

v2_right_sizing_scenarios.csv
Right-sizing output by site.

v2_port_utilization_simulation.csv
Simulated charger/port utilization results.

v2_port_sizing_scenario_results.csv
Detailed site-by-scenario port sizing results.

v2_port_sizing_scenario_summary.csv
Summary of the port-sizing scenario set.

v2_right_sizing_validation.csv
Validation table comparing right-sizing recommendations against utilization/scenario indicators.
```

### Generated JSON manifests

These files are useful for automated checks and reproducibility tracking:

```text
data/outputs/v2_workflow_success.json
data/outputs/v2_baseline_comparison.json
data/outputs/v2_workflow_completion_manifest.json
data/outputs/deliverable_package_v2/package_manifest.json
```

What they are for:

```text
v2_workflow_success.json
Machine-readable success marker for the completed V2 workflow.

v2_baseline_comparison.json
Machine-readable comparison between the current run and the stored baseline snapshot.

v2_workflow_completion_manifest.json
Completion manifest listing run status and generated outputs.

deliverable_package_v2/package_manifest.json
Manifest for the clean deliverable package.
```

### Generated chart images

The workflow also produces static chart/image outputs:

```text
data/outputs/charts/v2_readiness_score_chart.png
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

A copy of the README decision-map image is also synced to:

```text
docs/assets/charts/v2_site_decision_map_readme.png
```

### Tableau-ready CSV exports

After running:

```bash
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

the Tableau-ready files are generated under:

```text
data/outputs/tableau/
```

Expected Tableau export files:

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

These CSV files support the packaged Tableau workbook:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

### Clean deliverable package

The workflow also builds a cleaner review package under:

```text
data/outputs/deliverable_package_v2/
```

This package is meant to gather the most important reports, tables, charts, and manifests in a cleaner structure for review.

Important folders inside the package:

```text
data/outputs/deliverable_package_v2/reports/
data/outputs/deliverable_package_v2/tables/
data/outputs/deliverable_package_v2/charts/
data/outputs/deliverable_package_v2/inputs/
data/outputs/deliverable_package_v2/manifests/
```

Important package-level files:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/package_manifest.json
```

The package should include copied/synced versions of the major reports, tables, and charts listed above.

### Quick review order after a successful run

For a fast manual QA review, open these first:

```text
1. data/outputs/v2_run_summary.md
2. data/outputs/v2_executive_site_summary.md
3. data/outputs/v2_results_interpretation.md
4. data/outputs/v2_right_sizing_validation_report.md
5. data/outputs/v2_port_sizing_scenario_report.md
6. data/outputs/v2_baseline_comparison.md
7. data/outputs/deliverable_package_v2/README.md
8. data/outputs/deliverable_package_v2/package_manifest.json
```

Then review the Tableau export folder:

```text
data/outputs/tableau/
```

and open the packaged workbook if Tableau Desktop or Tableau Public is available:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```
