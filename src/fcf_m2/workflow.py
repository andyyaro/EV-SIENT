"""V3 workflow orchestrator and single source of truth for workflow steps (PY-09).

Run:  python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/<run>
      python -m fcf_m2.workflow run --mode legacy_v2   --out data/outputs/<run>
      python -m fcf_m2.workflow intake <their_file.csv> --out <cohort_dir> [--accept]
      python -m fcf_m2.workflow run --cohort <cohort_dir>
      python -m fcf_m2.workflow validate-contract <contract_dir>
      python -m fcf_m2.workflow docs

Without --cohort a run reads the reference study (the 12 Northern Virginia sites). A cohort is
another jurisdiction's sites, laid out as docs/INPUT_SCHEMA.md describes.

The STEPS manifest below is the only place workflow steps are defined; the generated
docs (docs/WORKFLOW_STEPS.md) and tests both derive from it, eliminating doc drift.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
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
from .scoring import NUMERIC_FIELDS, YES_NO_FIELDS, add_tiers, enrich_and_score, load_anchor_set

ROOT = Path(__file__).resolve().parents[2]
BASE_LOAD_GROWTH_PER_YEAR = 0.008  # commercial base-load growth planning proxy (labeled assumption)

STEPS = [
    ("load_inputs", "Load the reference study's inputs, or a cohort directory (docs/INPUT_SCHEMA.md), plus the anchors"),
    ("score_sites", "Score readiness (legacy min-max or V3 fixed anchors) + Erlang-C port screen"),
    ("right_sizing", "Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056); the reference study on its accepted legacy ranking"),
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
    lines = ["# V3 Workflow Steps (generated from fcf_m2.workflow.STEPS - do not edit by hand)", ""]
    lines.append(f"Step count: **{len(STEPS)}**")
    lines.append("")
    for i, (name, desc) in enumerate(STEPS, 1):
        lines.append(f"{i}. **{name}** - {desc}")
    lines.append("")
    return "\n".join(lines)


def _load_inputs():
    sites = pd.read_csv(ROOT / "data/inputs/real_sites_v2.csv")
    risk = pd.read_csv(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv")
    prov = pd.read_csv(ROOT / "data/provenance/field_provenance_v1.csv")
    meta = pd.read_csv(ROOT / "data/inputs/legacy_matlab_site_meta.csv")
    anchors = load_anchor_set(ROOT / "data/anchors/anchor_set_v1.json")
    return sites, risk, prov, meta, anchors


def _reference_info(sites: pd.DataFrame) -> dict:
    """What a run on the reference study says about its own inputs. Unchanged since v1."""
    return {
        "jurisdiction": jurisdiction_for,
        "source_date": "2026-06-24",
        "source_id": "real_sites_v2+frozen_v2_outputs+anchors_v1",
        "inputs_hashed": {
            "real_sites_v2.csv": contract.sha256_file(ROOT / "data/inputs/real_sites_v2.csv"),
            "legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv":
                contract.sha256_file(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv"),
            "field_provenance_v1.csv": contract.sha256_file(ROOT / "data/provenance/field_provenance_v1.csv"),
            "anchor_set_v1.json": contract.sha256_file(ROOT / "data/anchors/anchor_set_v1.json"),
            "legacy_matlab_site_meta.csv": contract.sha256_file(ROOT / "data/inputs/legacy_matlab_site_meta.csv"),
        },
        "cohort": None,
        "site_count": len(sites),
    }


#: The files a cohort directory may hold. Only `sites.csv` is required; each of the others has
#: a labelled default that the run records, in its summary and in the contract manifest, as a
#: sentence a reader can check. docs/INPUT_SCHEMA.md is the human description of all five.
COHORT_FILES = ("sites.csv", "electrical_risk.csv", "site_meta.csv", "provenance.csv", "cohort.json")
RISK_LEVELS = ("low", "medium", "high")
META_COLUMNS = ["site_id", "arrival_start_hr", "arrival_end_hr", "base_load_mean_kw", "base_load_peak_kw"]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-") or "cohort"


class CohortError(ValueError):
    """A cohort directory cannot be run, said in a sentence its owner can act on."""


def _load_cohort(cohort_dir: Path):
    """Read another jurisdiction's cohort, with every default it needs labelled (F-18).

    Until 2026-10-17 `run` read four fixed files and had no way in for anyone else's sites:
    a six-site Chicago-shaped cohort crashed on `KeyError` for want of MATLAB site meta, and
    once that was fabricated, was refused by RT-04 for not reproducing Northern Virginia's
    totals. This makes the four optional, says what stands in for each, and leaves RT-04 to
    the cohort it belongs to.
    """
    cohort_dir = Path(cohort_dir)
    sites_path = cohort_dir / "sites.csv"
    if not sites_path.is_file():
        raise CohortError(f"{cohort_dir} has no sites.csv. Make one from your own file with "
                          f"`python -m fcf_m2.workflow intake <file> --out {cohort_dir} --accept`, "
                          f"or see docs/INPUT_SCHEMA.md.")
    declared = {}
    if (cohort_dir / "cohort.json").is_file():
        declared = json.loads((cohort_dir / "cohort.json").read_text())
    defaults: list[str] = []

    sites = pd.read_csv(sites_path)
    if "site_id" not in sites.columns:
        raise CohortError("sites.csv has no site_id column, and sites that cannot be told apart "
                          "cannot be scored.")
    ids = sites["site_id"].astype("string").str.strip()
    if ids.isna().any() or (ids == "").any() or ids.duplicated().any():
        raise CohortError("Every site_id in sites.csv must be present and unique.")
    bad = [s for s in ids if not re.match(contract.COHORT_SITE_ID_PATTERN, s)]
    if bad:
        raise CohortError(f"site_id {bad[0]!r} is not usable: letters, digits, '.', '_' and '-' "
                          f"only, starting with a letter or digit, at most 40 characters.")
    sites["site_id"] = ids.astype(str)
    if "site_name" not in sites.columns or sites["site_name"].isna().any():
        names = sites.get("site_name", pd.Series([pd.NA] * len(sites)))
        sites["site_name"] = names.where(names.notna(), sites["site_id"])
        defaults.append("site_name: a site with no name is shown by its site_id.")
    short = sites["site_name"].astype(str).str.len() < 3
    if short.any():
        sites.loc[short, "site_name"] = "Site " + sites.loc[short, "site_name"].astype(str)
        defaults.append("site_name: a name under three characters is shown as 'Site <name>'.")
    if "site_type" not in sites.columns or sites["site_type"].isna().any():
        sites["site_type"] = sites.get("site_type", pd.Series([pd.NA] * len(sites))).fillna("unspecified")
        defaults.append("site_type: 'unspecified' where not given.")
    missing = [c for c in NUMERIC_FIELDS + YES_NO_FIELDS if c not in sites.columns]
    for column in missing:
        sites[column] = float("nan")
    if missing:
        defaults.append(f"{len(missing)} scored field(s) are not in sites.csv and are scored as "
                        f"absent, which earns no credit: {', '.join(missing)}.")

    risk_path = cohort_dir / "electrical_risk.csv"
    if risk_path.is_file():
        risk = pd.read_csv(risk_path)[["site_id", "electrical_risk_level"]]
        risk["site_id"] = risk["site_id"].astype(str).str.strip()
        risk["electrical_risk_level"] = risk["electrical_risk_level"].astype(str).str.strip().str.lower()
        wrong = sorted(set(risk["electrical_risk_level"]) - set(RISK_LEVELS))
        if wrong:
            raise CohortError(f"electrical_risk.csv uses {wrong}; the levels are {list(RISK_LEVELS)}.")
        unlisted = sorted(set(sites["site_id"]) - set(risk["site_id"]))
        if unlisted:
            risk = pd.concat([risk, pd.DataFrame({"site_id": unlisted, "electrical_risk_level": "medium"})])
            defaults.append(f"electrical risk: 'medium' for the {len(unlisted)} site(s) "
                            f"electrical_risk.csv does not list.")
    else:
        risk = pd.DataFrame({"site_id": sites["site_id"], "electrical_risk_level": "medium"})
        defaults.append("electrical risk: no electrical_risk.csv, so every site is 'medium', the "
                        "right-sizing default - no site is held back, or let through, on electrical grounds.")

    hours = pd.to_numeric(sites["hours_open"], errors="coerce").fillna(8.0).clip(1, 24)
    start = (hours < 24).astype(float) * 8.0
    derived_meta = pd.DataFrame({
        "site_id": sites["site_id"], "arrival_start_hr": start,
        "arrival_end_hr": (start + hours).clip(upper=24.0),
        "base_load_mean_kw": float("nan"), "base_load_peak_kw": float("nan")})
    meta_path = cohort_dir / "site_meta.csv"
    if meta_path.is_file():
        meta = pd.read_csv(meta_path)
        lacking = [c for c in META_COLUMNS if c not in meta.columns]
        if lacking:
            raise CohortError(f"site_meta.csv lacks {lacking}; see docs/INPUT_SCHEMA.md.")
        meta = meta[META_COLUMNS].copy()
        meta["site_id"] = meta["site_id"].astype(str).str.strip()
        unlisted = sorted(set(sites["site_id"]) - set(meta["site_id"]))
        if unlisted:
            meta = pd.concat([meta, derived_meta[derived_meta["site_id"].isin(unlisted)]])
            defaults.append(f"site meta: derived, as below, for the {len(unlisted)} site(s) "
                            f"site_meta.csv does not list.")
    else:
        meta = derived_meta
        defaults.append("site meta: no site_meta.csv, so arrivals run from 08:00 for each site's "
                        "opening hours (8 h where not recorded), and the building's base load is "
                        "left unknown rather than invented.")

    prov_path = cohort_dir / "provenance.csv"
    if prov_path.is_file():
        prov = pd.read_csv(prov_path, dtype={"site_id": str})
    else:
        from .confidence import FIELD_GROUP_WEIGHTS
        prov = pd.DataFrame([
            {"site_id": sid, "field_group": group, "source_class": "unconfirmed",
             "verification_status": "unreviewed", "source_org": declared.get("source_org", "unstated"),
             "source_date": declared.get("source_date", ""), "reviewer": "none",
             "assumption_type": "no provenance was supplied with this cohort", "unresolved_flag": "1"}
            for sid in sites["site_id"] for group in FIELD_GROUP_WEIGHTS])
        defaults.append("provenance: no provenance.csv, so every field group is 'unconfirmed' and "
                        "data confidence is Low until the jurisdiction says where its figures came from.")

    anchors = load_anchor_set(ROOT / "data/anchors/anchor_set_v1.json")
    jurisdiction = _slug(declared.get("jurisdiction") or cohort_dir.name)
    hashed = {name: contract.sha256_file(cohort_dir / name) for name in COHORT_FILES
              if (cohort_dir / name).is_file()}
    hashed["anchor_set_v1.json"] = contract.sha256_file(ROOT / "data/anchors/anchor_set_v1.json")
    cohort = {
        "cohort_id": _slug(declared.get("cohort_id") or cohort_dir.name),
        "jurisdiction": jurisdiction,
        "source_date": str(declared.get("source_date") or "unstated"),
        "source_org": str(declared.get("source_org") or "unstated"),
        "files": sorted(n for n in COHORT_FILES if (cohort_dir / n).is_file()),
        "defaults": defaults,
        "reference_totals_apply": contract.is_reference_cohort(hashed),
        "notes": [
            "Scores use the fixed anchor set built for the reference study; they are comparable "
            "across cohorts, but anchors were not calibrated to this jurisdiction.",
            "standards_register.csv lists the editions Virginia has adopted; confirm the editions "
            "this jurisdiction has adopted before relying on it.",
            f"CO2e uses the grid factor of the reference study's region ({config.GRID_FACTOR_SOURCE}) "
            "and costs use its screening tariff and cost classes; replace both with this "
            "jurisdiction's before quoting either.",
        ],
    }
    info = {
        "jurisdiction": lambda _sid: jurisdiction,
        "source_date": cohort["source_date"] if len(cohort["source_date"]) >= 8 else "unstated",
        "source_id": f"cohort:{cohort['cohort_id']}+anchors_v1",
        "inputs_hashed": hashed,
        "cohort": cohort,
        "site_count": len(sites),
    }
    return sites, risk, prov, meta, anchors, info


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


def run(mode: str, out_dir: Path, contract_dir: Path | None = None,
        cohort_dir: Path | None = None, as_of: date | None = None) -> dict:
    """Run the model. ``as_of`` is the date data confidence is judged on (its staleness
    penalty); without it, today. The platform passes it so that one project file scores the
    same on any day it is re-opened."""
    if cohort_dir is None:
        sites, risk, prov, meta, anchors = _load_inputs()
        info = _reference_info(sites)
    else:
        sites, risk, prov, meta, anchors, info = _load_cohort(cohort_dir)
    n_sites = info["site_count"]
    jurisdiction_of = info["jurisdiction"]

    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"{mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    generated_at = datetime.now(timezone.utc).isoformat()

    # Right-sizing (ports/pathway) follows the ranking that was ACCEPTED for these inputs. For
    # the reference study that is the legacy baseline (RT-04: 25 starter / 48 pathway must
    # reconcile); V3 fixed-anchor scores are reported alongside with a migration report and do
    # not silently re-baseline the port structure (PY-02 deliberate-migration rule). On the
    # fixed-anchor ranking the same rules give 25 / 47 (F-05). Any other cohort has no accepted
    # baseline to keep, and the cohort-relative legacy ranking is the volatile one v3 replaced,
    # so its plan follows the fixed-anchor ranking it is scored with: otherwise a site the
    # results call Tier 3 is planned, and described, as Tier 1. Which run is the reference
    # study is RT-04's own test (`contract.is_reference_run`), so the plan keeps the legacy
    # ranking exactly when the run is held to 25 / 48. Synthetic inputs are never the
    # reference study, including in the public bundle, where they sit at the reference paths.
    reference_run = contract.is_reference_run(prov, info["inputs_hashed"], info["cohort"])
    plan_on_legacy = mode == MODE_LEGACY or reference_run
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
            + ("Port/pathway structure remains anchored to the accepted legacy baseline pending deliberate re-baselining."
               if plan_on_legacy else
               "This cohort has no accepted legacy baseline, so its port/pathway structure follows the fixed-anchor ranking.")
        )
        migration.to_csv(out_dir / "scoring_migration_report.csv", index=False)
        scored = scored_v3
    else:
        scored = scored_legacy
    scored_legacy.to_csv(out_dir / "site_results_legacy_v2.csv", index=False)
    planned = scored_legacy if plan_on_legacy else scored
    if info["cohort"] is not None:
        info["cohort"]["plan_ranking"] = MODE_LEGACY if plan_on_legacy else MODE_V3

    legacy_rs = run_right_sizing_legacy(planned)
    legacy_rs.to_csv(out_dir / "right_sizing_legacy_2035_2050.csv", index=False)

    result = {"run_id": run_id, "mode": mode, "site_results": str(out_dir / f"site_results_{mode}.csv"),
              "plan_ranking": MODE_LEGACY if plan_on_legacy else MODE_V3}
    if info["cohort"] is not None:
        result["cohort"] = info["cohort"]

    if mode == MODE_LEGACY:
        result["right_sizing"] = str(out_dir / "right_sizing_legacy_2035_2050.csv")
        result["starter_total"] = int(legacy_rs["ports_now"].sum())
        result["pathway_total"] = int(legacy_rs["future_ready_capacity"].sum())
        (out_dir / "run_summary.json").write_text(json.dumps(result, indent=2))
        return result

    # ---- V3 branch ----
    v3_rs = run_right_sizing_v3(planned)
    v3_rs.to_csv(out_dir / "right_sizing_v3_canonical.csv", index=False)

    conf = build_confidence(prov, list(scored["site_id"]), today=as_of)
    conf.to_csv(out_dir / "data_confidence_v3.csv", index=False)

    site_table = pd.DataFrame({
        "site_id": scored["site_id"],
        "site_name_display": scored["site_name"],
        "site_name_safe": scored["site_name"].str.replace(r"[^A-Za-z0-9]+", "_", regex=True).str.strip("_"),
        "jurisdiction": scored["site_id"].map(jurisdiction_of),
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

    # A site missing any cost input gets no cost figures at all. Computed with its gaps as 0
    # it would look cheaper than a site whose costs were measured - the DEC-011 defect again,
    # one module down. Its rows are computed (the arithmetic needs them) and then withheld.
    cost_inputs = ("trenching_ft", "trench_cost_per_ft", "service_upgrade_cost_usd")
    costs_unknown = {sid for sid, gaps in zip(scored_legacy["site_id"], scored_legacy["absent_fields"])
                     if any(f in str(gaps).split("; ") for f in cost_inputs)}

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
    econ_known = econ_all[~econ_all["site_id"].isin(costs_unknown)]
    econ_known.to_csv(out_dir / "lifecycle_costs.csv", index=False)
    economics.portfolio_summary(econ_known).to_csv(out_dir / "lifecycle_costs_portfolio.csv", index=False)
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
        # NaN for a cohort that supplied no site meta: unknown, and written as unknown.
        base_load = float(m["base_load_mean_kw"]) * ((1 + BASE_LOAD_GROWTH_PER_YEAR) ** (year - BASELINE_YEAR))
        annual_kwh = round(energy_day * 365.0, 1) if ports > 0 else 0.0
        em = emissions.net_co2e_kg(annual_kwh)

        if year == BASELINE_YEAR or sid in costs_unknown:
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
            "jurisdiction": jurisdiction_of(sid),
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
            "base_load_kw": round(base_load, 1) if np.isfinite(base_load) else None,
            "service_capacity_kw": None,
            "spare_capacity_kw": None,
            "capacity_basis": "placeholder",
            "capacity_source": f"legacy adapter future-ready placeholder; utility/facility confirmation pending ({n_sites}/{n_sites} sites unconfirmed)",
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
            "equity_indicator": (None if "equity_gap_index" in str(row["absent_fields"]).split("; ")
                                 else round(float(row["equity_gap_index"]), 3)),
            "expansion_trigger_status": triggers.status_for_contract(False),
            "source_date": info["source_date"],
            "source_id": info["source_id"],
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
        "capacity": f"service/spare capacity NULL with capacity_basis=placeholder at all {n_sites} sites until utility/facility confirmation",
    }
    if info["cohort"] is not None:
        assumptions["cohort"] = info["cohort"]
        assumptions["costs_withheld_for_missing_inputs"] = sorted(costs_unknown)

    std_register = standards.build_register(
        site_table, battery_storage=scored["battery_storage_flag"], reference=reference_run)
    std_register.to_csv(out_dir / "standards_register.csv", index=False)

    cdir = contract_dir or (out_dir / "contract")
    contract.write_contract(cdir, scenario_table, site_table, prov, std_register,
                            assumptions, run_id, info["inputs_hashed"], cohort=info["cohort"])

    site_meta_for_matlab = pd.DataFrame({
        "site_id": meta.set_index("site_id").index,
        "arrival_start_hr": meta.set_index("site_id")["arrival_start_hr"].values,
        "arrival_end_hr": meta.set_index("site_id")["arrival_end_hr"].values,
        "base_load_mean_kw": meta.set_index("site_id")["base_load_mean_kw"].values,
        "base_load_peak_kw": meta.set_index("site_id")["base_load_peak_kw"].values,
    }).merge(planned[["site_id", "model_rank"]], on="site_id") \
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
        "claims_discipline": f"All values planning-support screening outputs; capacity placeholder at {n_sites}/{n_sites} sites; demand uncalibrated; costs screening-class; nothing approved.",
    })
    if info["cohort"] is not None:
        result["costs_withheld_for_missing_inputs"] = sorted(costs_unknown)
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
        except FileNotFoundError:
            # A missing file is a normal condition, not a crash. The declared platform
            # operation points at the shipped templates, so a bundle that omits them would
            # otherwise surface a raw traceback in the UI instead of a sentence.
            print(f"NO CAPACITY FILE\n  {args.capacity} does not exist in this installation.\n"
                  f"  Nothing was ingested and nothing changed.")
            return 0
        except observed.ObservationError as err:
            # Plain language, not a stack trace: the person holding this file is a
            # facility manager or a fellowship member, not a Python developer.
            print(f"CAPACITY FILE REJECTED\n  {err}")
            return 1
        upgrades = observed.resolve_capacity(records)
        print(f"CAPACITY - {len(records)} observation(s) across {len(upgrades)} site(s)\n")
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
        print(f"SESSIONS - {len(rows)} site-day(s) across {len(summaries)} site(s)\n")
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


def _intake(args) -> int:
    """Read another jurisdiction's file into a cohort directory `run --cohort` accepts.

    Two steps, because DEC-021's whole design is that a person sees every finding BEFORE
    anything happens to their data: without --accept this prints what intake would do and
    writes nothing; with --accept it writes the cohort. A refusal writes nothing either way.
    """
    from . import intake

    source = Path(args.file)
    if not source.is_file():
        print(f"no such file: {source}")
        return 1
    frame = pd.read_csv(source, dtype=object, keep_default_na=False)
    proposal = intake.propose(frame)
    print(f"Intake - {source.name}: {proposal.summary()}\n")
    for finding in proposal.findings:
        print(f"  {finding.severity.upper():<8} {finding.field}: {finding.explain}")
        if finding.detail:
            print(f"           {finding.detail}")
    if proposal.refused:
        print("\nREFUSED. Nothing was written.")
        return 1
    if not args.accept:
        print("\nNothing was written. If the readings above are right, run this again with "
              "--accept to write the cohort.")
        return 0

    out = Path(args.out)
    if (out / "sites.csv").exists():
        print(f"\n{out} already holds a cohort. Choose another --out; nothing was changed.")
        return 1
    applied, ledger = intake.apply(frame, proposal)
    applied["site_id"] = applied["site_id"].astype(str).str.strip()
    site_ids = list(applied["site_id"])
    source_date = args.source_date or "unstated"
    source_org = args.source_org or source.stem
    provenance = intake.accept(intake.provenance_rows(
        proposal, site_ids, reviewer="workflow intake --accept", source_org=source_org,
        source_date=source_date, applied=applied))

    out.mkdir(parents=True, exist_ok=True)
    applied.to_csv(out / "sites.csv", index=False)
    provenance.to_csv(out / "provenance.csv", index=False)
    pd.DataFrame([vars(e) for e in ledger]).to_csv(out / "intake_ledger.csv", index=False)
    (out / "intake_findings.json").write_text(json.dumps([vars(f) for f in proposal.findings], indent=2))
    (out / "cohort.json").write_text(json.dumps({
        "schema": "fcf-cohort/1",
        "cohort_id": _slug(out.name),
        "jurisdiction": _slug(args.jurisdiction or source.stem),
        "source_date": source_date,
        "source_org": source_org,
        "source_file": source.name,
        "source_sha256": contract.sha256_file(source),
        "accepted_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(f"\nWrote the cohort to {out}. The ledger of every change is intake_ledger.csv.")
    print(f"Next: python -m fcf_m2.workflow run --cohort {out}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="FCF M2 V3 workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--mode", choices=[MODE_LEGACY, MODE_V3], default=MODE_V3)
    p_run.add_argument("--out", default=None)
    p_run.add_argument("--contract-dir", default=None)
    p_run.add_argument("--cohort", default=None,
                       help="a cohort directory (docs/INPUT_SCHEMA.md); without it, the reference study")
    p_in = sub.add_parser(
        "intake", help="Read another jurisdiction's site file into a cohort directory.")
    p_in.add_argument("file", help="the jurisdiction's own CSV, in whatever shape it has")
    p_in.add_argument("--out", required=True, help="the cohort directory to write")
    p_in.add_argument("--accept", action="store_true",
                      help="write the cohort; without it, report and write nothing")
    p_in.add_argument("--jurisdiction", default=None, help="a short name, e.g. 'chicago'")
    p_in.add_argument("--source-date", default=None, help="when the figures were current, YYYY-MM-DD")
    p_in.add_argument("--source-org", default=None, help="who supplied the figures")
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
        stamp = datetime.now().strftime("run_%Y%m%d_%H%M%S")
        cohort = Path(args.cohort) if args.cohort else None
        out = Path(args.out) if args.out else (cohort / "outputs" / stamp if cohort
                                               else ROOT / "data/outputs" / stamp)
        cdir = Path(args.contract_dir) if args.contract_dir else None
        try:
            result = run(args.mode, out, cdir, cohort_dir=cohort)
        except CohortError as err:
            print(f"COHORT NOT RUN\n  {err}")
            sys.exit(1)
        print(json.dumps(result, indent=2))
    elif args.cmd == "intake":
        sys.exit(_intake(args))
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
            # RT-04 asserts the real study's accepted totals (25 starter / 48 pathway). A run
            # on SYNTHETIC inputs cannot reproduce them and must not be tuned until it does --
            # `run_is_synthetic()` exists for exactly this, and `write_contract()` already
            # consults it. This command did not, so `validate-contract` failed on every
            # synthetic contract, including the public bundle whose own REPRODUCTION.txt
            # instructs the recipient to run it.
            synthetic = False
            prov_path = cdir / "source_provenance.csv"
            if prov_path.is_file():
                synthetic = contract.run_is_synthetic(pd.read_csv(prov_path))
            # A cohort contract is held to the golden totals only if it read the reference
            # study's own inputs - decided from the digests it records, not from a flag.
            other_cohort = ("cohort" in manifest
                            and not contract.is_reference_cohort(manifest.get("inputs", {})))
            problems = contract.validate_scenario_table(
                st, site, expect_legacy_totals=not synthetic and not other_cohort)
            if synthetic:
                print("note: this contract declares SYNTHETIC inputs, so the real study's "
                      "25/48 golden totals are not asserted against it.")
            elif other_cohort:
                print(f"note: this contract is cohort {manifest['cohort'].get('cohort_id')!r}, not "
                      f"the reference study, so its 25/48 golden totals are not asserted against it.")
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
