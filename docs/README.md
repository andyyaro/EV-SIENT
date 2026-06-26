# Documentation

This folder contains the longer project documentation.

Use this page as a quick index. For the cleanest reviewer-facing path, start with:

- [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md) — current active documentation index
- [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) — reviewer-friendly path through the repo
- [../START_HERE.md](../START_HERE.md) — shortest project entry point
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md) — active V2 workflow guide
- [REPO_MAP.md](REPO_MAP.md) — repository structure and script map
- [../src/README.md](../src/README.md) — script-by-script source index
- [../REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md) — local reproduction checklist
- [MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md) — checks before pushing or sharing
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — current project state

## Recommended reading paths

### New reviewer

1. [../README.md](../README.md)
2. [ACTIVE_DOCS_INDEX.md](ACTIVE_DOCS_INDEX.md)
3. [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md)
4. [../START_HERE.md](../START_HERE.md)
5. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
6. [REPO_MAP.md](REPO_MAP.md)
7. [../src/README.md](../src/README.md)
8. [DATA_DICTIONARY.md](DATA_DICTIONARY.md)

### Reproducing the model

1. [../START_HERE.md](../START_HERE.md)
2. [../REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md)
3. [MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md)
4. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
5. [REPO_MAP.md](REPO_MAP.md)

Run the active V2 workflow with:

```bash
make setup
make run-v2
make check-v2
make links
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
```

### Understanding the technical method

1. [METHODOLOGY.md](METHODOLOGY.md)
2. [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
3. [DATA_SOURCES.md](DATA_SOURCES.md)
4. [V2_ELECTRICAL_RISK_SCENARIO_METHOD.md](V2_ELECTRICAL_RISK_SCENARIO_METHOD.md)
5. [V2_RIGHT_SIZING_SCENARIO_METHOD.md](V2_RIGHT_SIZING_SCENARIO_METHOD.md)
6. [checkpoints/V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md](checkpoints/V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md)

## Active V2 generated outputs

After a successful V2 run, open the clean package first:

```text
../data/outputs/deliverable_package_v2/README.md
../data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
../data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
../data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
../data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
../data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
```

Important direct V2 outputs:

```text
../data/outputs/v2_executive_site_summary.csv
../data/outputs/v2_port_sizing_scenario_summary.csv
../data/outputs/v2_baseline_comparison.md
../data/outputs/v2_workflow_success.json
```

## Main planning and reporting docs

- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
- [MODEL_FINDINGS_BRIEF.md](MODEL_FINDINGS_BRIEF.md)
- [MODEL_FINDINGS_REPORT.md](MODEL_FINDINGS_REPORT.md)
- [PRESENTATION_OUTLINE.md](PRESENTATION_OUTLINE.md)
- [RESULTS_INTERPRETATION.md](RESULTS_INTERPRETATION.md)
- [READINESS_MAP_GUIDE.md](READINESS_MAP_GUIDE.md)
- [DATA_CONFIDENCE_SCORE.md](DATA_CONFIDENCE_SCORE.md)
- [RECOMMENDATION_TIERS.md](RECOMMENDATION_TIERS.md)
- [SENSITIVITY_ANALYSIS.md](SENSITIVITY_ANALYSIS.md)

## Expansion and stakeholder docs

- [SITE_SCREENING_CHECKLIST.md](SITE_SCREENING_CHECKLIST.md)
- [ADDING_NEW_SITES_GUIDE.md](ADDING_NEW_SITES_GUIDE.md)
- [STAKEHOLDER_OUTREACH_PLAN.md](STAKEHOLDER_OUTREACH_PLAN.md)
- [SITE_EXPANSION_AND_OUTREACH_TRIAGE.md](SITE_EXPANSION_AND_OUTREACH_TRIAGE.md)
- [V2_PUBLIC_DATA_UPGRADE_WORKFLOW.md](V2_PUBLIC_DATA_UPGRADE_WORKFLOW.md)
- [V2_NEXT_BATCH_PLAN.md](V2_NEXT_BATCH_PLAN.md)
- [V2_BACKLOG_TRIAGE_CHECKLIST.md](V2_BACKLOG_TRIAGE_CHECKLIST.md)

## Technical and source docs

- [METHODOLOGY.md](METHODOLOGY.md)
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- [DATA_SOURCES.md](DATA_SOURCES.md)
- [OSM_AMENITIES.md](OSM_AMENITIES.md)
- [PROJECT_DECISIONS_LOG.md](PROJECT_DECISIONS_LOG.md)
- [CHART_STYLE_GUIDE.md](CHART_STYLE_GUIDE.md)

## Checkpoint and history docs

Use [checkpoints/README.md](checkpoints/README.md) for implementation history and milestone notes.

Checkpoint docs preserve project memory and auditability, but new reviewers should start with the active docs above.

## Main folders

- [../src/](../src/) — Python scripts
- [../data/inputs/](../data/inputs/) — active input files
- [../data/config/](../data/config/) — config and check rules
- [../data/source_extracts/](../data/source_extracts/) — source extracts and notes
- [checkpoints/](checkpoints/) — checkpoint and history notes
- `../data/outputs/` — generated local outputs ignored by Git

## Shareable local package

The active V2 workflow builds the package automatically through:

```bash
make run-v2
```

The V2 package is created at:

```text
../data/outputs/deliverable_package_v2/
```

A healthy V2 package reports:

```text
Copied files: 35/35
Synced files: 35/35
```

The stable V1 package can still be rebuilt on `main` with:

```bash
python src/build_deliverable_package.py
```
