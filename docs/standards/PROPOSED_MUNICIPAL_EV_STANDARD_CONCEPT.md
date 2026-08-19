# Proposed Standard Concept - "Municipal EV Charging Site Readiness and Emergency Access Standard"

> **Label required on every use:** This is a **Future City Fellowship design exercise, not an official UL/ULSE proposal.** It has no regulatory force. Every provisional parameter marked **TBV** requires validation by ULSE, the manufacturer, the adopted code, or the local AHJ before any real-world use.

**Project:** Future City Fellowship - Milestone 2 (Fairfax City + Prince William County, VA) · **Date:** 2026-07-19
**Basis:** Report 06 §4 (merged MCDA concept C2+C1); appendix `PROPOSED_STANDARD_RESEARCH_SPECIFICATION.md` (**cited but never produced - no such file exists in this repository or its history; noted 2026-07-28 rather than the citation being quietly deleted, because a reader following it deserves to know it leads nowhere**); fellowship requirement for one proposed standard with tests (EX01, IM-09).
**Integrity rule:** No numeric safety limit is invented in this document. Sourced parameters cite the adopted code by name and edition; everything else is marked **TBV by ULSE/AHJ/manufacturer/adopted code**.

---

## 1. Purpose and rationale

Municipal charging sites fail for reasons existing product standards do not test: responders who cannot find or operate a disconnect (client evidence, Adams interview), sites overbuilt then decommissioned (Neabsco; 17 stations removed), ADA layouts reworked after design freeze (fleet hub, one year lost), and load-management systems whose behavior on communications loss is undocumented. UL 2594 certifies the *equipment*; this concept addresses the *site*. It fills the gap between product listing (UL 2594/2231), installation code (NEC 625 as adopted), and fire code (SFPC) with a site-level readiness and verification framework a municipality can operate.

## 2. Scope and applicability

- **Covered:** publicly owned or operated EV charging sites in municipal jurisdictions; new construction and retrofit; AC Level 1/2 EVSE; sites with or without parking structures.
- **Reserved annexes (out of core scope):** DC fast charging (would invoke UL 2202); battery energy storage (defer entirely to UL 9540/9540A + NFPA 855); private/residential charging; fleet-only depots (adaptation note only).
- **Lifecycle stages covered:** site selection → design → commissioning → operations/monitoring → expansion → decommissioning.

## 3. Modules and test/verification tables

### Module 1 - Emergency access and disconnect (flagship)

| Test category | Verification method | Parameter basis |
|---|---|---|
| Apparatus approach | Measured approach route to each EVSE cluster | Dimensions per adopted fire-code access provisions - **sourced: 2021 Virginia SFPC as adopted (eff. 2024-01-18)**; cite the adopted edition in force at test time |
| Disconnect location and labeling | Visual inspection + label legibility at distance | Disconnect provisions - **sourced: NEC Article 625 as adopted in Virginia (2020 NEC via 2021 USBC)**; legibility distance **TBV by ULSE/AHJ** |
| Disconnect operation | Timed operation drill by a non-specialist responder | Target time **TBV by ULSE/AHJ** (responder time-study literature identified as pre-maturation research need) |
| Illumination of disconnect and signage | Light-level measurement at night | Level **TBV by ULSE/AHJ**; reference existing egress-lighting practice in the adopted code, do not invent a lux value |
| Responder information placard | On-site placard audit: system type, power, shutdown steps, 24/7 contact | Content checklist **sourced from fire-department pre-plan practice**; format **TBV by ULSE/AHJ** |

### Module 2 - Expandability and right-sizing documentation

| Test category | Verification method | Parameter basis |
|---|---|---|
| Pathway capacity declaration | Documented conduit/panel/space capacity vs. active ports, on file and current | Engineering documentation review - no numeric threshold invented |
| Utilization monitoring capability | Site demonstrates per-port session/energy reporting (OCPP data export) | **Sourced protocol (OCPP - not a ULSE standard)**; data minimums **TBV** (benchmark against federal NEVI uptime/reporting practice before maturation) |
| Expansion triggers | Written, measurable trigger policy exists, including an equity override | Policy audit - trigger values are **municipality-set**, not standard-set |
| Overload protection coordination | Service-capacity documentation vs. total EVSE rating | **Sourced: NEC load-calculation provisions as adopted (2020 NEC via 2021 USBC)** |

### Module 3 - Accessibility and site-condition cross-references

| Test category | Verification method | Parameter basis |
|---|---|---|
| Accessible route/space/reach | Dimensional check | **By reference to US Access Board EVSE guidance (TA 2022; NPRM 2024-09-03, still at NPRM as of 2026-07-19 - IM-02) and VA USBC ADA provisions in force** - no duplicate scoping |
| Impact protection | Bollard/wheel-stop placement inspection | **Sourced: adopted code provisions**; no dimensions invented |
| Enclosure/garage conditions | Ventilation/access review trigger for enclosed sites | Defer to AHJ review - checklist only (one enclosed candidate: PWC002 Neabsco) |
| Stormwater/firewater | Drainage/containment plan on file | **Sourced locally: VSMP-delegated local stormwater program requirements** |

