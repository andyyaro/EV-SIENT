# V2 Parity Batch 002 — Readiness Map Checkpoint

## Purpose

This checkpoint records the second V1-to-V2 feature parity implementation batch.

The goal was to mirror the V1 readiness-map feature in the V2 workflow while making the map script safer for the expanded V2 candidate set.

## Added or updated

```text
src/plot_site_map.py
src/run_v2.py
src/check_outputs_v2.py
```

## New V2 map output

```text
data/outputs/charts/v2_site_readiness_map.png
```

## What changed

The site-map script now better supports the 12-site V2 dataset by using:

```text
V2-specific hand-tuned label offsets
automatic label offsets for any future sites
Fairfax-area labeling instead of only Fairfax City labeling
dynamic planning notes for the current V2 candidate set
V2-specific workflow output path
```

## V2 workflow change

`src/run_v2.py` now includes:

```text
Create V2 readiness map
```

The step calls:

```text
src/plot_site_map.py
```

with V2 paths:

```text
--input data/inputs/real_sites_v2.csv
--results data/outputs/v2_site_results.csv
--sensitivity data/outputs/v2_sensitivity_summary.csv
--profile-results data/outputs/v2_profile_results.csv
--output data/outputs/charts/v2_site_readiness_map.png
```

## V2 checker change

`src/check_outputs_v2.py` now requires:

```text
data/outputs/charts/v2_site_readiness_map.png
```

## Remaining V1-to-V2 parity items

After this batch, the main remaining parity items are:

```text
Markdown run summary
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

Then visually inspect:

```text
data/outputs/charts/v2_site_readiness_map.png
```

The checker can confirm the file exists and is non-empty, but only visual review can confirm whether labels are clean enough for presentation.
