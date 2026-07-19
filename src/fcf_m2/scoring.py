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


def yesno_to_num(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
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
        df[col] = df[col].apply(yesno_to_num).fillna(0)
    for col in NUMERIC_FIELDS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.35)
    df["readiness_access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.65)

    df["install_cost_est_usd"] = df["trenching_ft"] * df["trench_cost_per_ft"] + df["service_upgrade_cost_usd"]
    df["existing_ports_total"] = df["existing_l2_ports_1mi"] + df["existing_dcfc_ports_3mi"]

    df, fallback_fields = normalize_fields(df, mode, anchor_set)
    df["ev_share_local_n"] = bounded_signal(df["ev_share_local"], EV_SHARE_HIGH_BENCHMARK)

    df["demand_subscore"] = 100 * (
        0.18 * df["nearby_households_1mi_n"]
        + 0.18 * df["nearby_jobs_1mi_n"]
        + 0.13 * df["aadt_nearest_n"]
        + 0.11 * df["amenities_count_0_5mi_n"]
        + 0.10 * df["parking_spaces_n"]
        + 0.08 * df["hours_open"].clip(lower=0, upper=24) / 24
        + 0.07 * df["avg_dwell_min_n"]
        + 0.08 * df["ev_share_local_n"]
        + 0.07 * (1 - df["existing_ports_total_n"])
    )
    df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]

    df["feasibility_subscore"] = 100 * (
        0.35 * df["spare_capacity_kw_n"]
        + 0.25 * (1 - df["distance_to_service_ft_n"])
        + 0.25 * (1 - df["install_cost_est_usd_n"])
        + 0.15 * (1 - df["trenching_ft_n"])
    )

    df["safety_subscore"] = 100 * (
        0.35 * df["ada_layout_possible"]
        + 0.35 * df["fire_access_ok"]
        + 0.15 * (1 - df["garage_enclosed"])
        + 0.10 * df["emergency_disconnect_visible"]
        + 0.05 * (1 - df["stormwater_risk"])
    )

    df["equity_subscore"] = 100 * df["equity_gap_index_n"]

    df["readiness_score"] = (
        0.45 * df["demand_subscore"]
        + 0.30 * df["feasibility_subscore"]
        + 0.15 * df["safety_subscore"]
        + 0.10 * df["equity_subscore"]
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
        return "Tier 1 — advance to site screening"
    if row["readiness_score"] >= 45:
        return "Tier 2 — promising candidate, refine data"
    return "Tier 3 — lower priority / monitor"


def add_tiers(results: pd.DataFrame) -> pd.DataFrame:
    results = results.copy()
    results["recommendation_tier"] = results.apply(recommendation_tier, axis=1)
    return results
