# Presentation Outline

## Slide 1 — Project title

```text
Public EV Charging Site-Readiness and Right-Sizing Prototype
Fairfax City and Prince William County candidate-site analysis
```

## Slide 2 — Problem and motivation

```text
Public EV charging decisions need more than a map of empty parking spaces.
Good sites should balance demand, electrical feasibility, public access, safety, ADA/accessibility, equity, and charger right-sizing.
```

## Slide 3 — Candidate sites map

```text
Show data/outputs/charts/site_readiness_map.png
Use the map to show where the six candidate sites are located and how their readiness scores compare spatially.
The star marker highlights the top candidate.
The subtitle should show that FFX002 is #1 in the base model, stable in sensitivity analysis, and #1 across all scoring profiles.
```

Speaker note:

```text
This map is a presentation visual, not a parcel map or engineering layout. It helps connect the ranking result to geography while reminding viewers that site-screening and technical review still come later.
```

## Slide 4 — Candidate sites

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Slide 5 — Data sources

```text
Official / official-derived / open GIS:
- City of Fairfax GIS addresses
- Prince William County GIS premise addresses
- AFDC / NREL public active EV charger data
- VDOT 2025 traffic data
- ACS 2024 5-Year household/equity data
- TIGER 2024 block group geometry
- LODES 2023 jobs data
- Official facility hours/parking for FFX002
- Official current renovation status for PWC004
- Reviewed OSM / Overpass POI categories for amenities

Planning estimates / proxies:
- Demand assumptions v1
- Electrical feasibility planning estimates
- Local EV adoption proxy
```

## Slide 6 — Model scoring structure

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

## Slide 7 — Ranked results

```text
1. FFX002 — 65.3
2. FFX001 — 57.3
3. PWC002 — 56.0
4. PWC004 — 52.7
5. PWC001 — 43.2
6. PWC003 — 29.5
```

## Slide 8 — Recommendation tiers

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC002 — High-review candidate
PWC004 — Tier 2 — promising candidate, refine data
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

## Slide 9 — Sensitivity analysis

```text
The model tested five uncertainty scenarios.
The ranking stayed stable across all five.
Every site had rank_range = 0.
```

## Slide 10 — Scoring profile analysis

```text
The model also tested five planning-priority profiles:
- base
- demand priority
- equity priority
- feasibility priority
- safety priority

FFX002 ranked #1 in every profile.
```

Speaker note:

```text
This matters because different stakeholders may value different things. A site that stays strong across multiple priority profiles is more defensible than a site that only ranks well under one weighting setup.
```

## Slide 11 — Strongest finding

```text
FFX002 is the strongest current candidate because it is:
1. ranked #1 in the base model,
2. stable across all sensitivity scenarios, and
3. ranked #1 across all scoring-priority profiles.
```

## Slide 12 — Remaining data gaps

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

## Slide 13 — Current source-quality note

```text
FFX002 parking and hours are now supported by an official facility page.
PWC004's official library page currently lists Chinn Park Library as closed for renovation.
PWC004 remains modeled under the future/reopened planning assumption.
PWC002 ranks third in the corrected model, but remains a high-review garage candidate.
Amenities now use reviewed OSM/Overpass six-category POI counts.
The site map is a planning visual only, not a parcel boundary or engineering map.
```

## Slide 14 — Final conclusion

```text
FFX002 is the most stable top candidate.
FFX001 is the second strongest current candidate.
PWC002 should remain in discussion but needs garage/fire/electrical review before advancement.
PWC004 is the strongest current Prince William County public-library candidate under future/reopened planning assumptions.
PWC003 should not be treated as a general-public site unless its access or use case changes.
```
