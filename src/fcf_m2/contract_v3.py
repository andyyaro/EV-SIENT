"""Contract v3: the authoritative output since DEC-027, from a new model run.

Why a new version and not a new v2
----------------------------------
v1 is frozen, and v2 is v1 widened (DEC-008): every v1 value is carried into v2 unchanged,
by construction. DEC-008 also said what happens when the model itself produces different
numbers: "those go into a **new run** with its own contract directory and its own
``model_version``, not into this v2". DEC-027 (2026-10-18) is that case. The canonical
``milestone2_v3`` plan now follows the fixed-anchor ranking and the V3 pathway rule, so the
reference study's pathway is **47**, where v1 and v2 hold the earlier ``legacy_v2`` figure,
**48**. Rewriting v2 would break its additivity promise; rewriting v1 would break its
freeze. v3 is the new run, in its own directory, with its own hash chain.

The container is v2's
---------------------
Same 60 fields, same order, same semantics, same observation rules. A v2 consumer reads a v3
row with one change of meaning to know about: the numbers are model version 3.1.0, so the
ports, pathway, waits, utilisation and cost fields of some sites differ from v2's.
``contract_version`` is a major bump because the published headline totals changed, and the
consumer rule is that consumers assert the major version: a reader written against v2 that
quoted 48 should fail loudly on v3, not quote 47 under a v2 label.

History stays separate
----------------------
v1 and v2 stay where they are, unmodified, as the record of what was published before
DEC-027. The v3 manifest pins both of their manifest digests under ``history`` so "which
earlier output does this replace?" stays answerable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config, contract, contract_v2
from .config import MODEL_VERSION, SCHEMA_VERSION_V2, SCHEMA_VERSION_V3

#: The decision that made this version, quoted in the manifest.
DECISION = "DEC-027"


def v3_field_order() -> list[str]:
    """v2's field order, unchanged."""
    return contract_v2.v2_field_order()


def build_schema_v3() -> dict:
    """v2's schema with v3's version pinned. One definition of every shared field."""
    schema = contract_v2.build_schema_v2()
    schema["title"] = "FCF canonical scenario row (contract v3)"
    schema["properties"]["contract_version"] = {"const": SCHEMA_VERSION_V3}
    return schema


def from_run(scenario_run: pd.DataFrame,
             confidence_reasons: dict[str, str] | None = None) -> pd.DataFrame:
    """Put a fresh run's scenario table into the v3 container.

    The shape change is v2's migration (``contract_v2.migrate_v1_to_v2``), reused rather than
    reimplemented, then the version is stamped. Every model value is carried unchanged.
    """
    out = contract_v2.migrate_v1_to_v2(scenario_run, confidence_reasons)
    out["contract_version"] = SCHEMA_VERSION_V3
    return out[v3_field_order()]


def validate_v3(scenario_v3: pd.DataFrame, site_table: pd.DataFrame,
                model_version: str = MODEL_VERSION) -> list[str]:
    """Every v2 rule (and so every v1 rule), with RT-04 at ``model_version``'s totals."""
    as_v2 = scenario_v3.assign(contract_version=SCHEMA_VERSION_V2)
    problems = contract_v2.validate_v2(as_v2, site_table, model_version=model_version)
    if set(scenario_v3["contract_version"].astype(str).unique()) != {SCHEMA_VERSION_V3}:
        problems.append(f"contract_version must be {SCHEMA_VERSION_V3} on every v3 row")
    return problems


