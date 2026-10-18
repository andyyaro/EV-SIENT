// Picks the engine: the real one in a Web Worker, or the Example City stand-in with ?engine=mock.

import type { EngineClient } from './protocol';
import { createMockEngine } from './mock';
import { createWorkerEngine } from './workerClient';

let engine: EngineClient | null = null;

export function getEngine(): EngineClient {
  if (!engine) {
    const wantMock = new URLSearchParams(location.search).get('engine') === 'mock';
    engine = wantMock ? createMockEngine() : createWorkerEngine();
  }
  return engine;
}
