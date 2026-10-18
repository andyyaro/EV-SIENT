// A stand-in engine that answers from recorded Example City outputs (src/engine/fixtures/,
// written by the real browser_api.py on synthetic data). Used for interface work and tests with
// ?engine=mock, so screens can be built without the 14 MB runtime. It never pretends to read
// the planner's own file: propose() always answers for Example City.

import type {
  AcceptResult, CheckResult, EngineClient, Explanation, FieldCatalog, OutputFiles, Proposal,
  RemapRequest, RunResult, RuntimeInfo,
} from './protocol';
import { EngineError } from './protocol';
import infoJson from './fixtures/info.json';
import fieldsJson from './fixtures/fields.json';
import proposalJson from './fixtures/proposal.json';
import checkJson from './fixtures/check.json';
import acceptJson from './fixtures/accept.json';
import runJson from './fixtures/run.json';

const explains = import.meta.glob('./fixtures/explain_*.json', { import: 'default' });

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function createMockEngine(): EngineClient {
  let proposal: Proposal | null = null;
  let accepted = false;
  let ran = false;
  return {
    kind: 'mock',
    async boot(onProgress) {
      const steps = [
        { stage: 'runtime', fraction: 0.4, message: 'Preparing the model on this device' },
        { stage: 'packages', fraction: 0.75, message: 'Loading the data tools' },
        { stage: 'engine', fraction: 0.95, message: 'Loading the model' },
        { stage: 'ready', fraction: 1, message: 'Ready' },
      ] as const;
      for (const s of steps) { onProgress?.({ ...s }); await wait(120); }
      return {
        ...(infoJson as unknown as RuntimeInfo),
        pyodide: 'mock', engine: { version: 'fixtures', sha256: '' },
        timingsMs: { runtime: 0, packages: 0, engine: 0 },
      };
    },
    async fields() { return fieldsJson as unknown as FieldCatalog; },
    async reset() { proposal = null; accepted = false; ran = false; },
    async propose() { await wait(150); proposal = proposalJson as unknown as Proposal; accepted = ran = false; return proposal; },
    async remap(request: RemapRequest) {
      if (!proposal) throw new EngineError('Upload a file first.');
      const mapping: Record<string, string> = {};
      const status = { ...proposal.status };
      const absent: string[] = [];
      for (const [k, v] of Object.entries(request.mapping)) {
        if (v) { mapping[k] = v; status[k] = 'matched'; } else { absent.push(k); status[k] = 'unmatched'; }
      }
      proposal = { ...proposal, mapping, status, absent };
      accepted = ran = false;
      return proposal;
    },
    async check() { if (!proposal) throw new EngineError('Upload a file first.'); return checkJson as unknown as CheckResult; },
    async accept() { if (!proposal) throw new EngineError('Upload a file first.'); accepted = true; return acceptJson as unknown as AcceptResult; },
    async run() {
      if (!accepted) throw new EngineError('Accept the checked file before running the model.');
      await wait(400); ran = true; return runJson as unknown as RunResult;
    },
    async explain(siteId: string) {
      if (!ran) throw new EngineError('Run the model first.');
      const load = explains[`./fixtures/explain_${siteId}.json`];
      if (!load) throw new EngineError(`No site ${siteId} in these results.`);
      return (await load()) as Explanation;
    },
    async outputFiles() {
      if (!ran) throw new EngineError('Run the model first.');
      return (await import('./fixtures/output_files.json')).default as unknown as OutputFiles;
    },
    cancel() { /* nothing runs long enough to cancel */ },
  };
}
