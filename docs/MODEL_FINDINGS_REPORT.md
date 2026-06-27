# Model Findings Report

## Project purpose

This prototype is a planning-support model for public EV charging site readiness and right-sizing in Fairfax City and Prince William County.

The model helps answer:

```text
1. Which candidate sites look strongest?
2. How many starter charging ports should be considered?
3. How much future-ready capacity should be planned for 2035 and 2050?
4. How complete or confirmed is the current data?
5. What should be checked next before a site advances?
6. Do port recommendations remain stable under alternate demand and charging assumptions?
```

The model supports early planning. It is not a final approval, procurement, permitting, engineering, or construction tool.

## Main public visual artifact

The primary public-facing visual artifact is the Tableau workbook:

[Open the EV Charging Site Readiness Workbook](https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite)

Use the visible sheet tabs in Tableau Public to navigate the full workbook.

Static PNG charts remain useful for reproducibility, GitHub previews, and the technical deliverable package, but Tableau is the main public visual layer.

## Candidate sites evaluated

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

## Scoring method

Each site receives planning subscores for demand, feasibility, safety/review context, and equity.

The final readiness score uses this weighting:

```text
readiness_score = 0.45*demand + 0.30*feasibility + 0.15*safety + 0.10*equity
```

Readiness score shows how promising a site looks under current assumptions. Data confidence is separate and shows how complete or confirmed the input data is.

## Current ranked results

```text
1. FFX002 — City of Fairfax Regional Library — readiness 58.8 — Tier 1
2. FFX004 — Fairfax County Government Center — readiness 54.4 — Tier 1
3. PWC006 — Bull Run Library — readiness 52.1 — Tier 2
4. FFX001 — Fairfax City Hall or municipal building — readiness 51.0 — Tier 2
5. PWC002 — Neabsco-Potomac Commuter Garage — readiness 50.3 — High-review
6. PWC007 — Central Library — readiness 50.2 — Tier 2
7. PWC004 — Chinn Park Regional Library — readiness 48.6 — Tier 2
8. FFX003 — Pohick Regional Library — readiness 46.8 — Tier 2
9. PWC008 — Potomac Library — readiness 40.1 — Tier 3
10. PWC001 — PWC McCoart Government Center — readiness 39.8 — Tier 3
11. PWC005 — Haymarket Gainesville Library — readiness 36.9 — Tier 3
12. PWC003 — Prince William County Public Safety Training Center — readiness 29.6 — special-use
```

## Recommendation interpretation

```text
FFX002 — strongest current public candidate
FFX004 — second-ranked Tier 1 candidate
PWC006 — strongest current Prince William County library candidate
PWC002 — useful high-review garage candidate
PWC003 — special-use / low public-priority unless the use case changes
```

## Current right-sizing interpretation

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

## Port-sizing scenario result

```text
The future-ready capacity plan is stable across the first five tested scenarios.
Base, high-growth, long-session, short-window, and peakier-demand scenarios do not exceed future-ready capacity.
Only the combined-stress scenario creates one-port gaps.
The combined-stress gaps affect PWC002 and PWC008.
```

## Cross-checks supporting the result

```text
1. Base model ranking: FFX002 ranked #1.
2. Scoring-profile analysis: FFX002 remains the strongest current public candidate across priority profiles.
3. Port-sizing scenario analysis: future-ready capacity is stable except under combined stress for PWC002 and PWC008.
4. Right-sizing validation: recommendations remain planning-screen outputs and still require site confirmation.
```

## Remaining data gaps

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

## Planning conclusion

FFX002 is the strongest current public candidate. FFX004 is the second-ranked Tier 1 candidate, and PWC006 is the strongest current Prince William County library candidate. PWC002 should remain in discussion but only as a high-review garage candidate. PWC003 should not be treated as a general-public site unless its access or use case changes.

The model should be used to prioritize follow-up questions and site screening, not to authorize construction, procurement, or final site selection.
