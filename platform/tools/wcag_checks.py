"""Targeted WCAG checks of the EV-SIENT Planner that axe-core and matrix.py do not make.

Written for the self-assessed Accessibility Conformance Report (docs/accessibility/ACR.md). It walks
the whole flow once in Chromium with the real engine (Example City, as planner_flow.py does), then
also confirms two of Your Columns with a direction on Map Columns, builds and runs Your Index, shows
the Results map (unless --no-map), and visits every screen:

  structure   headings, landmarks, page titles, tables (caption, header cells, scope), images and
              SVG names, label in name (2.5.3), live regions, native tooltips (1.3.1, 2.4.2, 2.4.6,
              1.1.1, 2.5.3, 4.1.2)
  focus       Tab through every screen in all four themes at 1440x900 and in light at 390x844:
              the order, no trap (2.1.2), a visible indicator, its contrast against what surrounds
              it from computed styles, and in light and dark a pixel comparison of the control
              focused and not focused (2.4.7, 1.4.11); whether anything the page draws covers the
              focused control (2.4.11)
  contrast    non-text contrast from screenshots: the edge of every text field and menu, check
              boxes, radio buttons, sliders, bordered buttons, chart marks, tier marks, map markers,
              in all four themes (1.4.11); and text contrast for the text axe could not judge
              (on the translucent sidebar and the compact step bar) (1.4.3)
  spacing     the WCAG 1.4.12 text-spacing style injected, at 1440x900 and 390x844: text clipped
              by an ancestor or by its own box, compared with the same page without the style
  zoom        200% (1440x900 seen at 720x450), 400% (1280x1024 seen at 320x256) and 320x640:
              page width, clipped text, and how much of the window fixed bars cover (1.4.4,
              1.4.10, 2.4.11)
  targets     every control under 24 by 24 px and whether the spacing exception holds (2.5.8)
  hover       style rules that reveal content on :hover or :focus (1.4.13)
  status      every change to a live region during the flow, with the action that caused it (4.1.3)
  errors      files that cannot be read or run, a field left unmatched on Map Columns, an invalid
              setting in Your Index: how each problem is said, where, and whether it is announced
              (3.3.1, 3.3.2, 3.3.3, 4.1.3)
  dialog      Common Questions: focus moves in, never reaches the page behind, Escape closes,
              focus returns (2.1.2, 2.4.3)
  step menu   the compact step menu below 1024 px when its value changes (3.2.2)
  downloads   the report as HTML, tagged PDF and Word: language, title, headings, tables, header
              cells, alternative text, and the PDF's structure tree in reading order
  axe         with --axe, axe-core on every screen visited, in all four themes at 1440x900 and in
              light at 390x844, with the same rules as a11y_audit.py; this reaches the screens
              a11y_audit.py does not (Your Columns open, Your Index refused and ranked, the map shown)

A second session uploads Example City with six more invented sites (Your Index ranks only with ten
or more), runs Your Index to its results and repeats the per-screen checks on Your Index and Explore.

Needs, beyond requirements-qa.txt: Pillow and pdfplumber (pip), and pdfinfo (poppler) on the PATH.
The page is opened with bypass_csp, only so the checks can add their own style and script; run
matrix.py and offline_check.py for the app under its real policy.

Usage:
  python platform/tools/wcag_checks.py http://127.0.0.1:5321 /tmp/wcag [--no-map] [--axe axe.min.js]
      [--screens start,results] [--skip focus,contrast,spacing,zoom,errors,downloads,index]
Writes <out>/wcag.json (everything), <out>/downloads/ and <out>/error-files/. Exits 0; the findings
are for a person to read, not a gate. platform/tools/a11y_evidence.py summarises them.
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planner_flow as pf  # noqa: E402
from a11y_audit import run_axe  # noqa: E402

AXE_PATH: str | None = None  # set by --axe

THEMES = [("light", "no-preference"), ("dark", "no-preference"), ("light", "more"), ("dark", "more")]
SCREENS = ["start", "upload", "map", "check", "fill", "run", "results", "explore", "yourindex", "report"]
HEADINGS = {"start": "Rank Your", "upload": "Upload", "map": "Map Columns", "check": "Check", "fill": "Public Data",
            "run": "Run", "results": "Results", "explore": "Explore", "yourindex": "Your Index", "report": "Report"}
DSF = 2

TEXT_SPACING_CSS = """
* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
p { margin-bottom: 2em !important; }
"""

# ---------------------------------------------------------------- in-page helpers

HELPERS_JS = r"""
() => {
  if (window.__w) return;
  const srOnly = (el) => !!el.closest('.hig-visually-hidden, .skip-link:not(:focus)');
  const hiddenTree = (el) => !!el.closest('[hidden], [aria-hidden="true"], [inert]');
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) return false;
    let p = el;
    while (p) { if (p.hidden) return false; const pc = getComputedStyle(p); if (pc.display === 'none') return false; p = p.parentElement; }
    return true;
  };
  const norm = (s) => (s || '').toLowerCase().replace(/[’']/g, '').replace(/[^\p{L}\p{N}%.]+/gu, ' ').trim();
  const text = (el) => (el.textContent || '').trim().replace(/\s+/g, ' ');
  const describe = (el) => {
    if (!el) return 'nothing';
    const cls = typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    const name = (el.getAttribute('aria-label') || text(el) || el.getAttribute('title') || el.value || '').slice(0, 60);
    return `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${cls} "${name}"`;
  };
  const byIds = (ids) => ids.split(/\s+/).map((id) => document.getElementById(id)).filter(Boolean).map(text).join(' ');
  const accName = (el) => {
    if (el.getAttribute('aria-labelledby')) return byIds(el.getAttribute('aria-labelledby'));
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
    if (el.labels && el.labels.length) return [...el.labels].map(text).join(' ');
    if (el.tagName === 'IMG') return el.getAttribute('alt') || '';
    return text(el) || el.getAttribute('title') || '';
  };
  // Text a sighted person sees inside a control: text nodes not visually hidden or aria-hidden-only decoration.
  const visibleText = (el) => {
    const parts = [];
    const walk = (n) => {
      if (n.nodeType === 3) { if (n.textContent.trim()) parts.push(n.textContent); return; }
      if (n.nodeType !== 1) return;
      if (n.matches('.hig-visually-hidden, svg, [hidden]')) return;
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      for (const c of n.childNodes) walk(c);
    };
    walk(el);
    return parts.join(' ').trim().replace(/\s+/g, ' ');
  };

  // ---- colours
  const parse = (c) => {
    if (!c) return null;
    let m = c.match(/^rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/);
    if (m) { let a = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]); return [ +m[1], +m[2], +m[3], a ]; }
    m = c.match(/^color\(srgb\s+([\d.e-]+)\s+([\d.e-]+)\s+([\d.e-]+)(?:\s*\/\s*([\d.]+%?))?\s*\)$/);
    if (m) { let a = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]); return [ m[1] * 255, m[2] * 255, m[3] * 255, a ]; }
    if (c === 'transparent') return [0, 0, 0, 0];
    return null;
  };
  const over = (top, bottom) => {
    const a = top[3];
    return [top[0] * a + bottom[0] * (1 - a), top[1] * a + bottom[1] * (1 - a), top[2] * a + bottom[2] * (1 - a), 1];
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  // Background painted behind an element, from its ancestors' background colours (images and
  // backdrop filters are not modelled; the pixel checks cover those).
  const bgBehind = (el) => {
    const layers = [];
    for (let p = el; p; p = p.parentElement) {
      const c = parse(getComputedStyle(p).backgroundColor);
      if (c && c[3] > 0) layers.push(c);
      if (c && c[3] >= 1) break;
    }
    let out = parse(getComputedStyle(document.body).backgroundColor) || [255, 255, 255, 1];
    if (out[3] < 1) out = over(out, [255, 255, 255, 1]);
    for (let i = layers.length - 1; i >= 0; i--) out = over(layers[i], out);
    return out;
  };
  const hex = (c) => '#' + c.slice(0, 3).map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

  // ---- focus
  const ringOf = (el) => {
    const out = [];
    const take = (cs, where) => {
      if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) out.push({ where, kind: 'outline', width: parseFloat(cs.outlineWidth), offset: parseFloat(cs.outlineOffset), color: cs.outlineColor });
      if (cs.boxShadow && cs.boxShadow !== 'none') {
        for (const m of cs.boxShadow.matchAll(/(rgba?\([^)]*\)|color\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+(-?[\d.]+)px(?:\s+(-?[\d.]+)px)?(\s+inset)?/g)) {
          const spread = parseFloat(m[5] || '0');
          if (spread > 0 || Math.abs(parseFloat(m[2])) > 0 || Math.abs(parseFloat(m[3])) > 0) out.push({ where, kind: m[6] ? 'inset-shadow' : 'shadow', width: Math.max(spread, Math.abs(parseFloat(m[2])), Math.abs(parseFloat(m[3]))), color: m[1] });
        }
      }
    };
    take(getComputedStyle(el), 'self');
    take(getComputedStyle(el, '::before'), '::before');
    take(getComputedStyle(el, '::after'), '::after');
    const field = el.closest('.st-inset-field');
    if (field) take(getComputedStyle(field), 'field');
    return out;
  };
  const coverage = (el) => {
    const r = el.getBoundingClientRect();
    const xs = [0.1, 0.5, 0.9], ys = [0.15, 0.5, 0.85];
    let inView = 0, mine = 0;
    const covers = new Set();
    for (const fx of xs) for (const fy of ys) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
      inView++;
      const hit = document.elementFromPoint(x, y);
      if (hit && (el.contains(hit) || hit.contains(el) || (el.labels && [...el.labels].some((l) => l.contains(hit))))) mine++;
      else if (hit) covers.add(describe(hit));
    }
    return { points: 9, inView, mine, coveredBy: [...covers] };
  };
  const keyOf = (el) => {
    const path = [];
    for (let p = el; p && p !== document.body; p = p.parentElement) {
      const i = p.parentElement ? [...p.parentElement.children].indexOf(p) : 0;
      path.push(p.tagName + i);
    }
    return path.reverse().join('/');
  };
  const focusInfo = () => {
    const el = document.activeElement;
    if (!el || el === document.body || el === document.documentElement) return null;
    window.__f = el;
    const r = el.getBoundingClientRect();
    const rings = ringOf(el);
    const behind = bgBehind(el.parentElement || el);
    const own = bgBehind(el);
    const ringContrast = rings.map((g) => {
      const c = parse(g.color);
      if (!c) return { ...g, vsOutside: null, vsInside: null };
      const solid = over(c, behind);
      return { ...g, colorHex: hex(solid), vsOutside: +ratio(solid, behind).toFixed(2), vsInside: +ratio(over(c, own), own).toFixed(2) };
    });
    return {
      key: keyOf(el), desc: describe(el), name: accName(el).slice(0, 80), role: el.getAttribute('role') || el.tagName.toLowerCase(),
      rect: { x: r.left, y: r.top, w: r.width, h: r.height }, focusVisible: el.matches(':focus-visible'),
      rings: ringContrast, cover: coverage(el), inMap: !!el.closest('.maplibregl-map'),
      bgOutside: hex(behind),
    };
  };

  // ---- structure
  const structure = () => {
    const headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]')].filter((h) => visible(h) || srOnly(h))
      .filter((h) => !hiddenTree(h))
      .map((h) => ({ level: h.getAttribute('aria-level') ? +h.getAttribute('aria-level') : +h.tagName[1], text: text(h).slice(0, 90) }));
    const skips = [];
    for (let i = 1; i < headings.length; i++) if (headings[i].level > headings[i - 1].level + 1) skips.push(`${headings[i - 1].level}->${headings[i].level} at "${headings[i].text}"`);
    const landmarks = [...document.querySelectorAll('main, nav, header, footer, aside, [role=main], [role=navigation], [role=banner], [role=contentinfo], [role=complementary], [role=region], section[aria-labelledby], section[aria-label], form[aria-label]')]
      .filter((x) => !hiddenTree(x)).map((x) => `${x.getAttribute('role') || x.tagName.toLowerCase()}${accName(x) ? ': ' + accName(x).slice(0, 40) : ''}`);
    const tables = [...document.querySelectorAll('table')].filter((t) => !t.closest('[hidden]')).map((t) => {
      const ths = [...t.querySelectorAll('th')];
      const tds = [...t.querySelectorAll('td')];
      return {
        name: (t.caption ? text(t.caption) : '') || accName(t) || (t.closest('[role=region]') ? accName(t.closest('[role=region]')) : ''),
        caption: !!t.caption, rows: t.rows.length, th: ths.length, td: tds.length,
        thCol: ths.filter((h) => h.scope === 'col' || h.closest('thead')).length,
        thRow: ths.filter((h) => h.scope === 'row').length,
        thNoScope: ths.filter((h) => !h.scope && !h.closest('thead')).length,
        emptyTh: ths.filter((h) => !text(h)).length,
        emptyTd: tds.filter((d) => !text(d)).length,
        layoutRole: t.getAttribute('role'),
        inScrollRegion: !!t.closest('[role=region][tabindex]'),
      };
    });
    const images = [...document.querySelectorAll('img, svg, [role=img], canvas')].filter((x) => !hiddenTree(x) && !x.closest('svg svg'))
      .map((x) => {
        const decorative = x.getAttribute('aria-hidden') === 'true' || x.getAttribute('role') === 'presentation' || x.getAttribute('alt') === '';
        const named = !!accName(x) || (x.tagName.toLowerCase() === 'svg' && !!x.querySelector(':scope > title'));
        return { tag: x.tagName.toLowerCase(), role: x.getAttribute('role'), decorative, name: named ? accName(x).slice(0, 80) : '', cls: typeof x.className === 'string' ? x.className : (x.className && x.className.baseVal) || '' };
      });
    const unnamedImages = images.filter((x) => !x.decorative && !x.name && (x.role === 'img' || x.tag === 'img'));
    const svgNoRole = images.filter((x) => x.tag === 'svg' && !x.decorative && !x.role);
    const controls = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [role=checkbox], [role=tab]')]
      .filter((el) => visible(el) && !hiddenTree(el));
    const labelInName = [];
    for (const el of controls) {
      if (!el.hasAttribute('aria-label') && !el.hasAttribute('aria-labelledby')) continue;
      const seen = visibleText(el);
      if (!seen) continue;
      const name = accName(el);
      if (!norm(name).includes(norm(seen))) labelInName.push({ control: describe(el), visible: seen.slice(0, 60), name: name.slice(0, 100), startsWith: norm(name).startsWith(norm(seen)) });
    }
    const unlabelled = controls.filter((el) => !accName(el).trim()).map(describe);
    const live = [...document.querySelectorAll('[aria-live], [role=status], [role=alert], [role=log], output')].filter((x) => !x.closest('[hidden]'))
      .map((x) => `${x.getAttribute('role') || x.tagName.toLowerCase()}${x.getAttribute('aria-live') ? '[' + x.getAttribute('aria-live') + ']' : ''}: "${text(x).slice(0, 60)}"`);
    const titles = [...document.querySelectorAll('[title]')].filter((x) => !hiddenTree(x)).map((x) => `${describe(x)} title="${x.getAttribute('title').slice(0, 60)}"`);
    const svgTitles = document.querySelectorAll('svg title').length;
    const autocomplete = [...document.querySelectorAll('input, select, textarea')].filter((x) => !x.closest('[hidden]'))
      .map((x) => `${x.type || x.tagName.toLowerCase()} ${accName(x).slice(0, 40)} autocomplete=${x.getAttribute('autocomplete')}`);
    const states = {};
    for (const a of ['aria-expanded', 'aria-pressed', 'aria-current', 'aria-checked', 'aria-sort', 'aria-invalid', 'aria-disabled', 'aria-busy', 'aria-describedby', 'aria-haspopup']) {
      const n = [...document.querySelectorAll(`[${a}]`)].filter((x) => !x.closest('[hidden]')).length;
      if (n) states[a] = n;
    }
    return {
      states,
      title: document.title, lang: document.documentElement.lang, h1: headings.filter((h) => h.level === 1).length,
      headings, skips, landmarks, tables, imagesCount: images.length, unnamedImages, svgNoRole, labelInName, unlabelled,
      live, titles, svgTitles, autocomplete,
    };
  };

  // ---- clipping
  const ownTextRect = (el) => {
    let box = null;
    for (const n of el.childNodes) {
      if (n.nodeType !== 3 || !n.textContent.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) {
        if (r.width < 1) continue;
        box = box ? { left: Math.min(box.left, r.left), top: Math.min(box.top, r.top), right: Math.max(box.right, r.right), bottom: Math.max(box.bottom, r.bottom) }
          : { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
      }
    }
    return box;
  };
  const clips = (cs) => ['hidden', 'clip'].includes(cs.overflowX) || ['hidden', 'clip'].includes(cs.overflowY);
  const clipped = () => {
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      if (el.closest('.maplibregl-map, script, style, select, option')) continue;
      const t = ownTextRect(el);
      if (!t) continue;
      if (srOnly(el) || hiddenTree(el) || !visible(el)) continue;
      const cs = getComputedStyle(el);
      if (clips(cs) && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) {
        out.push({ el: describe(el), how: 'own box', overflow: `${el.scrollWidth}x${el.scrollHeight} in ${el.clientWidth}x${el.clientHeight}`, ellipsis: cs.textOverflow === 'ellipsis' });
        continue;
      }
      for (let a = el.parentElement, i = 0; a && a !== document.body && i < 8; a = a.parentElement, i++) {
        const acs = getComputedStyle(a);
        // Inside a scroll container the text can be scrolled to, so it is not lost.
        if (['auto', 'scroll'].includes(acs.overflowX) || ['auto', 'scroll'].includes(acs.overflowY)) break;
        if (!clips(acs)) continue;
        if (a.matches('.hig-visually-hidden')) break;
        const ar = a.getBoundingClientRect();
        // Hidden on purpose for sight but kept for screen readers (a stacked table's header row).
        if (ar.width <= 1 || ar.height <= 1) break;
        const cut = Math.max(t.right - ar.right, ar.left - t.left, t.bottom - ar.bottom, ar.top - t.top);
        if (cut > 1.5) { out.push({ el: describe(el), how: 'ancestor', by: describe(a), cutPx: Math.round(cut) }); }
        break;
      }
    }
    return out;
  };

  // ---- target size (2.5.8)
  const targets = () => {
    const ctl = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button]')]
      .filter((el) => visible(el) && !hiddenTree(el) && !el.matches('.skip-link'))
      .filter((el) => !el.closest('.maplibregl-ctrl-attrib'));
    const box = (el) => ((el.matches('input[type=checkbox], input[type=radio]') && el.closest('label')) || el).getBoundingClientRect();
    const inSentence = (el) => el.tagName === 'A' && getComputedStyle(el).display === 'inline' && (el.parentElement?.textContent || '').trim().length > (el.textContent || '').trim().length + 3;
    const rects = ctl.map((el) => ({ el, r: box(el) }));
    const small = [];
    for (const { el, r } of rects) {
      if (r.width >= 23.5 && r.height >= 23.5) continue;
      if (inSentence(el)) continue;
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      // Spacing exception: a 24 px circle centred on the target meets no other target nor another small target's circle.
      let clash = null;
      for (const o of rects) {
        if (o.el === el) continue;
        const nx = Math.max(o.r.left, Math.min(cx, o.r.right)), ny = Math.max(o.r.top, Math.min(cy, o.r.bottom));
        if (Math.hypot(nx - cx, ny - cy) < 12) { clash = describe(o.el); break; }
      }
      small.push({ el: describe(el), size: `${Math.round(r.width)}x${Math.round(r.height)}`, spacingOk: !clash, clash });
    }
    return small;
  };

  // ---- hover and focus reveals (1.4.13)
  const reveals = () => {
    const out = [];
    const scan = (rules) => {
      for (const r of rules) {
        if (r.cssRules && !r.selectorText) { scan(r.cssRules); continue; }
        if (!r.selectorText || !/:hover|:focus-within/.test(r.selectorText)) continue;
        const s = r.style;
        const props = ['display', 'visibility', 'opacity', 'max-height', 'height', 'clip', 'clip-path', 'transform'].filter((p) => s.getPropertyValue(p));
        if (props.length) out.push(`${r.selectorText} { ${props.map((p) => p + ': ' + s.getPropertyValue(p)).join('; ')} }`);
      }
    };
    for (const sh of document.styleSheets) { try { scan(sh.cssRules); } catch (e) { out.push('unreadable sheet ' + sh.href); } }
    return out;
  };

  // ---- fixed bars
  const fixedCover = () => {
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
      if (!visible(el) || el.closest('.maplibregl-map')) continue;
      const r = el.getBoundingClientRect();
      const h = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
      const w = Math.max(0, Math.min(r.right, innerWidth) - Math.max(r.left, 0));
      if (h * w > 0) out.push({ el: describe(el), position: cs.position, heightPx: Math.round(h), widthPx: Math.round(w), shareOfWindow: +((h * w) / (innerWidth * innerHeight)).toFixed(2) });
    }
    return out;
  };

  const pageWidth = () => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth });

  // ---- placeholder text (1.4.3 applies to it): its colour over the field's own background
  const placeholders = () => [...document.querySelectorAll('input[placeholder], textarea[placeholder]')]
    .filter((el) => visible(el) && el.placeholder)
    .map((el) => {
      const c = parse(getComputedStyle(el, '::placeholder').color);
      const bg = bgBehind(el);
      const solid = c ? over(c, bg) : null;
      return { el: describe(el), placeholder: el.placeholder.slice(0, 40), color: solid ? hex(solid) : null, background: hex(bg),
               ratio: solid ? +ratio(solid, bg).toFixed(2) : null, fontSize: getComputedStyle(el).fontSize };
    });

  window.__w = { structure, focusInfo, clipped, targets, reveals, fixedCover, pageWidth, placeholders, describe, visible, hex };
}
"""

LIVE_LOG_JS = r"""
(() => {
  window.__liveLog = [];
  window.__mark = (m) => window.__liveLog.push({ t: performance.now(), mark: m });
  const regionOf = (n) => {
    const el = n.nodeType === 1 ? n : n.parentElement;
    return el && el.closest ? el.closest('[aria-live], [role=status], [role=alert], [role=log], output') : null;
  };
  const seen = new Map();
  const record = (r) => {
    if (!r || r.closest('[hidden]')) return;
    const text = (r.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 200);
    if (!text || seen.get(r) === text) return;
    seen.set(r, text);
    window.__liveLog.push({ t: performance.now(), role: r.getAttribute('role') || r.tagName.toLowerCase(), live: r.getAttribute('aria-live'), text });
  };
  const start = () => new MutationObserver((ms) => {
    for (const m of ms) {
      record(regionOf(m.target));
      for (const n of m.addedNodes) {
        record(regionOf(n));
        if (n.nodeType === 1) n.querySelectorAll && n.querySelectorAll('[aria-live], [role=status], [role=alert]').forEach(record);
      }
    }
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true });
  if (document.documentElement) start(); else addEventListener('DOMContentLoaded', start);
})();
"""

# ---------------------------------------------------------------- pixels


def _lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _ratio(a, b):
    x, y = _lum(a), _lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def shot(page, rect, pad):
    """A device-pixel screenshot of rect grown by pad CSS px, clipped to the window."""
    vw, vh = page.viewport_size["width"], page.viewport_size["height"]
    x0, y0 = max(0, rect["x"] - pad), max(0, rect["y"] - pad)
    x1, y1 = min(vw, rect["x"] + rect["w"] + pad), min(vh, rect["y"] + rect["h"] + pad)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None, None
    png = page.screenshot(clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}, animations="disabled")
    img = Image.open(io.BytesIO(png)).convert("RGB")
    inner = (round((rect["x"] - x0) * DSF), round((rect["y"] - y0) * DSF),
             round((rect["x"] - x0 + rect["w"]) * DSF), round((rect["y"] - y0 + rect["h"]) * DSF))
    return img, inner


def ring_and_inside(img, inner):
    """Pixels outside the element's box (the surround) and inside it."""
    w, h = img.size
    px = img.load()
    outside, inside, edge = [], [], []
    l, t, r, b = inner
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if l <= x < r and t <= y < b:
                inside.append(p)
                if x < l + 2 * DSF or x >= r - 2 * DSF or y < t + 2 * DSF or y >= b - 2 * DSF:
                    edge.append(p)
            else:
                outside.append(p)
    return outside, inside, edge


