// The Explain card's fixed wording, filled only from the engine's numbers (browser_api.explain).
// Shared by the Results detail panel and the report's site profiles, so both say the same thing.

import type { Driver, Explanation } from '../engine/protocol';
import { fmt } from './format';

export interface ExplainSummary {
  sentences: string[];
  top: Driver[];
  weakest: Explanation['subscores'][number] | null;
}

/** The drivers that add the most points, largest first (only those that add any). */
export function topDrivers(e: Explanation, n = 2): Driver[] {
  return e.drivers.filter((d) => d.points > 0).sort((a, b) => b.points - a.points).slice(0, n);
}

/** The subscore with the smallest share of its possible points. */
export function weakestArea(e: Explanation) {
  let worst: Explanation['subscores'][number] | null = null;
  for (const s of e.subscores) {
    if (s.max <= 0) continue;
    if (!worst || s.points / s.max < worst.points / worst.max) worst = s;
  }
  return worst;
}

/** Lower-case a label's first letter for use mid-sentence, unless it starts with an acronym (ADA). */
export function lowerFirst(label: string): string {
  return /^[A-Z0-9]{2,}\b/.test(label) ? label : label.charAt(0).toLowerCase() + label.slice(1);
}

export function explainSummary(e: Explanation, total: number): ExplainSummary {
  const top = topDrivers(e);
  const weakest = weakestArea(e);
  const sentences = [`${e.name} scores ${fmt.score(e.score)} of 100, rank ${e.rank} of ${total}.`];
  const part = (d: Driver) => `${lowerFirst(d.label)} (${fmt.signed(d.points)})`;
  if (top.length === 2) sentences.push(`Its largest contributions are ${part(top[0])} and ${part(top[1])}.`);
  else if (top.length === 1) sentences.push(`Its only contribution is ${part(top[0])}.`);
  else sentences.push('No driver adds points to its score.');
  if (weakest) {
    sentences.push(`Its weakest area is ${lowerFirst(weakest.label)} (${fmt.points(weakest.points)} of ${fmt.points(weakest.max)} possible).`);
  }
  return { sentences, top, weakest };
}

/** Said when the engine counted demand at less than full weight, in its own numbers. */
export function accessSentence(e: Explanation): string | null {
  if (!(e.accessAdjustment < 1)) return null;
  return `This site is not recorded as open to the public, so the engine counts its demand at ${fmt.pct(e.accessAdjustment)}. The demand points shown already include that adjustment.`;
}

export function driverLine(d: Driver): string {
  if (d.absent) return `${d.label}: not recorded, earns no credit (up to ${fmt.points(d.max)} possible).`;
  return `${d.label}: ${fmt.signed(d.points)} of ${fmt.points(d.max)} possible${d.inverted ? ', lower is better' : ''}.`;
}
