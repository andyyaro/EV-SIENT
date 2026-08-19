# Cached boundary data
- `tl_2024_va_counties.geojson` - Virginia county boundaries extracted from US Census Bureau TIGER/Line 2024 (`tl_2024_us_county.zip`, public domain), filtered to STATEFP=51.
- Source: https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip (downloaded 2026-07-19 during the legacy baseline run).
- Cached so the GIS map step runs fully offline (PY-06). Attribution: U.S. Census Bureau TIGER/Line Shapefiles, 2024.

Note (repo publication, 2026-07-19): the cached GeoJSON is filtered to counties within
0.5° of the candidate-site extent and geometry-simplified (tolerance 0.0005°) to keep the
repository small. This affects only map context outlines, not any model computation.
