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
```

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

## Stored extracts

The small extracts used by the model are stored in:

```text
data/source_extracts/site_coordinate_sources.csv
data/source_extracts/afdc_ev_supply_counts.csv
data/source_extracts/vdot_nearest_traffic_segments.csv
```
