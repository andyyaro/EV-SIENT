"""Missing data must never make a site look better than measured data.

Three places where it currently can. All three were found while designing Phase 6B - which
exists precisely to let a jurisdiction bring incomplete data - and all three were reproduced
by execution before being written down.

**None of them changes a published number today.** All 12 real sites carry strictly `0`/`1`
in every yes/no flag and a positive `parking_spaces`, so every path below is dormant on the
current inputs. They go live the moment intake accepts a file nobody here prepared, which is
the whole point of Phase 6B.

Two of the three are **deliberately not fixed yet** and are pinned here as *known* behaviour
rather than desired behaviour. A test that asserts a defect is not an endorsement of it; it
is how the defect stays visible until the decision that resolves it is made by someone
entitled to make it. See DEC-011.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import right_sizing, scoring  # noqa: E402


# ------------------------------------------------------- fixed: unclamped numeric flags

@pytest.mark.parametrize("value,expected", [
    (0, 0.0), (1, 1.0), (0.0, 0.0), (1.0, 1.0),
    (True, 1.0), (False, 0.0),
    ("1", 1.0), ("yes", 1.0), ("Y", 1.0), ("true", 1.0), ("T", 1.0),
    ("0", 0.0), ("no", 0.0), ("banana", 0.0), ("", 0.0),
    (float("nan"), 0.0),
])
def test_valid_flag_values_are_unchanged(value, expected):
    assert scoring.yesno_to_num(value) == expected


@pytest.mark.parametrize("value", [0.5, 7, -3, 2, 100, -0.0001, 1.5])
def test_a_flag_outside_zero_or_one_is_refused_not_clamped(value):
    """It used to `return float(value)` for any number, unclamped.

    A `7` on `fire_access_ok` contributed seven times the weight the rubric allocates to
    fire access. Clamping to 1 would be a cleaner that silently improves the data and hides
    whatever produced a 7, so it refuses instead.
    """
    with pytest.raises(scoring.FlagValueError, match="not a yes/no value"):
        scoring.yesno_to_num(value, "fire_access_ok")


def test_the_refusal_names_the_field():
    with pytest.raises(scoring.FlagValueError, match="stormwater_risk"):
        scoring.yesno_to_num(4, "stormwater_risk")


def test_the_same_value_no_longer_answers_differently_by_type():
    """`0.5` returned 0.5 while the string `"0.5"` returned 0.0, so whether a CSV cell
    happened to parse as text or as a number silently changed the score."""
    assert scoring.yesno_to_num("0.5") == 0.0
    with pytest.raises(scoring.FlagValueError):
        scoring.yesno_to_num(0.5)


def test_real_inputs_are_unaffected_so_no_published_number_moves():
    sites = pd.read_csv(REPO / "data/inputs/real_sites_v2.csv")
    for field in scoring.YES_NO_FIELDS:
        values = sites[field].dropna().unique()
        offenders = [v for v in values
                     if isinstance(v, (int, float)) and float(v) not in (0.0, 1.0)]
        assert offenders == [], f"{field} carries {offenders}; the refusal would now fire"


# --------------------------------------------- NOT fixed: absence beats measurement

def test_KNOWN_DEFECT_absent_parking_is_more_permissive_than_a_real_lot():
    """`site_capacity_cap` returns **6** when `parking_spaces <= 0`, and **2** for a real
    40-space lot. A site nobody counted is allowed three times the ports of one somebody did.

    Pinned, not fixed. The correct neutral is a design decision with a visible consequence -
    the conservative choice (cap 2 on absence) would lower port targets for any jurisdiction
    that omits the column, and that trade belongs to the project owner, not to this test.
    Phase 6B is where absence handling is decided; DEC-011 records it as open.
    """
    absent = right_sizing.site_capacity_cap(pd.Series({}))
    zero = right_sizing.site_capacity_cap(pd.Series({"parking_spaces": 0}))
    measured_small = right_sizing.site_capacity_cap(pd.Series({"parking_spaces": 40}))

    assert absent == 6 and zero == 6
    assert measured_small == 2
    assert absent > measured_small, (
        "If this now fails, absence stopped being more permissive than measurement -- "
        "which is the fix. Update DEC-011 and delete this test rather than adjusting it.")


@pytest.mark.parametrize("field", ["garage_enclosed", "stormwater_risk"])
def test_KNOWN_DEFECT_absent_inverted_flags_score_as_the_best_possible_case(field):
    """Both are in `INVERTED_DRIVERS`, so the formula uses `(1 - x)`. An absent value becomes
    `0.0`, and `1 - 0 = 1.0` - the maximum contribution.

    In plain terms: a site with no stormwater assessment scores as though an assessment had
    been done and found no risk. That is an affirmative safety claim manufactured from no
    data, and it is exactly the shape of thing the capacity guard exists to refuse one layer
    down.

    Pinned, not fixed, for the same reason as above: the pessimistic neutral (`1`) asserts
    the opposite unverified claim, and for `garage_enclosed` it also changes a user-visible
    review tier. DEC-011.
    """
    assert field in scoring.INVERTED_DRIVERS
    absent_term = 1 - scoring.yesno_to_num(float("nan"), field)
    measured_bad = 1 - scoring.yesno_to_num(1, field)
    measured_good = 1 - scoring.yesno_to_num(0, field)

    assert absent_term == 1.0 == measured_good
    assert measured_bad == 0.0
    assert absent_term > measured_bad, (
        "If this now fails, absence stopped scoring as the best case -- which is the fix. "
        "Update DEC-011 and delete this test rather than adjusting it.")


def test_all_twelve_real_sites_have_complete_flags_so_the_two_defects_are_dormant():
    """The reason neither is being fixed under time pressure: neither is live."""
    sites = pd.read_csv(REPO / "data/inputs/real_sites_v2.csv")
    assert len(sites) == 12
    for field in scoring.YES_NO_FIELDS:
        assert sites[field].notna().all(), f"{field} has a gap; the dormant defect is awake"
    parking = pd.to_numeric(sites["parking_spaces"], errors="coerce")
    assert (parking > 0).all(), "a site lost its parking count; the cap defect is awake"
