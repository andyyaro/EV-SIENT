# Demo Mode Guide

## Purpose

Demo mode lets you test the model with a larger synthetic dataset, such as 25, 50, or 100 candidate sites.

It is useful for checking:

```text
model scalability
ranking behavior
chart readability
recommendation-tier distribution
data-confidence behavior
workflow robustness
```

Demo mode is separate from the official V1 workflow.

```text
Official V1 workflow: src/run_all.py
Demo stress-test workflow: src/run_demo.py
```

## Important rule

Demo data is synthetic.

Do not treat demo results as real candidate-site recommendations.

## Quick 50-site run

From the repository root:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

This creates local demo files under:

```text
data/demo/
```

That folder is ignored by Git on purpose.

## Main demo outputs

For a 50-site run, the main files are:

```text
data/demo/demo_sites_50.csv
data/demo/outputs/demo_site_results_50.csv
data/demo/outputs/demo_action_matrix_50.md
data/demo/outputs/demo_run_summary_50.md
data/demo/outputs/charts/scalable/readiness_top_15.png
data/demo/outputs/charts/scalable/readiness_score_distribution.png
data/demo/outputs/charts/scalable/recommendation_tier_counts.png
data/demo/outputs/charts/scalable/readiness_full_compact.png
```

## What to open first

Open these in this order:

```text
1. data/demo/outputs/demo_run_summary_50.md
2. data/demo/outputs/charts/scalable/readiness_top_15.png
3. data/demo/outputs/charts/scalable/readiness_score_distribution.png
4. data/demo/outputs/charts/scalable/recommendation_tier_counts.png
5. data/demo/outputs/charts/scalable/readiness_full_compact.png
```

## Why scalable visuals are needed

A normal horizontal bar chart works for the official 6-site project.

It does not work well for 50 sites because labels overlap and the chart becomes unreadable.

Demo mode therefore generates scalable visuals:

```text
Top-N chart = presentation view
Distribution chart = score spread view
Tier-count chart = planning-funnel view
Full compact chart = audit appendix view
```

## Custom examples

### 25-site test

```bash
python src/run_demo.py --count 25 --seed 42 --top-n 12 --clean
```

### 100-site test

```bash
python src/run_demo.py --count 100 --seed 42 --top-n 20 --clean
```

### Skip the full compact chart

Use this if the full appendix chart is too large:

```bash
python src/run_demo.py --count 100 --seed 42 --top-n 20 --clean --skip-full-compact
```

## Manual workflow

The end-to-end demo runner wraps these steps:

```bash
python src/generate_demo_sites.py --count 50 --seed 42 --output data/demo/demo_sites_50.csv

python src/validate_site_data.py \
  --input data/demo/demo_sites_50.csv \
  --output data/demo/outputs/demo_data_quality_report_50.csv

python src/ev_charger_model.py \
  --input data/demo/demo_sites_50.csv \
  --output data/demo/outputs/demo_site_results_50.csv \
  --chart data/demo/outputs/charts/basic_readiness_score_chart_50.png \
  --utilization-chart-dir data/demo/outputs/utilization

python src/add_action_matrix.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --report data/demo/outputs/demo_action_matrix_50.md

python src/plot_scalable_readiness_charts.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15
```

## Cleaning demo outputs

```bash
rm -rf data/demo
```

## What not to do

Do not replace `data/inputs/real_sites_v1.csv` with demo data.

Do not run `src/run_all.py` expecting it to validate demo results. The official workflow is intentionally tied to the official V1 dataset and baseline checks.

Do not commit files under `data/demo/`.
