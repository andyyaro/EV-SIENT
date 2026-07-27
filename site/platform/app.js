/* Platform web tier.
 *
 * Reads two generated files and nothing else:
 *   provenance_v1.json  — every displayed number's lineage, precomputed by
 *                         fcf_m2.provenance.export_all
 *   operations.json     — what the platform can do, from fcf_m2.operations
 *
 * It computes NOTHING. Not a sum, not a rank, not a derived percentage. The moment this file
 * calculates a displayed value it becomes a second source of truth that can drift from the
 * model, which is the failure the whole contract architecture exists to prevent.
 *
 * The one rule that shapes the rest: a number is rendered only if its provenance resolves.
 * There is no "unknown" branch, because "unknown" looks like an answer.
 */

"use strict";

const STATE = {
  prov: null, ops: null, horizon: null, scenario: null,
  // Which tier this page is running in, DETECTED rather than configured.
  //
  // One file serves both. Asking the server settles it: a desktop session answers
  // /api/operations, the deployed static site 404s. A build-time flag would mean two
  // builds, and two builds drift.
  tier: "both", token: null,
};

const $ = (sel) => document.querySelector(sel);

async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

/* ------------------------------------------------------------------ formatting */

/* Formatting is presentation, never arithmetic. Nothing here changes a value. */
function formatValue(value, column) {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "number") return String(value);
  if (column.endsWith("_usd")) {
    return value.toLocaleString(undefined, { style: "currency", currency: "USD",
                                             maximumFractionDigits: 0 });
  }
  if (Number.isInteger(value)) return value.toLocaleString();
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/* Reassembles a full record from the normalised export. Mirrors
 * fcf_m2.provenance.entry_to_provenance, and a Python test asserts the two agree — the tiers
 * disagreeing about what a number means is the failure this file must not introduce. */
function resolve(key) {
  const entry = STATE.prov.entries[key];
  if (!entry) return null;
  const [siteId, horizon, scenario, column] = key.split("|");
  const shared = STATE.prov.shared;
  return {
    value: entry.v,
    column, siteId, horizon, scenario,
    contractVersion: shared.contract_version,
    modelVersion: shared.model_version,
    modelMode: entry.mode,
    runId: shared.run_id,
    generatedUtc: shared.generated_utc,
    engine: shared.engine,
    table: shared.table,
    tableSha256: shared.table_sha256,
    assumptionFlag: entry.flag,
    dataConfidence: entry.conf,
    capacityBasis: entry.basis,
    caveats: (entry.cav || []).map((k) => STATE.prov.caveat_text[k]),
    consumerRules: shared.consumer_rules,
    fieldProvenance: entry.fp ? STATE.prov.field_provenance[entry.fp] : null,
  };
}

/* ------------------------------------------------------------------ the number button */

function numberCell(siteId, column, { flagPlaceholder = false } = {}) {
  const key = `${siteId}|${STATE.horizon}|${STATE.scenario}|${column}`;
  const p = resolve(key);

  // No provenance, no number. Deliberately not a fallback render.
  if (!p) {
    const span = document.createElement("span");
    span.className = "muted";
    span.textContent = "not available";
    span.title = "This value has no resolvable provenance, so it is not shown.";
    return span;
  }

  const button = document.createElement("button");
  button.type = "button";
  button.className = "val";
  button.textContent = formatValue(p.value, column);
  button.dataset.key = key;
  button.setAttribute("aria-label",
    `${formatValue(p.value, column)} — ${column} for ${siteId}. Show where this number comes from.`);
  button.addEventListener("click", () => openPanel(key));

  if (flagPlaceholder && p.capacityBasis === "placeholder") {
    const flag = document.createElement("span");
    flag.className = "flag";
    flag.textContent = "placeholder";
    const holder = document.createElement("span");
    holder.append(button, flag);
    return holder;
  }
  return button;
}

/* ------------------------------------------------------------------ the provenance panel */

