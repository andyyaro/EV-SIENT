"""Create a GIS-based V2 EV charging site decision map.

This is the presentation GIS map. It uses GeoPandas with official Census county
boundaries and, when available, a light Contextily basemap.
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
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter
import pandas as pd

try:
    import geopandas as gpd
except ImportError as exc:
    raise SystemExit("GeoPandas is required. Install optional GIS dependencies with: pip install -r requirements-gis.txt") from exc

try:
    import contextily as ctx
except ImportError:
    ctx = None

DEFAULT_SITES = "data/inputs/real_sites_v2.csv"
DEFAULT_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_OUTPUT = "data/outputs/charts/v2_site_decision_map.png"
DEFAULT_BOUNDARY_ZIP = "data/source_extracts/gis/tl_2024_us_county.zip"
DEFAULT_BOUNDARY_URL = "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"
DEFAULT_PACKAGE_CHART = "data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png"
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
LABEL_SITE_IDS = {"FFX002", "FFX004", "PWC006", "PWC002", "PWC003", "PWC008", "PWC001"}
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


def marker_size(score: Any) -> float:
    number = safe_float(score)
    return 140 if number is None else 85 + number * 7.0


def review_note(row: pd.Series) -> str:
    """Return short, complete review notes without ellipses."""
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
    return gpd.GeoDataFrame(merged, geometry=gpd.points_from_xy(merged["lon"], merged["lat"]), crs=WGS84)


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


def add_basemap(ax) -> bool:
    if ctx is None:
        return False
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, attribution_size=6, alpha=0.98)
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


def county_label(row: pd.Series) -> str:
    name = str(row.get("NAME", ""))
    if name == "Fairfax":
        return "Fairfax County"
    if name == "Prince William":
        return "Prince William County"
    return name


def plot_county_context(ax, counties_3857: gpd.GeoDataFrame, basemap_added: bool) -> None:
    if not basemap_added:
        counties_3857.plot(ax=ax, facecolor="#f7f8fa", edgecolor="#475569", linewidth=1.0, alpha=0.55, zorder=1)
    counties_3857.boundary.plot(ax=ax, color="#0f172a", linewidth=0.95, alpha=0.55, zorder=3)
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


def plot_sites(ax, sites_3857: gpd.GeoDataFrame) -> None:
    high_risk = sites_3857[sites_3857["electrical_risk_level"].astype(str).str.lower() == "high"]
    if not high_risk.empty:
        ax.scatter(
            high_risk.geometry.x,
            high_risk.geometry.y,
            s=[marker_size(score) + 170 for score in high_risk["readiness_score"]],
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
            markersize=[marker_size(score) for score in subset["readiness_score"]],
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
            fontsize=8.7,
            fontweight="bold",
            color="white",
            path_effects=[pe.withStroke(linewidth=2.25, foreground="#111827")],
            zorder=6,
        )


def label_subset(sites_3857: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ranked_sites = sites_3857.sort_values("model_rank")
    top_five = set(ranked_sites.head(5)["site_id"].astype(str))
    high_risk = set(ranked_sites[ranked_sites["electrical_risk_level"].astype(str).str.lower() == "high"]["site_id"].astype(str))
    return ranked_sites[ranked_sites["site_id"].astype(str).isin(top_five | high_risk | LABEL_SITE_IDS)]


def add_site_labels(ax, sites_3857: gpd.GeoDataFrame) -> None:
    for _, row in label_subset(sites_3857).iterrows():
        site_id = str(row.get("site_id", ""))
        score = safe_float(row.get("readiness_score"))
        score_text = f"{score:.1f}" if score is not None else "n/a"
        label = f"#{fmt_int(row.get('model_rank'))} {site_id}\n{score_text} | {fmt_int(row.get('ports_now'))}->{fmt_int(row.get('future_ready_capacity'))} ports"
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


def style_map_axis(ax) -> None:
    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lon_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(lat_formatter))
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.18, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("#334155")


def ranked(sites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return sites.sort_values("model_rank")


def decision_lines(sites: gpd.GeoDataFrame) -> list[str]:
    data = ranked(sites)
    top = data.iloc[0]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")]
    lines = [
        f"Top overall: #{fmt_int(top.get('model_rank'))} {top.get('site_id')}",
        f"Score {safe_float(top.get('readiness_score')):.1f} | {fmt_int(top.get('ports_now'))}->{fmt_int(top.get('future_ready_capacity'))} ports",
    ]
    if not pwc.empty:
        top_pwc = pwc.iloc[0]
        lines.extend(["", f"Top PWC: #{fmt_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')}", f"Score {safe_float(top_pwc.get('readiness_score')):.1f} | {fmt_int(top_pwc.get('ports_now'))}->{fmt_int(top_pwc.get('future_ready_capacity'))} ports"])
    lines.extend(["", "Top 5 action list"])
    for _, row in data.head(5).iterrows():
        lines.append(f"#{fmt_int(row.get('model_rank'))} {row.get('site_id')} | {safe_float(row.get('readiness_score')):.1f} | {row.get('action_group')}")
    return lines


def review_lines(sites: gpd.GeoDataFrame) -> list[str]:
    data = ranked(sites)
    watch = data[(data["action_group"].isin(["High-review", "Special-use"])) | (data["electrical_risk_level"].astype(str).str.lower() == "high")]
    if watch.empty:
        return ["No high-review or special-use sites flagged."]
    return [f"{row.get('site_id')} — {review_note(row)}" for _, row in watch.head(6).iterrows()]


def port_lines(sites: gpd.GeoDataFrame) -> list[str]:
    lines = ["Site    Now -> Future"]
    for _, row in ranked(sites).iterrows():
        lines.append(f"{row.get('site_id'):<7} {fmt_int(row.get('ports_now')):>2} -> {fmt_int(row.get('future_ready_capacity')):<2}")
    return lines


def encoding_lines() -> list[str]:
    return [
        "Green = advance | Blue = promising",
        "Orange = high-review | Gray = monitor",
        "Pink = special-use",
        "Red halo = high electrical risk",
        "Number = model rank",
    ]


def draw_info_card(panel_ax, y: float, height: float, title: str, lines: list[str], monospace: bool = False, fontsize: float = 8.0) -> None:
    card = FancyBboxPatch((0.02, y), 0.96, height, transform=panel_ax.transAxes, boxstyle="round,pad=0.014,rounding_size=0.018", linewidth=1.0, edgecolor="#cbd5e1", facecolor="white", alpha=0.98, zorder=1)
    panel_ax.add_patch(card)
    panel_ax.text(0.07, y + height - 0.035, title, transform=panel_ax.transAxes, ha="left", va="top", fontsize=9.0, fontweight="bold", color="#111827", zorder=2)
    panel_ax.text(0.07, y + height - 0.075, "\n".join(lines), transform=panel_ax.transAxes, ha="left", va="top", fontsize=fontsize, family="monospace" if monospace else None, color="#111827", linespacing=1.15, zorder=2)


def draw_side_panel(panel_ax, sites: gpd.GeoDataFrame) -> None:
    panel_ax.set_axis_off()
    draw_info_card(panel_ax, 0.722, 0.258, "Top decisions", decision_lines(sites), fontsize=7.55)
    draw_info_card(panel_ax, 0.548, 0.154, "Review watchlist", review_lines(sites), fontsize=7.35)
    draw_info_card(panel_ax, 0.215, 0.313, "Port plan snapshot", port_lines(sites), monospace=True, fontsize=6.65)
    draw_info_card(panel_ax, 0.020, 0.175, "Map encoding", encoding_lines(), fontsize=7.05)


def refresh_package_manifest_hashes(manifest_path: Path) -> None:
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    files = manifest.get("files", [])
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

    manifest["copied_count"] = len([record for record in files if record.get("copied")])
    manifest["synced_count"] = len([record for record in files if record.get("copied") and record.get("in_sync")])
    manifest["missing_or_empty_sources"] = [record.get("source") for record in files if not record.get("copied")]
    manifest["out_of_sync_destinations"] = [record.get("destination") for record in files if record.get("copied") and not record.get("in_sync")]
    manifest["status"] = "complete" if not manifest["missing_or_empty_sources"] and not manifest["out_of_sync_destinations"] else "incomplete"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def sync_chart_to_package(output_path: Path, package_chart: Path) -> bool:
    """Keep the deliverable-package chart copy current when the map is regenerated directly."""
    package_root = package_chart.parents[1]
    if not package_root.exists():
        return False
    ensure_parent(package_chart)
    shutil.copy2(output_path, package_chart)
    refresh_package_manifest_hashes(package_root / "package_manifest.json")
    return True


def plot_gis_decision_map(sites: gpd.GeoDataFrame, counties: gpd.GeoDataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    sites_3857 = sites.to_crs(WEB_MERCATOR)
    counties_3857 = counties.to_crs(WEB_MERCATOR)

    fig = plt.figure(figsize=(16.8, 10.2), facecolor="white")
    ax = fig.add_axes([0.045, 0.115, 0.700, 0.765])
    panel_ax = fig.add_axes([0.765, 0.115, 0.205, 0.765])
    ax.set_facecolor("#eef2f7")

    set_map_extent(ax, sites_3857)
    basemap_added = add_basemap(ax)
    plot_county_context(ax, counties_3857, basemap_added)
    plot_sites(ax, sites_3857)
    add_site_labels(ax, sites_3857)
    add_north_arrow(ax)
    add_scale_bar(ax)
    draw_side_panel(panel_ax, sites)
    style_map_axis(ax)

    subtitle = "Official boundaries, basemap context, ranked candidates, action categories, and port-sizing notes."
    if not basemap_added:
        subtitle = "Official county boundaries and ranked candidate sites; basemap skipped or unavailable."

    fig.suptitle("V2 EV Charging Candidate Sites — GIS Decision Map", fontsize=14.6, fontweight="bold", y=0.967)
    fig.text(0.5, 0.922, subtitle, ha="center", fontsize=9.2, color="#111827")
    fig.text(0.5, 0.025, "Planning screen only — not an engineering, utility, permitting, procurement, or construction approval.", ha="center", fontsize=8.4, color="#475569")
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a GIS-based V2 EV charging decision map.")
    parser.add_argument("--sites", default=DEFAULT_SITES, help="V2 candidate-site input CSV with lat/lon.")
    parser.add_argument("--input", default=DEFAULT_EXECUTIVE_SUMMARY, help="V2 executive summary CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    parser.add_argument("--boundary-zip", default=DEFAULT_BOUNDARY_ZIP, help="Local Census county shapefile ZIP path.")
    parser.add_argument("--boundary-url", default=DEFAULT_BOUNDARY_URL, help="Boundary ZIP URL used when local file is missing.")
    parser.add_argument("--package-chart", default=DEFAULT_PACKAGE_CHART, help="Deliverable-package copy to sync when package already exists.")
    parser.add_argument("--no-download-boundary", action="store_true", help="Do not download boundary shapefile automatically.")
    parser.add_argument("--no-sync-package", action="store_true", help="Do not sync the regenerated chart into an existing deliverable package.")
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
    package_chart = Path(args.package_chart)

    sites = load_site_data(sites_path, executive_path)
    download_boundary_if_needed(boundary_zip, args.boundary_url, args.no_download_boundary)
    counties = load_county_boundaries(boundary_zip)
    plot_gis_decision_map(sites, counties, output_path)
    package_synced = False if args.no_sync_package else sync_chart_to_package(output_path, package_chart)

    print("V2 GIS DECISION MAP")
    print("-------------------")
    print(f"Sites: {sites_path}")
    print(f"Executive summary: {executive_path}")
    print(f"Boundary ZIP: {boundary_zip}")
    print(f"Output: {output_path}")
    print(f"Sites plotted: {len(sites)}")
    print(f"Package chart sync: {'updated' if package_synced else 'not needed / package not built yet'}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"GIS decision map failed: {exc}", file=sys.stderr)
        raise
