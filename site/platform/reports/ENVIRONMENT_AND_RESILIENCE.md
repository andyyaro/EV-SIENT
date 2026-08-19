# Environment and Resilience

**Project:** Future City Fellowship - Milestone 2, staged municipal EV charging (Fairfax City + Prince William County, VA)
**Date:** 2026-07-19 · **Basis:** Report 08; EX09, EX10, EX14, EX15; IM-01, IM-02.
**Claims discipline:** every environmental number in this project carries a baseline definition, a factor vintage, and an assumption list. Values below labeled "benchmark" or "provisional" are planning inputs, not measurements.

---

## 1. Site-relevant environmental conditions

| Condition | Finding | Design implication |
|---|---|---|
| **Heat** | Northern Virginia urban heat-island exposure is rising; parking-lot siting adds hard surface (Report 08, reasoned inference from regional climate data classes) | Equipment temperature ratings specified at procurement; shading/landscaping held as a design-stage option |
| **Heavy precipitation / flooding** | Regional heavy-rain intensity increasing; site-level exposure requires a FEMA flood-layer check per candidate - not yet performed (implementation-phase step) | FEMA layer check added to site screening (risk R09); stormwater screen already in the model |
| **Stormwater** | Both jurisdictions run VSMP-delegated local stormwater programs (Report 10 §1) | Drainage/firewater-containment plan per site, reviewed by City Public Works (Fairfax) / PWC Environmental Services |
| **Outages / severe weather** | Charging is unavailable during grid outages. **No battery storage is in scope (`battery_storage_flag=0` at all 12 sites), and therefore this project makes NO resilience claim.** Storage is noted only as a future option that would invoke UL 9540/9540A and NFPA 855. | Outage exposure is accepted at pilot scale; stated plainly in all materials |
| **Regional grid context** | PWC data-center load growth dominates the regional electricity story; county 2030 trajectory off-track per client (EX14 context). EV charging at pilot scale is small next to data-center load - a humility point, not a dismissal. | Aligns claims to the adopted PWC CESMP targets (50% GHG cut vs 2005 by 2030; 100% renewable county-gov electricity by 2030; county-wide 2035; carbon-neutral county ops 2050 - EX14), citing the plan rather than generic goals |

## 2. Grid emissions factor (authoritative value for all implementation artifacts)

- **Factor: 596.3 lb CO2e/MWh** - SRVC subregion total output emission rate, **eGRID2023 Rev 2** (data year 2023; initial release 2025-01-15; Rev 2 released 2025-06-12). Source: EPA eGRID summary data (**IM-01**).
- Correction note: the research package (EX10) carried ≈590.2; the implementation run verified EPA's published SRVC CO2e total output rate as 596.326 lb/MWh. **596.3 with vintage label is the value used everywhere in this implementation.**
- **Annual refresh:** eGRID is updated annually; eGRID2024 preliminary data exists via API (≈−1.8% CO2e average) but is not the official release and is not used. The model carries an annual-refresh field; every chart states the factor vintage (risk R12).
- The factor is expected to decline as the grid decarbonizes under the VCEA trajectory - cited as a tailwind, never invented as a number.

## 3. Net-CO2e model (the quantified environmental metric, Report 08 winner M2)

Net avoided CO2e = displaced tailpipe emissions − charging-related grid emissions:

1. Annual kWh delivered per horizon (2036/2046/2056) from modeled sessions × energy per session (scenario table inputs, all labeled).
2. Charging grid emissions = kWh × 596.3 lb CO2e/MWh (eGRID2023 Rev 2 SRVC, refreshed annually).
3. Displaced tailpipe emissions = (kWh ÷ EV efficiency benchmark) × displaced-vehicle gCO2/mile (EPA fleet-average **benchmark assumptions, labeled as such**).
4. Net = displaced − grid. Reported per horizon with the full assumption list.

"Electrification is not automatically zero-carbon" stays in the narrative - the 2024 regional capacity mix (36.2% gas, 14.5% nuclear, 11.5% coal, ~15.7% renewables incl. purchases, 0.1% battery; verified local workbook, Report 08) supports it. The paired resource-management metric (M4, avoided unnecessary active EVSE) carries the materials story grounded in the county's own decommissioning record.

## 4. Materials, circularity, and end of life (UL 3600 framing)

- **Procurement:** vendor circularity disclosure per the UL 3600 (1st ed., 2023-01-09, IM-05) reporting frame - recycled content, repairability, spare-part availability, warranty length, take-back program existence. Voluntary standard; adherence evidence is the per-site/program reporting sheet.
- **Repairability:** commonly-listed hardware with spare-parts clauses (risk R15); repair-over-replace preference documented in the maintenance plan.
- **Trenching minimization is also embodied-impact minimization:** conductor (copper/aluminum) and concrete quantities scale with trenching distance, so the model's trenching-distance criterion simultaneously reduces cost (McCoart evidence) and embodied materials. This point is stated explicitly in the presentation.
- **Replacement cycle:** ~10-year EVSE electronics refresh (industry practice **benchmark**, not a measured local value); pathway civil works (conduit, panel capacity) outlive the electronics - a further staged-deployment advantage.
- **Take-back/recycling:** documented route for EVSE electronics as e-waste; no traction-battery or storage-battery handling is in scope (no storage).
- **Decommissioning:** the county has already decommissioned 17 charging stations (~$20k/yr avoided keep-online cost, client evidence); that institutional experience is the template for the decommissioning plan required in proposed-standard Module 7.

## 5. Resilience statement (explicit)

**No resilience claim is made in this project.** There is no battery storage at any of the 12 candidate sites, charging depends on grid availability, and severe-weather outages will interrupt service. Any future storage addition would be a scope change invoking UL 9540/9540A and NFPA 855 (2026 ed.) and a new AHJ review - at which point resilience could be evaluated, not before.