function group(title, rows) {
  const wrap = document.createElement("div");
  wrap.className = "pv-group";
  const h = document.createElement("h3");
  h.textContent = title;
  wrap.append(h);
  const dl = document.createElement("dl");
  dl.style.margin = "0";
  for (const [label, value, cls] of rows) {
    if (value === null || value === undefined || value === "") continue;
    const row = document.createElement("div");
    row.className = "pv-row";
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = value;
    if (cls) dd.className = cls;
    row.append(dt, dd);
    dl.append(row);
  }
  wrap.append(dl);
  return wrap;
}

function openPanel(key) {
  const p = resolve(key);
  if (!p) return;

  const body = $("#panel-body");
  body.replaceChildren();

  const value = document.createElement("p");
  value.className = "pv-value";
  value.textContent = formatValue(p.value, p.column);
  const what = document.createElement("p");
  what.className = "pv-what";
  what.textContent = `${p.column} · ${p.siteId} · ${p.horizon} · ${p.scenario}`;
  body.append(value, what);

  body.append(group("Which run produced it", [
    ["Engine", p.engine],
    ["Mode", p.modelMode],
    ["Model version", p.modelVersion],
    ["Run id", p.runId],
    ["Generated", p.generatedUtc],
  ]));

  body.append(group("Which file it came from", [
    ["Contract", `v${p.contractVersion}`],
    ["Table", p.table],
    ["SHA-256", p.tableSha256, "pv-hash"],
  ]));

  if (p.fieldProvenance) {
    const fp = p.fieldProvenance;
    body.append(group("What backs it", [
      ["Field group", fp.field_group],
      ["Source class", fp.source_class],
      ["Verification", fp.verification_status],
      ["Source", fp.source_org],
      ["Source date", fp.source_date],
      ["Reviewer", fp.reviewer],
      ["Assumption", fp.assumption_type],
      ["Unresolved", fp.unresolved ? "yes" : "no"],
    ]));
  } else {
    const none = document.createElement("div");
    none.className = "pv-group";
    none.innerHTML = "<h3>What backs it</h3>" +
      "<p class='pv-rule'>This column has no typed provenance record of its own. It is not " +
      "attributed to another field's source — an unmapped column says so rather than " +
      "borrowing credibility it does not have.</p>";
    body.append(none);
  }

  body.append(group("How much to trust it", [
    ["Data confidence", p.dataConfidence],
    ["Capacity basis", p.capacityBasis],
    ["Assumption flag", p.assumptionFlag],
  ]));

  if (p.caveats.length) {
    const wrap = document.createElement("div");
    wrap.className = "pv-group";
    const h = document.createElement("h3");
    h.textContent = "What you must know about this number";
    wrap.append(h);
    for (const text of p.caveats) {
      const c = document.createElement("p");
      c.className = "pv-caveat";
      c.textContent = text;
      wrap.append(c);
    }
    body.append(wrap);
  }

  if (p.consumerRules && p.consumerRules.length) {
    const wrap = document.createElement("div");
    wrap.className = "pv-group";
    const h = document.createElement("h3");
    h.textContent = "Rules for anyone consuming this contract";
    wrap.append(h);
    for (const rule of p.consumerRules) {
      const r = document.createElement("p");
      r.className = "pv-rule";
      r.textContent = `• ${rule}`;
      wrap.append(r);
    }
    body.append(wrap);
  }

  $("#panel").hidden = false;
  $("#scrim").hidden = false;
  $("#panel-close").focus();

  // Make the open panel addressable, so a reader can copy the URL and send the provenance.
  const url = new URL(location.href);
  url.searchParams.set("number", key);
  history.replaceState(null, "", url);
}

function closePanel() {
  $("#panel").hidden = true;
  $("#scrim").hidden = true;
  const url = new URL(location.href);
  url.searchParams.delete("number");
  history.replaceState(null, "", url);
}

