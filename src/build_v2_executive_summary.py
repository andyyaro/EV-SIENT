"""Build a consolidated V2 executive site summary table.

This script joins the most decision-useful V2 outputs into one clean table for
reporting, screenshots, and presentations. It combines ranking, confidence,
electrical risk, right-sizing, port-simulation outputs, action labels, and
review flags.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_PORT_SIMULATION = "data/outputs/v2_port_utilization_simulation.csv"
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
    "sim_min_ports_current",
    "sim_utilization_current_at_ports_now",
    "sim_wait_current_at_ports_now",
    "sim_queue_risk_current_at_ports_now",
    "sim_min_ports_2035_high",
    "sim_min_ports_2050_high",
    "sim_status_2050_high_at_future_ready",
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


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_electrical_columns(electrical: pd.DataFrame) -> pd.DataFrame:
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

    current_status = str(row.get("sim_queue_risk_current_at_ports_now", "")).lower()
    future_status = str(row.get("sim_status_2050_high_at_future_ready", "")).lower()
    if current_status in {"elevated", "high"}:
        flags.append("Current port count may need closer utilization review")
    if future_status == "underbuilt":
        flags.append("Future-ready capacity may be underbuilt in 2050 high case")

    access = row.get("public_access", None)
    try:
        if float(access) < 1:
            flags.append("Public access/use case needs confirmation")
    except (TypeError, ValueError):
        pass

    if not flags:
        flags.append("Standard site screening needed")
    return semicolon_join(flags)


def pick_min_ports(group: pd.DataFrame) -> object:
    if group.empty:
        return ""
    acceptable = group[group["capacity_status"].isin(["right_sized", "acceptable_but_monitor"])]
    if acceptable.empty:
        best = group.sort_values(["estimated_wait_min", "utilization_pct"]).iloc[0]
    else:
        best = acceptable.sort_values("port_count").iloc[0]
    return int(best["port_count"])


def summarize_port_simulation(simulation: pd.DataFrame) -> pd.DataFrame:
    if simulation.empty or "site_id" not in simulation.columns:
        return pd.DataFrame(columns=["site_id"])

    rows = []
    for site_id, site_rows in simulation.groupby("site_id", dropna=False):
        current = site_rows[site_rows["demand_case"] == "current"].copy()
        high_2035 = site_rows[site_rows["demand_case"] == "2035_high"].copy()
        high_2050 = site_rows[site_rows["demand_case"] == "2050_high"].copy()

        current_ports_now = current[current.get("is_ports_now", False) == True] if "is_ports_now" in current.columns else pd.DataFrame()
        if current_ports_now.empty and not current.empty:
            current_ports_now = current.sort_values("port_count").head(1)

        future_ready = high_2050[high_2050.get("is_future_ready_capacity", False) == True] if "is_future_ready_capacity" in high_2050.columns else pd.DataFrame()
        if future_ready.empty and not high_2050.empty:
            future_ready = high_2050.sort_values("port_count").tail(1)

        current_row = current_ports_now.iloc[0] if not current_ports_now.empty else None
        future_row = future_ready.iloc[0] if not future_ready.empty else None

        rows.append(
            {
                "site_id": site_id,
                "sim_min_ports_current": pick_min_ports(current),
                "sim_utilization_current_at_ports_now": current_row.get("utilization_pct", "") if current_row is not None else "",
                "sim_wait_current_at_ports_now": current_row.get("estimated_wait_min", "") if current_row is not None else "",
                "sim_queue_risk_current_at_ports_now": current_row.get("queue_risk_level", "") if current_row is not None else "",
                "sim_min_ports_2035_high": pick_min_ports(high_2035),
                "sim_min_ports_2050_high": pick_min_ports(high_2050),
                "sim_status_2050_high_at_future_ready": future_row.get("capacity_status", "") if future_row is not None else "",
            }
        )
    return pd.DataFrame(rows)


def build_executive_summary(
    results: pd.DataFrame,
    electrical: pd.DataFrame,
    right_sizing: pd.DataFrame,
    port_simulation: pd.DataFrame,
) -> pd.DataFrame:
    required_results = {"site_id", "model_rank", "site_name", "readiness_score"}
    missing = required_results - set(results.columns)
    if missing:
        raise ValueError(f"V2 site results are missing required columns: {sorted(missing)}")

    electrical = normalize_electrical_columns(electrical)
    port_summary = summarize_port_simulation(port_simulation)

    electrical_keep = [col for col in ["site_id", "electrical_risk_level", "expected_rank", "expected_score"] if col in electrical.columns]
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
    if not port_summary.empty:
        merged = merged.merge(port_summary, on="site_id", how="left")
    merged = merged.rename(columns={"expected_rank": "expected_electrical_rank", "expected_score": "expected_electrical_score"})

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
        "electrical_risk_level",
        "ports_now",
        "sim_min_ports_current",
        "sim_utilization_current_at_ports_now",
        "sim_min_ports_2050_high",
        "future_ready_capacity",
        "sim_status_2050_high_at_future_ready",
        "major_review_flags",
    ]

    return f"""# V2 Executive Site Summary

{top_text}

This report consolidates the most decision-useful V2 outputs into one table. It now includes the port-utilization simulation summary alongside ranking, electrical risk, and right-sizing.

## Executive decision table

{markdown_table(summary, compact_columns)}

## Notes

- `ports_now` is the near-term installation recommendation from the V2 right-sizing module.
- `sim_min_ports_current` is the smallest simulated port count that avoids underbuilt status under current demand.
- `sim_min_ports_2050_high` is the smallest simulated port count that avoids underbuilt status under the 2050 high-growth case.
- `sim_status_2050_high_at_future_ready` checks whether the future-ready capacity still looks acceptable in the 2050 high-growth case.
- These simulation outputs are planning-screen signals, not detailed queueing, utility, or engineering results.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a consolidated V2 executive site summary table.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="V2 electrical risk summary CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--port-simulation", default=DEFAULT_PORT_SIMULATION, help="V2 port simulation CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Executive summary CSV output.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Executive summary Markdown report output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    electrical_path = Path(args.electrical_summary)
    right_sizing_path = Path(args.right_sizing)
    port_simulation_path = Path(args.port_simulation)
    output_path = Path(args.output)
    report_path = Path(args.report)

    results = read_required_csv(results_path, "V2 site results")
    electrical = read_required_csv(electrical_path, "V2 electrical summary")
    right_sizing = read_required_csv(right_sizing_path, "V2 right-sizing")
    port_simulation = read_optional_csv(port_simulation_path)

    summary = build_executive_summary(results, electrical, right_sizing, port_simulation)
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
    print(summary[["model_rank", "site_id", "readiness_score", "ports_now", "sim_min_ports_current", "sim_min_ports_2050_high", "future_ready_capacity", "sim_status_2050_high_at_future_ready"]].to_string(index=False))


if __name__ == "__main__":
    main()
