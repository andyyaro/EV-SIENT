// What the planner's index found: the formula in words and numbers, the checks it passed, the
// ranked sites with how steady each rank is, the sites left out or not ranked and why, and, when a
// readiness run is open, the two rankings side by side. Every heading says it is the planner's own.

import { useId, useState } from 'react';
import { Icon } from '../components/Icon';
import { NOT_OFFICIAL, fmtNumber, fmtPoints, fmtShare, fmtShareFine, siteLabel, steadiness, type IndexOutcome, type IndexSite } from './model';
import { SlopeGraph } from './SlopeGraph';

const GATE_NAMES: Record<string, string> = {
  minimum_data: 'Enough data to rank',
  coverage: 'Each column has enough values',
  outliers: 'No extreme values setting the scale',
  dominance: 'No one column runs the index',
  barely_counts: 'Every column changes the ranking',
  size_bias: 'Not just ranking sites by size',
  double_counting: 'No two columns count the same thing',
};

const LEVEL_WORDS = { block: 'Stops the Index', strong: 'Strong Warning', warn: 'Warning' } as const;

export function IndexResults({ r, onDownload, comparisonNote }: { r: IndexOutcome; onDownload(): void; comparisonNote: string | null }) {
  if (r.refused) return <Refused r={r} />;
  const s = r.summary!;
  return (
    <div className="yi-results">
      <section className="yi-card yi-formula" aria-labelledby="yi-formula-title">
        <p className="yi-badge"><Icon name="info.circle" size={16} strokeWidth={2} /> {NOT_OFFICIAL}</p>
        <h3 className="yi-formula__name" id="yi-formula-title">{r.name}</h3>
        <p className="yi-formula__eq">
          <span className="hig-visually-hidden">The formula: </span>
          Score =&nbsp;{r.formula.map((f, i) => (
            <span key={f.column} className="yi-formula__term">
              {i > 0 && <span aria-hidden="true"> + </span>}
              <span className="num">{fmtPoints(f.weight * 100)}</span>&nbsp;×&nbsp;credit for {f.column}
            </span>
          ))}
        </p>
        <ul className="yi-formula__list" role="list">
          {r.formula.map((f) => (
            <li key={f.column}>
              <span className="yi-formula__share num">{fmtShareFine(f.weight)}</span>
              <span>
                <strong>{f.column}</strong>, {f.directionWords}. {f.describe.replace(`${f.column}: `, '').replace(/^./, (x) => x.toUpperCase())}{' '}
                <span className="yi-muted">Has a value at {fmtShare(f.coverage)} of the sites scored.</span>
              </span>
            </li>
          ))}
        </ul>
        <p className="yi-hint">{s.note} {s.disclosure}</p>
      </section>

      <dl className="yi-metrics" aria-label="Your index, counts">
        <div className="yi-metric"><dt className="metric__label">Ranked</dt><dd className="metric__value">{fmtNumber(s.ranked)}</dd></div>
        <div className="yi-metric"><dt className="metric__label">Not Ranked</dt><dd className="metric__value">{fmtNumber(s.unranked)}</dd></div>
        <div className="yi-metric"><dt className="metric__label">Left Out by a Rule</dt><dd className="metric__value">{fmtNumber(s.excluded)}</dd></div>
        <div className="yi-metric"><dt className="metric__label">With a Missing Value</dt><dd className="metric__value">{fmtNumber(s.withMissing)}</dd></div>
      </dl>

      <Gates r={r} />

      <Ranked r={r} />

      {r.unranked.length > 0 && (
        <section className="section yi-section" aria-labelledby="yi-unranked-title">
          <h3 className="yi-h3" id="yi-unranked-title">Not Ranked ({r.unranked.length})</h3>
          <ul className="yi-reasons" role="list">
            {r.unranked.map((u) => (
              <li key={u.siteId}><strong>{siteLabel(u)}</strong> <span className="yi-site-id">{u.siteId}</span>: {u.reason} Missing: {u.missing.join(', ')}.</li>
            ))}
          </ul>
        </section>
      )}

      {r.excluded.length > 0 && (
        <section className="section yi-section" aria-labelledby="yi-excluded-title">
          <h3 className="yi-h3" id="yi-excluded-title">Left Out by a Rule ({r.excluded.length})</h3>
          <ul className="yi-reasons" role="list">
            {r.excluded.map((x) => (
              <li key={x.siteId}>
                <strong>{siteLabel(x)}</strong> <span className="yi-site-id">{x.siteId}</span>:{' '}
                {x.reasons.map((why, i) => (
                  <span key={i}>{i > 0 && '; '}{why.reason}{why.missing.length ? ` (no value for ${why.missing.join(', ')})` : ''}</span>
                ))}.
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="section yi-section" aria-labelledby="yi-compare-title">
        <h3 className="yi-h3" id="yi-compare-title">Compared With the Readiness Ranking</h3>
        {r.comparison && r.comparison.sites.length > 0
          ? <SlopeGraph c={r.comparison} />
          : <p className="yi-muted">{comparisonNote ?? 'Run the readiness model to see the two rankings side by side.'}</p>}
      </section>

      <div className="yi-download">
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus hig-pressable" onClick={onDownload}>
          <Icon name="square.and.arrow.down" size={17} />
          <span className="hig-button__label">Download Your Index (.csv)</span>
        </button>
        <p className="yi-hint">Every site with its rank, points, rank band and each column's credit, every heading marked as your own index.</p>
      </div>
    </div>
  );
}

function Refused({ r }: { r: IndexOutcome }) {
  return (
    <div className="yi-card yi-refused" role="status">
      <p className="yi-badge"><Icon name="info.circle" size={16} strokeWidth={2} /> {NOT_OFFICIAL}</p>
      <h3 className="yi-h3">The Index Could Not Rank These Sites Yet</h3>
      <ul className="yi-refusals" role="list">
        {r.refusals.map((x, i) => (
          <li className="yi-refusal" key={i}><Icon name="exclamationmark.triangle" size={16} strokeWidth={2} className="yi-refusal__icon" /><span>{x.message}</span></li>
        ))}
      </ul>
      {r.gates.map((g) => <p className="yi-hint" key={g.id}>{g.message}</p>)}
    </div>
  );
}

function Gates({ r }: { r: IndexOutcome }) {
  const checked = r.gatesChecked;
  const failed = new Set(r.gates.map((g) => g.id));
  const passed = checked.filter((g) => !failed.has(g)).length;
  return (
    <section className="section yi-section" aria-labelledby="yi-gates-title">
      <div className="section__head">
        <h3 className="yi-h3" id="yi-gates-title">Checks on the Index</h3>
        <span className="section__aside num">{passed} of {checked.length} passed</span>
      </div>
      <p className="yi-hint">Standard checks for a composite index (the European Commission JRC's), plus two of the planner's own. A warning does not stop the index; it says what to look at.</p>
      <ul className="yi-gates" role="list">
        {checked.map((id) => {
          const found = r.gates.filter((g) => g.id === id);
          if (!found.length) {
            return (
              <li className="yi-gate" key={id}>
                <span className="yi-gate__mark is-ok"><Icon name="checkmark.circle.fill" size={16} strokeWidth={2} /> Passed</span>
                <span className="yi-gate__name">{GATE_NAMES[id] ?? id}</span>
              </li>
            );
          }
          return found.map((g, i) => (
            <li className="yi-gate" key={`${id}-${i}`}>
              <span className={`yi-gate__mark is-${g.level}`}><Icon name="exclamationmark.triangle" size={16} strokeWidth={2} /> {LEVEL_WORDS[g.level] ?? 'Warning'}</span>
              <span className="yi-gate__name">{GATE_NAMES[id] ?? id}</span>
              <span className="yi-gate__text">{g.message}</span>
            </li>
          ));
        })}
      </ul>
    </section>
  );
}

const FIRST = 25;

function Ranked({ r }: { r: IndexOutcome }) {
  const [all, setAll] = useState(false);
  const n = r.sites.length;
  const sites = all ? r.sites : r.sites.slice(0, FIRST);
  const k = r.summary?.k ?? 0;
  const draws = r.robustness?.draws ?? 0;
  const below = new Map(r.rankChanges.map((c) => [c.below, c]));
  return (
    <section className="section yi-section" aria-labelledby="yi-ranked-title">
      <div className="section__head">
        <h3 className="yi-h3" id="yi-ranked-title">Ranked Sites, Your Index</h3>
        <span className="section__aside num">{n} ranked</span>
      </div>
      <p className="yi-hint">
        {draws > 0
          ? <>The rank band is the range a site's rank stays inside in 90% of {fmtNumber(draws)} runs with every weight moved by about {fmtShare(r.robustness!.spread)}{r.robustness!.ordinalMapsNudged.length ? ' and the level values nudged' : ''}. A narrow band means the rank holds up if the weights were a little different. "Top {k}" is the share of runs that put the site in the top {k}.</>
          : 'Rank bands were not computed (no weight draws were asked for).'}
      </p>
      <div className="st-table-wrap yi-ranked" role="region" aria-labelledby="yi-ranked-cap" tabIndex={0}>
        <table className="st-table yi-table">
          <caption id="yi-ranked-cap" className="hig-visually-hidden">{NOT_OFFICIAL}. {n} sites in rank order, with points out of 100 and each rank's band.</caption>
          <thead>
            <tr>
              <th scope="col" className="yi-num-col">Rank</th>
              <th scope="col">Site</th>
              <th scope="col" className="yi-num-col">Points</th>
              <th scope="col">Rank Band</th>
              {draws > 0 && <th scope="col" className="yi-num-col">Top {k}</th>}
            </tr>
          </thead>
          <tbody>
            {sites.map((s) => <SiteRow key={s.siteId} s={s} n={n} draws={draws} change={below.get(s.siteId)?.sentences ?? []} />)}
          </tbody>
        </table>
      </div>
      {n > FIRST && (
        <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus yi-more" aria-expanded={all} onClick={() => setAll((a) => !a)}>
          <span className="hig-button__label">{all ? `Show the First ${FIRST}` : `Show All ${n} Sites`}</span>
        </button>
      )}
    </section>
  );
}

function SiteRow({ s, n, draws, change }: { s: IndexSite; n: number; draws: number; change: string[] }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const rob = s.robustness;
  const band = rob ? steadiness(rob.rankLow, rob.rankHigh) : null;
  const gap = s.bounds.best - s.bounds.worst;
  return (
    <>
      <tr>
        <td className="yi-num-col num yi-rank">{s.rank}</td>
        <th scope="row" className="yi-site-cell">
          <button type="button" className="yi-site-btn hig-focus" aria-expanded={open} aria-controls={`${id}-why`} onClick={() => setOpen((o) => !o)}>
            <span>{siteLabel(s)}</span>
            <Icon name={open ? 'chevron.up' : 'chevron.down'} size={12} strokeWidth={2.4} />
          </button>
          <span className="yi-site-id">{s.siteId}</span>
        </th>
        <td className="yi-num-col num">
          {fmtPoints(s.score)}
          {gap > 0.05 && <span className="yi-best">best case {fmtPoints(s.bounds.best)}</span>}
        </td>
        <td className="yi-band-cell">
          {rob && band ? (
            <span className="yi-band">
              <RankBand low={rob.rankLow} high={rob.rankHigh} rank={s.rank!} n={n} />
              <span className="yi-band__text num">
                <span className={`yi-band__word is-${band.key}`}>{band.word}</span>{' '}
                {rob.rankLow === rob.rankHigh ? `rank ${rob.rankLow}` : `${rob.rankLow} to ${rob.rankHigh}`}
              </span>
            </span>
          ) : <span className="yi-muted">Not computed</span>}
        </td>
        {draws > 0 && <td className="yi-num-col num">{rob ? fmtShare(rob.topShare) : ''}</td>}
      </tr>
      <tr className="yi-why-row" id={`${id}-why`} hidden={!open}>
        <td colSpan={draws > 0 ? 5 : 4}>
          <div className="yi-why">
            <p className="yi-why__lead">
              {fmtPoints(s.score)} points{gap > 0.05 ? `, or up to ${fmtPoints(s.bounds.best)} if its missing values earned full credit` : ''}. Has values for {fmtShare(s.completeness)} of the columns.
            </p>
            <ul className="yi-drivers" role="list">
              {s.drivers.map((d) => (
                <li key={d.column} className={'yi-driver' + (d.absent ? ' is-absent' : '')}>
                  <span className="yi-driver__name">{d.column}</span>
                  <span className="yi-driver__raw">{d.absent ? 'No value: no credit' : `${d.raw ?? ''}, credit ${fmtNumber(Math.round(d.value * 100) / 100)}`}</span>
                  <span className="yi-driver__pts num">{fmtPoints(d.points)} of {fmtPoints(d.max)}</span>
                  <span className="yi-driver__track" aria-hidden="true" style={{ width: `${Math.max(8, d.max)}%` }}>
                    {!d.absent && <span className="yi-driver__fill" style={{ width: `${d.max > 0 ? Math.min(100, (d.points / d.max) * 100) : 0}%` }} />}
                  </span>
                </li>
              ))}
            </ul>
            {change.length > 0 && (
              <>
                <p className="yi-why__sub">What would lift it past the site above</p>
                <ul className="yi-plain" role="list">{change.map((x, i) => <li key={i}>{x}</li>)}</ul>
              </>
            )}
          </div>
        </td>
      </tr>
    </>
  );
}

/** The rank band as a small picture: the whole field of ranks, the band, and the site's rank. Decoration: the text beside it says the same. */
function RankBand({ low, high, rank, n }: { low: number; high: number; rank: number; n: number }) {
  const W = 120, pad = 5;
  const x = (k: number) => pad + ((k - 1) / Math.max(1, n - 1)) * (W - 2 * pad);
  return (
    <svg className="yi-band__svg" width={W} height={14} viewBox={`0 0 ${W} 14`} aria-hidden="true" focusable="false">
      <title>{`Rank ${rank}; ${low === high ? 'the same rank' : `between ${low} and ${high}`} in 90% of runs, of ${n}`}</title>
      <line className="yi-band__track" x1={pad} x2={W - pad} y1={7} y2={7} />
      <rect className="yi-band__range" x={x(low) - 3} y={3} width={Math.max(6, x(high) - x(low) + 6)} height={8} rx={4} />
      <circle className="yi-band__dot" cx={x(rank)} cy={7} r={3} />
    </svg>
  );
}
