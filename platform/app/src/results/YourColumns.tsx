// Your Columns in Results: the control that adds the planner's own columns to the ranked table and
// filters by one of them, and the site's card of its values. Every place says Not in the Score:
// these columns are shown, sorted and filtered, never used to rank.

import { useId, useState } from 'react';
import { Icon } from '../components/Icon';
import { useSession } from '../state/store';
import { NOT_IN_SCORE, carriedText, columnIndex, showCarried, type CarriedColumns, type CarriedFilter } from './carried';
import { plural } from './format';

/** A column name that may wrap after its underscores, never inside a word: heat_risk_<wbr>0_<wbr>100. */
export function breakable(name: string) {
  return name.split(/(?<=_)/).map((part, i) => <span key={i}>{i > 0 && <wbr />}{part}</span>);
}

export function filterText(f: CarriedFilter | null): string {
  if (!f) return '';
  if (f.kind === 'text') return f.contains.trim() ? `${f.column} contains "${f.contains.trim()}"` : '';
  const min = f.min.trim(), max = f.max.trim();
  if (min && max) return `${f.column} from ${min} to ${max}`;
  if (min) return `${f.column} of ${min} or more`;
  if (max) return `${f.column} of ${max} or less`;
  return '';
}

export function YourColumnsControl({ carried, total, showing }: { carried: CarriedColumns; total: number; showing: number }) {
  const view = useSession((s) => s.yourColumns);
  const setView = useSession((s) => s.setYourColumns);
  const [open, setOpen] = useState(false);
  const id = useId();
  const filter = view.filter;
  const filterCol = filter ? carried.columns[columnIndex(carried, filter.column)] : undefined;
  const active = filterText(filter);

  function toggle(name: string) {
    const shown = view.shown.includes(name) ? view.shown.filter((c) => c !== name) : [...view.shown, name];
    setView({ shown, sort: view.sort && !shown.includes(view.sort.column) ? null : view.sort });
  }

  function chooseFilter(name: string) {
    const col = carried.columns[columnIndex(carried, name)];
    if (!col) { setView({ filter: null }); return; }
    setView({ filter: col.numeric ? { column: name, kind: 'range', min: '', max: '' } : { column: name, kind: 'text', contains: '' } });
  }

  return (
    <div className="rs-yours">
      <div className="rs-yours__bar">
        <button
          type="button"
          className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable rs-yours__toggle"
          aria-expanded={open}
          aria-controls={`${id}-panel`}
          onClick={() => setOpen((o) => !o)}
        >
          <Icon name="line.3.horizontal.decrease" size={16} strokeWidth={2} />
          <span className="hig-button__label">Your Columns{view.shown.length ? ` (${view.shown.length} shown)` : ''}</span>
          <Icon name={open ? 'chevron.up' : 'chevron.down'} size={13} strokeWidth={2.4} />
        </button>
        <span className="rs-yours__count num" role="status">
          {active ? `Showing ${showing} of ${plural(total, 'site')}: ${active}.` : ''}
        </span>
        {active && (
          <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={() => setView({ filter: null })}>
            <span className="hig-button__label">Clear Filter</span>
          </button>
        )}
      </div>

      <div className="rs-yours__panel" id={`${id}-panel`} hidden={!open}>
        <p className="rs-yours__note">
          <Icon name="info.circle" size={18} className="rs-yours__note-icon" />
          <span>
            {plural(carried.columns.length, 'column')} from your file {carried.columns.length === 1 ? 'is' : 'are'} not read by the model. {carried.columns.length === 1 ? 'It is' : 'They are'} kept
            with each site and shown as you wrote {carried.columns.length === 1 ? 'it' : 'them'}. <strong>{NOT_IN_SCORE}:</strong> sorting or filtering by {carried.columns.length === 1 ? 'it' : 'them'} never changes a site's score or rank.
          </span>
        </p>

        <fieldset className="rs-yours__set">
          <legend className="rs-yours__legend">Show in the Table</legend>
          <ul className="rs-yours__options" role="list">
            {carried.columns.map((c) => (
              <li key={c.name}>
                <label className="rs-yours__option">
                  <input type="checkbox" checked={view.shown.includes(c.name)} onChange={() => toggle(c.name)} />
                  <span className="rs-yours__option-name">{breakable(c.name)}</span>
                  <span className="rs-yours__option-kind">{c.numeric ? 'Numbers' : 'Text'}</span>
                </label>
              </li>
            ))}
          </ul>
          {view.shown.length > 0 && (
            <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus rs-yours__clear" onClick={() => setView({ shown: [], sort: null })}>
              <span className="hig-button__label">Hide All</span>
            </button>
          )}
        </fieldset>

        <fieldset className="rs-yours__set">
          <legend className="rs-yours__legend">Filter the Table</legend>
          <div className="rs-yours__filter">
            <label className="rs-yours__field">
              <span className="rs-yours__label">Column</span>
              <span className="st-select">
                <select className="hig-focus" value={filter?.column ?? ''} onChange={(e) => chooseFilter(e.target.value)}>
                  <option value="">No Filter</option>
                  {carried.columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
                <Icon name="chevron.up.chevron.down" size={13} />
              </span>
            </label>
            {filter?.kind === 'text' && (
              <label className="rs-yours__field">
                <span className="rs-yours__label">Contains</span>
                <input className="rs-yours__input hig-focus" type="search" value={filter.contains} autoComplete="off"
                  onChange={(e) => setView({ filter: { ...filter, contains: e.target.value } })} />
              </label>
            )}
            {filter?.kind === 'range' && filterCol && (
              <>
                <label className="rs-yours__field rs-yours__field--num">
                  <span className="rs-yours__label">From</span>
                  <input className="rs-yours__input hig-focus num" type="text" inputMode="decimal" value={filter.min} autoComplete="off"
                    onChange={(e) => setView({ filter: { ...filter, min: e.target.value } })} />
                </label>
                <label className="rs-yours__field rs-yours__field--num">
                  <span className="rs-yours__label">To</span>
                  <input className="rs-yours__input hig-focus num" type="text" inputMode="decimal" value={filter.max} autoComplete="off"
                    onChange={(e) => setView({ filter: { ...filter, max: e.target.value } })} />
                </label>
              </>
            )}
          </div>
          <p className="footnote">The filter narrows the table only. The map, Compare and the downloads keep every site.</p>
        </fieldset>
      </div>
    </div>
  );
}

/** One site's values in Your Columns, for its details. */
export function YourColumnsCard({ carried, siteId }: { carried: CarriedColumns; siteId: string }) {
  return (
    <section className="sd-card sd-yours" aria-labelledby="sd-yours">
      <h3 className="sd-card__title" id="sd-yours">Your Columns <span className="sd-yours__tag">{NOT_IN_SCORE}</span></h3>
      <dl className="sd-yours__list">
        {carried.columns.map((c, k) => {
          const text = carriedText(carried, siteId, k);
          return (
            <div className="sd-yours__row" key={c.name}>
              <dt>{breakable(c.name)}</dt>
              <dd className={(c.numeric ? 'num' : '') + (text ? '' : ' is-blank')}>{showCarried(c, text)}</dd>
            </div>
          );
        })}
      </dl>
      <p className="footnote">From your file, as you wrote it. The model does not read these columns, so they play no part in this site's score, rank or port plan.</p>
    </section>
  );
}
