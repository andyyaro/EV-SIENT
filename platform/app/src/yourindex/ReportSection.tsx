// The report's section for the planner's own index: the formula, the checks, and the first sites
// in its order, under a heading that says it is the planner's and not the readiness score. Plain
// report markup, so the preview, the printout, the .html, the PDF and the Word file all carry it.

import { NOT_OFFICIAL, formulaWords, fmtPoints, fmtShare, siteLabel, type IndexOutcome } from './model';

export const INDEX_SECTION = ['rp-your-index', 'Your Index (Not the EV-SIENT Readiness Score)'] as const;

const TOP = 20;

export function IndexReportSection({ r, n }: { r: IndexOutcome; n: number }) {
  const s = r.summary!;
  const failed = r.gates;
  return (
    <section className="rp-section" aria-labelledby={INDEX_SECTION[0]}>
      <h2 className="rp-h2" id={INDEX_SECTION[0]}><span className="rp-h2__n">{n}.</span> {INDEX_SECTION[1]}</h2>
      <p className="rp-callout"><strong>{NOT_OFFICIAL}.</strong> The planner built this index from columns of their own file and chose its weights. It is not part of the readiness model: no readiness score, rank, tier or port plan in this report used it.</p>
      <h3 className="rp-h3">{r.name}</h3>
      <ul>{formulaWords(r).map((line, i) => <li key={i}>{line}</li>)}</ul>
      <p>{s.note} {s.disclosure}</p>
      <p>
        {s.ranked} sites ranked, {s.unranked} not ranked for too few values, {s.excluded} left out by the planner's rules.
        {r.robustness && r.robustness.draws > 0 ? ` Rank bands come from ${r.robustness.draws} runs with each weight moved by about ${fmtShare(r.robustness.spread)}.` : ''}
      </p>
      <p>
        Checks: {r.gatesChecked.length - new Set(failed.map((g) => g.id)).size} of {r.gatesChecked.length} passed.
        {failed.length > 0 && ' Warnings:'}
      </p>
      {failed.length > 0 && <ul>{failed.map((g, i) => <li key={i}>{g.message}</li>)}</ul>}
      <div className="rp-tablewrap" role="region" aria-label="Your index, first sites" tabIndex={0}>
        <table className="rp-table rp-table--compact">
          <caption>{NOT_OFFICIAL}: the first {Math.min(TOP, r.sites.length)} of {r.sites.length} ranked sites.</caption>
          <thead>
            <tr>
              <th scope="col" className="rp-num">Rank</th><th scope="col">Site</th><th scope="col" className="rp-num">Points (of 100)</th>
              <th scope="col">Rank Band (90% of Runs)</th>
            </tr>
          </thead>
          <tbody>
            {r.sites.slice(0, TOP).map((x) => (
              <tr key={x.siteId}>
                <td className="rp-num">{x.rank}</td>
                <th scope="row">{siteLabel(x)}</th>
                <td className="rp-num">{fmtPoints(x.score)}</td>
                <td>{x.robustness ? (x.robustness.rankLow === x.robustness.rankHigh ? `Rank ${x.robustness.rankLow}` : `${x.robustness.rankLow} to ${x.robustness.rankHigh}`) : 'Not computed'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {r.comparison && r.comparison.spearman !== null && (
        <p>Rank correlation with the readiness ranking over {r.comparison.n} sites in both: {Math.round(r.comparison.spearman * 100) / 100}. The two answer different questions; this shows where they agree, not which is right.</p>
      )}
      <p className="rp-note">Every site, with each column's credit, is in the Your Index download (.csv) and on the Your Index sheet of the Excel workbook.</p>
    </section>
  );
}
