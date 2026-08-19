"""Canonical cross-model data contract v1 (hybrid CSV + JSON manifest).

Python is the single producer; MATLAB, Excel, Tableau, static visuals, and the
presentation are consumers. Contract layout (data/contract/v1/):

    schema.json             - JSON Schema for scenario_table.csv rows
    scenario_table.csv      - site x horizon x case (long format, all required fields)
    site_table.csv          - identity dimension (one canonical spelling per site)
    source_provenance.csv   - field-level provenance (from confidence layer)
    standards_register.csv  - standards applicability register (from standards.py)
    assumptions.json        - every labeled assumption with provenance
    contract_manifest.json  - schema version, input/table hashes, generation stamp
    README.md               - consumer rules

Validation implements the research reconciliation tests RT-01..RT-05 and RT-07..RT-10
(RT-06 is not implemented -- see ``validate_scenario_table``) plus the acceptance rules:
invalid units, missing provenance, unsupported horizons, and placeholder capacity
presented as verified all FAIL validation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config
from .config import (
    BASELINE_YEAR,
    CAPACITY_BASIS_VALUES,
    EVSE_POWER_KW,
    GRID_FACTOR_LB_PER_MWH,
    GRID_FACTOR_SOURCE,
    GRID_FACTOR_VINTAGE,
    MODEL_VERSION,
    SCHEMA_VERSION,
    V3_HORIZON_LABELS,
    V3_HORIZONS,
    jurisdiction_for,
)

REQUIRED_FIELDS = [
    "contract_version", "run_id", "generated_at", "site_id", "site_name", "jurisdiction",
    "site_type", "public_or_fleet", "horizon_year", "horizon_label", "scenario_id",
    "scenario_name", "model_mode", "ports_active", "ports_pathway_capacity", "evse_power_kw",
    "sessions_per_day", "energy_per_session_kwh", "energy_required_kwh_day",
    "charging_window_hr", "average_dwell_hr", "peak_factor", "utilization",
    "average_wait_minutes", "peak_wait_minutes", "base_load_kw", "service_capacity_kw",
    "spare_capacity_kw", "capacity_basis", "capacity_source", "capacity_confidence",
    "managed_charging_policy", "energy_delivered_kwh", "energy_curtailed_kwh",
    "lifecycle_cost_nominal_usd", "lifecycle_cost_npv_usd", "avoided_overbuild_cost_usd",
    "grid_factor_value", "grid_factor_units", "grid_factor_vintage", "net_co2e_kg",
    "data_confidence", "equity_indicator", "expansion_trigger_status", "source_date",
    "source_id", "assumption_flag", "notes",
]

VALID_CASES = {"baseline", "base", "high", "stress_combined"}
VALID_HORIZONS = {BASELINE_YEAR, *V3_HORIZONS}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_schema(synthetic: bool = False) -> dict:
    """Build the contract's JSON Schema. ``synthetic=True`` admits generated sites.

    Widened, not relaxed. A synthetic run keeps ``SYN000``-style ids and the jurisdiction
    ``synthetic``, so its rows stay distinguishable from real ones at a glance and to any
    downstream consumer. Making synthetic ids match ``^(FFX|PWC)[0-9]{3}$`` would have
    satisfied the validator by making invented data indistinguishable from the real study's -
    the opposite of what a fixture is for.
    """
    """JSON Schema for one scenario_table row."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FCF M2 canonical scenario row",
        "type": "object",
        "required": REQUIRED_FIELDS,
        "properties": {
            "contract_version": {"const": SCHEMA_VERSION},
            "run_id": {"type": "string", "minLength": 8},
            "generated_at": {"type": "string"},
            "site_id": {"type": "string",
                        "pattern": "^(FFX|PWC|SYN)[0-9]{3}$" if synthetic
                                   else "^(FFX|PWC)[0-9]{3}$"},
            "site_name": {"type": "string", "minLength": 3},
            "jurisdiction": {"enum": ["fairfax", "pwc", "synthetic"] if synthetic
                                     else ["fairfax", "pwc"]},
            "site_type": {"type": "string"},
            "public_or_fleet": {"enum": ["public", "fleet", "mixed"]},
            "horizon_year": {"enum": sorted(VALID_HORIZONS)},
            "horizon_label": {"enum": sorted(set(V3_HORIZON_LABELS.values()))},
            "scenario_id": {"type": "string", "minLength": 5},
            "scenario_name": {"type": "string"},
            "model_mode": {"enum": [config.MODE_LEGACY, config.MODE_V3]},
            "ports_active": {"type": "integer", "minimum": 0, "maximum": 100},
            "ports_pathway_capacity": {"type": "integer", "minimum": 0, "maximum": 100},
            "evse_power_kw": {"type": "number", "exclusiveMinimum": 0, "maximum": 5000},
            "sessions_per_day": {"type": "number", "minimum": 0},
            "energy_per_session_kwh": {"type": "number", "minimum": 0, "maximum": 1000},
            "energy_required_kwh_day": {"type": "number", "minimum": 0},
            "charging_window_hr": {"type": "number", "minimum": 0, "maximum": 24},
            "average_dwell_hr": {"type": "number", "minimum": 0, "maximum": 24},
            "peak_factor": {"type": "number", "minimum": 0, "maximum": 10},
            "utilization": {"type": ["number", "null"], "minimum": 0, "maximum": 2},
            "average_wait_minutes": {"type": ["number", "null"], "minimum": 0},
            "peak_wait_minutes": {"type": ["number", "null"], "minimum": 0},
            "base_load_kw": {"type": ["number", "null"], "minimum": 0, "maximum": 5000},
            "service_capacity_kw": {"type": ["number", "null"], "minimum": 0, "maximum": 5000},
            "spare_capacity_kw": {"type": ["number", "null"], "minimum": 0, "maximum": 5000},
            "capacity_basis": {"enum": CAPACITY_BASIS_VALUES},
            "capacity_source": {"type": "string", "minLength": 3},
            "capacity_confidence": {"enum": ["high", "medium", "low", "none"]},
            "managed_charging_policy": {"enum": ["none", "clamp", "energy_aware"]},
            "energy_delivered_kwh": {"type": "number", "minimum": 0},
            "energy_curtailed_kwh": {"type": "number", "minimum": 0},
            "lifecycle_cost_nominal_usd": {"type": ["number", "null"], "minimum": 0},
            "lifecycle_cost_npv_usd": {"type": ["number", "null"], "minimum": 0},
            "avoided_overbuild_cost_usd": {"type": ["number", "null"]},
            "grid_factor_value": {"const": GRID_FACTOR_LB_PER_MWH},
            "grid_factor_units": {"const": "lb CO2e/MWh"},
            "grid_factor_vintage": {"type": "string", "minLength": 5},
            "net_co2e_kg": {"type": ["number", "null"]},
            "data_confidence": {"enum": ["High", "Medium", "Low"]},
            "equity_indicator": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "expansion_trigger_status": {"type": "string"},
            "source_date": {"type": "string", "minLength": 8},
            "source_id": {"type": "string", "minLength": 2},
            "assumption_flag": {"type": "string"},
            "notes": {"type": "string"},
        },
    }


