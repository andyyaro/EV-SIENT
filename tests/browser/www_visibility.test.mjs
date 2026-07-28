/**
 * The public site's caveats must be VISIBLE, not merely present in the markup.
 *
 * Why this exists
 * ---------------
 * `scripts/check_site_www.py` asserts that each page contains the authority disclaimer, the
 * source-vintage footer, and the sentence "placeholder at all twelve sites". Every one of those
 * checks passed on `index.html` while a reader could see **none** of them.
 *
 * The home page is a full-viewport `<iframe>` onto a third-party host. The iframe was
 * `position:absolute; top:0` over the whole viewport, so it painted straight over the
 * disclaimer — `document.elementFromPoint` at the disclaimer's own centre returned the IFRAME —
 * and `body{overflow:hidden}` meant the footer below it could not be scrolled to. The study's
 * single most important limitation was in the bytes and invisible on the screen.
 *
 * A string check cannot catch that. Only a layout engine can. So this asks the question a
 * reader would: *is the caveat the thing that is actually on screen at that point?*
 *
 * Deliberately narrow: it checks the two bands this repository controls. It does NOT try to
 * verify the iframe's contents, which are third-party and unverifiable by design.
 */

import test from "node:test";
import assert from "node:assert/strict";

import { launch, skipReason } from "./chrome_harness.mjs";

const BASE = process.env.WWW_URL || "http://127.0.0.1:8877";

const PAGES = ["index.html", "results.html", "methodology.html", "dashboard.html"];

const skip = await skipReason(`${BASE}/index.html`);
const available = !skip;

/** What a reader actually meets at the centre of the named element. */
const inspect = (chrome, selector) => chrome.eval(`(() => {
  const el = document.querySelector(${JSON.stringify(selector)});
  if (!el) return { missing: true };
  const r = el.getBoundingClientRect();
  const style = getComputedStyle(el);
  const cx = Math.min(Math.max(r.left + r.width / 2, 1), window.innerWidth - 1);
  const cy = Math.min(Math.max(r.top + r.height / 2, 1), window.innerHeight - 1);
  const hit = document.elementFromPoint(cx, cy);
  return {
    missing: false,
    width: Math.round(r.width),
    height: Math.round(r.height),
    withinViewport: r.top < window.innerHeight && r.bottom > 0,
    covered: !(hit === el || el.contains(hit) || el.contains(hit?.parentElement)),
    coveredBy: hit ? hit.tagName + "." + String(hit.className || "") : null,
    display: style.display,
    visibility: style.visibility,
    opacity: style.opacity,
  };
})()`);

for (const page of PAGES) {
  test(`${page}: the authority disclaimer is on screen, not painted over`, { skip }, async () => {
    const chrome = await launch(`${BASE}/${page}`,
      `!!document.querySelector(".fcf-authority")`,
      `${page} never rendered a .fcf-authority disclaimer`);
    try {
      const seen = await inspect(chrome, ".fcf-authority");
      assert.equal(seen.missing, false, `${page} has no authority disclaimer at all`);
      assert.notEqual(seen.display, "none", `${page}: disclaimer is display:none`);
      assert.notEqual(seen.visibility, "hidden", `${page}: disclaimer is visibility:hidden`);
      assert.ok(Number(seen.opacity) > 0.5, `${page}: disclaimer is transparent`);
      assert.ok(seen.height > 0 && seen.width > 0, `${page}: disclaimer has no area`);
      assert.equal(seen.covered, false,
        `${page}: the disclaimer is painted over by ${seen.coveredBy} — a reader cannot see it`);
    } finally {
      await chrome.close();
    }
  });
}

test("index.html: nothing important is stranded below an unscrollable fold", { skip }, async () => {
  // The original failure had two halves. The iframe covered the disclaimer, AND
  // body{overflow:hidden} put the vintage footer past a fold that could not be scrolled to.
  // Fixing only the first would leave the second.
  const chrome = await launch(`${BASE}/index.html`,
    `!!document.querySelector(".fcf-vintage")`, "no vintage footer");
  try {
    const state = await chrome.eval(`(() => {
      const f = document.querySelector(".fcf-vintage");
      const r = f.getBoundingClientRect();
      return {
        footerVisible: r.top < window.innerHeight && r.bottom > 0,
        overflow: getComputedStyle(document.body).overflow,
        scrollable: document.documentElement.scrollHeight > window.innerHeight + 1,
      };
    })()`);
    if (!state.footerVisible) {
      assert.ok(state.scrollable,
        "the source-vintage footer is off screen AND the page cannot scroll to it");
    }
  } finally {
    await chrome.close();
  }
});

test("index.html: the capacity sentence is inside something a reader can see", { skip }, async () => {
  const chrome = await launch(`${BASE}/index.html`,
    `!!document.querySelector(".fcf-authority")`, "no disclaimer");
  try {
    const shown = await chrome.eval(`(() => {
      const el = document.querySelector(".fcf-authority");
      return { text: el.innerText || "", rendered: el.getClientRects().length > 0 };
    })()`);
    assert.ok(shown.rendered, "the element carrying the capacity sentence renders no boxes");
    assert.match(shown.text, /placeholder at all twelve sites/i,
      "the rendered disclaimer text does not contain the capacity sentence");
  } finally {
    await chrome.close();
  }
});
