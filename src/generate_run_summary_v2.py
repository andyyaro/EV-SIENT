"""Generate a V2 Markdown summary of the latest model run.

This is the V2 companion to src/generate_run_summary.py. It keeps the V1 run
summary idea, but adds V2-specific sections for electrical-risk scenarios,
right-sizing scenarios, expanded charts, and the expanded candidate set.

Run from the repository root after the V2 workflow:

    python src/generate_run_summary_v2.py
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_QUALITY = "data/outputs/v2_data_quality_report.csv"
DEFAULT_SENSITIVITY = "data/outputs/v2_sensitivity_summary.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/v2_profile_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_OUTPUT = "data/outputs/v2_run_summary.md"

V2_CHART_OUTPUTS = [
    "data/outputs/charts/v2_readiness_score_chart.png",
    "data/outputs/charts/v2_polished_readiness_score_chart.png",
    "data/outputs/charts/v2_data_confidence_chart.png",
    "data/outputs/charts/v2_profile_score_heatmap.png",
    "data/outputs/charts/v2_profile_rank_stability_chart.png",
    "data/outputs/charts/v2_site_readiness_map.png",
]

V2_REPORT_OUTPUTS = [
    "data/outputs/v2_action_matrix.md",
    "data/outputs/v2_profile_comparison.md",
    "data/outputs/v2_electrical_feasibility_report.md",
    "data/outputs/v2_right_sizing_report.md",
    "data/outputs/v2_results_interpretation.md",
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


def ranked_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results
    if "model_rank" not in results.columns:
        return results.copy()
    ranked = results.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    return ranked.sort_values("model_rank")


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
        max_rank_range = pd.to_numeric(sensitivity["rank_range"], errors="coerce").max()
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
        return f"`{top_site}` stayed ranked #1 across all `{profiles_tested}` scoring profiles."

    return f"Top-ranked sites changed across scoring profiles: `{top_sites}`. This shows priority tradeoffs between demand, equity, feasibility, and safety."


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
    return markdown_table(top_by_profile, ["profile_name", "site_id", "site_name", "profile_readiness_score"])


def confidence_summary_text(results: pd.DataFrame) -> str:
    if results.empty or "data_confidence_level" not in results.columns:
        return "_No data-confidence output found._"

    counts = results["data_confidence_level"].value_counts().to_dict()
    return (
        f"Data confidence levels: High={counts.get('High', 0)}, "
        f"Medium={counts.get('Medium', 0)}, Low={counts.get('Low', 0)}."
    )


def action_summary_text(results: pd.DataFrame) -> str:
    if results.empty or "action_label" not in results.columns:
        return "_No action-matrix output found._"

    counts = results["action_label"].value_counts().to_dict()
    parts = [f"{label}={count}" for label, count in counts.items()]
    return "Action labels: " + ", ".join(parts) + "."


def electrical_summary_text(electrical: pd.DataFrame) -> str:
    if electrical.empty:
        return "_No electrical-risk scenario output found._"

    required = {"site_id", "expected_rank", "electrical_risk_level", "expected_score"}
    if not required.issubset(electrical.columns):
        return "Electrical scenario output exists, but required summary columns were not found."

    expected = electrical.copy()
    expected["expected_rank"] = pd.to_numeric(expected["expected_rank"], errors="coerce")
    expected = expected.sort_values("expected_rank")
    top = expected.iloc[0]
    high_risk_count = int((expected["electrical_risk_level"].astype(str) == "high").sum())
    return (
        f"Under the expected electrical case, `{top['site_id']}` remains the top adjusted site "
        f"with score `{top['expected_score']}`. High electrical risk sites: `{high_risk_count}`."
    )


def electrical_table(electrical: pd.DataFrame) -> str:
    if electrical.empty:
        return "_No electrical-risk scenario output found._"
    view = electrical.copy()
    if "expected_rank" in view.columns:
        view["expected_rank"] = pd.to_numeric(view["expected_rank"], errors="coerce")
        view = view.sort_values("expected_rank")
    return markdown_table(
        view,
        [
            "site_id",
            "site_name",
            "base_rank",
            "electrical_risk_level",
            "expected_rank",
            "conservative_rank",
            "expected_score",
            "conservative_score",
        ],
    )


def right_sizing_summary_text(right_sizing: pd.DataFrame) -> str:
    if right_sizing.empty:
        return "_No right-sizing scenario output found._"

    required = {"site_id", "model_rank", "ports_now", "future_ready_capacity", "expansion_strategy"}
    if not required.issubset(right_sizing.columns):
        return "Right-sizing output exists, but required columns were not found."

    ranked = right_sizing.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    top = ranked.iloc[0]
    return (
        f"The top site `{top['site_id']}` is recommended for `{top['ports_now']}` ports now "
        f"with future-ready capacity for `{top['future_ready_capacity']}` ports."
    )


def right_sizing_table(right_sizing: pd.DataFrame) -> str:
    if right_sizing.empty:
        return "_No right-sizing scenario output found._"
    view = right_sizing.copy()
    if "model_rank" in view.columns:
        view["model_rank"] = pd.to_numeric(view["model_rank"], errors="coerce")
        view = view.sort_values("model_rank")
    return markdown_table(
        view,
        [
            "model_rank",
            "site_id",
            "ports_now",
            "ports_2035_base",
            "ports_2035_high",
            "ports_2050_base",
            "ports_2050_high",
            "future_ready_capacity",
            "expansion_strategy",
        ],
    )


def existing_outputs_table(paths: list[str]) -> str:
    rows = []
    for path_text in paths:
        path = Path(path_text)
        rows.append({"output": path_text, "status": "present" if path.exists() else "missing"})
    return markdown_table(pd.DataFrame(rows), ["output", "status"])


def build_summary(
    results: pd.DataFrame,
    quality: pd.DataFrame,
    sensitivity: pd.DataFrame,
    profile_results: pd.DataFrame,
    electrical: pd.DataFrame,
    right_sizing: pd.DataFrame,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    quality_text, review_items = quality_summary(quality)
    sensitivity_text = sensitivity_summary_text(sensitivity)
    profile_text = profile_summary_text(profile_results)
    confidence_text = confidence_summary_text(results)
    action_text = action_summary_text(results)
    electrical_text = electrical_summary_text(electrical)
    right_sizing_text = right_sizing_summary_text(right_sizing)
    ranked = ranked_results(results)

    if ranked.empty:
        top_line = "_No model results found._"
    else:
        top = ranked.iloc[0]
        top_line = (
            f"**Top candidate:** {top.get('site_id', '')} — {top.get('site_name', '')} "
            f"with readiness score **{top.get('readiness_score', '')}**, "
            f"data confidence **{top.get('data_confidence_level', 'not available')}**, "
            f"and next action **{top.get('action_label', 'not available')}**."
        )

    ranking_table = markdown_table(
        ranked,
        [
            "model_rank",
            "site_id",
            "site_name",
            "readiness_score",
            "data_confidence_score",
            "data_confidence_level",
            "action_label",
            "recommendation_tier",
            "recommended_ports_now",
            "recommended_ports_2035",
            "recommended_ports_2050",
        ],
    )

    action_table = markdown_table(
        ranked,
        ["model_rank", "site_id", "readiness_confidence_cell", "action_label", "action_detail"],
    )

    confidence_table = markdown_table(
        ranked,
        ["model_rank", "site_id", "readiness_score", "data_confidence_score", "data_confidence_level", "data_confidence_reason"],
    )

    review_table = remaining_review_summary(review_items)
    profile_table = profile_top_table(profile_results)
    electrical_view = electrical_table(electrical)
    right_sizing_view = right_sizing_table(right_sizing)
    chart_table = existing_outputs_table(V2_CHART_OUTPUTS)
    report_table = existing_outputs_table(V2_REPORT_OUTPUTS)

    return f"""# V2 Model Run Summary

