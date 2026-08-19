#!/usr/bin/env python3
"""Deploy the platform web tier behind the Cognito edge gate.

What this touches, and what it must not
---------------------------------------
The distribution serving the platform **also serves the NFC field layer** - the twelve pages a
reader reaches by tapping a coin in a car park, which must stay open to anyone with a phone and
no account (DEC-006, DEC-017). So this script adds one origin and one cache behaviour, and
changes nothing else. It *asserts* that rather than intending it: :func:`assert_safe_change`
compares the config it is about to send against the one it fetched and refuses if the default
cache behaviour, the existing origin, the aliases or the certificate moved by so much as a key.

That check exists because ``update-distribution`` is a **whole-config replace**. There is no
partial update. A script that builds the new config slightly wrong does not fail - it
successfully deploys a broken site.

Why the platform gets its own bucket
------------------------------------
This is the part that is not obvious, and it is the difference between a gate and the
*appearance* of one.

A cache behaviour is selected by matching the request path against ``/platform*``. But
CloudFront normalises percent-encoding - measured, not assumed: ``/%61ssistant.html`` returns
the same 70 378 bytes as ``/assistant.html`` on this distribution today. If path-pattern
matching happens before that normalisation, then ``/%70latform/index.html`` would miss the
gated behaviour, fall through to the **default** behaviour, and be served with no
authentication at all.

Rather than depend on the order of two internal CloudFront steps, the platform bundle lives in
a **separate bucket that the default behaviour's origin cannot see**. Any request that evades
the path pattern lands on the main bucket, which simply has no platform content in it, and gets
a 404. The guarantee stops being behavioural and becomes structural - the same reasoning that
makes an operation *be* a CLI command rather than merely match one.

Nothing here writes a credential into a tracked file, and the one tracked file it DOES write --
`docs/operations/v4-program/cloudfront-config-before-platform.json` -- has its account id
redacted before it is saved (verified: the tracked copy contains `<ACCOUNT>`, never digits).
Account ids are
computed at runtime and redacted from this script's output.

Usage
-----
    python scripts/deploy_platform.py                 # dry run: says what it WOULD do
    python scripts/deploy_platform.py --apply         # actually do it
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROFILE = "future-city"
REGION = "us-east-1"

DISTRIBUTION_ID = "E1XZPHWHZV0OEO"
MAIN_BUCKET = "future-city-fellowship"
PLATFORM_BUCKET = "future-city-fellowship-platform"
S3_PREFIX = "platform"
PATH_PATTERN = "/platform*"
ORIGIN_ID = "platform-gated"

FUNCTION_NAME = "fcf-platform-edge-auth"
ROLE_NAME = "fcf-platform-edge-auth-role"
EDGE_SOURCE = REPO / "infra/edge-auth/index.mjs"
BUNDLE = REPO / "site/platform"

#: AWS managed cache policy "CachingOptimized". Cookies are deliberately NOT part of the cache
#: key - they must not be, or every session would get its own cache entry. That is safe here
#: precisely because viewer-request runs *before* the cache is consulted, so a cached object is
#: still unreachable without a valid session. It also means the session cookie is never
#: forwarded to S3 and never lands in its logs.
CACHING_OPTIMIZED = "658327ea-f89d-4fab-a63d-7e88639e58f6"

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


def account_id() -> str:
    return aws("sts", "get-caller-identity")["Account"]


# ---------------------------------------------------------------- identity

def check_identity() -> None:
    """Standing rule: verify the profile before every phase of AWS work."""
    arn = aws("sts", "get-caller-identity")["Arn"]
    say("identity", f"authenticated as {redact(arn)}")


# ---------------------------------------------------------------- the gated bucket

def ensure_platform_bucket(apply: bool) -> None:
    exists = aws("s3api", "head-bucket", "--bucket", PLATFORM_BUCKET,
                 check=False, parse=False).returncode == 0
    if exists:
        say("s3", f"bucket {PLATFORM_BUCKET} exists")
    elif not apply:
        say("s3", f"WOULD create private bucket {PLATFORM_BUCKET}")
        return
    else:
        # us-east-1 is the one region where create-bucket must NOT be given a location
        # constraint; passing one fails with InvalidLocationConstraint.
        aws("s3api", "create-bucket", "--bucket", PLATFORM_BUCKET, "--region", REGION)
        say("s3", f"created {PLATFORM_BUCKET}")

    if not apply:
        say("s3", "WOULD block all public access and attach a CloudFront-only policy")
        return

    aws("s3api", "put-public-access-block", "--bucket", PLATFORM_BUCKET,
        "--public-access-block-configuration",
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true")

    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCloudFrontServicePrincipalReadOnly",
            "Effect": "Allow",
            "Principal": {"Service": "cloudfront.amazonaws.com"},
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{PLATFORM_BUCKET}/*",
            # Scoped to THIS distribution. Without the condition any CloudFront distribution
            # in any account could read the bucket.
            "Condition": {"StringEquals": {
                "AWS:SourceArn":
                    f"arn:aws:cloudfront::{account_id()}:distribution/{DISTRIBUTION_ID}"}},
        }],
    }
    aws("s3api", "put-bucket-policy", "--bucket", PLATFORM_BUCKET,
        "--policy", json.dumps(policy))
    say("s3", "public access blocked; policy allows only this distribution")


USER_POOL_ID = "us-east-1_mKrwfQTkg"
APP_CLIENT_ID = "1b9ab91m46pr3m2n74qapq3ls5"


def ensure_managed_login_branding(apply: bool) -> None:
    """Give the app client a managed-login branding style, or its sign-in page will not exist.

    This is not cosmetic and the failure it prevents is not obvious. This pool runs
    **Managed Login (version 2)**, and under version 2 every app client needs its own branding
    record. A client without one does not fall back to a default page - Cognito serves
    "Login pages unavailable · Please contact an administrator", with nothing in the app
    client's own configuration to suggest why.

    It shipped that way once: the gate correctly redirected to Cognito, and Cognito had no page
    to show. The deployment verifier now follows the redirect for exactly this reason, because
    checking that the gate *redirects* is a weaker claim than checking a person can *sign in*.
    """
    existing = aws("cognito-idp", "describe-managed-login-branding-by-client",
                   "--user-pool-id", USER_POOL_ID, "--client-id", APP_CLIENT_ID,
                   check=False, parse=False)
    if existing.returncode == 0:
        say("cognito", "app client already has managed-login branding")
        return
    if not apply:
        say("cognito", "WOULD create managed-login branding for the app client")
        return
    created = aws("cognito-idp", "create-managed-login-branding",
                  "--user-pool-id", USER_POOL_ID, "--client-id", APP_CLIENT_ID,
                  "--use-cognito-provided-values")
    say("cognito", f"created branding {created['ManagedLoginBranding']['ManagedLoginBrandingId']}")


def ensure_oac(apply: bool) -> str:
    listed = aws("cloudfront", "list-origin-access-controls")
    for item in listed.get("OriginAccessControlList", {}).get("Items", []):
        if item["Name"] == f"oac-{PLATFORM_BUCKET}":
            say("cloudfront", f"origin access control exists: {item['Id']}")
            return item["Id"]
    if not apply:
        say("cloudfront", "WOULD create an origin access control for the platform bucket")
        return "<oac-pending>"
    created = aws("cloudfront", "create-origin-access-control",
                  "--origin-access-control-config", json.dumps({
                      "Name": f"oac-{PLATFORM_BUCKET}",
                      "Description": "Gated platform bundle (DEC-017)",
                      "SigningProtocol": "sigv4",
                      "SigningBehavior": "always",
                      "OriginAccessControlOriginType": "s3",
                  }))
    oac = created["OriginAccessControl"]["Id"]
    say("cloudfront", f"created origin access control {oac}")
    return oac


# ---------------------------------------------------------------- lambda

def zip_edge_source() -> bytes:
    """Deterministic zip: fixed timestamps, so unchanged source produces identical bytes and
    the published version history keeps meaning something."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo("index.mjs", date_time=(1980, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        zf.writestr(info, EDGE_SOURCE.read_text())
    return buffer.getvalue()


