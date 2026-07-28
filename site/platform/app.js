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
  prov: null, ops: null, engines: null, surfaces: null, simulink: null, horizon: null, scenario: null,
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

function renderSurfaces() {
  if (!STATE.surfaces) return;
  $("#surf-note").textContent = STATE.surfaces.deploy_note;
  const list = $("#surfaces");
  list.replaceChildren();
  for (const s of STATE.surfaces.surfaces) {
    const li = document.createElement("li");
    const head = document.createElement("div");
    head.className = "op-head";
    const h3 = document.createElement("h3");
    h3.textContent = s.title;
    const pill = document.createElement("span");
    pill.className = "pill pill-ok";
    pill.textContent = `${s.count} item${s.count === 1 ? "" : "s"}`;
    head.append(h3, pill);
    li.append(head);

    const detail = document.createElement("p");
    detail.textContent = s.detail;
    li.append(detail);

    if (s.href) {
      const a = document.createElement("a");
      a.className = "run";
      a.href = s.href;
      a.textContent = "Open";
      li.append(a);
    }
    for (const link of s.links || []) {
      const a = document.createElement("a");
      a.className = "linkchip";
      a.href = link.href;
      a.textContent = link.label;
      // External Tableau links open in a new tab; internal downloads do not.
      if (link.href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener noreferrer"; }
      li.append(a);
    }
    list.append(li);
  }
}

function renderSimulink() {
  if (!STATE.simulink) return;
  const s = STATE.simulink;
  const box = $("#simulink");
  box.replaceChildren();

  // The status leads. A block diagram is exactly the kind of artifact a reader assumes
  // produced something, so what it did NOT do goes first.
  const status = document.createElement("p");
  status.innerHTML = `<strong>${s.status}.</strong> ${s.status_detail}`;
  box.append(status);

  const meta = document.createElement("p");
  meta.className = "muted";
  meta.textContent = `${s.model} — built by MathWorks MATLAB ${s.built_by}, from ${s.from_run}.`;
  box.append(meta);

  const h = document.createElement("p");
  h.className = "muted";
  h.textContent = `${s.root.block_count} blocks at the top level, ` +
    `${Object.keys(s.subsystems).length} subsystem. Read from the .slx itself.`;
  box.append(h);

  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th scope='col'>Block</th><th scope='col'>Type</th></tr></thead>";
  const tbody = document.createElement("tbody");
  for (const b of s.root.blocks) {
    const tr = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    name.textContent = b.name;
    const type = document.createElement("td");
    type.textContent = b.type;
    tr.append(name, type);
    tbody.append(tr);
  }
  table.append(tbody);
  const wrap = document.createElement("div");
  wrap.className = "tablewrap";
  wrap.append(table);
  box.append(wrap);

  for (const note of [s.topology_note, s.connections_note]) {
    const p2 = document.createElement("p");
    p2.className = "pv-rule";
    p2.textContent = note;
    box.append(p2);
  }
}

function renderEngines() {
  if (!STATE.engines) return;
  const e = STATE.engines;
  $("#engines-headline").textContent = e.headline;

  const list = $("#engines");
  list.replaceChildren();
  for (const eng of e.engines) {
    const li = document.createElement("li");
    const badge = document.createElement("span");
    badge.className = `badge badge-${eng.id}`;
    badge.textContent = eng.name;

    const body = document.createElement("span");
    const status = document.createElement("strong");
    status.textContent = eng.status;
    const detail = document.createElement("span");
    detail.textContent = ` — ${eng.detail}`;
    body.append(status, detail);

    // The single most misreadable fact about this project, stated on every engine.
    if (!eng.ran_on_real_sites) {
      const warn = document.createElement("span");
      warn.className = "flag";
      warn.textContent = "never ran on the real sites";
      body.append(" ", warn);
    }
    if (eng.warning) {
      const w = document.createElement("p");
      w.className = "pv-caveat";
      w.textContent = eng.warning;
      body.append(w);
    }
    li.append(badge, body);
    list.append(li);
  }

  const g = e.guard_evidence;
  const guard = $("#guard");
  guard.replaceChildren();
  const gp = document.createElement("p");
  gp.innerHTML = `<strong>${g.title}.</strong> ${g.why_it_matters}`;
  const gs = document.createElement("p");
  gs.className = "muted";
  gs.textContent =
    `From ${g.from_run}: ${g.run_status_ok}/${g.rows} rows completed; capacity basis ` +
    `${g.capacity_basis.join(", ")}; service check ${g.service_check.join(", ")}; ` +
    `${g.strategies_skipped} rows had both managed-charging strategies skipped; ` +
    `peak clamp is null on every row` +
    (g.peak_clamp_all_null ? " (no number was invented to fill the gap)." : ".");
  guard.append(gp, gs);

  const dl = $("#divergences");
  dl.replaceChildren();
  for (const d of e.divergences) {
    const li = document.createElement("li");
    const head = document.createElement("div");
    head.className = "op-head";
    const h3 = document.createElement("h3");
    h3.textContent = d.between;
    const pill = document.createElement("span");
    pill.className = d.severity === "none" ? "pill pill-ok" : "pill pill-no";
    pill.textContent = d.severity;
    head.append(h3, pill);
    li.append(head);

    const finding = document.createElement("p");
    finding.textContent = d.finding;
    li.append(finding);

    for (const [label, key] of [["Deliberately unfixed", "deliberately_unfixed"],
                                ["How it was found", "how_found"],
                                ["Why it survived", "why_it_survived"]]) {
      if (d[key]) {
        const p2 = document.createElement("p");
        p2.className = "why";
        p2.textContent = `${label}: ${d[key]}`;
        li.append(p2);
      }
    }
    dl.append(li);
  }

  $("#cannot-show").textContent = `What cannot be shown: ${e.what_cannot_be_shown}`;
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
    const [prov, staticOps, engines, surfaces, simulink, detected] = await Promise.all([
      loadJSON("provenance_v1.json"),
      loadJSON("operations.json"),
      loadJSON("engines.json"),
      loadJSON("surfaces.json"),
      loadJSON("simulink.json"),
      detectTier(),
    ]);
    STATE.prov = prov;
    STATE.engines = engines;
    STATE.surfaces = surfaces;
    STATE.simulink = simulink;
    STATE.tier = detected.tier;
    // The desktop tier's list comes from the running server; the web tier's from the
    // generated file. Both are rendered by the same code from the same registry.
    STATE.ops = detected.ops || staticOps;

    renderRunLine();
    renderControls();
    renderSites();
    renderOperations();
    renderSurfaces();
    renderEngines();
    renderSimulink();
    await initFieldEntry();

    // Deep-link a provenance panel: ?number=SYN004|2036|base|ports_active
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

/* ------------------------------------------------------------------ field-data entry
 *
 * The form is BUILT FROM `field_schema.json`, which is generated from `observed.py`. Nothing
 * about which fields exist, which values are legal, or which combinations are refused is
 * written here — this file only draws what the schema describes and calls the shared
 * validator. That is the whole point: a hand-written form is a second copy of the model's
 * refusals, and a second copy drifts toward being more permissive than the thing it mirrors.
 *
 * What this deliberately does NOT do
 * ----------------------------------
 * It does not submit anything. A browser cannot write to the model, and pretending otherwise
 * would be the worst possible lie for this particular feature: someone records a capacity
 * confirmation in the field, sees a success message, and believes a site's evidence has been
 * updated when nothing has changed. So the form produces a **file**, says so plainly, and
 * points at the ingest step that actually reads it.
 */

const FIELD = { schema: null, formId: null, pending: [] };

function currentForm() {
  return FIELD.schema.forms.find((f) => f.id === FIELD.formId);
}

/** Site ids come from the contract, so the form cannot offer a site the model does not know. */
function knownSiteIds() {
  return [...new Set(Object.keys(STATE.prov.entries).map((k) => k.split("|")[0]))].sort();
}

function fieldControl(field) {
  const wrap = document.createElement("div");
  wrap.className = "fieldrow";

  const label = document.createElement("label");
  label.setAttribute("for", `f-${field.name}`);
  label.textContent = field.label + (field.required ? " *" : "");
  wrap.append(label);

  let input;
  if (field.type === "enum" || field.type === "site") {
    input = document.createElement("select");
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "—";
    input.append(blank);
    const values = field.type === "site" ? knownSiteIds() : field.values;
    for (const value of values) {
      const option = document.createElement("option");
      option.value = value;
      // The method a person picks caps how strong a claim the value can support. Showing that
      // at the point of choosing is the difference between a dropdown and an explanation.
      const note = field.value_notes && field.value_notes[value];
      option.textContent = note ? `${value} — ${note}` : value;
      input.append(option);
    }
    if (field.default) input.value = field.default;
  } else if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.rows = 2;
  } else {
    input = document.createElement("input");
    input.type = field.type === "date" ? "date"
      : (field.type === "number" || field.type === "integer") ? "number" : "text";
    if (field.type === "number") input.step = "any";
  }
  input.id = `f-${field.name}`;
  input.name = field.name;
  wrap.append(input);

  if (field.help) {
    const help = document.createElement("p");
    help.className = "muted fieldhelp";
    help.textContent = field.help;
    wrap.append(help);
  }
  return wrap;
}

function renderFieldForm() {
  const form = currentForm();
  const host = $("#field-fields");
  host.replaceChildren();
  for (const field of form.fields) host.append(fieldControl(field));

  const explain = document.createElement("p");
  explain.className = "prose muted";
  explain.textContent = form.explains;
  host.prepend(explain);

  $("#field-errors").replaceChildren();
  renderPending();
}

function readForm() {
  const row = {};
  for (const field of currentForm().fields) {
    const el = document.getElementById(`f-${field.name}`);
    row[field.name] = el ? el.value : "";
  }
  return row;
}

function showErrors(errors) {
  const host = $("#field-errors");
  host.replaceChildren();
  if (!errors.length) return;

  const heading = document.createElement("p");
  heading.className = "pv-caveat";
  heading.textContent = errors.length === 1
    ? "This observation was not added:"
    : `This observation was not added — ${errors.length} problems:`;
  host.append(heading);

  const list = document.createElement("ul");
  list.className = "errlist";
  for (const error of errors) {
    const item = document.createElement("li");
    // The message is the MODEL's own wording, carried through the schema. A friendlier
    // paraphrase here would be a third place the rules are described.
    item.textContent = error.message;
    list.append(item);
    const el = document.getElementById(`f-${error.field}`);
    if (el) el.setAttribute("aria-invalid", "true");
  }
  host.append(list);
}

function renderPending() {
  const rows = FIELD.pending.filter((p) => p.formId === FIELD.formId);
  const wrap = $("#pending-wrap");
  wrap.hidden = rows.length === 0;
  if (!rows.length) return;

  const form = currentForm();
  const thead = $("#pending thead");
  const tbody = $("#pending tbody");
  thead.replaceChildren();
  tbody.replaceChildren();

  const head = document.createElement("tr");
  for (const column of form.csv_columns) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = column;
    head.append(th);
  }
  thead.append(head);

  for (const entry of rows) {
    const tr = document.createElement("tr");
    for (const column of form.csv_columns) {
      const td = document.createElement("td");
      td.textContent = entry.row[column] || "";
      tr.append(td);
    }
    tbody.append(tr);
  }

  $("#pending-note").textContent =
    `${rows.length} observation${rows.length === 1 ? "" : "s"} held in this browser only. ` +
    `Nothing has been sent anywhere and no number on this page has changed. Download the CSV, ` +
    `then run the ingest step to see what it would change.`;
}

