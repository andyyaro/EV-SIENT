"""Serve a built app directory with the production Content Security Policy, for local checks.

Every response carries the CSP the host sends, so a page or worker that needs more than it
allows (eval, a CDN, inline script) fails here the way it would in production. Files under
/runtime/ and /assets/ are content-addressed and sent as immutable, so a reload shows the warm
boot a returning planner gets.

With --brotli, files under /assets/ and /runtime/ of 1 MB or more with a compressible type are
sent Brotli-compressed with Content-Encoding: br, whatever the request accepts, as deploy.sh
uploads them and CloudFront passes them through. That is the case the service worker must cache
correctly (needs the brotli command).

Usage: python3 platform/tools/serve_csp.py platform/app/dist --port 5181 [--brotli]
"""

from __future__ import annotations

import argparse
import functools
import http.server
import subprocess
from pathlib import Path

# The production policy (platform/infra/headers-function.js) less the map tile host, so a test
# also proves that nothing but the app's own origin is needed, and less the HTTPS upgrade, which
# a plain-HTTP local server cannot answer.
CSP = ("default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; "
       "connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
       "font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; "
       "frame-ancestors 'none'")

BROTLI_MIN_BYTES = 1_000_000
BROTLI_TYPES = {".wasm", ".mjs", ".js", ".json", ".css", ".svg", ".html", ".txt", ".csv", ".xml"}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm",
                      ".json": "application/json", ".zip": "application/zip", ".whl": "application/zip",
                      ".webmanifest": "application/manifest+json"}
    brotli = False
    compressed: dict[str, bytes] = {}

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        local = Path(self.translate_path(path))
        if (self.brotli and path.startswith(("/assets/", "/runtime/")) and local.is_file()
                and local.suffix in BROTLI_TYPES and local.stat().st_size >= BROTLI_MIN_BYTES):
            body = self.compressed.get(path)
            if body is None:
                body = subprocess.run(["brotli", "-q", "11", "-c", str(local)], check=True,
                                      capture_output=True).stdout
                self.compressed[path] = body
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(str(local)))
            self.send_header("Content-Encoding", "br")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass                                 # the page went away mid-download
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        if self.path.startswith(("/runtime/pyodide/", "/assets/")) or "/engine-" in self.path:
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--port", type=int, default=5181)
    ap.add_argument("--brotli", action="store_true", help="send large assets Brotli-encoded, as CloudFront does")
    args = ap.parse_args()
    Handler.brotli = args.brotli
    handler = functools.partial(Handler, directory=args.root)
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"serving {args.root} on http://localhost:{args.port} with the production CSP"
              + (", large assets Brotli-encoded" if args.brotli else ""), flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
