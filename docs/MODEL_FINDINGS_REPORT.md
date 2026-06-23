# Model Findings Report

## Project purpose

This prototype is a planning-support model for public EV charging site readiness and right-sizing in Fairfax City and Prince William County.

The model helps answer three practical planning questions:

```text
1. Which candidate sites look strongest for public EV charging?
2. How many starter charging ports should be considered?
3. What should happen next before a site advances?
```

This is not a construction, engineering, permitting, or procurement decision tool. Any real project would still need facility review, utility review, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, engineering design, and stakeholder approval.

## Candidate sites evaluated

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Data sources used

The model combines official, official-derived, open POI/GIS support, planning-estimate, and proxy data.

Key stronger inputs include:

```text
City of Fairfax GIS address data
Prince William County GIS address data
AFDC / NREL public EV charging station data
VDOT 2025 traffic volume data
ACS 2024 5-Year household and equity data
TIGER 2024 Virginia block group geometry
LODES 2023 employment data
Official facility hours/parking data for FFX002
Official current renovation-status documentation for PWC004
Reviewed OSM / Overpass POI categories for amenities
```

Inputs still needing stronger confirmation include:

```text
visitor and employee assumptions
remaining parking-space assumptions
remaining operating-hour assumptions
electrical distance/trenching/service-upgrade estimates
local EV adoption proxy values
```

## Scoring method

Each site receives four main planning subscores:

```text
demand_subscore
feasibility_subscore
safety_subscore
equity contribution
```

The final readiness score uses this weighting:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Then the model applies a public-access discount if a site is limited-access or not a normal general-public charging location.

## Scoring profile analysis

The project now includes scoring profiles that test whether the ranking changes when a stakeholder gives more weight to one planning priority.

The current profiles are:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

The profile analysis is a planning-sensitivity layer. It does not replace the main V1 ranking.

Latest result:

```text
base — FFX002 ranked #1 with score 65.3
demand_priority — FFX002 ranked #1 with score 63.3
equity_priority — FFX002 ranked #1 with score 68.7
feasibility_priority — FFX002 ranked #1 with score 64.1
safety_priority — FFX002 ranked #1 with score 70.1
```

Interpretation: FFX002 remains the strongest current candidate even when demand, equity, feasibility, or safety/AHJ considerations are weighted more heavily. This makes the top recommendation stronger than a single-scenario ranking.

## Amenities source update

The active amenities field is now based on a reviewed OpenStreetMap / Overpass POI extract:

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

Reviewed applied amenities values:

```text
PWC001 — 5
PWC002 — 6
PWC003 — 0
PWC004 — 5
FFX001 — 6
FFX002 — 6
```

The method uses six categories within 0.5 miles:

```text
civic_public
entertainment_culture
food
recreation
retail
transit
```

This is reproducible open POI/GIS support, not official local government confirmation. PWC003 remains 0 because its only OSM category was facility-related civic/public context and the site is limited or not general public.

## Final ranked results

Latest ranking after the corrected trenching-normalization fix:

```text
1. FFX002 — City of Fairfax Regional Library — readiness 65.3
2. FFX001 — Fairfax City Hall or municipal building — readiness 57.3
3. PWC002 — Neabsco-Potomac Commuter Garage — readiness 56.0
4. PWC004 — Chinn Park Regional Library — readiness 52.7
5. PWC001 — PWC McCoart Government Center — readiness 43.2
6. PWC003 — Prince William County Public Safety Training Center — readiness 29.5
```

## Recommendation tiers

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC002 — High-review candidate
PWC004 — Tier 2 — promising candidate, refine data
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

## Site-by-site interpretation

### FFX002 — City of Fairfax Regional Library

FFX002 is the strongest current candidate. It combines public library use, public accessibility, nearby jobs/households, strong equity context, official parking/hour support, reviewed OSM amenity support, lower planning-level electrical distance/cost burden than several other sites, and stable rank across all tested scoring profiles.

### FFX001 — Fairfax City Hall or municipal building

FFX001 is the second strongest current candidate. It has strong civic/public-use value and reviewed OSM amenity support.

### PWC002 — Neabsco-Potomac Commuter Garage

PWC002 is now the third-ranked site after the corrected trenching normalization. It has commuter, public-access, equity, and strong mixed-use amenity value, but it remains high-review because garage installations can involve additional fire/AHJ, access, ventilation, conduit-routing, emergency-disconnect, and electrical complexity.

### PWC004 — Chinn Park Regional Library

PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions. Its current official library page still lists Chinn Park Library as closed for renovation, so that remains a caveat.

### PWC001 — PWC McCoart Government Center

PWC001 remains below the stronger current candidates, but the reviewed OSM amenities update improved its demand support.

### PWC003 — Prince William County Public Safety Training Center

PWC003 remains the lowest-ranked site because it is not currently treated as a normal general-public charging site.

First decision needed:

```text
confirm whether the site should be public, fleet-only, or removed from the public-charging candidate list
```

## Port-planning result

Current V1 recommendations:

```text
FFX002 — 2 ports now, 2 by 2035, 2 by 2050
FFX001 — 2 ports now, 2 by 2035, 3 by 2050
PWC002 — 2 ports now, 3 by 2035, 3 by 2050
PWC004 — 2 ports now, 2 by 2035, 2 by 2050
PWC001 — 2 ports now, 2 by 2035, 3 by 2050
PWC003 — 2 ports now, 2 by 2035, 2 by 2050
```

Important caution: port recommendations are starter planning estimates. They should be recalibrated with better observed use, confirmed site hours, confirmed parking behavior, and stakeholder input.

## Cross-checks supporting the result

The current top recommendation is supported by three checks:

```text
1. Base model ranking: FFX002 ranked #1.
2. Sensitivity analysis: all six sites had rank_range = 0.
3. Scoring profile analysis: FFX002 ranked #1 across all five scoring profiles.
```

This does not mean FFX002 is ready to build. It means it is the strongest current site to advance into stakeholder and site-screening review.

## Remaining data gaps

The most important unresolved fields are:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
```

## Recommended stakeholder questions

### Electrical / facility questions

```text
What is the electrical service rating at or near the proposed charger location?
Is there spare electrical capacity for Level 2 charging without a major service upgrade?
Where is the nearest panel, transformer, or service point?
How difficult would conduit routing or trenching be?
Where could the emergency disconnect be placed so it is visible and accessible?
```

### Site / operations questions

```text
How many visitors use this site on a typical weekday and weekend?
How many employees regularly work at the site?
How many parking spaces are available near the likely charger location?
What hours would chargers realistically be available to the public?
Are there planned construction, parking, or electrification projects at this site?
```

### Safety / AHJ questions

```text
Would the proposed charger location maintain fire apparatus access?
Would any emergency disconnect or signage requirements apply?
For the garage site, are there ventilation, access, clearance, conduit-routing, or emergency-response concerns?
Are there stormwater or firefighting runoff concerns for the likely charger placement?
```

## Planning conclusion

The current prototype is strong enough to support a preliminary planning conversation.

Recommended near-term focus:

```text
1. Treat FFX002 as the most stable top candidate because it ranks first in the base model, stays stable in sensitivity analysis, and remains first across all scoring profiles.
2. Treat FFX001 as the second strongest current candidate.
3. Keep PWC002 in the discussion, but route it through garage/fire/electrical review before advancement.
4. Treat PWC004 as the strongest current Prince William County public-library candidate under future/reopened planning assumptions.
5. Keep PWC003 as special-use or fleet-only unless public access is confirmed.
6. Improve electrical capacity, visitor, parking, hours, and emergency-disconnect data before any implementation recommendation.
```
