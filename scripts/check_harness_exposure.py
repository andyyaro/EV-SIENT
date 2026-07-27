"""Gate what may be mirrored into the PUBLIC MATLAB harness repository.

The harness publishes *methodology*, never *findings*. The obvious gate -- grep for
``FFX###``/``PWC###`` and real site names -- was proposed and then shown not to work: the
two genuine leaks found in this repository were bare numbers, ``sessions_per_day = 1.16``
and ``spare_capacity_kW = 153.6``, which no string gate can see.

The principle this encodes instead
----------------------------------
A value identifies a site only if it *varies between sites*. ``charger_power_kW = 19.2``
and ``energy_per_session_kWh = 9.5`` are real values, but every one of the 12 sites carries
the same one, so they are modelling constants and a test fixture may use them freely.
``sessions_per_day`` takes 120 distinct values and ``base_load_mean_kW`` takes 8: those
identify. So the gate reads the canonical CSV, works out which columns actually discriminate
between sites, and fails on *those* values appearing in anything destined for the public repo.

It also refuses values recoverable by algebra rather than by lookup. ``energy_requested_kWh``
inverts exactly to ``sessions_per_day`` through the charger efficiency, so publishing the
former publishes the latter.

Run: ``python scripts/check_harness_exposure.py [--files ...]``
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "matlab/data/canonical/matlab_scenarios.csv"

# Files the harness would mirror. Everything here is scanned.
#
# The fixture CSV is in this list because it is published, and it was NOT being checked in
# any meaningful sense before: ``sync_matlab_harness.py --push`` did hand it to this gate,
# but the gate's rule -- a discriminating value on a line that also names its column -- is
# structurally unable to fire on a CSV, where the column names live in the header and the
# values live on every other line. It passed vacuously. See ``scan_csv``.
HARNESS_GLOBS = ("matlab/src/*.m", "matlab/tests/*.m", "matlab/data/harness/*.csv")

# A column identifies a site when it takes more than one value across the portfolio.
# Below this it is a modelling constant shared by every site.
DISCRIMINATING_MIN_DISTINCT = 2

# Columns that are identity or findings regardless of how they vary.
ALWAYS_FORBIDDEN_COLUMNS = ("site_name", "model_rank", "electrical_risk_level", "source_note")

# Free-text identifiers that must never appear.
FORBIDDEN_PATTERNS = [
    (re.compile(r"\b(?:FFX|PWC)\d{3}\b"), "real site id"),
    (re.compile(r"(?i)\b(?:fairfax|prince william|neabsco|manassas|woodbridge)\b"), "real place name"),
    (re.compile(r"(?i)\bkevin\s+milston\b"), "named stakeholder"),
    (re.compile(r"/Users/|/home/[a-z]", re.I), "absolute local path"),
]

# Numbers that are structurally uninteresting and would swamp the signal.
TRIVIAL = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 24, 100, 1000}

NUMBER = re.compile(r"(?<![\w.])(\d+\.\d+)(?![\w.])")


def discriminating_values() -> dict[float, list[str]]:
    """Map each site-discriminating value to the column(s) it came from.

    Matching on the value alone produced false positives -- 0.90 is a real
    ``sessions_per_day`` value and also an RGB component and a textbox width. A bare
    decimal is not evidence of a leak. What *is* evidence is a discriminating value
    sitting on a line that also names the field it belongs to, which is exactly the
    shape of the two real leaks: ``row.sessions_per_day = 1.16``.
    """
    df = pd.read_csv(CANONICAL)
    out: dict[float, list[str]] = {}
    for column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        distinct = series.nunique()
        forbidden_col = column in ALWAYS_FORBIDDEN_COLUMNS
        if distinct < DISCRIMINATING_MIN_DISTINCT and not forbidden_col:
            continue  # uniform across all sites: a modelling constant
        for value in series.unique():
            value = float(value)
            if value in TRIVIAL or float(value).is_integer():
                continue  # integers are too collision-prone to gate on
            out.setdefault(value, []).append(column)
    return out


def identifying_values() -> dict[str, dict[float, str]]:
    """``{column: {value: the single real site it resolves to}}``.

    A stricter and more literal reading of the same principle, needed because in a CSV the
    column name is present *by construction* and therefore carries no evidence at all.

    For source code, "a discriminating value on a line that also names its column" works:
    a ``.m`` file writing ``1.5`` next to the word ``dwell_hr`` is suspicious whether or not
    1.5 is unique. In a table, every value sits under its column name, so that test degrades
    to "is this value used anywhere in the real data", which fires constantly by chance --
    ``dwell_hr = 1.5`` matches **70 of 120** canonical rows across **7** sites and identifies
    nobody.

    So a tabular cell is a leak when the (column, value) pair resolves to **exactly one**
    real site. That is precisely the shape of the leaks this gate was built after:
    ``sessions_per_day = 1.16`` is FFX002's and no one else's.

    **Stated limitation:** a value shared by two or three sites is treated as clean, and it
    is not nothing -- it narrows twelve candidates to three. The alternative is a gate that
    fires on `dwell_hr`'s four levels forever and gets switched off, which protects less.
    """
    df = pd.read_csv(CANONICAL)
    if "site_id" not in df.columns:
        raise SystemExit(f"{CANONICAL} has no site_id column; cannot resolve values to sites")

    out: dict[str, dict[float, str]] = {}
    for column in df.columns:
        if column == "site_id":
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        frame = df.assign(_v=numeric).dropna(subset=["_v"])
        if frame.empty:
            continue
        sites_per_value = frame.groupby("_v")["site_id"].agg(["nunique", "first"])
        column_map = {
            float(value): str(row["first"])
            for value, row in sites_per_value.iterrows()
            if row["nunique"] == 1
            and float(value) not in TRIVIAL
            and not float(value).is_integer()   # integers collide far too easily
        }
        if column_map:
            out[column] = column_map
    return out


def scan_csv(path: Path, rel: Path, identifying: dict[str, dict[float, str]]) -> list[str]:
    """Column-aware scan for tabular files.

    The line-oriented rule below asks for a discriminating value and its column name on the
    **same line**, which is the right shape for source code (``row.sessions_per_day = 1.16``)
    and structurally impossible in a CSV: the column names are on line 1 and the values are
    on lines 2..N. So this gate reported the published fixture clean without ever being able
    to fail on it -- the fourth time in this project a check matched text where it needed to
    match meaning, and the first time on the gate protecting the *public* repository.

    Running it once it could see revealed a real leak: the published synthetic fixture
    carried ``sessions_per_day = 0.9``, which is PWC003's value and nobody else's.
    """
    problems: list[str] = []
    try:
        frame = pd.read_csv(path)
    except Exception as exc:                      # noqa: BLE001 - report, never skip silently
        return [f"{rel}: unreadable as CSV ({exc}); cannot certify it, so refusing it"]

    for column in frame.columns:
        column_map = identifying.get(column)
        if not column_map:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        for row, value in numeric.dropna().items():
            site = column_map.get(float(value))
            if site is None:
                continue
            problems.append(
                f"{rel}: row {row + 2}, column '{column}' holds {float(value):g} -- that is "
                f"{site}'s value in the canonical data and no other site's, so this cell "
                f"identifies a real facility")
    return problems


def scan(paths: list[Path]) -> list[str]:
    values = discriminating_values()
    identifying = identifying_values()
    problems: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # A path outside the repository is the normal case for this gate, not an error:
        # the question it answers is "may this file be published?", and a candidate is often
        # a downloaded CI artifact sitting in a temp directory. Crashing with a traceback on
        # the exact question the tool exists to answer is how a gate stops being used.
        try:
            rel = path.relative_to(REPO) if path.is_absolute() else path
        except ValueError:
            rel = path

        if path.suffix.lower() == ".csv":
            problems.extend(scan_csv(path, rel, identifying))

        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern, label in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    problems.append(f"{rel}:{lineno}: {label} -> {line.strip()[:90]}")
            for literal in NUMBER.findall(line):
                value = float(literal)
                if value not in values:
                    continue
                # Require the line to also name a column this value belongs to.
                named = [c for c in values[value] if c.lower() in line.lower()]
                if not named:
                    continue
                problems.append(
                    f"{rel}:{lineno}: real per-site value {literal} assigned to "
                    f"{', '.join(sorted(set(named)))} -> {line.strip()[:70]}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--files", nargs="*", help="explicit files to scan (default: the harness set)")
    args = ap.parse_args(argv)

    if args.files:
        paths = [Path(f) if Path(f).is_absolute() else REPO / f for f in args.files]
    else:
        paths = sorted(p for pattern in HARNESS_GLOBS for p in REPO.glob(pattern))

    if not paths:
        print("no files to scan", file=sys.stderr)
        return 1

    values = discriminating_values()
    problems = scan(paths)
    if problems:
        print("HARNESS EXPOSURE PROBLEMS (these must not reach the public repository):")
        print("\n".join(f"  {p}" for p in problems))
        return 1
    print(f"harness exposure clean ({len(paths)} files, "
          f"{len(values)} site-discriminating values gated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
