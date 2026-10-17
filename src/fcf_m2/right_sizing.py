"""Right-sizing: starter ports vs future-ready pathway, legacy and V3 horizons.

- ``legacy_v2`` mode reproduces the accepted V2 right-sizing exactly
  (2035/2050 base/high, multipliers 1.8/2.5/3.0/4.5, floors, parking cap).
- ``milestone2_v3`` mode produces the canonical 2026/2036/2046/2056 scenario set
  (PY-01) with the same floors/cap machinery, saturation-capped by the pathway.

The pathway (future-ready) capacity is computed with the legacy rule in both modes
so the 48-port pathway total is preserved; V3 activation targets are additionally
capped at the pathway (saturation logic).
"""

from __future__ import annotations

import math

import pandas as pd

from .config import (
    LEGACY_GROWTH_MULTIPLIERS,
    MODE_LEGACY,
    MODE_V3,
    V3_GROWTH_MULTIPLIERS,
    V3_STRESS_EXTRA,
    BASELINE_YEAR,
    V3_HORIZONS,
)
from .queueing import choose_ports


def to_number(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default: int = 0) -> int:
    return int(round(to_number(value, default)))


def even_ceiling(value: float, minimum: int = 2, maximum: int = 12) -> int:
    if value <= minimum:
        return minimum
    rounded = int(math.ceil(value))
    if rounded % 2 == 1:
        rounded += 1
    return max(minimum, min(maximum, rounded))


def ports_for_sessions(row: pd.Series, multiplier: float) -> int:
    sessions = to_number(row.get("expected_sessions_day", 0.3), 0.3) * multiplier
    avg_session_hr = to_number(row.get("avg_dwell_min", 120), 120) / 60
    hours_open = to_number(row.get("hours_open", 8), 8)
    ports, _, _ = choose_ports(sessions, avg_session_hr, hours_open)
    return max(2, int(ports))


def site_capacity_cap(row: pd.Series) -> int:
    """Ports the lot can take: 5% of its spaces, rounded up to an even number, 2 to 12.

    A lot nobody counted gets the minimum, 2 (DEC-011, decided 2026-10-17). It used to get
    6 - three times the 2 a measured 40-space lot gets - so leaving the column out was the
    surest way to a bigger plan.
    """
    parking_spaces = to_number(row.get("parking_spaces", 0), 0)
    if parking_spaces <= 0:
        return 2
    return even_ceiling(parking_spaces * 0.05, minimum=2, maximum=12)


def _is_public(row: pd.Series) -> bool:
    """A recorded yes only. A row with no such column is a caller that does not model access
    and is treated as public, as before; a recorded-as-absent value is not public (DEC-011)."""
    return to_number(row.get("public_access", 1), 0) >= 1


def apply_strategy_floors(row: pd.Series, targets: dict[str, int]) -> dict[str, int]:
    """Legacy floor logic, keyed generically: expects keys h1_base/h1_high/h2_base/h2_high."""
    rank = to_int(row.get("model_rank", 99), 99)
    score = to_number(row.get("readiness_score", 0), 0)
    tier = str(row.get("recommendation_tier", ""))
    existing_ports = to_number(row.get("existing_ports_total", 0), 0)
    site_type = str(row.get("site_type", "")).lower()
    risk = str(row.get("electrical_risk_level", "medium")).lower()

    adjusted = dict(targets)

    if not _is_public(row):
        for key in adjusted:
            adjusted[key] = min(adjusted[key], 2)
        return adjusted

    if tier.startswith("Tier 1"):
        adjusted["h1_base"] = max(adjusted["h1_base"], 4)
        adjusted["h1_high"] = max(adjusted["h1_high"], 6)
        adjusted["h2_base"] = max(adjusted["h2_base"], 6)
        adjusted["h2_high"] = max(adjusted["h2_high"], 8)
    elif score >= 50 and rank <= 6 and "garage" not in site_type:
        adjusted["h1_base"] = max(adjusted["h1_base"], 4)
        adjusted["h1_high"] = max(adjusted["h1_high"], 4)
        adjusted["h2_base"] = max(adjusted["h2_base"], 4)
        adjusted["h2_high"] = max(adjusted["h2_high"], 6)
    elif tier.startswith("Tier 2"):
        adjusted["h1_high"] = max(adjusted["h1_high"], 4)
        adjusted["h2_base"] = max(adjusted["h2_base"], 4)
        adjusted["h2_high"] = max(adjusted["h2_high"], 4)

    if existing_ports >= 50 and score < 45:
        adjusted["h1_base"] = min(adjusted["h1_base"], 2)
        adjusted["h1_high"] = min(adjusted["h1_high"], 4)
        adjusted["h2_base"] = min(adjusted["h2_base"], 4)
        adjusted["h2_high"] = min(adjusted["h2_high"], 4)

    if risk == "high":
        adjusted["ports_now"] = min(adjusted["ports_now"], 2)
        adjusted["h1_base"] = min(adjusted["h1_base"], 4)
        adjusted["h1_high"] = min(adjusted["h1_high"], 4)
        adjusted["h2_base"] = min(adjusted["h2_base"], 4)
        adjusted["h2_high"] = min(adjusted["h2_high"], 6)

    return adjusted


