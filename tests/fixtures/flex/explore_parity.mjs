#!/usr/bin/env node
// Native vs Pyodide parity for fcf_m2.flex.explore. The native interpreter builds the
// synthetic fixtures of tests/test_flex_explore.py (planted effects at 360 and 2,000 sites,
// pure noise, the Simpson's-paradox file), runs bridge_scan on each and hands the same table,
// entries and options to Pyodide in Node, loaded exactly as platform/tools/parity.mjs loads it
// (the fetched runtime and the built engine archive, its SHA-256 checked). Numbers must agree
// to 1e-9, everything else exactly. Prints the time each scan took in both runtimes.
//
// Needs: node platform/tools/fetch_runtime.mjs, venv/bin/python platform/tools/build_engine.py
// Usage: node tests/fixtures/flex/explore_parity.mjs [--csv <file> --entries <file.json>]
//   (--csv adds a file of your own, read as text cells; VENV_PY chooses the native python)

import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const app = join(repo, 'platform/app');
const runtimeDir = join(app, 'public/runtime/pyodide/314.0.7') + '/';
const engineDir = join(app, 'public/runtime/engine');
const TOLERANCE = 1e-9;

const args = process.argv.slice(2);
const opt = (name) => (args.includes(name) ? resolve(args[args.indexOf(name) + 1]) : null);

const NATIVE = String.raw`
import csv, json, sys, time
sys.path[:0] = [sys.argv[1] + "/src", sys.argv[1] + "/tests"]
import test_flex_explore as t
from fcf_m2.flex import explore

def table(raw):
    return {"columns": list(raw.columns), "rows": raw.values.tolist()}

cases = {}
raw, entries = t.planted()
cases["planted-360"] = (table(raw), entries, {"seed": 1})
raw, entries = t.planted(n=2000)
cases["planted-2000"] = (table(raw), entries, {"seed": 1})
raw, entries = t.null_table(1)
cases["noise-360"] = (table(raw), entries, {"seed": 1})
raw, entries = t.simpson()
cases["simpson-240"] = (table(raw), entries, {"seed": 1})
if len(sys.argv) > 3:
    with open(sys.argv[2], newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    with open(sys.argv[3]) as f:
        entries = json.load(f)
    cases["your-file"] = ({"columns": rows[0], "rows": rows[1:]}, entries, {"seed": 1, "asOf": "2026-10-18"})

out = {}
for name, (tab, entries, options) in cases.items():
    args = (json.dumps(tab), json.dumps(entries), json.dumps(options))
    t0 = time.perf_counter()
    result = explore.bridge_scan(*args)
    out[name] = {"args": args, "result": result, "ms": (time.perf_counter() - t0) * 1000}
sys.stdout.write(json.dumps(out))
`;

function native() {
  const py = process.env.VENV_PY || join(repo, 'venv/bin/python');
  const extra = opt('--csv') ? [opt('--csv'), opt('--entries')] : [];
  const r = spawnSync(py, ['-c', NATIVE, repo, ...extra], { maxBuffer: 1 << 30, encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`native run failed:\n${r.stderr}`);
  return JSON.parse(r.stdout);
}

async function pyodide() {
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
  if (!manifest.files.includes('src/fcf_m2/flex/explore.py')) throw new Error('the engine archive has no flex/explore.py; rebuild it');
  py.FS.mkdirTree('/work/pkgroot');
  py.unpackArchive(new Uint8Array(archive.buffer, archive.byteOffset, archive.length), 'zip', { extractDir: '/work/pkgroot' });
  py.runPython('import sys; sys.path.insert(0, "/work/pkgroot/src")');
  const t1 = performance.now();
  py.runPython('from fcf_m2.flex import explore');
  const scan = py.globals.get('explore').bridge_scan;
  console.log(`Pyodide ${py.version}: boot ${Math.round(t1 - t0)} ms, import explore ${Math.round(performance.now() - t1)} ms; engine ${manifest.version}`);
  return {
    run(args) {
      const s = performance.now();
      const result = scan(...args);
      return { result, ms: performance.now() - s };
    },
    close() { scan.destroy(); },
  };
}

const problems = [];
let numbersCompared = 0;
let worst = 0;

function compare(a, b, path) {
  if (typeof a === 'number' && typeof b === 'number') {
    numbersCompared++;
    const d = Math.abs(a - b);
    worst = Math.max(worst, d);
    if (d > TOLERANCE * Math.max(1, Math.abs(a), Math.abs(b))) problems.push(`${path}: ${a} vs ${b}`);
    return;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) { problems.push(`${path}: length ${a.length} vs ${b.length}`); return; }
    a.forEach((x, i) => compare(x, b[i], `${path}[${i}]`));
    return;
  }
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
      if (!(k in a) || !(k in b)) { problems.push(`${path}.${k}: only in ${k in a ? 'native' : 'pyodide'}`); continue; }
      compare(a[k], b[k], `${path}.${k}`);
    }
    return;
  }
  if (a !== b) problems.push(`${path}: ${JSON.stringify(a)?.slice(0, 120)} vs ${JSON.stringify(b)?.slice(0, 120)}`);
}

async function main() {
  const n = native();
  const p = await pyodide();
  for (const [name, { args, result, ms }] of Object.entries(n)) {
    const got = p.run(args);
    const a = JSON.parse(result), b = JSON.parse(got.result);
    const identical = result === got.result;
    compare(a, b, name);
    console.log(`${name}: ${a.health.rows} rows, ${a.checked} checked, ${a.passed} passed, ${a.cards.length} cards; ` +
      `native ${Math.round(ms)} ms, Pyodide ${Math.round(got.ms)} ms; JSON ${identical ? 'byte-identical' : 'compared by value'}`);
  }
  p.close();
  console.log(`${numbersCompared} numbers compared, largest difference ${worst.toExponential(2)}`);
  if (problems.length) {
    console.error(`EXPLORE PARITY FAILED: ${problems.length} mismatch(es)`);
    for (const m of problems.slice(0, 40)) console.error(`  ${m}`);
    process.exit(1);
  }
  console.log('EXPLORE PARITY OK: native and Pyodide agree (numbers to 1e-9, everything else exactly)');
}

main().catch((e) => { console.error(`explore_parity: ${e.stack || e.message}`); process.exit(2); });
