"""Missing data must never make a site look better than measured data.

Three places where it could. All three were found while designing Phase 6B - which exists
precisely to let a jurisdiction bring incomplete data - and reproduced by execution before
being written down. Until 2026-10-17 two of them were pinned here as KNOWN DEFECTS, deferred
to a decision about what absence should mean. DEC-011 now records that decision, and these
tests pin the fix instead:

**A value nobody recorded earns no credit, in either direction.** An absent yes/no is NaN,
not "no"; an inverted term (`1 - x`) with an absent `x` contributes 0, not its maximum; a lot
nobody counted gets the smallest capacity cap; and text that is neither a value nor a
recognisable blank is refused rather than guessed at.

**None of it changes a published number.** All 12 real sites carry strictly `0`/`1` in every
yes/no flag, a value in every numeric field and a positive `parking_spaces`, so every path
below is dormant on the current inputs - which `test_all_twelve_real_sites_are_complete` checks.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import right_sizing, scoring  # noqa: E402
from fcf_m2.config import MODE_LEGACY, MODE_V3  # noqa: E402


# ------------------------------------------------------- fixed: unclamped numeric flags

@pytest.mark.parametrize("value,expected", [
    (0, 0.0), (1, 1.0), (0.0, 0.0), (1.0, 1.0),
    (True, 1.0), (False, 0.0),
    ("1", 1.0), ("yes", 1.0), ("Y", 1.0), ("true", 1.0), ("T", 1.0), (" Yes ", 1.0),
    ("0", 0.0), ("no", 0.0), ("N", 0.0), ("false", 0.0), ("F", 0.0), ("1.0", 1.0), ("0.0", 0.0),
])
def test_valid_flag_values_are_unchanged(value, expected):
    assert scoring.yesno_to_num(value) == expected


@pytest.mark.parametrize("value", [float("nan"), None, "", "  ", "N/A", "na", "unknown", "-", "TBD"])
def test_a_blank_flag_is_absent_not_no(value):
    """It used to return 0.0 - "no" - which for the two inverted flags was the BEST answer."""
    assert math.isnan(scoring.yesno_to_num(value))


@pytest.mark.parametrize("value", ["banana", "partial", "maybe", "0.5", "2", "yes-ish"])
def test_a_flag_that_is_no_recognisable_answer_is_refused(value):
    """It used to become 0.0 silently, so a typo answered "no" for whoever wrote it."""
    with pytest.raises(scoring.FlagValueError, match="garage_enclosed"):
        scoring.yesno_to_num(value, "garage_enclosed")


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
    happened to parse as text or as a number silently changed the score. Both are refused."""
    for value in ("0.5", 0.5):
        with pytest.raises(scoring.FlagValueError):
            scoring.yesno_to_num(value)


def test_real_inputs_are_unaffected_so_no_published_number_moves():
    sites = pd.read_csv(REPO / "data/inputs/real_sites_v2.csv")
    for field in scoring.YES_NO_FIELDS:
        values = sites[field].dropna().unique()
        offenders = [v for v in values
                     if isinstance(v, (int, float)) and float(v) not in (0.0, 1.0)]
        assert offenders == [], f"{field} carries {offenders}; the refusal would now fire"


# ------------------------------------- fixed 2026-10-17: absence no longer beats measurement

SYNTHETIC = REPO / "data/synthetic/synthetic_sites_v2.csv"
SCORED_FIELDS = sorted(set(scoring.YES_NO_FIELDS) | set(scoring.NUMERIC_FIELDS))


def test_absent_parking_gets_the_smallest_cap_not_the_most_permissive():
    """`site_capacity_cap` returned **6** for an uncounted lot and **2** for a real 40-space
    one, so a site nobody counted was allowed three times the ports of one somebody did."""
    absent = right_sizing.site_capacity_cap(pd.Series({}))
    blank = right_sizing.site_capacity_cap(pd.Series({"parking_spaces": float("nan")}))
    zero = right_sizing.site_capacity_cap(pd.Series({"parking_spaces": 0}))
    measured_small = right_sizing.site_capacity_cap(pd.Series({"parking_spaces": 40}))
    assert absent == blank == zero == measured_small == 2


