"""Standards traceability register (PY-13).

Keyed by site x standard x lifecycle stage, with evidence, authority, adopted vs
latest edition, and open AHJ questions. Conditional standards (DCFC, BESS) are
emitted with applicability='conditional_out_of_scope' and are excluded from
active-scope views - they must never be shown as active when no DCFC/BESS exists.

Editions verified 2026-07-19 (see docs/methodology/current-facts-source-register.md).
"""

from __future__ import annotations

import pandas as pd

STANDARDS = [
    {
        "standard_id": "UL2594",
        "title": "UL 2594 Electric Vehicle Supply Equipment (AC L1/L2, <=1000 V)",
        "role": "highlighted_safety",
        "adopted_edition": "3rd ed., 2022-12-15",
        "latest_edition": "3rd ed., 2022-12-15 (revision activity through 2025)",
        "applicability": "active",
        "stages": {
            "design": "Specify UL 2594-listed EVSE only; installation per NEC 625 as adopted",
            "procurement": "Listing/certification marks required in bid documents",
            "installation": "Listed-equipment installation conditions honored",
            "commissioning": "Verify listing marks and personnel-protection function",
            "operation": "Maintain per listing conditions",
            "emergency_response": "Listed equipment supports predictable de-energization behavior",
            "end_of_life": "-",
        },
        "evidence_required": "Certification/listing records in procurement file; inspection sign-off",
        "authority": "Manufacturer listing (NRTL) + local building official",
        "open_ahj_question": "None specific; edition interpretation rests with AHJ",
    },
    {
        "standard_id": "UL3600",
        "title": "UL 3600 Measuring and Reporting Circular Economy Aspects",
        "role": "highlighted_sustainability",
        "adopted_edition": "1st ed., 2023-01-09",
        "latest_edition": "1st ed., 2023-01-09",
        "applicability": "active",
        "stages": {
            "design": "Materials/repairability considered in equipment selection",
            "procurement": "Vendor circularity disclosure (recycled content, repairability, take-back)",
            "installation": "-",
            "commissioning": "Baseline circularity reporting sheet opened per site",
            "operation": "Annual circularity reporting for the charging program",
            "emergency_response": "-",
            "end_of_life": "Take-back/recycling route documented and executed",
        },
        "evidence_required": "UL 3600-style circularity reporting sheet per site/program",
        "authority": "Program owner (sustainability office); voluntary standard",
        "open_ahj_question": "None (voluntary reporting standard)",
    },
    {
        "standard_id": "UL2231",
        "title": "UL 2231-1/-2 Personnel Protection Systems for EV Supply Circuits",
        "role": "supporting_essential",
        "adopted_edition": "2021 editions",
        "latest_edition": "2021 editions",
        "applicability": "active",
        "stages": {
            "design": "Embedded in listed EVSE per NEC listing practice",
            "procurement": "Confirm EVSE listing includes UL 2231 personnel protection",
            "installation": "-",
            "commissioning": "GFCI/CCID protection functional verification",
            "operation": "Periodic protection test per maintenance plan",
            "emergency_response": "-",
            "end_of_life": "-",
        },
        "evidence_required": "Listing detail; commissioning functional test record",
        "authority": "NRTL listing + electrical inspector",
        "open_ahj_question": "None",
    },
    {
        "standard_id": "NEC625",
        "title": "NEC Article 625 (NFPA 70) as adopted in Virginia (2020 NEC via 2021 USBC)",
        "role": "supporting_essential",
        "adopted_edition": "2020 NEC (2021 USBC, effective 2024-01-18)",
        "latest_edition": "2023 NEC published (NOT adopted in Virginia)",
        "applicability": "active",
        "stages": {
            "design": "Load calculations, disconnect provisions, circuit design",
            "procurement": "-",
            "installation": "Installation law for every EVSE circuit",
            "commissioning": "Electrical inspection approval",
            "operation": "-",
            "emergency_response": "Disconnect location/labeling per adopted provisions",
            "end_of_life": "Circuit decommissioning per code",
        },
        "evidence_required": "Permit + passed electrical inspection",
        "authority": "Building official / electrical inspector (Fairfax City / PWC)",
        "open_ahj_question": "Disconnect location and labeling acceptance at each site",
    },
    {
        "standard_id": "VA-USBC-SFPC",
        "title": "Virginia USBC / Statewide Fire Prevention Code (2021 editions)",
        "role": "supporting_essential",
        "adopted_edition": "2021 editions, effective 2024-01-18 (2024 cycle in development, ~2027)",
        "latest_edition": "2021 (2024 development cycle underway)",
        "applicability": "active",
        "stages": {
            "design": "Building/fire review lanes; EV-ready provisions (VCC 406.2.7 class)",
            "procurement": "-",
            "installation": "Permits under 2021 USBC",
            "commissioning": "Fire review sign-off where triggered",
            "operation": "Fire access maintained",
            "emergency_response": "Apparatus access; pre-plan with Fire Marshal",
            "end_of_life": "-",
        },
        "evidence_required": "Permit records; Fire Marshal review notes",
        "authority": "City/County building official + Fire Marshal",
        "open_ahj_question": "Fire access geometry; garage/enclosure conditions; 'sufficient EV charging' interpretation",
    },
    {
        "standard_id": "ACCESS-BOARD-EVSE",
        "title": "US Access Board EVSE accessibility (TA 2022; NPRM 2024-09-03; VA USBC ADA provisions now)",
        "role": "supporting_essential",
        "adopted_edition": "VA USBC ADA provisions (in force); Access Board rule at NPRM stage as of 2026-07-19",
        "latest_edition": "NPRM 2024-09-03; final rule NOT issued as of 2026-07-19; DOJ rulemaking to follow",
        "applicability": "active",
        "stages": {
            "design": "ADA-first layout at site screening (documented local cost/schedule driver)",
            "procurement": "Accessible charger interface requirements",
            "installation": "Accessible route/space/reach construction",
            "commissioning": "Dimensional verification",
            "operation": "Access maintained",
            "emergency_response": "-",
            "end_of_life": "-",
        },
        "evidence_required": "Dimensional check records; design drawings",
        "authority": "Building official + ADA coordinator; future DOJ standards",
        "open_ahj_question": "Treatment of EV-space ADA counts at small installations (rule status must be re-checked at design time)",
    },
    {
        "standard_id": "OCPP-ISO15118",
        "title": "OCPP (charger-network) and ISO 15118 (EV-charger) - supporting protocols, NOT ULSE standards",
        "role": "supporting_protocol",
        "adopted_edition": "current industry versions",
        "latest_edition": "current industry versions",
        "applicability": "active",
        "stages": {
            "design": "Managed-charging architecture",
            "procurement": "Require OCPP compliance to avoid network lock-in; no-app payment capability",
            "installation": "-",
            "commissioning": "Comms + fail-safe behavior test",
            "operation": "Utilization data export for triggers",
            "emergency_response": "Fail-safe on comms loss",
            "end_of_life": "-",
        },
        "evidence_required": "Vendor protocol conformance statement; commissioning comms test",
        "authority": "Program owner / vendor contract",
        "open_ahj_question": "None (contractual)",
    },
    {
        "standard_id": "UL2202",
        "title": "UL 2202 EV (DC) Charging System Equipment",
        "role": "conditional",
        "adopted_edition": "2022 edition",
        "latest_edition": "2022 edition",
        "applicability": "conditional_out_of_scope",
        "condition": "Applies ONLY if DC fast charging enters scope. No DCFC in the current plan.",
        "stages": {}, "evidence_required": "-", "authority": "-",
        "open_ahj_question": "-",
    },
    {
        "standard_id": "UL9540-9540A-NFPA855",
        "title": "UL 9540 / UL 9540A / NFPA 855 (energy storage)",
        "role": "conditional",
        "adopted_edition": "UL 9540A 5th ed. 2025-03-12; NFPA 855 2026 ed.",
        "latest_edition": "UL 9540A 6th-ed. activity 2026",
        "applicability": "conditional_out_of_scope",
        "condition": "Applies ONLY if battery storage enters scope. battery_storage_flag=0 at all 12 sites.",
        "stages": {}, "evidence_required": "-", "authority": "-",
        "open_ahj_question": "-",
    },
]

