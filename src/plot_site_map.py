"""Create a simple candidate-site readiness map.

This script intentionally uses only pandas and matplotlib. It does not require
GeoPandas, QGIS, web map tiles, or a GIS basemap. The output is a planning
visual that plots candidate sites by longitude/latitude and labels each site
with its readiness score.

Default output:
- data/outputs/charts/site_readiness_map.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v1.csv"
DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/site_readiness_map.png"


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_map_data(input_path: Path, results_path: Path) -> pd.DataFrame:
    """Load candidate coordinates and join readiness results when available."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sites = pd.read_csv(input_path)
    required_site_cols = {"site_id", "site_name", "lat", "lon"}
    missing_site_cols = required_site_cols - set(sites.columns)
    if missing_site_cols:
        raise ValueError(f"Input file is missing required columns: {sorted(missing_site_cols)}")

    if results_path.exists():
        results = pd.read_csv(results_path)
        keep_cols = [
            col for col in [
                "site_id",
                "model_rank",
                "readiness_score",
                "recommendation_tier",
                "recommended_ports_now",
            ]
            if col in results.columns
        ]
        data = sites.merge(results[keep_cols], on="site_id", how="left")
    else:
        data = sites.copy()
        data["model_rank"] = ""
        data["readiness_score"] = ""
        data["recommendation_tier"] = "Run ev_charger_model.py first"
        data["recommended_ports_now"] = ""

    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data = data.dropna(subset=["lat", "lon"]).copy()
    return data


def site_label(row: pd.Series) -> str:
    """Create a compact map label."""
    site_id = str(row.get("site_id", ""))
    score = row.get("readiness_score", "")
    if pd.isna(score) or score == "":
        return site_id
    return f"{site_id}\n{float(score):.1f}"


def marker_size(score) -> float:
    """Scale marker size by readiness score while keeping all sites visible."""
    try:
        return 80 + float(score) * 6
    except (TypeError, ValueError):
        return 180


def plot_site_map(data: pd.DataFrame, output_path: Path) -> None:
    """Create and save the site map."""
    ensure_parent_dir(output_path)

    plt.figure(figsize=(10, 7))

    if "readiness_score" in data.columns:
        scores = pd.to_numeric(data["readiness_score"], errors="coerce")
    else:
        scores = pd.Series([0] * len(data), index=data.index)

    sizes = [marker_size(score) for score in scores]
    scatter = plt.scatter(
        data["lon"],
        data["lat"],
        s=sizes,
        c=scores,
        alpha=0.75,
        edgecolors="black",
        linewidths=0.8,
    )

    for _, row in data.iterrows():
        plt.annotate(
            site_label(row),
            xy=(row["lon"], row["lat"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "alpha": 0.75, "lw": 0.3},
        )

    plt.colorbar(scatter, label="Readiness score")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Candidate EV Charging Sites — Readiness Map")
    plt.grid(True, alpha=0.25)

    lon_padding = max((data["lon"].max() - data["lon"].min()) * 0.12, 0.01)
    lat_padding = max((data["lat"].max() - data["lat"].min()) * 0.12, 0.01)
    plt.xlim(data["lon"].min() - lon_padding, data["lon"].max() + lon_padding)
    plt.ylim(data["lat"].min() - lat_padding, data["lat"].max() + lat_padding)

    footer = "Planning visual only — longitude/latitude scatter, no basemap or engineering site boundary."
    plt.figtext(0.5, 0.01, footer, ha="center", fontsize=8)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(output_path, dpi=200)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a simple readiness map of candidate EV charging sites.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Candidate-site input CSV.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV with readiness scores.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG map path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    results_path = Path(args.results)
    output_path = Path(args.output)

    data = load_map_data(input_path, results_path)
    plot_site_map(data, output_path)

    print("CANDIDATE SITE READINESS MAP")
    print("----------------------------")
    print(f"Input file: {input_path}")
    print(f"Results file: {results_path if results_path.exists() else 'not found; plotted coordinates only'}")
    print(f"Saved map: {output_path}")
    print()
    print("Sites plotted:")
    display_cols = [col for col in ["site_id", "site_name", "model_rank", "readiness_score", "recommendation_tier"] if col in data.columns]
    print(data[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()
