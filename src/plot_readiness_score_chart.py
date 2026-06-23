"""Create a presentation-ready readiness score bar chart.

This script reads the current model output and overwrites the main readiness
score chart with clearer score labels and recommendation-tier context.

Run from the repository root after the model step:

    python src/plot_readiness_score_chart.py

Default output:

    data/outputs/charts/readiness_score_chart.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/readiness_score_chart.png"

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def compact_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}. Run src/ev_charger_model.py first.")

    results = pd.read_csv(path)
    required = {"site_id", "site_name", "model_rank", "readiness_score", "recommendation_tier"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    results["model_rank"] = pd.to_numeric(results["model_rank"], errors="coerce")
    results["readiness_score"] = pd.to_numeric(results["readiness_score"], errors="coerce")
    return results.dropna(subset=["model_rank", "readiness_score"]).copy()


def plot_readiness_chart(results: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    ordered = results.sort_values("readiness_score", ascending=True).copy()
    ordered["tier_short"] = ordered["recommendation_tier"].apply(compact_tier)
    ordered["label"] = ordered["site_id"] + "\n" + ordered["site_name"]

    fig, ax = plt.subplots(figsize=(11, 6.4))
    bars = ax.barh(ordered["label"], ordered["readiness_score"])

    max_score = float(ordered["readiness_score"].max())
    ax.set_xlim(0, max(72, max_score + 9))
    ax.set_xlabel("Readiness score")
    ax.set_title("EV Charger Site Readiness Scores — Current Model Run")

    for bar, (_, row) in zip(bars, ordered.iterrows()):
        score = float(row["readiness_score"])
        tier = row["tier_short"]
        ax.text(
            score + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.1f}  |  {tier}",
            va="center",
            fontsize=9,
        )

    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    footer = "Higher score = stronger early planning candidate. High-review and special-use labels still require stakeholder/AHJ/site confirmation."
    fig.text(0.5, 0.01, footer, ha="center", fontsize=8)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a polished readiness score chart.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    output_path = Path(args.output)

    results = load_results(results_path)
    plot_readiness_chart(results, output_path)

    print("READINESS SCORE CHART")
    print("---------------------")
    print(f"Results file: {results_path}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
