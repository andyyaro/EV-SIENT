# Project Status

## Current phase

Phase 2 prototype development for the Public EV Charging Site-Readiness and Right-Sizing Model.

The project is now a working planning-support prototype. It validates candidate-site data, runs the readiness and right-sizing model, tests sensitivity scenarios, compares alternative scoring profiles, generates charts and a readiness map, creates dynamic Markdown summaries, checks outputs against V1 expectations, compares the run to a committed baseline, and builds a local deliverable package.

This project is still a planning-support model only. It does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, construction approval, or stakeholder approval.

## Current repo structure

```text
src/                  Python scripts
data/inputs/           Input datasets
data/config/           Config files for scoring profiles and output-check rules
data/source_extracts/  Small source extracts and source notes
data/baselines/        Committed V1 baseline outputs for regression comparison
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
3. src/plot_readiness_score_chart.py
4. src/run_sensitivity_analysis.py
5. src/run_profile_analysis.py
6. src/plot_profile_score_heatmap.py
7. src/plot_site_map.py
8. src/generate_run_summary.py
9. src/generate_results_interpretation.py
10. src/check_outputs.py
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

The configurable output checker passed after moving V1 assumptions into:

```text
data/config/output_check_rules_v1.json
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
Right-sizing logic added for recommended ports now, 2035, and 2050.
Sensitivity analysis added and strengthened.
Scoring profile analysis added.
Readiness score chart polished with score and tier annotations.
Profile score heatmap added to compare readiness and rank across scoring-priority profiles.
Readiness map label offsets and planning notes improved.
Dynamic model run summary added.
Dynamic generated results interpretation added.
Baseline snapshot and baseline comparison added.
Configurable output-check rules added.
Workflow success marker added to prevent stale packaging after failed runs.
Deliverable package builder added and expanded.
Findings brief, full findings report, and presentation outline added.
Stakeholder data request pack added.
Repository reorganized into cleaner folders.
```

## Current strongest findings

```text
FFX002 is the strongest current candidate.
FFX002 ranks #1 in the base model, stays stable across sensitivity scenarios, and ranks #1 across all five scoring profiles.
FFX001 is the second strongest current candidate and remains a Tier 1 alternative.
PWC002 moved ahead of PWC004 after the corrected trenching normalization, but remains high-review because of garage, fire/AHJ, access, ventilation, conduit-routing, emergency-disconnect, and electrical-review concerns.
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

## Current generated outputs

Expected local outputs include:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
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
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/deliverable_package/
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
PWC002 garage/fire/AHJ/access/ventilation/conduit review
PWC003 public, fleet-only, special-use, or removal decision
```

## Current stakeholder request files

```text
docs/STAKEHOLDER_DATA_REQUEST.md
data/source_extracts/stakeholder_data_request_fields.csv
```

Use these files to ask facility, utility, public works, parking, ADA/accessibility, Fire Marshal/AHJ, GIS, and planning contacts for the data needed to replace assumptions and placeholders.

## Current config and quality-control files

```text
data/config/scoring_profiles.csv
data/config/output_check_rules_v1.json
data/baselines/v1_baseline/site_results.csv
data/baselines/v1_baseline/sensitivity_summary.csv
data/baselines/v1_baseline/data_quality_report.csv
data/baselines/v1_baseline/baseline_manifest.json
```

`data/config/scoring_profiles.csv` controls the alternative scoring-priority profiles.

`data/config/output_check_rules_v1.json` controls V1 sanity-check expectations, including expected site IDs, expected top site, sensitivity stability rule, data-quality error rule, expected profile names, expected profile count, expected sites per profile, and profile score range.

## Next good improvements

```text
1. Inspect the new profile score heatmap for readability.
2. Replace visitor, employee, parking, and electrical assumptions with stronger stakeholder-confirmed site data when available.
3. Improve facility hours and parking for sites other than FFX002.
4. Prepare final presentation slides from docs/PRESENTATION_OUTLINE.md and the deliverable package.
5. Add more candidate sites if the project scope expands.
```
