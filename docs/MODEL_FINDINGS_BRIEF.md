# Model Findings Brief

## Project purpose

This prototype compares public EV charging candidate sites in Fairfax City and Prince William County.

The model supports early planning. It is not a final approval or construction tool.

## Candidate sites evaluated

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Latest ranked results

```text
1. FFX002 — City of Fairfax Regional Library — 65.3
2. FFX001 — Fairfax City Hall or municipal building — 57.3
3. PWC002 — Neabsco-Potomac Commuter Garage — 56.0
4. PWC004 — Chinn Park Regional Library — 52.7
5. PWC001 — PWC McCoart Government Center — 43.2
6. PWC003 — Prince William County Public Safety Training Center — 29.5
```

## Recommendation tiers

```text
FFX002 — Tier 1
FFX001 — Tier 1
PWC002 — High-review candidate
PWC004 — Tier 2
PWC001 — Tier 3
PWC003 — Low public-priority / special-use
```

## Key stability finding

FFX002 stayed ranked #1 across all five scoring profiles:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

Recommended profile-analysis visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

This chart is the main profile-analysis visual because it is easy to explain: a line staying at `#1` means the site remains the top candidate across scoring-priority views.

Supporting profile visual:

```text
data/outputs/charts/profile_score_heatmap.png
```

## Sensitivity finding

The ranking stayed stable across all five sensitivity scenarios. Every site had `rank_range = 0`.

## Planning conclusion

FFX002 is the strongest current candidate because it is top-ranked in the base model, stable across sensitivity scenarios, and stable across all scoring-priority profiles. FFX001 remains the second strongest candidate. PWC002 and PWC004 remain important but need more confirmation before advancement. PWC003 should not be treated as a general-public charging site unless its access or use case changes.
