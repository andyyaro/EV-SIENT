# V2 Deliverable Package — Expanded Content Checkpoint

## Status

The V2 deliverable package now includes additional ranking-stability and profile-analysis outputs.

## Updated files

```text
src/build_v2_deliverable_package.py
src/check_outputs_v2.py
```

## Newly packaged outputs

```text
reports/v2_action_matrix.md
reports/v2_profile_comparison.md
tables/v2_sensitivity_summary.csv
tables/v2_profile_results.csv
tables/v2_profile_rank_summary.csv
```

## Why this matters

The package already included the executive summary, right-sizing validation, run summary, charts, baseline comparison, and workflow manifest.

This update makes the package more useful for review because it also includes the files that explain:

```text
how readiness and confidence map to recommended actions
whether rankings stay stable under sensitivity testing
how sites perform under different scoring profiles
which sites are top-ranked by profile
```

## Package README update

The suggested review order now includes:

```text
reports/v2_action_matrix.md
reports/v2_profile_comparison.md
tables/v2_sensitivity_summary.csv
```

## Checker update

`src/check_outputs_v2.py` now checks for the newly copied package files so the workflow will fail if they are missing from the deliverable package.

## Validation command

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected deliverable-package output should now show:

```text
Copied files: 28/28
```
