# Repository Map

This file explains what each important part of the repo does.

Use this when you want to understand the project without reading every file.

## Short version

```text
START_HERE.md                    Short reproduction guide
REPRODUCIBILITY_CHECKLIST.md     Step-by-step reproduction checklist
README.md                        Project overview
src/                             Python scripts
data/inputs/                     Input datasets
data/outputs/                    Generated local outputs
data/config/                     Scoring and checker configuration
docs/                            Project documentation
data/baselines/                  Saved V1 benchmark outputs
```

## Main workflow

Run everything with:

```bash
python src/run_all.py
```

Then build the package with:

```bash
python src/build_deliverable_package.py
```

## Main scripts

| File | Purpose |
|---|---|
| `src/run_all.py` | Runs the full workflow in the correct order. |
| `src/validate_site_data.py` | Checks the input data for blocking errors and review items. |
| `src/ev_charger_model.py` | Main readiness scoring and right-sizing model. |
| `src/add_action_matrix.py` | Adds simple next-action labels from readiness and data confidence. |
| `src/plot_readiness_score_chart.py` | Creates the readiness score chart. |
| `src/plot_data_confidence_chart.py` | Creates the data confidence chart. |
| `src/run_sensitivity_analysis.py` | Tests whether rankings change under simple scenario changes. |
| `src/run_profile_analysis.py` | Tests different scoring-priority profiles. |
| `src/plot_profile_rank_stability.py` | Creates the main profile-analysis chart. |
| `src/plot_profile_score_heatmap.py` | Creates a supporting profile-analysis heatmap. |
| `src/plot_site_map.py` | Creates the candidate site map. |
| `src/generate_run_summary.py` | Creates the generated model summary. |
| `src/generate_results_interpretation.py` | Creates the generated plain-English interpretation. |
| `src/check_outputs.py` | Checks expected outputs and runs baseline comparison. |
| `src/build_deliverable_package.py` | Copies key files into a shareable deliverable package. |
| `src/build_osm_amenities.py` | Optional helper for OpenStreetMap amenity data. |

## Main input files

| File | Purpose |
|---|---|
| `data/inputs/real_sites_v1.csv` | Main candidate-site input dataset. |
| `data/inputs/sites_demo.csv` | Smaller starter/demo dataset. |
| `data/inputs/new_sites_template.csv` | Template for adding future candidate sites. |
| `data/config/scoring_profiles.csv` | Alternative scoring-priority profiles. |
| `data/config/output_check_rules_v1.json` | Expected output rules for the checker. |

## Main generated outputs

| File | Purpose |
|---|---|
| `data/outputs/site_results.csv` | Main result table. |
| `data/outputs/model_run_summary.md` | Short generated run summary. |
| `data/outputs/results_interpretation.md` | Plain-English generated interpretation. |
| `data/outputs/action_matrix.md` | Readiness-confidence next-action report. |
| `data/outputs/profile_comparison.md` | Scoring-profile comparison report. |
| `data/outputs/baseline_comparison.md` | Comparison against the saved baseline. |
| `data/outputs/data_quality_report.csv` | Data-quality findings. |
| `data/outputs/workflow_success.json` | Marker created only after the full workflow passes. |

## Main charts

| File | Purpose |
|---|---|
| `data/outputs/charts/readiness_score_chart.png` | Main ranking chart. |
| `data/outputs/charts/data_confidence_chart.png` | Shows how complete the current inputs are. |
| `data/outputs/charts/profile_rank_stability_chart.png` | Shows whether rankings change across scoring profiles. |
| `data/outputs/charts/site_readiness_map.png` | Shows candidate locations and readiness context. |
| `data/outputs/charts/profile_score_heatmap.png` | Supporting profile score visual. |

## Most important concepts

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is

action_label = what to do next
```

## Recommended reading path

For a quick review:

```text
START_HERE.md
REPRODUCIBILITY_CHECKLIST.md
data/outputs/model_run_summary.md
data/outputs/action_matrix.md
data/outputs/results_interpretation.md
```

For a deeper review:

```text
docs/MODEL_FINDINGS_BRIEF.md
docs/MODEL_FINDINGS_REPORT.md
docs/DATA_DICTIONARY.md
docs/DATA_SOURCES.md
docs/METHODOLOGY.md
```

## What not to edit first

Do not edit generated files directly:

```text
data/outputs/
data/outputs/charts/
data/outputs/deliverable_package/
```

Regenerate them with:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```
