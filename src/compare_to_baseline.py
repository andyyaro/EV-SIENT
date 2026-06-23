"""Compare current generated model outputs against a committed baseline.

The script reads a curated baseline under data/baselines/ and compares it to the
current local outputs under data/outputs/. It writes comparison reports to
`data/outputs/`, which stays ignored by Git.

Default use:

    python src/compare_to_baseline.py

Optional stricter use:

    python src/compare_to_baseline.py --fail-on-top-site-change --fail-on-rank-change
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SITE_COMPARE_COLUMNS = [
    "site_id",
    "site_name_current",
    "baseline_rank",
    "current_rank",
    "rank_delta",
    "baseline_readiness_score",
    "current_readiness_score",
    "readiness_score_delta",
    "baseline_recommendation_tier",
    "current_recommendation_tier",
    "tier_changed",
    "baseline_ports_now",
    "current_ports_now",
    "ports_now_delta",
    "baseline_ports_2035",
    "current_ports_2035",
    "ports_2035_delta",
    "baseline_ports_2050",
    "current_ports_2050",
    "ports_2050_delta",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare current model outputs to a baseline.")
    parser.add_argument("--baseline", default="data/baselines/v1_baseline", help="Baseline folder to compare against.")
    parser.add_argument("--current", default="data/outputs", help="Current generated output folder.")
    parser.add_argument("--output-dir", default="data/outputs", help="Folder for comparison reports.")
    parser.add_argument("--fail-on-top-site-change", action="store_true", help="Exit with failure if the top-ranked site changes.")
    parser.add_argument("--fail-on-rank-change", action="store_true", help="Exit with failure if any site rank changes.")
    parser.add_argument("--fail-on-tier-change", action="store_true", help="Exit with failure if any recommendation tier changes.")
    parser.add_argument("--max-score-delta", type=float, default=None, help="Exit with failure if any absolute readiness-score change exceeds this value.")
    return parser.parse_args()


def read_csv(folder: Path, file_name: str) -> pd.DataFrame:
    path = folder / file_name
    if not path.exists():
        raise SystemExit(f"Missing required file: {path.relative_to(PROJECT_ROOT)}")
    return pd.read_csv(path)


def read_manifest(baseline_dir: Path) -> dict[str, object]:
    manifest_path = baseline_dir / "baseline_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def get_top_site_id(results: pd.DataFrame) -> str:
    ranks = pd.to_numeric(results["model_rank"], errors="coerce")
    top_row = results.loc[ranks.idxmin()]
    return str(top_row["site_id"])


def quality_error_count(report: pd.DataFrame) -> int:
    if "severity" not in report.columns:
        return -1
    return int((report["severity"] == "ERROR").sum())


def build_site_comparison(baseline: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    baseline_small = baseline[
        [
            "site_id",
            "site_name",
            "model_rank",
            "readiness_score",
            "recommendation_tier",
            "recommended_ports_now",
            "recommended_ports_2035",
            "recommended_ports_2050",
        ]
    ].copy()
    current_small = current[
        [
            "site_id",
            "site_name",
            "model_rank",
            "readiness_score",
            "recommendation_tier",
            "recommended_ports_now",
            "recommended_ports_2035",
            "recommended_ports_2050",
        ]
    ].copy()

    baseline_small = baseline_small.rename(
        columns={
            "site_name": "site_name_baseline",
            "model_rank": "baseline_rank",
            "readiness_score": "baseline_readiness_score",
            "recommendation_tier": "baseline_recommendation_tier",
            "recommended_ports_now": "baseline_ports_now",
            "recommended_ports_2035": "baseline_ports_2035",
            "recommended_ports_2050": "baseline_ports_2050",
        }
    )
    current_small = current_small.rename(
        columns={
            "site_name": "site_name_current",
            "model_rank": "current_rank",
            "readiness_score": "current_readiness_score",
            "recommendation_tier": "current_recommendation_tier",
            "recommended_ports_now": "current_ports_now",
            "recommended_ports_2035": "current_ports_2035",
            "recommended_ports_2050": "current_ports_2050",
        }
    )

    comparison = baseline_small.merge(current_small, on="site_id", how="outer")
    comparison["rank_delta"] = comparison["current_rank"] - comparison["baseline_rank"]
    comparison["readiness_score_delta"] = (
        comparison["current_readiness_score"] - comparison["baseline_readiness_score"]
    )
    comparison["tier_changed"] = (
        comparison["current_recommendation_tier"] != comparison["baseline_recommendation_tier"]
    )
    comparison["ports_now_delta"] = comparison["current_ports_now"] - comparison["baseline_ports_now"]
    comparison["ports_2035_delta"] = comparison["current_ports_2035"] - comparison["baseline_ports_2035"]
    comparison["ports_2050_delta"] = comparison["current_ports_2050"] - comparison["baseline_ports_2050"]

    comparison = comparison.sort_values("current_rank", na_position="last")
    return comparison[SITE_COMPARE_COLUMNS]


def build_markdown_summary(
    comparison: pd.DataFrame,
    baseline_results: pd.DataFrame,
    current_results: pd.DataFrame,
    baseline_quality: pd.DataFrame,
    current_quality: pd.DataFrame,
    manifest: dict[str, object],
) -> str:
    baseline_top = get_top_site_id(baseline_results)
    current_top = get_top_site_id(current_results)
    rank_changes = int((comparison["rank_delta"].fillna(0) != 0).sum())
    tier_changes = int(comparison["tier_changed"].fillna(False).sum())
    max_score_delta = float(comparison["readiness_score_delta"].abs().max())

    lines: list[str] = []
    lines.append("# Baseline Comparison Report")
    lines.append("")
    lines.append(f"Baseline folder: `{manifest.get('baseline_label', 'data/baselines/v1_baseline')}`")
    if manifest.get("created_utc"):
        lines.append(f"Baseline created UTC: `{manifest['created_utc']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Baseline top site: `{baseline_top}`")
    lines.append(f"- Current top site: `{current_top}`")
    lines.append(f"- Sites with rank changes: `{rank_changes}`")
    lines.append(f"- Sites with tier changes: `{tier_changes}`")
    lines.append(f"- Maximum absolute readiness-score change: `{max_score_delta:.2f}`")
    lines.append(f"- Baseline data-quality ERROR count: `{quality_error_count(baseline_quality)}`")
    lines.append(f"- Current data-quality ERROR count: `{quality_error_count(current_quality)}`")
    lines.append("")
    lines.append("## Site-level comparison")
    lines.append("")
    lines.append("| Site | Baseline rank | Current rank | Rank delta | Baseline score | Current score | Score delta | Tier changed |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")

    for _, row in comparison.iterrows():
        lines.append(
            "| "
            f"{row['site_id']} | "
            f"{row['baseline_rank']} | "
            f"{row['current_rank']} | "
            f"{row['rank_delta']} | "
            f"{row['baseline_readiness_score']} | "
            f"{row['current_readiness_score']} | "
            f"{row['readiness_score_delta']:.2f} | "
            f"{row['tier_changed']} |"
        )

    lines.append("")
    lines.append("Generated comparison files stay local under `data/outputs/` and are ignored by Git.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    baseline_dir = PROJECT_ROOT / args.baseline
    current_dir = PROJECT_ROOT / args.current
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_results = read_csv(baseline_dir, "site_results.csv")
    current_results = read_csv(current_dir, "site_results.csv")
    baseline_quality = read_csv(baseline_dir, "data_quality_report.csv")
    current_quality = read_csv(current_dir, "data_quality_report.csv")
    manifest = read_manifest(baseline_dir)

    comparison = build_site_comparison(baseline_results, current_results)

    csv_path = output_dir / "baseline_comparison.csv"
    md_path = output_dir / "baseline_comparison.md"
    comparison.to_csv(csv_path, index=False)
    md_path.write_text(
        build_markdown_summary(
            comparison,
            baseline_results,
            current_results,
            baseline_quality,
            current_quality,
            manifest,
        ),
        encoding="utf-8",
    )

    print("BASELINE COMPARISON")
    print("-------------------")
    print(f"Wrote: {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote: {md_path.relative_to(PROJECT_ROOT)}")

    failures: list[str] = []
    if args.fail_on_top_site_change and get_top_site_id(baseline_results) != get_top_site_id(current_results):
        failures.append("Top-ranked site changed.")
    if args.fail_on_rank_change and (comparison["rank_delta"].fillna(0) != 0).any():
        failures.append("One or more site ranks changed.")
    if args.fail_on_tier_change and comparison["tier_changed"].fillna(False).any():
        failures.append("One or more recommendation tiers changed.")
    if args.max_score_delta is not None:
        max_delta = float(comparison["readiness_score_delta"].abs().max())
        if max_delta > args.max_score_delta:
            failures.append(f"Maximum score delta {max_delta:.2f} exceeds limit {args.max_score_delta:.2f}.")

    if failures:
        print("Result: FAILED")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Result: COMPLETED")
    print("Review the comparison report to see whether outputs changed from the baseline.")


if __name__ == "__main__":
    main()
