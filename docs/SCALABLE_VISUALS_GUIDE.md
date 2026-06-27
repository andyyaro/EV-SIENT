# Scalable Visuals Guide

## Purpose

This guide explains optional static-visual scripts for large synthetic demo runs or future larger candidate pools.

The active public-facing V2 visual artifact is Tableau:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
tableau/README.md
```

The scalable PNG scripts are support tools. They do not replace the Tableau workbook for the current 12-site public-facing artifact.

## When to use this guide

Use scalable visuals when:

```text
- testing demo mode with 25, 50, or more synthetic candidate sites,
- checking whether static charts remain readable for a larger future site pool,
- creating appendix or audit visuals for a large generated output,
- stress-testing visual readability outside the current Tableau workbook.
```

For the current official 12-site V2 workflow, use:

```bash
make full-v2-tableau
```

## Easiest path: run demo mode

For a complete 50-site synthetic workflow, run:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

This generates demo data, validates it, runs the model, adds action labels, runs scoring-profile analysis, and creates scalable support visuals.

## Scalable visual scripts

```text
src/plot_scalable_readiness_charts.py
src/plot_scalable_data_confidence_chart.py
```

Use these scripts directly when you already have a large model results CSV.

## Example for a 50-site demo result file

```bash
python src/plot_scalable_readiness_charts.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --input-sites data/demo/demo_sites_50.csv \
  --profile-results data/demo/outputs/demo_profile_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15

python src/plot_scalable_data_confidence_chart.py \
  --results data/demo/outputs/demo_site_results_50.csv \
  --output-dir data/demo/outputs/charts/scalable \
  --top-n 15
```

## Generated visuals

The scripts can create:

```text
readiness_top_15.png
data_confidence_top_15.png
readiness_map_top_15_labeled.png
profile_heatmap_top_15.png
profile_rank_stability_top_8.png
readiness_score_distribution.png
recommendation_tier_counts.png
data_confidence_full_compact.png
readiness_full_compact.png
scalable_readiness_visuals_summary.md
```

## Simple rule

```text
1–12 official V2 sites:
  use the Tableau workbook as the public visual layer
  use generated PNGs as technical support outputs

13–25 future or demo sites:
  use top-N readiness chart + top-N confidence chart + multi-panel map + compact full chart

26+ future or demo sites:
  use top-N readiness chart + top-N confidence chart + multi-panel map
  use profile heatmap + top-8 rank-stability chart
  use distribution chart + tier-count chart
  keep full compact charts as appendix only
```

## Important note

These scalable visuals do not change the model.

They only make larger result sets easier to read.
