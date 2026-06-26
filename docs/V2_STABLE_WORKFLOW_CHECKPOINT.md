# V2 Stable Workflow Checkpoint

## Status

The V2 expansion-planning workflow has reached a stable technical checkpoint.

The validated workflow command is:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected final result:

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.
```

Expected deliverable package health:

```text
Status: complete
Clean rebuild: True
Previous package removed: True
Copied files: 30/30
Synced files: 30/30
```

## Stable workflow scope

The current stable V2 workflow includes:

```text
12 candidate sites
23 workflow steps
site-readiness scoring
data-quality review
sensitivity analysis
scoring-profile analysis
electrical-risk scenario analysis
right-sizing scenario analysis
port-use simulation
right-sizing validation
executive site summary
GIS decision map
README GIS decision map
interpretation report
run summary
workflow success manifest
expanded baseline comparison
30-file deliverable package
hardened output/package checker
```

## Candidate sites

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

## Latest confirmed base ranking

```text
1. FFX002 — City of Fairfax Regional Library — 58.8 — Tier 1
2. FFX004 — Fairfax County Government Center — 54.4 — Tier 1
3. PWC006 — Bull Run Library — 52.1 — Tier 2
4. FFX001 — Fairfax City Hall or municipal building — 51.0 — Tier 2
5. PWC002 — Neabsco-Potomac Commuter Garage — 50.3 — High-review
6. PWC007 — Central Library — 50.2 — Tier 2
7. PWC004 — Chinn Park Regional Library — 48.6 — Tier 2
8. FFX003 — Pohick Regional Library — 46.8 — Tier 2
9. PWC008 — Potomac Library — 40.1 — Tier 3
10. PWC001 — PWC McCoart Government Center — 39.8 — Tier 3
11. PWC005 — Haymarket Gainesville Library — 36.9 — Tier 3
12. PWC003 — Prince William County Public Safety Training Center — 29.6 — special-use
```

## Main findings

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC007 is a credible Tier 2 Prince William candidate close to PWC002 but with fewer garage-specific complications.
PWC002 remains useful but high-review because it is a garage candidate with fire/AHJ/access/electrical uncertainty.
PWC003 should not advance as a general-public charging buildout unless public-access or use-case assumptions change.
```

## Right-sizing summary

```text
FFX002 — now 2 ports; future-ready capacity 8; install now and make future-ready
FFX004 — now 3 ports; future-ready capacity 8; install now and make future-ready
PWC006 — now 2 ports; future-ready capacity 4; install now and make future-ready
FFX001 — now 2 ports; future-ready capacity 4; starter install with expandable design
PWC002 — now 2 ports; future-ready capacity 3; electrical review before expansion
PWC007 — now 2 ports; future-ready capacity 4; starter install with expandable design
PWC004 — now 2 ports; future-ready capacity 4; starter install with expandable design
FFX003 — now 2 ports; future-ready capacity 4; starter install with expandable design
PWC008 — now 2 ports; future-ready capacity 2; monitor due to nearby supply
PWC001 — now 2 ports; future-ready capacity 3; electrical review before expansion
PWC005 — now 2 ports; future-ready capacity 2; monitor or small pilot
PWC003 — now 2 ports; future-ready capacity 2; do not advance general-public buildout
```

## Simulation validation summary

```text
Current simulated minimum ports: 2 for all sites
FFX004 current alignment: conservative_under_current_demand
Most other current alignments: aligned_now
Future alignment values: aligned_future_capacity, conservative_future_capacity, or extra_future_capacity
No current stable output is flagged as underbuilt by the simulation validation layer
```

## Visual outputs

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_utilization_simulation.png
docs/assets/charts/v2_site_decision_map_readme.png
```

The README decision map includes callout tags for all 12 candidate sites. Generated Matplotlib chart text uses Times New Roman. Basemap tile labels cannot be restyled because they are part of the map background image.

## Deliverable package

The stable package is generated locally at:

```text
data/outputs/deliverable_package_v2/
```

Open first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
data/outputs/deliverable_package_v2/reports/v2_baseline_comparison.md
```

## Baseline and checker guardrails

The stable checkpoint includes guardrails for:

```text
site count
site ranks, scores, tiers, and model port recommendations
data-quality counts
profile top sites
electrical expected-case ranks, scores, and risk levels
right-sizing ports and expansion strategies
port-simulation assumptions, rows, demand cases, and tested port options
right-sizing-validation alignment fields
executive-summary validation fields
README decision-map asset sync
deliverable-package manifest status
deliverable-package copied and synced counts
deliverable-package file hash sync
```

## Known review gaps

The stable workflow has no blocking code/output errors, but the planning model still depends on assumptions that need confirmation.

Main unresolved review items:

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
PWC003 public, fleet-only, special-use, or removal decision
```

These are planning-screen limitations, not workflow failures.

## Next development direction

The strongest next coding upgrade is a configurable simulation-assumption scenario layer:

```text
data/inputs/v2_simulation_assumptions.csv
src/run_port_assumption_scenarios.py
data/outputs/v2_port_assumption_scenarios.csv
data/outputs/v2_port_assumption_scenario_report.md
data/outputs/charts/v2_port_assumption_scenario_heatmap.png
```

That layer should test how port-sizing conclusions change under different assumptions for charging duration, charging-window hours, peak factor, and future demand multipliers.

## Important limitation

This is an early planning prototype. It does not replace stakeholder confirmation, utility review, engineering design, accessibility review, Fire Marshal/AHJ review, permitting, procurement, or construction planning.
