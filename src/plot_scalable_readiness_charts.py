"""Create scalable readiness visuals for larger candidate-site tests.

The default readiness chart is good for the official 6-site V1 run, but it
becomes crowded when the model is tested with 25, 50, or more candidate sites.

This script reads any model results CSV and creates a small set of scalable
planning visuals:

1. Top-N readiness chart
2. Full compact readiness chart
3. Readiness score distribution
4. Recommendation tier count chart

Example:

    python src/plot_scalable_readiness_charts.py \
      --results data/demo/outputs/demo_site_results_50.csv \
      --output-dir data/demo/outputs/charts \
      --top-n 15
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT_DIR = "data/outputs/charts/scalable"
DEFAULT_TOP_N = 15

REQUIRED_COLUMNS = {
    "site_id",
    "site_name",
    "model_rank",
    "readiness_score",
    "recommendation_tier",
}

TIER_ORDER = [
    "Tier 1 — advance to site screening",
    "High-review candidate",
    "Tier 2 — promising candidate, refine data",
    "Tier 3 — lower priority / monitor",
    "Low public-priority / special-use",
]

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def short_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    results = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    results = results.copy()
    results["model_rank"] = pd.to_numeric(results["model_rank"], errors="coerce")
    results["readiness_score"] = pd.to_numeric(results["readiness_score"], errors="coerce")
    results = results.dropna(subset=["model_rank", "readiness_score"])
    results["model_rank"] = results["model_rank"].astype(int)
    results["tier_short"] = results["recommendation_tier"].apply(short_tier)
    return results.sort_values("model_rank", ascending=True).reset_index(drop=True)


def site_rank_label(row: pd.Series, include_name: bool = False) -> str:
    rank_and_id = f"#{int(row['model_rank'])} {row['site_id']}"
    if include_name:
        return f"{rank_and_id}\n{row['site_name']}"
    return rank_and_id


def add_bar_labels(ax, rows: pd.DataFrame, show_tier: bool = True) -> None:
    for index, row in rows.iterrows():
        score = float(row["readiness_score"])
        label = f"{score:.1f}"
        if show_tier:
            label += f" | {row['tier_short']}"
        ax.text(
            score + 0.6,
            index,
            label,
            va="center",
            fontsize=8,
            clip_on=False,
        )


def plot_top_n(results: pd.DataFrame, output_dir: Path, top_n: int) -> Path:
    top = results.head(top_n).copy().reset_index(drop=True)
    height = max(5.5, 0.36 * len(top) + 1.8)
    fig, ax = plt.subplots(figsize=(12.8, height))

    labels = [site_rank_label(row, include_name=False) for _, row in top.iterrows()]
    ax.barh(labels, top["readiness_score"])
    ax.invert_yaxis()
    add_bar_labels(ax, top)

    max_score = float(top["readiness_score"].max()) if not top.empty else 100
    ax.set_xlim(0, max(75, max_score + 14))
    ax.set_xlabel("Readiness score")
    ax.set_title(f"Top {len(top)} Candidate Sites by Readiness Score", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)

    fig.text(
        0.5,
        0.035,
        "Top-N view is the main scalable ranking visual. Full site names remain in the CSV/results table.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=[0.06, 0.07, 0.98, 0.95])

    output_path = output_dir / f"readiness_top_{len(top)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_full_compact(results: pd.DataFrame, output_dir: Path) -> Path:
    rows = results.copy().reset_index(drop=True)
    height = max(7.0, 0.22 * len(rows) + 2.0)
    fig, ax = plt.subplots(figsize=(12.8, height))

    labels = [site_rank_label(row, include_name=False) for _, row in rows.iterrows()]
    ax.barh(labels, rows["readiness_score"])
    ax.invert_yaxis()

    for index, row in rows.iterrows():
        score = float(row["readiness_score"])
        ax.text(score + 0.5, index, f"{score:.1f}", va="center", fontsize=6.6, clip_on=False)

    max_score = float(rows["readiness_score"].max()) if not rows.empty else 100
    ax.set_xlim(0, max(75, max_score + 10))
    ax.tick_params(axis="y", labelsize=6.5)
    ax.set_xlabel("Readiness score")
    ax.set_title(f"Full Compact Readiness Ranking ({len(rows)} Sites)", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.20)
    ax.set_axisbelow(True)

    fig.text(
        0.5,
        0.025,
        "Appendix view only: use this to audit the complete ranking, not as the main presentation chart.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=[0.06, 0.05, 0.98, 0.95])

    output_path = output_dir / "readiness_full_compact.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_distribution(results: pd.DataFrame, output_dir: Path) -> Path:
    scores = results["readiness_score"].dropna()
    bins = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.hist(scores, bins=bins, edgecolor="black", alpha=0.82)
    ax.set_xlabel("Readiness score range")
    ax.set_ylabel("Number of sites")
    ax.set_title("Readiness Score Distribution", fontsize=14, pad=16)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)

    mean_score = scores.mean()
    median_score = scores.median()
    ax.axvline(mean_score, linestyle="--", linewidth=1.1, alpha=0.75)
    ax.axvline(median_score, linestyle=":", linewidth=1.4, alpha=0.75)
    ax.text(mean_score, ax.get_ylim()[1] * 0.95, f"mean {mean_score:.1f}", ha="center", va="top", fontsize=8)
    ax.text(median_score, ax.get_ylim()[1] * 0.82, f"median {median_score:.1f}", ha="center", va="top", fontsize=8)

    fig.text(
        0.5,
        0.035,
        "Distribution view shows whether scores are clustered, spread out, or dominated by a few high-scoring sites.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=[0.06, 0.07, 0.98, 0.95])

    output_path = output_dir / "readiness_score_distribution.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_tier_counts(results: pd.DataFrame, output_dir: Path) -> Path:
    tier_counts = results["recommendation_tier"].value_counts()
    ordered_tiers = [tier for tier in TIER_ORDER if tier in tier_counts.index]
    remaining_tiers = [tier for tier in tier_counts.index if tier not in ordered_tiers]
    ordered_tiers.extend(remaining_tiers)

    labels = [short_tier(tier) for tier in ordered_tiers]
    counts = [int(tier_counts[tier]) for tier in ordered_tiers]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bars = ax.bar(labels, counts)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_ylabel("Number of sites")
    ax.set_title("Recommendation Tier Counts", fontsize=14, pad=16)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelrotation=15)

    fig.text(
        0.5,
        0.035,
        "Tier-count view summarizes the planning funnel: how many sites advance, need review, or stay lower priority.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=[0.06, 0.09, 0.98, 0.95])

    output_path = output_dir / "recommendation_tier_counts.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_summary(results: pd.DataFrame, output_dir: Path, chart_paths: list[Path], top_n: int) -> Path:
    top = results.head(top_n)
    tier_counts = results["tier_short"].value_counts()

    lines = [
        "# Scalable Readiness Visuals Summary",
        "",
        f"Sites evaluated: {len(results)}",
        f"Top-N chart size: {len(top)}",
        "",
        "## Generated charts",
        "",
    ]

    for path in chart_paths:
        lines.append(f"- [{path.name}]({path.name})")

    lines.extend(["", "## Top sites", ""])
    lines.append("| Rank | Site ID | Readiness | Tier |")
    lines.append("|---:|---|---:|---|")
    for _, row in top.iterrows():
        lines.append(f"| {int(row['model_rank'])} | {row['site_id']} | {float(row['readiness_score']):.1f} | {row['tier_short']} |")

    lines.extend(["", "## Tier counts", ""])
    lines.append("| Tier | Count |")
    lines.append("|---|---:|")
    for tier, count in tier_counts.items():
        lines.append(f"| {tier} | {int(count)} |")

    lines.extend([
        "",
        "## How to use these visuals",
        "",
        "Use the top-N chart for presentation and the full compact chart for audit/review.",
        "Use the distribution and tier-count charts to understand whether the model creates a reasonable planning funnel.",
        "",
    ])

    output_path = output_dir / "scalable_readiness_visuals_summary.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create scalable readiness visuals from a model results CSV.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV to visualize.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Folder for generated scalable visuals.")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of sites to include in the main top-N chart.")
    parser.add_argument("--skip-full", action="store_true", help="Skip the full compact ranking chart.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    results = load_results(results_path)
    if results.empty:
        raise SystemExit("No valid rows found in results file.")

    top_n = max(1, min(args.top_n, len(results)))

    chart_paths: list[Path] = []
    chart_paths.append(plot_top_n(results, output_dir, top_n))
    chart_paths.append(plot_distribution(results, output_dir))
    chart_paths.append(plot_tier_counts(results, output_dir))
    if not args.skip_full:
        chart_paths.append(plot_full_compact(results, output_dir))

    summary_path = write_summary(results, output_dir, chart_paths, top_n)

    print("SCALABLE READINESS VISUALS")
    print("--------------------------")
    print(f"Results file: {results_path}")
    print(f"Sites evaluated: {len(results)}")
    print(f"Output folder: {output_dir}")
    print()
    print("Generated files:")
    for path in chart_paths:
        print(f"- {path}")
    print(f"- {summary_path}")


if __name__ == "__main__":
    main()