class ContractValidationError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Contract validation failed:\n- " + "\n- ".join(problems))


def validate_scenario_table(df: pd.DataFrame, site_table: pd.DataFrame,
                            expect_legacy_totals: bool = True) -> list[str]:
    """Rule-based validation implementing RT-01..RT-05, RT-07..RT-09 and master-prompt rules.

    RT-06 is **not implemented here** and never has been. The previous docstring claimed
    RT-01..RT-07 (implying RT-06 was covered) while omitting RT-08 (which is). Stating the
    gap is the point: a validator that overstates its own coverage is worse than one with a
    known hole, because nobody goes looking for the hole. RT-10, the manifest hash chain,
    lives in ``verify_hash_chain``.

    Returns list of problems (empty = valid). Raise via validate_or_raise().
    """
    problems: list[str] = []

    missing = [c for c in REQUIRED_FIELDS if c not in df.columns]
    if missing:
        return [f"missing required fields: {missing}"]

    # RT-01 identity: every site_id resolves in site dimension; consumers join on IDs.
    known = set(site_table["site_id"])
    unknown = sorted(set(df["site_id"]) - known)
    if unknown:
        problems.append(f"RT-01 identity: scenario rows reference unknown site_ids {unknown}")
    name_map = dict(zip(site_table["site_id"], site_table["site_name_display"]))
    mismatched = df[df.apply(lambda r: name_map.get(r["site_id"]) != r["site_name"], axis=1)]
    if len(mismatched):
        problems.append(f"RT-01 naming: {len(mismatched)} rows carry a site_name differing from the canonical spelling")

    # RT-02 completeness: 12 sites x horizons x required cases, no duplicates.
    dupes = df.duplicated(subset=["site_id", "horizon_year", "scenario_name"]).sum()
    if dupes:
        problems.append(f"RT-02: {dupes} duplicate (site, horizon, case) rows")
    for sid in known:
        sub = df[df["site_id"] == sid]
        if set(sub["horizon_year"]) != VALID_HORIZONS:
            problems.append(f"RT-02: {sid} horizons {sorted(set(sub['horizon_year']))} != {sorted(VALID_HORIZONS)}")
            break
    bad_cases = sorted(set(df["scenario_name"]) - VALID_CASES)
    if bad_cases:
        problems.append(f"RT-02: unsupported cases {bad_cases}")

    # unsupported horizons must fail
    bad_years = sorted(set(df["horizon_year"]) - VALID_HORIZONS)
    if bad_years:
        problems.append(f"unsupported horizon years {bad_years}")

    # RT-03 monotonicity + pathway bound
    over = df[df["ports_active"] > df["ports_pathway_capacity"]]
    if len(over):
        problems.append(f"RT-03: {len(over)} rows with ports_active > pathway capacity")
    for (sid, case), sub in df[df["scenario_name"] != "baseline"].groupby(["site_id", "scenario_name"]):
        seq = sub.sort_values("horizon_year")["ports_active"].tolist()
        if any(b < a for a, b in zip(seq, seq[1:])):
            problems.append(f"RT-03: {sid}/{case} ports_active decreases across horizons {seq}")

    # RT-04 legacy totals at baseline
    if expect_legacy_totals:
        base = df[(df["horizon_year"] == BASELINE_YEAR) & (df["scenario_name"] == "baseline")]
        starter = int(base["ports_active"].sum())
        pathway = int(base["ports_pathway_capacity"].sum())
        if starter != 25:
            problems.append(f"RT-04: baseline starter total {starter} != 25")
        if pathway != 48:
            problems.append(f"RT-04: pathway total {pathway} != 48")

    # RT-05 unit ranges
    if (df["evse_power_kw"] <= 0).any() or (df["evse_power_kw"] > 5000).any():
        problems.append("RT-05: evse_power_kw out of range (0, 5000]")
    if (df["charging_window_hr"] > 24).any() or (df["charging_window_hr"] < 0).any():
        problems.append("RT-05: charging_window_hr outside [0, 24]")
    active = df[df["ports_active"] > 0]
    if (active["sessions_per_day"] < 0.3 - 1e-9).any():
        problems.append("RT-05: sessions floor 0.3 violated on active rows")
    if (df["energy_required_kwh_day"] < 0).any():
        problems.append("RT-05: negative energy_required_kwh_day")

    # RT-07 placeholder propagation: placeholder/unknown capacity must not carry
    # verified-style confidence or a 'verified' source string.
    ph = df[df["capacity_basis"].isin(["placeholder", "unknown", "planning_proxy"])]
    bad_conf = ph[ph["capacity_confidence"].isin(["high"])]
    if len(bad_conf):
        problems.append(f"RT-07: {len(bad_conf)} placeholder-capacity rows claim high capacity confidence")
    bad_flag = ph[~ph["assumption_flag"].str.contains("placeholder", case=False, na=False)]
    if len(bad_flag):
        problems.append(f"RT-07: {len(bad_flag)} placeholder-capacity rows missing placeholder assumption_flag")
    bad_basis = sorted(set(df["capacity_basis"]) - set(CAPACITY_BASIS_VALUES))
    if bad_basis:
        problems.append(f"capacity_basis outside controlled vocabulary: {bad_basis}")

    # RT-08 energy accounting (pre-MATLAB static check)
    delivered_over = df[df["energy_delivered_kwh"] - (df["energy_required_kwh_day"] * 365) > 0.5]
    if len(delivered_over):
        problems.append(f"RT-08: {len(delivered_over)} rows deliver more energy than required")

    # RT-09 factor vintage
    co2_rows = df[df["net_co2e_kg"].notna()]
    if (co2_rows["grid_factor_vintage"].str.len() < 5).any():
        problems.append("RT-09: net_co2e rows missing grid factor vintage")

    # provenance: every row needs source_id + source_date
    if (df["source_id"].astype(str).str.len() < 2).any() or (df["source_date"].astype(str).str.len() < 8).any():
        problems.append("provenance: rows missing source_id/source_date")

    return problems



