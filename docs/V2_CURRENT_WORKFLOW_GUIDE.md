# V2 Current Workflow Guide

This is the main landing page for the active V2 EV charging site-readiness and right-sizing prototype.

Use this guide when working on the `v2-expansion-planning` branch.

## Current status

V2 is the active Phase 2 prototype branch.

The latest V2 workflow includes:

```text
12 real candidate sites
23 workflow steps
right-sizing scenarios
port-use simulation
right-sizing validation
executive site summary
readiness map
new decision map
expanded baseline comparison
deliverable package
workflow manifest
output checker
```

A successful run should end with:

```text
V2 OUTPUT CHECK
Status: PASSED
All expected V2 outputs are present and all 12 V2 candidate sites are represented in the main output tables.
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
14. Validate V2 right-sizing with simulation
15. Build V2 executive site summary
16. Create V2 decision map
17. Generate V2 interpretation report
18. Generate V2 run summary
19. Compare V2 outputs to baseline
20. Write V2 workflow completion manifest
21. Build V2 deliverable package
22. Compare V2 deliverable package manifest to baseline
23. Rebuild V2 deliverable package with final baseline comparison
```

The first baseline comparison creates the comparison files needed by the package. The second baseline comparison verifies the generated package manifest, then the final package rebuild copies the final comparison report into the package.

## What the checker validates

`src/check_outputs_v2.py` checks that:

```text
expected V2 files exist and are non-empty
main result tables include required columns
all 12 V2 candidate sites are represented
port simulation output exists
right-sizing validation output exists
executive summary output exists
readiness map output exists
decision map output exists
deliverable package output exists
workflow manifest reports success
baseline comparison reports pass
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
right-sizing-validation alignment guardrails
executive-summary validation fields and top site
deliverable-package manifest status, copied file counts, and required package destinations
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
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
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
v2_sensitivity_summary.csv
v2_profile_results.csv
v2_profile_rank_summary.csv
v2_profile_comparison.md
v2_electrical_risk_summary.csv
v2_electrical_feasibility_report.md
v2_right_sizing_scenarios.csv
v2_right_sizing_report.md
v2_port_utilization_simulation.csv
v2_port_utilization_simulation_report.md
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
data/outputs/charts/v2_port_utilization_simulation.png
```

## Readiness map vs decision map

The workflow now produces two map-style visuals:

```text
v2_site_readiness_map.png = analytical geography/readiness scatter
v2_site_decision_map.png = presentation-oriented decision graphic combining rank, tier, review risk, and port-sizing
```

Use the decision map for README, presentation, and stakeholder-facing review. Keep the readiness map as the more technical geography view.

## Deliverable package

The workflow creates a clean local package at:

```text
data/outputs/deliverable_package_v2/
```

The package contains:

```text
README.md
package_manifest.json
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
Copied files: 29/29
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

## What “passed” means

A passing V2 run means the local workflow generated the expected files, the tables have the expected structure, the 12 candidate sites are present, the workflow manifest is healthy, the expanded baseline comparison passed, and the deliverable package manifest passed the package guardrail.

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
