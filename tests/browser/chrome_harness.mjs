/**
 * A tiny Chrome-over-DevTools-Protocol harness, shared by every browser test.
 *
 * Why this is its own module
 * --------------------------
 * It began inside `field_form.test.mjs`. The moment a second browser test needed it, copying
 * it would have produced two CDP clients that drift apart — and a harness that behaves
 * differently in two files is worse than no harness, because a test can then pass for reasons
 * the other file would have caught.
 *
 * Zero dependencies, deliberately
 * -------------------------------
 * Chrome is driven using node's built-in `WebSocket` (Node 22+). No puppeteer, no playwright,
 * no jsdom. This repository keeps its test dependencies to what ships with the runtime, and a
 * browser harness is not a good reason to break that.
 *
 * Every caller skips rather than fails when Chrome or the server is absent, so CI without a
 * browser stays green — and the skip is loud in the output, never silent.
 */

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

export const chromePath = CHROME_CANDIDATES.find((p) => existsSync(p));

export async function serverIsUp(url) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

/** `false` when the suite can run, otherwise a loud reason string for node:test's `skip`. */
export async function skipReason(url) {
  if (!chromePath) return "SKIPPED: no Chrome binary found";
  if (!(await serverIsUp(url))) return `SKIPPED: nothing serving ${url}`;
  return false;
}

export class Chrome {
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

/**
 * Launch headless Chrome on `url` and wait until `readyExpression` evaluates truthy.
 *
 * `readyExpression` is required rather than optional: sleeping and hoping is how a browser
 * test becomes flaky, and every page has some element that means "the app has finished".
 * `whatWasExpected` is only used to make the timeout message say something useful.
 */
export async function launch(url, readyExpression, whatWasExpected = readyExpression) {
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

  // Wait for the app to finish, rather than sleeping and hoping.
  for (let attempt = 0; attempt < 60; attempt++) {
    const ready = await chrome.eval(readyExpression).catch(() => false);
    if (ready) return chrome;
    await new Promise((r) => setTimeout(r, 250));
  }
  await chrome.close();
  throw new Error(`the page never reached its ready state: ${whatWasExpected}`);
}
