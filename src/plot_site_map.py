"""Create a multi-panel candidate-site readiness map.

This script intentionally uses only pandas and matplotlib. It does not require
GeoPandas, QGIS, web map tiles, or a GIS basemap. The output is a planning
visual that plots candidate sites by longitude/latitude and labels each site
with its readiness score.

The map includes:
- an overview panel for all six candidate sites
- a Fairfax City zoom panel
- a Prince William County zoom panel
- marker size/color by readiness score
- marker shape by recommendation tier
- a star overlay for the top-ranked site
- a ranked summary panel for quick interpretation

Default output:
- data/outputs/charts/site_readiness_map.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v1.csv"
DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_SENSITIVITY = "data/outputs/sensitivity_summary.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/site_readiness_map.png"

LABEL_OFFSETS = {
    "FFX001": (-84, -10),
    "FFX002": (14, 16),
    "PWC001": (12, 12),
    "PWC002": (-84, 14),
    "PWC003": (8, 8),
    "PWC004": (12, 4),
}

ZOOM_LABEL_OFFSETS = {
    "FFX001": (-88, -12),
    "FFX002": (12, 16),
    "PWC001": (12, 12),
    "PWC002": (-78, 14),
    "PWC003": (8, 8),
    "PWC004": (12, 0),
}

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}

TIER_MARKERS = {
    "Tier 1": "o",
    "High-review": "s",
    "Tier 2": "^",
    "Tier 3": "D",
    "Special-use": "X",
}

TIER_ORDER = ["Tier 1", "High-review", "Tier 2", "Tier 3", "Special-use"]


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
            col
            for col in [
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
    data["tier_short"] = data.get("recommendation_tier", "").apply(compact_tier)
    data["readiness_score_num"] = pd.to_numeric(data.get("readiness_score", ""), errors="coerce")
    data["model_rank_num"] = pd.to_numeric(data.get("model_rank", ""), errors="coerce")
    data["locality_group"] = data["site_id"].astype(str).str.extract(r"^(FFX|PWC)", expand=False).fillna("Other")
    return data


def top_site_id_from_results(data: pd.DataFrame) -> str:
    if "model_rank_num" not in data.columns or "site_id" not in data.columns:
        return ""
    ranks = pd.to_numeric(data["model_rank_num"], errors="coerce")
    if ranks.isna().all():
        return ""
    return str(data.loc[ranks.idxmin()].get("site_id", ""))


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


def map_interpretation_note(data: pd.DataFrame, sensitivity: pd.DataFrame, profile_results: pd.DataFrame) -> str:
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


def safe_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def site_label(row: pd.Series) -> str:
    site_id = str(row.get("site_id", ""))
    score = safe_float(row.get("readiness_score_num", row.get("readiness_score", "")))
    rank = safe_float(row.get("model_rank_num", row.get("model_rank", "")))
    if score is None:
        return site_id
    rank_text = f"#{int(rank)} " if rank is not None else ""
    return f"{rank_text}{site_id}\n{score:.1f}"


def marker_size(score) -> float:
    score_number = safe_float(score)
    if score_number is None:
        return 180
    return 90 + score_number * 6


def planning_note(data: pd.DataFrame) -> str:
    site_ids = set(data["site_id"].astype(str)) if "site_id" in data.columns else set()
    notes = []
    if "PWC002" in site_ids:
        notes.append("PWC002 = high-review garage candidate")
    if "PWC004" in site_ids:
        notes.append("PWC004 = future/reopened planning assumption")
    if "PWC003" in site_ids:
        notes.append("PWC003 = public-access decision needed")
    return "; ".join(notes)


def score_norm(scores: pd.Series) -> tuple[Normalize, str]:
    valid_scores = scores.dropna()
    if valid_scores.empty:
        return Normalize(vmin=0, vmax=100), "viridis"

    vmin = float(valid_scores.min())
    vmax = float(valid_scores.max())
    if vmin == vmax:
        vmin = max(0, vmin - 1)
        vmax = vmax + 1
    return Normalize(vmin=vmin, vmax=vmax), "viridis"


def axis_bounds(data: pd.DataFrame, pad_factor: float = 0.20, min_lon_pad: float = 0.010, min_lat_pad: float = 0.010) -> tuple[float, float, float, float]:
    lon_min, lon_max = data["lon"].min(), data["lon"].max()
    lat_min, lat_max = data["lat"].min(), data["lat"].max()
    lon_pad = max((lon_max - lon_min) * pad_factor, min_lon_pad)
    lat_pad = max((lat_max - lat_min) * pad_factor, min_lat_pad)
    return lon_min - lon_pad, lon_max + lon_pad, lat_min - lat_pad, lat_max + lat_pad


def draw_cluster_boxes(ax, data: pd.DataFrame) -> None:
    """Draw light dashed boxes around clusters in the overview panel only."""
    if data.empty or "locality_group" not in data.columns:
        return

    for _, group in data.groupby("locality_group"):
        if group.empty:
            continue
        lon0, lon1, lat0, lat1 = axis_bounds(group, pad_factor=0.55, min_lon_pad=0.010, min_lat_pad=0.010)
        rect = Rectangle(
            (lon0, lat0),
            lon1 - lon0,
            lat1 - lat0,
            fill=False,
            linestyle="--",
            linewidth=0.9,
            alpha=0.40,
            zorder=1,
        )
        ax.add_patch(rect)


def plot_sites_on_axis(
    ax,
    data: pd.DataFrame,
    norm: Normalize,
    cmap_name: str,
    top_site: str,
    sensitivity: pd.DataFrame,
    profile_results: pd.DataFrame,
    label_offsets: dict[str, tuple[int, int]],
    show_legend: bool = False,
) -> None:
    """Draw site markers and labels on one map axis."""
    for tier, group in data.groupby("tier_short", dropna=False):
        scores = pd.to_numeric(group["readiness_score_num"], errors="coerce")
        sizes = [marker_size(score) for score in scores]
        ax.scatter(
            group["lon"],
            group["lat"],
            s=sizes,
            c=scores,
            cmap=cmap_name,
            norm=norm,
            marker=TIER_MARKERS.get(str(tier), "o"),
            alpha=0.78,
            edgecolors="black",
            linewidths=0.8,
            zorder=2,
        )

    if top_site:
        top_row = data[data["site_id"].astype(str) == top_site]
        if not top_row.empty:
            star_size = 300 if stable_top_candidate_found(data, sensitivity, profile_results) else 250
            ax.scatter(
                top_row["lon"],
                top_row["lat"],
                s=star_size,
                marker="*",
                facecolors="none",
                edgecolors="black",
                linewidths=1.2,
                zorder=4,
            )

    for _, row in data.iterrows():
        site_id = str(row.get("site_id", ""))
        ax.annotate(
            site_label(row),
            xy=(row["lon"], row["lat"]),
            xytext=label_offsets.get(site_id, (8, 8)),
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "lw": 0.4, "alpha": 0.6},
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "alpha": 0.84, "lw": 0.3},
            zorder=5,
        )

    ax.grid(True, alpha=0.25)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    if show_legend:
        add_tier_legend(ax, data)


def ranked_summary(data: pd.DataFrame) -> str:
    if data.empty:
        return "Ranked readiness\nNo sites loaded."

    summary = data.sort_values("model_rank_num", na_position="last").copy()
    lines = ["Ranked readiness", ""]
    for _, row in summary.iterrows():
        site_id = str(row.get("site_id", ""))
        score = safe_float(row.get("readiness_score_num", row.get("readiness_score", "")))
        rank = safe_float(row.get("model_rank_num", row.get("model_rank", "")))
        tier = compact_tier(row.get("recommendation_tier", ""))
        ports = row.get("recommended_ports_now", "")
        rank_text = f"#{int(rank)}" if rank is not None else "--"
        score_text = f"{score:.1f}" if score is not None else "n/a"
        ports_text = ""
        if str(ports) not in {"", "nan", "None"}:
            try:
                ports_text = f" | ports: {int(float(ports))}"
            except (TypeError, ValueError):
                ports_text = f" | ports: {ports}"
        lines.append(f"{rank_text} {site_id}: {score_text}")
        lines.append(f"   {tier}{ports_text}")

    lines.extend([
        "",
        "How to read",
        "shape = recommendation tier",
        "size/color = readiness score",
        "star = top-ranked site",
    ])
    return "\n".join(lines)


def add_tier_legend(ax, data: pd.DataFrame) -> None:
    if "tier_short" not in data.columns:
        return

    present_tiers = [tier for tier in TIER_ORDER if tier in set(data["tier_short"].astype(str))]
    extra_tiers = sorted(set(data["tier_short"].astype(str)) - set(present_tiers))
    tiers = present_tiers + extra_tiers
    handles = [
        Line2D(
            [0],
            [0],
            marker=TIER_MARKERS.get(tier, "o"),
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            color="black",
            markersize=7,
            label=tier,
        )
        for tier in tiers
    ]
    if handles:
        ax.legend(handles=handles, title="Recommendation tier", loc="lower left", fontsize=8, title_fontsize=8, framealpha=0.90)


def plot_site_map(
    data: pd.DataFrame,
    output_path: Path,
    sensitivity: pd.DataFrame | None = None,
    profile_results: pd.DataFrame | None = None,
) -> None:
    """Create and save the multi-panel site map."""
    ensure_parent_dir(output_path)
    sensitivity = sensitivity if sensitivity is not None else pd.DataFrame()
    profile_results = profile_results if profile_results is not None else pd.DataFrame()

    scores = data["readiness_score_num"] if "readiness_score_num" in data.columns else pd.Series([0] * len(data), index=data.index)
    norm, cmap_name = score_norm(scores)
    top_site = top_site_id_from_results(data)

    fig = plt.figure(figsize=(15.8, 9.2))
    grid = fig.add_gridspec(
        2,
        3,
        width_ratios=[1.70, 1.06, 0.86],
        height_ratios=[1, 1],
        left=0.055,
        right=0.985,
        bottom=0.15,
        top=0.88,
        wspace=0.28,
        hspace=0.34,
    )

    ax_overview = fig.add_subplot(grid[:, 0])
    ax_ffx = fig.add_subplot(grid[0, 1])
    ax_pwc = fig.add_subplot(grid[1, 1])
    panel_ax = fig.add_subplot(grid[:, 2])
    panel_ax.axis("off")

    draw_cluster_boxes(ax_overview, data)
    plot_sites_on_axis(ax_overview, data, norm, cmap_name, top_site, sensitivity, profile_results, LABEL_OFFSETS, show_legend=True)
    ax_overview.set_title("Overview: all candidate sites", fontsize=10, pad=8)
    lon0, lon1, lat0, lat1 = axis_bounds(data, pad_factor=0.22, min_lon_pad=0.018, min_lat_pad=0.018)
    ax_overview.set_xlim(lon0, lon1)
    ax_overview.set_ylim(lat0, lat1)

    ffx = data[data["locality_group"] == "FFX"].copy()
    if not ffx.empty:
        plot_sites_on_axis(ax_ffx, ffx, norm, cmap_name, top_site, sensitivity, profile_results, ZOOM_LABEL_OFFSETS)
        ax_ffx.set_title("Zoom: Fairfax City", fontsize=10, pad=8)
        lon0, lon1, lat0, lat1 = axis_bounds(ffx, pad_factor=1.10, min_lon_pad=0.008, min_lat_pad=0.008)
        ax_ffx.set_xlim(lon0, lon1)
        ax_ffx.set_ylim(lat0, lat1)

    pwc = data[data["locality_group"] == "PWC"].copy()
    if not pwc.empty:
        plot_sites_on_axis(ax_pwc, pwc, norm, cmap_name, top_site, sensitivity, profile_results, ZOOM_LABEL_OFFSETS)
        ax_pwc.set_title("Zoom: Prince William County", fontsize=10, pad=8)
        lon0, lon1, lat0, lat1 = axis_bounds(pwc, pad_factor=0.30, min_lon_pad=0.012, min_lat_pad=0.012)
        ax_pwc.set_xlim(lon0, lon1)
        ax_pwc.set_ylim(lat0, lat1)

    panel_ax.text(
        0.0,
        1.0,
        ranked_summary(data),
        transform=panel_ax.transAxes,
        fontsize=8.5,
        va="top",
        ha="left",
        linespacing=1.30,
        bbox={"boxstyle": "round,pad=0.55", "fc": "white", "alpha": 0.95, "lw": 0.6},
    )

    cax = panel_ax.inset_axes([0.02, 0.04, 0.58, 0.035])
    mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap_name)
    mappable.set_array([])
    cbar = fig.colorbar(mappable, cax=cax, orientation="horizontal")
    cbar.set_label("Readiness score", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    fig.suptitle("Candidate EV Charging Sites — Readiness Map", fontsize=15, y=0.975)
    fig.text(0.50, 0.915, map_interpretation_note(data, sensitivity, profile_results), ha="center", fontsize=9)

    note = planning_note(data)
    if note:
        fig.text(0.50, 0.075, f"Planning notes: {note}.", ha="center", fontsize=8)
    footer = "Planning visual only — longitude/latitude scatter, no basemap, parcel boundary, engineering layout, utility-service map, or permitting decision."
    fig.text(0.50, 0.040, footer, ha="center", fontsize=8)

    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a multi-panel readiness map of candidate EV charging sites.")
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
