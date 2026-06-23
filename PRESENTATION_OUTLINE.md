# Presentation Outline

## Slide 1 — Project title

Title:

```text
Public EV Charging Site-Readiness and Right-Sizing Prototype
```

Subtitle:

```text
Fairfax City and Prince William County candidate-site analysis
```

Key message:

```text
This prototype helps compare candidate public EV charging sites using demand, feasibility, safety/AHJ review, equity, and right-sizing signals.
```

## Slide 2 — Problem and motivation

Key points:

```text
Public EV charging decisions need more than a simple map of empty parking spaces.
Good sites should balance demand, electrical feasibility, public access, safety, ADA/accessibility, equity, and charger right-sizing.
Early planning needs a transparent model that can show assumptions and data gaps clearly.
```

Speaker note:

```text
The goal is not to replace engineers or permitting officials. The goal is to make early site screening more structured and explainable.
```

## Slide 3 — Candidate sites

Show the six candidate sites:

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

Optional visual:

```text
Map or simple table of candidate sites.
```

## Slide 4 — Data sources

Organize sources by quality:

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

Speaker note:

```text
A major strength of the prototype is that it labels what is official, what is official-derived, and what still needs confirmation.
```

## Slide 5 — Model scoring structure

Show formula:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Explain signals:

```text
Demand = EV adoption, jobs, households, traffic, amenities, parking, dwell time, existing charger supply
Feasibility = spare capacity, estimated install cost, distance to service, ADA layout possibility
Safety/AHJ = fire access, garage context, emergency disconnect, stormwater, battery storage
Equity = ACS-derived local equity gap signal
```

## Slide 6 — Ranked results

Show latest ranking:

```text
1. FFX002 — City of Fairfax Regional Library — 59.8
2. FFX001 — Fairfax City Hall or municipal building — 53.1
3. PWC004 — Chinn Park Regional Library — 46.5
4. PWC002 — Neabsco-Potomac Commuter Garage — 43.2
5. PWC001 — PWC McCoart Government Center — 40.1
6. PWC003 — Prince William County Public Safety Training Center — 18.6
```

Optional visual:

```text
readiness_score_chart.png
```

## Slide 7 — Recommendation tiers

Show planning tiers:

```text
FFX002 — Tier 1 — advance to site screening
FFX001 — Tier 1 — advance to site screening
PWC004 — Tier 2 — promising candidate, refine data
PWC002 — High-review candidate
PWC001 — Tier 3 — lower priority / monitor
PWC003 — Low public-priority / special-use
```

Speaker note:

```text
The tiers are useful because a site can have public value but still need high review before implementation.
```

## Slide 8 — Key site interpretations

Use concise bullets:

```text
FFX002: strongest candidate; stable first place; library/public-use context; lower planning install burden.
FFX001: stable second; civic/public-use role; should advance to screening.
PWC004: strongest current PWC public-library candidate.
PWC002: valuable commuter/equity site, but garage/fire/electrical review is required.
PWC001: lower priority under current assumptions.
PWC003: limited/non-public access; better treated as special-use or fleet question unless access changes.
```

## Slide 9 — Sensitivity analysis

Explain scenarios:

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

Finding:

```text
The ranking stayed stable across all five scenarios.
Every site had rank_range = 0.
```

Speaker note:

```text
This does not prove the model is final. It means the current ranking is stable under the tested V1 uncertainty scenarios.
```

## Slide 10 — Remaining data gaps

Show unresolved items:

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

Speaker note:

```text
The prototype is strongest when it is honest about what still needs confirmation.
```

## Slide 11 — Stakeholder questions

Suggested questions:

```text
What electrical service rating is available near the candidate parking area?
Is there spare capacity for Level 2 chargers?
Where is the nearest panel, transformer, or service point?
How difficult would trenching/conduit routing be?
Where could an emergency disconnect be placed and visible?
Are there ADA, fire access, garage, ventilation, or stormwater concerns?
What are realistic visitor, employee, parking, and operating-hour counts?
Are there existing EV charging plans or constraints at the site?
```

## Slide 12 — Final planning conclusion

Conclusion:

```text
FFX002 and FFX001 are stable top candidates.
PWC004 is the strongest current Prince William County public-library candidate.
PWC002 should remain in the discussion because of its commuter and equity role, but it needs deeper garage/fire/electrical review.
PWC003 should not be treated as a general-public charging site unless its access or use case changes.
```

Final note:

```text
The model is ready for stakeholder review, data refinement, and future expansion to additional candidate sites.
```
