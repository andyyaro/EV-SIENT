# Stakeholder Data Request Pack

## Purpose

This document turns the model's remaining data gaps into clear stakeholder questions.

The goal is to make it easy to ask facility staff, public works staff, utility contacts, parking/transportation staff, or Fire Marshal/AHJ reviewers for the exact information needed to improve the EV charging site-readiness model.

The model is already useful for early planning, but the next improvement is replacing V1 assumptions and placeholders with confirmed site data.

## How to use this document

Use this as a meeting checklist, email attachment, or interview guide.

The companion structured file is:

```text
data/source_extracts/stakeholder_data_request_fields.csv
```

That CSV lists each requested field, why it matters, likely owner, recommended question, affected sites, and priority level.

## Sites covered

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Highest-priority requests

These fields matter most because they directly affect feasibility, safety/AHJ review, and whether a site can advance beyond early screening.

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
likely_charger_area
nearest_panel_or_transformer_location
trenching_or_conduit_difficulty
ada_accessible_route_confirmed
fire_access_confirmed
```

## Electrical and utility questions

Ask facility/public works/utility contacts:

```text
1. What is the electrical service rating at or near the likely charger area?
2. Is there spare electrical capacity for Level 2 EV chargers without a major service upgrade?
3. Where is the nearest panel, transformer, switchgear, or service point to the likely charger area?
4. Would conduit routing or trenching be simple, moderate, or difficult?
5. Are there known electrical constraints, planned upgrades, or utility coordination requirements at this site?
6. Is there a preferred area where EV chargers should be placed from an electrical routing perspective?
```

Why this matters:

```text
Electrical capacity and routing affect the feasibility score, estimated installation burden, and whether a site should advance to detailed screening.
```

## Emergency disconnect, Fire Marshal, and AHJ questions

Ask facility staff, Fire Marshal/AHJ contacts, or public safety reviewers:

```text
1. Where could an emergency disconnect be placed so it is visible and accessible to responders?
2. Would the proposed charger location maintain fire apparatus access?
3. Are there clearance, signage, bollard, emergency-response, or access requirements that should be considered early?
4. For the garage site, are there ventilation, clearance, fire-response, conduit-routing, or access constraints?
5. Are there stormwater or firefighting runoff concerns near the likely charger area?
```

Why this matters:

```text
These answers affect safety scoring, AHJ review flags, and whether a site should be treated as straightforward or high-review.
```

## ADA and accessibility questions

Ask facilities, ADA/accessibility staff, or site planners:

```text
1. Is there an ADA-accessible route from the likely charger area to the main building or public destination?
2. Are accessible parking spaces already located near the likely charger area?
3. Would adding chargers require changes to striping, slopes, access aisles, curb ramps, or signage?
4. Are there known accessibility constraints at the candidate parking area?
```

Why this matters:

```text
ADA/accessibility confirmation affects feasibility and whether the site can advance responsibly.
```

## Parking, usage, and operations questions

Ask facility managers, parking/transportation staff, library staff, or public works contacts:

```text
1. How many parking spaces are available at the site or near the likely charger area?
2. What are typical weekday and weekend visitor counts?
3. How many employees or staff regularly work at the site?
4. What hours would chargers realistically be available to the public?
5. Are there parking restrictions, security gates, overnight limits, event conflicts, or enforcement issues?
6. Are there existing plans for EV charging, fleet electrification, parking changes, or construction at this site?
```

Why this matters:

```text
Visitor, employee, parking, and operating-hour data affect demand scoring and charger right-sizing.
```

## Site-specific notes

### PWC001 — PWC McCoart Government Center

Main data needs:

```text
electrical service rating
spare capacity
emergency disconnect visibility
confirmed parking count
visitor/employee counts
likely charger placement
```

Suggested focus:

```text
Confirm whether the visitor/public parking area has practical electrical routing and enough public access to justify Level 2 chargers.
```

### PWC002 — Neabsco-Potomac Commuter Garage

Main data needs:

```text
garage fire/AHJ/access review
electrical routing constraints
ventilation or clearance concerns
emergency disconnect location
confirmed parking use/occupancy
```

Suggested focus:

```text
Treat this as a high-review candidate. Do not evaluate it like a simple surface-lot installation until garage-specific review is completed.
```

### PWC003 — Public Safety Training Center

Main data needs:

```text
public-access confirmation
fleet-only or special-use decision
electrical service rating
spare capacity
emergency disconnect visibility
```

Suggested focus:

```text
First confirm whether this should be a public charging site, a fleet/support site, or removed from the general-public candidate list.
```

### PWC004 — Chinn Park Regional Library

Main data needs:

```text
electrical service rating
spare capacity
emergency disconnect visibility
confirmed parking count
visitor/staff counts
likely charger placement
```

Suggested focus:

```text
Confirm whether the library/recreation parking context can support a straightforward public Level 2 installation.
```

### FFX001 — Fairfax City Hall or municipal building

Main data needs:

```text
electrical service rating
spare capacity
emergency disconnect visibility
confirmed parking count
visitor/employee counts
likely charger placement
```

Suggested focus:

```text
Confirm whether municipal visitor/staff parking has a practical charger location and electrical route.
```

### FFX002 — City of Fairfax Regional Library

Main data needs:

```text
electrical service rating
spare capacity
emergency disconnect visibility
confirmed parking count
visitor/staff counts
likely charger placement
```

Suggested focus:

```text
This is the current strongest candidate. Confirm site-level details needed to move from model screening to site screening.
```

## Suggested email template

Subject:

```text
EV Charging Site Screening Data Request
```

Body:

```text
Hello,

I am working on a planning-support prototype that evaluates candidate public EV charging sites in Fairfax City and Prince William County. The model compares sites using demand, electrical feasibility, safety/AHJ review, ADA/accessibility, equity, and right-sizing signals.

The model is not an engineering or permitting decision tool. I am trying to replace early V1 assumptions with better site-specific information.

Could you help confirm any of the following for the sites listed below?

1. Electrical service rating near the likely charger area
2. Available spare capacity or whether an upgrade would likely be needed
3. Nearest panel, transformer, switchgear, or service point
4. Likely trenching/conduit routing difficulty
5. Emergency disconnect location/visibility
6. Fire apparatus access or AHJ concerns
7. ADA-accessible route or accessible parking constraints
8. Typical visitor counts, employee counts, parking supply, and operating hours
9. Any existing EV charging, fleet electrification, construction, or parking plans

Candidate sites:
- [insert sites relevant to this contact]

Any estimates, documents, maps, or referrals to the correct staff contact would be very helpful.

Thank you,
Andy Yaro
Future City Fellowship Project
George Mason University
```

## How responses should update the model

When stakeholder answers come back:

```text
1. Update data/inputs/real_sites_v1.csv.
2. Add or update a supporting source extract in data/source_extracts/ if the answer is structured.
3. Update data/source_dataset_log.csv and data/dataset_metadata.csv if a new source is used.
4. Re-run the validator, model, and sensitivity script.
5. Compare the before/after ranking and recommendation tiers.
```

Run commands:

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/run_sensitivity_analysis.py
```

## Important caution

Stakeholder answers should be documented carefully. If a value is estimated, label it as an estimate. If it is confirmed from a facility drawing, utility review, or official staff response, label it as confirmed and record the source.
