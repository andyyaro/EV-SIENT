# Reviewer Guide

This guide is for someone who wants to inspect, reproduce, or review the active V2 prototype without reading the entire repository first.

## What to know first

The active technical branch is:

```text
v2-expansion-planning
```

The stable V1 baseline lives on `main`, but the current Phase 2 prototype work is on `v2-expansion-planning`.

The prototype is a planning-support tool. It does not replace technical, utility, accessibility, permitting, procurement, or stakeholder review.

## Public visual artifact

The main public-facing visual artifact is the Tableau workbook:

[Open the EV Charging Site Readiness Workbook](https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite)

Tableau Public opens the workbook through one starting worksheet URL. Use the visible sheet tabs to navigate the full workbook.

Local Tableau files:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
tableau/README.md
src/build_tableau_exports.py
```

Static PNG charts are still generated for reproducibility, GitHub previews, and the technical deliverable package, but Tableau is the primary public visual layer.

## Fast review path

Read these in order:

1. [../README.md](../README.md) — project overview, Tableau link, and preview visuals.
2. [../START_HERE.md](../START_HERE.md) — shortest explanation and run path.
3. [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md) — clean index of active reviewer-facing docs.
4. [../tableau/README.md](../tableau/README.md) — Tableau workbook link and refresh notes.
5. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md) — active workflow guide.
6. [REPO_MAP.md](REPO_MAP.md) — repository structure and script map.
7. [../src/README.md](../src/README.md) — script-by-script index.
8. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — important input and output fields.
9. [PROJECT_STATUS.md](PROJECT_STATUS.md) — current project state.

## Reproduce the active V2 workflow

From the repository root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make setup
make run-v2
make check-v2
make tableau-exports
```

Equivalent all-in review command:

```bash
make review
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
```

A healthy V2 check should report:

```text
Status: PASSED
Copied files: 35/35
Synced files: 35/35
```

The workflow marker tracks one additional detailed sensitivity output, so the marker and package counts are intentionally different:

```text
workflow marker: 36 generated outputs
clean deliverable package: 35 selected review files
```

## Technical package review

After running the workflow, review the generated package for reproducibility:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

## Main files to inspect

| Area | File |
|---|---|
| Public interactive workbook | `tableau/EV_Charging_Site_Readiness_Workbook.twbx` |
| Tableau documentation | `tableau/README.md` |
| Tableau CSV export builder | `src/build_tableau_exports.py` |
| Active workflow runner | `src/run_v2.py` |
| Output checker | `src/check_outputs_v2.py` |
| Main model | `src/ev_charger_model.py` |
| Executive summary builder | `src/build_v2_executive_summary.py` |
| Port-use simulation | `src/run_port_utilization_simulation.py` |
| Port-sizing scenario analysis | `src/run_port_sizing_scenario_analysis.py` |
| Right-sizing validation | `src/validate_right_sizing_with_simulation.py` |
| Deliverable package builder | `src/build_v2_deliverable_package.py` |
| Active input dataset | `data/inputs/real_sites_v2.csv` |
| Scenario assumptions | `data/inputs/v2_port_sizing_scenarios.csv` |
| Baseline snapshot | `data/baselines/v2_baseline_snapshot.json` |

## What not to edit directly

Do not manually edit generated outputs. Regenerate them instead.

```text
data/outputs/
data/outputs/tableau/
data/outputs/charts/
data/outputs/deliverable_package/
data/outputs/deliverable_package_v2/
data/demo/
```

Do not move scripts until imports, workflows, docs, Tableau refresh instructions, and reproducibility commands are updated together.

## Current interpretation to verify

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 is useful but high-review.
PWC003 should remain special-use unless its use case changes.
```

Port-sizing scenario layer:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

## Reviewer checklist

```text
make check-v2 passes
make tableau-exports runs after current V2 outputs exist
make links passes
Tableau Public tabs are visible
README preview images render
baseline comparison does not show unexpected failures
candidate-site count remains 12 unless intentionally changed
all major V2 outputs are present
clean deliverable package is hash-synced
```