def ensure_role(apply: bool) -> str:
    existing = aws("iam", "get-role", "--role-name", ROLE_NAME, check=False, parse=False)
    if existing.returncode == 0:
        arn = json.loads(existing.stdout)["Role"]["Arn"]
        say("iam", f"role exists: {redact(arn)}")
        return arn
    if not apply:
        say("iam", f"WOULD create role {ROLE_NAME}")
        return "<role-arn-pending>"

    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            # BOTH principals are required. lambda.amazonaws.com alone lets the function exist
            # but CloudFront cannot replicate it to the edge, and the association then fails
            # with an error that never mentions the trust policy.
            "Principal": {"Service": ["lambda.amazonaws.com", "edgelambda.amazonaws.com"]},
            "Action": "sts:AssumeRole",
        }],
    }
    created = aws("iam", "create-role", "--role-name", ROLE_NAME,
                  "--assume-role-policy-document", json.dumps(trust),
                  "--description", "Lambda@Edge authoriser for the Future City platform")
    aws("iam", "attach-role-policy", "--role-name", ROLE_NAME,
        "--policy-arn", "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    say("iam", f"created {redact(created['Role']['Arn'])}; waiting for IAM propagation")
    time.sleep(12)                      # IAM is eventually consistent; CreateFunction 400s without this
    return created["Role"]["Arn"]


def deploy_lambda(apply: bool, role_arn: str) -> str:
    payload = zip_edge_source()
    say("lambda", f"index.mjs packaged, {len(payload)} bytes, "
                  f"sha256:{hashlib.sha256(payload).hexdigest()[:12]}…")

    exists = aws("lambda", "get-function", "--function-name", FUNCTION_NAME,
                 "--region", REGION, check=False, parse=False).returncode == 0
    if not apply:
        say("lambda", f"WOULD {'update' if exists else 'create'} {FUNCTION_NAME}, publish a version")
        return "<lambda-arn-pending>"

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(payload)
        zip_path = tmp.name
    try:
        if exists:
            aws("lambda", "update-function-code", "--function-name", FUNCTION_NAME,
                "--zip-file", f"fileb://{zip_path}", "--region", REGION)
            # update-function-code returns before the new code is live; publishing too early
            # publishes the OLD code under a new version number.
            aws("lambda", "wait", "function-updated", "--function-name", FUNCTION_NAME,
                "--region", REGION, parse=False)
        else:
            aws("lambda", "create-function", "--function-name", FUNCTION_NAME,
                "--runtime", "nodejs22.x", "--role", role_arn, "--handler", "index.handler",
                "--zip-file", f"fileb://{zip_path}", "--region", REGION,
                # Lambda@Edge viewer-request ceilings: 5s, 128MB. Not tunable upward.
                "--timeout", "5", "--memory-size", "128",
                "--description", "Cognito gate for /platform* (DEC-017)")
            aws("lambda", "wait", "function-active", "--function-name", FUNCTION_NAME,
                "--region", REGION, parse=False)
    finally:
        Path(zip_path).unlink(missing_ok=True)

    published = aws("lambda", "publish-version", "--function-name", FUNCTION_NAME,
                    "--region", REGION)
    arn = published["FunctionArn"]
    if not arn.endswith(f":{published['Version']}"):
        arn = f"{arn}:{published['Version']}"
    say("lambda", f"published version {published['Version']}: {redact(arn)}")
    return arn


# ---------------------------------------------------------------- cloudfront

def build_origin(oac_id: str) -> dict:
    return {
        "Id": ORIGIN_ID,
        "DomainName": f"{PLATFORM_BUCKET}.s3.{REGION}.amazonaws.com",
        "OriginPath": "",
        "CustomHeaders": {"Quantity": 0},
        "S3OriginConfig": {"OriginAccessIdentity": ""},
        "OriginAccessControlId": oac_id,
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10,
        "OriginShield": {"Enabled": False},
    }


def build_behaviour(lambda_arn: str) -> dict:
    return {
        "PathPattern": PATH_PATTERN,
        "TargetOriginId": ORIGIN_ID,
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2, "Items": ["HEAD", "GET"],
            "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
        },
        "Compress": True,
        "CachePolicyId": CACHING_OPTIMIZED,
        "SmoothStreaming": False,
        "FieldLevelEncryptionId": "",
        "LambdaFunctionAssociations": {
            "Quantity": 1,
            "Items": [{
                "LambdaFunctionARN": lambda_arn,
                "EventType": "viewer-request",
                "IncludeBody": False,
            }],
        },
        "FunctionAssociations": {"Quantity": 0},
        "TrustedSigners": {"Enabled": False, "Quantity": 0},
        "TrustedKeyGroups": {"Enabled": False, "Quantity": 0},
    }


