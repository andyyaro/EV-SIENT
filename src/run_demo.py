"""Run an end-to-end synthetic demo workflow.

This is separate from src/run_all.py on purpose.

src/run_all.py is the official V1 workflow for the real six candidate sites.
src/run_demo.py is for synthetic stress tests with larger datasets, such as
25, 50, or 100 candidate sites.

Demo mode creates local files under data/demo/. Those files are intentionally
not part of the official deliverable package.

Example:

    python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = "data/demo"
DEFAULT_COUNT = 50
DEFAULT_SEED = 42
DEFAULT_TOP_N = 15

SCALABLE_REVIEW_ORDER = [
    "readiness_top_{top_n}.png",
    "readiness_map_top_{top_n}_labeled.png",
    "profile_heatmap_top_{top_n}.png",
    "profile_rank_stability_top_{top_n}.png",
    "readiness_score_distribution.png",
    "recommendation_tier_counts.png",
    "data_confidence_full_compact.png",
    "readiness_full_compact.png",
]


def repo_path(path: str | Path) -> Path:
    return PROJECT_ROOT / path


def run_command(command: list[str]) -> None:
    print()
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def tier_funnel_sentence(results: pd.DataFrame) -> str:
    if results.empty or "recommendation_tier" not in results.columns:
        return "No tier interpretation available."
    short_names = {
        "Tier 1 — advance to site screening": "Tier 1",
        "Tier 2 — promising candidate, refine data": "Tier 2",
        "High-review candidate": "High-review",
        "Tier 3 — lower priority / monitor": "Tier 3",
        "Low public-priority / special-use": "Special-use",
    }
    tiers = results["recommendation_tier"].map(lambda value: short_names.get(str(value), str(value)))
    counts = tiers.value_counts()
    top_tier = counts.idxmax()
    top_count = int(counts.max())
    total = len(results)
    tier1_count = int(counts.get("Tier 1", 0))
    high_review_count = int(counts.get("High-review", 0))
    return (
        f"Most sites fall into {top_tier} ({top_count} of {total}), while {tier1_count} sites are Tier 1 "
        f"and {high_review_count} sites need high review. This suggests the demo run creates a broad review pool "
        "rather than over-selecting top candidates."
    )


def scalable_review_paths(scalable_dir: Path, top_n: int) -> list[Path]:
    paths: list[Path] = []
    for template in SCALABLE_REVIEW_ORDER:
        candidate = scalable_dir / template.format(top_n=top_n)
        if candidate.exists():
            paths.append(candidate.relative_to(PROJECT_ROOT))
    return paths


def write_demo_summary(
    results_path: Path,
    summary_path: Path,
    quality_report_path: Path,
    action_matrix_path: Path,
    profile_results_path: Path,
    profile_summary_path: Path,
    profile_report_path: Path,
    scalable_dir: Path,
    count: int,
    seed: int,
    top_n: int,
    include_full_compact: bool,
) -> None:
    results = pd.read_csv(results_path)
    ranked = results.sort_values("model_rank").copy()
    actual_top_n = min(top_n, len(ranked))

    lines = [
        "# Demo Mode Run Summary",
        "",
        "## Purpose",
        "",
        "This is a synthetic scalability test. It is not an official site recommendation.",
        "",
        "## Demo settings",
        "",
        f"- Candidate sites generated: {count}",
        f"- Random seed: {seed}",
        f"- Top-N chart size: {actual_top_n}",
        f"- Full compact chart included: {'yes' if include_full_compact else 'no'}",
        "",
        "## Quick interpretation",
        "",
        tier_funnel_sentence(ranked),
        "",
        "## Main files",
        "",
        f"- Results CSV: `{results_path.relative_to(PROJECT_ROOT)}`",
        f"- Data quality report: `{quality_report_path.relative_to(PROJECT_ROOT)}`",
        f"- Action matrix: `{action_matrix_path.relative_to(PROJECT_ROOT)}`",
        f"- Profile results CSV: `{profile_results_path.relative_to(PROJECT_ROOT)}`",
        f"- Profile summary CSV: `{profile_summary_path.relative_to(PROJECT_ROOT)}`",
        f"- Profile comparison report: `{profile_report_path.relative_to(PROJECT_ROOT)}`",
        f"- Scalable chart folder: `{scalable_dir.relative_to(PROJECT_ROOT)}`",
        "",
        "## Top 10 demo sites",
        "",
        "| Rank | Site ID | Readiness | Confidence | Tier | Action |",
        "|---:|---|---:|---:|---|---|",
    ]

    for _, row in ranked.head(10).iterrows():
        action = row.get("action_label", "")
        lines.append(
            f"| {int(row['model_rank'])} | {row['site_id']} | {float(row['readiness_score']):.1f} | "
            f"{float(row['data_confidence_score']):.1f} | {row['recommendation_tier']} | {action} |"
        )

    lines.extend(["", "## Tier counts", "", "| Tier | Count |", "|---|---:|"])
    for tier, count_value in ranked["recommendation_tier"].value_counts().items():
        lines.append(f"| {tier} | {int(count_value)} |")

    lines.extend(["", "## Data confidence counts", "", "| Confidence level | Count |", "|---|---:|"])
    for confidence, count_value in ranked["data_confidence_level"].value_counts().items():
        lines.append(f"| {confidence} | {int(count_value)} |")

    review_paths = scalable_review_paths(scalable_dir, actual_top_n)
    lines.extend(["", "## Recommended visual review order", ""])
    for number, path in enumerate(review_paths, start=1):
        lines.append(f"{number}. `{path}`")

    lines.extend([
        "",
        "## Reminder",
        "",
        "Use demo mode to check scalability and visual readability. Do not merge demo data into the official V1 dataset.",
        "",
    ])

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a synthetic demo workflow for larger candidate-site sets.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Number of synthetic demo sites to generate.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducible demo data.")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of sites for the main scalable ranking chart.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT, help="Root folder for local demo inputs and outputs.")
    parser.add_argument("--clean", action="store_true", help="Delete the demo output root before running.")
    parser.add_argument("--skip-full-compact", action="store_true", help="Skip the full compact ranking chart.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    demo_root = repo_path(args.output_root)
    if args.clean and demo_root.exists():
        shutil.rmtree(demo_root)

    input_path = demo_root / f"demo_sites_{args.count}.csv"
    output_dir = demo_root / "outputs"
    charts_dir = output_dir / "charts"
    utilization_dir = output_dir / "utilization"
    scalable_dir = charts_dir / "scalable"

    quality_report_path = output_dir / f"demo_data_quality_report_{args.count}.csv"
    results_path = output_dir / f"demo_site_results_{args.count}.csv"
    action_matrix_path = output_dir / f"demo_action_matrix_{args.count}.md"
    profile_results_path = output_dir / f"demo_profile_results_{args.count}.csv"
    profile_summary_path = output_dir / f"demo_profile_rank_summary_{args.count}.csv"
    profile_report_path = output_dir / f"demo_profile_comparison_{args.count}.md"
    basic_chart_path = charts_dir / f"basic_readiness_score_chart_{args.count}.png"
    summary_path = output_dir / f"demo_run_summary_{args.count}.md"

    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    utilization_dir.mkdir(parents=True, exist_ok=True)
    scalable_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable

    run_command([py, "src/generate_demo_sites.py", "--count", str(args.count), "--seed", str(args.seed), "--output", str(input_path.relative_to(PROJECT_ROOT))])
    run_command([py, "src/validate_site_data.py", "--input", str(input_path.relative_to(PROJECT_ROOT)), "--output", str(quality_report_path.relative_to(PROJECT_ROOT))])
    run_command([
        py,
        "src/ev_charger_model.py",
        "--input",
        str(input_path.relative_to(PROJECT_ROOT)),
        "--output",
        str(results_path.relative_to(PROJECT_ROOT)),
        "--chart",
        str(basic_chart_path.relative_to(PROJECT_ROOT)),
        "--utilization-chart-dir",
        str(utilization_dir.relative_to(PROJECT_ROOT)),
    ])
    run_command([py, "src/add_action_matrix.py", "--results", str(results_path.relative_to(PROJECT_ROOT)), "--report", str(action_matrix_path.relative_to(PROJECT_ROOT))])
    run_command([
        py,
        "src/run_profile_analysis.py",
        "--site-results",
        str(results_path.relative_to(PROJECT_ROOT)),
        "--input-sites",
        str(input_path.relative_to(PROJECT_ROOT)),
        "--output",
        str(profile_results_path.relative_to(PROJECT_ROOT)),
        "--summary-output",
        str(profile_summary_path.relative_to(PROJECT_ROOT)),
        "--report-output",
        str(profile_report_path.relative_to(PROJECT_ROOT)),
    ])

    scalable_command = [
        py,
        "src/plot_scalable_readiness_charts.py",
        "--results",
        str(results_path.relative_to(PROJECT_ROOT)),
        "--input-sites",
        str(input_path.relative_to(PROJECT_ROOT)),
        "--profile-results",
        str(profile_results_path.relative_to(PROJECT_ROOT)),
        "--output-dir",
        str(scalable_dir.relative_to(PROJECT_ROOT)),
        "--top-n",
        str(args.top_n),
    ]
    if args.skip_full_compact:
        scalable_command.append("--skip-full")
    run_command(scalable_command)

    include_full_compact = not args.skip_full_compact
    write_demo_summary(
        results_path=results_path,
        summary_path=summary_path,
        quality_report_path=quality_report_path,
        action_matrix_path=action_matrix_path,
        profile_results_path=profile_results_path,
        profile_summary_path=profile_summary_path,
        profile_report_path=profile_report_path,
        scalable_dir=scalable_dir,
        count=args.count,
        seed=args.seed,
        top_n=args.top_n,
        include_full_compact=include_full_compact,
    )

    print()
    print("DEMO MODE COMPLETE")
    print("------------------")
    print(f"Demo input: {input_path.relative_to(PROJECT_ROOT)}")
    print(f"Demo results: {results_path.relative_to(PROJECT_ROOT)}")
    print(f"Demo summary: {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"Main scalable chart: {(scalable_dir / f'readiness_top_{min(args.top_n, args.count)}.png').relative_to(PROJECT_ROOT)}")
    print(f"Scalable map: {(scalable_dir / f'readiness_map_top_{min(args.top_n, args.count)}_labeled.png').relative_to(PROJECT_ROOT)}")
    print(f"Profile heatmap: {(scalable_dir / f'profile_heatmap_top_{min(args.top_n, args.count)}.png').relative_to(PROJECT_ROOT)}")
    print()
    print("These are local demo outputs. They are intentionally separate from the official V1 deliverable package.")


if __name__ == "__main__":
    main()
