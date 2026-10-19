// Your Index: a workspace where the planner builds a ranking of their own from the columns of
// their file whose direction they confirmed, and sees how far it can be trusted. It is never the
// EV-SIENT readiness score and says so on every surface (docs/FLEXIBLE_ANALYSIS.md section 3).
// It needs a confirmed column dictionary, not a readiness run; with a run open it also compares
// the two rankings.

import { useEffect, useMemo, useRef, useState } from 'react';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { getEngine } from '../engine/client';
import type { ColumnEntry, Direction, IndexSpec, IndexValidation } from '../engine/protocol';
import { projectName } from '../lib/projectName';
import { useSession } from '../state/store';
import { Builder, Refusals, placeRefusals } from './Builder';
import { IndexResults } from './IndexResults';
import { indexCsv } from './indexCsv';
import { SelectField } from './SelectField';
import {
  NOT_OFFICIAL, REAL_ONLY_TEXT, confirmedDirection, defaultValue, freeName, isNumeric, newSpec, outcome, role, scorable,
} from './model';
import './yourindex.css';

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

const messageOf = (e: unknown) => (e instanceof Error ? e.message : String(e));
const realOnly = (e: unknown) => messageOf(e).startsWith(REAL_ONLY_TEXT);

/** A criterion whose column's confirmed direction changed since it was added follows the dictionary. */
function followDirections(spec: IndexSpec, entries: ColumnEntry[]): IndexSpec | null {
  const byName = new Map(entries.map((e) => [e.name, e]));
  let changed = false;
  const criteria = spec.criteria.map((c) => {
    const e = byName.get(c.column);
    const d = e ? confirmedDirection(e) : null;
    if (!e || !d || d === c.direction) return c;
    const s = scorable(e);
    if (!s.ok) return c;
    changed = true;
    const kind = s.kinds.includes(c.value.kind) ? c.value.kind : s.kinds[0];
    return { ...c, direction: d as Direction, value: defaultValue(e, kind, d) };
  });
  return changed ? { ...spec, criteria } : null;
}

/** A column to check size bias against: one whose name says population, if any. */
function populationGuess(entries: ColumnEntry[]): string {
  return entries.find((e) => isNumeric(e) && role(e) !== 'flag' && /popul/i.test(e.name))?.name ?? '';
}