def surround_colour(outside):
    if not outside:
        return None
    return collections.Counter(outside).most_common(1)[0][0]


def max_contrast(pixels, bg):
    best, col = 1.0, None
    for p in set(pixels):
        r = _ratio(p, bg)
        if r > best:
            best, col = r, p
    return round(best, 2), (_hex(col) if col else None)


def focus_pixels(page, rect):
    """Compare the focused control with the same control not focused: how strongly the indicator stands out."""
    a, inner = shot(page, rect, 8)
    if a is None:
        return None
    page.evaluate("() => window.__f && window.__f.blur()")
    page.wait_for_timeout(30)
    b, _ = shot(page, rect, 8)
    page.evaluate("() => window.__f && window.__f.focus({ preventScroll: true })")
    if b is None or a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    changed = strong = 0
    best = 1.0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            p, q = pa[x, y], pb[x, y]
            if p == q:
                continue
            changed += 1
            r = _ratio(p, q)
            best = max(best, r)
            if r >= 3:
                strong += 1
    perimeter = 2 * (rect["w"] + rect["h"]) * DSF
    return {"changedPx": changed, "px3to1": strong, "maxChange": round(best, 2),
            "ringCssPxAt3to1": round(strong / perimeter / DSF, 2) if perimeter else None}


# ---------------------------------------------------------------- flow helpers


