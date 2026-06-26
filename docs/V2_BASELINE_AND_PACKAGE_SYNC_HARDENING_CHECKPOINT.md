# V2 Baseline and Package Sync Hardening Checkpoint

## Status

The V2 validation layer has been hardened after the GIS decision-map refresh, README map updates, Times New Roman chart style switch, and deliverable-package sync work.

## Updated files

```text
src/check_outputs_v2.py
src/compare_v2_to_baseline.py
data/baselines/v2_baseline_snapshot.json
```

## What changed

```text
Expanded the output checker so it expects the full current V2 package contents.
Added direct hash-sync checking for the README GIS decision-map asset under docs/assets/charts/.
Strengthened deliverable-package validation so expected_count, copied_count, and synced_count must all match the 30 package payload files.
Required clean rebuild confirmation in the package manifest.
Required every manifest record that is copied to also be marked in_sync.
Required the baseline-comparison JSON to include the newer checks: port simulation, right-sizing validation, executive summary, and deliverable-package manifest.
Expanded the saved baseline package-manifest guardrails to include all 30 copied package payload destinations.
Tightened baseline manifest comparison to check synced_count and out_of_sync_destinations, not only copied_count.
```

## Why this matters

The V2 workflow now fails faster if any of the following happens:

```text
A generated output is missing or empty.
One of the 12 candidate sites drops out of a main table.
The README decision-map asset is stale compared with the generated README map.
The deliverable package contains stale copied files.
The deliverable package manifest omits expected tables, reports, charts, or manifests.
The baseline comparison does not cover the newer simulation, validation, executive, and package layers.
```

## Validation commands

Run from the repository root:

```bash
python -m py_compile src/check_outputs_v2.py src/compare_v2_to_baseline.py
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected final checker result:

```text
Status: PASSED
```

Expected package health:

```text
Copied files: 30/30
Synced files: 30/30
```

## Notes

This hardening step does not change site scores, rankings, right-sizing logic, or port-simulation assumptions. It only strengthens reproducibility and synchronization checks around the current V2 outputs.
