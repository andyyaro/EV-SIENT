"""Accessibility audit of the EV-SIENT Planner: axe-core on every screen, increased contrast, and the
whole flow by keyboard.

  axe       Every screen (Start, Upload with the sample loaded, Map Columns, Check, Run, Results with
            a site selected and two sites in Compare, Report) in light and dark, and in the
            increased-contrast themes (prefers-contrast: more), in Chromium and WebKit, against
            WCAG 2.2 A and AA and axe's best practices. With --map, Results again after Show Map,
            checking the OpenFreeMap and OpenStreetMap credit is on the map.
  keyboard  Chromium only: from a fresh Start screen to a downloaded report using only Tab,
            Shift+Tab, Enter and Space. Fails on a control that cannot be reached, a focus trap,
            or a focused control with no visible focus indicator.

axe-core is not a dependency of the app: pass the path of axe.min.js from a scratch install
(npm install axe-core@4.13.0 in any folder outside the repository).

Usage:
  python3 platform/tools/a11y_audit.py http://localhost:5184 /tmp/a11y --axe /path/to/axe.min.js [--mock] [--map]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planner_flow as pf  # noqa: E402

AXE_SCREENS = ["start", "upload", "map", "check", "fill", "run", "results", "report"]
APPEARANCES = [("light", "no-preference"), ("dark", "no-preference"), ("light", "more"), ("dark", "more")]
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]


def run_axe(page, axe_path: str) -> dict:
    if not page.evaluate("typeof window.axe !== 'undefined'"):
        page.add_script_tag(path=axe_path)
    return page.evaluate(
        """async (tags) => {
            const r = await axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations', 'incomplete'] });
            const slim = (list) => list.map((v) => ({ id: v.id, impact: v.impact, help: v.help,
              nodes: v.nodes.map((n) => ({ target: n.target.join(' '), summary: (n.failureSummary || '').slice(0, 400),
                                           data: n.any && n.any[0] && n.any[0].data ? n.any[0].data : null })) }));
            return { violations: slim(r.violations), incomplete: slim(r.incomplete) };
        }""",
        TAGS,
    )


def axe_audit(p, args, origin: str, out: Path) -> tuple[list, int]:
    rows, violations = [], 0
    for name in args.browsers.split(","):
        browser = getattr(p, name).launch()
        # axe is injected as a script tag, which a deployed CSP rightly blocks; matrix.py checks the
        # app under its real CSP.
        page = browser.new_page(viewport={"width": 1440, "height": 900}, bypass_csp=True)
        watch = pf.Watch(origin)
        watch.attach(page)
        timing = pf.run_flow(page, args.base, args.mock)
        print(f"== axe {name} {browser.version}: flow done {timing}", flush=True)
        for size in args.sizes.split(","):
            w, h = (int(n) for n in size.split("x"))
            page.set_viewport_size({"width": w, "height": h})
            for scheme, contrast in APPEARANCES:
                page.emulate_media(color_scheme=scheme, contrast=contrast)
                theme = scheme + ("-hc" if contrast == "more" else "")
                for screen in AXE_SCREENS:
                    pf.show(page, screen)
                    got = page.evaluate("document.documentElement.dataset.theme")
                    r = run_axe(page, args.axe)
                    n = sum(len(v["nodes"]) for v in r["violations"])
                    violations += n
                    rows.append({"browser": name, "size": size, "theme": theme, "dataTheme": got, "screen": screen, **r})
                    tag = "ok" if not n else "FAIL " + ", ".join(f"{v['id']} x{len(v['nodes'])}" for v in r["violations"])
                    print(f"  {name} {size} {theme:8} {screen:8} {tag}", flush=True)
                    if args.shots and contrast == "more":
                        shot = out / "contrast" / name / f"{size}-{theme}-{screen}.jpg"
                        shot.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(shot), full_page=True, type="jpeg", quality=70)
        if args.map and name == args.browsers.split(",")[0]:
            page.set_viewport_size({"width": 1440, "height": 900})
            page.emulate_media(color_scheme="light", contrast="no-preference")
            pf.show(page, "results")
            page.get_by_role("button", name="Show Map", exact=True).click()
            page.locator(".maplibregl-ctrl-attrib").wait_for(timeout=30_000)
            page.wait_for_timeout(4000)
            credit = page.locator(".maplibregl-ctrl-attrib").inner_text()
            visible = page.locator(".maplibregl-ctrl-attrib-inner").is_visible()
            page.locator(".rs-map").screenshot(path=str(out / f"map-{name}.png"))
            r = run_axe(page, args.axe)
            n = sum(len(v["nodes"]) for v in r["violations"])
            violations += n
            rows.append({"browser": name, "size": "1440x900", "theme": "light", "screen": "results+map",
                         "credit": credit, "creditVisible": visible, **r})
            ok = visible and "OpenStreetMap" in credit and "OpenFreeMap" in credit
            violations += 0 if ok else 1
            print(f"  map credit visible={visible}: {credit!r} axe: {'ok' if not n else n}", flush=True)
        rows.append({"browser": name, "consoleErrors": watch.errors, "offsite": sorted(set(watch.offsite))})
        browser.close()
    return rows, violations


# ---------- Keyboard ----------

ACTIVE_JS = r"""
() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const cs = getComputedStyle(el);
  const before = getComputedStyle(el, '::before');
  const ring = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0)
    || (cs.boxShadow && cs.boxShadow !== 'none')
    || (before.outlineStyle !== 'none' && parseFloat(before.outlineWidth) > 0)
    || (el.closest('.st-inset-field') && getComputedStyle(el.closest('.st-inset-field')).boxShadow !== 'none');
  const r = el.getBoundingClientRect();
  const label = el.labels && el.labels.length ? el.labels[0].textContent : '';
  const name = (el.getAttribute('aria-label') || label || el.innerText || el.value || el.getAttribute('title') || '').trim().replace(/\s+/g, ' ');
  return { tag: el.tagName.toLowerCase(), name: name.slice(0, 80), cls: typeof el.className === 'string' ? el.className : '',
           ring, focusVisible: el.matches(':focus-visible'), inView: r.bottom > 0 && r.top < innerHeight && r.width > 0 };
}
"""


class Keyboard:
    def __init__(self, page):
        self.page = page
        self.stops: list[dict] = []
        self.problems: list[str] = []

    def tab_to(self, want: str, limit: int = 120, back: bool = False) -> dict:
        """Press Tab until the focused control's name starts with `want`."""
        seen = []
        for _ in range(limit):
            self.page.keyboard.press("Shift+Tab" if back else "Tab")
            a = self.page.evaluate(ACTIVE_JS)
            if not a:
                continue
            self.stops.append(a)
            if not a["ring"] and a["tag"] not in ("main",):
                self.problems.append(f"no visible focus indicator on {a['tag']} {a['name']!r}")
            if not a["inView"]:
                self.problems.append(f"focused control not scrolled into view: {a['tag']} {a['name']!r}")
            key = (a["tag"], a["name"], a["cls"])
            if a["name"].startswith(want):
                return a
            seen.append(key)
            if len(seen) > 12 and len(set(seen[-12:])) <= 2:
                raise AssertionError(f"focus trapped while looking for {want!r}: {seen[-3:]}")
        raise AssertionError(f"could not reach {want!r} with Tab in {limit} presses")

    def press(self, want: str, key: str = "Enter", **kw) -> None:
        self.tab_to(want, **kw)
        self.page.keyboard.press(key)
        self.page.wait_for_timeout(300)


