# Project Decisions Log

This log keeps the major project decisions in one place.

## Decision 1 — Use real candidate sites

`data/inputs/real_sites_v1.csv` is the default input dataset.

## Decision 2 — Keep large raw exports out of the repo

The repo stores small model-ready extracts and documentation instead of every large raw file.

## Decision 3 — Use official or official-derived location data

Candidate addresses and coordinates are based on official GIS or facility sources where available.

## Decision 4 — Use AFDC/NREL for existing EV charging supply

Existing nearby public active Level 2 and DC fast charging supply is counted from AFDC/NREL extracts.

## Decision 5 — Use VDOT traffic data

Traffic exposure uses the nearest VDOT Bidirectional Traffic Volume 2025 segment.

## Decision 6 — Use ACS and LODES for households/jobs

Nearby households and jobs are official-derived from ACS/TIGER and LODES/TIGER methods.

## Decision 7 — Use ACS-derived equity index

`equity_gap_index` uses ACS 2024 5-Year indicators and TIGER geometry.

## Decision 8 — Use planning estimates where confirmed data is unavailable

Demand, parking, amenities, electrical distance/cost, and local EV adoption values are clearly labeled when they are assumptions, planning estimates, or proxies.

## Decision 9 — Keep parking weight low until verified

Parking is included in demand scoring but kept at a low weight because current parking values are V1 assumptions.

## Decision 10 — Use benchmark scaling for local EV share

`ev_share_local` is scaled against a fixed 10 percent benchmark instead of min-max scaling.

## Decision 11 — Discount limited public access

Limited or non-public sites stay in the dataset but receive public-access discounts.

## Decision 12 — Keep garage sites high-review

Garage sites can have strong public value but require extra fire/AHJ, access, ventilation, conduit-routing, and electrical review.

## Decision 13 — Add right-sizing logic

The model recommends starter ports for now, 2035, and 2050 using expected sessions, dwell time, open hours, utilization, and mean wait.

## Decision 14 — Add sensitivity analysis

The model tests five low/base/high uncertainty scenarios. The latest result showed stable ranking across all five scenarios.

## Decision 15 — Add recommendation tiers

The model now outputs planning tiers, recommendations, priority reasons, and next data needs.

## Decision 16 — Add reporting layer

The repo includes a model findings brief and presentation outline for stakeholder communication.

## Decision 17 — Reorganize repository structure

The repo now uses a cleaner layout:

```text
src/                  Python scripts
data/inputs/           Main input datasets
data/source_extracts/  Small model-ready extracts
data/outputs/          Generated outputs ignored by Git
docs/                  Documentation and reporting
```

## Current expected recommendation interpretation

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC004 — Tier 2 / strongest current PWC public-library candidate
PWC002 — High-review candidate because of garage context
PWC001 — Tier 3 / lower priority under current assumptions
PWC003 — Low public-priority / special-use because public access is limited
```

## Current unresolved items

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

## Maintenance rule

Whenever the project changes a source, assumption, formula, output interpretation, or stakeholder-facing conclusion, update the relevant docs in `docs/`.
