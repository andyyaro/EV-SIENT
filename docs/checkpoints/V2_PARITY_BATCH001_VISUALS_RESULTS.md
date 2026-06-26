# V2 Parity Batch 001 — Visual Outputs Results

## Status

The V2 visual parity batch ran successfully.

The V2 workflow now includes the V1-style polished visual outputs, and `src/check_outputs_v2.py` passed after those outputs were generated.

## Confirmed workflow sections

The successful run included:

```text
3. Create V2 polished readiness score chart
4. Create V2 data confidence chart
8. Create V2 profile score heatmap
9. Create V2 profile rank stability chart
```

## Confirmed generated chart outputs

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
```

The V2 workflow also still generates:

```text
data/outputs/charts/v2_readiness_score_chart.png
data/outputs/charts/v2/*.png utilization charts
```

## Current V2 model status during this run

The main ranking remained stable:

```text
Rank 1  FFX002 — City of Fairfax Regional Library — 58.8
Rank 2  FFX004 — Fairfax County Government Center — 54.4
Rank 3  PWC006 — Bull Run Library — 52.1
Rank 4  FFX001 — Fairfax City Hall or municipal building — 51.0
Rank 5  PWC002 — Neabsco-Potomac Commuter Garage — 50.3
Rank 6  PWC007 — Central Library — 50.2
```

The profile analysis still shows that FFX002 is strongest overall, while FFX004 leads the demand-priority view:

```text
base: FFX002
demand_priority: FFX004
equity_priority: FFX002
feasibility_priority: FFX002
safety_priority: FFX002
```

## Output checker status

```text
V2 OUTPUT CHECK
Status: PASSED
```

## Remaining V1-to-V2 parity items

The next parity work should focus on:

```text
readiness map
Markdown run summary
V2 success marker / output manifest
V2 baseline comparison
optional deliverable package / demo-mode parity
```

## Recommended next step

The next best implementation step is the V2 readiness map, because V1 has a map output and V2 does not yet call that map in the V2 workflow.

The existing map script should be checked carefully because the V2 candidate set has 12 sites rather than the smaller original site set.
