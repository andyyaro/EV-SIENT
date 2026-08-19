"""Contract v2: additive over v1, carrying what the V4 field-data loop produces.

v1 is **frozen**. Nothing in this module writes to it, and
``tests/test_contract_v2.py`` pins its manifest digest so a change to it fails a gate rather
than being noticed later. v2 lives beside it at ``data/contract/v2/`` with its own hash
chain.

Additive means additive
-----------------------
Every one of v1's 48 fields appears in v2 with **identical semantics and identical values**
for the same run. A consumer written against v1 can read a v2 row and get the same answers.
The migration is therefore a widening, not a translation, and the test suite asserts that
rather than trusting it.

What v2 adds, and why each field could not go in v1
--------------------------------------------------
v1 has exactly one field for the observed world, ``expansion_trigger_status``, and it holds
``awaiting_observed_data`` on all 120 rows because there was no way to observe anything.
V4 built that way in, which produces information v1 has nowhere to put:

* the measured values behind a trigger decision, and the decision's own reasoning
* when and how a capacity value was confirmed, and whether two sources disagreed
* why a site's confidence is what it is, rather than only what it is

One correction rides along
--------------------------
``horizon_label`` takes ``now`` in v1. It is arithmetically correct and it decays: read in
2036, "now" is simply false, and it is the one horizon word the program names as prohibited.
v2 uses ``baseline``. v1 keeps ``now`` forever, because v1 is frozen -- which is exactly the
situation an immutable contract plus an additive successor is designed to handle.

The guardrail
-------------
**v2 ships with zero real observations.** Every added field is empty, or carries
``awaiting_observed_data``, and says so. A site whose capacity is still a placeholder still
says ``placeholder`` in v2, exactly as loudly as in v1.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config, contract
from .config import (
    MODEL_VERSION,
    MODEL_VERSION_V4,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
)

# --------------------------------------------------------------------------- schema delta

#: Fields v2 adds. Ordered as they appear in the emitted table, after every v1 field.
V2_ADDED_FIELDS: dict[str, str] = {
    # -- what was observed -------------------------------------------------------------
    "observed_months": "months of charger operating data behind the trigger decision",
    "observed_utilization": "measured average utilisation, 0-1; empty when unobserved",
    "observed_uptime": "measured availability, 0-1; the gate the policy checks first",
    "observed_p90_wait_min": "measured p90 wait, minutes; empty when unobserved",
    "observed_source_system": "which system reported it, for provenance",
    # -- how capacity came to be believed ------------------------------------------------
    "capacity_observed_date": "when the capacity value was confirmed; empty while placeholder",
    "capacity_method": "how it was established (utility record, panel schedule, walkthrough...)",
    "capacity_conflict": "text of any unresolved disagreement between sources; empty when none",
    # -- why the model says what it says ---------------------------------------------------
    "data_confidence_reason": "why the confidence level is what it is, not merely what it is",
    "trigger_outcome": "evaluated decision: expand_review_recommended | hold | awaiting_observed_data",
    "trigger_rule_trace": "the rules that produced that outcome, in order",
    "trigger_equity_override": "whether the equity override lowered the utilisation gate",
}

#: The v1 field whose vocabulary v2 corrects. v1 keeps its value; v1 is frozen.
HORIZON_LABEL_V1_TO_V2 = {"now": "baseline"}

#: What an added field says when nothing has been observed. Never a zero, never a default --
#: a defaulted uptime of 1.0 would walk straight past the reliability gate.
#:
#: ``None`` rather than ``""`` deliberately. An empty string survives a CSV round-trip as
#: ``NaN``, so a ``""`` in memory and a ``NaN`` from disk would be two encodings of the same
#: fact, and every rule downstream would have to know both. ``None`` writes as an empty CSV
#: cell and reads back as ``NaN``, which JSON Schema sees as ``null`` -- one meaning,
#: "not observed", with one representation at each layer.
UNOBSERVED = None
UNOBSERVED_STATUS = "awaiting_observed_data (proposed policy, not adopted)"

#: Added fields that hold text. Tracked explicitly because a column of nothing but empties
#: reads back from CSV as ``float64``, and assigning a date string into a float column raises
#: rather than upcasting. ``apply_observations`` normalises these before writing into them.
V2_TEXT_FIELDS = ("observed_source_system", "capacity_observed_date", "capacity_method",
                  "capacity_conflict", "data_confidence_reason", "trigger_outcome",
                  "trigger_rule_trace")


def v2_field_order() -> list[str]:
    """Every v1 field in its original order, then every v2 addition."""
    return list(contract.REQUIRED_FIELDS) + list(V2_ADDED_FIELDS)


def build_schema_v2() -> dict:
    """v1's schema widened, not rewritten.

    Starts from ``contract.build_schema()`` so a change to a shared field cannot diverge
    between the two versions -- there is one definition of what ``ports_active`` is.
    """
    schema = contract.build_schema()
    schema["title"] = "FCF canonical scenario row (contract v2)"
    schema["required"] = v2_field_order()
    schema["properties"]["contract_version"] = {"const": SCHEMA_VERSION_V2}
    # horizon_label's vocabulary changes; every other shared property is inherited as-is.
    schema["properties"]["horizon_label"] = {
        "enum": sorted({HORIZON_LABEL_V1_TO_V2.get(v, v)
                        for v in schema["properties"]["horizon_label"]["enum"]})
    }
    # V4 is a THIRD mode. legacy_v2 and milestone2_v3 rows remain valid v2 rows -- v2 is a
    # container change, not a modelling change, and a v2 file full of milestone2_v3 rows is
    # exactly what this repository ships today.
    schema["properties"]["model_mode"] = {
        "enum": [config.MODE_LEGACY, config.MODE_V3, config.MODE_V4]
    }
    # ``null`` is admissible on every added field except the two that are always populated.
    # It is not laxness: null IS the value, meaning NOT OBSERVED. Requiring a number here
    # would force a default into the column, and the only defaults available -- 0, or 1.0 for
    # uptime -- are each a number that reads as a measurement and walks past a gate.
    schema["properties"].update({
        "observed_months": {"type": ["number", "null"], "minimum": 0},
        "observed_utilization": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "observed_uptime": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "observed_p90_wait_min": {"type": ["number", "null"], "minimum": 0},
        "observed_source_system": {"type": ["string", "null"]},
        "capacity_observed_date": {"type": ["string", "null"]},
        "capacity_method": {"type": ["string", "null"],
                            "enum": [None, "", *sorted(set(observed_methods()))]},
        "capacity_conflict": {"type": ["string", "null"]},
        # Always populated: a row with no stated reason for its confidence is the thing the
        # V4 loop exists to eliminate.
        "data_confidence_reason": {"type": "string", "minLength": 20},
        "trigger_outcome": {"type": "string", "minLength": 4},
        "trigger_rule_trace": {"type": ["string", "null"]},
        "trigger_equity_override": {"type": ["boolean", "string", "null"]},
    })
    return schema


def observed_methods() -> list[str]:
    """The controlled capacity-observation vocabulary, read from its one definition.

    Imported lazily to keep ``contract_v2`` importable without ``observed``'s dependencies,
    and read rather than restated so the schema cannot drift from the ingestion rules.
    """
    from .observed import METHOD_TO_BASIS
    return list(METHOD_TO_BASIS)


# --------------------------------------------------------------------------- migration

def migrate_v1_to_v2(scenario_v1: pd.DataFrame,
                     confidence_reasons: dict[str, str] | None = None) -> pd.DataFrame:
    """Widen a v1 scenario table into v2 shape.

    Pure and total: it reads a v1 table and returns a v2 table, touching nothing on disk.
    Every v1 value is carried through **unchanged** except ``contract_version`` and the
    ``horizon_label`` vocabulary correction, both of which are asserted by the tests.

    Added fields are filled with the honest empty state, never a plausible default.
    """
    missing = [f for f in contract.REQUIRED_FIELDS if f not in scenario_v1.columns]
    if missing:
        raise contract.ContractValidationError(
            [f"cannot migrate: v1 table is missing {', '.join(missing)}"])

    out = scenario_v1.copy()
    out["contract_version"] = SCHEMA_VERSION_V2
    out["horizon_label"] = out["horizon_label"].map(lambda v: HORIZON_LABEL_V1_TO_V2.get(v, v))

    reasons = confidence_reasons or {}
    for name in V2_ADDED_FIELDS:
        out[name] = UNOBSERVED
    out["trigger_outcome"] = UNOBSERVED_STATUS
    out["trigger_equity_override"] = False
    out["data_confidence_reason"] = out["site_id"].map(
        lambda sid: reasons.get(sid, "no field observations received; confidence derives from "
                                     "typed source provenance only"))

    return out[v2_field_order()]


def apply_observations(scenario_v2: pd.DataFrame, capacity_upgrades: dict,
                       session_summaries: dict, trigger_decisions: dict) -> pd.DataFrame:
    """Fold real observations into a v2 table.

    Separate from ``migrate_v1_to_v2`` on purpose: migration is a shape change and this is a
    content change, and conflating them would make it impossible to tell whether a v2 value
    came from v1 or from the field. With no observations supplied this is the identity
    function, which is the state the repository ships in.
    """
    out = scenario_v2.copy()

    # A v2 table read back from CSV has float64 columns wherever nothing was ever observed,
    # because a column of empty cells has no other type to be. Writing "2026-05-04" into one
    # raises rather than upcasting. Widen to object first, so the first real observation the
    # project ever receives lands instead of crashing the run that receives it.
    for name in V2_TEXT_FIELDS:
        if name in out.columns and out[name].dtype != object:
            out[name] = out[name].astype(object).where(~out[name].isna(), None)

    for site_id, upgrade in (capacity_upgrades or {}).items():
        rows = out.site_id == site_id
        if not rows.any():
            continue
        out.loc[rows, "capacity_basis"] = upgrade.new_basis
        out.loc[rows, "capacity_source"] = upgrade.capacity_source
        out.loc[rows, "capacity_observed_date"] = upgrade.observed_date.isoformat()
        out.loc[rows, "capacity_method"] = upgrade.method
        out.loc[rows, "capacity_conflict"] = " | ".join(upgrade.conflicts)
        if upgrade.service_capacity_kw is not None:
            out.loc[rows, "service_capacity_kw"] = upgrade.service_capacity_kw
        if upgrade.spare_capacity_kw is not None:
            out.loc[rows, "spare_capacity_kw"] = upgrade.spare_capacity_kw

    for site_id, summary in (session_summaries or {}).items():
        rows = out.site_id == site_id
        if not rows.any():
            continue
        out.loc[rows, "observed_months"] = summary.months_observed
        # Written only when actually derived. A missing metric stays empty and the
        # trigger trace says why, rather than a zero that reads like a measurement.
        if summary.avg_utilization is not None:
            out.loc[rows, "observed_utilization"] = round(summary.avg_utilization, 4)
        if summary.uptime is not None:
            out.loc[rows, "observed_uptime"] = round(summary.uptime, 4)
        if summary.p90_wait_min is not None:
            out.loc[rows, "observed_p90_wait_min"] = summary.p90_wait_min

    for site_id, decision in (trigger_decisions or {}).items():
        rows = out.site_id == site_id
        if not rows.any():
            continue
        out.loc[rows, "trigger_outcome"] = decision.outcome
        out.loc[rows, "trigger_rule_trace"] = " | ".join(decision.rule_trace)
        out.loc[rows, "trigger_equity_override"] = decision.equity_override_applied

    return out


# --------------------------------------------------------------------------- validation

def _is_blank(series: pd.Series) -> pd.Series:
    """True where a value is genuinely absent, in memory OR after a CSV round-trip.

    ``astype(str)`` is the trap this exists to avoid: on a missing value it produces the
    string ``"<NA>"`` (or ``"nan"``), which is not empty, so an emptiness test written that
    way reports every unobserved field as populated. That is not a cosmetic bug -- the
    orphaned-observation rule below would then fire on all 120 correct rows and the rule
    would be deleted for crying wolf, taking the real check with it.
    """
    return series.isna() | (series.astype(str).str.strip().isin(["", "nan", "<NA>", "None"]))


def validate_v2(scenario_v2: pd.DataFrame, site_table: pd.DataFrame) -> list[str]:
    """Every v1 rule, plus the rules that only make sense once observation is possible."""
    problems = contract.validate_scenario_table(scenario_v2, site_table)

    if set(scenario_v2.contract_version.unique()) != {SCHEMA_VERSION_V2}:
        problems.append(f"contract_version must be {SCHEMA_VERSION_V2} on every v2 row")

    stale = sorted(set(scenario_v2.horizon_label.unique()) & set(HORIZON_LABEL_V1_TO_V2))
    if stale:
        problems.append(
            f"v2 must not carry the retired horizon vocabulary {stale}; "
            f"v1 keeps it, v2 corrects it")

    missing = [f for f in V2_ADDED_FIELDS if f not in scenario_v2.columns]
    if missing:
        problems.append(f"v2 is missing added field(s): {', '.join(missing)}")

    # The guardrail, enforced rather than documented: an observed value may not appear on a
    # row that claims no observation, because that is a number with no provenance.
    # Checked on EVERY observed_* column, not just uptime. The rule above is stated
    # generally and was enforced on one field; observed_utilization, observed_p90_wait_min
    # and observed_months could all be set on an "awaiting" row and validate clean. Measured
    # before fixing: setting all three on row 0 of the shipped v2 returned no problems.
    # Guarded. Widening this check to every observed_* column hoisted `claims_none` out of
    # the `if "observed_uptime" in columns` test it used to sit inside, so a v2-labelled table
    # MISSING the added fields stopped being reported ("v2 is missing added field(s): ...")
    # and started dying with an AttributeError before it could report anything -- reached
    # through the validate-contract platform operation, which would show a traceback instead
    # of a readable FAIL. Widening a check must not narrow the inputs it survives.
    if "trigger_outcome" not in scenario_v2.columns:
        return problems
    claims_none = scenario_v2.trigger_outcome.astype(str).str.startswith("awaiting")
    for column in (c for c in V2_ADDED_FIELDS if c.startswith("observed_")):
        if column not in scenario_v2.columns:
            continue
        orphaned = scenario_v2[claims_none & ~_is_blank(scenario_v2[column])]
        if not orphaned.empty:
            problems.append(
                f"{len(orphaned)} row(s) carry {column} while reporting "
                f"awaiting_observed_data - an observed value with no observation behind it")

    # A verified capacity must name when and how it was verified.
    if "capacity_observed_date" in scenario_v2.columns:
        verified = scenario_v2.capacity_basis.astype(str).str.startswith("verified")
        undated = scenario_v2[verified & _is_blank(scenario_v2.capacity_observed_date)]
        if not undated.empty:
            problems.append(
                f"{len(undated)} row(s) claim a verified capacity_basis with no "
                f"capacity_observed_date - verification with no date is not verification")

    return problems


# --------------------------------------------------------------------------- writing

def write_contract_v2(out_dir: str | Path, scenario_v2: pd.DataFrame, site_table: pd.DataFrame,
                      provenance: pd.DataFrame, standards_register: pd.DataFrame,
                      assumptions: dict, run_id: str, inputs_hashed: dict[str, str],
                      model_version: str = MODEL_VERSION) -> Path:
    """Write ``data/contract/v2/`` with its own hash chain. Never touches v1.

    ``model_version`` defaults to ``MODEL_VERSION`` (3.0.0), **not** to ``MODEL_VERSION_V4``,
    and the distinction is the whole point. The contract version and the model version are
    different facts: v2 is a container change, and the numbers inside today's v2 were
    produced by the V3 model, on rows that say ``model_mode = milestone2_v3``. Stamping
    4.0.0 on them would be a version claiming work that has not happened -- the same defect
    as a placeholder capacity presented as verified, one layer up. The bump happens when V4
    is genuinely complete, which is the program's own rule.
    """
    out = Path(out_dir)
    if out.resolve().name == "v1":
        raise contract.ContractValidationError(
            ["refusing to write v2 content into data/contract/v1: v1 is frozen"])
    out.mkdir(parents=True, exist_ok=True)

    problems = validate_v2(scenario_v2, site_table)
    if problems:
        raise contract.ContractValidationError(problems)

    schema = build_schema_v2()
    schema_problems = contract.validate_against_json_schema(scenario_v2, schema)
    if schema_problems:
        raise contract.ContractValidationError(schema_problems)

    (out / "schema.json").write_text(json.dumps(schema, indent=2))
    scenario_v2.to_csv(out / "scenario_table.csv", index=False)
    site_table.to_csv(out / "site_table.csv", index=False)
    provenance.to_csv(out / "source_provenance.csv", index=False)
    standards_register.to_csv(out / "standards_register.csv", index=False)
    (out / "assumptions.json").write_text(json.dumps(assumptions, indent=2))

    tables = ["schema.json", "scenario_table.csv", "site_table.csv",
              "source_provenance.csv", "standards_register.csv", "assumptions.json"]
    manifest = {
        "contract_version": SCHEMA_VERSION_V2,
        "model_version": model_version,
        "model_version_note": (
            "The contract version and the model version are separate facts. Contract v2 is a "
            "container change: it adds fields for observations. The numbers in it were "
            "produced by model version "
            f"{model_version}. Model version {MODEL_VERSION_V4} is reserved for when V4 is "
            "genuinely complete and is not claimed by this artifact."),
        "supersedes": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "producer": {"package": "fcf_m2", "module": "fcf_m2.contract_v2"},
        "inputs": inputs_hashed,
        "tables": {name: contract.sha256_file(out / name) for name in tables},
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
            "horizon_label_change": (
                "v1 used 'now' for the baseline year. v2 uses 'baseline': 'now' is "
                "time-relative text frozen into a dated artifact, and reads as false the "
                "moment the artifact is a year old."),
        },
        "relationship_to_v1": [
            "ADDITIVE. Every v1 field is present with identical semantics and identical "
            "values for the same run.",
            "v1 is FROZEN. Nothing regenerates or edits it. Its manifest digest is pinned "
            "by a test.",
            "A consumer written against v1 can read a v2 row and get the same answers.",
            f"v2 adds {len(V2_ADDED_FIELDS)} fields carrying what the V4 field-data loop "
            f"produces, which v1 had nowhere to put.",
        ],
        "consumer_rules": [
            "Join on site_id only; site_name is display text.",
            "MATLAB refuses feasibility claims when capacity_basis is not "
            "verified_utility/verified_facility.",
            "Excel/Tableau/presentation quote contract values; no re-derivation.",
            "Any schema change bumps contract_version; consumers assert the major version.",
            "An empty observed_* field means NOT OBSERVED. It never means zero.",
        ],
    }
    (out / "contract_manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "README.md").write_text(_readme_v2())
    return out


def _readme_v2() -> str:
    added = "\n".join(f"| `{name}` | {why} |" for name, why in V2_ADDED_FIELDS.items())
    return f"""# Canonical data contract v2

