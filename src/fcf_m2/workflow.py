"""V3 workflow orchestrator and single source of truth for workflow steps (PY-09).

Run:  python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/<run>
      python -m fcf_m2.workflow run --mode legacy_v2   --out data/outputs/<run>
      python -m fcf_m2.workflow validate-contract <contract_dir>
      python -m fcf_m2.workflow docs

The STEPS manifest below is the only place workflow steps are defined; the generated
docs (docs/WORKFLOW_STEPS.md) and tests both derive from it, eliminating doc drift.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, contract, demand, economics, emissions, peak_wait, standards, triggers
from .confidence import build_confidence
from .config import (
    BASELINE_YEAR, ENERGY_PER_SESSION_KWH, EVSE_POWER_KW, GRID_FACTOR_VINTAGE,
    MODE_LEGACY, MODE_V3, SCHEMA_VERSION, V3_GROWTH_MULTIPLIERS, V3_HORIZON_LABELS,
    V3_HORIZONS, V3_STRESS_EXTRA, jurisdiction_for,
)
from .queueing import erlang_c
from .right_sizing import run_right_sizing_legacy, run_right_sizing_v3
from .scoring import add_tiers, enrich_and_score, load_anchor_set

ROOT = Path(__file__).resolve().parents[2]
BASE_LOAD_GROWTH_PER_YEAR = 0.008  # commercial base-load growth planning proxy (labeled assumption)

STEPS = [
    ("load_inputs", "Load site table, electrical-risk fixture, provenance, anchors, MATLAB site meta"),
    ("score_sites", "Score readiness (legacy min-max or V3 fixed anchors) + Erlang-C port screen"),
    ("right_sizing", "Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056)"),
    ("confidence", "Structured field-level data confidence (V3) / legacy confidence passthrough"),
    ("peak_wait", "Peak-window Erlang and seeded discrete-event wait simulation (P10/P50/P90)"),
    ("economics", "Lifecycle NPC: staged vs overbuild vs defer at 2036/2046/2056, low/base/high"),
    ("emissions", "Net avoided CO2e with sourced grid factor + avoided-EVSE resource metric"),
    ("scenario_table", "Assemble canonical scenario rows (all required contract fields)"),
    ("contract", "Validate + write versioned hybrid CSV/JSON contract with manifest hashes"),
    ("matlab_adapter", "Generate MATLAB input CSV from the contract (capacity_basis on every row)"),
    ("summary", "Write run summary with headline totals and claims-discipline labels"),
]


def generate_docs() -> str:
    lines = ["# V3 Workflow Steps (generated from fcf_m2.workflow.STEPS — do not edit by hand)", ""]
    lines.append(f"Step count: **{len(STEPS)}**")
    lines.append("")
    for i, (name, desc) in enumerate(STEPS, 1):
        lines.append(f"{i}. **{name}** — {desc}")
    lines.append("")
    return "\n".join(lines)


def _load_inputs():
    sites = pd.read_csv(ROOT / "data/inputs/real_sites_v2.csv")
    risk = pd.read_csv(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv")
    prov = pd.read_csv(ROOT / "data/provenance/field_provenance_v1.csv")
    meta = pd.read_csv(ROOT / "data/inputs/legacy_matlab_site_meta.csv")
    anchors = load_anchor_set(ROOT / "data/anchors/anchor_set_v1.json")
    return sites, risk, prov, meta, anchors


def _sessions_multiplier(year: int, case: str) -> float:
    if year == BASELINE_YEAR:
        return 1.0
    if case == "stress_combined":
        return V3_GROWTH_MULTIPLIERS[(year, "high")] * V3_STRESS_EXTRA
    return V3_GROWTH_MULTIPLIERS[(year, case)]


def _sessions_by_year(base_sessions: float, case: str) -> dict:
    """Linear interpolation of the horizon multipliers for annual cash flows."""
    pts = {BASELINE_YEAR: 1.0}
    for hy in V3_HORIZONS:
        pts[hy] = _sessions_multiplier(hy, case if case != "baseline" else "base")
    years = sorted(pts)
    out = {}
    for y in range(BASELINE_YEAR, 2057):
        for a, b in zip(years, years[1:]):
            if a <= y <= b:
                frac = (y - a) / (b - a)
                out[y] = base_sessions * (pts[a] + frac * (pts[b] - pts[a]))
                break
    return out


def run(mode: str, out_dir: Path, contract_dir: Path | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"{mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    generated_at = datetime.now(timezone.utc).isoformat()

    sites, risk, prov, meta, anchors = _load_inputs()

    # Right-sizing (ports/pathway) is always anchored to the ACCEPTED legacy baseline
    # (RT-04: 25 starter / 48 pathway must reconcile). V3 fixed-anchor scores are
    # reported alongside with a migration report — they do not silently re-baseline
    # the port structure (PY-02 deliberate-migration rule).
    scored_legacy = enrich_and_score(sites, mode=MODE_LEGACY)
    scored_legacy = scored_legacy.merge(risk[["site_id", "electrical_risk_level"]], on="site_id", how="left")
    scored_legacy = add_tiers(scored_legacy)

    if mode == MODE_V3:
        scored_v3 = enrich_and_score(sites, mode=MODE_V3, anchor_set=anchors)
        scored_v3 = scored_v3.merge(risk[["site_id", "electrical_risk_level"]], on="site_id", how="left")
        scored_v3 = add_tiers(scored_v3)
        scored_v3.to_csv(out_dir / "site_results_milestone2_v3.csv", index=False)
        migration = scored_legacy[["site_id", "site_name", "readiness_score", "model_rank"]].rename(
            columns={"readiness_score": "legacy_score", "model_rank": "legacy_rank"}).merge(
            scored_v3[["site_id", "readiness_score", "model_rank"]].rename(
                columns={"readiness_score": "v3_anchor_score", "model_rank": "v3_anchor_rank"}), on="site_id")
        migration["rank_change"] = migration["legacy_rank"] - migration["v3_anchor_rank"]
        migration["explanation"] = (
            "Fixed anchors widen normalization ranges beyond the cohort extremes, so cohort-extreme "
            "sites compress toward the middle; ranking changes are a property of anchor choice, not new data. "
            "Port/pathway structure remains anchored to the accepted legacy baseline pending deliberate re-baselining."
        )
        migration.to_csv(out_dir / "scoring_migration_report.csv", index=False)
        scored = scored_v3
    else:
        scored = scored_legacy
    scored_legacy.to_csv(out_dir / "site_results_legacy_v2.csv", index=False)

    legacy_rs = run_right_sizing_legacy(scored_legacy)
    legacy_rs.to_csv(out_dir / "right_sizing_legacy_2035_2050.csv", index=False)

    result = {"run_id": run_id, "mode": mode, "site_results": str(out_dir / f"site_results_{mode}.csv")}

    if mode == MODE_LEGACY:
        result["right_sizing"] = str(out_dir / "right_sizing_legacy_2035_2050.csv")
        result["starter_total"] = int(legacy_rs["ports_now"].sum())
        result["pathway_total"] = int(legacy_rs["future_ready_capacity"].sum())
        (out_dir / "run_summary.json").write_text(json.dumps(result, indent=2))
        return result

    # ---- V3 branch ----
    v3_rs = run_right_sizing_v3(scored_legacy)
    v3_rs.to_csv(out_dir / "right_sizing_v3_canonical.csv", index=False)

    conf = build_confidence(prov, list(scored["site_id"]))
    conf.to_csv(out_dir / "data_confidence_v3.csv", index=False)

    site_table = pd.DataFrame({
        "site_id": scored["site_id"],
        "site_name_display": scored["site_name"],
        "site_name_safe": scored["site_name"].str.replace(r"[^A-Za-z0-9]+", "_", regex=True).str.strip("_"),
        "jurisdiction": scored["site_id"].map(jurisdiction_for),
        "lat": scored.get("lat"), "lon": scored.get("lon"),
        "site_type": scored["site_type"],
        "public_access": scored["public_access"],
        "garage_enclosed": scored["garage_enclosed"],
    })

    scored_idx = scored_legacy.set_index("site_id")
    conf_idx = conf.set_index("site_id")
    meta_idx = meta.set_index("site_id")
    legacy_idx = legacy_rs.set_index("site_id")

    # peak/discrete-event stats at baseline ports (seeded, reproducible)
    peak_stats = {}
    for sid in scored["site_id"]:
        row = scored_idx.loc[sid]
        ports_now = int(legacy_idx.loc[sid, "ports_now"])
        dwell_hr = row["avg_dwell_min"] / 60 if row["avg_dwell_min"] > 0 else 2
        sim = peak_wait.simulate_waits(row["expected_sessions_day"], dwell_hr, row["hours_open"], ports_now)
        pk_wait, _ = peak_wait.peak_window_wait(row["expected_sessions_day"], dwell_hr, row["hours_open"], ports_now)
        peak_stats[sid] = {"sim": sim, "peak_erlang_wait_min": pk_wait}
    pd.DataFrame([
        {"site_id": sid, "ports": s["sim"].ports, "mean_wait_min": s["sim"].mean_wait_min,
         "p10_wait_min": s["sim"].p10_wait_min, "p50_wait_min": s["sim"].p50_wait_min,
         "p90_wait_min": s["sim"].p90_wait_min, "peak_p90_wait_min": s["sim"].peak_p90_wait_min,
         "peak_erlang_wait_min": s["peak_erlang_wait_min"], "sim_utilization": s["sim"].mean_utilization,
         "seed": s["sim"].seed}
        for sid, s in peak_stats.items()
    ]).to_csv(out_dir / "peak_wait_simulation.csv", index=False)

    # economics per site (staged targets = base case trajectory)
    econ_rows = []
    for sid in scored["site_id"]:
        row = scored_idx.loc[sid]
        sub = v3_rs[(v3_rs["site_id"] == sid)]
        staged_targets = {hy: int(sub[(sub["horizon_year"] == hy) & (sub["case"] == "base")]["ports_active"].iloc[0])
                          for hy in V3_HORIZONS}
        inputs = economics.SiteCostInputs(
            site_id=sid,
            ports_now=int(legacy_idx.loc[sid, "ports_now"]),
            ports_pathway=int(sub["ports_pathway"].max()),
            staged_targets=staged_targets,
            trenching_ft=float(row["trenching_ft"]),
            trench_cost_per_ft=float(row["trench_cost_per_ft"]),
            service_upgrade_cost_usd=float(row["service_upgrade_cost_usd"]),
            sessions_day_by_year=_sessions_by_year(float(row["expected_sessions_day"]), "base"),
        )
        for esc_case in ("low", "base", "high"):
            econ_rows.append(economics.compare_cases(inputs, esc_case))
    econ_all = pd.concat(econ_rows, ignore_index=True)
    econ_all.to_csv(out_dir / "lifecycle_costs.csv", index=False)
    economics.portfolio_summary(econ_all).to_csv(out_dir / "lifecycle_costs_portfolio.csv", index=False)
    econ_idx = econ_all[(econ_all["escalation_case"] == "base")].set_index(["site_id", "horizon_year", "cost_case"])

    # scenario table assembly
    rows = []
    for _, s in v3_rs.iterrows():
        sid, year, case = s["site_id"], int(s["horizon_year"]), s["case"]
        row = scored_idx.loc[sid]
        m = meta_idx.loc[sid]
        mult = _sessions_multiplier(year, case)
        sessions = float(row["expected_sessions_day"]) * mult
        ports = int(s["ports_active"])
        dwell_hr = row["avg_dwell_min"] / 60 if row["avg_dwell_min"] > 0 else 2
        hours = float(row["hours_open"])
        lam, mu = sessions / max(hours, 1), 1 / max(dwell_hr, 0.1)
        _, wait_hr, util = erlang_c(lam, mu, ports) if ports > 0 else (np.nan, np.nan, np.nan)
        wait_min = float(wait_hr * 60) if np.isfinite(wait_hr) else None
        pk_wait_min, _ = peak_wait.peak_window_wait(sessions, dwell_hr, hours, ports) if ports > 0 else (None, None)
        energy_day = round(sessions * ENERGY_PER_SESSION_KWH, 2)
        base_load = float(m["base_load_mean_kw"]) * ((1 + BASE_LOAD_GROWTH_PER_YEAR) ** (year - BASELINE_YEAR))
        annual_kwh = round(energy_day * 365.0, 1) if ports > 0 else 0.0
        em = emissions.net_co2e_kg(annual_kwh)

        if year == BASELINE_YEAR:
            cost_nom = cost_npv = avoided = None
        else:
            k = (sid, year, "STG")
            cost_nom = float(econ_idx.loc[k, "lifecycle_cost_nominal_usd"])
            cost_npv = float(econ_idx.loc[k, "lifecycle_cost_npv_usd"])
            avoided = float(econ_idx.loc[k, "avoided_overbuild_cost_usd"])

        rows.append({
            "contract_version": SCHEMA_VERSION,
            "run_id": run_id,
            "generated_at": generated_at,
            "site_id": sid,
            "site_name": row["site_name"],
            "jurisdiction": jurisdiction_for(sid),
            "site_type": row["site_type"],
            "public_or_fleet": "public" if row["public_access"] >= 1 else "mixed",
            "horizon_year": year,
            "horizon_label": V3_HORIZON_LABELS[year],
            "scenario_id": f"{sid}_{year}_{case}",
            "scenario_name": case,
            "model_mode": MODE_V3,
            "ports_active": ports,
            "ports_pathway_capacity": int(s["ports_pathway"]),
            "evse_power_kw": EVSE_POWER_KW,
            "sessions_per_day": round(sessions, 3),
            "energy_per_session_kwh": ENERGY_PER_SESSION_KWH,
            "energy_required_kwh_day": energy_day,
            "charging_window_hr": round(float(m["arrival_end_hr"]) - float(m["arrival_start_hr"]), 2),
            "average_dwell_hr": round(dwell_hr, 2),
            "peak_factor": config.PEAK_WINDOW_SHARE / (config.PEAK_WINDOW_HOURS / max(hours, 1)),
            "utilization": round(float(util), 4) if np.isfinite(util) else None,
            "average_wait_minutes": round(wait_min, 2) if wait_min is not None else None,
            "peak_wait_minutes": round(pk_wait_min, 2) if pk_wait_min is not None and np.isfinite(pk_wait_min) else None,
            "base_load_kw": round(base_load, 1),
            "service_capacity_kw": None,
            "spare_capacity_kw": None,
            "capacity_basis": "placeholder",
            "capacity_source": "legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)",
            "capacity_confidence": "none",
            "managed_charging_policy": "none",
            "energy_delivered_kwh": annual_kwh,
            "energy_curtailed_kwh": 0.0,
            "lifecycle_cost_nominal_usd": cost_nom,
            "lifecycle_cost_npv_usd": cost_npv,
            "avoided_overbuild_cost_usd": avoided,
            "grid_factor_value": em["grid_factor_value"],
            "grid_factor_units": em["grid_factor_units"],
            "grid_factor_vintage": GRID_FACTOR_VINTAGE,
            "net_co2e_kg": em["net_co2e_avoided_kg"] if ports > 0 else 0.0,
            "data_confidence": conf_idx.loc[sid, "data_confidence_level_v3"],
            "equity_indicator": round(float(row["equity_gap_index"]), 3),
            "expansion_trigger_status": triggers.status_for_contract(False),
            "source_date": "2026-06-24",
            "source_id": "real_sites_v2+frozen_v2_outputs+anchors_v1",
            "assumption_flag": "growth multipliers provisional; demand synthetic_uncalibrated; capacity placeholder; costs screening-class; emissions benchmark assumptions",
            "notes": str(s["right_sizing_reason"]),
        })
    scenario_table = pd.DataFrame(rows)

    avoided_evse = emissions.avoided_evse_metric(
        scenario_table.rename(columns={"scenario_name": "case", "ports_pathway_capacity": "ports_pathway"})
        [["site_id", "horizon_year", "case", "ports_active", "ports_pathway"]])
    avoided_evse.to_csv(out_dir / "avoided_evse_metric.csv", index=False)

    assumptions = {
        "growth_multipliers": {f"{y}_{c}": v for (y, c), v in V3_GROWTH_MULTIPLIERS.items()},
        "growth_provenance": config.GROWTH_PROVENANCE,
        "stress_extra_multiplier": V3_STRESS_EXTRA,
        "demand_model": json.loads(json.dumps(demand.current_model_record().__dict__)),
        "base_load_growth_per_year": {"value": BASE_LOAD_GROWTH_PER_YEAR,
                                      "label": "commercial base-load growth planning proxy (assumption; facility interval data pending)"},
        "energy_per_session_kwh": {"value": ENERGY_PER_SESSION_KWH, "label": "benchmark assumption (typical public L2 session), TBV with observed data"},
        "economics": {**config.ECON, "provenance": config.ECON_PROVENANCE},
        "emissions": emissions.net_co2e_kg(1000.0),
        "trigger_policy": config.TRIGGER_POLICY,
        "capacity": "service/spare capacity NULL with capacity_basis=placeholder at all 12 sites until utility/facility confirmation",
    }

    std_register = standards.build_register(site_table)
    std_register.to_csv(out_dir / "standards_register.csv", index=False)

    cdir = contract_dir or (out_dir / "contract")
    inputs_hashed = {
        "real_sites_v2.csv": contract.sha256_file(ROOT / "data/inputs/real_sites_v2.csv"),
        "legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv":
            contract.sha256_file(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv"),
        "field_provenance_v1.csv": contract.sha256_file(ROOT / "data/provenance/field_provenance_v1.csv"),
        "anchor_set_v1.json": contract.sha256_file(ROOT / "data/anchors/anchor_set_v1.json"),
        "legacy_matlab_site_meta.csv": contract.sha256_file(ROOT / "data/inputs/legacy_matlab_site_meta.csv"),
    }
    contract.write_contract(cdir, scenario_table, site_table, prov, std_register,
                            assumptions, run_id, inputs_hashed)

    site_meta_for_matlab = pd.DataFrame({
        "site_id": meta.set_index("site_id").index,
        "arrival_start_hr": meta.set_index("site_id")["arrival_start_hr"].values,
        "arrival_end_hr": meta.set_index("site_id")["arrival_end_hr"].values,
        "base_load_mean_kw": meta.set_index("site_id")["base_load_mean_kw"].values,
        "base_load_peak_kw": meta.set_index("site_id")["base_load_peak_kw"].values,
    }).merge(scored_legacy[["site_id", "model_rank"]], on="site_id") \
      .merge(risk[["site_id", "electrical_risk_level"]], on="site_id")
    from .matlab_adapter import build_matlab_input
    matlab_df = build_matlab_input(scenario_table, site_meta_for_matlab, out_dir / "matlab_scenarios.csv")

    base_2026 = scenario_table[(scenario_table["horizon_year"] == BASELINE_YEAR)]
    result.update({
        "right_sizing": str(out_dir / "right_sizing_v3_canonical.csv"),
        "contract_dir": str(cdir),
        "scenario_rows": len(scenario_table),
        "matlab_rows": len(matlab_df),
        "starter_total_2026": int(base_2026["ports_active"].sum()),
        "pathway_total": int(base_2026["ports_pathway_capacity"].sum()),
        "legacy_starter_total": int(legacy_rs["ports_now"].sum()),
        "legacy_pathway_total": int(legacy_rs["future_ready_capacity"].sum()),
        "high_confidence_sites": int((conf["data_confidence_level_v3"] == "High").sum()),
        "claims_discipline": "All values planning-support screening outputs; capacity placeholder at 12/12 sites; demand uncalibrated; costs screening-class; nothing approved.",
    })
    (out_dir / "run_summary.json").write_text(json.dumps(result, indent=2))
    return result


def _ingest_observations(args) -> int:
    """Report what a set of observations would change. Deliberately read-only.

    This command **never writes**. Rule 2 of the data-flow document is that received values
    enter the site inputs and the model *re-runs*, generating a new run_id -- scenario rows
    are never edited in place. A command that quietly mutated the contract would be the
    hand-edit that rule exists to prevent, so this one shows the consequence and stops.
    """
    from . import observed, triggers

    if not args.capacity and not args.sessions:
        print("Nothing to ingest. Pass --capacity and/or --sessions.\n"
              "Templates: data/observed/observed_capacity_template.csv,\n"
              "           data/observed/observed_sessions_template.csv")
        return 2

    exit_code = 0

    if args.capacity:
        try:
            records = observed.read_capacity_observations(args.capacity)
        except observed.ObservationError as err:
            # Plain language, not a stack trace: the person holding this file is a
            # facility manager or a fellowship member, not a Python developer.
            print(f"CAPACITY FILE REJECTED\n  {err}")
            return 1
        upgrades = observed.resolve_capacity(records)
        print(f"CAPACITY — {len(records)} observation(s) across {len(upgrades)} site(s)\n")
        for site_id, upgrade in upgrades.items():
            arrow = "->" if upgrade.upgraded else "unchanged,"
            print(f"  {site_id}: {upgrade.previous_basis} {arrow} {upgrade.new_basis}")
            if upgrade.service_capacity_kw is not None:
                print(f"      service capacity: {upgrade.service_capacity_kw:g} kW")
            if upgrade.spare_capacity_kw is not None:
                print(f"      spare capacity:   {upgrade.spare_capacity_kw:g} kW")
            print(f"      provenance: {upgrade.capacity_source}")
            for conflict in upgrade.conflicts:
                print(f"      !! CONFLICT, needs a human: {conflict}")
                exit_code = max(exit_code, 3)
            print()

    if args.sessions:
        try:
            rows = observed.read_session_observations(args.sessions)
        except observed.ObservationError as err:
            print(f"SESSION FILE REJECTED\n  {err}")
            return 1
        summaries = observed.summarise_sessions(rows)
        print(f"SESSIONS — {len(rows)} site-day(s) across {len(summaries)} site(s)\n")
        for site_id, summary in summaries.items():
            print(f"  {site_id}: {summary.days_observed} days "
                  f"({summary.months_observed} months observed)")
            if not summary.sufficient_for_triggers:
                # Named, never defaulted. A defaulted uptime of 1.0 would walk straight
                # past the reliability gate that exists to catch exactly that.
                print(f"      cannot evaluate triggers - missing: "
                      f"{', '.join(summary.missing_for_triggers)}")
                print()
                continue
            metrics = triggers.ObservedMetrics(
                site_id=site_id, months_observed=summary.months_observed,
                avg_utilization=summary.avg_utilization, p90_wait_min=summary.p90_wait_min,
                uptime=summary.uptime, equity_index_percentile=0.5)
            decision = triggers.evaluate(metrics, args.ports_active, args.ports_pathway,
                                         site_id=site_id)
            print(f"      utilisation {summary.avg_utilization:.0%} · "
                  f"uptime {summary.uptime:.1%} · p90 wait {summary.p90_wait_min:g} min")
            print(f"      -> {decision.outcome}")
            for line in decision.rule_trace:
                print(f"         {line}")
            print()
        print("  (equity percentile defaults to 0.5 here; the model supplies the real value "
              "during a run)")

    print("\nNOTHING WAS WRITTEN. This command reports only.")
    print("To apply these, put the values into the site inputs and re-run the model "
          "(make run-v3), which generates a new run_id. Scenario rows are never edited "
          "in place - see docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md")
    return exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(description="FCF M2 V3 workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--mode", choices=[MODE_LEGACY, MODE_V3], default=MODE_V3)
    p_run.add_argument("--out", default=None)
    p_run.add_argument("--contract-dir", default=None)
    p_val = sub.add_parser("validate-contract")
    p_val.add_argument("contract_dir")
    sub.add_parser("docs")

    # The V4 loop needs a way in from the command line. Without one, a capacity
    # confirmation returned by a facility manager has nowhere to go except a person
    # editing a contract row by hand -- which is exactly what
    # docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md forbids.
    p_obs = sub.add_parser(
        "ingest-observations",
        help="Read field observations, report what they would change. Writes nothing.")
    p_obs.add_argument("--capacity", default=None,
                       help="CSV of capacity confirmations (observed_capacity_template.csv shape)")
    p_obs.add_argument("--sessions", default=None,
                       help="CSV of charger operating data (observed_sessions_template.csv shape)")
    p_obs.add_argument("--ports-active", type=int, default=4,
                       help="ports currently energised, for trigger evaluation")
    p_obs.add_argument("--ports-pathway", type=int, default=8,
                       help="pathway capacity, for trigger evaluation")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        out = Path(args.out) if args.out else ROOT / "data/outputs" / datetime.now().strftime("run_%Y%m%d_%H%M%S")
        cdir = Path(args.contract_dir) if args.contract_dir else None
        result = run(args.mode, out, cdir)
        print(json.dumps(result, indent=2))
    elif args.cmd == "validate-contract":
        cdir = Path(args.contract_dir)
        st = pd.read_csv(cdir / "scenario_table.csv")
        site = pd.read_csv(cdir / "site_table.csv")

        # One command, version-aware -- not one command per version. The version is read
        # from the artifact rather than passed as a flag, so a v2 directory cannot be
        # validated under v1's weaker rules by getting the flag wrong.
        manifest = json.loads((cdir / "contract_manifest.json").read_text())
        version = manifest.get("contract_version", config.SCHEMA_VERSION)
        if version == config.SCHEMA_VERSION_V2:
            from . import contract_v2
            problems = contract_v2.validate_v2(st, site)
        elif version == config.SCHEMA_VERSION:
            problems = contract.validate_scenario_table(st, site)
        else:
            problems = [f"unknown contract_version {version!r}; known versions are "
                        f"{', '.join(config.CONTRACT_VERSIONS)}"]

        problems += contract.verify_hash_chain(cdir)
        schema = json.loads((cdir / "schema.json").read_text())
        problems += contract.validate_against_json_schema(st, schema)
        if problems:
            print("FAIL:\n- " + "\n- ".join(problems))
            sys.exit(1)
        print(f"Contract v{version} valid: all rule checks, JSON Schema, and RT-10 hash "
              f"chain PASS.")
    elif args.cmd == "ingest-observations":
        sys.exit(_ingest_observations(args))
    elif args.cmd == "docs":
        docs = generate_docs()
        (ROOT / "docs/WORKFLOW_STEPS.md").write_text(docs)
        print(docs)


if __name__ == "__main__":
    main()
