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


def repo_path(path: str | Path) -> Path:
    return PROJECT_ROOT / path


def run_command(command: list[str]) -> None:
    print()
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def write_demo_summary(
    results_path: Path,
    summary_path: Path,
    quality_report_path: Path,
    action_matrix_path: Path,
    scalable_dir: Path,
    count: int,
    seed: int,
    top_n: int,
) -> None:
    results = pd.read_csv(results_path)
    ranked = results.sort_values("model_rank").copy()

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
        f"- Top-N chart size: {top_n}",
        "",
        "## Main files",
        "",
        f"- Results CSV: `{results_path.relative_to(PROJECT_ROOT)}`",
        f"- Data quality report: `{quality_report_path.relative_to(PROJECT_ROOT)}`",
        f"- Action matrix: `{action_matrix_path.relative_to(PROJECT_ROOT)}`",
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

    lines.extend([
        "",
        "## Tier counts",
        "",
        "| Tier | Count |",
        "|---|---:|",
    ])

    for tier, count_value in ranked["recommendation_tier"].value_counts().items():
        lines.append(f"| {tier} | {int(count_value)} |")

    lines.extend([
        "",
        "## Data confidence counts",
        "",
        "| Confidence level | Count |",
        "|---|---:|",
    ])

    for confidence, count_value in ranked["data_confidence_level"].value_counts().items():
        lines.append(f"| {confidence} | {int(count_value)} |")

    lines.extend([
        "",
        "## Recommended visual review order",
        "",
        f"1. `{scalable_dir.relative_to(PROJECT_ROOT) / f'readiness_top_{min(top_n, len(ranked))}.png'}`",
        f"2. `{scalable_dir.relative_to(PROJECT_ROOT) / 'readiness_score_distribution.png'}`",
        f"3. `{scalable_dir.relative_to(PROJECT_ROOT) / 'recommendation_tier_counts.png'}`",
        f"4. `{scalable_dir.relative_to(PROJECT_ROOT) / 'readiness_full_compact.png'}`",
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
    basic_chart_path = charts_dir / f"basic_readiness_score_chart_{args.count}.png"
    summary_path = output_dir / f"demo_run_summary_{args.count}.md"

    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    utilization_dir.mkdir(parents=True, exist_ok=True)
    scalable_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable

    run_command([
        py,
        "src/generate_demo_sites.py",
        "--count",
        str(args.count),
        "--seed",
        str(args.seed),
        "--output",
        str(input_path.relative_to(PROJECT_ROOT)),
    ])

    run_command([
        py,
        "src/validate_site_data.py",
        "--input",
        str(input_path.relative_to(PROJECT_ROOT)),
        "--output",
        str(quality_report_path.relative_to(PROJECT_ROOT)),
    ])

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

    run_command([
        py,
        "src/add_action_matrix.py",
        "--results",
        str(results_path.relative_to(PROJECT_ROOT)),
        "--report",
        str(action_matrix_path.relative_to(PROJECT_ROOT)),
    ])

    scalable_command = [
        py,
        "src/plot_scalable_readiness_charts.py",
        "--results",
        str(results_path.relative_to(PROJECT_ROOT)),
        "--output-dir",
        str(scalable_dir.relative_to(PROJECT_ROOT)),
        "--top-n",
        str(args.top_n),
    ]
    if args.skip_full_compact:
        scalable_command.append("--skip-full")
    run_command(scalable_command)

    write_demo_summary(
        results_path=results_path,
        summary_path=summary_path,
        quality_report_path=quality_report_path,
        action_matrix_path=action_matrix_path,
        scalable_dir=scalable_dir,
        count=args.count,
        seed=args.seed,
        top_n=args.top_n,
    )

    print()
    print("DEMO MODE COMPLETE")
    print("------------------")
    print(f"Demo input: {input_path.relative_to(PROJECT_ROOT)}")
    print(f"Demo results: {results_path.relative_to(PROJECT_ROOT)}")
    print(f"Demo summary: {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"Main scalable chart: {(scalable_dir / f'readiness_top_{min(args.top_n, args.count)}.png').relative_to(PROJECT_ROOT)}")
    print()
    print("These are local demo outputs. They are intentionally separate from the official V1 deliverable package.")


if __name__ == "__main__":
    main()
