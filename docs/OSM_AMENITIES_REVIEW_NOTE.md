# OSM Amenities Review Note

## What happened

The OSM/Overpass amenities workflow successfully fetched points of interest for all six candidate sites after retry handling was added.

The raw run summary is stored in:

```text
data/source_extracts/amenities_0_5mi_v3_osm_run_summary.csv
```

The reviewed applied extract is stored in:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

## Successful fetch summary

```text
PWC001 — 39 POIs — 5 categories
PWC002 — 58 POIs — 6 categories
PWC003 — 1 POI — 1 category
PWC004 — 47 POIs — 5 categories
FFX001 — 121 POIs — 6 categories
FFX002 — 113 POIs — 6 categories
```

## Applied reviewed values

```text
PWC001 — 5
PWC002 — 6
PWC003 — 0
PWC004 — 5
FFX001 — 6
FFX002 — 6
```

## Decision

The project now uses reviewed OSM-only amenity counts for the active `amenities_count_0_5mi` model field.

Manual V1 values are retained only for comparison/history.

## Special review note

PWC003 remains 0 even though OSM found one civic/public category. The detailed POI appears tied to the facility itself, and the site is limited or not general public, so it should not increase the general-public amenity signal.

## Source-quality note

OpenStreetMap / Overpass is useful open POI/GIS support and the method is reproducible. It is not official local government confirmation.
