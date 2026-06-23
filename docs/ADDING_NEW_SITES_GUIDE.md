# Adding New Candidate Sites Guide

## Purpose

This guide explains how to add new EV charging candidate sites without breaking the model.

Use this when expanding beyond the first six sites.

Template file:

```text
data/inputs/new_sites_template.csv
```

Main model input file:

```text
data/inputs/real_sites_v1.csv
```

## Simple workflow

```text
1. Copy the template row from data/inputs/new_sites_template.csv.
2. Create a new site_id.
3. Fill in the best public data first.
4. Label uncertain values clearly in notes.
5. Add the new row to data/inputs/real_sites_v1.csv.
6. Run the validator.
7. Run the full workflow.
8. Review the rankings and data-quality report.
9. Only prioritize outreach for sites that rank well or have major uncertainty.
```

## Site ID format

Use short stable IDs:

```text
FFX003
FFX004
PWC005
PWC006
```

Keep the prefix tied to the locality:

```text
FFX = Fairfax City / Fairfax area candidate
PWC = Prince William County candidate
```

## Good candidate categories

Start with public or civic locations before random private sites.

Good first categories:

```text
libraries
city or county buildings
commuter lots
parks and recreation centers
community centers
public garages
transit-adjacent parking
public safety or fleet-support sites, if marked special-use
```

## Quick screening questions

Before adding a site, ask:

```text
1. Is there parking?
2. Is it public or clearly useful for a public agency use case?
3. Is it near people, jobs, roads, or public destinations?
4. Is there likely room for Level 2 chargers?
5. Is the site easy enough to explain to a reviewer?
6. Would this site add something different from sites already in the model?
```

If most answers are no, do not add the site yet.

## Fields to fill first

These are the minimum fields to make a first-pass model row useful:

```text
site_id
site_name
site_type
address
city
state
zip
lat
lon
public_access
parking_spaces
hours_open
avg_dwell_min
nearby_households_1mi
nearby_jobs_1mi
aadt_nearest
amenities_count_0_5mi
existing_l2_ports_1mi
existing_dcfc_ports_3mi
equity_gap_index
distance_to_service_ft
trenching_ft
trench_cost_per_ft
service_upgrade_cost_usd
ada_layout_possible
fire_access_ok
garage_enclosed
stormwater_risk
notes
```

## Fields that can start as placeholders

These can be placeholders in a first-pass row, but they should be tracked for later confirmation:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
ev_registrations_local
ev_share_local
```

Use the notes column to say they are assumptions.

## Simple default values

Use these only when you do not have better information yet:

```text
elec_service_voltage = 480
elec_service_rating_amp = 0
spare_capacity_kw = 0
trench_cost_per_ft = 150
emergency_disconnect_visible = 0
battery_storage_flag = 0
battery_storage_kwh = 0
```

For public sites:

```text
public_access = 1
```

For limited or fleet-only sites:

```text
public_access = 0
```

## Site type values

Use simple labels already supported by the project style:

```text
library
office
garage
public_safety
park
community_center
commuter_lot
transit
other
```

## Notes column rule

The notes field should always answer:

```text
What is confirmed?
What is estimated?
What still needs follow-up?
```

Example:

```text
Coordinates and address from official facility page; parking and visitors are V1 assumptions; electrical service rating, spare capacity, and emergency disconnect remain unconfirmed.
```

## After adding new sites

Run:

```bash
python src/validate_site_data.py
python src/run_all.py
python src/build_deliverable_package.py
```

Then review:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/results_interpretation.md
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/profile_rank_stability_chart.png
```

## When to add outreach rows

Do not reach out for every new site immediately.

First run the model. Then add outreach tasks for:

```text
sites that rank near the top
sites with unclear public access
sites with garage or special-use complexity
sites where electrical assumptions strongly affect the score
sites that look promising but have weak input confidence
```

Add those tasks to:

```text
data/source_extracts/stakeholder_response_tracker.csv
```

## Simple rule

Add many sites with public data first. Then verify only the strongest or most uncertain sites.