def build_strategy(row: pd.Series, future_ready_capacity: int) -> tuple[str, str]:
    rank = to_int(row.get("model_rank", 99), 99)
    score = to_number(row.get("readiness_score", 0), 0)
    tier = str(row.get("recommendation_tier", ""))
    risk = str(row.get("electrical_risk_level", "medium")).lower()
    existing_ports = to_number(row.get("existing_ports_total", 0), 0)
    site_type = str(row.get("site_type", "")).lower()

    if not _is_public(row):
        return ("do_not_advance_general_public_buildout",
                "Limited or non-public access means port planning should wait until the use case is confirmed.")
    if risk == "high":
        return ("electrical_review_before_expansion",
                "Install conservatively and complete electrical/AHJ review before planning larger expansion.")
    if "garage" in site_type:
        return ("garage_review_before_buildout",
                "Garage context requires fire/AHJ/access review before treating the site as a normal expansion candidate.")
    if tier.startswith("Tier 1") or (rank <= 3 and score >= 50):
        return ("install_now_and_make_future_ready",
                f"Strong ranking supports installing starter ports now while preparing pathway capacity for about {future_ready_capacity} ports.")
    if score >= 45:
        return ("starter_install_with_expandable_design",
                f"Promising candidate; install starter ports and preserve room or conduit for about {future_ready_capacity} future-ready ports.")
    if existing_ports >= 50:
        return ("monitor_due_to_nearby_supply",
                "Nearby existing charging supply is high, so keep the buildout conservative unless local need is confirmed.")
    return ("monitor_or_small_pilot",
            "Lower current readiness suggests a small pilot or monitoring approach before larger investment.")


def _base_targets(row: pd.Series, multipliers: dict[str, float]) -> dict[str, int]:
    model_ports_now = to_int(row.get("recommended_ports_now", 2), 2)
    return {
        "ports_now": max(2, model_ports_now),
        "h1_base": ports_for_sessions(row, multipliers["h1_base"]),
        "h1_high": ports_for_sessions(row, multipliers["h1_high"]),
        "h2_base": ports_for_sessions(row, multipliers["h2_base"]),
        "h2_high": ports_for_sessions(row, multipliers["h2_high"]),
    }


def _future_ready(row: pd.Series, targets: dict[str, int], cap: int) -> int:
    future_ready_capacity = max(targets["ports_now"], targets["h1_high"], targets["h2_base"])
    if str(row.get("recommendation_tier", "")).startswith("Tier 1"):
        future_ready_capacity = max(future_ready_capacity, min(targets["h2_high"], cap))
    return min(future_ready_capacity, cap)


def run_right_sizing_legacy(results: pd.DataFrame) -> pd.DataFrame:
    """Exact legacy V2 right-sizing (2035/2050)."""
    df = _merge_risk_defaults(results)
    rows = []
    m = {"h1_base": LEGACY_GROWTH_MULTIPLIERS["2035_base"], "h1_high": LEGACY_GROWTH_MULTIPLIERS["2035_high"],
         "h2_base": LEGACY_GROWTH_MULTIPLIERS["2050_base"], "h2_high": LEGACY_GROWTH_MULTIPLIERS["2050_high"]}
    for _, row in df.iterrows():
        targets = apply_strategy_floors(row, _base_targets(row, m))
        cap = site_capacity_cap(row)
        for key in ["h1_base", "h1_high", "h2_base", "h2_high"]:
            targets[key] = min(targets[key], cap)
        future_ready_capacity = _future_ready(row, targets, cap)
        strategy, reason = build_strategy(row, future_ready_capacity)
        rows.append({
            "site_id": row.get("site_id"),
            "site_name": row.get("site_name"),
            "model_rank": to_int(row.get("model_rank", 0), 0),
            "readiness_score": to_number(row.get("readiness_score", 0), 0),
            "recommendation_tier": row.get("recommendation_tier", ""),
            "electrical_risk_level": row.get("electrical_risk_level", "medium"),
            "expected_sessions_day_now": round(to_number(row.get("expected_sessions_day", 0.3), 0.3), 3),
            "model_recommended_ports_now": to_int(row.get("recommended_ports_now", 2), 2),
            "ports_now": targets["ports_now"],
            "ports_2035_base": targets["h1_base"],
            "ports_2035_high": targets["h1_high"],
            "ports_2050_base": targets["h2_base"],
            "ports_2050_high": targets["h2_high"],
            "site_capacity_cap": cap,
            "future_ready_capacity": future_ready_capacity,
            "expansion_strategy": strategy,
            "right_sizing_reason": reason,
        })
    return pd.DataFrame(rows).sort_values("model_rank").reset_index(drop=True)