/* ------------------------------------------------------------------ rendering */

function renderSites() {
  const tbody = $("#sites tbody");
  tbody.replaceChildren();

  const siteIds = [...new Set(
    Object.keys(STATE.prov.entries).map((k) => k.split("|")[0])
  )].sort();

  for (const siteId of siteIds) {
    const tr = document.createElement("tr");

    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = siteId;
    tr.append(th);

    for (const [column, opts] of [
      ["ports_active", { num: true }],
      ["ports_pathway_capacity", { num: true }],
      ["capacity_basis", { flagPlaceholder: false }],
      ["data_confidence", {}],
    ]) {
      const td = document.createElement("td");
      if (opts.num) td.className = "num";
      td.append(numberCell(siteId, column, opts));
      tr.append(td);
    }
    tbody.append(tr);
  }
}

function renderOperations() {
  const banner = $("#tier-note");
  if (banner) {
    banner.textContent = STATE.tier === "desktop"
      ? "You are running the DESKTOP tier. Everything below executes locally on this machine."
      : "You are viewing the WEB tier. It shows results and cannot execute anything.";
    banner.className = STATE.tier === "desktop" ? "tier tier-desktop" : "tier tier-web";
  }
  const list = $("#operations");
  list.replaceChildren();
  for (const op of STATE.ops.operations) {
    const li = document.createElement("li");

    const head = document.createElement("div");
    head.className = "op-head";
    const h3 = document.createElement("h3");
    h3.textContent = op.label;
    const pill = document.createElement("span");
    pill.className = `pill ${op.available ? "pill-ok" : "pill-no"}`;
    pill.textContent = op.available ? "available here" : "desktop app";
    head.append(h3, pill);
    li.append(head);

    const desc = document.createElement("p");
    desc.textContent = op.description;
    li.append(desc);

    // The reason is shown, never omitted. An unexplained disabled control is
    // indistinguishable from a broken one.
    if (!op.available && op.unavailable_reason) {
      const why = document.createElement("p");
      why.className = "why";
      why.textContent = op.unavailable_reason;
      li.append(why);
    }
    if (op.caveat) {
      const cav = document.createElement("p");
      cav.textContent = op.caveat;
      li.append(cav);
    }

    if (op.available && STATE.tier === "desktop") {
      const run = document.createElement("button");
      run.type = "button";
      run.className = "run";
      run.textContent = "Run";
      const out = document.createElement("pre");
      out.className = "op-out";
      out.hidden = true;
      run.addEventListener("click", () => runOperation(op.id, run, out));
      li.append(run, out);
    }
    list.append(li);
  }
}

function renderControls() {
  const keys = Object.keys(STATE.prov.entries);
  const horizons = [...new Set(keys.map((k) => k.split("|")[1]))].sort();
  const scenarios = [...new Set(keys.map((k) => k.split("|")[2]))].sort();

  const hSel = $("#horizon"), sSel = $("#scenario");
  hSel.replaceChildren(...horizons.map((h) => new Option(h, h)));
  sSel.replaceChildren(...scenarios.map((s) => new Option(s, s)));

  STATE.horizon = horizons.includes("2026") ? "2026" : horizons[0];
  STATE.scenario = scenarios.includes("baseline") ? "baseline" : scenarios[0];
  hSel.value = STATE.horizon;
  sSel.value = STATE.scenario;

  const rerender = () => {
    STATE.horizon = hSel.value;
    STATE.scenario = sSel.value;
    renderSites();
  };
  hSel.addEventListener("change", rerender);
  sSel.addEventListener("change", rerender);
}

function renderRunLine() {
  const s = STATE.prov.shared;
  $("#run-line").textContent =
    `Contract v${s.contract_version} · mode from run ${s.run_id} · produced by ${s.engine} · ` +
    `table SHA-256 ${String(s.table_sha256).slice(0, 12)}…`;
  $("#foot-provenance").textContent = STATE.prov.engine_note;
}

