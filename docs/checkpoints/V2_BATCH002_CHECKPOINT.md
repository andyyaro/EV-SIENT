# V2 Batch 002 Checkpoint

## Scope

This checkpoint summarizes the V2 Batch 002 upgrade for the Public EV Charging Site-Readiness and Right-Sizing Model.

Batch 002 added and refined four Prince William County library candidates:

```text
PWC005 — Haymarket Gainesville Library
PWC006 — Bull Run Library
PWC007 — Central Library
PWC008 — Potomac Library
```

## Public-data upgrades applied

The following data categories have been upgraded or reviewed for the four Batch 002 library candidates:

```text
Official address / hours / location reference
Coordinates from official map references or map review
ACS household estimates
LODES workplace jobs estimates
VDOT traffic screening values
ACS-based equity index
Reviewed OSM amenities categories
AFDC / NREL EV charging supply counts
Draft parking estimates from map review
```

## Draft parking estimates applied

```text
PWC005 — 85 spaces
PWC006 — 150 spaces
PWC007 — 63 spaces
PWC008 — 150 spaces
```

These are draft map-review estimates. They should be replaced later if an official parking count or stakeholder-confirmed value becomes available.

## Current V2 ranking after Batch 002 upgrades

```text
Rank 1  FFX002 — City of Fairfax Regional Library — 58.8 — Tier 1
Rank 2  FFX004 — Fairfax County Government Center — 54.4 — Tier 1
Rank 3  PWC006 — Bull Run Library — 52.1 — Tier 2
Rank 4  FFX001 — Fairfax City Hall or municipal building — 51.0 — Tier 2
Rank 5  PWC002 — Neabsco-Potomac Commuter Garage — 50.3 — High-review
Rank 6  PWC007 — Central Library — 50.2 — Tier 2
Rank 7  PWC004 — Chinn Park Regional Library — 48.6 — Tier 2
Rank 8  FFX003 — Pohick Regional Library — 46.8 — Tier 2
Rank 9  PWC008 — Potomac Library — 40.1 — Tier 3
Rank 10 PWC001 — PWC McCoart Government Center — 39.8 — Tier 3
Rank 11 PWC005 — Haymarket Gainesville Library — 36.9 — Tier 3
Rank 12 PWC003 — Prince William County Public Safety Training Center — 29.6 — special-use
```

## Interpretation

Bull Run Library is the strongest Batch 002 candidate and is stable as a top-3 V2 site. It remains a Tier 2 candidate because electrical service, spare capacity, emergency disconnect visibility, and final parking evidence still require confirmation.

Central Library remains a credible Tier 2 candidate. It is close to Neabsco-Potomac Garage in score, but it carries fewer garage/fire-review complications.

Potomac Library has strong nearby activity and amenities, but AFDC supply counts show substantial existing nearby public charging, which reduces its unmet-need signal in the current model.

Haymarket Gainesville Library improves geographic coverage for western Prince William County but remains lower priority under the current scoring because its demand and surrounding activity signals are weaker than the stronger candidates.

## Sensitivity result

The Batch 002 rankings are stable under the current sensitivity scenarios:

```text
FFX002 stays rank 1.
FFX004 stays rank 2.
PWC006 stays rank 3.
PWC007 stays rank 6.
PWC008 stays rank 9.
PWC005 stays rank 11.
```

This means the current conclusions are not highly fragile under the tested scoring assumptions.

## Remaining unconfirmed fields

The main remaining unconfirmed fields across the candidate set are:

```text
Electrical service rating
Spare capacity or upgrade need
Emergency disconnect location / visibility
Final parking confirmation
Visitor / employee assumptions
Potential charger placement constraints
```

## Recommended next action

The next technical step should be a V2 electrical-feasibility refinement pass. This can be handled as a scenario-based approximation rather than pretending to know exact utility/service capacity.

Recommended approach:

```text
Create low / medium / high electrical-feasibility scenarios.
Estimate service upgrade risk from site type, distance-to-service, trenching, and likely panel/service limitations.
Preserve AHJ / Fire Marshal / electrical review flags instead of treating assumptions as final.
Rerun the V2 workflow and compare rankings.
```
