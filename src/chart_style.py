"""Shared chart styling for the Future City Fellowship prototype.

Generated Matplotlib charts use Times New Roman so every V2 chart has a
consistent report-style typography. Font files are intentionally not committed to
the repo; Times New Roman is expected to come from the local operating system.
"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib import font_manager

PRIMARY_FONT = "Times New Roman"
FONT_FALLBACKS = [
    "Times New Roman",
    "Times",
    "Nimbus Roman",
    "Liberation Serif",
    "DejaVu Serif",
]


def available_chart_fonts() -> list[str]:
    """Return preferred chart font family names visible to Matplotlib."""
    preferred = set(FONT_FALLBACKS)
    return sorted({font.name for font in font_manager.fontManager.ttflist if font.name in preferred})


def preferred_chart_font() -> str:
    """Return the best available chart font family name."""
    available = set(available_chart_fonts())
    for family in FONT_FALLBACKS:
        if family in available:
            return family
    return "DejaVu Serif"


def apply_chart_style() -> str:
    """Apply the shared chart font and calm presentation defaults.

    Returns the selected Matplotlib font family name for diagnostics.
    """
    selected_font = preferred_chart_font()
    font_stack = [selected_font] + [font for font in FONT_FALLBACKS if font != selected_font]
    mpl.rcParams.update({
        "font.family": [selected_font],
        "font.serif": font_stack,
        "font.sans-serif": font_stack,
        "font.monospace": font_stack,
        "axes.titlesize": 14,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 16,
        "savefig.dpi": 220,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return selected_font
