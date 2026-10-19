// The ranked sites as a table: the complete accessible view of everything the map and charts show.
// Each site's name is a button that selects it (arrow keys move between sites); the last column
// adds the site to Compare.

import { useRef, type KeyboardEvent } from 'react';
import type { SiteResult } from '../engine/protocol';
import { fmt, isNumber, tierKey, tierShort } from './format';

interface Props {
  sites: SiteResult[];
  selectedId: string | null;
  compare: string[];
  onSelect(siteId: string, from: 'table'): void;
  onToggleCompare(siteId: string): void;
}

export function RankedTable({ sites, selectedId, compare, onSelect, onToggleCompare }: Props) {
  const body = useRef<HTMLTableSectionElement>(null);
  const full = compare.length >= 3;
  const tabStop = sites.some((s) => s.siteId === selectedId) ? selectedId : sites[0]?.siteId;

  function onKey(e: KeyboardEvent<HTMLButtonElement>, i: number) {
    const to = e.key === 'ArrowDown' ? i + 1 : e.key === 'ArrowUp' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? sites.length - 1 : -1;
    if (to < 0 || to >= sites.length || to === i) return;
    e.preventDefault();
    onSelect(sites[to].siteId, 'table');
    body.current?.querySelectorAll<HTMLButtonElement>('button.rs-site')[to]?.focus();
  }

  return (
    <div className="hig-table hig-table--ios rs-table rs-ranked" role="region" aria-labelledby="rs-ranked-cap" tabIndex={0}>
      {/* Explicit table roles: on narrow screens each row is laid out as a stacked card (results.css),
          and the roles keep the table's meaning for screen readers whatever the CSS display. */}
      <table className="hig-table__grid" role="table">
        <caption id="rs-ranked-cap" className="hig-visually-hidden">
          Ranked sites, {sites.length} in all. Choose a site's name to show its details; the up and down arrow keys move between sites.
        </caption>
        <thead role="rowgroup">
          <tr role="row">
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing rs-col-rank"><span className="hig-table__heading-label">Rank</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading rs-col-site"><span className="hig-table__heading-label">Site</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Score</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Tier</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Data Confidence</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Ports Now</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Pathway</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--center"><span className="hig-table__heading-label">Compare</span></th>
          </tr>
        </thead>
        <tbody ref={body} role="rowgroup">
          {sites.map((s, i) => {
            const selected = s.siteId === selectedId;
            const inCompare = compare.includes(s.siteId);
            const tk = tierKey(s.tier);
            const mapped = isNumber(s.lat) && isNumber(s.lon);
            return (
              <tr
                key={s.siteId}
                role="row"
                className={'hig-table__row rs-row' + (selected ? ' is-selected' : '')}
                onClick={(e) => { if (!(e.target as HTMLElement).closest('input, label, button')) onSelect(s.siteId, 'table'); }}
              >
                <td role="cell" className="hig-table__cell hig-table__cell--trailing rs-rank num">{s.rank}</td>
                <th scope="row" role="rowheader" className="hig-table__cell hig-table__cell--leading rs-col-site">
                  <button
                    type="button"
                    className="rs-site hig-focus"
                    aria-current={selected ? 'true' : undefined}
                    tabIndex={s.siteId === tabStop ? 0 : -1}
                    onClick={() => onSelect(s.siteId, 'table')}
                    onKeyDown={(e) => onKey(e, i)}
                  >
                    <span className="rs-site__name">{s.name}</span>
                    <span className="rs-site__id num">{s.siteId}{mapped ? '' : ' · not on map'}</span>
                  </button>
                </th>
                <td role="cell" className="hig-table__cell hig-table__cell--trailing rs-score num"><span className="rs-cell-label" aria-hidden="true">Score </span>{fmt.score(s.score)}</td>
                <td role="cell" className="hig-table__cell hig-table__cell--leading rs-col-tier">
                  <span className={`tier tier--${tk}`} title={s.tier}><span className="tier__mark" aria-hidden="true" />{tierShort(s.tier)}</span>
                </td>
                <td role="cell" className="hig-table__cell hig-table__cell--leading rs-col-conf">
                  <span className="rs-cell-label" aria-hidden="true">Confidence </span>{s.confidence.level ?? 'Not recorded'}
                </td>
                <td role="cell" className="hig-table__cell hig-table__cell--trailing num rs-col-ports"><span className="rs-cell-label" aria-hidden="true">Ports Now </span>{fmt.int(s.portsNow)}</td>
                <td role="cell" className="hig-table__cell hig-table__cell--trailing num rs-col-ports"><span className="rs-cell-label" aria-hidden="true">Pathway </span>{fmt.int(s.pathwayPorts)}</td>
                <td role="cell" className="hig-table__cell hig-table__cell--center rs-col-compare">
                  <label className="rs-check">
                    <input
                      type="checkbox"
                      checked={inCompare}
                      disabled={!inCompare && full}
                      onChange={() => onToggleCompare(s.siteId)}
                    />
                    <span className="hig-visually-hidden">Compare {s.name}</span>
                  </label>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
