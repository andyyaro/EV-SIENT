# Results Interpretation

This file explains the current model result in plain English.

## Latest ranking

```text
1. FFX002 — City of Fairfax Regional Library — 59.9
2. FFX001 — Fairfax City Hall or municipal building — 53.1
3. PWC004 — Chinn Park Regional Library — 48.0
4. PWC002 — Neabsco-Potomac Commuter Garage — 44.3
5. PWC001 — PWC McCoart Government Center — 42.1
6. PWC003 — Prince William County Public Safety Training Center — 18.6
```

## Current recommendation tiers

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC004 — Tier 2 — promising candidate, refine data
PWC002 — High-review candidate
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

## Main interpretation

FFX002 is the strongest current candidate. It remains first and combines public library use, nearby jobs/households, equity value, official parking/hour support, reviewed OSM amenity support, lower planning install burden, and cross-profile stability.

FFX001 is the second strongest current candidate because of its civic/public-use role, reviewed OSM amenity support, and stable ranking.

PWC004 is the strongest current Prince William County public-library candidate under the future/reopened planning assumption, but the current official library page lists Chinn Park Library as closed for renovation.

PWC002 has commuter and equity value, but it remains high-review because garage installations can create additional fire/AHJ, ventilation, access, conduit-routing, and electrical questions.

PWC001 remains lower priority than the top candidates, but reviewed OSM amenities improved its demand support.

PWC003 is low public-priority because it is limited or non-public access and has weak surrounding public-demand indicators.

## Sensitivity and profile interpretation

The current top result is supported by two stability checks.

```text
Sensitivity analysis:
- rankings stayed stable across all five uncertainty scenarios
- every site had rank_range = 0

Scoring profile analysis:
- FFX002 ranked #1 under the base profile
- FFX002 ranked #1 under the demand-priority profile
- FFX002 ranked #1 under the equity-priority profile
- FFX002 ranked #1 under the feasibility-priority profile
- FFX002 ranked #1 under the safety-priority profile
```

Plain-English meaning: FFX002 is not just winning under one scoring setup. It remains the top site when the model emphasizes different planning priorities.

## What the result does not mean

The result does not mean a site is ready to build. It means a site is a stronger or weaker early planning candidate under the current data and assumptions.

Any real project would still need utility, engineering, ADA, Fire Marshal/AHJ, stormwater, permitting, procurement, and stakeholder review.
