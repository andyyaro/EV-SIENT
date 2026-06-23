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
1. FFX002 — City of Fairfax Regional Library — 59.9
2. FFX001 — Fairfax City Hall or municipal building — 53.1
3. PWC004 — Chinn Park Regional Library — 48.0
4. PWC002 — Neabsco-Potomac Commuter Garage — 44.3
5. PWC001 — PWC McCoart Government Center — 42.1
6. PWC003 — Prince William County Public Safety Training Center — 18.6
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

## Site-by-site interpretation

FFX002 is the strongest current candidate. It ranks first and combines public access, library/public-use context, equity value, nearby jobs/households, official parking/hour support, reviewed OSM amenity support, and lower planning-level install burden.

FFX001 is the second strongest current candidate. It has strong civic/public-use value, reviewed OSM amenity support, and remains the second-ranked site.

PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions, but the current official library page lists Chinn Park Library as closed for renovation.

PWC002 has meaningful commuter, public-access, and equity value, but it remains high-review because garage installations can involve additional fire/AHJ, access, ventilation, conduit-routing, emergency-disconnect, and electrical complexity.

PWC001 remains lower priority than the top candidates, but reviewed OSM amenities improved its demand support.

PWC003 remains the lowest public-charging priority because it is limited or non-public access and has low surrounding public-demand indicators.

## Sensitivity finding

The ranking stayed stable across all five sensitivity scenarios. Every site had `rank_range = 0`.

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

FFX002 and FFX001 are stable top candidates. PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions, but its current closure status remains a caveat. PWC002 should remain in the discussion because of its commuter and equity role, but it needs deeper garage/fire/electrical review before advancement. PWC003 should not be treated as a general-public charging site unless its access or use case changes.
