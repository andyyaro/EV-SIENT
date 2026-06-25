# V2 First Model Run Notes

## Purpose

This note records the first V2 model run after adding the first new V2 site:

```text
FFX003 — Pohick Regional Library
```

This is a screening run, not a final V2 baseline.

## Command used

```bash
python src/ev_charger_model.py \
  --input data/inputs/real_sites_v2.csv \
  --output data/outputs/v2_site_results.csv \
  --chart data/outputs/charts/v2_readiness_score_chart.png \
  --utilization-chart-dir data/outputs/charts/v2
```

## Run status

The model ran successfully on `data/inputs/real_sites_v2.csv`.

The run produced:

```text
data/outputs/v2_site_results.csv
data/outputs/charts/v2_readiness_score_chart.png
data/outputs/charts/v2/utilization_vs_ports_*.png
```

## V2 ranking after adding Pohick

```text
1. FFX002 — City of Fairfax Regional Library — 65.3 — Tier 1
2. FFX001 — Fairfax City Hall or municipal building — 57.3 — Tier 1
3. PWC002 — Neabsco-Potomac Commuter Garage — 56.0 — High-review candidate
4. PWC004 — Chinn Park Regional Library — 52.7 — Tier 2
5. FFX003 — Pohick Regional Library — 46.8 — Tier 2
6. PWC001 — PWC McCoart Government Center — 43.2 — Tier 3
7. PWC003 — Prince William County Public Safety Training Center — 29.5 — Low public-priority / special-use
```

## Interpretation

Pohick entered the model in the middle of the current candidate set.

This is a reasonable first result. It did not displace the strongest V1 candidates, and it did not rank unrealistically high.

Pohick is currently a promising but still preliminary V2 site.

## Pohick result details

```text
site_id: FFX003
site_name: Pohick Regional Library
model_rank: 5
readiness_score: 46.8
data_confidence_score: 59.0
data_confidence_level: Medium
recommendation_tier: Tier 2 — promising candidate, refine data
recommended_ports_now: 2
recommended_ports_2035: 2
recommended_ports_2050: 2
review_reason: Emergency disconnect visibility not confirmed
```

## Why Pohick is not a top site yet

The main reason is weaker demand signal compared with the top-ranked sites.

Pohick demand subscore:

```text
36.7
```

For comparison:

```text
FFX002 demand subscore: 57.0
FFX001 demand subscore: 54.9
PWC002 demand subscore: 67.3
PWC004 demand subscore: 51.5
```

So Pohick is not bad. It is simply not as strong as the current top candidates under the present assumptions.

## What to improve before a V2 baseline

Before turning this into a baseline result, replace the most important assumptions for Pohick:

```text
nearby_households_1mi
nearby_jobs_1mi
aadt_nearest
amenities_count_0_5mi
equity_gap_index
ev_registrations_local
ev_share_local
employees_day
visitors_day
distance_to_service_ft
trenching_ft
service_upgrade_cost_usd
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
```

## Recommended next move

Do not create a V2 baseline yet.

Next, rerun the backlog triage so the next cleanup target rises after V2C003/Pohick has been marked as added.

Then clean up the next 2–3 strongest backlog candidates before running a broader V2 comparison.
