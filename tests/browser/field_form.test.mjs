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
 * Zero dependencies, deliberately
 * -------------------------------
 * Chrome is driven over the DevTools Protocol using node's built-in `WebSocket` (Node 22+).
 * No puppeteer, no playwright, no jsdom. This repository keeps its test dependencies to what
 * ships with the runtime, and a browser harness is not a good reason to break that.
 *
 * Skips rather than fails when Chrome or the server is absent, so CI without a browser stays
 * green — the skip is loud in the output.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME_CANDIDATES = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
];

const PAGE = process.env.PLATFORM_URL || "http://127.0.0.1:8799/index.html";

const chromePath = CHROME_CANDIDATES.find((p) => existsSync(p));

async function serverIsUp() {
  try {
    const res = await fetch(PAGE, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

const available = chromePath && (await serverIsUp());
const skip = !available
  ? `SKIPPED: ${!chromePath ? "no Chrome binary found" : `nothing serving ${PAGE}`}`
  : false;

// ---------------------------------------------------------------- a tiny CDP client

class Chrome {
  constructor(proc, socket, profileDir) {
    this.proc = proc;
    this.socket = socket;
    this.profileDir = profileDir;
    this.nextId = 1;
    this.pending = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (this.pending.delete(id)) reject(new Error(`${method} timed out`));
      }, 20000);
    });
  }

  /** Evaluate an expression in the page and return its value. */
  async eval(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression, returnByValue: true, awaitPromise: true,
    });
    if (result.exceptionDetails) {
      throw new Error(`page threw: ${result.exceptionDetails.text} ` +
        `${result.exceptionDetails.exception?.description || ""}`);
    }
    return result.result.value;
  }

  async close() {
    try { this.socket.close(); } catch { /* already gone */ }
    this.proc.kill("SIGTERM");
    try { rmSync(this.profileDir, { recursive: true, force: true }); } catch { /* best effort */ }
  }
}

async function launch(url) {
  const profileDir = mkdtempSync(join(tmpdir(), "fcf-chrome-"));
  const proc = spawn(chromePath, [
    "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=0", `--user-data-dir=${profileDir}`, url,
  ], { stdio: ["ignore", "pipe", "pipe"] });

  // Chrome prints the DevTools websocket URL to stderr once it is listening.
  const wsUrl = await new Promise((resolve, reject) => {
    let buffer = "";
    const timer = setTimeout(() => reject(new Error("Chrome never announced a DevTools port")), 20000);
    proc.stderr.on("data", (chunk) => {
      buffer += chunk.toString();
      const match = buffer.match(/ws:\/\/[^\s]+/);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
    proc.on("exit", (code) => { clearTimeout(timer); reject(new Error(`Chrome exited ${code}`)); });
  });

  // Attach to the page target rather than the browser endpoint.
  const base = wsUrl.replace(/^ws:\/\//, "http://").replace(/\/devtools\/browser\/.*$/, "");
  let pageWs = null;
  for (let attempt = 0; attempt < 40 && !pageWs; attempt++) {
    const targets = await fetch(`${base}/json/list`).then((r) => r.json()).catch(() => []);
    const page = targets.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
    if (page) pageWs = page.webSocketDebuggerUrl;
    else await new Promise((r) => setTimeout(r, 250));
  }
  if (!pageWs) throw new Error("no page target appeared");

  const socket = new WebSocket(pageWs);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  const chrome = new Chrome(proc, socket, profileDir);
  await chrome.send("Runtime.enable");

  // Wait for the app to finish building the form, rather than sleeping and hoping.
  for (let attempt = 0; attempt < 60; attempt++) {
    const ready = await chrome.eval(`!!document.querySelector("#f-site_id")`).catch(() => false);
    if (ready) return chrome;
    await new Promise((r) => setTimeout(r, 250));
  }
  await chrome.close();
  throw new Error("the entry form never rendered");
}

// ---------------------------------------------------------------- the tests

let chrome;

test.before(async () => { if (available) chrome = await launch(PAGE); });
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
