// Explore: descriptive patterns in the planner's own columns (docs/FLEXIBLE_ANALYSIS.md, section 2).
// The engine runs every check on this device, counts each one, holds the false discovery rate at
// 10% across all of them and writes every sentence from fixed templates. This screen shows what it
// found, says how many patterns were checked against how many passed (zero is a real answer), and
// keeps saying that none of it is part of the EV-SIENT readiness score or ranks a site.

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { Progress } from '../components/Progress';
import type { ExploreCard } from '../engine/protocol';
import { useSession } from '../state/store';
import { ColumnSummaries, type Summary } from './ColumnSummaries';
import { PatternCard } from './PatternCard';
import { scanIsForCurrentFile, useExplore } from './exploreStore';
import { MEASURES, NOT_THE_SCORE, int, labelsOf, plural } from './text';
import './explore.css';

type Filter = 'all' | 'between' | 'missing';

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'between', label: 'Between Columns' },
  { key: 'missing', label: 'Missing Values' },
];

/** Roles that Explore compares; the rest (IDs, names, places, free text) are described only. */
const COMPARED_ROLES = new Set(['count', 'measure', 'score', 'percentage', 'money', 'year', 'ordinal', 'category', 'flag']);

function Disclosure({ id, title, count, open, onToggle, children, level = 2 }: {
  id: string; title: string; count?: number; open: boolean; onToggle: () => void; children: ReactNode; level?: 2 | 3;
}) {
  const Heading = level === 2 ? 'h2' : 'h3';
  return (
    <div className={'hig-disclosure hig-disclosure--group xp-disclosure' + (open ? ' hig-disclosure--open' : '')}>
      <Heading className="xp-disclosure__heading">
        <button type="button" className="hig-disclosure__trigger hig-disclosure__row hig-focus" aria-expanded={open} aria-controls={id} onClick={onToggle}>
          <span className="hig-disclosure__label">
            {title}{typeof count === 'number' && <span className="xp-disclosure__count num"> ({int(count)})</span>}
          </span>
          <span className="hig-disclosure__chevron" aria-hidden="true"><Icon name="chevron.right" size={17} strokeWidth={2.4} /></span>
        </button>
      </Heading>
      <div className="hig-disclosure__content xp-disclosure__content" id={id} hidden={!open}>{children}</div>
    </div>
  );
}

