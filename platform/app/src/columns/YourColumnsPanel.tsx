// Your Columns on Map Columns: one card per column of the planner's file, as the engine's column
// dictionary reads it (docs/FLEXIBLE_ANALYSIS.md section 1). Closed until the planner opens it, so
// the model mapping above works exactly as before. Nothing here changes the readiness score.

import { useEffect, useMemo, useState } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import type { ColumnEntry } from '../engine/protocol';
import { plural } from '../lib/fieldText';
import { useSession } from '../state/store';
import { ColumnCard } from './ColumnCard';
import { canRank, readingProblems } from './columnText';
import { confirmColumns, engineMessage, loadColumns } from './dictionary';
import './columns.css';

type Filter = 'all' | 'problems' | 'rank' | 'todo';

const FILTERS: { key: Filter; label: string; test: (e: ColumnEntry) => boolean }[] = [
  { key: 'all', label: 'All', test: () => true },
  { key: 'todo', label: 'Not Confirmed', test: (e) => e['evsient:provenance'] !== 'confirmed_by_user' },
  { key: 'rank', label: 'Can Rank Sites', test: (e) => canRank(e['evsient:role']) },
  { key: 'problems', label: 'Reading Problems', test: (e) => readingProblems(e).length > 0 },
];

export function YourColumnsPanel() {
  const table = useSession((s) => s.table);
  const proposal = useSession((s) => s.proposal);
  const busy = useSession((s) => s.busy);
  const labels = useSession((s) => s.columnDictionary?.labels);
  const [open, setOpen] = useState(false);
  const [entries, setEntries] = useState<ColumnEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [announcement, setAnnouncement] = useState('');
  const [confirmingAll, setConfirmingAll] = useState(false);

  // A new file starts closed, with nothing read yet.
  useEffect(() => { setOpen(false); setEntries(null); setError(null); setFilter('all'); }, [table]);

  // Read (or read again after a change in Map Columns, which the cards record) while open.
  useEffect(() => {
    if (!open || !proposal) return;
    let live = true;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        await useSession.getState().bootEngine();
        const result = await loadColumns();
        if (live) setEntries(result.entries);
      } catch (e) {
        if (live) setError(engineMessage(e));
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => { live = false; };
  }, [open, proposal]);

  const counts = useMemo(() => {
    const list = entries ?? [];
    return {
      confirmed: list.filter((e) => e['evsient:provenance'] === 'confirmed_by_user').length,
      rankable: list.filter((e) => canRank(e['evsient:role'])).length,
      directed: list.filter((e) => canRank(e['evsient:role']) && e['evsient:direction'] && e['evsient:direction'] !== 'neither').length,
      noDirection: list.filter((e) => canRank(e['evsient:role']) && !e['evsient:direction']).length,
      problems: list.filter((e) => readingProblems(e).length > 0).length,
    };
  }, [entries]);

  if (!table || !proposal) return null;

  const shown = entries ? entries.filter(FILTERS.find((f) => f.key === filter)!.test) : [];
  const unconfirmed = entries?.filter((e) => e['evsient:provenance'] !== 'confirmed_by_user') ?? [];
  const disabled = !!busy || confirmingAll;

  /** Keep a card's result: the engine's whole dictionary comes back, so every card updates. */
  function confirmed(next: ColumnEntry[], message: string) {
    setEntries(next);
    setAnnouncement(message);
  }

  async function confirmAllAsSuggested() {
    if (!unconfirmed.length) return;
    setConfirmingAll(true);
    setError(null);
    try {
      const n = unconfirmed.length;
      const result = await confirmColumns(unconfirmed.map((e) => ({ column: e.name, confirm: true })), {});
      setEntries(result.entries);
      setAnnouncement(`Confirmed ${plural(n, 'column')} as suggested. No direction was chosen for any of them.`);
    } catch (e) {
      setError(engineMessage(e));
    } finally {
      setConfirmingAll(false);
    }
  }

  return (
    <section className="section yc" aria-labelledby="yc-title">
      <div className="section__head">
        <h2 id="yc-title" className="section__title">Your Columns <span className="st-count num">{table.columns.length}</span></h2>
      </div>
      <p className="section__intro">
        How the planner reads every column in your file, including the ones the model does not use. Check each one,
        and choose a direction for any column you may want to rank sites by. Nothing here changes the readiness score.
      </p>
      <button
        type="button"
        className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus yc-open"
        aria-expanded={open}
        aria-controls="yc-panel"
        onClick={() => setOpen((o) => !o)}
      >
        <Icon name={open ? 'chevron.up' : 'chevron.down'} size={16} strokeWidth={2.2} />
        <span className="hig-button__label">{open ? 'Hide Your Columns' : 'Review Your Columns'}</span>
      </button>

      <div id="yc-panel" className="yc-panel" hidden={!open}>
        <div role="status" aria-live="polite" className="st-inline-status">
          {loading && !entries ? 'Reading your columns.' : confirmingAll ? 'Confirming your columns.' : announcement}
        </div>

        {error && (
          <Banner tone={entries ? 'error' : 'info'} title={entries ? 'That Change Was Not Made' : 'Your Columns Are Not Available'} onDismiss={entries ? () => setError(null) : undefined}>
            <p>{error}</p>
          </Banner>
        )}

        {entries && (
          <>
            <div className="yc-summary card">
              <ul className="yc-summary__counts" aria-label="Your Columns summary">
                <li><strong className="num">{counts.confirmed}</strong> of {plural(entries.length, 'column')} confirmed</li>
                <li><strong className="num">{counts.directed}</strong> of {counts.rankable} that could rank sites have a direction</li>
                {counts.problems > 0 && <li><strong className="num">{counts.problems}</strong> with reading problems</li>}
              </ul>
              {unconfirmed.length > 0 && (
                <div className="yc-summary__all">
                  <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" disabled={disabled} onClick={() => void confirmAllAsSuggested()}>
                    <span className="hig-button__label">Confirm All as Suggested</span>
                  </button>
                  <p className="footnote">Accepts the kind and unit shown for the {plural(unconfirmed.length, 'column')} not yet confirmed. It never chooses a direction; choose those one by one.</p>
                </div>
              )}
            </div>

            <div className="st-filter yc-filter" role="group" aria-label="Show columns">
              {FILTERS.map((f) => {
                const n = entries.filter(f.test).length;
                return (
                  <button key={f.key} type="button" className={`st-filter__btn hig-focus${filter === f.key ? ' is-on' : ''}`} aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
                    {f.label}<span className="num">{n}</span>
                  </button>
                );
              })}
            </div>

            {counts.noDirection > 0 && filter !== 'problems' && (
              <p className="footnote yc-gap-bottom">
                {plural(counts.noDirection, 'column')} could rank sites but {counts.noDirection === 1 ? 'has' : 'have'} no direction yet. A column needs a direction you chose before it can be used to rank sites.
              </p>
            )}

            {shown.length
              ? <ul className="yc-list">{shown.map((e) => <ColumnCard key={e.name} entry={e} label={labels?.[e.name]} disabled={disabled} onConfirmed={confirmed} />)}</ul>
              : <p className="footnote">No columns match this filter.</p>}
          </>
        )}
      </div>
    </section>
  );
}
