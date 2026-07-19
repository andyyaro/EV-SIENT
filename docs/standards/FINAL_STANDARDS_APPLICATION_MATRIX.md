# Final Standards Application Matrix

**Project:** Future City Fellowship — Milestone 2, staged municipal EV charging (Fairfax City + Prince William County, VA)
**Date:** 2026-07-19 · **Status:** Design intent only — no permit has been applied for, no equipment has been procured, and nothing in this matrix constitutes achieved compliance. Adopted-edition interpretations and all permit determinations rest with the local Authority Having Jurisdiction (AHJ).
**Consistency note:** This matrix is the narrative rendering of the machine register `data/contract/v1/standards_register.csv` (identical standards set, roles, editions, and applicability flags for all 12 candidate sites).
**Evidence:** EX01, EX03–EX09, EX16 (external evidence register); IM-02, IM-03, IM-04, IM-05, IM-10 (current-facts source register, verified 2026-07-19).

---

## 1. Standards set at a glance

| Standard / instrument | Role in this plan | Adopted / governing edition (Virginia, 2026-07-19) | Latest published edition | Applicability at the 12 candidate sites |
|---|---|---|---|---|
| **UL 2594** — Electric Vehicle Supply Equipment (AC L1/L2, ≤1000 V) | **Highlighted safety standard** | 3rd ed., 2022-12-15 (IM-04, EX03) | 3rd ed. (revision activity through 2025) | Active — governs the exact equipment class proposed (AC Level 2) |
| **UL 3600** — Measuring and Reporting Circular Economy Aspects | **Highlighted sustainability standard** (voluntary) | 1st ed., 2023-01-09 (IM-05, EX06) | 1st ed., 2023-01-09 | Active — program-level circularity reporting frame |
| UL 2231-1/-2 — Personnel Protection Systems for EV Supply Circuits | Essential supporting (embedded in EVSE listing) | 2021 editions (IM-10, EX04) | 2021 editions | Active — required by NEC listing practice for EVSE |
| NEC Article 625 (NFPA 70) as adopted in Virginia | Essential supporting — installation law | **2020 NEC**, via 2021 USBC, effective 2024-01-18 (IM-03, EX07) | 2023 NEC published; **not adopted in Virginia** | Active — installation law for every EVSE circuit |
| Virginia USBC / SFPC | Essential supporting — permitting and fire-review lanes | 2021 editions, effective 2024-01-18; permits solely under 2021 USBC since 2025-01-18; 2024 code-development cycle underway, expected conclusion ≈2027 (IM-03) | 2021 (2024 cycle in development) | Active — building permit, electrical inspection, fire review at every site |
| US Access Board EVSE accessibility guidance | Essential supporting — accessibility | VA USBC ADA provisions in force today; Access Board TA document (2022); **rule still at NPRM stage** (published 2024-09-03, no final rule as of 2026-07-19; DOJ rulemaking would follow) (IM-02, EX09) | NPRM 2024-09-03 | Active — design to TA guidance now; documented local cost/schedule driver (EX09; client evidence) |
| OCPP + ISO 15118 | Supporting interoperability **protocols — explicitly NOT ULSE standards** (EX16) | Current industry versions (contractual, not code-adopted) | Current industry versions | Active — managed charging, network portability, fail-safe behavior |
| UL 2202 — EV (DC) Charging System Equipment | **Conditional** | 2022 edition (IM-10, EX03) | 2022 edition | **Out of scope** — applies only if DC fast charging is added; no DCFC in the current plan |
| UL 9540 / UL 9540A + NFPA 855 — energy storage | **Conditional** | UL 9540A 5th ed., 2025-03-12 (6th-ed. activity 2026); NFPA 855 2026 ed. (IM-10, EX05) | Same | **Out of scope** — applies only if battery storage is added; `battery_storage_flag=0` at all 12 sites |

**Adopted-vs-latest discipline (must be stated in every presentation):** Virginia enforces the **2020 NEC** through the 2021 USBC. The 2023 NEC exists but is not law in Virginia; designing or presenting to a non-adopted edition invites AHJ rejection. The 2024 Virginia code-development cycle is underway (expected conclusion ≈2027), so the adopted basis must be re-verified at design time (IM-03).