def write_contract_v3(out_dir: str | Path, scenario_v3: pd.DataFrame, site_table: pd.DataFrame,
                      provenance: pd.DataFrame, standards_register: pd.DataFrame,
                      assumptions: dict, run_id: str, inputs_hashed: dict[str, str],
                      history: dict[str, str], totals: dict, changes_md: str) -> Path:
    """Write ``data/contract/v3/`` with its own hash chain. Never touches v1 or v2.

    ``changes_md`` is the per-site account of what differs from v2, computed from the data by
    the caller (``scripts/build_contract_v3.py``) so that no site is named in this module.
    """
    out = Path(out_dir)
    if out.resolve().name in ("v1", "v2"):
        raise contract.ContractValidationError(
            [f"refusing to write v3 content into data/contract/{out.resolve().name}: "
             f"v1 and v2 are frozen history"])

    problems = validate_v3(scenario_v3, site_table)
    if problems:
        raise contract.ContractValidationError(problems)
    schema = build_schema_v3()
    schema_problems = contract.validate_against_json_schema(scenario_v3, schema)
    if schema_problems:
        raise contract.ContractValidationError(schema_problems)

    out.mkdir(parents=True, exist_ok=True)
    (out / "schema.json").write_text(json.dumps(schema, indent=2))
    scenario_v3.to_csv(out / "scenario_table.csv", index=False)
    site_table.to_csv(out / "site_table.csv", index=False)
    provenance.to_csv(out / "source_provenance.csv", index=False)
    standards_register.to_csv(out / "standards_register.csv", index=False)
    (out / "assumptions.json").write_text(json.dumps(assumptions, indent=2))

    tables = ["schema.json", "scenario_table.csv", "site_table.csv",
              "source_provenance.csv", "standards_register.csv", "assumptions.json"]
    manifest = {
        "contract_version": SCHEMA_VERSION_V3,
        "model_version": MODEL_VERSION,
        "model_version_note": (
            f"Model version {MODEL_VERSION} is the V3 model with the {DECISION} plan: the "
            "milestone2_v3 port plan follows the fixed-anchor ranking and its pathway is the V3 "
            "rule over the V3 targets. Contracts v1 and v2 were produced by model version "
            f"{config.MODEL_VERSION_V1_V2}. Model version {config.MODEL_VERSION_V4} is reserved "
            "for when V4 is genuinely complete and is not claimed by this artifact."),
        "supersedes": SCHEMA_VERSION_V2,
        "decision": DECISION,
        "authoritative": True,
        "run_id": run_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "producer": {"package": "fcf_m2", "module": "fcf_m2.contract_v3"},
        "inputs": inputs_hashed,
        "tables": {name: contract.sha256_file(out / name) for name in tables},
        "reference_totals": totals,
        "history": history,
        "grid_factor": {
            "source": config.GRID_FACTOR_SOURCE,
            "value_lb_per_mwh": config.GRID_FACTOR_LB_PER_MWH,
            "vintage": config.GRID_FACTOR_VINTAGE,
        },
        "conventions": {
            "baseline_year": config.BASELINE_YEAR,
            "horizons": config.V3_HORIZONS,
            "cases": sorted(contract.VALID_CASES),
            "discount_rate_real": config.ECON["discount_rate_real"],
        },
        "relationship_to_v2": [
            "SAME CONTAINER. Every v2 field is present, in v2's order, with v2's semantics and "
            "v2's observation rules.",
            "NEW RUN. The values come from model version " + MODEL_VERSION + ", not from v1, so "
            "they are not carried from v2. The fields that differ are named in README.md.",
            "v1 and v2 are FROZEN HISTORY. Nothing regenerates or edits them; their manifest "
            "digests are pinned under 'history'.",
        ],
        "consumer_rules": [
            "Join on site_id only; site_name is display text.",
            "MATLAB refuses feasibility claims when capacity_basis is not "
            "verified_utility/verified_facility.",
            "Excel/Tableau/presentation quote contract values; no re-derivation.",
            "Any schema change bumps contract_version; consumers assert the major version.",
            "An empty observed_* field means NOT OBSERVED. It never means zero.",
            "Quote this contract for current figures. Quote v1 or v2 only as the earlier "
            "legacy_v2 result, labelled as such.",
        ],
    }
    (out / "contract_manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "README.md").write_text(_readme_v3(totals, changes_md))
    return out


def _readme_v3(totals: dict, changes_md: str) -> str:
    official = totals["official"]
    earlier = totals["earlier_legacy_v2"]
    return f"""# Canonical data contract v3

**The authoritative output.** Produced by a new model run (model version {MODEL_VERSION})
under {DECISION}, 2026-10-18. v1 and v2 are frozen history and are never regenerated.

## Why it exists

The reference study's official future-ready (pathway) total is the one the canonical
`milestone2_v3` rules produce: **{official['starter']} starter ports and a {official['pathway']}-port
pathway**. v1 and v2 hold **{earlier['starter']} / {earlier['pathway']}**, the earlier `legacy_v2`
result: until {DECISION} the V3 plan kept the cohort-relative legacy ranking and the legacy
pathway rule so that {earlier['pathway']} survived. A reviewer noted that the project published two
output versions without saying which one counts. This one counts; the others are history.

`legacy_v2` mode still reproduces {earlier['starter']} / {earlier['pathway']} bit-exactly.

## What is different from v2

Same {len(v3_field_order())} fields, same order, same meaning, same validation rules. The values
differ only where the plan changed: the canonical plan follows the fixed-anchor ranking the
results show, and the pathway is the V3 rule (`right_sizing._future_ready` over the 2036/2046
V3 targets). Per site, against v2:

{changes_md}

Energy and emissions do not depend on port counts and are unchanged. Outside the scenario
table, the one difference is typographic: `standards_register.csv` writes a hyphen where the
frozen v1 and v2 registers carry an em dash (the generator was corrected after v1 was frozen).

## Read with care

`lifecycle_cost_nominal_usd`, `lifecycle_cost_npv_usd` and `avoided_overbuild_cost_usd` keep
v1's meaning: each site's base-case staged trajectory only. The `high` and `stress_combined`
rows of a horizon repeat its `base` value; they are not the cost of those scenarios.

**Zero real observations.** Every `observed_*` field is empty and every row reports
`awaiting_observed_data`. An empty `observed_*` field means NOT OBSERVED. It never means zero.

## Provenance

Own hash chain in `contract_manifest.json`, same construction as v1 and v2. The manifest pins
the v1 and v2 manifest digests under `history`. Rebuild with
`python scripts/build_contract_v3.py`; check with `--check`; validate with
`python -m fcf_m2.workflow validate-contract data/contract/v3`.
"""


__all__ = ["DECISION", "v3_field_order", "build_schema_v3", "from_run", "validate_v3",
           "write_contract_v3"]
