// Up to three sites side by side. A row's highest (or, for cost and wait, lowest) value carries a
// word tag, so the differences scan without relying on color. Your Columns follow as their own
// group, untagged: they are the planner's values, not in the score.

import { Icon } from '../components/Icon';
import type { SiteResult } from '../engine/protocol';
import { NOT_IN_SCORE, carriedText, showCarried, type CarriedColumns } from './carried';
import { fmt, isNumber, sentence, SUBSCORE_KEYS, subscoreLabel, tierKey, tierShort } from './format';

interface Row {
  label: string;
  value(s: SiteResult): number | null;
  show(s: SiteResult): string;
  /** Which end of the row to tag, if any. */
  best?: 'high' | 'low';
  group?: string;
}

const ROWS: Row[] = [
  { group: 'Readiness', label: 'Rank', value: (s) => s.rank, show: (s) => String(s.rank), best: 'low' },
  { label: 'Score', value: (s) => s.score, show: (s) => fmt.score(s.score), best: 'high' },
  ...SUBSCORE_KEYS.map((k): Row => ({ label: subscoreLabel(k), value: (s) => s.subscores[k], show: (s) => fmt.one(s.subscores[k]), best: 'high' })),
  { group: 'Data Confidence', label: 'Confidence Score', value: (s) => s.confidence.score, show: (s) => `${fmt.one(s.confidence.score)}${s.confidence.level ? ` (${s.confidence.level})` : ''}`, best: 'high' },
  { group: 'Ports', label: 'Ports Now', value: (s) => s.portsNow, show: (s) => fmt.int(s.portsNow) },
  { label: 'Pathway Ports', value: (s) => s.pathwayPorts, show: (s) => fmt.int(s.pathwayPorts) },
  { label: 'Capacity Cap', value: (s) => s.capacityCap, show: (s) => fmt.int(s.capacityCap) },
  { group: 'Operations and Cost', label: 'Expected Sessions per Day', value: (s) => s.expectedSessionsDay, show: (s) => fmt.one(s.expectedSessionsDay) },
  { label: 'Utilization', value: (s) => s.utilization, show: (s) => fmt.pct(s.utilization) },
  { label: 'Mean Wait', value: (s) => s.meanWaitMin, show: (s) => fmt.minutes(s.meanWaitMin), best: 'low' },
  { label: 'Install Cost (Screening)', value: (s) => s.installCostUsd, show: (s) => fmt.usd(s.installCostUsd), best: 'low' },
  { label: 'Electrical Risk', value: () => null, show: (s) => (s.electricalRisk ? sentence(s.electricalRisk) : 'Not recorded') },
];

function bestOf(row: Row, sites: SiteResult[]): Set<string> {
  if (!row.best || sites.length < 2) return new Set();
  const vals = sites.map((s) => row.value(s)).filter(isNumber);
  if (vals.length < 2 || Math.min(...vals) === Math.max(...vals)) return new Set();
  const target = row.best === 'high' ? Math.max(...vals) : Math.min(...vals);
  return new Set(sites.filter((s) => row.value(s) === target).map((s) => s.siteId));
}

function groups(carried: CarriedColumns | null): { group: string; rows: Row[] }[] {
  const out: { group: string; rows: Row[] }[] = [];
  const yours = (carried?.columns ?? []).map((c, k): Row => ({
    group: k === 0 ? `Your Columns (${NOT_IN_SCORE})` : undefined, label: c.name, value: () => null,
    show: (s) => showCarried(c, carriedText(carried!, s.siteId, k)),
  }));
  for (const r of [...ROWS, ...yours]) {
    if (r.group || !out.length) out.push({ group: r.group ?? '', rows: [] });
    out[out.length - 1].rows.push(r);
  }
  return out;
}

const tagWord = (row: Row) => (row.label === 'Rank' ? 'Best' : row.best === 'high' ? 'Highest' : 'Lowest');

export function ComparePanel({ sites, onRemove, onSelect, carried = null }: {
  sites: SiteResult[]; onRemove(id: string): void; onSelect(id: string): void; carried?: CarriedColumns | null;
}) {
  if (!sites.length) {
    return (
      <div className="rs-compare-empty">
        <p>Choose up to three sites with the Compare boxes in the table, or Add to Compare on a site's details, to see them side by side.</p>
      </div>
    );
  }
  return (
    <div className="hig-table hig-table--ios rs-table rs-compare" role="region" aria-labelledby="rs-compare-cap" tabIndex={0}>
      {/* Explicit roles: on narrow screens each row's label sits above its values (results.css). */}
      <table className="hig-table__grid" role="table" style={{ '--rs-n': sites.length } as React.CSSProperties}>
        <caption id="rs-compare-cap" className="hig-visually-hidden">
          {sites.length === 1 ? 'One site chosen to compare. Add another to see differences.' : `${sites.length} sites side by side.`} Tags mark each row's highest or lowest value.
        </caption>
        <thead role="rowgroup">
          <tr role="row">
            <td role="cell" className="hig-table__heading rs-compare__corner" />
            {sites.map((s) => (
              <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading rs-compare__site" key={s.siteId}>
                <span className="rs-compare__name">
                  <button type="button" className="rs-compare__link hig-focus" onClick={() => onSelect(s.siteId)}>{s.name}</button>
                </span>
                <span className={`tier tier--${tierKey(s.tier)}`}><span className="tier__mark" aria-hidden="true" />{tierShort(s.tier)}</span>
                <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus rs-compare__remove" onClick={() => onRemove(s.siteId)} aria-label={`Remove ${s.name} from Compare`}>
                  <Icon name="xmark" size={14} strokeWidth={2.2} /><span className="hig-button__label">Remove</span>
                </button>
              </th>
            ))}
          </tr>
        </thead>
        {groups(carried).map(({ group, rows }) => (
          <tbody key={group} role="rowgroup" className={group.startsWith('Your Columns') ? 'rs-compare__yours' : undefined}>
            <tr role="row" className="rs-compare__grouprow">
              <th scope="rowgroup" role="rowheader" colSpan={sites.length + 1} className="rs-compare__group">{group}</th>
            </tr>
            {rows.map((row) => {
              const best = bestOf(row, sites);
              return (
                <tr role="row" className="hig-table__row" key={row.label}>
                  <th scope="row" role="rowheader" className="hig-table__cell hig-table__cell--leading rs-compare__label">{row.label}</th>
                  {sites.map((s) => (
                    <td role="cell" className={'hig-table__cell hig-table__cell--leading num' + (best.has(s.siteId) ? ' is-best' : '')} key={s.siteId}>
                      <span className="rs-compare__value">{row.show(s)}</span>
                      {best.has(s.siteId) && <span className="rs-compare__tag">{tagWord(row)}</span>}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        ))}
      </table>
    </div>
  );
}
