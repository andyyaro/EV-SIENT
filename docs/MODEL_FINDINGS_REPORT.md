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

The model combines official, official-derived, planning-estimate, manual-estimate, and proxy data.

Official or official-derived inputs include:

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
```

Planning, proxy, or manual-estimate inputs include:

```text
visitor and employee assumptions
remaining parking-space assumptions
remaining operating-hour assumptions
amenity category counts
electrical distance/trenching/service-upgrade estimates
local EV adoption proxy values
```

The model labels weaker inputs clearly so they can be improved later.

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

## Final ranked results

Latest V1 ranking after the local EV adoption proxy, ACS equity update, electrical feasibility estimates, official FFX002 facility hours/parking update, sensitivity analysis, and recommendation tier layer:

```text
1. FFX002 — City of Fairfax Regional Library — readiness 59.9
2. FFX001 — Fairfax City Hall or municipal building — readiness 53.1
3. PWC004 — Chinn Park Regional Library — readiness 46.5
4. PWC002 — Neabsco-Potomac Commuter Garage — readiness 43.2
5. PWC001 — PWC McCoart Government Center — readiness 40.1
6. PWC003 — Prince William County Public Safety Training Center — readiness 18.6
```

## Recommendation tiers

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC004 — Tier 2 — promising candidate, refine data
PWC002 — High-review candidate
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

## Source-quality update from official facility pages

FFX002 now has stronger facility support:

```text
parking_spaces = 199 official spaces
hours_open = 9.29 weekly-average daily public open hours
```

PWC004 has an important official status note:

```text
The official Prince William Public Libraries locations page currently lists Chinn Park Library as closed for renovation.
```

The model keeps PWC004 as a future/reopened planning candidate for now, but this should be treated as a project scope decision.

## Site-by-site interpretation

### FFX002 — City of Fairfax Regional Library

FFX002 is the strongest current candidate. It ranks first in the base model and remains first under all tested sensitivity scenarios.

Planning interpretation:

```text
Tier 1 — advance to site screening
```

Why it performs well:

```text
public library use
public accessibility
strong surrounding demand context
strong equity context
official parking and operating-hours support
lower planning-level electrical distance/cost burden than several other sites
stable first-place ranking under sensitivity testing
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and average dwell time
confirm likely charger placement
```

### FFX001 — Fairfax City Hall or municipal building

FFX001 is the second strongest current candidate and remains second across all tested scenarios.

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and operating hours
confirm parking count and likely charger placement
```

### PWC004 — Chinn Park Regional Library

PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions.

Important caveat:

```text
The official library locations page currently lists Chinn Park Library as closed for renovation.
```

The project should decide whether PWC004 should be modeled using current closure status or future reopened site conditions.

### PWC002 — Neabsco-Potomac Commuter Garage

PWC002 remains important because it has a commuter-garage role and strong equity context. However, it is treated as high-review because garage installations can involve additional complexity.

Why it needs more review:

```text
garage/enclosed context
higher planning service-upgrade cost
fire/AHJ/access/ventilation/conduit-routing questions
emergency disconnect visibility not confirmed
```

### PWC001 — PWC McCoart Government Center

PWC001 is a public civic site but ranks below the stronger current candidates under V1 assumptions.

### PWC003 — Prince William County Public Safety Training Center

PWC003 remains the lowest-ranked site because it is not currently treated as a normal general-public charging site.

First decision needed:

```text
confirm whether the site should be public, fleet-only, or removed from the public-charging candidate list
```

## Sensitivity analysis result

The model tested five uncertainty scenarios:

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

The ranking stayed stable across all five scenarios.

```text
Every site had rank_range = 0.
```

This means the current ranking is stable under the tested V1 assumptions. It does not mean the ranking is final or guaranteed.

## Port-planning result

Current V1 recommendations:

```text
FFX002 — 1 port now, 2 by 2035, 2 by 2050
FFX001 — 1 port now, 2 by 2035, 2 by 2050
PWC004 — 1 port now, 1 by 2035, 2 by 2050
PWC002 — 2 ports now, 2 by 2035, 2 by 2050
PWC001 — 2 ports now, 2 by 2035, 2 by 2050
PWC003 — 2 ports now, 2 by 2035, 2 by 2050
```

Important caution: port recommendations are starter planning estimates. They should be recalibrated with better observed use, confirmed site hours, confirmed parking behavior, and stakeholder input.

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
amenities_count_0_5mi
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
1. Treat FFX002 and FFX001 as stable top candidates.
2. Treat PWC004 as the strongest current Prince William County public-library candidate under future/reopened planning assumptions.
3. Decide how to handle PWC004's current renovation closure in the project scope.
4. Keep PWC002 in the discussion, but route it through garage/fire/electrical review.
5. Keep PWC003 as special-use or fleet-only unless public access is confirmed.
6. Improve electrical capacity, visitor, parking, hours, and emergency-disconnect data before any implementation recommendation.
```
