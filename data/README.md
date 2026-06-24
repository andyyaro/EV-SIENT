# Data Folder

This folder stores input datasets, configuration files, source extracts, baseline snapshots, raw-export notes, and generated local outputs.

## Structure

- [data/inputs/](inputs/) — main model input CSVs
- [data/config/](config/) — model configuration, output manifest, and output-check rules
- [data/source_extracts/](source_extracts/) — small model-ready extracts
- [data/baselines/](baselines/) — committed benchmark snapshots
- [data/raw_exports/](raw_exports/) — notes about raw exports not committed to the repo
- [data/outputs/](outputs/) — generated local outputs ignored by Git

## Main input files

| File | Purpose |
|---|---|
| [data/inputs/real_sites_v1.csv](inputs/real_sites_v1.csv) | Current real candidate-site dataset. |
| [data/inputs/sites_demo.csv](inputs/sites_demo.csv) | Small starter/demo dataset. |
| [data/inputs/new_sites_template.csv](inputs/new_sites_template.csv) | Template for future candidate-site rows. |

Use [docs/SITE_SCREENING_CHECKLIST.md](../docs/SITE_SCREENING_CHECKLIST.md) and [docs/ADDING_NEW_SITES_GUIDE.md](../docs/ADDING_NEW_SITES_GUIDE.md) before copying new rows into [data/inputs/real_sites_v1.csv](inputs/real_sites_v1.csv).

## Config files

| File | Purpose |
|---|---|
| [data/config/output_manifest_v1.json](config/output_manifest_v1.json) | Expected outputs, checker-required files, and package contents. |
| [data/config/scoring_profiles.csv](config/scoring_profiles.csv) | Alternative scoring-priority profiles used by [src/run_profile_analysis.py](../src/run_profile_analysis.py). |
| [data/config/output_check_rules_v1.json](config/output_check_rules_v1.json) | V1 output-check expectations used by [src/check_outputs.py](../src/check_outputs.py). |

## Baseline snapshots

Committed benchmark outputs live in [data/baselines/v1_baseline/](baselines/v1_baseline/).

## Generated outputs

Generated outputs are written to:

- [data/outputs/](outputs/)
- [data/outputs/charts/](outputs/charts/)
- [data/outputs/deliverable_package/](outputs/deliverable_package/)

Typical generated files:

- [data/outputs/data_quality_report.csv](outputs/data_quality_report.csv)
- [data/outputs/site_results.csv](outputs/site_results.csv)
- [data/outputs/action_matrix.md](outputs/action_matrix.md)
- [data/outputs/sensitivity_results.csv](outputs/sensitivity_results.csv)
- [data/outputs/sensitivity_summary.csv](outputs/sensitivity_summary.csv)
- [data/outputs/profile_results.csv](outputs/profile_results.csv)
- [data/outputs/profile_rank_summary.csv](outputs/profile_rank_summary.csv)
- [data/outputs/profile_comparison.md](outputs/profile_comparison.md)
- [data/outputs/model_run_summary.md](outputs/model_run_summary.md)
- [data/outputs/results_interpretation.md](outputs/results_interpretation.md)
- [data/outputs/baseline_comparison.csv](outputs/baseline_comparison.csv)
- [data/outputs/baseline_comparison.md](outputs/baseline_comparison.md)
- [data/outputs/workflow_success.json](outputs/workflow_success.json)
- [data/outputs/amenities_osm_summary_0_5mi.csv](outputs/amenities_osm_summary_0_5mi.csv)
- [data/outputs/amenities_osm_pois_0_5mi.csv](outputs/amenities_osm_pois_0_5mi.csv)
- [data/outputs/charts/readiness_score_chart.png](outputs/charts/readiness_score_chart.png)
- [data/outputs/charts/data_confidence_chart.png](outputs/charts/data_confidence_chart.png)
- [data/outputs/charts/profile_rank_stability_chart.png](outputs/charts/profile_rank_stability_chart.png)
- [data/outputs/charts/profile_score_heatmap.png](outputs/charts/profile_score_heatmap.png)
- [data/outputs/charts/site_readiness_map.png](outputs/charts/site_readiness_map.png)

Recommended profile-analysis visual: [data/outputs/charts/profile_rank_stability_chart.png](outputs/charts/profile_rank_stability_chart.png)

Supporting profile-analysis visual: [data/outputs/charts/profile_score_heatmap.png](outputs/charts/profile_score_heatmap.png)

[workflow_success.json](outputs/workflow_success.json) is created only after [src/run_all.py](../src/run_all.py) passes. The deliverable package builder checks it before packaging generated outputs.

Files under [data/outputs/](outputs/) are local generated artifacts and are ignored by Git.

## Source documentation files

- [data/source_dataset_log.csv](source_dataset_log.csv)
- [data/dataset_metadata.csv](dataset_metadata.csv)

## Source extracts

Small extracts live in [data/source_extracts/](source_extracts/).

Examples:

- [acs_equity_inputs_1mi.csv](source_extracts/acs_equity_inputs_1mi.csv)
- [acs_equity_index_1mi.csv](source_extracts/acs_equity_index_1mi.csv)
- [official_facility_hours_parking_v1.csv](source_extracts/official_facility_hours_parking_v1.csv)
- [amenity_official_source_inventory_v1.csv](source_extracts/amenity_official_source_inventory_v1.csv)
- [amenities_0_5mi_v2_official_supported.csv](source_extracts/amenities_0_5mi_v2_official_supported.csv)
- [amenities_0_5mi_v3_osm_run_summary.csv](source_extracts/amenities_0_5mi_v3_osm_run_summary.csv)
- [amenities_0_5mi_v4_osm_reviewed.csv](source_extracts/amenities_0_5mi_v4_osm_reviewed.csv)
- [electrical_feasibility_v1.csv](source_extracts/electrical_feasibility_v1.csv)
- [local_ev_adoption_v1.csv](source_extracts/local_ev_adoption_v1.csv)
- [sensitivity_scenarios_v1.csv](source_extracts/sensitivity_scenarios_v1.csv)
- [site_screening_checklist.csv](source_extracts/site_screening_checklist.csv)
- [stakeholder_data_request_fields.csv](source_extracts/stakeholder_data_request_fields.csv)
- [stakeholder_response_tracker.csv](source_extracts/stakeholder_response_tracker.csv)

## Site screening checklist

Use [data/source_extracts/site_screening_checklist.csv](source_extracts/site_screening_checklist.csv) before adding new candidate sites.

## Stakeholder follow-up tracker

Use [data/source_extracts/stakeholder_response_tracker.csv](source_extracts/stakeholder_response_tracker.csv) to record outreach status, response summaries, source dates, confidence levels, and whether a model update is needed.

## Raw exports

Raw-export notes live in [data/raw_exports/README.md](raw_exports/README.md).
