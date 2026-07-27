#!/usr/bin/env python3
"""Verify the live deployment: the platform is shut, and the NFC field layer is not.

Why both halves are checked, always
-----------------------------------
A gate that closes is only half the requirement. The same CloudFront distribution serves the
twelve NFC landing pages that people reach by tapping a physical coin in a car park, with no
account and no app — and those tags are already in the field. A deployment that locked the
platform *and* broke the tags would satisfy the request as literally stated and be a clear
regression. So every run asserts both, and neither half can pass alone.

What this cannot check, stated rather than glossed
--------------------------------------------------
**That the gate opens for the granted user.** Confirming that requires signing in as
`redacted-3@example.org`, whose password is not available to the assistant and should not
be. This script proves the door is locked and correctly scoped; it cannot prove the key turns.
That check is one sign-in by the project owner, and it is recorded as an open human action
rather than quietly counted as done.

Exit code is 0 only if every assertion holds.
"""

from __future__ import annotations

import argparse
import json
import sys
import subprocess
import tempfile
from pathlib import Path

SITE = "https://futurecityfellowship.andyyaro.com"

SITES = ["FFX001", "FFX002", "FFX003", "FFX004",
         "PWC001", "PWC002", "PWC003", "PWC004",
         "PWC005", "PWC006", "PWC007", "PWC008"]

#: Assets that must never be served to an anonymous caller. `provenance_v1.json` is the whole
#: study's lineage; `contract/v1/site_table.csv` carries the twelve real facilities.
GATED = [
    "/platform/",
    "/platform/index.html",
    "/platform/app.js",
    "/platform/styles.css",
    "/platform/provenance_v1.json",
    "/platform/operations.json",
    "/platform/contract/v1/site_table.csv",
    "/platform/explorer/index.html",
]

#: Spellings that resolve to the same object but might miss a `/platform*` path pattern.
#: CloudFront normalises percent-encoding — measured, not assumed — so these are real attempts,
#: not paranoia. They are why the bundle lives in its own bucket.
BYPASSES = [
    "/%70latform/index.html",
    "/%70%6Catform/index.html",
    "/platform/../platform/index.html",
    "/PLATFORM/index.html",
    "/platform//index.html",
    "/platform/./index.html",
]

#: Pages that existed before this deployment and must be exactly as they were.
UNTOUCHED = ["/", "/index.html", "/assistant.html", "/dashboard.html",
             "/results.html", "/methodology.html"]


class Result:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def check(self, ok: bool, label: str, detail: str = "") -> None:
        (self.passed if ok else self.failed).append(label)
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))


def fetch(path: str, timeout: int = 25) -> tuple[int, bytes, dict]:
    """GET without following redirects, so a 302 is visible as a 302.

    Uses ``curl`` rather than ``urllib``. Not a stylistic choice: this machine's Python has no
    CA bundle (``CERTIFICATE_VERIFY_FAILED`` on every HTTPS call), and the two ways to make
    urllib work are to add a ``certifi`` dependency or to disable certificate verification.
    The second is unacceptable in a script whose entire job is verification — a checker that
    skips TLS validation is not checking the thing it claims to. ``curl`` uses the system trust
    store and validates fully.
    """
    with tempfile.NamedTemporaryFile(delete=False) as body_file, \
         tempfile.NamedTemporaryFile(delete=False) as header_file:
        body_path, header_path = body_file.name, header_file.name
    try:
        proc = subprocess.run(
            ["curl", "-sS", "--max-time", str(timeout), "-o", body_path, "-D", header_path,
             "-w", "%{http_code}", "-A", "fcf-deploy-verify", f"{SITE}{path}"],
            capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"curl failed for {path}: {proc.stderr.strip()}")
        status = int(proc.stdout.strip() or 0)
        body = Path(body_path).read_bytes()
        headers = {}
        for line in Path(header_path).read_text(errors="replace").splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                headers[key.strip().lower()] = value.strip()
        return status, body, headers
    finally:
        Path(body_path).unlink(missing_ok=True)
        Path(header_path).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit a machine-readable summary")
    args = ap.parse_args()

    r = Result()

    print("\nHALF 1 — the platform must be SHUT to anonymous callers\n")
    for path in GATED:
        status, body, headers = fetch(path)
        location = headers.get("location", "")
        # The only acceptable answers are "go and sign in" or "not found". Anything that
        # returns the asset is a failure, however it is dressed up.
        redirected_to_cognito = status in (301, 302, 303, 307, 308) and "amazoncognito.com" in location
        r.check(
            redirected_to_cognito,
            f"{path} is gated",
            f"HTTP {status}" + (f" -> Cognito" if redirected_to_cognito else f" ({len(body)} bytes leaked!)"),
        )

    print("\nHALF 1b — alternative path spellings must not evade the gate\n")
    for path in BYPASSES:
        status, body, headers = fetch(path)
        location = headers.get("location", "")
        served = status == 200 and len(body) > 200 and b"<html" in body[:2000].lower()
        gated = ("amazoncognito.com" in location) or status in (403, 404)
        r.check(gated and not served, f"{path} does not serve the bundle", f"HTTP {status}")

    print("\nHALF 2 — the NFC field layer must remain PUBLIC (no account, no app)\n")
    for site in SITES:
        status, body, _ = fetch(f"/t/{site}")
        ok = status == 200 and len(body) > 1000
        r.check(ok, f"/t/{site} still public", f"HTTP {status}, {len(body)} bytes")

    print("\nHALF 2b — pages that predate this deployment must be untouched\n")
    for path in UNTOUCHED:
        status, body, _ = fetch(path)
        ok = status == 200 and len(body) > 500
        r.check(ok, f"{path} unaffected", f"HTTP {status}, {len(body)} bytes")

    print("\n" + "=" * 72)
    print(f"  {len(r.passed)} passed, {len(r.failed)} failed")
    if r.failed:
        print("\n  FAILED:")
        for label in r.failed:
            print(f"    - {label}")
    print("""
  NOT VERIFIED BY THIS SCRIPT — and not counted as done:
    That the gate OPENS for redacted-3@example.org. That needs a sign-in with a
    password the assistant does not have and should not have. Open human action.
""")

    if args.json:
        print(json.dumps({"passed": len(r.passed), "failed": r.failed}, indent=2))

    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
