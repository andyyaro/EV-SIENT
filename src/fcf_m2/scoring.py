"""Site readiness scoring.

Two normalization regimes:

- ``legacy_v2``: cohort-relative min-max (exact port of the accepted V2 baseline).
- ``milestone2_v3``: fixed benchmark anchors (PY-02) from a versioned anchor set,
  with controlled cohort fallback for un-anchored fields. The same site receives
  the same score regardless of which other sites are in the run.

Subscore weights, the EV-share benchmark, the demand formula, and the port chooser
are identical in both modes; only normalization differs (plus the V3 confidence
layer, which lives in confidence.py).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (ANCHOR_SET_VERSION, DEMAND_COEFFICIENTS, DEMAND_FLOOR_SESSIONS, MODE_LEGACY,
                     MODE_V3, TIER1_MAX_RANK, TIER1_MIN_SCORE, TIER2_MIN_SCORE)
from .queueing import choose_ports

EV_SHARE_HIGH_BENCHMARK = 0.10

# --- Scoring weights -----------------------------------------------------------
# These were inline numeric literals inside the formula below, which meant the 3D
# explorer's driver attribution mirrored them by hand: the two agreed only because
# somebody kept them in step. Naming them here makes this module the single source,
# so fcf3d.build_sites imports them and a drift gate can prove they still match.
# The values are unchanged -- this is a refactor, not a re-weighting.

SUBSCORE_WEIGHTS: dict[str, float] = {
    "demand_subscore": 0.45,
    "feasibility_subscore": 0.30,
    "safety_subscore": 0.15,
    "equity_subscore": 0.10,
}

# Per-driver weights within each subscore. Each block sums to 1.00.
# "invert" marks the terms the formula wraps in (1 - x): lower raw is better.
DEMAND_WEIGHTS: dict[str, float] = {
    "nearby_households_1mi_n": 0.18,
    "nearby_jobs_1mi_n": 0.18,
    "aadt_nearest_n": 0.13,
    "amenities_count_0_5mi_n": 0.11,
    "parking_spaces_n": 0.10,
    "hours_open_n": 0.08,
    "avg_dwell_min_n": 0.07,
    "ev_share_local_n": 0.08,
    "existing_ports_total_n": 0.07,
}
FEASIBILITY_WEIGHTS: dict[str, float] = {
    "spare_capacity_kw_n": 0.35,
    "distance_to_service_ft_n": 0.25,
    "install_cost_est_usd_n": 0.25,
    "trenching_ft_n": 0.15,
}
SAFETY_WEIGHTS: dict[str, float] = {
    "ada_layout_possible": 0.35,
    "fire_access_ok": 0.35,
    "garage_enclosed": 0.15,
    "emergency_disconnect_visible": 0.10,
    "stormwater_risk": 0.05,
}
EQUITY_WEIGHTS: dict[str, float] = {"equity_gap_index_n": 1.00}

DRIVER_WEIGHTS: dict[str, dict[str, float]] = {
    "demand_subscore": DEMAND_WEIGHTS,
    "feasibility_subscore": FEASIBILITY_WEIGHTS,
    "safety_subscore": SAFETY_WEIGHTS,
    "equity_subscore": EQUITY_WEIGHTS,
}

# Terms the formula applies as (1 - x).
INVERTED_DRIVERS: frozenset[str] = frozenset({
    "existing_ports_total_n", "distance_to_service_ft_n", "install_cost_est_usd_n",
    "trenching_ft_n", "garage_enclosed", "stormwater_risk",
})

YES_NO_FIELDS = [
    "public_access", "ada_layout_possible", "fire_access_ok", "garage_enclosed",
    "emergency_disconnect_visible", "stormwater_risk", "battery_storage_flag",
]

NUMERIC_FIELDS = [
    "employees_day", "visitors_day", "fleet_vehicles", "parking_spaces", "hours_open",
    "avg_dwell_min", "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest",
    "amenities_count_0_5mi", "ev_share_local", "existing_l2_ports_1mi",
    "existing_dcfc_ports_3mi", "equity_gap_index", "spare_capacity_kw",
    "distance_to_service_ft", "trenching_ft", "trench_cost_per_ft",
    "service_upgrade_cost_usd", "elec_service_rating_amp",
]

NORMALIZE_COLS = [
    "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest", "amenities_count_0_5mi",
    "parking_spaces", "avg_dwell_min", "existing_ports_total", "spare_capacity_kw",
    "distance_to_service_ft", "trenching_ft", "install_cost_est_usd", "equity_gap_index",
]


#: Cell text that means "nobody recorded this". Read as ABSENT - never as "no", never as 0.
#: Shared with intake, which reports every such cell as a finding before anything runs.
TEXT_NULLS = frozenset({
    "", "na", "n/a", "n.a.", "nan", "none", "null", "unknown", "unk", "-", "--", "?", "tbd",
    "not known", "not assessed", "not recorded",
})
YES_TOKENS = frozenset({"1", "1.0", "y", "yes", "true", "t"})
NO_TOKENS = frozenset({"0", "0.0", "n", "no", "false", "f"})

#: Port sizing needs an operating day and a session length even where a file has none. These
#: are the values the sizing code already declared as its own defaults
#: (`right_sizing.ports_for_sessions`), and they are LABELLED: a site that used one lists the
#: field in `absent_fields`, and the readiness score gives the field no credit. Until
#: 2026-10-17 an absent `hours_open` became 0, which the queue model reads as all of a day's
#: sessions arriving in one hour - the largest port plan any site could get.
SIZING_DEFAULTS: dict[str, float] = {"hours_open": 8.0, "avg_dwell_min": 120.0}


class FlagValueError(ValueError):
    """A yes/no field carried something that is neither yes, no, nor a recognisable blank."""


class FieldValueError(ValueError):
    """A numeric field carried text that is neither a number nor a recognisable blank."""


def yesno_to_num(value, field: str = "yes/no field") -> float:
    """Map a yes/no field to 1.0 (yes), 0.0 (no) or NaN (not recorded). Refuses anything else.

    **Not recorded is not "no" (DEC-011, decided 2026-10-17).** A blank cell, or text such as
    ``n/a`` or ``unknown``, returns NaN, and ``enrich_and_score`` gives an unrecorded flag no
    credit in either direction. It used to return 0.0, and for ``garage_enclosed`` and
    ``stormwater_risk``, which score as ``1 - x``, that meant an unrecorded hazard earned the
    maximum safety credit. A string that is none of these - ``"banana"``, ``"partial"``,
    ``"0.5"`` - is refused, as a numeric 0.5 already was; it used to become 0.0, so a typo
    silently answered "no".

    The numeric branch used to ``return float(value)`` for *any* int or float, unclamped.
    Two consequences, both reproduced before this was changed:

    * ``0.5``, ``7`` and ``-3`` passed straight through into a subscore whose weights assume
      the term is 0 or 1. A value of 7 on ``fire_access_ok`` contributes seven times the
      weight the rubric allocates to fire access.
    * The same value answered differently depending on its type: ``0.5`` → ``0.5``, but the
      string ``"0.5"`` → ``0.0``, because the string branch is strictly binary. Whether a
      CSV cell parsed as text or as a number silently changed the score.

    It refuses rather than clamping. Clamping 7 to 1 would be a cleaner that quietly improves
    data - the thing this project exists not to do - and it would hide the upstream mistake
    that produced a 7. All 12 current sites carry strictly 0/1 in every flag, so **no
    published number moves**; this closes the door before Phase 6B opens it to data nobody
    here prepared.
    """
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return float("nan")
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        as_float = float(value)
        if as_float in (0.0, 1.0):
            return as_float
        raise FlagValueError(
            f"{field}: {value!r} is not a yes/no value. Expected 0 or 1. A flag outside "
            f"that set is not clamped, because clamping would silently improve the data and "
            f"hide whatever produced the value.")
    text = str(value).strip().lower()
    if text in YES_TOKENS:
        return 1.0
    if text in NO_TOKENS:
        return 0.0
    if text in TEXT_NULLS:
        return float("nan")
    raise FlagValueError(
        f"{field}: {value!r} is not a yes/no value. Expected yes/no, 1/0 or true/false, or "
        f"a blank cell where nobody knows. It is refused rather than read as \"no\", because "
        f"guessing would decide the answer for whoever wrote it.")


def to_numeric_strict(series: pd.Series, field: str) -> pd.Series:
    """Numbers stay numbers, recognisable blanks become NaN, and any other text is refused.

    ``pd.to_numeric(errors="coerce")`` turned ``"1,400"`` visitors, ``"n/a"`` staff and a typo
    alike into NaN, then the NaN into 0, with no record anywhere (F-07). Intake now parses and
    reports each such cell before a run; this is the backstop for a table that reaches the
    model without passing through intake. A numeric column is returned unchanged.
    """
    out = pd.to_numeric(series, errors="coerce")
    if out.isna().sum() == series.isna().sum():
        return out
    text = series.astype(str).str.strip().str.lower()
    bad = out.isna() & series.notna() & ~text.isin(TEXT_NULLS)
    if bad.any():
        rows = [int(i) + 2 for i in np.flatnonzero(bad.to_numpy())[:5]]
        raise FieldValueError(
            f"{field}: {series[bad].iloc[0]!r} is not a number (file row(s) {rows}, counting "
            f"the header as row 1). Run the file through intake, which reads thousands "
            f"separators and reports every cell it changes, or leave the cell blank.")
    return out


def minmax(series: pd.Series) -> pd.Series:
    """Legacy cohort-relative 0-1 scaling, over the values that were recorded.

    An absent value stays NaN rather than entering the range as 0. As a 0 it used to stretch
    the cohort's minimum, which moved every OTHER site's normalised value - one site's gap
    changed its neighbours' scores. On a complete table this is the original arithmetic.
    """
    s = pd.to_numeric(series, errors="coerce")
    lo, hi = s.min(), s.max()
    if not hi > lo:
        return pd.Series(np.where(s.isna(), np.nan, 0.0), index=s.index)
    return (s - lo) / (hi - lo)


def bounded_signal(series: pd.Series, high_benchmark: float) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return (s / high_benchmark).clip(lower=0, upper=1)


def load_anchor_set(path: str | Path) -> dict:
    with open(path) as f:
        data = json.load(f)
    if data.get("anchor_set_version") != ANCHOR_SET_VERSION:
        raise ValueError(
            f"Anchor set version mismatch: file has {data.get('anchor_set_version')!r}, "
            f"code expects {ANCHOR_SET_VERSION!r}"
        )
    return data


def anchored(series: pd.Series, lo: float, hi: float) -> pd.Series:
    """Fixed-anchor 0-1 scaling: independent of the cohort. An absent value stays NaN."""
    s = pd.to_numeric(series, errors="coerce")
    if hi <= lo:
        return pd.Series(np.where(s.isna(), np.nan, 0.0), index=s.index)
    return ((s - lo) / (hi - lo)).clip(lower=0.0, upper=1.0)


def normalize_fields(df: pd.DataFrame, mode: str, anchor_set: dict | None,
                     absent: dict[str, pd.Series] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Return df with *_n columns plus the list of fields that used cohort fallback.

    ``absent`` marks values nobody recorded; their *_n is NaN, and the formula gives a NaN
    term no credit. Without it every value is taken as recorded, which was the only case
    before 2026-10-17.
    """
    fallback_fields: list[str] = []
    anchors = (anchor_set or {}).get("anchors", {})
    for col in NORMALIZE_COLS:
        values = df[col].mask(absent[col]) if absent and col in absent else df[col]
        if mode == MODE_LEGACY:
            df[col + "_n"] = minmax(values)
        else:
            a = anchors.get(col)
            if a is None:
                df[col + "_n"] = minmax(values)
                fallback_fields.append(col)
            else:
                df[col + "_n"] = anchored(values, a["lo"], a["hi"])
    return df, fallback_fields