def set_theme(page, scheme, contrast):
    page.emulate_media(color_scheme=scheme, contrast=contrast)
    page.wait_for_timeout(150)
    return page.evaluate("document.documentElement.dataset.theme")


def show(page, screen):
    step = screen.split("-")[0]
    if step in pf.SCREENS:
        pf.show(page, step)
    else:
        pf.go(page, step)
        page.locator("#main h1", has_text=HEADINGS[step]).first.wait_for(timeout=30_000)
        page.evaluate("() => window.scrollTo(0, 0)")
        pf.settle(page)
    page.evaluate(HELPERS_JS)
    if step == "yourindex":
        table = page.locator("button.hig-disclosure__trigger", has_text="Every Site as a Table")
        if table.count() and table.first.get_attribute("aria-expanded") != "true":
            table.first.click()
        page.evaluate("() => window.scrollTo(0, 0)")


def mark(page, what):
    page.evaluate("(m) => window.__mark && window.__mark(m)", what)


def your_columns_and_index(page, log):
    """Confirm two numeric columns with a direction on Map Columns, then build and run Your Index."""
    pf.go(page, "map")
    page.locator("#main h1", has_text="Map Columns").first.wait_for()
    mark(page, "Map Columns: Review Your Columns")
    page.get_by_role("button", name="Review Your Columns").click()
    page.locator(".yc-list").wait_for(timeout=60_000)
    mark(page, "Your Columns: filter Can Rank Sites")
    page.locator(".yc-filter button", has_text="Can Rank Sites").click()
    done = 0
    for i in range(6):
        cards = page.locator(".yc-list > li")
        if done >= 2 or i >= cards.count():
            break
        card = cards.nth(i)
        name = card.locator(".yc-card__name").inner_text()
        btn = card.locator(".yc-card__actions button")
        mark(page, f"Your Columns: open {name}")
        btn.click()
        radios = card.locator(".yc-direction input[type=radio]")
        if not radios.count():
            btn.click()
            continue
        radios.first.check()
        mark(page, f"Your Columns: Confirm Column {name}")
        card.get_by_role("button", name="Confirm Column").click()
        page.wait_for_function("() => /Confirmed/.test(document.querySelector('#yc-panel [role=status]')?.textContent || '')", timeout=60_000)
        done += 1
        page.wait_for_timeout(300)
    log["columnsConfirmed"] = done
    pf.go(page, "yourindex")
    page.locator("#main h1", has_text="Your Index").first.wait_for(timeout=30_000)
    page.get_by_role("button", name="Start Your Index").click()
    for _ in range(2):
        add = page.locator(".yi-add-list button")
        if add.count():
            mark(page, "Your Index: Add column")
            add.first.click()
            page.wait_for_timeout(200)
    page.locator("#yi-name").fill("Accessibility check index")
    mark(page, "Your Index: Run Your Index")
    page.get_by_role("button", name="Run Your Index").click()
    page.locator("#yi-results-title").wait_for(timeout=120_000)
    log["indexRan"] = True


