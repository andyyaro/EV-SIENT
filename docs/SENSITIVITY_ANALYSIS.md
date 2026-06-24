# Sensitivity Analysis

Sensitivity analysis tests whether rankings are stable when uncertain assumptions change.

This file now combines the method note and the latest results interpretation.

## Run command

```bash
python src/run_sensitivity_analysis.py
```

The full workflow also runs this step through:

```bash
python src/run_all.py
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

## Latest interpretation

The latest confirmed run tested five scenarios.

Main finding:

```text
Every site had rank_range = 0.
```

That means the ranking remained stable across the tested V1 uncertainty scenarios.

Stable ranking across scenarios:

```text
1. FFX002 — City of Fairfax Regional Library
2. FFX001 — Fairfax City Hall or municipal building
3. PWC002 — Neabsco-Potomac Commuter Garage
4. PWC004 — Chinn Park Regional Library
5. PWC001 — PWC McCoart Government Center
6. PWC003 — Prince William County Public Safety Training Center
```

## Planning conclusion

The current ranking is stable under the tested V1 uncertainty scenarios.

This does not prove the ranking is final. It only means the ranking stayed stable under the five tested scenarios.

Planning interpretation:

```text
FFX002 and FFX001 are stable Tier 1 candidates.
PWC002 remains in the discussion because of its commuter and equity role, but it needs deeper garage, fire/AHJ, electrical, access, and parking-operator review before advancement.
PWC004 remains promising only under the future/reopened planning assumption.
PWC003 should not be treated as a general-public charging site unless its access or use case changes.
```

## Current limitation

This is a scenario test, not a full Monte Carlo simulation. It changes a few major uncertain inputs using fixed multipliers.