Generated: {generated_at}

## Executive summary

{top_line}

{sensitivity_text}

{profile_text}

{electrical_text}

{right_sizing_text}

{confidence_text}

{action_text}

This is a planning-support output only. It does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.

## Data-quality summary

{quality_text}

## Current ranking, confidence, action, and model right-sizing output

{ranking_table}

## Readiness-confidence action matrix

{action_table}

See `data/outputs/v2_action_matrix.md` for the dedicated V2 action-matrix report.

## Data confidence summary

{confidence_table}

## Remaining review items by field

{review_table}

## Sensitivity summary

{sensitivity_text}

## Scoring profile summary

{profile_text}

{profile_table}

See `data/outputs/v2_profile_comparison.md` for the full V2 scoring-profile report.

## Electrical-risk scenario summary

{electrical_text}

{electrical_view}

See `data/outputs/v2_electrical_feasibility_report.md` for the full V2 electrical-feasibility scenario report.

## Right-sizing scenario summary

{right_sizing_text}

{right_sizing_view}

See `data/outputs/v2_right_sizing_report.md` for the full V2 right-sizing scenario report.

## Generated visual outputs

{chart_table}

## Generated Markdown reports

{report_table}

## Next data to improve

The highest-priority remaining confirmations are:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
visitor and employee counts
operating hours
final parking counts and charger placement
site-specific AHJ / Fire Marshal triggers
stormwater and ADA layout details
```
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown summary of the latest V2 model run.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 model results CSV.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, help="V2 data-quality report CSV.")
    parser.add_argument("--sensitivity", default=DEFAULT_SENSITIVITY, help="V2 sensitivity summary CSV.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="V2 scoring profile results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="V2 electrical risk summary CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output Markdown summary path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    quality_path = Path(args.quality)
    sensitivity_path = Path(args.sensitivity)
    profile_results_path = Path(args.profile_results)
    electrical_path = Path(args.electrical_summary)
    right_sizing_path = Path(args.right_sizing)
    output_path = Path(args.output)

    results = read_csv_if_exists(results_path)
    quality = read_csv_if_exists(quality_path)
    sensitivity = read_csv_if_exists(sensitivity_path)
    profile_results = read_csv_if_exists(profile_results_path)
    electrical = read_csv_if_exists(electrical_path)
    right_sizing = read_csv_if_exists(right_sizing_path)

    summary = build_summary(results, quality, sensitivity, profile_results, electrical, right_sizing)
    ensure_parent_dir(output_path)
    output_path.write_text(summary, encoding="utf-8")

    print("V2 MODEL RUN SUMMARY")
    print("--------------------")
    print(f"Results file: {results_path if results_path.exists() else 'not found'}")
    print(f"Quality file: {quality_path if quality_path.exists() else 'not found'}")
    print(f"Sensitivity file: {sensitivity_path if sensitivity_path.exists() else 'not found'}")
    print(f"Profile results file: {profile_results_path if profile_results_path.exists() else 'not found'}")
    print(f"Electrical summary file: {electrical_path if electrical_path.exists() else 'not found'}")
    print(f"Right-sizing file: {right_sizing_path if right_sizing_path.exists() else 'not found'}")
    print(f"Saved summary: {output_path}")


if __name__ == "__main__":
    main()
