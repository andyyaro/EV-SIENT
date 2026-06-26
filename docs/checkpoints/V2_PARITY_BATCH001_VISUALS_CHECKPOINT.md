# V2 Parity Batch 001 — Visual Outputs Checkpoint

## Purpose

This checkpoint records the first V1-to-V2 feature parity implementation batch.

The goal was not to add a brand-new model feature. The goal was to mirror V1 visual-output features inside the V2 workflow, using V2-specific input and output paths.

## Added to V2 workflow

The V2 workflow now calls the existing chart scripts with V2 paths:

```text
src/plot_readiness_score_chart.py
src/plot_data_confidence_chart.py
src/plot_profile_score_heatmap.py
src/plot_profile_rank_stability.py
```

## New V2 chart outputs

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
```

These are separate from the existing model-generated V2 readiness chart:

```text
data/outputs/charts/v2_readiness_score_chart.png
```

## Checker update

`src/check_outputs_v2.py` now checks that these V2 parity chart outputs exist and are not empty.

## Heatmap correction

The profile score heatmap footer was made dynamic. This matters because V2 can have different top sites under different scoring profiles.

For example, the base profile can rank one site first while the demand-priority profile ranks another site first. The chart should explain that tradeoff instead of hardcoding a single stable top-site message.

## Parity status after this batch

Mirrored in V2 after this batch:

```text
polished readiness score chart
data confidence chart
profile score heatmap
profile rank stability chart
```

Still remaining from the V1 parity audit:

```text
readiness map
Markdown run summary
V2 success marker / output manifest
V2 baseline comparison
optional deliverable package / demo-mode parity
```

## Next recommended parity batch

The next parity batch should focus on the V2 readiness map. The map script already exists, but it was originally designed around the first smaller site set. The V2 version should be checked carefully because the V2 candidate set now has 12 sites.