/* ------------------------------------------------------------------ boot */

/* Ask the server which tier we are in. The static deployment has no /api, so a failed
 * request is a definite answer, not an error worth surfacing. */
async function detectTier() {
  STATE.token = new URLSearchParams(location.search).get("token");
  if (!STATE.token) return { tier: "both", ops: null };
  try {
    const res = await fetch(`/api/operations?token=${encodeURIComponent(STATE.token)}`,
                            { cache: "no-store" });
    if (!res.ok) return { tier: "both", ops: null };
    const ops = await res.json();
    return { tier: "desktop", ops };
  } catch {
    return { tier: "both", ops: null };
  }
}

async function runOperation(id, button, output) {
  button.disabled = true;
  const original = button.textContent;
  button.textContent = "Running…";
  output.hidden = false;
  output.textContent = "Running. This executes the same command the CLI runs.";
  try {
    const res = await fetch(`/api/run/${encodeURIComponent(id)}?token=${encodeURIComponent(STATE.token)}`,
                            { method: "POST" });
    const body = await res.json();
    // Show what actually happened, including failure. A green tick that hides a non-zero
    // exit code would make this platform a worse witness than the terminal it replaces.
    const status = body.ok ? "finished, exit 0" : `FAILED, exit ${body.returncode}`;
    output.textContent = `${status}\n\n${(body.stdout || "").trim()}` +
      ((body.stderr || "").trim() ? `\n\n[stderr]\n${body.stderr.trim()}` : "");
    output.className = body.ok ? "op-out" : "op-out op-out-bad";
  } catch (err) {
    output.className = "op-out op-out-bad";
    output.textContent = `Could not reach the local server: ${err.message}`;
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

async function main() {
  try {
    const [prov, staticOps, detected] = await Promise.all([
      loadJSON("provenance_v1.json"),
      loadJSON("operations.json"),
      detectTier(),
    ]);
    STATE.prov = prov;
    STATE.tier = detected.tier;
    // The desktop tier's list comes from the running server; the web tier's from the
    // generated file. Both are rendered by the same code from the same registry.
    STATE.ops = detected.ops || staticOps;

    renderRunLine();
    renderControls();
    renderSites();
    renderOperations();

    // Deep-link a provenance panel: ?number=FFX004|2036|base|ports_active
    //
    // A shareable link to a number's lineage is the useful form of "show your working" --
    // you can send someone the provenance rather than the claim. It also means the panel
    // itself is renderable without a click, which is how it gets checked.
    const wanted = new URLSearchParams(location.search).get("number");
    if (wanted) {
      if (STATE.prov.entries[wanted]) {
        const [, horizon, scenario] = wanted.split("|");
        $("#horizon").value = horizon;
        $("#scenario").value = scenario;
        STATE.horizon = horizon;
        STATE.scenario = scenario;
        renderSites();
        openPanel(wanted);
      } else {
        // Refuse rather than open an empty panel: a link to a number that does not exist
        // must say so, not show a blank explanation.
        const p = document.createElement("p");
        p.className = "pv-caveat";
        p.textContent = `No number matches "${wanted}", so there is nothing to explain. ` +
          `A provenance link must name an existing site, horizon, case and column.`;
        document.getElementById("main").prepend(p);
      }
    }
  } catch (err) {
    // Say what failed. A blank page that looks intentional is worse than an error.
    const main = document.getElementById("main");
    const p = document.createElement("p");
    p.className = "pv-caveat";
    p.textContent =
      `This page could not load its data, so it is showing nothing rather than showing ` +
      `numbers it cannot explain. (${err.message})`;
    main.prepend(p);
  }

  $("#panel-close").addEventListener("click", closePanel);
  $("#scrim").addEventListener("click", closePanel);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("#panel").hidden) closePanel();
  });
}

document.addEventListener("DOMContentLoaded", main);