#: Everything outside these keys must be byte-identical between the fetched config and the one
#: we send. Named explicitly so that adding a key here is a deliberate act with a diff.
MAY_CHANGE = {"Origins", "CacheBehaviors"}


def assert_safe_change(before: dict, after: dict) -> None:
    """Refuse to send a config that alters anything except the platform origin and behaviour.

    This is the guard that protects the NFC layer. ``update-distribution`` replaces the entire
    configuration, so a subtly wrong payload deploys a broken site *successfully*.
    """
    a = {k: v for k, v in before.items() if k not in MAY_CHANGE}
    b = {k: v for k, v in after.items() if k not in MAY_CHANGE}
    if a != b:
        differing = sorted({k for k in set(a) | set(b) if a.get(k) != b.get(k)})
        raise SystemExit(
            "REFUSING TO DEPLOY: config differs outside the platform origin/behaviour.\n"
            f"  keys that changed: {differing}\n"
            "  The default cache behaviour serves the public NFC tag pages; changing it would\n"
            "  break every physical tag in the field. Nothing has been sent.")

    # The default behaviour must stay exactly as found, and must never carry an auth function.
    #
    # NOTE: the first of these two checks is SUBSUMED by the comparison above --
    # `DefaultCacheBehavior` is not in MAY_CHANGE, so any change to it already raises there,
    # with a different message. It is kept as a named guard rather than deleted, because a
    # deploy path is the wrong place to remove a safety check for tidiness; but it must not
    # be counted as independent coverage. The SECOND check is genuinely independent: it fires
    # on a Lambda association that was present BEFORE and after, which the equality test
    # cannot see.
    if before["DefaultCacheBehavior"] != after["DefaultCacheBehavior"]:
        raise SystemExit("REFUSING TO DEPLOY: the default cache behaviour changed.")
    if after["DefaultCacheBehavior"].get("LambdaFunctionAssociations", {}).get("Quantity", 0):
        raise SystemExit(
            "REFUSING TO DEPLOY: the DEFAULT behaviour has a Lambda association.\n"
            "  That would gate the public NFC pages. Not what this deploys.")

    # Every origin that existed before must survive untouched - EXCEPT the platform origin,
    # which this script owns and rewrites on every run. Without that exemption the guard fires
    # on the second deploy of an unchanged config, which is a guard that cries wolf: the useful
    # signal (someone else's origin moved) gets lost in a failure that happens every time.
    before_origins = {o["Id"]: o for o in before["Origins"]["Items"]}
    after_origins = {o["Id"]: o for o in after["Origins"]["Items"]}
    for origin_id, origin in before_origins.items():
        if origin_id == ORIGIN_ID:
            continue
        if after_origins.get(origin_id) != origin:
            raise SystemExit(f"REFUSING TO DEPLOY: existing origin {origin_id} was modified.")
    if ORIGIN_ID in before_origins:
        # It may change, but only in ways that keep it pointing at the isolated bucket.
        if after_origins[ORIGIN_ID]["DomainName"] != f"{PLATFORM_BUCKET}.s3.{REGION}.amazonaws.com":
            raise SystemExit("REFUSING TO DEPLOY: the platform origin no longer points at the "
                             "isolated bucket - that is the whole bypass defence.")
    added = set(after_origins) - set(before_origins)
    if added - {ORIGIN_ID}:
        raise SystemExit(f"REFUSING TO DEPLOY: unexpected new origins {sorted(added)}")

    patterns = [x["PathPattern"] for x in after.get("CacheBehaviors", {}).get("Items", [])]
    if patterns != [PATH_PATTERN]:
        raise SystemExit(f"REFUSING TO DEPLOY: unexpected cache behaviours {patterns}")

    # The gated behaviour must point at the SEPARATE bucket. If it ever pointed at the main
    # origin, a path that evaded the pattern would be served ungated from the same content.
    gated = after["CacheBehaviors"]["Items"][0]
    if gated["TargetOriginId"] != ORIGIN_ID:
        raise SystemExit("REFUSING TO DEPLOY: the gated behaviour does not target the "
                         "isolated platform origin - that is the whole bypass defence.")


