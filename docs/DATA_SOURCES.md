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

## Dataset freshness and metadata

Dataset freshness, publication details, record counts, access status, license notes, and raw-export names are tracked in:

```text
data/dataset_metadata.csv
```

This file is the reviewer-facing metadata table for answering questions like:

```text
Where did the dataset come from?
How fresh was the dataset or export?
How many records did the source show?
Was the data public?
What license or access note was shown?
Which raw export or screenshot supported the metadata?
```

Important metadata fields:

```text
dataset_name
source_owner
source_type
dataset_status
records
info_updated
data_updated
published_date
access
license
raw_export_used
metadata_source
notes
```

Example documented metadata item:

```text
VDOT Bidirectional Traffic Volume 2025
records: 126,011
info_updated: 2026-06-12 3:49:27 PM EDT
data_updated: 2026-06-15 3:30:15 PM EDT
published_date: 2026-06-12 11:26:56 AM EDT
access: Public
license: Custom License
metadata_source: Virginia Roads dataset details panel screenshot
```

The companion source-use log is:

```text
data/source_dataset_log.csv
```

Use `dataset_metadata.csv` for dataset freshness and portal details. Use `source_dataset_log.csv` for how each source supports model fields.

If a source does not expose a metadata item clearly, keep the value as `Unknown` instead of guessing.

## Source traceability audit result

The current input rows are source-traceable enough for a V1 planning prototype, but not all fields are equally strong.

```text
Strongest support:
- candidate addresses and coordinates
- existing nearby public EV charger counts
- nearest traffic exposure
- nearby households
- nearby jobs
- equity index
- FFX002 official parking and facility hours
- PWC004 official current closure/renovation status

Medium support:
- amenities_count_0_5mi from reviewed OSM / Overpass POI categories

Weakest support / still needs confirmation:
- electrical service rating
- spare electrical capacity
- emergency disconnect visibility
- likely charger area
- distance to service
- trenching/routing difficulty
- employees_day
- visitors_day
- hours_open except FFX002
- parking_spaces except FFX002
- local EV adoption counts
- PWC002 garage-specific technical review
- PWC004 future/reopened timeline
- PWC003 public vs fleet/special-use decision
```

## Field-to-source summary

| Field or decision | Current source/support | Current source quality | Main caution |
|---|---|---|---|
| `address`, `city`, `state`, `zip`, `lat`, `lon` | City of Fairfax GeoHub and Prince William County GIS premise/address data | Official | Coordinates support planning-level mapping, not parcel design. |
| `existing_l2_ports_1mi`, `existing_dcfc_ports_3mi` | AFDC / NREL public active EV station extract | Official | Counts depend on extract date and filtering method. |
| `aadt_nearest` | VDOT Bidirectional Traffic Volume 2025 nearest segment | Official-derived | Nearest segment is a traffic exposure proxy, not observed site entries. |
| `nearby_households_1mi` | ACS 2024 5-Year + TIGER 2024 area-weighted block groups | Official-derived | Buffer method is approximate. |
| `nearby_jobs_1mi` | LODES 2023 + TIGER 2024 area-weighted block groups | Official-derived | Jobs are workplace-area estimates, not site visitor counts. |
| `equity_gap_index` | ACS 2024 5-Year equity indicators + TIGER 2024 geometry | Official-derived | Composite index is project-created from official-derived components. |
| `amenities_count_0_5mi` | Reviewed OpenStreetMap / Overpass six-category POI extract | Open POI / GIS support | Reproducible open data, but not official local government confirmation. |
| FFX002 `parking_spaces`, `hours_open` | Fairfax County Public Library official branch page | Official | Employees, visitors, and dwell time remain V1 assumptions. |
| PWC004 current closure/renovation status | Prince William Public Libraries official locations page | Official | Closure status is documented, but PWC004 remains modeled as a future/reopened planning candidate. |
| `employees_day`, `visitors_day`, `avg_dwell_min` | `demand_assumptions_v1.csv` | Manual estimate | Should be replaced with stakeholder or facility data when available. |
| `parking_spaces`, except FFX002 | `demand_assumptions_v1.csv` | Manual estimate | Should be replaced with official facility/GIS/stakeholder data. |
| `hours_open`, except FFX002 | `demand_assumptions_v1.csv` | Manual estimate | Charging hours may differ from building hours. |
| `distance_to_service_ft`, `trenching_ft`, `service_upgrade_cost_usd` | `electrical_feasibility_v1.csv` | Planning estimate | Not engineering-confirmed; should be updated after likely charger area is known. |
| `elec_service_rating_amp`, `spare_capacity_kw`, `emergency_disconnect_visible` | Placeholder zeros in current V1 input | Placeholder | Needs facility, utility, electrical, or AHJ confirmation. |
| `ev_registrations_local`, `ev_share_local` | `local_ev_adoption_v1.csv` | Planning proxy | Not official locality-level DMV registration data. |
| PWC002 garage review | Model review flag and stakeholder tracker | Unresolved review item | Needs fire/AHJ, ventilation, routing, emergency-response, access, and parking-operator review. |
| PWC003 public-use status | `public_access = 0` and stakeholder tracker | Unresolved use-case decision | Decide whether it is public, fleet-only, special-use, or removed. |
| PWC004 future/reopened timeline | Official current closure page + project planning assumption | Unresolved timeline decision | Do not treat as an active-current recommendation until timeline is clearer. |

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
stakeholder_response_tracker.csv
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
likely_charger_area
distance_to_service_ft
trenching_ft
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
PWC002 garage-specific review
PWC004 reopening or usable-planning timeline
PWC003 public, fleet-only, special-use, or removal decision
```

These should be replaced or confirmed with facility, utility, local government, stakeholder, or documented GIS/POI data when possible.

## Do-not-overclaim rule

If a value is a manual estimate, planning estimate, planning proxy, or placeholder, do not describe it as confirmed. Use the value for early comparison only and keep the assumption visible in the input notes, data confidence score, stakeholder tracker, and reporting language.