def results_actions(page):
    """Actions on Results that should be announced."""
    pf.go(page, "results")
    page.locator("#main h1", has_text="Results").first.wait_for()
    mark(page, "Results: choose site 3 in the table")
    page.locator(".rs-ranked button.rs-site").nth(2).click()
    page.wait_for_timeout(300)
    mark(page, "Results: arrow down in the table")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(300)
    mark(page, "Results: add a third site to Compare")
    boxes = page.locator(".rs-ranked .rs-check input")
    for i in range(boxes.count()):
        if not boxes.nth(i).is_checked() and boxes.nth(i).is_enabled():
            boxes.nth(i).check()
            break
    page.wait_for_timeout(300)
    mark(page, "Results: sort by Fleet")
    sort = page.locator("th.rs-col-yours button.rs-sort").first
    if sort.count():
        sort.click()
        page.wait_for_timeout(300)
        page.locator("th.rs-col-rank button.rs-sort").click()
        page.wait_for_timeout(300)


def show_map(page, info):
    pf.go(page, "results")
    page.locator("#main h1", has_text="Results").first.wait_for()
    mark(page, "Results: Show Map")
    page.get_by_role("button", name="Show Map", exact=True).click()
    try:
        page.locator(".maplibregl-ctrl-attrib").wait_for(timeout=30_000)
        page.wait_for_timeout(3000)
        info["map"] = "shown"
        info["mapCredit"] = page.locator(".maplibregl-ctrl-attrib").inner_text()
    except Exception as e:  # noqa: BLE001
        info["map"] = f"not shown: {e}"


# ---------------------------------------------------------------- checks

NONTEXT = [
    ("text field", "input[type=text], input[type=search], input[type=number], input[type=date], input:not([type]), textarea", "edge"),
    ("menu", "select", "edge"),
    ("field group", ".st-inset-fields", "edge"),
    ("check box", "input[type=checkbox]:not(:disabled)", "max"),
    ("radio button", "input[type=radio]:not(:disabled)", "max"),
    ("slider", "input[type=range]", "max"),
    ("bordered button", ".hig-button--bordered:not(:disabled)", "edge"),
    ("filter button", ".st-filter__btn", "edge"),
    ("tier mark", ".tier__mark, .rp-tier__mark", "max"),
    ("map marker", ".rs-marker", "max"),
    ("score bar", ".sd-bar__fill, .ex__fill, .xp-bar__fill, .rp-bar__fill", "max"),
    ("bar track", ".ex__track, .xp-bar__track, .xp-spread__track", "max"),
    ("strength mark", ".xp-strength__dot, .xp-strength__band", "max"),
    ("slope graph", ".yi-slope__line, .yi-slope__dot", "max"),
    ("report plot", ".rp-plot circle, .rp-plot line, .rp-plot rect", "max"),
    ("status icon", ".st-status__icon, .st-banner__icon", "max"),
    ("map control", ".maplibregl-ctrl-group button", "max"),
]

AXE_UNDECIDED_TEXT = [
    ("sidebar step label", ".nav-sidebar .hig-sidebar__label"),
    ("sidebar brand", ".nav-brand__title, .nav-brand__sub"),
    ("sidebar footer", ".nav-sidebar__foot"),
    ("sidebar step note", ".app-steps__why"),
    ("compact bar", ".app-compact__brand span, .app-compact select"),
    ("sidebar current step", ".nav-sidebar .is-selected .hig-sidebar__label"),
    ("rank cell", ".rs-row .rs-rank"),
    ("selected row", ".rs-row.is-selected .hig-table__cell"),
    ("report plot note", ".rp-plot__note"),
]


def nontext(page, per=4):
    out = []
    items = page.evaluate(
        """(groups) => {
            const res = [];
            for (const [label, sel, how] of groups) {
              let n = 0;
              for (const el of document.querySelectorAll(sel)) {
                if (!window.__w.visible(el) || el.closest('[hidden]')) continue;
                if (n >= %d) break;
                el.setAttribute('data-wcag-probe', label + '|' + n);
                res.push([label, how, label + '|' + n]);
                n++;
              }
            }
            return res;
        }""" % per,
        [list(g) for g in NONTEXT],
    )
    for label, how, probe in items:
        loc = page.locator(f'[data-wcag-probe="{probe}"]')
        try:
            loc.scroll_into_view_if_needed(timeout=2000)
        except Exception:  # noqa: BLE001
            continue
        r = loc.evaluate("(el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, d: window.__w.describe(el) }; }")
        img, inner = shot(page, r, 3)
        if img is None:
            continue
        outside, inside, edge = ring_and_inside(img, inner)
        bg = surround_colour(outside)
        if bg is None:
            continue
        ratio, col = max_contrast(edge if how == "edge" else inside, bg)
        out.append({"kind": label, "el": r["d"], "surround": _hex(bg), "strongest": col, "ratio": ratio, "measured": how})
    page.evaluate("() => document.querySelectorAll('[data-wcag-probe]').forEach((e) => e.removeAttribute('data-wcag-probe'))")
    return out


