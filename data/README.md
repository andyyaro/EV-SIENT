# Data Folder

This folder documents the datasets used to build the current prototype dataset.

The model uses `real_sites_v1.csv` as the current working site dataset. The files in this folder explain where the official inputs came from and preserve the small extracts used to update the model.

## Why not store every full raw export?

Some official exports can be very large. For example, the Prince William County Premise Addresses export used during this work was much larger than the small number of rows needed for the model. To keep the repository clean, this folder stores:

```text
- a dataset log
- small source extracts used in the model
- notes explaining which raw exports were used
```

The full raw datasets can be re-downloaded from the official source portals when needed.

## Files

```text
source_dataset_log.csv
source_extracts/site_coordinate_sources.csv
source_extracts/afdc_ev_supply_counts.csv
raw_exports/README.md
```

## Datasets used so far

```text
City of Fairfax GeoHub Addresses
Prince William County GIS Premise Addresses
AFDC / NREL Alternative Fuel Stations export
```

## Current use in the model

These datasets support the following `real_sites_v1.csv` fields:

```text
address
city
state
zip
lat
lon
existing_l2_ports_1mi
existing_dcfc_ports_3mi
notes
```

## Important note

This data folder is for transparency and reproducibility. The model is still a planning prototype and does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, or permitting review.
