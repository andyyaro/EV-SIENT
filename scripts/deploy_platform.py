#!/usr/bin/env python3
"""Publish the public site: the public pages, the NFC field pages and the error page.

That is all this script does. It used to also build a Cognito-gated `/platform*` path on the same
distribution (a private bucket, an origin, a cache behaviour and a Lambda@Edge authoriser). The
owner retired that gate on 2026-10-18 (DEC-030): the planner now lives at
https://app.futurecity.andyyaro.com with synthetic samples only, so nothing on this
distribution needs a sign-in. The gate's AWS resources were removed by hand, and this script
cannot recreate any of them. A gate or platform mode is refused, not quietly ignored.

What this touches, and what it must not
---------------------------------------
The distribution also serves the NFC field layer - the twelve pages a reader reaches by tapping
a coin in a car park, which must stay open to anyone with a phone and no account (DEC-006,
DEC-017). This script never sends a distribution config. It reads the live one, read only, to
report anything the retirement left behind, and the only CloudFront write it makes is an
invalidation after a real publish.

Every sync to the public bucket adds and replaces and never deletes. A checkout lacks the
vendored third-party files that are fetched rather than committed (CesiumJS by
scripts/vendor_cesium.sh, for one), so a `--delete` sync from it would remove live copies that
no tracked folder produces. :func:`deletion_refusal` turns any deletion an `s3 sync` reports
into a refusal.

Nothing here writes a tracked file, and account ids are computed at runtime and redacted from
this script's output.

Usage
-----
    python scripts/deploy_platform.py                 # dry run: says what it WOULD do
    python scripts/deploy_platform.py --apply         # actually publish
    python scripts/check_live_vs_main.py              # afterwards: is live byte-identical to main?
    python scripts/verify_deployment.py               # and: NFC pages open, no /platform content

`--www-only` is still accepted, as a no-op: the public site is the only thing there is to deploy.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROFILE = "future-city"
REGION = "us-east-1"

DISTRIBUTION_ID = "E1XZPHWHZV0OEO"
MAIN_BUCKET = "future-city-fellowship"

#: The planner that replaced the gated path (DEC-030). Named in every refusal so the person who
#: reaches for the old mode learns where the thing they wanted went.
PLANNER_URL = "https://app.futurecity.andyyaro.com"

#: What the retired gate looked like on the distribution. Used only to REPORT leftovers from the
#: read-only config fetch; nothing in this script builds any of them.
RETIRED_PATH_PATTERN = "/platform*"
RETIRED_ORIGIN_ID = "platform-gated"

#: Command-line spellings of a gate or platform deploy. Each is refused with a clear message;
#: none of them deploys anything.
RETIRED_MODES = ("--platform", "--gate", "--full", "--with-gate", "--platform-only")

#: The public half of the main bucket besides site/www: local folder -> key prefix. These files
#: have no extension, so their type must be named or S3 stores them as binary, and they keep the
#: five-minute cache they were first uploaded with on 2026-07-27 (measured live 2026-10-17).
FIELD_TREES = {"site/nfc-landing": "t/", "site/nfc-capture": "f/", "site/errors": "errors/"}
FIELD_HEADERS = ["--content-type", "text/html;charset=utf-8", "--cache-control", "public,max-age=300"]
#: Every public page revalidates on each load, as the live copies have since 2026-10-15; images,
#: the PDF and the vendored script carry no Cache-Control, also as live.
PAGE_HEADERS = ["--cache-control", "no-cache"]

#: Which commit the public half was published from. Written on every --apply, read by
#: scripts/check_live_vs_main.py. Audit F-14 found production matching no commit at all.
MARKER_KEY = "deployed.json"

ACCOUNT_RE = re.compile(r"\b\d{12}\b")


def redact(text) -> str:
    """Account ids never reach this script's output, its logs, or the ledger."""
    return ACCOUNT_RE.sub("<ACCOUNT>", str(text))


def aws(*args: str, parse: bool = True, check: bool = True):
    proc = subprocess.run(["aws", *args, "--profile", PROFILE, "--output", "json"],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"aws {' '.join(args[:3])} failed:\n{redact(proc.stderr)}")
    if not parse:
        return proc
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def say(step: str, message) -> None:
    print(f"  [{step}] {redact(message)}")


# ---------------------------------------------------------------- identity

def check_identity() -> None:
    """Standing rule: verify the profile before every phase of AWS work."""
    arn = aws("sts", "get-caller-identity")["Arn"]
    say("identity", f"authenticated as {redact(arn)}")


# ---------------------------------------------------------------- the retired gate

def retired_mode_refusal(argv: list[str]) -> str | None:
    """Why a command line asking for the gate or the platform bundle is refused, or None."""
    asked = [a for a in argv if a.split("=", 1)[0] in RETIRED_MODES]
    if not asked:
        return None
    return (f"REFUSING {' '.join(asked)}: the Cognito-gated /platform* path was retired on "
            f"2026-10-18 (DEC-030) and this script no longer deploys it. The planner lives at "
            f"{PLANNER_URL} and carries synthetic samples only. Nothing was changed. Run "
            f"without that flag to publish the public site.")


