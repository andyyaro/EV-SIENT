"""Create a simple candidate-site readiness map.

This script intentionally uses only pandas and matplotlib. It does not require
GeoPandas, QGIS, web map tiles, or a GIS basemap. The output is a planning
visual that plots candidate sites by longitude/latitude and labels each site
with its readiness score.

The map also adds a short interpretation note when the top candidate is stable
across sensitivity scenarios and scoring profiles.

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
DEFAULT_SENSITIVITY = "data/outputs/sensitivity_summary.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/site_readiness_map.png"

LABEL_OFFSETS = {
    "FFX001": (-70, -14),
    "FFX002": (12, 14),
    "PWC001": (12, 12),
    "PWC002": (-78, 14),
    "PWC003": (8, 8),
    "PWC004": (12, 4),
}

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compact_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


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


def top_site_id_from_results(data: pd.DataFrame) -> str:
    if "model_rank" not in data.columns or "site_id" not in data.columns:
        return ""
    ranks = pd.to_numeric(data["model_rank"], errors="coerce")
    if ranks.isna().all():
        return ""
    top_row = data.loc[ranks.idxmin()]
    return str(top_row.get("site_id", ""))


def profile_top_site(profile_results: pd.DataFrame) -> tuple[str, int]:
    required = {"profile_name", "profile_rank", "site_id"}
    if profile_results.empty or not required.issubset(profile_results.columns):
        return "", 0

    top_by_profile = (
        profile_results.sort_values(["profile_name", "profile_rank"])
        .groupby("profile_name", as_index=False)
        .first()
    )
    top_sites = top_by_profile["site_id"].astype(str).unique().tolist()
    if len(top_sites) == 1:
        return top_sites[0], len(top_by_profile)
    return "", len(top_by_profile)


def sensitivity_is_stable(sensitivity: pd.DataFrame) -> bool:
    if sensitivity.empty or "rank_range" not in sensitivity.columns:
        return False
    rank_range = pd.to_numeric(sensitivity["rank_range"], errors="coerce")
    return bool(not rank_range.isna().any() and (rank_range == 0).all())


def map_interpretation_note(
    data: pd.DataFrame,
    sensitivity: pd.DataFrame,
    profile_results: pd.DataFrame,
) -> str:
    top_site = top_site_id_from_results(data)
    profile_site, profile_count = profile_top_site(profile_results)
    stable_sensitivity = sensitivity_is_stable(sensitivity)

    if top_site and stable_sensitivity and profile_site == top_site and profile_count > 0:
        return f"{top_site} is the stable top candidate: #1 in the base model, stable in sensitivity, and #1 across {profile_count} scoring profiles."
    if top_site and profile_site == top_site and profile_count > 0:
        return f"{top_site} is #1 in the base model and #1 across {profile_count} scoring profiles."
    if top_site and stable_sensitivity:
        return f"{top_site} is #1 in the base model; sensitivity ranks stayed stable."
    if top_site:
        return f"{top_site} is the current #1 site under the base model."
    return "Candidate locations shown with readiness-score markers."


def stable_top_candidate_found(data: pd.DataFrame, sensitivity: pd.DataFrame, profile_results: pd.DataFrame) -> bool:
    top_site = top_site_id_from_results(data)
    profile_site, profile_count = profile_top_site(profile_results)
    return bool(top_site and sensitivity_is_stable(sensitivity) and profile_site == top_site and profile_count > 0)


def site_label(row: pd.Series) -> str:
    """Create a compact map label."""
    site_id = str(row.get("site_id", ""))
    score = row.get("readiness_score", "")
    rank = row.get("model_rank", "")

    if pd.isna(score) or score == "":
        return site_id

    try:
        rank_text = f"#{int(rank)} " if pd.notna(rank) and str(rank) != "" else ""
    except (TypeError, ValueError):
        rank_text = ""

    return f"{rank_text}{site_id}\n{float(score):.1f}"


def marker_size(score) -> float:
    """Scale marker size by readiness score while keeping all sites visible."""
    try:
        return 80 + float(score) * 6
    except (TypeError, ValueError):
        return 180


def label_offset(site_id: str) -> tuple[int, int]:
    """Return a hand-tuned label offset so nearby labels do not overlap."""
    return LABEL_OFFSETS.get(str(site_id), (8, 8))


def planning_note(data: pd.DataFrame) -> str:
    site_ids = set(data["site_id"].astype(str)) if "site_id" in data.columns else set()
    notes = []
    if "PWC002" in site_ids:
        notes.append("PWC002 = high-review garage candidate")
    if "PWC004" in site_ids:
        notes.append("PWC004 = future/reopened planning assumption")
    return "; ".join(notes)


def plot_site_map(
    data: pd.DataFrame,
    output_path: Path,
    sensitivity: pd.DataFrame | None = None,
    profile_results: pd.DataFrame | None = None,
) -> None:
    """Create and save the site map."""
    ensure_parent_dir(output_path)
    sensitivity = sensitivity if sensitivity is not None else pd.DataFrame()
    profile_results = profile_results if profile_results is not None else pd.DataFrame()

    fig, ax = plt.subplots(figsize=(11.2, 8.4))

    if "readiness_score" in data.columns:
        scores = pd.to_numeric(data["readiness_score"], errors="coerce")
    else:
        scores = pd.Series([0] * len(data), index=data.index)

    sizes = [marker_size(score) for score in scores]
    scatter = ax.scatter(
        data["lon"],
        data["lat"],
        s=sizes,
        c=scores,
        alpha=0.75,
        edgecolors="black",
        linewidths=0.8,
        zorder=2,
    )

    top_site = top_site_id_from_results(data)
    if top_site:
        top_row = data[data["site_id"].astype(str) == top_site]
        if not top_row.empty:
            star_size = 260 if stable_top_candidate_found(data, sensitivity, profile_results) else 220
            ax.scatter(
                top_row["lon"],
                top_row["lat"],
                s=star_size,
                marker="*",
                alpha=0.9,
                edgecolors="black",
                linewidths=0.9,
                zorder=4,
            )

    for _, row in data.iterrows():
        offset = label_offset(row.get("site_id", ""))
        ax.annotate(
            site_label(row),
            xy=(row["lon"], row["lat"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "lw": 0.4, "alpha": 0.6},
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "alpha": 0.80, "lw": 0.3},
            zorder=5,
        )

    cbar = fig.colorbar(scatter, ax=ax, label="Readiness score")
    cbar.ax.tick_params(labelsize=8)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.suptitle("Candidate EV Charging Sites — Readiness Map", fontsize=14)
    ax.set_title(map_interpretation_note(data, sensitivity, profile_results), fontsize=9, pad=8)
    ax.grid(True, alpha=0.25)

    lon_padding = max((data["lon"].max() - data["lon"].min()) * 0.16, 0.01)
    lat_padding = max((data["lat"].max() - data["lat"].min()) * 0.16, 0.01)
    ax.set_xlim(data["lon"].min() - lon_padding, data["lon"].max() + lon_padding)
    ax.set_ylim(data["lat"].min() - lat_padding, data["lat"].max() + lat_padding)

    note = planning_note(data)
    if note:
        fig.text(0.5, 0.055, f"Planning notes: {note}.", ha="center", fontsize=8)
    footer = "Planning visual only — longitude/latitude scatter, no basemap, parcel boundary, engineering layout, or permitting decision."
    fig.text(0.5, 0.018, footer, ha="center", fontsize=8)
    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a simple readiness map of candidate EV charging sites.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Candidate-site input CSV.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV with readiness scores.")
    parser.add_argument("--sensitivity", default=DEFAULT_SENSITIVITY, help="Sensitivity summary CSV.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Scoring profile results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG map path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    results_path = Path(args.results)
    sensitivity_path = Path(args.sensitivity)
    profile_results_path = Path(args.profile_results)
    output_path = Path(args.output)

    data = load_map_data(input_path, results_path)
    sensitivity = read_csv_if_exists(sensitivity_path)
    profile_results = read_csv_if_exists(profile_results_path)
    interpretation = map_interpretation_note(data, sensitivity, profile_results)
    plot_site_map(data, output_path, sensitivity, profile_results)

    print("CANDIDATE SITE READINESS MAP")
    print("----------------------------")
    print(f"Input file: {input_path}")
    print(f"Results file: {results_path if results_path.exists() else 'not found; plotted coordinates only'}")
    print(f"Sensitivity file: {sensitivity_path if sensitivity_path.exists() else 'not found'}")
    print(f"Profile results file: {profile_results_path if profile_results_path.exists() else 'not found'}")
    print(f"Saved map: {output_path}")
    print(f"Map note: {interpretation}")
    print(f"Planning note: {planning_note(data)}")
    print()
    print("Sites plotted:")
    display_cols = [col for col in ["site_id", "site_name", "model_rank", "readiness_score", "recommendation_tier"] if col in data.columns]
    print(data[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()
