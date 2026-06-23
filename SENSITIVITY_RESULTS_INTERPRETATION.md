# Sensitivity Results Interpretation

## Latest run

The latest sensitivity run used five scenarios:

```text
very_low_demand_high_cost
low_demand_high_cost
base_case
high_demand_base_cost
very_high_demand_low_cost
```

The purpose was to test whether the ranking changes when V1 assumptions are pushed below and above the base case.

## Main finding

The ranking remained stable across all five scenarios.

```text
Every site had rank_range = 0.
```

This means each candidate site kept the same rank under the tested downside, base, and upside assumptions.

## Stable ranking across scenarios

```text
1. FFX002 — City of Fairfax Regional Library
2. FFX001 — Fairfax City Hall or municipal building
3. PWC004 — Chinn Park Regional Library
4. PWC002 — Neabsco-Potomac Commuter Garage
5. PWC001 — PWC McCoart Government Center
6. PWC003 — Prince William County Public Safety Training Center
```

## Score ranges

```text
FFX002 — 58.8 to 61.4, range 2.6
FFX001 — 52.2 to 54.5, range 2.3
PWC004 — 45.8 to 47.6, range 1.8
PWC002 — 42.4 to 44.4, range 2.0
PWC001 — 39.6 to 41.1, range 1.5
PWC003 — 18.6 to 18.8, range 0.2
```

## Interpretation

The current ranking is stable under the tested V1 uncertainty scenarios.

The strongest current candidate is FFX002 because it stays first in every scenario and has the highest average readiness score.

FFX001 is also stable as the second-ranked site.

PWC004 remains the strongest Prince William County library/public-service site in the current model.

PWC002 has stronger demand and equity signals than some other PWC sites, but its garage context and higher planning feasibility burden keep it below PWC004 in every tested scenario.

PWC001 remains below PWC004 and PWC002 because its planning install-cost burden is higher and its equity contribution is lower.

PWC003 remains last because it is limited or non-public access and has low surrounding public-charging demand indicators.

## Port-planning observations

The ranking is stable, but recommended ports still change by scenario.

Examples:

```text
FFX002 moves from 1 current port in lower-demand scenarios to 2 current ports in higher-demand scenarios.
PWC004 moves from 1 current port in lower/base scenarios to 2 current ports in the very high demand / low cost scenario.
PWC002 generally stays at 2 current ports, but reaches 3 ports by 2050 in the very high demand / low cost scenario.
PWC001 reaches 3 ports by 2050 in the very high demand / low cost scenario.
```

This means the priority ranking is stable, but right-sizing still depends on demand growth assumptions.

## Important caution

This result does not prove the ranking is final.

It only means the ranking is stable under the five V1 scenarios currently tested. The model still needs better confirmed data for:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open
parking_spaces
amenities_count_0_5mi
local EV adoption counts
```

## Planning conclusion

For the current prototype, FFX002 and FFX001 are stable top candidates. PWC004 is the strongest current Prince William County public library candidate. PWC002 should remain in the discussion because of its equity and commuter-garage role, but it needs deeper garage/fire/electrical review before it can be treated as a straightforward implementation site.