function downloadPending() {
  const form = currentForm();
  const rows = FIELD.pending.filter((p) => p.formId === FIELD.formId).map((p) => p.row);
  const csv = FieldValidate.toCsv(form, rows);
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `observed_${form.id}.csv`;
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function initFieldEntry() {
  try {
    FIELD.schema = await loadJSON("field_schema.json");
  } catch (err) {
    $("#field-fields").textContent =
      `The entry form could not load its rules (${err.message}), so it is not being shown. ` +
      `A form that cannot check what you type would accept observations the model refuses.`;
    $("#field-form").querySelector("button").disabled = true;
    return;
  }

  const kind = $("#form-kind");
  for (const form of FIELD.schema.forms) {
    const option = document.createElement("option");
    option.value = form.id;
    option.textContent = form.label;
    kind.append(option);
  }
  FIELD.formId = FIELD.schema.forms[0].id;
  kind.value = FIELD.formId;
  kind.addEventListener("change", () => {
    FIELD.formId = kind.value;
    renderFieldForm();
  });

  $("#field-form").addEventListener("submit", (event) => {
    event.preventDefault();
    for (const el of $("#field-fields").querySelectorAll("[aria-invalid]")) {
      el.removeAttribute("aria-invalid");
    }
    const row = readForm();
    const errors = FieldValidate.validateRow(currentForm(), row);
    showErrors(errors);
    if (errors.length) return;
    FIELD.pending.push({ formId: FIELD.formId, row });
    renderFieldForm();
  });

  $("#field-download").addEventListener("click", downloadPending);
  $("#field-clear").addEventListener("click", () => {
    FIELD.pending = FIELD.pending.filter((p) => p.formId !== FIELD.formId);
    renderPending();
  });

  renderFieldForm();
}
