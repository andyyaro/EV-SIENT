# V2 Current Workflow Guide

This is the main landing page for the active V2 EV charging site-readiness and right-sizing prototype.

Use this guide when working on the `v2-expansion-planning` branch.

## Current status

V2 is now a stable Phase 2 technical workflow on the active development branch.

The latest V2 workflow includes:

```text
12 real candidate sites
24 workflow steps
right-sizing scenarios
port-use simulation
port-sizing scenario analysis
right-sizing validation
executive site summary with scenario-sensitivity fields
readiness map
GIS decision map
README GIS decision map with all 12 site callout tags
Times New Roman chart typography
expanded baseline comparison
35-file deliverable package
workflow manifest
hardened output/package checker
```

A successful run should end with:

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, the port-sizing scenario analysis is present, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.
```

A healthy package build should show:

```text
Status: complete
Clean rebuild: True
Previous package removed: True
Copied files: 35/35
Synced files: 35/35
```

## Branch to use

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
```

Use `main` only for the stable V1 workflow. Use `v2-expansion-planning` for the active V2 model work.

## One-command V2 run

From the repository root:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Or from a clean local update:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

## What the V2 workflow does

`src/run_v2.py` runs the full V2 workflow in this order:

```text
1. Run V2 site-readiness model
2. Add V2 readiness-confidence action matrix
3. Create V2 polished readiness score chart
4. Create V2 data confidence chart
5. Validate V2 site input data
6. Run V2 sensitivity analysis
7. Run V2 scoring-profile analysis
8. Create V2 profile score heatmap
9. Create V2 profile rank stability chart
10. Create V2 readiness map
11. Run V2 electrical-feasibility scenario analysis
12. Run V2 right-sizing scenario analysis
13. Run V2 port-use simulation
14. Run V2 port-sizing scenario analysis
15. Validate V2 right-sizing with simulation
16. Build V2 executive site summary
17. Create V2 GIS decision maps
18. Generate V2 interpretation report
19. Generate V2 run summary
20. Compare V2 outputs to baseline
21. Write V2 workflow completion manifest
22. Build V2 deliverable package
23. Compare V2 deliverable package manifest to baseline
24. Rebuild V2 deliverable package with final baseline comparison
```

The first baseline comparison creates the comparison files needed by the package. The second baseline comparison verifies the generated package manifest, then the final package rebuild copies the final comparison report into the package.

## What the checker validates

`src/check_outputs_v2.py` checks that:

```text
expected V2 files exist and are non-empty
main result tables include required columns
all 12 V2 candidate sites are represented
port simulation output exists
port-sizing scenario outputs exist
right-sizing validation output exists
executive summary output exists
executive summary includes scenario-sensitivity fields
readiness map output exists
GIS decision map output exists
README GIS decision map output exists
README GIS decision-map asset is synced with the generated chart
deliverable package exists
package manifest reports a clean rebuild
package manifest reports 35 copied files and 35 synced files
package file hashes match current source outputs
workflow manifest reports success
baseline comparison reports pass
baseline comparison covers simulation, port-sizing scenarios, validation, executive, and package layers
```

## What the expanded baseline comparison validates

`src/compare_v2_to_baseline.py` checks:

```text
site count
site ranking, readiness scores, tiers, and model port recommendations
data-quality counts
profile top sites
electrical expected-case ranks, scores, and risk levels
right-sizing ports and expansion strategies
port-simulation row count, assumptions, tested port options, demand cases, and current simulated minimum ports
port-sizing scenario row count, scenario names, required fields, and future-capacity alignment labels
right-sizing-validation alignment guardrails
executive-summary validation fields, scenario-sensitivity fields, and top site
deliverable-package manifest status, copied file counts, synced file counts, and required package destinations
```

## Current V2 candidate sites

```text
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
FFX003 — Pohick Regional Library
FFX004 — Fairfax County Government Center
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
PWC005 — Haymarket Gainesville Library
PWC006 — Bull Run Library
PWC007 — Central Library
PWC008 — Potomac Library
```

## Files to open first

