"""The superseded-notice cover must keep telling the truth about the model it corrects.

A cover page that corrects a stale ranking is itself a set of claims - FFX002 at 58.8 under
one mode, FFX004 at 53.4 under another, capacity unverified everywhere. Those are exactly the
kind of hand-written figures that went stale in the document it is stamped onto. If the model
is ever re-baselined, an unchecked cover becomes a second wrong artifact sitting on top of the
first.

So every number on the cover is asserted against the canonical fixtures here. The tests read
`LINES` from the script rather than parsing the PDF, so they run anywhere - CI has neither
`qpdf` nor `mutool`, and stamping is deliberately a manual step.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import stamp_report_cover as cover  # noqa: E402

LEGACY = REPO / "tests/fixture_legacy_v2_site_results.csv"
CANONICAL = REPO / "tests/fixture_milestone2_v3_site_results.csv"
CONTRACT = REPO / "data/contract/v1/scenario_table.csv"

pytestmark = pytest.mark.skipif(not CANONICAL.is_file(), reason="fixtures absent")


@pytest.fixture(scope="module")
def text() -> str:
    return " ".join(line for line, *_ in cover.LINES)


def top_of(path: Path):
    frame = pd.read_csv(path).sort_values("model_rank")
    return frame.iloc[0], frame.iloc[1]


def test_the_legacy_figure_it_corrects_is_the_legacy_figure(text):
    """'lists FFX002 ... first at 58.8' must still be what legacy_v2 produces."""
    first, _ = top_of(LEGACY)
    assert first["site_id"] == "FFX002"
    assert f"{first['readiness_score']}" in text
    assert "58.8" in text


def test_the_canonical_replacement_is_correct(text):
    """The cover names the canonical winner, its score, and the runner-up's score."""
    first, second = top_of(CANONICAL)
    assert first["site_id"] == "FFX004", "the canonical top site changed"
    assert f"{first['readiness_score']}" in text, "the cover's canonical score is stale"
    assert second["site_id"] == "FFX002"
    assert f"{second['readiness_score']}" in text, "the cover's runner-up score is stale"


def test_the_two_modes_are_both_named(text):
    assert "legacy_v2" in text
    assert "milestone2_v3" in text


def test_the_capacity_claim_still_holds(text):
    scenarios = pd.read_csv(CONTRACT)
    assert "placeholder at all twelve sites" in text
    assert set(scenarios["capacity_basis"]) == {"placeholder"}
    assert scenarios["site_id"].nunique() == 12


def test_the_confidence_claim_still_holds(text):
    scenarios = pd.read_csv(CONTRACT)
    assert "none reaches Medium" in text
    assert set(scenarios["data_confidence"]) == {"Low"}


def test_it_refuses_to_claim_the_report_is_current(text):
    """The whole point of the cover. It may not soften into 'may be out of date'."""
    assert "SUPERSEDED" in text
    assert "not current model output" in text


def test_it_does_not_claim_a_feasibility_finding(text):
    assert "Neither ranking is a feasibility finding" in text


# ------------------------------------------------------------------ the artifact itself

REPORT = REPO / "site/www/reports/Public_EV_Charging_Planning_Report.pdf"


@pytest.mark.skipif(not REPORT.is_file(), reason="report absent")
def test_the_published_report_is_actually_stamped():
    """A stamp that exists only in the script and never reached the file is the exact failure
    this whole exercise is about.

    Checked by page count rather than by scanning for the cover's words. The first version of
    this test scanned the bytes for the sentinel and failed against a correctly-stamped file:
    qpdf compresses content streams, so the text is not plaintext anywhere in the PDF. The
    script's own fallback had the same bug and was fixed with it.
    """
    assert cover.page_count(REPORT) == cover.ORIGINAL_PAGES + 1, (
        f"expected {cover.ORIGINAL_PAGES + 1} pages (1 cover + {cover.ORIGINAL_PAGES} "
        f"original), found {cover.page_count(REPORT)}; run scripts/stamp_report_cover.py")


@pytest.mark.skipif(not REPORT.is_file(), reason="report absent")
def test_the_cover_was_not_applied_twice():
    """Two covers would mean the guard in the script stopped working."""
    assert cover.page_count(REPORT) <= cover.ORIGINAL_PAGES + 1, "more than one cover page"
