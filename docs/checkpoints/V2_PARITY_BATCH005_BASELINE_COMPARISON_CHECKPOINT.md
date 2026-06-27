# V2 Parity Batch 005 — Baseline Comparison Checkpoint

## Purpose

This checkpoint records the fifth V1-to-V2 feature parity implementation batch.

The goal was to add a V2 baseline comparison so the prototype can detect accidental changes to rankings, readiness scores, recommended ports, electrical-risk scenario results, and right-sizing scenario results.

## Added or updated

```text
data/baselines/v2_baseline_snapshot.json
src/compare_v2_to_baseline.py
src/run_v2.py
src/check_outputs_v2.py
```

## New committed baseline snapshot

```text
data/baselines/v2_baseline_snapshot.json
```

This snapshot captures the stable V2 results after the visual, map, run-summary, and workflow-manifest parity batches.

## New generated comparison outputs

```text
data/outputs/v2_baseline_comparison.json
data/outputs/v2_baseline_comparison.md
```

## What the baseline comparison checks

The comparison checks:

```text
site count
site ranking
readiness scores within tolerance
recommendation tiers
model recommended ports
quality counts
profile top sites
electrical expected-case ranks and risk levels
right-sizing ports and expansion strategies
```

## V2 workflow change

`src/run_v2.py` now includes:

```text
16. Compare V2 outputs to baseline
```

The step calls:

```text
src/compare_v2_to_baseline.py
```

with V2 paths:

```text
--baseline data/baselines/v2_baseline_snapshot.json
--results data/outputs/v2_site_results.csv
--quality data/outputs/v2_data_quality_report.csv
--profile-results data/outputs/v2_profile_results.csv
--electrical-summary data/outputs/v2_electrical_risk_summary.csv
--right-sizing data/outputs/v2_right_sizing_scenarios.csv
--json-output data/outputs/v2_baseline_comparison.json
--md-output data/outputs/v2_baseline_comparison.md
```

## V2 checker change

`src/check_outputs_v2.py` now requires:

```text
data/outputs/v2_baseline_comparison.json
data/outputs/v2_baseline_comparison.md
```

It also checks that the JSON comparison status is:

```text
pass
```

and that no comparison checks failed.

## Why this matters

This makes the V2 prototype more professional and reproducible. If a future code or data change accidentally changes the site rankings, readiness scores, port recommendations, or scenario outputs, the baseline comparison will flag it immediately.

## Remaining V1-to-V2 parity items

After this batch, the core V1-to-V2 parity work is essentially complete. The remaining items are optional packaging/demo improvements:

```text
optional deliverable package parity
optional demo-mode parity
```

## Validation needed

Run:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

The workflow should include:

```text
16. Compare V2 outputs to baseline
```

and the comparison should report:

```text
Status: PASS
```
