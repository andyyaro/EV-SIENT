# Technical Integration Architecture

**Project:** Future City Fellowship — Milestone 2, staged municipal EV charging (Fairfax City + Prince William County, VA)
**Date:** 2026-07-19 · **Status:** Design intent pending AHJ/utility confirmation. Service capacity is unconfirmed at 12/12 candidate sites; nothing here is an as-built description.
**Basis:** Report 07 (Technical Integration and Failure-Mitigation Research); `FAILURE_MITIGATION_OPTIONS.csv` (**pre-V3 research archive, not tracked in this repository** — cited here as the evidentiary basis, not as a file a reader can open); EX16 (protocols); EX12 (Dominion programs).
**Companion visual:** `../assets/architecture/integration_architecture.png`

---

## 1. System context

The proposed system is a chain from the utility to the municipal decision process, with an emergency-isolation path and a monitoring layer that exists specifically to feed expansion decisions:

1. **Utility service (Dominion) → transformer/feeder → facility service entrance.** Interconnection, tariff, and capacity live here. Both jurisdictions are Dominion territory (EX12); the Dominion Level 2 make-ready program includes interconnection review.
2. **Service entrance and panel → metering and submetering.** NEC load calculations (2020 NEC as adopted via the 2021 USBC) govern circuit allocation; a local submeter provides the second, network-independent data path.
3. **Load management / charging management system.** Allocates power setpoints across ports; must carry a documented default-safe curtailment profile for communications loss, and sits above hardwired overcurrent protection that works with all software dead.
4. **EVSE ports (UL 2594-listed, UL 2231 personnel protection embedded).** AC Level 2, the only equipment class in scope.
5. **Communications.** OCPP between chargers and the network backend; ISO 15118 / J1772 signaling between vehicle and charger. These are supporting industry protocols, not ULSE standards (EX16).
6. **User and fleet operations.** Public users at 11 surface-lot sites and one commuter garage (PWC002 Neabsco); the county fleet hub is a separate coordination-only track.
7. **Emergency disconnect and responder access.** A verified, labeled, illuminated disconnect that cuts EVSE output, reachable by fire apparatus — proposed-standard Module 1, and the subject of a Fire Marshal pre-plan walkthrough.
8. **Monitoring and decision-support layer.** Sessions, energy, and uptime flow from the network backend and the local meter to city/county-owned storage, where expansion triggers convert observed utilization into governance decisions (budget, expansion, or decommissioning).

## 2. Interface register (the eight interfaces that must be explained)

| # | Interface | What crosses it | Owner | Failure question |
|---|---|---|---|---|
| 1 | Utility ↔ service entrance | Capacity, interconnection, tariff/demand charges | Dominion + facility | Is service adequate? **Unconfirmed at 12/12 sites** — the highest-value single data request in the project |
| 2 | Panel ↔ load manager | Circuit allocation, load calculations (NEC 625/220 as adopted) | Electrical engineer of record | What happens at full simultaneous draw? |
| 3 | Load manager ↔ EVSE | Power setpoints, curtailment commands (OCPP) | Vendor | Fail-safe on comms loss? |
| 4 | EVSE ↔ vehicle | Charging session, personnel protection (UL 2231) | Listed equipment (manufacturer) | Shock/fault protection |
| 5 | EVSE/network ↔ data layer | Sessions, energy, uptime | Network operator | Data continuity for expansion triggers |
| 6 | Site ↔ responders | Access route, disconnect, signage | Fire Marshal/AHJ + facility | Can a responder isolate power fast? |
| 7 | Site ↔ environment | Runoff, heat, flood exposure | Facility + local stormwater authority | Firewater containment |
| 8 | Data layer ↔ governance | Trigger evidence → expansion decisions | City/county | Who owns the stop/go call? |

## 3. Responsibility register

| Element | Design responsibility | Operating responsibility | Approval / oversight authority |
|---|---|---|---|
| Utility service and interconnection | Dominion (with facility input) | Dominion | Dominion (SCC-regulated tariffs) |
| Service entrance, panel, circuits | Electrical engineer of record | Facility operations / public works | Building official + electrical inspector (permit) |
| Load management configuration | Vendor + engineer of record | Vendor under contract; facility oversight | Program owner (contract); electrical inspector for protection settings |
| EVSE equipment | Manufacturer (UL 2594/2231 listing) | Facility/network operator maintenance contract | NRTL listing; building official at inspection |
| Communications and network backend | Network vendor (OCPP conformance) | Network operator | Program owner via contract SLAs (NEVI 97% uptime as benchmark practice) |
| Emergency disconnect and signage | Engineer of record per NEC 625 as adopted | Facility operations (annual verification) | Fire Marshal + electrical inspector |
| Stormwater/site conditions | Civil designer | Facility operations | Local VSMP-delegated stormwater program |
| Monitoring data and expansion triggers | Program owner (dual-path design) | Program owner; monthly export to city/county storage | Board of County Supervisors / City Council via CIP — **the human stop/go authority** |
| Accessibility (ADA-first layout) | Site designer to Access Board TA guidance + VA USBC ADA provisions | Facility operations (keep routes clear) | Building official + ADA coordinator |

## 4. Failure-mode headline (for the presentation)

The three failure modes with direct client-evidence resonance: **overbuild/underuse** (Neabsco decommissioning), **cost blowout via trenching distance** (McCoart), and **inaccessible/unclear shutdown** (Adams interview). Top-ranked mitigations (full ranking in `FAILURE_MITIGATION_OPTIONS.csv`, carried into `RISK_REGISTER.csv`): (1) default-safe curtailment on comms loss; (2) verified, labeled, illuminated emergency disconnect at commissioning; (3) service-capacity confirmation before design freeze; (4) dual-path utilization logging; (5) ADA-first site layout. Every mitigation is design intent pending AHJ/utility confirmation.
