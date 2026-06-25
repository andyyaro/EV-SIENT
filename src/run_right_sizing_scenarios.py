"""Run V2 EV charging right-sizing scenarios.

This module improves the V2 prototype's port-planning logic by separating:

1. what to install now, and
2. what to prepare for later under base and high growth cases.

It uses the V2 model output as input, so it should run after ev_charger_model.py.

Run from the repository root after python src/run_v2.py has generated results:

    python src/run_right_sizing_scenarios.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ev_charger_model import choose_ports

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_OUTPUT = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_REPORT = "data/outputs/v2_right_sizing_report.md"

GROWTH_MULTIPLIERS = {
    "now": 1.0,
    "2035_base": 1.8,
    "2035_high": 2.5,
    "2050_base": 3.0,
    "2050_high": 4.5,
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def to_number(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default: int = 0) -> int:
    return int(round(to_number(value, default)))


def even_ceiling(value: float, minimum: int = 2, maximum: int = 12) -> int:
    """Round a capacity target up to a practical even number."""
    if value <= minimum:
        return minimum
    rounded = int(math.ceil(value))
    if rounded % 2 == 1:
        rounded += 1
    return max(minimum, min(maximum, rounded))


def ports_for_sessions(row: pd.Series, multiplier: float) -> int:
    sessions = to_number(row.get("expected_sessions_day", 0.3), 0.3) * multiplier
    avg_session_hr = to_number(row.get("avg_dwell_min", 120), 120) / 60
    hours_open = to_number(row.get("hours_open", 8), 8)
    ports, _, _ = choose_ports(sessions, avg_session_hr, hours_open)
    return max(2, int(ports))


def site_capacity_cap(row: pd.Series) -> int:
    """Approximate practical future-ready capacity from parking size."""
    parking_spaces = to_number(row.get("parking_spaces", 0), 0)
    if parking_spaces <= 0:
        return 6
    return even_ceiling(parking_spaces * 0.05, minimum=2, maximum=12)


def apply_strategy_floors(row: pd.Series, targets: dict[str, int]) -> dict[str, int]:
    """Add planning floors so strong sites preserve expansion room."""
    rank = to_int(row.get("model_rank", 99), 99)
    score = to_number(row.get("readiness_score", 0), 0)
    tier = str(row.get("recommendation_tier", ""))
    existing_ports = to_number(row.get("existing_ports_total", 0), 0)
    site_type = str(row.get("site_type", "")).lower()
    risk = str(row.get("electrical_risk_level", "medium")).lower()
    public_access = to_number(row.get("public_access", 1), 1)

    adjusted = dict(targets)

    if public_access < 1:
        adjusted["ports_now"] = min(adjusted["ports_now"], 2)
        adjusted["ports_2035_base"] = min(adjusted["ports_2035_base"], 2)
        adjusted["ports_2035_high"] = min(adjusted["ports_2035_high"], 2)
        adjusted["ports_2050_base"] = min(adjusted["ports_2050_base"], 2)
        adjusted["ports_2050_high"] = min(adjusted["ports_2050_high"], 2)
        return adjusted

    if tier.startswith("Tier 1"):
        adjusted["ports_2035_base"] = max(adjusted["ports_2035_base"], 4)
        adjusted["ports_2035_high"] = max(adjusted["ports_2035_high"], 6)
        adjusted["ports_2050_base"] = max(adjusted["ports_2050_base"], 6)
        adjusted["ports_2050_high"] = max(adjusted["ports_2050_high"], 8)
    elif score >= 50 and rank <= 6 and "garage" not in site_type:
        adjusted["ports_2035_base"] = max(adjusted["ports_2035_base"], 4)
        adjusted["ports_2035_high"] = max(adjusted["ports_2035_high"], 4)
        adjusted["ports_2050_base"] = max(adjusted["ports_2050_base"], 4)
        adjusted["ports_2050_high"] = max(adjusted["ports_2050_high"], 6)
    elif tier.startswith("Tier 2"):
        adjusted["ports_2035_high"] = max(adjusted["ports_2035_high"], 4)
        adjusted["ports_2050_base"] = max(adjusted["ports_2050_base"], 4)
        adjusted["ports_2050_high"] = max(adjusted["ports_2050_high"], 4)

    if existing_ports >= 50 and score < 45:
        adjusted["ports_2035_base"] = min(adjusted["ports_2035_base"], 2)
        adjusted["ports_2035_high"] = min(adjusted["ports_2035_high"], 4)
        adjusted["ports_2050_base"] = min(adjusted["ports_2050_base"], 4)
        adjusted["ports_2050_high"] = min(adjusted["ports_2050_high"], 4)

    if risk == "high":
        adjusted["ports_now"] = min(adjusted["ports_now"], 2)
        adjusted["ports_2035_base"] = min(adjusted["ports_2035_base"], 4)
        adjusted["ports_2035_high"] = min(adjusted["ports_2035_high"], 4)
        adjusted["ports_2050_base"] = min(adjusted["ports_2050_base"], 4)
        adjusted["ports_2050_high"] = min(adjusted["ports_2050_high"], 6)

    return adjusted


def build_strategy(row: pd.Series, future_ready_capacity: int) -> tuple[str, str]:
    rank = to_int(row.get("model_rank", 99), 99)
    score = to_number(row.get("readiness_score", 0), 0)
    tier = str(row.get("recommendation_tier", ""))
    risk = str(row.get("electrical_risk_level", "medium")).lower()
    existing_ports = to_number(row.get("existing_ports_total", 0), 0)
    site_type = str(row.get("site_type", "")).lower()
    public_access = to_number(row.get("public_access", 1), 1)

    if public_access < 1:
        return (
            "do_not_advance_general_public_buildout",
            "Limited or non-public access means port planning should wait until the use case is confirmed.",
        )

    if risk == "high":
        return (
            "electrical_review_before_expansion",
            "Install conservatively and complete electrical/AHJ review before planning larger expansion.",
        )

    if "garage" in site_type:
        return (
            "garage_review_before_buildout",
            "Garage context requires fire/AHJ/access review before treating the site as a normal expansion candidate.",
        )

    if tier.startswith("Tier 1") or (rank <= 3 and score >= 50):
        return (
            "install_now_and_make_future_ready",
            f"Strong ranking supports installing starter ports now while preparing pathway capacity for about {future_ready_capacity} ports.",
        )

    if score >= 45:
        return (
            "starter_install_with_expandable_design",
            f"Promising candidate; install starter ports and preserve room or conduit for about {future_ready_capacity} future-ready ports.",
        )

    if existing_ports >= 50:
        return (
            "monitor_due_to_nearby_supply",
            "Nearby existing charging supply is high, so keep the buildout conservative unless local need is confirmed.",
        )

    return (
        "monitor_or_small_pilot",
        "Lower current readiness suggests a small pilot or monitoring approach before larger investment.",
    )


def run_right_sizing(results: pd.DataFrame, electrical_summary: pd.DataFrame | None = None) -> pd.DataFrame:
    df = results.copy()

    if electrical_summary is not None and not electrical_summary.empty:
        cols = ["site_id", "electrical_risk_level", "electrical_risk_reason"]
        available = [col for col in cols if col in electrical_summary.columns]
        df = df.merge(electrical_summary[available], on="site_id", how="left")

    if "electrical_risk_level" not in df.columns:
        df["electrical_risk_level"] = "medium"
    df["electrical_risk_level"] = df["electrical_risk_level"].fillna("medium")

    if "existing_ports_total" not in df.columns:
        df["existing_ports_total"] = to_number(0)
        if "existing_l2_ports_1mi" in df.columns and "existing_dcfc_ports_3mi" in df.columns:
            df["existing_ports_total"] = (
                pd.to_numeric(df["existing_l2_ports_1mi"], errors="coerce").fillna(0)
                + pd.to_numeric(df["existing_dcfc_ports_3mi"], errors="coerce").fillna(0)
            )

    rows = []
    for _, row in df.iterrows():
        model_ports_now = to_int(row.get("recommended_ports_now", 2), 2)
        targets = {
            "ports_now": max(2, model_ports_now),
            "ports_2035_base": ports_for_sessions(row, GROWTH_MULTIPLIERS["2035_base"]),
            "ports_2035_high": ports_for_sessions(row, GROWTH_MULTIPLIERS["2035_high"]),
            "ports_2050_base": ports_for_sessions(row, GROWTH_MULTIPLIERS["2050_base"]),
            "ports_2050_high": ports_for_sessions(row, GROWTH_MULTIPLIERS["2050_high"]),
        }
        targets = apply_strategy_floors(row, targets)

        cap = site_capacity_cap(row)
        for key in ["ports_2035_base", "ports_2035_high", "ports_2050_base", "ports_2050_high"]:
            targets[key] = min(targets[key], cap)

        future_ready_capacity = max(
            targets["ports_now"],
            targets["ports_2035_high"],
            targets["ports_2050_base"],
        )
        if str(row.get("recommendation_tier", "")).startswith("Tier 1"):
            future_ready_capacity = max(future_ready_capacity, min(targets["ports_2050_high"], cap))
        future_ready_capacity = min(future_ready_capacity, cap)

        strategy, reason = build_strategy(row, future_ready_capacity)

        rows.append(
            {
                "site_id": row.get("site_id"),
                "site_name": row.get("site_name"),
                "model_rank": to_int(row.get("model_rank", 0), 0),
                "readiness_score": to_number(row.get("readiness_score", 0), 0),
                "recommendation_tier": row.get("recommendation_tier", ""),
                "electrical_risk_level": row.get("electrical_risk_level", "medium"),
                "expected_sessions_day_now": round(to_number(row.get("expected_sessions_day", 0.3), 0.3), 3),
                "model_recommended_ports_now": model_ports_now,
                "ports_now": targets["ports_now"],
                "ports_2035_base": targets["ports_2035_base"],
                "ports_2035_high": targets["ports_2035_high"],
                "ports_2050_base": targets["ports_2050_base"],
                "ports_2050_high": targets["ports_2050_high"],
                "site_capacity_cap": cap,
                "future_ready_capacity": future_ready_capacity,
                "expansion_strategy": strategy,
                "right_sizing_reason": reason,
            }
        )

    return pd.DataFrame(rows).sort_values("model_rank").reset_index(drop=True)


def build_report(right_sizing: pd.DataFrame) -> str:
    lines = [
        "# V2 Right-Sizing Scenario Report",
        "",
        "## Purpose",
        "",
        "This report separates near-term installation from future-ready planning capacity.",
        "The goal is to avoid overbuilding today while still preparing strong sites for 2035 and 2050 growth.",
        "",
        "## Growth cases",
        "",
        "```text",
        "2035_base: current estimated sessions x 1.8",
        "2035_high: current estimated sessions x 2.5",
        "2050_base: current estimated sessions x 3.0",
        "2050_high: current estimated sessions x 4.5",
        "```",
        "",
        "## Top site right-sizing recommendations",
        "",
        "| Rank | Site | Now | 2035 Base | 2035 High | 2050 Base | 2050 High | Future-ready | Strategy |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for _, row in right_sizing.head(8).iterrows():
        lines.append(
            f"| {int(row['model_rank'])} | {row['site_id']} | {int(row['ports_now'])} | "
            f"{int(row['ports_2035_base'])} | {int(row['ports_2035_high'])} | "
            f"{int(row['ports_2050_base'])} | {int(row['ports_2050_high'])} | "
            f"{int(row['future_ready_capacity'])} | {row['expansion_strategy']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation guide",
            "",
            "`ports_now` is the near-term install recommendation.",
            "`ports_2035_base` and `ports_2050_base` are expected-growth planning targets.",
            "`ports_2035_high` and `ports_2050_high` are faster-growth stress cases.",
            "`future_ready_capacity` means the site should preserve space, conduit, or electrical pathway for that many ports if practical.",
            "",
            "A future-ready recommendation does not mean every port should be installed now.",
            "It means the site should avoid design choices that make later expansion expensive.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 right-sizing scenario analysis.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Path to V2 site results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="Path to electrical risk summary CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Right-sizing scenario CSV output.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Right-sizing Markdown report output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    electrical_path = Path(args.electrical_summary)
    output_path = Path(args.output)
    report_path = Path(args.report)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}. Run python src/run_v2.py first.")

    results = pd.read_csv(results_path)
    electrical = pd.read_csv(electrical_path) if electrical_path.exists() else None

    right_sizing = run_right_sizing(results, electrical)

    ensure_parent_dir(output_path)
    ensure_parent_dir(report_path)
    right_sizing.to_csv(output_path, index=False)
    report_path.write_text(build_report(right_sizing), encoding="utf-8")

    print("V2 RIGHT-SIZING SCENARIO ANALYSIS")
    print("---------------------------------")
    print(f"Input results: {results_path}")
    print(f"Right-sizing output: {output_path}")
    print(f"Report output: {report_path}")
    print()
    display_cols = [
        "model_rank",
        "site_id",
        "site_name",
        "ports_now",
        "ports_2035_base",
        "ports_2035_high",
        "ports_2050_base",
        "ports_2050_high",
        "future_ready_capacity",
        "expansion_strategy",
    ]
    print(right_sizing[display_cols].to_string(index=False))
    print()
    print("Done. Use the right-sizing report to separate near-term install from future-ready planning.")


if __name__ == "__main__":
    main()
