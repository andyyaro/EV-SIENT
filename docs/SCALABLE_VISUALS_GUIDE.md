# Scalable Visuals Guide

## Purpose

The default readiness chart works well for the official 6-site V1 model run.

When the model is tested with 25, 50, or more candidate sites, one full bar chart becomes crowded. The labels overlap and the chart becomes hard to read.

Use scalable visuals for larger test runs.

## Easiest path: run demo mode

For a complete 50-site synthetic workflow, run:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

This generates demo data, validates it, runs the model, adds action labels, and creates scalable visuals.

## Scalable visual script

```text
src/plot_scalable_readiness_charts.py
```

Use this script directly when you already have a model results CSV.

## Example for a 50-site demo result file

```bash
python src/plot_scalable_readiness_charts.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15
```

## Generated visuals

The script creates:

```text
readiness_top_15.png
readiness_score_distribution.png
recommendation_tier_counts.png
readiness_full_compact.png
scalable_readiness_visuals_summary.md
```

## How to use each visual

### Top-N readiness chart

Use this as the main presentation chart.

It shows only the strongest sites, so it stays readable even when the full dataset has 50 or more candidates.

### Readiness score distribution

Use this to understand the overall score spread.

It answers:

```text
Are most sites clustered in the middle?
Are only a few sites clearly strong?
Are there many low-priority sites?
```

### Recommendation tier counts

Use this to understand the planning funnel.

It answers:

```text
How many sites advance?
How many sites need technical review?
How many sites stay lower priority?
```

### Full compact readiness chart

Use this only as an appendix or audit chart.

It includes every site but intentionally uses compact labels. It is useful for checking the full ranking, not for presentation.

## Simple rule

```text
1–10 sites:
  normal readiness chart is fine

11–25 sites:
  top-N chart + compact full chart

26+ sites:
  top-N chart + distribution chart + tier-count chart
  full compact chart only as appendix
```

## Important note

These scalable visuals do not change the model.

They only make larger result sets easier to read.
