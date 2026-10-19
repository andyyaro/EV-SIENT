// The engine's score breakdown and rank-stability checks (browser_api.stability), fetched once
// per run, and the fixed wording the Results screen and the report use to say them. Every number
// is the engine's; this file only words it. The method is docs/methodology/rank_stability.md.

import { getEngine } from '../engine/client';
import type { InputRange, InputScenarioKey, RunResult, StabilityResult, StabilitySite } from '../engine/protocol';
import { useLoad, type Loadable } from './data';
import { andList, fmt } from './format';

const cache = new Map<string, Promise<StabilityResult>>();

export function fetchStability(runId: string): Promise<StabilityResult> {
  let p = cache.get(runId);
  if (!p) {
    p = getEngine().stability();
    p.catch(() => cache.delete(runId));
    cache.set(runId, p);
  }
  return p;
}

export function useStability(run: RunResult | null): Loadable<StabilityResult> {
  return useLoad(run ? `${run.runId}\u0000stability` : null, () => fetchStability(run!.runId));
}

const whole = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

/** "1 to 4", or "1" when the range is a single rank. */
export function rankRange(low: number, high: number): string {
  return low === high ? `${low}` : `${low} to ${high}`;
}

/** A share of the drawn weightings as a whole percentage; "Under 1%" rather than a misleading 0%. */
export function share(p: number): string {
  if (p > 0 && p < 0.005) return 'Under 1%';
  if (p < 1 && p > 0.995) return 'Over 99%';
  return fmt.pct(p);
}

/** e.g. "in 1,416 of 2,000 weightings" */
export function shareCount(p: number, draws: number): string {
  return `in ${whole.format(Math.round(p * draws))} of ${whole.format(draws)} weightings`;
}

/** Weight in points of 100, as the planner reads it: 0.45 -> "45". */
export function weightPoints(w: number): string {
  return fmt.int(w * 100);
}

/** The one-sentence summary of a site's rank stability across the drawn weightings. */
export function rankSentence(site: StabilitySite, total: number, draws: number): string {
  const s = site.stability;
  const where = s.rankLow === s.rankHigh
    ? `It ranks ${s.rankLow} of ${total} under almost every weighting tried`
    : `Under most weightings tried it ranks between ${s.rankLow} and ${s.rankHigh} of ${total}`;
  const first = s.pFirst > 0
    ? `and comes first ${shareCount(s.pFirst, draws)}`
    : 'and never comes first';
  return `${where} (5th to 95th percentile), ${first}.`;
}

const SCENARIO_LEAD: Record<InputScenarioKey, string> = {
  capacity: 'If its electrical capacity, not yet confirmed, turned out anywhere from none to plenty',
  unconfirmed: 'If every input not yet confirmed here did the same',
};

/** A plain sentence for one input scenario at one site, or null when nothing at the site is unconfirmed. */
export function inputSentence(key: InputScenarioKey, r: InputRange | undefined, total: number): string | null {
  if (!r || !r.drivers.length) return null;
  const ranks = r.bestRank === r.worstRank ? `rank ${r.bestRank}` : `rank anywhere from ${r.bestRank} to ${r.worstRank} of ${total}`;
  return `${SCENARIO_LEAD[key]}, the score could be ${fmt.score(r.low)} to ${fmt.score(r.high)}, and the site could ${ranks}.`;
}

export const STABILITY_CAVEAT =
  'A planning-support check, not a probability that a site is the right choice. "Chance" is the share of plausible weightings drawn around the defaults in which the site lands there; the input ranges say what unconfirmed inputs could do, not what they are likely to do.';

/** What each 5-point move of one weight does to first place. */
export function caseLine(r: StabilityResult, nameOf: (id: string) => string): string {
  const flips = r.sensitivity.cases.filter((c) => c.topChanged);
  const n = r.sensitivity.cases.length;
  if (!flips.length) {
    return `Moving any one weight up or down by ${fmt.int(r.sensitivity.step)} points (the others scaled to match) leaves ${nameOf(r.sensitivity.top)} first in all ${n} cases.`;
  }
  const parts = flips.map((c) => `${c.label} ${c.change > 0 ? 'up' : 'down'} ${fmt.int(Math.abs(c.change))} points puts ${nameOf(c.top)} first`);
  return `Moving one weight up or down by ${fmt.int(r.sensitivity.step)} points (the others scaled to match) changes first place in ${flips.length} of ${n} cases: ${andList(parts)}.`;
}

/** One sentence per input scenario: how many sites could rank first. */
export function inputLines(r: StabilityResult, total: number): string[] {
  const u = r.inputUncertainty;
  if (!u.done) return [`Unconfirmed inputs were not checked: ${u.reason}`];
  return u.scenarios.map((sc) => {
    const n = sc.couldBeFirst.length;
    const lead = sc.key === 'capacity'
      ? 'If electrical capacity, where it is not yet confirmed, turned out anywhere from none to plenty'
      : 'If every input not yet confirmed were allowed to do the same';
    return `${lead}, ${n === total ? `any of the ${total} sites` : `${n} of the ${total} sites`} could rank first.`;
  });
}

/** How far the drawn weights typically moved, against the defaults, in points of 100. */
export function weightsLine(r: StabilityResult): string {
  const spread = r.rankStability.weightSpread.map((w) => `${w.label} ${Math.round(w.low * 100)} to ${Math.round(w.high * 100)}`).join(', ');
  const defaults = r.weights.map((w) => `${w.label} ${Math.round(w.weight * 100)}`).join(', ');
  return `Across the weightings each weight typically moved within ${spread} points (5th to 95th percentile; defaults ${defaults}).`;
}
