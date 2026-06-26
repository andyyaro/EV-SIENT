# V2 Port-Sizing Scenario Analysis Checkpoint

## Status

A new V2 port-sizing scenario analysis layer has been added.

This is the port-sizing counterpart to the existing scoring-profile analysis.

```text
Scoring-profile analysis = stress-tests site ranking under different scoring priorities
Port-sizing scenario analysis = stress-tests port recommendations under different demand and charging assumptions
```

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

## Workflow integration

The V2 workflow now runs this after the base port-use simulation and before right-sizing validation:

```text
13. Run V2 port-use simulation
14. Run V2 port-sizing scenario analysis
15. Validate V2 right-sizing with simulation
```

The full workflow now has 24 steps.

## Package integration

The clean V2 deliverable package now includes the scenario input, scenario results, scenario summary, scenario report, and scenario heatmap.

Expected package health after a full run:

```text
Copied files: 35/35
Synced files: 35/35
```

## Baseline/checker integration

The baseline comparison now includes a `port_sizing_scenarios` check.

The output checker now verifies:

```text
port-sizing scenario result file exists
port-sizing scenario summary exists
port-sizing scenario report exists
port-sizing scenario heatmap exists
all 12 candidate sites are represented in the scenario results
all 6 expected scenarios are present
scenario results have 72 rows
scenario summary has 6 rows
package manifest includes the new scenario artifacts
```

## Interpretation

The analysis should help answer questions like:

```text
Do the future-ready port recommendations still hold if charging sessions are longer?
Which sites become constrained if future demand grows faster?
Does a shorter usable charging window change the minimum recommended ports?
Which future-ready capacities are robust, and which are sensitive to stress assumptions?
```

## Important limitation

This is a planning-screen stress test. It does not replace engineering design, charger utilization studies, utility review, procurement planning, permitting, or stakeholder confirmation.
