# Raw Exports

This folder explains the raw exports used so far.

The full raw exports are not all committed here because some are large and only a few rows or derived counts are needed for the current prototype.

## Raw exports used during current data build

```text
Addresses.csv
Premise_Address.csv
alt_fuel_stations (Jun 23 2026).csv
Traffic_Volume_ADT.csv
VDOT_Bidirectional_Traffic_Volume_2025.zip
VDOT_Bidirectional_Traffic_Volume_2025.geojson.zip
ACSDT5Y2024.B11001-2026-06-23T052522.csv
tl_2024_51_bg.zip
va_wac_S000_JT00_2023.csv.gz
```

## Official raw exports identified for next equity build

The next equity build should use official U.S. Census Bureau ACS 2024 5-Year Detailed Tables at block-group geography plus TIGER 2024 Virginia block group geometry.

Official source table inventory:

```text
data/source_extracts/acs_equity_official_tables.csv
```

Raw ACS exports to download next:

```text
ACS 2024 5-Year Detailed Table B19013 — median household income
ACS 2024 5-Year Detailed Table B08201 — household vehicles available
ACS 2024 5-Year Detailed Table B25003 — tenure / renter occupied
ACS 2024 5-Year Detailed Table B25024 — units in structure / multifamily housing
```

Geometry already identified:

```text
tl_2024_51_bg.zip — TIGER Line 2024 Virginia Block Groups
```

The final project-ready equity extract should be:

```text
data/source_extracts/acs_equity_inputs_1mi.csv
```

That extract should only be filled after the official ACS table exports are downloaded and processed, following the same official-derived pattern used for households and jobs.

## How each raw export was used

### Addresses.csv

Source: City of Fairfax GeoHub Addresses

Used to verify:

```text
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

Fields used:

```text
address
zip
latitude
longitude
```

### Premise_Address.csv

Source: Prince William County GIS Premise Addresses

Used to verify:

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC004 — Chinn Park Regional Library
```

Fields used:

```text
address
zip
latitude
longitude
```

### alt_fuel_stations (Jun 23 2026).csv

Source: AFDC / NREL Alternative Fuel Stations export

Used to calculate:

```text
existing_l2_ports_1mi
existing_dcfc_ports_3mi
```

Filters used:

```text
fuel type = ELEC
access = public
status = active / existing
Level 2 ports counted within 1 mile
DC fast ports counted within 3 miles
```

### Traffic_Volume_ADT.csv

Source: VDOT Bidirectional Traffic Volume 2025

This was the first traffic table export downloaded. It contains traffic-volume attributes such as ADT but does not include enough geometry by itself to compute the nearest road segment for each site.

Used as supporting reference for:

```text
aadt_nearest
```

### VDOT_Bidirectional_Traffic_Volume_2025.zip

Source: VDOT Bidirectional Traffic Volume 2025 shapefile export

Used to calculate the nearest traffic-volume segment for each confirmed candidate site.

Fields used:

```text
ADT
ROUTE_COMM
ROUTE_NAME
START_LABE
END_LABEL
FROM_JURIS
TO_JURISDI
geometry
```

### VDOT_Bidirectional_Traffic_Volume_2025.geojson.zip

Source: VDOT Bidirectional Traffic Volume 2025 GeoJSON export

This was uploaded as an alternative geometry export. The shapefile ZIP was used for processing because it was smaller and easier to handle.

### ACSDT5Y2024.B11001-2026-06-23T052522.csv

Source: U.S. Census Bureau ACS 2024 5-Year B11001 Household Type table

Used to calculate:

```text
nearby_households_1mi
```

### tl_2024_51_bg.zip

Source: U.S. Census Bureau TIGER Line 2024 Virginia Block Groups

Used as the geometry layer for area-weighted 1-mile household and job estimates.

### va_wac_S000_JT00_2023.csv.gz

Source: U.S. Census Bureau LODES 2023 Virginia Workplace Area Characteristics

Used to calculate:

```text
nearby_jobs_1mi
```

The file gives workplace jobs at census block level. For the current prototype, jobs were aggregated to block groups and then estimated within each 1-mile site buffer by area weighting.

## Stored extracts

The small extracts used by the model are stored in:

```text
data/source_extracts/site_coordinate_sources.csv
data/source_extracts/afdc_ev_supply_counts.csv
data/source_extracts/vdot_nearest_traffic_segments.csv
data/source_extracts/acs_households_1mi.csv
data/source_extracts/lodes_jobs_1mi.csv
data/source_extracts/acs_equity_official_tables.csv
```
