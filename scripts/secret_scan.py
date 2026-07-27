"""Secret scan over tracked files. The single source of truth for both gates.

``scripts/verify.sh`` and ``.github/workflows/tests.yml`` both call this module, so the two
cannot drift apart. They previously each carried their own copy of the regex with *different*
exclusions, which meant the gate passed in CI and failed locally.

Patterns match a secret's **value**, not its name
-------------------------------------------------
The earlier gate matched the bare string ``aws_secret_access_key``. Any file that *describes*
the scan -- CI's own workflow, an audit document, this module -- therefore tripped it, and the
fix kept being another path exclusion. That list can only grow, and a scanner that is routinely
suppressed stops being read.

A credential name is not a credential. These patterns require the accompanying value: a key id
with its 16 trailing characters, a secret key with 40 base64 characters after the assignment, a
PEM header, a token with its full body. Prose may name a credential; it may not carry one.

Also covers, per the V4 program's secrets rule: AWS account ids in ARN or assignment context.
Twelve consecutive digits are not treated as an account id on their own -- that would flag
phone numbers, coordinates, and row counts -- so the context is required.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# name -> (compiled pattern, what it means)
PATTERNS: dict[str, tuple[re.Pattern, str]] = {
    "aws_access_key_id": (
        re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ABIA|ACCA)[0-9A-Z]{16,}\b"),
        "AWS access key id or IAM unique id",
    ),
    "aws_secret_access_key": (
        re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{40}\b"),
        "AWS secret access key with a value",
    ),
    "aws_session_token": (
        re.compile(r"(?i)aws_session_token\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{100,}"),
        "AWS session token with a value",
    ),
    "aws_account_id_in_arn": (
        re.compile(r"arn:aws[a-z-]*:[a-z0-9-]*:[a-z0-9-]*:\d{12}:"),
        "AWS account id inside an ARN",
    ),
    "aws_account_id_assigned": (
        re.compile(r"(?i)\b(?:aws_)?account[_-]?id\s*[:=]\s*[\"']?\d{12}\b"),
        "AWS account id assigned to a variable",
    ),
    "private_key_block": (
        re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
        "PEM private key block",
    ),
    "github_token": (
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        "GitHub token",
    ),
    "openai_key": (
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
        "OpenAI-style API key",
    ),
    "slack_token": (
        re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
        "Slack token",
    ),
    "generic_pem_or_pkcs12": (
        re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----"),
        "SSH/RSA private key",
    ),
}

# Files this scanner must not flag for containing its own pattern definitions.
# Deliberately tiny: only the scanner and its test. Everything else is scanned.
SELF = {"scripts/secret_scan.py", "tests/test_secret_scan.py"}

BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pptx", ".docx", ".xlsx", ".glb",
    ".zip", ".slx", ".slxc", ".mat", ".ico", ".woff", ".woff2", ".ttf",
}


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f]


def scan() -> list[str]:
    """Return one human-readable finding per match. Empty means clean."""
    findings: list[str] = []
    for rel in tracked_files():
        if rel in SELF or Path(rel).suffix.lower() in BINARY_SUFFIXES:
            continue
        path = REPO / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable; nothing text-like to leak
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, (pattern, description) in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{rel}:{lineno}: {name} ({description})")
    return findings


if __name__ == "__main__":
    findings = scan()
    if findings:
        print("POTENTIAL SECRETS IN TRACKED FILES:")
        print("\n".join(findings))
        print(f"\n{len(findings)} finding(s). Nothing above is printed with its value.")
        sys.exit(1)
    print(f"secret scan clean ({len(tracked_files())} tracked files, {len(PATTERNS)} patterns)")
