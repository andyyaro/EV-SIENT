// How Stable Are These Ranks: the whole cohort at once. The plain sentence about the smallest
// weight change that flips first place, what each 5-point move of one weight does, the share of
// plausible weightings each site comes first or in the top three, its rank range, and what
// unconfirmed inputs could do. Every number is the engine's (browser_api.stability).

import type { RunResult } from '../engine/protocol';
import { fmt, plural } from './format';
import { caseLine, inputLines, rankRange, share, STABILITY_CAVEAT, useStability, weightsLine } from './stability';
import '../styles/stability.css';

export function StabilityOverview({ run }: { run: RunResult }) {
  const stab = useStability(run);
  const total = run.sites.length;
  const nameOf = (id: string) => run.sites.find((s) => s.siteId === id)?.name ?? id;

  return (
    <section className="section rk-overview" aria-labelledby="rs-stable-title">
      <div className="section__head"><h2 className="section__title" id="rs-stable-title">How Stable Are These Ranks</h2></div>
      {stab.status === 'loading' && <p className="sd-loading" role="status">Checking how firm the ranks are</p>}
      {stab.status === 'error' && <p className="sd-error" role="alert">The stability check could not be read: {stab.message}</p>}
      {stab.status === 'ready' && (() => {
        const r = stab.value;
        const draws = r.rankStability.draws;
        return (
          <div className="rk-card">
            <p className="rk-line rk-flip">{r.sensitivity.sentence}</p>
            <p className="rk-line">{caseLine(r, nameOf)}</p>
            {inputLines(r, total).map((t) => <p className="rk-line" key={t}>{t}</p>)}
            <div className="rk-scroll" role="region" aria-labelledby="rk-table-cap" tabIndex={0}>
              {/* Explicit table roles: on narrow screens each row is laid out as a short card (stability.css). */}
              <table className="rk-table" role="table">
                <caption id="rk-table-cap" className="rk-caption">
                  Across {draws.toLocaleString('en-US')} weightings drawn around the defaults
                </caption>
                <thead role="rowgroup">
                  <tr role="row">
                    <th scope="col" role="columnheader" className="rk-n">Rank</th>
                    <th scope="col" role="columnheader" className="rk-site">Site</th>
                    <th scope="col" role="columnheader" className="rk-n">Score</th>
                    <th scope="col" role="columnheader" className="rk-n">First</th>
                    <th scope="col" role="columnheader" className="rk-n">Top Three</th>
                    <th scope="col" role="columnheader" className="rk-n">Rank Range</th>
                  </tr>
                </thead>
                <tbody role="rowgroup">
                  {r.sites.map((s) => (
                    <tr role="row" key={s.siteId}>
                      <td role="cell" className="rk-n num"><span className="rk-cell-label" aria-hidden="true">Rank </span>{s.rank}</td>
                      <th scope="row" role="rowheader" className="rk-site">{s.name}</th>
                      <td role="cell" className="rk-n num"><span className="rk-cell-label" aria-hidden="true">Score </span>{fmt.score(s.score)}</td>
                      <td role="cell" className="rk-n num"><span className="rk-cell-label" aria-hidden="true">First </span>{share(s.stability.pFirst)}</td>
                      <td role="cell" className="rk-n num"><span className="rk-cell-label" aria-hidden="true">Top Three </span>{share(s.stability.pTop3)}</td>
                      <td role="cell" className="rk-n num"><span className="rk-cell-label" aria-hidden="true">Rank Range </span>{rankRange(s.stability.rankLow, s.stability.rankHigh)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="footnote">
              {STABILITY_CAVEAT} First and Top Three are shares of the {plural(draws, 'weighting')}; Rank Range is the 5th to 95th percentile.{' '}
              {weightsLine(r)}
            </p>
          </div>
        );
      })()}
    </section>
  );
}
