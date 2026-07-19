"""Automated MATLAB adapter (PY-14): generate MATLAB input from the canonical contract.

Replaces the hand-built ``site_year_scenarios_from_andy_v2.csv``. Every row carries
``capacity_basis``; placeholder capacity triggers a visible warning both here and in
the MATLAB-side guard (ML-04).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MATLAB_COLUMNS = [
    "scenario_id", "site_id", "site_name", "horizon_year", "case", "ports",
    "charger_power_kW", "spare_capacity_kW", "service_capacity_kW", "capacity_basis",
    "capacity_source", "base_load_mean_kW", "base_load_peak_kW", "arrival_start_hr",
    "arrival_end_hr", "dwell_hr", "sessions_per_day", "energy_per_session_kWh",
    "managed_charging_policy", "model_rank", "electrical_risk_level", "source_note",
]


def build_matlab_input(scenario_table: pd.DataFrame, site_meta: pd.DataFrame,
                       out_path: str | Path) -> pd.DataFrame:
    """Project the contract onto the MATLAB input schema.

    site_meta must carry: site_id, arrival_start_hr, arrival_end_hr, base_load_mean_kw,
    base_load_peak_kw, model_rank, electrical_risk_level.
    """
    meta = site_meta.set_index("site_id")
    rows = []
    warned = 0
    for _, r in scenario_table.iterrows():
        sid = r["site_id"]
        m = meta.loc[sid]
        placeholder = r["capacity_basis"] not in ("verified_utility", "verified_facility")
        if placeholder:
            warned += 1
        rows.append({
            "scenario_id": r["scenario_id"],
            "site_id": sid,
            "site_name": r["site_name"],
            "horizon_year": int(r["horizon_year"]),
            "case": r["scenario_name"],
            "ports": int(r["ports_active"]),
            "charger_power_kW": r["evse_power_kw"],
            "spare_capacity_kW": r["spare_capacity_kw"] if pd.notna(r["spare_capacity_kw"]) else "",
            "service_capacity_kW": r["service_capacity_kw"] if pd.notna(r["service_capacity_kw"]) else "",
            "capacity_basis": r["capacity_basis"],
            "capacity_source": r["capacity_source"],
            "base_load_mean_kW": float(m["base_load_mean_kw"]),
            "base_load_peak_kW": float(m["base_load_peak_kw"]),
            "arrival_start_hr": float(m["arrival_start_hr"]),
            "arrival_end_hr": float(m["arrival_end_hr"]),
            "dwell_hr": float(r["average_dwell_hr"]),
            "sessions_per_day": float(r["sessions_per_day"]),
            "energy_per_session_kWh": float(r["energy_per_session_kwh"]),
            "managed_charging_policy": r["managed_charging_policy"],
            "model_rank": int(m["model_rank"]),
            "electrical_risk_level": m["electrical_risk_level"],
            "source_note": (
                f"Generated from canonical contract {r['contract_version']} run {r['run_id']}. "
                + ("CAPACITY IS A PLANNING PLACEHOLDER - no feasibility claim permitted. "
                   if placeholder else "Capacity verified. ")
                + "Do not hand-edit; regenerate via fcf_m2.matlab_adapter."
            ),
        })
    df = pd.DataFrame(rows, columns=MATLAB_COLUMNS)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    if warned:
        print(f"WARNING: {warned}/{len(df)} MATLAB scenario rows carry non-verified capacity_basis "
              "- placeholder captions are mandatory on every capacity visual.")
    return df
