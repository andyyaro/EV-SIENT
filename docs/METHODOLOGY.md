# Methodology

This document explains how the EV Charger Site-Readiness and Right-Sizing Prototype scores candidate sites, recommends starter charging ports, and translates outputs into planning recommendation tiers.

The model is a planning-support tool. It does not replace utility review, engineering, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.

## Main questions

```text
1. Should this site be prioritized for public EV charging?
2. If yes, how many starter charging ports should be considered?
3. What planning action should happen next?
```

## Main input

```text
data/inputs/real_sites_v1.csv
```

## Main scoring structure

Each site receives four major signals:

```text
demand_subscore
feasibility_subscore
safety_subscore
equity contribution
```

The final readiness score is:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Limited or non-public sites receive an additional public-access discount.

## Demand subscore

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

EV share is scaled against a fixed benchmark:

```text
ev_share_signal = min(ev_share_local / 0.10, 1.0)
```

The fixed benchmark avoids exaggerating small EV-share differences in a six-site dataset.

## Amenities method

The active `amenities_count_0_5mi` field now uses a reviewed OpenStreetMap / Overpass POI method instead of the original manual V1 count.

The reviewed source extract is:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

The OSM workflow counts whether each site has POIs in six planning categories within 0.5 miles:

```text
civic_public
entertainment_culture
food
recreation
retail
transit
```

The method is consistent across all six sites. It is reproducible open POI/GIS support, but it is not official local government confirmation.

Special review rule:

```text
PWC003 remains 0 for amenities_count_0_5mi because its only OSM category was facility-related civic/public context and the site is limited or not general public.
```

## Feasibility subscore

Current feasibility components:

```text
0.35 * spare electrical capacity
0.25 * low estimated installation cost
0.20 * short distance to service
0.20 * ADA layout possible
```

Current limitation: distance, trenching, and service-upgrade cost are planning-level V1 estimates. Electrical service rating, spare capacity, and emergency disconnect visibility still need facility, utility, or site review.

## Safety subscore

Current safety components:

```text
0.35 * fire access OK
0.20 * not an enclosed garage
0.20 * emergency disconnect visible or confirmed
0.15 * no stormwater/firefighting runoff concern
0.10 * no battery storage flag
```

Garage sites remain high-review because they may involve extra fire/AHJ, ventilation, access, conduit-routing, and emergency-disconnect questions.

## Public access adjustment

```text
public_access = 1 -> access_adjustment = 1.00
public_access = 0 -> access_adjustment = 0.35
public_access = 1 -> readiness_access_adjustment = 1.00
public_access = 0 -> readiness_access_adjustment = 0.65
```

This keeps limited-access sites in the dataset without letting them rank like normal public charging sites.

## Port recommendations

The model estimates expected sessions per day and uses a simple queueing/utilization check to recommend starter charging ports for:

```text
now
2035
2050
```

The port recommendation is separate from readiness. A site can be high priority but still only need a small starter installation.

## Recommendation tier layer

The model adds planning guidance columns:

```text
model_rank
recommendation_tier
planning_recommendation
priority_reason
data_needed_next
```

Current tier categories:

```text
Tier 1 — advance to site screening
Tier 2 — promising candidate, refine data
High-review candidate
Low public-priority / special-use
Tier 3 — lower priority / monitor
```

## Sensitivity analysis

Sensitivity analysis tests whether rankings remain stable when uncertain V1 assumptions change. The current five scenarios are:

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

The latest result showed that every site had `rank_range = 0`, meaning the current ranking stayed stable under the tested V1 scenarios.
