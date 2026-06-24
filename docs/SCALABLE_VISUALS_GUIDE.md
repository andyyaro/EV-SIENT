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

This generates demo data, validates it, runs the model, adds action labels, runs scoring-profile analysis, and creates scalable visuals.

## Scalable visual script

```text
src/plot_scalable_readiness_charts.py
```

Use this script directly when you already have a model results CSV.

## Example for a 50-site demo result file

```bash
python src/plot_scalable_readiness_charts.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --input-sites data/demo/demo_sites_50.csv \
  --profile-results data/demo/outputs/demo_profile_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15
```

## Generated visuals

The script can create:

```text
readiness_top_15.png
readiness_map_top_15_labeled.png
profile_heatmap_top_15.png
profile_rank_stability_top_8.png
readiness_score_distribution.png
recommendation_tier_counts.png
data_confidence_full_compact.png
readiness_full_compact.png
scalable_readiness_visuals_summary.md
```

Some visuals require optional inputs:

```text
--input-sites enables the scalable readiness map
--profile-results enables the profile heatmap and rank-stability chart
```

## How to use each visual

### Top-N readiness chart

Use this as the main presentation ranking chart.

It shows only the strongest sites, so it stays readable even when the full dataset has 50 or more candidates.

### Multi-panel readiness map

Use this as the scalable geographic planning visual.

It uses an overview panel for all sites and separate zoom panels for the Fairfax and Prince William demo clusters. The overview labels only the top 5 sites, while the zoom panels label the strongest local sites.

### Top-N profile heatmap

Use this as the scalable version of the official profile heatmap.

It keeps only the top-N base-model sites and shows how their scores/ranks change across scoring-priority profiles.

### Top-8 profile rank stability chart

Use this as the scalable version of the official rank-stability visual.

The heatmap can stay at top-N, but the line chart gets crowded faster. The default rank-stability chart is therefore limited to the top 8 base-model sites, with the top 3 emphasized and the rest faded.

### Readiness score distribution

Use this to understand the overall score spread.

It now zooms to the observed score range instead of always using 0–100, so it avoids wasted empty chart space.

It answers:

```text
Are most sites clustered in the middle?
Are only a few sites clearly strong?
Are there many low-priority sites?
```

### Recommendation tier counts

Use this to understand the planning funnel.

It is horizontal for readability and includes an automatic interpretation sentence.

It answers:

```text
How many sites advance?
How many sites need technical review?
How many sites stay lower priority?
```

### Data confidence compact chart

Use this to review confidence across larger result sets.

It is an audit-style chart, not the main presentation chart.

### Full compact readiness chart

Use this only as an appendix or audit chart.

It includes every site but intentionally uses compact labels. It is useful for checking the full ranking, not for presentation.

## Simple rule

```text
1–10 sites:
  normal readiness chart is fine

11–25 sites:
  top-N chart + multi-panel map + compact full chart

26+ sites:
  top-N chart + multi-panel map + profile heatmap + top-8 rank-stability chart
  distribution chart + tier-count chart
  full compact charts only as appendix
```

## Important note

These scalable visuals do not change the model.

They only make larger result sets easier to read.
