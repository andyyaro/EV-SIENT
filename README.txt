# EV Charger Site-Readiness and Right-Sizing Prototype

This repository contains a working Python prototype for a public EV charging planning model.

The model does not only ask how many EV chargers a site can fit. It asks whether a site is actually ready for chargers from a demand, electrical, cost, accessibility, and fire-response perspective.

## Current default workflow

The script uses the current real candidate-site dataset by default:

```bash
python ev_charger_model.py
```

Default input:

```text
real_sites_v1.csv
```

Default output:

```text
site_results.csv
```

The script uses Python's built-in `argparse` module so the input and output files can be changed from the terminal without editing the code.

Optional examples:

```bash
python ev_charger_model.py --input sites.csv
python ev_charger_model.py --input real_sites_v1.csv --output real_site_results.csv
```

## Install requirements

```bash
pip install pandas numpy matplotlib
```

## Main files

```text
ev_charger_model.py      Main model script
real_sites_v1.csv        Current real candidate site dataset
sites.csv                Older starter/demo dataset
site_results.csv         Model output after running the script
README.txt               Repo overview and run instructions
DATA_SOURCES.md          Data source and field plan
PROJECT_STATUS.md        Current project status and next steps
data/README.md           Data folder explanation
data/source_dataset_log.csv
                         Dataset source log
data/dataset_metadata.csv
                         Dataset freshness and metadata notes
data/source_extracts/    Small model-ready source extracts
```

## What the script does

1. Reads a candidate-site CSV file.
2. Cleans numeric and yes/no fields.
3. Applies a public-access adjustment so limited-access facilities do not rank like normal public charging sites.
4. Scores each site for demand, feasibility, safety, and equity.
5. Estimates charging sessions per day.
6. Recommends EV charging ports for now, 2035, and 2050.
7. Flags sites that may need AHJ, Fire Marshal, ADA, utility, stormwater, or safety review.
8. Adds a plain-English `review_reason` column.
9. Exports results and charts.

## Outputs

After running the script, the folder should contain:

```text
site_results.csv
readiness_score_chart.png
utilization_vs_ports_<site_name>.png
```

`site_results.csv` is the main output table. It includes readiness score, demand score, feasibility score, safety score, expected daily charging sessions, recommended port counts, utilization, wait time, install cost estimate, public access adjustment, AHJ review flag, and review reason.

`readiness_score_chart.png` compares candidate sites by readiness score.

Each `utilization_vs_ports_<site_name>.png` chart shows how estimated utilization changes as more ports are installed for that site.

## Current real dataset status

`real_sites_v1.csv` currently includes Fairfax City and Prince William County candidate sites:

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

`PWC003` is no longer a staging row. It now represents the Prince William County Public Safety Training Center at 13101 Public Safety Dr, Nokesville, VA 20181. It is marked as limited/not general public access, so the model keeps it in the dataset but discounts it as a public charging priority.

## Official and official-derived data added

The current V1 dataset includes the following official or official-derived inputs:

```text
- Fairfax City GIS coordinates for Fairfax City Hall and City of Fairfax Regional Library
- Prince William County GIS coordinates for McCoart Government Center, Neabsco-Potomac Commuter Garage, Public Safety Training Center, and Chinn Park Regional Library
- AFDC / NREL public active EV station counts for nearby Level 2 and DC fast charging supply
- VDOT Bidirectional Traffic Volume 2025 nearest AADT values
- ACS 2024 5-Year B11001 household estimates within 1 mile
- TIGER Line 2024 Virginia block group geometry for area-weighted estimates
- LODES 2023 Virginia Workplace Area Characteristics job estimates within 1 mile
```

The small extracts used by the model are stored in:

```text
data/source_extracts/site_coordinate_sources.csv
data/source_extracts/afdc_ev_supply_counts.csv
data/source_extracts/vdot_nearest_traffic_segments.csv
data/source_extracts/acs_households_1mi.csv
data/source_extracts/lodes_jobs_1mi.csv
data/source_extracts/demand_assumptions_v1.csv
```

The repository does not commit every full raw export because several raw files are large. Instead, the repo stores small source extracts and documentation so the model remains readable and reproducible.

## Current V1 interpretation

The current model separates sites into two broad groups:

```text
Public charging priority sites:
- City of Fairfax Regional Library
- Chinn Park Regional Library
- PWC McCoart Government Center
- Fairfax City Hall or municipal building

Special/high-review sites:
- Neabsco-Potomac Commuter Garage
- Prince William County Public Safety Training Center
```

The garage remains a high-review site because enclosed garages raise extra ventilation, access, and emergency-response questions. The Public Safety Training Center remains useful as a special-use or fleet-support candidate, but its limited public access prevents it from ranking like a normal public charging site.

## Still placeholder or unresolved

The following fields still need better official data, stakeholder input, site review, or improved assumptions:

```text
employees_day
visitors_day
fleet_vehicles
parking_spaces
hours_open
amenities_count_0_5mi
ev_registrations_local
ev_share_local
equity_gap_index
elec_service_rating_amp
spare_capacity_kw
distance_to_service_ft
trenching_ft
service_upgrade_cost_usd
ada_layout_possible
fire_access_ok
emergency_disconnect_visible
stormwater_risk
battery_storage_flag
battery_storage_kwh
```

## Important limitation

This model is a prototype planning tool. It does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, or permitting review. It helps rank candidate sites and flag issues that deserve deeper review.
