# V2 Stable Workflow Checkpoint

## Status

The active V2 workflow is stable with the port-sizing scenario analysis included.

Run:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected checker result:

```text
Status: PASSED
```

Expected package result:

```text
Copied files: 35/35
Synced files: 35/35
```

## Current stable scope

```text
12 candidate sites
24 workflow steps
site-readiness scoring
data-quality review
sensitivity analysis
scoring-profile analysis
electrical-risk scenario analysis
right-sizing scenario analysis
port-use simulation
port-sizing scenario analysis
right-sizing validation
executive site summary
GIS decision map
README GIS decision map
interpretation report
run summary
workflow success manifest
expanded baseline comparison
35-file deliverable package
hardened output/package checker
```

## Current ranking summary

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
12. PWC003 — special-use — 29.6
```

## Main findings

```text
FFX002 is the strongest current candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 remains useful but high-review.
PWC003 should stay special-use unless its use case changes.
```

## Right-sizing summary

```text
FFX002 — now 2 ports; future-ready capacity 8
FFX004 — now 3 ports; future-ready capacity 8
PWC006 — now 2 ports; future-ready capacity 4
Most Tier 2 library candidates — starter install with expandable design
PWC002 and PWC001 — review before expansion
PWC008 and PWC005 — monitor or small pilot
PWC003 — do not advance as a general-public buildout without use-case confirmation
```

## Port-sizing scenario summary

The scenario layer tests whether port recommendations stay reasonable under alternate charging-duration, daily-window, peak-demand, and future-demand assumptions.

```text
base: no future-ready capacity gaps
high_growth: no future-ready capacity gaps
long_sessions: no future-ready capacity gaps
short_daily_window: no future-ready capacity gaps
peakier_demand: no future-ready capacity gaps
combined_stress: 2 future-ready capacity gaps
```

Combined-stress gaps:

```text
PWC002 — future-ready capacity 3, scenario minimum 4, gap 1
PWC008 — future-ready capacity 2, scenario minimum 3, gap 1
```

## Key files to review

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/deliverable_package_v2/reports/v2_baseline_comparison.md
```

## Guardrails now covered

```text
site count
site ranks and scores
profile top sites
electrical expected-case outputs
right-sizing outputs
port simulation outputs
port-sizing scenario outputs
right-sizing validation
executive-summary fields
README decision-map asset sync
deliverable-package hash sync
```

## Next development direction

The strongest next coding upgrade is integrating port-sizing scenario fields into the executive site summary.

## Important limitation

This is an early planning prototype. It does not replace required site, engineering, accessibility, utility, permitting, or stakeholder review.
