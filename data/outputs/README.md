# Generated Outputs

This folder is for files created when the scripts run locally.

Generated outputs are ignored by Git so local runs do not clutter `git status`.

## Main generated CSV, Markdown, and metadata outputs

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/action_matrix.md
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
```

`site_results.csv` includes readiness, confidence, and action-matrix fields.

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is

action_label = what to do next
```

`workflow_success.json` is written only after `src/run_all.py` completes successfully. The deliverable package builder uses it to avoid packaging stale outputs after a failed or partial run.

## Generated chart outputs

```text
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
```

Recommended profile visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

The heatmap is kept as a supporting view, but the rank-stability chart is easier to explain in a presentation.

## Optional OSM amenities outputs

```text
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
```

## Deliverable package

The package builder creates a local shareable folder:

```text
data/outputs/deliverable_package/
```

It includes selected charts, run outputs, data tables, reports, a package README, and a package manifest.

## Regenerate outputs

From the repository root:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```

`src/run_all.py` runs the validator, model, action matrix, readiness chart, data confidence chart, sensitivity analysis, scoring profile analysis, profile visuals, readiness map, generated summaries, output checks, and baseline comparison.