**Additive over v1. v1 is frozen and is never regenerated.**

Every one of v1's {len(contract.REQUIRED_FIELDS)} fields appears here with identical
semantics and identical values for the same run, so a consumer written against v1 reads a v2
row and gets the same answers. v2 adds {len(V2_ADDED_FIELDS)} fields carrying what the V4
field-data loop produces - information v1 had nowhere to put, because when v1 was written
there was no way to observe anything.

## What v2 adds

| Field | What it carries |
|---|---|
{added}

## The one correction

`horizon_label` used `now` for the baseline year. v2 uses `baseline`. `now` is
time-relative text frozen into a dated artifact: read a year later it is simply false, and it
is the one horizon word this program names as prohibited. **v1 keeps `now` forever**, because
v1 is frozen - which is precisely the situation an immutable contract plus an additive
successor exists to handle.

## What is in it today

**Zero real observations.** Every `observed_*` field is empty and every row reports
`awaiting_observed_data`. That is the correct state until a facility manager or the utility
sends something. A site whose capacity is a placeholder still says `placeholder`, exactly as
loudly as in v1.

**An empty `observed_*` field means NOT OBSERVED. It never means zero.** A defaulted uptime
of 1.0 would walk straight past the reliability gate that exists to catch exactly that.

## Rules enforced by validation, not merely stated

1. `contract_version` is `{SCHEMA_VERSION_V2}` on every row.
2. The retired `now` vocabulary may not appear.
3. A row reporting `awaiting_observed_data` may not carry an observed value - that would be
   a number with no observation behind it.
4. A `verified_*` capacity basis must name the date it was verified. Verification with no
   date is not verification.
5. Every v1 rule still applies, because `validate_v2` runs them first.

## Provenance

Own hash chain in `contract_manifest.json`, same construction as v1: SHA-256 over every
table plus every hashed input. Verify with `fcf_m2.contract.verify_hash_chain`.
"""


__all__ = [
    "V2_ADDED_FIELDS", "HORIZON_LABEL_V1_TO_V2", "UNOBSERVED", "UNOBSERVED_STATUS",
    "v2_field_order", "build_schema_v2", "migrate_v1_to_v2", "apply_observations",
    "validate_v2", "write_contract_v2",
]
