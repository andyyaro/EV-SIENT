// Picks the engine: the real one in a Web Worker, or the Example City stand-in with ?engine=mock.
// The stand-in is imported only when asked for, so its recorded fixtures stay out of the
// production bundle's main chunk.

import type { EngineClient } from './protocol';
import { createWorkerEngine } from './workerClient';

let engine: EngineClient | null = null;

/** The stand-in, loaded on first use, behind the same interface. */
function lazyMock(): EngineClient {
  const loaded = import('./mock').then((m) => m.createMockEngine());
  const later = <K extends keyof EngineClient>(key: K) =>
    (async (...args: unknown[]) => {
      const mock = await loaded;
      return (mock[key] as (...a: unknown[]) => unknown)(...args);
    }) as EngineClient[K];
  return {
    kind: 'mock',
    boot: later('boot'),
    fields: later('fields'),
    reset: later('reset'),
    propose: later('propose'),
    remap: later('remap'),
    check: later('check'),
    fill: later('fill'),
    accept: later('accept'),
    run: later('run'),
    explain: later('explain'),
    provenance: later('provenance'),
    columns: later('columns'),
    columnsConfirm: later('columnsConfirm'),
    columnsRestore: later('columnsRestore'),
    explore: later('explore'),
    indexValidate: later('indexValidate'),
    indexRun: later('indexRun'),
    outputFiles: later('outputFiles'),
    cancel() { void loaded.then((m) => m.cancel()); },
  };
}

export function getEngine(): EngineClient {
  if (!engine) {
    const wantMock = new URLSearchParams(location.search).get('engine') === 'mock';
    engine = wantMock ? lazyMock() : createWorkerEngine();
  }
  return engine;
}
