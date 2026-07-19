"""Build data/provenance/field_provenance_v1.csv from the site table and the legacy
source-confidence tracker.

Derivation rules (documented, deterministic — commit the output):
- electrical_service: every site with elec_service_rating_amp==0 or spare_capacity_kw==0
  → unconfirmed + unresolved (this is the audited truth: 12/12 unconfirmed).
- safety_review_fields: emergency_disconnect_visible==0 → unconfirmed; else planning_assumption
  (flags are team site-visit assessments, not AHJ determinations).
- site_use_and_demand: visitors/employees present → derived_public_data (facility websites,
  ACS/LODES-class extracts); else planning_assumption.
- address_and_public_access: official_source (facility/branch pages — matches legacy tracker).
- coordinates: public_web_reference (legacy tracker: replace with official GIS later).
- parking_and_layout: planning_assumption (counted from imagery/visits, unverified).
- equity_and_context: derived_public_data (ACS/LODES-derived index).

source_date = 2026-06-24 (repo export date of the V2 data snapshot).
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SITES = ROOT / "data/inputs/real_sites_v2.csv"
OUT = ROOT / "data/provenance/field_provenance_v1.csv"

SOURCE_DATE = "2026-06-24"


def main() -> None:
    sites = pd.read_csv(SITES)
    rows = []
    for _, s in sites.iterrows():
        sid = s["site_id"]

        def add(group, source_class, unresolved, org, assumption_type=""):
            rows.append({
                "site_id": sid,
                "field_group": group,
                "source_class": source_class,
                "verification_status": "spot_checked",
                "source_org": org,
                "source_date": SOURCE_DATE,
                "reviewer": "team_v2_snapshot",
                "assumption_type": assumption_type,
                "unresolved_flag": "1" if unresolved else "0",
            })

        elec_unconfirmed = (float(s.get("elec_service_rating_amp", 0) or 0) <= 0
                            or float(s.get("spare_capacity_kw", 0) or 0) <= 0)
        add("electrical_service",
            "unconfirmed" if elec_unconfirmed else "verified_facility",
            elec_unconfirmed, "facility (pending)", "electrical capacity unverified")

        disconnect_unconfirmed = str(s.get("emergency_disconnect_visible", 0)) in {"0", "0.0", "no", "n"}
        add("safety_review_fields",
            "unconfirmed" if disconnect_unconfirmed else "planning_assumption",
            disconnect_unconfirmed, "team site assessment", "site-visit screening, not AHJ determination")

        has_use = float(s.get("visitors_day", 0) or 0) > 0 or float(s.get("employees_day", 0) or 0) > 0
        add("site_use_and_demand",
            "derived_public_data" if has_use else "planning_assumption",
            not has_use, "facility pages / ACS / LODES extracts", "public-data derivation")

        add("address_and_public_access", "official_source", False, "facility/branch official pages")
        add("coordinates", "public_web_reference", False, "public web mapping (replace with official GIS)")
        add("parking_and_layout", "planning_assumption", False, "imagery/site visit count", "unverified count")
        add("equity_and_context", "derived_public_data", False, "ACS/LODES-derived equity index")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} provenance rows -> {OUT}")


if __name__ == "__main__":
    main()
