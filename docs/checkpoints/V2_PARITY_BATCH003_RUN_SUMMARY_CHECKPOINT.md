# V2 Parity Batch 003 — Run Summary Checkpoint

## Purpose

This checkpoint records the third V1-to-V2 feature parity implementation batch.

The goal was to mirror the V1 Markdown run-summary feature inside the V2 workflow while adding V2-specific sections for electrical-risk scenarios and right-sizing scenarios.

## Added or updated

```text
src/generate_run_summary_v2.py
src/run_v2.py
src/check_outputs_v2.py
```

## New V2 run-summary output

```text
data/outputs/v2_run_summary.md
```

## What the V2 run summary includes

The V2 run summary includes:

```text
top candidate summary
current ranking table
data-quality summary
remaining review items by field
sensitivity summary
scoring profile summary
electrical-risk scenario summary
right-sizing scenario summary
generated visual outputs
generated Markdown reports
next data to improve
```

## V2 workflow change

`src/run_v2.py` now includes:

```text
14. Generate V2 run summary
```

The step calls:

```text
src/generate_run_summary_v2.py
```

with V2 paths:

```text
--results data/outputs/v2_site_results.csv
--quality data/outputs/v2_data_quality_report.csv
--sensitivity data/outputs/v2_sensitivity_summary.csv
--profile-results data/outputs/v2_profile_results.csv
--electrical-summary data/outputs/v2_electrical_risk_summary.csv
--right-sizing data/outputs/v2_right_sizing_scenarios.csv
--output data/outputs/v2_run_summary.md
```

## V2 checker change

`src/check_outputs_v2.py` now requires:

```text
data/outputs/v2_run_summary.md
```

It also checks that the file contains key sections:

```text
# V2 Model Run Summary
Electrical-risk scenario summary
Right-sizing scenario summary
Generated visual outputs
```

## Remaining V1-to-V2 parity items

After this batch, the main remaining parity items are:

```text
V2 success marker / output manifest
V2 baseline comparison
optional deliverable package / demo-mode parity
```

## Validation needed

Run:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Then open:

```text
data/outputs/v2_run_summary.md
```

The checker confirms the file exists and includes the required sections, but human review should confirm the summary is readable enough for future reporting.
