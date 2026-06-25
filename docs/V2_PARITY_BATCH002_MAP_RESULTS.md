# V2 Parity Batch 002 — Readiness Map Results

## Status

The V2 readiness-map parity batch ran successfully.

The V2 workflow now generates a V2-specific readiness map, and the V2 output checker passed after the map was added.

## Confirmed workflow section

The successful run included:

```text
10. Create V2 readiness map
```

## Confirmed generated map output

```text
data/outputs/charts/v2_site_readiness_map.png
```

## Confirmed map inputs

The map step used:

```text
--input data/inputs/real_sites_v2.csv
--results data/outputs/v2_site_results.csv
--sensitivity data/outputs/v2_sensitivity_summary.csv
--profile-results data/outputs/v2_profile_results.csv
--output data/outputs/charts/v2_site_readiness_map.png
```

## Map interpretation note from the run

```text
FFX002 is #1 in the base model; sensitivity ranks stayed stable. Profile results show the priority tradeoffs.
```

## Planning notes from the run

```text
PWC002 = high-review garage candidate
PWC003 = public-access decision needed
PWC008 = monitor due to nearby charging supply
PWC006 = strongest current PWC library candidate
```

## Sites plotted

The map plotted all 12 V2 candidate sites:

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
FFX003 — Pohick Regional Library
FFX004 — Fairfax County Government Center
PWC005 — Haymarket Gainesville Library
PWC006 — Bull Run Library
PWC007 — Central Library
PWC008 — Potomac Library
```

## Output checker status

```text
V2 OUTPUT CHECK
Status: PASSED
```

## Remaining V1-to-V2 parity items

After this batch, the main remaining parity items are:

```text
Markdown run summary
V2 success marker / output manifest
V2 baseline comparison
optional deliverable package / demo-mode parity
```

## Recommended next step

The next best parity step is the Markdown run summary, because V1 generates a run summary and V2 currently generates the interpretation report but not a separate V2 run-summary file.
