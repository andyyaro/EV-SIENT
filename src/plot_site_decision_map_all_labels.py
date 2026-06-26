"""Run the V2 GIS decision-map generator with all 12 sites labeled on the report map.

This wrapper keeps the README map compact while forcing both the full report map
and README map to show visible external callout tags for every candidate site.
It uses the shared project chart style so the GIS map typography matches the
other generated charts, and it enlarges the decision panel typography for
presentation/readability without letting sections overlap.
"""

from __future__ import annotations

from chart_style import apply_chart_style, preferred_chart_font
import plot_site_decision_map as base

SELECTED_FONT = apply_chart_style()
SELECTED_FONT = preferred_chart_font()

ALL_DECISION_MAP_LABEL_IDS = {
    "FFX001", "FFX002", "FFX003", "FFX004",
    "PWC001", "PWC002", "PWC003", "PWC004",
    "PWC005", "PWC006", "PWC007", "PWC008",
}

PANEL_TITLE_SIZE = 13.8
SECTION_TITLE_SIZE = 10.6
BODY_SIZE = 7.7
SMALL_BODY_SIZE = 7.0
TABLE_HEADER_SIZE = 6.75
TABLE_BODY_SIZE = 6.65
LEGEND_SIZE = 6.9
METRIC_NUMBER_SIZE = 15.8
METRIC_LABEL_SIZE = 7.6


def project_style_text(
    panel_ax,
    x: float,
    y: float,
    value: str,
    size: float = BODY_SIZE,
    weight: str | None = None,
    family: str | None = None,
    color: str = "#111827",
) -> None:
    """Draw dashboard text with the shared Times New Roman chart font."""
    panel_ax.text(
        x,
        y,
        value,
        transform=panel_ax.transAxes,
        ha="left",
        va="top",
        fontsize=size,
        fontweight=weight,
        fontname=SELECTED_FONT,
        color=color,
        zorder=3,
    )


