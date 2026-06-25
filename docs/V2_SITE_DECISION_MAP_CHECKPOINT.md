# V2 Site Decision Map Checkpoint

## Status

A new presentation-oriented V2 site decision map has been added to the workflow.

## New script

```text
src/plot_site_decision_map.py
```

## New output

```text
data/outputs/charts/v2_site_decision_map.png
```

## Purpose

The existing readiness map remains useful as a technical geography/readiness scatter. The new decision map is designed to be more useful for README, presentation, and stakeholder-facing review.

It combines:

```text
site rank
readiness score
recommendation/action category
electrical-review risk
right-sizing ports now
future-ready capacity
planning guardrails
```

## Workflow integration

`src/run_v2.py` now includes:

```text
16. Create V2 decision map
```

The full V2 workflow now has 23 steps.

## Package integration

The decision map is copied into the V2 deliverable package at:

```text
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
```

The package manifest baseline now expects 29 copied files.

## Validation

The output checker now requires:

```text
data/outputs/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
```

## Recommended README update after local generation

After running the workflow and reviewing the new image, copy it into the committed README assets:

```bash
cp data/outputs/charts/v2_site_decision_map.png docs/assets/charts/v2_site_decision_map.png
```

Then update the README preview to use the decision map for the map section.
