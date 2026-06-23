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

The current V1 model evaluates six sites:

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
```

Planning, proxy, or manual-estimate inputs include:

```text
visitor and employee assumptions
parking-space assumptions
operating-hour assumptions
amenity category counts
electrical distance/trenching/service-upgrade estimates
local EV adoption proxy values
```

The model labels these weaker inputs clearly so they can be improved later.

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

## What the scores mean

The readiness score is a planning signal, not a final approval.

```text
Higher readiness_score = stronger current public-charging candidate
Higher demand_subscore = stronger demand indicators
Higher feasibility_subscore = easier planning-level build conditions
Higher safety_subscore = fewer model-level review triggers
```

A site can score well and still need additional review. For example, a site may have strong demand and equity value but still need garage, electrical, Fire Marshal, or emergency-disconnect review before advancing.

## Final ranked results

Latest V1 ranking after the local EV adoption proxy, ACS equity update, electrical feasibility estimates, sensitivity analysis, and recommendation tier layer:

```text
1. FFX002 — City of Fairfax Regional Library — readiness 59.8
2. FFX001 — Fairfax City Hall or municipal building — readiness 53.1
3. PWC004 — Chinn Park Regional Library — readiness 46.5
4. PWC002 — Neabsco-Potomac Commuter Garage — readiness 43.2
5. PWC001 — PWC McCoart Government Center — readiness 40.1
6. PWC003 — Prince William County Public Safety Training Center — readiness 18.6
```

## Recommendation tiers

The model now converts scores and review flags into planning recommendation tiers.

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC004 — Tier 2 — promising candidate, refine data
PWC002 — High-review candidate
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

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
lower planning-level electrical distance/cost burden than several other sites
stable first-place ranking under sensitivity testing
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and operating hours
confirm parking count and likely charger placement
```

### FFX001 — Fairfax City Hall or municipal building

FFX001 is the second strongest current candidate and remains second across all tested scenarios.

Planning interpretation:

```text
Tier 1 — advance to site screening
```

Why it performs well:

```text
public municipal site
high nearby jobs
strong public/civic role
stable second-place ranking
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and operating hours
confirm parking count and likely charger placement
```

### PWC004 — Chinn Park Regional Library

PWC004 is the strongest current Prince William County public-library candidate in the model.

Planning interpretation:

```text
Tier 2 — promising candidate, refine data
```

Why it performs well:

```text
public library use
strong traffic context
moderate planning-level feasibility
stronger public-use fit than the other current PWC sites
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and operating hours
confirm parking count and likely charger placement
```

### PWC002 — Neabsco-Potomac Commuter Garage

PWC002 remains important because it has a commuter-garage role and strong equity context. However, it is treated as high-review because garage installations can involve additional complexity.

Planning interpretation:

```text
High-review candidate
```

Why it stays in the discussion:

```text
commuter parking role
public access
high equity signal
longer dwell time potential
```

Why it needs more review:

```text
garage/enclosed context
higher planning service-upgrade cost
fire/AHJ/access/ventilation/conduit-routing questions
emergency disconnect visibility not confirmed
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
complete garage fire/AHJ/access review
confirm charger placement and conduit routing
```

### PWC001 — PWC McCoart Government Center

PWC001 is a public civic site but ranks below the stronger current candidates under V1 assumptions.

Planning interpretation:

```text
Tier 3 — lower priority / monitor
```

Why it ranks lower:

```text
moderate demand score
higher planning install-cost burden than some alternatives
lower equity contribution than PWC002 and the Fairfax City sites
```

Important next confirmations:

```text
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
confirm visitor/employee counts and operating hours
confirm parking count and likely charger placement
```

### PWC003 — Prince William County Public Safety Training Center

PWC003 remains the lowest-ranked site because it is not currently treated as a normal general-public charging site.

Planning interpretation:

```text
Low public-priority / special-use
```

Why it ranks low:

```text
limited or non-public access
low nearby household and job density
low surrounding public-demand indicators
special-use/public-safety facility context
```

Important next confirmations:

```text
confirm whether the site should be public, fleet-only, or removed from the public-charging candidate list
confirm electrical service rating
confirm spare capacity or upgrade need
confirm emergency disconnect location/visibility
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

This means the current ranking is stable under the tested V1 assumptions. It does not mean the ranking is final or guaranteed. It means the current site order did not change when uncertain demand, EV adoption, trenching, and service-upgrade cost assumptions were pushed lower and higher.

## Port-planning result

The model recommends starter port counts for the current period and planning growth counts for 2035 and 2050.

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

## Main findings

The strongest overall finding is that FFX002 and FFX001 are stable top candidates under the current V1 model.

The strongest Prince William County public-library/public-service candidate is PWC004.

PWC002 should not be dismissed because of its commuter and equity role, but it should not be treated as straightforward because garage installations require deeper review.

PWC003 should not be treated as a normal general-public charging candidate unless its access/use case changes.

## Remaining data gaps

The most important unresolved fields are:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open
parking_spaces
amenities_count_0_5mi
local EV adoption counts
```

The current validator reports no blocking errors or warnings, but still flags review items because these fields are not fully confirmed.

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

### Equity / planning questions

```text
Are there nearby communities with lower home-charging access?
Are there renters or multifamily residents who may benefit from public charging?
Are there existing public chargers nearby that already meet demand?
Could this site serve both destination charging and community-access charging?
```

## Planning conclusion

The current prototype is strong enough to support a preliminary planning conversation.

Recommended near-term focus:

```text
1. Treat FFX002 and FFX001 as stable top candidates.
2. Treat PWC004 as the strongest current Prince William County public-library candidate.
3. Keep PWC002 in the discussion, but route it through garage/fire/electrical review.
4. Keep PWC003 as special-use or fleet-only unless public access is confirmed.
5. Improve electrical capacity, visitor, parking, hours, and emergency-disconnect data before any implementation recommendation.
```