---

## 2. Lifecycle application matrix

Legend: each cell states what the standard requires or contributes at that stage. "—" = the standard has no distinct role at that stage.

### 2.1 UL 2594 (highlighted safety standard)

| Stage | Application |
|---|---|
| Design | Specify UL 2594-listed EVSE only; design listed-equipment installation per NEC 625 as adopted (2020 NEC) |
| Procurement | Listing/certification marks (NRTL) required in bid documents |
| Certification | Certification is the manufacturer's, via NRTL listing — the municipality verifies the listing, it does not certify equipment |
| Installation | Listed-equipment installation conditions honored (mounting, environment, clearances per listing) |
| Commissioning | Verify listing marks and personnel-protection function before energization sign-off |
| Operation | Maintain per listing conditions; no field modifications that void the listing |
| Emergency response | Listed equipment supports predictable de-energization behavior |
| End of life | Removal without compromising remaining listed circuits (see NEC 625 row) |
| Evidence of adherence | Certification/listing records in the procurement file; electrical inspection sign-off |
| Deciding authority | Manufacturer NRTL listing + local building official |
| Open questions | None specific; edition interpretation rests with the AHJ |

### 2.2 UL 3600 (highlighted sustainability standard — voluntary)

| Stage | Application |
|---|---|
| Design | Materials and repairability considered in equipment selection |
| Procurement | Vendor circularity disclosure required: recycled content, repairability, spare-part availability, take-back program |
| Certification | Not a certification play — UL 3600 is a measurement/reporting standard; adherence is self-reported per its framework |
| Installation | — |
| Commissioning | Baseline circularity reporting sheet opened per site |
| Operation | Annual circularity reporting for the charging program |
| Emergency response | — |
| End of life | Take-back/recycling route documented and executed; feeds decommissioning record |
| Evidence of adherence | UL 3600-style circularity reporting sheet per site/program |
| Deciding authority | Program owner (sustainability office); voluntary standard — no AHJ role |
| Open questions | None (voluntary reporting standard) |

### 2.3 UL 2231-1/-2 (essential supporting — personnel protection)

| Stage | Application |
|---|---|
| Design | Embedded in listed EVSE per NEC listing practice — not separately designed |
| Procurement | Confirm the EVSE listing includes UL 2231 personnel protection |
| Certification | Carried inside the manufacturer's UL 2594 listing |
| Installation | — (embedded) |
| Commissioning | GFCI/CCID protection functional verification |
| Operation | Periodic protection test per the maintenance plan |
| Emergency response | Shock/fault protection is the standard's core function (interface 4 in the integration architecture) |
| End of life | — |
| Evidence of adherence | Listing detail; commissioning functional test record |
| Deciding authority | NRTL listing + electrical inspector |
| Open questions | None |

### 2.4 NEC Article 625 as adopted in Virginia (2020 NEC via 2021 USBC)

| Stage | Application |
|---|---|
| Design | Load calculations, disconnect provisions, circuit design per the adopted 2020 NEC |
| Procurement | Circuit components and disconnects specified to adopted-code requirements |
| Certification | Not applicable (code, not product standard); compliance shown at inspection |
| Installation | Installation law for every EVSE circuit — permits required |
| Commissioning | Electrical inspection approval |
| Operation | Circuits maintained per code; modifications re-permitted |
| Emergency response | Disconnect location/labeling per adopted provisions |
| End of life | Circuit decommissioning per code |
| Evidence of adherence | Permit + passed electrical inspection |
| Deciding authority | Building official / electrical inspector (Fairfax City Code Administration; PWC Building Development Division) |
| Open questions | Disconnect location and labeling acceptance at each site (AHJ determination) |

### 2.5 Virginia USBC / SFPC (2021 editions)

