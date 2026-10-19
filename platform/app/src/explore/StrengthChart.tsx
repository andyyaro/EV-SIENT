// How strong a pattern is and how sure the engine is of that: the effect on a 0 to 1 scale with its
// 95% interval. Drawn with plain elements like the driver bars in Results, and described in words
// for screen readers; the same numbers are written beside it.

import type { ExploreCard } from '../engine/protocol';
import { measure, num2, strength } from './text';

export function StrengthChart({ effect }: { effect: NonNullable<ExploreCard['effect']> }) {
  const m = measure(effect.name);
  const s = strength(effect);
  const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
  const interval = s.low !== null && s.high !== null;
  const words = `Strength ${num2(s.value)} on a scale from 0 to 1`
    + (interval ? `, 95% interval ${num2(s.low!)} to ${num2(s.high!)}.` : '.');
  return (
    <figure className="xp-strength">
      <div className="xp-strength__plot" role="img" aria-label={words}>
        <span className="xp-strength__track" aria-hidden="true">
          <span className="xp-strength__tick" style={{ left: '50%' }} />
          {interval && (
            <span className="xp-strength__band" style={{ left: pct(s.low!), width: pct(Math.max(0.004, s.high! - s.low!)) }} />
          )}
          <span className="xp-strength__dot" style={{ left: pct(s.value) }} />
        </span>
        <span className="xp-strength__scale" aria-hidden="true">
          <span>0</span><span>0.5</span><span>1</span>
        </span>
      </div>
      <figcaption className="xp-strength__caption">
        <span className="xp-strength__value num">
          {m.name}: {num2(effect.value)}
          {interval && <span className="xp-strength__interval"> (95% interval {num2(effect.low!)} to {num2(effect.high!)})</span>}
        </span>
      </figcaption>
    </figure>
  );
}
