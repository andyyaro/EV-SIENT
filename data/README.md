# Data Folder

This folder stores input datasets, configuration files, source extracts, baseline snapshots, raw-export notes, and generated local outputs.

## Structure

```text
data/inputs/           Main model input CSVs
data/config/           Small model configuration and output-check rule files
data/source_extracts/  Small model-ready extracts used to populate input fields
data/baselines/        Curated committed benchmark snapshots for regression comparison
data/raw_exports/      Notes about raw exports that are too large or unnecessary to commit
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

`output_check_rules_v1.json` defines the current V1 sanity-check expectations used by `src/check_outputs.py`, including expected site IDs, expected top site, profile names, profile count, expected sites per profile, data-quality error rule, sensitivity stability rule, and profile score range.

## Baseline snapshots

Committed benchmark outputs live in:

```text
data/baselines/v1_baseline/
```

The combined output-check step compares the current local run against this baseline and writes the comparison reports under `data/outputs/`.

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
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/deliverable_package/
```

These are local run artifacts. They are ignored by Git so local script runs do not clutter the repository.

Do not commit files from `data/outputs/` by default. If the project needs to publish a specific output, copy or export that file intentionally as a separate deliverable.

## Source documentation files

```text
data/source_dataset_log.csv
data/dataset_metadata.csv
```

These files track source quality, freshness, raw exports used, and fields supported.

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
```

## Raw exports

The repo does not store every full raw export because some official data files are large. Raw-export notes live in:

```text
data/raw_exports/README.md
```

## Important note

This data folder supports transparency and reproducibility. The model is still a planning prototype and does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, permitting, procurement, or stakeholder review.
