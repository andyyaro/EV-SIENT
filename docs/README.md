# Documentation

This folder contains the longer project documentation.

## Start files

- [../START_HERE.md](../START_HERE.md)
- [../REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md)
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
- [V2_STABLE_WORKFLOW_CHECKPOINT.md](V2_STABLE_WORKFLOW_CHECKPOINT.md)
- [V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md](V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md)
- [REPO_MAP.md](REPO_MAP.md)

## Short reading path

1. [../START_HERE.md](../START_HERE.md)
2. [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
3. [../REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md)
4. [REPO_MAP.md](REPO_MAP.md)
5. [PROJECT_STATUS.md](PROJECT_STATUS.md)
6. [V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md](V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md)
7. [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
8. [DATA_SOURCES.md](DATA_SOURCES.md)
9. [METHODOLOGY.md](METHODOLOGY.md)

## Active V2 generated outputs

For the latest V2 run, use the local deliverable package after running:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
```

Open first:

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

## Main planning/reporting docs

- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)
- [V2_STABLE_WORKFLOW_CHECKPOINT.md](V2_STABLE_WORKFLOW_CHECKPOINT.md)
- [V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md](V2_PORT_SIZING_SCENARIO_ANALYSIS_CHECKPOINT.md)
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

## Technical/source docs

- [METHODOLOGY.md](METHODOLOGY.md)
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- [DATA_SOURCES.md](DATA_SOURCES.md)
- [OSM_AMENITIES.md](OSM_AMENITIES.md)
- [PROJECT_DECISIONS_LOG.md](PROJECT_DECISIONS_LOG.md)

## Main folders

- [src/](../src/)
- [data/inputs/](../data/inputs/)
- [data/config/](../data/config/)
- [data/outputs/](../data/outputs/)

## Shareable local package

The active V2 workflow builds the package automatically through:

```bash
python src/run_v2.py
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
