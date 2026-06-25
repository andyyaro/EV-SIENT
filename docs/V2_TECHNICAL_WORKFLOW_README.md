# V2 Technical Workflow README

## Project focus

This V2 prototype supports public EV charging site-readiness and right-sizing analysis for Fairfax City and Prince William County.

The model is intentionally transparent and beginner-friendly. It uses CSV inputs, Python scripts, pandas, numpy, and matplotlib rather than heavy GIS or machine learning.

## Main branch for V2 work

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
```

## Main input file

```text
data/inputs/real_sites_v2.csv
```

This file stores the current V2 candidate-site data. It includes original V1 sites plus expanded V2 candidates.

## Main workflow command

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

The workflow runs:

```text
1. V2 site-readiness model
2. readiness-confidence action matrix
3. input data-quality validation
4. sensitivity analysis
5. scoring-profile analysis
6. electrical-feasibility scenario analysis
7. interpretation report generation
```

## Main local outputs

The generated local outputs are written under:

```text
data/outputs/
data/outputs/charts/
```

Important V2 outputs:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_action_matrix.md
data/outputs/v2_data_quality_report.csv
data/outputs/v2_sensitivity_summary.csv
data/outputs/v2_profile_results.csv
data/outputs/v2_profile_comparison.md
data/outputs/v2_electrical_scenario_results.csv
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_electrical_feasibility_report.md
data/outputs/v2_results_interpretation.md
data/outputs/charts/v2_readiness_score_chart.png
```

Generated outputs are local artifacts and are generally ignored by Git. Polished summaries should be copied into `docs/` when they need to be version-controlled.

## Current model dimensions

The model evaluates sites using:

```text
demand
feasibility
safety / review triggers
equity
right-sizing / port recommendation
data confidence
sensitivity
scoring profile comparison
electrical-risk scenarios
```

## Current V2 interpretation after Batch 002 upgrades

The current V2 run shows:

```text
FFX002 — City of Fairfax Regional Library remains the top overall public candidate.
FFX004 — Fairfax County Government Center remains second.
PWC006 — Bull Run Library is the strongest Prince William County Batch 002 site and remains rank 3.
PWC007 — Central Library is a credible Tier 2 candidate.
PWC002 — Neabsco-Potomac Garage remains useful but becomes less attractive under electrical-risk screening because garage context raises review complexity.
PWC008 — Potomac Library remains lower priority because nearby existing charging supply is high.
PWC005 — Haymarket Gainesville Library improves geographic coverage but remains lower priority under current demand signals.
```

## Electrical-risk scenario analysis

The electrical scenario module is located at:

```text
src/run_electrical_risk_scenarios.py
```

It creates three cases:

```text
optimistic_electrical_case
expected_electrical_case
conservative_electrical_case
```

This is a planning screen only. It does not replace utility, facilities, AHJ, Fire Marshal, or engineering review.

The key idea is:

```text
Do not pretend unconfirmed electrical fields are known.
Model them as risk and test whether rankings stay stable.
```

## Current data sources and extracts

Important source extract files include:

```text
data/source_extracts/afdc_ev_supply_counts_v2_batch002_reviewed.csv
data/source_extracts/v2_batch002_parking_review_template.csv
data/source_extracts/v2_batch002_amenities_osm_reviewed.csv
data/source_extracts/v2_next_upgrade_batch.csv
```

Raw official exports may exist locally under:

```text
data/raw_exports/
```

Raw exports are not always committed because they can be large or externally downloaded.

## Current known limitations

The prototype still contains several unconfirmed or scenario-based assumptions:

```text
electrical service rating
spare electrical capacity
emergency disconnect visibility
final charger placement
final parking confirmation
visitor and employee assumptions
site-specific AHJ / Fire Marshal triggers
stormwater and ADA layout details
```

These are not failures. They are exactly the fields the model is designed to surface for future review.

## Recommended next technical options

Option A: add the next candidate batch.

```text
Transit or commuter parking sites would expand the model beyond libraries and government buildings.
```

Option B: improve the right-sizing logic.

```text
Add stronger 2035 / 2050 growth assumptions and show why a site gets 2, 3, or 4 ports.
```

Option C: improve reporting.

```text
Create a polished V2 summary table and a one-command export for presentation-ready outputs.
```

Option D: improve scenario logic.

```text
Add cost-sensitivity or electrical-capacity-specific cases.
```
