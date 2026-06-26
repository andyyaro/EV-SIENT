"""Run the V2 GIS decision-map generator with all 12 sites labeled on the report map.

This wrapper keeps the README map less crowded while forcing the full report map
to label every candidate site. It also locks all Matplotlib text on this map to
the detected Libre Caslon chart font, including text calls that otherwise pass a
family such as "monospace".
"""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from chart_style import apply_chart_style, preferred_chart_font
import plot_site_decision_map as base

SELECTED_FONT = apply_chart_style()
SELECTED_FONT = preferred_chart_font()


def _lock_text_kwargs(kwargs: dict) -> dict:
    """Force a consistent chart font for every text artist in the GIS map."""
    locked = dict(kwargs)
    locked.pop("family", None)
    locked.pop("fontfamily", None)
    locked.setdefault("fontname", SELECTED_FONT)
    return locked


_original_axes_text = Axes.text
_original_axes_annotate = Axes.annotate
_original_figure_text = Figure.text
_original_figure_suptitle = Figure.suptitle


def _axes_text_with_locked_font(self, *args, **kwargs):
    return _original_axes_text(self, *args, **_lock_text_kwargs(kwargs))


def _axes_annotate_with_locked_font(self, *args, **kwargs):
    return _original_axes_annotate(self, *args, **_lock_text_kwargs(kwargs))


def _figure_text_with_locked_font(self, *args, **kwargs):
    return _original_figure_text(self, *args, **_lock_text_kwargs(kwargs))


def _figure_suptitle_with_locked_font(self, *args, **kwargs):
    return _original_figure_suptitle(self, *args, **_lock_text_kwargs(kwargs))


Axes.text = _axes_text_with_locked_font
Axes.annotate = _axes_annotate_with_locked_font
Figure.text = _figure_text_with_locked_font
Figure.suptitle = _figure_suptitle_with_locked_font

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
    print(f"GIS map font locked to: {SELECTED_FONT}")
    base.main()
