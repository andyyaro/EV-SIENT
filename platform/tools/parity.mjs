#!/usr/bin/env node
// Native vs Pyodide parity for the browser path. Runs the same browser_api calls (propose,
// remap, check, accept, run with a fixed asOf, explain for every site, provenance for a set of
// cells per site, output_files) on
// Example City and on the 12-site synthetic cohort twice: natively with the repo's venv, and
// under Pyodide in Node with exactly what the browser gets (the fetched runtime directory and
// the built engine archive, its SHA-256 checked). Numbers must agree to 1e-9, everything else
// exactly. The clock is frozen in both, so run ids and timestamps agree too; elapsed seconds
// are the one field left out. Exits non-zero on any mismatch.
//
// Needs: node platform/tools/fetch_runtime.mjs, venv/bin/python platform/tools/build_engine.py
// Usage: node platform/tools/parity.mjs   (VENV_PY=<python> to choose the native interpreter)

import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const app = join(repo, 'platform/app');
const runtimeDir = join(app, 'public/runtime/pyodide/314.0.7') + '/';
const engineDir = join(app, 'public/runtime/engine');
const TOLERANCE = 1e-9;
const IGNORED_KEYS = new Set(['elapsedSec']);

const CASES = {
  'example-city': 'data/intake/example/example_city_facilities.csv',
  'synthetic-cohort': 'data/synthetic/synthetic_sites_v2.csv',
};

// Run identically in both runtimes. It freezes the engine's clock (only here, never in the
// engine) and replaces the session's random temp path, the two things that differ by design.
const DRIVER = String.raw`
import csv, io, json
import datetime as _dt
from fcf_m2 import browser_api as api, contract, contract_v2, workflow

class _Frozen(_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        moment = cls(2026, 10, 18, 12, 0, 0, tzinfo=_dt.timezone.utc)
        return moment if tz else moment.replace(tzinfo=None)

for module in (api, contract, contract_v2, workflow):
    module.datetime = _Frozen

def _drive(cases_json):
    out = {}
    for name, text in json.loads(cases_json).items():
        rows = list(csv.reader(io.StringIO(text)))
        table = {"fileName": name + ".csv", "columns": rows[0], "rows": rows[1:]}
        api.reset()
        root = str(api._session.root)
        got = {"propose": json.loads(api.propose(json.dumps(table)))}
        got["remap"] = json.loads(api.remap(json.dumps({"mapping": got["propose"]["mapping"]})))
        got["check"] = json.loads(api.check())
        got["accept"] = json.loads(api.accept(json.dumps(
            {"jurisdiction": name, "sourceOrg": "parity", "sourceDate": "2026-10-01"})))
        got["run"] = json.loads(api.run(json.dumps({"asOf": "2026-10-18"})))
        got["explain"] = {s["siteId"]: json.loads(api.explain(s["siteId"])) for s in got["run"]["sites"]}
        got["provenance"] = {
            f"{s['siteId']}|{year}|{scenario}|{column}": json.loads(api.provenance(json.dumps(
                {"siteId": s["siteId"], "horizonYear": year, "scenario": scenario, "column": column})))
            for s in got["run"]["sites"]
            for year, scenario in ((2026, "baseline"), (2046, "stress_combined"))
            for column in ("ports_active", "spare_capacity_kw", "net_co2e_kg", "data_confidence")}
        files = json.loads(api.output_files())["files"]
        got["output_files"] = {k: v.replace(root, "<session>") for k, v in files.items()}
        out[name] = got
    return json.dumps(out, allow_nan=False)
`;

async function cases() {
  const out = {};
  for (const [name, rel] of Object.entries(CASES)) out[name] = (await readFile(join(repo, rel), 'utf8')).replace(/^﻿/, '');
  return JSON.stringify(out);
}

function native(casesJson) {
  // VENV_PY lets CI use the runner's interpreter, as scripts/verify.sh does.
  const py = process.env.VENV_PY || join(repo, 'venv/bin/python');
  // The engine prints its own warnings to stdout; keep stdout for the result.
  const script = `${DRIVER}\nimport contextlib, sys\nwith contextlib.redirect_stdout(sys.stderr):\n    result = _drive(sys.stdin.read())\nsys.stdout.write(result)\n`;
  const r = spawnSync(py, ['-c', script], {
    input: casesJson, env: { ...process.env, PYTHONPATH: join(repo, 'src') }, maxBuffer: 1 << 28, encoding: 'utf8',
  });
  if (r.status !== 0) throw new Error(`native run failed:\n${r.stderr}`);
  return JSON.parse(r.stdout);
}

async function pyodide(casesJson) {
  const { loadPyodide } = await import(pathToFileURL(join(app, 'node_modules/pyodide/pyodide.mjs')).href);
  const t0 = performance.now();
  const py = await loadPyodide({
    indexURL: runtimeDir, lockFileURL: runtimeDir + 'pyodide-lock.json', packageBaseUrl: runtimeDir,
    stdout: () => {}, stderr: (s) => process.stderr.write(`[pyodide] ${s}\n`),
  });
  await py.loadPackage(['numpy', 'pandas', 'jsonschema'], { checkIntegrity: true, messageCallback: () => {} });
  const manifest = JSON.parse(await readFile(join(engineDir, 'engine.json'), 'utf8'));
  const archive = await readFile(join(engineDir, manifest.file));
  const digest = createHash('sha256').update(archive).digest('hex');
  if (digest !== manifest.sha256) throw new Error(`${manifest.file} does not match engine.json`);
  py.FS.mkdirTree('/work/pkgroot');
  // Pyodide takes a plain Uint8Array, not a Node Buffer.
  py.unpackArchive(new Uint8Array(archive.buffer, archive.byteOffset, archive.length), 'zip', { extractDir: '/work/pkgroot' });
  py.runPython('import sys; sys.path.insert(0, "/work/pkgroot/src")');
  py.runPython(DRIVER);
  const t1 = performance.now();
  const drive = py.globals.get('_drive');
  const out = drive(casesJson);
  drive.destroy();
  console.log(`Pyodide ${py.version}: boot ${Math.round(t1 - t0)} ms, both cases ${Math.round(performance.now() - t1)} ms; engine ${manifest.version}`);
  return JSON.parse(out);
}

