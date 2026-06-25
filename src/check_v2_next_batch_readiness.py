"""Check whether the next V2 candidate batch is ready for model-row promotion.

This does not fetch public data. It checks the committed next-batch tracker and
reports which fields still block promotion into data/inputs/real_sites_v2.csv.

Run from the repository root:

    python src/check_v2_next_batch_readiness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BATCH_PATH = Path("data/source_extracts/v2_next_upgrade_batch.csv")
BACKLOG_PATH = Path("data/source_extracts/v2_candidate_site_backlog.csv")
REAL_SITES_PATH = Path("data/inputs/real_sites_v2.csv")

FIELDS_REQUIRED_BEFORE_PROMOTION = [
    "address",
    "city",
    "state",
    "zip",
]

HARD_BLOCKER_KEYWORDS = [
    "lat/lon",
    "parking",
    "hours",
    "ownership",
    "access rules",
]


def split_blockers(value: str) -> list[str]:
    return [part.strip().lower() for part in str(value).split(";") if part.strip()]


def main() -> None:
    print("V2 NEXT-BATCH READINESS CHECK")
    print("-----------------------------")

    missing_files = [path for path in [BATCH_PATH, BACKLOG_PATH, REAL_SITES_PATH] if not path.exists()]
    if missing_files:
        print("Status: FAILED")
        for path in missing_files:
            print(f"- Missing required file: {path}")
        sys.exit(1)

    batch = pd.read_csv(BATCH_PATH, dtype=str).fillna("")
    backlog = pd.read_csv(BACKLOG_PATH, dtype=str).fillna("")
    real_sites = pd.read_csv(REAL_SITES_PATH, dtype=str).fillna("")

    real_site_ids = set(real_sites["site_id"].astype(str))
    backlog_ids = set(backlog["candidate_id"].astype(str))

    errors: list[str] = []
    warnings: list[str] = []

    for _, row in batch.iterrows():
        candidate_id = row["candidate_id"]
        future_site_id = row["future_site_id"]
        site_name = row["site_name"]

        if candidate_id not in backlog_ids:
            errors.append(f"{candidate_id} — {site_name}: candidate_id is not present in the V2 backlog.")

        if future_site_id in real_site_ids:
            warnings.append(f"{candidate_id} — {site_name}: future_site_id {future_site_id} already exists in real_sites_v2.csv.")

        for field in FIELDS_REQUIRED_BEFORE_PROMOTION:
            if not str(row.get(field, "")).strip():
                warnings.append(f"{candidate_id} — {site_name}: missing {field} in next-batch tracker.")

        blockers = split_blockers(row.get("blocking_fields_before_model_row", ""))
        if blockers:
            warnings.append(f"{candidate_id} — {site_name}: blockers before model-row promotion: {', '.join(blockers)}")

        lower_blocker_text = "; ".join(blockers)
        for keyword in HARD_BLOCKER_KEYWORDS:
            if keyword in lower_blocker_text:
                warnings.append(f"{candidate_id} — {site_name}: verify {keyword} before promotion.")

    if errors:
        print("Status: FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print("Status: REVIEW NEEDED")
    print(f"Batch candidates checked: {len(batch)}")
    print("No structural errors found, but these candidates are not model-ready until blockers are resolved.")
    print()
    print("Review items:")
    for warning in warnings:
        print(f"- {warning}")


if __name__ == "__main__":
    main()
