"""Generate a dynamic plain-English interpretation of the latest model outputs.

This script creates a generated interpretation file from the current CSV outputs.
It is meant to complement the static documentation in docs/.

Run from the repository root after the model pipeline has produced outputs:

    python src/generate_results_interpretation.py

Default output:

    data/outputs/results_interpretation.md
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_QUALITY = "data/outputs/data_quality_report.csv"
DEFAULT_SENSITIVITY = "data/outputs/sensitivity_summary.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/results_interpretation.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dynamic results interpretation Markdown.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model site results CSV.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, help="Data-quality report CSV.")
    parser.add_argument("--sensitivity", default=DEFAULT_SENSITIVITY, help="Sensitivity summary CSV.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Scoring profile results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output Markdown path.")
    return parser.parse_args()


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No data available._"

    available = [column for column in columns if column in df.columns]
    if not available:
        return "_No matching columns available._"

    view = df[available].copy()
    view.columns = [column.replace("_", " ") for column in view.columns]

    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows: list[str] = []
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in view.columns) + " |")
    return "\n".join([header, separator] + rows)


def get_ranked_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results
    if "model_rank" not in results.columns:
        return results
    ranked = results.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    return ranked.sort_values("model_rank")


def top_candidate_text(results: pd.DataFrame) -> str:
    ranked = get_ranked_results(results)
    if ranked.empty:
        return "No model results were found."

    top = ranked.iloc[0]
    return (
        f"The current top candidate is `{top.get('site_id', '')}` — {top.get('site_name', '')} "
        f"with readiness score `{top.get('readiness_score', '')}` and tier `{top.get('recommendation_tier', '')}`."
    )


def sensitivity_text(sensitivity: pd.DataFrame) -> str:
    if sensitivity.empty:
        return "No sensitivity summary was found."
    if "rank_range" not in sensitivity.columns:
        return "Sensitivity output exists, but `rank_range` was not found."

    rank_range = pd.to_numeric(sensitivity["rank_range"], errors="coerce")
    if rank_range.isna().any():
        return "Sensitivity output has blank or non-numeric rank-range values."
    if (rank_range == 0).all():
        return "The ranking stayed stable across all sensitivity scenarios. Every site had `rank_range = 0`."

    max_range = int(rank_range.max())
    moving_sites = sensitivity.loc[rank_range > 0, "site_id"].astype(str).tolist() if "site_id" in sensitivity.columns else []
    return f"Some sites moved across sensitivity scenarios. Maximum rank movement was `{max_range}`. Moving sites: `{moving_sites}`."


def profile_text(profile_results: pd.DataFrame) -> str:
    required = {"profile_name", "profile_rank", "site_id", "site_name", "profile_readiness_score"}
    if profile_results.empty:
        return "No scoring profile results were found."
    if not required.issubset(profile_results.columns):
        return "Profile output exists, but required columns were not found."

    top_by_profile = (
        profile_results.sort_values(["profile_name", "profile_rank"])
        .groupby("profile_name", as_index=False)
        .first()
    )
    top_sites = top_by_profile["site_id"].astype(str).unique().tolist()

    if len(top_sites) == 1:
        top_site = top_sites[0]
        profile_count = len(top_by_profile)
        return f"`{top_site}` ranked #1 across all `{profile_count}` scoring profiles, so the top recommendation is stable across different planning priorities."

    return f"The #1 site changed across scoring profiles. Top sites by profile were: `{top_sites}`."


def quality_text(quality: pd.DataFrame) -> str:
    if quality.empty or "severity" not in quality.columns:
        return "No data-quality report was found."

    counts = quality["severity"].value_counts().to_dict()
    return (
        f"Data-quality counts: ERROR `{counts.get('ERROR', 0)}`, WARNING `{counts.get('WARNING', 0)}`, "
        f"REVIEW `{counts.get('REVIEW', 0)}`, INFO `{counts.get('INFO', 0)}`."
    )


def site_interpretation(row: pd.Series) -> str:
    site_id = row.get("site_id", "")
    site_name = row.get("site_name", "")
    rank = row.get("model_rank", "")
    score = row.get("readiness_score", "")
    tier = row.get("recommendation_tier", "")
    priority_reason = row.get("priority_reason", "")
    planning_recommendation = row.get("planning_recommendation", "")
    review_reason = row.get("review_reason", "")
    data_needed = row.get("data_needed_next", "")

    lines = [f"### {site_id} — {site_name}", ""]
    lines.append(f"Rank `{rank}` with readiness score `{score}`. Current tier: `{tier}`.")
    if priority_reason:
        lines.append("")
        lines.append(f"Why it ranks this way: {priority_reason}")
    if planning_recommendation:
        lines.append("")
        lines.append(f"Planning interpretation: {planning_recommendation}")
    if review_reason and review_reason != "No obvious model-level review trigger":
        lines.append("")
        lines.append(f"Review trigger: {review_reason}")
    if data_needed:
        lines.append("")
        lines.append(f"Next data needed: {data_needed}")
    lines.append("")
    return "\n".join(lines)


def build_interpretation(
    results: pd.DataFrame,
    quality: pd.DataFrame,
    sensitivity: pd.DataFrame,
    profile_results: pd.DataFrame,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    ranked = get_ranked_results(results)

    lines: list[str] = []
    lines.append("# Generated Results Interpretation")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("This file is generated from the latest local model outputs. It should be regenerated after model, data, or scoring changes.")
    lines.append("")

    lines.append("## Main finding")
    lines.append("")
    lines.append(top_candidate_text(ranked))
    lines.append("")
    lines.append(sensitivity_text(sensitivity))
    lines.append("")
    lines.append(profile_text(profile_results))
    lines.append("")
    lines.append(quality_text(quality))
    lines.append("")

    lines.append("## Ranked results")
    lines.append("")
    lines.append(
        markdown_table(
            ranked,
            ["model_rank", "site_id", "site_name", "readiness_score", "recommendation_tier", "recommended_ports_now", "recommended_ports_2035", "recommended_ports_2050"],
        )
    )
    lines.append("")

    lines.append("## Site-by-site interpretation")
    lines.append("")
    if ranked.empty:
        lines.append("_No site-level results found._")
        lines.append("")
    else:
        for _, row in ranked.iterrows():
            lines.append(site_interpretation(row))

    lines.append("## What this result means")
    lines.append("")
    lines.append("The result identifies stronger and weaker early planning candidates under the current data, assumptions, and scoring logic.")
    lines.append("")
    lines.append("A high rank does not mean a site is ready to build. It means the site is a stronger candidate for stakeholder review, site screening, and data confirmation.")
    lines.append("")

    lines.append("## What this result does not replace")
    lines.append("")
    lines.append("This generated interpretation does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    quality_path = Path(args.quality)
    sensitivity_path = Path(args.sensitivity)
    profile_results_path = Path(args.profile_results)
    output_path = Path(args.output)

    results = read_csv_if_exists(results_path)
    quality = read_csv_if_exists(quality_path)
    sensitivity = read_csv_if_exists(sensitivity_path)
    profile_results = read_csv_if_exists(profile_results_path)

    ensure_parent_dir(output_path)
    output_path.write_text(
        build_interpretation(results, quality, sensitivity, profile_results),
        encoding="utf-8",
    )

    print("GENERATED RESULTS INTERPRETATION")
    print("--------------------------------")
    print(f"Results file: {results_path if results_path.exists() else 'not found'}")
    print(f"Quality file: {quality_path if quality_path.exists() else 'not found'}")
    print(f"Sensitivity file: {sensitivity_path if sensitivity_path.exists() else 'not found'}")
    print(f"Profile results file: {profile_results_path if profile_results_path.exists() else 'not found'}")
    print(f"Saved interpretation: {output_path}")


if __name__ == "__main__":
    main()
