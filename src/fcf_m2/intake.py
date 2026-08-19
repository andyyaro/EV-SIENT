"""Data intake: let a jurisdiction bring its own file, and never silently improve it.

What this is for
----------------
Today the model reads five files whose column names, units and coordinate frame are those of
one Northern Virginia study. `scoring.enrich_and_score` indexes 27 columns directly, so a file
missing one raises `KeyError: 'aadt_nearest'` - measured, not assumed. That is what makes this
a study rather than a product (DEC-000).

This module inserts one stage in front of the existing pipeline. A jurisdiction supplies
whatever shape it has; intake **proposes** a reading of it; a human sees the proposal and every
finding **before** anything runs; on acceptance the canonical frame is materialised and every
transformation is recorded.

The rule that shapes all of it
-----------------------------
**Cleaning must never silently improve data quality.**

Every inferred mapping, unit conversion, imputation, dropped row and substituted default is
recorded with its reason and surfaced in provenance. A transformation that cannot be explained
to the user in one sentence does not ship - so each one below carries that sentence, and the
`Finding.explain` field is not documentation, it is the thing shown to the person deciding.

The failure this guards against is not a crash. It is a run that succeeds on data nobody
inspected and produces numbers nobody can defend. A file with eight of twenty-seven fields
should yield a **run with low confidence**, not a refusal and not a confident answer.

Two things it deliberately will not do
--------------------------------------
**It will not reproject coordinates.** Doing that properly means `pyproj`; doing it by hand is
a transformation that cannot be explained in one sentence, and would silently move sites. A
non-geographic coordinate frame is therefore *refused with an explanation*, not guessed at.
Adding the dependency is its own decision (DEC-000 §open question), not something to smuggle in
here.

**It will not accept a mapping it merely suspects.** A column matched below the confidence
floor is reported as unmapped and the field is treated as absent. An absence is scored; a wrong
mapping is a wrong number with no trace.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .scoring import NUMERIC_FIELDS, YES_NO_FIELDS

#: Identity and geometry the model needs beyond the 27 scored fields.
IDENTITY_FIELDS = ["site_id", "site_name", "site_type", "lat", "lon"]

#: Confidence below which a proposed mapping is NOT offered as a match. A name that merely
#: rhymes with a canonical field is worse than an honest absence: the absence is scored and
#: visible, the bad match silently answers a question with the wrong column.
MATCH_FLOOR = 0.62

#: Known aliases per canonical field. Deliberately hand-written rather than inferred - a
#: fuzzy matcher that invents its own synonyms is a matcher nobody can audit.
ALIASES: dict[str, list[str]] = {
    "site_id": ["id", "siteid", "site_code", "facility_id", "asset_id"],
    "site_name": ["name", "facility", "facility_name", "location_name", "building"],
    "site_type": ["type", "category", "facility_type", "use", "building_type"],
    "lat": ["latitude", "y", "lat_dd", "ycoord"],
    "lon": ["longitude", "lng", "long", "x", "lon_dd", "xcoord"],
    "employees_day": ["employees", "staff", "staff_count", "workers", "fte"],
    "visitors_day": ["visitors", "daily_visitors", "footfall", "patrons", "visits_per_day"],
    "parking_spaces": ["parking", "spaces", "stalls", "parking_stalls", "spots"],
    "hours_open": ["hours", "open_hours", "operating_hours", "hours_per_day"],
    "avg_dwell_min": ["dwell", "dwell_time", "avg_dwell", "average_dwell_minutes"],
    "nearby_households_1mi": ["households", "households_1mi", "hh_1mi", "homes_nearby"],
    "nearby_jobs_1mi": ["jobs", "jobs_1mi", "employment_1mi", "jobs_nearby"],
    "aadt_nearest": ["aadt", "traffic", "traffic_count", "adt", "daily_traffic"],
    "amenities_count_0_5mi": ["amenities", "amenity_count", "poi_count", "services_nearby"],
    "ev_share_local": ["ev_share", "ev_penetration", "ev_pct", "ev_percentage"],
    "existing_l2_ports_1mi": ["l2_ports", "level2_ports", "existing_l2", "ac_ports"],
    "existing_dcfc_ports_3mi": ["dcfc_ports", "dc_fast_ports", "existing_dcfc", "dc_ports"],
    "equity_gap_index": ["equity", "equity_index", "equity_score", "disadvantage_index"],
    "spare_capacity_kw": ["spare_capacity", "available_capacity", "headroom_kw"],
    "distance_to_service_ft": ["service_distance", "distance_to_service", "run_length"],
    "trenching_ft": ["trenching", "trench_length", "trench_ft"],
    "trench_cost_per_ft": ["trench_cost", "trenching_cost", "cost_per_ft"],
    "service_upgrade_cost_usd": ["upgrade_cost", "service_upgrade", "electrical_upgrade_cost"],
    "elec_service_rating_amp": ["service_rating", "service_amps", "main_breaker", "amperage"],
    "fleet_vehicles": ["fleet", "fleet_count", "municipal_vehicles"],
    "public_access": ["public", "publicly_accessible", "open_to_public"],
    "ada_layout_possible": ["ada", "accessible_layout", "ada_possible"],
    "fire_access_ok": ["fire_access", "fire_ok", "emergency_access"],
    "garage_enclosed": ["enclosed", "garage", "is_garage", "structure_enclosed"],
    "emergency_disconnect_visible": ["disconnect_visible", "emergency_disconnect"],
    "stormwater_risk": ["stormwater", "flood_risk", "drainage_risk"],
    "battery_storage_flag": ["battery", "has_battery", "bess", "storage_present"],
}

#: Unit suffixes we can convert, and the factor to the canonical unit. Every conversion here
#: is a multiplication anyone can check - nothing that needs a projection or a lookup table.
UNIT_CONVERSIONS: dict[str, dict[str, float]] = {
    "distance_to_service_ft": {"_m": 3.280839895, "_metres": 3.280839895, "_meters": 3.280839895},
    "trenching_ft": {"_m": 3.280839895, "_metres": 3.280839895, "_meters": 3.280839895},
    "spare_capacity_kw": {"_w": 0.001, "_watts": 0.001, "_mw": 1000.0},
    "avg_dwell_min": {"_hr": 60.0, "_hours": 60.0, "_h": 60.0, "_sec": 1 / 60.0},
    "hours_open": {"_min": 1 / 60.0, "_minutes": 1 / 60.0},
}


#: Which confidence field group each INPUT field belongs to.
#:
#: Intake needs its own map. `provenance.FIELD_GROUP_FOR_COLUMN` is keyed on the *contract
#: output* columns and knows only 3 of the 32 fields read here, so relying on it put 29 fields
#: into `site_use_and_demand` by default. That group then inherited `missing` from the one
#: genuinely absent field and scored 0, while four other groups scored 0 for having no fields
#: at all. The overall verdict came out "Low", which was correct - and correct by accident,
#: which is not the same thing and would have hidden the next mistake.
FIELD_GROUP_FOR_INPUT: dict[str, str] = {
    # identity and access
    "site_id": "address_and_public_access",
    "site_name": "address_and_public_access",
    "site_type": "address_and_public_access",
    "public_access": "address_and_public_access",
    # geometry
    "lat": "coordinates",
    "lon": "coordinates",
    # the electrical fields, which gate feasibility and are weighted heaviest
    "elec_service_rating_amp": "electrical_service",
    "spare_capacity_kw": "electrical_service",
    "distance_to_service_ft": "electrical_service",
    "trenching_ft": "electrical_service",
    "trench_cost_per_ft": "electrical_service",
    "service_upgrade_cost_usd": "electrical_service",
    "emergency_disconnect_visible": "electrical_service",
    # surrounding context
    "equity_gap_index": "equity_and_context",
    "nearby_households_1mi": "equity_and_context",
    "nearby_jobs_1mi": "equity_and_context",
    "aadt_nearest": "equity_and_context",
    "amenities_count_0_5mi": "equity_and_context",
    "ev_share_local": "equity_and_context",
    "existing_l2_ports_1mi": "equity_and_context",
    "existing_dcfc_ports_3mi": "equity_and_context",
    # the physical site
    "parking_spaces": "parking_and_layout",
    "ada_layout_possible": "parking_and_layout",
    "garage_enclosed": "parking_and_layout",
    # review flags
    "fire_access_ok": "safety_review_fields",
    "stormwater_risk": "safety_review_fields",
    "battery_storage_flag": "safety_review_fields",
    # how the building is used
    "employees_day": "site_use_and_demand",
    "visitors_day": "site_use_and_demand",
    "fleet_vehicles": "site_use_and_demand",
    "hours_open": "site_use_and_demand",
    "avg_dwell_min": "site_use_and_demand",
}

SEVERITY_ORDER = {"refusal": 0, "warning": 1, "note": 2}


@dataclass(frozen=True)
class Finding:
    """One thing the reader must see before deciding, in a sentence they can act on."""

    severity: str                 # refusal | warning | note
    field: str
    explain: str                  # ONE sentence. If it needs two, the transformation is too clever.
    detail: str = ""

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_ORDER:
            raise ValueError(f"unknown severity {self.severity!r}")
        if not self.explain.strip():
            raise ValueError(
                f"finding for {self.field!r} has no explanation; a transformation that cannot "
                f"be explained to the user in one sentence does not ship (DEC-000)")


@dataclass
class Proposal:
    """What intake *would* do. Nothing is applied until this is accepted."""

    mapping: dict[str, str] = field(default_factory=dict)       # canonical -> supplied column
    conversions: dict[str, float] = field(default_factory=dict)  # canonical -> multiplier
    absent: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    row_count: int = 0

    @property
    def refused(self) -> bool:
        return any(f.severity == "refusal" for f in self.findings)

    @property
    def completeness(self) -> float:
        """Share of the fields the model scores that this file actually supplies."""
        total = len(NUMERIC_FIELDS) + len(YES_NO_FIELDS)
        return round(len(self.mapping and set(self.mapping) & _scored_fields()) / total, 4)

    def summary(self) -> str:
        by = {"refusal": 0, "warning": 0, "note": 0}
        for finding in self.findings:
            by[finding.severity] += 1
        return (f"{len(self.mapping)} of {len(_all_fields())} fields mapped, "
                f"{len(self.absent)} absent, {by['refusal']} refusal(s), "
                f"{by['warning']} warning(s), {by['note']} note(s)")


def _scored_fields() -> set[str]:
    return set(NUMERIC_FIELDS) | set(YES_NO_FIELDS)


def _all_fields() -> list[str]:
    return IDENTITY_FIELDS + list(NUMERIC_FIELDS) + list(YES_NO_FIELDS)


def _normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")



#: Unit suffixes stripped from a supplied column name BEFORE it is compared to a canonical one.
#:
#: A unit suffix is metadata about a column, not part of what the column means, and leaving it
#: in wrecks the comparison: `trench_length_m` against `trenching_ft` shares one token out of
#: five because `_m` and `_ft` are both counted as meaningful. Measured on the messy fixture,
#: `dwell_hr` failed to match `avg_dwell_min` at all and was reported absent while the file
#: plainly supplied it - an honest failure, but an avoidable one.
#:
#: Stripped for MATCHING only. The original name is still what the unit conversion is detected
#: from, so removing the suffix here cannot lose the conversion.
UNIT_SUFFIXES = ("_m", "_metres", "_meters", "_ft", "_feet", "_km", "_mi", "_miles",
                 "_kw", "_mw", "_w", "_watts", "_hr", "_hours", "_h", "_min", "_minutes",
                 "_sec", "_seconds", "_usd", "_dollars", "_pct", "_percent")


def _strip_units(name: str) -> str:
    normalised = _normalise(name)
    for suffix in sorted(UNIT_SUFFIXES, key=len, reverse=True):
        if normalised.endswith(suffix) and len(normalised) > len(suffix) + 1:
            return normalised[: -len(suffix)]
    return normalised


def _similarity(a: str, b: str) -> float:
    """Token overlap, not edit distance.

    `visitors_day` and `visitors_per_day` share their meaningful tokens; edit distance would
    score them poorly for the two characters that differ. Conversely `l2_ports` and `dc_ports`
    are one token apart and must NOT match, which token overlap handles and a character
    measure does not.
    """
    at, bt = set(_normalise(a).split("_")), set(_normalise(b).split("_"))
    if not at or not bt:
        return 0.0
    return len(at & bt) / len(at | bt)


def _detect_conversion(canonical: str, supplied: str) -> tuple[float, str] | None:
    """A unit multiplier implied by the supplied column's suffix, or None."""
    table = UNIT_CONVERSIONS.get(canonical)
    if not table:
        return None
    normalised = "_" + _normalise(supplied)
    for suffix, factor in table.items():
        if normalised.endswith(suffix):
            return factor, suffix.lstrip("_")
    return None