def keyboard_audit(p, args, out: Path) -> tuple[dict, int]:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    page = context.new_page()
    kb = Keyboard(page)
    result: dict = {"steps": []}
    try:
        page.goto(pf.app_url(args.base, args.mock))
        page.locator("#main h1").wait_for()
        page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
        # The skip link comes first and shows when focused.
        page.keyboard.press("Tab")
        skip = page.evaluate("() => { const a = document.activeElement; const r = a.getBoundingClientRect(); return [a.textContent, r.top >= 0 && r.bottom <= innerHeight]; }")
        result["skipLink"] = skip
        if skip != ["Skip to Content", True]:
            kb.problems.append(f"skip link not first or not visible when focused: {skip}")

        kb.press("Try the Example City Sample")
        page.locator("#found-title").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
        result["steps"].append("Upload: sample loaded")
        kb.press("Continue to Map Columns")
        page.locator("#main h1", has_text="Map Columns").wait_for()
        if page.get_by_role("button", name="Accept All Matched", exact=True).count():
            kb.press("Accept All Matched")
        kb.press("Continue to Check")
        page.locator(".st-coverage").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
        result["steps"].append("Check")
        # Type a jurisdiction, as a planner would, in the source details.
        kb.tab_to("", limit=1)  # leave the heading
        for _ in range(200):
            a = page.evaluate(ACTIVE_JS)
            if a and a["tag"] == "input":
                break
            page.keyboard.press("Tab")
        page.keyboard.type("City of Example")
        kb.press("Continue to Run")
        page.locator("#main h1", has_text="Run").wait_for()
        kb.press("Run the Model")
        page.locator("#main h1", has_text="Results").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
        result["steps"].append("Results")
        # Choose a site with the arrow keys, add two to Compare with Space.
        kb.tab_to("Example City", limit=60)
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        selected = page.evaluate("document.querySelector('.rs-ranked button[aria-current=\"true\"] .rs-site__name')?.textContent")
        result["selectedByKeyboard"] = selected
        kb.press("Compare ", key="Space")
        kb.press("Compare ", key="Space")
        chosen = page.locator(".rs-ranked .rs-check input:checked").count()
        result["compareByKeyboard"] = chosen
        if chosen < 1:
            kb.problems.append("could not add a site to Compare by keyboard")
        # Go to Report through the sidebar: Shift+Tab back to the step list.
        kb.press("Report", back=True, limit=200)
        page.locator("#main h1", has_text="Report").wait_for()
        page.locator(".rp-sheet .rp").first.wait_for(timeout=120_000)
        result["steps"].append("Report")
        with page.expect_download(timeout=60_000) as dl:
            kb.press("Download .html")
        d = dl.value
        target = out / d.suggested_filename
        d.save_as(str(target))
        result["downloaded"] = d.suggested_filename
        result["downloadBytes"] = target.stat().st_size
        with page.expect_download(timeout=60_000) as dl2:
            kb.press("Download .evsient")
        result["projectFile"] = dl2.value.suggested_filename
    except Exception as e:  # noqa: BLE001
        kb.problems.append(f"flow stopped: {e}")
    result["tabStops"] = len(kb.stops)
    result["problems"] = sorted(set(kb.problems))
    page.screenshot(path=str(out / "keyboard-end.png"))
    browser.close()
    for prob in result["problems"]:
        print(f"  keyboard: {prob}")
    print(f"== keyboard: {result.get('steps')} downloaded {result.get('downloaded')} ({result.get('downloadBytes')} bytes), "
          f"project {result.get('projectFile')}, {result['tabStops']} tab stops, {len(result['problems'])} problems", flush=True)
    return result, len(result["problems"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--axe", required=True, help="path to axe.min.js")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--browsers", default="chromium,webkit")
    ap.add_argument("--sizes", default="1440x900,390x844")
    ap.add_argument("--map", action="store_true", help="also show the map (contacts tiles.openfreemap.org)")
    ap.add_argument("--shots", action="store_true", help="screenshots of the increased-contrast screens")
    ap.add_argument("--skip", default="", help="comma list: axe,keyboard")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    origin = "{0.scheme}://{0.netloc}".format(urlparse(args.base))
    skip = set(filter(None, args.skip.split(",")))
    report: dict = {}
    failures = 0
    with sync_playwright() as p:
        if "axe" not in skip:
            report["axe"], n = axe_audit(p, args, origin, out)
            failures += n
        if "keyboard" not in skip:
            report["keyboard"], n = keyboard_audit(p, args, out)
            failures += n
    (out / "a11y.json").write_text(json.dumps(report, indent=1))
    print(f"{failures} problems. Findings: {out / 'a11y.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
