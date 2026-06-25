"""Run scenario-based electrical-feasibility screening for V2 results.

This script does not pretend to know true utility capacity or panel data. It uses
transparent planning assumptions to classify sites as low, medium, or high
model-level electrical risk, then stress-tests the readiness ranking under three
simple electrical-feasibility scenarios.

Run from the repository root after the V2 model has produced v2_site_results.csv:

    python src/run_electrical_risk_scenarios.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_SCENARIO_OUTPUT = "data/outputs/v2_electrical_scenario_results.csv"
DEFAULT_SUMMARY_OUTPUT = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_REPORT_OUTPUT = "data/outputs/v2_electrical_feasibility_report.md"

SCENARIO_PENALTIES = {
    "optimistic_electrical_case": {"low": 0.0, "medium": 1.0, "high": 2.0},
    "expected_electrical_case": {"low": 0.5, "medium": 3.0, "high": 6.0},
    "conservative_electrical_case": {"low": 2.0, "medium": 6.0, "high": 12.0},
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


def yesno(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 1.0 if str(value).strip().lower() in {"1", "yes", "y", "true", "t"} else 0.0


def classify_electrical_risk(row: pd.Series) -> pd.Series:
    """Return simple electrical-risk screening fields for one site."""
    points = 0.0
    reasons: list[str] = []
    data_needs: list[str] = []

    site_type = str(row.get("site_type", "")).strip().lower()
    service_amp = to_number(row.get("elec_service_rating_amp", 0))
    spare_kw = to_number(row.get("spare_capacity_kw", 0))
    distance_ft = to_number(row.get("distance_to_service_ft", 0))
    trenching_ft = to_number(row.get("trenching_ft", 0))
    upgrade_cost = to_number(row.get("service_upgrade_cost_usd", 0))
    garage = yesno(row.get("garage_enclosed", 0))
    emergency_disconnect = yesno(row.get("emergency_disconnect_visible", 0))
    stormwater = yesno(row.get("stormwater_risk", 0))
    battery = yesno(row.get("battery_storage_flag", 0))
    public_access = yesno(row.get("public_access", 0))

    if service_amp <= 0:
        points += 2
        reasons.append("electrical service rating unknown")
        data_needs.append("confirm electrical service rating")
    elif service_amp < 200:
        points += 2
        reasons.append("low service rating may limit charger capacity")
    elif service_amp < 400:
        points += 1
        reasons.append("moderate service rating may require careful load review")

    if spare_kw <= 0:
        points += 2
        reasons.append("spare capacity unknown")
        data_needs.append("confirm spare capacity or upgrade need")
    elif spare_kw < 20:
        points += 2
        reasons.append("low spare capacity")
    elif spare_kw < 50:
        points += 1
        reasons.append("moderate spare capacity")

    if emergency_disconnect == 0:
        points += 2
        reasons.append("emergency disconnect visibility not confirmed")
        data_needs.append("confirm emergency disconnect location and visibility")

    if garage == 1:
        points += 2
        reasons.append("garage or enclosed-structure context adds fire/AHJ review risk")
        data_needs.append("confirm garage fire/AHJ requirements")

    if public_access == 0:
        points += 1
        reasons.append("public-access/use case is not fully confirmed")

    if distance_ft > 150:
        points += 2
        reasons.append("long service-distance assumption")
    elif distance_ft > 100:
        points += 1
        reasons.append("moderate service-distance assumption")

    if trenching_ft > 150:
        points += 2
        reasons.append("long trenching assumption")
    elif trenching_ft > 100:
        points += 1
        reasons.append("moderate trenching assumption")

    if upgrade_cost >= 45_000:
        points += 2
        reasons.append("high service-upgrade cost assumption")
    elif upgrade_cost >= 25_000:
        points += 1
        reasons.append("moderate service-upgrade cost assumption")

    if stormwater == 1:
        points += 1
        reasons.append("stormwater or runoff review risk")

    if battery == 1:
        points += 2
        reasons.append("battery-storage review risk")

    if "public_safety" in site_type:
        points += 2
        reasons.append("public-safety facility context may limit implementation")

    if points >= 8:
        level = "high"
    elif points >= 4:
        level = "medium"
    else:
        level = "low"

    if not reasons:
        reasons.append("no major model-level electrical risk trigger")
    if not data_needs:
        data_needs.append("confirm final electrical design assumptions before procurement")

    return pd.Series(
        {
            "electrical_risk_points": points,
            "electrical_risk_level": level,
            "electrical_risk_reason": "; ".join(reasons),
            "electrical_data_needed_next": "; ".join(dict.fromkeys(data_needs)),
        }
    )


def build_scenario_results(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    working = results.copy()
    risk_fields = working.apply(classify_electrical_risk, axis=1)
    working = pd.concat([working, risk_fields], axis=1)

    scenario_rows = []
    for scenario_name, penalties in SCENARIO_PENALTIES.items():
        for _, row in working.iterrows():
            risk_level = str(row["electrical_risk_level"])
            penalty = penalties[risk_level]
            adjusted_score = max(0.0, to_number(row.get("readiness_score", 0)) - penalty)
            scenario_rows.append(
                {
                    "scenario": scenario_name,
                    "site_id": row["site_id"],
                    "site_name": row["site_name"],
                    "site_type": row.get("site_type", ""),
                    "base_rank": int(row.get("model_rank", 0)),
                    "base_readiness_score": to_number(row.get("readiness_score", 0)),
                    "electrical_risk_level": risk_level,
                    "electrical_risk_points": row["electrical_risk_points"],
                    "electrical_penalty_points": penalty,
                    "electrical_adjusted_score": round(adjusted_score, 1),
                    "electrical_risk_reason": row["electrical_risk_reason"],
                    "electrical_data_needed_next": row["electrical_data_needed_next"],
                }
            )

    scenario_df = pd.DataFrame(scenario_rows)
    scenario_df = scenario_df.sort_values(["scenario", "electrical_adjusted_score"], ascending=[True, False])
    scenario_df["electrical_adjusted_rank"] = scenario_df.groupby("scenario").cumcount() + 1
    scenario_df = scenario_df.sort_values(["scenario", "electrical_adjusted_rank"]).reset_index(drop=True)

    summary_rows = []
    for site_id, group in scenario_df.groupby("site_id", sort=False):
        expected = group[group["scenario"] == "expected_electrical_case"].iloc[0]
        conservative = group[group["scenario"] == "conservative_electrical_case"].iloc[0]
        optimistic = group[group["scenario"] == "optimistic_electrical_case"].iloc[0]
        summary_rows.append(
            {
                "site_id": site_id,
                "site_name": expected["site_name"],
                "base_rank": int(expected["base_rank"]),
                "base_readiness_score": expected["base_readiness_score"],
                "electrical_risk_level": expected["electrical_risk_level"],
                "electrical_risk_points": expected["electrical_risk_points"],
                "optimistic_rank": int(optimistic["electrical_adjusted_rank"]),
                "expected_rank": int(expected["electrical_adjusted_rank"]),
                "conservative_rank": int(conservative["electrical_adjusted_rank"]),
                "optimistic_score": optimistic["electrical_adjusted_score"],
                "expected_score": expected["electrical_adjusted_score"],
                "conservative_score": conservative["electrical_adjusted_score"],
                "worst_case_rank_change": int(conservative["electrical_adjusted_rank"] - expected["base_rank"]),
                "electrical_risk_reason": expected["electrical_risk_reason"],
                "electrical_data_needed_next": expected["electrical_data_needed_next"],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values(["expected_rank", "conservative_rank"]).reset_index(drop=True)
    return scenario_df, summary_df


def build_report(summary: pd.DataFrame, scenario_results: pd.DataFrame) -> str:
    expected = scenario_results[scenario_results["scenario"] == "expected_electrical_case"].copy()
    conservative = scenario_results[scenario_results["scenario"] == "conservative_electrical_case"].copy()

    expected_top = expected.sort_values("electrical_adjusted_rank").head(5)
    conservative_top = conservative.sort_values("electrical_adjusted_rank").head(5)

    lines = [
        "# V2 Electrical-Feasibility Scenario Report",
        "",
        "## Purpose",
        "",
        "This report stress-tests the V2 candidate rankings under simple electrical-feasibility assumptions.",
        "It does not replace utility, engineering, AHJ, Fire Marshal, or facilities review.",
        "Instead, it helps the prototype avoid pretending that unconfirmed electrical fields are known facts.",
        "",
        "## Scenario definitions",
        "",
        "```text",
        "optimistic_electrical_case: low risk = 0 point penalty, medium = 1, high = 2",
        "expected_electrical_case: low risk = 0.5 point penalty, medium = 3, high = 6",
        "conservative_electrical_case: low risk = 2 point penalty, medium = 6, high = 12",
        "```",
        "",
        "## Top sites under expected electrical case",
        "",
    ]

    for _, row in expected_top.iterrows():
        lines.append(
            f"- Rank {int(row['electrical_adjusted_rank'])}: {row['site_id']} — {row['site_name']} "
            f"({row['electrical_adjusted_score']:.1f}, {row['electrical_risk_level']} electrical risk)"
        )

    lines.extend(["", "## Top sites under conservative electrical case", ""])
    for _, row in conservative_top.iterrows():
        lines.append(
            f"- Rank {int(row['electrical_adjusted_rank'])}: {row['site_id']} — {row['site_name']} "
            f"({row['electrical_adjusted_score']:.1f}, {row['electrical_risk_level']} electrical risk)"
        )

    lines.extend(
        [
            "",
            "## Electrical risk summary",
            "",
            "| Site | Base Rank | Expected Rank | Conservative Rank | Risk | Main reason |",
            "|---|---:|---:|---:|---|---|",
        ]
    )

    for _, row in summary.sort_values("base_rank").iterrows():
        reason = str(row["electrical_risk_reason"]).split("; ")[0]
        lines.append(
            f"| {row['site_id']} | {int(row['base_rank'])} | {int(row['expected_rank'])} | "
            f"{int(row['conservative_rank'])} | {row['electrical_risk_level']} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A site that remains strong under the expected and conservative cases is less sensitive to electrical uncertainty.",
            "A site that drops under the conservative case should not be removed automatically; it should be flagged for earlier electrical review.",
            "",
            "## Data still needed",
            "",
            "The most important next confirmations are:",
            "",
            "```text",
            "electrical service rating",
            "available spare capacity or likely upgrade requirement",
            "electrical room / transformer / service distance",
            "emergency disconnect location and visibility",
            "AHJ and Fire Marshal triggers for garages, batteries, and unusual sites",
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 electrical-feasibility scenario analysis.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Path to V2 site results CSV.")
    parser.add_argument("--scenario-output", default=DEFAULT_SCENARIO_OUTPUT, help="Detailed scenario output CSV.")
    parser.add_argument("--summary-output", default=DEFAULT_SUMMARY_OUTPUT, help="Electrical risk summary CSV.")
    parser.add_argument("--report-output", default=DEFAULT_REPORT_OUTPUT, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    scenario_output = Path(args.scenario_output)
    summary_output = Path(args.summary_output)
    report_output = Path(args.report_output)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}. Run python src/run_v2.py first.")

    results = pd.read_csv(results_path)
    scenario_results, summary = build_scenario_results(results)

    ensure_parent_dir(scenario_output)
    ensure_parent_dir(summary_output)
    ensure_parent_dir(report_output)

    scenario_results.to_csv(scenario_output, index=False)
    summary.to_csv(summary_output, index=False)
    report_output.write_text(build_report(summary, scenario_results), encoding="utf-8")

    print("V2 ELECTRICAL-FEASIBILITY SCENARIO ANALYSIS")
    print("---------------------------------------------")
    print(f"Input results: {results_path}")
    print(f"Detailed output: {scenario_output}")
    print(f"Summary output: {summary_output}")
    print(f"Report output: {report_output}")
    print()
    print("Expected electrical case ranking:")
    expected = scenario_results[scenario_results["scenario"] == "expected_electrical_case"]
    display_cols = [
        "electrical_adjusted_rank",
        "site_id",
        "site_name",
        "base_rank",
        "base_readiness_score",
        "electrical_adjusted_score",
        "electrical_risk_level",
    ]
    print(expected[display_cols].to_string(index=False))
    print()
    print("Done. Use the electrical report to see which candidates are sensitive to electrical uncertainty.")


if __name__ == "__main__":
    main()
