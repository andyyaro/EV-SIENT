# Documentation

This folder contains the longer project documentation.

## Start files

```text
../START_HERE.md
../REPRODUCIBILITY_CHECKLIST.md
REPO_MAP.md
```

## Short reading path

```text
1. ../START_HERE.md
2. ../REPRODUCIBILITY_CHECKLIST.md
3. REPO_MAP.md
4. DATA_DICTIONARY.md
5. DATA_SOURCES.md
6. METHODOLOGY.md
7. PROJECT_STATUS.md
```

## Main generated outputs

For the latest model-run result, use:

```text
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/action_matrix.md
data/outputs/profile_comparison.md
data/outputs/baseline_comparison.md
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/site_readiness_map.png
```

## Main planning/reporting docs

```text
PROJECT_STATUS.md
MODEL_FINDINGS_BRIEF.md
MODEL_FINDINGS_REPORT.md
PRESENTATION_OUTLINE.md
RESULTS_INTERPRETATION.md
READINESS_MAP_GUIDE.md
DATA_CONFIDENCE_SCORE.md
RECOMMENDATION_TIERS.md
SENSITIVITY_ANALYSIS.md
SENSITIVITY_RESULTS_INTERPRETATION.md
```

## Expansion and stakeholder docs

```text
SITE_SCREENING_CHECKLIST.md
ADDING_NEW_SITES_GUIDE.md
STAKEHOLDER_DATA_REQUEST.md
STAKEHOLDER_CONTACT_PLAN.md
```

## Technical/source docs

```text
METHODOLOGY.md
DATA_DICTIONARY.md
DATA_SOURCES.md
OSM_AMENITIES_WORKFLOW.md
OSM_AMENITIES_REVIEW_NOTE.md
PROJECT_DECISIONS_LOG.md
```

## Main folders

```text
src/
data/inputs/
data/config/
data/outputs/
```

## Shareable local package

After running the full workflow, build the package with:

```bash
python src/build_deliverable_package.py
```

The package is created at:

```text
data/outputs/deliverable_package/
```
