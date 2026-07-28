"""Generate SYNTHETIC observation fixtures that exercise the V4 ingestion path.

These are not data. Every row is fabricated, every site id is `SYN*`, and the files carry
that statement in their own contents so a fixture can never be mistaken for a receipt.

They exist so the ingestion path, the capacity-upgrade precedence rules and the trigger
evaluation are all exercised by tests before any real observation arrives. Shipping an
untested pipeline and calling it ready would be its own kind of dishonesty.

The fixtures deliberately include the awkward cases, because those are the ones that
matter: a utility record disagreeing with a facility walkthrough, a site with poor uptime
that must be held back regardless of how good its utilisation looks, and a site whose
observations are too short to satisfy the minimum observation window.
"""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data/observed/fixtures"

SYNTHETIC_NOTE = ("SYNTHETIC FIXTURE - fabricated for testing. Not an observation of any "
                  "real facility. Site ids SYN* are not project sites.")

CAPACITY_ROWS = [
    # a clean facility confirmation -> verified_facility
    dict(site_id="SYN001", observed_date="2026-09-01", method="facility_panel_schedule",
         service_capacity_kw=400, spare_capacity_kw="", measured_peak_kw="",
         source_org="SYNTHETIC facility", source_document="SYNTHETIC panel schedule A",
         observer="SYNTHETIC reviewer", verification_status="reviewed", notes=SYNTHETIC_NOTE),
    # utility beats facility on precedence...
    dict(site_id="SYN002", observed_date="2026-09-02", method="facility_walkthrough",
         service_capacity_kw=500, spare_capacity_kw=120, measured_peak_kw=310,
         source_org="SYNTHETIC facility", source_document="SYNTHETIC walkthrough note",
         observer="SYNTHETIC reviewer", verification_status="spot_checked", notes=SYNTHETIC_NOTE),
    # ...and disagrees with it, which must be surfaced rather than silently resolved
    dict(site_id="SYN002", observed_date="2026-09-10", method="utility_service_record",
         service_capacity_kw=450, spare_capacity_kw=90, measured_peak_kw="",
         source_org="SYNTHETIC utility", source_document="SYNTHETIC service record 77",
         observer="SYNTHETIC engineer", verification_status="reviewed", notes=SYNTHETIC_NOTE),
    # weaker evidence must not claim more than it supports
    dict(site_id="SYN003", observed_date="2026-09-03", method="comparable_site_proxy",
         service_capacity_kw=300, spare_capacity_kw="", measured_peak_kw="",
         source_org="SYNTHETIC planning", source_document="SYNTHETIC proxy note",
         observer="SYNTHETIC planner", verification_status="unreviewed", notes=SYNTHETIC_NOTE),
]


def session_rows(seed: int = 20260727) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    start = date(2026, 9, 1)
    # site: (days, ports, uptime, sessions/day, p90 wait)
    # Chosen so that every branch of triggers.evaluate is exercised, including the ones
    # that must REFUSE. A fixture where nothing ever qualifies would leave the expansion
    # path untested; a fixture where everything qualifies would leave the gates untested.
    profiles = {
        "SYN001": (210, 4, 0.99, 15.0, 14.0),  # healthy + strong demand -> expansion review
        "SYN002": (210, 4, 0.88, 15.0, 18.0),  # SAME demand, poor uptime -> must HOLD anyway
        "SYN003": (210, 4, 0.99, 1.2, 1.0),    # healthy, little demand -> hold
        "SYN004": (40, 2, 0.99, 15.0, 14.0),   # would qualify, but too short -> hold
        "SYN005": (210, 4, 0.99, 9.0, 4.0),    # middling: holds normally, passes on equity override
    }
    for site_id, (days, ports, uptime, per_day, wait) in profiles.items():
        for day in range(days):
            sessions = max(0.0, round(rng.gauss(per_day, per_day * 0.15), 2))
            dwell = round(rng.gauss(95, 12), 1)
            possible = ports * 12.0            # a 12-hour operating window
            available = round(possible * uptime, 2)
            rows.append(dict(
                site_id=site_id,
                date=(start + timedelta(days=day)).isoformat(),
                sessions=sessions,
                energy_kwh=round(sessions * 9.5, 2),
                mean_dwell_min=dwell,
                facility_visitors_day=int(rng.gauss(300, 40)),
                ports_in_service=ports,
                port_hours_available=available,
                port_hours_possible=possible,
                # Clamped to `sessions`. Drawn from an unrelated gaussian it exceeded the
                # session count on 13 of 880 rows -- a site-day with 0.96 sessions and 1
                # delayed. A fixture that cannot happen teaches the reader the wrong shape,
                # and any validator written against it inherits the impossibility.
                # FLOORED, not rounded. `sessions` is a fractional daily average and
                # `sessions_delayed` is an integer count, so rounding still produced
                # delayed=1 against sessions=0.96. Flooring guarantees
                # delayed <= floor(sessions) <= sessions for every row.
                sessions_delayed=int(min(math.floor(sessions),
                                         max(0, rng.gauss(sessions * 0.2, 1)))),
                wait_p90_min=round(max(0.0, rng.gauss(wait, wait * 0.2)), 1),
                observer="SYNTHETIC reviewer",
                source_system="SYNTHETIC network export",
            ))
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    cap = OUT / "synthetic_capacity_observations.csv"
    with open(cap, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(CAPACITY_ROWS[0]), lineterminator="\n")
        w.writeheader(); w.writerows(CAPACITY_ROWS)

    ses = OUT / "synthetic_session_observations.csv"
    rows = session_rows()
    with open(ses, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    print(f"wrote {cap.relative_to(REPO)} ({len(CAPACITY_ROWS)} rows)")
    print(f"wrote {ses.relative_to(REPO)} ({len(rows)} rows, "
          f"{len({r['site_id'] for r in rows})} synthetic sites)")
    print("Every row is fabricated. No row describes any real facility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