def propose(frame: pd.DataFrame) -> Proposal:
    """Read a supplied frame and say what intake WOULD do with it. Changes nothing.

    Separating the proposal from its application is the whole design. A user who cannot see
    what a mapping decided before it runs is being asked to trust a black box with the
    provenance of every number downstream.
    """
    proposal = Proposal(row_count=len(frame))
    supplied = list(frame.columns)
    taken: set[str] = set()

    for canonical in _all_fields():
        candidates = []
        for column in supplied:
            if column in taken:
                continue
            # Compared with unit suffixes removed from BOTH sides, so `trench_length_m` and
            # `trenching_ft` are judged on what they mean rather than on how they are measured.
            bare_column = _strip_units(column)
            bare_canonical = _strip_units(canonical)
            score = max(
                _similarity(bare_canonical, bare_column),
                max((_similarity(_strip_units(alias), bare_column)
                     for alias in ALIASES.get(canonical, [])), default=0.0),
            )
            if _normalise(column) == _normalise(canonical) or bare_column == bare_canonical:
                score = 1.0
            candidates.append((score, column))
        candidates.sort(reverse=True)

        if not candidates or candidates[0][0] < MATCH_FLOOR:
            proposal.absent.append(canonical)
            continue

        score, column = candidates[0]
        proposal.mapping[canonical] = column
        taken.add(column)

        if score < 1.0:
            proposal.findings.append(Finding(
                "warning", canonical,
                f"{canonical} was matched to the supplied column '{column}', which is a guess "
                f"based on the name and not a declared mapping.",
                detail=f"match confidence {score:.2f}"))

        conversion = _detect_conversion(canonical, column)
        if conversion:
            factor, unit = conversion
            proposal.conversions[canonical] = factor
            proposal.findings.append(Finding(
                "warning", canonical,
                f"{canonical} appears to be supplied in {unit} and every value will be "
                f"multiplied by {factor:g} to reach the unit the model expects.",
                detail=f"from column '{column}'"))

    for canonical in proposal.absent:
        if canonical in _scored_fields():
            proposal.findings.append(Finding(
                "note", canonical,
                f"{canonical} is not present in this file, so it will be scored as an absence "
                f"and will lower this jurisdiction's data confidence rather than being "
                f"substituted with a default."))

    _check_identity(frame, proposal)
    _check_coordinates(frame, proposal)
    proposal.findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.field))
    return proposal


