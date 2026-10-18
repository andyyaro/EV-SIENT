// Why a site scores what it does: a fixed sentence filled from the engine's numbers, then each
// driver's points against its maximum, grouped by subscore. Bars are decoration: every value is
// also written out, so the card reads the same without color or without sight.

import type { Explanation } from '../engine/protocol';
import { fmt } from './format';
import { accessSentence, explainSummary } from './explainText';

export function ExplainCard({ e, total }: { e: Explanation; total: number }) {
  const { sentences } = explainSummary(e, total);
  const access = accessSentence(e);
  const scale = Math.max(...e.drivers.map((d) => d.max), 1);
  return (
    <div className="ex">
      <p className="ex__sentence">{sentences.join(' ')}</p>
      {access && (
        <p className="ex__access">
          <span className="ex__access-tag">Demand at {fmt.pct(e.accessAdjustment)}</span> {access}
        </p>
      )}
      <p className="ex__key footnote">
        Each bar is the most a driver can add; the filled part is what it adds for this site. The drivers add up to the score.
      </p>
      {e.subscores.map((sub) => {
        const drivers = e.drivers.filter((d) => d.subscore === sub.key);
        const hid = `ex-${e.siteId}-${sub.key}`;
        return (
          <section className="ex__group" key={sub.key} aria-labelledby={hid}>
            <h4 className="ex__group-head" id={hid}>
              <span className="ex__group-name">{sub.label}</span>
              <span className="ex__group-pts num">
                {fmt.points(sub.points)} of {fmt.points(sub.max)} points
                <span className="ex__group-weight"> · weight {fmt.weight(sub.weight)}</span>
              </span>
            </h4>
            <ul className="ex__drivers" role="list">
              {drivers.map((d) => (
                <li className={'ex__driver' + (d.absent ? ' is-absent' : '')} key={d.key}>
                  <span className="ex__label">
                    {d.label}
                    {d.inverted && <span className="ex__hint"> (lower is better)</span>}
                  </span>
                  <span className="ex__value num">
                    {d.absent ? 'Not recorded: earns no credit' : <>{fmt.signed(d.points)}<span className="ex__of"> of {fmt.points(d.max)}</span></>}
                  </span>
                  <span className="ex__track" style={{ width: `${(d.max / scale) * 100}%` }} aria-hidden="true">
                    {!d.absent && <span className="ex__fill" style={{ width: `${d.max > 0 ? Math.min(100, (d.points / d.max) * 100) : 0}%` }} />}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
