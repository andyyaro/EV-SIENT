// One site's score as four contributions: the bar is split into compartments as wide as each
// subscore's weight, each filled to the points the site earns there, so the filled parts add up
// to the score. The bar is decoration; the table under it says every number, and the parts are
// the engine's own rounding, so they add up exactly to the published score.

import type { StabilitySite } from '../engine/protocol';
import { fmt } from './format';
import { weightPoints } from './stability';

export function ScoreBreakdown({ site }: { site: StabilitySite }) {
  const capId = `sb-cap-${site.siteId}`;
  return (
    <div className="sb">
      <div className="sb__bar" aria-hidden="true">
        {site.subscores.map((s) => (
          <span className={`sb__part sb__part--${s.key}`} key={s.key} style={{ flexGrow: s.max, flexBasis: 0 }}>
            <span className="sb__fill" style={{ width: `${s.max > 0 ? Math.min(100, (s.shown / s.max) * 100) : 0}%` }} />
          </span>
        ))}
      </div>
      <div className="sb__scale" aria-hidden="true"><span>0</span><span>100 points</span></div>
      <table className="sb__table" aria-describedby={capId}>
        <caption className="hig-visually-hidden">Score breakdown for {site.name}: the points each subscore adds, and its weight.</caption>
        <thead>
          <tr>
            <th scope="col">Subscore</th>
            <th scope="col" className="sb__n">Weight</th>
            <th scope="col" className="sb__n">Value</th>
            <th scope="col" className="sb__n">Points</th>
          </tr>
        </thead>
        <tbody>
          {site.subscores.map((s) => (
            <tr key={s.key}>
              <th scope="row"><span className={`sb__swatch sb__swatch--${s.key}`} aria-hidden="true" />{s.label}</th>
              <td className="sb__n num">{weightPoints(s.weight)}</td>
              <td className="sb__n num">{fmt.one(s.value)}</td>
              <td className="sb__n num">{fmt.one(s.shown)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Score</th>
            <td className="sb__n num">100</td>
            <td />
            <td className="sb__n num sb__total">{fmt.score(site.score)}</td>
          </tr>
        </tfoot>
      </table>
      <p className="footnote" id={capId}>
        Each subscore runs from 0 to 100 and adds its weight times its value: {site.subscores[0] && (
          <>{weightPoints(site.subscores[0].weight)}% of {fmt.one(site.subscores[0].value)} is {fmt.one(site.subscores[0].shown)} points. </>
        )}
        The four add up to the score.
        {site.accessAdjustment < 1 && ` Demand is counted at ${fmt.pct(site.accessAdjustment)} here because the site is not recorded as open to the public; the value shown already includes that.`}
      </p>
    </div>
  );
}
