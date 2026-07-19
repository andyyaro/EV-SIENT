"""Lifecycle-cost module (PY-11), implementing the research lifecycle specification.

Cases per site, cash flows per year 2026–2056:
- OVB  (overbuild):  energize the full future-ready pathway in 2026.
- STG  (staged):     energize starter ports 2026; pre-build pathway; energize more
                     ports when horizon activation targets rise (trigger-year proxy).
- DEF  (defer):      pathway only; no active ports (floor comparator).

Principal measures: net present cost (NPC) / total cost of ownership at each horizon,
and avoided cost = NPC(OVB) − NPC(STG). ROI is deliberately NOT computed (research
Report 09: no honest revenue line exists for free/low-fee public charging).

Every input is a screening benchmark (config.ECON, provenance in config.ECON_PROVENANCE).
Outputs must always be labeled screening/planning estimates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import BASELINE_YEAR, ECON, ENERGY_PER_SESSION_KWH, V3_HORIZONS

END_YEAR = 2056
YEARS = list(range(BASELINE_YEAR, END_YEAR + 1))


@dataclass
class SiteCostInputs:
    site_id: str
    ports_now: int
    ports_pathway: int
    # activation targets by horizon year for the staged path (base case)
    staged_targets: dict          # {2036: n, 2046: n, 2056: n}
    trenching_ft: float
    trench_cost_per_ft: float
    service_upgrade_cost_usd: float
    sessions_day_by_year: dict    # {year: sessions/day at active build-out}


def civil_cost(inputs: SiteCostInputs, esc: float, year_offset: int, retrofit: bool = False) -> float:
    base = inputs.trenching_ft * inputs.trench_cost_per_ft + inputs.service_upgrade_cost_usd
    base *= (1 + ECON["contingency_civil_share"])
    if retrofit:
        base *= ECON["retrofit_civil_multiplier"]
    return base * ((1 + esc) ** year_offset)


def hardware_cost(n_ports: int, esc: float, year_offset: int) -> float:
    unit = ECON["hardware_usd_per_port"] * (1 + ECON["install_soft_cost_share"])
    return n_ports * unit * ((1 + esc) ** year_offset)


def active_ports_profile(case: str, inputs: SiteCostInputs) -> dict:
    """Active ports per year for a case."""
    profile = {}
    active = 0
    for year in YEARS:
        if case == "OVB":
            active = inputs.ports_pathway if year >= BASELINE_YEAR else 0
        elif case == "STG":
            if year == BASELINE_YEAR:
                active = inputs.ports_now
            for hy in V3_HORIZONS:
                # trigger-year proxy: ramp to each horizon target 2 years before the horizon
                if year == hy - 2:
                    active = max(active, min(inputs.staged_targets.get(hy, active), inputs.ports_pathway))
        elif case == "DEF":
            active = 0
        profile[year] = active
    return profile


def annual_cash_flows(case: str, inputs: SiteCostInputs, esc: float) -> pd.DataFrame:
    """Nominal cash flows per year for one site and case."""
    ports = active_ports_profile(case, inputs)
    rows = []
    prev_active = 0
    for year in YEARS:
        t = year - BASELINE_YEAR
        capex = 0.0
        notes = []

        if year == BASELINE_YEAR:
            # initial civil work: all cases build the pathway (STG/DEF pay the pathway premium;
            # OVB trenches for everything at once)
            base_civil = civil_cost(inputs, esc, 0)
            if case in ("STG", "DEF"):
                capex += base_civil * (1 + ECON["pathway_premium_share"])
                notes.append("civil+pathway premium")
            else:
                capex += base_civil
                notes.append("civil full buildout")

        added = ports[year] - prev_active
        if added > 0:
            capex += hardware_cost(added, esc, t)
            notes.append(f"+{added} ports hardware")
            if case == "STG" and year > BASELINE_YEAR:
                # expansion inside pre-built pathway: light install work (20% of a fresh civil run)
                capex += 0.2 * civil_cost(inputs, esc, t)
                notes.append("pathway expansion install")

        # replacement ~year 10 for ports active since baseline
        if t == ECON["replacement_year_offset"] and ports[year] > 0:
            capex += ports[year] * ECON["replacement_usd_per_port"] * ((1 + esc) ** t)
            notes.append("electronics refresh")

        active = ports[year]
        opex = active * (ECON["network_fee_usd_per_port_yr"] + ECON["maintenance_usd_per_port_yr"])
        opex += ECON["inspection_admin_usd_per_site_yr"] if active > 0 else 0.0
        sessions = inputs.sessions_day_by_year.get(year, 0.0)
        # energy served is capped by active port throughput implicitly via sessions input
        energy_kwh = sessions * ENERGY_PER_SESSION_KWH * 365 if active > 0 else 0.0
        opex += energy_kwh * ECON["tariff_usd_per_kwh"]
        opex *= (1 + esc) ** t

        # decommissioning in OVB end-state for never-needed ports (client's Neabsco pattern):
        decomm = 0.0
        if case == "OVB" and year == END_YEAR:
            unneeded = max(0, inputs.ports_pathway - inputs.staged_targets.get(2056, inputs.ports_now))
            decomm = unneeded * ECON["decommission_usd_per_port"] * ((1 + esc) ** t)
            if unneeded:
                notes.append(f"decommission {unneeded} unneeded ports")

        rows.append({"year": year, "active_ports": active, "capex_usd": capex,
                     "opex_usd": opex, "decommission_usd": decomm,
                     "total_usd": capex + opex + decomm, "notes": "; ".join(notes)})
        prev_active = ports[year]
    return pd.DataFrame(rows)


def npc_at_horizons(flows: pd.DataFrame, discount: float) -> dict:
    """Cumulative nominal and discounted cost at each horizon year."""
    out = {}
    for hy in V3_HORIZONS:
        window = flows[flows["year"] <= hy]
        t = window["year"] - BASELINE_YEAR
        nominal = float(window["total_usd"].sum())
        npv = float((window["total_usd"] / (1 + discount) ** t).sum())
        out[hy] = {"nominal": round(nominal, 0), "npv": round(npv, 0)}
    return out


def compare_cases(inputs: SiteCostInputs, escalation_case: str = "base") -> pd.DataFrame:
    """NPC comparison rows for one site: OVB vs STG vs DEF at 2036/2046/2056."""
    esc = ECON["escalation"][escalation_case]
    disc = ECON["discount_rate_real"]
    rows = []
    flows = {case: annual_cash_flows(case, inputs, esc) for case in ("OVB", "STG", "DEF")}
    npcs = {case: npc_at_horizons(f, disc) for case, f in flows.items()}
    for hy in V3_HORIZONS:
        avoided_nominal = npcs["OVB"][hy]["nominal"] - npcs["STG"][hy]["nominal"]
        avoided_npv = npcs["OVB"][hy]["npv"] - npcs["STG"][hy]["npv"]
        for case in ("OVB", "STG", "DEF"):
            rows.append({
                "site_id": inputs.site_id,
                "horizon_year": hy,
                "cost_case": case,
                "escalation_case": escalation_case,
                "discount_rate_real": disc,
                "lifecycle_cost_nominal_usd": npcs[case][hy]["nominal"],
                "lifecycle_cost_npv_usd": npcs[case][hy]["npv"],
                "avoided_overbuild_cost_usd": round(avoided_npv, 0) if case == "STG" else 0.0,
                "avoided_overbuild_cost_nominal_usd": round(avoided_nominal, 0) if case == "STG" else 0.0,
                "estimate_class": "screening_planning_estimate",
            })
    return pd.DataFrame(rows)


def portfolio_summary(all_rows: pd.DataFrame) -> pd.DataFrame:
    """Portfolio totals per horizon/cost case/escalation case."""
    g = (all_rows.groupby(["horizon_year", "cost_case", "escalation_case"])
         [["lifecycle_cost_nominal_usd", "lifecycle_cost_npv_usd",
           "avoided_overbuild_cost_usd", "avoided_overbuild_cost_nominal_usd"]]
         .sum().round(0).reset_index())
    g["estimate_class"] = "screening_planning_estimate"
    return g
