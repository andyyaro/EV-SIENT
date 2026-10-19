"""
build_sites.py - Future City Fellowship 3D map ETL.

Joins the ChargeReady NOVA model outputs into ONE georeferenced record per
candidate site, emitted as:

  web/data/sites.geojson   RFC 7946 FeatureCollection (one Point per site)
  web/data/sites.json      the same records, flat, for the comparison table
  web/data/manifest.json   run provenance + field dictionary

Source tables (all keyed on site_id):
  tests/fixture_legacy_v2_site_results.csv          full scoring detail
  tests/fixture_legacy_v2_right_sizing.csv          ports trajectory
  data/inputs/legacy_v2_electrical_risk_summary_*   electrical risk + rank sensitivity
  dashboard/tableau/patch_package/tbl_peak_waits    queueing results
  dashboard/tableau/patch_package/tbl_avoided_evse  avoided-overbuild economics
  data/contract/v3/scenario_table.csv               per-horizon scenarios (milestone2_v3;
                                                    v1 for legacy_v2 - DEC-027)
  data/provenance/site_coordinate_sources.csv       coordinate provenance

Nothing here re-runs the model. This is a read-only projection of frozen
model outputs into a shape a 3D client can consume.

Usage:
    python -m fcf3d.build_sites --repo /path/to/Future-City-Fellowship --out web/data
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

SCHEMA_VERSION = "fcf3d/1.0.0"

# --------------------------------------------------------------------------
# Source resolution
# --------------------------------------------------------------------------

# --- Modes -------------------------------------------------------------------
# The repository is dual-mode and the map must be too. Reading the legacy_v2
# baseline while the repository's canonical truth is milestone2_v3 is how a map
# ends up telling planners a story the model never told -- especially when the
# output field names carry a horizon convention V3 explicitly retired.
#
# Each mode declares its own sources AND its own horizon vocabulary. A field
# name never carries a horizon its data does not have: legacy_v2 emits
# ports_2035/ports_2050 because that is genuinely what it computed, and
# milestone2_v3 emits ports_2026/2036/2046/2056 because that is what it computed.

MODE_LEGACY = "legacy_v2"
MODE_V3 = "milestone2_v3"
MODES = (MODE_V3, MODE_LEGACY)
DEFAULT_MODE = MODE_V3

MODE_SOURCES: dict[str, dict[str, str]] = {
    MODE_LEGACY: {
        "results": "tests/fixture_legacy_v2_site_results.csv",
        "right_sizing": "tests/fixture_legacy_v2_right_sizing.csv",
    },
    MODE_V3: {
        "results": "tests/fixture_milestone2_v3_site_results.csv",
        "right_sizing": "tests/fixture_milestone2_v3_right_sizing.csv",
    },
}

# Horizon vocabulary per mode. Keys are the emitted field suffixes; the values
# are what the viewer shows a human.
MODE_HORIZONS: dict[str, list[tuple[str, str]]] = {
    MODE_LEGACY: [("now", "Now"), ("2035", "2035"), ("2050", "2050")],
    MODE_V3: [("2026", "2026 baseline"), ("2036", "2036"), ("2046", "2046"), ("2056", "2056")],
}

MODE_NOTES: dict[str, str] = {
    MODE_LEGACY: (
        "legacy_v2 baseline - the accepted V2 numbers, reproduced bit-exact and retained "
        "for continuity. Its Now/2035/2050 horizons were RETIRED by milestone2_v3. These "
        "are not the repository's current planning numbers."
    ),
    MODE_V3: (
        "milestone2_v3 - the repository's canonical mode: 2026 baseline with 2036/2046/2056 "
        "horizons, cohort-independent fixed-anchor scoring, and typed data confidence."
    ),
}

OPTIONAL = {
    "peak_waits": "dashboard/tableau/patch_package/tbl_peak_waits.csv",
    "avoided_evse": "dashboard/tableau/patch_package/tbl_avoided_evse.csv",
    "scenarios": "data/contract/v1/scenario_table.csv",
    "coord_sources": "data/provenance/site_coordinate_sources.csv",
    "readiness_conf": "dashboard/tableau/patch_package/tbl_readiness_confidence.csv",
}
#: Per-mode overrides of OPTIONAL. milestone2_v3 reads the authoritative contract v3 (DEC-027),
#: whose plan is the one in its right-sizing fixture; legacy_v2 keeps the frozen v1 it matches.
MODE_OPTIONAL: dict[str, dict[str, str]] = {
    MODE_V3: {"scenarios": "data/contract/v3/scenario_table.csv"},
    MODE_LEGACY: {},
}
# electrical risk file is date-stamped
ELECTRICAL_GLOB = "data/inputs/legacy_v2_electrical_risk_summary_frozen_*.csv"


class SourceMissing(RuntimeError):
    pass


def resolve_sources(repo: str, mode: str = DEFAULT_MODE) -> dict[str, str]:
    """Locate every input table for ``mode``. Raises if a required table is absent."""
    if mode not in MODE_SOURCES:
        raise SourceMissing(f"unknown mode {mode!r}; expected one of {list(MODES)}")
    found: dict[str, str] = {}
    for key, rel in MODE_SOURCES[mode].items():
        path = os.path.join(repo, rel)
        if not os.path.isfile(path):
            raise SourceMissing(f"required table missing for mode {mode}: {rel}")
        found[key] = path
    for key, rel in {**OPTIONAL, **MODE_OPTIONAL.get(mode, {})}.items():
        path = os.path.join(repo, rel)
        if os.path.isfile(path):
            found[key] = path
    matches = sorted(glob.glob(os.path.join(repo, ELECTRICAL_GLOB)))
    if matches:
        found["electrical"] = matches[-1]  # newest freeze
    return found


# --------------------------------------------------------------------------
# Derivation helpers
# --------------------------------------------------------------------------

# --- Model weights, mirrored from fcf_m2.scoring.score_sites ------------------
# Kept in one place so the map's "why this rank" attribution is the model's own
# arithmetic, not a re-interpretation of it. test_build_sites.py asserts that
# reconstructing the score from these weights reproduces readiness_score.

# Imported, not copied. These used to be a hand-maintained duplicate of the numbers
# inside fcf_m2.scoring's formula; they agreed only because somebody kept them in step,
# and the explorer's own test only checked that its copy summed to 1.0 -- never that it
# matched the model. Importing makes drift impossible rather than merely detectable.
from fcf_m2.scoring import (  # noqa: E402
    DRIVER_WEIGHTS,
    INVERTED_DRIVERS,
    SUBSCORE_WEIGHTS,
)

SUBSCORES = [
    ("demand_subscore", "Demand"),
    ("feasibility_subscore", "Feasibility"),
    ("safety_subscore", "Safety"),
    ("equity_subscore", "Equity"),
]


@dataclass(frozen=True)
class Driver:
    """One term inside a subscore.

    column      normalized [0,1] column produced by the model
    weight      its weight within the subscore
    invert      True when the model applies (1 - x), i.e. lower raw is better
    raw_column  the un-normalized column, shown as the human-readable value
    """

    column: str
    label: str
    weight: float
    subscore: str
    invert: bool = False
    raw_column: str | None = None
    unit: str = ""
    fmt: str = "{:,.0f}"

    def effective(self, row: pd.Series) -> float | None:
        """The value the model actually multiplies by `weight`."""
        if self.column not in row or pd.isna(row[self.column]):
            return None
        val = float(row[self.column])
        return 1.0 - val if self.invert else val


DRIVERS: list[Driver] = [
    # --- demand (× 0.45, and × readiness_access_adjustment) ---
    Driver("nearby_households_1mi_n", "Households within 1 mi", 0.18, "demand_subscore",
           raw_column="nearby_households_1mi"),
    Driver("nearby_jobs_1mi_n", "Jobs within 1 mi", 0.18, "demand_subscore",
           raw_column="nearby_jobs_1mi"),
    Driver("aadt_nearest_n", "Adjacent traffic (AADT)", 0.13, "demand_subscore",
           raw_column="aadt_nearest", unit="veh/day"),
    Driver("amenities_count_0_5mi_n", "Amenities within 0.5 mi", 0.11, "demand_subscore",
           raw_column="amenities_count_0_5mi"),
    Driver("parking_spaces_n", "Parking supply", 0.10, "demand_subscore",
           raw_column="parking_spaces", unit="spaces"),
    Driver("hours_open_n", "Operating hours", 0.08, "demand_subscore",
           raw_column="hours_open", unit="hr", fmt="{:,.1f}"),
    Driver("avg_dwell_min_n", "Average dwell time", 0.07, "demand_subscore",
           raw_column="avg_dwell_min", unit="min"),
    Driver("ev_share_local_n", "Local EV adoption", 0.08, "demand_subscore",
           raw_column="ev_share_local", unit="share", fmt="{:.3f}"),
    Driver("existing_ports_total_n", "Nearby charger saturation", 0.07, "demand_subscore",
           invert=True, raw_column="existing_ports_total", unit="ports"),
    # --- feasibility (× 0.30) ---
    Driver("spare_capacity_kw_n", "Spare electrical capacity", 0.35, "feasibility_subscore",
           raw_column="spare_capacity_kw", unit="kW"),
    Driver("distance_to_service_ft_n", "Distance to electrical service", 0.25,
           "feasibility_subscore", invert=True, raw_column="distance_to_service_ft", unit="ft"),
    Driver("install_cost_est_usd_n", "Estimated install cost", 0.25, "feasibility_subscore",
           invert=True, raw_column="install_cost_est_usd", unit="USD"),
    Driver("trenching_ft_n", "Trenching required", 0.15, "feasibility_subscore",
           invert=True, raw_column="trenching_ft", unit="ft"),
    # --- safety (× 0.15); these are already 0/1 flags, not _n columns ---
    Driver("ada_layout_possible", "ADA-compliant layout possible", 0.35, "safety_subscore"),
    Driver("fire_access_ok", "Fire apparatus access", 0.35, "safety_subscore"),
    Driver("garage_enclosed", "Open-air (not enclosed garage)", 0.15, "safety_subscore",
           invert=True),
    Driver("emergency_disconnect_visible", "Emergency disconnect visible", 0.10,
           "safety_subscore"),
    Driver("stormwater_risk", "Stormwater exposure", 0.05, "safety_subscore", invert=True),
    # --- equity (× 0.10) ---
    Driver("equity_gap_index_n", "Equity gap index", 1.00, "equity_subscore",
           raw_column="equity_gap_index", fmt="{:.3f}"),
]

TIER_RANK = {
    "Tier 1": 1,
    "Tier 2": 2,
    "Tier 3": 3,
    "High-review": 2,
    "Low public-priority": 4,
}


def tier_key(tier: str) -> int:
    for prefix, val in TIER_RANK.items():
        if str(tier).startswith(prefix):
            return val
    return 9


def _clean(value: Any) -> Any:
    """NaN/inf -> None so the JSON is strict-valid."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 6)
    if isinstance(value, (int, bool, str)):
        return value
    if hasattr(value, "item"):
        return _clean(value.item())
    return value


