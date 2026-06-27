# Stakeholder Outreach Plan

## Purpose

This document turns the model's remaining data gaps into a simple outreach workflow and clear stakeholder questions.

The goal is to replace early V2 assumptions and placeholders with confirmed or clearly estimated site, facility, parking, utility, accessibility, review, GIS, planning, or operations information.

Companion files:

```text
data/source_extracts/stakeholder_data_request_fields.csv
data/source_extracts/stakeholder_response_tracker.csv
```

`stakeholder_data_request_fields.csv` is the detailed field-by-field checklist.

`stakeholder_response_tracker.csv` is where outreach status, answers, source dates, confidence levels, and model-update decisions should be recorded.

## Sites covered

```text
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
FFX003 — Pohick Regional Library
FFX004 — Fairfax County Government Center
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
PWC005 — Haymarket Gainesville Library
PWC006 — Bull Run Library
PWC007 — Central Library
PWC008 — Potomac Library
```

## Best order of outreach

Start with the sites where better data would most improve planning decisions:

```text
1. FFX002 — confirm the strongest current public candidate first.
2. FFX004 — confirm the second-ranked Tier 1 candidate.
3. PWC006 — confirm the strongest current Prince William County library candidate.
4. PWC002 — clarify garage-specific constraints.
5. PWC007 and PWC004 — refine promising Prince William library assumptions.
6. FFX001 and FFX003 — refine Fairfax-area Tier 2 assumptions.
7. PWC008, PWC001, and PWC005 — confirm whether these should stay monitor/small-pilot candidates.
8. PWC003 — decide whether it is public, fleet/special-use, or removed from the public list.
```

## Contact groups to identify

```text
facility or site manager
parking or operations contact
public works or sustainability contact
library or municipal operations contact
technical reviewer for electrical/site questions
safety or authority-review contact where applicable
accessibility reviewer
GIS or planning data contact
```

## Highest-priority confirmations

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
likely_charger_area
nearest_panel_or_transformer_location
trenching_or_conduit_difficulty
accessible_route_confirmed
site_access_confirmed
confirmed_public_charging_hours
confirmed_visitor_or_parking_use
public_access
PWC002 garage-specific review
PWC003 public vs fleet/special-use decision
```

## Site-specific focus

```text
FFX002 — confirm likely charger placement, practical charging hours, electrical capacity, accessibility route, and site operations.
FFX004 — confirm public parking, likely charger placement, electrical route, and civic-site operations.
PWC006 — confirm library parking, likely charger placement, electrical route, and public charging hours.
PWC002 — keep as high-review; confirm garage-specific access, routing, ventilation, and review constraints before advancement.
PWC003 — first decide whether it should be public, fleet-only, special-use, or removed from the public-candidate list.
PWC004 and PWC007 — confirm parking, practical charging hours, likely charger placement, and electrical route.
PWC008 and PWC005 — confirm whether monitor/small-pilot status still makes sense after better site data.
PWC001 — confirm whether assumptions should be upgraded or kept as lower priority.
```

## First email structure

```text
Subject: EV charging site-readiness data request for [site name]

Hello [Name],

I am working on a planning-support prototype that compares public EV charging candidate sites in Fairfax City and Prince William County.

I am trying to replace early assumptions with better site information. Could you help confirm a few planning details for [site name]?

The main questions are:
1. Where would EV chargers most likely be placed at this site?
2. What are the realistic public charging hours?
3. How many parking spaces are available near the likely charger area?
4. Are typical visitor or employee counts available?
5. Is there known electrical capacity near the likely charger area?
6. Are there any site constraints that should be considered before this location advances?

Even approximate answers are helpful if they are clearly labeled as estimates.

Thank you,
Andy Yaro
Future City Fellowship
George Mason University
```

## Core stakeholder questions

```text
1. What is the electrical service rating at or near the likely charger area?
2. Is there spare capacity for Level 2 charging without a major upgrade?
3. Where is the nearest panel, transformer, switchgear, or service point?
4. Would conduit routing or trenching be simple, moderate, or difficult?
5. Where could required visible site equipment be placed?
6. Are there accessibility, parking-layout, circulation, clearance, or review constraints near the likely charger area?
7. What are typical visitor counts, employee counts, parking supply, and operating hours?
8. Are there planned construction, parking, electrification, or facility projects that affect this site?
```

## How to record responses

For every response, update:

```text
data/source_extracts/stakeholder_response_tracker.csv
```

Use these fields carefully:

```text
response_status
response_summary
response_source
response_date
confidence_level
model_update_needed
next_action
notes
```

Recommended status values:

```text
Not started
Contact identified
Request sent
Response received
Needs follow-up
Confirmed
Unable to confirm
Not applicable
```

Recommended confidence values:

```text
Low
Medium
High
Unknown
```

## Minimum evidence before changing the model

Do not overwrite a V2 assumption unless the answer has enough traceability.

Minimum information to record:

```text
who or what source provided the answer
response date or source date
whether the value is confirmed or estimated
confidence level
which model field should change
whether the current input notes need to change
```

## How responses should update the model

When stakeholder answers come back:

```text
1. Update data/source_extracts/stakeholder_response_tracker.csv.
2. Update data/inputs/real_sites_v2.csv if a model field changes.
3. Add a note in the input row explaining the source.
4. Add or update a supporting source extract in data/source_extracts/ if the answer is structured.
5. Update data/source_dataset_log.csv and data/dataset_metadata.csv if a new source is used.
6. Run make full-v2-tableau.
7. Inspect data/outputs/v2_executive_site_summary.csv, data/outputs/tableau/, and data/outputs/deliverable_package_v2/README.md.
8. Refresh the Tableau workbook only if the public visual artifact intentionally changes.
```

Run commands:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make full-v2-tableau
git status --short
```

## Simple rule

Do not overwrite a V2 assumption unless the new value has a source, date, and confidence level recorded in the tracker.

If a value is estimated, label it as an estimate. If it is confirmed from a staff response, facility drawing, official page, or other source, label it as confirmed and record the source.
