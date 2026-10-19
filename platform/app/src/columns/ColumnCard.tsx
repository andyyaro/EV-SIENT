// One card per column of the planner's file: what the engine proposes it is, why, how its cells
// read, and the planner's own choices. Nothing is applied until Confirm Column, and a direction is
// never filled in for the planner: a suggested one is shown beside the choice, not chosen.

import { useId, useRef, useState, type FormEvent } from 'react';
import { Icon } from '../components/Icon';
import type { ColumnChange, ColumnEntry, ColumnRole, Direction } from '../engine/protocol';
import { fieldLabel, plainText } from '../lib/fieldText';
import { useSession } from '../state/store';
import {
  DATE_ORDER_LABEL, DECIMAL_LABEL, DIRECTION_LABEL, ROLE_HINT, ROLE_LABEL, canRank, cellsText, directionWords, hasAmbiguous,
  hasUnit, higherMeans, missingCandidates, notShownText, rangeText, readingProblems, roleChoices, sentence,
  suggestedDirection, typeWords, valuesText,
} from './columnText';
import { MAX_LABEL, confirmColumns, engineMessage } from './dictionary';

interface Draft {
  label: string;
  role: ColumnRole;
  unit: string;
  direction: Direction | null;
  missing: string[];
  decimal: '' | '.' | ',';
  dateFormat: string;
}

function draftFor(entry: ColumnEntry, label: string): Draft {
  return {
    label, role: entry['evsient:role'], unit: entry['evsient:unit'] ?? '', direction: entry['evsient:direction'],
    missing: [], decimal: '', dateFormat: '',
  };
}

/** The changes a draft makes to an entry, as the engine takes them, always with confirm: true. */
export function changesFor(entry: ColumnEntry, draft: Draft): ColumnChange {
  const change: ColumnChange = { column: entry.name, confirm: true };
  const role = draft.role;
  if (role !== entry['evsient:role']) change.role = role;
  if (hasUnit(role)) {
    const unit = draft.unit.trim() || null;
    if (unit !== (entry['evsient:unit'] ?? null)) change.unit = unit;
  }
  if (canRank(role) && draft.direction && draft.direction !== entry['evsient:direction']) change.direction = draft.direction;
  if (draft.missing.length) change.missingValues = [...(entry.missingValues ?? []), ...draft.missing];
  if (draft.decimal) change.decimalSeparator = draft.decimal;
  if (draft.dateFormat && role === 'date') change.dateFormat = draft.dateFormat;
  return change;
}

const NUMERIC_ROLES = new Set<ColumnRole>(['count', 'measure', 'score', 'percentage', 'money', 'year', 'latitude', 'longitude']);