After a successful V2 run, start here:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
data/outputs/deliverable_package_v2/reports/v2_baseline_comparison.md
```

The deliverable package is the cleanest review folder because it collects the most important outputs into one place.

## Main V2 output folder

```text
data/outputs/
```

Important V2 outputs:

```text
v2_site_results.csv
v2_action_matrix.md
v2_data_quality_report.csv
v2_sensitivity_results.csv
v2_sensitivity_summary.csv
v2_profile_results.csv
v2_profile_rank_summary.csv
v2_profile_comparison.md
v2_electrical_scenario_results.csv
v2_electrical_risk_summary.csv
v2_electrical_feasibility_report.md
v2_right_sizing_scenarios.csv
v2_right_sizing_report.md
v2_port_utilization_simulation.csv
v2_port_utilization_simulation_report.md
v2_port_sizing_scenario_results.csv
v2_port_sizing_scenario_summary.csv
v2_port_sizing_scenario_report.md
v2_right_sizing_validation.csv
v2_right_sizing_validation_report.md
v2_executive_site_summary.csv
v2_executive_site_summary.md
v2_results_interpretation.md
v2_run_summary.md
v2_baseline_comparison.json
v2_baseline_comparison.md
v2_workflow_success.json
```

Important V2 charts:

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_utilization_simulation.png
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
```

## Readiness map vs GIS decision map

The workflow produces two map-style visuals:

```text
v2_site_readiness_map.png = analytical geography/readiness scatter
v2_site_decision_map.png = presentation-oriented GIS decision graphic combining rank, tier, review risk, and port-sizing
v2_site_decision_map_readme.png = README-optimized GIS decision graphic with all 12 candidate callout tags
```

Use the decision map for README, presentation, and stakeholder-facing review. Keep the readiness map as the more technical geography view.

## Port-sizing scenario analysis

The port-sizing scenario analysis is the port-sizing counterpart to the scoring-profile analysis.

```text
Scoring-profile analysis = stress-tests site ranking under different scoring priorities
Port-sizing scenario analysis = stress-tests port recommendations under different charging and demand assumptions
```

The active scenario input is:

```text
data/inputs/v2_port_sizing_scenarios.csv
```

The main scenario outputs are:

```text
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
```

Current scenario interpretation:

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

## Executive-summary scenario fields

The executive summary now includes the scenario stress-test result at the site level.

```text
scenario_max_min_ports_2050_high
scenario_future_capacity_gap
scenario_sensitivity_level
scenario_stress_note
```

Use these fields to quickly see whether a site is robust across tested assumptions or sensitive only under combined stress.

## Chart typography

Generated Matplotlib charts use the shared Times New Roman chart style configured in:

```text
src/chart_style.py
sitecustomize.py
src/sitecustomize.py
```

Basemap tile labels cannot be restyled because they are part of the background map image.

## Deliverable package

The workflow creates a clean local package at:

```text
data/outputs/deliverable_package_v2/
```

The package contains:

```text
README.md
package_manifest.json
inputs/
reports/
tables/
charts/
manifests/
```

The package builder uses a clean rebuild by default, so stale copied files are removed before the package is rebuilt.

A healthy package build should show:

```text
Status: complete
Clean rebuild: True
Previous package removed: True
Copied files: 35/35
Synced files: 35/35
```

## Current model interpretation

The current V2 run identifies:

```text
FFX002 — City of Fairfax Regional Library
```

as the strongest current public candidate.

The current V2 ranking also shows:

```text
FFX004 — stable second-ranked Tier 1 candidate
PWC006 — strongest current Prince William County library candidate
PWC002 — useful high-review garage candidate, but needs garage/fire/AHJ/electrical review
PWC003 — special-use / low public-priority unless the public-access use case changes
```

## Current right-sizing interpretation

```text
FFX002 — install 2 now; plan future-ready capacity of 8
FFX004 — install 3 now; plan future-ready capacity of 8
PWC006 — install 2 now; plan future-ready capacity of 4
Most Tier 2 library candidates — starter install with expandable design
PWC002 and PWC001 — require electrical review before expansion
PWC008 and PWC005 — monitor or small pilot
PWC003 — do not advance as a general-public buildout without use-case confirmation
```

## What “passed” means

A passing V2 run means the local workflow generated the expected files, the tables have the expected structure, the 12 candidate sites are present, the workflow manifest is healthy, the expanded baseline comparison passed, the port-sizing scenario layer is present, the executive summary includes scenario-sensitivity fields, the README GIS decision-map asset is synced, and the deliverable package manifest passed the package guardrails.

It does not mean a site is ready to build.

## Known assumptions still needing confirmation

The main unresolved review items are:

```text
electrical service rating
spare electrical capacity
emergency disconnect visibility
visitor and employee counts
operating hours
parking count and likely charger placement
ADA/accessibility layout review
Fire Marshal / AHJ review where applicable
stormwater or site civil constraints where applicable
PWC002 garage-specific review
PWC003 public-access / fleet-only / special-use decision
```

These are planning-screen gaps, not code failures.

## Important limitation

The prototype is for early planning support only. It does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, permitting, procurement, stakeholder confirmation, or construction planning.