def add_site_labels_force_visible(
    ax,
    sites_3857: base.gpd.GeoDataFrame,
    label_ids: set[str],
    fontsize: float = 6.7,
    show_ports: bool = True,
) -> None:
    """Draw external callout tags for every requested site.

    The README decision map previously showed numbered markers for all sites but
    only labeled a subset. This replacement keeps the normal label-selection
    behavior for any explicitly requested set, but when the all-label set is
    passed it guarantees every candidate gets a visible, unclipped callout.
    """
    rows = base.label_subset(sites_3857, label_ids)
    if set(label_ids) >= ALL_DECISION_MAP_LABEL_IDS:
        rows = sites_3857.sort_values("model_rank")

    for _, row in rows.iterrows():
        site_id = str(row.get("site_id", ""))
        score_text = base.fmt_score(row.get("readiness_score"))
        if show_ports:
            label = f"#{base.fmt_int(row.get('model_rank'))} {site_id}\n{score_text} | {base.fmt_ports(row)} ports"
        else:
            label = f"#{base.fmt_int(row.get('model_rank'))} {site_id}\n{score_text}"
        dx, dy = base.LABEL_OFFSETS.get(site_id, (12, 10))
        ax.annotate(
            label,
            xy=(row.geometry.x, row.geometry.y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if dx < 0 else "left",
            va="center",
            fontsize=fontsize,
            fontname=SELECTED_FONT,
            color="#111827",
            arrowprops={"arrowstyle": "-", "lw": 0.62, "color": "#334155", "alpha": 0.74},
            bbox={"boxstyle": "round,pad=0.20", "fc": "white", "ec": "#cbd5e1", "alpha": 0.96, "lw": 0.55},
            zorder=20,
            annotation_clip=False,
            clip_on=False,
        )


def draw_metric_pills_large(panel_ax, sites: base.gpd.GeoDataFrame) -> None:
    metrics = [
        ("Sites", len(sites)),
        ("Advance", base.action_count(sites, "Advance")),
        ("Review", base.action_count(sites, "High-review")),
        ("High risk", base.high_risk_count(sites)),
    ]
    for index, (label, value) in enumerate(metrics):
        x = 0.065 + index * 0.232
        panel_ax.add_patch(
            base.FancyBboxPatch(
                (x, 0.830),
                0.210,
                0.072,
                transform=panel_ax.transAxes,
                boxstyle="round,pad=0.010,rounding_size=0.012",
                linewidth=0.7,
                edgecolor="#d0d7de",
                facecolor="#f8fafc",
                zorder=2,
            )
        )
        panel_ax.text(
            x + 0.105,
            0.878,
            str(value),
            transform=panel_ax.transAxes,
            ha="center",
            va="center",
            fontsize=METRIC_NUMBER_SIZE,
            fontweight="bold",
            fontname=SELECTED_FONT,
            color="#111827",
            zorder=3,
        )
        panel_ax.text(
            x + 0.105,
            0.845,
            label,
            transform=panel_ax.transAxes,
            ha="center",
            va="center",
            fontsize=METRIC_LABEL_SIZE,
            fontname=SELECTED_FONT,
            color="#475569",
            zorder=3,
        )


def draw_pwc_table_large(panel_ax, sites: base.gpd.GeoDataFrame, y: float) -> None:
    base.text(panel_ax, 0.07, y, "PWC cluster", size=SECTION_TITLE_SIZE, weight="bold")
    y -= 0.040
    base.text(panel_ax, 0.07, y, "Rank  Site    Score  Action       Ports", size=TABLE_HEADER_SIZE, color="#64748b")
    y -= 0.026
    for _, row in base.ranked(sites[sites["site_id"].astype(str).isin(base.PWC_CLUSTER_IDS)]).iterrows():
        color = base.ACTION_COLORS.get(str(row.get("action_group", "")), "#64748b")
        panel_ax.scatter(
            [0.083],
            [y - 0.003],
            transform=panel_ax.transAxes,
            s=39,
            color=color,
            edgecolors="#111827",
            linewidths=0.50,
            zorder=3,
        )
        base.text(
            panel_ax,
            0.110,
            y,
            f"#{base.fmt_int(row.get('model_rank')):<2}  {row.get('site_id'):<7} {base.fmt_score(row.get('readiness_score')):<5} {str(row.get('action_group')):<11} {base.fmt_ports(row)}",
            size=TABLE_BODY_SIZE,
        )
        y -= 0.0235


def draw_port_snapshot_large(panel_ax, sites: base.gpd.GeoDataFrame, y: float) -> None:
    """Draw a compact port summary so the legend remains readable."""
    base.text(panel_ax, 0.07, y, "Port plan", size=SECTION_TITLE_SIZE, weight="bold")
    data = base.ranked(sites)
    top = data.iloc[0]
    top_two = data.iloc[1]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")].iloc[0]
    lines = [
        f"Largest future-ready sites: {top.get('site_id')} {base.fmt_ports(top)} ports; {top_two.get('site_id')} {base.fmt_ports(top_two)} ports",
        f"Top PWC library candidate: {pwc.get('site_id')} {base.fmt_ports(pwc)} ports",
        "Full 12-site port table is in the executive summary and package.",
    ]
    yy = y - 0.040
    for line in lines:
        base.text(panel_ax, 0.07, yy, line, size=SMALL_BODY_SIZE)
        yy -= 0.026


def draw_encoding_large(panel_ax, y: float) -> None:
    base.text(panel_ax, 0.07, y, "Map encoding", size=SECTION_TITLE_SIZE, weight="bold")
    items = [
        ("Advance", base.ACTION_COLORS["Advance"], "filled"),
        ("Promising", base.ACTION_COLORS["Promising"], "filled"),
        ("High-review", base.ACTION_COLORS["High-review"], "filled"),
        ("Monitor", base.ACTION_COLORS["Monitor"], "filled"),
        ("Special-use", base.ACTION_COLORS["Special-use"], "filled"),
        ("High electrical risk", "#b91c1c", "halo"),
        ("Number = model rank", "#4c78a8", "number"),
    ]
    start_y = y - 0.036
    for idx, (label, color, mode) in enumerate(items):
        x = 0.09 if idx < 4 else 0.55
        row_y = start_y - (idx if idx < 4 else idx - 4) * 0.0215
        if mode == "halo":
            panel_ax.scatter([x], [row_y], transform=panel_ax.transAxes, s=48, facecolors="none", edgecolors=color, linewidths=1.7, zorder=3)
        elif mode == "number":
            panel_ax.scatter([x], [row_y], transform=panel_ax.transAxes, s=48, color=color, edgecolors="#111827", linewidths=0.7, zorder=3)
            panel_ax.text(x, row_y, "1", transform=panel_ax.transAxes, ha="center", va="center", fontsize=5.9, fontweight="bold", fontname=SELECTED_FONT, color="white", zorder=4)
        else:
            panel_ax.scatter([x], [row_y], transform=panel_ax.transAxes, s=48, color=color, edgecolors="#111827", linewidths=0.7, zorder=3)
        panel_ax.text(x + 0.032, row_y, label, transform=panel_ax.transAxes, ha="left", va="center", fontsize=LEGEND_SIZE, fontname=SELECTED_FONT, color="#111827", zorder=3)


def draw_dashboard_panel_large(panel_ax, sites: base.gpd.GeoDataFrame) -> None:
    base.panel_bg(panel_ax)
    base.text(panel_ax, 0.07, 0.952, "Decision dashboard", size=PANEL_TITLE_SIZE, weight="bold")
    draw_metric_pills_large(panel_ax, sites)
    base.rule(panel_ax, 0.798)

    data = base.ranked(sites)
    top = data.iloc[0]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")]
    top_pwc = pwc.iloc[0]

    base.text(panel_ax, 0.07, 0.770, "Top decisions", size=SECTION_TITLE_SIZE, weight="bold")
    top_lines = [
        f"Top: #{base.fmt_int(top.get('model_rank'))} {top.get('site_id')} | {base.fmt_score(top.get('readiness_score'))} | {base.fmt_ports(top)} ports",
        f"Top PWC: #{base.fmt_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')} | {base.fmt_score(top_pwc.get('readiness_score'))} | {base.fmt_ports(top_pwc)} ports",
        f"Next: #{base.fmt_int(data.iloc[1].get('model_rank'))} {data.iloc[1].get('site_id')} • #{base.fmt_int(data.iloc[2].get('model_rank'))} {data.iloc[2].get('site_id')} • #{base.fmt_int(data.iloc[3].get('model_rank'))} {data.iloc[3].get('site_id')}",
    ]
    y = 0.730
    for line in top_lines:
        base.text(panel_ax, 0.07, y, line, size=BODY_SIZE)
        y -= 0.030
    base.rule(panel_ax, 0.635)

    draw_pwc_table_large(panel_ax, sites, 0.606)
    base.rule(panel_ax, 0.438)

    base.text(panel_ax, 0.07, 0.412, "Review watchlist", size=SECTION_TITLE_SIZE, weight="bold")
    y = 0.374
    for line in base.review_lines(sites):
        base.text(panel_ax, 0.07, y, line, size=BODY_SIZE)
        y -= 0.030
    base.rule(panel_ax, 0.280)

    draw_port_snapshot_large(panel_ax, sites, 0.254)
    base.rule(panel_ax, 0.148)
    draw_encoding_large(panel_ax, 0.122)


def draw_readme_panel_large(panel_ax, sites: base.gpd.GeoDataFrame) -> None:
    base.panel_bg(panel_ax)
    data = base.ranked(sites)
    top = data.iloc[0]
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")]
    top_pwc = pwc.iloc[0]
    base.text(panel_ax, 0.07, 0.925, "Top decisions", size=12.0, weight="bold")
    lines = [
        f"#{base.fmt_int(top.get('model_rank'))} {top.get('site_id')} — top overall",
        f"{base.fmt_score(top.get('readiness_score'))} | {base.fmt_ports(top)} ports",
        "",
        f"#{base.fmt_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')} — top PWC",
        f"{base.fmt_score(top_pwc.get('readiness_score'))} | {base.fmt_ports(top_pwc)} ports",
        "",
        "PWC cluster",
    ]
    for _, row in base.ranked(sites[sites["site_id"].astype(str).isin(base.PWC_CLUSTER_IDS)]).head(3).iterrows():
        lines.append(f"#{base.fmt_int(row.get('model_rank'))} {row.get('site_id')} — {row.get('action_group')} | {base.fmt_ports(row)}")
    y = 0.875
    for line in lines:
        base.text(panel_ax, 0.07, y, line, size=8.5)
        y -= 0.039 if line == "" else 0.032
    base.rule(panel_ax, 0.390)
    draw_encoding_large(panel_ax, 0.345)


base.text = project_style_text
base.add_site_labels = add_site_labels_force_visible
base.draw_metric_pills = draw_metric_pills_large
base.draw_pwc_table = draw_pwc_table_large
base.draw_port_snapshot = draw_port_snapshot_large
base.draw_encoding = draw_encoding_large
base.draw_dashboard_panel = draw_dashboard_panel_large
base.draw_readme_panel = draw_readme_panel_large

base.MAIN_LABEL_SITE_IDS = ALL_DECISION_MAP_LABEL_IDS
base.README_LABEL_SITE_IDS = ALL_DECISION_MAP_LABEL_IDS

base.LABEL_OFFSETS.update({
    "FFX001": (-84, -14),
    "FFX002": (12, 12),
    "FFX003": (14, -10),
    "FFX004": (-82, 18),
    "PWC001": (-84, 28),
    "PWC002": (-92, 14),
    "PWC003": (12, -26),
    "PWC004": (16, 20),
    "PWC005": (12, 18),
    "PWC006": (-84, -12),
    "PWC007": (18, 18),
    "PWC008": (14, -20),
})


if __name__ == "__main__":
    print(f"GIS map chart font: {SELECTED_FONT}")
    print("GIS decision dashboard: enlarged right-panel typography with compact port summary")
    print("GIS README map: all 12 candidate callout tags enabled")
    base.main()