@pytest.mark.parametrize("field", ["garage_enclosed", "stormwater_risk"])
def test_an_absent_inverted_flag_earns_no_safety_credit(field):
    """Both score as `(1 - x)`. An absent value used to become 0.0, and `1 - 0 = 1.0` - the
    maximum: a site with no stormwater assessment scored as though one had found no risk."""
    sites = pd.read_csv(SYNTHETIC)
    sites[field] = 0
    recorded_good = scoring.enrich_and_score(sites)["safety_subscore"]
    sites[field] = float("nan")
    absent = scoring.enrich_and_score(sites)
    sites[field] = 1
    recorded_bad = scoring.enrich_and_score(sites)["safety_subscore"]
    assert (absent["safety_subscore"].to_numpy() == recorded_bad.to_numpy()).all()
    assert (absent["safety_subscore"].to_numpy() < recorded_good.to_numpy()).all()
    assert (absent["absent_fields"].str.contains(field)).all()


@pytest.mark.parametrize("mode", [MODE_LEGACY, MODE_V3])
@pytest.mark.parametrize("field", SCORED_FIELDS)
def test_blanking_any_recorded_value_never_raises_that_sites_score(field, mode):
    """The rule itself, for every field and every site: replacing a recorded value with a
    blank may lower a site's score or leave it alone, never raise it."""
    sites = pd.read_csv(SYNTHETIC)
    anchors = scoring.load_anchor_set(REPO / "data/anchors/anchor_set_v1.json") if mode == MODE_V3 else None
    before = scoring.enrich_and_score(sites, mode, anchors).set_index("site_id")["readiness_score"]
    for i in range(len(sites)):
        blanked = sites.copy()
        blanked[field] = blanked[field].astype(object)
        blanked.loc[i, field] = None
        after = scoring.enrich_and_score(blanked, mode, anchors).set_index("site_id")["readiness_score"]
        site = sites.loc[i, "site_id"]
        assert after[site] <= before[site] + 1e-9, f"blank {field} raised {site}"


def test_an_absent_value_does_not_move_the_other_sites():
    """In the cohort-relative legacy scaling an absent value used to enter the range as 0,
    stretching the minimum and so changing every OTHER site's normalised value."""
    sites = pd.read_csv(SYNTHETIC)
    column = sites["distance_to_service_ft"]
    # A site holding neither end of the range, so blanking it must leave the range alone.
    i = next(k for k in range(len(sites)) if column.min() < column[k] < column.max())
    before = scoring.enrich_and_score(sites).set_index("site_id")["distance_to_service_ft_n"]
    blanked = sites.copy()
    blanked["distance_to_service_ft"] = blanked["distance_to_service_ft"].astype(object)
    blanked.loc[i, "distance_to_service_ft"] = "n/a"
    after = scoring.enrich_and_score(blanked).set_index("site_id")["distance_to_service_ft_n"]
    site = sites.loc[i, "site_id"]
    others = [s for s in before.index if s != site]
    assert (after[others] - before[others]).abs().max() < 1e-12
    assert math.isnan(after[site])


def test_unrecorded_access_and_enclosure_cannot_lift_a_tier():
    row = pd.Series({"public_access": float("nan"), "garage_enclosed": 0.0,
                     "model_rank": 1, "readiness_score": 90.0})
    assert scoring.recommendation_tier(row) == "Low public-priority / special-use"
    row["public_access"], row["garage_enclosed"] = 1.0, float("nan")
    assert scoring.recommendation_tier(row) == "High-review candidate"
    assert right_sizing.build_strategy(pd.Series({"public_access": float("nan")}), 4)[0] == \
        "do_not_advance_general_public_buildout"


def test_a_number_written_as_text_is_refused_not_zeroed():
    """`pd.to_numeric(errors="coerce")` made "1,400" visitors, "n/a" staff and a typo all 0."""
    sites = pd.read_csv(SYNTHETIC)
    sites["visitors_day"] = sites["visitors_day"].astype(object)
    sites.loc[3, "visitors_day"] = "1,400"
    with pytest.raises(scoring.FieldValueError, match=r"visitors_day.*row\(s\) \[5\]"):
        scoring.enrich_and_score(sites)
    sites.loc[3, "visitors_day"] = "n/a"
    scored = scoring.enrich_and_score(sites)
    assert "visitors_day" in scored.loc[scored["site_id"] == sites.loc[3, "site_id"], "absent_fields"].iloc[0]


def test_all_twelve_real_sites_are_complete_so_no_published_number_moves():
    """Why the fix could ship without a re-baseline: none of these paths is live on the real
    inputs, and the run's own `absent_fields` column says so."""
    sites = pd.read_csv(REPO / "data/inputs/real_sites_v2.csv")
    assert len(sites) == 12
    for field in SCORED_FIELDS:
        assert sites[field].notna().all(), f"{field} has a gap; absence handling is now live"
    parking = pd.to_numeric(sites["parking_spaces"], errors="coerce")
    assert (parking > 0).all(), "a site lost its parking count"
    assert (scoring.enrich_and_score(sites)["absent_fields"] == "").all()