def expected_sessions(df: pd.DataFrame) -> pd.Series:
    """Legacy demand formula (synthetic, uncalibrated - see demand.py for status/calibration)."""
    c = DEMAND_COEFFICIENTS
    sessions = (
        c["visitors_day"] * df["visitors_day"]
        + c["employees_day"] * df["employees_day"]
        + c["nearby_jobs_1mi"] * df["nearby_jobs_1mi"]
        + c["nearby_households_1mi"] * df["nearby_households_1mi"] * (1 + df["ev_share_local"])
    )
    return sessions.clip(lower=DEMAND_FLOOR_SESSIONS)


def enrich_and_score(sites: pd.DataFrame, mode: str = MODE_LEGACY, anchor_set: dict | None = None) -> pd.DataFrame:
    """Score sites. In legacy mode this is numerically identical to the V2 baseline."""
    if mode == MODE_V3 and anchor_set is None:
        raise ValueError("milestone2_v3 mode requires a loaded anchor set")

    df = sites.copy()

    # Absence is recorded BEFORE anything is filled in, because afterwards it cannot be seen.
    absent: dict[str, pd.Series] = {}
    for col in YES_NO_FIELDS:
        # Field name passed through so a refusal says WHICH flag was wrong, not just that
        # one was. "banana is not a yes/no value" is useless when there are seven flags.
        # An unrecorded flag stays NaN in the output: it is not "no" (DEC-011).
        df[col] = df[col].apply(lambda v, c=col: yesno_to_num(v, c))
        absent[col] = df[col].isna()
    for col in NUMERIC_FIELDS:
        df[col] = to_numeric_strict(df[col], col)
        absent[col] = df[col].isna()
        # Filled so the arithmetic below can run - 0, or a labelled sizing default - but the
        # absence mask, not the filled value, decides the score.
        df[col] = df[col].fillna(SIZING_DEFAULTS.get(col, 0))

    # An unrecorded public_access is not public access: NaN >= 1 is False.
    df["access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.35)
    df["readiness_access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.65)

    df["install_cost_est_usd"] = df["trenching_ft"] * df["trench_cost_per_ft"] + df["service_upgrade_cost_usd"]
    df["existing_ports_total"] = df["existing_l2_ports_1mi"] + df["existing_dcfc_ports_3mi"]
    # A total with an unrecorded part is itself unrecorded.
    absent["install_cost_est_usd"] = (absent["trenching_ft"] | absent["trench_cost_per_ft"]
                                      | absent["service_upgrade_cost_usd"])
    absent["existing_ports_total"] = absent["existing_l2_ports_1mi"] | absent["existing_dcfc_ports_3mi"]

    df, fallback_fields = normalize_fields(df, mode, anchor_set, absent)
    df["ev_share_local_n"] = bounded_signal(df["ev_share_local"].mask(absent["ev_share_local"]),
                                            EV_SHARE_HIGH_BENCHMARK)

    # hours_open has no persisted _n column; the formula normalises it inline.
    # fcf3d.build_sites reconstructs the same term, so keep the two in step.
    df["hours_open_n"] = df["hours_open"].mask(absent["hours_open"]).clip(lower=0, upper=24) / 24

    # DEC-011, decided 2026-10-17: a value nobody recorded earns NO credit, in either direction.
    # For most terms that is what filling with 0 always did. For the six inverted terms it was
    # the opposite: `1 - 0` is the maximum, so a site with no stormwater assessment scored as if
    # one had been done and found no risk, and an unmeasured trench scored as the shortest
    # possible. On a table with no gaps both helpers are the original arithmetic exactly.
    def credit(col: str) -> pd.Series:
        return df[col].fillna(0)

    def inverse_credit(col: str) -> pd.Series:
        return (1 - df[col]).fillna(0)

    df["demand_subscore"] = 100 * (
        DEMAND_WEIGHTS["nearby_households_1mi_n"] * credit("nearby_households_1mi_n")
        + DEMAND_WEIGHTS["nearby_jobs_1mi_n"] * credit("nearby_jobs_1mi_n")
        + DEMAND_WEIGHTS["aadt_nearest_n"] * credit("aadt_nearest_n")
        + DEMAND_WEIGHTS["amenities_count_0_5mi_n"] * credit("amenities_count_0_5mi_n")
        + DEMAND_WEIGHTS["parking_spaces_n"] * credit("parking_spaces_n")
        + DEMAND_WEIGHTS["hours_open_n"] * credit("hours_open_n")
        + DEMAND_WEIGHTS["avg_dwell_min_n"] * credit("avg_dwell_min_n")
        + DEMAND_WEIGHTS["ev_share_local_n"] * credit("ev_share_local_n")
        + DEMAND_WEIGHTS["existing_ports_total_n"] * inverse_credit("existing_ports_total_n")
    )
    df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]

    df["feasibility_subscore"] = 100 * (
        FEASIBILITY_WEIGHTS["spare_capacity_kw_n"] * credit("spare_capacity_kw_n")
        + FEASIBILITY_WEIGHTS["distance_to_service_ft_n"] * inverse_credit("distance_to_service_ft_n")
        + FEASIBILITY_WEIGHTS["install_cost_est_usd_n"] * inverse_credit("install_cost_est_usd_n")
        + FEASIBILITY_WEIGHTS["trenching_ft_n"] * inverse_credit("trenching_ft_n")
    )

    df["safety_subscore"] = 100 * (
        SAFETY_WEIGHTS["ada_layout_possible"] * credit("ada_layout_possible")
        + SAFETY_WEIGHTS["fire_access_ok"] * credit("fire_access_ok")
        + SAFETY_WEIGHTS["garage_enclosed"] * inverse_credit("garage_enclosed")
        + SAFETY_WEIGHTS["emergency_disconnect_visible"] * credit("emergency_disconnect_visible")
        + SAFETY_WEIGHTS["stormwater_risk"] * inverse_credit("stormwater_risk")
    )

    df["equity_subscore"] = 100 * (
        EQUITY_WEIGHTS["equity_gap_index_n"] * credit("equity_gap_index_n"))

    # Which inputs this site did not have, in its own row, so every output carries its gaps.
    gaps = pd.DataFrame({col: absent[col] for col in YES_NO_FIELDS + NUMERIC_FIELDS})
    df["absent_fields"] = gaps.apply(lambda r: "; ".join(c for c in gaps.columns if r[c]), axis=1)

    df["readiness_score"] = sum(
        weight * df[subscore] for subscore, weight in SUBSCORE_WEIGHTS.items()
    ).round(1)

    df["expected_sessions_day"] = expected_sessions(df)

    port_rows = []
    for _, row in df.iterrows():
        avg_session_hr = row["avg_dwell_min"] / 60 if row["avg_dwell_min"] > 0 else 2
        ports_now, util_now, wait_now = choose_ports(row["expected_sessions_day"], avg_session_hr, row["hours_open"])
        port_rows.append(
            {
                "recommended_ports_now": int(ports_now),
                "estimated_utilization": util_now,
                "mean_wait_min": wait_now,
            }
        )
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(port_rows)], axis=1)

    ranked = df.sort_values("readiness_score", ascending=False).reset_index(drop=True)
    ranked["model_rank"] = range(1, len(ranked) + 1)
    ranked["scoring_mode"] = mode
    ranked["anchor_set_version"] = ANCHOR_SET_VERSION if mode == MODE_V3 else ""
    ranked["anchor_fallback_fields"] = "; ".join(fallback_fields)
    return ranked


def recommendation_tier(row: pd.Series) -> str:
    """Legacy tier logic (used by both modes).

    Tier 1 is relative to the cohort (`config.TIER1_MAX_RANK`): see the note there before
    comparing tiers across two runs. An unrecorded public_access is treated as not public,
    and an unrecorded garage_enclosed as needing review (DEC-011): neither gap may lift a
    site into a tier that a recorded answer could have kept it out of.
    """
    if not row["public_access"] >= 1:
        return "Low public-priority / special-use"
    if not row["garage_enclosed"] == 0:
        return "High-review candidate"
    if row["model_rank"] <= TIER1_MAX_RANK and row["readiness_score"] >= TIER1_MIN_SCORE:
        return "Tier 1 - advance to site screening"
    if row["readiness_score"] >= TIER2_MIN_SCORE:
        return "Tier 2 - promising candidate, refine data"
    return "Tier 3 - lower priority / monitor"


def add_tiers(results: pd.DataFrame) -> pd.DataFrame:
    results = results.copy()
    results["recommendation_tier"] = results.apply(recommendation_tier, axis=1)
    return results