STAGES = ["design", "procurement", "installation", "commissioning", "operation",
          "emergency_response", "end_of_life"]


def build_register(site_table: pd.DataFrame) -> pd.DataFrame:
    """One row per site x standard x stage (active standards) plus one conditional row
    per site x conditional standard (marked out of scope)."""
    rows = []
    for _, site in site_table.iterrows():
        for std in STANDARDS:
            if std["applicability"] == "conditional_out_of_scope":
                rows.append({
                    "site_id": site["site_id"],
                    "standard_id": std["standard_id"],
                    "standard_title": std["title"],
                    "role": std["role"],
                    "stage": "n/a",
                    "requirement": std.get("condition", ""),
                    "adopted_edition": std["adopted_edition"],
                    "latest_edition": std["latest_edition"],
                    "applicability": std["applicability"],
                    "evidence_required": "-",
                    "authority": "-",
                    "open_ahj_question": "-",
                })
                continue
            for stage in STAGES:
                req = std["stages"].get(stage, "-")
                if req == "-":
                    continue
                rows.append({
                    "site_id": site["site_id"],
                    "standard_id": std["standard_id"],
                    "standard_title": std["title"],
                    "role": std["role"],
                    "stage": stage,
                    "requirement": req,
                    "adopted_edition": std["adopted_edition"],
                    "latest_edition": std["latest_edition"],
                    "applicability": "active",
                    "evidence_required": std["evidence_required"],
                    "authority": std["authority"],
                    "open_ahj_question": std["open_ahj_question"],
                })
    return pd.DataFrame(rows)
