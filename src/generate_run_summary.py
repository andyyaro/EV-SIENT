"""Generate a Markdown summary of the latest model run.

This script reads local generated outputs and writes a concise run summary that
can be copied into reports, slides, emails, or project notes.

Run from the repository root after running the model pipeline:

    python src/generate_run_summary.py

Default output:
- data/outputs/model_run_summary.md
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
DEFAULT_PROFILE_SUMMARY = "data/outputs/profile_rank_summary.csv"
DEFAULT_OUTPUT = "data/outputs/model_run_summary.md"

CHART_OUTPUTS = [
    "data/outputs/charts/readiness_score_chart.png",
    "data/outputs/charts/site_readiness_map.png",
]


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    """Create a simple Markdown table from selected columns."""
    if df.empty:
        return "_No data available._"

    available = [col for col in columns if col in df.columns]
    if not available:
        return "_No matching columns available._"

    view = df[available].copy()
    view.columns = [col.replace("_", " ") for col in view.columns]

    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        values = [str(row[col]) for col in view.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator] + rows)


def quality_summary(quality: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    if quality.empty or "severity" not in quality.columns:
        return "_No data-quality report found._", pd.DataFrame()

    severity_order = ["ERROR", "WARNING", "REVIEW", "INFO"]
    counts = quality["severity"].value_counts().to_dict()
    lines = [f"- **{severity}:** {counts.get(severity, 0)}" for severity in severity_order]

    review_items = quality[quality["severity"].isin(["ERROR", "WARNING", "REVIEW"])].copy()
    return "\n".join(lines), review_items


def remaining_review_summary(review_items: pd.DataFrame) -> str:
    if review_items.empty:
        return "No remaining error, warning, or review items."

    if "field" not in review_items.columns:
        return "Review items exist, but field-level details were not found."

    field_counts = (
        review_items.groupby("field")
        .size()
        .reset_index(name="count")
        .sort_values(["count", "field"], ascending=[False, True])
    )
    return markdown_table(field_counts, ["field", "count"])


def sensitivity_summary_text(sensitivity: pd.DataFrame) -> str:
    if sensitivity.empty:
        return "_No sensitivity summary found._"

    if "rank_range" in sensitivity.columns:
        max_rank_range = sensitivity["rank_range"].max()
        if max_rank_range == 0:
            return "The site ranking stayed stable across all tested sensitivity scenarios (`rank_range = 0` for every site)."
        return f"The maximum rank movement across sensitivity scenarios was `{max_rank_range}`."

    return "Sensitivity output exists, but `rank_range` was not found."


def profile_summary_text(profile_results: pd.DataFrame) -> str:
    if profile_results.empty:
        return "_No scoring profile analysis found._"

    required = {"profile_name", "profile_rank", "site_id", "site_name", "profile_readiness_score"}
    if not required.issubset(profile_results.columns):
        return "Profile output exists, but required profile columns were not found."

    top_by_profile = (
        profile_results.sort_values(["profile_name", "profile_rank"])
        .groupby("profile_name", as_index=False)
        .first()
    )
    top_sites = top_by_profile["site_id"].astype(str).unique().tolist()

    if len(top_sites) == 1:
        top_site = top_sites[0]
        profiles_tested = len(top_by_profile)
        return f"`{top_site}` stayed ranked #1 across all `{profiles_tested}` scoring profiles. This means the top recommendation is stable when demand, equity, feasibility, or safety is weighted more heavily."

    return f"Top-ranked sites changed across scoring profiles: `{top_sites}`. Review `data/outputs/profile_comparison.md` for details."


def profile_top_table(profile_results: pd.DataFrame) -> str:
    if profile_results.empty:
        return "_No scoring profile analysis found._"

    required = {"profile_name", "profile_rank", "site_id", "site_name", "profile_readiness_score"}
    if not required.issubset(profile_results.columns):
        return "_Profile output exists, but required profile columns were not found._"

    top_by_profile = (
        profile_results.sort_values(["profile_name", "profile_rank"])
        .groupby("profile_name", as_index=False)
        .first()
        .sort_values("profile_name")
    )
    return markdown_table(
        top_by_profile,
        ["profile_name", "site_id", "site_name", "profile_readiness_score"],
    )


def confidence_summary_text(results: pd.DataFrame) -> str:
    if results.empty or "data_confidence_level" not in results.columns:
        return "_No data-confidence output found._"

    counts = results["data_confidence_level"].value_counts().to_dict()
    return (
        f"Data confidence levels: High={counts.get('High', 0)}, "
        f"Medium={counts.get('Medium', 0)}, Low={counts.get('Low', 0)}."
    )


def build_summary(
    results: pd.DataFrame,
    quality: pd.DataFrame,
    sensitivity: pd.DataFrame,
    profile_results: pd.DataFrame,
    profile_summary: pd.DataFrame,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    quality_text, review_items = quality_summary(quality)
    sensitivity_text = sensitivity_summary_text(sensitivity)
    profile_text = profile_summary_text(profile_results)
    confidence_text = confidence_summary_text(results)

    if results.empty:
        top_line = "_No model results found._"
    else:
        ranked = results.sort_values("model_rank") if "model_rank" in results.columns else results.copy()
        top = ranked.iloc[0]
        top_line = (
            f"**Top candidate:** {top.get('site_id', '')} — {top.get('site_name', '')} "
            f"with readiness score **{top.get('readiness_score', '')}** "
            f"and data confidence **{top.get('data_confidence_level', 'not available')}**."
        )

    ranking_table = markdown_table(
        results.sort_values("model_rank") if not results.empty and "model_rank" in results.columns else results,
        [
            "model_rank",
            "site_id",
            "site_name",
            "readiness_score",
            "data_confidence_score",
            "data_confidence_level",
            "recommendation_tier",
            "recommended_ports_now",
            "recommended_ports_2035",
            "recommended_ports_2050",
        ],
    )

    confidence_table = markdown_table(
        results.sort_values("model_rank") if not results.empty and "model_rank" in results.columns else results,
        ["model_rank", "site_id", "readiness_score", "data_confidence_score", "data_confidence_level", "data_confidence_reason"],
    )

    review_table = remaining_review_summary(review_items)
    profile_table = profile_top_table(profile_results)
    chart_lines = "\n".join([f"- `{path}`" for path in CHART_OUTPUTS])

    summary = f"""# Model Run Summary

