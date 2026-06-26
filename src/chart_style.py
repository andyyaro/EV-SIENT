"""Shared chart styling for the Future City Fellowship prototype.

The project uses Libre Caslon Condensed for generated Matplotlib charts when the
font is available locally. Font files are intentionally not committed to the repo;
install the font on your machine or place the .otf files in a local ignored font
folder such as fonts/.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FONT_FAMILY = "Libre Caslon Condensed"
FONT_PATTERNS = (
    "LibreCaslonCondensed-*.otf",
    "LibreCaslonCondensed-*.ttf",
    "Libre Caslon Condensed*.otf",
    "Libre Caslon Condensed*.ttf",
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


def apply_chart_style() -> None:
    """Apply the shared chart font and calm presentation defaults."""
    _register_local_fonts()
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": [FONT_FAMILY, "Libre Caslon", "Georgia", "Times New Roman", "DejaVu Serif"],
        "font.sans-serif": [FONT_FAMILY, "Libre Caslon", "DejaVu Sans"],
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
