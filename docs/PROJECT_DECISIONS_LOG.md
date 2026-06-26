# Project Decisions Log

This log keeps the major project decisions in one place.

## Current active workflow decision

The active Phase 2 workflow is V2 on `v2-expansion-planning`.

```text
Runner: src/run_v2.py
Checker: src/check_outputs_v2.py
Candidate sites: 12
Workflow steps: 24
Deliverable package payload: 35 files
```

Decision: preserve `main` as the stable V1 workflow and use `v2-expansion-planning` for active V2 prototype work.

## Current expected recommendation interpretation

```text
FFX002 — strongest current candidate
FFX004 — second-ranked Tier 1 candidate
PWC006 — strongest current Prince William County library candidate
PWC002 — useful high-review garage candidate
PWC007 — credible Tier 2 Prince William candidate
PWC008 — lower priority under base scoring, but sensitive under combined port-sizing stress
PWC003 — special-use / low-priority unless the use case changes
```

## Current port-sizing scenario interpretation

Decision: keep the port-sizing scenario analysis as a separate stress-test layer, similar in purpose to scoring-profile analysis.

```text
Scoring-profile analysis = stress-tests site ranking under different scoring priorities
Port-sizing scenario analysis = stress-tests port recommendations under different charging and demand assumptions
```

Current scenario result:

```text
base: no future-ready capacity gaps
high_growth: no future-ready capacity gaps
long_sessions: no future-ready capacity gaps
short_daily_window: no future-ready capacity gaps
peakier_demand: no future-ready capacity gaps
combined_stress: 2 future-ready capacity gaps
```

Combined-stress gaps:

```text
PWC002 — future-ready capacity 3, scenario minimum 4, gap 1
PWC008 — future-ready capacity 2, scenario minimum 3, gap 1
```

## Current unresolved items

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open where still estimated
parking_spaces where still estimated
local EV adoption counts
PWC002 garage-specific review
PWC003 use-case decision
```

## Major historical decisions retained

```text
Use real candidate sites.
Keep large raw exports out of the repository.
Use official or official-derived location data where possible.
Use AFDC/NREL extracts for existing charging supply.
Use VDOT traffic data.
Use ACS and LODES-derived households/jobs signals.
Use an ACS-derived equity index.
Use planning estimates where confirmed data is unavailable.
Keep parking weight low until verified.
Discount limited access.
Keep garage sites high-review.
Add right-sizing logic.
Add sensitivity analysis.
Add recommendation tiers.
Add reporting layers.
Reorganize repository structure.
Add stakeholder outreach tracking.
Use reviewed OSM amenities counts.
Use committed baseline snapshots.
Add scoring-profile analysis.
Add local deliverable package builders.
Add generated results interpretation.
Move V1 output-check rules into config.
Correct trenching normalization.
Verify Markdown links.
Enforce input schema and template consistency.
Merge overlapping documentation.
Add scalable demo mode.
Add V2 electrical-risk scenarios.
Add V2 right-sizing scenarios.
Add V2 port-use simulation.
Add V2 right-sizing validation.
Add V2 executive summary.
Add V2 GIS decision maps.
Add V2 deliverable-package hash sync.
Add V2 port-sizing scenario analysis.
```

## Current V2 package decision

The V2 deliverable package is generated locally and ignored by Git.

```text
data/outputs/deliverable_package_v2/
```

The current package contains 35 source payload files plus a package README and package manifest.

## Current V2 baseline decision

The V2 baseline snapshot is a committed guardrail file.

```text
data/baselines/v2_baseline_snapshot.json
```

It checks site count, rankings, data-quality counts, profile top sites, electrical expected-case outputs, right-sizing outputs, port-use simulation, port-sizing scenarios, right-sizing validation, executive summary fields, and package-manifest sync.

## Maintenance rule

Whenever the project changes a source, assumption, formula, output interpretation, workflow, demo feature, or stakeholder-facing conclusion, update the relevant docs in `docs/`, `data/`, and the repository root.
