"""Build a consolidated V2 executive site summary table.

This script joins the most decision-useful V2 outputs into one clean table for
reporting, screenshots, and presentations. It does not replace the detailed CSV
or Markdown outputs; it gives a single view that combines ranking, confidence,
electrical risk, right-sizing, action labels, and review flags.

Run from the repository root after V2 electrical and right-sizing outputs exist:

    python src/build_v2_executive_summary.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_OUTPUT = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_REPORT = "data/outputs/v2_executive_site_summary.md"

OUTPUT_COLUMNS = [
    "model_rank",
    "site_id",
    "site_name",
    "readiness_score",
    "data_confidence_level",
    "recommendation_tier",
    "action_label",
    "electrical_risk_level",
    "expected_electrical_rank",
    "expected_electrical_score",
    "ports_now",
    "ports_2035_base",
    "ports_2035_high",
    "ports_2050_base",
    "ports_2050_high",
    "future_ready_capacity",
    "expansion_strategy",
    "major_review_flags",
    "planning_recommendation",
    "data_needed_next",
]


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {path}")
    return pd.read_csv(path)


def normalize_electrical_columns(electrical: pd.DataFrame) -> pd.DataFrame:
    """Normalize electrical summary column names across earlier V2 versions."""
    data = electrical.copy()
    rename_map = {}
    if "electrical_adjusted_rank" in data.columns and "expected_rank" not in data.columns:
        rename_map["electrical_adjusted_rank"] = "expected_rank"
    if "electrical_adjusted_score" in data.columns and "expected_score" not in data.columns:
        rename_map["electrical_adjusted_score"] = "expected_score"
    if rename_map:
        data = data.rename(columns=rename_map)
    return data


def semicolon_join(items: list[str]) -> str:
    cleaned = []
    seen = set()
    for item in items:
        text = str(item).strip()
        if not text or text.lower() == "nan":
            continue
        if text not in seen:
            cleaned.append(text)
            seen.add(text)
    return "; ".join(cleaned)


def build_review_flags(row: pd.Series) -> str:
    flags: list[str] = []

    review_reason = str(row.get("review_reason", "")).strip()
    if review_reason and review_reason.lower() != "nan":
        flags.extend([part.strip() for part in review_reason.split(";") if part.strip()])

    risk = str(row.get("electrical_risk_level", "")).strip().lower()
    if risk == "high":
        flags.append("High electrical-risk screen")
    elif risk == "medium":
        flags.append("Electrical assumptions need confirmation")

    tier = str(row.get("recommendation_tier", "")).lower()
    strategy = str(row.get("expansion_strategy", "")).lower()
    if "high-review" in tier:
        flags.append("High-review candidate")
    if "garage" in tier or "garage" in strategy:
        flags.append("Garage / Fire Marshal / AHJ review likely")
    if "electrical_review" in strategy:
        flags.append("Electrical review before expansion")
    if "monitor_due_to_nearby_supply" in strategy:
        flags.append("Nearby charging supply may reduce priority")
    if "do_not_advance" in strategy:
        flags.append("Do not advance as general-public buildout")

    access = row.get("public_access", None)
    try:
        if float(access) < 1:
            flags.append("Public access/use case needs confirmation")
    except (TypeError, ValueError):
        pass

    if not flags:
        flags.append("Standard site screening needed")
    return semicolon_join(flags)


def build_executive_summary(results: pd.DataFrame, electrical: pd.DataFrame, right_sizing: pd.DataFrame) -> pd.DataFrame:
    required_results = {"site_id", "model_rank", "site_name", "readiness_score"}
    missing = required_results - set(results.columns)
    if missing:
        raise ValueError(f"V2 site results are missing required columns: {sorted(missing)}")

    electrical = normalize_electrical_columns(electrical)

    electrical_keep = [
        col
        for col in ["site_id", "electrical_risk_level", "expected_rank", "expected_score"]
        if col in electrical.columns
    ]
    if "site_id" not in electrical_keep:
        raise ValueError("Electrical summary is missing site_id.")

    right_sizing_keep = [
        col
        for col in [
            "site_id",
            "ports_now",
            "ports_2035_base",
            "ports_2035_high",
            "ports_2050_base",
            "ports_2050_high",
            "future_ready_capacity",
            "expansion_strategy",
        ]
        if col in right_sizing.columns
    ]
    if "site_id" not in right_sizing_keep:
        raise ValueError("Right-sizing output is missing site_id.")

    merged = results.merge(electrical[electrical_keep], on="site_id", how="left")
    merged = merged.merge(right_sizing[right_sizing_keep], on="site_id", how="left")
    merged = merged.rename(
        columns={
            "expected_rank": "expected_electrical_rank",
            "expected_score": "expected_electrical_score",
        }
    )

    merged["major_review_flags"] = merged.apply(build_review_flags, axis=1)
    merged["model_rank"] = pd.to_numeric(merged["model_rank"], errors="coerce")
    merged = merged.sort_values("model_rank")

    for col in OUTPUT_COLUMNS:
        if col not in merged.columns:
            merged[col] = ""

    return merged[OUTPUT_COLUMNS]


def markdown_table(data: pd.DataFrame, columns: list[str]) -> str:
    if data.empty:
        return "_No executive summary data available._"

    view = data[[col for col in columns if col in data.columns]].copy()
    view.columns = [col.replace("_", " ") for col in view.columns]
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        values = [str(row[col]).replace("|", "/") for col in view.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator] + rows)


def build_markdown_report(summary: pd.DataFrame) -> str:
    top = summary.iloc[0] if not summary.empty else None
    top_text = "No top site available."
    if top is not None:
        top_text = (
            f"Top candidate: **{top['site_id']} — {top['site_name']}** "
            f"with readiness score **{top['readiness_score']}**, strategy **{top['expansion_strategy']}**, "
            f"and future-ready capacity **{top['future_ready_capacity']}**."
        )

    compact_columns = [
        "model_rank",
        "site_id",
        "readiness_score",
        "data_confidence_level",
        "electrical_risk_level",
        "ports_now",
        "future_ready_capacity",
        "expansion_strategy",
        "major_review_flags",
    ]

    return f"""# V2 Executive Site Summary

