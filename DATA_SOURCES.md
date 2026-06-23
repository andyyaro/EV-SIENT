# Data Sources and Field Plan

This file tracks where each input in the EV charging site-readiness model should come from.

The goal is to keep the model transparent and defensible. Some fields come from official datasets, while other fields require manual review, stakeholder input, or site assumptions.

## Source quality levels

| Level | Meaning | Use in model |
|---|---|---|
| Official | Comes from a government, DOE/NREL, Census, VDOT, or local government source | Best source for model inputs |
| Official-derived | Calculated from official data, such as a buffer estimate | Good for planning, but the method should be documented |
| Stakeholder evidence | Comes from interviews or project notes | Useful for known site constraints and calibration |
| Manual estimate | Estimated from maps, site review, assumptions, or early planning judgment | Acceptable for prototype, but should be labeled |
| Unknown | Not available yet | Keep blank or use conservative placeholder |

## Current working dataset

```text
real_sites_v1.csv
```

The older `sites.csv` file is still available as a starter/demo dataset, but the model now runs on `real_sites_v1.csv` by default.

## Current candidate sites

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

`PWC003` now represents the Prince William County Public Safety Training Center. It is marked as limited/not general public access in the working CSV because the facility is primarily a public safety training location.

## Official data already added

### 1. Fairfax City GeoHub Addresses

Used for official address and coordinates for:

```text
FFX001 — 10455 Armstrong St, Fairfax, VA 22030
FFX002 — 10360 North Street, Fairfax, VA 22030-2514
```

Model fields supported:

```text
address
city
state
zip
lat
lon
```

### 2. Prince William County GIS Premise Addresses

Used for official address and coordinates for:

```text
PWC001 — 1 County Complex Ct, Woodbridge, VA 22192
PWC002 — 14801 Dining Way, Woodbridge, VA 22191
PWC003 — 13101 Public Safety Dr, Nokesville, VA 20181
PWC004 — 13065 Chinn Park Dr, Woodbridge, VA 22192
```

Model fields supported:

```text
address
city
state
zip
lat
lon
```

### 3. DOE / AFDC / NREL Alternative Fuel Stations

Used for official nearby public active EV charging supply.

Model fields supported:

```text
existing_l2_ports_1mi
existing_dcfc_ports_3mi
```

Current AFDC-derived values:

```text
PWC001: existing_l2_ports_1mi = 10, existing_dcfc_ports_3mi = 0
PWC002: existing_l2_ports_1mi = 62, existing_dcfc_ports_3mi = 60
PWC003: existing_l2_ports_1mi = 0, existing_dcfc_ports_3mi = 0
PWC004: existing_l2_ports_1mi = 0, existing_dcfc_ports_3mi = 27
FFX001: existing_l2_ports_1mi = 28, existing_dcfc_ports_3mi = 39
FFX002: existing_l2_ports_1mi = 14, existing_dcfc_ports_3mi = 23
```

### 4. VDOT Bidirectional Traffic Volume 2025

Used for official traffic exposure near each confirmed candidate site.

Model field supported:

```text
aadt_nearest
```

Current VDOT-derived nearest AADT values:

```text
PWC001: aadt_nearest = 51000
PWC002: aadt_nearest = 8300
PWC003: aadt_nearest = 490
PWC004: aadt_nearest = 45000
FFX001: aadt_nearest = 9700
FFX002: aadt_nearest = 12000
```

Notes:

```text
AADT means Annual Average Daily Traffic.
Values were assigned using the nearest traffic-volume geometry to each site coordinate.
The source extract is stored at data/source_extracts/vdot_nearest_traffic_segments.csv.
PWC002's nearest segment is a ramp near the garage; nearby I-95 segments have much higher ADT, so this may deserve later review.
```

### 5. U.S. Census ACS 2024 5-Year Household Type and TIGER Block Groups

Used for household context around each confirmed candidate site.

Model field supported:

```text
nearby_households_1mi
```

Current ACS-derived values:

```text
PWC001: nearby_households_1mi = 3576
PWC002: nearby_households_1mi = 5263
PWC003: nearby_households_1mi = 58
PWC004: nearby_households_1mi = 5022
FFX001: nearby_households_1mi = 4231
FFX002: nearby_households_1mi = 4964
```

Notes:

```text
Values use ACS 2024 5-Year B11001 total households.
Block group geometry comes from TIGER Line 2024 Virginia block groups.
Values are area-weighted estimates for a 1-mile site buffer.
The source extract is stored at data/source_extracts/acs_households_1mi.csv.
```

### 6. U.S. Census LEHD LODES 2023 Workplace Area Characteristics

Used for workplace/job density around each confirmed candidate site.

Model field supported:

```text
nearby_jobs_1mi
```

Current LODES-derived values:

```text
PWC001: nearby_jobs_1mi = 5195
PWC002: nearby_jobs_1mi = 9890
PWC003: nearby_jobs_1mi = 33
PWC004: nearby_jobs_1mi = 3140
FFX001: nearby_jobs_1mi = 18057
FFX002: nearby_jobs_1mi = 15718
```

Notes:

```text
Values use LODES 2023 Virginia Workplace Area Characteristics, all jobs.
The source file is va_wac_S000_JT00_2023.csv.gz.
Workplace block jobs were aggregated to block groups for the current prototype.
Values are then area-weighted estimates for a 1-mile site buffer.
The source extract is stored at data/source_extracts/lodes_jobs_1mi.csv.
```

## Priority official sources still needed

### Local government facility pages and GIS

Use for candidate site names, addresses, hours, parking, public-access details, and facility details when published.

Possible sources:

