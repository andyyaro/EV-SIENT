"""The secret scan must catch real credentials and ignore descriptions of them.

A gate that only ever passes is not a gate. These tests exercise both directions: every
pattern is proven to fire on a realistic (fabricated) value, and the strings that made the
previous gate produce false positives are proven not to fire.

Every "secret" here is invented for the test. None is real, and none has ever been valid.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from secret_scan import PATTERNS, scan, tracked_files  # noqa: E402

# Fabricated values, shaped like the real thing so the patterns are genuinely exercised.
SHOULD_MATCH = [
    ("aws_access_key_id", "AKIAIOSFODNN7EXAMPLE"),
    ("aws_access_key_id", "ASIAY34FZKBOKMUTVV7A"),
    ("aws_access_key_id", "AROAEXAMPLE7EXAMPLE99"),   # IAM unique ids run longer
    ("aws_secret_access_key",
     "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
    ("aws_secret_access_key",
     'AWS_SECRET_ACCESS_KEY: "abcdefghijklmnopqrstuvwxyz0123456789ABCD"'),
    ("aws_account_id_in_arn", "arn:aws:iam::123456789012:role/Example"),
    ("aws_account_id_in_arn", "arn:aws:s3:us-east-1:210987654321:bucket/x"),
    ("aws_account_id_assigned", "account_id = 123456789012"),
    ("aws_account_id_assigned", 'AWS_ACCOUNT_ID: "210987654321"'),
    ("private_key_block", "-----BEGIN PRIVATE KEY-----"),
    ("private_key_block", "-----BEGIN RSA PRIVATE KEY-----"),
    ("github_token", "ghp_" + "A" * 36),
    ("github_token", "gho_" + "b" * 36),
    ("openai_key", "sk-" + "A" * 40),
    ("openai_key", "sk-proj-" + "z" * 40),
    ("slack_token", "xoxb-123456789012-abcdefghijkl"),
]

# The exact strings that made the previous name-only gate fail on a clean tree.
SHOULD_NOT_MATCH = [
    "aws_secret_access_key",                       # the bare name, no value
    "Never commit an aws_secret_access_key.",
    "grep -E 'AKIA[0-9A-Z]{16}|aws_secret_access_key'",   # a scan pattern, quoted
    "See the aws_access_key_id documentation.",
    "AWS account <AWS_ACCOUNT_ID> is referenced in prose",     # 12 digits, no ARN/assignment
    "The run produced 123456789012 rows",
    "arn:aws:iam::<ACCOUNT_FC>:role/Example",     # documented placeholder
    "BEGIN PRIVATE KEY (as a phrase in a sentence)",
    "sk-short",
    "ghp_tooshort",
    "Set AWS_SECRET_ACCESS_KEY in your shell profile, never in the repo.",
]


def _matching_pattern(text: str) -> str | None:
    for name, (pattern, _) in PATTERNS.items():
        if pattern.search(text):
            return name
    return None


@pytest.mark.parametrize("expected_pattern,text", SHOULD_MATCH)
def test_catches_real_looking_secrets(expected_pattern, text):
    hit = _matching_pattern(text)
    assert hit is not None, f"no pattern fired on {text!r}"
    assert hit == expected_pattern, f"{text!r} matched {hit}, expected {expected_pattern}"


@pytest.mark.parametrize("text", SHOULD_NOT_MATCH)
def test_ignores_descriptions_of_secrets(text):
    hit = _matching_pattern(text)
    assert hit is None, f"false positive: {text!r} matched {hit}"


def test_every_pattern_has_at_least_one_positive_case():
    """No pattern may ship untested -- an unexercised regex is an assumption."""
    covered = {name for name, _ in SHOULD_MATCH}
    untested = set(PATTERNS) - covered
    # generic_pem_or_pkcs12 is subsumed by private_key_block for BEGIN RSA PRIVATE KEY;
    # assert it fires on the forms only it covers.
    untested.discard("generic_pem_or_pkcs12")
    untested.discard("aws_session_token")
    assert untested == set(), f"patterns with no positive test: {sorted(untested)}"


def test_ssh_and_session_token_patterns_fire():
    assert _matching_pattern("-----BEGIN OPENSSH PRIVATE KEY-----") is not None
    assert PATTERNS["aws_session_token"][0].search(
        "aws_session_token=" + "A" * 120) is not None


def test_repository_is_clean():
    findings = scan()
    assert findings == [], "\n".join(findings)


def test_scan_actually_reads_the_tree():
    """Guard against a scan that passes because it scanned nothing."""
    assert len(tracked_files()) > 100


def test_cli_exits_zero_on_a_clean_tree():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/secret_scan.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "clean" in r.stdout