def undecided_text(page):
    out = []
    for label, sel in AXE_UNDECIDED_TEXT:
        loc = page.locator(sel)
        for i in range(min(loc.count(), 3)):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            r = el.evaluate("(el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return { x: r.left, y: r.top, w: r.width, h: r.height, d: window.__w.describe(el), size: cs.fontSize, weight: cs.fontWeight }; }")
            img, inner = shot(page, r, 2)
            if img is None:
                continue
            outside, inside, _ = ring_and_inside(img, inner)
            bg = surround_colour(outside + inside)
            ratio, col = max_contrast(inside, bg)
            out.append({"kind": label, "el": r["d"], "font": f"{r['size']} {r['weight']}", "background": _hex(bg), "text": col, "ratio": ratio})
    return out


def focus_walk(page, pixels, limit=260):
    # Start from the top of the document, as a page just loaded: a marker before everything, out of the tab order.
    page.evaluate("""() => {
        let s = document.getElementById('__wcag_start');
        if (!s) { s = document.createElement('span'); s.id = '__wcag_start'; s.tabIndex = -1; document.body.prepend(s); }
        window.scrollTo(0, 0);
        s.focus({ preventScroll: true });
    }""")
    page.mouse.move(0, 0)
    stops, seen = [], {}
    result = {"stops": stops, "ended": None}
    for _ in range(limit):
        page.keyboard.press("Tab")
        info = page.evaluate("() => window.__w.focusInfo()")
        if info is None:
            result["ended"] = "left the page (focus returned to the browser)"
            break
        if stops and info["key"] == stops[-1]["key"]:
            # A date field's day, month and year are separate stops within one element.
            stops[-1]["subStops"] = stops[-1].get("subStops", 1) + 1
            if stops[-1]["subStops"] > 6:
                result["ended"] = f"stuck on one control: {info['desc']}"
                break
            continue
        if info["key"] in seen:
            result["ended"] = f"returned to an earlier stop: {info['desc']}"
            result["repeat"] = info["key"] == stops[0]["key"] if stops else False
            break
        seen[info["key"]] = len(stops)
        if pixels and not info["inMap"]:
            info["pixels"] = focus_pixels(page, info["rect"])
        stops.append(info)
    else:
        result["ended"] = f"still moving after {limit} presses"
    return result


def summarise_focus(walk):
    stops = walk["stops"]
    no_ring = [s["desc"] for s in stops if not s["rings"]]
    weak = []
    for s in stops:
        best = max([g["vsOutside"] or 0 for g in s["rings"]] + [0])
        px = s.get("pixels")
        if s["rings"] and best < 3 and not (px and px["ringCssPxAt3to1"] and px["ringCssPxAt3to1"] >= 1):
            weak.append({"el": s["desc"], "ringVsOutside": best, "rings": s["rings"], "pixels": px})
    covered = [{"el": s["desc"], "visiblePoints": s["cover"]["mine"], "inView": s["cover"]["inView"], "by": s["cover"]["coveredBy"]}
               for s in stops if s["cover"]["mine"] < s["cover"]["inView"] or s["cover"]["inView"] == 0]
    hidden = [c for c in covered if c["visiblePoints"] == 0]
    px_weak = [{"el": s["desc"], **s["pixels"]} for s in stops if s.get("pixels") and (s["pixels"]["ringCssPxAt3to1"] or 0) < 1]
    return {"count": len(stops), "ended": walk["ended"], "noIndicator": no_ring, "weakByStyle": weak, "weakByPixels": px_weak,
            "partlyCovered": [c for c in covered if c["visiblePoints"] > 0], "entirelyHidden": hidden,
            "order": [s["name"] or s["desc"] for s in stops]}


def text_spacing(page):
    before = page.evaluate("() => window.__w.clipped()")
    width0 = page.evaluate("() => window.__w.pageWidth()")
    page.add_style_tag(content=TEXT_SPACING_CSS)
    page.wait_for_timeout(200)
    after = page.evaluate("() => window.__w.clipped()")
    width1 = page.evaluate("() => window.__w.pageWidth()")
    page.evaluate("() => document.querySelectorAll('style').forEach((s) => { if (s.textContent.includes('word-spacing: 0.16em')) s.remove(); })")
    old = {(c["el"], c["how"]) for c in before}
    return {"clippedBefore": len(before), "newlyClipped": [c for c in after if (c["el"], c["how"]) not in old],
            "pageWidthBefore": width0, "pageWidthAfter": width1}


def zoom_state(page):
    return {"pageWidth": page.evaluate("() => window.__w.pageWidth()"), "clipped": page.evaluate("() => window.__w.clipped()"),
            "fixed": page.evaluate("() => window.__w.fixedCover()")}


# ---------------------------------------------------------------- errors

