# V2 Enhancement — Executive Site Summary Checkpoint

## Purpose

This checkpoint records the first post-parity V2 enhancement after the core V1-to-V2 feature parity work was completed.

The goal was to create one consolidated decision table that joins the most useful V2 outputs into a single report-ready file.

## Added or updated

```text
src/build_v2_executive_summary.py
src/run_v2.py
src/check_outputs_v2.py
```

## New generated outputs

```text
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
```

## What the executive summary joins

The executive summary combines fields from:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_right_sizing_scenarios.csv
```

## Main columns

```text
model_rank
site_id
site_name
readiness_score
data_confidence_level
recommendation_tier
action_label
electrical_risk_level
expected_electrical_rank
expected_electrical_score
ports_now
ports_2035_base
ports_2035_high
ports_2050_base
ports_2050_high
future_ready_capacity
expansion_strategy
major_review_flags
planning_recommendation
data_needed_next
```

## V2 workflow change

`src/run_v2.py` now includes:

```text
13. Build V2 executive site summary
```

The step calls:

```text
src/build_v2_executive_summary.py
```

with V2 paths:

```text
--results data/outputs/v2_site_results.csv
--electrical-summary data/outputs/v2_electrical_risk_summary.csv
--right-sizing data/outputs/v2_right_sizing_scenarios.csv
--output data/outputs/v2_executive_site_summary.csv
--report data/outputs/v2_executive_site_summary.md
```

## V2 checker change

`src/check_outputs_v2.py` now requires:

```text
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
```

It also checks that the executive CSV has the required reporting columns and enough site rows.

## Why this matters

Before this enhancement, the key decision information was spread across multiple files:

```text
site ranking
confidence
action matrix
electrical-risk scenarios
right-sizing scenarios
review flags
```

The executive summary gives one file that can be used for reports, screenshots, presentation tables, or quick decision review.

## Validation needed

Run:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

The workflow should include:

```text
13. Build V2 executive site summary
```

and the checker should pass.