def _check_identity(frame: pd.DataFrame, proposal: Proposal) -> None:
    """A file with no usable site identity cannot be ingested at all."""
    column = proposal.mapping.get("site_id")
    if column is None:
        proposal.findings.append(Finding(
            "refusal", "site_id",
            "No column in this file could be read as a site identifier, and rows that cannot "
            "be told apart cannot be scored, compared, or corrected later."))
        return
    values = frame[column].astype(str).str.strip()
    if values.duplicated().any():
        duplicates = sorted(values[values.duplicated()].unique())[:5]
        proposal.findings.append(Finding(
            "refusal", "site_id",
            "Site identifiers must be unique and this file repeats at least one, so two "
            "different places would be scored as the same site.",
            detail=f"repeated: {duplicates}"))
    if (values == "").any() or values.isin({"nan", "None"}).any():
        proposal.findings.append(Finding(
            "refusal", "site_id",
            "At least one row has no site identifier, and an unidentified row cannot be "
            "attributed to a place."))


def _check_coordinates(frame: pd.DataFrame, proposal: Proposal) -> None:
    """Refuse a non-geographic coordinate frame rather than guessing at it."""
    lat_col, lon_col = proposal.mapping.get("lat"), proposal.mapping.get("lon")
    if not lat_col or not lon_col:
        proposal.findings.append(Finding(
            "note", "lat/lon",
            "This file has no coordinates, so the map surfaces will be unavailable; every "
            "other calculation is unaffected."))
        return
    try:
        lat = pd.to_numeric(frame[lat_col], errors="coerce")
        lon = pd.to_numeric(frame[lon_col], errors="coerce")
    except Exception:
        return
    if lat.dropna().empty or lon.dropna().empty:
        return
    out_of_range = (lat.abs() > 90).any() or (lon.abs() > 180).any()
    if out_of_range:
        proposal.findings.append(Finding(
            "refusal", "lat/lon",
            "These coordinates are outside the range of latitude and longitude, so the file is "
            "in a projected coordinate system this tool will not convert - reprojecting it "
            "here would move every site by an amount nobody could check.",
            detail=(f"lat range [{lat.min():.1f}, {lat.max():.1f}], "
                    f"lon range [{lon.min():.1f}, {lon.max():.1f}]")))