def error_checks(browser, base, out_dir):
    """Problem files and invalid choices: what the planner says, where, and with what role."""
    work = out_dir / "error-files"
    work.mkdir(parents=True, exist_ok=True)
    sample = (Path(__file__).resolve().parents[1] / "app/public/samples/example-city.csv").read_text(encoding="utf-8")
    lines = sample.splitlines()
    head = lines[0]
    cols = head.split(",")
    files = {
        "binary-junk.csv": bytes(range(256)) * 20,
        "empty.csv": b"",
        "headers-only.csv": (head + "\n").encode(),
        "notes.txt": b"just some notes, not a table\n",
        "duplicate-ids.csv": "\n".join([head, lines[1], lines[1], *lines[2:]]).encode(),
        "bad-coordinates.csv": "\n".join([head, lines[1].replace("45.012", "999"), *lines[2:]]).encode(),
    }
    results = {}
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, bypass_csp=True, accept_downloads=True)
    ctx.add_init_script(LIVE_LOG_JS)
    for name, data in files.items():
        (work / name).write_bytes(data)
        page = ctx.new_page()
        page.goto(pf.app_url(base, False))
        page.locator("#main h1", has_text="Rank Your Candidate Charging Sites").first.wait_for(timeout=60_000)
        page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
        start_btn = page.get_by_role("button", name=re.compile("^(Start a New Project|New Project|Upload a File|Start With Your Own File)", re.I))
        if start_btn.count():
            start_btn.first.click()
        else:
            pf.go(page, "upload")
        page.locator("#main h1", has_text="Upload").first.wait_for()
        page.locator("input[type=file]").set_input_files(str(work / name))
        page.wait_for_timeout(2500)
        try:
            page.wait_for_function("() => !document.querySelector('.st-inline-status .hig-progress')", timeout=60_000)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(800)
        page.evaluate(HELPERS_JS)
        r = page.evaluate("""() => {
            const banners = [...document.querySelectorAll('.st-banner, .st-refusal, [role=alert]')].map((b) => ({
              role: b.getAttribute('role'), title: (b.querySelector('.st-banner__title')?.textContent || '').trim(),
              text: (b.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 400) }));
            const next = [...document.querySelectorAll('.st-actions button')].map((b) => ({ label: b.textContent.trim(), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
              describedBy: b.getAttribute('aria-describedby') ? (document.getElementById(b.getAttribute('aria-describedby'))?.textContent || '').trim() : null }));
            const why = [...document.querySelectorAll('.st-actions__why, .st-actions p')].map((p) => p.textContent.trim());
            return { banners, next, why, detect: document.querySelector('.st-detect')?.textContent || null, focus: window.__w.describe(document.activeElement) };
        }""")
        r["live"] = page.evaluate("() => window.__liveLog.filter((x) => x.text).map((x) => `${x.role}${x.live ? '[' + x.live + ']' : ''}: ${x.text}`)")
        # Files that reach the model: what Check says.
        if name in ("duplicate-ids.csv", "bad-coordinates.csv"):
            try:
                page.get_by_role("button", name="Continue to Map Columns", exact=True).click(timeout=5000)
                page.locator("#main h1", has_text="Map Columns").first.wait_for(timeout=30_000)
                acc = page.get_by_role("button", name="Accept All Matched", exact=True)
                if acc.count():
                    acc.first.click()
                page.get_by_role("button", name="Continue to Check", exact=True).click(timeout=10_000)
                page.locator("#main h1", has_text="Check").first.wait_for(timeout=30_000)
                page.locator(".st-coverage").wait_for(timeout=60_000)
                page.wait_for_timeout(800)
                r["check"] = page.evaluate("""() => ({
                  mustFix: [...document.querySelectorAll('#main [class*=must], #main .st-issue, #main [role=alert]')].map((x) => (x.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 300)).slice(0, 8),
                  next: [...document.querySelectorAll('.st-actions button')].map((b) => ({ label: b.textContent.trim(), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true' })),
                  why: [...document.querySelectorAll('.st-actions p, .st-actions__why')].map((p) => p.textContent.trim()),
                  headings: [...document.querySelectorAll('#main h2, #main h3')].map((h) => h.textContent.trim()).slice(0, 20) })""")
            except Exception as e:  # noqa: BLE001
                r["check"] = f"could not reach Check: {e}"
        results[name] = r
        page.close()

    # Start: a project file that is not one.
    page = ctx.new_page()
    page.goto(pf.app_url(base, False))
    page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    page.evaluate(HELPERS_JS)
    (work / "not-a-project.evsient").write_bytes(b"this is not a project file")
    page.locator("#main input[type=file]").first.set_input_files(str(work / "not-a-project.evsient"))
    page.wait_for_timeout(2500)
    results["start: not-a-project.evsient"] = page.evaluate("""() => ({
        alerts: [...document.querySelectorAll('#main [role=alert], #main .st-banner')].map((b) => ({ role: b.getAttribute('role'), text: (b.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 400) })),
        focus: window.__w.describe(document.activeElement),
        live: window.__liveLog.filter((x) => x.text).slice(-4).map((x) => `${x.role}: ${x.text}`) })""")
    page.close()

    # Map Columns: a required field left unmatched.
    page = ctx.new_page()
    page.goto(pf.app_url(base, False))
    page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    page.get_by_role("button", name="Try the Example City Sample", exact=True).click()
    page.locator("#found-title").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    page.get_by_role("button", name="Continue to Map Columns", exact=True).click()
    page.locator("#main h1", has_text="Map Columns").first.wait_for()
    show_all = page.locator('button[aria-controls="grp-matched-list"]', has_text="Show All")
    if show_all.count():
        show_all.click()
    page.evaluate(HELPERS_JS)
    page.locator("#col-site_id").select_option("")
    page.wait_for_timeout(1500)
    results["map: site_id left unmatched"] = page.evaluate("""() => ({
        row: (document.querySelector('#field-site_id')?.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 400),
        select: (() => { const s = document.querySelector('#col-site_id'); return s ? { invalid: s.getAttribute('aria-invalid'), describedBy: s.getAttribute('aria-describedby') && [...s.getAttribute('aria-describedby').split(' ')].map((i) => document.getElementById(i)?.textContent?.trim()).join(' | ') } : null; })(),
        next: [...document.querySelectorAll('.st-actions button')].map((b) => ({ label: b.textContent.trim(), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
              describedBy: b.getAttribute('aria-describedby') ? (document.getElementById(b.getAttribute('aria-describedby'))?.textContent || '').trim() : null })),
        live: window.__liveLog.slice(-6).map((x) => x.text || x.mark),
    })""")
    page.close()
    ctx.close()
    return results


def index_error(page):
    """Your Index: make a setting invalid and read back how it is said."""
    pf.go(page, "yourindex")
    page.locator("#main h1", has_text="Your Index").first.wait_for()
    page.evaluate(HELPERS_JS)
    name = page.locator("#yi-name")
    before = name.input_value()
    name.fill("")
    page.wait_for_timeout(600)
    r = page.evaluate("""() => {
        const el = document.querySelector('#yi-name');
        const ids = (el.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
        return { invalid: el.getAttribute('aria-invalid'), describedBy: ids.map((i) => (document.getElementById(i)?.textContent || '').trim()),
                 runDisabled: [...document.querySelectorAll('button')].find((b) => /Run Your Index/.test(b.textContent))?.disabled,
                 runWhy: (document.getElementById('yi-run-why')?.textContent || '').trim(),
                 alerts: [...document.querySelectorAll('.yi [role=alert]')].map((a) => a.textContent.trim().slice(0, 200)) };
    }""")
    low, high = page.get_by_label("No Credit At", exact=True), page.get_by_label("Full Credit At", exact=True)
    r["numberFields"] = low.count()
    if low.count() and high.count():
        low.first.fill("10")
        high.first.fill("10")
        page.wait_for_timeout(600)
        r["sameEnds"] = page.evaluate("""() => [...document.querySelectorAll('.yi-crit [aria-invalid=true]')].map((el) => ({
            label: el.labels && el.labels[0] ? el.labels[0].textContent.trim() : el.getAttribute('aria-label'),
            describedBy: (el.getAttribute('aria-describedby') || '').split(' ').filter(Boolean).map((i) => (document.getElementById(i)?.textContent || '').trim()) }))""")
    name.fill(before or "Accessibility check index")
    return r


def dialog_check(page):
    pf.go(page, "start")
    page.locator("#main h1", has_text="Rank Your").first.wait_for()
    link = page.locator(".nav-sidebar a[href='#faq']")
    link.focus()
    page.keyboard.press("Enter")
    page.locator("dialog.app-faq[open]").wait_for()
    inside = page.evaluate("() => !!document.activeElement.closest('dialog')")
    # A modal dialog makes the page behind it inert: Tab may pass to the browser's own controls
    # (the document body is then the active element) but must never reach the page behind.
    behind = []
    for _ in range(25):
        page.keyboard.press("Tab")
        where = page.evaluate("() => { const a = document.activeElement; return !a || a === document.body ? 'browser' : a.closest('dialog') ? 'dialog' : window.__w.describe(a); }")
        if where not in ("browser", "dialog"):
            behind.append(where)
    stays = not behind
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    closed = page.locator("dialog.app-faq[open]").count() == 0
    back = page.evaluate("() => document.activeElement && document.activeElement.getAttribute('href') === '#faq'")
    return {"focusMovesIn": inside, "tabNeverReachesPageBehind": stays, "reachedBehind": behind[:5], "escapeCloses": closed, "focusReturnsToLink": back}


def step_menu_on_input(page):
    """3.2.2: the compact step menu (below 1024 px) goes to the chosen step as soon as its value changes."""
    page.set_viewport_size({"width": 390, "height": 844})
    pf.go(page, "results")
    page.locator("#main h1", has_text="Results").first.wait_for()
    menu = page.locator(".app-compact select")
    menu.focus()
    before = page.evaluate("() => location.hash")
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(500)
    after_key = page.evaluate("() => ({ hash: location.hash, focus: window.__w ? window.__w.describe(document.activeElement) : document.activeElement.tagName })")
    page.keyboard.press("Escape")
    pf.go(page, "results")
    page.locator("#main h1", has_text="Results").first.wait_for()
    # What a browser that changes the value on arrow keys (Chrome and Edge on Windows, Firefox) sends: one change event.
    menu.select_option("run")
    page.wait_for_timeout(500)
    after_change = page.evaluate("() => ({ hash: location.hash, h1: document.querySelector('#main h1')?.textContent, focus: document.activeElement.tagName + ' ' + (document.activeElement.textContent || '').slice(0, 30) })")
    pf.go(page, "results")
    page.set_viewport_size({"width": 1440, "height": 900})
    return {"before": before, "afterArrowUpHere": after_key, "afterOneChange": after_change}


def map_keyboard(page):
    """The map canvas takes arrow keys; Tab must still leave it."""
    canvas = page.locator(".maplibregl-canvas")
    if not canvas.count():
        return {"skipped": "map not shown"}
    canvas.focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Tab")
    left = page.evaluate("() => !document.activeElement.classList.contains('maplibregl-canvas')")
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Shift+Tab")
    back_out = page.evaluate("() => !document.activeElement.classList.contains('maplibregl-canvas')")
    markers = page.locator(".rs-marker").count()
    return {"tabLeavesCanvas": left, "shiftTabLeaves": back_out, "markersAsButtons": markers,
            "canvasLabel": canvas.get_attribute("aria-label")}


