"""Run scoring-profile analysis for EV charging candidate sites.

The main model uses one V1 weighting setup. This script tests several planning
priority profiles, such as demand priority, equity priority, feasibility
priority, and safety priority.

It does not replace the main ranking. It helps show whether rankings stay stable
when public priorities change.

Run from the repository root after the main model has generated site_results.csv:

    python src/run_profile_analysis.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_RESULTS = "data/outputs/site_results.csv"
DEFAULT_INPUT_SITES = "data/inputs/real_sites_v1.csv"
DEFAULT_PROFILES = "data/config/scoring_profiles.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_PROFILE_SUMMARY = "data/outputs/profile_rank_summary.csv"
DEFAULT_PROFILE_REPORT = "data/outputs/profile_comparison.md"

REQUIRED_PROFILE_COLUMNS = [
    "profile_name",
    "profile_label",
    "description",
    "demand_weight",
    "feasibility_weight",
    "safety_weight",
    "equity_weight",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scoring-profile analysis.")
    parser.add_argument("--site-results", default=DEFAULT_SITE_RESULTS, help="Generated site_results.csv path.")
    parser.add_argument("--input-sites", default=DEFAULT_INPUT_SITES, help="Input candidate-site CSV path.")
    parser.add_argument("--profiles", default=DEFAULT_PROFILES, help="Scoring profiles CSV path.")
    parser.add_argument("--output", default=DEFAULT_PROFILE_RESULTS, help="Profile-level output CSV path.")
    parser.add_argument("--summary-output", default=DEFAULT_PROFILE_SUMMARY, help="Profile rank summary CSV path.")
    parser.add_argument("--report-output", default=DEFAULT_PROFILE_REPORT, help="Markdown report path.")
    return parser.parse_args()


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    if values.max() == values.min():
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - values.min()) / (values.max() - values.min())


def yesno_to_num(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip().lower()
    return 1.0 if value in {"1", "y", "yes", "true", "t"} else 0.0


def load_profiles(path: Path) -> pd.DataFrame:
    profiles = pd.read_csv(path)
    missing = [column for column in REQUIRED_PROFILE_COLUMNS if column not in profiles.columns]
    if missing:
        raise SystemExit(f"Scoring profiles file is missing columns: {missing}")

    weight_columns = ["demand_weight", "feasibility_weight", "safety_weight", "equity_weight"]
    for column in weight_columns:
        profiles[column] = pd.to_numeric(profiles[column], errors="coerce")

    if profiles[weight_columns].isna().any().any():
        raise SystemExit("Scoring profiles file has blank or non-numeric weights.")

    weight_totals = profiles[weight_columns].sum(axis=1)
    if not np.allclose(weight_totals, 1.0):
        bad_profiles = profiles.loc[~np.isclose(weight_totals, 1.0), "profile_name"].tolist()
        raise SystemExit(f"Each profile's weights must sum to 1. Problem profiles: {bad_profiles}")

    return profiles


def build_profile_tier(row: pd.Series) -> str:
    if row["public_access"] == 0:
        return "Low public-priority / special-use"
    if row["garage_enclosed"] == 1:
        return "High-review candidate"
    if row["profile_rank"] <= 2 and row["profile_readiness_score"] >= 50:
        return "Tier 1 — advance to site screening"
    if row["profile_readiness_score"] >= 45:
        return "Tier 2 — promising candidate, refine data"
    return "Tier 3 — lower priority / monitor"


def prepare_site_data(site_results_path: Path, input_sites_path: Path) -> pd.DataFrame:
    results = pd.read_csv(site_results_path)
    inputs = pd.read_csv(input_sites_path)

    needed_input_columns = ["site_id", "equity_gap_index", "public_access", "garage_enclosed"]
    missing_input = [column for column in needed_input_columns if column not in inputs.columns]
    if missing_input:
        raise SystemExit(f"Input sites file is missing columns needed for profile analysis: {missing_input}")

    needed_result_columns = [
        "site_id",
        "site_name",
        "site_type",
        "model_rank",
        "readiness_score",
        "recommendation_tier",
        "demand_subscore",
        "feasibility_subscore",
        "safety_subscore",
    ]
    missing_results = [column for column in needed_result_columns if column not in results.columns]
    if missing_results:
        raise SystemExit(f"site_results.csv is missing columns needed for profile analysis: {missing_results}")

    context = inputs[needed_input_columns].copy()
    context["equity_gap_index"] = pd.to_numeric(context["equity_gap_index"], errors="coerce").fillna(0)
    context["equity_score"] = 100 * minmax(context["equity_gap_index"])
    context["public_access"] = context["public_access"].apply(yesno_to_num)
    context["garage_enclosed"] = context["garage_enclosed"].apply(yesno_to_num)
    context["readiness_access_adjustment"] = np.where(context["public_access"] >= 1, 1.00, 0.65)

    sites = results[needed_result_columns].merge(context, on="site_id", how="left")
    if sites["equity_score"].isna().any():
        missing_sites = sites.loc[sites["equity_score"].isna(), "site_id"].tolist()
        raise SystemExit(f"Could not merge input context for sites: {missing_sites}")

    return sites


def run_profiles(sites: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, profile in profiles.iterrows():
        scored = sites.copy()
        raw_score = (
            profile["demand_weight"] * scored["demand_subscore"]
            + profile["feasibility_weight"] * scored["feasibility_subscore"]
            + profile["safety_weight"] * scored["safety_subscore"]
            + profile["equity_weight"] * scored["equity_score"]
        )
        scored["profile_readiness_score"] = (raw_score * scored["readiness_access_adjustment"]).round(1)
        scored = scored.sort_values("profile_readiness_score", ascending=False).reset_index(drop=True)
        scored["profile_rank"] = range(1, len(scored) + 1)

        for _, row in scored.iterrows():
            output_row = {
                "profile_name": profile["profile_name"],
                "profile_label": profile["profile_label"],
                "profile_description": profile["description"],
                "demand_weight": profile["demand_weight"],
                "feasibility_weight": profile["feasibility_weight"],
                "safety_weight": profile["safety_weight"],
                "equity_weight": profile["equity_weight"],
                "profile_rank": row["profile_rank"],
                "site_id": row["site_id"],
                "site_name": row["site_name"],
                "site_type": row["site_type"],
                "profile_readiness_score": row["profile_readiness_score"],
                "base_model_rank": row["model_rank"],
                "base_readiness_score": row["readiness_score"],
                "rank_change_vs_base": row["profile_rank"] - row["model_rank"],
                "base_recommendation_tier": row["recommendation_tier"],
                "profile_recommendation_tier": "",
                "demand_subscore": row["demand_subscore"],
                "feasibility_subscore": row["feasibility_subscore"],
                "safety_subscore": row["safety_subscore"],
                "equity_score": row["equity_score"],
                "public_access": row["public_access"],
                "garage_enclosed": row["garage_enclosed"],
            }
            rows.append(output_row)

    profile_results = pd.DataFrame(rows)
    profile_results["profile_recommendation_tier"] = profile_results.apply(build_profile_tier, axis=1)
    return profile_results


def summarize_profiles(profile_results: pd.DataFrame) -> pd.DataFrame:
    summary = (
        profile_results.groupby(["site_id", "site_name"], as_index=False)
        .agg(
            best_profile_rank=("profile_rank", "min"),
            worst_profile_rank=("profile_rank", "max"),
            average_profile_rank=("profile_rank", "mean"),
            min_profile_score=("profile_readiness_score", "min"),
            max_profile_score=("profile_readiness_score", "max"),
            average_profile_score=("profile_readiness_score", "mean"),
            base_model_rank=("base_model_rank", "first"),
            base_readiness_score=("base_readiness_score", "first"),
        )
        .sort_values(["average_profile_rank", "best_profile_rank"])
    )
    summary["profile_rank_range"] = summary["worst_profile_rank"] - summary["best_profile_rank"]
    summary["profile_score_range"] = summary["max_profile_score"] - summary["min_profile_score"]
    return summary


def build_markdown_report(profile_results: pd.DataFrame, summary: pd.DataFrame) -> str:
    lines: list[str] = []
    lines.append("# Scoring Profile Comparison")
    lines.append("")
    lines.append("This report tests how site rankings change when different planning priorities are emphasized.")
    lines.append("")
    lines.append("The main model ranking is not replaced. Profile analysis is a planning-sensitivity layer.")
    lines.append("")

    lines.append("## Profiles tested")
    lines.append("")
    profile_table = profile_results[
        ["profile_name", "profile_label", "profile_description", "demand_weight", "feasibility_weight", "safety_weight", "equity_weight"]
    ].drop_duplicates()
    for _, row in profile_table.iterrows():
        lines.append(
            f"- `{row['profile_name']}`: {row['profile_description']} "
            f"(demand={row['demand_weight']:.2f}, feasibility={row['feasibility_weight']:.2f}, "
            f"safety={row['safety_weight']:.2f}, equity={row['equity_weight']:.2f})"
        )
    lines.append("")

    lines.append("## Top site by profile")
    lines.append("")
    lines.append("| Profile | Rank 1 site | Score | Tier |")
    lines.append("|---|---|---:|---|")
    for profile_name, group in profile_results.groupby("profile_name", sort=False):
        top = group.sort_values("profile_rank").iloc[0]
        lines.append(
            f"| {profile_name} | {top['site_id']} — {top['site_name']} | "
            f"{top['profile_readiness_score']:.1f} | {top['profile_recommendation_tier']} |"
        )
    lines.append("")

    lines.append("## Rank stability across profiles")
    lines.append("")
    lines.append("| Site | Base rank | Best profile rank | Worst profile rank | Rank range | Average profile rank |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['site_id']} — {row['site_name']} | {int(row['base_model_rank'])} | "
            f"{int(row['best_profile_rank'])} | {int(row['worst_profile_rank'])} | "
            f"{int(row['profile_rank_range'])} | {row['average_profile_rank']:.2f} |"
        )
    lines.append("")

    stable_sites = summary.loc[summary["profile_rank_range"] == 0, "site_id"].tolist()
    moving_sites = summary.loc[summary["profile_rank_range"] > 0, "site_id"].tolist()
    lines.append("## Quick interpretation")
    lines.append("")
    lines.append(f"- Sites with no rank movement across profiles: `{stable_sites}`")
    lines.append(f"- Sites that move when priorities change: `{moving_sites}`")
    lines.append("")
    lines.append("Generated profile outputs stay local under `data/outputs/` and are ignored by Git.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    site_results_path = PROJECT_ROOT / args.site_results
    input_sites_path = PROJECT_ROOT / args.input_sites
    profiles_path = PROJECT_ROOT / args.profiles
    output_path = PROJECT_ROOT / args.output
    summary_output_path = PROJECT_ROOT / args.summary_output
    report_output_path = PROJECT_ROOT / args.report_output

    if not site_results_path.exists():
        raise FileNotFoundError(f"Site results file not found: {site_results_path}")
    if not input_sites_path.exists():
        raise FileNotFoundError(f"Input sites file not found: {input_sites_path}")
    if not profiles_path.exists():
        raise FileNotFoundError(f"Scoring profiles file not found: {profiles_path}")

    sites = prepare_site_data(site_results_path, input_sites_path)
    profiles = load_profiles(profiles_path)
    profile_results = run_profiles(sites, profiles)
    summary = summarize_profiles(profile_results)

    ensure_parent_dir(output_path)
    ensure_parent_dir(summary_output_path)
    ensure_parent_dir(report_output_path)

    profile_results.to_csv(output_path, index=False)
    summary.to_csv(summary_output_path, index=False)
    report_output_path.write_text(build_markdown_report(profile_results, summary), encoding="utf-8")

    print("SCORING PROFILE ANALYSIS")
    print("------------------------")
    print(f"Profiles tested: {len(profiles)}")
    print(f"Sites analyzed: {sites['site_id'].nunique()}")
    print(f"Saved: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {summary_output_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {report_output_path.relative_to(PROJECT_ROOT)}")
    print()
    print("Top site by profile:")
    for profile_name, group in profile_results.groupby("profile_name", sort=False):
        top = group.sort_values("profile_rank").iloc[0]
        print(f"- {profile_name}: {top['site_id']} ({top['profile_readiness_score']:.1f})")


if __name__ == "__main__":
    main()