@dataclass
class LedgerEntry:
    canonical_field: str
    action: str
    reason: str
    detail: str = ""


def apply(frame: pd.DataFrame, proposal: Proposal) -> tuple[pd.DataFrame, list[LedgerEntry]]:
    """Materialise the canonical frame described by an ACCEPTED proposal.

    Refuses if the proposal contains a refusal. The caller is expected to have shown the
    findings to a human first; this function's job is to make sure a refusal cannot be walked
    past by a caller that did not.
    """
    if proposal.refused:
        reasons = [f.explain for f in proposal.findings if f.severity == "refusal"]
        raise ValueError("this file cannot be ingested:\n  " + "\n  ".join(reasons))

    ledger: list[LedgerEntry] = []
    out = pd.DataFrame(index=range(len(frame)))

    for canonical in _all_fields():
        column = proposal.mapping.get(canonical)
        if column is None:
            # NOT defaulted. An absent field stays absent, is scored as an absence, and lowers
            # confidence. Substituting a plausible number here is precisely the silent
            # improvement DEC-000 forbids.
            out[canonical] = pd.NA
            ledger.append(LedgerEntry(
                canonical, "left absent",
                "not supplied in this file; scored as an absence rather than defaulted"))
            continue

        series = frame[column]
        if canonical in NUMERIC_FIELDS or canonical in ("lat", "lon"):
            series = pd.to_numeric(series, errors="coerce")
        factor = proposal.conversions.get(canonical)
        if factor:
            series = series * factor
            ledger.append(LedgerEntry(
                canonical, f"multiplied by {factor:g}",
                "supplied in a different unit from the one the model expects",
                detail=f"from column '{column}'"))
        out[canonical] = series.values
        if column != canonical:
            ledger.append(LedgerEntry(
                canonical, f"read from '{column}'",
                "column name differed from the canonical name"))

    return out, ledger


