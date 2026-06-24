# Repository Map

This file explains the main parts of the repo without making you read every file.

## Start files

- [START_HERE.md](../START_HERE.md) — short reproduction guide
- [REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md) — step-by-step reproduction checklist
- [README.md](../README.md) — project overview

## Main folders

- [src/](../src/) — Python scripts
- [data/inputs/](../data/inputs/) — input datasets
- [data/config/](../data/config/) — scoring, checker, and output manifest configuration
- [data/outputs/](../data/outputs/) — generated local outputs
- [data/baselines/](../data/baselines/) — saved V1 benchmark outputs
- [docs/](../docs/) — project documentation

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
| [src/run_all.py](../src/run_all.py) | Runs the official V1 workflow. |
| [src/run_demo.py](../src/run_demo.py) | Runs a synthetic larger-site demo workflow. |
| [src/generate_demo_sites.py](../src/generate_demo_sites.py) | Creates synthetic demo candidate sites. |
| [src/validate_site_data.py](../src/validate_site_data.py) | Checks input data. |
| [src/ev_charger_model.py](../src/ev_charger_model.py) | Main readiness and right-sizing model. |
| [src/add_action_matrix.py](../src/add_action_matrix.py) | Adds next-action labels. |
| [src/check_outputs.py](../src/check_outputs.py) | Checks outputs and runs baseline comparison. |
| [src/build_deliverable_package.py](../src/build_deliverable_package.py) | Builds the shareable package. |
| [src/plot_scalable_readiness_charts.py](../src/plot_scalable_readiness_charts.py) | Creates scalable visuals for larger test runs. |
| [src/sync_visual_assets.py](../src/sync_visual_assets.py) | Copies generated PNG visuals into committed Markdown preview assets. |
| [src/project_config.py](../src/project_config.py) | Loads shared config files. |

## Main input and config files

| File | Purpose |
|---|---|
| [data/inputs/real_sites_v1.csv](../data/inputs/real_sites_v1.csv) | Main candidate-site dataset. |
| [data/inputs/new_sites_template.csv](../data/inputs/new_sites_template.csv) | Template for new candidate sites. |
| [data/config/output_manifest_v1.json](../data/config/output_manifest_v1.json) | Expected outputs and package contents. |
| [data/config/scoring_profiles.csv](../data/config/scoring_profiles.csv) | Scoring-priority profiles. |
| [data/config/output_check_rules_v1.json](../data/config/output_check_rules_v1.json) | Checker rules. |

## Main generated outputs

- [data/outputs/site_results.csv](../data/outputs/site_results.csv)
- [data/outputs/model_run_summary.md](../data/outputs/model_run_summary.md)
- [data/outputs/results_interpretation.md](../data/outputs/results_interpretation.md)
- [data/outputs/action_matrix.md](../data/outputs/action_matrix.md)
- [data/outputs/profile_comparison.md](../data/outputs/profile_comparison.md)
- [data/outputs/baseline_comparison.md](../data/outputs/baseline_comparison.md)
- [data/outputs/data_quality_report.csv](../data/outputs/data_quality_report.csv)

## Main charts

- [data/outputs/charts/readiness_score_chart.png](../data/outputs/charts/readiness_score_chart.png)
- [data/outputs/charts/data_confidence_chart.png](../data/outputs/charts/data_confidence_chart.png)
- [data/outputs/charts/profile_rank_stability_chart.png](../data/outputs/charts/profile_rank_stability_chart.png)
- [data/outputs/charts/site_readiness_map.png](../data/outputs/charts/site_readiness_map.png)
- [data/outputs/charts/profile_score_heatmap.png](../data/outputs/charts/profile_score_heatmap.png)

## Demo mode for larger tests

For a full 50-site synthetic test, use:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

See [DEMO_MODE_GUIDE.md](DEMO_MODE_GUIDE.md).

## Scalable visuals for larger tests

For 25, 50, or more candidate sites, use:

```bash
python src/plot_scalable_readiness_charts.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15
```

See [SCALABLE_VISUALS_GUIDE.md](SCALABLE_VISUALS_GUIDE.md).

## Recommended reading path

Quick review:

1. [START_HERE.md](../START_HERE.md)
2. [REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md)
3. [data/outputs/model_run_summary.md](../data/outputs/model_run_summary.md)
4. [data/outputs/action_matrix.md](../data/outputs/action_matrix.md)
5. [data/outputs/results_interpretation.md](../data/outputs/results_interpretation.md)

Deeper review:

1. [MODEL_FINDINGS_BRIEF.md](MODEL_FINDINGS_BRIEF.md)
2. [MODEL_FINDINGS_REPORT.md](MODEL_FINDINGS_REPORT.md)
3. [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
4. [DATA_SOURCES.md](DATA_SOURCES.md)
5. [METHODOLOGY.md](METHODOLOGY.md)

## What not to edit first

Do not edit generated outputs directly:

- [data/outputs/](../data/outputs/)
- [data/outputs/charts/](../data/outputs/charts/)
- [data/outputs/deliverable_package/](../data/outputs/deliverable_package/)
- [data/demo/](../data/demo/)

Regenerate official outputs with:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```

Generate demo outputs with:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```