def run_is_synthetic(provenance: pd.DataFrame) -> bool:
    """True only when EVERY provenance row declares synthetic inputs.

    Used to decide whether the RT-04 golden-baseline totals apply. They are the real study's
    accepted figures (25 starter / 48 pathway) and a run on invented inputs cannot reproduce
    them - nor should it be made to. Tuning a synthetic fixture until it hits the real totals
    would encode the real results inside data labelled as invented, which is both a false
    label and a leak.

    The test is deliberately **all**, not **any**. A run that mixes real and synthetic
    provenance gets the strict check, because the safe default when the input's nature is
    ambiguous is to hold it to the real study's standard. A single flag anyone could set would
    be a way to switch off the golden baseline by accident; the run has to prove what it is.
    """
    if provenance is None or len(provenance) == 0 or "source_class" not in provenance:
        return False
    return bool((provenance["source_class"].astype(str) == "synthetic_model").all())


def validate_or_raise(df: pd.DataFrame, site_table: pd.DataFrame, **kw) -> None:
    problems = validate_scenario_table(df, site_table, **kw)
    if problems:
        raise ContractValidationError(problems)


def validate_against_json_schema(df: pd.DataFrame, schema: dict, sample: int | None = None) -> list[str]:
    """Validate rows against the JSON Schema (jsonschema library)."""
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema)
    problems = []
    records = df.to_dict(orient="records")
    if sample:
        records = records[:sample]
    for i, rec in enumerate(records):
        rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
        for err in validator.iter_errors(rec):
            problems.append(f"row {i} ({rec.get('site_id')}/{rec.get('horizon_year')}): {err.message}")
            if len(problems) > 20:
                return problems
    return problems


