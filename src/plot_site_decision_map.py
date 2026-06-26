"""Create a GIS-based V2 EV charging site decision map.

This is a true map redesign. It uses GeoPandas with an official county
boundary shapefile and, when available, a light web basemap from Contextily.

Default inputs:
- data/inputs/real_sites_v2.csv
- data/outputs/v2_executive_site_summary.csv

Default output:
- data/outputs/charts/v2_site_decision_map.png

Install optional GIS dependencies before running:

    pip install -r requirements-gis.txt
"""

from __future__ import annotations

import argparse
import math
import sys
import textwrap
import urllib.request
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter
import pandas as pd

try:
    import geopandas as gpd
except ImportError as exc:  # pragma: no cover - friendly runtime message
    raise SystemExit(
        "GeoPandas is required for the GIS decision map.\n"
        "Install the optional GIS dependencies with:\n\n"
        "    pip install -r requirements-gis.txt\n"
    ) from exc

try:
    import contextily as ctx
except ImportError:  # Contextily is optional; map still works without tiles.
    ctx = None

DEFAULT_SITES = "data/inputs/real_sites_v2.csv"
DEFAULT_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_OUTPUT = "data/outputs/charts/v2_site_decision_map.png"
DEFAULT_BOUNDARY_ZIP = "data/source_extracts/gis/tl_2024_us_county.zip"
DEFAULT_BOUNDARY_URL = "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"
WEB_MERCATOR = "EPSG:3857"
WGS84 = "EPSG:4326"

# Target local geographies plus small independent cities inside/near the PWC area.
TARGET_GEOIDS = {
    "51059",  # Fairfax County
    "51600",  # Fairfax City
    "51153",  # Prince William County
    "51683",  # Manassas City
    "51685",  # Manassas Park City
}

ACTION_COLORS = {
    "Advance": "#1b9e77",
    "Promising": "#4c78a8",
    "High-review": "#f28e2b",
    "Monitor": "#8c8c8c",
    "Special-use": "#b55a7a",
}

ACTION_ORDER = ["Advance", "Promising", "High-review", "Monitor", "Special-use"]

# Only label the sites that carry the story. All sites still get ranked markers.
ALWAYS_LABEL_SITE_IDS = {"FFX002", "FFX004", "PWC006", "PWC002", "PWC003", "PWC008", "PWC001"}

