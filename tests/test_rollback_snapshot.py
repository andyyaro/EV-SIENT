"""The CloudFront snapshots say what they are, and the deploy can no longer rebuild the gate.

`docs/operations/v4-program/cloudfront-config-before-platform.json` records the distribution
before the Cognito-gated `/platform*` path was added. `deploy_platform.py` once overwrote it with
the CURRENT config on every run, so six commits carried a file that named itself
`before-platform` while containing the `platform-gated` origin and the `/platform*` cache
behaviour. The pre-change state was recovered from `93c651d`, the only revision that still held
it. Nothing objected at the time because every check asked whether the file was present,
well-formed and free of account digits; none asked whether its CONTENT matched its NAME.

The gate was retired on 2026-10-18 (DEC-030). The deploy script now publishes the public site
alone: it writes no snapshot, sends no distribution config, and refuses a gate or platform mode.
These tests hold that, so nothing in the repository can quietly put the gate back.
"""

from __future__ import annotations

import importlib.util
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


def deploy_module():
    spec = importlib.util.spec_from_file_location("deploy_platform", DEPLOY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def code_lines(path: Path) -> list[str]:
    """Source lines that are not comments, so a history note cannot satisfy or fail a test."""
    return [line for line in path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")]


# ---------------------------------------------------------------- the snapshots

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
    """A twelve-digit account id in a tracked file is the one thing the standing rules forbid
    outright."""
    raw = BEFORE.read_text()
    assert not re.search(r"\b\d{12}\b", raw), "a 12-digit account id is in the tracked snapshot"
    assert "<ACCOUNT>" in raw, "the redaction placeholder is missing; was this file redacted?"


@pytest.mark.skipif(not OBSERVED.is_file(), reason="no observed-state snapshot recorded yet")
def test_the_observed_snapshot_is_a_different_file_from_the_rollback_one():
    assert OBSERVED != BEFORE
    raw = OBSERVED.read_text()
    assert not re.search(r"\b\d{12}\b", raw), "the observed snapshot carries an account id"


# ---------------------------------------------------------------- the deploy cannot rebuild the gate

def test_the_deploy_script_writes_no_snapshot_and_sends_no_distribution_config():
    """Asserted against the source because the alternative is running a deploy, and a check that
    can only be performed by doing the thing it guards is not a check."""
    code = "\n".join(code_lines(DEPLOY))
    for forbidden in ("update-distribution", "write_text(", "cloudfront-config-before-platform",
                      "cloudfront-config-observed"):
        assert forbidden not in code, f"the public-site deploy still does {forbidden!r}"


def test_the_deploy_script_creates_none_of_the_gate_resources():
    code = "\n".join(code_lines(DEPLOY))
    for call in ("create-bucket", "put-bucket-policy", "create-origin-access-control",
                 "create-function", "update-function-code", "publish-version", "create-role",
                 "create-managed-login-branding", "infra/edge-auth", "granted.mjs",
                 "LambdaFunctionAssociations\": {"):
        assert call not in code, f"the deploy script still references {call!r}"


def test_the_gate_source_is_gone_from_the_repository():
    for path in ("infra/edge-auth/index.mjs", "infra/edge-auth/granted.mjs.example",
                 "tests/edge_auth/edge_auth.test.mjs"):
        assert not (REPO / path).exists(), f"{path} is back; DEC-030 retired it"


@pytest.mark.parametrize("flag", ["--platform", "--gate", "--full", "--with-gate",
                                  "--platform-only", "--platform=yes"])
def test_every_gate_or_platform_mode_is_refused_before_anything_runs(flag, capsys, monkeypatch):
    deploy = deploy_module()

    def no_aws(*_args, **_kwargs):
        raise AssertionError("a refused mode reached AWS")

    monkeypatch.setattr(deploy, "aws", no_aws)
    monkeypatch.setattr(deploy.subprocess, "run", no_aws)
    assert deploy.main([flag, "--apply"]) == 2
    err = capsys.readouterr().err
    assert "DEC-030" in err and deploy.PLANNER_URL in err and "Nothing was changed" in err


def test_the_public_site_flags_are_not_refused():
    deploy = deploy_module()
    assert deploy.retired_mode_refusal([]) is None
    assert deploy.retired_mode_refusal(["--apply"]) is None
    assert deploy.retired_mode_refusal(["--www-only", "--apply"]) is None


def test_gate_leftovers_on_the_distribution_are_reported():
    deploy = deploy_module()
    clean = {
        "Origins": {"Quantity": 1, "Items": [{"Id": "main"}]},
        "CacheBehaviors": {"Quantity": 0},
        "DefaultCacheBehavior": {"TargetOriginId": "main",
                                 "LambdaFunctionAssociations": {"Quantity": 0}},
    }
    assert deploy.gate_leftovers(clean) == []
    gated = json.loads(json.dumps(clean))
    gated["Origins"]["Items"].append({"Id": "platform-gated"})
    gated["CacheBehaviors"] = {"Quantity": 1, "Items": [{"PathPattern": "/platform*"}]}
    gated["DefaultCacheBehavior"]["LambdaFunctionAssociations"] = {"Quantity": 1}
    found = deploy.gate_leftovers(gated)
    assert len(found) == 3
    assert any("/platform*" in f for f in found) and any("platform-gated" in f for f in found)
    assert any("DEFAULT" in f for f in found)


@pytest.mark.skipif(not BEFORE.is_file(), reason="rollback snapshot absent")
def test_the_pre_gate_snapshot_has_no_gate_leftovers():
    """The state the retirement returned the distribution to, in the gate's respect."""
    assert deploy_module().gate_leftovers(config_of(BEFORE)) == []