def split_sentences(text: Any) -> list[str]:
    """Split the model's semicolon-delimited prose fields into list items."""
    if not isinstance(text, str) or not text.strip():
        return []
    parts = [p.strip(" .;") for p in text.split(";")]
    return [p[0].upper() + p[1:] for p in parts if p]


def attribute_drivers(row: pd.Series) -> list[dict]:
    """
    Decompose the readiness score into per-driver point contributions using the
    model's own weights.

        earned  = subscore_weight * driver_weight * 100 * effective * access_adj
        possible = subscore_weight * driver_weight * 100 * access_adj
        forgone = possible - earned

    `earned` is how many readiness points this driver actually delivered;
    `forgone` is how many it left on the table. Ranking by those two numbers
    gives strengths and constraints that are true to the model rather than
    thresholded by eye.
    """
    # demand terms carry the public-access penalty; the others do not
    access_adj = float(row.get("readiness_access_adjustment", 1.0) or 1.0)

    out: list[dict] = []
    for drv in DRIVERS:
        eff = drv.effective(row)
        if eff is None:
            continue
        adj = access_adj if drv.subscore == "demand_subscore" else 1.0
        possible = SUBSCORE_WEIGHTS[drv.subscore] * drv.weight * 100.0 * adj
        earned = possible * eff
        entry = {
            "driver": drv.label,
            "subscore": drv.subscore,
            "subscore_label": dict(SUBSCORES)[drv.subscore],
            "effective": round(eff, 4),
            "points_earned": round(earned, 2),
            "points_possible": round(possible, 2),
            "points_forgone": round(possible - earned, 2),
            "lower_is_better": drv.invert,
        }
        if drv.raw_column and drv.raw_column in row and not pd.isna(row[drv.raw_column]):
            raw = float(row[drv.raw_column])
            entry["raw"] = _clean(raw)
            entry["raw_display"] = (drv.fmt.format(raw) + (f" {drv.unit}" if drv.unit else "")).strip()
        out.append(entry)
    return out


