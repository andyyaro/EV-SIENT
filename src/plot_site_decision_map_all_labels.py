"""Run the V2 GIS decision-map generator with all 12 sites labeled on the report map.

This wrapper keeps the README map less crowded while forcing the full report map
to label every candidate site. It intentionally uses the same default Matplotlib
font behavior as the profile heatmap instead of forcing a separate display font.
"""

from __future__ import annotations

import matplotlib as mpl

import plot_site_decision_map as base

HEATMAP_FONT_STACK = ["DejaVu Sans"]

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": HEATMAP_FONT_STACK,
    "font.serif": HEATMAP_FONT_STACK,
    "font.monospace": HEATMAP_FONT_STACK,
})


def heatmap_style_text(panel_ax, x: float, y: float, value: str, size: float = 6.4, weight: str | None = None, family: str | None = None, color: str = "#111827") -> None:
    """Draw dashboard text with the same default-style font as the heatmap.

    The base decision-map dashboard sometimes asks for monospace text to make
    mini tables align. For visual consistency with the heatmap, this wrapper
    ignores that requested family and lets Matplotlib use the shared sans font.
    """
    panel_ax.text(
        x,
        y,
        value,
        transform=panel_ax.transAxes,
        ha="left",
        va="top",
        fontsize=size,
        fontweight=weight,
        color=color,
        zorder=3,
    )


base.text = heatmap_style_text

base.MAIN_LABEL_SITE_IDS = {
    "FFX001", "FFX002", "FFX003", "FFX004",
    "PWC001", "PWC002", "PWC003", "PWC004",
    "PWC005", "PWC006", "PWC007", "PWC008",
}

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
    print("GIS map font style: heatmap/default Matplotlib sans")
    base.main()