// ---------- comparison ----------

const problems = [];
let numbersCompared = 0;
let worst = 0;

function sameNumber(a, b) {
  numbersCompared++;
  const d = Math.abs(a - b);
  worst = Math.max(worst, d);
  return d <= TOLERANCE * Math.max(1, Math.abs(a), Math.abs(b));
}

function compare(a, b, path) {
  if (typeof a === 'number' && typeof b === 'number') {
    if (!sameNumber(a, b)) problems.push(`${path}: ${a} vs ${b}`);
    return;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) { problems.push(`${path}: length ${a.length} vs ${b.length}`); return; }
    a.forEach((x, i) => compare(x, b[i], `${path}[${i}]`));
    return;
  }
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of keys) {
      if (IGNORED_KEYS.has(k)) continue;
      if (!(k in a) || !(k in b)) { problems.push(`${path}.${k}: only in ${k in a ? 'native' : 'pyodide'}`); continue; }
      compare(a[k], b[k], `${path}.${k}`);
    }
    return;
  }
  if (a !== b) problems.push(`${path}: ${JSON.stringify(a)?.slice(0, 120)} vs ${JSON.stringify(b)?.slice(0, 120)}`);
}

function csvRows(text) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') quoted = false; else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; }
    else if (c !== '\r') cell += c;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  return rows;
}

const asNumber = (s) => (s.trim() !== '' && Number.isFinite(Number(s)) ? Number(s) : null);

// A hash over files that differ only in a float's last bits differs too; it is checked through
// the files it covers, so a 64-hex string that disagrees is noted, not failed.
const HASH = /^[0-9a-f]{64}$/;
let hashesDiffering = 0;

function compareText(a, b, path) {
  if (a === b) return true;
  if (path.endsWith('.csv')) {
    const ra = csvRows(a), rb = csvRows(b);
    if (ra.length !== rb.length) { problems.push(`${path}: ${ra.length} vs ${rb.length} rows`); return false; }
    ra.forEach((row, i) => {
      if (row.length !== rb[i].length) { problems.push(`${path} row ${i + 1}: ${row.length} vs ${rb[i].length} cells`); return; }
      row.forEach((cell, j) => {
        const x = asNumber(cell), y = asNumber(rb[i][j]);
        if (x !== null && y !== null) { if (!sameNumber(x, y)) problems.push(`${path} r${i + 1}c${j + 1}: ${cell} vs ${rb[i][j]}`); }
        else if (cell !== rb[i][j] && !(HASH.test(cell) && HASH.test(rb[i][j]) && ++hashesDiffering)) {
          problems.push(`${path} r${i + 1}c${j + 1}: ${cell} vs ${rb[i][j]}`);
        }
      });
    });
    return false;
  }
  if (path.endsWith('.json')) {
    const strip = (v) => (typeof v === 'string' && HASH.test(v) ? '<sha256>' : Array.isArray(v) ? v.map(strip)
      : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, strip(x)])) : v);
    const ja = JSON.parse(a), jb = JSON.parse(b);
    hashesDiffering += (JSON.stringify(ja).match(/"[0-9a-f]{64}"/g) || []).filter((h) => !b.includes(h)).length;
    compare(strip(ja), strip(jb), path);
    return false;
  }
  problems.push(`${path}: text differs`);
  return false;
}

async function main() {
  const casesJson = await cases();
  const t0 = performance.now();
  const n = native(casesJson);
  console.log(`native: both cases ${Math.round(performance.now() - t0)} ms (including interpreter start)`);
  const p = await pyodide(casesJson);
  for (const name of Object.keys(CASES)) {
    const { output_files: nf, ...nRest } = n[name];
    const { output_files: pf, ...pRest } = p[name];
    compare(nRest, pRest, name);
    const files = [...new Set([...Object.keys(nf), ...Object.keys(pf)])].sort();
    let identical = 0;
    const within = [];
    for (const f of files) {
      if (!(f in nf) || !(f in pf)) { problems.push(`${name}/${f}: only in ${f in nf ? 'native' : 'pyodide'}`); continue; }
      if (compareText(nf[f], pf[f], `${name}/${f}`)) identical++;
      else within.push(f);
    }
    const sites = nRest.run.sites.length;
    console.log(`${name}: ${sites} sites, ${Object.keys(nRest.explain).length} explanations, ` +
      `${identical} of ${files.length} output files byte-identical` + (within.length ? ` (compared by value: ${within.join(', ')})` : ''));
  }
  console.log(`${numbersCompared} numbers compared, largest difference ${worst.toExponential(2)}` +
    (hashesDiffering ? `; ${hashesDiffering} file hashes differ because their files differ within tolerance` : ''));
  if (problems.length) {
    console.error(`PARITY FAILED: ${problems.length} mismatch(es)`);
    for (const m of problems.slice(0, 40)) console.error(`  ${m}`);
    process.exit(1);
  }
  console.log('PARITY OK: native and Pyodide agree (numbers to 1e-9, everything else exactly)');
}

main().catch((e) => { console.error(`parity: ${e.stack || e.message}`); process.exit(2); });