def gate_leftovers(config: dict) -> list[str]:
    """Anything on the distribution that the retired gate put there. Reported, never changed.

    The default behaviour must never carry a Lambda association either: that would gate the
    public NFC pages, which is the one outcome every version of this script has existed to
    prevent.
    """
    found = []
    for behaviour in config.get("CacheBehaviors", {}).get("Items", []) or []:
        if behaviour.get("PathPattern") == RETIRED_PATH_PATTERN:
            found.append(f"cache behaviour {RETIRED_PATH_PATTERN}")
    for origin in config.get("Origins", {}).get("Items", []) or []:
        if origin.get("Id") == RETIRED_ORIGIN_ID:
            found.append(f"origin {RETIRED_ORIGIN_ID}")
    default = config.get("DefaultCacheBehavior", {})
    if default.get("LambdaFunctionAssociations", {}).get("Quantity", 0):
        found.append("a Lambda association on the DEFAULT behaviour (it would gate the NFC pages)")
    return found


def report_distribution() -> None:
    """Read the live distribution config and say whether the gate is really gone. Read only."""
    config = aws("cloudfront", "get-distribution-config", "--id", DISTRIBUTION_ID)["DistributionConfig"]
    leftovers = gate_leftovers(config)
    if leftovers:
        say("cloudfront", f"NOTE: the distribution still carries {', '.join(leftovers)}. This "
                          "script does not change the distribution; remove it by hand (DEC-030)")
    else:
        say("cloudfront", f"no {RETIRED_PATH_PATTERN} behaviour, no gated origin, no Lambda on the "
                          "default behaviour; the distribution config is left untouched")


# ---------------------------------------------------------------- the public website

WWW = REPO / "site/www"

#: Objects that exist only because the same picture was uploaded six times under six names,
#: plus one orphan nothing references. Removing them reclaims 6.5 MB of the site's 8.1 MB and
#: saves a visitor the same on every load of the results page. Safe: the bucket has versioning
#: ENABLED (verified before writing this), and the surviving copy is tracked in git as
#: site/www/img/card-background.png.
STALE_OBJECTS = [f"top-model-findings-cards-bgs/image{n}.png" for n in range(1, 7)] + \
                ["top-model-findings-cards-bgs/image1.jpeg"]


def object_exists(bucket: str, key: str) -> bool:
    """Whether an object is actually there. Used so a dry run cannot promise a phantom delete."""
    proc = subprocess.run(["aws", "s3api", "head-object", "--bucket", bucket, "--key", key,
                           "--profile", PROFILE], capture_output=True, text=True)
    return proc.returncode == 0


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def public_trees() -> dict[str, str]:
    """Every folder published to the main bucket: local folder -> key prefix."""
    return {"site/www": "", **FIELD_TREES}


def uncommitted_public_files() -> list[str]:
    """Changed or untracked files under the public folders. The marker names a commit, and a file
    that differs from it would make the marker a false statement about what is live."""
    out = git("status", "--porcelain", "--untracked-files=all", "--", *public_trees())
    return [line[3:] for line in out.splitlines() if line.strip()]


def sync_changes(output: str) -> tuple[int, int]:
    """Uploads and deletions in an `s3 sync` listing, dry run or not. Progress lines are not
    objects: counting every line reported 119 objects written for the 41-file deploy of
    2026-10-17."""
    lines = [line.removeprefix("(dryrun) ") for line in output.splitlines()]
    return (sum(line.startswith("upload: ") for line in lines),
            sum(line.startswith("delete: ") for line in lines))


def deletions_from(sync_output: str) -> list[str]:
    """The S3 URLs an `s3 sync` listing deletes (or, as a dry run, would delete)."""
    lines = [line.removeprefix("(dryrun) ") for line in sync_output.splitlines()]
    return [line.removeprefix("delete: ").strip() for line in lines if line.startswith("delete: ")]


def deletion_refusal(deletions: list[str]) -> str | None:
    """Why a sync's output must be treated as a failure, or None.

    The public syncs are never given --delete, so this should never fire. It exists because
    "never" was once a property of one flag in one place: on 2026-10-17 a --delete sync from a
    checkout without the vendored CesiumJS would have removed the 377 files the live explorer
    loaded. A checkout still lacks every fetched-not-committed file, so any deletion is refused.
    """
    if not deletions:
        return None
    vendored = [d for d in deletions if "/vendor/" in d]
    detail = f", {len(vendored)} of them under a vendor/ folder" if vendored else ""
    return (f"the sync reported {len(deletions)} deletion(s){detail}. The public syncs only add "
            f"and replace; removing anything from the live site is a decision for a person")


