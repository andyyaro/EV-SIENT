#!/usr/bin/env node
// Writes the pinned Pyodide subset the planner's browser loads: platform/app/public/runtime/
// pyodide/314.0.7/. The app never reaches a CDN at run time, so everything Pyodide needs to
// start and to load numpy, pandas and jsonschema is copied here, and nothing else.
//
// Core files come from node_modules/pyodide where present (the npm package is the same build),
// else from the jsDelivr mirror. Wheels come from the mirror. Every file is checked against a
// pinned SHA-256 (core files below, wheels from the lock) and the script fails closed on any
// mismatch. Downloads are cached in platform/app/.cache/.
//
// Usage (from anywhere): node platform/tools/fetch_runtime.mjs

import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { existsSync } from 'node:fs';
import { copyFile, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const VERSION = '314.0.7';
const CDN = `https://cdn.jsdelivr.net/pyodide/v${VERSION}/full/`;
const WANTED = ['numpy', 'pandas', 'jsonschema'];

// The files loadPyodide fetches before any package, pinned to the 314.0.7 release as published
// on npm. The lock is pinned too, because the wheel hashes are only as good as the lock.
const CORE = {
  'pyodide.mjs': '6f1d60f7bf529beb300f0f47983c921d3982363640ba20af0e38efdddbc66109',
  'pyodide.asm.mjs': 'f7cdc8ece80678ceb712f8e65ebe6d3a83203a180c399865f49612a051693635',
  'pyodide.asm.wasm': 'cc36e3cab04fdfc9a63ff13eb52eae2b911bf46c025cc7b281f394bd3de1d5e6',
  'python_stdlib.zip': 'fa1957e5777068fc4f7437f96d860ae2fbe9c19732ba06c84e004ec16dd7dd7a',
  'pyodide-lock.json': '5dc2fc119108bc148c7457dc86e7675b5c87e1cafd420b9c34c1eaef7b36c010',
};

const here = dirname(fileURLToPath(import.meta.url));
const app = resolve(here, '../app');
const npmDir = join(app, 'node_modules/pyodide');
const cacheDir = join(app, '.cache/pyodide', VERSION);
const outDir = join(app, 'public/runtime/pyodide', VERSION);

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');
const mb = (n) => (n < 104858 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(2)} MB`);

/** A file's bytes, from node_modules, the cache or the mirror, checked against `expected`. */
async function obtain(name, expected, { npm = false } = {}) {
  const sources = [];
  if (npm) sources.push(join(npmDir, name));
  sources.push(join(cacheDir, name));
  for (const path of sources) {
    if (!existsSync(path)) continue;
    const buf = await readFile(path);
    if (sha256(buf) === expected) return buf;
    if (path.startsWith(npmDir)) {
      throw new Error(`${name} in node_modules/pyodide does not match the pinned ${VERSION} hash. Reinstall pyodide@${VERSION}.`);
    }
    console.warn(`  cached ${name} does not match its hash; downloading it again`);
  }
  const res = await fetch(CDN + name);
  if (!res.ok) throw new Error(`Downloading ${name} failed: HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  const got = sha256(buf);
  if (got !== expected) throw new Error(`${name} from ${CDN} has SHA-256 ${got}, expected ${expected}. Refusing to use it.`);
  await mkdir(cacheDir, { recursive: true });
  await writeFile(join(cacheDir, name), buf);
  return buf;
}

// Pyodide looks packages up by canonical name (PEP 503), while `depends` uses the spelling of
// each package's own metadata, so jsonschema asks for jsonschema_specifications.
const canonical = (s) => s.toLowerCase().replace(/[-_.]+/g, '-');

function closure(lock, wanted) {
  const byCanonical = new Map(Object.keys(lock.packages).map((k) => [canonical(k), k]));
  const seen = new Set();
  const stack = [...wanted];
  while (stack.length) {
    const asked = stack.pop();
    const key = byCanonical.get(canonical(asked));
    if (!key) throw new Error(`${asked} is not in the Pyodide ${VERSION} lock.`);
    if (seen.has(key)) continue;
    seen.add(key);
    stack.push(...lock.packages[key].depends);
  }
  return [...seen].sort();
}

async function main() {
  await mkdir(outDir, { recursive: true });
  // Start from an empty directory, so a wheel dropped from the closure cannot linger.
  for (const entry of await readdir(outDir)) await rm(join(outDir, entry), { recursive: true });

  const sizes = [];
  for (const [name, hash] of Object.entries(CORE)) {
    const buf = await obtain(name, hash, { npm: true });
    if (name === 'pyodide-lock.json') continue;
    await writeFile(join(outDir, name), buf);
    sizes.push([name, buf.length]);
  }

  const lock = JSON.parse((await obtain('pyodide-lock.json', CORE['pyodide-lock.json'], { npm: true })).toString());
  const names = closure(lock, WANTED);
  const trimmed = { ...lock, packages: {} };
  for (const key of names) {
    const pkg = lock.packages[key];
    if (pkg.package_type !== 'package') throw new Error(`${key} is a ${pkg.package_type}; this script only expects wheels.`);
    const buf = await obtain(pkg.file_name, pkg.sha256);
    await writeFile(join(outDir, pkg.file_name), buf);
    trimmed.packages[key] = pkg;
    sizes.push([pkg.file_name, buf.length]);
  }
  // Only the closure is listed, so a package outside it cannot be loaded even by accident.
  await writeFile(join(outDir, 'pyodide-lock.json'), JSON.stringify(trimmed, null, 1) + '\n');
  sizes.push(['pyodide-lock.json (trimmed)', (await stat(join(outDir, 'pyodide-lock.json'))).size]);

  const width = Math.max(...sizes.map(([n]) => n.length));
  for (const [n, s] of sizes) console.log(`  ${n.padEnd(width)}  ${mb(s).padStart(9)}`);
  const total = sizes.reduce((a, [, s]) => a + s, 0);
  const wheels = names.map((k) => lock.packages[k].file_name);
  const wheelTotal = sizes.filter(([n]) => wheels.includes(n)).reduce((a, [, s]) => a + s, 0);
  console.log(`Pyodide ${VERSION}: ${names.length} packages (${names.join(', ')})`);
  console.log(`Wheels ${mb(wheelTotal)}, core ${mb(total - wheelTotal)}, total ${mb(total)} in ${outDir}`);
  // Wheels are already compressed; the core files are what gzip or brotli on the host shrinks.
  let gz = 0;
  for (const [n] of sizes.filter(([n]) => !wheels.includes(n) && !n.startsWith('pyodide-lock'))) {
    gz += gzipSync(await readFile(join(outDir, n)), { level: 9 }).length;
  }
  console.log(`First visit transfers about ${mb(gz + wheelTotal)} (core gzipped to ${mb(gz)}, plus the wheels)`);
}

main().catch((e) => {
  console.error(`fetch_runtime: ${e.message}`);
  process.exit(1);
});
