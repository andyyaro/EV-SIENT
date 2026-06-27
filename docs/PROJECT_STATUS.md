# Project Status

## Current phase

Phase 2 prototype development for the Public EV Charging Site-Readiness and Right-Sizing Model.

Active branch:

```text
v2-expansion-planning
```

Main workflow guide:

```text
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

Tableau workbook guide:

```text
tableau/README.md
```

This is a planning-support prototype. It supports screening, prioritization, discussion, and follow-up review. It is not a final approval tool.

## Current status summary

V2 is now a stable, reproducible workflow with:

```text
12 real candidate sites
24-step V2 model workflow
V2 output checker
expanded baseline comparison
35-file clean deliverable package
full Tableau CSV export builder
Tableau export checker
QA-polished packaged Tableau workbook
published Tableau Public workbook with visible worksheet tabs
```

The main public visual artifact is the Tableau workbook. Static PNG charts remain support outputs for reproducibility, GitHub previews, and the technical package.

## Current commands

Run the full current workflow from the repo root:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make full-v2-tableau
```

Equivalent raw commands:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

For Tableau-only refresh after current V2 outputs already exist:

```bash
make tableau-exports
make check-tableau
```

## Expected V2 check

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, sensitivity outputs and the port-sizing scenario layer are present, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.
```

## Expected Tableau check

```text
TABLEAU EXPORT CHECK
--------------------
Status: PASSED
Checked exports: 15/15
Candidate sites represented: 12/12
Exact export set, required columns, row counts, numeric fields, and site coverage are valid.
```

## Expected package check

```text
Status: complete
Clean rebuild: True
Previous package removed: True
Copied files: 35/35
Synced files: 35/35
```

## Current candidate set

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

## Current interpretation

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 remains useful but high-review because of garage and site-review uncertainty.
PWC003 should not be treated as a general-public priority unless public access or use-case assumptions change.
```

## Current right-sizing interpretation

```text
FFX002 — install 2 now; plan future-ready capacity of 8
FFX004 — install 3 now; plan future-ready capacity of 8
PWC006 — install 2 now; plan future-ready capacity of 4
FFX001, PWC007, PWC004, FFX003 — starter install with expandable design
PWC002 and PWC001 — review before expansion
PWC008 — monitor due to nearby supply
PWC005 — monitor or small pilot
PWC003 — do not advance general-public buildout without use-case confirmation
```

## Current scenario interpretation

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Base, high-growth, long-session, short-window, and peakier-demand scenarios do not exceed future-ready capacity.
Only the combined-stress scenario creates one-port gaps.
The combined-stress gaps affect PWC002 and PWC008.
```

## Current Tableau status

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx = packaged interactive Tableau workbook
tableau/README.md = Tableau workbook documentation and refresh notes
src/build_tableau_exports.py = regenerates the 15 Tableau-ready CSV inputs
src/check_tableau_exports.py = validates exact Tableau file set, schemas, row counts, numeric fields, and 12-site coverage
data/outputs/tableau/ = generated local Tableau CSV inputs ignored by Git
```

## Current generated-package status

The V2 workflow creates a clean local package at:

```text
data/outputs/deliverable_package_v2/
```

The package contains selected reports, tables, charts, inputs, and manifests for technical review.

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

## Completed recent work

```text
Expanded V2 candidate set to 12 sites.
Added scenario, simulation, validation, executive-summary, and package layers.
Expanded and QA-polished the packaged Tableau workbook.
Published the Tableau Public workbook and documented the workbook entry point.
Added full Tableau CSV export generation for all 15 workbook inputs.
Added Tableau export checker for exact file set, schemas, row counts, numeric fields, and 12-site coverage.
Wired Tableau export generation and checking into the Makefile workflow.
Refreshed repo documentation so Tableau is the main public visual layer and static PNGs are support outputs.
```

## Next likely technical improvements

```text
Continue replacing placeholder site-review assumptions with verified site data.
Add a concise scenario interpretation block to the stakeholder-facing package README.
Consider a small site-review data intake template for future follow-up.
```
