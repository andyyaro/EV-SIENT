# V2 GIS Decision Map Upgrade Checkpoint

## Status

The V2 GIS decision-map workflow has been upgraded from a static report map into a stronger report-plus-README map system with a cleaner executive dashboard.

## Updated script

```text
src/plot_site_decision_map.py
```

## Outputs

```text
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
docs/assets/charts/v2_site_decision_map_readme.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png
```

## Upgrade details

```text
Removed the circular zoom lens after visual review showed it created clutter.
Replaced the zoom lens with a dedicated PWC cluster dashboard section.
Removed the main-map focus ring and connector line.
Kept the main map clean as the regional geospatial overview.
Rebuilt the right-side panel as one unified Decision dashboard instead of stacked cards.
Reduced spreadsheet-like clutter in the panel.
Highlighted the top overall site and top PWC site in the top-decision section.
Added a readable PWC cluster section with rank, site ID, score, action category, and now-to-future ports.
Simplified the port section so it supports the map instead of dominating it.
Kept the key-metrics row.
Kept the visual map-encoding section with marker symbols.
Kept the full report map.
Kept the separate README-optimized map.
Refreshes the README asset under docs/assets/charts/ when the map script runs.
Syncs both map outputs into an existing deliverable package when present.
Refreshes package manifest hashes when package chart copies are updated directly.
```

## Package sync behavior

The deliverable package now includes both GIS decision-map outputs:

```text
charts/v2_site_decision_map.png
charts/v2_site_decision_map_readme.png
```

The package builder stores SHA-256 hashes for source and copied files. The V2 checker recomputes those hashes and fails if a copied package file is stale.

## Validation commands

```bash
python -m py_compile src/plot_site_decision_map.py src/run_v2.py src/build_v2_deliverable_package.py src/check_outputs_v2.py
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected package health:

```text
Copied files: 30/30
Synced files: 30/30
```
