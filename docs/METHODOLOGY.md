# Methodology

This document explains how the EV Charger Site-Readiness and Right-Sizing Prototype scores candidate sites, estimates starter charging ports, tracks data confidence, stress-tests assumptions, and translates outputs into planning actions.

The model is a planning-support tool. It does not replace utility review, engineering, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.

## Main questions

```text
1. Should this site be prioritized for public EV charging follow-up?
2. If yes, how many starter charging ports should be considered?
3. How much future-ready capacity should be planned for 2035 and 2050?
4. How complete or confirmed is the current site data?
5. What planning action should happen next?
6. Do recommendations remain stable under alternate assumptions?
```

## Active input

The active Phase 2 input file is:

```text
data/inputs/real_sites_v2.csv
```

The stable V1 input remains available on `main`:

```text
data/inputs/real_sites_v1.csv
```

## Main public visual artifact

The main public-facing visual artifact is the Tableau workbook:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
tableau/README.md
```

Tableau-ready CSV inputs are generated from current V2 outputs with:

```bash
python src/build_tableau_exports.py
```

Static PNG charts remain generated support outputs for reproducibility, GitHub previews, and the technical deliverable package.

## Main scoring structure

Each site receives four major signals:

```text
demand_subscore
feasibility_subscore
safety_subscore
equity_subscore
```

The final readiness score is:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Limited or non-public sites receive an additional access adjustment so they can remain in the dataset without ranking like normal public-charging sites.

## Demand subscore

The current V2 demand subscore uses:

```text
0.18 * nearby households within 1 mile
0.18 * nearby jobs within 1 mile
0.13 * nearest AADT traffic exposure
0.11 * nearby amenities
0.10 * parking spaces
0.08 * operating-hours signal
0.07 * average dwell time
0.08 * local EV-share signal
0.07 * inverse existing nearby charger supply
```

The local EV-share signal is scaled against a fixed benchmark:

```text
ev_share_signal = min(ev_share_local / 0.10, 1.0)
```

The fixed benchmark avoids exaggerating small EV-share differences in a small candidate-site dataset.

Existing nearby charging supply lowers demand pressure because a site with many nearby chargers may have less unmet public-charging need.

## Amenities method

The active `amenities_count_0_5mi` field uses a reviewed OpenStreetMap / Overpass POI method instead of the original manual V1 count.

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

The method is consistent across the active site set. It is reproducible open POI/GIS support, but it is not official local government confirmation.

Special review rule:

```text
PWC003 remains 0 for amenities_count_0_5mi because its only OSM category was facility-related civic/public context and the site is limited or not general public.
```

## Feasibility subscore

Current feasibility components:

```text
0.35 * spare electrical capacity signal
0.25 * inverse distance-to-service signal
0.25 * inverse estimated install-cost signal
0.15 * inverse trenching-distance signal
```

Current limitation: distance, trenching, and service-upgrade cost are planning-level estimates. Electrical service rating, spare capacity, and emergency disconnect visibility still need facility, utility, or site review.

## Safety / review subscore

Current safety and review components:

```text
0.35 * ADA layout possible
0.35 * fire access OK
0.15 * not an enclosed garage
0.10 * emergency disconnect visible or confirmed
0.05 * no stormwater risk flag
```

Garage sites remain high-review because they may involve extra fire/AHJ, ventilation, access, conduit-routing, emergency-disconnect, and operator-review questions.

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

The right-sizing scenario layer expands this into:

```text
ports_now
ports_2035_base
ports_2035_high
ports_2050_base
ports_2050_high
future_ready_capacity
expansion_strategy
```

The port recommendation is separate from readiness. A site can be high priority but still only need a small starter installation.

## Port-use simulation

The port-use simulation tests port counts under different demand cases. It estimates:

```text
utilization percentage
peak demand ratio
estimated wait minutes
queue risk level
capacity status
```

This is a planning-screen simulation, not a detailed traffic, queuing, utility, or site-design study.

## Port-sizing scenario analysis

The port-sizing scenario analysis stress-tests port recommendations under alternate assumptions.

The scenario input is:

```text
data/inputs/v2_port_sizing_scenarios.csv
```

Current scenarios:

```text
base
high_growth
long_sessions
short_daily_window
peakier_demand
combined_stress
```

Current interpretation:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

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

The tier layer summarizes broad planning priority. It does not mean a site is ready to build.

## Data confidence layer

The model also adds a separate data-confidence layer.

```text
data_confidence_score
data_confidence_level
data_confidence_reason
```

The confidence score does not change the readiness ranking. It shows how complete or confirmed the current inputs are.

The score is lowered by missing, placeholder, or high-review items such as:

```text
electrical service rating
spare electrical capacity
emergency disconnect visibility
distance to service
trenching distance
parking spaces
operating hours
visitor and employee assumptions
public access uncertainty
garage context
planning-assumption notes
unconfirmed notes
```

## Readiness-confidence action matrix

After the main model runs, `src/add_action_matrix.py` combines readiness and confidence into simple next-action fields:

```text
readiness_band
confidence_band
readiness_confidence_cell
action_label
action_detail
```

This prevents the project from treating a high readiness score as permission to build. The action matrix says what should be checked next.

## Sensitivity analysis

Sensitivity analysis tests whether rankings remain stable when uncertain assumptions change. The current five scenarios are:

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

This is a scenario test, not a full Monte Carlo simulation.

## Scoring-profile analysis

Scoring-profile analysis tests whether rankings change when different planning priorities are emphasized.

Profiles are configured in:

```text
data/config/scoring_profiles.csv
```

Current profiles:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

## Important limitation

A high readiness score does not mean a site is build-ready.

The prototype is for early planning support only. Any real project would still need utility, engineering, accessibility, fire/AHJ, stormwater, permitting, procurement, stakeholder, and site-owner review.
