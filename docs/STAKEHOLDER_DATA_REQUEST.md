# Stakeholder Data Request Pack

## Purpose

This document turns the model's remaining data gaps into clear stakeholder questions.

The goal is to help replace V1 assumptions and placeholders with confirmed site, facility, parking, utility, accessibility, AHJ, GIS, planning, or operations information.

The companion structured file is:

```text
data/source_extracts/stakeholder_data_request_fields.csv
```

That CSV should remain the detailed field-by-field checklist. This Markdown file is the human-readable meeting and follow-up guide.

## Sites covered

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Highest-priority confirmations

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
likely_charger_area
nearest_panel_or_transformer_location
trenching_or_conduit_difficulty
ada_accessible_route_confirmed
fire_access_confirmed
confirmed_public_charging_hours
confirmed_visitor_or_parking_use
```

## Site-specific focus

```text
PWC001 — confirm public visitor parking, likely charger area, electrical route, and site-use assumptions.
PWC002 — keep as high-review because it is a garage candidate; confirm garage-specific access, routing, ventilation, and AHJ constraints before advancement.
PWC003 — first decide whether it should be public, fleet-only, special-use, or removed from the public-candidate list.
PWC004 — first confirm renovation/closure status and realistic future planning timeline; keep as future/reopened until that caveat is resolved.
FFX001 — confirm municipal visitor/staff parking, likely charger area, and electrical route.
FFX002 — parking count and facility hours already have official facility-page support, but confirm likely charger placement, practical charging hours, electrical capacity, and site operations.
```

## Core stakeholder questions

```text
1. What is the electrical service rating at or near the likely charger area?
2. Is there spare capacity for Level 2 charging without a major upgrade?
3. Where is the nearest panel, transformer, switchgear, or service point?
4. Would conduit routing or trenching be simple, moderate, or difficult?
5. Where could a required disconnect or related safety equipment be placed so it is visible and accessible?
6. Are there accessibility, parking-layout, circulation, clearance, or review constraints near the likely charger area?
7. What are typical visitor counts, employee counts, parking supply, and operating hours?
8. Are there planned construction, parking, electrification, or facility projects that affect this site?
```

## How responses should update the model

When stakeholder answers come back:

```text
1. Update data/inputs/real_sites_v1.csv.
2. Add or update a supporting source extract in data/source_extracts/ if the answer is structured.
3. Update data/source_dataset_log.csv and data/dataset_metadata.csv if a new source is used.
4. Re-run the full model workflow.
5. Inspect the updated generated interpretation and baseline comparison.
6. Rebuild the deliverable package.
```

Run commands:

```bash
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

## Important caution

Stakeholder answers should be documented carefully. If a value is estimated, label it as an estimate. If it is confirmed from a facility drawing, utility review, official staff response, or official source, label it as confirmed and record the source.