LABEL_OFFSETS = {
    "FFX002": (12, 12),
    "FFX004": (-80, 18),
    "PWC006": (-82, -12),
    "FFX001": (-82, -14),
    "PWC002": (-90, 14),
    "PWC003": (12, -26),
    "PWC008": (14, -20),
    "PWC001": (-82, 28),
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    return int(round(number))


def format_int(value: Any) -> str:
    number = safe_int(value)
    return str(number) if number is not None else "-"


def short_tier(value: Any) -> str:
    text = str(value or "")
    lower = text.lower()
    if "tier 1" in lower:
        return "Tier 1"
    if "tier 2" in lower:
        return "Tier 2"
    if "tier 3" in lower:
        return "Tier 3"
    if "high-review" in lower:
        return "High-review"
    if "special-use" in lower or "low public-priority" in lower:
        return "Special-use"
    return text if text else "Unclassified"


def action_group(row: pd.Series) -> str:
    tier = short_tier(row.get("recommendation_tier", ""))
    strategy = str(row.get("expansion_strategy", "")).lower()
    site_id = str(row.get("site_id", ""))

    if tier == "Special-use" or site_id == "PWC003" or "do_not_advance" in strategy:
        return "Special-use"
    if tier == "High-review" or "review" in strategy:
        return "High-review"
    if tier == "Tier 3" or "monitor" in strategy:
        return "Monitor"
    if tier == "Tier 1":
        return "Advance"
    return "Promising"


def marker_size(score: Any) -> float:
    number = safe_float(score)
    if number is None:
        return 140
    return 85 + number * 7.0


def review_note(row: pd.Series) -> str:
    site_id = str(row.get("site_id", ""))
    flags = str(row.get("major_review_flags", "")).strip()
    if flags and flags.lower() != "nan":
        return flags
    if site_id == "PWC002":
        return "garage / Fire Marshal / AHJ review"
    if site_id == "PWC003":
        return "special-use or public-access decision"
    if site_id == "PWC008":
        return "nearby charging supply is already high"
    if str(row.get("electrical_risk_level", "")).lower() == "high":
        return "electrical review before expansion"
    return "verify site assumptions"


def load_site_data(sites_path: Path, executive_path: Path) -> gpd.GeoDataFrame:
    if not sites_path.exists():
        raise FileNotFoundError(f"Site input file not found: {sites_path}")
    if not executive_path.exists():
        raise FileNotFoundError(f"Executive summary file not found: {executive_path}")

    sites = pd.read_csv(sites_path)
    executive = pd.read_csv(executive_path)

    required_site_cols = {"site_id", "lat", "lon"}
    missing_site_cols = sorted(required_site_cols - set(sites.columns))
    if missing_site_cols:
        raise ValueError(f"Site input is missing required columns: {missing_site_cols}")

    required_exec_cols = {"model_rank", "site_id", "site_name", "readiness_score", "recommendation_tier"}
    missing_exec_cols = sorted(required_exec_cols - set(executive.columns))
    if missing_exec_cols:
        raise ValueError(f"Executive summary is missing required columns: {missing_exec_cols}")

    merged = executive.merge(sites[["site_id", "lat", "lon"]], on="site_id", how="left")
    merged["lat"] = pd.to_numeric(merged["lat"], errors="coerce")
    merged["lon"] = pd.to_numeric(merged["lon"], errors="coerce")
    merged["model_rank"] = pd.to_numeric(merged["model_rank"], errors="coerce")
    merged["readiness_score"] = pd.to_numeric(merged["readiness_score"], errors="coerce")
    merged = merged.dropna(subset=["lat", "lon"]).copy()
    merged["action_group"] = merged.apply(action_group, axis=1)
    merged["tier_short"] = merged["recommendation_tier"].apply(short_tier)

    return gpd.GeoDataFrame(
        merged,
        geometry=gpd.points_from_xy(merged["lon"], merged["lat"]),
        crs=WGS84,
    )


def download_boundary_if_needed(boundary_zip: Path, boundary_url: str, no_download: bool) -> None:
    if boundary_zip.exists() and boundary_zip.stat().st_size > 0:
        return
    if no_download:
        raise FileNotFoundError(
            f"Boundary shapefile ZIP not found: {boundary_zip}\n"
            "Download it manually or rerun without --no-download-boundary."
        )
    ensure_parent(boundary_zip)
    print(f"Downloading county boundary shapefile: {boundary_url}")
    urllib.request.urlretrieve(boundary_url, boundary_zip)


def load_county_boundaries(boundary_zip: Path) -> gpd.GeoDataFrame:
    counties = gpd.read_file(f"zip://{boundary_zip.resolve()}")
    if counties.crs is None:
        counties = counties.set_crs(WGS84)
    if "STATEFP" in counties.columns:
        counties = counties[counties["STATEFP"].astype(str) == "51"].copy()
    if "GEOID" in counties.columns:
        counties = counties[counties["GEOID"].astype(str).isin(TARGET_GEOIDS)].copy()
    if counties.empty:
        raise ValueError("County shapefile loaded, but target Fairfax / Prince William geographies were not found.")
    return counties


def add_basemap(ax) -> bool:
    if ctx is None:
        return False
    try:
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            attribution_size=6,
            alpha=0.98,
        )
        return True
    except Exception as exc:  # pragma: no cover - depends on network/tile provider
        print(f"Basemap skipped: {exc}")
        return False


def webmercator_to_lon_formatter(x: float, _pos: int) -> str:
    lon = x / 6378137.0 * 180.0 / math.pi
    return f"{lon:.2f}°"


