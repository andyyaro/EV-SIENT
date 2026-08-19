"""The desktop tier's local server: serves the same UI, and can actually execute.

Why this is the common denominator
----------------------------------
Four platform architectures were designed independently, and every one of them needs exactly
this: something local that serves the web tier's files and can run an operation. It is the
Python-native angle's entire answer, the sidecar for a Tauri or Electron shell, and the
"companion" for the web-first angle. So it is built first, before the shell is chosen, and
none of that work is wasted whichever wins.

**One UI, two tiers.** The files served here are byte-identical to the ones deployed publicly
``site/platform/``. The only difference is that this server answers ``/api/*``, so the same
page shows the same operations list with the desktop-only entries *enabled*.

Security posture, and why it is what it is
------------------------------------------
A local HTTP server on a developer's machine is a real attack surface, and this one can
execute commands. So:

* **Loopback only.** Binds ``127.0.0.1``, never ``0.0.0.0``. Nothing on the network can reach it.
* **Ephemeral port**, printed at start. Not a well-known port another process can squat.
* **A per-session token**, generated at start and required on every ``/api/*`` request. Without
  it a browser tab you happen to have open on some other site cannot drive this server, which
  is the actual threat - a local server with no token is reachable by any page you visit.
* **No CORS headers.** The UI is same-origin; a cross-origin caller has no business here.
* **Operations only.** It can run what the registry declares and nothing else. There is no
  "run arbitrary command" endpoint, because there is no honest reason for one.

Stdlib only, deliberately. No FastAPI, no Flask, no uvicorn. Every dependency added here has
to be packaged into whatever desktop artifact ships, and ``http.server`` is already present in
any Python that can run the model at all.
"""

from __future__ import annotations

import json
import secrets
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import operations

REPO = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO / "site/platform"

#: Bound to loopback, always. Written as a constant so a well-meaning change to make it
#: "accessible from my phone" has to delete this comment first.
HOST = "127.0.0.1"


class PlatformHandler(SimpleHTTPRequestHandler):
    """Serves the web tier's files, plus a small API the desktop tier alone answers."""

    server_version = "FCFPlatform/1.0"
    token: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    # -- quieter logging: one line per request, not the stdlib's two ------------------
    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()} {fmt % args}")

    # -- the API ---------------------------------------------------------------------

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # Same-origin only. No Access-Control-Allow-Origin, on purpose.
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _authorised(self, query: dict) -> bool:
        supplied = (self.headers.get("X-Platform-Token")
                    or (query.get("token") or [""])[0])
        # Constant-time comparison. The token is short-lived, but a timing oracle on a
        # localhost endpoint is still a free win for an attacker and costs nothing to close.
        return secrets.compare_digest(supplied, self.token)

    def do_GET(self) -> None:                                    # noqa: N802 (stdlib name)
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return super().do_GET()

        query = parse_qs(parsed.query)
        if not self._authorised(query):
            return self._json(403, {"error": "missing or invalid session token"})

        if parsed.path == "/api/operations":
            return self._json(200, {
                "tier": operations.TIER_DESKTOP,
                "tier_note": ("This is the desktop tier. Everything here runs locally on "
                              "your machine."),
                "operations": operations.for_tier(operations.TIER_DESKTOP),
            })

        return self._json(404, {"error": f"no such endpoint: {parsed.path}"})

    def do_POST(self) -> None:                                   # noqa: N802 (stdlib name)
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if not self._authorised(query):
            return self._json(403, {"error": "missing or invalid session token"})

        if not parsed.path.startswith("/api/run/"):
            return self._json(404, {"error": f"no such endpoint: {parsed.path}"})

        operation_id = parsed.path[len("/api/run/"):]
        if operation_id not in operations.OPERATIONS_BY_ID:
            # Named explicitly rather than 404'd vaguely: the UI renders the registry, so an
            # unknown id means the UI and the registry have drifted, which is worth saying.
            return self._json(404, {
                "error": f"unknown operation {operation_id!r}",
                "known": sorted(operations.OPERATIONS_BY_ID),
            })

        try:
            result = operations.run(operation_id)
        except Exception as exc:                                  # noqa: BLE001
            # Report the failure. A silent 500 leaves the UI showing a spinner forever, and
            # "it didn't work" with no reason is the thing this project keeps refusing to ship.
            return self._json(500, {"operation": operation_id, "error": str(exc)})

        return self._json(200 if result.ok else 400, {
            "operation": result.operation_id,
            "ok": result.ok,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })


def serve(port: int = 0, open_browser: bool = False) -> tuple[ThreadingHTTPServer, str, str]:
    """Start the local server. Returns (server, url, token).

    ``port=0`` asks the OS for a free ephemeral port, which is the right default: a fixed
    port is one another process can already be holding, and one an attacker can predict.
    """
    if not WEB_ROOT.is_dir():
        raise SystemExit(
            f"{WEB_ROOT} does not exist. Build the web tier first:\n"
            f"    python scripts/build_platform_web.py")

    token = secrets.token_urlsafe(32)
    handler = type("BoundHandler", (PlatformHandler,), {"token": token})
    httpd = ThreadingHTTPServer((HOST, port), handler)
    actual_port = httpd.server_address[1]
    url = f"http://{HOST}:{actual_port}/index.html?token={token}"

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    if open_browser:
        import webbrowser
        webbrowser.open(url)
    return httpd, url, token


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Serve the platform locally (desktop tier).")
    ap.add_argument("--port", type=int, default=0, help="0 asks the OS for a free port")
    ap.add_argument("--open", action="store_true", help="open a browser at the URL")
    args = ap.parse_args()

    httpd, url, _token = serve(port=args.port, open_browser=args.open)
    print("Future City Fellowship - platform, desktop tier")
    print(f"  serving {WEB_ROOT.relative_to(REPO)}")
    print(f"  {url}")
    print("  bound to loopback only; the token above is required for every API call")
    print("  Ctrl-C to stop")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n  stopping")
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
