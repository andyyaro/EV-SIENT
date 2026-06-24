"""
Rank V2 candidate backlog rows by how close they are to graduating into real_sites_v2.csv.

This script does not decide final site quality. It only helps the team see which
backlog rows are closest to being model-ready based on public-data completeness,
status fields, and the manual priority labels in the backlog.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEFAULT_INPUT = "data/source_extracts/v2_candidate_site_backlog.csv"
DEFAULT_OUTPUT_CSV = "data/outputs/v2_candidate_site_backlog_triage.csv"
DEFAULT_OUTPUT_MD = "data/outputs/v2_candidate_site_backlog_triage.md"

OUTPUT_COLUMNS = [
    "candidate_id",
    "site_name",
    "locality",
    "site_type",
    "city",
    "initial_priority",
    "model_ready_status",
    "review_status",
    "decision",
    "triage_score",
    "triage_group",
    "blocking_gaps",
    "recommended_next_action",
]


PRIORITY_POINTS = {
    "high": 20,
    "medium": 12,
    "low": 6,
}

MODEL_READY_POINTS = {
    "added": 35,
    "ready": 30,
    "almost_ready": 20,
    "not_ready": 0,
}

REVIEW_STATUS_POINTS = {
    "added_to_v2_model": 25,
    "ready_for_model": 20,
    "public_data_in_progress": 10,
    "needs_more_public_data": 3,
    "new": 0,
    "parked_for_later": -10,
    "rejected": -30,
}

DECISION_POINTS = {
    "add_to_real_sites_v2": 15,
    "collect_more_data": 5,
    "needs_stakeholder_before_model": 0,
    "park_for_future": -10,
    "reject_for_now": -30,
}


FIELDS_THAT_BLOCK_GRADUATION = [
    "address",
    "zip",
    "lat",
    "lon",
]


PUBLIC_DATA_HINTS = [
    "parking",
    "hours",
    "nearby chargers",
    "traffic",
    "demographics",
    "ownership",
]


def clean(value: object) -> str:
    """Normalize a CSV cell into a lowercase stripped string."""
    return str(value or "").strip()


def clean_lower(value: object) -> str:
    return clean(value).lower()


def has_value(row: dict[str, str], field: str) -> bool:
    return bool(clean(row.get(field)))


def split_missing_public_data(value: str) -> list[str]:
    parts = []
    for part in clean(value).replace(",", ";").split(";"):
        part = part.strip()
        if part:
            parts.append(part)
    return parts


def status_is_resolved(value: str) -> bool:
    status = clean_lower(value)
    if not status:
        return False
    unresolved_prefixes = ("needs", "unknown", "not_checked", "unclear")
    return not status.startswith(unresolved_prefixes)


def find_blocking_gaps(row: dict[str, str]) -> list[str]:
    gaps = []

    for field in FIELDS_THAT_BLOCK_GRADUATION:
        if not has_value(row, field):
            gaps.append(field)

    if not status_is_resolved(row.get("public_access_status", "")):
        gaps.append("public_access_status")

    if not status_is_resolved(row.get("parking_evidence_status", "")):
        gaps.append("parking evidence")

    if not status_is_resolved(row.get("existing_ev_charging_nearby_status", "")):
        gaps.append("nearby EV charging check")

    missing_public_data = split_missing_public_data(row.get("missing_public_data", ""))
    for hint in PUBLIC_DATA_HINTS:
        if any(hint in item.lower() for item in missing_public_data):
            gaps.append(hint)

    return sorted(set(gaps))


def score_row(row: dict[str, str]) -> int:
    score = 0

    score += PRIORITY_POINTS.get(clean_lower(row.get("initial_priority")), 0)
    score += MODEL_READY_POINTS.get(clean_lower(row.get("model_ready_status")), 0)
    score += REVIEW_STATUS_POINTS.get(clean_lower(row.get("review_status")), 0)
    score += DECISION_POINTS.get(clean_lower(row.get("decision")), 0)

    if has_value(row, "address"):
        score += 5
    if has_value(row, "zip"):
        score += 3
    if has_value(row, "lat") and has_value(row, "lon"):
        score += 10
    if status_is_resolved(row.get("public_access_status", "")):
        score += 5
    if status_is_resolved(row.get("parking_evidence_status", "")):
        score += 8
    if status_is_resolved(row.get("existing_ev_charging_nearby_status", "")):
        score += 5

    missing_public_data_count = len(split_missing_public_data(row.get("missing_public_data", "")))
    score -= min(25, missing_public_data_count * 2)

    if clean_lower(row.get("review_status")) == "rejected":
        score = min(score, 0)
    if clean_lower(row.get("review_status")) == "parked_for_later":
        score = min(score, 30)

    return max(0, min(100, score))


def build_triage_group(score: int, gaps: list[str], row: dict[str, str]) -> str:
    if clean_lower(row.get("model_ready_status")) == "added":
        return "already_added_to_v2_model"
    if clean_lower(row.get("review_status")) == "rejected":
        return "rejected"
    if clean_lower(row.get("review_status")) == "parked_for_later":
        return "parked_for_later"
    if score >= 75 and not gaps:
        return "ready_for_model_row"
    if score >= 55:
        return "near_ready_collect_targeted_data"
    if score >= 35:
        return "useful_but_needs_public_data"
    return "early_backlog_candidate"


def build_next_action(group: str, gaps: list[str]) -> str:
    if group == "already_added_to_v2_model":
        return "Run the V2 model and review the output."
    if group == "ready_for_model_row":
        return "Create a full real_sites_v2.csv row and mark backlog status as added_to_v2_model."
    if group == "near_ready_collect_targeted_data":
        top_gaps = "; ".join(gaps[:4]) if gaps else "remaining public-data fields"
        return f"Collect targeted missing data first: {top_gaps}."
    if group == "useful_but_needs_public_data":
        top_gaps = "; ".join(gaps[:5]) if gaps else "basic public-data fields"
        return f"Keep in backlog and complete public-data review: {top_gaps}."
    if group == "parked_for_later":
        return "Leave parked until V2 needs this site type or location."
    if group == "rejected":
        return "Do not add to real_sites_v2.csv unless new information changes the decision."
    return "Keep as backlog idea; verify address, coordinates, parking, hours, and public access."


def triage_row(row: dict[str, str]) -> dict[str, str]:
    gaps = find_blocking_gaps(row)
    score = score_row(row)
    group = build_triage_group(score, gaps, row)

    return {
        "candidate_id": clean(row.get("candidate_id")),
        "site_name": clean(row.get("site_name")),
        "locality": clean(row.get("locality")),
        "site_type": clean(row.get("site_type")),
        "city": clean(row.get("city")),
        "initial_priority": clean(row.get("initial_priority")),
        "model_ready_status": clean(row.get("model_ready_status")),
        "review_status": clean(row.get("review_status")),
        "decision": clean(row.get("decision")),
        "triage_score": str(score),
        "triage_group": group,
        "blocking_gaps": "; ".join(gaps) if gaps else "none",
        "recommended_next_action": build_next_action(group, gaps),
    }


def load_backlog(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Backlog file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]], path: Path, top_n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    top_rows = rows[:top_n]

    lines = [
        "# V2 Candidate Backlog Triage",
        "",
        "This report ranks backlog candidates by how close they are to graduating into `real_sites_v2.csv`.",
        "",
        "A high score does not mean the site is a final recommendation. It means the row is closer to being model-ready.",
        "",
        f"Rows reviewed: {len(rows)}",
        f"Top rows shown: {len(top_rows)}",
        "",
        "| Rank | Candidate | Site | Type | City | Score | Group | Blocking gaps | Next action |",
        "|---:|---|---|---|---|---:|---|---|---|",
    ]

    for index, row in enumerate(top_rows, start=1):
        lines.append(
            "| {rank} | {candidate_id} | {site_name} | {site_type} | {city} | {score} | {group} | {gaps} | {action} |".format(
                rank=index,
                candidate_id=row["candidate_id"],
                site_name=row["site_name"],
                site_type=row["site_type"],
                city=row["city"],
                score=row["triage_score"],
                group=row["triage_group"],
                gaps=row["blocking_gaps"],
                action=row["recommended_next_action"],
            )
        )

    lines.extend(
        [
            "",
            "## How to use this report",
            "",
            "1. Start with the highest-scoring candidates.",
            "2. Fill the listed blocking gaps from public sources first.",
            "3. Move a candidate into `real_sites_v2.csv` only after the minimum model-ready fields are filled.",
            "4. Save stakeholder outreach for sites that rank well or remain high-value but uncertain after model screening.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage V2 candidate backlog rows.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to V2 candidate backlog CSV.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Path to write triage CSV.")
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD, help="Path to write Markdown summary.")
    parser.add_argument("--top-n", type=int, default=15, help="Number of top rows to show in the Markdown summary.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_md = Path(args.output_md)

    backlog_rows = load_backlog(input_path)
    triaged_rows = [triage_row(row) for row in backlog_rows]
    triaged_rows.sort(key=lambda row: int(row["triage_score"]), reverse=True)

    write_csv(triaged_rows, output_csv)
    write_markdown(triaged_rows, output_md, args.top_n)

    print("V2 CANDIDATE BACKLOG TRIAGE")
    print("---------------------------")
    print(f"Input: {input_path}")
    print(f"Rows reviewed: {len(triaged_rows)}")
    print(f"Saved CSV: {output_csv}")
    print(f"Saved Markdown: {output_md}")
    print()
    print("Top candidates to clean up first:")
    for row in triaged_rows[: args.top_n]:
        print(f"- {row['candidate_id']} | {row['site_name']} | score {row['triage_score']} | {row['triage_group']}")


if __name__ == "__main__":
    main()