def webmercator_to_lat_formatter(y: float, _pos: int) -> str:
    lat = (2.0 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2.0) * 180.0 / math.pi
    return f"{lat:.2f}°"


def set_map_extent(ax, sites_3857: gpd.GeoDataFrame, pad_meters: float = 14500) -> None:
    minx, miny, maxx, maxy = sites_3857.total_bounds
    ax.set_xlim(minx - pad_meters, maxx + pad_meters)
    ax.set_ylim(miny - pad_meters, maxy + pad_meters)


def county_label(row: pd.Series) -> str:
    name = str(row.get("NAME", ""))
    if name == "Fairfax":
        return "Fairfax County"
    if name == "Prince William":
        return "Prince William County"
    if name == "Manassas Park":
        return "Manassas Park"
    return name


def plot_county_context(ax, counties_3857: gpd.GeoDataFrame, basemap_added: bool) -> None:
    if not basemap_added:
        counties_3857.plot(ax=ax, facecolor="#f7f8fa", edgecolor="#475569", linewidth=1.0, alpha=0.62, zorder=1)
    counties_3857.boundary.plot(ax=ax, color="#0f172a", linewidth=1.05, alpha=0.72, zorder=3)

    for _, row in counties_3857.iterrows():
        label = county_label(row)
        if not label:
            continue
        point = row.geometry.representative_point()
        ax.text(
            point.x,
            point.y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color="#334155",
            alpha=0.70,
            path_effects=[pe.withStroke(linewidth=3.5, foreground="white", alpha=0.88)],
            zorder=2 if basemap_added else 4,
        )


def plot_sites(ax, sites_3857: gpd.GeoDataFrame) -> None:
    for action in ACTION_ORDER:
        subset = sites_3857[sites_3857["action_group"] == action]
        if subset.empty:
            continue
        edgecolors = ["#7f1d1d" if str(risk).lower() == "high" else "#111827" for risk in subset["electrical_risk_level"]]
        linewidths = [2.6 if str(risk).lower() == "high" else 1.05 for risk in subset["electrical_risk_level"]]
        subset.plot(
            ax=ax,
            markersize=[marker_size(score) for score in subset["readiness_score"]],
            color=ACTION_COLORS[action],
            edgecolor=edgecolors,
            linewidth=linewidths,
            alpha=0.94,
            zorder=5,
        )

    for _, row in sites_3857.sort_values("model_rank").iterrows():
        rank = format_int(row.get("model_rank"))
        ax.text(
            row.geometry.x,
            row.geometry.y,
            rank,
            ha="center",
            va="center",
            fontsize=8.7,
            fontweight="bold",
            color="white",
            path_effects=[pe.withStroke(linewidth=2.25, foreground="#111827")],
            zorder=6,
        )


def sites_to_label(sites_3857: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ranked = sites_3857.sort_values("model_rank")
    top_five_ids = set(ranked.head(5)["site_id"].astype(str))
    high_risk_ids = set(ranked[ranked["electrical_risk_level"].astype(str).str.lower() == "high"]["site_id"].astype(str))
    label_ids = top_five_ids | high_risk_ids | ALWAYS_LABEL_SITE_IDS
    return ranked[ranked["site_id"].astype(str).isin(label_ids)]


def add_site_labels(ax, sites_3857: gpd.GeoDataFrame) -> None:
    for _, row in sites_to_label(sites_3857).iterrows():
        site_id = str(row.get("site_id", ""))
        score = safe_float(row.get("readiness_score"))
        score_text = f"{score:.1f}" if score is not None else "n/a"
        ports_now = format_int(row.get("ports_now"))
        future = format_int(row.get("future_ready_capacity"))
        label = f"#{format_int(row.get('model_rank'))} {site_id}\n{score_text} | {ports_now}->{future} ports"
        dx, dy = LABEL_OFFSETS.get(site_id, (10, 10))
        ax.annotate(
            label,
            xy=(row.geometry.x, row.geometry.y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if dx < 0 else "left",
            va="center",
            fontsize=7.1,
            color="#111827",
            arrowprops={"arrowstyle": "-", "lw": 0.55, "color": "#334155", "alpha": 0.68},
            bbox={"boxstyle": "round,pad=0.20", "fc": "white", "ec": "#cbd5e1", "alpha": 0.94, "lw": 0.55},
            zorder=7,
        )


def add_map_legend(ax) -> None:
    handles = [
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor=ACTION_COLORS[action], markeredgecolor="#111827", markersize=8, label=action)
        for action in ACTION_ORDER
    ]
    handles.append(
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="white", markeredgecolor="#7f1d1d", markeredgewidth=2.4, markersize=8, label="High electrical risk")
    )
    ax.legend(handles=handles, loc="lower left", title="Planning action", fontsize=8.0, title_fontsize=8.5, framealpha=0.94)


