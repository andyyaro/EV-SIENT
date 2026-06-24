"""Create a simple data-confidence bar chart.

This script reads the current model output and creates a chart that separates
site promise from input-data confidence.

Run from the repository root after the model step:

    python src/plot_data_confidence_chart.py

Default output:

    data/outputs/charts/data_confidence_chart.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/data_confidence_chart.png"


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}. Run src/ev_charger_model.py first.")

    results = pd.read_csv(path)
    required = {
        "site_id",
        "site_name",
        "model_rank",
        "readiness_score",
        "data_confidence_score",
        "data_confidence_level",
    }
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    results["model_rank"] = pd.to_numeric(results["model_rank"], errors="coerce")
    results["readiness_score"] = pd.to_numeric(results["readiness_score"], errors="coerce")
    results["data_confidence_score"] = pd.to_numeric(results["data_confidence_score"], errors="coerce")
    return results.dropna(subset=["model_rank", "readiness_score", "data_confidence_score"]).copy()


def plot_data_confidence_chart(results: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    ordered = results.sort_values("data_confidence_score", ascending=True).copy()
    ordered["label"] = ordered["site_id"] + "\n" + ordered["site_name"]

    fig, ax = plt.subplots(figsize=(12.5, 6.4))
    bars = ax.barh(ordered["label"], ordered["data_confidence_score"])

    max_score = float(ordered["data_confidence_score"].max())
    ax.set_xlim(0, max(90, max_score + 25))
    ax.set_xlabel("Data confidence score")
    ax.set_title("EV Charger Site Data Confidence — Current Model Run")

    for bar, (_, row) in zip(bars, ordered.iterrows()):
        confidence_score = float(row["data_confidence_score"])
        readiness_score = float(row["readiness_score"])
        confidence_level = str(row["data_confidence_level"])
        ax.text(
            confidence_score + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{confidence_score:.1f}  |  {confidence_level}  |  readiness {readiness_score:.1f}",
            va="center",
            fontsize=9,
            clip_on=False,
        )

    ax.axvline(50, linestyle="--", linewidth=1, alpha=0.5)
    ax.axvline(75, linestyle="--", linewidth=1, alpha=0.5)
    ax.text(50, -0.65, "Medium", ha="center", fontsize=8)
    ax.text(75, -0.65, "High", ha="center", fontsize=8)

    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    footer = "Confidence is separate from readiness. It shows how complete the current input data is, not whether a site is good or bad."
    fig.text(0.5, 0.01, footer, ha="center", fontsize=8)

    fig.tight_layout(rect=[0, 0.04, 0.98, 1])
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a data-confidence chart.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    output_path = Path(args.output)

    results = load_results(results_path)
    plot_data_confidence_chart(results, output_path)

    print("DATA CONFIDENCE CHART")
    print("---------------------")
    print(f"Results file: {results_path}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
