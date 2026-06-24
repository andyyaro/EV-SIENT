"""Create a data-confidence visual.

This script reads the current model output and creates a chart that separates
site promise from input-data confidence.

The visual includes:
- a readiness-vs-confidence scatter panel
- a confidence-by-site bar panel
- threshold guides for Low, Medium, and High confidence
- short labels that show rank, site ID, and score

Run from the repository root after the model step:

    python src/plot_data_confidence_chart.py

Default output:

    data/outputs/charts/data_confidence_chart.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/data_confidence_chart.png"

CONFIDENCE_THRESHOLDS = {
    "Medium": 50,
    "High": 75,
}

LEVEL_MARKERS = {
    "High": "o",
    "Medium": "s",
    "Low": "X",
}

LEVEL_ORDER = ["High", "Medium", "Low"]

SCATTER_LABEL_OFFSETS = {
    "FFX002": (8, 8),
    "FFX001": (8, -14),
    "PWC002": (8, 8),
    "PWC004": (8, -14),
    "PWC001": (8, 8),
    "PWC003": (8, -14),
}


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


def site_short_label(row: pd.Series) -> str:
    rank = int(row["model_rank"])
    site_id = str(row["site_id"])
    return f"#{rank} {site_id}"


def confidence_gap(score: float) -> float:
    """Return points needed to reach High confidence."""
    return max(CONFIDENCE_THRESHOLDS["High"] - float(score), 0)


def chart_subtitle(results: pd.DataFrame) -> str:
    top = results.sort_values("model_rank").iloc[0]
    top_site = str(top["site_id"])
    top_conf = float(top["data_confidence_score"])
    top_level = str(top["data_confidence_level"])
    return f"{top_site} is the top readiness site, but confidence remains {top_level} ({top_conf:.1f}/100) until stakeholder and electrical data are confirmed."


def add_confidence_thresholds(ax) -> None:
    for label, value in CONFIDENCE_THRESHOLDS.items():
        ax.axvline(value, linestyle="--", linewidth=1, alpha=0.45)
        ax.text(value, 1.02, label, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8)


def add_level_legend(ax, present_levels: list[str]) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker=LEVEL_MARKERS.get(level, "o"),
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            color="black",
            markersize=7,
            label=level,
        )
        for level in present_levels
    ]
    if handles:
        ax.legend(handles=handles, title="Confidence level", loc="lower right", fontsize=8, title_fontsize=8, framealpha=0.9)


def plot_scatter_panel(ax, results: pd.DataFrame) -> None:
    """Plot readiness score against confidence score."""
    present_levels = [level for level in LEVEL_ORDER if level in set(results["data_confidence_level"].astype(str))]

    for level in present_levels:
        group = results[results["data_confidence_level"].astype(str) == level]
        sizes = 90 + group["readiness_score"] * 5
        ax.scatter(
            group["data_confidence_score"],
            group["readiness_score"],
            s=sizes,
            marker=LEVEL_MARKERS.get(level, "o"),
            alpha=0.78,
            edgecolors="black",
            linewidths=0.8,
            label=level,
            zorder=3,
        )

    for _, row in results.iterrows():
        site_id = str(row["site_id"])
        ax.annotate(
            f"{site_short_label(row)}\nR {row['readiness_score']:.1f} | C {row['data_confidence_score']:.1f}",
            xy=(row["data_confidence_score"], row["readiness_score"]),
            xytext=SCATTER_LABEL_OFFSETS.get(site_id, (8, 8)),
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "lw": 0.4, "alpha": 0.55},
            bbox={"boxstyle": "round,pad=0.22", "fc": "white", "alpha": 0.86, "lw": 0.3},
            zorder=5,
        )

    add_confidence_thresholds(ax)
    add_level_legend(ax, present_levels)

    ax.set_xlim(0, 100)
    y_min = max(0, float(results["readiness_score"].min()) - 8)
    y_max = min(100, float(results["readiness_score"].max()) + 10)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Data confidence score")
    ax.set_ylabel("Readiness score")
    ax.set_title("Readiness vs. data confidence", fontsize=11, pad=8)
    ax.grid(True, alpha=0.22)
    ax.set_axisbelow(True)

    ax.text(
        0.02,
        0.98,
        "Upper-right = stronger case\nUpper-left = promising, verify first",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8,
        bbox={"boxstyle": "round,pad=0.30", "fc": "white", "alpha": 0.86, "lw": 0.4},
    )


def plot_bar_panel(ax, results: pd.DataFrame) -> None:
    """Plot confidence score by site in model-rank order."""
    ordered = results.sort_values("model_rank", ascending=True).copy()
    ordered["short_label"] = ordered.apply(site_short_label, axis=1)
    y_positions = range(len(ordered))

    bars = ax.barh(list(y_positions), ordered["data_confidence_score"])
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(ordered["short_label"], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Data confidence score")
    ax.set_title("Confidence by model rank", fontsize=11, pad=8)

    for bar, (_, row) in zip(bars, ordered.iterrows()):
        score = float(row["data_confidence_score"])
        readiness = float(row["readiness_score"])
        level = str(row["data_confidence_level"])
        gap = confidence_gap(score)
        gap_text = "High-ready" if gap == 0 else f"+{gap:.1f} to High"
        ax.text(
            min(score + 1.2, 96),
            bar.get_y() + bar.get_height() / 2,
            f"{score:.1f} | {level} | readiness {readiness:.1f} | {gap_text}",
            va="center",
            fontsize=8,
            clip_on=False,
        )

    add_confidence_thresholds(ax)
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)


def plot_data_confidence_chart(results: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    fig = plt.figure(figsize=(14.8, 7.6))
    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.18, 1.0],
        left=0.07,
        right=0.965,
        bottom=0.16,
        top=0.82,
        wspace=0.25,
    )
    scatter_ax = fig.add_subplot(grid[0, 0])
    bar_ax = fig.add_subplot(grid[0, 1])

    plot_scatter_panel(scatter_ax, results)
    plot_bar_panel(bar_ax, results)

    fig.suptitle("EV Charger Site Data Confidence — Current Model Run", fontsize=15, y=0.965)
    fig.text(0.5, 0.895, chart_subtitle(results), ha="center", fontsize=9)

    footer = "Confidence is separate from readiness. It shows how complete and source-supported the inputs are, not whether a site is good or bad."
    fig.text(0.5, 0.055, footer, ha="center", fontsize=8)

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