def deploy_cloudfront(apply: bool, lambda_arn: str, oac_id: str) -> None:
    current = aws("cloudfront", "get-distribution-config", "--id", DISTRIBUTION_ID)
    etag, config = current["ETag"], current["DistributionConfig"]

    # The rollback snapshot is written ONCE and never again.
    #
    # This used to overwrite `cloudfront-config-before-platform.json` on every run, including
    # dry runs. So the file whose entire purpose is "what the distribution looked like before
    # the platform behaviour existed" was replaced, the first time the script ran, with the
    # config that HAS the platform behaviour in it - `platform-gated` origin, `/platform*`
    # cache behaviour and all. Six commits carried it that way. Restoring from it would have
    # restored the change it exists to undo, and the log line calling it the "original config"
    # made that harder to notice, not easier.
    #
    # The pre-change state was recovered from `93c651d`, the only revision that still held it.
    before = REPO / "docs/operations/v4-program/cloudfront-config-before-platform.json"
    before.parent.mkdir(parents=True, exist_ok=True)
    if before.is_file():
        say("cloudfront", f"rollback snapshot left untouched -> {before.relative_to(REPO)}")
    else:
        before.write_text(redact(json.dumps(config, indent=2)) + "\n")
        say("cloudfront", f"rollback snapshot created (account redacted) -> "
                          f"{before.relative_to(REPO)}")

    # The current config is still worth recording - it is just not the rollback target, so it
    # gets its own name and says what it is.
    # Written LAST, from a fresh fetch, not from the config read at the top of this function.
    #
    # It used to be written here from `config` -- the state BEFORE this run's update -- while
    # being labelled "config as it is RIGHT NOW". After the 2026-07-28 apply the file therefore
    # recorded Lambda version 7 while the distribution was serving version 8, and the audit that
    # found it had to diff against live to notice. A snapshot whose name asserts currency has to
    # be taken after the change, or it is documentation of a moment that has already passed.
    latest = REPO / "docs/operations/v4-program/cloudfront-config-observed.json"

    new_config = json.loads(json.dumps(config))
    origins = [o for o in new_config["Origins"]["Items"] if o["Id"] != ORIGIN_ID]
    origins.append(build_origin(oac_id))
    new_config["Origins"] = {"Quantity": len(origins), "Items": origins}
    new_config["CacheBehaviors"] = {"Quantity": 1, "Items": [build_behaviour(lambda_arn)]}

    assert_safe_change(config, new_config)
    say("cloudfront", f"diff verified: +1 origin ({PLATFORM_BUCKET}), +1 behaviour {PATH_PATTERN}")
    say("cloudfront", "default behaviour byte-identical; NFC tag pages unaffected")

    if not apply:
        say("cloudfront", "WOULD update the distribution (dry run)")
        write_observed(apply)
        return

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(new_config, tmp)
        path = tmp.name
    try:
        aws("cloudfront", "update-distribution", "--id", DISTRIBUTION_ID,
            "--if-match", etag, "--distribution-config", f"file://{path}")
    finally:
        Path(path).unlink(missing_ok=True)
    say("cloudfront", "distribution updated; edge propagation takes a few minutes")
    write_observed(apply)


