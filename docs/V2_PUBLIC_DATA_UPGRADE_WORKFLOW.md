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

Current V2 method note:

```text
The current V2 calculator uses a centroid-in-buffer screening estimate. Do not describe it as area-weighted unless polygon overlap is added later.
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

Current V2 method note:

```text
The current V2 calculator aggregates jobs to block groups and uses a centroid-in-buffer screening estimate.
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

Important caveat:

```text
Nearest VDOT segment is a screening-level value, not final site-access validation.
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
open_gis_support_reviewed
```

Reason:

```text
OSM/Overpass is reproducible open geospatial support, but it is not official local-government confirmation.
```

Current V2 method note:

```text
Use the reviewed OSM category count, not the raw POI total.
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

Current V2 method note:

```text
The current V2 calculator uses a centroid-in-buffer screening estimate and a project-created composite equity index.
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

## First V2 upgrade batch status

The first V2 public-data upgrade batch is complete for these two sites:

```text
FFX003 — Pohick Regional Library
FFX004 — Fairfax County Government Center
```

Completed upgrade groups for both sites:

```text
households — completed_official_derived
jobs — completed_official_derived
traffic — completed_official_derived_screening_value
amenities — completed_open_gis_support_reviewed
equity — completed_official_derived
EV adoption — documented_proxy_not_upgraded
```

Do not treat EV adoption as official for this batch until a current locality-level DMV/state/local EV registration source is found.

Electrical and site-layout fields remain unconfirmed placeholders until facility, utility, or technical review confirms them.

## How to rerun the V2 model workflow

After V2 input rows or source extracts are updated, run:

```bash
python src/run_v2.py
```

This generates the V2-specific model, action matrix, quality, sensitivity, scoring-profile, and interpretation outputs under `data/outputs/`.

## Files to update after each upgrade

For each upgraded V2 site, update:

```text
data/inputs/real_sites_v2.csv
data/source_extracts/v2_source_confidence_tracker.csv
data/source_extracts/v2_public_data_upgrade_tasks.csv
data/source_extracts/v2cXXX_model_row_assumptions.csv
data/source_extracts/v2cXXX_*_public_data_notes.md
```

If a new project-ready extract is created, store it under:

```text
data/source_extracts/
```

Example V2 extracts:

```text
v2_acs_households_1mi.csv
v2_lodes_jobs_1mi.csv
v2_vdot_nearest_traffic_segments.csv
v2_acs_equity_inputs_1mi.csv
v2_acs_equity_index_1mi.csv
v2_amenities_osm_summary_0_5mi.csv
v2_amenities_osm_pois_0_5mi.csv
v2_public_data_upgrade_recommendations.csv
v2_public_data_upgrade_recommendations_reviewed.csv
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

To complete numeric upgrades locally, confirm whether these raw exports exist on your machine under `data/raw_exports/` or another known folder:

```text
tl_2024_51_bg.zip
va_wac_S000_JT00_2023.csv.gz
VDOT_Bidirectional_Traffic_Volume_2025.zip or VDOT_Bidirectional_Traffic_Volume_2025.geojson.zip
ACS 2024 household/equity table exports
OSM/Overpass amenities extract or export method
current DMV/state/local EV registration source, if available
```

Install optional V2 public-data dependencies when needed:

```bash
python -m pip install -r requirements-v2.txt
```

## Rule for remaining V2 sites

Every future V2 site should follow this order:

```text
1. Add backlog row.
2. Collect official/public location data.
3. Add preliminary model row only if clean enough.
4. Add source confidence tracker row groups.
5. Run public-data upgrade pass for households, jobs, traffic, amenities, equity, and EV adoption.
6. Rerun model with python src/run_v2.py.
7. Only then decide whether stakeholder outreach is worth it.
```

This keeps V2 scalable, honest, and defensible.
