"""Presentation visuals with mandatory source/date/assumption footers (PY-17).

Every chart produced through this module carries: source, source date/vintage,
scenario, model version, and (when applicable) assumption/proxy labels.
``footer()`` is the single choke point; ``audit_footer_metadata()`` provides the
automated visual QA hook (PY-17 acceptance: no unlabeled final chart).

Palette follows the Phase 1 identity: warm beige background, dark green, black.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .config import MODEL_VERSION, SCHEMA_VERSION_V3

BEIGE = "#F5F0E6"
DARK_GREEN = "#1B4332"
MID_GREEN = "#40694F"
BLACK = "#1A1A1A"
ACCENT = "#B08948"

_FOOTER_LOG: list[dict] = []

#: Provenance keyed by the FIGURE it was stamped on, so `save()` cannot attribute one chart's
#: source to another. It used to take `_FOOTER_LOG[-1]` -- simply the most recent footer call --
#: which meant a figure saved without calling `footer()` was logged carrying the PREVIOUS
#: chart's source, vintage and scenario, and `audit_footer_metadata` passed it, because that
#: audit only checks that a filename appears in the log and `save()` always writes one.
#: Reproduced before fixing: two charts, one stamped and one not, produced two log entries with
#: identical provenance and a clean audit.
_FOOTER_BY_FIGURE: dict[int, dict] = {}


def style_axes(ax):
    ax.set_facecolor(BEIGE)
    ax.figure.set_facecolor(BEIGE)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BLACK)
    ax.tick_params(colors=BLACK)
    ax.title.set_color(BLACK)
    return ax


def footer(fig, source: str, source_date: str, scenario: str,
           assumption: str | None = None) -> None:
    """Stamp the mandatory provenance footer onto a figure and log it for QA."""
    parts = [f"Source: {source}", f"Vintage: {source_date}", f"Scenario: {scenario}",
             # Charts are drawn from the authoritative contract, v3 since DEC-027.
             f"Model: fcf_m2 v{MODEL_VERSION} / contract v{SCHEMA_VERSION_V3}"]
    if assumption:
        parts.append(f"Assumption: {assumption}")
    text = "  ·  ".join(parts)
    fig.text(0.01, 0.005, text, fontsize=6.2, color=BLACK, alpha=0.85, ha="left", va="bottom")
    entry = {"source": source, "source_date": source_date,
             "scenario": scenario, "assumption": assumption or ""}
    _FOOTER_LOG.append(entry)
    _FOOTER_BY_FIGURE[id(fig)] = entry


def log_path_for(path: str | Path, relative_to: str | Path | None = None) -> str:
    """Portable path for the footer log.

    The footer log is a tracked artifact, so it must never record the absolute
    path of whichever machine built it: that leaks a local directory layout and
    trips the repository's no-absolute-paths hygiene gate. Paths are recorded
    relative to ``relative_to`` (the repo root) when they sit underneath it, and
    otherwise fall back to the bare filename - never an absolute path.
    """
    path = Path(path)
    if relative_to is not None:
        try:
            return Path(path).resolve().relative_to(Path(relative_to).resolve()).as_posix()
        except ValueError:
            pass  # outside the repo; fall through to the filename
    return path.name


def save(fig, path: str | Path, log_path: str | Path | None = None,
         relative_to: str | Path | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    # This figure's OWN footer, never merely the most recent one. A figure that was never
    # stamped is recorded as unstamped, which is what makes the audit below able to fail.
    stamped = _FOOTER_BY_FIGURE.pop(id(fig), None)
    entry = dict(stamped) if stamped is not None else {"unstamped": True}
    entry["file"] = log_path_for(path, relative_to)
    if log_path:
        log_path = Path(log_path)
        existing = json.loads(log_path.read_text()) if log_path.exists() else []
        existing.append(entry)
        log_path.write_text(json.dumps(existing, indent=2))
    return path


def audit_footer_metadata(log_path: str | Path, chart_dir: str | Path) -> list[str]:
    """QA: every final PNG in chart_dir must appear in the footer log."""
    log_path, chart_dir = Path(log_path), Path(chart_dir)
    logged = set()
    if log_path.exists():
        logged = {Path(e["file"]).name for e in json.loads(log_path.read_text()) if e.get("file")}
    unstamped = set()
    if log_path.exists():
        unstamped = {Path(e["file"]).name for e in json.loads(log_path.read_text())
                     if e.get("file") and e.get("unstamped")}
    problems = []
    for png in sorted(chart_dir.glob("*.png")):
        if png.name not in logged:
            problems.append(f"unlabeled chart (no footer log entry): {png.name}")
        elif png.name in unstamped:
            # The case the old audit could not see: an entry EXISTS, because save() always
            # writes one, but the figure carried no footer of its own.
            problems.append(f"chart saved with no footer() call of its own: {png.name}")
    return problems