def add_north_arrow(ax) -> None:
    ax.annotate(
        "N",
        xy=(0.962, 0.925),
        xytext=(0.962, 0.840),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "lw": 1.1, "color": "#111827"},
        color="#111827",
        zorder=8,
    )


def add_scale_bar(ax, length_m: int = 16093) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    start_x = x0 + (x1 - x0) * 0.055
    start_y = y0 + (y1 - y0) * 0.055
    ax.plot([start_x, start_x + length_m], [start_y, start_y], color="#111827", lw=2.2, zorder=8)
    ax.plot([start_x, start_x], [start_y - 700, start_y + 700], color="#111827", lw=1.2, zorder=8)
    ax.plot([start_x + length_m, start_x + length_m], [start_y - 700, start_y + 700], color="#111827", lw=1.2, zorder=8)
    ax.text(start_x + length_m / 2, start_y + 1500, "10 miles", ha="center", va="bottom", fontsize=7.5, color="#111827", zorder=8)


def style_map_axis(ax) -> None:
    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(webmercator_to_lon_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(webmercator_to_lat_formatter))
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.18, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("#334155")


def wrap_line(text: str, width: int = 40) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def decision_panel_lines(sites: gpd.GeoDataFrame) -> list[str]:
    ranked = sites.sort_values("model_rank")
    top = ranked.iloc[0]
    pwc = ranked[ranked["site_id"].astype(str).str.startswith("PWC")]
    top_pwc = pwc.iloc[0] if not pwc.empty else None

    lines = [
        "Decision summary",
        "",
        f"Top site: #{format_int(top.get('model_rank'))} {top.get('site_id')}",
        f"Score {safe_float(top.get('readiness_score')):.1f} | {format_int(top.get('ports_now'))}->{format_int(top.get('future_ready_capacity'))} ports",
    ]
    if top_pwc is not None:
        lines.extend([
            "",
            f"Top PWC: #{format_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')}",
            f"Score {safe_float(top_pwc.get('readiness_score')):.1f} | {format_int(top_pwc.get('ports_now'))}->{format_int(top_pwc.get('future_ready_capacity'))} ports",
        ])

    lines.extend(["", "Top 5 action list"])
    for _, row in ranked.head(5).iterrows():
        score = safe_float(row.get("readiness_score"))
        score_text = f"{score:.1f}" if score is not None else "n/a"
        lines.append(f"#{format_int(row.get('model_rank'))} {row.get('site_id')} | {score_text} | {row.get('action_group')}")

    lines.extend(["", "Review watchlist"])
    watchlist = ranked[(ranked["action_group"].isin(["High-review", "Special-use"])) | (ranked["electrical_risk_level"].astype(str).str.lower() == "high")]
    for _, row in watchlist.head(6).iterrows():
        lines.append(f"{row.get('site_id')}: {textwrap.shorten(review_note(row), width=38, placeholder='...')}")

    lines.extend(["", "Port plan snapshot", "Site    Now -> Future"])
    for _, row in ranked.head(8).iterrows():
        lines.append(f"{row.get('site_id'):<7} {format_int(row.get('ports_now')):>2} -> {format_int(row.get('future_ready_capacity')):<2}")
    return lines