def downloads(page, out_dir):
    pf.go(page, "report")
    page.locator("#main h1", has_text="Report").first.wait_for()
    page.locator(".rp-sheet .rp").first.wait_for(timeout=120_000)
    saved = {}
    dl = out_dir / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    for label in ["Download .html: Report", "Download .pdf: Accessible PDF", "Download .docx: Word Document"]:
        mark(page, f"Report: {label}")
        with page.expect_download(timeout=240_000) as d:
            page.get_by_role("button", name=label, exact=True).click()
        path = dl / d.value.suggested_filename
        d.value.save_as(str(path))
        saved[label] = str(path)
        page.wait_for_function("() => /Saved/.test(document.querySelector('.rp-dl-foot')?.textContent || '')", timeout=60_000)
    return saved


# ---------------------------------------------------------------- documents

def check_pdf(path):
    import pdfplumber
    import subprocess

    out = {"file": Path(path).name}
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    out["pdfinfo"] = {k.strip(): v.strip() for k, v in (ln.split(":", 1) for ln in info.splitlines() if ":" in ln)
                      if k.strip() in ("Title", "Tagged", "Pages", "PDF version", "Producer", "Creator", "UserProperties")}
    with pdfplumber.open(path) as pdf:
        cat = pdf.doc.catalog
        def res(x):
            from pdfminer.pdftypes import resolve1
            return resolve1(x)
        out["lang"] = (res(cat.get("Lang")) or b"").decode() if isinstance(res(cat.get("Lang")), bytes) else str(res(cat.get("Lang")))
        mark_info = res(cat.get("MarkInfo")) or {}
        out["markInfo"] = {k: str(res(v)) for k, v in mark_info.items()}
        vp = res(cat.get("ViewerPreferences")) or {}
        out["displayDocTitle"] = str(res(vp.get("DisplayDocTitle"))) if vp else None
        out["outlines"] = "Outlines" in cat
        meta = res(cat.get("Metadata"))
        if meta is not None:
            xmp = meta.get_data().decode("utf-8", "replace")
            out["pdfuaPart"] = (re.search(r"pdfuaid:part[>=\"']+(\d)", xmp) or [None, None])[1]
        tree = pdf.structure_tree
        types = collections.Counter()
        order = []
        figures = []

        def walk(nodes, depth=0):
            for n in nodes:
                t = n.get("type")
                types[t] += 1
                text_ = ""
                if t and (t.startswith("H") or t in ("Caption", "TH", "Figure")):
                    order.append({"type": t, "alt": n.get("alt_text"), "depth": depth})
                if t == "Figure":
                    figures.append({"alt": n.get("alt_text"), "actual": n.get("actual_text")})
                walk(n.get("children", []), depth + 1)
                _ = text_

        walk(tree)
        out["structTypes"] = dict(types.most_common())
        out["figures"] = figures
        # Headings with their text, from the marked content each heading tags.
        heads = []
        for pno, page in enumerate(pdf.pages):
            try:
                st = page.structure_tree
            except Exception:  # noqa: BLE001
                continue
            mc = collections.defaultdict(str)
            for ch in page.chars:
                if ch.get("mcid") is not None:
                    mc[ch["mcid"]] += ch["text"]

            def collect(nodes):
                for n in nodes:
                    t = n.get("type", "")
                    if re.fullmatch(r"H\d?", t or "") or t == "Title":
                        txt = "".join(mc.get(m, "") for m in n.get("mcids", []) or [])
                        if not txt:
                            for c in n.get("children", []):
                                txt += "".join(mc.get(m, "") for m in c.get("mcids", []) or [])
                        heads.append({"page": pno + 1, "type": t, "text": txt.strip()[:90]})
                    collect(n.get("children", []))

            collect(st)
        out["headingsInOrder"] = heads
        # Tables: header cells and their scope.
        th_scope = collections.Counter()

        def tables(nodes):
            for n in nodes:
                if n.get("type") == "TH":
                    th_scope[str((n.get("attributes") or {}).get("Scope"))] += 1
                tables(n.get("children", []))

        tables(tree)
        out["thScope"] = dict(th_scope)
        # Text that is drawn but not tagged (artifacts are expected for headers, footers and page numbers).
        untagged = 0
        total = 0
        for page in pdf.pages:
            for ch in page.chars:
                total += 1
                if ch.get("mcid") is None:
                    untagged += 1
        out["chars"] = total
        out["charsWithoutMcid"] = untagged
    return out


def check_docx(path):
    z = zipfile.ZipFile(path)
    doc = z.read("word/document.xml").decode("utf-8")
    styles = z.read("word/styles.xml").decode("utf-8") if "word/styles.xml" in z.namelist() else ""
    core = z.read("docProps/core.xml").decode("utf-8") if "docProps/core.xml" in z.namelist() else ""
    out = {"file": Path(path).name}
    out["title"] = (re.search(r"<dc:title>(.*?)</dc:title>", core) or [None, None])[1]
    out["languages"] = sorted(set(re.findall(r'<w:lang [^>]*w:val="([^"]+)"', doc + styles)))
    out["headingStyles"] = dict(collections.Counter(re.findall(r'<w:pStyle w:val="(Heading\d|Title)"', doc)))
    tbls = re.findall(r"<w:tbl>.*?</w:tbl>", doc, flags=re.S)
    out["tables"] = len(tbls)
    out["tablesWithHeaderRow"] = sum(1 for t in tbls if "<w:tblHeader" in t)
    out["tableCaptionsOrDescriptions"] = sum(1 for t in tbls if "<w:tblCaption" in t or "<w:tblDescription" in t)
    pics = re.findall(r"<wp:docPr [^>]*>", doc)
    out["images"] = len(pics)
    out["imagesWithAlt"] = sum(1 for p in pics if re.search(r'descr="[^"]+"', p))
    out["imagesDecorative"] = doc.count("adec:decorative") + doc.count("a16:decorative")
    out["imageAlt"] = [re.search(r'descr="([^"]*)"', p).group(1)[:120] if re.search(r'descr="([^"]*)"', p) else None for p in pics]
    out["emptyParagraphsUsedForSpace"] = len(re.findall(r"<w:p>\s*</w:p>|<w:p/>", doc))
    out["hyperlinks"] = doc.count("<w:hyperlink")
    return out


def check_html(path):
    s = Path(path).read_text(encoding="utf-8")
    return {"file": Path(path).name, "lang": (re.search(r'<html[^>]*lang="([^"]+)"', s) or [None, None])[1],
            "title": (re.search(r"<title>(.*?)</title>", s, re.S) or [None, None])[1],
            "h1": len(re.findall(r"<h1[\s>]", s)), "h2": len(re.findall(r"<h2[\s>]", s)), "h3": len(re.findall(r"<h3[\s>]", s)),
            "tables": len(re.findall(r"<table[\s>]", s)), "captions": len(re.findall(r"<caption[\s>]", s)),
            "thScopeCol": len(re.findall(r'<th[^>]*scope="col"', s)), "thScopeRow": len(re.findall(r'<th[^>]*scope="row"', s)),
            "imgs": len(re.findall(r"<img[\s>]", s)), "svgs": len(re.findall(r"<svg[\s>]", s)),
            "scripts": len(re.findall(r"<script[\s>]", s))}


