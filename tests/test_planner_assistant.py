"""The planner assistant's Node tests, run from pytest so the usual test run covers them.

The tests live in platform/assistant/test (node:test). They check the server's request
validation, the spend ledger (concurrency, cap reached, settle), the rate limits, the request
handling with a fake model, the browser's payload builder against the Never tier, and the
answer checks. Node 22.18 or later runs the browser's TypeScript files directly.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TESTS = sorted((REPO / "platform/assistant/test").glob("*.test.mjs"))

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is required for the assistant tests")


def _node_strips_types() -> bool:
    out = subprocess.run(["node", "-p", "process.features.typescript ?? false"], capture_output=True, text=True, check=False)
    return out.stdout.strip() not in ("", "false", "undefined")


@pytest.mark.parametrize("path", TESTS, ids=[p.name for p in TESTS])
def test_assistant_node_suite(path: Path) -> None:
    if "payload" in path.name or "answer" in path.name:
        if not _node_strips_types():
            pytest.skip("this node cannot run TypeScript files directly")
    result = subprocess.run(
        ["node", "--test", "--test-reporter=tap", str(path)],
        cwd=REPO, capture_output=True, text=True, timeout=300, check=False,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]


def test_suite_is_present() -> None:
    assert len(TESTS) >= 5


def _edge_config():
    spec = importlib.util.spec_from_file_location("edge_config", REPO / "platform/assistant/deploy/edge_config.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_edge_config_adds_and_removes_the_assistant_behaviour() -> None:
    edge = _edge_config()
    live = json.loads((REPO / "platform/infra/distribution-config.json").read_text())
    domain = "abc123def456.lambda-url.us-east-2.on.aws"
    new = edge.transform({"ETag": "E1", "DistributionConfig": live}, domain, "E2ABCDEFGHIJK", remove=False)
    origins = {o["Id"]: o for o in new["Origins"]["Items"]}
    assert new["Origins"]["Quantity"] == len(new["Origins"]["Items"]) == len(live["Origins"]["Items"]) + 1
    lam = origins[edge.ORIGIN_ID]
    assert lam["DomainName"] == domain and lam["OriginAccessControlId"] == "E2ABCDEFGHIJK"
    assert lam["CustomOriginConfig"]["OriginProtocolPolicy"] == "https-only"
    first = new["CacheBehaviors"]["Items"][0]
    assert first["PathPattern"] == "/api/assistant/*"
    assert first["CachePolicyId"] == edge.CACHING_DISABLED
    assert first["OriginRequestPolicyId"] == edge.ALL_VIEWER_EXCEPT_HOST
    assert "POST" in first["AllowedMethods"]["Items"] and first["Compress"] is False
    assert first["FunctionAssociations"] == live["DefaultCacheBehavior"]["FunctionAssociations"]
    assert new["CacheBehaviors"]["Quantity"] == len(live["CacheBehaviors"]["Items"]) + 1
    # Everything else is untouched, and running it again changes nothing.
    for key in ("DefaultCacheBehavior", "CustomErrorResponses", "Aliases", "ViewerCertificate", "PriceClass"):
        assert new[key] == live[key]
    assert edge.transform(new, domain, "E2ABCDEFGHIJK", remove=False) == new
    assert edge.transform(new, None, None, remove=True) == live
    with pytest.raises(SystemExit):
        edge.transform(live, "evil.example.com", "E2ABCDEFGHIJK", remove=False)


def test_csp_already_allows_the_same_origin_api() -> None:
    js = (REPO / "platform/infra/headers-function.js").read_text()
    assert "\"connect-src 'self'" in js