def draw_side_panel(panel_ax, sites: gpd.GeoDataFrame) -> None:
    panel_ax.set_axis_off()
    panel = FancyBboxPatch(
        (0.02, 0.02),
        0.96,
        0.96,
        transform=panel_ax.transAxes,
        boxstyle="round,pad=0.014,rounding_size=0.018",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="white",
        alpha=0.98,
        zorder=1,
    )
    panel_ax.add_patch(panel)
    panel_ax.text(
        0.07,
        0.95,
        "\n".join(decision_panel_lines(sites)),
        transform=panel_ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.4,
        color="#111827",
        linespacing=1.27,
        zorder=2,
    )


def plot_gis_decision_map(sites: gpd.GeoDataFrame, counties: gpd.GeoDataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    sites_3857 = sites.to_crs(WEB_MERCATOR)
    counties_3857 = counties.to_crs(WEB_MERCATOR)

    fig = plt.figure(figsize=(16.8, 10.2), facecolor="white")
    ax = fig.add_axes([0.045, 0.115, 0.690, 0.765])
    panel_ax = fig.add_axes([0.755, 0.145, 0.215, 0.695])
    ax.set_facecolor("#eef2f7")

    set_map_extent(ax, sites_3857, pad_meters=15000)
    basemap_added = add_basemap(ax)
    plot_county_context(ax, counties_3857, basemap_added)
    plot_sites(ax, sites_3857)
    add_site_labels(ax, sites_3857)
    add_map_legend(ax)
    add_north_arrow(ax)
    add_scale_bar(ax)
    draw_side_panel(panel_ax, sites)
    style_map_axis(ax)

    subtitle = "Official county boundaries, basemap context, ranked candidate sites, action categories, and right-sizing notes."
    if not basemap_added:
        subtitle = "Official county boundaries and ranked candidate sites; basemap skipped or unavailable."

    fig.suptitle("V2 Public EV Charging Candidate Sites — GIS Decision Map", fontsize=16, fontweight="bold", y=0.967)
    fig.text(0.5, 0.922, subtitle, ha="center", fontsize=9.6, color="#111827")
    fig.text(
        0.5,
        0.025,
        "Planning screen only — not an engineering, utility, permitting, procurement, or construction approval.",
        ha="center",
        fontsize=8.4,
        color="#475569",
    )

    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a GIS-based V2 EV charging decision map.")
    parser.add_argument("--sites", default=DEFAULT_SITES, help="V2 candidate-site input CSV with lat/lon.")
    parser.add_argument("--input", default=DEFAULT_EXECUTIVE_SUMMARY, help="V2 executive summary CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    parser.add_argument("--boundary-zip", default=DEFAULT_BOUNDARY_ZIP, help="Local Census county shapefile ZIP path.")
    parser.add_argument("--boundary-url", default=DEFAULT_BOUNDARY_URL, help="Boundary ZIP URL used when local file is missing.")
    parser.add_argument("--no-download-boundary", action="store_true", help="Do not download boundary shapefile automatically.")
    # Backward-compatible ignored arguments from older workflow versions.
    parser.add_argument("--results", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--electrical-summary", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--right-sizing", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--right-sizing-validation", default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sites_path = Path(args.sites)
    executive_path = Path(args.input)
    output_path = Path(args.output)
    boundary_zip = Path(args.boundary_zip)

    sites = load_site_data(sites_path, executive_path)
    download_boundary_if_needed(boundary_zip, args.boundary_url, args.no_download_boundary)
    counties = load_county_boundaries(boundary_zip)
    plot_gis_decision_map(sites, counties, output_path)

    print("V2 GIS DECISION MAP")
    print("-------------------")
    print(f"Sites: {sites_path}")
    print(f"Executive summary: {executive_path}")
    print(f"Boundary ZIP: {boundary_zip}")
    print(f"Output: {output_path}")
    print(f"Sites plotted: {len(sites)}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"GIS decision map failed: {exc}", file=sys.stderr)
        raise
