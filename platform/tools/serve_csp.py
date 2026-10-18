"""Serve a built app directory with the production Content Security Policy, for local checks.

Every response carries the CSP the host sends, so a page or worker that needs more than it
allows (eval, a CDN, inline script) fails here the way it would in production. Files under
/runtime/ and /assets/ are content-addressed and sent as immutable, so a reload shows the warm
boot a returning planner gets.

Usage: python3 platform/tools/serve_csp.py platform/app/dist --port 5181
"""

from __future__ import annotations

import argparse
import functools
import http.server

CSP = ("default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self' blob:; "
       "connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
       "object-src 'none'; base-uri 'none'; frame-ancestors 'none'")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm",
                      ".json": "application/json", ".zip": "application/zip", ".whl": "application/zip"}

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
    args = ap.parse_args()
    handler = functools.partial(Handler, directory=args.root)
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"serving {args.root} on http://localhost:{args.port} with the production CSP", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
