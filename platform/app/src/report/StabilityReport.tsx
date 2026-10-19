// The report's rank-stability parts, in the report's own markup so the preview, the printout,
// the .html file and the PDF and Word downloads all carry them: a short paragraph in each site
// profile, and a part of Methods with the plain sentence about which weight change flips first
// place and the whole cohort's table. Every number is the engine's (browser_api.stability).

import { fmt } from '../results/format';
import {
  caseLine, inputLines, inputSentence, rankRange, rankSentence, share, STABILITY_CAVEAT, weightsLine,
} from '../results/stability';
import type { ReportModel } from './reportModel';

const scrollRegion = (label: string) => ({ role: 'region', 'aria-label': label, tabIndex: 0 }) as const;

export function ProfileStability({ m, siteId }: { m: ReportModel; siteId: string }) {
  const r = m.stability;
  const s = r?.sites.find((x) => x.siteId === siteId);
  if (!r || !s) return null;
  const N = m.run.sites.length;
  const inputs = r.inputUncertainty.done
    ? (['capacity', 'unconfirmed'] as const).map((k) => inputSentence(k, s.inputRange[k], N)).filter((t): t is string => !!t)
    : [];
  return (
    <>
      <h4 className="rp-h4">How Stable Is This Rank</h4>
      <p>
        {rankSentence(s, N, r.rankStability.draws)} It is in the top three in {share(s.stability.pTop3)} of them.
        Moving any one weight by {fmt.int(r.sensitivity.step)} points {s.weightCases.best === s.weightCases.worst
          ? `leaves it at rank ${s.weightCases.best}`
          : `puts it anywhere from rank ${s.weightCases.best} to ${s.weightCases.worst}`}.
        {inputs.length > 0 && ` ${inputs.join(' ')}`}
      </p>
    </>
  );
}

export function MethodsStability({ m }: { m: ReportModel }) {
  const r = m.stability;
  if (!r) {
    return (
      <>
        <h3 className="rp-h3" id="rp-stability">How Stable the Ranks Are</h3>
        <p>The engine's rank-stability check was not available for this report.</p>
      </>
    );
  }
  const N = m.run.sites.length;
  const nameOf = (id: string) => m.run.sites.find((s) => s.siteId === id)?.name ?? id;
  return (
    <>
      <h3 className="rp-h3" id="rp-stability">How Stable the Ranks Are</h3>
      <p>
        The weights are a judgement, and many inputs are not yet confirmed, so the report checks how much the order depends on them.
        It re-weights the scores above and changes none of them. {STABILITY_CAVEAT}
      </p>
      <p><strong>Which weight change flips first place:</strong> {r.sensitivity.sentence}</p>
      <p>{caseLine(r, nameOf)}</p>
      {inputLines(r, N).map((t) => <p key={t}>{t}</p>)}
      <div className="rp-tablewrap" {...scrollRegion('Rank stability table')}>
        <table className="rp-table rp-table--compact">
          <caption>
            Rank stability across {r.rankStability.draws.toLocaleString('en-US')} weightings drawn around the defaults (fixed seed {r.rankStability.seed}).
            First and Top Three are shares of the weightings; Rank Range is the 5th to 95th percentile.
          </caption>
          <thead>
            <tr>
              <th scope="col" className="rp-num">Rank</th>
              <th scope="col">Site</th>
              <th scope="col" className="rp-num">Score</th>
              <th scope="col" className="rp-num">First</th>
              <th scope="col" className="rp-num">Top Three</th>
              <th scope="col" className="rp-num">Rank Range</th>
              <th scope="col" className="rp-num">One Weight Moved</th>
            </tr>
          </thead>
          <tbody>
            {r.sites.map((s) => (
              <tr key={s.siteId}>
                <td className="rp-num">{s.rank}</td>
                <th scope="row">{s.name}</th>
                <td className="rp-num">{fmt.score(s.score)}</td>
                <td className="rp-num">{share(s.stability.pFirst)}</td>
                <td className="rp-num">{share(s.stability.pTop3)}</td>
                <td className="rp-num">{rankRange(s.stability.rankLow, s.stability.rankHigh)}</td>
                <td className="rp-num">{rankRange(s.weightCases.best, s.weightCases.worst)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rp-note">{weightsLine(r)} One Weight Moved is the best and worst rank when any one weight moves {fmt.int(r.sensitivity.step)} points up or down.</p>
    </>
  );
}
