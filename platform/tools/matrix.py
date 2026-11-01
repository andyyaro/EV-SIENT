"""Device matrix for the EV-SIENT Planner: every screen at every window size, in Chromium and WebKit,
light and dark.

For each browser it walks the whole flow once with the Example City sample (the real engine by
default; --mock uses the recorded stand-in), then shows every screen at every size in both
appearances and checks:

  - no horizontal page scroll (the page is never wider than the window);
  - nothing is covered: every visible control, scrolled into view, is the topmost element at its
    centre, so neither the compact step bar nor the sidebar (nor anything else) sits over it;
  - tap targets: every control at least 24 by 24 px (WCAG 2.5.8; links inside a sentence are
    exempt), and primary controls (large buttons, Back and Continue, the step menu, the sidebar
    steps) at least 44 px tall;
  - no console errors or uncaught exceptions, and no requests to other sites.

Screenshots (JPEG, full page) go to <out-dir>/<browser>/<theme>/<width>x<height>-<screen>.jpg and the
findings to <out-dir>/matrix.json. Exits 1 when anything fails.

Usage:
  python3 platform/tools/matrix.py http://localhost:5184 /tmp/matrix            # real engine
  python3 platform/tools/matrix.py http://localhost:5184 /tmp/matrix --mock     # recorded stand-in
  options: --browsers chromium,webkit  --sizes 390x844,1440x900  --screens start,results  --no-shots
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

SIZES = ["320x640", "360x780", "390x844", "430x932", "844x390", "768x1024", "820x1180",
         "1024x768", "1366x1024", "1440x900", "1920x1080"]
THEMES = ["light", "dark"]

# Runs in the page: returns every problem on the current screen at the current size.
CHECK_JS = r"""
() => {
  const out = { hscroll: null, covered: [], small: [], primarySmall: [] };
  const doc = document.documentElement;
  if (doc.scrollWidth > window.innerWidth + 1) out.hscroll = { scrollWidth: doc.scrollWidth, innerWidth: window.innerWidth };

  const describe = (el) => {
    const name = (el.getAttribute('aria-label') || el.textContent || el.getAttribute('title') || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 50);
    return `${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''} "${name}"`;
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) return false;
    if (el.closest('.hig-visually-hidden, [hidden], [aria-hidden="true"]')) return false;
    return true;
  };
  // The control a tap actually lands on: a checkbox inside its label is measured as the label.
  // A list row's action button stretches its hit area over the whole row (hig.css ::before).
  const target = (el) => (el.matches('input[type=checkbox], input[type=radio]') && el.closest('label'))
    || (el.matches('.hig-list-row__action') && el.offsetParent) || el;
  const inSentence = (el) => {
    if (el.tagName !== 'A') return false;
    if (getComputedStyle(el).display !== 'inline') return false;
    const p = el.parentElement;
    return !!p && (p.textContent || '').trim().length > (el.textContent || '').trim().length + 3;
  };
  const PRIMARY = '.hig-button--large, .st-actions button, .app-compact select, .app-compact__brand, .nav-sidebar .hig-sidebar__row, .st-run__button';

  const controls = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button]')]
    .filter((el) => !el.closest('.maplibregl-map') || el.matches('.rs-marker'))
    .filter((el) => !el.matches('.skip-link')) // off screen until focused; a11y_audit.py checks it by keyboard
    .filter(visible);
  const startY = window.scrollY;
  for (const el of controls) {
    const t = target(el);
    const r0 = t.getBoundingClientRect();
    if (!inSentence(el) && (r0.width < 23.5 || r0.height < 23.5)) out.small.push(`${describe(el)} ${Math.round(r0.width)}x${Math.round(r0.height)}`);
    if (el.matches(PRIMARY) && r0.height < 43.5) out.primarySmall.push(`${describe(el)} ${Math.round(r0.width)}x${Math.round(r0.height)}`);

    // Fixed navigation is always in view; content is scrolled to the middle of the window first.
    if (!el.closest('.nav-sidebar, .app-compact')) t.scrollIntoView({ block: 'center', inline: 'nearest' });
    const r = t.getBoundingClientRect();
    const x = Math.min(Math.max(r.left + r.width / 2, 1), window.innerWidth - 2);
    const y = Math.min(Math.max(r.top + Math.min(r.height, window.innerHeight) / 2, 1), window.innerHeight - 2);
    const hit = document.elementFromPoint(x, y);
    const ok = hit && (t.contains(hit) || hit.contains(t) || (el.labels && [...el.labels].some((l) => l.contains(hit))));
    if (!ok) out.covered.push(`${describe(el)} under ${hit ? describe(hit) : 'nothing'}`);
  }
  window.scrollTo(0, startY);
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--mock", action="store_true", help="use the recorded Example City stand-in instead of the real engine")
    ap.add_argument("--browsers", default="chromium,webkit")
    ap.add_argument("--sizes", default=",".join(SIZES))
    ap.add_argument("--screens", default=",".join(pf.SCREENS))
    ap.add_argument("--themes", default=",".join(THEMES))
    ap.add_argument("--no-shots", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    origin = "{0.scheme}://{0.netloc}".format(urlparse(args.base))
    sizes = [tuple(int(n) for n in s.split("x")) for s in args.sizes.split(",")]
    screens = args.screens.split(",")
    themes = args.themes.split(",")
    results: list[dict] = []
    failures = 0

    with sync_playwright() as p:
        for name in args.browsers.split(","):
            browser = getattr(p, name).launch()
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            watch = pf.Watch(origin)
            watch.attach(page)
            timing = pf.run_flow(page, args.base, args.mock)
            print(f"== {name} {browser.version}: flow done {timing}", flush=True)
            for w, h in sizes:
                page.set_viewport_size({"width": w, "height": h})
                for theme in themes:
                    page.emulate_media(color_scheme=theme)
                    for screen in screens:
                        before = len(watch.errors)
                        pf.show(page, screen)
                        found = page.evaluate(CHECK_JS)
                        if screen == "compare":
                            page.locator("#rs-compare-title").scroll_into_view_if_needed()
                        if not args.no_shots:
                            shot = out / name / theme / f"{w}x{h}-{screen}.jpg"
                            shot.parent.mkdir(parents=True, exist_ok=True)
                            pf.screenshot(page, str(shot), full_page=screen != "compare", type="jpeg", quality=70)
                        errors = watch.errors[before:]
                        bad = bool(found["hscroll"] or found["covered"] or found["small"] or found["primarySmall"] or errors)
                        failures += bad
                        results.append({"browser": name, "theme": theme, "size": f"{w}x{h}", "screen": screen,
                                        "ok": not bad, **found, "errors": errors})
                        if bad:
                            print(f"  FAIL {name} {theme} {w}x{h} {screen}: "
                                  + json.dumps({k: v for k, v in {**found, "errors": errors}.items() if v}), flush=True)
            if watch.offsite:
                failures += 1
                print(f"  FAIL {name}: requests to other sites: {sorted(set(watch.offsite))}")
            results.append({"browser": name, "timing": timing, "offsite": sorted(set(watch.offsite)), "errors": watch.errors})
            browser.close()

    (out / "matrix.json").write_text(json.dumps(results, indent=1))
    checked = sum(1 for r in results if "screen" in r)
    print(f"{checked} screen checks, {failures} failing. Findings: {out / 'matrix.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
