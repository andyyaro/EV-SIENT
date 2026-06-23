# Data Folder

This folder stores input datasets, configuration files, source extracts, baseline snapshots, raw-export notes, and generated local outputs.

## Structure

```text
data/inputs/           Main model input CSVs
data/config/           Model configuration and output-check rules
data/source_extracts/  Small model-ready extracts
data/baselines/        Committed benchmark snapshots
data/raw_exports/      Notes about raw exports not committed to the repo
data/outputs/          Generated local outputs ignored by Git
```

## Main input files

```text
data/inputs/real_sites_v1.csv   Current real candidate-site dataset
data/inputs/sites_demo.csv      Small starter/demo dataset
```

## Config files

```text
data/config/scoring_profiles.csv
data/config/output_check_rules_v1.json
```

`scoring_profiles.csv` defines the alternative scoring-priority profiles used by `src/run_profile_analysis.py`.

`output_check_rules_v1.json` defines V1 output-check expectations used by `src/check_outputs.py`.

## Baseline snapshots

Committed benchmark outputs live in:

```text
data/baselines/v1_baseline/
```

## Generated outputs

Generated outputs are written to:

```text
data/outputs/
data/outputs/charts/
data/outputs/deliverable_package/
```

Typical generated files:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
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
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/deliverable_package/
```

Recommended profile-analysis visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

Supporting profile-analysis visual:

```text
data/outputs/charts/profile_score_heatmap.png
```

`workflow_success.json` is created only after `src/run_all.py` passes. The deliverable package builder checks it before packaging generated outputs.

Files under `data/outputs/` are local generated artifacts and are ignored by Git.

## Source documentation files

```text
data/source_dataset_log.csv
data/dataset_metadata.csv
```

## Source extracts

Small extracts live in:

```text
data/source_extracts/
```

Examples:

```text
acs_equity_inputs_1mi.csv
acs_equity_index_1mi.csv
official_facility_hours_parking_v1.csv
amenity_official_source_inventory_v1.csv
amenities_0_5mi_v2_official_supported.csv
amenities_0_5mi_v3_osm_run_summary.csv
amenities_0_5mi_v4_osm_reviewed.csv
electrical_feasibility_v1.csv
local_ev_adoption_v1.csv
sensitivity_scenarios_v1.csv
stakeholder_data_request_fields.csv
stakeholder_response_tracker.csv
```

## Stakeholder follow-up tracker

```text
data/source_extracts/stakeholder_response_tracker.csv
```

Use this tracker to record outreach status, response summaries, source dates, confidence levels, and whether a model update is needed.

## Raw exports

Raw-export notes live in:

```text
data/raw_exports/README.md
```