export function ColumnCard({ entry, label, disabled, onConfirmed }: {
  entry: ColumnEntry;
  label: string | undefined;
  disabled: boolean;
  /** The engine's whole dictionary after the change, and a sentence for the planner. */
  onConfirmed: (entries: ColumnEntry[], message: string) => void;
}) {
  const fields = useSession((s) => s.fields);
  const id = useId();
  const toggleRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Draft>(() => draftFor(entry, label ?? ''));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const name = entry.name;
  const role = entry['evsient:role'];
  const confirmed = entry['evsient:provenance'] === 'confirmed_by_user';
  const direction = entry['evsient:direction'];
  const suggestion = suggestedDirection(entry);
  const problems = readingProblems(entry);
  const evidence = entry['evsient:evidence'].filter((e) => e.signal !== 'direction');
  const modelField = entry['evsient:modelField'];
  const values = valuesText(entry);
  const range = rangeText(entry['evsient:range']);
  const title = label || name;
  const reading = entry['evsient:reading'];
  const choices = roleChoices(entry);
  const candidates = missingCandidates(entry);
  const ambiguous = hasAmbiguous(entry);

  function openEditor() {
    setDraft(draftFor(entry, label ?? ''));
    setError(null);
    setOpen(true);
  }

  function close() {
    setOpen(false);
    setError(null);
    requestAnimationFrame(() => toggleRef.current?.focus());
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setError(null);
    try {
      const result = await confirmColumns([changesFor(entry, draft)], { [name]: draft.label });
      setOpen(false);
      const chose = canRank(draft.role) && draft.direction ? ` Direction: ${directionWords(draft.direction)}.` : '';
      onConfirmed(result.entries, `Confirmed ${draft.label.trim() || name}.${chose}`);
      // The card may have left a filtered list; focus then goes to the list's first card, or the panel.
      requestAnimationFrame(() => {
        const target = toggleRef.current?.isConnected ? toggleRef.current
          : document.querySelector<HTMLElement>('.yc-list .yc-card__actions button') ?? document.querySelector<HTMLElement>('.yc-open');
        target?.focus();
      });
    } catch (e) {
      setError(engineMessage(e));
    } finally {
      setSaving(false);
    }
  }

  const set = (patch: Partial<Draft>) => setDraft((d) => ({ ...d, ...patch }));
  const draftRankable = canRank(draft.role);

  return (
    <li className="yc-card">
      <div className="yc-card__top">
        <div className="yc-card__titles">
          <h3 id={`${id}-name`} className="yc-card__name">{title}</h3>
          {label && <p className="yc-card__file">Column in your file: <span className="yc-mono">{name}</span></p>}
        </div>
        {confirmed
          ? <span className="st-status st-status--green"><Icon name="checkmark.circle.fill" size={16} strokeWidth={2} className="st-status__icon" /><span>Confirmed</span></span>
          : <span className="st-status st-status--gray"><Icon name="questionmark.circle" size={16} strokeWidth={2} className="st-status__icon" /><span>Suggested</span></span>}
      </div>

      <dl className="yc-facts">
        <div className="yc-fact">
          <dt>Kind</dt>
          <dd>{ROLE_LABEL[role]} <span className="yc-quiet">(read as {typeWords(entry.type)})</span></dd>
        </div>
        {values && <div className="yc-fact"><dt>{entry.categoriesOrdered ? 'Levels' : 'Values'}</dt><dd>{values}</dd></div>}
        {hasUnit(role) && <div className="yc-fact"><dt>Unit</dt><dd>{entry['evsient:unit'] ?? <span className="yc-quiet">None given</span>}</dd></div>}
        {range && <div className="yc-fact"><dt>Range</dt><dd>{range}</dd></div>}
        <div className="yc-fact">
          <dt>Direction</dt>
          <dd>
            {!canRank(role)
              ? <>Not ranked. <span className="yc-quiet">This kind of column has no order, so higher or lower cannot be better.</span></>
              : direction
              ? <>{sentence(directionWords(direction))}</>
              : <>
                  <span className="yc-needs"><Icon name="exclamationmark.triangle" size={14} strokeWidth={2} /> Not chosen yet</span>
                  {suggestion && <span className="yc-quiet"> Suggested: {directionWords(suggestion.direction)}.</span>}
                </>}
          </dd>
        </div>
        {modelField && (
          <div className="yc-fact"><dt>Model</dt><dd>Map Columns uses this column for {fieldLabel(fields, modelField)}.</dd></div>
        )}
        <div className="yc-fact"><dt>Cells</dt><dd>{cellsText(entry)}</dd></div>
      </dl>

      {evidence.length > 0 && (
        <div className="yc-why">
          <p className="yc-sub">Why This Was Suggested</p>
          <ul className="yc-why__list">
            {evidence.map((e, i) => <li key={i}>{sentence(plainText(fields, e.text))}</li>)}
          </ul>
        </div>
      )}

      {problems.length > 0 && (
        <div className="yc-problems">
          <p className="yc-sub"><Icon name="exclamationmark.triangle" size={16} strokeWidth={2} className="yc-problems__icon" /> Reading Problems</p>
          <ul className="yc-problems__list">
            {problems.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}

      <div className="yc-card__actions">
        <button
          ref={toggleRef}
          type="button"
          className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus"
          aria-expanded={open}
          aria-controls={`${id}-edit`}
          disabled={disabled && !open}
          onClick={() => (open ? close() : openEditor())}
        >
          <Icon name={open ? 'chevron.up' : 'pencil'} size={16} strokeWidth={2} />
          <span className="hig-button__label">
            {open ? 'Close' : confirmed ? 'Change' : 'Review and Confirm'}
            <span className="hig-visually-hidden"> {title}</span>
          </span>
        </button>
      </div>

      <div id={`${id}-edit`} className="yc-edit" hidden={!open}>
        {open && (
          <form onSubmit={submit} noValidate>
            <div className="yc-edit__grid">
              <div className="yc-field">
                <label htmlFor={`${id}-label`} className="yc-field__label">Label</label>
                <input
                  id={`${id}-label`} className="yc-input hig-focus" type="text" maxLength={MAX_LABEL} autoComplete="off"
                  value={draft.label} placeholder={name} aria-describedby={`${id}-label-hint`}
                  onChange={(e) => set({ label: e.target.value })}
                />
                <p id={`${id}-label-hint`} className="yc-field__hint">The name shown in the planner. Your file is not changed.</p>
              </div>

              <div className="yc-field">
                <label htmlFor={`${id}-role`} className="yc-field__label">Kind of Column</label>
                <span className="st-select st-select--wide">
                  <select id={`${id}-role`} className="hig-focus" value={draft.role} aria-describedby={`${id}-role-hint`}
                    onChange={(e) => set({ role: e.target.value as ColumnRole })}>
                    {choices.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                  </select>
                  <Icon name="chevron.up.chevron.down" size={13} />
                </span>
                <p id={`${id}-role-hint`} className="yc-field__hint">{ROLE_HINT[draft.role]}</p>
              </div>

              {hasUnit(draft.role) && (
                <div className="yc-field">
                  <label htmlFor={`${id}-unit`} className="yc-field__label">{draft.role === 'money' ? 'Currency' : 'Unit'}</label>
                  <input
                    id={`${id}-unit`} className="yc-input hig-focus" type="text" maxLength={32} autoComplete="off" spellCheck={false}
                    value={draft.unit} aria-describedby={`${id}-unit-hint`}
                    onChange={(e) => set({ unit: e.target.value })}
                  />
                  <p id={`${id}-unit-hint`} className="yc-field__hint">
                    {draft.role === 'money' ? 'A three-letter code, such as USD, EUR or KES.' : 'A short unit code, such as kW, m2 or kW.h. Leave empty if there is none.'}
                  </p>
                </div>
              )}

              {ambiguous && NUMERIC_ROLES.has(draft.role) && (
                <div className="yc-field">
                  <label htmlFor={`${id}-decimal`} className="yc-field__label">Decimal Mark</label>
                  <span className="st-select st-select--wide">
                    <select id={`${id}-decimal`} className="hig-focus" value={draft.decimal} onChange={(e) => set({ decimal: e.target.value as Draft['decimal'] })}>
                      <option value="">Not Chosen</option>
                      {(['.', ','] as const).map((m) => <option key={m} value={m}>{DECIMAL_LABEL[m]}</option>)}
                    </select>
                    <Icon name="chevron.up.chevron.down" size={13} />
                  </span>
                  <p className="yc-field__hint">Some cells could be read two ways. Choose the mark your file uses for decimals.</p>
                </div>
              )}

              {ambiguous && draft.role === 'date' && (
                <div className="yc-field">
                  <label htmlFor={`${id}-date`} className="yc-field__label">Date Order</label>
                  <span className="st-select st-select--wide">
                    <select id={`${id}-date`} className="hig-focus" value={draft.dateFormat} onChange={(e) => set({ dateFormat: e.target.value })}>
                      <option value="">Not Chosen</option>
                      {Object.entries(DATE_ORDER_LABEL).map(([f, text]) => <option key={f} value={f}>{text}</option>)}
                    </select>
                    <Icon name="chevron.up.chevron.down" size={13} />
                  </span>
                  <p className="yc-field__hint">Some dates could be read with the day and month either way round.</p>
                </div>
              )}
            </div>

            {draftRankable ? (
              <fieldset className="yc-direction" aria-describedby={`${id}-dir-hint`}>
                <legend className="yc-field__label">Direction</legend>
                <p id={`${id}-dir-hint`} className="yc-field__hint">
                  {higherMeans(entry, draft.role)} Choose one before this column can be used to rank sites.
                  {suggestion && ` ${suggestion.because}`}
                </p>
                <div className="yc-direction__options">
                  {(['higher_better', 'lower_better', 'neither'] as Direction[]).map((d) => (
                    <label key={d} className="yc-radio">
                      <input type="radio" name={`${id}-direction`} value={d} checked={draft.direction === d} onChange={() => set({ direction: d })} />
                      <span>{DIRECTION_LABEL[d]}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            ) : (
              <p className="yc-field__hint yc-gap">Direction: not ranked. This kind of column has no order, so higher or lower cannot be better.</p>
            )}

            {candidates.length > 0 && (
              <fieldset className="yc-missing">
                <legend className="yc-field__label">Treat as Missing</legend>
                <p className="yc-field__hint">Cells marked here are read as missing, and earn no credit in anything ranked by this column.</p>
                <div className="yc-direction__options">
                  {candidates.map((c) => (
                    <label key={c.pattern} className="yc-radio">
                      <input type="checkbox" checked={draft.missing.includes(c.pattern)}
                        onChange={(e) => set({ missing: e.target.checked ? [...draft.missing, c.pattern] : draft.missing.filter((m) => m !== c.pattern) })} />
                      <span><span className="yc-mono">{c.pattern}</span> <span className="yc-quiet">({c.count.toLocaleString('en-US')} {c.count === 1 ? 'cell' : 'cells'})</span></span>
                    </label>
                  ))}
                </div>
              </fieldset>
            )}

            {reading && reading.patterns.length > 0 && (
              <div className="yc-reading">
                <p className="yc-sub" id={`${id}-reading`}>How the Cells Were Read</p>
                <div className="yc-reading__wrap" tabIndex={0} role="region" aria-labelledby={`${id}-reading`}>
                  <table className="yc-reading__table">
                    <thead><tr><th scope="col">In Your File</th><th scope="col">Read As</th><th scope="col" className="yc-num">Cells</th></tr></thead>
                    <tbody>
                      {reading.patterns.slice(0, 12).map((p, i) => (
                        <tr key={i}>
                          <td className="yc-mono">{p.pattern === '' ? <span className="yc-quiet">(empty)</span> : p.pattern}</td>
                          <td>{p.readAs}</td>
                          <td className="yc-num">{p.count.toLocaleString('en-US')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {(reading.patterns.length > 12 || notShownText(reading.patternsNotShown)) && (
                  <p className="yc-field__hint">
                    {reading.patterns.length > 12 ? `${reading.patterns.length - 12} more patterns are not shown here. ` : ''}
                    {notShownText(reading.patternsNotShown) ?? ''}
                  </p>
                )}
              </div>
            )}

            {error && <p className="yc-error" role="alert"><Icon name="exclamationmark.triangle" size={16} strokeWidth={2} /> {error}</p>}

            <div className="yc-edit__buttons">
              <button type="submit" className="hig-button hig-button--ios hig-button--medium hig-button--bordered-prominent hig-focus" disabled={saving || disabled}>
                <Icon name="checkmark" size={16} strokeWidth={2.2} />
                <span className="hig-button__label">{saving ? 'Confirming' : 'Confirm Column'}</span>
              </button>
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={close}>
                <span className="hig-button__label">Cancel</span>
              </button>
              {draftRankable && !draft.direction && (
                <p className="yc-field__hint yc-edit__why">No direction chosen. You can confirm without one, but this column cannot rank sites until you choose.</p>
              )}
            </div>
          </form>
        )}
      </div>
    </li>
  );
}
