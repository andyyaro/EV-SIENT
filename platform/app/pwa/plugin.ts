// Writes dist/sw.js from pwa/sw.js once a production build is on disk, with the build's file
// lists in place of the template's marker:
//
//   shell    every file the app needs to open and run offline, each with its SHA-256: index.html,
//            the hashed bundles under assets/ (not source maps), the files from public/, and
//            runtime/engine/engine.json, so the page and the engine it names move together
//   runtime  the pinned Pyodide files and the engine archive engine.json names, kept by the
//            worker on first use of the model
//   version  a hash of both lists, so any change to any file gives a new worker
//
// The engine-check build (dev only) gets no worker.

import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join, relative, resolve, sep } from 'node:path';
import type { Plugin, ResolvedConfig } from 'vite';

const MARKER = '/* build: manifest */ null';
const ENGINE_JSON = 'runtime/engine/engine.json';

function walk(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]);
}

/** The PDF maker's compiler and fonts: about 30 MB, fetched only when a planner asks for a PDF. */
function onDemand(path: string): boolean {
  return path.startsWith('assets/') && /\.(wasm|otf)$/.test(path);
}

function inShell(path: string): boolean {
  if (path === ENGINE_JSON) return true;
  if (path.startsWith('runtime/') || path.endsWith('.map') || onDemand(path)) return false;
  // The error page is CloudFront's, and the worker is not part of its own shell.
  return path !== '404.html' && path !== 'sw.js';
}

export function serviceWorker(template: string): Plugin {
  let config: ResolvedConfig;
  return {
    name: 'evsient-service-worker',
    apply: 'build',
    configResolved(resolved) { config = resolved; },
    closeBundle() {
      if (config.mode === 'engine-check') return;
      const dist = resolve(config.root, config.build.outDir);
      const files = walk(dist).map((f) => relative(dist, f).split(sep).join('/')).sort();
      const sha256 = (path: string) => createHash('sha256').update(readFileSync(join(dist, path))).digest('hex');
      const shell = files.filter(inShell).map((url) => ({ url, sha256: sha256(url) }));
      const runtime = files.filter((f) => f.startsWith('runtime/pyodide/'));
      if (existsSync(join(dist, ENGINE_JSON))) {
        const engine = JSON.parse(readFileSync(join(dist, ENGINE_JSON), 'utf8')) as { file: string };
        runtime.push(`runtime/engine/${engine.file}`);
      } else {
        this.warn(`${ENGINE_JSON} is not in the build; the planner will not work offline (run platform/tools/build_engine.py)`);
      }
      const later = files.filter(onDemand);
      const version = createHash('sha256').update(JSON.stringify({ shell, runtime, later })).digest('hex').slice(0, 16);
      const source = readFileSync(template, 'utf8');
      if (!source.includes(MARKER)) throw new Error(`${template} has lost its manifest marker`);
      writeFileSync(join(dist, 'sw.js'), source.replace(MARKER, JSON.stringify({ version, shell, runtime, later })));
    },
  };
}
