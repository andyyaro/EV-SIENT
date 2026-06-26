# Reviewer Guide

This guide is for someone who wants to inspect, reproduce, or review the active V2 prototype without reading the entire repository first.

## What to know first

The active technical branch is:

```text
v2-expansion-planning
```

The stable V1 baseline lives on `main`, but the current Phase 2 prototype work is on `v2-expansion-planning`.

The prototype is a planning-support tool. It does not replace engineering review, utility review, Fire Marshal or AHJ review, ADA review, stormwater review, procurement, or stakeholder confirmation.

## Fast review path

Read these in order:

1. [../README.md](../README.md) — project overview and preview visuals.
2. [../START_HERE.md](../START_HERE.md) — shortest explanation and run path.
3. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md) — active workflow guide.
4. [REPO_MAP.md](REPO_MAP.md) — repository structure and script map.
5. [../src/README.md](../src/README.md) — script-by-script index.
6. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — important input and output fields.
7. [PROJECT_STATUS.md](PROJECT_STATUS.md) — current project state.

After running the workflow, review the generated package first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

## Reproduce the active V2 workflow

From the repository root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make setup
make run-v2
make check-v2
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
```

A healthy run should report:

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

## Check links

Preferred command:

```bash
make links
```

Equivalent raw command:

```bash
lychee --verbose --no-progress \
  --accept 200,204,206,301,302,303,307,308 \
  --include-fragments \
  --exclude-path data/outputs \
  --exclude-path data/run_history \
  './**/*.md'
```

A clean link audit should end with zero errors.

## Main files to inspect

| Area | File |
|---|---|
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
data/outputs/charts/
data/outputs/deliverable_package/
data/outputs/deliverable_package_v2/
data/demo/
```

Do not move scripts until imports, workflows, docs, and reproducibility commands are updated together.

## Current interpretation to verify

The current V2 interpretation is:

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 is useful but high-review.
PWC003 should remain special-use unless its use case changes.
```

The port-sizing scenario layer currently indicates:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

## Reviewer checklist

Before trusting a result, confirm:

```text
make check-v2 passes
make links passes
README preview images render
baseline comparison does not show unexpected failures
candidate-site count remains 12 unless intentionally changed
all major V2 outputs are present
clean deliverable package is hash-synced
```
