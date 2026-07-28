"""Generate the SYNTHETIC scenario file the public MATLAB harness runs on.

The harness exists to obtain free MathWorks MATLAB in CI. It publishes *methodology*,
never *findings*, so it must never carry the real canonical CSV -- redacted or not.
Redaction leaks by column co-occurrence; synthesis does not, because there is nothing
real left to correlate.

What this file has to get right
-------------------------------
A synthetic fixture that exercises fewer code paths than the real one quietly turns the
harness into a different, weaker test while still reporting green. The real CSV was
profiled and the generator reproduces its *structure* -- row count, the horizon x case
grid, the value ranges, and specifically the branch-selecting edge cases -- while sharing
none of its per-site values:

* 12 sites x (1 baseline + 3 horizons x 3 cases) = 120 rows, matching the real shape
* ``sessions_per_day < 1`` on some rows, so the ``nSessions == 1`` branch in
  makeSessionProfiles is exercised (12 real rows do this; a fixture without them skips it)
* all four ``dwell_hr`` values, including 3.0
* all three arrival-window archetypes
* ``capacity_basis = placeholder`` and empty capacity columns on every row, because the
  fail-closed guard is the single most valuable thing the harness demonstrates

Site ids are ``SYN001..SYN012`` -- structurally valid, obviously synthetic, and matching no
real facility. The MATLAB tests read ids from the data rather than naming them, so they run
unchanged against either file.

Deterministic: a fixed seed, so the fixture is reproducible and diffable.
"""

from __future__ import annotations

import argparse
import importlib.util
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "matlab/data/harness/harness_scenarios_synthetic.csv"


