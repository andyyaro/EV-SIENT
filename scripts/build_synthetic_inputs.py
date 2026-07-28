#!/usr/bin/env python3
"""Generate a synthetic site-input set, so a public installer can run without real site data.

Why this exists
---------------
DEC-016 decided the real input data stays private and that any public installer ships a
synthetic set instead. That decision was made in July and the synthetic set was never built,
which made the public installer **unbuildable** rather than merely undone: `workflow.py` needs
`data/inputs/real_sites_v2.csv` to run at all, so a public artifact could only ever leak the
real data or fail to start.

The four files this produces are the complete set `_load_inputs()` reads. Building only the
sites table would have left three others still pointing at real sites.

What is and is not shared with the real data
-------------------------------------------
An earlier version of this docstring claimed **"nothing here is derived from the real files —
not copied, not perturbed, not sampled, not fitted to their distributions."** An adversarial
review showed that was false, and it was false in the way overclaims usually are: broadly
true, precisely wrong, and contradicted by a comment twelve lines further down that read
"Copied verbatim from the real file."

The accurate statement is narrower and worth reading carefully.

**Not shared — no facility is distinguishable.** No site id, name, address, postcode or
coordinate. No per-site measurement. No rank order, spacing, or correlation structure. No
row-to-row correspondence. Every facility-scale number is drawn from the ranges in `PROFILES`,
which are stated generic assumptions about what a public library or a county office is like —
argue with them, they are measurements of nothing.

**Shared, deliberately, and none of it distinguishes a facility:**

* **Schema vocabularies.** `site_type` is `library|office|public_safety|garage` and the seven
  provenance field groups are the seven the model reads. These must match or the model cannot
  parse the file. They describe the *format*, not any building.
* **Boolean and small-integer domains.** `public_access` is 0 or 1 in both. Twelve ranks are
  1..12 in both. This is arithmetic, not leakage.
* **The study's uniform conventions** — 480 V service, $150/ft trenching, the safety-review
  flags. These are identical across all twelve real rows *because they are assumptions the
  study adopted*, not measurements. Each is one fact that is true of every site equally, so it
  separates no site from any other.
* **The electrical placeholders**, `elec_service_rating_amp = 0` and `spare_capacity_kw = 0`.
  See below — these are load-bearing.

**Previously shared and now fixed.** The first version drew `avg_dwell_min`, the arrival
hours, the spare-capacity placeholders, the EV-share values and the electrical risk points from
`rng.choice` lists that were *exactly the real file's distinct values* — read off it while
exploring the schema. That is support-fitting: it publishes the precise set of values in use
across the twelve real facilities. The lists are now chosen independently and share no member
with the real ones. The risk free-text strings, previously copied verbatim, are reworded.

What is deliberately NOT randomised
-----------------------------------
Two groups of columns are copied as constants, and both are copied because they are *not*
facility data:

* **The electrical placeholders.** `elec_service_rating_amp = 0` and `spare_capacity_kw = 0`
  are what makes `capacity_basis` come out `placeholder` at every site — the study's central
  epistemic state and the condition the fail-closed capacity guard tests. Randomising them
  would make the synthetic run *more confident* than the real one, which is the one direction a
  fixture must never move.
* **The study's uniform assumptions** — 480 V service, $150/ft trenching, the safety-review
  flags. These are the same for every row in the real file because they are conventions the
  study adopted, not measurements of any building.

Honesty markers
---------------
Every site is `SYN0xx`, in a county that does not exist, with the state code `ZZ`, on a
coordinate grid that is not Northern Virginia. The provenance table records
`source_class = synthetic_model` for every field group, so a run against this data cannot claim an official source for anything. A reader who
sees a number from this set and goes looking for its provenance is told, in the provenance
system's own vocabulary, that it was invented.

Run: python scripts/build_synthetic_inputs.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data/synthetic"

#: Fixed so the set is reproducible. The value is arbitrary and carries no meaning.
SEED = 20260728

#: A coordinate grid deliberately placed where the study's sites are not. Kansas farmland,
#: chosen because it is unambiguously not Northern Virginia — a reader who plots these cannot
#: mistake them for the real candidates, and the site map's own axes auto-scale so the plot
#: still renders. The cached TIGER boundary overlay will not match, which is correct: these
#: are not places in that boundary.
GRID_LAT, GRID_LON = 38.5000, -98.0000


#: Categorical supports, chosen independently of the real data.
#:
#: The first version used [90, 120, 180, 240] for dwell and [7, 8, 10] / [11, 16, 17] for
#: arrival hours — which an adversarial review correctly identified as *exactly* the real
#: file's distinct values, because they had been read off it while exploring the schema. That
#: is support-fitting: it publishes the precise set of values in use across the twelve real
#: facilities, and it falsified this module's own claim that nothing was fitted.
#:
#: The FIRST attempt at the fix failed in a subtler way, and the same review caught it. The
#: replacement spare-capacity set [42.0, 63.0, 84.0, 168.0] was the real set scaled by exactly
#: 35/32 — every ratio 1.09375, both normalising to the multiplier vector {2, 3, 4, 8}. No
#: value matched, and the relative structure was preserved perfectly. That is *perturbation*,
#: which is the signature this module claims to avoid: a set that shares no member can still
#: share its shape. The current values have a different shape, not merely different members.
DWELL_CHOICES = [75, 105, 150, 210]
ARRIVAL_START_CHOICES = [6, 9, 11]
ARRIVAL_END_CHOICES = [14, 18, 19]
SPARE_PLACEHOLDER_CHOICES = [25.0, 60.0, 90.0, 130.0]

#: Generic profiles per facility type. Every range here is a stated assumption about what such
#: a building is like — argue with the numbers, they are not measurements of anything.
PROFILES = {
    "library": dict(
        employees=(8, 25), visitors=(150, 600), parking=(40, 120),
        hours=(8.0, 10.0), dwell=(90, 120), households=(2000, 9000),
        jobs=(1500, 12000), aadt=(6000, 28000), amenities=(4, 18),
        l2=(0, 6), dcfc=(0, 4), equity=(0.25, 0.80), dist_ft=(60, 260),
        upgrade=(45000, 120000)),
    "office": dict(
        employees=(60, 320), visitors=(80, 420), parking=(120, 420),
        hours=(8.0, 9.5), dwell=(180, 240), households=(1200, 7000),
        jobs=(4000, 26000), aadt=(9000, 42000), amenities=(3, 14),
        l2=(0, 8), dcfc=(0, 6), equity=(0.20, 0.75), dist_ft=(80, 320),
        upgrade=(60000, 165000)),
    "public_safety": dict(
        employees=(20, 70), visitors=(15, 90), parking=(45, 140),
        hours=(24.0, 24.0), dwell=(120, 180), households=(600, 4500),
        jobs=(800, 6000), aadt=(3000, 16000), amenities=(1, 8),
        l2=(0, 3), dcfc=(0, 2), equity=(0.30, 0.85), dist_ft=(100, 380),
        upgrade=(70000, 180000)),
    "garage": dict(
        employees=(4, 14), visitors=(200, 900), parking=(250, 700),
        hours=(12.0, 16.0), dwell=(180, 240), households=(2500, 11000),
        jobs=(6000, 30000), aadt=(12000, 48000), amenities=(6, 22),
        l2=(2, 12), dcfc=(0, 8), equity=(0.15, 0.65), dist_ft=(40, 200),
        upgrade=(50000, 140000)),
}

#: Twelve invented facilities in an invented county. The names are generic on purpose — a
#: memorable fake name is a fake name someone repeats as though it were real.
SITES = [
    ("SYN001", "Northgate Branch Library", "library", 0),
    ("SYN002", "Riverbend Branch Library", "library", 0),
    ("SYN003", "Eastfield Branch Library", "library", 0),
    ("SYN004", "County Administration Building", "office", 0),
    ("SYN005", "Public Works Operations Centre", "office", 0),
    ("SYN006", "Health and Human Services Centre", "office", 0),
    ("SYN007", "Westmark Community Centre", "office", 0),
    ("SYN008", "Fire and Rescue Station 12", "public_safety", 0),
    ("SYN009", "Emergency Operations Centre", "public_safety", 0),
    ("SYN010", "Civic Centre Parking Structure", "garage", 1),
    ("SYN011", "Transit Centre Parking Structure", "garage", 1),
    ("SYN012", "Fairground Parking Structure", "garage", 0),
]

#: Copied verbatim from the real file and NOT randomised — see the module docstring. These are
#: the study's uniform conventions and its electrical placeholders, neither of which is a
#: measurement of any building.
CONSTANTS = {
    "state": "ZZ", "fleet_vehicles": "0", "elec_service_voltage": "480",
    "elec_service_rating_amp": "0", "spare_capacity_kw": "0",
    "trench_cost_per_ft": "150", "ada_layout_possible": "1", "fire_access_ok": "1",
    "emergency_disconnect_visible": "0", "stormwater_risk": "0",
    "battery_storage_flag": "0", "battery_storage_kwh": "0",
}

SITE_COLUMNS = [
    "site_id", "site_name", "site_type", "address", "city", "state", "zip", "lat", "lon",
    "public_access", "employees_day", "visitors_day", "fleet_vehicles", "parking_spaces",
    "hours_open", "avg_dwell_min", "nearby_households_1mi", "nearby_jobs_1mi",
    "aadt_nearest", "amenities_count_0_5mi", "ev_registrations_local", "ev_share_local",
    "existing_l2_ports_1mi", "existing_dcfc_ports_3mi", "equity_gap_index",
    "elec_service_voltage", "elec_service_rating_amp", "spare_capacity_kw",
    "distance_to_service_ft", "trenching_ft", "trench_cost_per_ft",
    "service_upgrade_cost_usd", "ada_layout_possible", "fire_access_ok", "garage_enclosed",
    "emergency_disconnect_visible", "stormwater_risk", "battery_storage_flag",
    "battery_storage_kwh", "notes",
]

FIELD_GROUPS = ["address_and_public_access", "coordinates", "electrical_service",
                "equity_and_context", "parking_and_layout", "safety_review_fields",
                "site_use_and_demand"]


def build_sites(rng: random.Random) -> list[dict]:
    rows = []
    for index, (site_id, name, site_type, enclosed) in enumerate(SITES):
        p = PROFILES[site_type]
        row = dict(CONSTANTS)
        row.update({
            "site_id": site_id,
            "site_name": name,
            "site_type": site_type,
            "address": f"{100 + index * 37} Example Road",
            "city": "Springfield Township",
            "zip": f"{60000 + index}",
            # A regular grid, not scattered — a reader should be able to tell at a glance that
            # these coordinates were generated rather than surveyed.
            "lat": f"{GRID_LAT + (index // 4) * 0.045:.5f}",
            "lon": f"{GRID_LON + (index % 4) * 0.055:.5f}",
            "public_access": "1" if site_type != "public_safety" else "0",
            "employees_day": rng.randint(*p["employees"]),
            "visitors_day": rng.randint(*p["visitors"]),
            "parking_spaces": rng.randint(*p["parking"]),
            "hours_open": f"{rng.uniform(*p['hours']):.2f}",
            "avg_dwell_min": rng.choice(DWELL_CHOICES),
            "nearby_households_1mi": rng.randint(*p["households"]),
            "nearby_jobs_1mi": rng.randint(*p["jobs"]),
            "aadt_nearest": rng.randint(*p["aadt"]),
            "amenities_count_0_5mi": rng.randint(*p["amenities"]),
            "ev_registrations_local": rng.choice([1500, 2050, 2900]),
            "ev_share_local": rng.choice(["0.0165", "0.0242", "0.0307"]),
            "existing_l2_ports_1mi": rng.randint(*p["l2"]),
            "existing_dcfc_ports_3mi": rng.randint(*p["dcfc"]),
            "equity_gap_index": f"{rng.uniform(*p['equity']):.3f}",
            "distance_to_service_ft": rng.randrange(*p["dist_ft"], 20),
            "garage_enclosed": str(enclosed),
            "service_upgrade_cost_usd": rng.randrange(*p["upgrade"], 5000),
            "notes": "SYNTHETIC FIXTURE — invented facility, not a real place. "
                     "Generated by scripts/build_synthetic_inputs.py for public distribution "
                     "under DEC-016. No value here describes any actual building.",
        })
        # Trenching follows service distance, as it must physically.
        row["trenching_ft"] = row["distance_to_service_ft"]
        rows.append({c: row[c] for c in SITE_COLUMNS})
    return rows


def build_risk_summary(sites: list[dict], rng: random.Random) -> list[dict]:
    """The legacy V2 electrical-risk table. Every site's risk reason states the same thing the
    real study states — that the electrical service is unknown — because that is true of the
    synthetic set too: its capacity fields are placeholders."""
    # Worded here rather than copied. The real file's risk strings were reproduced verbatim in
    # the first version; they say the same thing, but publishing the study's exact phrasing is
    # republishing its text, and the review flagged it.
    reason = ("service rating not established for this synthetic site; spare capacity not "
              "established; disconnect visibility not established")
    needed = ("establish service rating; establish spare capacity or upgrade requirement; "
              "establish disconnect location and visibility")
    scored = []
    for site in sites:
        base = rng.uniform(24.0, 60.0)
        scored.append((site, base))
    scored.sort(key=lambda t: -t[1])

    rows = []
    for rank, (site, base) in enumerate(scored, start=1):
        enclosed = site["garage_enclosed"] == "1"
        points = 12.5 if enclosed else rng.choice([4.5, 7.5])
        rows.append({
            "site_id": site["site_id"],
            "site_name": site["site_name"],
            "base_rank": rank,
            "base_readiness_score": f"{base:.1f}",
            "electrical_risk_level": "high" if points >= 9 else "medium",
            "electrical_risk_points": f"{points:.1f}",
            "optimistic_rank": rank,
            "expected_rank": rank,
            "conservative_rank": rank,
            "optimistic_score": f"{base - 1.0:.1f}",
            "expected_score": f"{base - 3.0:.1f}",
            "conservative_score": f"{base - 8.0:.1f}",
            "worst_case_rank_change": 0,
            "electrical_risk_reason": reason + ("; enclosed-structure context adds review risk" if enclosed else ""),
            "electrical_data_needed_next": needed + ("; establish enclosed-structure requirements" if enclosed else ""),
        })
    rows.sort(key=lambda r: r["site_id"])
    return rows


def build_matlab_meta(sites: list[dict], rng: random.Random) -> list[dict]:
    """Base loads and spare capacity are labelled UNVERIFIED PLANNING PROXIES in the real file
    and are exactly that here. The wording is preserved so the platform's caveat for
    `base_load_kw` still applies verbatim to a synthetic run."""
    rows = []
    for site in sites:
        mean = rng.uniform(45.0, 130.0)
        rows.append({
            "site_id": site["site_id"],
            "arrival_start_hr": rng.choice(ARRIVAL_START_CHOICES),
            "arrival_end_hr": rng.choice(ARRIVAL_END_CHOICES),
            "base_load_mean_kw": f"{mean:.1f}",
            "base_load_peak_kw": f"{mean * rng.uniform(1.05, 1.35):.1f}",
            "spare_capacity_kw_placeholder": f"{rng.choice(SPARE_PLACEHOLDER_CHOICES):.1f}",
            "provenance": "SYNTHETIC planning placeholder generated for public distribution "
                          "(DEC-016); base loads and spare capacity are INVENTED and describe "
                          "no real building",
        })
    return rows


def build_field_provenance(sites: list[dict]) -> list[dict]:
    """Every field group of every synthetic site is recorded as `synthetic`.

    This is the file that makes the whole set honest downstream. The confidence system reads
    `source_class` and `verification_status`; recording an official source for invented data
    would let a synthetic run report the same confidence as a real one. It reports lower,
    because it is worth less.
    """
    rows = []
    for site in sites:
        for group in FIELD_GROUPS:
            rows.append({
                "site_id": site["site_id"],
                "field_group": group,
                # The model's OWN vocabulary, not an invented one. `confidence.py` scores
                # source_class against a fixed table and REFUSED an unrecognised value —
                # correctly, since an unknown class would otherwise score 0 silently.
                # `synthetic_model` already existed and is worth 30, below planning_assumption
                # (35) and above unconfirmed (15), which is the right place for invented data.
                "source_class": "synthetic_model",
                "verification_status": "unreviewed",
                "source_org": "generated fixture (scripts/build_synthetic_inputs.py)",
                "source_date": "2026-07-28",
                "reviewer": "synthetic_fixture",
                "assumption_type": "invented value; describes no real facility",
                "unresolved_flag": "1",
            })
    return rows


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = columns or list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rng = random.Random(SEED)
    sites = build_sites(rng)
    risk = build_risk_summary(sites, rng)
    meta = build_matlab_meta(sites, rng)
    provenance = build_field_provenance(sites)

    write_csv(OUT / "synthetic_sites_v2.csv", sites, SITE_COLUMNS)
    write_csv(OUT / "synthetic_v2_electrical_risk_summary.csv", risk)
    write_csv(OUT / "synthetic_matlab_site_meta.csv", meta)
    write_csv(OUT / "synthetic_field_provenance_v1.csv", provenance)

    (OUT / "README.md").write_text(
        "# Synthetic site inputs — invented data, for public distribution\n\n"
        # This paragraph used to say "nothing here was derived from the real inputs -- not
        # copied, not perturbed, not fitted to their distributions." That is the exact
        # overclaim the module docstring above records as having been disproved by adversarial
        # review, and it was still being written into every public bundle. The accurate
        # statement is narrower, so it is the narrower one that ships.
        "**No file here describes any real building.** No site id, name, address, postcode or\n"
        "coordinate; no per-site measurement; no rank order, spacing or correlation structure;\n"
        "no row-to-row correspondence with the real study. Every facility-scale number is drawn\n"
        "from generic stated assumptions about what a public library or county office is like,\n"
        "written down in `scripts/build_synthetic_inputs.py` where they can be argued with.\n\n"
        "**What IS shared with the real files, deliberately, none of it distinguishing a\n"
        "facility:** the schema vocabularies (the model cannot parse a file that uses others);\n"
        "boolean and small-integer domains (0/1 flags, ranks 1..12 — arithmetic, not leakage);\n"
        "the study's uniform conventions such as 480 V service and $150/ft trenching, which are\n"
        "identical across all twelve real rows *because they are assumptions the study adopted*,\n"
        "so each separates no site from any other; and the electrical placeholders\n"
        "(`elec_service_rating_amp = 0`, `spare_capacity_kw = 0`), which must be preserved or\n"
        "the fail-closed capacity guard would stop firing.\n\n"
        "It exists because DEC-016 requires a public installer to ship synthetic inputs\n"
        "rather than the twelve real facilities' data, and `workflow.py` cannot run without\n"
        "*some* site table.\n\n"
        "## What is NOT randomised, and why\n\n"
        "- `elec_service_rating_amp = 0` and `spare_capacity_kw = 0` are kept as placeholders.\n"
        "  They are what makes `capacity_basis` come out `placeholder` at every site. A\n"
        "  fixture that invented electrical capacity would make the synthetic run **more\n"
        "  confident** than the real one — the one direction a fixture must never move.\n"
        "- The study's uniform conventions (480 V, $150/ft trenching, the safety-review\n"
        "  flags) are the same for every real row because they are assumptions, not\n"
        "  measurements.\n\n"
        "## Honesty markers\n\n"
        "Site ids are `SYN001`–`SYN012`. The county does not exist. The coordinate grid is\n"
        "not Northern Virginia, so a site map drawn from this data cannot be mistaken for the\n"
        "real candidates. Every field group is recorded with `source_class = synthetic`, so a\n"
        "reader who follows any number to its provenance is told it was invented.\n\n"
        "Regenerate with `python scripts/build_synthetic_inputs.py` (seeded, reproducible).\n")

    print(f"wrote {OUT.relative_to(REPO)}/")
    for name, rows in [("synthetic_sites_v2.csv", sites),
                       ("synthetic_v2_electrical_risk_summary.csv", risk),
                       ("synthetic_matlab_site_meta.csv", meta),
                       ("synthetic_field_provenance_v1.csv", provenance)]:
        print(f"  {name:44} {len(rows):3} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