Generated: {generated_at}

## Executive summary

{top_line}

{sensitivity_text}

{profile_text}

{confidence_text}

This is a planning-support output only. It does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.

## Data-quality summary

{quality_text}

## Current ranking, confidence, and right-sizing output

{ranking_table}

## Data confidence summary

{confidence_table}

## Remaining review items by field

{review_table}

## Sensitivity summary

{sensitivity_text}

## Scoring profile summary

{profile_text}

{profile_table}

See `data/outputs/profile_comparison.md` for the full scoring-profile report.

## Generated visual outputs

{chart_lines}

## Next data to improve

The highest-priority remaining confirmations are:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
```
"""
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown summary of the latest model run.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, help="Data-quality report CSV.")
    parser.add_argument("--sensitivity", default=DEFAULT_SENSITIVITY, help="Sensitivity summary CSV.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Scoring profile results CSV.")
    parser.add_argument("--profile-summary", default=DEFAULT_PROFILE_SUMMARY, help="Scoring profile summary CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output Markdown summary path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    quality_path = Path(args.quality)
    sensitivity_path = Path(args.sensitivity)
    profile_results_path = Path(args.profile_results)
    profile_summary_path = Path(args.profile_summary)
    output_path = Path(args.output)

    results = read_csv_if_exists(results_path)
    quality = read_csv_if_exists(quality_path)
    sensitivity = read_csv_if_exists(sensitivity_path)
    profile_results = read_csv_if_exists(profile_results_path)
    profile_summary = read_csv_if_exists(profile_summary_path)

    summary = build_summary(results, quality, sensitivity, profile_results, profile_summary)
    ensure_parent_dir(output_path)
    output_path.write_text(summary, encoding="utf-8")

    print("MODEL RUN SUMMARY")
    print("-----------------")
    print(f"Results file: {results_path if results_path.exists() else 'not found'}")
    print(f"Quality file: {quality_path if quality_path.exists() else 'not found'}")
    print(f"Sensitivity file: {sensitivity_path if sensitivity_path.exists() else 'not found'}")
    print(f"Profile results file: {profile_results_path if profile_results_path.exists() else 'not found'}")
    print(f"Saved summary: {output_path}")


if __name__ == "__main__":
    main()