def run_right_sizing_v3(results: pd.DataFrame) -> pd.DataFrame:
    """Canonical V3 scenario set: one row per site x horizon x case (PY-01).

    Pathway capacity uses the legacy rule (preserving the 48-port pathway).
    Horizon activation targets: queueing-driven ports under the V3 multipliers,
    with the legacy floor machinery mapped 2036->h1, 2046->h2, then 2056 computed
    directly and saturation-capped by the pathway.
    """
    df = _merge_risk_defaults(results)
    legacy = run_right_sizing_legacy(results).set_index("site_id")

    rows = []
    for _, row in df.iterrows():
        sid = row["site_id"]
        cap = site_capacity_cap(row)
        pathway = int(legacy.loc[sid, "future_ready_capacity"])
        ports_now = int(legacy.loc[sid, "ports_now"])

        m = {"h1_base": V3_GROWTH_MULTIPLIERS[(2036, "base")], "h1_high": V3_GROWTH_MULTIPLIERS[(2036, "high")],
             "h2_base": V3_GROWTH_MULTIPLIERS[(2046, "base")], "h2_high": V3_GROWTH_MULTIPLIERS[(2046, "high")]}
        targets = apply_strategy_floors(row, _base_targets(row, m))
        for key in ["h1_base", "h1_high", "h2_base", "h2_high"]:
            targets[key] = min(targets[key], cap)

        p2056 = {}
        for case in ("base", "high"):
            raw = ports_for_sessions(row, V3_GROWTH_MULTIPLIERS[(2056, case)])
            prev = targets["h2_base"] if case == "base" else targets["h2_high"]
            p2056[case] = min(max(raw, prev), cap)

        stress = {}
        for year, key in ((2036, "h1_high"), (2046, "h2_high"), (2056, None)):
            if year == 2056:
                raw = ports_for_sessions(row, V3_GROWTH_MULTIPLIERS[(2056, "high")] * V3_STRESS_EXTRA)
                stress[year] = min(max(raw, p2056["high"]), cap)
            else:
                raw = ports_for_sessions(row, V3_GROWTH_MULTIPLIERS[(year, "high")] * V3_STRESS_EXTRA)
                stress[year] = min(max(raw, targets[key]), cap)

        per_year = {
            2026: {"baseline": ports_now},
            2036: {"base": targets["h1_base"], "high": targets["h1_high"], "stress_combined": stress[2036]},
            2046: {"base": targets["h2_base"], "high": targets["h2_high"], "stress_combined": stress[2046]},
            2056: {"base": p2056["base"], "high": p2056["high"], "stress_combined": stress[2056]},
        }

        # Monotonic non-decreasing enforcement within each case across horizons (RT-03),
        # then saturation cap at pathway.
        for case in ("base", "high", "stress_combined"):
            prev = ports_now
            for year in V3_HORIZONS:
                val = max(per_year[year][case], prev)
                val = min(val, max(pathway, ports_now))
                per_year[year][case] = val
                prev = val

        strategy, reason = build_strategy(row, pathway)
        for year in [BASELINE_YEAR] + V3_HORIZONS:
            for case, ports in per_year[year].items():
                rows.append({
                    "site_id": sid,
                    "site_name": row.get("site_name"),
                    "model_rank": to_int(row.get("model_rank", 0), 0),
                    "horizon_year": year,
                    "case": case,
                    "ports_active": int(ports),
                    "ports_pathway": int(max(pathway, ports_now)),
                    "site_capacity_cap": cap,
                    "expansion_strategy": strategy,
                    "right_sizing_reason": reason,
                })
    return pd.DataFrame(rows).sort_values(["model_rank", "horizon_year", "case"]).reset_index(drop=True)


def _merge_risk_defaults(results: pd.DataFrame) -> pd.DataFrame:
    df = results.copy()
    if "electrical_risk_level" not in df.columns:
        df["electrical_risk_level"] = "medium"
    df["electrical_risk_level"] = df["electrical_risk_level"].fillna("medium")
    if "existing_ports_total" not in df.columns:
        df["existing_ports_total"] = (
            pd.to_numeric(df.get("existing_l2_ports_1mi", 0), errors="coerce").fillna(0)
            + pd.to_numeric(df.get("existing_dcfc_ports_3mi", 0), errors="coerce").fillna(0)
        )
    return df
