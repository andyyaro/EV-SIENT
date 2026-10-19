"""Contract v3: the one authoritative output, with v1 and v2 kept as separate history (DEC-027).

Claims made about v3 in prose, asserted here:

1. **v1 and v2 are untouched.** Their manifests are pinned (v1 in ``test_contract_v2.py``,
   v2 here), and v3 records both digests as its history.
2. **v3 is the canonical run.** 25 starter / 47 pathway, per site as the canonical rules give
   them, and a fresh run of the model reproduces it (``build_contract_v3.py --check``).
3. **v3 is v2's container.** Same fields, order and rules, so a v2 reader needs no code change,
   only the major version it asserts.
4. **The only differences from v2 are the ones DEC-027 made.** Every field outside the plan
   and its consequences holds v2's value.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, contract, contract_v2, contract_v3  # noqa: E402

V1 = REPO / "data/contract/v1"
V2 = REPO / "data/contract/v2"
V3 = REPO / "data/contract/v3"

#: The frozen v2 manifest digest. Same rule as v1's pin: if this fails, something rewrote
#: v2. Revert it; do not update the constant.
V2_MANIFEST_SHA256 = "747ddc61333d7d701849ac6bffe5262711ff465c027628b1ada1475432eb317d"

#: Fields DEC-027 is allowed to move, and why each moves: the plan (ports, pathway, notes),
#: the queue at those ports (utilisation and the two waits), and the costs of that plan.
PERMITTED_TO_DIFFER = {
    "contract_version", "run_id", "generated_at", "horizon_label",
    "ports_active", "ports_pathway_capacity", "notes",
    "utilization", "average_wait_minutes", "peak_wait_minutes",
    "lifecycle_cost_nominal_usd", "lifecycle_cost_npv_usd", "avoided_overbuild_cost_usd",
}


@pytest.fixture(scope="module")
def v2_rows() -> pd.DataFrame:
    return pd.read_csv(V2 / "scenario_table.csv")


@pytest.fixture(scope="module")
def v3_rows() -> pd.DataFrame:
    return pd.read_csv(V3 / "scenario_table.csv")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((V3 / "contract_manifest.json").read_text())


def _totals(df: pd.DataFrame) -> tuple[int, int]:
    base = df[(df.horizon_year == config.BASELINE_YEAR) & (df.scenario_name == "baseline")]
    return int(base.ports_active.sum()), int(base.ports_pathway_capacity.sum())


# --------------------------------------------------------------------- history is untouched

def test_v2_manifest_digest_is_pinned():
    actual = contract.sha256_file(V2 / "contract_manifest.json")
    assert actual == V2_MANIFEST_SHA256, (
        "data/contract/v2/contract_manifest.json changed. v2 is frozen history since DEC-027; "
        "revert whatever rewrote it, and put new numbers in v3.")


def test_v3_pins_the_history_it_replaces(manifest):
    assert manifest["history"] == {
        "contract/v1/contract_manifest.json": contract.sha256_file(V1 / "contract_manifest.json"),
        "contract/v2/contract_manifest.json": contract.sha256_file(V2 / "contract_manifest.json"),
    }
    assert manifest["supersedes"] == config.SCHEMA_VERSION_V2
    assert manifest["decision"] == "DEC-027" and manifest["authoritative"] is True


def test_history_still_holds_the_earlier_legacy_v2_totals(v2_rows):
    assert _totals(pd.read_csv(V1 / "scenario_table.csv")) == _totals(v2_rows) == (25, 48)


def test_writing_v3_into_a_frozen_directory_is_refused(tmp_path, v3_rows):
    for name in ("v1", "v2"):
        frozen = tmp_path / name
        frozen.mkdir()
        with pytest.raises(contract.ContractValidationError, match="frozen history"):
            contract_v3.write_contract_v3(frozen, v3_rows, pd.DataFrame(), pd.DataFrame(),
                                          pd.DataFrame(), {}, "run", {}, {}, {}, "")
        assert list(frozen.iterdir()) == []


# --------------------------------------------------------------------- v3 is the canonical run

def test_v3_holds_the_official_totals(v3_rows, manifest):
    assert _totals(v3_rows) == (contract.REFERENCE_STARTER_TOTAL, contract.REFERENCE_PATHWAY_TOTAL) == (25, 47)
    assert manifest["reference_totals"]["official"]["pathway"] == 47
    assert manifest["reference_totals"]["earlier_legacy_v2"]["pathway"] == 48
    assert manifest["model_version"] == config.MODEL_VERSION != config.MODEL_VERSION_V1_V2


def test_v3_pathway_ceiling_holds_at_every_horizon(v3_rows):
    for (year, case), rows in v3_rows.groupby(["horizon_year", "scenario_name"]):
        assert int(rows.ports_pathway_capacity.sum()) == 47, (year, case)
    assert (v3_rows.ports_active <= v3_rows.ports_pathway_capacity).all()


def test_v3_passes_every_rule_its_schema_and_its_hash_chain(v3_rows):
    site = pd.read_csv(V3 / "site_table.csv")
    assert contract_v3.validate_v3(v3_rows, site) == []
    assert contract.validate_against_json_schema(v3_rows, contract_v3.build_schema_v3()) == []
    assert contract.verify_hash_chain(V3) == []


def test_rt04_holds_each_contract_to_its_own_models_totals(v2_rows, v3_rows):
    """48 is right for the 3.0.0 rows of v1/v2 and wrong for v3, and the reverse."""
    site = pd.read_csv(V3 / "site_table.csv")
    assert contract.validate_scenario_table(v2_rows, site, model_version=config.MODEL_VERSION_V1_V2) == []
    wrong = contract.validate_scenario_table(v2_rows, site, model_version=config.MODEL_VERSION)
    assert any("RT-04: pathway total 48 != 47" in p for p in wrong)
    wrong = contract.validate_scenario_table(v3_rows, site, model_version=config.MODEL_VERSION_V1_V2)
    assert any("RT-04: pathway total 47 != 48" in p for p in wrong)


def test_tracked_v3_matches_a_fresh_run_of_the_model():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_contract_v3.py"), "--check"],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_contract_command_accepts_v3():
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, 'src'); from fcf_m2 import workflow; "
                               "workflow.main(['validate-contract', 'data/contract/v3'])"],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Contract v3.0.0 valid" in result.stdout


# --------------------------------------------------------------------- v3 is v2's container

def test_v3_has_v2s_fields_in_v2s_order(v3_rows):
    assert list(v3_rows.columns) == contract_v2.v2_field_order() == contract_v3.v3_field_order()
    assert set(v3_rows.contract_version.astype(str)) == {config.SCHEMA_VERSION_V3}
    assert "now" not in set(v3_rows.horizon_label)


def test_v3_ships_with_zero_observations(v3_rows):
    for column in contract_v2.V2_ADDED_FIELDS:
        if column.startswith("observed_") or column.startswith("capacity_"):
            assert bool(contract_v2._is_blank(v3_rows[column]).all()), column
    assert v3_rows.trigger_outcome.astype(str).str.startswith("awaiting").all()


# --------------------------------------------------------------------- only DEC-027 moved

def test_every_other_field_holds_v2s_value(v2_rows, v3_rows):
    key = ["site_id", "horizon_year", "scenario_name"]
    a = v2_rows.sort_values(key).reset_index(drop=True)
    b = v3_rows.sort_values(key).reset_index(drop=True)
    differing = []
    for column in a.columns:
        if column in PERMITTED_TO_DIFFER:
            continue
        left, right = a[column], b[column]
        numeric = (pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right)
                   and not pd.api.types.is_bool_dtype(left))
        if numeric:
            same = ((left - right).abs() < 1e-9) | (left.isna() & right.isna())
        else:
            same = left.astype(str) == right.astype(str)
        if not bool(same.all()):
            differing.append(column)
    assert differing == [], f"fields DEC-027 does not explain changed: {differing}"


def test_emissions_and_energy_did_not_move(v2_rows, v3_rows):
    """Emissions follow energy, and energy follows sessions, not ports."""
    for column in ("net_co2e_kg", "energy_delivered_kwh"):
        assert v2_rows[column].sum() == pytest.approx(v3_rows[column].sum())


def test_v3_readme_names_the_decision_and_the_history():
    readme = (V3 / "README.md").read_text()
    assert "DEC-027" in readme and "legacy_v2" in readme
    assert "47-port" in readme and "25 / 48" in readme
    assert "\u2014" not in readme
