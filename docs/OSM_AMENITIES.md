# OSM Amenities Workflow and Review

## Purpose

This document explains how the project uses OpenStreetMap / Overpass points of interest to support the active `amenities_count_0_5mi` field.

It combines the earlier workflow note and review note into one document.

The OSM workflow is used to improve or challenge the original manual amenities count. It does **not** automatically update the main model input. The output must be reviewed before any value is applied to `data/inputs/real_sites_v1.csv`.

## Source quality

OpenStreetMap is a public, community-maintained geospatial database. It is useful for nearby points-of-interest screening, but it is not the same as official local government GIS confirmation.

For this project, treat the reviewed OSM result as:

```text
Open POI / GIS support
```

not:

```text
Official local government confirmation
```

## Run command

From the repository root:

```bash
python src/build_osm_amenities.py
```

The script uses only Python standard library tools plus pandas. No GeoPandas, OSMnx, or QGIS is required.

## Safer command after timeout or rate-limit errors

Public Overpass servers can return temporary 504 timeout or 429 rate-limit errors. The script retries failed sites, waits longer by default, and marks failed sites clearly instead of treating missing results as true zero-amenity sites.

Recommended command after an incomplete run:

```bash
python src/build_osm_amenities.py --pause 15 --retries 4 --retry-wait 30
```

You can also fetch one failed site at a time:

```bash
python src/build_osm_amenities.py --site-id PWC002 --pause 15 --retries 4 --retry-wait 30
```

## Default local outputs

```text
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
```

The summary output gives one row per candidate site.

The detailed POI output gives the individual OSM features found near each site.

## Categories counted

The script groups POIs into planning-friendly categories:

```text
food
retail
entertainment_culture
recreation
transit
civic_public
```

Tag inventory:

```text
data/source_extracts/osm_amenity_query_tags_v1.csv
```

## What to inspect after a run

After running the script, check:

```text
fetch_status
osm_poi_total_0_5mi
osm_category_count_0_5mi
osm_categories_found
```

Compare those values to the current model field:

```text
current_model_amenities_count_0_5mi
```

If `fetch_status` is `failed`, do not treat blank or missing POI counts as zero amenities.

## Review rule before updating the model

Do not blindly replace the current value.

Use this rule:

```text
If OSM categories match the local context and look reasonable, create or update a reviewed amenities extract before changing real_sites_v1.csv.
```

Current reviewed applied extract:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

When changing the active model field, also update:

```text
data/inputs/real_sites_v1.csv
data/source_dataset_log.csv
data/dataset_metadata.csv
docs/DATA_SOURCES.md
docs/METHODOLOGY.md
docs/PROJECT_DECISIONS_LOG.md
```

## Latest reviewed OSM run

The OSM / Overpass amenities workflow successfully fetched points of interest for all six candidate sites after retry handling was added.

Raw run summary:

```text
data/source_extracts/amenities_0_5mi_v3_osm_run_summary.csv
```

Reviewed applied extract:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

Successful fetch summary:

```text
PWC001 — 39 POIs — 5 categories
PWC002 — 58 POIs — 6 categories
PWC003 — 1 POI — 1 category
PWC004 — 47 POIs — 5 categories
FFX001 — 121 POIs — 6 categories
FFX002 — 113 POIs — 6 categories
```

Applied reviewed values:

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

Manual V1 values are retained only for comparison and history.

## Special review note for PWC003

PWC003 remains 0 even though OSM found one civic/public category. The detailed POI appears tied to the facility itself, and the site is limited or not general public, so it should not increase the general-public amenity signal.

## Limitations

OpenStreetMap completeness varies. A missing POI does not always mean the amenity does not exist.

Some OSM features may be duplicated as both a node and an area. The script deduplicates by OSM element ID, but some real-world duplicates may still appear if the same place is mapped multiple ways.

The current radius is:

```text
805 meters, approximately 0.5 miles
```

## Troubleshooting

If the script fails with a timeout or API error, wait and run it again later. Public Overpass servers can be busy.

Use the safer retry command:

```bash
python src/build_osm_amenities.py --pause 15 --retries 4 --retry-wait 30
```
