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


def test_a_signing_step_must_survive_the_archiving_step(text):
    """A signing step that the next step undoes is worse than no signing step.

    The workflow ad-hoc signed `run-platform.command` and then archived it with `zip`. Ad-hoc
    signing a shell script writes the signature to extended attributes rather than into the
    file, and `zip` discards extended attributes — so the step destroyed its own output one
    line later and every build produced an unsigned artifact while the workflow read as though
    it did not. Measured by running these steps by hand on macOS 26.5.1: the staging file
    carried `com.apple.cs.CodeDirectory`, `CodeRequirements` and `CodeSignature`; after
    zip+unzip it carried none and `codesign -dv` reported "code object is not signed at all".

    Nothing here forbids signing. It requires that a signing step be packaged in a way that
    keeps the signature — `ditto -c -k`, which preserves extended attributes — so the workflow
    cannot silently go back to claiming something it does not do.
    """
    # Comment lines are stripped first. The block explaining WHY there is no signing step
    # names `codesign` several times, and matching the word rather than the command is the
    # same text-versus-meaning error this repository keeps finding — including, on the first
    # run of this test, here.
    runnable = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    if not any("codesign" in line for line in runnable):
        return
    archiving = [line for line in runnable
                 if re.search(r"\b(zip|ditto)\b", line) and "unzip" not in line]
    assert any("ditto -c -k" in line for line in archiving), (
        "the workflow signs the run script and then archives with plain `zip`, which discards "
        "the extended attributes the signature lives in. Either archive with `ditto -c -k` or "
        "drop the signing step — do not ship a build that appears to sign and does not.")


#: Affirmative signing claims that were actually made in this repository and were false. Each
#: is pinned as a literal pattern rather than inferred, for the reason in the test below.
FALSE_SIGNING_CLAIMS = [
    r"artifact\s+\*{0,2}is\*{0,2}\s+ad-?hoc\s+signed",
    r"artifact\s+\*{0,2}is\*{0,2}\s+signed",
    r"ad-?hoc\s+signing\s+is\s+applied",
    r"artifacts?\s+are\s+signed",
]


def test_no_shipped_document_claims_the_artifact_is_signed(text):
    """The install guide said "The artifact *is* ad-hoc signed", and the workflow header said
    "Ad-hoc signing is applied where it costs nothing". Neither was true.

    **What this test does, precisely:** it forbids a short list of affirmative phrasings that
    were actually written here, and separately requires the guide to state the true position.
    It does **not** understand English, and two earlier attempts that tried to failed:

    * the first looked for a negation within a few lines, and passed the false sentence because
      an unrelated paragraph two lines away contained "used to";
    * the second scoped to the sentence, and passed it again because YAML comment lines join
      into one pseudo-sentence and the section heading "What is NOT claimed" supplied the word
      "NOT" from three lines above.

    A heuristic that keeps finding excuses is worse than a narrow check that cannot. This one is
    narrow on purpose, and its narrowness is stated so nobody reads a pass as "no document
    overclaims about signing" — it means "none of the four phrasings we got wrong before".
    """
    runnable = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    signs = any("codesign" in line for line in runnable) and "ditto -c -k" in text
    if signs:
        return

    # The workflow's own header is checked too. It kept saying "Ad-hoc signing is applied where
    # it costs nothing" for a commit after the signing step was deleted — a stale claim in the
    # file that defines the behaviour, which is the worst place for one.
    for name in ("docs/INSTALL.md", "README.md", "DEPLOYMENT.md",
                 ".github/workflows/package.yml"):
        doc = REPO / name
        if not doc.is_file():
            continue
        prose = " ".join(doc.read_text().splitlines())
        for pattern in FALSE_SIGNING_CLAIMS:
            found = re.search(pattern, prose, re.I)
            assert not found, (
                f"{name} asserts the artifact is signed ({found.group(0)!r}); the packaging "
                f"workflow has no signing step and produces an unsigned artifact")


def test_the_install_guide_states_that_nothing_is_signed(text):
    """The other half, and the one that cannot be satisfied by deleting a sentence: the guide
    has to say what is true, not merely avoid saying what is false."""
    runnable = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    if any("codesign" in line for line in runnable):
        return
    guide = REPO / "docs/INSTALL.md"
    if not guide.is_file():
        pytest.skip("install guide absent")
    prose = " ".join(guide.read_text().splitlines())
    assert re.search(r"(carries no signature|is not signed|nothing is signed|"
                     r"no signature at all)", prose, re.I), (
        "docs/INSTALL.md never states that the downloaded artifact is unsigned, which is the "
        "one thing a reader hitting Gatekeeper needs to know is expected")


def test_the_install_guide_states_the_measured_gatekeeper_outcome():
    """The number a reader needs is what actually happens, not what ought to. `spctl -a -t exec`
    exits 3 on this artifact — measured on both the signed staging file and the unsigned
    extracted one, which is why removing the signing step changed nothing for a recipient."""
    guide = REPO / "docs/INSTALL.md"
    if not guide.is_file():
        pytest.skip("install guide absent")
    body = guide.read_text()
    assert "spctl" in body, "the guide must name the command whose result it reports"
    assert re.search(r"\bexit(s|ed)?\b[^.\n]{0,30}\b3\b", body, re.I), (
        "the guide must state the measured exit status rather than describing the outcome "
        "loosely")


def test_the_release_body_only_points_at_files_a_downloader_can_open(text):
    """The Release page is read by someone who has the zip and nothing else.

    The body said *"See `docs/INSTALL.md` for the exact click-paths"*. `docs/` is excluded from
    the public bundle by DEC-016 and this repository is PRIVATE, so that sentence pointed at a
    file the reader had no way to open — at the exact moment they were staring at a Gatekeeper
    refusal and needed it. Every repo-relative path the body names must therefore be something
    the staging step actually puts in the archive.
    """
    if "body:" not in text:
        pytest.skip("the release job has no body")
    body = text.split("body:")[-1]
    staged = text  # the staging step's `cp` lines are in the same workflow file

    referenced = set(re.findall(r"`([A-Za-z0-9_./-]+\.(?:md|txt|json|csv|py|sh))`", body))
    unreachable = []
    for ref in sorted(referenced):
        leaf = ref.split("/")[-1]
        # Present if the staging step copies it, or if it is generated into the bundle.
        if re.search(rf"cp \.\./[A-Za-z0-9_./-]*{re.escape(leaf)}\b", staged):
            continue
        if leaf in ("LIMITATIONS.txt", "REPRODUCTION.txt", "RELEASE_MANIFEST.json"):
            continue  # written directly into the archive by build_release_artifact.py
        unreachable.append(ref)

    assert not unreachable, (
        f"the Release body sends a downloader to {unreachable}, which the artifact does not "
        f"contain and which they cannot reach in a private repository")


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
