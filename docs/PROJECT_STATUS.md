# Project Status

## Current phase

Phase 2 prototype development for the Public EV Charging Site-Readiness and Right-Sizing Model.

The active technical branch is:

```text
v2-expansion-planning
```

The main V2 guide is:

```text
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

This project is a planning-support model only. It does not replace required technical, utility, permitting, procurement, accessibility, Fire Marshal/AHJ, or stakeholder review.

## Current V2 status

V2 is now a stable, reproducible planning-support workflow with:

```text
12 real candidate sites
24-step reproducible workflow
site-readiness ranking
data-quality validation
sensitivity analysis
scoring-profile analysis
readiness and confidence charts
profile heatmap and rank-stability chart
readiness map
GIS decision map
README GIS decision map with all 12 site callout tags
electrical-risk scenario analysis
right-sizing scenario analysis
port-use simulation
port-sizing scenario analysis
right-sizing validation
executive site summary with scenario-sensitivity fields
interpretation report
run summary
expanded baseline comparison
workflow manifest
35-file clean deliverable package
hardened output checker requiring all 12 V2 sites
hash-sync package validation
Times New Roman chart typography
```

The current V2 workflow is validated locally with:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected final checker result:

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, the port-sizing scenario analysis is present, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.
```

Expected deliverable package result:

```text
Status: complete
Clean rebuild: True
Previous package removed: True
Copied files: 35/35
Synced files: 35/35
```

## Current repo structure

```text
src/                  Python scripts
data/inputs/           Input datasets
data/config/           Config files for scoring profiles, output checks, and output/package manifest
data/source_extracts/  Small source extracts and source notes
data/baselines/        Committed baseline outputs for comparison
data/outputs/          Generated local outputs ignored by Git
data/demo/             Generated synthetic demo outputs ignored by Git
docs/                  Documentation and reporting
```

## Current V2 workflow

Run from the repository root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

`src/run_v2.py` currently runs:

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

## V2 deliverable package

The V2 workflow creates a clean local package at:

```text
data/outputs/deliverable_package_v2/
```

The package includes:

```text
README.md
package_manifest.json
inputs/
reports/
tables/
charts/
manifests/
```

The package builder performs a clean rebuild by default so stale copied files do not survive. The package manifest stores SHA-256 hashes and is only healthy when every copied file matches its current source output.

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

## Latest confirmed V2 ranking

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

## Current strongest findings

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 remains useful but high-review because it is a garage candidate with fire/AHJ/electrical uncertainty.
PWC003 should not be treated as a general-public priority unless public access or use-case assumptions change.
```

## Current V2 right-sizing interpretation

```text
FFX002 — install 2 now; plan future-ready capacity of 8
FFX004 — install 3 now; plan future-ready capacity of 8
PWC006 — install 2 now; plan future-ready capacity of 4
FFX001, PWC007, PWC004, FFX003 — starter install with expandable design
PWC002 and PWC001 — electrical review before expansion
PWC008 — monitor due to nearby supply
PWC005 — monitor or small pilot
PWC003 — do not advance general-public buildout without use-case confirmation
```

## Current V2 port-sizing scenario interpretation

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Base, high-growth, long-session, short-window, and peakier-demand scenarios do not exceed future-ready capacity.
Only the combined-stress scenario creates one-port gaps.
The combined-stress gaps affect PWC002 and PWC008.
```

## Executive-summary scenario fields

The executive summary now includes one site-level scenario sensitivity summary from the port-sizing scenario analysis.

```text
scenario_max_min_ports_2050_high
scenario_future_capacity_gap
scenario_sensitivity_level
scenario_stress_note
```

Expected interpretation:

```text
Most sites — robust
PWC002 — combined_stress_sensitive
PWC008 — combined_stress_sensitive
```

## Current V2 visual status

```text
v2_site_decision_map.png = full report GIS decision map
v2_site_decision_map_readme.png = README-optimized GIS decision map with all 12 site callout tags
v2_port_sizing_scenario_heatmap.png = port-sizing scenario stress-test heatmap
docs/assets/charts/v2_site_decision_map_readme.png = committed README asset synced from generated output
```

Generated Matplotlib charts use the shared Times New Roman chart style. Basemap tile labels cannot be restyled because they are baked into the background tile image.

## Current known review gaps

The data-quality checker currently has no blocking errors, but several fields remain review items.

Main unresolved items before any advancement:

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

These are planning-screen gaps, not workflow failures.

## Stable V1 status

The stable V1 workflow remains available on `main`.

Run V1 with:

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
```

V1 remains useful as the stable baseline. V2 is the active Phase 2 development branch.

## Demo scalability workflow

The repo also has a synthetic demo workflow for checking larger candidate pools.

Run from the repository root:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

Demo mode is not an official recommendation layer. It is for stress-testing scalability, visual readability, workflow robustness, and larger candidate-pool behavior.

## Completed V2 work so far

```text
Expanded V2 candidate set to 12 sites.
Added Batch 002 Prince William library candidates.
Added reviewed public-data extracts.
Added AFDC nearby charging supply counts.
Added VDOT/traffic, ACS/equity, jobs, and amenities signals.
Added electrical-risk scenario analysis.
Added V2 right-sizing scenarios.
Added port-use simulation.
Added port-sizing scenario analysis.
Integrated port simulation into the executive summary.
Integrated port-sizing scenario fields into the executive summary.
Added right-sizing validation layer.
Added GIS decision map and README decision map.
Added all 12 site callout tags to the README decision map.
Set generated chart typography to Times New Roman.
Added clean 35-file V2 deliverable package.
Expanded package contents with profile, stability, GIS-map, simulation, port-sizing scenario, validation, and baseline outputs.
Strengthened output checker to require all 12 V2 site IDs.
Hardened package and README asset hash-sync checks.
Expanded baseline comparison to cover simulation, port-sizing scenarios, validation, executive, and package manifest layers.
Added current V2 workflow guide and refreshed repo documentation.
```

## Next likely technical improvements

```text
Continue replacing placeholder electrical/site-review assumptions with verified site data.
Add a concise scenario interpretation block to the stakeholder-facing package README.
Consider a small site-review data intake template for AHJ / ADA / utility follow-up.
```

## Important limitation

A high readiness score does not mean a site is build-ready.

The model is for planning support only and still requires stakeholder, utility, engineering, ADA/accessibility, Fire Marshal/AHJ, permitting, procurement, and site review.
