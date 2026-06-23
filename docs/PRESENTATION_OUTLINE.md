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

## Slide 3 — Candidate sites

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Slide 4 — Data sources

```text
Official / official-derived:
- City of Fairfax GIS addresses
- Prince William County GIS premise addresses
- AFDC / NREL public active EV charger data
- VDOT 2025 traffic data
- ACS 2024 5-Year household/equity data
- TIGER 2024 block group geometry
- LODES 2023 jobs data

Planning estimates / proxies:
- Demand assumptions v1
- Amenities 0.5-mile category count
- Electrical feasibility planning estimates
- Local EV adoption proxy
```

## Slide 5 — Model scoring structure

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

## Slide 6 — Ranked results

```text
1. FFX002 — 59.8
2. FFX001 — 53.1
3. PWC004 — 46.5
4. PWC002 — 43.2
5. PWC001 — 40.1
6. PWC003 — 18.6
```

## Slide 7 — Recommendation tiers

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC004 — Tier 2 — promising candidate, refine data
PWC002 — High-review candidate
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

## Slide 8 — Sensitivity analysis

```text
The model tested five scenarios.
The ranking stayed stable across all five.
Every site had rank_range = 0.
```

## Slide 9 — Remaining data gaps

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

## Slide 10 — Final conclusion

```text
FFX002 and FFX001 are stable top candidates.
PWC004 is the strongest current Prince William County public-library candidate.
PWC002 should remain in discussion but needs garage/fire/electrical review.
PWC003 should not be treated as a general-public site unless its access or use case changes.
```