### Module 4 - Monitoring and expansion triggers

| Test category | Verification method | Parameter basis |
|---|---|---|
| Dual-path data logging | Network data and independent local meter both operating; monthly export to municipality-owned storage demonstrated | Governance practice (Report 07 mitigation #4); retention period **TBV by municipality records rules** |
| Trigger evidence chain | Each expansion decision on file traces to observed utilization data | Decision-log audit - process requirement, no thresholds |
| Data staleness control | Every published figure carries source date; refresh checklist executed | Documentation audit; refresh interval **TBV by municipality** (annual minimum recommended for grid factors) |

### Module 5 - Managed-charging fail-safe

| Test category | Verification method | Parameter basis |
|---|---|---|
| Comms-loss behavior | Disconnect network link; observe EVSE output settles to documented default-safe profile | Functional test; safe-state output value **TBV by manufacturer/adopted code** - never exceeding the NEC-calculated circuit limit (**sourced: 2020 NEC as adopted**) |
| Hardwired protection independence | Overcurrent protection operates with all software/network disabled | **Sourced: NEC baseline requirement (2020 NEC as adopted)** - non-negotiable |
| Local fallback service | Non-networked minimum charging service demonstrated | Vendor capability test; service level **TBV by manufacturer** |

### Module 6 - Commissioning and evidence package

| Test category | Verification method | Parameter basis |
|---|---|---|
| Listing verification | UL 2594 listing marks and UL 2231 personnel-protection scope confirmed on installed units | **Sourced: UL 2594 3rd ed. (2022-12-15); UL 2231-1/-2 2021 eds.** |
| Inspection records | Permit + passed electrical inspection + fire review sign-off on file | **Sourced: 2021 Virginia USBC/SFPC process** |
| Module test records | M1–M5 verification results compiled in a single site evidence package | Checklist - completeness, not thresholds |
| Fire-department pre-plan | Walkthrough with Fire Marshal completed and documented | Fire-service practice; scheduling **TBV by AHJ** |

### Module 7 - Materials, take-back, and end of life

| Test category | Verification method | Parameter basis |
|---|---|---|
| Circularity disclosure | Vendor disclosure on file: recycled content, repairability, spare-part availability, warranty, take-back | **Sourced framing: UL 3600 (1st ed., 2023-01-09)** - reporting categories, not invented thresholds |
| Take-back/recycling route | Documented route for EVSE electronics e-waste | Documentation review |
| Replacement planning | ~10-year electronics refresh horizon documented (industry practice benchmark, EX15 class); pathway designed to outlive electronics | Planning-document review; exact interval **TBV by manufacturer** |
| Decommissioning plan | Removal, circuit decommissioning per code, site restoration plan on file | **Sourced: NEC as adopted** for circuits; template: the county's own 17-station decommissioning experience |

## 4. Conformance levels

| Level | Requirements |
|---|---|
| **Ready-Basic** | Module 1 pass + Module 3 accessibility pass + Module 6 evidence package complete |
| **Ready-Expandable** | Ready-Basic + Modules 2 and 7 documentation complete |
| **Ready-Managed** | Ready-Expandable + Modules 4 and 5 demonstrated (fail-safe test passed, dual-path monitoring live) |

The staged pilot targets **Ready-Managed** at pilot sites, because the pilot's decision value depends on monitoring continuity (Report 07 §3).

## 5. Inspection intervals (provisional - TBV by ULSE/AHJ)

| Event / interval | Scope |
|---|---|
| Commissioning | All modules (full evidence package) |
| Annually | Module 1 (labels, lighting, access route); Module 4 data-continuity check; Module 7 circularity report |
| On any expansion event | Module 2 re-verification (pathway declaration vs. new port count) |
| On code-edition change (e.g., conclusion of Virginia's 2024 code cycle ≈2027, or Access Board final rule) | Module 3 cross-references re-checked |

## 6. Research still needed before this concept could mature

1. Adopted-edition citation compilation per jurisdiction (the 2024 Virginia cycle will change the base ≈2027 - IM-03).
2. Responder time-study literature to ground the Module 1 disconnect-operation target.
3. Monitoring-data minimums benchmarked against federal NEVI uptime/reporting requirements.
4. ULSE feedback channel (Standards Academy contact) on concept viability - **as a fellowship learning exercise, not a submission.**

> **Repeat label:** This is a Future City Fellowship design exercise, not an official UL/ULSE proposal. All TBV parameters require validation by ULSE, the AHJ, the manufacturer, or the adopted code.
