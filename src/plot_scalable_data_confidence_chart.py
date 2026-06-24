"""Create a readable Top-N data-confidence chart for larger demo runs.

The full compact confidence chart is useful as an appendix, but it becomes too
dense for presentation when the dataset has 25, 50, or more sites. This script
creates a smaller Top-N confidence view that matches the scalable demo workflow.

Example:

    python src/plot_scalable_data_confidence_chart.py \
      --results data/demo/outputs/demo_site_results_50.csv \
      --output-dir data/demo/outputs/charts/scalable \
      --top-n 15
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/demo/outputs/demo_site_results_50.csv"
DEFAULT_OUTPUT_DIR = "data/demo/outputs/charts/scalable"
DEFAULT_TOP_N = 15

REQUIRED_COLUMNS = {
    "site_id",
    "model_rank",
    "readiness_score",
    "data_confidence_score",
    "data_confidence_level",
}


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    data = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    data = data.copy()
    data["model_rank"] = pd.to_numeric(data["model_rank"], errors="coerce")
    data["readiness_score"] = pd.to_numeric(data["readiness_score"], errors="coerce")
    data["data_confidence_score"] = pd.to_numeric(data["data_confidence_score"], errors="coerce")
    data = data.dropna(subset=["model_rank", "readiness_score", "data_confidence_score"])
    data["model_rank"] = data["model_rank"].astype(int)
    return data.sort_values("model_rank", ascending=True).reset_index(drop=True)


def site_rank_label(row: pd.Series) -> str:
    return f"#{int(row['model_rank'])} {row['site_id']}"


def add_confidence_bands(ax) -> None:
    ax.axvspan(0, 50, alpha=0.06)
    ax.axvspan(50, 75, alpha=0.10)
    ax.axvspan(75, 100, alpha=0.06)
    ax.axvline(50, linestyle="--", linewidth=1, alpha=0.45)
    ax.axvline(75, linestyle="--", linewidth=1, alpha=0.45)

    ax.text(25, 1.015, "Low", ha="center", va="bottom", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.text(62.5, 1.015, "Medium", ha="center", va="bottom", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.text(87.5, 1.015, "High", ha="center", va="bottom", transform=ax.get_xaxis_transform(), fontsize=8)


def plot_top_n_confidence(results: pd.DataFrame, output_dir: Path, top_n: int) -> Path:
    top = results.head(top_n).copy().reset_index(drop=True)
    height = max(5.5, 0.36 * len(top) + 1.8)
    fig, ax = plt.subplots(figsize=(12.8, height))

    labels = [site_rank_label(row) for _, row in top.iterrows()]
    add_confidence_bands(ax)
    ax.barh(labels, top["data_confidence_score"])
    ax.invert_yaxis()

    for index, row in top.iterrows():
        confidence = float(row["data_confidence_score"])
        level = str(row["data_confidence_level"])
        readiness = float(row["readiness_score"])
        ax.text(
            confidence + 0.6,
            index,
            f"{confidence:.1f} | {level} | readiness {readiness:.1f}",
            va="center",
            fontsize=8,
            clip_on=False,
        )

    ax.set_xlim(0, 100)
    ax.set_xlabel("Data confidence score")
    ax.set_title(f"Top {len(top)} Candidate Sites by Data Confidence", fontsize=14, pad=18)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    fig.text(
        0.5,
        0.035,
        "Confidence shows input support/completeness, not site readiness. Use this Top-N view before the full compact appendix chart.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=[0.06, 0.08, 0.98, 0.93])

    output_path = output_dir / f"data_confidence_top_{len(top)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a scalable Top-N data-confidence chart.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV to visualize.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Folder for generated scalable visuals.")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of sites to include in the readable chart.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(Path(args.results))
    if results.empty:
        raise SystemExit("No valid rows found in results file.")

    top_n = max(1, min(args.top_n, len(results)))
    output_path = plot_top_n_confidence(results, output_dir, top_n)

    print("SCALABLE DATA CONFIDENCE CHART")
    print("------------------------------")
    print(f"Results file: {args.results}")
    print(f"Sites evaluated: {len(results)}")
    print(f"Top-N chart size: {top_n}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
