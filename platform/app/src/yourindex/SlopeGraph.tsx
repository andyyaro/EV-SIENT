// Your index beside the readiness ranking, as a slope graph: each line joins a site's place in the
// planner's order (left) to its place in the readiness order (right). Positions are the order among
// the sites shown; the true ranks are written beside every line end. A table holds every site, so
// nothing here is read from the picture alone. Never drawn on the readiness tier colours.

import { useId, useState } from 'react';
import { Icon } from '../components/Icon';
import { NOT_OFFICIAL, fmtNumber, fmtPoints, type ComparisonRow, type IndexComparison } from './model';

const SHOW = 10;

function shown(c: IndexComparison): ComparisonRow[] {
  const rows = c.sites.filter((r) => r.indexRank <= SHOW || r.readinessRank <= SHOW);
  // A readiness order with many ties (every site rank 1) would bring in every site: keep it short.
  return rows.sort((a, b) => a.indexRank - b.indexRank).slice(0, 2 * SHOW);
}

const label = (r: ComparisonRow) => r.name || r.siteId;
const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);

export function SlopeGraph({ c }: { c: IndexComparison }) {
  const [table, setTable] = useState(false);
  const id = useId();
  const rows = shown(c);
  if (!rows.length) return null;
  const left = [...rows].sort((a, b) => a.indexRank - b.indexRank || a.siteId.localeCompare(b.siteId));
  const right = [...rows].sort((a, b) => a.readinessRank - b.readinessRank || a.indexRank - b.indexRank);
  const yL = new Map(left.map((r, i) => [r.siteId, i]));
  const yR = new Map(right.map((r, i) => [r.siteId, i]));
  const biggest = new Set([...rows].sort((a, b) => Math.abs(b.shift) - Math.abs(a.shift)).filter((r) => r.shift !== 0).slice(0, 3).map((r) => r.siteId));

  const W = 640, row = 26, top = 34, H = top + rows.length * row + 8;
  const x1 = 240, x2 = W - 150;
  const y = (i: number) => top + i * row + row / 2;

  const rho = c.spearman;
  const agreement = rho === null
    ? 'The readiness scores do not vary across these sites, so the two orders cannot be compared with one number.'
    : `Rank correlation between the two orders: ${fmtNumber(Math.round(rho * 100) / 100)} (1 is the same order, 0 is unrelated, -1 is reversed), over ${c.n} sites in both.`;
  const summary = `${NOT_OFFICIAL}, beside the readiness ranking, for the ${rows.length} sites in the top ${SHOW} of either. ${agreement}`;

  return (
    <figure className="yi-slope" aria-labelledby={`${id}-cap`}>
      <figcaption id={`${id}-cap`} className="yi-slope__cap">
        <span className="yi-slope__title">Your Index Rank Beside Readiness Rank</span>
        <span className="yi-hint">{summary} The two answer different questions: this shows where they agree, not which is right.</span>
      </figcaption>
      <div className="yi-slope__scroll" role="region" aria-label="Slope graph, scrolls sideways on a narrow screen" tabIndex={0}>
        <svg className="yi-slope__svg" viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-label={summary}>
          <text className="yi-slope__head" x={x1} y={18} textAnchor="end">Your index (not official)</text>
          <text className="yi-slope__head" x={x2} y={18} textAnchor="start">Readiness</text>
          <line className="yi-slope__axis" x1={x1 + 8} x2={x1 + 8} y1={top} y2={H - 8} />
          <line className="yi-slope__axis" x1={x2 - 8} x2={x2 - 8} y1={top} y2={H - 8} />
          {rows.map((r) => {
            const a = y(yL.get(r.siteId)!), b = y(yR.get(r.siteId)!);
            const hi = biggest.has(r.siteId);
            return (
              <g key={r.siteId} className={hi ? 'yi-slope__site is-big' : 'yi-slope__site'}>
                <title>{`${label(r)}: your index rank ${r.indexRank}, readiness rank ${r.readinessRank}${r.shift ? `, ${Math.abs(r.shift)} places ${r.shift > 0 ? 'higher' : 'lower'} in your index` : ', the same place'}`}</title>
                <line className="yi-slope__line" x1={x1 + 8} y1={a} x2={x2 - 8} y2={b} />
                <circle className="yi-slope__dot" cx={x1 + 8} cy={a} r={4} />
                <circle className="yi-slope__dot" cx={x2 - 8} cy={b} r={4} />
                <text className="yi-slope__label" x={x1 - 4} y={a} textAnchor="end" dominantBaseline="central">{`${r.indexRank}. ${clip(label(r), 30)}`}</text>
                <text className="yi-slope__label" x={x2 + 4} y={b} textAnchor="start" dominantBaseline="central">{`${r.readinessRank}. ${clip(r.siteId, 16)}`}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <p className="yi-hint">Heavier lines mark the largest differences. Hover a line, or open the table, for each site's two ranks.</p>
      <div className={'hig-disclosure hig-disclosure--group yi-disclosure' + (table ? ' hig-disclosure--open' : '')}>
        <button type="button" className="hig-disclosure__trigger hig-disclosure__row hig-focus" aria-expanded={table} aria-controls={`${id}-table`} onClick={() => setTable((t) => !t)}>
          <span className="hig-disclosure__label">Every Site as a Table ({c.sites.length})</span>
          <span className="hig-disclosure__chevron" aria-hidden="true"><Icon name="chevron.right" size={17} strokeWidth={2.4} /></span>
        </button>
        <div className="hig-disclosure__content" id={`${id}-table`} hidden={!table}>
          <div className="st-table-wrap" role="region" aria-label="Both rankings, every site" tabIndex={0}>
            <table className="st-table yi-table">
              <caption className="hig-visually-hidden">{NOT_OFFICIAL}: each site's rank in your index and in the readiness ranking, in your index's order.</caption>
              <thead>
                <tr>
                  <th scope="col">Site</th>
                  <th scope="col" className="yi-num-col">Your Index Rank</th>
                  <th scope="col" className="yi-num-col">Your Index Points</th>
                  <th scope="col" className="yi-num-col">Readiness Rank</th>
                  <th scope="col">Difference</th>
                </tr>
              </thead>
              <tbody>
                {[...c.sites].sort((a, b) => a.indexRank - b.indexRank).map((r) => (
                  <tr key={r.siteId}>
                    <th scope="row" className="yi-site-cell">{label(r)}<span className="yi-site-id">{r.siteId}</span></th>
                    <td className="yi-num-col num">{r.indexRank}</td>
                    <td className="yi-num-col num">{fmtPoints(r.indexScore)}</td>
                    <td className="yi-num-col num">{r.readinessRank}</td>
                    <td>{r.shift === 0 ? 'Same place' : `${Math.abs(r.shift)} ${Math.abs(r.shift) === 1 ? 'place' : 'places'} ${r.shift > 0 ? 'higher' : 'lower'} in your index`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(c.notInIndex.length > 0 || c.notInReadiness.length > 0) && (
            <p className="yi-hint">
              {c.notInIndex.length > 0 && `${c.notInIndex.length} ${c.notInIndex.length === 1 ? 'site has' : 'sites have'} a readiness score but no rank in your index (left out by a rule or not ranked). `}
              {c.notInReadiness.length > 0 && `${c.notInReadiness.length} ${c.notInReadiness.length === 1 ? 'site is' : 'sites are'} ranked in your index but not in the readiness run.`}
            </p>
          )}
        </div>
      </div>
    </figure>
  );
}
