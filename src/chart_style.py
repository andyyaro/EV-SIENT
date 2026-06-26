"""Shared chart styling for the Future City Fellowship prototype.

Generated Matplotlib charts use the Libre Caslon family when it is available
locally. Font files are intentionally not committed to the repo; install the
font on your machine, keep it in ~/Library/Fonts, or place the files in a local
ignored folder such as fonts/.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FONT_FALLBACKS = [
    "Libre Caslon Text",
    "Libre Caslon Display",
    "Libre Caslon",
    "Georgia",
    "Times New Roman",
    "DejaVu Serif",
]
FONT_PATTERNS = (
    "*Libre*Caslon*.otf",
    "*Libre*Caslon*.ttf",
    "LibreCaslon*.otf",
    "LibreCaslon*.ttf",
)
LOCAL_FONT_DIRS = (
    PROJECT_ROOT / "fonts",
    PROJECT_ROOT / "assets" / "fonts",
    PROJECT_ROOT / "docs" / "assets" / "fonts",
    PROJECT_ROOT / "data" / "fonts",
)
SYSTEM_FONT_DIRS = (
    Path.home() / "Library" / "Fonts",
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path.home() / ".local" / "share" / "fonts",
    Path("/usr/local/share/fonts"),
    Path("/usr/share/fonts"),
)


def _candidate_font_dirs() -> list[Path]:
    dirs: list[Path] = []
    env_dirs = os.environ.get("FCF_FONT_DIRS", "")
    for item in env_dirs.split(os.pathsep):
        if item.strip():
            dirs.append(Path(item).expanduser())
    dirs.extend(LOCAL_FONT_DIRS)
    dirs.extend(SYSTEM_FONT_DIRS)
    return dirs


def _register_local_fonts() -> int:
    registered = 0
    seen: set[Path] = set()
    for directory in _candidate_font_dirs():
        if not directory.exists():
            continue
        for pattern in FONT_PATTERNS:
            for font_path in directory.rglob(pattern):
                resolved = font_path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                try:
                    font_manager.fontManager.addfont(str(resolved))
                    registered += 1
                except Exception:
                    continue
    return registered


def available_libre_caslon_fonts() -> list[str]:
    """Return Libre Caslon font family names visible to Matplotlib."""
    _register_local_fonts()
    names = sorted({font.name for font in font_manager.fontManager.ttflist if "Libre Caslon" in font.name})
    return names


def preferred_chart_font() -> str:
    """Return the best available chart font family name."""
    available = set(available_libre_caslon_fonts())
    for family in FONT_FALLBACKS:
        if family in available:
            return family
    for family in sorted(available):
        if "Libre Caslon" in family:
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
