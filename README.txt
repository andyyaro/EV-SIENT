# EV Charger Site-Readiness and Right-Sizing Starter Project

This folder contains the first working prototype for the EV charging model.

## What to run first

1. Open PyCharm.
2. Open this folder as a project.
3. Open the PyCharm Terminal.
4. Run:

pip install pandas numpy matplotlib

5. Run:

python ev_charger_model.py

## What files you will get

After running the script, the folder will contain:

- site_results.csv
- readiness_score_chart.png
- utilization_vs_ports_chart.png

## What each file means

site_results.csv:
This is the main output table. It shows each site's readiness score, expected charging sessions per day, recommended starter ports, future ports, estimated utilization, install cost, and AHJ review flag.

readiness_score_chart.png:
This chart compares candidate sites by overall readiness.

utilization_vs_ports_chart.png:
This chart shows how utilization changes as you add more ports for one site.

## What to edit next

Edit sites.csv to replace the demo sites with real Fairfax City / Prince William County sites.

Start with simple candidate sites:
- a library
- a civic building
- a commuter garage
- a clinic or public facility
- a fleet lot

You do NOT need Kaggle for the first run. Kaggle is useful later for practice notebooks or extra EV datasets. Your first working model should start with sites.csv.
