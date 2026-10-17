#!/usr/bin/env python3
"""Deploy the public AI assistant's Lambda from the repository.

Why this exists
---------------
Until 2026-10-17 the assistant's code existed only inside AWS: 1,842 lines deployed as
`$LATEST`, one published version from June, and nothing in any branch. The change that made
the assistant public on 2026-10-15 therefore had no reviewable history and no rollback point
except a four-month-old version. `infra/assistant/lambda_function.py` is now the source of
truth and this script is the only route from it to AWS.

What it does, in order
----------------------
1. Zips `infra/assistant/lambda_function.py` and compares its SHA-256 with the deployed code.
   Identical bytes -> nothing to do, and it says so.
2. `update-function-code`, then waits until the update has finished.
3. `publish-version`, described with the commit it came from, so every deployed state is a
   numbered, immutable version that can be pointed back to.
4. Moves the `live` alias to that version. API Gateway invokes the alias, never `$LATEST`, so
   a half-finished console edit cannot reach visitors.

Usage
-----
    python scripts/deploy_assistant.py            # dry run: says what it WOULD do
    python scripts/deploy_assistant.py --apply    # actually deploy
    python scripts/deploy_assistant.py --rollback 7 --apply   # point `live` at version 7
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROFILE = "future-city"
REGION = "us-east-1"
FUNCTION_NAME = "future-city-assistant-chat"
ALIAS = "live"
SOURCE = REPO / "infra/assistant/lambda_function.py"

ACCOUNT_RE = re.compile(r"\b\d{12}\b")


def redact(text) -> str:
    """Account ids never reach this script's output."""
    return ACCOUNT_RE.sub("<ACCOUNT>", str(text))


def aws(*args: str):
    proc = subprocess.run(["aws", *args, "--profile", PROFILE, "--region", REGION,
                           "--output", "json"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"aws {' '.join(args[:2])} failed:\n{redact(proc.stderr)}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def say(step: str, message) -> None:
    print(f"  [{step}] {redact(message)}")


def build_zip() -> bytes:
    """A deterministic zip: fixed timestamp and permissions, so equal source means equal bytes."""
    buffer = io.BytesIO()
    info = zipfile.ZipInfo("lambda_function.py", date_time=(1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(info, SOURCE.read_bytes())
    return buffer.getvalue()


def code_sha256(blob: bytes) -> str:
    """The digest Lambda reports as CodeSha256: base64 of the raw SHA-256."""
    return base64.b64encode(hashlib.sha256(blob).digest()).decode()


def git_head() -> str:
    proc = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True)
    dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--",
                            str(SOURCE.relative_to(REPO))], capture_output=True, text=True)
    return proc.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")


def point_alias(version: str, apply: bool) -> None:
    if not apply:
        say("alias", f"WOULD point '{ALIAS}' at version {version}")
        return
    aws("lambda", "update-alias", "--function-name", FUNCTION_NAME, "--name", ALIAS,
        "--function-version", version)
    say("alias", f"'{ALIAS}' -> version {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="actually deploy")
    parser.add_argument("--rollback", metavar="VERSION",
                        help="point the alias at an existing version instead of deploying")
    args = parser.parse_args()

    say("identity", aws("sts", "get-caller-identity")["Arn"])

    if args.rollback:
        point_alias(args.rollback, args.apply)
        return 0

    blob = build_zip()
    local = code_sha256(blob)
    deployed = aws("lambda", "get-function-configuration",
                   "--function-name", FUNCTION_NAME)["CodeSha256"]
    alias = aws("lambda", "get-alias", "--function-name", FUNCTION_NAME, "--name", ALIAS)
    say("code", f"repository {local[:12]}... deployed $LATEST {deployed[:12]}... "
                f"'{ALIAS}' -> version {alias['FunctionVersion']}")

    if local == deployed:
        say("code", "deployed code already matches the repository - nothing to upload")
    elif not args.apply:
        say("code", "WOULD upload the repository code")
    else:
        zip_path = REPO / "infra/assistant/.deploy.zip"
        zip_path.write_bytes(blob)
        try:
            aws("lambda", "update-function-code", "--function-name", FUNCTION_NAME,
                "--zip-file", f"fileb://{zip_path}")
        finally:
            zip_path.unlink(missing_ok=True)
        subprocess.run(["aws", "lambda", "wait", "function-updated", "--function-name",
                        FUNCTION_NAME, "--profile", PROFILE, "--region", REGION], check=True)
        say("code", "uploaded and update finished")

    if not args.apply:
        say("version", "WOULD publish a version and move the alias to it")
        return 0

    published = aws("lambda", "publish-version", "--function-name", FUNCTION_NAME,
                    "--description", f"repository {git_head()}")
    say("version", f"published version {published['Version']}")
    point_alias(published["Version"], apply=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