export function ExploreView() {
  const table = useSession((s) => s.table);
  const go = useSession((s) => s.go);
  const { status, result, entries, changed, error, scan, compareDictionary } = useExplore();
  const [filter, setFilter] = useState<Filter>('all');
  const [howOpen, setHowOpen] = useState(false);
  const [colsOpen, setColsOpen] = useState<boolean | null>(null);
  const [notOpen, setNotOpen] = useState(false);
  const [announce, setAnnounce] = useState('');
  const announced = useRef<unknown>(null);

  // Opening the screen checks the file the planner has open now, once; coming back to it only
  // asks whether the column descriptions changed since.
  useEffect(() => {
    if (!table) return;
    if (scanIsForCurrentFile()) void compareDictionary();
    else void scan();
  }, [table, scan, compareDictionary]);

  useEffect(() => {
    if (status === 'done' && result && announced.current !== result) {
      announced.current = result;
      setAnnounce(`Checked ${plural(result.checked, 'pattern')}. ${int(result.passed)} passed.`);
    }
  }, [status, result]);

  const labels = useMemo(() => labelsOf(result), [result]);

  // Pooled patterns in the engine's order, each with the within-group check that belongs to it.
  const patterns = useMemo(() => {
    const cards = result?.cards ?? [];
    const companions = new Map<string, ExploreCard>();
    for (const c of cards) {
      const of = (c.stratum as { of?: string } | null)?.of;
      if (c.kind === 'within' && of) companions.set(of, c);
    }
    return cards.filter((c) => c.kind !== 'within').map((card) => ({ card, companion: companions.get(card.id) }));
  }, [result]);

  const counts = {
    all: patterns.length,
    between: patterns.filter((p) => p.card.kind !== 'missingness').length,
    missing: patterns.filter((p) => p.card.kind === 'missingness').length,
  };
  const shown = patterns.filter((p) => filter === 'all' || (filter === 'missing') === (p.card.kind === 'missingness'));

  const head = (
    <header className="page-head">
      <span className="page-head__eyebrow">Your Data · Exploratory</span>
      <h1 className="page-head__title" tabIndex={-1}>Explore</h1>
      <p className="page-head__lede">
        Patterns in the columns of your own file, checked on this device. They describe your sites; they are not part of the EV-SIENT readiness score and never change a site&apos;s rank.
      </p>
    </header>
  );

  if (!table) {
    return (
      <div className="page page--wide xp">
        {head}
        <p className="prose">Upload a file first. Explore reads the columns of the file you upload.</p>
      </div>
    );
  }

  if (status === 'unavailable') {
    return (
      <div className="page page--wide xp" data-explore-state="unavailable">
        {head}
        <Banner tone="info" title="Explore Needs the Full Planner">
          <p>
            This copy of the planner is running on recorded sample answers, a stand-in used for testing. The stand-in cannot read
            the columns of your own file, so there are no patterns to show here. Everything else in the planner works as usual.
          </p>
          <p>Open the planner without the sample stand-in to explore your columns.</p>
        </Banner>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="page page--wide xp" data-explore-state="error">
        {head}
        <Banner
          tone="error"
          title="Explore Could Not Finish"
          action={<button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => void scan()}>Try Again</button>}
        >
          <p>{error}</p>
          <p>Your file and your readiness results are unchanged.</p>
        </Banner>
      </div>
    );
  }

  if (status !== 'done' || !result) {
    return (
      <div className="page page--wide xp" data-explore-state="busy">
        {head}
        <div className="xp-busy" role="status">
          <Progress label="Checking patterns in your columns on this device" detail="Every pair of columns is compared and counted. This can take a little while on a large file." />
        </div>
      </div>
    );
  }

  const health = result.health as { rows?: number; columns?: number; described?: number; unknown?: number };
  const summaries = (result.summaries ?? []) as Summary[];
  const skipped = (result.skipped ?? []) as { column: string; reason: string }[];
  const suppressed = (result.suppressed ?? []) as { note: string }[];
  const fdrPct = `${Math.round(result.fdr * 100)}%`;
  const compared = entries.filter((e) => COMPARED_ROLES.has(e['evsient:role']));
  const confirmed = compared.filter((e) => e['evsient:provenance'] === 'confirmed_by_user').length;
  const notTested = new Set(skipped.map((x) => x.column));
  const comparedCount = compared.filter((e) => !notTested.has(e.name)).length;
  const zero = result.passed === 0;
  const columnsOpen = colsOpen ?? zero;
  const notCompared = skipped.length + suppressed.length + (health.unknown ?? 0);
  const stratum = typeof result.stratum === 'string' ? labels[result.stratum] ?? result.stratum : null;

  return (
    <div className="page page--wide xp" data-explore-state="done">
      {head}

      <div className="xp-claims" role="note" aria-labelledby="xp-claims-title">
        <span className="xp-claims__icon" aria-hidden="true"><Icon name="info.circle" size={22} /></span>
        <div>
          <p className="xp-claims__title" id="xp-claims-title">What These Patterns Are</p>
          <p className="xp-claims__text">
            {NOT_THE_SCORE} Each pattern says that two columns tend to go together across your sites. It does not say that one
            changes the other, and it is a starting point for a question, not an answer.
          </p>
        </div>
      </div>

      {changed && (
        <Banner
          tone="stale"
          title="Your Column Descriptions Changed"
          action={<button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => void scan()}>Check Again</button>}
        >
          <p>These patterns were checked before the change. Check again to see them with the descriptions as they are now.</p>
        </Banner>
      )}

      <dl className="xp-metrics" aria-label="What was checked">
        <div className="xp-metric"><dt className="metric__label">Patterns Checked</dt><dd className="metric__value num">{int(result.checked)}</dd></div>
        <div className="xp-metric"><dt className="metric__label">Patterns That Passed</dt><dd className="metric__value num">{int(result.passed)}<span className="xp-metric__of"> of {int(result.checked)}</span></dd></div>
        <div className="xp-metric"><dt className="metric__label">Sites in Your File</dt><dd className="metric__value num">{int(health.rows ?? 0)}</dd></div>
        <div className="xp-metric"><dt className="metric__label">Columns Compared</dt><dd className="metric__value num">{int(comparedCount)}<span className="xp-metric__of"> of {int(health.columns ?? 0)}</span></dd></div>
      </dl>
      <p className="xp-bar-note">
        Every pattern checked counts. A pattern passes only when it still stands out from chance after all {plural(result.checked, 'check')} are
        taken into account, with the share of false finds held at {fdrPct} (the Benjamini-Hochberg method). Groups of fewer
        than {int(result.minGroup)} sites are never compared, and patterns resting on fewer than 30 sites are marked Few Sites.
      </p>

      {compared.length > 0 && confirmed < compared.length && (
        <div className="notice xp-unconfirmed" role="note">
          <span className="notice__icon xp-unconfirmed__icon" aria-hidden="true"><Icon name="info.circle" size={20} /></span>
          <div className="xp-unconfirmed__body">
            <p className="notice__title">Read With the App&apos;s Own Column Descriptions</p>
            <p className="notice__body">
              {confirmed
                ? `You have confirmed ${int(confirmed)} of the ${plural(compared.length, 'column')} Explore can compare; the rest are read as the app described them.`
                : `Explore read ${plural(compared.length, 'column')} as the app described them; you have not confirmed any yet.`}
              {' '}That is fine for describing patterns, and whether higher or lower is better is not needed here. If a column looks misread, check it in Map Columns.
            </p>
          </div>
          <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={() => go('map')}>
            <span className="hig-button__label">Go to Map Columns</span>
          </button>
        </div>
      )}

      {result.checked === 0 ? (
        <section className="section xp-zero" aria-labelledby="xp-zero-title">
          <div className="xp-zero__card">
            <span className="xp-zero__icon" aria-hidden="true"><Icon name="info.circle" size={28} strokeWidth={1.7} /></span>
            <div>
              <h2 className="section__title" id="xp-zero-title">Too Few Sites to Compare</h2>
              <p className="xp-zero__lede">
                {`Explore only compares groups of ${int(result.minGroup)} or more sites, and no pair of columns in this file has that many sites with values in both. So no pattern could be checked, and there is nothing to pass or fail.`}
              </p>
              <p className="xp-zero__next">Each column on its own is still described below. With more sites in the file, Explore can compare them.</p>
            </div>
          </div>
        </section>
      ) : zero ? (
        <section className="section xp-zero" aria-labelledby="xp-zero-title">
          <div className="xp-zero__card">
            <span className="xp-zero__icon" aria-hidden="true"><Icon name="checkmark.circle" size={28} strokeWidth={1.7} /></span>
            <div>
              <h2 className="section__title" id="xp-zero-title">No Pattern Passed</h2>
              <p className="xp-zero__lede">
                {`Explore checked ${plural(result.checked, 'pattern')} between your columns and none of them passed. That is a finished, useful answer, not an error.`}
              </p>
              <ul className="xp-zero__list">
                <li>No pair of your columns goes together more clearly than chance alone would produce, once all {int(result.checked)} checks are counted.</li>
                <li>So nothing in this file should be read as a trend across your sites. If someone points to one, ask whether it holds up here.</li>
                <li>Weak patterns can still exist: with more sites, or with columns read differently, a check can pass that does not pass now.</li>
              </ul>
              <p className="xp-zero__next">Each column on its own is described below: its spread, its groups and how much of it is blank.</p>
            </div>
          </div>
        </section>
      ) : (
        <section className="section" aria-labelledby="xp-found-title">
          <div className="section__head">
            <h2 className="section__title" id="xp-found-title">Patterns That Passed</h2>
            <span className="section__aside num">{int(result.passed)} of {int(result.checked)} checked</span>
          </div>
          <p className="section__intro">
            Strongest first. {NOT_THE_SCORE}
            {stratum ? ` Each pattern was also checked within each ${stratum}.` : ''}
          </p>
          <div className="st-filter" role="group" aria-label="Show patterns">
            {FILTERS.map((f) => (
              <button key={f.key} type="button" className={'st-filter__btn hig-focus' + (filter === f.key ? ' is-on' : '')} aria-pressed={filter === f.key}
                onClick={() => setFilter(f.key)} disabled={f.key !== 'all' && counts[f.key] === 0}>
                {f.label} <span className="num">{counts[f.key]}</span>
              </button>
            ))}
          </div>
          <div className="xp-list">
            {shown.map(({ card, companion }) => <PatternCard key={card.id} card={card} companion={companion} labels={labels} />)}
          </div>
          <Disclosure id="xp-how" title="How to Read a Pattern" level={3} open={howOpen} onToggle={() => setHowOpen((o) => !o)}>
            <dl className="xp-how">
              <div><dt>Sites Compared</dt><dd>How many sites have a value in both columns. Blank and unknown cells are left out, never guessed.</dd></div>
              <div><dt>Adjusted q</dt><dd>How clearly the pattern stands out from chance once every check is counted. Lower is clearer; a pattern passes at {result.fdr.toFixed(2)} or below.</dd></div>
              <div><dt>Strength</dt><dd>The dot is the size of the pattern from 0 (none) to 1; the shaded band is its 95% interval, the range it would likely fall in with similar sites.</dd></div>
              {Object.values(MEASURES).map((m) => (
                <div key={m.name}><dt>{m.name}</dt><dd>{m.what}</dd></div>
              ))}
            </dl>
          </Disclosure>
        </section>
      )}

      <section className="section xp-section" aria-label="Your columns one by one">
        <Disclosure id="xp-cols" title="Your Columns One by One" count={summaries.length} open={columnsOpen} onToggle={() => setColsOpen(!columnsOpen)}>
          <p className="section__intro">Each column on its own, from your file. {NOT_THE_SCORE}</p>
          <ColumnSummaries summaries={summaries} minGroup={result.minGroup} />
        </Disclosure>
      </section>

      {notCompared > 0 && (
        <section className="section xp-section" aria-label="What was not compared">
          <Disclosure id="xp-not" title="What Was Not Compared" count={notCompared} open={notOpen} onToggle={() => setNotOpen((o) => !o)}>
            <ul className="xp-not">
              {suppressed.map((x, i) => <li key={`s${i}`}>{x.note}</li>)}
              {skipped.map((x) => <li key={`k${x.column}`}><span className="xp-not__col">{labels[x.column] ?? x.column}</span>: {x.reason}.</li>)}
              {(health.unknown ?? 0) > 0 && (
                <li>{plural(health.unknown!, 'column')} could not be described, so {health.unknown === 1 ? 'it was' : 'they were'} left out. Describe {health.unknown === 1 ? 'it' : 'them'} in Map Columns to include {health.unknown === 1 ? 'it' : 'them'}.</li>
              )}
            </ul>
          </Disclosure>
        </section>
      )}

      <div className="xp-foot">
        <p className="footnote">
          Checked on this device; nothing was sent anywhere. Settings: false discovery rate {result.fdr.toFixed(2)}, smallest group {int(result.minGroup)} sites, 95% intervals from repeated resampling.
        </p>
        <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={() => void scan()}>
          <Icon name="arrow.clockwise" size={15} strokeWidth={2} />
          <span className="hig-button__label">Check Again</span>
        </button>
      </div>

      <p className="hig-visually-hidden" aria-live="polite" aria-atomic="true">{announce}</p>
    </div>
  );
}
