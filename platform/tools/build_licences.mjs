#!/usr/bin/env node
// Writes platform/app/public/licences.txt: the notices for everything the deployed planner ships.
//
//   1. The planner's own code (Apache-2.0, the repository's LICENSE).
//   2. Every JavaScript package bundled into the app: the runtime dependencies in
//      platform/app/package.json and everything they depend on, each with its version and the
//      licence file(s) from its folder in node_modules.
//   3. The Python runtime served from /runtime/: Pyodide (MPL-2.0), CPython (PSF License), and
//      every wheel in public/runtime/pyodide/<version>/, with the licence files from each wheel's
//      .dist-info. When the runtime has not been fetched yet, a fixed list with each package's
//      licence name is written instead, so a build never fails on it.
//
// Run by `npm run prebuild` (and `predev`), or by hand: node platform/tools/build_licences.mjs

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { strFromU8, unzipSync } from '../app/node_modules/fflate/esm/index.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../..');
const app = resolve(here, '../app');
const out = join(app, 'public/licences.txt');

const RULE = '='.repeat(78);
const rule = '-'.repeat(78);
const LICENCE_FILE = /^(licen[cs]e|copying|notice|copyright)([-._].*)?$/i;

// Licence texts are copied as written; only line endings and trailing blank lines change.
const tidy = (text) => text.replace(/\r\n?/g, '\n').trimEnd();

// ---------- JavaScript packages ----------

