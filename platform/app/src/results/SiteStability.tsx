// Two cards for one site in the Results detail panel: its Score Breakdown, with the weights, and
// How Stable Is This Rank: the rank range and chance of first place across plausible weightings,
// the rank range with one weight moved 5 points, what unconfirmed inputs could do, and the plain
// sentence about which weight change flips the top site. Every number is the engine's
// (browser_api.stability); the wording is ./stability.ts.

import type { RunResult, SiteResult } from '../engine/protocol';
import { ScoreBreakdown } from './ScoreBreakdown';
import { inputSentence, rankRange, rankSentence, share, STABILITY_CAVEAT, useStability, weightsLine } from './stability';
import '../styles/stability.css';

export function SiteStability({ run, site }: { run: RunResult; site: SiteResult }) {
  const stab = useStability(run);
  const total = run.sites.length;
  const loading = <p className="sd-loading" role="status">Reading the engine's breakdown</p>;
  const failed = stab.status === 'error'
    ? <p className="sd-error" role="alert">This could not be read: {stab.message}</p> : null;
  const s = stab.status === 'ready' ? stab.value.sites.find((x) => x.siteId === site.siteId) : undefined;
  const r = stab.status === 'ready' ? stab.value : null;
  const draws = r?.rankStability.draws ?? 0;

  return (
    <>
      <section className="sd-card" aria-labelledby="sd-breakdown">
        <h3 className="sd-card__title" id="sd-breakdown">Score Breakdown</h3>
        {stab.status === 'loading' && loading}
        {failed}
        {r && !s && <p className="footnote">The engine's breakdown has no row for this site.</p>}
        {s && <ScoreBreakdown site={s} />}
      </section>

      <section className="sd-card" aria-labelledby="sd-stable">
        <h3 className="sd-card__title" id="sd-stable">How Stable Is This Rank</h3>
        {stab.status === 'loading' && loading}
        {failed}
        {r && s && (
          <>
            <dl className="sd-facts">
              <div className="sd-fact"><dt>Rank Range</dt><dd className="num">{rankRange(s.stability.rankLow, s.stability.rankHigh)}</dd></div>
              <div className="sd-fact"><dt>Chance of First Place</dt><dd className="num">{share(s.stability.pFirst)}</dd></div>
              <div className="sd-fact"><dt>Chance of Top Three</dt><dd className="num">{share(s.stability.pTop3)}</dd></div>
              <div className="sd-fact"><dt>One Weight Moved 5 Points</dt><dd className="num">{rankRange(s.weightCases.best, s.weightCases.worst)}</dd></div>
            </dl>
            <p className="rk-line">
              Published rank {s.rank} of {total}. {rankSentence(s, total, draws)}
            </p>
            <p className="rk-line rk-flip"><strong>Which weight change flips first place:</strong> {r.sensitivity.sentence}</p>
            {r.inputUncertainty.done ? (
              (['capacity', 'unconfirmed'] as const).map((k) => {
                const text = inputSentence(k, s.inputRange[k], total);
                return text ? <p className="rk-line" key={k}>{text}</p> : null;
              })
            ) : (
              <p className="rk-line">Unconfirmed inputs were not checked: {r.inputUncertainty.reason}</p>
            )}
            <p className="footnote">
              {STABILITY_CAVEAT} Rank Range is the 5th to 95th percentile across {draws.toLocaleString('en-US')} weightings drawn around
              the defaults. {weightsLine(r)}
            </p>
          </>
        )}
      </section>
    </>
  );
}