def _identifying_values() -> dict[str, dict[float, str]]:
    """``{column: {value: the one real site it resolves to}}``, from the exposure gate.

    Imported from ``check_harness_exposure`` rather than restated, so the generator and the
    gate cannot drift into disagreeing about what counts as identifying. One definition.
    """
    path = REPO / "scripts/check_harness_exposure.py"
    spec = importlib.util.spec_from_file_location("_fcf_exposure", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.identifying_values()


def avoid_real(column: str, value: float, identifying: dict[str, dict[float, str]],
               step: float = 0.01, decimals: int = 2) -> float:
    """Nudge a generated value off any real value that pins a single site.

    Synthesising from a random draw does not guarantee the result differs from real data --
    it only makes collision unlikely, and unlikely happened. The published fixture carried
    ``sessions_per_day = 0.9``, which is **PWC003's value and nobody else's**, so a public
    file contained a real per-site figure. The exposure gate could not see it: its rule
    wants a value and its column name on one line, which a CSV can never satisfy.

    The one-sentence explanation this owes the reader: *if a generated number happens to
    equal a real number that identifies a single site, add one cent-sized step until it
    does not.* The nudge is at most a few hundredths, so the fixture's structure, ranges and
    branch coverage are untouched, and it is deterministic, so the file stays diffable.
    """
    column_map = identifying.get(column)
    if not column_map:
        return value
    guarded = round(float(value), decimals)
    for _ in range(100):
        if guarded not in column_map:
            return guarded
        guarded = round(guarded + step, decimals)
    raise SystemExit(
        f"could not find a non-identifying value near {value} for column {column!r}; "
        f"this needs a human, not a wider search")


COLUMNS = [
    "scenario_id", "site_id", "site_name", "horizon_year", "case", "ports",
    "charger_power_kW", "spare_capacity_kW", "service_capacity_kW", "capacity_basis",
    "capacity_source", "base_load_mean_kW", "base_load_peak_kW", "arrival_start_hr",
    "arrival_end_hr", "dwell_hr", "sessions_per_day", "energy_per_session_kWh",
    "managed_charging_policy", "model_rank", "electrical_risk_level", "source_note",
]

# Uniform across all 12 real sites, so these are modelling constants rather than
# identifying data and the fixture may use the true values.
CHARGER_POWER_KW = 19.2
ENERGY_PER_SESSION_KWH = 9.5

# Per-site base load, highest first. See the note in rows(): the regression panel takes
# the first two site ids in sorted order, so those two must be demanding enough for the
# capacity-limited strategies to bind. Values are fabricated.
BASE_LOAD_MEAN_KW = [96.0, 88.0, 41.5, 36.0, 74.0, 52.5, 45.0, 63.0, 33.0, 58.0, 49.0, 70.0]

# Three use-class archetypes: (start, end, dwell). Shapes, not real windows.
ARCHETYPES = [(7.0, 11.0, 4.0), (8.0, 16.0, 3.0), (10.0, 17.0, 1.5), (9.0, 15.0, 2.0)]

HORIZONS = [2026, 2036, 2046, 2056]
CASES = {2026: ["baseline"], 2036: ["base", "high", "stress_combined"],
         2046: ["base", "high", "stress_combined"], 2056: ["base", "high", "stress_combined"]}

SOURCE_NOTE = (
    "SYNTHETIC harness fixture - not project data. Generated by "
    "scripts/make_harness_fixture.py to exercise the MATLAB pipeline in a public CI "
    "runner. Values are fabricated; no row corresponds to any real facility. "
    "CAPACITY IS A PLANNING PLACEHOLDER - no feasibility claim permitted."
)
CAPACITY_SOURCE = "synthetic fixture; capacity deliberately undefined to exercise the fail-closed guard"


def rows(seed: int = 20260727) -> list[dict]:
    rng = random.Random(seed)
    identifying = _identifying_values()
    out: list[dict] = []
    for n in range(1, 13):
        site_id = f"SYN{n:03d}"
        start, end, dwell = ARCHETYPES[n % len(ARCHETYPES)]
        # Base loads are NOT monotonic in the site number, deliberately.
        #
        # test_regression composes its golden panel from the first two site ids in
        # sorted order. When base load rose with n, that panel was the two LIGHTEST
        # sites, their capacity never bound at any plausible cap, and the real MATLAB
        # run produced a golden in which curtailed and unmet were identically zero and
        # peak_clamp equalled peak_unmanaged -- four of seven columns carrying no
        # information. A regression baseline that cannot distinguish the managed
        # strategies from the unmanaged one would not detect a regression in them.
        #
        # The panel sites therefore carry the heaviest loads, so the clamp and
        # energy-aware branches actually bind and the golden discriminates.
        base_mean = avoid_real("base_load_mean_kW", BASE_LOAD_MEAN_KW[n - 1],
                               identifying, step=0.1, decimals=1)
        base_peak = avoid_real("base_load_peak_kW", base_mean * rng.uniform(1.3, 1.6),
                               identifying, step=0.1, decimals=1)
        # Every fourth site is deliberately low-demand so sessions_per_day < 1 and the
        # single-session branch is exercised, as it is by 12 rows of the real file.
        low_demand = (n % 4 == 0)
        for horizon in HORIZONS:
            for case in CASES[horizon]:
                growth = {2026: 1.0, 2036: 1.9, 2046: 2.8, 2056: 3.4}[horizon]
                case_mult = {"baseline": 1.0, "base": 1.0, "high": 1.35, "stress_combined": 1.55}[case]
                base_sessions = 0.35 if low_demand else rng.uniform(1.1, 3.2)
                sessions = avoid_real("sessions_per_day",
                                      base_sessions * growth * case_mult, identifying)
                ports = min(8, max(2, 2 * round((sessions * dwell / 6) + 0.5)))
                out.append({
                    "scenario_id": f"{site_id}_{horizon}_{case}",
                    "site_id": site_id,
                    "site_name": f"Synthetic Site {n:02d}",
                    "horizon_year": horizon,
                    "case": case,
                    "ports": ports,
                    "charger_power_kW": CHARGER_POWER_KW,
                    "spare_capacity_kW": "",       # empty: triggers the fail-closed guard
                    "service_capacity_kW": "",     # empty: same
                    "capacity_basis": "placeholder",
                    "capacity_source": CAPACITY_SOURCE,
                    "base_load_mean_kW": base_mean,
                    "base_load_peak_kW": base_peak,
                    "arrival_start_hr": start,
                    "arrival_end_hr": end,
                    "dwell_hr": dwell,
                    "sessions_per_day": sessions,
                    "energy_per_session_kWh": ENERGY_PER_SESSION_KWH,
                    "managed_charging_policy": "none",
                    "model_rank": "",              # FINDING column: present, deliberately empty
                    "electrical_risk_level": "",   # FINDING column: present, deliberately empty
                    "source_note": SOURCE_NOTE,
                })
    return out


def write(path: Path, seed: int = 20260727) -> Path:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    data = rows(seed)
    # newline="" is required by the csv module, but csv.writer then defaults to a CRLF
    # line terminator. The Python producer that writes the real canonical CSV emits LF, and
    # a fixture that differs from the real file in its line endings is a fixture that can
    # fail where the real file passes -- which is the one thing a harness fixture must not do.
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--seed", type=int, default=20260727)
    args = ap.parse_args()
    path = write(Path(args.out), args.seed)
    data = rows(args.seed)
    lows = sum(1 for r in data if float(r["sessions_per_day"]) < 1)
    print(f"wrote {path} — {len(data)} rows, {len({r['site_id'] for r in data})} synthetic sites")
    print(f"  sessions_per_day: {min(float(r['sessions_per_day']) for r in data)} - "
          f"{max(float(r['sessions_per_day']) for r in data)}  ({lows} rows below 1.0)")
    print(f"  dwell_hr values : {sorted({float(r['dwell_hr']) for r in data})}")
    print(f"  capacity_basis  : placeholder on all rows (fail-closed guard exercised)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
