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

from .config import ANCHOR_SET_VERSION, DEMAND_COEFFICIENTS, DEMAND_FLOOR_SESSIONS, MODE_LEGACY, MODE_V3
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


class FlagValueError(ValueError):
    """A yes/no field carried something that is neither yes nor no."""


def yesno_to_num(value, field: str = "yes/no field") -> float:
    """Map a yes/no field to 0.0 or 1.0. Refuses anything that is neither.

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
    if pd.isna(value):
        return 0.0
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
    value = str(value).strip().lower()
    return 1.0 if value in {"1", "y", "yes", "true", "t"} else 0.0


def minmax(series: pd.Series) -> pd.Series:
    """Legacy cohort-relative 0-1 scaling."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def bounded_signal(series: pd.Series, high_benchmark: float) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
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
    """Fixed-anchor 0-1 scaling: independent of the cohort."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if hi <= lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(lower=0.0, upper=1.0)


def normalize_fields(df: pd.DataFrame, mode: str, anchor_set: dict | None) -> tuple[pd.DataFrame, list[str]]:
    """Return df with *_n columns plus the list of fields that used cohort fallback."""
    fallback_fields: list[str] = []
    anchors = (anchor_set or {}).get("anchors", {})
    for col in NORMALIZE_COLS:
        if mode == MODE_LEGACY:
            df[col + "_n"] = minmax(df[col])
        else:
            a = anchors.get(col)
            if a is None:
                df[col + "_n"] = minmax(df[col])
                fallback_fields.append(col)
            else:
                df[col + "_n"] = anchored(df[col], a["lo"], a["hi"])
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

    for col in YES_NO_FIELDS:
        # Field name passed through so a refusal says WHICH flag was wrong, not just that
        # one was. "banana is not a yes/no value" is useless when there are seven flags.
        df[col] = df[col].apply(lambda v, c=col: yesno_to_num(v, c)).fillna(0)
    for col in NUMERIC_FIELDS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.35)
    df["readiness_access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.65)

    df["install_cost_est_usd"] = df["trenching_ft"] * df["trench_cost_per_ft"] + df["service_upgrade_cost_usd"]
    df["existing_ports_total"] = df["existing_l2_ports_1mi"] + df["existing_dcfc_ports_3mi"]

    df, fallback_fields = normalize_fields(df, mode, anchor_set)
    df["ev_share_local_n"] = bounded_signal(df["ev_share_local"], EV_SHARE_HIGH_BENCHMARK)

    # hours_open has no persisted _n column; the formula normalises it inline.
    # fcf3d.build_sites reconstructs the same term, so keep the two in step.
    df["hours_open_n"] = df["hours_open"].clip(lower=0, upper=24) / 24
    df["demand_subscore"] = 100 * (
        DEMAND_WEIGHTS["nearby_households_1mi_n"] * df["nearby_households_1mi_n"]
        + DEMAND_WEIGHTS["nearby_jobs_1mi_n"] * df["nearby_jobs_1mi_n"]
        + DEMAND_WEIGHTS["aadt_nearest_n"] * df["aadt_nearest_n"]
        + DEMAND_WEIGHTS["amenities_count_0_5mi_n"] * df["amenities_count_0_5mi_n"]
        + DEMAND_WEIGHTS["parking_spaces_n"] * df["parking_spaces_n"]
        + DEMAND_WEIGHTS["hours_open_n"] * df["hours_open_n"]
        + DEMAND_WEIGHTS["avg_dwell_min_n"] * df["avg_dwell_min_n"]
        + DEMAND_WEIGHTS["ev_share_local_n"] * df["ev_share_local_n"]
        + DEMAND_WEIGHTS["existing_ports_total_n"] * (1 - df["existing_ports_total_n"])
    )
    df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]

    df["feasibility_subscore"] = 100 * (
        FEASIBILITY_WEIGHTS["spare_capacity_kw_n"] * df["spare_capacity_kw_n"]
        + FEASIBILITY_WEIGHTS["distance_to_service_ft_n"] * (1 - df["distance_to_service_ft_n"])
        + FEASIBILITY_WEIGHTS["install_cost_est_usd_n"] * (1 - df["install_cost_est_usd_n"])
        + FEASIBILITY_WEIGHTS["trenching_ft_n"] * (1 - df["trenching_ft_n"])
    )

    df["safety_subscore"] = 100 * (
        SAFETY_WEIGHTS["ada_layout_possible"] * df["ada_layout_possible"]
        + SAFETY_WEIGHTS["fire_access_ok"] * df["fire_access_ok"]
        + SAFETY_WEIGHTS["garage_enclosed"] * (1 - df["garage_enclosed"])
        + SAFETY_WEIGHTS["emergency_disconnect_visible"] * df["emergency_disconnect_visible"]
        + SAFETY_WEIGHTS["stormwater_risk"] * (1 - df["stormwater_risk"])
    )

    df["equity_subscore"] = 100 * (
        EQUITY_WEIGHTS["equity_gap_index_n"] * df["equity_gap_index_n"])

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
    """Legacy tier logic (used by both modes)."""
    if row["public_access"] == 0:
        return "Low public-priority / special-use"
    if row["garage_enclosed"] == 1:
        return "High-review candidate"
    if row["model_rank"] <= 2 and row["readiness_score"] >= 50:
        return "Tier 1 - advance to site screening"
    if row["readiness_score"] >= 45:
        return "Tier 2 - promising candidate, refine data"
    return "Tier 3 - lower priority / monitor"


def add_tiers(results: pd.DataFrame) -> pd.DataFrame:
    results = results.copy()
    results["recommendation_tier"] = results.apply(recommendation_tier, axis=1)
    return results