```text
Prince William County official facility pages
Fairfax City official facility pages
library system pages
public works / public safety / government center pages
local GIS open data
```

## Fields that likely need manual or stakeholder inputs

These fields are important but are usually not available in open public datasets:

```text
spare_capacity_kw
distance_to_service_ft
trenching_ft
trench_cost_per_ft
service_upgrade_cost_usd
ada_layout_possible
fire_access_ok
garage_enclosed
emergency_disconnect_visible
stormwater_risk
battery_storage_flag
battery_storage_kwh
```

How to handle them in the prototype:

```text
Use stakeholder interview evidence when available.
Use conservative manual assumptions when necessary.
Explain uncertain inputs clearly in the notes column.
Do not present these fields as official engineering determinations unless verified by the appropriate office.
```

## Field-by-field plan for `real_sites_v1.csv`

| Field | Planned source | Source quality | Notes |
|---|---|---|---|
| `site_id` | Project-created ID | Manual estimate | Use short stable IDs like PWC001 or FFX001 |
| `site_name` | Local government / facility page | Official | Public facility name |
| `site_type` | Project classification | Manual estimate | library, office, garage, clinic, fleet, community center, public safety |
| `address` | Local government / GIS source | Official | Use official address where possible |
| `city` | Local government / GIS source | Official |  |
| `state` | Local government / GIS source | Official | Usually VA |
| `zip` | Local government / GIS source | Official |  |
| `lat` | Official local GIS address point when available | Official if GIS | Fairfax and PWC coordinates added for confirmed rows |
| `lon` | Official local GIS address point when available | Official if GIS | Fairfax and PWC coordinates added for confirmed rows |
| `public_access` | Facility page / site knowledge | Official or manual estimate | 1 if public can access site; 0 if access is limited |
| `employees_day` | Facility estimate / stakeholder input | Manual estimate | Hard to get officially |
| `visitors_day` | Facility estimate / stakeholder input | Manual estimate | Hard to get officially |
| `fleet_vehicles` | Stakeholder input / fleet plan | Stakeholder evidence or manual estimate | Use 0 if not a fleet site |
| `parking_spaces` | Site page, GIS, stakeholder evidence, or manual count | Official, stakeholder, or manual estimate | PWC002 parking still needs confirmation |
| `hours_open` | Facility page | Official or manual estimate | Current values are planning assumptions unless otherwise noted |
| `avg_dwell_min` | Site-type assumption | Manual estimate | Based on library, garage, office, clinic, public safety, etc. |
| `nearby_households_1mi` | Census ACS | Official-derived | Added with ACS B11001 and TIGER block group geometry |
| `nearby_jobs_1mi` | Census LEHD LODES | Official-derived | Added with LODES WAC and TIGER block group geometry |
| `aadt_nearest` | VDOT / Virginia Roads | Official | Added for confirmed rows using nearest traffic segment |
| `amenities_count_0_5mi` | OpenStreetMap / manual map count | Public/open data or manual estimate | Not government official unless using local GIS |
| `ev_registrations_local` | State/local registration source if available | Official if found | Optional for later |
| `ev_share_local` | State/local registration source or regional assumption | Official or manual estimate | Use same assumption for v1 if needed |
| `existing_l2_ports_1mi` | AFDC / NREL Alternative Fuel Stations | Official | Count public active L2 ports within 1 mile |
| `existing_dcfc_ports_3mi` | AFDC / NREL Alternative Fuel Stations | Official | Count public active DC fast ports within 3 miles |
| `equity_gap_index` | ACS-derived index | Official-derived / project-created | Project-created score using official ACS variables |
| `elec_service_voltage` | Facility/utility data | Manual estimate | Often unknown publicly |
| `elec_service_rating_amp` | Facility/utility data | Manual estimate | Often unknown publicly |
| `spare_capacity_kw` | Facility/utility/stakeholder input | Stakeholder evidence or manual estimate | Important uncertainty field |
| `distance_to_service_ft` | Site map / facility input | Manual estimate | Distance from charger location to electrical service |
| `trenching_ft` | Site map / facility input | Manual estimate | Important cost driver |
| `trench_cost_per_ft` | Cost assumption | Manual estimate | Keep constant for prototype unless better data found |
| `service_upgrade_cost_usd` | Facility/utility/stakeholder input | Stakeholder evidence or manual estimate | Important cost driver |
| `ada_layout_possible` | Site review / ADA review | Manual estimate | 1 if likely possible, 0 if unresolved/problematic |
| `fire_access_ok` | Fire/AHJ/site review | Manual estimate | Do not treat as official without review |
| `garage_enclosed` | Site type / facility page | Official or manual estimate | Garages require extra review |
| `emergency_disconnect_visible` | Site review | Manual estimate | Often unknown until design stage |
| `stormwater_risk` | Site review / local stormwater context | Manual estimate | Especially important for runoff concerns |
| `battery_storage_flag` | Project design input | Manual estimate | 1 if storage is proposed/present |
| `battery_storage_kwh` | Project design input | Manual estimate | 0 if none |
| `notes` | Project notes | Manual / stakeholder evidence | Explain uncertain assumptions and interview evidence |

## Near-term dataset plan

For version 1, the most important rule is honesty:

```text
Official values should be marked as official.
Estimated values should be clearly marked as estimates.
Unknown safety/electrical values should not be presented as verified.
```

Best next data work:

```text
1. Improve site-specific public_access handling and public_safety behavior in the model.
2. Improve site-specific parking, hours, visitor, employee, and electrical assumptions.
3. Fill missing dataset freshness metadata for older source files.
4. Begin equity-gap scoring from ACS variables.
5. Improve feasibility assumptions for electrical capacity, trenching, and service upgrade cost.
```
