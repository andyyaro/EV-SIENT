"""Intake must let a jurisdiction in without quietly making its data look better than it is.

The property under test
-----------------------
DEC-000's hard constraint is one sentence: **cleaning must never silently improve data
quality.** Most of this file is that sentence turned into assertions, because the failure it
describes is invisible by construction - a run that succeeds on data nobody inspected looks
exactly like a run on data somebody did.

The gate (DEC-000): a deliberately messy third-party-shaped fixture runs end to end and
produces a **correctly-degraded** confidence rating, with every transformation traceable.
Correctly-degraded means neither of the two easy answers: not a refusal, and not a confident
number.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import confidence, intake  # noqa: E402

FIXTURE = REPO / "data/intake/fixtures/messy_third_party.csv"

pytestmark = pytest.mark.skipif(not FIXTURE.is_file(), reason="messy fixture absent")


@pytest.fixture(scope="module")
def messy() -> pd.DataFrame:
    return pd.read_csv(FIXTURE)


@pytest.fixture(scope="module")
def proposal(messy):
    return intake.propose(messy)


# ---------------------------------------------------------------- the fixture is messy

def test_the_fixture_uses_no_canonical_column_names(messy):
    """If the fixture accidentally used our names, every test below would pass vacuously."""
    canonical = set(intake._all_fields())
    overlap = canonical & set(messy.columns)
    assert overlap == set(), f"fixture uses canonical names: {overlap}"


# ---------------------------------------------------------------- propose changes nothing

def test_proposing_does_not_modify_the_supplied_frame(messy):
    """A user must be able to look before anything happens to their file."""
    before = messy.copy(deep=True)
    intake.propose(messy)
    pd.testing.assert_frame_equal(messy, before)


def test_every_finding_explains_itself_in_one_sentence(proposal):
    """A transformation that cannot be explained to the user in one sentence does not ship."""
    for finding in proposal.findings:
        assert finding.explain.strip(), finding
        assert finding.explain.count(".") <= 2, (
            f"finding for {finding.field} needs more than one sentence, which means the "
            f"transformation is too clever to ship: {finding.explain}")


def test_a_finding_cannot_be_created_without_an_explanation():
    with pytest.raises(ValueError, match="one sentence"):
        intake.Finding("warning", "some_field", "   ")


# ---------------------------------------------------------------- absence is not improvement

def test_an_absent_field_stays_absent_and_is_never_defaulted(messy, proposal):
    """The core of DEC-000. Substituting a plausible number for a missing one is precisely the
    silent improvement the rule forbids: the run succeeds and nothing downstream can tell the
    invented value from a supplied one."""
    assert "aadt_nearest" in proposal.absent
    canonical, _ = intake.apply(messy, proposal)
    assert canonical["aadt_nearest"].isna().all(), "an absent field was given a value"


def test_an_absence_is_reported_to_the_user_before_the_run(proposal):
    notes = [f for f in proposal.findings if f.field == "aadt_nearest"]
    assert notes, "the user is not told the field is missing"
    assert "absence" in notes[0].explain or "not present" in notes[0].explain


def test_an_absent_field_reaches_provenance_as_missing_not_omitted(proposal):
    """A field left OUT of the provenance table scores as though it was never expected, which
    makes an incomplete file look exactly as trustworthy as a complete one."""
    prov = intake.provenance_rows(proposal, ["S1"], "r", "org", "2026-07-28")
    assert "missing" in set(prov["source_class"]), (
        "the absent field's group did not reach provenance as missing")


# ---------------------------------------------------------------- guessing is bounded

def test_a_match_below_the_floor_is_reported_absent_not_guessed():
    """An absence is scored and visible; a wrong mapping is a wrong number with no trace."""
    frame = pd.DataFrame({"site_id": ["A"], "wholly_unrelated_column": [1]})
    proposal = intake.propose(frame)
    assert "wholly_unrelated_column" not in proposal.mapping.values()
    assert "aadt_nearest" in proposal.absent


def test_similar_but_different_fields_do_not_collide():
    """`l2_ports` and `dcfc_ports` are one token apart and mean different things. A character
    distance would confuse them; token overlap must not."""
    frame = pd.DataFrame({"site_id": ["A"], "l2_ports": [2], "dcfc_ports": [1]})
    proposal = intake.propose(frame)
    assert proposal.mapping.get("existing_l2_ports_1mi") == "l2_ports"
    assert proposal.mapping.get("existing_dcfc_ports_3mi") == "dcfc_ports"


def test_every_inferred_mapping_is_flagged_as_inferred(proposal):
    """Whenever the supplied name differs from the canonical one, the mapping is a guess -
    regardless of how confidently it scored. Keying this off the match score alone let alias
    matches score 1.0 and be recorded as a confirmed source."""
    prov = intake.provenance_rows(proposal, ["S1"], "r", "org", "2026-07-28")
    inferred_groups = prov[prov["source_class"] == "unconfirmed"]
    assert len(inferred_groups) > 0, "no mapping was recorded as inferred, which cannot be right"


# ---------------------------------------------------------------- conversions announce themselves

def test_a_unit_conversion_is_applied_and_declared(messy, proposal):
    assert "avg_dwell_min" in proposal.conversions
    stated = [f for f in proposal.findings
              if f.field == "avg_dwell_min" and "multiplied" in f.explain]
    assert stated, "a unit conversion happened without telling the user"
    canonical, ledger = intake.apply(messy, proposal)
    # 1.5 hours in the file, 90 minutes in the model.
    assert canonical["avg_dwell_min"].iloc[0] == pytest.approx(90.0)
    assert any("multiplied" in entry.action for entry in ledger)


def test_a_unit_suffix_does_not_prevent_a_correct_match():
    """`trench_length_m` and `trenching_ft` mean the same thing measured differently. Leaving
    the suffix in the comparison made them score too low to match, and the field was reported
    absent while the file plainly supplied it."""
    frame = pd.DataFrame({"site_id": ["A"], "trench_length_m": [46]})
    proposal = intake.propose(frame)
    assert proposal.mapping.get("trenching_ft") == "trench_length_m"
    assert proposal.conversions.get("trenching_ft") == pytest.approx(3.280839895)


# ---------------------------------------------------------------- refusals

def test_a_file_with_no_site_identifier_is_refused():
    frame = pd.DataFrame({"some_number": [1, 2]})
    proposal = intake.propose(frame)
    assert proposal.refused
    with pytest.raises(ValueError, match="cannot be ingested"):
        intake.apply(frame, proposal)


def test_duplicate_site_identifiers_are_refused():
    """Two different places scored as one site is not a degraded answer, it is a wrong one."""
    frame = pd.DataFrame({"site_id": ["A", "A"], "staff": [1, 2]})
    proposal = intake.propose(frame)
    assert proposal.refused
    assert any("unique" in f.explain for f in proposal.findings)


def test_projected_coordinates_are_refused_not_reprojected():
    """Reprojecting by hand would move every site by an amount nobody could check, and doing it
    properly means a new dependency that is its own decision (DEC-000)."""
    frame = pd.DataFrame({"site_id": ["A"], "lat": [4512345.0], "lon": [512345.0]})
    proposal = intake.propose(frame)
    assert proposal.refused
    assert any("projected coordinate system" in f.explain for f in proposal.findings)


def test_apply_refuses_to_be_walked_past(messy):
    """The caller is expected to show findings to a human first. This is the guard for the
    caller that does not."""
    frame = pd.DataFrame({"site_id": ["A", "A"]})
    proposal = intake.propose(frame)
    with pytest.raises(ValueError):
        intake.apply(frame, proposal)


# ---------------------------------------------------------------- THE GATE

def test_the_messy_file_runs_end_to_end_with_degraded_confidence(messy, proposal):
    """DEC-000's gate. Neither of the two easy answers: not a refusal, not a confident number."""
    assert not proposal.refused, "a merely messy file must not be refused"
    canonical, ledger = intake.apply(messy, proposal)
    sites = list(canonical["site_id"])

    prov = intake.provenance_rows(proposal, sites, "reviewer", "Neighbouring County", "2026-07-28")
    scored = confidence.build_confidence(prov, sites)
    assert (scored["data_confidence_level_v3"] == "Low").all(), (
        "an unreviewed guessed mapping must not produce anything above Low")
    assert len(ledger) >= len(proposal.mapping), "not every field's handling was recorded"