{top_text}

This report consolidates the most decision-useful V2 outputs into one table. It is intended for quick review, reporting, screenshots, and presentation preparation.

## Executive decision table

{markdown_table(summary, compact_columns)}

## Notes

- `ports_now` is the near-term installation recommendation from the V2 right-sizing module.
- `future_ready_capacity` is the practical planning capacity target from the V2 right-sizing module.
- `electrical_risk_level` is a planning-screening signal, not a utility engineering result.
- `major_review_flags` summarizes likely follow-up review needs and does not replace AHJ, Fire Marshal, ADA, stormwater, or utility review.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a consolidated V2 executive site summary table.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="V2 electrical risk summary CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Executive summary CSV output.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Executive summary Markdown report output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    electrical_path = Path(args.electrical_summary)
    right_sizing_path = Path(args.right_sizing)
    output_path = Path(args.output)
    report_path = Path(args.report)

    results = read_required_csv(results_path, "V2 site results")
    electrical = read_required_csv(electrical_path, "V2 electrical summary")
    right_sizing = read_required_csv(right_sizing_path, "V2 right-sizing")

    summary = build_executive_summary(results, electrical, right_sizing)
    ensure_parent_dir(output_path)
    ensure_parent_dir(report_path)
    summary.to_csv(output_path, index=False)
    report_path.write_text(build_markdown_report(summary), encoding="utf-8")

    print("V2 EXECUTIVE SITE SUMMARY")
    print("-------------------------")
    print(f"Rows: {len(summary)}")
    print(f"Saved CSV: {output_path}")
    print(f"Saved report: {report_path}")
    print()
    print(summary[["model_rank", "site_id", "readiness_score", "electrical_risk_level", "ports_now", "future_ready_capacity", "expansion_strategy"]].to_string(index=False))


if __name__ == "__main__":
    main()
