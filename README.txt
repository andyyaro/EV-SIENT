# EV Charger Site-Readiness and Right-Sizing Prototype

This repository contains a working Python prototype for a public EV charging planning model.

The model does not only ask how many EV chargers a site can fit. It asks whether a site is actually ready for chargers from a demand, electrical, cost, accessibility, and fire-response perspective.

## Current default workflow

The script now uses the real candidate-site dataset by default:

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
ev_charger_model.py   Main model script
real_sites_v1.csv     Current real/staging candidate site dataset
sites.csv             Older starter/demo dataset
site_results.csv      Model output after running the script
DATA_SOURCES.md       Data source and field plan
PROJECT_STATUS.md     Current project status and next steps
```

## What the script does

1. Reads a candidate-site CSV file.
2. Cleans numeric and yes/no fields.
3. Scores each site for demand, feasibility, safety, and equity.
4. Estimates charging sessions per day.
5. Recommends EV charging ports for now, 2035, and 2050.
6. Flags sites that may need AHJ, Fire Marshal, ADA, utility, stormwater, or safety review.
7. Adds a plain-English `review_reason` column.
8. Exports results and charts.

## Outputs

After running the script, the folder should contain:

```text
site_results.csv
readiness_score_chart.png
utilization_vs_ports_<site_name>.png
```

`site_results.csv` is the main output table. It includes readiness score, demand score, feasibility score, safety score, expected daily charging sessions, recommended port counts, utilization, wait time, install cost estimate, AHJ review flag, and review reason.

`readiness_score_chart.png` compares candidate sites by readiness score.

Each `utilization_vs_ports_<site_name>.png` chart shows how estimated utilization changes as more ports are installed for that site.

## Current real dataset status

`real_sites_v1.csv` currently includes Fairfax City and Prince William County candidate sites.

Official data already added:

```text
- Fairfax City GIS coordinates for Fairfax City Hall and City of Fairfax Regional Library
- Prince William County GIS coordinates for McCoart Government Center, Neabsco-Potomac Commuter Garage, and Chinn Park Regional Library
- AFDC public active EV station counts for nearby Level 2 and DC fast charging supply
```

Still placeholder or unresolved:

```text
- PWC003 is still a staging public health facility row because a specific official facility has not been confirmed yet.
- Demand fields such as employees, visitors, households, jobs, traffic, and amenities still need official or defensible data.
- Electrical capacity, trenching distance, service upgrade cost, ADA layout, fire access, emergency disconnect, stormwater, and battery storage fields still need stakeholder, site-review, or manual assumptions.
```

## Important limitation

This model is a prototype planning tool. It does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, or permitting review. It helps rank candidate sites and flag issues that deserve deeper review.
