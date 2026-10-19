"""Install and offline check for a built planner, in Chromium and WebKit through Playwright.

For each browser, in a fresh profile:

  1. the manifest is linked, parses, names the app and its icons load at their stated sizes
     (Chromium also asks the browser itself for installability errors);
  2. the service worker registers at /sw.js and holds the whole app shell;
  3. the whole flow runs online on Example City with the real engine (planner_flow.run_flow);
  4. the worker then holds every runtime file, stored decoded: no Content-Encoding header and the
     file's own length, which is what goes wrong when CloudFront's Brotli objects are cached as-is;
  5. the server is stopped, the page reloads, and the whole flow runs again with the real engine.

It serves the build itself, with serve_csp.py (the production CSP, large assets Brotli-encoded as
CloudFront sends them), so that "offline" can mean what it means to a planner: the origin cannot
be reached. Playwright's offline emulation is not enough in WebKit, where it also fails loads the
service worker answers from its cache; Chromium gets both. Any CSP violation, console error or
request to another site fails the check.

Usage:
  python3 platform/tools/offline_check.py platform/app/dist [--port 5277] [--browsers chromium,webkit]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planner_flow as pf  # noqa: E402

WATCH_CSP = """
document.addEventListener('securitypolicyviolation', (e) => {
  (window.__csp = window.__csp || []).push(`${e.violatedDirective} blocked ${e.blockedURI}`);
});
"""

MANIFEST_JS = """async () => {
  const link = document.querySelector('link[rel=manifest]');
  if (!link) return { error: 'no <link rel=manifest>' };
  const m = await (await fetch(link.href)).json();
  const icons = [];
  for (const icon of m.icons || []) {
    const img = new Image();
    img.src = new URL(icon.src, link.href).href;
    try { await img.decode(); icons.push({ ...icon, width: img.naturalWidth, height: img.naturalHeight }); }
    catch { icons.push({ ...icon, error: 'did not load' }); }
  }
  return { name: m.name, short_name: m.short_name, start_url: m.start_url, display: m.display,
           theme_color: m.theme_color, background_color: m.background_color, icons };
}"""

CACHES_JS = """async () => {
  const out = {};
  for (const name of await caches.keys()) out[name] = (await (await caches.open(name)).keys()).map((r) => new URL(r.url).pathname);
  return out;
}"""

STORED_JS = """async (path) => {
  const r = await caches.match(path);
  if (!r) return null;
  return { encoding: r.headers.get('content-encoding'), length: r.headers.get('content-length'),
           type: r.headers.get('content-type'), bytes: (await r.arrayBuffer()).byteLength };
}"""


def sw_manifest(base: str) -> dict:
    source = urllib.request.urlopen(f"{base}/sw.js").read().decode()
    return json.loads(re.search(r"const MANIFEST = (\{.*?\});\n", source).group(1))


def wait_for(page, js: str, test, what: str, timeout_s: float = 120):
    end = time.time() + timeout_s
    while time.time() < end:
        value = page.evaluate(js)
        if test(value):
            return value
        page.wait_for_timeout(500)
    raise TimeoutError(f"timed out waiting for {what}: last {value!r}")


class Server:
    """serve_csp.py on 127.0.0.1, started and stopped by the check."""

    def __init__(self, root: str, port: int) -> None:
        self.args = [sys.executable, str(Path(__file__).with_name("serve_csp.py")), root, "--port", str(port), "--brotli"]
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        self.proc = subprocess.Popen(self.args, stdout=subprocess.PIPE, text=True)
        self.proc.stdout.readline()                  # its "serving ..." line: listening now

    def stop(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None


def check_browser(p, name: str, base: str, manifest: dict, root: str, server: Server) -> dict:
    problems: list[str] = []
    browser = p[name].launch()
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(WATCH_CSP)
    watch = pf.Watch(origin=base)
    watch.attach(page)
    result: dict = {"browser": f"{name} {browser.version}"}
    try:
        page.goto(base + "/")
        m = page.evaluate(MANIFEST_JS)
        result["manifest"] = m
        if m.get("error") or m.get("name") != "EV-SIENT Planner" or m.get("display") != "standalone":
            problems.append(f"manifest: {m}")
        for icon in m.get("icons", []):
            stated = icon.get("sizes", "")
            if icon.get("error") or (stated != "any" and stated != f"{icon.get('width')}x{icon.get('height')}"):
                problems.append(f"icon {icon['src']}: {icon}")
        if name == "chromium":
            cdp = context.new_cdp_session(page)
            errors = cdp.send("Page.getInstallabilityErrors").get("installabilityErrors", [])
            result["installability_errors"] = errors
            if errors:
                problems.append(f"Chromium installability errors: {errors}")

        state = wait_for(page, "navigator.serviceWorker.ready.then((r) => r.active && r.active.state)",
                         lambda v: v == "activated", "the service worker to activate")
        result["service_worker"] = state

        timings = pf.run_flow(page, base, mock=False)
        result["online"] = timings
        shell_name = f"evsient-shell-{manifest['version']}"
        cached = wait_for(page, CACHES_JS,
                          lambda c: len(c.get("evsient-runtime", [])) >= len(manifest["runtime"])
                          and len(c.get(shell_name, [])) >= len(manifest["shell"]),
                          "the shell and runtime to be cached", timeout_s=180)
        result["cached"] = {k: len(v) for k, v in cached.items()}
        sizes = {"/" + u: (Path(root) / u).stat().st_size for u in manifest["runtime"]}
        for path in ["/runtime/pyodide/314.0.7/pyodide.asm.wasm", "/runtime/pyodide/314.0.7/pyodide.asm.mjs",
                     "/" + next(u for u in manifest["runtime"] if u.startswith("runtime/engine/"))]:
            stored = page.evaluate(STORED_JS, path)
            result.setdefault("stored", {})[path] = stored
            if not stored or stored["encoding"] or (path in sizes and stored["bytes"] != sizes[path]):
                problems.append(f"{path} stored wrongly: {stored} (file is {sizes.get(path)} bytes)")

        server.stop()
        if name == "chromium":
            context.set_offline(True)
        page.reload()
        timings = pf.run_flow(page, base, mock=False)
        result["offline"] = timings
        result["offline_controlled"] = page.evaluate("!!navigator.serviceWorker.controller")
    except Exception as e:  # report it with whatever else was found
        problems.append(f"{type(e).__name__}: {str(e)[:400]}")
    result["csp"] = page.evaluate("window.__csp || []") if not page.is_closed() else []
    problems += [f"CSP: {c}" for c in result["csp"]]
    problems += watch.errors + [f"offsite request: {u}" for u in watch.offsite]
    result["problems"] = problems
    browser.close()
    return result



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="the built app, e.g. platform/app/dist")
    ap.add_argument("--port", type=int, default=5277)
    ap.add_argument("--browsers", default="chromium,webkit")
    ap.add_argument("--json", help="write the full results here")
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    server = Server(args.root, args.port)
    results = []
    with sync_playwright() as p:
        browsers = {"chromium": p.chromium, "webkit": p.webkit, "firefox": p.firefox}
        for name in args.browsers.split(","):
            server.start()
            try:
                manifest = sw_manifest(base)
                r = check_browser(browsers, name, base, manifest, args.root, server)
            finally:
                server.stop()
            results.append(r)
            print(f"== {r['browser']}")
            for key in ("service_worker", "installability_errors", "online", "cached", "offline", "offline_controlled"):
                if key in r:
                    print(f"  {key}: {r[key]}")
            print("  " + ("OK" if not r["problems"] else "PROBLEMS:\n    " + "\n    ".join(r["problems"])), flush=True)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
    return 1 if any(r["problems"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