export function YourIndexView() {
  const proposal = useSession((s) => s.proposal);
  const columns = useSession((s) => s.columns);
  const specs = useSession((s) => s.indexSpecs);
  const active = useSession((s) => s.indexActive);
  const indexRun = useSession((s) => s.indexResult);
  const run = useSession((s) => s.run);
  const details = useSession((s) => s.details);
  const table = useSession((s) => s.table);
  const loadColumns = useSession((s) => s.loadColumns);
  const confirmColumns = useSession((s) => s.confirmColumns);
  const setIndexSpecs = useSession((s) => s.setIndexSpecs);
  const runIndex = useSession((s) => s.runIndex);
  const go = useSession((s) => s.go);

  const mock = getEngine().kind === 'mock';
  const [engineNote, setEngineNote] = useState<string | null>(mock ? REAL_ONLY_TEXT : null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [validation, setValidation] = useState<{ for: string; v: IndexValidation } | null>(null);
  const [checking, setChecking] = useState(false);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('');
  const entries = useMemo(() => columns?.entries ?? [], [columns]);
  const [population, setPopulation] = useState(() => populationGuess(entries));
  const resultsRef = useRef<HTMLHeadingElement>(null);

  const spec: IndexSpec | null = specs[active] ?? null;
  const specJson = spec ? JSON.stringify(spec) : '';

  // The dictionary as the engine holds it now (another screen may have confirmed more columns).
  useEffect(() => {
    if (mock || !proposal) return;
    loadColumns().catch((e) => (realOnly(e) ? setEngineNote(REAL_ONLY_TEXT) : setLoadError(messageOf(e))));
  }, [mock, proposal, loadColumns]);

  useEffect(() => { if (!population) setPopulation(populationGuess(entries)); }, [entries, population]);

  useEffect(() => {
    if (!spec || !entries.length) return;
    const next = followDirections(spec, entries);
    if (next) setIndexSpecs(specs.map((x, i) => (i === active ? next : x)));
  }, [entries, spec, specs, active, setIndexSpecs]);

  // Live validation: the engine checks the settings a moment after each change.
  useEffect(() => {
    if (!spec || engineNote) return;
    let current = true;
    setChecking(true);
    const timer = window.setTimeout(() => {
      getEngine().indexValidate(spec)
        .then((v) => { if (current) setValidation({ for: specJson, v }); })
        .catch((e) => { if (current) { if (realOnly(e)) setEngineNote(REAL_ONLY_TEXT); else setValidation({ for: specJson, v: { ok: false, refusals: [{ code: 'engine', message: messageOf(e) }], spec: null } }); } })
        .finally(() => { if (current) setChecking(false); });
    }, 300);
    return () => { current = false; window.clearTimeout(timer); };
  }, [specJson, columns, engineNote]);

  const update = (next: IndexSpec) => setIndexSpecs(specs.map((x, i) => (i === active ? next : x)));
  const start = () => setIndexSpecs([...specs, newSpec(freeName('My Index', specs))], specs.length);
  const duplicate = () => spec && setIndexSpecs([...specs, { ...structuredClone(spec), name: freeName(`${spec.name} Copy`, specs) }], specs.length);
  const remove = () => {
    if (!spec || !window.confirm(`Delete ${spec.name}? Its settings are removed from this session and from the next project file you save.`)) return;
    setIndexSpecs(specs.filter((_, i) => i !== active), Math.max(0, active - 1));
  };

  const options = population ? { populationColumn: population } : undefined;
  const inputNow = spec ? JSON.stringify({ spec, options: options ?? {} }) : '';
  const v = validation && validation.for === specJson ? validation.v : null;
  const refusals = v?.refusals ?? [];
  const placed = spec ? placeRefusals(refusals, spec) : null;
  const ready = !!v?.ok && !checking;
  const blocked = !spec ? null : checking || !v ? 'Checking the settings' : v.ok ? null : 'Fix the items marked above first.';

  async function doRun() {
    if (!spec || !ready || running) return;
    setRunning(true);
    setStatus('Running your index on this device. With many sites this can take a little while.');
    try {
      await runIndex(spec, options);
      setStatus('Your index has run. The results are below.');
      requestAnimationFrame(() => resultsRef.current?.focus());
    } catch (e) {
      if (realOnly(e)) { setEngineNote(REAL_ONLY_TEXT); setStatus(''); }
      else setStatus(`Your index could not run: ${messageOf(e)}`);
    } finally {
      setRunning(false);
    }
  }

  const result = indexRun ? outcome(indexRun.result) : null;
  const stale = !!indexRun && indexRun.input !== inputNow;
  const comparisonNote = !run
    ? 'Run the readiness model (the Run step) to see the two rankings side by side.'
    : indexRun && indexRun.runId !== run.runId
      ? 'The readiness model has run again since your index ran. Run Your Index again to compare with the latest run.'
      : result && !result.comparison
        ? 'Run Your Index again to compare it with the readiness run.'
        : 'No site is ranked in both.';

  const head = (
    <PageHead
      title="Your Index"
      lede="Rank your sites by the columns that matter to you, weighted your way. The engine on this device checks the settings and scores every site."
    >
      <p className="yi-badge yi-badge--head"><Icon name="info.circle" size={16} strokeWidth={2} /> {NOT_OFFICIAL}. It is labelled as yours everywhere it appears.</p>
    </PageHead>
  );

  if (engineNote) {
    return (
      <div className="page yi">
        {head}
        <div className="yi-card yi-calm" role="status">
          <Icon name="info.circle" size={22} className="yi-calm__icon" />
          <div>
            <p className="yi-calm__title">Your Index Needs the Full Engine</p>
            <p>
              Your index reads your own file's columns, so it runs only with the full planner engine on this device. This copy of the planner is using
              recorded sample answers instead, which cannot read your columns. Open the planner without "engine=mock" in the address to build your index.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page page--wide yi">
      {head}

      {loadError && (
        <div className="yi-card yi-calm" role="alert">
          <Icon name="exclamationmark.triangle" size={22} className="yi-calm__icon" />
          <div><p className="yi-calm__title">Your Columns Could Not Be Read</p><p>{loadError}</p></div>
        </div>
      )}

      {!spec ? (
        <div className="yi-card yi-empty">
          <h2 className="yi-h3">Start an Index</h2>
          <p>
            Choose columns from your file, give each a weight, and say how its values earn credit. Only columns whose direction you have
            confirmed can be scored. Your settings are kept with this session and saved in the project file.
          </p>
          <button type="button" className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus hig-pressable" onClick={start}>
            <Icon name="plus" size={17} strokeWidth={2.2} />
            <span className="hig-button__label">Start Your Index</span>
          </button>
        </div>
      ) : (
        <>
          <div className="yi-card yi-picker">
            <div className="yi-picker__fields">
              {specs.length > 1 && (
                <SelectField label="Index" value={String(active)} onChange={(x) => setIndexSpecs(specs, Number(x))}>
                  {specs.map((x, i) => <option key={i} value={i}>{x.name || `Index ${i + 1}`}</option>)}
                </SelectField>
              )}
              <div className="yi-field yi-field--grow">
                <label className="yi-field__label" htmlFor="yi-name">Index Name</label>
                <input
                  id="yi-name" className="yi-text hig-focus" type="text" value={spec.name} maxLength={120}
                  aria-invalid={placed!.name.length > 0 || undefined}
                  aria-describedby={placed!.name.length ? 'yi-name-errs' : 'yi-name-hint'}
                  onChange={(e) => update({ ...spec, name: e.target.value })}
                />
                <span className="yi-hint" id="yi-name-hint">A name of your own, so it is never mistaken for the readiness score.</span>
              </div>
            </div>
            <Refusals items={placed!.name} id="yi-name-errs" />
            <div className="yi-picker__buttons">
              <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={start}>
                <span className="hig-button__label">New Index</span>
              </button>
              <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={duplicate}>
                <span className="hig-button__label">Duplicate</span>
              </button>
              <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={remove}>
                <span className="hig-button__label">Delete</span>
              </button>
            </div>
          </div>

          <Refusals items={placed!.general} />

          {columns
            ? <Builder key={active} spec={spec} entries={entries} refusals={refusals} onChange={update}
                onConfirmDirection={(column, direction) => confirmColumns([{ column, direction }]).catch((e) => setStatus(messageOf(e)))} />
            : <p className="st-inline-status" role="status">Reading your columns</p>}

          <section className="section yi-section yi-run" aria-labelledby="yi-run-title">
            <h2 className="section__title" id="yi-run-title">Run</h2>
            <div className="yi-card yi-run__card">
              <SelectField
                label="Check for Size Bias Against" value={population} onChange={setPopulation}
                hint="A column such as population: the index is checked for simply ranking bigger places higher."
              >
                <option value="">No Size Check</option>
                {entries.filter((e) => isNumeric(e) && role(e) !== 'flag').map((e) => <option key={e.name} value={e.name}>{e.name}</option>)}
              </SelectField>
              <div className="yi-run__go">
                <button
                  type="button" className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus hig-pressable"
                  onClick={doRun} disabled={!ready || running} aria-busy={running || undefined} aria-describedby={blocked ? 'yi-run-why' : undefined}
                >
                  <Icon name="play.fill" size={16} />
                  <span className="hig-button__label">{running ? 'Running' : 'Run Your Index'}</span>
                </button>
                {blocked && !running && <p className="yi-hint" id="yi-run-why">{blocked}</p>}
              </div>
            </div>
            <p className="st-inline-status" role="status" aria-live="polite">{status}</p>
          </section>
        </>
      )}

      {result && (
        <section className="section yi-section" aria-labelledby="yi-results-title">
          <div className="section__head">
            <h2 className="section__title" id="yi-results-title" ref={resultsRef} tabIndex={-1}>Results: {result.name ?? 'Your Index'}</h2>
          </div>
          {stale && (
            <div className="notice yi-stale" role="status">
              <span className="notice__icon" aria-hidden="true"><Icon name="clock" size={20} /></span>
              <div>
                <p className="notice__title">Out of Date</p>
                <p className="notice__body">You changed the settings since these results were made. Run Your Index again to update them.</p>
              </div>
            </div>
          )}
          <IndexResults
            r={result}
            comparisonNote={comparisonNote}
            onDownload={() => { const out = indexCsv(result, projectName(details, table?.fileName)); save(out.blob, out.name); setStatus(`Saved ${out.name}.`); }}
          />
          {run && (
            <p className="yi-hint yi-foot">
              The readiness results are on the{' '}
              <button type="button" className="yi-link hig-focus" onClick={() => go('results')}>Results</button> step. Your index never changes them.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
