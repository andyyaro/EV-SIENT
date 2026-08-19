"""The rollback snapshot must record the state you would roll back TO.

`docs/operations/v4-program/cloudfront-config-before-platform.json` exists so the CloudFront
change that put the platform behind a Cognito gate can be undone. `deploy_platform.py`
overwrote it with the CURRENT config on every run, including dry runs - so the first run after
the change replaced the pre-change state with the post-change state, and six commits carried a
file that named itself `before-platform` while containing the `platform-gated` origin and the
`/platform*` cache behaviour. Restoring from it would have restored the change it exists to
undo.

Nothing objected because every check in the repository asked whether the file was present,
well-formed and free of account digits. All three were true the whole time. What no check asked
was whether its CONTENT still matched its NAME.

The pre-change state was recovered from `93c651d`, the only revision that still held it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "docs/operations/v4-program"
BEFORE = OPS / "cloudfront-config-before-platform.json"
OBSERVED = OPS / "cloudfront-config-observed.json"
DEPLOY = REPO / "scripts/deploy_platform.py"


def config_of(path: Path) -> dict:
    payload = json.loads(path.read_text())
    return payload.get("DistributionConfig", payload)


@pytest.mark.skipif(not BEFORE.is_file(), reason="rollback snapshot absent")
def test_the_before_snapshot_predates_the_platform():
    cfg = config_of(BEFORE)
    origins = [o["Id"] for o in cfg.get("Origins", {}).get("Items", [])]
    assert not any("platform" in o.lower() for o in origins), (
        f"the file named 'before-platform' contains a platform origin {origins} - it is a "
        f"snapshot of the state AFTER the change, so rolling back to it would reapply the "
        f"change rather than undo it")

    behaviours = cfg.get("CacheBehaviors", {})
    patterns = [b.get("PathPattern") for b in behaviours.get("Items", [])]
    assert behaviours.get("Quantity", 0) == 0 and not patterns, (
        f"the pre-platform snapshot carries cache behaviours {patterns}; before the platform "
        f"existed the distribution had none")


@pytest.mark.skipif(not BEFORE.is_file(), reason="rollback snapshot absent")
def test_the_snapshot_carries_no_account_digits():
    """Unchanged obligation, restated here because this file is written by a deploy script and
    a twelve-digit account id in a tracked file is the one thing the standing rules forbid
    outright."""
    raw = BEFORE.read_text()
    assert not re.search(r"\b\d{12}\b", raw), "a 12-digit account id is in the tracked snapshot"
    assert "<ACCOUNT>" in raw, "the redaction placeholder is missing; was this file redacted?"


@pytest.mark.skipif(not DEPLOY.is_file(), reason="deploy script absent")
def test_the_deploy_script_never_overwrites_the_rollback_snapshot():
    """A rollback target that the deploy rewrites is not a rollback target.

    Asserted against the source because the alternative is running a deploy, and a check that
    can only be performed by doing the thing it guards is not a check.
    """
    source = DEPLOY.read_text()
    assert "cloudfront-config-before-platform.json" in source

    # The write must be conditional on the file not already existing.
    guarded = re.search(
        r"before\s*=\s*REPO\s*/\s*\"docs/operations/v4-program/"
        r"cloudfront-config-before-platform\.json\"(.{0,600})", source, re.S)
    assert guarded, "the rollback snapshot path is no longer bound to a `before` variable"
    block = guarded.group(1)
    assert re.search(r"if\s+before\.is_file\(\)", block), (
        "the deploy script writes the rollback snapshot unconditionally; it must skip the "
        "write when the snapshot already exists, or it destroys the state it records")


@pytest.mark.skipif(not DEPLOY.is_file(), reason="deploy script absent")
def test_the_script_does_not_call_the_current_config_the_original():
    """The log line said "original config saved" while saving the current one. Wording is not
    cosmetic here: it is what a person reads while deciding whether the rollback path is
    intact."""
    source = DEPLOY.read_text()
    for line in source.splitlines():
        if "say(" in line and "original config" in line:
            pytest.fail(f"the script still calls the saved config the original: {line.strip()}")


@pytest.mark.skipif(not OBSERVED.is_file(), reason="no observed-state snapshot recorded yet")
def test_the_observed_snapshot_is_a_different_file_from_the_rollback_one():
    assert OBSERVED != BEFORE
    raw = OBSERVED.read_text()
    assert not re.search(r"\b\d{12}\b", raw), "the observed snapshot carries an account id"
