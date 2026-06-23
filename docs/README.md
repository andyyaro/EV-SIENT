# Documentation

This folder is for human-readable project documentation, reporting, and presentation material.

## Recommended reading order

```text
1. PROJECT_STATUS.md
2. MODEL_FINDINGS_BRIEF.md
3. MODEL_FINDINGS_REPORT.md
4. PRESENTATION_OUTLINE.md
5. RESULTS_INTERPRETATION.md
6. READINESS_MAP_GUIDE.md
7. STAKEHOLDER_DATA_REQUEST.md
8. METHODOLOGY.md
9. DATA_DICTIONARY.md
10. DATA_SOURCES.md
11. RECOMMENDATION_TIERS.md
12. SENSITIVITY_ANALYSIS.md
13. SENSITIVITY_RESULTS_INTERPRETATION.md
14. OSM_AMENITIES_WORKFLOW.md
15. OSM_AMENITIES_REVIEW_NOTE.md
16. PROJECT_DECISIONS_LOG.md
```

## Latest generated outputs

The static docs explain the project story and methodology. For the latest model-run result, use the generated files under `data/outputs/`:

```text
data/outputs/results_interpretation.md
data/outputs/model_run_summary.md
data/outputs/profile_comparison.md
data/outputs/baseline_comparison.md
data/outputs/charts/site_readiness_map.png
```

Generated outputs are local files ignored by Git.

## Main code

```text
src/
```

## Main input data

```text
data/inputs/
```

## Main config files

```text
data/config/scoring_profiles.csv
data/config/output_check_rules_v1.json
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
