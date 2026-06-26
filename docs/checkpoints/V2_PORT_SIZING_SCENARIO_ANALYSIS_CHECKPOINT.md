# V2 Port-Sizing Scenario Analysis Checkpoint

## Status

A new V2 port-sizing scenario analysis layer has been added and polished for review.

This is the port-sizing counterpart to the existing scoring-profile analysis.

```text
Scoring-profile analysis = stress-tests site ranking under different scoring priorities
Port-sizing scenario analysis = stress-tests port recommendations under different demand and charging assumptions
```

The scenario layer is now also integrated into the V2 executive site summary.

## New input

```text
data/inputs/v2_port_sizing_scenarios.csv
```

The scenario input currently includes:

```text
base
high_growth
long_sessions
short_daily_window
peakier_demand
combined_stress
```

Each scenario controls:

```text
average charging duration
usable daily charging window
peak-demand factor
current demand multiplier
2035 high-demand multiplier
2050 high-demand multiplier
```

## New script

```text
src/run_port_sizing_scenario_analysis.py
```

The script compares each site's current and future-ready port plan against the scenario assumptions.

## New outputs

```text
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
```

## Executive-summary integration

The executive site summary now reads the detailed scenario result table and adds one scenario-sensitivity summary per site.

Updated script:

```text
src/build_v2_executive_summary.py
```

New executive-summary fields:

```text
scenario_max_min_ports_2050_high
scenario_future_capacity_gap
scenario_sensitivity_level
scenario_stress_note
```

How to read them:

```text
scenario_max_min_ports_2050_high = highest scenario-based 2050 high-demand minimum port count
scenario_future_capacity_gap = largest future-ready capacity gap found across tested scenarios
scenario_sensitivity_level = robust, combined_stress_sensitive, or scenario_sensitive
scenario_stress_note = plain-English note for the decision table
```

Expected site-level interpretation:

```text
Most sites: robust
PWC002: combined_stress_sensitive
PWC008: combined_stress_sensitive
```

## Visual/report polish

The scenario heatmap now uses presentation-friendly labels instead of raw code-style scenario names.

Examples:

```text
high_growth -> High Growth
long_sessions -> Long Sessions
short_daily_window -> Short Daily Window
peakier_demand -> Peakier Demand
combined_stress -> Combined Stress
```

The heatmap title is shorter, text contrast is improved, and the chart includes a note explaining that the cell values are the minimum tested port counts that avoid an underbuilt result under each scenario.

The Markdown report now includes a headline finding before the detailed tables.

## Workflow integration

The V2 workflow now runs this after the base port-use simulation and before right-sizing validation:

```text
13. Run V2 port-use simulation
14. Run V2 port-sizing scenario analysis
15. Validate V2 right-sizing with simulation
```

The executive summary then uses the generated scenario output at step 16.

The full workflow still has 24 steps.

## Package integration

The clean V2 deliverable package includes the scenario input, scenario results, scenario summary, scenario report, scenario heatmap, and the updated executive summary carrying the scenario-sensitivity fields.

Expected package health after a full run:

```text
Copied files: 35/35
Synced files: 35/35
```

## Baseline/checker/manifest integration

The baseline comparison includes a `port_sizing_scenarios` check and now requires the executive summary scenario-sensitivity fields.

The output checker verifies:

```text
port-sizing scenario result file exists
port-sizing scenario summary exists
port-sizing scenario report exists
port-sizing scenario heatmap exists
all 12 candidate sites are represented in the scenario results
all 6 expected scenarios are present
scenario results have 72 rows
scenario summary has 6 rows
executive summary includes scenario-sensitivity fields
package manifest includes the scenario artifacts
```

The V2 workflow success marker records:

```text
workflow_step_count: 24
Generated outputs: 35/35
```

## Current interpretation

The latest scenario output shows that the current future-ready capacity plan is stable across the first five scenarios.

```text
base: no future-ready capacity gaps
high_growth: no future-ready capacity gaps
long_sessions: no future-ready capacity gaps
short_daily_window: no future-ready capacity gaps
peakier_demand: no future-ready capacity gaps
combined_stress: 2 future-ready capacity gaps
```

The combined-stress scenario identifies two one-port gaps:

```text
PWC002: future-ready capacity 3, scenario minimum 4, gap 1
PWC008: future-ready capacity 2, scenario minimum 3, gap 1
```

This supports the interpretation that the V2 right-sizing recommendations are robust under normal and moderate stress assumptions, with limited sensitivity under the most aggressive combined-stress case.

## Important limitation

This is a planning-screen stress test. It does not replace engineering design, charger utilization studies, utility review, procurement planning, permitting, or stakeholder confirmation.
