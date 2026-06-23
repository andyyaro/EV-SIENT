# Model Findings Brief

## Project purpose

This prototype evaluates public EV charging candidate sites in Fairfax City and Prince William County.

The model is designed to support early planning decisions. It does not replace engineering design, utility review, Fire Marshal/AHJ review, ADA/accessibility review, stormwater review, permitting, procurement, or stakeholder approval.

## Main planning question

The model asks:

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

## Main data sources and source quality

The model combines several types of data.

Official or official-derived sources include:

```text
City of Fairfax GeoHub Addresses
Prince William County GIS Premise Addresses
AFDC / NREL Alternative Fuel Stations public active EV charger data
VDOT Bidirectional Traffic Volume 2025
ACS 2024 5-Year household and equity indicators
TIGER 2024 Virginia block group geometry
LODES 2023 workplace/job data
```

Planning estimates or proxies include:

```text
Demand assumptions v1
Amenities 0.5-mile V1 category count
Electrical feasibility V1 planning estimates
Local EV adoption V1 proxy
```

The model clearly labels planning estimates and proxies so they are not confused with confirmed engineering or official local registration data.

## Scoring method

Each site receives four major signals:

```text
demand_subscore
feasibility_subscore
safety_subscore
equity contribution
```

The final score is calculated as:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Limited or non-public sites receive an additional public-access discount.

## Latest ranked results

```text
1. FFX002 — City of Fairfax Regional Library — 59.8
2. FFX001 — Fairfax City Hall or municipal building — 53.1
3. PWC004 — Chinn Park Regional Library — 46.5
4. PWC002 — Neabsco-Potomac Commuter Garage — 43.2
5. PWC001 — PWC McCoart Government Center — 40.1
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

### FFX002 — City of Fairfax Regional Library

FFX002 is the strongest current candidate. It ranks first, remains stable under sensitivity testing, and combines public access, library/public-use context, equity value, nearby jobs/households, and the lowest planning-level install burden among the current candidates.

Recommended next step:

```text
Advance to site screening and confirm electrical capacity, emergency disconnect location, visitor counts, parking layout, and charger placement.
```

### FFX001 — Fairfax City Hall or municipal building

FFX001 is the second strongest current candidate. It has strong civic/public-use value and remains stable as the second-ranked site across sensitivity scenarios.

Recommended next step:

```text
Advance to site screening and confirm electrical capacity, parking/charger placement, site access, and emergency disconnect visibility.
```

### PWC004 — Chinn Park Regional Library

PWC004 is the strongest current Prince William County library/public-service candidate. It ranks above the other PWC sites because it has a stronger mix of public access, demand indicators, and planning feasibility than the other PWC candidates.

Recommended next step:

```text
Keep as a promising candidate and refine visitor count, hours, parking count, electrical capacity, and emergency disconnect assumptions.
```

### PWC002 — Neabsco-Potomac Commuter Garage

PWC002 has meaningful commuter, public-access, and equity value, but it remains a high-review candidate because garage installations can involve additional fire/AHJ, access, ventilation, conduit-routing, emergency-disconnect, and electrical complexity.

Recommended next step:

```text
Keep in the planning discussion, but do not treat it as straightforward until garage/fire/AHJ/access/electrical review is completed.
```

### PWC001 — PWC McCoart Government Center

PWC001 remains a lower-priority current candidate under the present V1 assumptions. Its public/civic role is useful, but it is below PWC004 and PWC002 in the current scoring because of its planning install-cost burden and lower equity contribution.

Recommended next step:

```text
Monitor and revisit if stronger demand, parking, electrical, or stakeholder data improves its case.
```

### PWC003 — Prince William County Public Safety Training Center

PWC003 remains the lowest public-charging priority because it is limited or non-public access and has low surrounding public-demand indicators.

Recommended next step:

```text
Confirm whether this site should be public charging, fleet/support charging, or removed from the general-public candidate list.
```

## Sensitivity analysis finding

The model was tested under five scenarios:

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

This means the current ranking is stable under the tested V1 uncertainty scenarios. It does not mean the ranking is final or guaranteed under all possible assumptions.

## Important remaining data gaps

The most important fields still needing confirmation are:

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

## Recommended stakeholder questions

For facilities, utility, or site owners:

```text
What is the electrical service rating at or near the candidate parking area?
Is there spare capacity for Level 2 charging without a service upgrade?
Where is the nearest panel, transformer, or service point?
Would trenching/conduit routing be simple, moderate, or difficult?
Where could an emergency disconnect be placed and remain visible to responders?
Are there ADA-accessible parking spaces or routes near the candidate area?
Are there fire access, garage, ventilation, or stormwater concerns?
What are the best estimates for daily visitors, employees, parking supply, and operating hours?
Are there existing EV charging plans or constraints at the site?
```

## Planning conclusion

For the current prototype, FFX002 and FFX001 are stable top candidates. PWC004 is the strongest current Prince William County public-library candidate. PWC002 should remain in the discussion because of its commuter and equity role, but it needs deeper garage/fire/electrical review before advancement. PWC003 should not be treated as a general-public charging site unless its access or use case changes.
