# Model Findings Brief

## Project purpose

This prototype evaluates public EV charging candidate sites in Fairfax City and Prince William County.

The model supports early planning decisions. It does not replace engineering design, utility review, Fire Marshal/AHJ review, ADA/accessibility review, stormwater review, permitting, procurement, or stakeholder approval.

## Main planning question

```text
Which sites look most ready for public EV charging, how many starter ports should be considered, and what should be checked next?
```

## Candidate sites evaluated

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Latest ranked results

```text
1. FFX002 — City of Fairfax Regional Library — 65.3
2. FFX001 — Fairfax City Hall or municipal building — 57.3
3. PWC002 — Neabsco-Potomac Commuter Garage — 56.0
4. PWC004 — Chinn Park Regional Library — 52.7
5. PWC001 — PWC McCoart Government Center — 43.2
6. PWC003 — Prince William County Public Safety Training Center — 29.5
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

## Key stability finding

FFX002 is not only the top-ranked site under the base model. It also stayed ranked #1 across all five scoring profiles:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

This means FFX002 remains the strongest current candidate even when the model gives more weight to demand, equity, feasibility, or safety/AHJ factors.

## Site-by-site interpretation

FFX002 is the strongest current candidate. It ranks first and combines public access, library/public-use context, equity value, nearby jobs/households, official parking/hour support, reviewed OSM amenity support, lower planning-level install burden, and cross-profile stability.

FFX001 is the second strongest current candidate. It has strong civic/public-use value, reviewed OSM amenity support, and remains the second-ranked site.

PWC002 now ranks third after the corrected trenching normalization, but it remains high-review because garage installations can involve additional fire/AHJ, access, ventilation, conduit-routing, emergency-disconnect, and electrical complexity.

PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions, but the current official library page lists Chinn Park Library as closed for renovation.

PWC001 remains lower priority than the top candidates, but reviewed OSM amenities improved its demand support.

PWC003 remains the lowest public-charging priority because it is limited or non-public access and has low surrounding public-demand indicators.

## Sensitivity finding

The ranking stayed stable across all five sensitivity scenarios. Every site had `rank_range = 0`.

## Scoring profile finding

The profile analysis tested five different planning-priority perspectives. FFX002 remained the #1 site in every profile.

This supports a stronger planning conclusion: the top recommendation is stable across both uncertainty scenarios and stakeholder-priority scenarios.

## Remaining data gaps

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

## Planning conclusion

FFX002 is the strongest current candidate because it is top-ranked in the base model, stable across sensitivity scenarios, and stable across all scoring-priority profiles. FFX001 remains the second strongest candidate. PWC002 is now the third-ranked site, but it needs deeper garage/fire/electrical review before advancement. PWC004 remains the strongest current Prince William County public-library candidate under future/reopened planning assumptions, but its current closure status remains a caveat. PWC003 should not be treated as a general-public charging site unless its access or use case changes.
