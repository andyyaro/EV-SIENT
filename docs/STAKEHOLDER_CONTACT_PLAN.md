# Stakeholder Contact Plan

## Purpose

This plan turns the model's remaining data gaps into a simple outreach workflow.

The goal is to replace V1 assumptions with documented answers where possible.

Companion tracker:

```text
data/source_extracts/stakeholder_response_tracker.csv
```

Companion question checklist:

```text
data/source_extracts/stakeholder_data_request_fields.csv
```

## Best order of outreach

```text
1. FFX002 — confirm the top candidate first.
2. FFX001 — confirm the Tier 1 backup candidate.
3. PWC002 — clarify garage-specific constraints.
4. PWC004 — clarify future/reopened planning timeline.
5. PWC003 — decide whether it is public, fleet/special-use, or removed from the public list.
6. PWC001 — confirm whether assumptions should be upgraded or kept as lower priority.
```

## Contact groups to identify

```text
facility or site manager
parking or operations contact
public works or sustainability contact
library or municipal operations contact
technical reviewer for electrical/site questions
GIS or planning data contact
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

## How responses should update the model

```text
1. Update stakeholder_response_tracker.csv.
2. If a model field changes, update data/inputs/real_sites_v1.csv.
3. Add a note in the input row explaining the source.
4. Re-run python src/run_all.py.
5. Review data/outputs/results_interpretation.md.
6. Rebuild the package with python src/build_deliverable_package.py.
```

## Highest-priority fields

```text
likely_charger_area
elec_service_rating_amp
spare_capacity_kw
distance_to_service_ft
trenching_ft
emergency_disconnect_visible
ada_layout_possible
parking_spaces
visitors_day
employees_day
hours_open
public_access
```

## Simple rule

Do not overwrite a V1 assumption unless the new value has a source, date, and confidence level recorded in the tracker.
