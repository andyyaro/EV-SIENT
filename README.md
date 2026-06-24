# EV Charger Site-Readiness and Right-Sizing Prototype

![Model Pipeline Check](https://github.com/andyyaro/Future-City-Fellowship-/actions/workflows/model-check.yml/badge.svg)

This repository contains a Python planning-support prototype for comparing public EV charging candidate sites in Fairfax City and Prince William County.

The model evaluates sites using demand, implementation feasibility, site review, equity, data confidence, and charger right-sizing signals. It supports early planning only; it is not a construction, procurement, or approval tool.

## Start here

For the shortest reproduction guide, open:

```text
START_HERE.md
```

For a stricter step-by-step reproduction checklist, open:

```text
REPRODUCIBILITY_CHECKLIST.md
```

For a simple map of the repo, open:

```text
docs/REPO_MAP.md
```

## Quick run

From the repository root:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```

A successful run should show:

```text
Sanity check: PASSED
Baseline comparison: COMPLETED
Missing files: 0
```

## Main outputs to review

```text
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/action_matrix.md
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/site_readiness_map.png
```

## Main input and output files

```text
data/inputs/real_sites_v1.csv      Main candidate-site input dataset
data/outputs/site_results.csv      Main model result table
data/outputs/deliverable_package/  Shareable local package
```

## Main workflow scripts

```text
src/run_all.py                    Run the full workflow
src/ev_charger_model.py           Main scoring and right-sizing model
src/add_action_matrix.py          Adds next-action labels
src/check_outputs.py              Checks generated outputs
src/build_deliverable_package.py  Builds the shareable package
```

See `docs/REPO_MAP.md` for the full script and file map.

## Core result fields

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is

action_label = what to do next
```

## Current planning interpretation

```text
FFX002 — stable top candidate
FFX001 — stable second candidate
PWC002 — high-review garage candidate
PWC004 — promising with future/reopened timeline caveat
PWC001 — lower-priority monitor candidate
PWC003 — special-use / not general-public priority under current assumptions
```

## Documentation

```text
START_HERE.md
REPRODUCIBILITY_CHECKLIST.md
docs/REPO_MAP.md
docs/DATA_DICTIONARY.md
docs/DATA_SOURCES.md
docs/METHODOLOGY.md
docs/PROJECT_STATUS.md
```

The longer documentation and presentation files remain in `docs/`.

## Important limitation

The prototype is useful for transparent early planning, but any real project decision must be checked with the appropriate site owner, technical reviewers, permitting offices, and procurement process.
