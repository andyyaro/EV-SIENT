# Sensitivity Analysis

Sensitivity analysis tests whether rankings are stable when uncertain assumptions change.

## Run command

```bash
python src/run_sensitivity_analysis.py
```

## Outputs

```text
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
```

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

## Current limitation

This is a scenario test, not a full Monte Carlo simulation. It changes a few major uncertain inputs using fixed multipliers.