def write_contract(out_dir: str | Path, scenario_table: pd.DataFrame, site_table: pd.DataFrame,
                   provenance: pd.DataFrame, standards_register: pd.DataFrame,
                   assumptions: dict, run_id: str, inputs_hashed: dict[str, str]) -> Path:
    """Write the full versioned contract directory with manifest hashes."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    synthetic = run_is_synthetic(provenance)
    validate_or_raise(scenario_table, site_table, expect_legacy_totals=not synthetic)
    schema = build_schema(synthetic=synthetic)
    schema_problems = validate_against_json_schema(scenario_table, schema)
    if schema_problems:
        raise ContractValidationError(schema_problems)

    (out / "schema.json").write_text(json.dumps(schema, indent=2))
    scenario_table.to_csv(out / "scenario_table.csv", index=False)
    site_table.to_csv(out / "site_table.csv", index=False)
    provenance.to_csv(out / "source_provenance.csv", index=False)
    standards_register.to_csv(out / "standards_register.csv", index=False)
    (out / "assumptions.json").write_text(json.dumps(assumptions, indent=2))

    tables = ["schema.json", "scenario_table.csv", "site_table.csv",
              "source_provenance.csv", "standards_register.csv", "assumptions.json"]
    manifest = {
        # Stated in the artifact itself, not only in the build log. A contract directory that
        # travels without saying its inputs were invented is one someone quotes.
        "synthetic_inputs": synthetic,
        "legacy_totals_checked": not synthetic,
        "contract_version": SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "run_id": run_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "producer": {"package": "fcf_m2", "module": "fcf_m2.contract"},
        "inputs": inputs_hashed,
        "tables": {name: sha256_file(out / name) for name in tables},
        "grid_factor": {
            "source": GRID_FACTOR_SOURCE,
            "value_lb_per_mwh": GRID_FACTOR_LB_PER_MWH,
            "vintage": GRID_FACTOR_VINTAGE,
        },
        "conventions": {
            "baseline_year": BASELINE_YEAR,
            "horizons": V3_HORIZONS,
            "cases": sorted(VALID_CASES),
            "discount_rate_real": config.ECON["discount_rate_real"],
        },
        "consumer_rules": [
            "Join on site_id only; site_name is display text.",
            "MATLAB refuses feasibility claims when capacity_basis is not verified_utility/verified_facility.",
            "Excel/Tableau/presentation quote contract values; no re-derivation.",
            "Any schema change bumps contract_version; consumers assert the major version.",
        ],
    }
    (out / "contract_manifest.json").write_text(json.dumps(manifest, indent=2))
    _write_readme(out)
    return out


def verify_hash_chain(contract_dir: str | Path) -> list[str]:
    """RT-10: manifest table hashes match files on disk."""
    out = Path(contract_dir)
    manifest = json.loads((out / "contract_manifest.json").read_text())
    problems = []
    for name, expected in manifest["tables"].items():
        actual = sha256_file(out / name)
        if actual != expected:
            problems.append(f"RT-10: {name} hash mismatch (stale contract)")
    return problems


def _write_readme(out: Path) -> None:
    (out / "README.md").write_text(
        "# Canonical Cross-Model Data Contract v1\n\n"
        "Producer: `fcf_m2` (Python V3). Consumers: MATLAB/Simulink V3, Excel workbook, "
        "Tableau exports, static visuals, presentation.\n\n"
        "## Files\n"
        "| File | Purpose |\n|---|---|\n"
        "| `schema.json` | JSON Schema for scenario_table rows |\n"
        "| `scenario_table.csv` | site x horizon (2026/2036/2046/2056) x case (baseline/base/high/stress_combined) |\n"
        "| `site_table.csv` | identity dimension - one canonical spelling per site; join on `site_id` only |\n"
        "| `source_provenance.csv` | field-level provenance (typed source classes) |\n"
        "| `standards_register.csv` | standards applicability per site/stage |\n"
        "| `assumptions.json` | every labeled assumption with provenance |\n"
        "| `contract_manifest.json` | version, input/table SHA-256 hashes, generation stamp |\n\n"
        "## Consumer rules\n"
        "1. Join on `site_id` only - never on names.\n"
        "2. `capacity_basis` is machine-readable placeholder-vs-verified provenance: any consumer "
        "using capacity MUST propagate the placeholder label when basis is not "
        "`verified_utility`/`verified_facility`.\n"
        "3. Presentation numbers cite `contract_version` + `generated_utc` from the manifest.\n"
        "4. Validation: `python -m fcf_m2.workflow validate-contract <dir>` re-runs all rules "
        "and the RT-10 hash chain.\n\n"
        "All values are planning-support outputs. Nothing here is an engineering, permitting, "
        "budget, or procurement value.\n"
    )
