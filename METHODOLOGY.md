# Methodology

This document explains how the EV Charger Site-Readiness and Right-Sizing Prototype scores candidate sites and recommends starter charging ports.

The goal is transparency. The model should be easy to inspect, adjust, and explain to a planner, mentor, reviewer, or stakeholder.

## What the model is trying to answer

The model asks two related but different questions:

```text
1. Should this site be prioritized for public EV charging?
2. If yes, how many starter charging ports should be considered?
```

These are not the same question. A site can rank highly as a strategic public charging location but still only need a small starter installation. A site can also need extra review even if its demand looks strong.

## Input dataset

The current working dataset is:

```text
real_sites_v1.csv
```

Each row represents one candidate site. Current V1 candidate sites are:

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

The older `sites.csv` remains in the repository as a starter/demo dataset.

## Data sources used in V1

The current V1 model combines official, official-derived, and assumption-based fields.

Official or official-derived sources already used:

```text
- City of Fairfax GeoHub Addresses
- Prince William County GIS Premise Addresses
- AFDC / NREL Alternative Fuel Stations export
- VDOT Bidirectional Traffic Volume 2025
- ACS 2024 5-Year B11001 Household Type
- TIGER Line 2024 Virginia Block Groups
- LODES 2023 Virginia Workplace Area Characteristics
```

Small model-ready extracts are stored under:

```text
data/source_extracts/
```

The repository does not store all full raw exports because some are large. Instead, it stores the extracted values used by the model and documents the source files in the data folder.

## Overall scoring structure

Each site receives four major subscores:

```text
demand_subscore
feasibility_subscore
safety_subscore
equity contribution
```

The final readiness score is calculated as:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Then, if the site is limited-access or not generally open to the public, the model applies a public-access discount.

## Normalization

Several input fields use different units. For example:

```text
nearby households = count of households
nearby jobs = count of jobs
traffic = AADT vehicles per day
existing charging ports = count of ports
installation cost = dollars
```

To compare these fields fairly, the model converts selected fields to a 0-to-1 scale using min-max normalization.

That means the lowest value among the candidate sites becomes 0 and the highest value becomes 1.

This is useful for a small prototype, but it also means scores are relative to the current candidate list. Adding more sites later can change normalized values and rankings.

## Demand subscore

The demand subscore estimates how strongly a site looks like a public charging opportunity.

Current demand components:

```text
0.30 * local EV share
0.20 * nearby jobs within 1 mile
0.20 * nearby households within 1 mile
0.10 * nearest AADT traffic
0.10 * nearby amenities
0.10 * average dwell time
-0.20 * existing nearby charger supply
```

In plain English:

```text
More EV adoption helps.
More nearby jobs help.
More nearby households help.
More traffic helps.
More amenities help.
Longer dwell time helps.
More existing chargers nearby reduce new need.
```

Current limitation: amenities are still mostly zero/placeholders, so they do not yet meaningfully affect the current rankings.

## Public access adjustment

The model now includes a public-access adjustment.

```text
public_access = 1 means normal public charging candidate.
public_access = 0 means limited-access, private, or special-use site.
```

Limited-access sites stay in the model, but they are discounted as public charging priorities.

Current adjustment:

```text
public_access = 1 -> access_adjustment = 1.00
public_access = 0 -> access_adjustment = 0.35
```

The demand subscore is multiplied by `access_adjustment`.

The final readiness score also receives a separate access discount:

```text
public_access = 1 -> readiness_access_adjustment = 1.00
public_access = 0 -> readiness_access_adjustment = 0.65
```

This is why the Prince William County Public Safety Training Center can remain in the dataset without ranking like a normal public library or city hall site.

## Feasibility subscore

The feasibility subscore estimates how easy the site may be to build on from a planning perspective.

Current feasibility components:

```text
0.35 * spare electrical capacity
0.25 * low estimated installation cost
0.20 * short distance to service
0.20 * ADA layout possible
```

In plain English:

```text
More spare electrical capacity helps.
Lower install cost helps.
Shorter service distance helps.
ADA layout feasibility helps.
```

Current limitation: many electrical and cost fields are still placeholders or assumptions. This subscore should be improved with stakeholder input, utility review, or site review.

## Safety subscore

The safety subscore estimates whether the site has obvious model-level review concerns.

Current safety components:

