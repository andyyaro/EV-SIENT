"""Central configuration for the FCF Milestone 2 V3 model.

Two explicit model modes:

- ``legacy_v2``      - reproduces the accepted V2 baseline exactly (cohort-relative
                       min-max scoring, 2035/2050 horizons, legacy multipliers).
- ``milestone2_v3``  - canonical 2026 baseline + 2036/2046/2056 horizons, fixed-anchor
                       scoring, structured confidence, economics and emissions layers.

Most result-changing constants live here with their provenance labels, and new ones
belong here. Some still sit in the module that uses them -- the scoring subscore weights
in ``scoring.py``, the confidence field weights and thresholds in ``confidence.py``, the
base-load growth rate in ``workflow.py``, the demand calibration guards in ``demand.py``.
Those are named rather than hidden, because a docstring claiming completeness it does not
have is how a reader stops looking. Nothing in this file asserts external approval: multipliers are provisional planning conventions
pending calibration, and cost/emission inputs are screening benchmarks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "1.0.0"
#: Contract v2 is ADDITIVE over v1: every v1 field survives with identical semantics, and
#: v2 adds the fields the V4 field-data loop produces. v1 is frozen -- see
#: tests/test_contract_v2.py, which pins its manifest digest so a change to it fails.
SCHEMA_VERSION_V2 = "2.0.0"
CONTRACT_VERSIONS = (SCHEMA_VERSION, SCHEMA_VERSION_V2)
MODEL_VERSION = "3.0.0"
#: Bumped to 4.0.0 only when V4 is genuinely complete, per the program's own rule.
MODEL_VERSION_V4 = "4.0.0"
ANCHOR_SET_VERSION = "anchors_v1_2026-07"

MODE_LEGACY = "legacy_v2"
MODE_V3 = "milestone2_v3"
#: V4 is a THIRD mode, not a replacement. legacy_v2 must still reproduce bit-exact and
#: milestone2_v3 must still reproduce; V4 adds the observed-data loop on top of them.
MODE_V4 = "v4"

#: The recommendation tiers' thresholds (`scoring.recommendation_tier`). Named here, rather
#: than left as literals, because one of them is a policy with a consequence nobody had
#: written down (F-09, 2026-10-17): **Tier 1 is relative to the cohort.** It requires a rank
#: of TIER1_MAX_RANK or better, so at most two sites can hold it in any run, however many sites
#: the run has and however they score - while the v3 SCORES are built to be cohort-independent.
#: A Tier 1 site in one run and a Tier 2 site in another can therefore have the same score.
#: Compare scores across cohorts, never tiers. Changing a value here re-baselines the
#: right-sizing floors that key on the tier, and with them RT-04's 25 / 48.
TIER1_MAX_RANK = 2
TIER1_MIN_SCORE = 50
TIER2_MIN_SCORE = 45

BASELINE_YEAR = 2026
V3_HORIZONS = [2036, 2046, 2056]
V3_HORIZON_LABELS = {2026: "now", 2036: "plus10", 2046: "plus20", 2056: "plus30"}

# Legacy growth multipliers (accepted V2 baseline; DO NOT CHANGE).
LEGACY_GROWTH_MULTIPLIERS = {
    "now": 1.0,
    "2035_base": 1.8,
    "2035_high": 2.5,
    "2050_base": 3.0,
    "2050_high": 4.5,
}

# V3 growth multipliers - provisional planning conventions per research Report 05 §3.
# Status: synthetic_uncalibrated. Replace with an adoption-curve model once observed
# session data and local EV-registration trends are available (see demand.py).
V3_GROWTH_MULTIPLIERS = {
    (2026, "baseline"): 1.0,
    (2036, "base"): 1.9,
    (2036, "high"): 2.6,
    (2046, "base"): 3.0,
    (2046, "high"): 4.5,
    (2056, "base"): 4.0,
    (2056, "high"): 6.0,
}
V3_STRESS_EXTRA = 1.15  # stress_combined = high multiplier x 1.15 (matches legacy stress-test spirit)

GROWTH_PROVENANCE = (
    "Provisional planning convention (research Report 05 s3): 2036 re-anchors the legacy "
    "2035 cases; 2046 inherits the legacy 2050 cases on the evidence that regional adoption "
    "is front-loaded; 2056 extends with saturation capped by pathway capacity. "
    "Status: synthetic_uncalibrated - pending team adoption and observed-data calibration."
)

EVSE_POWER_KW = 19.2          # AC Level 2, per legacy model and MATLAB adapter
CHARGER_EFFICIENCY = 0.92     # wall-to-battery; benchmark assumption, label on outputs

# Demand-model coefficients (legacy formula, PY-03): synthetic, uncalibrated.
DEMAND_MODEL_STATUS = "synthetic_uncalibrated"
DEMAND_COEFFICIENTS = {
    "visitors_day": 0.0015,
    "employees_day": 0.0006,
    "nearby_jobs_1mi": 0.00002,
    "nearby_households_1mi": 0.00003,  # multiplied by (1 + ev_share_local)
}
DEMAND_FLOOR_SESSIONS = 0.3
DEMAND_COEFFICIENT_PROVENANCE = (
    "Coefficients are synthetic screening values chosen by the team for the V2 prototype; "
    "no published derivation exists. They must not be presented as calibrated. "
    "Calibration path: fcf_m2.demand.calibrate() with observed session data."
)

# Queueing (legacy, PY-04 preserved screen)
TARGET_UTILIZATION = 0.70
MAX_MEAN_WAIT_MIN = 10.0
MAX_PORTS_SEARCH = 20

# Peak-period modeling (PY-04 additions)
PEAK_WINDOW_SHARE = 0.55      # share of daily sessions arriving inside the peak window
PEAK_WINDOW_HOURS = 4.0
SIM_RANDOM_SEED = 20260719
SIM_N_DAYS = 400              # simulated days for P10/P50/P90 wait statistics

# Energy / emissions (PY-12). Each value carries provenance in assumptions.json.
ENERGY_PER_SESSION_KWH = 9.5  # benchmark assumption: typical public L2 session 8-12 kWh (AFDC-class benchmark). TBV with observed data.
GRID_FACTOR_LB_PER_MWH = 596.3
GRID_FACTOR_SOURCE = "EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, total output emission rate CO2e"
GRID_FACTOR_VINTAGE = "eGRID2023r2, accessed 2026-07-19"
GRID_FACTOR_NEXT_REFRESH = "eGRID2024 (preliminary API data available 2026; re-pull official release annually)"
EV_EFFICIENCY_KWH_PER_MI = 0.30   # EPA-class light-duty EV benchmark; assumption label required
DISPLACED_GASOLINE_G_CO2_PER_MI = 400.0  # EPA fleet-average-class benchmark for displaced gasoline LDV; assumption label required
LB_TO_KG = 0.45359237

# Economics (PY-11) - screening/planning estimates, never budgets.
ECON = {
    "hardware_usd_per_port": 6500.0,        # listed dual-port L2 pedestal per-port hardware benchmark; vendor quote TBV
    "install_soft_cost_share": 0.25,        # NREL: soft costs can exceed 50% on some projects; 25% screening midpoint
    "pathway_premium_share": 0.15,          # extra conduit/panel space during initial civil work (client evidence: small vs retrofit)
    "retrofit_civil_multiplier": 1.8,       # re-trench premium when no pathway exists (sensitivity-tested)
    "network_fee_usd_per_port_yr": 1000.0,  # [client contact] operating frame (~$1k/station/yr)
    "maintenance_usd_per_port_yr": 400.0,   # AFDC/DOE L2 benchmark
    "tariff_usd_per_kwh": 0.11,             # placeholder commercial energy rate; Dominion tariff TBV
    "demand_charge_usd_per_kw_month": 0.0,  # unknown without tariff; 0 with explicit "not modeled" label unless supplied
    "replacement_usd_per_port": 2500.0,     # ~year-10 electronics refresh benchmark
    "replacement_year_offset": 10,
    "decommission_usd_per_port": 800.0,     # order-of-magnitude from county decommissioning experience class
    "inspection_admin_usd_per_site_yr": 300.0,
    "contingency_civil_share": 0.25,        # screening-class estimate contingency
    "discount_rate_real": 0.03,             # OMB A-94-style real rate class; planning assumption, stated on outputs
    "escalation": {"low": 0.01, "base": 0.025, "high": 0.04},
}
ECON_PROVENANCE = (
    "All cost lines are screening/planning benchmarks (AFDC/NREL cost classes + client operating "
    "evidence). None are quotes, budgets, or engineering estimates. Site quotes, the Dominion tariff, "
    "and vendor fee schedules are required before any budget use."
)

# Expansion-trigger policy defaults (PY-20) - PROPOSED configuration, not adopted policy.
TRIGGER_POLICY = {
    "policy_status": "proposed_default_pending_team_and_client_adoption",
    "utilization_threshold": 0.40,      # sustained average utilization
    "wait_threshold_min": 10.0,         # repeated mean-wait events
    "reliability_uptime_min": 0.97,     # NEVI-benchmark uptime before expansion decisions rely on data
    "min_observation_months": 6,
    "equity_override": {
        "enabled": True,
        "equity_index_percentile_min": 0.60,   # site in top 40% equity-gap need
        "reduced_utilization_threshold": 0.25, # lower bar so low-adoption areas are not starved
        "note": "Equity override allows expansion review at lower observed utilization in high-equity-need areas; requires the same human approval gate.",
    },
    "budget_gate": "human_approval_required",
    "pathway_gate": "ports_active_plus_step_must_not_exceed_ports_pathway",
}

CAPACITY_BASIS_VALUES = [
    "verified_utility",
    "verified_facility",
    "engineering_estimate",
    "planning_proxy",
    "placeholder",
    "unknown",
]

JURISDICTIONS = {"FFX": "fairfax", "PWC": "pwc"}


@dataclass
class RunConfig:
    mode: str = MODE_V3
    baseline_year: int = BASELINE_YEAR
    horizons: list[int] = field(default_factory=lambda: list(V3_HORIZONS))
    anchor_set: str = ANCHOR_SET_VERSION
    seed: int = SIM_RANDOM_SEED


def jurisdiction_for(site_id: str) -> str:
    prefix = str(site_id)[:3].upper()
    if prefix == "FFX":
        return "fairfax"
    if prefix == "PWC":
        return "pwc"
    # Synthetic sites belong to no real jurisdiction, and saying so is the point: a run on
    # invented data must not be able to claim Fairfax City or Prince William County. Returning
    # "unknown" would have been ambiguous with a genuine data gap.
    if prefix == "SYN":
        return "synthetic"
    return "unknown"
