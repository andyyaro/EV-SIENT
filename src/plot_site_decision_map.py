"""Create GIS-based V2 EV charging decision maps.

The report map is a full planning figure for the deliverable package. The README
map is a cleaner, smaller visual generated from the same data for GitHub.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Circle, ConnectionPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter
import pandas as pd

try:
    import geopandas as gpd
except ImportError as exc:
    raise SystemExit(
        "GeoPandas is required. Install optional GIS dependencies with: "
        "pip install -r requirements-gis.txt"
    ) from exc

try:
    import contextily as ctx
except ImportError:
    ctx = None

DEFAULT_SITES = "data/inputs/real_sites_v2.csv"
DEFAULT_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_OUTPUT = "data/outputs/charts/v2_site_decision_map.png"
DEFAULT_README_OUTPUT = "data/outputs/charts/v2_site_decision_map_readme.png"
DEFAULT_DOCS_README_OUTPUT = "docs/assets/charts/v2_site_decision_map_readme.png"
DEFAULT_BOUNDARY_ZIP = "data/source_extracts/gis/tl_2024_us_county.zip"
DEFAULT_BOUNDARY_URL = "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"
DEFAULT_PACKAGE_CHART = "data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png"
DEFAULT_PACKAGE_README_CHART = "data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png"

WEB_MERCATOR = "EPSG:3857"
WGS84 = "EPSG:4326"
TARGET_GEOIDS = {"51059", "51600", "51153", "51683", "51685"}

ACTION_ORDER = ["Advance", "Promising", "High-review", "Monitor", "Special-use"]
ACTION_COLORS = {
    "Advance": "#1b9e77",
    "Promising": "#4c78a8",
    "High-review": "#f28e2b",
    "Monitor": "#8c8c8c",
    "Special-use": "#b55a7a",
}

MAIN_LABEL_SITE_IDS = {"FFX002", "FFX004", "PWC006", "PWC002", "PWC003", "PWC008", "PWC001"}
README_LABEL_SITE_IDS = {"FFX002", "FFX004", "PWC006", "PWC002", "PWC003"}
PWC_CLUSTER_IDS = {"PWC001", "PWC002", "PWC004", "PWC007", "PWC008"}

LABEL_OFFSETS = {
    "FFX002": (12, 12),
    "FFX004": (-82, 18),
    "PWC006": (-84, -12),
    "FFX001": (-84, -14),
    "PWC002": (-92, 14),
    "PWC003": (12, -26),
    "PWC008": (14, -20),
    "PWC001": (-84, 28),
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    return int(round(number)) if number is not None else None


def fmt_int(value: Any) -> str:
    number = safe_int(value)
    return str(number) if number is not None else "-"


def fmt_score(value: Any) -> str:
    number = safe_float(value)
    return f"{number:.1f}" if number is not None else "n/a"


def short_tier(value: Any) -> str:
    text = str(value or "").lower()
    if "tier 1" in text:
        return "Tier 1"
    if "tier 2" in text:
        return "Tier 2"
    if "tier 3" in text:
        return "Tier 3"
    if "high-review" in text:
        return "High-review"
    if "special-use" in text or "low public-priority" in text:
        return "Special-use"
    return str(value or "Unclassified")


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


def marker_size(score: Any, scale: float = 1.0) -> float:
    number = safe_float(score)
    base = 140 if number is None else 85 + number * 7.0
    return base * scale


def review_note(row: pd.Series) -> str:
    site_id = str(row.get("site_id", ""))
    if site_id == "PWC002":
        return "garage / AHJ / electrical review"
    if site_id == "PWC001":
        return "emergency disconnect visibility"
    if site_id == "PWC003":
        return "public-access / special-use decision"
    if site_id == "PWC008":
        return "nearby charging supply already high"
    if str(row.get("electrical_risk_level", "")).lower() == "high":
        return "electrical review before expansion"
    return "verify site assumptions"


def load_site_data(sites_path: Path, executive_path: Path) -> gpd.GeoDataFrame:
    sites = pd.read_csv(sites_path)
    executive = pd.read_csv(executive_path)
    required_sites = {"site_id", "lat", "lon"}
    required_exec = {"model_rank", "site_id", "site_name", "readiness_score", "recommendation_tier"}
    missing_sites = sorted(required_sites - set(sites.columns))
    missing_exec = sorted(required_exec - set(executive.columns))
    if missing_sites:
        raise ValueError(f"Site input is missing required columns: {missing_sites}")
    if missing_exec:
        raise ValueError(f"Executive summary is missing required columns: {missing_exec}")

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
        raise FileNotFoundError(f"Boundary ZIP not found: {boundary_zip}")
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
        raise ValueError("Target county boundaries were not found in the shapefile.")
    return counties


def add_basemap(ax, alpha: float = 0.98, show_attribution: bool = True) -> bool:
    if ctx is None:
        return False
    try:
        attribution = ctx.providers.CartoDB.Positron.attribution if show_attribution else False
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            attribution=attribution,
            attribution_size=6,
            alpha=alpha,
        )
        return True
    except Exception as exc:
        print(f"Basemap skipped: {exc}")
        return False


def lon_formatter(x: float, _pos: int) -> str:
    return f"{x / 6378137.0 * 180.0 / math.pi:.2f}°"


def lat_formatter(y: float, _pos: int) -> str:
    lat = (2.0 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2.0) * 180.0 / math.pi
    return f"{lat:.2f}°"


def set_map_extent(ax, sites_3857: gpd.GeoDataFrame, pad_meters: float = 15000) -> None:
    minx, miny, maxx, maxy = sites_3857.total_bounds
    ax.set_xlim(minx - pad_meters, maxx + pad_meters)
    ax.set_ylim(miny - pad_meters, maxy + pad_meters)


def padded_bounds(layer: gpd.GeoDataFrame, pad_meters: float) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = layer.total_bounds
    return minx - pad_meters, miny - pad_meters, maxx + pad_meters, maxy + pad_meters


def county_label(row: pd.Series) -> str:
    name = str(row.get("NAME", ""))
    if name == "Fairfax":
        return "Fairfax County"
    if name == "Prince William":
        return "Prince William County"
    return name


def plot_county_context(ax, counties_3857: gpd.GeoDataFrame, basemap_added: bool, labels: bool = True) -> None:
    if not basemap_added:
        counties_3857.plot(ax=ax, facecolor="#f7f8fa", edgecolor="#475569", linewidth=1.0, alpha=0.55, zorder=1)
    counties_3857.boundary.plot(ax=ax, color="#0f172a", linewidth=0.95, alpha=0.55, zorder=3)
    if not labels:
        return
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
            alpha=0.66,
            path_effects=[pe.withStroke(linewidth=3.5, foreground="white", alpha=0.86)],
            zorder=2 if basemap_added else 4,
        )


def plot_sites(
    ax,
    sites_3857: gpd.GeoDataFrame,
    size_scale: float = 1.0,
    rank_fontsize: float = 8.7,
    high_risk_halo: bool = True,
) -> None:
    high_risk = sites_3857[sites_3857["electrical_risk_level"].astype(str).str.lower() == "high"]
    if high_risk_halo and not high_risk.empty:
        ax.scatter(
            high_risk.geometry.x,
            high_risk.geometry.y,
            s=[marker_size(score, size_scale) + 170 * size_scale for score in high_risk["readiness_score"]],
            facecolors="none",
            edgecolors="#b91c1c",
            linewidths=2.8,
            alpha=0.72,
            zorder=4,
        )

    for action in ACTION_ORDER:
        subset = sites_3857[sites_3857["action_group"] == action]
        if subset.empty:
            continue
        subset.plot(
            ax=ax,
            markersize=[marker_size(score, size_scale) for score in subset["readiness_score"]],
            color=ACTION_COLORS[action],
            edgecolor=["#7f1d1d" if str(risk).lower() == "high" else "#111827" for risk in subset["electrical_risk_level"]],
            linewidth=[2.2 if str(risk).lower() == "high" else 1.05 for risk in subset["electrical_risk_level"]],
            alpha=0.94,
            zorder=5,
        )
    for _, row in sites_3857.sort_values("model_rank").iterrows():
        ax.text(
            row.geometry.x,
            row.geometry.y,
            fmt_int(row.get("model_rank")),
            ha="center",
            va="center",
            fontsize=rank_fontsize,
            fontweight="bold",
            color="white",
            path_effects=[pe.withStroke(linewidth=2.25, foreground="#111827")],
            zorder=6,
        )


def label_subset(sites_3857: gpd.GeoDataFrame, label_ids: set[str]) -> gpd.GeoDataFrame:
    ranked_sites = sites_3857.sort_values("model_rank")
    top_five = set(ranked_sites.head(5)["site_id"].astype(str))
    high_risk = set(ranked_sites[ranked_sites["electrical_risk_level"].astype(str).str.lower() == "high"]["site_id"].astype(str))
    return ranked_sites[ranked_sites["site_id"].astype(str).isin(top_five | high_risk | label_ids)]


def add_site_labels(
    ax,
    sites_3857: gpd.GeoDataFrame,
    label_ids: set[str],
    fontsize: float = 7.1,
    show_ports: bool = True,
) -> None:
    for _, row in label_subset(sites_3857, label_ids).iterrows():
        site_id = str(row.get("site_id", ""))
        score_text = fmt_score(row.get("readiness_score"))
        if show_ports:
            label = f"#{fmt_int(row.get('model_rank'))} {site_id}\n{score_text} | {fmt_int(row.get('ports_now'))}->{fmt_int(row.get('future_ready_capacity'))} ports"
        else:
            label = f"#{fmt_int(row.get('model_rank'))} {site_id}\n{score_text}"
        dx, dy = LABEL_OFFSETS.get(site_id, (10, 10))
        ax.annotate(
            label,
            xy=(row.geometry.x, row.geometry.y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if dx < 0 else "left",
            va="center",
            fontsize=fontsize,
            color="#111827",
            arrowprops={"arrowstyle": "-", "lw": 0.55, "color": "#334155", "alpha": 0.68},
            bbox={"boxstyle": "round,pad=0.20", "fc": "white", "ec": "#cbd5e1", "alpha": 0.94, "lw": 0.55},
            zorder=7,
        )


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
    start_x = x0 + (x1 - x0) * 0.365
    start_y = y0 + (y1 - y0) * 0.055
    ax.plot([start_x, start_x + length_m], [start_y, start_y], color="#111827", lw=2.2, zorder=8)
    ax.plot([start_x, start_x], [start_y - 700, start_y + 700], color="#111827", lw=1.2, zorder=8)
    ax.plot([start_x + length_m, start_x + length_m], [start_y - 700, start_y + 700], color="#111827", lw=1.2, zorder=8)
    ax.text(start_x + length_m / 2, start_y + 1500, "10 miles", ha="center", va="bottom", fontsize=7.5, color="#111827", zorder=8)


def style_map_axis(ax, compact: bool = False) -> None:
    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lon_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(lat_formatter))
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.18, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("#334155")
    if compact:
        ax.set_xlabel("")
        ax.set_ylabel("")


def ranked(sites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return sites.sort_values("model_rank")


def high_risk_count(sites: gpd.GeoDataFrame) -> int:
    return int((sites["electrical_risk_level"].astype(str).str.lower() == "high").sum())


def action_count(sites: gpd.GeoDataFrame, action: str) -> int:
    return int((sites["action_group"] == action).sum())


def review_watchlist(sites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = ranked(sites)
    return data[
        (data["action_group"].isin(["High-review", "Special-use"]))
        | (data["electrical_risk_level"].astype(str).str.lower() == "high")
    ]


def decision_lines(sites: gpd.GeoDataFrame) -> list[str]:
    data = ranked(sites)
    top = data.iloc[0]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")]
    lines = [
        f"Top overall: #{fmt_int(top.get('model_rank'))} {top.get('site_id')}",
        f"Score {fmt_score(top.get('readiness_score'))} | {fmt_int(top.get('ports_now'))}->{fmt_int(top.get('future_ready_capacity'))} ports",
    ]
    if not pwc.empty:
        top_pwc = pwc.iloc[0]
        lines.extend([
            "",
            f"Top PWC: #{fmt_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')}",
            f"Score {fmt_score(top_pwc.get('readiness_score'))} | {fmt_int(top_pwc.get('ports_now'))}->{fmt_int(top_pwc.get('future_ready_capacity'))} ports",
        ])
    lines.extend(["", "Top 4 action list"])
    for _, row in data.head(4).iterrows():
        lines.append(f"#{fmt_int(row.get('model_rank'))} {row.get('site_id')} | {fmt_score(row.get('readiness_score'))} | {row.get('action_group')}")
    return lines


def review_lines(sites: gpd.GeoDataFrame) -> list[str]:
    watch = review_watchlist(sites)
    if watch.empty:
        return ["No high-review or special-use sites flagged."]
    return [f"{row.get('site_id')} — {review_note(row)}" for _, row in watch.head(6).iterrows()]


def port_lines(sites: gpd.GeoDataFrame, limit: int | None = None) -> list[str]:
    lines = ["Site    Now -> Future"]
    data = ranked(sites)
    if limit is not None:
        data = data.head(limit)
    for _, row in data.iterrows():
        lines.append(f"{row.get('site_id'):<7} {fmt_int(row.get('ports_now')):>2} -> {fmt_int(row.get('future_ready_capacity')):<2}")
    return lines


def draw_info_card(panel_ax, y: float, height: float, title: str, lines: list[str], monospace: bool = False, fontsize: float = 8.0) -> None:
    card = FancyBboxPatch(
        (0.02, y),
        0.96,
        height,
        transform=panel_ax.transAxes,
        boxstyle="round,pad=0.014,rounding_size=0.018",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="white",
        alpha=0.98,
        zorder=1,
    )
    panel_ax.add_patch(card)
    panel_ax.text(0.07, y + height - 0.035, title, transform=panel_ax.transAxes, ha="left", va="top", fontsize=9.0, fontweight="bold", color="#111827", zorder=2)
    panel_ax.text(
        0.07,
        y + height - 0.075,
        "\n".join(lines),
        transform=panel_ax.transAxes,
        ha="left",
        va="top",
        fontsize=fontsize,
        family="monospace" if monospace else None,
        color="#111827",
        linespacing=1.12,
        zorder=2,
    )


def draw_metric_card(panel_ax, sites: gpd.GeoDataFrame, y: float = 0.820, height: float = 0.160) -> None:
    card = FancyBboxPatch(
        (0.02, y),
        0.96,
        height,
        transform=panel_ax.transAxes,
        boxstyle="round,pad=0.014,rounding_size=0.018",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="white",
        alpha=0.98,
        zorder=1,
    )
    panel_ax.add_patch(card)
    panel_ax.text(0.07, y + height - 0.035, "Key metrics", transform=panel_ax.transAxes, ha="left", va="top", fontsize=9.0, fontweight="bold", color="#111827", zorder=2)

    metrics = [
        ("Sites", len(sites)),
        ("Advance", action_count(sites, "Advance")),
        ("Review", action_count(sites, "High-review")),
        ("High risk", high_risk_count(sites)),
    ]
    box_y = y + 0.030
    box_w = 0.205
    gap = 0.025
    for index, (label, value) in enumerate(metrics):
        box_x = 0.07 + index * (box_w + gap)
        pill = FancyBboxPatch(
            (box_x, box_y),
            box_w,
            0.070,
            transform=panel_ax.transAxes,
            boxstyle="round,pad=0.010,rounding_size=0.012",
            linewidth=0.7,
            edgecolor="#d0d7de",
            facecolor="#f8fafc",
            zorder=2,
        )
        panel_ax.add_patch(pill)
        panel_ax.text(box_x + box_w / 2, box_y + 0.046, str(value), transform=panel_ax.transAxes, ha="center", va="center", fontsize=11.5, fontweight="bold", color="#111827", zorder=3)
        panel_ax.text(box_x + box_w / 2, box_y + 0.018, label, transform=panel_ax.transAxes, ha="center", va="center", fontsize=6.6, color="#475569", zorder=3)


def draw_encoding_card(panel_ax, y: float = 0.020, height: float = 0.170) -> None:
    card = FancyBboxPatch(
        (0.02, y),
        0.96,
        height,
        transform=panel_ax.transAxes,
        boxstyle="round,pad=0.014,rounding_size=0.018",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="white",
        alpha=0.98,
        zorder=1,
    )
    panel_ax.add_patch(card)
    panel_ax.text(0.07, y + height - 0.034, "Map encoding", transform=panel_ax.transAxes, ha="left", va="top", fontsize=9.0, fontweight="bold", color="#111827", zorder=2)

    items = [
        ("Advance", ACTION_COLORS["Advance"], "filled"),
        ("Promising", ACTION_COLORS["Promising"], "filled"),
        ("High-review", ACTION_COLORS["High-review"], "filled"),
        ("Monitor", ACTION_COLORS["Monitor"], "filled"),
        ("Special-use", ACTION_COLORS["Special-use"], "filled"),
        ("High electrical risk", "#b91c1c", "halo"),
        ("Number = model rank", "#4c78a8", "number"),
    ]
    x_left = 0.09
    x_right = 0.52
    start_y = y + height - 0.076
    row_gap = 0.028
    for idx, (label, color, mode) in enumerate(items):
        col_x = x_left if idx < 4 else x_right
        row_y = start_y - (idx if idx < 4 else idx - 4) * row_gap
        if mode == "halo":
            panel_ax.scatter([col_x], [row_y], transform=panel_ax.transAxes, s=54, facecolors="none", edgecolors=color, linewidths=1.9, zorder=3)
        elif mode == "number":
            panel_ax.scatter([col_x], [row_y], transform=panel_ax.transAxes, s=54, color=color, edgecolors="#111827", linewidths=0.7, zorder=3)
            panel_ax.text(col_x, row_y, "1", transform=panel_ax.transAxes, ha="center", va="center", fontsize=6.0, fontweight="bold", color="white", zorder=4)
        else:
            panel_ax.scatter([col_x], [row_y], transform=panel_ax.transAxes, s=54, color=color, edgecolors="#111827", linewidths=0.7, zorder=3)
        panel_ax.text(col_x + 0.030, row_y, label, transform=panel_ax.transAxes, ha="left", va="center", fontsize=6.9, color="#111827", zorder=3)


def draw_dashboard_panel(panel_ax, sites: gpd.GeoDataFrame) -> None:
    panel_ax.set_axis_off()
    draw_metric_card(panel_ax, sites, 0.815, 0.165)
    draw_info_card(panel_ax, 0.625, 0.165, "Top decisions", decision_lines(sites), fontsize=6.95)
    draw_info_card(panel_ax, 0.505, 0.105, "Review watchlist", review_lines(sites), fontsize=7.0)
    draw_info_card(panel_ax, 0.205, 0.275, "Port plan snapshot", port_lines(sites), monospace=True, fontsize=6.35)
    draw_encoding_card(panel_ax, 0.020, 0.160)


def add_pwc_focus_circle(ax, cluster: gpd.GeoDataFrame, pad_meters: float = 4200) -> tuple[float, float, float]:
    minx, miny, maxx, maxy = padded_bounds(cluster, pad_meters)
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    radius = max(maxx - minx, maxy - miny) * 0.58
    focus_circle = Circle(
        (center_x, center_y),
        radius,
        fill=False,
        linewidth=1.25,
        linestyle="--",
        edgecolor="#475569",
        alpha=0.78,
        zorder=4,
    )
    ax.add_patch(focus_circle)
    return center_x, center_y, radius


def apply_circular_inset_clip(inset_ax):
    clip_circle = Circle((0.5, 0.5), 0.495, transform=inset_ax.transAxes)
    artists = []
    artists.extend(list(inset_ax.collections))
    artists.extend(list(inset_ax.images))
    artists.extend(list(inset_ax.lines))
    artists.extend([patch for patch in inset_ax.patches if patch is not clip_circle])
    for artist in artists:
        try:
            artist.set_clip_path(clip_circle)
        except Exception:
            pass

    inset_ax.set_facecolor("none")
    for spine in inset_ax.spines.values():
        spine.set_visible(False)
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])

    frame_circle = Circle(
        (0.5, 0.5),
        0.495,
        transform=inset_ax.transAxes,
        fill=False,
        edgecolor="#334155",
        linewidth=1.45,
        zorder=20,
        clip_on=False,
    )
    frame_circle.set_path_effects([
        pe.withSimplePatchShadow(offset=(2, -2), alpha=0.18),
        pe.Normal(),
    ])
    inset_ax.add_patch(frame_circle)
    return frame_circle


def draw_pwc_zoom_inset(parent_ax, sites_3857: gpd.GeoDataFrame, counties_3857: gpd.GeoDataFrame, include_labels: bool = True) -> None:
    cluster = sites_3857[sites_3857["site_id"].astype(str).isin(PWC_CLUSTER_IDS)].copy()
    if cluster.empty:
        return

    center_x, center_y, radius = add_pwc_focus_circle(parent_ax, cluster, pad_meters=4200)
    minx, miny, maxx, maxy = padded_bounds(cluster, 4200)

    inset_ax = parent_ax.inset_axes([0.045, 0.650, 0.275, 0.275])
    inset_ax.set_xlim(minx, maxx)
    inset_ax.set_ylim(miny, maxy)

    add_basemap(inset_ax, alpha=0.94, show_attribution=False)
    counties_3857.boundary.plot(ax=inset_ax, color="#0f172a", linewidth=0.65, alpha=0.42, zorder=3)
    plot_sites(inset_ax, cluster, size_scale=0.60, rank_fontsize=6.7, high_risk_halo=True)
    if include_labels:
        add_site_labels(inset_ax, cluster, {"PWC002", "PWC008"}, fontsize=5.5, show_ports=False)
    apply_circular_inset_clip(inset_ax)

    parent_ax.text(
        0.182,
        0.947,
        "Zoom: PWC cluster",
        transform=parent_ax.transAxes,
        ha="center",
        va="center",
        fontsize=7.2,
        color="#111827",
        bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "#cbd5e1", "alpha": 0.95, "lw": 0.7},
        zorder=25,
    )

    connector = ConnectionPatch(
        xyA=(center_x + radius * 0.70, center_y + radius * 0.12),
        coordsA=parent_ax.transData,
        xyB=(0.86, 0.24),
        coordsB=inset_ax.transAxes,
        color="#64748b",
        linewidth=0.9,
        alpha=0.75,
        zorder=9,
    )
    parent_ax.add_artist(connector)


def draw_readme_panel(panel_ax, sites: gpd.GeoDataFrame) -> None:
    panel_ax.set_axis_off()
    data = ranked(sites)
    top = data.iloc[0]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")]
    top_pwc = pwc.iloc[0] if not pwc.empty else None

    lines = [
        "Top decisions",
        "",
        f"#{fmt_int(top.get('model_rank'))} {top.get('site_id')} — top overall",
        f"{fmt_score(top.get('readiness_score'))} | {fmt_int(top.get('ports_now'))}->{fmt_int(top.get('future_ready_capacity'))} ports",
    ]
    if top_pwc is not None:
        lines.extend([
            "",
            f"#{fmt_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')} — top PWC",
            f"{fmt_score(top_pwc.get('readiness_score'))} | {fmt_int(top_pwc.get('ports_now'))}->{fmt_int(top_pwc.get('future_ready_capacity'))} ports",
        ])
    lines.extend(["", "Review flags"])
    for _, row in review_watchlist(sites).head(3).iterrows():
        lines.append(f"{row.get('site_id')} — {review_note(row)}")

    card = FancyBboxPatch(
        (0.03, 0.50),
        0.94,
        0.46,
        transform=panel_ax.transAxes,
        boxstyle="round,pad=0.016,rounding_size=0.020",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="white",
        alpha=0.98,
        zorder=1,
    )
    panel_ax.add_patch(card)
    panel_ax.text(0.09, 0.93, "\n".join(lines), transform=panel_ax.transAxes, ha="left", va="top", fontsize=8.3, color="#111827", linespacing=1.18, zorder=2)

    draw_encoding_card(panel_ax, y=0.07, height=0.34)


def plot_map_core(
    ax,
    sites_3857: gpd.GeoDataFrame,
    counties_3857: gpd.GeoDataFrame,
    label_ids: set[str],
    include_inset: bool,
    compact: bool = False,
) -> bool:
    ax.set_facecolor("#eef2f7")
    set_map_extent(ax, sites_3857, pad_meters=14500 if compact else 15000)
    basemap_added = add_basemap(ax, show_attribution=True)
    plot_county_context(ax, counties_3857, basemap_added, labels=not compact)
    plot_sites(ax, sites_3857, size_scale=1.05 if compact else 1.0, rank_fontsize=8.5 if compact else 8.7)
    add_site_labels(ax, sites_3857, label_ids, fontsize=6.7 if compact else 7.1, show_ports=not compact)
    if include_inset:
        draw_pwc_zoom_inset(ax, sites_3857, counties_3857, include_labels=not compact)
    add_north_arrow(ax)
    add_scale_bar(ax)
    style_map_axis(ax, compact=compact)
    return basemap_added


def plot_gis_decision_map_report(sites: gpd.GeoDataFrame, counties: gpd.GeoDataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    sites_3857 = sites.to_crs(WEB_MERCATOR)
    counties_3857 = counties.to_crs(WEB_MERCATOR)

    fig = plt.figure(figsize=(17.4, 10.3), facecolor="white")
    ax = fig.add_axes([0.045, 0.115, 0.695, 0.765])
    panel_ax = fig.add_axes([0.758, 0.115, 0.222, 0.765])

    basemap_added = plot_map_core(ax, sites_3857, counties_3857, MAIN_LABEL_SITE_IDS, include_inset=True, compact=False)
    draw_dashboard_panel(panel_ax, sites)

    subtitle = "Official boundaries, basemap context, ranked candidates, circular PWC zoom lens, action categories, and port-sizing notes."
    if not basemap_added:
        subtitle = "Official county boundaries and ranked candidate sites; basemap skipped or unavailable."

    fig.suptitle("V2 EV Charging Candidate Sites — GIS Decision Map", fontsize=14.6, fontweight="bold", y=0.967)
    fig.text(0.5, 0.922, subtitle, ha="center", fontsize=9.2, color="#111827")
    fig.text(0.5, 0.025, "Planning screen only — not an engineering, utility, permitting, procurement, or construction approval.", ha="center", fontsize=8.4, color="#475569")
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_gis_decision_map_readme(sites: gpd.GeoDataFrame, counties: gpd.GeoDataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    sites_3857 = sites.to_crs(WEB_MERCATOR)
    counties_3857 = counties.to_crs(WEB_MERCATOR)

    fig = plt.figure(figsize=(14.6, 8.0), facecolor="white")
    ax = fig.add_axes([0.045, 0.130, 0.690, 0.760])
    panel_ax = fig.add_axes([0.758, 0.155, 0.220, 0.695])

    basemap_added = plot_map_core(ax, sites_3857, counties_3857, README_LABEL_SITE_IDS, include_inset=True, compact=True)
    draw_readme_panel(panel_ax, sites)

    subtitle = "Ranked public charging candidates with action categories, review flags, and circular PWC zoom lens."
    if not basemap_added:
        subtitle = "Ranked public charging candidates; basemap skipped or unavailable."

    fig.suptitle("V2 EV Charging Candidate Sites", fontsize=14.0, fontweight="bold", y=0.968)
    fig.text(0.5, 0.925, subtitle, ha="center", fontsize=8.8, color="#111827")
    fig.text(0.5, 0.030, "Planning screen only — not design, permitting, utility approval, procurement, or construction direction.", ha="center", fontsize=7.8, color="#475569")
    fig.savefig(output_path, dpi=210, bbox_inches="tight")
    plt.close(fig)


def refresh_package_manifest_hashes(manifest_path: Path, synced_pairs: list[tuple[Path, Path]] | None = None) -> None:
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    files = manifest.get("files", [])
    existing_destinations = {Path(str(record.get("destination", ""))).as_posix() for record in files}
    for source, destination in synced_pairs or []:
        destination_text = destination.as_posix()
        if destination_text not in existing_destinations:
            files.append({
                "source": source.as_posix(),
                "destination": destination_text,
                "copied": False,
                "size_bytes": 0,
                "source_sha256": None,
                "destination_sha256": None,
                "in_sync": False,
            })
            existing_destinations.add(destination_text)

    for record in files:
        source = Path(str(record.get("source", "")))
        destination = Path(str(record.get("destination", "")))
        if not source.exists() or not destination.exists() or source.stat().st_size == 0 or destination.stat().st_size == 0:
            record["copied"] = False
            record["size_bytes"] = 0
            record["source_sha256"] = None
            record["destination_sha256"] = None
            record["in_sync"] = False
            continue
        source_hash = sha256_file(source)
        destination_hash = sha256_file(destination)
        record["copied"] = True
        record["size_bytes"] = destination.stat().st_size
        record["source_sha256"] = source_hash
        record["destination_sha256"] = destination_hash
        record["in_sync"] = source_hash == destination_hash

    manifest["expected_count"] = len(files)
    manifest["copied_count"] = len([record for record in files if record.get("copied")])
    manifest["synced_count"] = len([record for record in files if record.get("copied") and record.get("in_sync")])
    manifest["missing_or_empty_sources"] = [record.get("source") for record in files if not record.get("copied")]
    manifest["out_of_sync_destinations"] = [record.get("destination") for record in files if record.get("copied") and not record.get("in_sync")]
    manifest["status"] = "complete" if not manifest["missing_or_empty_sources"] and not manifest["out_of_sync_destinations"] else "incomplete"
    manifest["files"] = files
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def sync_generated_maps(
    report_output: Path,
    readme_output: Path,
    docs_readme_output: Path,
    package_report_chart: Path,
    package_readme_chart: Path,
    sync_package: bool = True,
    sync_docs: bool = True,
) -> dict[str, bool]:
    status = {
        "docs_readme": False,
        "package_report": False,
        "package_readme": False,
    }
    if sync_docs:
        ensure_parent(docs_readme_output)
        shutil.copy2(readme_output, docs_readme_output)
        status["docs_readme"] = True

    if sync_package:
        package_root = package_report_chart.parents[1]
        if package_root.exists():
            ensure_parent(package_report_chart)
            ensure_parent(package_readme_chart)
            shutil.copy2(report_output, package_report_chart)
            shutil.copy2(readme_output, package_readme_chart)
            refresh_package_manifest_hashes(
                package_root / "package_manifest.json",
                [(report_output, package_report_chart), (readme_output, package_readme_chart)],
            )
            status["package_report"] = True
            status["package_readme"] = True
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create GIS-based V2 EV charging decision maps.")
    parser.add_argument("--sites", default=DEFAULT_SITES, help="V2 candidate-site input CSV with lat/lon.")
    parser.add_argument("--input", default=DEFAULT_EXECUTIVE_SUMMARY, help="V2 executive summary CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Full report map PNG path.")
    parser.add_argument("--readme-output", default=DEFAULT_README_OUTPUT, help="README-optimized map PNG path.")
    parser.add_argument("--docs-readme-output", default=DEFAULT_DOCS_README_OUTPUT, help="Committed README asset copy path.")
    parser.add_argument("--boundary-zip", default=DEFAULT_BOUNDARY_ZIP, help="Local Census county shapefile ZIP path.")
    parser.add_argument("--boundary-url", default=DEFAULT_BOUNDARY_URL, help="Boundary ZIP URL used when local file is missing.")
    parser.add_argument("--package-chart", default=DEFAULT_PACKAGE_CHART, help="Deliverable-package report-map copy.")
    parser.add_argument("--package-readme-chart", default=DEFAULT_PACKAGE_README_CHART, help="Deliverable-package README-map copy.")
    parser.add_argument("--no-download-boundary", action="store_true", help="Do not download boundary shapefile automatically.")
    parser.add_argument("--no-sync-package", action="store_true", help="Do not sync regenerated charts into an existing deliverable package.")
    parser.add_argument("--no-sync-docs", action="store_true", help="Do not refresh the README asset under docs/assets.")
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
    readme_output_path = Path(args.readme_output)
    docs_readme_output_path = Path(args.docs_readme_output)
    boundary_zip = Path(args.boundary_zip)
    package_chart = Path(args.package_chart)
    package_readme_chart = Path(args.package_readme_chart)

    sites = load_site_data(sites_path, executive_path)
    download_boundary_if_needed(boundary_zip, args.boundary_url, args.no_download_boundary)
    counties = load_county_boundaries(boundary_zip)

    plot_gis_decision_map_report(sites, counties, output_path)
    plot_gis_decision_map_readme(sites, counties, readme_output_path)
    sync_status = sync_generated_maps(
        output_path,
        readme_output_path,
        docs_readme_output_path,
        package_chart,
        package_readme_chart,
        sync_package=not args.no_sync_package,
        sync_docs=not args.no_sync_docs,
    )

    print("V2 GIS DECISION MAPS")
    print("--------------------")
    print(f"Sites: {sites_path}")
    print(f"Executive summary: {executive_path}")
    print(f"Boundary ZIP: {boundary_zip}")
    print(f"Report output: {output_path}")
    print(f"README output: {readme_output_path}")
    print(f"Docs README asset: {'updated' if sync_status['docs_readme'] else 'not updated'}")
    print(f"Package report map: {'updated' if sync_status['package_report'] else 'not needed / package not built yet'}")
    print(f"Package README map: {'updated' if sync_status['package_readme'] else 'not needed / package not built yet'}")
    print(f"Sites plotted: {len(sites)}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"GIS decision maps failed: {exc}", file=sys.stderr)
        raise
