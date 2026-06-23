# Data Sources

This file summarizes the main source types used by the EV charging site-readiness prototype.

## Source quality labels

```text
Official = direct value from a government, utility, agency, or official source
Official-derived = calculated from official data
Open POI / GIS support = reproducible open geospatial or POI source, but not official local government confirmation
Manual estimate = project-created estimate that should be improved later
Planning estimate = conservative V1 estimate used for feasibility/cost placeholders
Planning proxy = temporary proxy when official local data is not accessible
Model logic = scoring, ranking, scenario, or tiering method created by the project
Placeholder = unresolved value intentionally left for future confirmation
```

## Main official, official-derived, or open-GIS sources used

```text
City of Fairfax GeoHub Addresses
Prince William County GIS Premise Addresses
AFDC / NREL Alternative Fuel Stations public active EV charger data
VDOT Bidirectional Traffic Volume 2025
ACS 2024 5-Year household and equity indicators
TIGER 2024 Virginia block group geometry
LODES 2023 workplace/job data
Fairfax County Public Library official branch page for FFX002 hours/parking
Prince William Public Libraries official locations page for PWC004 current renovation status
OpenStreetMap / Overpass reviewed POI extract for amenities_count_0_5mi
```

## Main planning estimates and proxies

```text
Demand assumptions v1
Electrical feasibility V1 planning estimates
Local EV adoption V1 proxy
Sensitivity scenarios V1
```

## Amenities source note

The original manual V1 amenities count has been superseded for the active model.

Current active field:

```text
amenities_count_0_5mi
```

Current source:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

This is a reviewed OpenStreetMap / Overpass six-category count within 0.5 miles. It is reproducible open POI/GIS support, not official local government confirmation.

## Main model-ready extracts

Small extracts are stored in:

```text
data/source_extracts/
```

Important examples:

```text
acs_equity_inputs_1mi.csv
acs_equity_index_1mi.csv
official_facility_hours_parking_v1.csv
amenities_0_5mi_v4_osm_reviewed.csv
electrical_feasibility_v1.csv
local_ev_adoption_v1.csv
sensitivity_scenarios_v1.csv
stakeholder_data_request_fields.csv
```

## Raw export policy

Large raw data exports are not all committed to the repository. The repo stores small model-ready extracts and documentation instead.

Raw-export notes are stored in:

```text
data/raw_exports/README.md
```

## Highest-priority data gaps

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
```

These should be replaced or confirmed with facility, utility, local government, stakeholder, or documented GIS/POI data when possible.
