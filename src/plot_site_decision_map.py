"""Create a V2 EV charging decision map.

This figure is designed to be more presentation-oriented than the detailed
readiness map. It combines geography, rank, readiness score, action category,
right-sizing, electrical risk, and validation notes into one decision graphic.

Run from the repository root after the V2 workflow has generated model outputs:

    python src/plot_site_decision_map.py \
      --input data/inputs/real_sites_v2.csv \
      --results data/outputs/v2_site_results.csv \
      --electrical-summary data/outputs/v2_electrical_risk_summary.csv \
      --right-sizing data/outputs/v2_right_sizing_scenarios.csv \
      --right-sizing-validation data/outputs/v2_right_sizing_validation.csv \
      --output data/outputs/charts/v2_site_decision_map.png
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from textwrap import shorten

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v2.csv"
DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_RIGHT_SIZING_VALIDATION = "data/outputs/v2_right_sizing_validation.csv"
DEFAULT_OUTPUT = "data/outputs/charts/v2_site_decision_map.png"

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Advance",
    "Tier 2 — promising candidate, refine data": "Promising",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Monitor",
    "Low public-priority / special-use": "Special-use",
}

TIER_MARKERS = {
    "Advance": "o",
    "Promising": "^",
    "High-review": "s",
    "Monitor": "D",
    "Special-use": "X",
}

TIER_ORDER = ["Advance", "Promising", "High-review", "Monitor", "Special-use"]

CALLOUT_OFFSETS = {
    "FFX001": (-72, -12),
    "FFX002": (16, -2),
    "FFX003": (12, -14),
    "FFX004": (-66, 18),
    "PWC001": (-66, 26),
    "PWC002": (-72, 14),
    "PWC003": (12, -22),
    "PWC004": (12, 22),
    "PWC005": (10, 16),
    "PWC006": (-58, -8),
    "PWC007": (12, -20),
    "PWC008": (12, -18),
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required file not found: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def safe_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def safe_int(value) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    return int(round(number))


def compact_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


def load_decision_data(
    input_path: Path,
    results_path: Path,
    electrical_path: Path,
    right_sizing_path: Path,
    validation_path: Path,
) -> pd.DataFrame:
    """Load and merge the V2 output layers used by the decision map."""
    sites = read_csv(input_path)
    required_site_cols = {"site_id", "site_name", "lat", "lon"}
    missing_site_cols = required_site_cols - set(sites.columns)
    if missing_site_cols:
        raise ValueError(f"Input file is missing required columns: {sorted(missing_site_cols)}")

    results = read_csv(results_path)
    electrical = read_csv(electrical_path)
    right_sizing = read_csv(right_sizing_path)
    validation = read_csv(validation_path)

    result_cols = [
        col for col in [
            "site_id", "model_rank", "readiness_score", "recommendation_tier",
            "action_label", "review_reason", "data_confidence_level",
        ] if col in results.columns
    ]
    electrical_cols = [
        col for col in ["site_id", "electrical_risk_level", "expected_rank", "expected_score"]
        if col in electrical.columns
    ]
    sizing_cols = [
        col for col in [
            "site_id", "ports_now", "ports_2035_base", "ports_2035_high",
            "ports_2050_base", "ports_2050_high", "future_ready_capacity",
            "expansion_strategy",
        ] if col in right_sizing.columns
    ]
    validation_cols = [
        col for col in [
            "site_id", "current_alignment", "future_alignment",
            "simulation_supported_strategy", "right_sizing_validation_note",
        ] if col in validation.columns
    ]

    data = sites.merge(results[result_cols], on="site_id", how="left")
    data = data.merge(electrical[electrical_cols], on="site_id", how="left")
    data = data.merge(right_sizing[sizing_cols], on="site_id", how="left")
    data = data.merge(validation[validation_cols], on="site_id", how="left")

    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data["model_rank_num"] = pd.to_numeric(data.get("model_rank", ""), errors="coerce")
    data["readiness_score_num"] = pd.to_numeric(data.get("readiness_score", ""), errors="coerce")
    data["tier_short"] = data.get("recommendation_tier", "").apply(compact_tier)
    data["locality_group"] = data["site_id"].astype(str).str.extract(r"^(FFX|PWC)", expand=False).fillna("Other")
    data = data.dropna(subset=["lat", "lon"]).sort_values("model_rank_num", na_position="last").copy()
    return data


def top_site_id(data: pd.DataFrame) -> str:
    ranked = data.sort_values("model_rank_num", na_position="last")
    if ranked.empty:
        return ""
    return str(ranked.iloc[0].get("site_id", ""))


def score_norm(scores: pd.Series) -> tuple[Normalize, str]:
    valid = pd.to_numeric(scores, errors="coerce").dropna()
    if valid.empty:
        return Normalize(vmin=0, vmax=100), "viridis"
    vmin = float(valid.min())
    vmax = float(valid.max())
    if vmin == vmax:
        vmin = max(0, vmin - 1)
        vmax += 1
    return Normalize(vmin=vmin, vmax=vmax), "viridis"


def axis_bounds(data: pd.DataFrame, pad_factor: float, min_lon_pad: float, min_lat_pad: float) -> tuple[float, float, float, float]:
    lon_min, lon_max = data["lon"].min(), data["lon"].max()
    lat_min, lat_max = data["lat"].min(), data["lat"].max()
    lon_pad = max((lon_max - lon_min) * pad_factor, min_lon_pad)
    lat_pad = max((lat_max - lat_min) * pad_factor, min_lat_pad)
    return lon_min - lon_pad, lon_max + lon_pad, lat_min - lat_pad, lat_max + lat_pad


def marker_size(score) -> float:
    number = safe_float(score)
    if number is None:
        return 180
    return 105 + number * 6.0


def marker_text_color(score) -> str:
    number = safe_float(score)
    if number is None:
        return "black"
    return "white" if number < 43 else "black"


def needs_review(row: pd.Series) -> bool:
    tier = str(row.get("tier_short", ""))
    electrical_risk = str(row.get("electrical_risk_level", "")).lower()
    return tier in {"High-review", "Special-use"} or electrical_risk == "high"


def style_axis(ax, zoom: bool = False) -> None:
    ax.grid(True, alpha=0.18, linewidth=0.7)
    ax.tick_params(labelsize=8)
    ax.xaxis.set_major_locator(MaxNLocator(5 if zoom else 6))
    ax.yaxis.set_major_locator(MaxNLocator(5 if zoom else 6))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.set_xlabel("Longitude", fontsize=8.5)
    ax.set_ylabel("Latitude", fontsize=8.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_alpha(0.85)


def draw_focus_box(ax, data: pd.DataFrame, locality: str) -> None:
    group = data[data["locality_group"] == locality]
    if group.empty:
        return
    lon0, lon1, lat0, lat1 = axis_bounds(group, pad_factor=0.55, min_lon_pad=0.010, min_lat_pad=0.010)
    ax.add_patch(
        Rectangle(
            (lon0, lat0),
            lon1 - lon0,
            lat1 - lat0,
            fill=False,
            linestyle="--",
            linewidth=0.9,
            alpha=0.35,
            zorder=1,
        )
    )


def automatic_offset(index: int) -> tuple[int, int]:
    angle = (index * 137.5) % 360
    radius = 18
    return int(round(math.cos(math.radians(angle)) * radius)), int(round(math.sin(math.radians(angle)) * radius))


def plot_map_panel(
    ax,
    data: pd.DataFrame,
    norm: Normalize,
    cmap_name: str,
    top_site: str,
    title: str,
    zoom: bool,
    callouts: bool,
) -> None:
    """Plot numbered markers and optional short callouts."""
    for _, row in data.iterrows():
        tier = str(row.get("tier_short", ""))
        score = row.get("readiness_score_num", None)
        rank = safe_int(row.get("model_rank_num"))
        site_id = str(row.get("site_id", ""))
        line_width = 2.0 if needs_review(row) else 0.8
        edge = "black"
        ax.scatter(
            [row["lon"]],
            [row["lat"]],
            s=marker_size(score),
            c=[score],
            cmap=cmap_name,
            norm=norm,
            marker=TIER_MARKERS.get(tier, "o"),
            alpha=0.86,
            edgecolors=edge,
            linewidths=line_width,
            zorder=3,
        )
        if rank is not None:
            ax.text(
                row["lon"],
                row["lat"],
                str(rank),
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold",
                color=marker_text_color(score),
                zorder=4,
            )
        if site_id == top_site:
            ax.scatter(
                [row["lon"]],
                [row["lat"]],
                s=310,
                marker="*",
                facecolors="none",
                edgecolors="black",
                linewidths=1.2,
                zorder=5,
            )

    if callouts:
        ordered = data.sort_values("model_rank_num", na_position="last").reset_index(drop=True)
        for index, row in ordered.iterrows():
            site_id = str(row.get("site_id", ""))
            rank = safe_int(row.get("model_rank_num"))
            label = f"#{rank} {site_id}" if rank is not None else site_id
            offset = CALLOUT_OFFSETS.get(site_id, automatic_offset(index))
            ax.annotate(
                label,
                xy=(row["lon"], row["lat"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=6.8,
                ha="right" if offset[0] < 0 else "left",
                va="center",
                arrowprops={"arrowstyle": "-", "lw": 0.32, "alpha": 0.52},
                bbox={"boxstyle": "round,pad=0.16", "fc": "white", "alpha": 0.88, "lw": 0.25},
                zorder=6,
            )

    ax.set_title(title, fontsize=10, pad=8)
    style_axis(ax, zoom=zoom)


def site_title(row: pd.Series) -> str:
    return f"{row.get('site_id', '')} — {shorten(str(row.get('site_name', '')), width=36, placeholder='...')}"


def decision_line(row: pd.Series) -> str:
    score = safe_float(row.get("readiness_score_num"))
    score_text = f"{score:.1f}" if score is not None else "n/a"
    ports_now = safe_int(row.get("ports_now"))
    future_ready = safe_int(row.get("future_ready_capacity"))
    ports_text = f"{ports_now}->{future_ready} ports" if ports_now is not None and future_ready is not None else "ports n/a"
    tier = str(row.get("tier_short", ""))
    return f"#{safe_int(row.get('model_rank_num'))} {row.get('site_id')} | {score_text} | {tier} | {ports_text}"


def decision_summary(data: pd.DataFrame) -> str:
    ranked = data.sort_values("model_rank_num", na_position="last")
    lines = ["Decision summary", ""]
    lines.append("Advance first")
    advance = ranked[ranked["tier_short"] == "Advance"].head(2)
    if advance.empty:
        advance = ranked.head(2)
    for _, row in advance.iterrows():
        lines.append(f"• {decision_line(row)}")

    if "PWC006" in set(data["site_id"].astype(str)):
        pwc006 = data[data["site_id"].astype(str) == "PWC006"].iloc[0]
        lines.extend(["", "Best current PWC library option", f"• {decision_line(pwc006)}"])

    review_rows = ranked[ranked.apply(needs_review, axis=1)]
    if not review_rows.empty:
        lines.extend(["", "Review before advancement"])
        for _, row in review_rows.head(4).iterrows():
            risk = str(row.get("electrical_risk_level", "unknown"))
            tier = str(row.get("tier_short", ""))
            lines.append(f"• {row.get('site_id')} | {tier} | electrical risk: {risk}")

    return "\n".join(lines)


def port_plan(data: pd.DataFrame, max_rows: int = 7) -> str:
    ranked = data.sort_values("model_rank_num", na_position="last").head(max_rows)
    lines = ["Right-sizing snapshot", "", "Site     Now  2035  2050  Future", "-------------------------------"]
    for _, row in ranked.iterrows():
        site = str(row.get("site_id", ""))
        now = safe_int(row.get("ports_now"))
        p2035 = safe_int(row.get("ports_2035_base"))
        p2050 = safe_int(row.get("ports_2050_base"))
        future = safe_int(row.get("future_ready_capacity"))
        lines.append(f"{site:<7} {now or '-':>3}  {p2035 or '-':>4}  {p2050 or '-':>4}  {future or '-':>6}")
    return "\n".join(lines)


def guardrail_notes(data: pd.DataFrame) -> str:
    site_ids = set(data["site_id"].astype(str))
    lines = ["Planning guardrails", ""]
    if "PWC002" in site_ids:
        lines.append("• PWC002: garage / Fire Marshal / AHJ / electrical review")
    if "PWC003" in site_ids:
        lines.append("• PWC003: special-use or public-access decision")
    if "PWC008" in site_ids:
        lines.append("• PWC008: monitor because nearby charging supply is high")
    high_electrical = data[data.get("electrical_risk_level", "").astype(str).str.lower() == "high"]
    if not high_electrical.empty:
        ids = ", ".join(high_electrical["site_id"].astype(str).tolist())
        lines.append(f"• High electrical-risk screen: {ids}")
    return "\n".join(lines)


def add_text_box(ax, x: float, y: float, text: str, fontsize: float = 8.0, monospace: bool = False) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=fontsize,
        family="monospace" if monospace else None,
        linespacing=1.25,
        bbox={"boxstyle": "round,pad=0.52", "fc": "white", "alpha": 0.96, "lw": 0.6},
    )


def add_decision_legend(ax) -> None:
    handles = [
        Line2D([0], [0], marker=TIER_MARKERS[tier], linestyle="None", markerfacecolor="white", markeredgecolor="black", color="black", markersize=7, label=tier)
        for tier in TIER_ORDER
    ]
    handles.append(Line2D([0], [0], marker="*", linestyle="None", markerfacecolor="white", markeredgecolor="black", color="black", markersize=9, label="Top-ranked"))
    handles.append(Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="white", markeredgecolor="black", markeredgewidth=2.0, color="black", markersize=7, label="Needs review"))
    ax.legend(handles=handles, title="Map encoding", loc="lower left", fontsize=7.5, title_fontsize=8, framealpha=0.92)


def plot_decision_map(data: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)
    norm, cmap_name = score_norm(data["readiness_score_num"])
    top_site = top_site_id(data)

    fig = plt.figure(figsize=(16.8, 9.4))
    grid = fig.add_gridspec(
        2,
        3,
        width_ratios=[1.55, 1.00, 1.05],
        height_ratios=[1, 1],
        left=0.055,
        right=0.985,
        bottom=0.11,
        top=0.875,
        wspace=0.28,
        hspace=0.34,
    )
    ax_overview = fig.add_subplot(grid[:, 0])
    ax_ffx = fig.add_subplot(grid[0, 1])
    ax_pwc = fig.add_subplot(grid[1, 1])
    panel_ax = fig.add_subplot(grid[:, 2])
    panel_ax.axis("off")

    draw_focus_box(ax_overview, data, "FFX")
    draw_focus_box(ax_overview, data, "PWC")
    plot_map_panel(ax_overview, data, norm, cmap_name, top_site, "Overview: ranked candidate sites", zoom=False, callouts=False)
    lon0, lon1, lat0, lat1 = axis_bounds(data, pad_factor=0.20, min_lon_pad=0.018, min_lat_pad=0.018)
    ax_overview.set_xlim(lon0, lon1)
    ax_overview.set_ylim(lat0, lat1)
    add_decision_legend(ax_overview)

    ffx = data[data["locality_group"] == "FFX"].copy()
    if not ffx.empty:
        plot_map_panel(ax_ffx, ffx, norm, cmap_name, top_site, "Fairfax-area zoom", zoom=True, callouts=True)
        lon0, lon1, lat0, lat1 = axis_bounds(ffx, pad_factor=1.10, min_lon_pad=0.012, min_lat_pad=0.010)
        ax_ffx.set_xlim(lon0, lon1)
        ax_ffx.set_ylim(lat0, lat1)

    pwc = data[data["locality_group"] == "PWC"].copy()
    if not pwc.empty:
        plot_map_panel(ax_pwc, pwc, norm, cmap_name, top_site, "Prince William County zoom", zoom=True, callouts=True)
        lon0, lon1, lat0, lat1 = axis_bounds(pwc, pad_factor=0.36, min_lon_pad=0.018, min_lat_pad=0.016)
        ax_pwc.set_xlim(lon0, lon1)
        ax_pwc.set_ylim(lat0, lat1)

    add_text_box(panel_ax, 0.00, 1.00, decision_summary(data), fontsize=8.0)
    add_text_box(panel_ax, 0.00, 0.50, port_plan(data), fontsize=7.7, monospace=True)
    add_text_box(panel_ax, 0.00, 0.235, guardrail_notes(data), fontsize=7.8)

    cax = panel_ax.inset_axes([0.00, 0.055, 0.82, 0.035])
    mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap_name)
    mappable.set_array([])
    cbar = fig.colorbar(mappable, cax=cax, orientation="horizontal")
    cbar.set_label("Readiness score", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    fig.suptitle("EV Charging Site Readiness & Right-Sizing Decision Map", fontsize=15.5, y=0.965)
    fig.text(
        0.50,
        0.915,
        "V2 planning screen: ranked readiness, action category, review risk, and port-sizing strategy.",
        ha="center",
        fontsize=9,
    )
    fig.text(
        0.50,
        0.045,
        "Planning screen only — not engineering design, permitting approval, utility approval, procurement, or construction direction.",
        ha="center",
        fontsize=8,
    )
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a V2 EV charging decision map.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="V2 candidate-site input CSV.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="V2 electrical risk summary CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--right-sizing-validation", default=DEFAULT_RIGHT_SIZING_VALIDATION, help="V2 right-sizing validation CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    results_path = Path(args.results)
    electrical_path = Path(args.electrical_summary)
    right_sizing_path = Path(args.right_sizing)
    validation_path = Path(args.right_sizing_validation)
    output_path = Path(args.output)

    data = load_decision_data(input_path, results_path, electrical_path, right_sizing_path, validation_path)
    plot_decision_map(data, output_path)

    print("V2 SITE DECISION MAP")
    print("--------------------")
    print(f"Input file: {input_path}")
    print(f"Results file: {results_path}")
    print(f"Electrical summary: {electrical_path}")
    print(f"Right-sizing: {right_sizing_path}")
    print(f"Right-sizing validation: {validation_path}")
    print(f"Saved map: {output_path}")
    print(f"Sites plotted: {len(data)}")
    print(f"Top site: {top_site_id(data)}")


if __name__ == "__main__":
    main()
