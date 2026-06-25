# V2 Public Data Upgrade Workflow

## Purpose

This workflow defines how new V2 sites should be upgraded from early screening assumptions to stronger public-data-supported rows.

This is the standard process for newly added V2 sites and for the remaining V2 expansion candidates.

## Simple rule

Do not treat a newly added V2 site as serious until the high-impact public-data fields have been upgraded as much as possible.

The basic path is:

```text
preliminary V2 row
→ source confidence tracker
→ public-data upgrade pass
→ rerun model
→ review ranking
→ decide whether stakeholder outreach is worth it
```

## Upgrade groups

### 1. Households

Model field:

```text
nearby_households_1mi
```

Preferred source:

```text
ACS 2024 5-Year household tables + TIGER 2024 Virginia block group geometry
```

Source confidence after upgrade:

```text
official_derived
```

Reason:

```text
The source is official Census data, but the 1-mile buffer value is calculated by the project.
```

## 2. Jobs

Model field:

```text
nearby_jobs_1mi
```

Preferred source:

```text
LODES 2023 workplace jobs + TIGER 2024 Virginia block group geometry
```

Source confidence after upgrade:

```text
official_derived
```

Reason:

```text
The source is Census LEHD/LODES data, but the 1-mile buffer value is calculated by the project.
```

## 3. Traffic

Model field:

```text
aadt_nearest
```

Preferred source:

```text
VDOT Bidirectional Traffic Volume 2025 nearest segment
```

Source confidence after upgrade:

```text
official_derived
```

Reason:

```text
The source is an official VDOT traffic-volume dataset, but the nearest-segment match is calculated by the project.
```

## 4. Amenities

Model field:

```text
amenities_count_0_5mi
```

Preferred source:

```text
Reviewed OpenStreetMap / Overpass six-category POI method
```

Source confidence after upgrade:

```text
open_gis_support
```

Reason:

```text
OSM/Overpass is reproducible open geospatial support, but it is not official local-government confirmation.
```

## 5. Equity

Model field:

```text
equity_gap_index
```

Preferred source:

```text
ACS 2024 5-Year equity indicators + TIGER 2024 Virginia block group geometry
```

Source confidence after upgrade:

```text
official_derived
```

Reason:

```text
The source indicators are official Census data, but the composite equity index is project-created.
```

## 6. EV adoption

Model fields:

```text
ev_registrations_local
ev_share_local
```

Preferred source:

```text
Current DMV/state/local EV registration source, if available
```

Source confidence after upgrade:

```text
official_source or official_derived
```

Important caveat:

```text
If no accessible locality-level DMV/state EV registration export is available, keep this as a documented proxy and do not label it official.
```

## Current V2 sites needing this upgrade

```text
FFX003 — Pohick Regional Library
FFX004 — Fairfax County Government Center
```

## Files to update after each upgrade

For each upgraded V2 site, update:

```text
data/inputs/real_sites_v2.csv
data/source_extracts/v2_source_confidence_tracker.csv
data/source_extracts/v2cXXX_model_row_assumptions.csv
data/source_extracts/v2cXXX_*_public_data_notes.md
```

If a new project-ready extract is created, store it under:

```text
data/source_extracts/
```

Example future extracts:

```text
v2_acs_households_1mi.csv
v2_lodes_jobs_1mi.csv
v2_vdot_nearest_traffic_segments.csv
v2_acs_equity_inputs_1mi.csv
v2_acs_equity_index_1mi.csv
v2_amenities_0_5mi_osm_reviewed.csv
v2_local_ev_adoption.csv
```

## Raw data needed

The existing V1 documentation already identifies the source families used for official-derived public-data fields:

```text
ACS 2024 5-Year + TIGER 2024 block groups
LODES 2023 workplace/job data
VDOT Bidirectional Traffic Volume 2025
Reviewed OSM / Overpass POI extract
AFDC / NREL station extract
```

For V2, the same source families should be reused so the comparison stays methodologically consistent.

## User/local-machine help needed

The repo does not commit all large raw exports.

To complete the numeric upgrade locally, confirm whether these raw exports exist on your machine under `data/raw_exports/` or another known folder:

```text
tl_2024_51_bg.zip
va_wac_S000_JT00_2023.csv.gz
VDOT_Bidirectional_Traffic_Volume_2025.zip
ACS 2024 household/equity table exports
OSM/Overpass amenities extract or export method
current DMV/state/local EV registration source, if available
```

If they are present locally, the next step is to compute updated values for FFX003 and FFX004 and write small model-ready extracts under `data/source_extracts/`.

If they are not present locally, the next step is to download or recreate the public-data extracts first.

## Rule for remaining V2 sites

Every future V2 site should follow this order:

```text
1. Add backlog row.
2. Collect official/public location data.
3. Add preliminary model row only if clean enough.
4. Add source confidence tracker row groups.
5. Run public-data upgrade pass for households, jobs, traffic, amenities, equity, and EV adoption.
6. Rerun model.
7. Only then decide whether stakeholder outreach is worth it.
```

This keeps V2 scalable, honest, and defensible.
