// The ranked sites as a table: the complete accessible view of everything the map and charts show.
// Each site's name is a button that selects it (arrow keys move between sites); the last column
// adds the site to Compare. Columns from the planner's own file (Your Columns) follow, tinted and
// labelled Not in the Score; their headings sort the table, and Rank puts it back in rank order.

import { useRef, type KeyboardEvent } from 'react';
import { Icon } from '../components/Icon';
import type { SiteResult } from '../engine/protocol';
import { breakable } from './YourColumns';
import { NOT_IN_SCORE, carriedText, columnIndex, showCarried, type CarriedColumns } from './carried';
import { fmt, isNumber, tierKey, tierShort } from './format';

interface Props {
  sites: SiteResult[];
  selectedId: string | null;
  compare: string[];
  onSelect(siteId: string, from: 'table'): void;
  onToggleCompare(siteId: string): void;
  carried?: CarriedColumns | null;
  /** Your Columns shown as table columns, in the order the planner added them. */
  shown?: string[];
  /** null is rank order. */
  sort?: { column: string; dir: 1 | -1 } | null;
  onSort?(column: string | null): void;
}

export function RankedTable({ sites, selectedId, compare, onSelect, onToggleCompare, carried = null, shown = [], sort = null, onSort }: Props) {
  const extra = shown.map((name) => ({ name, k: columnIndex(carried, name) })).filter((c) => c.k >= 0);
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
          Ranked sites, {sites.length} {sites.length === 1 ? 'site' : 'sites'} shown{sort ? `, sorted by ${sort.column}, ${sort.dir === 1 ? 'lowest' : 'highest'} first` : ', in rank order'}. Choose a site's name to show its details; the up and down arrow keys move between sites.
          {extra.length > 0 && ' The last columns come from your file. They are not in the score and do not change the rank.'}
        </caption>
        <thead role="rowgroup">
          <tr role="row">
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing rs-col-rank" aria-sort={extra.length ? (sort ? 'none' : 'ascending') : undefined}>
              {extra.length && onSort ? (
                <button type="button" className="rs-sort hig-focus" onClick={() => onSort(null)}>
                  <span className="hig-table__heading-label">Rank</span>
                  {!sort && <Icon name="chevron.up" size={12} strokeWidth={2.4} />}
                </button>
              ) : <span className="hig-table__heading-label">Rank</span>}
            </th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading rs-col-site"><span className="hig-table__heading-label">Site</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Score</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Tier</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Data Confidence</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Ports Now</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Pathway</span></th>
            <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--center"><span className="hig-table__heading-label">Compare</span></th>
            {extra.map(({ name, k }) => {
              const on = sort?.column === name;
              const numeric = carried!.columns[k].numeric;
              return (
                <th
                  scope="col" role="columnheader" key={name}
                  className={'hig-table__heading rs-col-yours ' + (numeric ? 'hig-table__cell--trailing' : 'hig-table__cell--leading')}
                  aria-sort={on ? (sort!.dir === 1 ? 'ascending' : 'descending') : 'none'}
                >
                  <button
                    type="button" className="rs-sort hig-focus" onClick={() => onSort?.(name)}
                    aria-label={`${name}, ${NOT_IN_SCORE.toLowerCase()}. Sort by this column${on ? (sort!.dir === 1 ? ', now ascending' : ', now descending') : ''}.`}
                  >
                    <span className="rs-yours-head">
                      <span className="hig-table__heading-label rs-yours-head__name">{breakable(name)}</span>
                      <span className="rs-yours-head__note">{NOT_IN_SCORE}</span>
                    </span>
                    {on && <Icon name={sort!.dir === 1 ? 'chevron.up' : 'chevron.down'} size={12} strokeWidth={2.4} />}
                  </button>
                </th>
              );
            })}
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
                {extra.map(({ name, k }, j) => {
                  const col = carried!.columns[k];
                  const text = carriedText(carried!, s.siteId, k);
                  return (
                    <td role="cell" key={name} className={'hig-table__cell rs-col-yours ' + (col.numeric ? 'hig-table__cell--trailing num' : 'hig-table__cell--leading rs-yours-text') + (j === 0 ? ' rs-yours-first' : '') + (text ? '' : ' is-blank')}>
                      <span className="rs-cell-label" aria-hidden="true">{name}: </span>{showCarried(col, text)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
