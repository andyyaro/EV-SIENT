# V2 Baseline Comparison Expansion Checkpoint

## Status

The V2 baseline comparison has been expanded beyond the original core model checks.

## Updated files

```text
src/compare_v2_to_baseline.py
src/run_v2.py
data/baselines/v2_baseline_snapshot.json
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

## What changed

The baseline comparison now checks these additional V2 layers:

```text
port simulation
right-sizing validation
executive summary validation fields
deliverable package manifest
```

## New baseline-comparison checks

`src/compare_v2_to_baseline.py` now validates:

```text
site count
site results
quality counts
profile top sites
electrical expected-case outputs
right-sizing outputs
port-simulation row count, demand cases, port options, assumptions, and current simulated minimum ports
right-sizing-validation guardrails
executive-summary required fields and current-alignment values
deliverable-package manifest status, copied file counts, and required copied destinations
```

## Workflow change

`src/run_v2.py` now runs 22 steps instead of 20.

The added workflow behavior is:

```text
18. Compare V2 outputs to baseline
19. Write V2 workflow completion manifest
20. Build V2 deliverable package
21. Compare V2 deliverable package manifest to baseline
22. Rebuild V2 deliverable package with final baseline comparison
```

The first comparison creates the baseline comparison report needed by the package. The second comparison checks the generated package manifest. The final package rebuild copies the final baseline comparison report into the package.

## Expected successful result

The V2 workflow should still finish with:

```text
V2 workflow complete.
```

Then the output checker should still finish with:

```text
V2 OUTPUT CHECK
Status: PASSED
```

## Why this matters

Before this checkpoint, the baseline comparison mainly protected the core ranking, scoring, electrical, and right-sizing outputs. It did not directly guard newer V2 layers such as simulation validation, executive summary fields, or the deliverable package manifest.

This change makes the V2 regression guard match the current V2 workflow more closely.
