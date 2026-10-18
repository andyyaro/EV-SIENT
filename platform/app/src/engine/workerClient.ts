// The real engine: Pyodide plus fcf_m2 in a module Web Worker (./engine.worker.ts), reached
// through Comlink. OWNED BY THE ENGINE WORKSTREAM: this placeholder only fixes the shape.

import type { EngineClient } from './protocol';
import { EngineError } from './protocol';

export function createWorkerEngine(): EngineClient {
  const notYet = async (): Promise<never> => {
    throw new EngineError('The on-device engine is not wired up yet. Open the app with ?engine=mock to use the Example City sample.');
  };
  return {
    kind: 'worker',
    boot: notYet,
    fields: notYet,
    reset: notYet,
    propose: notYet,
    remap: notYet,
    check: notYet,
    accept: notYet,
    run: notYet,
    explain: notYet,
    outputFiles: notYet,
    cancel() {},
  };
}
