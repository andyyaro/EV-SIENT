# V2 Parity Batch 005 — Baseline Comparison Results

## Status

The V2 baseline-comparison parity batch ran successfully.

The V2 workflow now compares current outputs against the committed V2 baseline snapshot, and the V2 output checker passed after validating the comparison output.

## Confirmed workflow section

The successful run included:

```text
16. Compare V2 outputs to baseline
```

## Confirmed generated comparison outputs

```text
data/outputs/v2_baseline_comparison.json
data/outputs/v2_baseline_comparison.md
```

## Confirmed comparison status

```text
V2 BASELINE COMPARISON
Status: PASS
```

## Confirmed passed checks

```text
PASS site_count: Site count matches baseline: 12.
PASS site_results: Ranks, readiness scores, tiers, and model port recommendations match baseline.
PASS quality_counts: Quality counts match baseline: {'ERROR': 0, 'WARNING': 0, 'REVIEW': 38, 'INFO': 12}.
PASS profile_top_sites: Profile top sites match baseline: {'base': 'FFX002', 'demand_priority': 'FFX004', 'equity_priority': 'FFX002', 'feasibility_priority': 'FFX002', 'safety_priority': 'FFX002'}.
PASS electrical_expected: Expected electrical-case ranks, scores, and risk levels match baseline.
PASS right_sizing: Right-sizing ports, future-ready capacity, and strategies match baseline.
```

## Output checker status

```text
V2 OUTPUT CHECK
Status: PASSED
```

## V1-to-V2 parity progress after this batch

The core V1-to-V2 parity work is now complete.

V2 now mirrors or upgrades the major V1 workflow features:

```text
site scoring
recommended ports
right-sizing scenarios
action matrix
data validation
sensitivity analysis
profile analysis
polished readiness chart
data confidence chart
profile heatmap
profile rank stability chart
readiness map
interpretation report
Markdown run summary
workflow success marker / output manifest
baseline comparison
output checker
```

## Remaining items

The only remaining V1-style items are optional polish/package items:

```text
optional deliverable package parity
optional demo-mode parity
```

## Recommended next step

The project can now safely move from parity work back to V2 enhancement work. The strongest next technical enhancement is a consolidated V2 executive output table that joins ranking, confidence, electrical risk, right-sizing, review flags, and strategy into one CSV for easier reporting and presentation.
