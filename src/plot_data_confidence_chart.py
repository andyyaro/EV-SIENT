"""Create a simple data-confidence chart.

This script reads the current model output and creates a clean horizontal bar
chart showing how complete and source-supported each site's input data is.

The chart intentionally keeps the visual simple:
- one bar per candidate site
- site order follows model rank
- labels show confidence score and confidence level
- faint bands mark Low, Medium, and High confidence
- threshold lines mark Medium and High confidence

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

from chart_style import apply_chart_style

apply_chart_style()

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/data_confidence_chart.png"

MEDIUM_THRESHOLD = 50
HIGH_THRESHOLD = 75


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}. Run src/ev_charger_model.py first.")

    results = pd.read_csv(path)
    required = {"site_id", "model_rank", "readiness_score", "data_confidence_score", "data_confidence_level"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    results["model_rank"] = pd.to_numeric(results["model_rank"], errors="coerce")
    results["readiness_score"] = pd.to_numeric(results["readiness_score"], errors="coerce")
    results["data_confidence_score"] = pd.to_numeric(results["data_confidence_score"], errors="coerce")
    return results.dropna(subset=["model_rank", "readiness_score", "data_confidence_score"]).copy()


def site_label(row: pd.Series) -> str:
    return f"#{int(row['model_rank'])} {row['site_id']}"


def confidence_message(results: pd.DataFrame) -> str:
    top = results.sort_values("model_rank").iloc[0]
    return (
        f"Top site {top['site_id']} has {float(top['data_confidence_score']):.1f}/100 confidence "
        f"({top['data_confidence_level']}). Stakeholder and electrical confirmation should raise confidence."
    )


def add_confidence_bands(ax) -> None:
    ax.axvspan(0, MEDIUM_THRESHOLD, facecolor="#fdecec", alpha=0.55, zorder=0)
    ax.axvspan(MEDIUM_THRESHOLD, HIGH_THRESHOLD, facecolor="#fff4d6", alpha=0.55, zorder=0)
    ax.axvspan(HIGH_THRESHOLD, 100, facecolor="#eaf6ea", alpha=0.55, zorder=0)

    band_labels = [(25, "Low"), (62.5, "Medium"), (87.5, "High")]
    for x_value, label in band_labels:
        ax.text(x_value, 1.015, label, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8, alpha=0.85)


def add_threshold_lines(ax) -> None:
    ax.axvline(MEDIUM_THRESHOLD, linestyle="--", linewidth=1, alpha=0.45, zorder=1)
    ax.axvline(HIGH_THRESHOLD, linestyle="--", linewidth=1, alpha=0.45, zorder=1)


def plot_data_confidence_chart(results: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    ordered = results.sort_values("model_rank", ascending=True).copy()
    ordered["label"] = ordered.apply(site_label, axis=1)

    fig, ax = plt.subplots(figsize=(12.8, 6.8))
    add_confidence_bands(ax)
    bars = ax.barh(ordered["label"], ordered["data_confidence_score"], zorder=2)
    ax.invert_yaxis()

    for bar, (_, row) in zip(bars, ordered.iterrows()):
        score = float(row["data_confidence_score"])
        level = str(row["data_confidence_level"])
        ax.text(score + 1.2, bar.get_y() + bar.get_height() / 2, f"{score:.1f} — {level}", va="center", fontsize=9, clip_on=False, zorder=3)

    add_threshold_lines(ax)

    ax.set_xlim(0, 100)
    ax.set_xlabel("Data confidence score")
    ax.set_title("Data Confidence by Candidate Site", fontsize=14, pad=18)
    ax.grid(axis="x", alpha=0.18, zorder=0)
    ax.set_axisbelow(True)

    fig.text(0.5, 0.90, confidence_message(ordered), ha="center", fontsize=9)
    footer = "Confidence is not readiness. It shows how complete and source-supported the current input data is."
    fig.text(0.5, 0.035, footer, ha="center", fontsize=8)

    fig.tight_layout(rect=[0.06, 0.08, 0.96, 0.88])
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
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