def reconstruct_score(row: pd.Series) -> float:
    """Rebuild readiness_score from DRIVERS. Used by the test suite as a guard
    against these weights drifting away from fcf_m2.scoring."""
    return round(sum(d["points_earned"] for d in attribute_drivers(row)), 1)


def mine_strengths_constraints(
    row: pd.Series, top_n: int = 5
) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (strengths, constraints, full_attribution)."""
    attribution = attribute_drivers(row)
    # a strength must actually be capturing most of what it could
    strengths = [d for d in attribution if d["effective"] >= 0.60]
    strengths.sort(key=lambda d: -d["points_earned"])
    # a constraint is ranked by points lost, not by how low the value looks
    constraints = [d for d in attribution if d["points_forgone"] >= 0.20]
    constraints.sort(key=lambda d: -d["points_forgone"])
    return strengths[:top_n], constraints[:top_n], attribution


def build_scenarios(scen: pd.DataFrame | None, site_id: str) -> list[dict]:
    if scen is None:
        return []
    sub = scen[scen["site_id"] == site_id]
    out = []
    for _, r in sub.iterrows():
        out.append(
            {
                "scenario_id": r.get("scenario_id"),
                "horizon_year": _clean(r.get("horizon_year")),
                "horizon_label": r.get("horizon_label"),
                "scenario_name": r.get("scenario_name"),
                "ports_active": _clean(r.get("ports_active")),
                "ports_pathway_capacity": _clean(r.get("ports_pathway_capacity")),
                "evse_power_kw": _clean(r.get("evse_power_kw")),
                "sessions_per_day": _clean(r.get("sessions_per_day")),
                "energy_required_kwh_day": _clean(r.get("energy_required_kwh_day")),
                "utilization": _clean(r.get("utilization")),
                "peak_wait_minutes": _clean(r.get("peak_wait_minutes")),
                "lifecycle_cost_npv_usd": _clean(r.get("lifecycle_cost_npv_usd")),
                "avoided_overbuild_cost_usd": _clean(r.get("avoided_overbuild_cost_usd")),
                "net_co2e_kg": _clean(r.get("net_co2e_kg")),
            }
        )
    out.sort(key=lambda s: (s["horizon_year"] or 0, str(s["scenario_name"])))
    return out


# --------------------------------------------------------------------------
# Core build
# --------------------------------------------------------------------------


@dataclass
class BuildResult:
    features: list[dict] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def prepare(res: pd.DataFrame) -> pd.DataFrame:
    """Recreate the one driver term the model computes inline rather than as a
    persisted `_n` column: hours_open.clip(0, 24) / 24."""
    res = res.copy()
    if "hours_open_n" not in res.columns and "hours_open" in res.columns:
        res["hours_open_n"] = res["hours_open"].clip(lower=0, upper=24) / 24.0
    if "readiness_access_adjustment" not in res.columns:
        res["readiness_access_adjustment"] = res.get("public_access", 1).apply(
            lambda v: 1.00 if float(v or 0) >= 1 else 0.65
        )
    return res


def load(paths: dict[str, str]) -> dict[str, pd.DataFrame]:
    frames = {}
    for key, path in paths.items():
        frames[key] = pd.read_csv(path)
    return frames


def ports_by_horizon(row, rs_rows, mode: str) -> dict[str, Any]:
    """Per-horizon active ports, keyed by the horizon vocabulary of ``mode``.

    A field name never carries a horizon its data does not have. In legacy_v2 the
    right-sizing fixture is one row per site with recommended_ports_<year> columns;
    in milestone2_v3 it is one row per (site, horizon, case), so the canonical
    horizons are read from the data rather than assumed.
    """
    out: dict[str, Any] = {}
    if mode == MODE_LEGACY:
        out["ports_now"] = _clean(row.get("recommended_ports_now"))
        out["ports_2035"] = _clean(row.get("recommended_ports_2035"))
        out["ports_2050"] = _clean(row.get("recommended_ports_2050"))
        return out
    # milestone2_v3: aggregate the base path, which is what the headline series reports
    out["ports_2026"] = _clean(row.get("recommended_ports_now"))
    if rs_rows is None or len(rs_rows) == 0:
        return out
    for horizon in sorted(int(h) for h in rs_rows["horizon_year"].unique()):
        sub = rs_rows[rs_rows["horizon_year"] == horizon]
        base = sub[sub["case"].isin(("baseline", "base"))]
        high = sub[sub["case"].isin(("baseline", "high"))]
        if len(base):
            out[f"ports_{horizon}"] = _clean(float(base["ports_active"].iloc[0]))
        if len(high):
            out[f"ports_{horizon}_high"] = _clean(float(high["ports_active"].iloc[0]))
    return out


def build(frames: dict[str, pd.DataFrame], sources: dict[str, str],
          mode: str = DEFAULT_MODE) -> BuildResult:
    res = prepare(frames["results"])
    # legacy_v2 right-sizing is one row per site; milestone2_v3 is one row per
    # (site, horizon, case). Keep the raw frame so both shapes can be served.
    rs_all = frames["right_sizing"]
    rs = rs_all.set_index("site_id")
    elec = frames.get("electrical")
    elec_i = elec.set_index("site_id") if elec is not None else None
    waits = frames.get("peak_waits")
    waits_i = waits.set_index("site_id") if waits is not None else None
    coords = frames.get("coord_sources")
    coords_i = coords.set_index("site_id") if coords is not None else None
    scen = frames.get("scenarios")
    avoided = frames.get("avoided_evse")
    if mode == MODE_V3 and scen is not None:
        # The Tableau patch package carries contract v1's plan. In milestone2_v3 the pathway
        # ports not energized are worked out from contract v3's own rows, by the model's
        # function, so the map cannot show one plan's ports beside another's avoided ports.
        from fcf_m2.emissions import avoided_evse_metric
        avoided = avoided_evse_metric(
            scen.rename(columns={"scenario_name": "case", "ports_pathway_capacity": "ports_pathway"})
            [["site_id", "horizon_year", "case", "ports_active", "ports_pathway"]])

    out = BuildResult()

    # portfolio context for relative bars in the UI
    score_min = float(res["readiness_score"].min())
    score_max = float(res["readiness_score"].max())

    for _, row in res.sort_values("model_rank").iterrows():
        sid = row["site_id"]
        lon, lat = float(row["lon"]), float(row["lat"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            out.warnings.append(f"{sid}: coordinates out of range")
            continue

        strengths, constraints, attribution = mine_strengths_constraints(row)

        # sanity-check our weight table against the model's own output
        rebuilt = round(sum(d["points_earned"] for d in attribution), 1)
        actual = round(float(row["readiness_score"]), 1)
        if abs(rebuilt - actual) > 0.15:
            out.warnings.append(
                f"{sid}: driver attribution {rebuilt} != readiness_score {actual} "
                "(fcf3d.build_sites DRIVERS may have drifted from fcf_m2.scoring)"
            )

        # AHJ / safety review reasons are first-class constraints
        if int(row.get("ahj_review_flag", 0) or 0) == 1:
            for reason in split_sentences(row.get("review_reason")):
                constraints.insert(
                    0, {"driver": "AHJ review", "note": reason, "subscore_label": "Safety"}
                )

        rs_rows = rs_all[rs_all["site_id"] == sid] if "site_id" in rs_all.columns else None
        if sid in rs.index:
            picked = rs.loc[sid]
            if isinstance(picked, pd.DataFrame):
                # V3: several horizon/case rows. The site-level summary row is the
                # baseline, which is the only one carrying "now" semantics.
                baseline = picked[picked["case"] == "baseline"] if "case" in picked else picked
                rs_row = (baseline.iloc[0] if len(baseline) else picked.iloc[0])
            else:
                rs_row = picked
        else:
            rs_row = None
        el_row = elec_i.loc[sid] if elec_i is not None and sid in elec_i.index else None
        wt_row = waits_i.loc[sid] if waits_i is not None and sid in waits_i.index else None
        co_row = coords_i.loc[sid] if coords_i is not None and sid in coords_i.index else None

        avoided_now = None
        if avoided is not None:
            m = avoided[(avoided["site_id"] == sid) & (avoided["horizon_year"] == 2026)]
            if len(m):
                avoided_now = {
                    "avoided_active_evse_ports": _clean(m.iloc[0]["avoided_active_evse_ports"]),
                    "avoided_network_fee_usd_yr": _clean(m.iloc[0]["avoided_network_fee_usd_yr"]),
                }

        props: dict[str, Any] = {
            # identity
            "site_id": sid,
            "site_name": row["site_name"],
            "site_type": row["site_type"],
            "address": row.get("address"),
            "city": row.get("city"),
            "state": row.get("state"),
            "zip": str(row.get("zip")),
            "jurisdiction": "fairfax" if str(sid).startswith("FFX") else "prince_william",
            "public_access": bool(row.get("public_access", 0)),
            "garage_enclosed": bool(row.get("garage_enclosed", 0)),
            # ranking
            "model_rank": int(row["model_rank"]),
            "readiness_score": _clean(row["readiness_score"]),
            "readiness_score_pct": round(
                (float(row["readiness_score"]) - score_min)
                / max(score_max - score_min, 1e-9)
                * 100,
                1,
            ),
            "recommendation_tier": row.get("recommendation_tier"),
            "tier_key": tier_key(row.get("recommendation_tier", "")),
            "readiness_band": row.get("readiness_band"),
            "confidence_band": row.get("confidence_band"),
            "action_label": row.get("action_label"),
            "action_detail": row.get("action_detail"),
            "planning_recommendation": row.get("planning_recommendation"),
            "priority_reason": row.get("priority_reason"),
            # subscores
            "subscores": {
                key: _clean(row.get(key)) for key, _label in SUBSCORES
            },
            "subscore_labels": {key: label for key, label in SUBSCORES},
            # confidence
            "data_confidence_score": _clean(row.get("data_confidence_score")),
            "data_confidence_level": row.get("data_confidence_level"),
            "data_confidence_reason": row.get("data_confidence_reason"),
            "data_needed_next": split_sentences(row.get("data_needed_next")),
            # right-sizing
            # Horizon-bearing port fields are named by the ACTIVE MODE. See
            # ports_by_horizon(): legacy_v2 emits now/2035/2050, milestone2_v3 emits
            # 2026/2036/2046/2056. Never a 2050 field holding a 2046 number.
            **ports_by_horizon(row, rs_rows, mode),
            "expected_sessions_day": _clean(row.get("expected_sessions_day")),
            "estimated_utilization": _clean(row.get("estimated_utilization")),
            "mean_wait_min": _clean(row.get("mean_wait_min")),
            "install_cost_est_usd": _clean(row.get("install_cost_est_usd")),
            "parking_spaces": _clean(row.get("parking_spaces")),
            # narrative
            "strengths": strengths,
            "constraints": constraints,
            "driver_attribution": attribution,
            "score_reconstructed": rebuilt,
            "ahj_review_flag": int(row.get("ahj_review_flag", 0) or 0),
            "review_reasons": split_sentences(row.get("review_reason")),
            # placement defaults for the 3D asset
            "asset": {
                "model": "evse_canopy",
                "heading_deg": 0.0,
                "offset_east_m": 0.0,
                "offset_north_m": 0.0,
                "clamp_to_ground": True,
            },
        }

        if rs_row is not None:
            right_sizing: dict[str, Any] = {
                "mode": mode,
                "site_capacity_cap": _clean(rs_row.get("site_capacity_cap")),
                "expansion_strategy": rs_row.get("expansion_strategy"),
                "right_sizing_reason": rs_row.get("right_sizing_reason"),
            }
            if mode == MODE_LEGACY:
                right_sizing.update({
                    "ports_now": _clean(rs_row.get("ports_now")),
                    "ports_2035_base": _clean(rs_row.get("ports_2035_base")),
                    "ports_2035_high": _clean(rs_row.get("ports_2035_high")),
                    "ports_2050_base": _clean(rs_row.get("ports_2050_base")),
                    "ports_2050_high": _clean(rs_row.get("ports_2050_high")),
                    "future_ready_capacity": _clean(rs_row.get("future_ready_capacity")),
                })
            else:
                right_sizing["future_ready_capacity"] = _clean(rs_row.get("ports_pathway"))
                for horizon in sorted(int(h) for h in rs_rows["horizon_year"].unique()):
                    sub = rs_rows[rs_rows["horizon_year"] == horizon]
                    for case, suffix in (("baseline", "base"), ("base", "base"), ("high", "high")):
                        hit = sub[sub["case"] == case]
                        if len(hit):
                            right_sizing[f"ports_{horizon}_{suffix}"] = _clean(
                                float(hit["ports_active"].iloc[0]))
            props["right_sizing"] = right_sizing
            ports_now_key = "ports_now" if mode == MODE_LEGACY else "ports_2026"
            active = (rs_row.get("ports_now") if mode == MODE_LEGACY
                      else rs_row.get("ports_active"))
            props["asset"]["ports"] = int(active or props.get(ports_now_key) or 2)
            pathway = (rs_row.get("future_ready_capacity") if mode == MODE_LEGACY
                       else rs_row.get("ports_pathway"))
            props["asset"]["pathway_ports"] = int(pathway or props["asset"]["ports"])
        else:
            ports_now_key = "ports_now" if mode == MODE_LEGACY else "ports_2026"
            props["asset"]["ports"] = int(props.get(ports_now_key) or 2)
            props["asset"]["pathway_ports"] = props["asset"]["ports"]

        if el_row is not None:
            props["electrical"] = {
                "risk_level": el_row.get("electrical_risk_level"),
                "risk_points": _clean(el_row.get("electrical_risk_points")),
                "risk_reason": split_sentences(el_row.get("electrical_risk_reason")),
                "data_needed_next": split_sentences(el_row.get("electrical_data_needed_next")),
                "rank_optimistic": _clean(el_row.get("optimistic_rank")),
                "rank_expected": _clean(el_row.get("expected_rank")),
                "rank_conservative": _clean(el_row.get("conservative_rank")),
                "worst_case_rank_change": _clean(el_row.get("worst_case_rank_change")),
            }

        if wt_row is not None:
            props["queueing"] = {
                "ports": _clean(wt_row.get("ports")),
                "mean_wait_min": _clean(wt_row.get("mean_wait_min")),
                "p90_wait_min": _clean(wt_row.get("p90_wait_min")),
                "peak_p90_wait_min": _clean(wt_row.get("peak_p90_wait_min")),
                "peak_erlang_wait_min": _clean(wt_row.get("peak_erlang_wait_min")),
                "sim_utilization": _clean(wt_row.get("sim_utilization")),
            }

        if co_row is not None:
            props["coordinate_provenance"] = {
                "source_dataset": co_row.get("source_dataset"),
                "source_owner": co_row.get("source_owner"),
                "source_quality": co_row.get("source_quality"),
                "notes": co_row.get("notes"),
            }

        if avoided_now:
            props["avoided_overbuild"] = avoided_now

        props["scenarios"] = build_scenarios(scen, sid)

        out.features.append(
            {
                "type": "Feature",
                "id": sid,
                "geometry": {"type": "Point", "coordinates": [lon, lat, 0.0]},
                "properties": props,
            }
        )

    out.manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # The active mode travels with the data. A viewer that cannot say which
        # mode it is showing cannot be trusted about any number on the screen.
        "mode": mode,
        "mode_note": MODE_NOTES[mode],
        "mode_is_canonical": mode == MODE_V3,
        "horizons": [year for year, _label in MODE_HORIZONS[mode]],
        "horizon_labels": {year: label for year, label in MODE_HORIZONS[mode]},
        "site_count": len(out.features),
        "score_min": round(score_min, 2),
        "score_max": round(score_max, 2),
        "sources": {k: os.path.basename(v) for k, v in sources.items()},
        "disclaimer": (
            "Planning prototype only. Screening-class estimates; not an "
            "engineering, permitting, or procurement tool. Electrical service "
            "capacity is unconfirmed for all sites pending utility/facility review. "
            "0 of 12 sites reach High data confidence. Massing is illustrative, not a design."
        ),
        "warnings": out.warnings,
    }
    return out


def write(result: BuildResult, out_dir: str) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "name": "chargeready_nova_candidate_sites",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3/CRS84"}},
        "metadata": result.manifest,
        "features": result.features,
    }
    paths = {}
    paths["geojson"] = os.path.join(out_dir, "sites.geojson")
    with open(paths["geojson"], "w") as fh:
        json.dump(fc, fh, indent=1)

    paths["json"] = os.path.join(out_dir, "sites.json")
    flat = [f["properties"] | {"lon": f["geometry"]["coordinates"][0],
                               "lat": f["geometry"]["coordinates"][1]}
            for f in result.features]
    with open(paths["json"], "w") as fh:
        json.dump(flat, fh, indent=1)

    paths["manifest"] = os.path.join(out_dir, "manifest.json")
    with open(paths["manifest"], "w") as fh:
        json.dump(result.manifest, fh, indent=1)

    # inline copy so web/index.html also runs straight off the filesystem,
    # where fetch() of a local JSON file is blocked by CORS
    paths["inline"] = os.path.join(out_dir, "sites.inline.js")
    with open(paths["inline"], "w") as fh:
        fh.write("/* generated by fcf3d.build_sites - do not edit */\n")
        fh.write("window.__FCF_SITES__ = ")
        json.dump(fc, fh, separators=(",", ":"))
        fh.write(";\n")
    return paths


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="path to the Future-City-Fellowship repo")
    ap.add_argument("--out", default="explorer/web/data", help="output directory")
    ap.add_argument("--mode", default=DEFAULT_MODE, choices=list(MODES),
                    help=f"model mode to project (default: {DEFAULT_MODE}, the canonical one)")
    args = ap.parse_args(argv)

    sources = resolve_sources(args.repo, args.mode)
    frames = load(sources)
    result = build(frames, sources, args.mode)
    paths = write(result, args.out)

    print(f"[fcf3d] mode={args.mode} - {result.manifest['site_count']} sites -> {args.out}")
    for warning in result.warnings:
        print(f"  ! {warning}")
    for key, path in paths.items():
        print(f"  {key:9s} {path} ({os.path.getsize(path):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
