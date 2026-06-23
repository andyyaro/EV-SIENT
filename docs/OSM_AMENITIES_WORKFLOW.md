# OSM Amenities Workflow

## Purpose

This workflow downloads nearby OpenStreetMap points of interest using the Overpass API and summarizes amenities within 0.5 miles of each candidate EV charging site.

The output is meant to improve or challenge the current manual `amenities_count_0_5mi` field.

This does **not** automatically update the main model input. Review the output first.

## Source quality

OpenStreetMap is a public, community-maintained geospatial database. It is useful for POI screening, but it is not the same as official local government GIS data.

For this project, treat the output as:

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

## Safer command after timeout/rate-limit errors

Public Overpass servers can return temporary 504 timeout or 429 rate-limit errors. The script now retries failed sites, waits longer by default, and marks failed sites clearly instead of treating them as true zero-amenity sites.

Recommended command after an incomplete run:

```bash
python src/build_osm_amenities.py --pause 15 --retries 4 --retry-wait 30
```

You can also fetch one failed site at a time:

```bash
python src/build_osm_amenities.py --site-id PWC002 --pause 15 --retries 4 --retry-wait 30
```

## Default outputs

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

## What to inspect

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

## How to decide whether to update the model

Do not blindly replace the current value.

Use this rule:

```text
If OSM categories match the local context and look reasonable, create a reviewed amenities v2 extract before changing real_sites_v1.csv.
```

Recommended next reviewed file:

```text
data/source_extracts/amenities_0_5mi_v3_osm_reviewed.csv
```

Then update:

```text
data/inputs/real_sites_v1.csv
data/source_dataset_log.csv
data/dataset_metadata.csv
docs/DATA_SOURCES.md
docs/METHODOLOGY.md
docs/PROJECT_DECISIONS_LOG.md
```

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
