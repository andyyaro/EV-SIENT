# Raw Exports

This folder explains the raw exports used so far.

The full raw exports are not all committed here because some are large and only a few rows or derived counts are needed for the current prototype.

## Raw exports used during current data build

```text
Addresses.csv
Premise_Address.csv
alt_fuel_stations (Jun 23 2026).csv
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

## Stored extracts

The small extracts used by the model are stored in:

```text
data/source_extracts/site_coordinate_sources.csv
data/source_extracts/afdc_ev_supply_counts.csv
```
