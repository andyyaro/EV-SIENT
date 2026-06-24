# Project Status

## Current phase

Phase 2 prototype development for the Public EV Charging Site-Readiness and Right-Sizing Model.

The project is now a working planning-support prototype. It validates candidate-site data, runs the readiness and right-sizing model, adds a readiness-confidence action matrix, tests sensitivity scenarios, compares alternative scoring profiles, generates charts and a readiness map, creates dynamic Markdown summaries, checks outputs against V1 expectations, compares the run to a committed baseline, and builds a local deliverable package.

This project is a planning-support model only. It does not replace required technical, permitting, procurement, or stakeholder review.

## Current repo structure

```text
src/                  Python scripts
data/inputs/           Input datasets
data/config/           Config files for scoring profiles, output checks, and output/package manifest
data/source_extracts/  Small source extracts and source notes
data/baselines/        Committed V1 baseline outputs for comparison
data/outputs/          Generated outputs ignored by Git
docs/                  Documentation and reporting
```

## Current full workflow

Run from the repository root:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```

`src/run_all.py` currently runs:

```text
1. src/validate_site_data.py
2. src/ev_charger_model.py
3. src/add_action_matrix.py
4. src/plot_readiness_score_chart.py
5. src/plot_data_confidence_chart.py
6. src/run_sensitivity_analysis.py
7. src/run_profile_analysis.py
8. src/plot_profile_score_heatmap.py
9. src/plot_profile_rank_stability.py
10. src/plot_site_map.py
11. src/generate_run_summary.py
12. src/generate_results_interpretation.py
13. src/check_outputs.py
```

The package builder creates a shareable local folder at:

```text
data/outputs/deliverable_package/
```

Generated outputs are local and ignored by Git.

## Latest confirmed successful run

Latest confirmed user rerun: 2026-06-23.

```text
Data-quality result: ERROR 0, WARNING 0, REVIEW 20, INFO 6
Output check: PASSED
Baseline comparison: COMPLETED
Workflow success marker: OK
Deliverable package: PASSED with 0 missing files
```

Latest confirmed documentation/package link audit:

```text
Checked local Markdown links: 369
Skipped external/anchor links: 19
Broken local links: 0
Copied files: 38
Missing files: 0
```

## V1 reviewer-ready checkpoint

Status: V1 reviewer-ready package prepared.

Local shareable ZIP:

```text
data/outputs/deliverable_package_clean.zip
```

The clean ZIP is generated locally and ignored by Git. It should be recreated from the latest successful workflow before sharing.

Current reviewer package result:

```text
Workflow status: passed
Copied files: 38
Missing files: 0
Broken local package links: 0
No __MACOSX or .DS_Store files in the clean ZIP
```

Current main result:

```text
FFX002 — City of Fairfax Regional Library is the strongest current candidate.
```

Main caution:

```text
A high readiness score does not mean a site is build-ready.
The model is for planning support only and still requires stakeholder, utility, engineering, ADA/accessibility, Fire Marshal/AHJ, permitting, procurement, and site review.
```

Main unresolved items before any advancement:

```text
electrical service rating
spare electrical capacity
emergency disconnect visibility
likely charger placement
employees_day and visitors_day
parking and charging hours except where already officially supported
PWC002 garage-specific review
PWC004 reopening or usable-planning timeline
PWC003 public, fleet-only, special-use, or removal decision
```

Next phase:

```text
Stakeholder confirmation and selected site screening, starting with FFX002, then FFX001, then PWC002.
```

## Baseline decision

The committed V1 baseline will stay as-is for now. The corrected current run should be compared against the existing baseline instead of replacing it.

## Completed so far

```text
Real candidate sites added.
Official and official-derived coordinates added.
Existing nearby charger supply added from AFDC/NREL.
VDOT AADT traffic signal added.
ACS households and equity index added.
LODES jobs signal added.
Demand assumptions added and documented.
Official FFX002 facility hours and parking added.
Official PWC004 current renovation status documented.
PWC004 future/reopened planning assumption confirmed.
Reviewed OSM/Overpass amenities count added and applied.
Planning electrical feasibility estimates added.
Local EV adoption proxy added.
Recommendation tier layer added.
Data confidence score added.
Readiness-confidence action matrix added.
Right-sizing logic added for recommended ports now, 2035, and 2050.
Sensitivity analysis added and strengthened.
Scoring profile analysis added.
Readiness score chart polished with score and tier annotations.
Data confidence chart added.
Profile rank-stability chart added as the main profile-analysis visual.
Profile score heatmap kept as a supporting visual.
Readiness map label offsets and planning notes improved.
Dynamic model run summary added.
Dynamic generated results interpretation added.
Baseline snapshot and baseline comparison added.
Configurable output-check rules added.
Output manifest added as the shared source for expected outputs and package contents.
Workflow success marker added to prevent stale packaging after failed runs.
Deliverable package builder added and expanded.
Deliverable package Markdown links now rewrite correctly when docs are copied.
Findings brief, full findings report, and presentation outline added.
Stakeholder outreach plan added.
Repository reorganized into cleaner folders.
Overlapping OSM, sensitivity, and stakeholder docs merged into cleaner consolidated docs.
```

## Current strongest findings

```text
FFX002 is the strongest current candidate.
FFX002 ranks #1 in the base model, stays stable across sensitivity scenarios, and ranks #1 across all five scoring profiles.
FFX001 is the second strongest current candidate and remains a Tier 1 alternative.
PWC002 moved ahead of PWC004 after the corrected trenching normalization, but remains a high-review garage candidate.
PWC004 remains a promising Tier 2 library candidate only under the future/reopened planning assumption because of the renovation/closure caveat.
PWC001 remains a lower-priority monitored candidate under the current V1 dataset.
PWC003 should not be treated as a general-public priority unless public access or use-case assumptions change.
```

## Latest confirmed ranking

```text
1. FFX002 — City of Fairfax Regional Library — 65.3 — Tier 1
2. FFX001 — Fairfax City Hall or municipal building — 57.3 — Tier 1
3. PWC002 — Neabsco-Potomac Commuter Garage — 56.0 — High-review candidate
4. PWC004 — Chinn Park Regional Library — 52.7 — Tier 2
5. PWC001 — PWC McCoart Government Center — 43.2 — Tier 3
6. PWC003 — Prince William County Public Safety Training Center — 29.5 — Low public-priority / special-use
```

## Current action-matrix interpretation

```text
FFX002 — Verify key data, then advance
FFX001 — Promising, but fix data first
PWC002 — Technical review before advancement
PWC004 — Promising with timeline caveat
PWC001 — Monitor or deprioritize
PWC003 — Special-use decision needed
```

## Current generated outputs

Expected local outputs include:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/action_matrix.md
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/profile_results.csv
data/outputs/profile_rank_summary.csv
data/outputs/profile_comparison.md
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/baseline_comparison.csv
data/outputs/baseline_comparison.md
data/outputs/workflow_success.json
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/deliverable_package/
```

Recommended profile-analysis visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

Use `data/outputs/results_interpretation.md` for the latest generated plain-English interpretation of the current run.

## Remaining data improvements

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
PWC004 reopening or usable-planning timeline
PWC002 garage-specific review
PWC003 public, fleet-only, special-use, or removal decision
```

## Current stakeholder request files

```text
docs/STAKEHOLDER_OUTREACH_PLAN.md
data/source_extracts/stakeholder_data_request_fields.csv
data/source_extracts/stakeholder_response_tracker.csv
```

Use these files to ask contacts for the data needed to replace assumptions and placeholders.