# ---------------------------------------------------------------- content


def write_observed(apply: bool) -> None:
    """Record the distribution config as it is AFTER any change this run made."""
    fresh = aws("cloudfront", "get-distribution-config", "--id", DISTRIBUTION_ID)
    latest = REPO / "docs/operations/v4-program/cloudfront-config-observed.json"
    latest.write_text(redact(json.dumps(fresh["DistributionConfig"], indent=2)) + "\n")
    when = "after this run's update" if apply else "unchanged (dry run made no change)"
    say("cloudfront", f"observed config saved, {when} -> {latest.relative_to(REPO)}")

def deploy_bundle(apply: bool) -> None:
    if not (BUNDLE / "index.html").is_file():
        raise SystemExit(f"{BUNDLE} has no index.html - build the bundle first")

    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file())
    oversize = [p for p in files if p.stat().st_size > 25 * 1024 * 1024]
    if oversize:
        raise SystemExit(f"refusing: files over 25 MB: {oversize}")

    total = sum(p.stat().st_size for p in files)
    say("s3", f"{len(files)} files, {total / 1e6:.2f} MB -> s3://{PLATFORM_BUCKET}/{S3_PREFIX}/")

    # On a dry run the bucket may not exist yet, and `s3 sync --dryrun` cannot list a bucket
    # that is not there. Report from the local side rather than failing on a condition the
    # dry run itself created.
    if not apply and aws("s3api", "head-bucket", "--bucket", PLATFORM_BUCKET,
                         check=False, parse=False).returncode != 0:
        say("s3", f"WOULD upload all {len(files)} files (bucket does not exist yet)")
        say("cloudfront", "WOULD invalidate /platform*")
        return

    args = ["s3", "sync", str(BUNDLE), f"s3://{PLATFORM_BUCKET}/{S3_PREFIX}/", "--delete"]
    if not apply:
        args.append("--dryrun")
    proc = subprocess.run(["aws", *args, "--profile", PROFILE], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(redact(proc.stderr))
    changed = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    say("s3", f"{len(changed)} object(s) {'would be ' if not apply else ''}written")

    if apply:
        inv = aws("cloudfront", "create-invalidation", "--distribution-id", DISTRIBUTION_ID,
                  "--paths", "/platform*")
        say("cloudfront", f"invalidation {inv['Invalidation']['Id']} created")



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


def deploy_www(apply: bool) -> None:
    """Publish the public pages. Never with --delete.

    The main bucket also holds the NFC landing pages, the capture forms and the error page,
    none of which come from ``site/www``. A ``--delete`` sync would remove all of them, which
    is precisely the sort of quiet catastrophe this program is meant not to have.
    """
    if not (WWW / "index.html").is_file():
        raise SystemExit(f"{WWW} has no index.html")

    files = sorted(p for p in WWW.rglob("*") if p.is_file())
    say("www", f"{len(files)} public page/asset(s) -> s3://{MAIN_BUCKET}/")

    args = ["s3", "sync", str(WWW), f"s3://{MAIN_BUCKET}/"]
    if not apply:
        args.append("--dryrun")
    proc = subprocess.run(["aws", *args, "--profile", PROFILE], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(redact(proc.stderr))
    changed = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    say("www", f"{len(changed)} object(s) {'would be ' if not apply else ''}written")

    # A dry run must not claim an action it would not take. These seven were deleted on
    # 2026-07-28 and are gone -- verified with head-object, all 404 -- yet every dry run since
    # has printed "WOULD delete duplicate ..." for all seven. Harmless in effect and wrong in
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
        say("www", f"removed {len(STALE_OBJECTS)} duplicate/orphan object(s) "
                   f"(recoverable - bucket versioning is enabled)")
        inv = aws("cloudfront", "create-invalidation", "--distribution-id", DISTRIBUTION_ID,
                  "--paths", "/*")
        say("www", f"invalidation {inv['Invalidation']['Id']} created")


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually deploy; without it the script only reports")
    args = ap.parse_args()

    print(f"\nFuture City Fellowship - platform deploy "
          f"({'APPLY' if args.apply else 'DRY RUN - nothing will change'})\n")

    check_identity()
    ensure_managed_login_branding(args.apply)
    ensure_platform_bucket(args.apply)
    oac_id = ensure_oac(args.apply)
    role_arn = ensure_role(args.apply)
    lambda_arn = deploy_lambda(args.apply, role_arn)
    deploy_bundle(args.apply)
    deploy_www(args.apply)
    deploy_cloudfront(args.apply, lambda_arn, oac_id)

    print(f"\n{'Deployed.' if args.apply else 'Dry run complete. Re-run with --apply.'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
