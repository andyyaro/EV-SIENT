// The Results workspace: what the numbers are (the engine's claims line, always shown), the totals,
// the ranked sites with a map and one site's details beside them, and Compare.

import { useEffect, useMemo, useRef, useState } from 'react';
import { Icon } from '../components/Icon';
import { useSession } from '../state/store';
import { ComparePanel } from './ComparePanel';
import { RankedTable } from './RankedTable';
import { SiteDetail } from './SiteDetail';
import { SiteMap } from './SiteMap';
import { YourColumnsControl } from './YourColumns';
import { columnIndex, compareCarried, passesFilter } from './carried';
import { useOutputFiles } from './data';
import { fmt, plural } from './format';
import '../styles/results.css';

export function ResultsView() {
  const run = useSession((s) => s.run);
  const fields = useSession((s) => s.fields);
  const selectedId = useSession((s) => s.selectedSiteId);
  const compare = useSession((s) => s.compare);
  const stale = useSession((s) => s.staleReason);
  const selectSite = useSession((s) => s.selectSite);
  const toggleCompare = useSession((s) => s.toggleCompare);
  const go = useSession((s) => s.go);
  const carried = useSession((s) => s.carried);
  const view = useSession((s) => s.yourColumns);
  const setView = useSession((s) => s.setYourColumns);
  const files = useOutputFiles(run);
  const [notesOpen, setNotesOpen] = useState(false);
  const [announce, setAnnounce] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);
  const splitRef = useRef<HTMLDivElement>(null);
  const pendingFocus = useRef(false);

  const site = run?.sites.find((s) => s.siteId === selectedId) ?? run?.sites[0] ?? null;

  // The table's rows: every site, or those the planner's filter keeps, in rank order or sorted by
  // one of Your Columns. Only the order on screen changes; every rank is the engine's.
  const tableSites = useMemo(() => {
    const all = run?.sites ?? [];
    if (!carried) return all;
    const kept = all.filter((s) => passesFilter(carried, view.filter, s.siteId));
    const k = view.sort ? columnIndex(carried, view.sort.column) : -1;
    if (k < 0) return kept;
    return [...kept].sort((a, b) => compareCarried(carried, k, a.siteId, b.siteId, view.sort!.dir) || a.rank - b.rank);
  }, [run, carried, view.filter, view.sort]);

  // On a narrow screen the details sit below the table: after choosing a site there, move to them.
  function focusTitle() {
    titleRef.current?.focus({ preventScroll: true });
    titleRef.current?.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  useEffect(() => {
    if (!pendingFocus.current) return;
    pendingFocus.current = false;
    focusTitle();
  }, [site?.siteId]);

  if (!run) {
    return (
      <div className="page">
        <header className="page-head"><h1 className="page-head__title">Results</h1></header>
        <p className="prose">Run the model first. Results appear here once a run finishes.</p>
      </div>
    );
  }

  const stacked = () => !!splitRef.current && getComputedStyle(splitRef.current).getPropertyValue('--rs-stacked').trim() === '1';

  function choose(siteId: string, from: 'table' | 'map' | 'compare') {
    const s = run!.sites.find((x) => x.siteId === siteId);
    if (!s) return;
    if (from === 'compare' || (from === 'table' && stacked())) {
      if (siteId === site?.siteId) focusTitle();
      else pendingFocus.current = true;
    }
    selectSite(siteId);
    setAnnounce(`Showing ${s.name}, rank ${s.rank} of ${run!.sites.length}.`);
  }

  function sortBy(column: string | null) {
    const now = view.sort;
    const sort = column === null ? null : now?.column !== column ? { column, dir: 1 as const } : now.dir === 1 ? { column, dir: -1 as const } : null;
    setView({ sort });
    setAnnounce(sort ? `Sorted by ${sort.column}, ${sort.dir === 1 ? 'lowest' : 'highest'} first. Not in the score: ranks are unchanged.` : 'In rank order.');
  }

  function toggle(siteId: string) {
    const s = run!.sites.find((x) => x.siteId === siteId);
    const was = compare.includes(siteId);
    if (!was && compare.length >= 3) { setAnnounce('Compare holds three sites. Remove one first.'); return; }
    toggleCompare(siteId);
    const n = compare.length + (was ? -1 : 1);
    setAnnounce(`${s?.name ?? siteId} ${was ? 'removed from' : 'added to'} Compare. ${n} of 3 chosen.`);
  }

  const t = run.totals;
  const compareSites = compare.map((id) => run.sites.find((s) => s.siteId === id)).filter((s): s is NonNullable<typeof s> => !!s).sort((a, b) => a.rank - b.rank);
  const extras = run.defaults.length + run.notes.length + run.costsWithheld.length;

  return (
    <div className="page page--wide rs">
      <header className="page-head rs-head">
        <h1 className="page-head__title">Results</h1>
        <p className="page-head__lede">
          {plural(t.sites, 'site')} ranked by readiness. Choose a site to see why it scores what it does, and compare up to three.
        </p>
      </header>

      {stale && (
        <div className="notice rs-stale" role="status">
          <span className="notice__icon" aria-hidden="true"><Icon name="exclamationmark.triangle" size={20} /></span>
          <div className="rs-stale__body">
            <p className="notice__title">Out of Date</p>
            <p className="notice__body">{stale} These results are from the last run. Run the model again to update them.</p>
          </div>
          <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={() => go('run')}>
            <span className="hig-button__label">Go to Run</span>
          </button>
        </div>
      )}

      <div className="rs-claims" role="note" aria-labelledby="rs-claims-title">
        <span className="rs-claims__icon" aria-hidden="true"><Icon name="info.circle" size={22} /></span>
        <div>
          <p className="rs-claims__title" id="rs-claims-title">What These Numbers Are</p>
          <p className="rs-claims__text">{run.claims}</p>
        </div>
      </div>

      <dl className="rs-metrics" aria-label="Totals">
        <div className="rs-metric"><dt className="metric__label">Sites Ranked</dt><dd className="metric__value">{fmt.int(t.sites)}</dd></div>
        <div className="rs-metric"><dt className="metric__label">Starter Ports Now</dt><dd className="metric__value">{fmt.int(t.starterPorts2026)}</dd></div>
        <div className="rs-metric"><dt className="metric__label">Pathway Ports</dt><dd className="metric__value">{fmt.int(t.pathwayPorts)}</dd></div>
        <div className="rs-metric"><dt className="metric__label">High-Confidence Sites</dt><dd className="metric__value">{fmt.int(t.highConfidenceSites)}<span className="rs-metric__of"> of {fmt.int(t.sites)}</span></dd></div>
      </dl>

      <div className={'hig-disclosure hig-disclosure--group rs-disclosure' + (notesOpen ? ' hig-disclosure--open' : '')}>
        <button
          type="button"
          className="hig-disclosure__trigger hig-disclosure__row hig-focus"
          aria-expanded={notesOpen}
          aria-controls="rs-notes"
          onClick={() => setNotesOpen((o) => !o)}
        >
          <span className="hig-disclosure__label">Defaults, Notes and Withheld Costs <span className="rs-disclosure__count">({extras})</span></span>
          <span className="hig-disclosure__chevron" aria-hidden="true"><Icon name="chevron.right" size={17} strokeWidth={2.4} /></span>
        </button>
        <div className="hig-disclosure__content rs-notes" id="rs-notes" hidden={!notesOpen}>
          <NoteList title="Defaults the Engine Applied" items={run.defaults} empty="None: every optional input was supplied." />
          <NoteList title="Notes" items={run.notes} empty="None." />
          <NoteList title="Costs Withheld for Missing Inputs" items={run.costsWithheld} empty="None: every site has the inputs its costs need." />
          <p className="footnote">Run {run.runId} · data confidence judged as of {run.asOf}.</p>
        </div>
      </div>

      <section className="section" aria-labelledby="rs-ranked-title">
        <div className="section__head"><h2 className="section__title" id="rs-ranked-title">Ranked Sites</h2></div>
        <div className="rs-split" ref={splitRef}>
          <div className="rs-master">
            {carried && <YourColumnsControl carried={carried} total={run.sites.length} showing={tableSites.length} />}
            {tableSites.length ? (
              <RankedTable
                sites={tableSites} selectedId={site?.siteId ?? null} compare={compare} onSelect={choose} onToggleCompare={toggle}
                carried={carried} shown={view.shown} sort={view.sort} onSort={sortBy}
              />
            ) : <p className="rs-compare-empty">No site matches the filter. Clear it to see every site.</p>}
            <SiteMap
              sites={run.sites} selectedId={site?.siteId ?? null} onSelect={(id) => choose(id, 'map')}
              carried={carried} colourBy={view.mapColour} onColourBy={(mapColour) => setView({ mapColour })}
            />
          </div>
          <div className="rs-detail">
            {site && (
              <SiteDetail
                ref={titleRef}
                run={run}
                site={site}
                fields={fields}
                files={files}
                carried={carried}
                inCompare={compare.includes(site.siteId)}
                compareFull={compare.length >= 3}
                onToggleCompare={() => toggle(site.siteId)}
                onBack={() => {
                  const btn = document.querySelector<HTMLButtonElement>('.rs-ranked button[aria-current="true"]');
                  btn?.focus({ preventScroll: true });
                  btn?.scrollIntoView({ block: 'center' });
                }}
              />
            )}
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="rs-compare-title">
        <div className="section__head">
          <h2 className="section__title" id="rs-compare-title">Compare Sites</h2>
          <span className="section__aside num">{compare.length} of 3 chosen</span>
        </div>
        <ComparePanel sites={compareSites} onRemove={toggle} onSelect={(id) => choose(id, 'compare')} carried={carried} />
      </section>

      <p className="hig-visually-hidden" aria-live="polite" aria-atomic="true">{announce}</p>
    </div>
  );
}

function NoteList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="rs-notes__group">
      <h3 className="rs-notes__title">{title}</h3>
      {items.length ? (
        <ul className="rs-notes__list">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
      ) : (
        <p className="rs-notes__empty">{empty}</p>
      )}
    </div>
  );
}
