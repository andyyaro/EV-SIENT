"""Contract v2: is it really additive, and is v1 really frozen?

Two claims are made about v2 in prose. Prose does not hold, so both are asserted here:

1. **v1 is frozen.** Its manifest digest is pinned. Regenerating v1, editing a row by hand,
   or a producer change that happens to reach it all fail this file rather than being
   discovered by a consumer months later.
2. **v2 is additive.** Every v1 field survives with the same value. Only two fields are
   permitted to change, and each is named with its reason.

The third group of tests covers what v2 exists for: the observed-data fields, and the
refusals that stop an observed number appearing without an observation behind it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, contract, contract_v2, observed  # noqa: E402

V1 = REPO / "data/contract/v1"
V2 = REPO / "data/contract/v2"

#: The frozen v1 manifest digest.
#:
#: This is the whole immutability mechanism, so it is worth saying what changing it means.
#: If a code change alters v1 this test fails, and the ONLY correct response is to revert the
#: change or route it into v2. Updating this constant to match the new output is how an
#: immutable contract silently stops being immutable, and the four teammates who join later
#: will have no way to tell it happened.
V1_MANIFEST_SHA256 = "0dc7bf37a2c9b057edacf282ddea294994bef7a9d2369b3fcc65a784676b8df8"


@pytest.fixture(scope="module")
def v1_rows() -> pd.DataFrame:
    return pd.read_csv(V1 / "scenario_table.csv")


@pytest.fixture(scope="module")
def v2_rows() -> pd.DataFrame:
    return pd.read_csv(V2 / "scenario_table.csv")


@pytest.fixture(scope="module")
def site_table() -> pd.DataFrame:
    return pd.read_csv(V1 / "site_table.csv")


# --------------------------------------------------------------------- v1 is frozen

def test_v1_manifest_digest_is_pinned():
    """The pin. If this fails, something changed v1 -- find out what before touching it."""
    actual = contract.sha256_file(V1 / "contract_manifest.json")
    assert actual == V1_MANIFEST_SHA256, (
        "data/contract/v1/contract_manifest.json changed.\n"
        "v1 is frozen. Do not update this constant to make the test pass -- that is how an "
        "immutable contract stops being immutable without anyone noticing.\n"
        "Either revert whatever regenerated v1, or route the change into contract v2.\n"
        f"  expected {V1_MANIFEST_SHA256}\n  actual   {actual}")


def test_v1_hash_chain_still_verifies():
    """A pinned manifest proves nothing if the tables it describes drifted underneath it."""
    assert contract.verify_hash_chain(V1) == []


def test_v1_still_declares_version_1_and_the_old_horizon_vocabulary(v1_rows):
    """v1 keeps 'now' forever. That is the point of freezing it, not an oversight."""
    assert set(v1_rows.contract_version.unique()) == {config.SCHEMA_VERSION}
    assert "now" in set(v1_rows.horizon_label.unique())


def test_writing_v2_into_the_v1_directory_is_refused(tmp_path, v2_rows, site_table):
    frozen = tmp_path / "v1"
    frozen.mkdir()
    with pytest.raises(contract.ContractValidationError, match="v1 is frozen"):
        contract_v2.write_contract_v2(
            frozen, v2_rows, site_table, pd.DataFrame(), pd.DataFrame(), {}, "run", {})
    assert list(frozen.iterdir()) == [], "a refused write must leave nothing behind"


# --------------------------------------------------------------------- v2 is additive

def test_every_v1_field_survives_in_v2(v2_rows):
    missing = [f for f in contract.REQUIRED_FIELDS if f not in v2_rows.columns]
    assert missing == [], f"v2 dropped v1 field(s): {missing}"


def test_v1_fields_come_first_and_added_fields_follow(v2_rows):
    """Column order is part of the contract: a positional CSV consumer depends on it."""
    assert list(v2_rows.columns) == contract_v2.v2_field_order()
    assert list(v2_rows.columns[:len(contract.REQUIRED_FIELDS)]) == list(contract.REQUIRED_FIELDS)


def test_every_shared_field_holds_the_same_value(v1_rows, v2_rows):
    """The core additivity claim, checked value by value rather than asserted in a README."""
    permitted_to_change = {"contract_version", "horizon_label"}
    key = ["site_id", "horizon_year", "scenario_name"]
    a = v1_rows.sort_values(key).reset_index(drop=True)
    b = v2_rows.sort_values(key).reset_index(drop=True)
    assert len(a) == len(b) == 120

    differing = []
    for column in contract.REQUIRED_FIELDS:
        if column in permitted_to_change:
            continue
        left, right = a[column], b[column]
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            same = ((left - right).abs() < 1e-12) | (left.isna() & right.isna())
        else:
            same = left.astype(str) == right.astype(str)
        if not bool(same.all()):
            differing.append(f"{column} ({int((~same).sum())} rows)")
    assert differing == [], f"v2 is not additive; these fields changed: {differing}"


def test_the_two_permitted_changes_are_exactly_what_was_promised(v2_rows):
    assert set(v2_rows.contract_version.unique()) == {config.SCHEMA_VERSION_V2}
    assert "now" not in set(v2_rows.horizon_label.unique()), \
        "v2 must not carry the retired 'now' vocabulary"
    assert "baseline" in set(v2_rows.horizon_label.unique())


def test_horizon_label_change_is_a_rename_not_a_reassignment(v1_rows, v2_rows):
    """'now' became 'baseline' on the SAME rows. A relabelling that moved rows between
    horizons would pass a spelling check and be a data corruption."""
    key = ["site_id", "horizon_year", "scenario_name"]
    a = v1_rows.sort_values(key).reset_index(drop=True)
    b = v2_rows.sort_values(key).reset_index(drop=True)
    expected = a.horizon_label.map(lambda v: contract_v2.HORIZON_LABEL_V1_TO_V2.get(v, v))
    assert (expected == b.horizon_label).all()
    # and the year each label describes is untouched
    assert (a.horizon_year == b.horizon_year).all()
    assert set(b[b.horizon_label == "baseline"].horizon_year.unique()) == {config.BASELINE_YEAR}


def test_a_v1_consumer_reading_v2_gets_v1_answers(v1_rows, v2_rows):
    """The practical form of the additivity promise: the published headline totals."""
    def totals(df):
        base = df[(df.horizon_year == config.BASELINE_YEAR) & (df.scenario_name == "baseline")]
        return int(base.ports_active.sum()), int(base.ports_pathway_capacity.sum())
    assert totals(v2_rows) == totals(v1_rows) == (25, 48)


# --------------------------------------------------------------------- v2 validates

def test_tracked_v2_passes_every_v1_rule_and_every_v2_rule(v2_rows, site_table):
    assert contract_v2.validate_v2(v2_rows, site_table) == []


def test_tracked_v2_passes_its_own_json_schema(v2_rows):
    problems = contract.validate_against_json_schema(v2_rows, contract_v2.build_schema_v2())
    assert problems == []


def test_tracked_v2_hash_chain_verifies():
    assert contract.verify_hash_chain(V2) == []


def test_v2_schema_accepts_all_three_modes():
    """V4 is a THIRD mode. A v2 file of milestone2_v3 rows is what ships today."""
    modes = contract_v2.build_schema_v2()["properties"]["model_mode"]["enum"]
    assert set(modes) == {config.MODE_LEGACY, config.MODE_V3, config.MODE_V4}


def test_v2_schema_pins_the_v2_version():
    assert contract_v2.build_schema_v2()["properties"]["contract_version"] == {
        "const": config.SCHEMA_VERSION_V2}


def test_v1_schema_still_pins_the_v1_version():
    """Widening v2 must not have widened v1 through the shared build_schema() call."""
    assert contract.build_schema()["properties"]["contract_version"] == {
        "const": config.SCHEMA_VERSION}
    assert contract.build_schema()["properties"]["model_mode"]["enum"] == [
        config.MODE_LEGACY, config.MODE_V3]


# --------------------------------------------------------------------- honesty of the empty state

def test_v2_ships_with_zero_observations(v2_rows):
    """The state the repository is actually in. If this starts failing because real data
    arrived, the fix is to update the test with the provenance -- not to delete it."""
    for column in ["observed_months", "observed_utilization", "observed_uptime",
                   "observed_p90_wait_min", "observed_source_system",
                   "capacity_observed_date", "capacity_method", "capacity_conflict"]:
        blank = contract_v2._is_blank(v2_rows[column])
        assert bool(blank.all()), (
            f"{column} carries a value on {int((~blank).sum())} row(s), but no field "
            f"observations have been received. A value with no observation behind it is "
            f"exactly what v2's validation exists to catch.")


def test_every_row_still_reports_awaiting_observed_data(v2_rows):
    assert v2_rows.trigger_outcome.str.startswith("awaiting").all()
    assert (v2_rows.expansion_trigger_status.astype(str).str.contains("awaiting")).all()


def test_capacity_is_still_placeholder_at_all_twelve_sites(v2_rows):
    """v2 must not have quietly upgraded anything. The placeholder is the headline
    limitation of the entire study and it survives the version bump intact."""
    assert set(v2_rows.capacity_basis.unique()) == {"placeholder"}
    assert v2_rows.site_id.nunique() == 12


def test_confidence_reason_is_populated_and_specific(v2_rows):
    reasons = v2_rows.data_confidence_reason
    assert not contract_v2._is_blank(reasons).any()
    assert reasons.str.len().min() > 30, "a reason short enough to be generic is not a reason"
    assert reasons.str.contains("provenance").all()


def test_blank_detector_survives_a_csv_round_trip(tmp_path):
    """The bug this guards against: astype(str) renders a missing value as '<NA>', which is
    not empty, so a naive emptiness test reports every unobserved field as populated."""
    frame = pd.DataFrame({"x": ["", None, float("nan"), "value"]})
    frame.to_csv(tmp_path / "rt.csv", index=False)
    reloaded = pd.read_csv(tmp_path / "rt.csv")
    assert contract_v2._is_blank(reloaded.x).tolist() == [True, True, True, False]


# --------------------------------------------------------------------- v2's own refusals

@pytest.fixture
def clean_v2(v2_rows) -> pd.DataFrame:
    return v2_rows.copy()


def test_an_observed_value_without_an_observation_is_refused(clean_v2, site_table):
    clean_v2.loc[0, "observed_uptime"] = 0.98          # a measurement...
    # ...on a row that still says nothing was measured.
    problems = contract_v2.validate_v2(clean_v2, site_table)
    assert any("no observation behind it" in p for p in problems), problems


def test_a_verified_capacity_without_a_date_is_refused(clean_v2, site_table):
    # capacity_observed_date is already absent on every tracked row -- nothing has been
    # verified. Claiming a verified basis over that absence is the exact defect: a site
    # described as confirmed with no record of when anyone confirmed it.
    assert contract_v2._is_blank(clean_v2.capacity_observed_date).all()
    clean_v2.loc[0, "capacity_basis"] = "verified_utility"
    clean_v2.loc[0, "capacity_confidence"] = "high"
    problems = contract_v2.validate_v2(clean_v2, site_table)
    assert any("capacity_observed_date" in p for p in problems), problems


def test_the_retired_horizon_vocabulary_is_refused(clean_v2, site_table):
    clean_v2.loc[clean_v2.horizon_label == "baseline", "horizon_label"] = "now"
    problems = contract_v2.validate_v2(clean_v2, site_table)
    assert any("retired horizon vocabulary" in p for p in problems), problems


def test_a_v1_version_string_in_a_v2_table_is_refused(clean_v2, site_table):
    clean_v2["contract_version"] = config.SCHEMA_VERSION
    problems = contract_v2.validate_v2(clean_v2, site_table)
    assert any("contract_version must be" in p for p in problems), problems


def test_v2_still_enforces_the_v1_placeholder_rule(clean_v2, site_table):
    """RT-07 through validate_v2: v2 runs every v1 rule first, it does not replace them."""
    clean_v2.loc[0, "capacity_confidence"] = "high"     # on a placeholder-capacity row
    problems = contract_v2.validate_v2(clean_v2, site_table)
    assert any("RT-07" in p for p in problems), problems


def test_migration_refuses_a_table_that_is_not_v1_shaped():
    with pytest.raises(contract.ContractValidationError, match="cannot migrate"):
        contract_v2.migrate_v1_to_v2(pd.DataFrame({"site_id": ["FFX001"]}))


# --------------------------------------------------------------------- folding in observations

def _summary(site_id="FFX002", **kw):
    base = dict(site_id=site_id, days_observed=180, months_observed=5.91,
                avg_utilization=0.42, p90_wait_min=11.0, uptime=0.97,
                total_sessions=900.0, total_energy_kwh=18000.0)
    base.update(kw)
    return observed.SiteObservationSummary(**base)


def test_apply_observations_with_nothing_is_the_identity(v2_rows):
    """The state that ships. It must be a no-op on VALUES.

    ``check_dtype=False`` is not a weakened assertion. Applying nothing widens the empty
    text columns from the ``float64`` a CSV of empty cells reads back as, to ``object``, so
    the first real observation can be written into them at all. That widening is asserted
    separately below rather than waved through here -- what must not change is any value.
    """
    out = contract_v2.apply_observations(v2_rows.copy(), {}, {}, {})
    assert list(out.columns) == list(v2_rows.columns)

    # Every field inherited from v1 is untouched, values and dtypes both.
    pd.testing.assert_frame_equal(out[list(contract.REQUIRED_FIELDS)],
                                  v2_rows[list(contract.REQUIRED_FIELDS)])

    # Added fields are compared on MEANING, because `None` and `NaN` are the same fact and
    # assert_frame_equal calls them different. Which cells are empty must not change.
    for column in contract_v2.V2_ADDED_FIELDS:
        before, after = contract_v2._is_blank(v2_rows[column]), contract_v2._is_blank(out[column])
        assert (before == after).all(), \
            f"{column}: applying nothing changed which cells are empty"
        populated = ~before
        if populated.any():
            assert (v2_rows[column][populated].astype(str) ==
                    out[column][populated].astype(str)).all(), \
                f"{column}: applying nothing changed a populated value"


def test_applying_nothing_widens_empty_text_columns_so_the_first_observation_can_land(v2_rows):
    """The defect this prevents, exactly: a column of nothing but empty cells reads back
    from CSV as float64, and writing '2026-05-04' into a float64 column raises instead of
    upcasting. Uncaught, the run that received the project's first real utility record is
    the run that crashes."""
    from_disk = v2_rows.copy()
    assert from_disk.capacity_observed_date.dtype == "float64", \
        "precondition: the tracked v2 has no observed dates, so the column reads as float64"
    with pytest.raises(TypeError):
        from_disk.loc[0, "capacity_observed_date"] = "2026-05-04"

    widened = contract_v2.apply_observations(v2_rows.copy(), {}, {}, {})
    widened.loc[0, "capacity_observed_date"] = "2026-05-04"      # must not raise
    assert widened.loc[0, "capacity_observed_date"] == "2026-05-04"


def test_applying_a_session_summary_populates_only_that_site(v2_rows):
    out = contract_v2.apply_observations(v2_rows.copy(), {}, {"FFX002": _summary()}, {})
    touched = out[out.site_id == "FFX002"]
    untouched = out[out.site_id != "FFX002"]
    assert (touched.observed_uptime == 0.97).all()
    assert (touched.observed_months == 5.91).all()
    assert contract_v2._is_blank(untouched.observed_uptime).all()


def test_a_missing_metric_stays_empty_rather_than_becoming_zero(v2_rows):
    """The defect this prevents: a defaulted uptime of 1.0, or a defaulted wait of 0,
    walks straight past the gate that exists to catch an under-observed site."""
    out = contract_v2.apply_observations(
        v2_rows.copy(), {}, {"FFX002": _summary(uptime=None, p90_wait_min=None)}, {})
    touched = out[out.site_id == "FFX002"]
    assert contract_v2._is_blank(touched.observed_uptime).all()
    assert contract_v2._is_blank(touched.observed_p90_wait_min).all()
    assert (touched.observed_months == 5.91).all(), "the metrics that DO exist still land"


def test_applying_a_capacity_upgrade_records_when_and_how(v2_rows, site_table):
    upgrade = observed.CapacityUpgrade(
        site_id="PWC001", previous_basis="placeholder", new_basis="verified_utility",
        service_capacity_kw=400.0, spare_capacity_kw=180.0,
        capacity_source="Dominion Energy service record 2026-05-04",
        observed_date=date(2026, 5, 4), method="utility_service_record")
    out = contract_v2.apply_observations(v2_rows.copy(), {"PWC001": upgrade}, {}, {})
    touched = out[out.site_id == "PWC001"]
    assert (touched.capacity_basis == "verified_utility").all()
    assert (touched.capacity_observed_date == "2026-05-04").all()
    assert (touched.capacity_method == "utility_service_record").all()
    assert (touched.service_capacity_kw == 400.0).all()
    # and the other eleven sites are untouched -- one site's utility record says nothing
    # about anyone else's panel.
    assert set(out[out.site_id != "PWC001"].capacity_basis.unique()) == {"placeholder"}


def test_a_capacity_conflict_is_carried_not_resolved(v2_rows):
    upgrade = observed.CapacityUpgrade(
        site_id="PWC001", previous_basis="placeholder", new_basis="verified_utility",
        service_capacity_kw=350.0, spare_capacity_kw=150.0,
        capacity_source="utility record | CONFLICT, unresolved",
        observed_date=date(2026, 5, 4), method="utility_service_record",
        conflicts=["service_capacity_kw disagreement: verified_utility=400 kW, "
                   "verified_facility=350 kW"])
    out = contract_v2.apply_observations(v2_rows.copy(), {"PWC001": upgrade}, {}, {})
    conflict = out[out.site_id == "PWC001"].capacity_conflict
    assert conflict.str.contains("disagreement").all()
    assert conflict.str.contains("400").all() and conflict.str.contains("350").all(), \
        "both disputed values must survive; a conflict silently resolved is a number invented"


def test_capacity_upgrade_carries_the_winning_method():
    """observed.resolve_capacity must report HOW capacity was established, not only that
    it was. v2 needs the controlled value, not a sentence a consumer has to parse."""
    obs = observed.CapacityObservation(
        site_id="FFX001", observed_date=date(2026, 6, 1), method="facility_panel_schedule",
        source_org="City of Fairfax Facilities", source_document="panel schedule PS-14",
        observer="J. Rivera", service_capacity_kw=300.0, spare_capacity_kw=120.0)
    upgrades = observed.resolve_capacity([obs])
    assert upgrades["FFX001"].method == "facility_panel_schedule"
    assert upgrades["FFX001"].new_basis == "verified_facility"


def test_a_folded_observation_then_passes_validation(v2_rows, site_table):
    """End to end: fold a full observation set in and the result is a valid v2 table.
    This is the shape v2 takes the day real data arrives."""
    upgrade = observed.CapacityUpgrade(
        site_id="PWC001", previous_basis="placeholder", new_basis="verified_utility",
        service_capacity_kw=400.0, spare_capacity_kw=180.0,
        capacity_source="Dominion Energy service record 2026-05-04",
        observed_date=date(2026, 5, 4), method="utility_service_record")
    decision = type("D", (), {"outcome": "hold", "equity_override_applied": False,
                              "rule_trace": ["uptime=0.97 >= 0.95", "utilization 0.42 < 0.60"]})()
    out = contract_v2.apply_observations(
        v2_rows.copy(), {"PWC001": upgrade}, {"PWC001": _summary("PWC001")},
        {"PWC001": decision})
    # RT-07 requires a placeholder assumption_flag only on placeholder rows; PWC001 is now
    # verified, so its flag must no longer claim placeholder capacity.
    out.loc[out.site_id == "PWC001", "assumption_flag"] = "capacity verified 2026-05-04"
    out.loc[out.site_id == "PWC001", "capacity_confidence"] = "high"
    assert contract_v2.validate_v2(out, site_table) == []


# --------------------------------------------------------------------- the builder is reproducible

def test_rebuilding_v2_reproduces_the_tracked_bytes():
    """A generated artifact that cannot be regenerated is a hand-edited artifact wearing a
    disguise. Runs the real script rather than re-calling the library."""
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_contract_v2.py"), "--check"],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_manifest_records_its_parent():
    manifest = json.loads((V2 / "contract_manifest.json").read_text())
    assert manifest["contract_version"] == config.SCHEMA_VERSION_V2
    assert manifest["supersedes"] == config.SCHEMA_VERSION
    assert manifest["model_version"] == config.MODEL_VERSION_V4
    # v2 records the exact v1 it was derived from, so "which v1?" is answerable later.
    assert manifest["inputs"]["contract/v1/contract_manifest.json"] == V1_MANIFEST_SHA256


def test_v2_readme_states_the_empty_field_rule():
    readme = (V2 / "README.md").read_text()
    assert "NOT OBSERVED" in readme
    assert "never means zero" in readme.lower()
    assert "frozen" in readme.lower()
