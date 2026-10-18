"""Device-matrix QA for the redesign: every page x every viewport, Chromium and WebKit, light and dark.
Usage: python3 matrix.py BASE_URL OUT_DIR [--shots]
Reports horizontal overflow, console errors, failed requests, nav layout per width, and whether the
bottom tab bar hides the end of the page. Screenshots (with --shots) go to OUT_DIR/<engine>/<scheme>/."""
import sys, os, json
from playwright.sync_api import sync_playwright

BASE, OUT = sys.argv[1].rstrip('/'), sys.argv[2]
SHOTS = '--shots' in sys.argv
PAGES = ['index.html', 'sites.html', 'sites.html#FFX004', 'sites.html#PWC002', 'compare.html', 'outlook.html', 'explore.html', 'method.html',
         'standards.html', 'assistant.html', 'about.html', 'privacy.html', 'more.html', '404.html', 'devices.html']
VIEWPORTS = [(320, 640), (360, 780), (375, 667), (390, 844), (430, 932), (844, 390), (932, 430),
             (744, 1133), (768, 1024), (820, 1180), (834, 1194), (1024, 768), (1180, 820), (1366, 1024),
             (1440, 900), (1920, 1080)]
if os.environ.get('MATRIX_PAGES'):
    PAGES = os.environ['MATRIX_PAGES'].split(',')
if os.environ.get('MATRIX_QUICK'):
    VIEWPORTS = [(320, 640), (390, 844), (844, 390), (820, 1180), (1024, 768), (1440, 900)]
SHOT_VP = {(320, 640), (390, 844), (844, 390), (820, 1180), (1024, 768), (1180, 820), (1440, 900), (1920, 1080)}

PROBE = """() => {
  const de = document.documentElement, vw = de.clientWidth;
  const over = [];
  if (de.scrollWidth > vw + 1) {
    document.querySelectorAll('body *').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width && r.right > vw + 1) {
        let p = el.parentElement, clipped = false;
        while (p && p !== document.body) { const s = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) { clipped = true; break; } p = p.parentElement; }
        if (!clipped) over.push((el.tagName + '.' + (el.className && el.className.baseVal === undefined ? el.className : '')).slice(0, 70) + ' r=' + Math.round(r.right));
      }
    });
  }
  const side = document.querySelector('.nav-sidebar'), tab = document.querySelector('.nav-tabbar');
  const vis = el => !!el && getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().width > 0;
  const foot = document.querySelector('.site-foot');
  let footCovered = null;
  if (foot && vis(tab)) {
    de.style.scrollBehavior='auto'; window.scrollTo({top: de.scrollHeight, behavior: 'instant'});
    const fr = foot.getBoundingClientRect(), tr = tab.querySelector('.hig-tab-bar__tabs').getBoundingClientRect();
    footCovered = fr.bottom > tr.top + 1;
    window.scrollTo({top: 0, behavior: 'instant'});
  }
  const tiny = [];
  document.querySelectorAll('a, button, [role=tab], [role=radio], select, input').forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width || getComputedStyle(el).visibility === 'hidden') return;
    if (el.closest('.prose, p, li .footnote, .site-foot, .footnote, td, .dv-caption')) return;  // inline text links are exempt (WCAG 2.5.8)
    if (r.width < 24 || r.height < 24) {
      // A design-system row or card can stretch the link over the whole row with a pseudo-element; hit-test it.
      const row = el.closest('li, .hig-list-row, .card, [class*="row"], [class*="card"]');
      if (row) {
        const rr = row.getBoundingClientRect(), x = r.left + Math.min(r.width / 2, 8);
        el.scrollIntoView({block: 'center', behavior: 'instant'});
        const rr2 = row.getBoundingClientRect(), r2 = el.getBoundingClientRect();
        const pts = [[r2.left + 4, rr2.top + 3], [r2.left + 4, rr2.bottom - 3]];
        const ok = rr2.height >= 24 && pts.every(([px, py]) => { const h = document.elementFromPoint(px, py); return h && (h === el || el.contains(h)); });
        if (ok) return;
      }
    }
    if (r.width < 24 || r.height < 24) tiny.push((el.tagName + ' ' + (el.textContent || el.getAttribute('aria-label') || '').trim()).slice(0, 40) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  return { sw: de.scrollWidth, vw, over: over.slice(0, 6), side: vis(side), tab: vis(tab), footCovered, tiny: tiny.slice(0, 6), h1: document.querySelectorAll('h1').length };
}"""

report = []
with sync_playwright() as p:
    for eng_name in ('chromium', 'webkit'):
        browser = getattr(p, eng_name).launch()
        for scheme in ('light', 'dark'):
            for (w, h) in VIEWPORTS:
                ctx = browser.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme, device_scale_factor=1,
                                          has_touch=w < 1024, is_mobile=False)
                page = ctx.new_page()
                errs, fails = [], []
                page.on('console', lambda m: errs.append(m.text[:160]) if m.type == 'error' else None)
                page.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)[:160]))
                page.on('requestfailed', lambda r: fails.append(r.url[-80:]) if 'tableau' not in r.url else None)
                for path in PAGES:
                    errs.clear(); fails.clear()
                    page.goto(BASE + '/' + path, wait_until='networkidle')
                    page.wait_for_timeout(250)
                    r = page.evaluate(PROBE)
                    expect_side = w >= 1024
                    issues = []
                    if r['sw'] > r['vw'] + 1: issues.append(f"overflow {r['sw']}>{r['vw']} {r['over']}")
                    if path != 'devices.html' and r['side'] != expect_side: issues.append(f"sidebar shown={r['side']} expected={expect_side}")
                    if path != 'devices.html' and r['tab'] == expect_side: issues.append(f"tabbar shown={r['tab']}")
                    if r['footCovered']: issues.append('tab bar covers the footer at page end')
                    if r['h1'] != 1: issues.append(f"{r['h1']} h1")
                    if r['tiny']: issues.append('small targets ' + '; '.join(r['tiny']))
                    if errs: issues.append('console: ' + ' | '.join(errs[:3]))
                    if fails: issues.append('failed: ' + ' | '.join(fails[:3]))
                    if issues: report.append(f"{eng_name} {scheme} {w}x{h} {path}: " + ' || '.join(issues))
                    if SHOTS and (w, h) in SHOT_VP and (eng_name == 'webkit' or w >= 1024):
                        d = os.path.join(OUT, eng_name, scheme); os.makedirs(d, exist_ok=True)
                        page.screenshot(path=os.path.join(d, f"{path.replace('.html','').replace('#','-')}_{w}x{h}.png"), full_page=True)
                ctx.close()
        browser.close()
print('\n'.join(report) if report else 'MATRIX: no issues')
print(len(report), 'issue lines;', len(PAGES), 'pages x', len(VIEWPORTS), 'viewports x 2 engines x 2 schemes')