| Stage | Application |
|---|---|
| Design | Building and fire review lanes; EV-ready provisions (2021 VCC §406.2.7 class, EX07/EX08); fire-access geometry |
| Procurement | — (process instrument, not equipment) |
| Certification | Not applicable; permits and approvals are the instrument |
| Installation | Permits issued under the 2021 USBC |
| Commissioning | Fire review sign-off where triggered |
| Operation | Fire access maintained; SFPC operational provisions |
| Emergency response | Apparatus access; pre-plan walkthrough with the Fire Marshal |
| End of life | Demolition/removal permits as applicable |
| Evidence of adherence | Permit records; Fire Marshal review notes |
| Deciding authority | City/County building official + Fire Marshal (Fairfax City Fire Marshal; PWC Fire Marshal's Office) |
| Open questions | Fire-access geometry per site; garage/enclosure conditions (relevant only at PWC002 Neabsco, the single enclosed candidate); interpretation of the "sufficient EV charging" EV-ready requirement (EX08) |

### 2.6 US Access Board EVSE accessibility (TA 2022; NPRM 2024-09-03) + VA USBC ADA provisions

| Stage | Application |
|---|---|
| Design | ADA-first layout at site screening — the documented local cost/schedule driver (a full year of fleet-hub redesign per client evidence, EX09 context) |
| Procurement | Accessible charger interface requirements (reach ranges, operable parts, no-app payment pairs with the digital-access finding in Report 10) |
| Certification | Not applicable; conformance shown by dimensional verification |
| Installation | Accessible route/space/reach constructed per design |
| Commissioning | Dimensional verification against TA guidance and USBC ADA provisions |
| Operation | Access maintained (no storage, snow, or equipment blocking routes/aisles) |
| Emergency response | Accessible routes double as clear approach paths |
| End of life | — |
| Evidence of adherence | Dimensional check records; design drawings |
| Deciding authority | Building official + ADA coordinator; future DOJ standards once the rule finalizes |
| Open questions | Treatment of EV-space ADA counts at small installations — **the rule is still at NPRM as of 2026-07-19 (IM-02) and its status must be re-checked at design time** |

### 2.7 OCPP + ISO 15118 (supporting protocols — NOT ULSE standards)

| Stage | Application |
|---|---|
| Design | Managed-charging architecture (charger↔network via OCPP; EV↔charger via ISO 15118/J1772 signaling) |
| Procurement | Require OCPP compliance to avoid network lock-in; require no-app/tap-to-pay capability |
| Certification | Vendor protocol conformance statement (contractual, not a listing) |
| Installation | — |
| Commissioning | Communications test + demonstrated fail-safe behavior |
| Operation | Utilization data export feeding expansion triggers (dual-path with local metering) |
| Emergency response | Default-safe curtailment on communications loss |
| End of life | Data export/portability before network contract closure |
| Evidence of adherence | Vendor protocol conformance statement; commissioning comms test record |
| Deciding authority | Program owner / vendor contract — no AHJ role |
| Open questions | None (contractual) |

### 2.8 Conditional standards (out of current scope — must not be presented as active)

| Standard | Trigger | Current status |
|---|---|---|
| UL 2202 (2022 ed.) | DC fast charging enters scope | No DCFC in the plan — reserved annex only |
| UL 9540 / UL 9540A (5th ed., 2025-03-12; 6th-ed. activity 2026) + NFPA 855 (2026 ed.) | Battery energy storage enters scope | `battery_storage_flag=0` at all 12 sites — no storage, and therefore **no resilience claim is made anywhere in this project** |

---

## 3. Decisions that remain with the AHJ / Fire Marshal

Adopted-edition interpretations; disconnect location and labeling acceptance; garage/enclosure conditions (PWC002); fire-access geometry; stormwater/runoff requirements; and all permit determinations. The standards above **govern the team's design intent**; they do not evidence achieved compliance (Report 06, §2).

## 4. Value proposition (why adherence is cheap insurance)

Listed equipment avoids failed inspections and redesign — the client's ADA-driven fleet-hub redesign cost a full year (EX09 context, client interview); certification marks transfer liability assurance to manufacturers; OCPP prevents stranded-network lock-in; UL 3600 reporting pre-empts end-of-life cost surprises (the county has already decommissioned 17 stations). Framed as avoided-redesign and avoided-incident exposure, not quantified ROI — no defensible local incident-cost data exists (Report 06, §5).
