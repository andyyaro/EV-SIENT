# Data Folder

This folder documents the datasets used to build the current prototype dataset.

The model uses `real_sites_v1.csv` as the current working site dataset. The files in this folder explain where official inputs came from and preserve the small extracts used to update the model.

## Why not store every full raw export?

Some official exports can be very large. To keep the repository clean, this folder stores:

```text
- a dataset log
- a dataset freshness metadata log
- small source extracts used in the model
- notes explaining which raw exports were used
```

The full raw datasets can be re-downloaded from the official source portals when needed.

## Files

```text
source_dataset_log.csv
dataset_metadata.csv
source_extracts/site_coordinate_sources.csv
source_extracts/afdc_ev_supply_counts.csv
source_extracts/vdot_nearest_traffic_segments.csv
source_extracts/acs_households_1mi.csv
source_extracts/lodes_jobs_1mi.csv
source_extracts/demand_assumptions_v1.csv
raw_exports/README.md
```

## What the metadata file tracks

`dataset_metadata.csv` tracks details such as records, update dates, published dates, access, license type, raw export used, and whether the dataset has actually been used yet.

This helps show dataset freshness and prevents the project from treating an old or incomplete export as fully verified.

## Datasets used or staged so far

```text
City of Fairfax GeoHub Addresses
Prince William County GIS Premise Addresses
AFDC NREL Alternative Fuel Stations export
VDOT Bidirectional Traffic Volume 2025
ACS 2024 5-Year B11001 Household Type
TIGER Line 2024 Virginia Block Groups
LODES 2023 Virginia Workplace Area Characteristics
```

## Current use in the model

These datasets support or are planned to support the following `real_sites_v1.csv` fields:

```text
address
city
state
zip
lat
lon
nearby_households_1mi
nearby_jobs_1mi
existing_l2_ports_1mi
existing_dcfc_ports_3mi
aadt_nearest
notes
```

## Important note

This data folder is for transparency and reproducibility. The model is still a planning prototype and does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, or permitting review.
