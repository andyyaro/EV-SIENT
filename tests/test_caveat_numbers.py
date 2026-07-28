"""Every number written into a caveat must still be true of the contract.

Why this exists
---------------
`CAVEAT_TEXT["wait_simulated"]` was revised **four times in one session**. Each revision fixed
a real error and introduced a smaller one:

1. "The p50 and p90 are 0.0 at every site" — true of a *different statistic* in a *different
   table* at *one horizon*, while attached to columns reaching 215.35.
2. "it is not nil" — false on the 8 rows where the wait is exactly 0.00.
3. "it ... reaches 215 minutes ... blank on 5 rows" — true of `peak_wait_minutes`, false of
   `average_wait_minutes`, which tops out at 68.72 with no blanks.
4. "69 minutes and 215 ... both at PWC002" — the average maximum is at PWC008; and "0.00 from
   2036 onward" missed two non-zero rows.

The pattern is the point. A sentence carrying four numbers, about two columns, across four
horizons, cannot be reliably checked by reading it. Prose drifts silently; a test does not.

So the numbers in the caveat are asserted against the contract here. If the data changes or
someone edits the sentence, this fails and names the clause. It does not check the *wording* —
that is a human judgement — only that every quantity the sentence asserts is still true.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import provenance  # noqa: E402

CONTRACT = REPO / "data/contract/v1/scenario_table.csv"
DES_TABLE = REPO / "dashboard/tableau/patch_package/tbl_peak_waits.csv"

pytestmark = pytest.mark.skipif(not CONTRACT.is_file(), reason="contract absent")


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    return pd.read_csv(CONTRACT)


@pytest.fixture(scope="module")
def caveat() -> str:
    return provenance.CAVEAT_TEXT["wait_simulated"]


# ------------------------------------------------------- the quantities the sentence asserts

def test_the_quietest_site_never_exceeds_the_stated_ceiling(scenarios, caveat):
    """The caveat states a hard ceiling for the near-nil site. It must be a real bound."""
    stated = float(re.search(r"never exceeds ([\d.]+) minutes", caveat).group(1))
    per_site = scenarios.groupby("site_id")[["average_wait_minutes", "peak_wait_minutes"]].max()
    quietest = per_site.max(axis=1).idxmin()
    observed = per_site.loc[quietest].max()
    assert observed <= stated, (
        f"{quietest} reaches {observed}, above the {stated} the caveat promises as a ceiling")


def test_zero_is_the_most_common_value_at_that_site(scenarios, caveat):
    """'0.00 on most of them' is a majority claim, so a majority is what is checked."""
    assert "0.00 on most of them" in caveat
    per_site = scenarios.groupby("site_id")[["average_wait_minutes", "peak_wait_minutes"]].max()
    quietest = per_site.max(axis=1).idxmin()
    rows = scenarios[scenarios.site_id == quietest]
    zeros = int(((rows.average_wait_minutes == 0) & (rows.peak_wait_minutes == 0)).sum())
    assert zeros > len(rows) / 2, f"only {zeros} of {len(rows)} rows are 0.00 at {quietest}"


def test_the_stated_average_and_peak_maxima_match_the_contract(scenarios, caveat):
    stated_avg = float(re.search(r"AVERAGE wait reaches about (\d+)", caveat).group(1))
    stated_peak = float(re.search(r"PEAK about (\d+)", caveat).group(1))
    assert round(scenarios.average_wait_minutes.max()) == stated_avg
    assert round(scenarios.peak_wait_minutes.max()) == stated_peak


def test_the_two_maxima_really_are_at_different_sites(scenarios, caveat):
    """This clause was added because a draft asserted both maxima were at the same site."""
    assert "DIFFERENT sites" in caveat
    avg_site = scenarios.loc[scenarios.average_wait_minutes.idxmax(), "site_id"]
    peak_site = scenarios.loc[scenarios.peak_wait_minutes.idxmax(), "site_id"]
    assert avg_site != peak_site, (
        f"both maxima are at {avg_site}; the caveat says they are at different sites")


def test_the_blank_row_count_is_exact(scenarios, caveat):
    stated = int(re.search(r"BLANK on (\d+)", caveat).group(1))
    assert int(scenarios.peak_wait_minutes.isna().sum()) == stated


def test_only_the_peak_column_is_ever_blank(caveat, scenarios):
    """The caveat says the PEAK column is 'additionally' blank, which claims the average is
    not. That distinction is the whole reason revision 3 was wrong."""
    assert "peak column is additionally BLANK" in caveat
    assert int(scenarios.average_wait_minutes.isna().sum()) == 0, (
        "average_wait_minutes has blanks, so 'additionally' misattributes them to the peak")


# ------------------------------------------------------- the other table it distinguishes

@pytest.mark.skipif(not DES_TABLE.is_file(), reason="discrete-event table absent")
def test_the_discrete_event_zeros_it_contrasts_with_are_real():
    """The caveat's closing clause exists to stop a reader confusing these two statistics.
    If the discrete-event zeros ever stop being zero, the contrast stops being true."""
    des = pd.read_csv(DES_TABLE)
    assert (des.p50_wait_min == 0).all(), "p50 is no longer 0.0 at every site"
    assert (des.p90_wait_min == 0).all(), "p90 is no longer 0.0 at every site"
    assert len(des) == 12


# ------------------------------------------------------- the capacity caveat, same treatment

def test_the_capacity_caveat_still_matches_every_contract_row(scenarios):
    """'PLACEHOLDER at all 12 sites' is the load-bearing sentence of the whole project."""
    text = provenance.CAVEAT_TEXT["capacity_placeholder"]
    stated = int(re.search(r"all (\d+) sites", text).group(1))
    assert scenarios.site_id.nunique() == stated
    assert set(scenarios.capacity_basis) == {"placeholder"}, (
        "the caveat claims placeholder everywhere; the contract disagrees")