```text
0.35 * fire access OK
0.20 * not an enclosed garage
0.20 * emergency disconnect visible or confirmed
0.15 * no stormwater or firefighting runoff concern
0.10 * no battery storage flag
```

In plain English:

```text
Fire apparatus access matters.
Enclosed garages require extra attention.
Emergency disconnect visibility matters.
Stormwater and firefighting runoff concerns matter.
Battery storage adds review complexity.
```

This subscore is a planning flag only. It does not replace Fire Marshal, AHJ, ADA, utility, stormwater, engineering, or permitting review.

## Equity contribution

The final score includes an equity contribution worth 10 percent of the readiness score.

Current field:

```text
equity_gap_index
```

Current limitation: `equity_gap_index` is still a project-created placeholder. It should later be improved using ACS variables such as income, vehicle access, renter share, or other defensible equity indicators.

## Expected sessions per day

The model estimates expected charging sessions per day separately from readiness score.

This means:

```text
readiness_score = site priority
expected_sessions_day = estimated use level
recommended_ports_now = starter port count
```

Expected sessions are currently based on:

```text
visitors_day
employees_day
fleet_vehicles
ev_share_local
site_type behavior assumptions
public access adjustment
equity factor
amenities factor
existing charger supply factor
```

A fallback minimum of 0.3 sessions per day is used so every site can still be evaluated by the queueing logic.

## Site-type behavior assumptions

Different site types have different charging behavior assumptions.

Current site types include:

```text
library
office
clinic
garage
public_safety
fleet
```

Examples:

```text
Libraries have shorter average charging sessions than garages.
Garages have longer dwell time.
Public safety sites are treated as special-use and lower public-capture sites.
Fleet sites are modeled separately from public visitors.
```

These are adjustable prototype assumptions, not permanent facts.

## Port recommendation logic

The model recommends ports using a simple queueing/utilization check.

It tests one port, then two ports, then three ports, and so on until the site meets both conditions:

```text
estimated utilization <= target utilization
mean wait time <= 10 minutes
```

The model recommends:

```text
recommended_ports_now
recommended_ports_2035
recommended_ports_2050
```

Future years use simple growth assumptions:

```text
2035 demand = current expected sessions * 1.6
2050 demand = current expected sessions * 2.4
```

These future values are planning scenarios, not forecasts.

## AHJ review flag

The model creates an `ahj_review_flag` when a site has review concerns.

Current triggers include:

```text
garage_enclosed = 1
battery_storage_flag = 1
fire_access_ok = 0
emergency_disconnect_visible = 0
stormwater_risk = 1
ada_layout_possible = 0
```

The model also creates a plain-English `review_reason` explaining what triggered the review flag.

Examples:

```text
Emergency disconnect visibility not confirmed
Enclosed garage or limited ventilation/access
Limited or non-public access
Stormwater or firefighting runoff concern
```

## Current interpretation of V1 results

The current V1 model generally separates sites into two groups.

Public charging priority sites:

```text
City of Fairfax Regional Library
Chinn Park Regional Library
PWC McCoart Government Center
Fairfax City Hall or municipal building
```

Special or high-review sites:

```text
Neabsco-Potomac Commuter Garage
Prince William County Public Safety Training Center
```

The garage has a higher review burden because it is an enclosed/garage setting and already has significant nearby charging supply. The Public Safety Training Center is a real facility, but it is limited-access and rural, so it is better interpreted as a special-use or fleet-support candidate rather than a normal public charging priority.

## Current limitations

The current model is useful for a transparent V1 prototype, but several fields still need improvement:

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
electrical capacity assumptions
trenching and service upgrade assumptions
ADA layout assumptions
fire access assumptions
emergency disconnect assumptions
stormwater assumptions
battery storage assumptions
```

## What should be improved next

Recommended next improvements:

```text
1. Build a data dictionary for every CSV column.
2. Improve visitor, employee, parking, and hours assumptions.
3. Add amenities near each site.
4. Improve equity scoring using ACS variables.
5. Improve electrical, trenching, and service upgrade assumptions.
6. Add clearer special-use handling for fleet or public safety facilities.
```

## Important limitation

This is a planning-support prototype. It does not approve, design, permit, or certify EV charging installations.

Any real project would still need review from the appropriate AHJ, Fire Marshal, ADA/accessibility reviewers, utility, stormwater staff, engineers, and permitting offices.
