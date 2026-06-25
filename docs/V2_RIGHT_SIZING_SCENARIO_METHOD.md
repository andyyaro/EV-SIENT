# V2 Right-Sizing Scenario Method

## Why this exists

The original V2 model recommended ports for now, 2035, and 2050 from estimated charging sessions. That was useful, but it did not clearly separate:

```text
what to install now
what to prepare for later
what happens under expected EV growth
what happens under faster EV growth
```

The right-sizing scenario module adds that missing planning layer.

## New outputs

The V2 workflow now writes:

```text
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_right_sizing_report.md
```

## New columns

```text
ports_now
ports_2035_base
ports_2035_high
ports_2050_base
ports_2050_high
site_capacity_cap
future_ready_capacity
expansion_strategy
right_sizing_reason
```

## Meaning of base and high

```text
base = normal or expected growth case
high = faster-growth case
```

For example:

```text
ports_2035_base = recommended 2035 target under expected growth
ports_2035_high = recommended 2035 target if EV demand grows faster
ports_2050_base = recommended 2050 target under expected growth
ports_2050_high = recommended 2050 target if EV demand grows faster
```

## Growth multipliers

The current planning multipliers are:

```text
2035_base = current estimated sessions x 1.8
2035_high = current estimated sessions x 2.5
2050_base = current estimated sessions x 3.0
2050_high = current estimated sessions x 4.5
```

## Future-ready capacity

`future_ready_capacity` does not mean every port should be installed now.

It means the site should try to preserve enough space, conduit, panel pathway, or design flexibility for that number of ports if practical.

Example:

```text
ports_now = 2
future_ready_capacity = 6
```

This means:

```text
Install 2 ports now, but design the site so it can expand toward 6 ports later without expensive rework.
```

## Strategy rules

The module adds simple planning strategy labels:

```text
install_now_and_make_future_ready
starter_install_with_expandable_design
electrical_review_before_expansion
garage_review_before_buildout
monitor_due_to_nearby_supply
monitor_or_small_pilot
do_not_advance_general_public_buildout
```

These strategy labels help explain whether a site should be built now, prepared for later, monitored, or reviewed first.

## Important limitation

This remains a planning-support screen. It does not replace engineering design, utility review, facilities confirmation, AHJ review, or Fire Marshal review.

The purpose is to make the prototype more practical for city/county planning by avoiding two extremes:

```text
underbuilding a strong future site
or overbuilding a site with weak demand or high review risk
```