def provenance_rows(proposal: Proposal, site_ids: list[str], reviewer: str,
                    source_org: str, source_date: str) -> pd.DataFrame:
    """Typed provenance for the confidence system that already exists.

    Keyed per **site x field_group**, which is the shape `confidence.build_confidence` reads.
    Intake's decisions are column-level, so every site in one file gets the same assessment -
    that is correct, because the mapping that was guessed was guessed for all of them.

    Aggregated **pessimistically**: a field group takes the weakest source_class among its
    fields. A group containing one missing field cannot honestly claim to be fully sourced, and
    averaging would let a well-sourced field disguise an absent one. The same reasoning as the
    fail-closed capacity guard - the weakest evidence sets the claim.

    Absent fields are emitted as `missing`, never omitted. A field simply left out of the
    provenance table scores as though it had never been expected, which would make an
    incomplete file look exactly as trustworthy as a complete one.
    """
    # Weakest first: whichever appears earliest wins the group.
    RANK = ["missing", "unconfirmed", "planning_assumption", "derived_public_data",
            "public_web_reference", "official_source"]

    per_group: dict[str, dict[str, Any]] = {}
    for canonical in _all_fields():
        group = FIELD_GROUP_FOR_INPUT[canonical]
        mapped = canonical in proposal.mapping
        inferred = mapped and _strip_units(proposal.mapping[canonical]) != _strip_units(canonical)
        source_class = ("missing" if not mapped
                        else "unconfirmed" if inferred
                        else "public_web_reference")
        note = ("field not supplied" if not mapped
                else f"read from the supplied column '{proposal.mapping[canonical]}'; "
                     f"mapping inferred from its name" if inferred else "")

        current = per_group.get(group)
        if current is None or RANK.index(source_class) < RANK.index(current["source_class"]):
            per_group[group] = {"source_class": source_class, "assumption_type": note,
                                "weakest_field": canonical}
        elif note and not current["assumption_type"]:
            current["assumption_type"] = note

    rows = []
    for site_id in site_ids:
        for group, assessment in sorted(per_group.items()):
            rows.append({
                "site_id": site_id,
                "field_group": group,
                "source_class": assessment["source_class"],
                "verification_status": "unreviewed",
                "source_org": source_org,
                "source_date": source_date,
                "reviewer": reviewer,
                "assumption_type": assessment["assumption_type"],
                "unresolved_flag": "1" if assessment["source_class"] in
                                          ("missing", "unconfirmed") else "0",
            })
    return pd.DataFrame(rows)


