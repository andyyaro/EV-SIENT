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

`equity_gap_index` uses ACS 2024 5-Year indicators and TIGER geometry. The main model reads the precomputed value from the input CSV; the current repo does not ask users to run a separate custom equity-builder script.

## Decision 8 — Use planning estimates where confirmed data is unavailable

Demand, parking, electrical distance/cost, and local EV adoption values are clearly labeled when they are assumptions, planning estimates, or proxies.

## Decision 9 — Keep parking weight low until verified

Parking is included in demand scoring but kept at a low weight because several current parking values are still V1 assumptions.

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

The repo includes a model findings brief, a full model findings report, and a presentation outline for stakeholder communication.

## Decision 17 — Reorganize repository structure

The repo now uses a cleaner layout:

```text
src/                  Python scripts
data/inputs/           Main input datasets
data/config/           Model config and output-check rules
data/source_extracts/  Small model-ready extracts
data/baselines/        Committed benchmark snapshots
data/outputs/          Generated outputs ignored by Git
docs/                  Documentation and reporting
```

## Decision 18 — Add stakeholder data request pack

The repo now includes a stakeholder data request guide and structured request-field extract.

```text
docs/STAKEHOLDER_DATA_REQUEST.md
data/source_extracts/stakeholder_data_request_fields.csv
```

Reason: the strongest next improvement is replacing V1 assumptions and placeholders with confirmed site, facility, utility, parking, ADA/accessibility, Fire Marshal/AHJ, GIS, or planning data.

Source quality: planning data request. These files are not observed site data; they are a checklist for future data collection.

## Decision 19 — Apply official FFX002 hours and parking; document PWC004 closure status

The repo now includes:

```text
data/source_extracts/official_facility_hours_parking_v1.csv
```

Decision: update FFX002 `parking_spaces` from 160 to 199 and `hours_open` from 8.00 to 9.29 using the official Fairfax County Public Library branch page.

Decision: document that the official Prince William Public Libraries locations page currently lists Chinn Park Library as closed for renovation.

Scope decision: keep PWC004 in the model as a future/reopened planning candidate, not as a current operating-site recommendation. The closure remains documented as an important caveat.

Source quality: official facility webpage for FFX002 fields and official current-status webpage for PWC004.

## Decision 20 — Use reviewed OSM amenities counts

The project now uses reviewed OpenStreetMap / Overpass amenity counts for `amenities_count_0_5mi`.

```text
data/source_extracts/amenities_0_5mi_v4_osm_reviewed.csv
```

Decision: do not mix manual and OSM values in the active model field. Manual V1 amenity values are retained only for comparison and history.

Source quality: open POI/GIS support, not official local government confirmation.

## Decision 21 — Use committed baseline snapshots and one combined output check

The project now uses a small committed baseline snapshot instead of external storage for run comparison.

```text
data/baselines/v1_baseline/
src/check_outputs.py
src/create_baseline_snapshot.py
```

Decision: normal generated outputs remain ignored under `data/outputs/`, while selected benchmark snapshots under `data/baselines/` can be committed after review.

Decision: `src/check_outputs.py` is the single final output-check command. It runs sanity checks and then generates the baseline comparison report.

Reason: this keeps the project reproducible without cloud credentials, external links, storage cost, or extra authentication complexity.

## Decision 22 — Add scoring profile analysis

The project now includes configurable scoring profiles for testing different planning priorities.

```text
data/config/scoring_profiles.csv
src/run_profile_analysis.py
```

Decision: the main V1 ranking remains the primary ranking. Profile analysis is a planning-sensitivity layer that shows how rankings change when demand, equity, feasibility, or safety is weighted more heavily.

Reason: different stakeholders may care about different priorities, so the model should show whether recommendations are stable across reasonable policy perspectives.

## Decision 23 — Add local deliverable package builder

The project now includes a script that gathers key generated outputs and reporting documents into one local shareable folder.

```text
src/build_deliverable_package.py
data/outputs/deliverable_package/
```

Decision: the deliverable package is generated locally and ignored by Git.

Reason: the project needs an easy way to share maps, summaries, CSV tables, and reporting files without committing generated output artifacts to the repository.

## Decision 24 — Add generated results interpretation

The project now includes a generated plain-English interpretation built from the latest local outputs.

```text
src/generate_results_interpretation.py
data/outputs/results_interpretation.md
```

Decision: static docs remain useful for the project story, but the generated interpretation should be used when sharing the latest model run because it adapts to ranking, tier, sensitivity, profile, and review-trigger changes.

Reason: this reduces the risk that the deliverable package contains stale result sentences after future data or model updates.

## Decision 25 — Move V1 output-check rules into config

The project now stores output-check expectations in a config file instead of hard-coding all V1 assumptions directly inside the checker.

```text
data/config/output_check_rules_v1.json
src/check_outputs.py
```

Decision: the current V1 sanity-check rules include expected site IDs, expected top site, zero data-quality errors, zero sensitivity rank movement, expected profile names, expected profile count, expected sites per profile, and allowed profile score range.

Reason: this makes the checker easier to maintain if the project adds sites, changes the official top-site expectation, changes scoring profiles, or creates a future V2 benchmark.

## Decision 26 — Correct trenching normalization and guard against stale packages

The feasibility score uses `trenching_ft_n`, so `trenching_ft` must be part of the normalized input list in `src/ev_charger_model.py`.

```text
src/ev_charger_model.py
src/run_all.py
src/build_deliverable_package.py
data/outputs/workflow_success.json
```

Decision: restore `trenching_ft` normalization and treat the corrected run as the current model output. After the correction, PWC002 moves ahead of PWC004, but PWC002 remains a high-review garage candidate.

Decision: `src/run_all.py` writes `data/outputs/workflow_success.json` only after the full workflow passes. `src/build_deliverable_package.py` checks that marker before building the shareable package.

Reason: this prevents packaging stale local outputs after a failed or partial pipeline run.

## Decision 27 — Verify Markdown links in repo docs and the deliverable package

The project now treats Markdown link correctness as part of documentation quality.

Decision: keep the main README-style docs clickable and make the generated deliverable package README clickable.

Decision: when Markdown reports are copied into the local deliverable package, `src/build_deliverable_package.py` rewrites internal links so they resolve correctly from inside `data/outputs/deliverable_package/`.

Decision: if a copied package document links to a repo file that is not included in the package, the package builder rewrites that target as a GitHub repository link instead of leaving a broken local path.

Verified local audit result:

```text
Checked local Markdown links: 369
Skipped external/anchor links: 19
Broken local links: 0
All checked local Markdown links exist.
```

Verified package result:

```text
Copied files: 38
Missing files: 0
```

Reason: the project package is meant to be reviewed by other people, so links inside README files, copied reports, charts, config files, and package contents should work without requiring the reviewer to manually hunt through folders.

## Current expected recommendation interpretation

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC002 — High-review candidate because of garage context
PWC004 — Tier 2 / strongest current PWC public-library candidate under future/reopened planning assumptions
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
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
```

## Maintenance rule

Whenever the project changes a source, assumption, formula, output interpretation, or stakeholder-facing conclusion, update the relevant docs in `docs/`.
