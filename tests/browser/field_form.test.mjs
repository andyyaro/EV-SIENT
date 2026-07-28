/**
 * Drive the field-entry form in a real browser and check what a person would actually see.
 *
 * Why this exists rather than another unit test
 * --------------------------------------------
 * This program has shipped two blank Tableau sheets and a sign-in page that did not exist,
 * both times because the check verified the step under our control instead of the outcome the
 * reader experiences. The parity test proves the *rules* agree with the model; it says nothing
 * about whether submitting the form does anything, whether a refusal is visible, or whether
 * the page still claims "no field observations have been received" after you have typed one
 * in. Those are the failures a user would hit first, and only a browser can see them.
 *
 * The Chrome-over-DevTools-Protocol client lives in `./chrome_harness.mjs` — zero
 * dependencies, and shared so two browser suites cannot drift apart. Skips rather than fails
 * when Chrome or the server is absent, so CI without a browser stays green; the skip is loud.
 */

import test from "node:test";
import assert from "node:assert/strict";

import { launch, skipReason } from "./chrome_harness.mjs";

const PAGE = process.env.PLATFORM_URL || "http://127.0.0.1:8799/index.html";

const skip = await skipReason(PAGE);
const available = !skip;

// ---------------------------------------------------------------- the tests

let chrome;

test.before(async () => {
  if (available) chrome = await launch(PAGE, '!!document.querySelector("#f-site_id")',
                                     "the entry form never rendered");
});
test.after(async () => { if (chrome) await chrome.close(); });

/** Fill the visible form and press Add. Returns what the page shows afterwards. */
const submit = (values) => chrome.eval(`(() => {
  for (const [name, value] of Object.entries(${JSON.stringify(values)})) {
    const el = document.getElementById("f-" + name);
    if (el) el.value = value;
  }
  document.getElementById("field-form")
    .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  return {
    errors: [...document.querySelectorAll("#field-errors .errlist li")].map((li) => li.textContent),
    invalidFields: [...document.querySelectorAll('#field-fields [aria-invalid="true"]')].map((e) => e.id),
    pendingVisible: !document.getElementById("pending-wrap").hidden,
    pendingRows: document.querySelectorAll("#pending tbody tr").length,
  };
})()`);

const VALID = {
  site_id: "FFX001", observed_date: "2026-07-01", method: "utility_load_study",
  service_capacity_kw: "400", spare_capacity_kw: "120", measured_peak_kw: "180",
  source_org: "Dominion Energy", source_document: "Load study LS-2026-114",
  observer: "A. Yaro", verification_status: "reviewed", notes: "",
};

test("the page loads with no console errors", { skip }, async () => {
  const errors = await chrome.eval(`window.__errs || []`);
  assert.deepEqual(errors, []);
});

test("an unattributed observation is REFUSED, visibly", { skip }, async () => {
  // The defect this whole feature guards against: a row with no source document must not be
  // silently accepted. The person has to SEE the refusal, not just have it happen.
  const result = await submit({ ...VALID, source_document: "", observer: "" });
  assert.ok(result.errors.length >= 2, `expected refusals, got ${JSON.stringify(result.errors)}`);
  assert.ok(result.errors.some((e) => /provenance|source document/i.test(e)),
    `no message explained the attribution rule: ${JSON.stringify(result.errors)}`);
  assert.equal(result.pendingRows, 0, "a refused row must not be queued");
  assert.ok(result.invalidFields.includes("f-source_document"),
    "the offending field itself must be marked, not only the summary");
});

test("a row confirming nothing is REFUSED", { skip }, async () => {
  const result = await submit({ ...VALID, service_capacity_kw: "", spare_capacity_kw: "" });
  assert.ok(result.errors.some((e) => /nothing to confirm/i.test(e)),
    JSON.stringify(result.errors));
  assert.equal(result.pendingRows, 0);
});

test("a negative capacity is REFUSED", { skip }, async () => {
  const result = await submit({ ...VALID, service_capacity_kw: "-1" });
  assert.ok(result.errors.length > 0);
  assert.equal(result.pendingRows, 0);
});

test("a valid observation is accepted and queued", { skip }, async () => {
  const result = await submit(VALID);
  assert.deepEqual(result.errors, [], "a valid row must produce no complaints");
  assert.ok(result.pendingVisible, "the pending table must appear");
  assert.equal(result.pendingRows, 1);
});

test("the queue says plainly that nothing has been submitted", { skip }, async () => {
  const note = await chrome.eval(`document.getElementById("pending-note").textContent`);
  assert.match(note, /nothing has been sent|no number on this page has changed/i,
    `the pending note must not imply the observation was recorded: ${note}`);
});

test("the empty state STILL says no observations have been received", { skip }, async () => {
  // The most tempting lie in this feature. Typing a row into a browser does not give the study
  // any field data, and the headline state must not soften just because a form was filled in.
  const text = await chrome.eval(`document.getElementById("field-state").textContent`);
  assert.match(text, /No field observations have been received/i,
    "queuing a row in the browser must not change what the study claims it has");
});

test("the CSV is built in the model's own column order", { skip }, async () => {
  const csv = await chrome.eval(`(() => {
    const form = FIELD.schema.forms.find((f) => f.id === FIELD.formId);
    const rows = FIELD.pending.filter((p) => p.formId === FIELD.formId).map((p) => p.row);
    return FieldValidate.toCsv(form, rows);
  })()`);
  const [header, first] = csv.trim().split("\n");
  assert.equal(header, "site_id,observed_date,method,service_capacity_kw,spare_capacity_kw," +
    "measured_peak_kw,source_org,source_document,observer,verification_status,notes");
  assert.ok(first.startsWith("FFX001,2026-07-01,utility_load_study,400"), first);
});

test("switching to the session form rebuilds the fields", { skip }, async () => {
  const fields = await chrome.eval(`(() => {
    const kind = document.getElementById("form-kind");
    kind.value = "session";
    kind.dispatchEvent(new Event("change"));
    return [...document.querySelectorAll("#field-fields .fieldrow label")].map((l) => l.textContent);
  })()`);
  assert.ok(fields.some((f) => /Port-hours possible/i.test(f)), JSON.stringify(fields));
  assert.ok(!fields.some((f) => /Source document/i.test(f)),
    "capacity-only fields must not linger after switching forms");
});
