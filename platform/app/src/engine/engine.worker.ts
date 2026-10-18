// The real engine: Pyodide plus the unmodified fcf_m2 package, in a module Web Worker.
//
// Everything is served from this app's own origin (/runtime/, written by platform/tools/):
// the pinned Pyodide subset and the engine archive, whose SHA-256 is checked against
// engine.json before it is unpacked. Pyodide is imported at run time from that URL, never
// bundled, and its lock lists only numpy, pandas, jsonschema and their dependencies, so no
// other package can be fetched and no CDN is ever asked.
//
// Each method takes and returns the JSON strings src/fcf_m2/browser_api.py uses. A Python
// ValueError is a message for the planner and arrives as an EngineError with that message;
// anything else is a fault, logged here with its traceback and reported as a short sentence.

import * as Comlink from 'comlink';
import type { PyodideAPI } from 'pyodide';
import type { BootProgress } from './protocol';

const PYODIDE_VERSION = '314.0.7';
const origin = new URL(import.meta.env.BASE_URL, self.location.origin);
const INDEX_URL = new URL(`runtime/pyodide/${PYODIDE_VERSION}/`, origin).href;
const ENGINE_URL = new URL('runtime/engine/', origin).href;
const PKGROOT = '/work/pkgroot';

const GENERIC = 'The model stopped because of an internal error. Try again, and reload the page if it happens again.';

interface EngineManifest { version: string; file: string; sha256: string; files: string[] }

type Progress = (p: BootProgress) => void;

// Calls into browser_api through one small dispatcher, so a ValueError's plain message can be
// told apart from a fault without parsing tracebacks in JavaScript.
const BRIDGE = `
import sys, traceback
sys.path.insert(0, "${PKGROOT}/src")
from fcf_m2 import browser_api as _api

def _call(name, arg=None):
    fn = getattr(_api, name)
    try:
        return ("ok", fn() if arg is None else fn(arg))
    except ValueError as e:
        return ("refused", str(e))
    except Exception as e:
        return ("fault", "".join(traceback.format_exception(e)))

_call
`;

type Call = (name: string, arg?: string) => { toJs(): [string, string]; destroy(): void };

let call: Call | null = null;
let booting: Promise<string> | null = null;

const hex = (buf: ArrayBuffer) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

async function fetchOk(url: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`Could not load ${url} (HTTP ${res.status}).`);
  return res;
}

async function start(onProgress?: Progress): Promise<string> {
  const report = (stage: BootProgress['stage'], fraction: number, message: string) => {
    // A Comlink proxy returns a promise; a page that has gone away must not fail the boot.
    Promise.resolve(onProgress?.({ stage, fraction, message })).catch(() => {});
  };
  const t0 = performance.now();
  report('runtime', 0.02, 'Preparing the model on this device (about 14 MB, once)');
  // Fetched from this origin at run time; @vite-ignore keeps it out of the bundle.
  const { loadPyodide } = (await import(/* @vite-ignore */ `${INDEX_URL}pyodide.mjs`)) as {
    loadPyodide: (o: Record<string, unknown>) => Promise<PyodideAPI>;
  };
  const py = await loadPyodide({
    indexURL: INDEX_URL,
    lockFileURL: `${INDEX_URL}pyodide-lock.json`,
    // Also Pyodide's fallback for packages missing from the lock: this origin, never a CDN.
    packageBaseUrl: INDEX_URL,
    env: { HOME: '/work' },
  });
  const t1 = performance.now();

  report('packages', 0.3, 'Loading the data tools');
  await py.loadPackage(['numpy', 'pandas', 'jsonschema'], { checkIntegrity: true, messageCallback: () => {} });
  // Importing pandas is most of the boot (about 2 s); doing it here keeps the stages honest.
  py.runPython('import numpy, pandas, jsonschema');
  const t2 = performance.now();

  report('engine', 0.92, 'Loading the model');
  const manifest = (await (await fetchOk(`${ENGINE_URL}engine.json`, { cache: 'no-cache' })).json()) as EngineManifest;
  const archive = await (await fetchOk(ENGINE_URL + manifest.file)).arrayBuffer();
  const digest = hex(await crypto.subtle.digest('SHA-256', archive));
  if (digest !== manifest.sha256) {
    throw new Error(`The model archive ${manifest.file} does not match its published checksum; refusing to load it.`);
  }
  py.FS.mkdirTree(PKGROOT);
  py.unpackArchive(archive, 'zip', { extractDir: PKGROOT });
  call = py.runPython(BRIDGE) as unknown as Call;
  const info = JSON.parse(invoke('info'));
  const t3 = performance.now();

  report('ready', 1, 'Ready');
  return JSON.stringify({
    ...info,
    pyodide: py.version,
    engine: { version: manifest.version, sha256: manifest.sha256 },
    timingsMs: { runtime: Math.round(t1 - t0), packages: Math.round(t2 - t1), engine: Math.round(t3 - t2) },
  });
}

class EngineError extends Error {
  constructor(message: string) { super(message); this.name = 'EngineError'; }
}

function invoke(name: string, arg?: string): string {
  if (!call) throw new Error('The model is not loaded yet.');
  const result = arg === undefined ? call(name) : call(name, arg);
  let status: string, payload: string;
  try { [status, payload] = result.toJs(); } finally { result.destroy(); }
  if (status === 'ok') return payload;
  if (status === 'refused') throw new EngineError(payload);
  console.error(`fcf_m2.browser_api.${name} failed:\n${payload}`);
  throw new Error(GENERIC);
}

async function ready(): Promise<void> {
  if (!booting) throw new Error('The model is not loaded yet.');
  await booting;
}

const api = {
  /** Starts Pyodide and the engine once; later calls wait for the same start. */
  boot(onProgress?: Progress): Promise<string> {
    if (!booting) {
      booting = start(onProgress).catch((e: unknown) => {
        booting = null;
        console.error('Engine boot failed:', e);
        const text = e instanceof Error ? e.message : String(e);
        throw new Error(text.startsWith('The model archive') ? text
          : 'The model could not start on this device. Check the connection and reload the page.');
      });
    }
    return booting;
  },
  async info() { await ready(); return invoke('info'); },
  async fields() { await ready(); return invoke('fields'); },
  async reset() { await ready(); return invoke('reset'); },
  async propose(tableJson: string) { await ready(); return invoke('propose', tableJson); },
  async remap(mappingJson: string) { await ready(); return invoke('remap', mappingJson); },
  async check() { await ready(); return invoke('check'); },
  async accept(detailsJson: string) { await ready(); return invoke('accept', detailsJson); },
  async run(optionsJson: string) { await ready(); return invoke('run', optionsJson); },
  async explain(siteId: string) { await ready(); return invoke('explain', siteId); },
  async output_files() { await ready(); return invoke('output_files'); },
};

export type EngineWorkerApi = typeof api;

Comlink.expose(api);
