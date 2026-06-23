# Data Folder

This folder stores input datasets, source extracts, raw-export notes, and generated local outputs.

## Structure

```text
data/inputs/           Main model input CSVs
data/source_extracts/  Small model-ready extracts used to populate input fields
data/raw_exports/      Notes about raw exports that are too large or unnecessary to commit
data/outputs/          Generated local outputs ignored by Git
```

## Main input files

```text
data/inputs/real_sites_v1.csv   Current real candidate-site dataset
data/inputs/sites_demo.csv      Small starter/demo dataset
```

## Generated outputs

Generated outputs are written to:

```text
data/outputs/
data/outputs/charts/
```

Typical generated files:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/model_run_summary.md
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
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
