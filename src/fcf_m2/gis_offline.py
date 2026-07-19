"""Offline-reproducible site map (PY-06).

Uses the cached Virginia county boundary GeoJSON shipped in-repo
(data/cache/boundaries/tl_2024_va_counties.geojson, US Census TIGER/Line 2024,
attribution in ATTRIBUTION.md). No network access is ever required:

- with geopandas installed: boundary + site map, no basemap tiles (offline mode);
- without geopandas: pure-matplotlib fallback (sites + boundary outlines read
  via the json module).

Run with FCF_OFFLINE=1 to assert that no network call is attempted (the module
performs none in any path; the env var simply records the intent in the footer).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from . import visuals

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "data/cache/boundaries/tl_2024_va_counties.geojson"


def _plot_boundary_pure(ax) -> None:
    data = json.loads(BOUNDARY.read_text())
    for feat in data["features"]:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                ax.plot(xs, ys, color=visuals.MID_GREEN, linewidth=0.4, alpha=0.6)


def build_site_map(sites: pd.DataFrame, out_path: str | Path,
                   title: str = "Candidate Site Readiness Map") -> Path:
    """Offline site map: cached boundaries + scored sites."""
    fig, ax = plt.subplots(figsize=(9, 7))
    visuals.style_axes(ax)

    try:
        import geopandas as gpd  # optional
        gdf = gpd.read_file(BOUNDARY)
        gdf.boundary.plot(ax=ax, color=visuals.MID_GREEN, linewidth=0.4, alpha=0.6)
    except ImportError:
        _plot_boundary_pure(ax)

    top3 = set(sites.nsmallest(3, "model_rank")["site_id"]) if "model_rank" in sites else set()
    for _, s in sites.iterrows():
        is_top = s["site_id"] in top3
        ax.scatter(s["lon"], s["lat"],
                   s=140 if is_top else 60,
                   color=visuals.DARK_GREEN if is_top else visuals.ACCENT,
                   edgecolors=visuals.BLACK, linewidths=0.5, zorder=5)
        ax.annotate(s["site_id"], (s["lon"], s["lat"]), textcoords="offset points",
                    xytext=(6, 4), fontsize=7, color=visuals.BLACK)

    pad = 0.15
    ax.set_xlim(sites["lon"].min() - pad, sites["lon"].max() + pad)
    ax.set_ylim(sites["lat"].min() - pad, sites["lat"].max() + pad)
    ax.set_title(title, color=visuals.BLACK, fontsize=13)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    mode = "offline (FCF_OFFLINE set)" if os.environ.get("FCF_OFFLINE") else "offline-capable (cached boundaries)"
    visuals.footer(fig,
                   source="US Census TIGER/Line 2024 (cached in repo) + real_sites_v2.csv",
                   source_date="TIGER 2024 / sites 2026-06-24",
                   scenario=f"site map, {mode}",
                   assumption="no basemap tiles in offline mode")
    return visuals.save(fig, out_path)