/** Where `name` resolves from `fromDir`, as Node would find it. */
function findPackage(name, fromDir) {
  let dir = fromDir;
  for (;;) {
    const candidate = join(dir, 'node_modules', name);
    if (existsSync(join(candidate, 'package.json'))) return candidate;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}

function licenceFiles(dir) {
  return readdirSync(dir)
    .filter((f) => LICENCE_FILE.test(f) && statSync(join(dir, f)).isFile())
    .sort()
    .map((f) => ({ name: f, text: tidy(readFileSync(join(dir, f), 'utf8')) }));
}

function jsPackages() {
  const root = JSON.parse(readFileSync(join(app, 'package.json'), 'utf8'));
  const seen = new Map();
  const queue = Object.keys(root.dependencies ?? {}).map((name) => ({ name, from: app }));
  while (queue.length) {
    const { name, from } = queue.shift();
    const dir = findPackage(name, from);
    if (!dir) continue; // an optional dependency that is not installed
    const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'));
    const key = `${pkg.name}@${pkg.version}`;
    if (seen.has(key)) continue;
    // Type definitions are never bundled.
    if (pkg.name.startsWith('@types/')) continue;
    const licence = typeof pkg.license === 'string' ? pkg.license : pkg.license?.type ?? 'see licence text';
    seen.set(key, { name: pkg.name, version: pkg.version, licence, homepage: pkg.homepage ?? '', files: licenceFiles(dir) });
    for (const dep of Object.keys(pkg.dependencies ?? {})) queue.push({ name: dep, from: dir });
  }
  return [...seen.values()].sort((a, b) => a.name.localeCompare(b.name));
}

// ---------- Python runtime ----------

// Used only when public/runtime/ has not been fetched: the packages the engine loads, with the
// licence each one declares. The versions are the ones in the pinned Pyodide lock.
const WHEELS_FALLBACK = [
  ['numpy', 'BSD-3-Clause and bundled notices'], ['pandas', 'BSD-3-Clause'], ['python-dateutil', 'Apache-2.0 and BSD-3-Clause'],
  ['pytz', 'MIT'], ['six', 'MIT'], ['jsonschema', 'MIT'], ['jsonschema-specifications', 'MIT'], ['referencing', 'MIT'],
  ['rpds-py', 'MIT'], ['attrs', 'MIT'], ['pyrsistent', 'MIT'], ['typing-extensions', 'PSF-2.0'],
];

function metadataField(meta, field) {
  const m = meta.match(new RegExp(`^${field}: (.+)$`, 'mi'));
  return m ? m[1].trim() : '';
}

function pythonRuntime() {
  const base = join(app, 'public/runtime/pyodide');
  const version = existsSync(base) ? readdirSync(base).find((d) => /^\d/.test(d)) : null;
  if (!version) return { version: null, python: null, wheels: null };
  const dir = join(base, version);
  const lock = JSON.parse(readFileSync(join(dir, 'pyodide-lock.json'), 'utf8'));
  const wheels = [];
  for (const file of readdirSync(dir).filter((f) => f.endsWith('.whl')).sort()) {
    const members = unzipSync(new Uint8Array(readFileSync(join(dir, file))), {
      filter: (f) => /\.dist-info\/(METADATA|.*(licen[cs]e|copying|notice)[^/]*)$/i.test(f.name),
    });
    const metaPath = Object.keys(members).find((p) => p.endsWith('.dist-info/METADATA'));
    const meta = metaPath ? strFromU8(members[metaPath]) : '';
    const licence = metadataField(meta, 'License-Expression') || metadataField(meta, 'License')
      || (meta.match(/^Classifier: License :: (?:OSI Approved :: )?(.+)$/m)?.[1] ?? 'see licence text');
    const files = Object.keys(members)
      .filter((p) => p !== metaPath)
      .sort()
      .map((p) => ({ name: p.replace(/^[^/]+\.dist-info\/(licenses\/)?/, ''), text: tidy(strFromU8(members[p])) }));
    wheels.push({ name: metadataField(meta, 'Name') || file, version: metadataField(meta, 'Version'), licence, files });
  }
  return { version, python: lock.info?.python ?? null, wheels };
}

// ---------- Writing ----------

function section(lines, title, version, licence, files, note) {
  lines.push(rule, `${title}${version ? ` ${version}` : ''}`, `Licence: ${licence}`);
  if (note) lines.push(note);
  lines.push(rule, '');
  if (!files.length) lines.push('(No licence file is included in this package; the licence named above applies.)', '');
  for (const f of files) {
    if (files.length > 1) lines.push(`[${f.name}]`, '');
    lines.push(f.text, '');
  }
}

const js = jsPackages();
const py = pythonRuntime();
const lines = [];

lines.push(
  'EV-SIENT Planner: licences and notices',
  RULE,
  '',
  'This file lists the software the planner is built from and runs on, with each licence.',
  'It is generated when the planner is built, by platform/tools/build_licences.mjs.',
  '',
  'Contents',
  '  1. The planner',
  '  2. JavaScript packages bundled into the planner',
  '  3. The Python runtime the model runs on (Pyodide, CPython and Python packages)',
  '',
  'Map data shown after Show Map on the Results step is not part of the planner: the basemap',
  'comes from OpenFreeMap (openfreemap.org) using OpenStreetMap data, (c) OpenStreetMap',
  'contributors, available under the Open Database License (openstreetmap.org/copyright).',
  '',
  '',
  RULE,
  '1. The planner',
  RULE,
  '',
  'The EV-SIENT Planner and the EV-SIENT model (the fcf_m2 package) are licensed under the',
  'Apache License, Version 2.0. The full text follows.',
  '',
  tidy(readFileSync(join(repo, 'LICENSE'), 'utf8')),
  '',
  '',
  RULE,
  '2. JavaScript packages bundled into the planner',
  RULE,
  '',
  ...js.map((p) => `  ${p.name} ${p.version} (${p.licence})`),
  '',
);
for (const p of js) section(lines, p.name, p.version, p.licence, p.files, p.homepage ? `Home: ${p.homepage}` : '');

lines.push(
  '',
  RULE,
  '3. The Python runtime the model runs on',
  RULE,
  '',
  'The model runs in the browser on Pyodide, a build of CPython for WebAssembly, served from this',
  'site\'s /runtime/ folder unchanged from the Pyodide release. Pyodide\'s own source code and the',
  'notices for the libraries compiled into its runtime are at https://github.com/pyodide/pyodide.',
  '',
  `  Pyodide ${py.version ?? '(version as fetched by platform/tools/fetch_runtime.mjs)'} (MPL-2.0)`,
  `  CPython ${py.python ?? '3.14'} (PSF-2.0)`,
  ...(py.wheels ?? WHEELS_FALLBACK.map(([name, licence]) => ({ name, version: '', licence })))
    .map((w) => `  ${w.name}${w.version ? ` ${w.version}` : ''} (${w.licence})`),
  '',
);
section(lines, 'Pyodide', py.version, 'Mozilla Public License 2.0 (MPL-2.0)',
  [{ name: 'MPL-2.0', text: tidy(readFileSync(join(here, 'licences/MPL-2.0.txt'), 'utf8')) }],
  'Source: https://github.com/pyodide/pyodide');
section(lines, 'CPython', py.python, 'Python Software Foundation License Version 2 (PSF-2.0)',
  [{ name: 'LICENSE', text: tidy(readFileSync(join(here, 'licences/CPython-3.14.txt'), 'utf8')) }],
  'Source: https://www.python.org/');
if (py.wheels) {
  for (const w of py.wheels) section(lines, w.name, w.version, w.licence, w.files, '');
} else {
  lines.push('(The runtime had not been fetched when this file was built, so the licence texts of the Python', 'packages above are not included. Each package\'s licence is named in the list.)', '');
}

writeFileSync(out, lines.join('\n') + '\n');
const kb = (statSync(out).size / 1024).toFixed(0);
console.log(`licences.txt: ${js.length} JavaScript packages, ${py.wheels ? py.wheels.length : 0} Python wheels, ${kb} KB`);
