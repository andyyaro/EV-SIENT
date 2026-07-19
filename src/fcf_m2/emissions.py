"""Emissions and environmental outcome layer (PY-12).

Net CO2e = displaced gasoline emissions − charging grid emissions, with every factor
carrying source + vintage. Also computes the avoided-EVSE resource metric (M4) and an
optional renewable-matched scenario. Negative or counterintuitive values are reported
as computed — never clipped.

Baseline definition (required for any 'avoided' claim): each kWh delivered displaces
gasoline miles at EV_EFFICIENCY_KWH_PER_MI driven instead of a gasoline LDV emitting
DISPLACED_GASOLINE_G_CO2_PER_MI. Both are labeled benchmark assumptions.
"""

from __future__ import annotations

import pandas as pd

from .config import (
    CHARGER_EFFICIENCY,
    DISPLACED_GASOLINE_G_CO2_PER_MI,
    ENERGY_PER_SESSION_KWH,
    EV_EFFICIENCY_KWH_PER_MI,
    GRID_FACTOR_LB_PER_MWH,
    GRID_FACTOR_NEXT_REFRESH,
    GRID_FACTOR_SOURCE,
    GRID_FACTOR_VINTAGE,
    LB_TO_KG,
)


def annual_energy_delivered_kwh(sessions_day: float, active_ports: int) -> float:
    """Energy delivered to vehicles per year. Zero when no ports are active."""
    if active_ports <= 0:
        return 0.0
    return sessions_day * ENERGY_PER_SESSION_KWH * 365.0


def net_co2e_kg(energy_delivered_kwh: float, renewable_matched_share: float = 0.0) -> dict:
    """Net avoided CO2e for a year's delivered energy.

    grid emissions   = grid energy (delivered / charger efficiency) x grid factor
    displaced        = miles enabled x gasoline LDV rate
    net avoided      = displaced − grid  (may be negative; reported as computed)
    """
    grid_energy_mwh = (energy_delivered_kwh / CHARGER_EFFICIENCY) / 1000.0
    effective_factor = GRID_FACTOR_LB_PER_MWH * (1.0 - renewable_matched_share)
    grid_kg = grid_energy_mwh * effective_factor * LB_TO_KG

    miles = energy_delivered_kwh / EV_EFFICIENCY_KWH_PER_MI
    displaced_kg = miles * DISPLACED_GASOLINE_G_CO2_PER_MI / 1000.0

    return {
        "energy_delivered_kwh": round(energy_delivered_kwh, 1),
        "grid_emissions_kg": round(grid_kg, 1),
        "displaced_tailpipe_kg": round(displaced_kg, 1),
        "net_co2e_avoided_kg": round(displaced_kg - grid_kg, 1),
        "renewable_matched_share": renewable_matched_share,
        "grid_factor_value": GRID_FACTOR_LB_PER_MWH,
        "grid_factor_units": "lb CO2e/MWh",
        "grid_factor_source": GRID_FACTOR_SOURCE,
        "grid_factor_vintage": GRID_FACTOR_VINTAGE,
        "grid_factor_next_refresh": GRID_FACTOR_NEXT_REFRESH,
        "assumption_note": (
            f"energy/session {ENERGY_PER_SESSION_KWH} kWh (benchmark); EV efficiency "
            f"{EV_EFFICIENCY_KWH_PER_MI} kWh/mi (EPA-class benchmark); displaced gasoline LDV "
            f"{DISPLACED_GASOLINE_G_CO2_PER_MI} gCO2/mi (fleet-average-class benchmark); charger "
            f"efficiency {CHARGER_EFFICIENCY}. No observed baseline exists yet - values are "
            "screening estimates, not measured reductions."
        ),
    }


def avoided_evse_metric(scenarios: pd.DataFrame) -> pd.DataFrame:
    """M4: pathway ports not energized = avoided hardware/fees/embodied resources.

    Grounded in the client's decommissioning experience (17 of 70 ports taken offline).
    """
    df = scenarios.copy()
    df["avoided_active_evse_ports"] = (df["ports_pathway"] - df["ports_active"]).clip(lower=0)
    df["avoided_network_fee_usd_yr"] = df["avoided_active_evse_ports"] * 1000.0
    df["avoided_evse_note"] = (
        "Ports kept as pathway-only capacity instead of energized hardware; avoided annual "
        "network/maintenance fees use the client's ~$1k/station/yr operating frame (screening)."
    )
    return df[["site_id", "horizon_year", "case", "avoided_active_evse_ports",
               "avoided_network_fee_usd_yr", "avoided_evse_note"]]
