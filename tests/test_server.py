"""The desktop tier's local server serves the same UI, executes only what is declared, and
cannot be driven by a page you happen to have open somewhere else.

The threat that shapes this file
--------------------------------
A local HTTP server that can execute commands is reachable by **any web page in your
browser**, not just the one you opened deliberately. Loopback is not a security boundary
against that: `http://127.0.0.1:PORT` is a perfectly ordinary URL for a script on any site to
fetch. The token is what closes it, so the token behaviour is tested harder than the features.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import operations as ops, server  # noqa: E402


@pytest.fixture(scope="module")
def live():
    httpd, url, token = server.serve(port=0)
    base = url.split("/index.html")[0]
    yield base, token
    httpd.shutdown()


def call(base, path, token=None, method="GET"):
    req = urllib.request.Request(f"{base}{path}", method=method)
    if token:
        req.add_header("X-Platform-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


# ------------------------------------------------------------------ the token

def test_the_api_refuses_with_no_token(live):
    base, _ = live
    status, body = call(base, "/api/operations")
    assert status == 403 and "token" in body["error"]


def test_the_api_refuses_a_wrong_token(live):
    base, _ = live
    status, body = call(base, "/api/operations", "not-the-token")
    assert status == 403


def test_the_api_refuses_an_empty_token(live):
    base, _ = live
    status, _ = call(base, "/api/operations", "")
    assert status == 403


def test_running_an_operation_also_requires_the_token(live):
    """The read endpoint being protected is not enough — execution is the dangerous one."""
    base, _ = live
    status, _ = call(base, "/api/run/validate-contract-v1", None, "POST")
    assert status == 403


def test_the_token_is_long_enough_to_be_unguessable():
    _httpd, _url, token = server.serve(port=0)
    _httpd.shutdown()
    assert len(token) >= 32, "a short token on a local execution endpoint is not a token"


def test_two_servers_get_different_tokens():
    """A fixed or derived token would be as good as none — every session must be its own."""
    a_httpd, _u, a = server.serve(port=0)
    b_httpd, _u2, b = server.serve(port=0)
    a_httpd.shutdown(); b_httpd.shutdown()
    assert a != b


# ------------------------------------------------------------------ the binding

def test_it_binds_loopback_only():
    """0.0.0.0 would put an execution endpoint on the network. The constant exists so that
    change cannot be made casually."""
    assert server.HOST == "127.0.0.1"
    source = (REPO / "src/fcf_m2/server.py").read_text()
    assert '"0.0.0.0"' not in source and "'0.0.0.0'" not in source


def test_it_takes_an_ephemeral_port_by_default():
    import inspect
    assert inspect.signature(server.serve).parameters["port"].default == 0


def test_it_sends_no_cors_header(live):
    """A cross-origin caller has no business here. An Access-Control-Allow-Origin header
    would hand the execution API to any site that asks."""
    base, token = live
    req = urllib.request.Request(f"{base}/api/operations")
    req.add_header("X-Platform-Token", token)
    with urllib.request.urlopen(req, timeout=30) as r:
        assert r.headers.get("Access-Control-Allow-Origin") is None
        assert r.headers.get("X-Content-Type-Options") == "nosniff"


# ------------------------------------------------------------------ what it will run

def test_it_lists_the_registry_and_nothing_else(live):
    base, token = live
    status, body = call(base, "/api/operations", token)
    assert status == 200
    assert body["tier"] == ops.TIER_DESKTOP
    assert body["operations"] == ops.for_tier(ops.TIER_DESKTOP)


def test_the_desktop_tier_can_run_everything_it_lists(live):
    base, token = live
    _status, body = call(base, "/api/operations", token)
    assert all(entry["available"] for entry in body["operations"])


def test_it_runs_a_declared_operation_and_returns_its_real_output(live):
    base, token = live
    status, body = call(base, "/api/run/validate-contract-v1", token, "POST")
    assert status == 200 and body["ok"] is True
    assert "Contract v1.0.0 valid" in body["stdout"]


def test_it_refuses_an_operation_that_is_not_in_the_registry(live):
    """There is no 'run arbitrary command' endpoint, because there is no honest reason for
    one. Anything not declared is refused by name."""
    base, token = live
    status, body = call(base, "/api/run/rm%20-rf%20/", token, "POST")
    assert status == 404 and "unknown operation" in body["error"]
    assert "known" in body, "the refusal should say what IS available"


def test_it_refuses_an_unknown_endpoint(live):
    base, token = live
    status, body = call(base, "/api/anything", token)
    assert status == 404 and "no such endpoint" in body["error"]


# ------------------------------------------------------------------ one UI, two tiers

def test_it_serves_the_same_files_the_web_tier_serves(live):
    """Byte-identical, not merely similar. Two copies of the UI would drift."""
    base, _ = live
    with urllib.request.urlopen(f"{base}/index.html", timeout=30) as r:
        served = r.read()
    assert served == (REPO / "site/platform/index.html").read_bytes()


def test_static_files_do_not_require_the_token(live):
    """They are published publicly anyway; requiring a token would only break the page."""
    base, _ = live
    with urllib.request.urlopen(f"{base}/app.js", timeout=30) as r:
        assert r.status == 200


def test_it_depends_on_nothing_outside_the_standard_library():
    """Every dependency here has to be packaged into whatever desktop artifact ships.

    Checked by parsing the IMPORTS, not by searching the text. The first version of this test
    lowercased the file and looked for "flask" — and failed on the docstring sentence "No
    FastAPI, no Flask, no uvicorn", which is the prose explaining they are *not* used. Sixth
    time in this program a check has matched text where structure was what mattered.
    """
    import ast
    tree = ast.parse((REPO / "src/fcf_m2/server.py").read_text())

    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:                       # relative import: our own package
                continue
            if node.module:
                roots.add(node.module.split(".")[0])

    allowed_stdlib = set(sys.stdlib_module_names)
    outside = sorted(r for r in roots if r not in allowed_stdlib)
    assert outside == [], (
        f"server.py imports non-stdlib module(s): {outside}. Everything here must be "
        f"packageable into the desktop artifact without adding a dependency.")


def test_the_only_project_import_is_the_operations_registry():
    """The server orchestrates; it must not reach into the model. If it imported scoring or
    the contract directly it would become a second execution path."""
    import ast
    tree = ast.parse((REPO / "src/fcf_m2/server.py").read_text())
    relative = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.level
                for alias in node.names}
    assert relative == {"operations"}, (
        f"server.py imports {sorted(relative)} from the package; it should orchestrate "
        f"through the operations registry alone")
