# OSM Amenities Review Note

## What happened

The OSM/Overpass amenities workflow successfully fetched points of interest for all six candidate sites after retry handling was added.

The reviewed local run summary is stored in:

```text
data/source_extracts/amenities_0_5mi_v3_osm_run_summary.csv
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

## Interpretation

The OSM run supports the general amenity pattern already in the model.

```text
FFX001 and FFX002 have the strongest surrounding amenity context.
PWC002 also has strong mixed-use amenity support.
PWC004 has useful public-use context under the future/reopened planning assumption.
PWC001 has more nearby POI support than the older manual count suggested.
PWC003 should not automatically increase because its one OSM category appears to reflect civic/public facility context rather than general-public charging dwell activity.
```

## Decision for now

Do not directly replace `amenities_count_0_5mi` yet.

Reason:

```text
The OSM six-category system is not one-to-one with the older manual amenities count.
OpenStreetMap is useful open POI/GIS support, but it is not official local government confirmation.
The detailed POI output should be reviewed before changing the main model input.
```

## Next decision needed

Choose one of these approaches:

```text
Option A — keep the current manual amenities count but cite OSM as support.
Option B — replace the field with the OSM six-category count.
Option C — create a normalized amenity score using both manual context and OSM support.
```

Recommended approach:

```text
Option C, but only after reviewing the detailed POI file.
```