def sync_public(local: str, prefix: str, headers: list[str], apply: bool,
                filters: tuple[str, ...] = ()) -> int:
    """`s3 sync` one public folder, never with --delete. Returns the objects (to be) written."""
    args = ["s3", "sync", str(REPO / local), f"s3://{MAIN_BUCKET}/{prefix}", *filters, *headers,
            "--no-progress"]
    if not apply:
        args.append("--dryrun")
    proc = subprocess.run(["aws", *args, "--profile", PROFILE], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(redact(proc.stderr))
    refusal = deletion_refusal(deletions_from(proc.stdout))
    if refusal:
        raise SystemExit(f"REFUSING: {refusal}")
    return sync_changes(proc.stdout)[0]


def deploy_www(apply: bool) -> None:
    """Publish the public pages, the NFC pages and the error page. Never with --delete.

    A deploy only adds and replaces. The bucket also holds folder markers no local folder has,
    and removing anything from the public site is a decision for a person, not a side effect of
    a sync - the quiet catastrophe this program is meant not to have.
    """
    if not (WWW / "index.html").is_file():
        raise SystemExit(f"{WWW} has no index.html")

    files = sorted(p for p in WWW.rglob("*") if p.is_file())
    say("www", f"{len(files)} public page/asset(s) -> s3://{MAIN_BUCKET}/")
    written = sync_public("site/www", "", PAGE_HEADERS, apply, ("--exclude", "*", "--include", "*.html"))
    written += sync_public("site/www", "", [], apply, ("--exclude", "*.html"))
    for local, prefix in FIELD_TREES.items():
        count = sum(1 for p in (REPO / local).iterdir() if p.is_file())
        say("www", f"{count} field page(s) {local} -> s3://{MAIN_BUCKET}/{prefix}")
        written += sync_public(local, prefix, FIELD_HEADERS, apply)
    say("www", f"{written} object(s) {'would be ' if not apply else ''}written")

    marker = {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
              "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if not apply:
        say("www", f"WOULD write {MARKER_KEY} naming commit {marker['commit'][:7]}")
    else:
        proc = subprocess.run(["aws", "s3", "cp", "-", f"s3://{MAIN_BUCKET}/{MARKER_KEY}",
                               "--content-type", "application/json", *PAGE_HEADERS,
                               "--profile", PROFILE],
                              input=json.dumps(marker, indent=1) + "\n", capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(redact(proc.stderr))
        say("www", f"{MARKER_KEY} names commit {marker['commit'][:7]}")

    # A dry run must not claim an action it would not take. These seven were deleted on
    # 2026-07-28 and are gone -- verified with head-object, all 404 -- yet every dry run since
    # had printed "WOULD delete duplicate ..." for all seven. Harmless in effect and wrong in
    # kind: this project's whole standard is that the report matches what happens, and a plan
    # that lists phantom deletions is the same defect as a check that cannot fail.
    present = [k for k in STALE_OBJECTS if object_exists(MAIN_BUCKET, k)]
    if not apply:
        for key in present:
            say("www", f"WOULD delete duplicate {key}")
        if not present:
            say("www", f"none of the {len(STALE_OBJECTS)} known duplicates remain; nothing to delete")
    for key in present:
        if not apply:
            continue
        subprocess.run(["aws", "s3", "rm", f"s3://{MAIN_BUCKET}/{key}", "--profile", PROFILE],
                       capture_output=True, text=True)
    if apply:
        say("www", f"removed {len(present)} duplicate/orphan object(s) "
                   f"(recoverable - bucket versioning is enabled)")
        inv = aws("cloudfront", "create-invalidation", "--distribution-id", DISTRIBUTION_ID,
                  "--paths", "/*")
        say("www", f"invalidation {inv['Invalidation']['Id']} created")


# ---------------------------------------------------------------- main

def preflight(apply: bool) -> None:
    """Refuse before the first change, not halfway through a deploy.

    A file under the public folders that differs from HEAD would make deployed.json name a
    commit that is not what went live. A dry run reports it as WOULD REFUSE and carries on, so
    its plan is still complete.
    """
    reasons = []
    dirty = uncommitted_public_files()
    if dirty:
        reasons.append(f"{len(dirty)} file(s) under the public folders differ from HEAD "
                       f"({', '.join(dirty[:3])}{', ...' if len(dirty) > 3 else ''}); commit them first")
    for reason in reasons:
        say("preflight", f"{'REFUSING' if apply else 'WOULD REFUSE'}: {reason}")
    if apply and reasons:
        raise SystemExit("REFUSING: nothing was changed.")
    if not reasons:
        say("preflight", "the public folders match HEAD")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    refusal = retired_mode_refusal(argv)
    if refusal:
        print(refusal, file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually publish; without it the script only reports")
    ap.add_argument("--www-only", action="store_true",
                    help="accepted for old runbooks; the public site is all this script deploys")
    args = ap.parse_args(argv)

    print(f"\nFuture City Fellowship - public site deploy "
          f"({'APPLY' if args.apply else 'DRY RUN - nothing will change'})\n")
    if args.www_only:
        say("note", "--www-only is the only mode now (DEC-030); it changes nothing")

    check_identity()
    preflight(args.apply)
    report_distribution()
    deploy_www(args.apply)

    print(f"\n{'Deployed.' if args.apply else 'Dry run complete. Re-run with --apply.'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
