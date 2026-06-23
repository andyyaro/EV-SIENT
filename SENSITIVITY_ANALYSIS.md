# Sensitivity Analysis

## Purpose

The prototype includes several values that are still assumptions, planning estimates, or proxies. Sensitivity analysis helps show whether the site ranking is stable when those uncertain values change.

This is important because the model should not pretend that V1 assumptions are exact.

## Script

Run:

```bash
python run_sensitivity_analysis.py
```

Outputs:

```text
sensitivity_results.csv
sensitivity_summary.csv
```

## Scenarios

The current script tests five scenarios.

### 1. very_low_demand_high_cost

Purpose: strong downside test.

```text
employees_day = 50% of base
visitors_day = 50% of base
ev_share_local = 60% of base
service_upgrade_cost_usd = 160% of base
trenching_ft = 140% of base
```

### 2. low_demand_high_cost

Purpose: moderate downside test.

```text
employees_day = 75% of base
visitors_day = 75% of base
ev_share_local = 80% of base
service_upgrade_cost_usd = 125% of base
trenching_ft = 115% of base
```

### 3. base_case

Purpose: current V1 dataset.

```text
all values = current real_sites_v1.csv values
```

### 4. high_demand_base_cost

Purpose: moderate upside demand test.

```text
employees_day = 125% of base
visitors_day = 125% of base
ev_share_local = 125% of base
service_upgrade_cost_usd = base
trenching_ft = base
```

### 5. very_high_demand_low_cost

Purpose: strong upside test.

```text
employees_day = 175% of base
visitors_day = 175% of base
ev_share_local = 160% of base
service_upgrade_cost_usd = 80% of base
trenching_ft = 85% of base
```

## How to read sensitivity_summary.csv

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
Small rank_range = ranking is stable under tested assumptions
Large rank_range = ranking depends heavily on uncertain assumptions
High average_readiness_score = site performs well across scenarios
Low average_readiness_score = site remains weak across scenarios
```

## Why this matters

The current model still needs better support for:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open
parking_spaces
amenities_count_0_5mi
local EV adoption counts
```

Sensitivity analysis helps keep the prototype honest while those inputs are improved.

## Current limitation

This is a simple scenario analysis, not a full Monte Carlo simulation. It changes a few major uncertain inputs using fixed multipliers. Later, the project can add random sampling or distributions if needed.