def test_guessed_data_never_outranks_the_real_study():
    """The failure that makes all of this pointless if it happens.

    Measured once: accepting the mapping upgraded `unconfirmed` to `public_web_reference` and
    the messy fixture scored 58.5 (Medium) while the real Northern Virginia study - whose
    electrical fields are genuinely unverified - scored 33.8 (Low). Guessed data outranked
    measured data. Acceptance now confirms the MAPPING only.
    """
    real_prov = pd.read_csv(REPO / "data/provenance/field_provenance_v1.csv")
    real_sites = sorted(real_prov["site_id"].unique())
    real_score = confidence.build_confidence(real_prov, real_sites)["data_confidence_score_v3"].max()

    messy = pd.read_csv(FIXTURE)
    proposal = intake.propose(messy)
    canonical, _ = intake.apply(messy, proposal)
    sites = list(canonical["site_id"])
    accepted = intake.accept(
        intake.provenance_rows(proposal, sites, "r", "Neighbouring County", "2026-07-28"))
    intake_score = confidence.build_confidence(accepted, sites)["data_confidence_score_v3"].max()

    assert intake_score < real_score, (
        f"a guessed third-party mapping scored {intake_score} against the real study's "
        f"{real_score}; intake is making data look better than it is")


def test_accepting_a_mapping_does_not_improve_the_source_class(proposal):
    """Accepting confirms that `staff` means `employees_day`. It says nothing about whether the
    staff count is accurate, and must not pretend otherwise."""
    prov = intake.provenance_rows(proposal, ["S1"], "r", "org", "2026-07-28")
    accepted = intake.accept(prov)
    assert list(accepted["source_class"]) == list(prov["source_class"])
    assert (accepted["verification_status"] == "reviewed").all()


def test_accepting_still_leaves_a_missing_field_unresolved(proposal):
    prov = intake.provenance_rows(proposal, ["S1"], "r", "org", "2026-07-28")
    accepted = intake.accept(prov)
    for _, row in accepted.iterrows():
        if row["source_class"] == "missing":
            assert row["unresolved_flag"] == "1", "review cannot resolve an absent field"


# ---------------------------------------------------------------- traceability

def test_every_ledger_entry_carries_a_reason(messy, proposal):
    _canonical, ledger = intake.apply(messy, proposal)
    for entry in ledger:
        assert entry.reason.strip(), f"{entry.canonical_field} was transformed with no reason"


def test_every_canonical_field_is_grouped_for_confidence():
    """An ungrouped field defaults into some group and silently changes its score. This bit:
    relying on the contract's column map put 29 of 32 fields into one group by default."""
    for field in intake._all_fields():
        assert field in intake.FIELD_GROUP_FOR_INPUT, f"{field} has no confidence group"
