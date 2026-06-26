# V2 Deliverable Package Checkpoint

## Status

The V2 workflow now builds a clean local deliverable package folder.

## Added or updated

```text
src/build_v2_deliverable_package.py
src/run_v2.py
src/check_outputs_v2.py
src/write_v2_workflow_success_marker.py
```

## New workflow step

```text
20. Build V2 deliverable package
```

The package is built after the baseline comparison and workflow manifest so it can include the latest baseline and workflow status files.

## Package folder

```text
data/outputs/deliverable_package_v2/
```

## Package structure

```text
data/outputs/deliverable_package_v2/
  README.md
  package_manifest.json
  tables/
  reports/
  charts/
  manifests/
```

## Important packaged outputs

```text
tables/v2_executive_site_summary.csv
reports/v2_executive_site_summary.md
tables/v2_right_sizing_validation.csv
reports/v2_right_sizing_validation_report.md
reports/v2_run_summary.md
reports/v2_results_interpretation.md
charts/v2_polished_readiness_score_chart.png
charts/v2_site_readiness_map.png
charts/v2_port_utilization_simulation.png
manifests/v2_workflow_success.json
manifests/v2_baseline_comparison.json
```

## Checker update

`src/check_outputs_v2.py` now verifies the package README, package manifest, and several key copied package files.

## Validation command

```bash
make run-v2
make check-v2
```

## Purpose

The deliverable package gives one clean folder for screenshots, review, submission, and future presentation preparation without manually hunting through all generated output files.
