"""The packaging workflow's constraints are billing and honesty constraints, so they are pinned.

Why a test rather than a comment
--------------------------------
Two of these fail *silently and expensively*. A `branches:` trigger added during a debugging
session would build Windows artifacts on every push, and Windows runners bill at **2x** against
a 2 000 minute monthly allowance on a private repository. Nobody notices until the allowance is
gone. The precedent is recent: a hung test suite consumed 106 runner-minutes in one afternoon
before it was spotted.

The third is an honesty constraint. There is no Apple Developer account, so nothing this
project ships is notarized, and a workflow that implied otherwise would be making a security
claim it cannot support.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/package.yml"

pytestmark = pytest.mark.skipif(not WORKFLOW.is_file(), reason="packaging workflow absent")


@pytest.fixture(scope="module")
def text() -> str:
    return WORKFLOW.read_text()


def test_it_triggers_on_tags_only(text):
    """The expensive one. Windows runners bill at 2x on a private repo."""
    assert re.search(r"push:\s*\n\s*tags:", text), "the push trigger must be tag-scoped"
    trigger_block = text.split("jobs:")[0]
    assert "branches:" not in trigger_block, (
        "a branch trigger would build Windows artifacts on every push, at 2x billing")


def test_it_is_never_scheduled(text):
    """A nightly build spends the allowance while everyone is asleep."""
    assert "schedule:" not in text.split("jobs:")[0]


def test_every_job_bounds_its_runtime(text):
    """Nothing bounded the damage when a hung suite ran for an hour. Both jobs are capped."""
    assert text.count("timeout-minutes:") >= text.count("runs-on:"), (
        "every job needs a timeout; an unbounded job can burn the whole allowance")


def test_it_never_claims_notarization(text):
    """There is no Apple Developer account. Claiming notarization would be a security claim
    this project cannot support, and the one thing the requirement names explicitly."""
    lowered = text.lower()
    if "notariz" in lowered:
        for line in text.splitlines():
            if "notariz" in line.lower():
                assert re.search(r"\b(not|no|never|nothing)\b", line, re.I), (
                    f"a line mentions notarization without negating it: {line.strip()}")


def test_the_artifact_build_is_the_public_one(text):
    """--public is what swaps in the synthetic inputs and inspects the finished archive. A
    packaging workflow that built the internal artifact would ship the real site data."""
    assert "--public" in text, "the packaged artifact must be built with --public"


def test_it_verifies_the_built_package_for_credentials(text):
    """Verified by inspecting the built package, never by assuming — the requirement's own
    wording, and the lesson from an artifact whose inputs were correctly substituted and which
    still carried 36 real facility identifiers."""
    assert "AKIA" in text, "the credential scan must run against the built archive"
    assert "zipfile" in text, "the scan must open the archive rather than check the source tree"


def test_the_release_notes_state_the_data_is_synthetic(text):
    """Someone downloading reads the release page, not DECISIONS.md."""
    body = text.split("body:")[-1] if "body:" in text else ""
    assert "SYNTHETIC" in body.upper(), "the release body must say the data is synthetic"
    lowered = body.lower()
    assert ("notarized" in lowered or "signing certificate" in lowered), (
        "the release body must state the signing limitation")
    # And must state it as an ABSENCE. Matching the word alone would pass a body that claimed
    # the artifacts WERE notarized.
    assert re.search(r"(neither|not|no)\b[^.]{0,80}(notariz|sign)", lowered), (
        "the signing limitation must be stated as an absence, not merely mentioned")


def test_the_install_guide_never_advises_disabling_gatekeeper():
    """Explicitly forbidden: that advice makes every future download less safe to open one
    file, and it is not necessary."""
    guide = REPO / "docs/INSTALL.md"
    if not guide.is_file():
        pytest.skip("install guide absent")
    lowered = guide.read_text().lower()
    lines = guide.read_text().splitlines()
    for forbidden in ["spctl --master-disable", "master-disable", "disable gatekeeper system"]:
        for index, line in enumerate(lines):
            if forbidden not in line.lower():
                continue
            # The negation may wrap onto an adjacent line — English sentences do not respect
            # line breaks, and checking one line at a time is the same match-the-text-where-
            # meaning-was-intended mistake this project keeps hitting. Read a window.
            window = " ".join(lines[max(0, index - 2):index + 3]).lower()
            assert re.search(r"\b(not|never|do not|don't|would make|less safe|unnecessary)\b",
                             window), (
                f"the guide appears to recommend {forbidden!r}: {line.strip()}")