def twelve_sites(out_dir):
    """Example City with six more invented sites (Your Index ranks only with 10 or more)."""
    sample = (Path(__file__).resolve().parents[1] / "app/public/samples/example-city.csv").read_text(encoding="utf-8").splitlines()
    rows = [sample[0], *sample[1:]]
    for line in sample[1:7]:
        new = line.replace("EXC-0", "EXC-1", 1).replace("Example City ", "Example City East ", 1)
        new = re.sub(r",(4[45]\.\d+),", lambda m: "," + f"{float(m.group(1)) + 0.02:.3f}" + ",", new, count=1)
        rows.append(new)
    path = out_dir / "error-files" / "example-city-12.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def index_session(browser, base, out_dir, skip):
    """A second session with twelve invented sites, so Your Index ranks and shows its results."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=DSF, bypass_csp=True)
    ctx.add_init_script(LIVE_LOG_JS)
    page = ctx.new_page()
    page.goto(pf.app_url(base, False))
    page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    page.get_by_role("button", name="Start a New Project", exact=True).click()
    page.locator("#main h1", has_text="Upload").first.wait_for()
    page.locator("input[type=file]").set_input_files(str(twelve_sites(out_dir)))
    page.locator("#found-title").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    page.get_by_role("button", name="Continue to Map Columns", exact=True).click()
    page.locator("#main h1", has_text="Map Columns").first.wait_for()
    acc = page.get_by_role("button", name="Accept All Matched", exact=True)
    if acc.count():
        acc.first.click()
    page.get_by_role("button", name="Continue to Check", exact=True).click()
    page.locator(".st-coverage").wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    nxt = page.get_by_role("button", name="Continue to Public Data", exact=True)
    if nxt.count():
        nxt.click()
        page.locator("#main h1", has_text="Public Data").first.wait_for()
    page.get_by_role("button", name="Continue to Run", exact=True).click()
    page.get_by_role("button", name="Run the Model", exact=True).click()
    page.locator("#main h1", has_text="Results").first.wait_for(timeout=pf.BOOT_TIMEOUT_MS)
    info: dict = {}
    your_columns_and_index(page, info)
    info["refused"] = page.locator(".yi-refused").count() > 0
    info["screen"] = check_screen(page, "yourindex-ranked", skip)
    info["exploreScreen"] = check_screen(page, "explore-twelve", skip)
    info["errors"] = index_error(page) if "errors" not in skip else None
    info["liveLog"] = page.evaluate("() => window.__liveLog")
    ctx.close()
    return info


def check_screen(page, screen, skip):
    """Every per-screen check, in light first, then the other themes and window sizes."""
    r: dict = {}
    page.set_viewport_size({"width": 1440, "height": 900})
    set_theme(page, "light", "no-preference")
    show(page, screen)
    if screen == "map":
        # Your Columns open, one card's editor open.
        if page.locator("#yc-panel[hidden]").count():
            page.get_by_role("button", name="Review Your Columns").click()
        page.locator(".yc-list").wait_for(timeout=60_000)
        ed = page.locator(".yc-list > li .yc-card__actions button").first
        if ed.get_attribute("aria-expanded") != "true":
            ed.click()
        page.evaluate("() => window.scrollTo(0, 0)")
    r["structure"] = page.evaluate("() => window.__w.structure()")
    r["targets1440"] = page.evaluate("() => window.__w.targets()")
    if AXE_PATH:
        r["axe"] = {}
        for scheme, contrast in THEMES:
            theme = set_theme(page, scheme, contrast)
            r["axe"][f"{theme} 1440x900"] = run_axe(page, AXE_PATH)
        set_theme(page, "light", "no-preference")
        n = sum(len(v["nodes"]) for x in r["axe"].values() for v in x["violations"])
        print(f"   axe: {n} violation nodes in four themes", flush=True)
    if "focus" not in skip:
        r["focus"] = {}
        for scheme, contrast in THEMES:
            theme = set_theme(page, scheme, contrast)
            walk = focus_walk(page, pixels=contrast == "no-preference")
            r["focus"][theme] = summarise_focus(walk)
            if theme == "light":
                r["focus"]["light"]["raw"] = walk["stops"]
            print(f"   focus {theme}: {r['focus'][theme]['count']} stops, ended: {walk['ended']}", flush=True)
    if "contrast" not in skip:
        r["nontext"], r["undecidedText"], r["placeholders"] = {}, {}, {}
        for scheme, contrast in THEMES:
            theme = set_theme(page, scheme, contrast)
            page.evaluate("() => window.scrollTo(0, 0)")
            r["nontext"][theme] = nontext(page)
            r["undecidedText"][theme] = undecided_text(page)
            r["placeholders"][theme] = page.evaluate("() => window.__w.placeholders()")
        set_theme(page, "light", "no-preference")
    if "spacing" not in skip:
        page.evaluate("() => window.scrollTo(0, 0)")
        r["textSpacing1440"] = text_spacing(page)
    # Narrow: focus not covered by the compact bar, spacing, targets.
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(250)
    page.evaluate("() => window.scrollTo(0, 0)")
    if "focus" not in skip:
        walk = focus_walk(page, pixels=False)
        r["focus390"] = summarise_focus(walk)
        print(f"   focus 390: {r['focus390']['count']} stops, hidden {len(r['focus390']['entirelyHidden'])}", flush=True)
    r["targets390"] = page.evaluate("() => window.__w.targets()")
    if AXE_PATH:
        r["axe"]["light 390x844"] = run_axe(page, AXE_PATH)
    if "contrast" not in skip:
        r["undecidedText390"] = {}
        for scheme, contrast in THEMES:
            theme = set_theme(page, scheme, contrast)
            page.evaluate("() => window.scrollTo(0, 0)")
            r["undecidedText390"][theme] = undecided_text(page)
        set_theme(page, "light", "no-preference")
    if "spacing" not in skip:
        r["textSpacing390"] = text_spacing(page)
    if "zoom" not in skip:
        r["zoom"] = {}
        for label, (w, h) in {"200% of 1440x900": (720, 450), "400% of 1280x1024": (320, 256), "320x640": (320, 640)}.items():
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(250)
            page.evaluate("() => window.scrollTo(0, 0)")
            r["zoom"][label] = zoom_state(page)
            if label == "400% of 1280x1024" and "focus" not in skip:
                walk = focus_walk(page, pixels=False)
                s = summarise_focus(walk)
                r["zoom"][label]["focus"] = {"count": s["count"], "entirelyHidden": s["entirelyHidden"], "partlyCovered": len(s["partlyCovered"])}
    page.set_viewport_size({"width": 1440, "height": 900})
    return r


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--no-map", action="store_true", help="do not show the Results map (it contacts tiles.openfreemap.org)")
    ap.add_argument("--screens", default=",".join(SCREENS))
    ap.add_argument("--skip", default="", help="comma list of sections to skip: focus,contrast,spacing,zoom,errors,downloads,index")
    ap.add_argument("--axe", help="path to axe.min.js (4.13.0, as CI pins): also run axe-core on every screen visited")
    args = ap.parse_args()
    global AXE_PATH
    AXE_PATH = args.axe
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    skip = set(filter(None, args.skip.split(",")))
    screens = args.screens.split(",")
    report: dict = {"base": args.base, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "screens": {}, "setup": {}}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        report["browser"] = f"chromium {browser.version}"
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=DSF, bypass_csp=True, accept_downloads=True)
        ctx.add_init_script(LIVE_LOG_JS)
        page = ctx.new_page()
        watch = pf.Watch(urlparse_origin(args.base))
        watch.attach(page)
        report["setup"]["timing"] = pf.run_flow(page, args.base, False)
        mark(page, "flow done")
        your_columns_and_index(page, report["setup"])
        results_actions(page)
        if not args.no_map:
            show_map(page, report["setup"])
            report["setup"]["mapKeyboard"] = map_keyboard(page)
        page.evaluate(HELPERS_JS)
        report["hoverReveals"] = page.evaluate("() => window.__w.reveals()")

        for screen in screens:
            print(f"== {screen}", flush=True)
            report["screens"][screen] = check_screen(page, screen, skip)

        page.set_viewport_size({"width": 1440, "height": 900})
        set_theme(page, "light", "no-preference")
        report["dialog"] = dialog_check(page)
        report["stepMenu"] = step_menu_on_input(page)
        if "downloads" not in skip:
            report["downloads"] = downloads(page, out)
        report["liveLog"] = page.evaluate("() => window.__liveLog")
        report["consoleErrors"] = watch.errors
        report["offsite"] = sorted(set(watch.offsite))
        ctx.close()
        if "index" not in skip:
            report["yourIndexRanked"] = index_session(browser, args.base, out, skip)
        if "errors" not in skip:
            report["errors"] = error_checks(browser, args.base, out)
        browser.close()

    if "downloads" not in skip:
        docs = {}
        for label, path in report["downloads"].items():
            try:
                docs[label] = check_pdf(path) if path.endswith(".pdf") else check_docx(path) if path.endswith(".docx") else check_html(path)
            except Exception as e:  # noqa: BLE001
                docs[label] = {"error": repr(e)}
        report["documents"] = docs
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (out / "wcag.json").write_text(json.dumps(report, indent=1, default=str))
    print(f"Wrote {out / 'wcag.json'}")
    return 0


def urlparse_origin(base: str) -> str:
    from urllib.parse import urlparse
    u = urlparse(base)
    return f"{u.scheme}://{u.netloc}"


if __name__ == "__main__":
    sys.exit(main())
