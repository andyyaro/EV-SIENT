"""Run scenario sensitivity analysis for the EV charger site-readiness model.

This script tests whether rankings are stable when uncertain assumptions change.
It does not replace confirmed facility, utility, or stakeholder data.

Default usage:
    python run_sensitivity_analysis.py

Outputs:
    sensitivity_results.csv
    sensitivity_summary.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ev_charger_model import enrich_and_score


SCENARIOS = {
    "low_demand_high_cost": {
        "description": "Lower visitor/employee demand and EV adoption; higher planning install cost.",
        "employees_day_multiplier": 0.75,
        "visitors_day_multiplier": 0.75,
        "ev_share_local_multiplier": 0.80,
        "service_upgrade_cost_multiplier": 1.25,
        "trenching_ft_multiplier": 1.15,
    },
    "base_case": {
        "description": "Current best V1 dataset values.",
        "employees_day_multiplier": 1.00,
        "visitors_day_multiplier": 1.00,
        "ev_share_local_multiplier": 1.00,
        "service_upgrade_cost_multiplier": 1.00,
        "trenching_ft_multiplier": 1.00,
    },
    "high_demand_base_cost": {
        "description": "Higher visitor/employee demand and EV adoption; same planning install cost.",
        "employees_day_multiplier": 1.25,
        "visitors_day_multiplier": 1.25,
        "ev_share_local_multiplier": 1.25,
        "service_upgrade_cost_multiplier": 1.00,
        "trenching_ft_multiplier": 1.00,
    },
}


def apply_scenario(df: pd.DataFrame, settings: dict[str, float]) -> pd.DataFrame:
    """Return a scenario-adjusted copy of the site input data."""
    scenario_df = df.copy()

    adjustable_fields = [
        ("employees_day", "employees_day_multiplier"),
        ("visitors_day", "visitors_day_multiplier"),
        ("ev_share_local", "ev_share_local_multiplier"),
        ("service_upgrade_cost_usd", "service_upgrade_cost_multiplier"),
        ("trenching_ft", "trenching_ft_multiplier"),
    ]

    for column, multiplier_name in adjustable_fields:
        if column not in scenario_df.columns:
            continue
        scenario_df[column] = pd.to_numeric(scenario_df[column], errors="coerce").fillna(0)
        scenario_df[column] = scenario_df[column] * settings[multiplier_name]

    # Keep EV share in a realistic percentage range.
    if "ev_share_local" in scenario_df.columns:
        scenario_df["ev_share_local"] = scenario_df["ev_share_local"].clip(lower=0, upper=0.20)

    return scenario_df


def run_scenarios(input_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sites = pd.read_csv(input_path)
    all_results = []

    for scenario_name, settings in SCENARIOS.items():
        scenario_sites = apply_scenario(sites, settings)
        results = enrich_and_score(scenario_sites).copy()
        results.insert(0, "scenario", scenario_name)
        results.insert(1, "scenario_description", settings["description"])
        results["rank"] = range(1, len(results) + 1)
        all_results.append(results)

    sensitivity_results = pd.concat(all_results, ignore_index=True)

    summary = (
        sensitivity_results
        .groupby(["site_id", "site_name"], as_index=False)
        .agg(
            best_rank=("rank", "min"),
            worst_rank=("rank", "max"),
            average_rank=("rank", "mean"),
            min_readiness_score=("readiness_score", "min"),
            max_readiness_score=("readiness_score", "max"),
            average_readiness_score=("readiness_score", "mean"),
        )
        .sort_values(["average_rank", "average_readiness_score"], ascending=[True, False])
    )

    summary["rank_range"] = summary["worst_rank"] - summary["best_rank"]
    summary["readiness_score_range"] = summary["max_readiness_score"] - summary["min_readiness_score"]

    return sensitivity_results, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EV charger model sensitivity scenarios.")
    parser.add_argument("--input", default="real_sites_v1.csv", help="Input candidate-site CSV.")
    parser.add_argument("--results-output", default="sensitivity_results.csv", help="Detailed scenario results CSV.")
    parser.add_argument("--summary-output", default="sensitivity_summary.csv", help="Summary CSV by site.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sensitivity_results, summary = run_scenarios(input_path)
    sensitivity_results.to_csv(args.results_output, index=False)
    summary.to_csv(args.summary_output, index=False)

    print("EV CHARGER SENSITIVITY ANALYSIS")
    print("-------------------------------")
    print(f"Input file: {args.input}")
    print(f"Detailed output: {args.results_output}")
    print(f"Summary output: {args.summary_output}")
    print()
    print("Scenario summary by site:")
    print(summary.to_string(index=False))
    print()
    print("Done. Use sensitivity_summary.csv to see whether rankings are stable.")


if __name__ == "__main__":
    main()