def accept(provenance: pd.DataFrame) -> pd.DataFrame:
    """Record that a human reviewed and accepted the proposed mapping.

    What acceptance means, and the distinction that matters
    ------------------------------------------------------
    Accepting a proposal confirms **the mapping** - that `staff` really is the employee count
    this model means by `employees_day`. It says nothing whatever about **the data**: whether
    that count is accurate, current, or came from anywhere better than a guess.

    So acceptance clears the *mapping* uncertainty and nothing else. `verification_status`
    becomes `reviewed` and `unresolved_flag` clears for mapped fields, but `source_class`
    **does not improve**, because intake has no knowledge of where the jurisdiction's numbers
    came from and inventing one would be exactly the silent improvement this module exists to
    prevent.

    The first version did upgrade it, from `unconfirmed` to `public_web_reference`. Measured
    consequence: a messy third-party file with one missing field scored **58.5 (Medium)** while
    the real Northern Virginia study - whose electrical fields are genuinely unverified -
    scored **33.8 (Low)**. Guessed data outranked measured data. A jurisdiction wanting a
    higher rating must supply provenance for its own figures; there is no path to one through
    this function.
    """
    out = provenance.copy()
    out["verification_status"] = "reviewed"
    out["unresolved_flag"] = out["source_class"].map(
        lambda c: "1" if c == "missing" else "0")
    return out
