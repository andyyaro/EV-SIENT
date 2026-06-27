# Sensitivity Analysis

Sensitivity analysis tests whether rankings are stable when uncertain assumptions change.

This file summarizes the method and current V2 interpretation.

## Run command

For the active V2 workflow, run sensitivity analysis through the full workflow:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

or:

```bash
make full-v2
```

The standalone script is:

```bash
python src/run_sensitivity_analysis.py --input data/inputs/real_sites_v2.csv --results-output data/outputs/v2_sensitivity_results.csv --summary-output data/outputs/v2_sensitivity_summary.csv
```

## Outputs

```text
data/outputs/v2_sensitivity_results.csv
data/outputs/v2_sensitivity_summary.csv
```

## Public visual layer

The main public-facing visual layer is the Tableau workbook documented in:

```text
tableau/README.md
```

Static sensitivity/profile charts remain technical support outputs.

## Current scenarios

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

## Scenario multipliers

The scenario configuration is documented in:

```text
data/source_extracts/sensitivity_scenarios_v1.csv
```

Main adjusted fields:

```text
employees_day
visitors_day
ev_share_local
service_upgrade_cost_usd
trenching_ft
```

## How to read the summary

Important columns:

```text
best_rank
worst_rank
average_rank
min_readiness_score
max_readiness_score
rank_range
readiness_score_range
```

Interpretation:

```text
Small rank_range = stable ranking under tested assumptions
Large rank_range = ranking depends heavily on uncertain assumptions
High average_readiness_score = site performs well across scenarios
Low average_readiness_score = site remains weak across scenarios
```

## Current V2 interpretation

The active V2 workflow uses 12 candidate sites. The latest high-level planning interpretation remains:

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 remains useful but high-review.
PWC003 should not be treated as a general-public priority unless its use case changes.
```

## Relation to scoring-profile and port-sizing scenario analysis

Sensitivity analysis is only one stability layer.

```text
Sensitivity analysis = changes demand and cost assumptions.
Scoring-profile analysis = changes planning priority weights.
Port-sizing scenario analysis = changes charging-duration, charging-window, peak-demand, and future-demand assumptions.
```

The current port-sizing scenario result is:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

## Current limitation

This is a scenario test, not a full Monte Carlo simulation. It changes a few major uncertain inputs using fixed multipliers.
