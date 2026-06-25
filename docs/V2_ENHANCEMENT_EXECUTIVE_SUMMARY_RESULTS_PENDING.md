# V2 Enhancement — Executive Site Summary Pending Validation

## Status

The V2 executive site summary enhancement has been implemented and is ready for local validation.

## Added or updated

```text
src/build_v2_executive_summary.py
src/run_v2.py
src/check_outputs_v2.py
docs/V2_ENHANCEMENT_EXECUTIVE_SUMMARY_CHECKPOINT.md
```

## New generated outputs

```text
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
```

## New V2 workflow step

```text
13. Build V2 executive site summary
```

The step runs after right-sizing and before the interpretation report.

## Purpose

The executive summary gives one clean decision table that combines:

```text
ranking
readiness score
data confidence
recommendation tier
action label
electrical risk
expected electrical rank/score
ports now
2035 and 2050 right-sizing values
future-ready capacity
expansion strategy
major review flags
planning recommendation
data needed next
```

## Validation needed

Run:

```bash
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

The checker should pass after confirming:

```text
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
```
