/**
 * The public site must work on a phone: no sideways scrolling, thumb-sized primary links, and a
 * home page that does not hand a phone a desktop-only third-party layout.
 *
 * Why this exists
 * ---------------
 * Rendered at 390 px (an iPhone 15) the site had three faults no string check could see:
 * `results.html` laid out at 484 px and `methodology.html` at 414 px, so both scrolled
 * sideways; every primary nav link was 29 px tall against a 44 px touch minimum; and the home
 * page was a Framer iframe laid out at a fixed 1 200 px, so a phone saw a cropped corner of it.
 *
 * Phone widths are emulated over DevTools (`Emulation.setDeviceMetricsOverride`, `mobile:
 * true`), which applies the viewport meta tag the way a phone does - including widening the
 * layout viewport to fit content that overflows, which is exactly the failure being caught.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { launch, skipReason } from "./chrome_harness.mjs";

const BASE = process.env.WWW_URL || "http://127.0.0.1:8877";
const PAGES = ["index.html", "results.html", "methodology.html", "dashboard.html",
  "assistant.html", "privacy.html", "standards.html"];
// 320 is the narrowest phone still in use (iPhone SE 1st gen); 390 the most common iPhone.
const WIDTHS = [320, 390];

const skip = await skipReason(`${BASE}/index.html`);

/** Open `page` already laid out at a phone width, then wait for it to finish loading. */
async function openAsPhone(page, width) {
  const chrome = await launch("about:blank", "true");
  await chrome.send("Emulation.setDeviceMetricsOverride", {
    width, height: 844, deviceScaleFactor: 2, mobile: true,
  });
  await chrome.send("Emulation.setTouchEmulationEnabled", { enabled: true });
  await chrome.send("Page.enable");
  await chrome.send("Page.navigate", { url: `${BASE}/${page}` });
  for (let attempt = 0; attempt < 60; attempt++) {
    const ready = await chrome.eval(
      `location.href.endsWith(${JSON.stringify(page)}) && document.readyState === "complete"`,
    ).catch(() => false);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 250));
  }
  // The results gallery and the methodology wheel lay themselves out on the first frames.
  await chrome.eval("new Promise((r) => setTimeout(r, 600))");
  return chrome;
}

for (const width of WIDTHS) {
  for (const page of PAGES) {
    test(`${page} @ ${width}px: no sideways scrolling`, { skip }, async () => {
      const chrome = await openAsPhone(page, width);
      try {
        const m = await chrome.eval(`({
          layout: window.innerWidth,
          content: document.documentElement.scrollWidth,
        })`);
        // A phone widens the layout viewport to fit overflowing content, so both numbers
        // must be checked against the device width, not just against each other.
        assert.equal(m.layout, width,
          `${page}: the phone laid the page out at ${m.layout}px instead of ${width}px - ` +
          `something is wider than the screen, so the page scrolls sideways`);
        assert.ok(m.content <= width,
          `${page}: content is ${m.content}px wide on a ${width}px screen`);
      } finally {
        await chrome.close();
      }
    });
  }
}

test("primary nav links are at least 44px tall on a phone", { skip }, async () => {
  for (const page of ["results.html", "methodology.html", "dashboard.html", "assistant.html"]) {
    const chrome = await openAsPhone(page, 390);
    try {
      const short = await chrome.eval(`[...document.querySelectorAll(".topnav a")]
        .map((a) => [a.textContent.trim(), Math.round(a.getBoundingClientRect().height)])
        .filter(([, h]) => h < 44)`);
      assert.deepEqual(short, [], `${page}: nav links under 44px tall: ${JSON.stringify(short)}`);
    } finally {
      await chrome.close();
    }
  }
});

test("index.html on a phone: the page's own landing shows, and Framer is never fetched", { skip }, async () => {
  const chrome = await openAsPhone("index.html", 390);
  try {
    await chrome.eval("new Promise((r) => setTimeout(r, 1500))");
    const state = await chrome.eval(`(() => {
      const shown = (sel) => { const el = document.querySelector(sel);
        return !!el && el.getClientRects().length > 0; };
      return {
        mobileLanding: shown(".landing-mobile"),
        frameWrap: shown(".landing-wrap"),
        links: [...document.querySelectorAll(".lm-nav a")].map((a) => a.getAttribute("href")),
        framerFetched: performance.getEntriesByType("resource")
          .some((e) => e.name.includes("framer")),
      };
    })()`);
    assert.equal(state.mobileLanding, true, "the phone landing is not displayed");
    assert.equal(state.frameWrap, false, "the desktop Framer iframe is still displayed on a phone");
    assert.equal(state.framerFetched, false,
      "a phone still downloads the Framer page it never shows");
    for (const href of ["dashboard.html", "results.html", "methodology.html", "assistant.html"]) {
      assert.ok(state.links.includes(href), `the phone landing has no link to ${href}`);
    }
  } finally {
    await chrome.close();
  }
});

test("index.html on a desktop still shows the Framer landing", { skip }, async () => {
  const chrome = await launch(`${BASE}/index.html`,
    `document.readyState === "complete"`, "index.html never finished loading");
  try {
    await chrome.send("Emulation.setDeviceMetricsOverride", {
      width: 1280, height: 800, deviceScaleFactor: 1, mobile: false,
    });
    const state = await chrome.eval(`({
      frame: document.querySelector(".landing-wrap").getClientRects().length > 0,
      mobile: document.querySelector(".landing-mobile").getClientRects().length > 0,
    })`);
    assert.equal(state.frame, true, "the Framer landing is hidden on a desktop");
    assert.equal(state.mobile, false, "the phone landing is showing on a desktop");
  } finally {
    await chrome.close();
  }
});
