# Results Interpretation

This file explains the current V2 model result in plain English.

For the freshest local run, prefer the generated file:

```text
data/outputs/v2_results_interpretation.md
```

For the main interactive visual, use the Tableau workbook documented in:

```text
tableau/README.md
```

## Latest ranking

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

## Main interpretation

FFX002 is the strongest current public candidate. It combines a library use case, strong surrounding demand signals, and a manageable starter-install recommendation. Its action remains cautious: verify key data and complete site screening before advancement.

FFX004 is the second-ranked Tier 1 candidate. It has strong civic demand context and future-ready planning value, but it still needs site-level confirmation.

PWC006 is the strongest current Prince William County library candidate.

PWC002 remains useful but high-review because garage installations can create additional review questions around access, routing, emergency response, electrical capacity, and operator coordination.

PWC003 is low public-priority because it is limited or non-public access and has weak surrounding public-demand indicators. Its next step is not advancement; the project first needs to decide whether it is public, fleet-only, special-use, or removed from the public-candidate list.

## Port-sizing scenario interpretation

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Only the combined-stress scenario creates one-port gaps, affecting PWC002 and PWC008.
```

Plain-English meaning: the future-ready plan is not fragile under normal tested variations, but PWC002 and PWC008 should be watched if multiple stress assumptions happen at once.

## Right-sizing interpretation

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

## What the result does not mean

The result does not mean a site is ready to build. It means a site is a stronger or weaker early planning candidate under the current data and assumptions.

The action matrix and decision quadrant are designed to prevent overclaiming. They turn readiness, confidence, complexity, and scenario behavior into next-step labels, not project approvals.

Any real project would still need utility, engineering, accessibility, permitting, procurement, stakeholder, and site-owner review.
