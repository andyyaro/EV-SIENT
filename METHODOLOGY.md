# Methodology

This document explains how the EV Charger Site-Readiness and Right-Sizing Prototype scores candidate sites, recommends starter charging ports, and translates outputs into planning recommendation tiers.

The goal is transparency. The model should be easy to inspect, adjust, and explain to a planner, mentor, reviewer, or stakeholder.

## What the model is trying to answer

The model asks three related but different questions:

```text
1. Should this site be prioritized for public EV charging?
2. If yes, how many starter charging ports should be considered?
3. What planning action should happen next?
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

The current V1 model combines official, official-derived, planning-estimate, and proxy fields.

Official or official-derived sources already used:

```text
- City of Fairfax GeoHub Addresses
- Prince William County GIS Premise Addresses
- AFDC / NREL Alternative Fuel Stations export
- VDOT Bidirectional Traffic Volume 2025
- ACS 2024 5-Year B11001 Household Type
- TIGER Line 2024 Virginia Block Groups
- LODES 2023 Virginia Workplace Area Characteristics
- ACS 2024 5-Year equity indicators and TIGER geometry
```

Manual, planning-estimate, or proxy extracts already used:

```text
- Demand assumptions v1
- Amenities 0.5-mile V1 category count
- Electrical feasibility V1 planning estimates
- Local EV adoption V1 proxy
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
amenities = count of nearby public-use amenity categories
parking = count of parking spaces
existing charging ports = count of ports
installation cost = dollars
```

To compare these fields fairly, the model converts selected fields to a 0-to-1 scale using min-max normalization.

That means the lowest value among the candidate sites becomes 0 and the highest value becomes 1.

This is useful for a small prototype, but it also means scores are relative to the current candidate list. Adding more sites later can change normalized values and rankings.

Important exception: `ev_share_local` is not min-max normalized. The model now scales it against a fixed 10 percent high-adoption benchmark. This prevents small local EV-share differences from becoming exaggerated when the candidate list only has a few sites.

## Demand subscore

The demand subscore estimates how strongly a site looks like a public charging opportunity.

Current demand components:

```text
0.25 * local EV share signal
0.18 * nearby jobs within 1 mile
0.18 * nearby households within 1 mile
0.10 * nearest AADT traffic
0.10 * nearby amenities
0.09 * parking spaces
0.10 * average dwell time
-0.20 * existing nearby charger supply
```

The local EV-share signal is calculated as:

```text
ev_share_signal = min(ev_share_local / 0.10, 1.0)
```

This means 10 percent local EV share or higher receives the maximum EV-share demand signal. A 2 percent local EV share receives a 0.20 signal.

In plain English:

```text
More EV adoption helps.
More nearby jobs help.
More nearby households help.
More traffic helps.
More amenities help.
More parking helps slightly because it suggests a larger site capacity.
Longer dwell time helps.
More existing chargers nearby reduce new need.
```

Current limitation: amenities, parking, and local EV adoption are not all official local values yet. `amenities_count_0_5mi`, `parking_spaces`, and the current local EV adoption values should later be replaced with stronger GIS/POI, facility, DMV/locality, stakeholder, or documented manual-count data.

Important weighting note: the current 0.09 parking weight is intentionally low because `parking_spaces` is not official data yet. Once parking counts become official or strongly verified, this weight should be revisited and may need to be increased or recalibrated against the other demand indicators.

## Public access adjustment

The model includes a public-access adjustment.

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

Current limitation: distance, trenching, and service-upgrade cost are planning-level V1 estimates. Electrical service rating, spare capacity, and emergency disconnect visibility still need stakeholder input, utility review, or site review.

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

## Recommendation tier layer

After scoring and port right-sizing, the model now adds a planning recommendation layer.

The normal `site_results.csv` output includes:

```text
model_rank
recommendation_tier
planning_recommendation
priority_reason
data_needed_next
```

The recommendation layer is intentionally separate from the readiness score. A site can have public value but still require high review before it should advance.

Current tier categories:

```text
Tier 1 — advance to site screening
Tier 2 — promising candidate, refine data
High-review candidate
Low public-priority / special-use
Tier 3 — lower priority / monitor
```

Plain-English interpretation:

```text
Tier 1 = strong current candidate; advance to site screening and stakeholder confirmation.
Tier 2 = promising candidate; improve assumptions before advancement.
High-review = keep in discussion, but review garage/fire/AHJ/access/electrical issues first.
Low public-priority = do not advance as public charging until access/use case is confirmed.
Tier 3 = monitor or revisit after stronger data is available.
```

The recommendation layer does not replace utility, engineering, ADA, Fire Marshal, AHJ, stormwater, permitting, or procurement review.
