"""Boot the worker engine in real browsers and run Example City end to end.

Opens engine-check.html (the dev-only harness) in Chromium and WebKit through Playwright, once
in a fresh profile (a cold boot, nothing cached) and once more after a reload (a warm boot),
and prints the boot and run timings, the engine's refusals as the page received them, and every
console error or Content Security Policy violation. Exits non-zero if a run fails or any CSP
violation is seen.

Usage:
  python3 platform/tools/browser_check.py --base http://localhost:5181          # vite dev
  python3 platform/tools/browser_check.py --base http://localhost:5182 --cancel # built, with CSP
"""

from __future__ import annotations

import argparse
import json
import sys

from playwright.sync_api import sync_playwright

WATCH_CSP = """
document.addEventListener('securitypolicyviolation', (e) => {
  (window.__csp = window.__csp || []).push(`${e.violatedDirective} blocked ${e.blockedURI}`);
});
"""


def one_load(page, url: str) -> dict:
    page.goto(url)
    # Polled from here rather than with wait_for_function, whose predicate is compiled inside
    # the page and so is itself refused by a CSP without 'unsafe-eval'.
    for _ in range(960):
        if page.evaluate("window.__engineCheck !== undefined"):
            break
        page.wait_for_timeout(250)
    else:
        raise TimeoutError(f"{url} did not finish in 4 minutes")
    return page.evaluate("({check: window.__engineCheck, csp: window.__csp || []})")


def check_browser(p, name: str, base: str, cancel: bool) -> dict:
    browser = getattr(p, name).launch()
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(WATCH_CSP)
    console: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
    url = f"{base}/engine-check.html" + ("?cancel=1" if cancel else "")
    cold = one_load(page, url)
    warm = one_load(page, url)
    version = browser.version
    browser.close()
    csp = cold["csp"] + warm["csp"] + [c for c in console if "Content Security Policy" in c or "Refused to" in c]
    return {"browser": f"{name} {version}", "cold": cold["check"], "warm": warm["check"], "console": console, "csp": csp}


def summary(r: dict) -> str:
    lines = [f"== {r['browser']}"]
    for label in ("cold", "warm"):
        c = r[label]
        if not c["ok"]:
            lines.append(f"  {label}: FAILED {c['error']}")
            continue
        res = c["result"]
        t = res["info"]["timingsMs"]
        lines.append(f"  {label}: boot {res['bootMs']} ms (runtime {t['runtime']}, packages {t['packages']}, "
                     f"engine {t['engine']}), run {res['runMs']} ms (engine {res['engineElapsedSec']} s), "
                     f"{len(res['ranking'])} sites, counts {res['counts']}")
    res = r["cold"].get("result") or {}
    if res:
        lines.append(f"  engine {res['info']['engine']['version']} on Pyodide {res['info']['pyodide']}, "
                     f"Python {res['info']['python']}, {res['info']['packages']}")
        lines.append(f"  ranking {res['ranking']}")
        lines.append(f"  explain sums {res['explainSums']}")
        for x in res["refusals"]:
            lines.append(f"  refusal [{x['label']}]: {x.get('name')}: {x.get('message')}")
        if "cancel" in res:
            lines.append(f"  cancel: {res['cancel']}; after: {res['afterCancel']}")
    lines.append(f"  CSP violations: {r['csp'] or 'none'}")
    other = [c for c in r["console"] if c not in r["csp"]]
    if other:
        lines.append("  console errors/warnings:\n    " + "\n    ".join(c[:300] for c in other))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--browsers", nargs="+", default=["chromium", "webkit"])
    ap.add_argument("--cancel", action="store_true", help="also stop a run mid-way and run again")
    ap.add_argument("--json", help="write the full results here")
    args = ap.parse_args()
    results = []
    with sync_playwright() as p:
        for name in args.browsers:
            r = check_browser(p, name, args.base.rstrip("/"), args.cancel)
            results.append(r)
            print(summary(r), flush=True)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=1)
    bad = [r for r in results if not (r["cold"]["ok"] and r["warm"]["ok"]) or r["csp"]]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
