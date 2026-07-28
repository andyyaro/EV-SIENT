/**
 * The first thing anyone sees in the 3D explorer is a dialog asking for a Cesium ion token.
 *
 * Why this is a browser test
 * -------------------------
 * Phase 9's rule is that approachability is a property of the *path in*. For this feature the
 * path in is a modal that, until it was rewritten, opened by asking a non-technical reader for
 * an API token — a thing they do not have, cannot easily get, and do not need. Everything the
 * study contains works without one.
 *
 * That is not a claim a source-reading check can make. Whether the reader's first action is
 * "continue" or "paste a token" depends on what actually renders and what is actually
 * focusable, so it is asserted here against a real browser.
 *
 * Deliberately NOT asserted: that the map initialises. The vendored CesiumJS is gitignored
 * (~20 MB, DEC-002) so a clean clone falls back to the pinned CDN, and a test that needed the
 * globe to draw would pass on this machine and fail in CI for reasons unrelated to the gate.
 * The gate itself is plain HTML shown before any of that, which is exactly why it is testable.
 */

import test from "node:test";
import assert from "node:assert/strict";

import { launch, skipReason } from "./chrome_harness.mjs";

const PAGE = process.env.EXPLORER_URL || "http://127.0.0.1:8799/explorer/index.html";

const skip = await skipReason(PAGE);
const available = !skip;

let chrome;

test.before(async () => {
  if (available) {
    chrome = await launch(
      PAGE,
      `!!document.querySelector("#tokenGate") &&
       !document.querySelector("#tokenGate").classList.contains("hidden")`,
      "the token gate never became visible");
  }
});
test.after(async () => { if (chrome) await chrome.close(); });

test("the gate's FIRST action continues without a token", { skip }, async () => {
  // The whole point. A reader with no Cesium account must not have to work out that the
  // secondary button is the one for them.
  const first = await chrome.eval(
    `document.querySelector("#tokenGate button")?.id`);
  assert.equal(first, "tokenSkip",
    "the first button in the dialog must be the one that needs nothing from the reader");
});

test("the gate does not open by demanding a token", { skip }, async () => {
  const heading = await chrome.eval(
    `document.getElementById("tokenGateTitle")?.textContent.trim()`);
  assert.doesNotMatch(heading, /token|ion|key|api/i,
    `the first words a reader reads must not be jargon: ${heading}`);
});

test("the gate says plainly that nothing is lost by skipping", { skip }, async () => {
  const text = await chrome.eval(`document.getElementById("tokenGate").innerText`);
  assert.match(text, /without|skip|nothing/i, text);
  // Identical epistemics: it must not oversell the token either.
  assert.doesNotMatch(text, /required|must have|you need a/i,
    `the token is optional and the copy must not imply otherwise: ${text}`);
});

test("skipping actually dismisses the gate", { skip }, async () => {
  const hidden = await chrome.eval(`(() => {
    document.getElementById("tokenSkip").click();
    return document.getElementById("tokenGate").classList.contains("hidden");
  })()`);
  assert.equal(hidden, true, "clicking continue must dismiss the dialog");
});

// ------------------------------------------------------------------ accessibility

test("the dialog announces itself as a dialog", { skip }, async () => {
  const roles = await chrome.eval(`(() => {
    const g = document.getElementById("tokenGate");
    return { role: g.getAttribute("role"), modal: g.getAttribute("aria-modal"),
             labelled: g.getAttribute("aria-labelledby") };
  })()`);
  assert.equal(roles.role, "dialog");
  assert.equal(roles.modal, "true");
  assert.ok(roles.labelled, "a dialog with no accessible name is unannounceable");
  const labelTarget = await chrome.eval(
    `!!document.getElementById(${JSON.stringify(roles.labelled)})`);
  assert.ok(labelTarget, "aria-labelledby points at an element that does not exist");
});

test("the token input has a real label, not just a placeholder", { skip }, async () => {
  // A placeholder is not an accessible name: it disappears on focus and screen readers
  // treat it inconsistently.
  const labelled = await chrome.eval(`(() => {
    const input = document.getElementById("tokenInput");
    const label = document.querySelector('label[for="tokenInput"]');
    return { hasLabel: !!label, text: label?.textContent.trim() || null,
             describedBy: input.getAttribute("aria-describedby") };
  })()`);
  assert.ok(labelled.hasLabel, "#tokenInput has no <label for>");
  assert.ok(labelled.text && labelled.text.length > 0, "the label is empty");
});

test("every control in the gate is reachable by keyboard", { skip }, async () => {
  const unreachable = await chrome.eval(`(() => {
    const gate = document.getElementById("tokenGate");
    return [...gate.querySelectorAll("button, input")]
      .filter((el) => el.tabIndex < 0 || el.disabled)
      .map((el) => el.id || el.tagName);
  })()`);
  assert.deepEqual(unreachable, [], `not keyboard reachable: ${JSON.stringify(unreachable)}`);
});

// ------------------------------------------------------------------ reduced motion

test("a reader who asks for reduced motion gets no camera flight", { skip }, async () => {
  // The strongest motion in this app is a 2-second camera swoop across a globe, which is a
  // classic vestibular trigger. Asserting the CSS media query exists would prove nothing:
  // the flight duration is set in JavaScript, so the only honest check is to emulate the
  // preference and read back the duration the app would actually use.
  await chrome.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "reduce" }],
  });
  const reduced = await chrome.eval(`flightDuration(2.0)`);
  assert.equal(reduced, 0, "a reduced-motion reader would still be flown across the globe");

  await chrome.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "no-preference" }],
  });
  const normal = await chrome.eval(`flightDuration(2.0)`);
  assert.equal(normal, 2.0, "everyone else must keep the flight");
});
