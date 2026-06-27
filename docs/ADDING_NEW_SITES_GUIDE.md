# Adding New Candidate Sites Guide

## Purpose

This guide explains how to add new EV charging candidate sites without breaking the model, Tableau exports, or V2 reproducibility checks.

The active Phase 2 workflow is V2 on:

```text
v2-expansion-planning
```

Active V2 input file:

```text
data/inputs/real_sites_v2.csv
```

Template file:

```text
data/inputs/new_sites_template.csv
```

Stable V1 input file:

```text
data/inputs/real_sites_v1.csv
```

Use V1 only when reproducing the original stable baseline. Use V2 for current expansion-planning work.

## Public visual artifact

The main public-facing visual artifact is the Tableau workbook:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
tableau/README.md
```

When official V2 sites are added, Tableau-ready CSVs must also be regenerated and checked:

```bash
make tableau-exports
make check-tableau
```

Generated Tableau CSVs live under:

```text
data/outputs/tableau/
```

They are generated local outputs and should not be manually edited.

## Important checker warning

The V2 checker and Tableau checker are intentionally strict. They currently expect the 12-site V2 candidate set and the current V2 output/package/Tableau guardrails.

If you add, remove, or rename official V2 sites in `data/inputs/real_sites_v2.csv`, update these before treating the run as stable:

```text
src/check_outputs_v2.py
src/check_tableau_exports.py
data/baselines/v2_baseline_snapshot.json
src/compare_v2_to_baseline.py
```

The V1 checker remains locked to the stable V1 baseline.

For synthetic stress tests, do not edit the official input file. Use demo mode instead:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

## Template consistency status

The current template is meant to have the same column names and column order as the main input file.

```text
data/inputs/new_sites_template.csv
should match the active real-sites input being expanded
```

The example row uses `NEW001` only as a placeholder. Do not copy `NEW001` into the final model as a real site.

## Simple V2 workflow for adding a site

```text
1. Copy the template row from data/inputs/new_sites_template.csv.
2. Create a new site_id.
3. Fill in the best public data first.
4. Label uncertain values clearly in notes.
5. Add the new row to data/inputs/real_sites_v2.csv only when it is an official V2 expansion.
6. Update V2 checker, Tableau checker, and baseline expectations before treating the result as stable.
7. Run the validator.
8. Run the full V2 workflow.
9. Regenerate and validate Tableau exports.
10. Review rankings, data confidence, action labels, data-quality report, right-sizing, port-sizing scenarios, executive summary, and Tableau workbook inputs.
11. Only prioritize outreach for sites that rank well or have major uncertainty.
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
special-use public agency sites, if clearly marked special-use
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
Coordinates and address from official facility page; parking and visitors are assumptions; electrical service rating, spare capacity, and emergency disconnect remain unconfirmed.
```

## After adding new V2 sites

For an official V2 expansion, run:

```bash
python src/validate_site_data.py --input data/inputs/real_sites_v2.csv --output data/outputs/v2_data_quality_report.csv
make full-v2-tableau
```

Equivalent raw commands:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

Then review:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_executive_site_summary.csv
data/outputs/tableau/
data/outputs/deliverable_package_v2/README.md
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

Only save and commit the packaged Tableau workbook if the official public visual artifact intentionally changes.
