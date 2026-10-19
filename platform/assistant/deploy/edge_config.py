#!/usr/bin/env python3
"""Add (or remove) the assistant's origin and /api/assistant/* behaviour in a CloudFront config.

Makes no AWS calls. It reads the JSON that `aws cloudfront get-distribution-config` printed,
and writes the DistributionConfig to pass to `update-distribution`, for review first:

    aws cloudfront get-distribution-config --id E1JXKS26TDP3Z2 --profile future-city > live.json
    python3 deploy/edge_config.py live.json --domain <FunctionUrlDomain> --oac <OriginAccessControlId> > new.json
    diff <(python3 -m json.tool live.json) <(python3 -m json.tool new.json)   # review
    aws cloudfront update-distribution --id E1JXKS26TDP3Z2 --if-match <ETag from live.json> \
        --distribution-config file://new.json --profile future-city

`--remove` takes the behaviour and origin out again (turning the assistant off at the edge).
Running it twice gives the same result. Keep live.json and new.json out of the repository:
they hold the account ID.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys

ORIGIN_ID = "lambda-evsient-assistant"
PATH = "/api/assistant/*"
# AWS managed policies (the flat-rate plans allow only managed ones).
CACHING_DISABLED = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
ALL_VIEWER_EXCEPT_HOST = "b689b0a8-53d0-40ab-baf2-68738e2966ac"


def origin(domain: str, oac: str) -> dict:
    return {
        "Id": ORIGIN_ID,
        "DomainName": domain,
        "OriginPath": "",
        "CustomHeaders": {"Quantity": 0},
        "CustomOriginConfig": {
            "HTTPPort": 80,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "https-only",
            "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]},
            # A streamed answer can pause while the model thinks; 60 s is the most allowed
            # without a quota increase, and the function itself stops at 45 s.
            "OriginReadTimeout": 60,
            "OriginKeepaliveTimeout": 5,
        },
        "OriginAccessControlId": oac,
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10,
        "OriginShield": {"Enabled": False},
    }


def behaviour(function_arn: str) -> dict:
    return {
        "PathPattern": PATH,
        "TargetOriginId": ORIGIN_ID,
        "ViewerProtocolPolicy": "https-only",
        "AllowedMethods": {
            "Quantity": 7,
            "Items": ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"],
            "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
        },
        # No compression: it would hold back a streamed answer.
        "Compress": False,
        "CachePolicyId": CACHING_DISABLED,
        "OriginRequestPolicyId": ALL_VIEWER_EXCEPT_HOST,
        "FunctionAssociations": {"Quantity": 1, "Items": [{"EventType": "viewer-response", "FunctionARN": function_arn}]},
        "LambdaFunctionAssociations": {"Quantity": 0},
        "TrustedSigners": {"Enabled": False, "Quantity": 0},
        "TrustedKeyGroups": {"Enabled": False, "Quantity": 0},
        "FieldLevelEncryptionId": "",
        "SmoothStreaming": False,
    }


def _set(items: list, quantity_holder: dict) -> None:
    quantity_holder["Items"] = items
    quantity_holder["Quantity"] = len(items)


def transform(live: dict, domain: str | None, oac: str | None, remove: bool) -> dict:
    cfg = copy.deepcopy(live.get("DistributionConfig", live))
    origins = [o for o in cfg["Origins"]["Items"] if o["Id"] != ORIGIN_ID]
    behaviours = [b for b in cfg.get("CacheBehaviors", {}).get("Items", []) if b["PathPattern"] != PATH]
    if not remove:
        if not domain or not re.fullmatch(r"[a-z0-9]+\.lambda-url\.[a-z0-9-]+\.on\.aws", domain):
            raise SystemExit("--domain must be the function URL's host, like abc123.lambda-url.us-east-2.on.aws")
        if not oac or not re.fullmatch(r"[A-Z0-9]{8,20}", oac):
            raise SystemExit("--oac must be the origin access control ID from the stack outputs")
        # The headers function (and its CSP) is the one the default behaviour uses.
        assoc = cfg["DefaultCacheBehavior"].get("FunctionAssociations", {}).get("Items", [])
        arn = next((a["FunctionARN"] for a in assoc if a["EventType"] == "viewer-response"), None)
        if not arn:
            raise SystemExit("the default behaviour has no viewer-response function to reuse")
        origins.append(origin(domain, oac))
        # First in the list, so it wins over any broader pattern added later.
        behaviours.insert(0, behaviour(arn))
    _set(origins, cfg["Origins"])
    cfg.setdefault("CacheBehaviors", {})
    _set(behaviours, cfg["CacheBehaviors"])
    return cfg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("live", help="output of get-distribution-config (or a bare DistributionConfig)")
    p.add_argument("--domain", help="FunctionUrlDomain from the stack outputs")
    p.add_argument("--oac", help="OriginAccessControlId from the stack outputs")
    p.add_argument("--remove", action="store_true", help="take the assistant out of the config")
    a = p.parse_args(argv)
    with open(a.live, encoding="utf-8") as f:
        live = json.load(f)
    if "ETag" in live:
        print(f"ETag for --if-match: {live['ETag']}", file=sys.stderr)
    json.dump(transform(live, a.domain, a.oac, a.remove), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
