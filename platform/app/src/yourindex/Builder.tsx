// The Your Index builder: the columns in the index with their weights and value functions, the
// columns that cannot be scored and why, the rules that leave sites out, and how missing values
// count. Every change is saved in the session at once and checked by the engine (live validation);
// what the engine refuses is shown in its own words next to the field it is about.

import { useId, useState } from 'react';
import { Icon } from '../components/Icon';
import type { ColumnEntry, Direction, IndexRefusal, IndexSpec } from '../engine/protocol';
import { breakable } from '../results/YourColumns';
import { NumberField } from './NumberField';
import { SelectField } from './SelectField';
import {
  DIRECTION_WORDS, KIND_WORDS, MIN_COVERAGE, OP_WORDS, ROLE_WORDS, defaultValue, directionsFor, fmtNumber, fmtShare,
  fmtShareFine, isLabels, isNumeric, levels, missingLeftOut, newCriterion, observedRange, opsFor, proposedDirection, role,
  ruleComplete, ruleFrom, ruleLogic, ruleReason, scorable, shares, type Criterion, type Kind, type Rule, type RuleOp,
} from './model';

interface Props {
  spec: IndexSpec;
  entries: ColumnEntry[];
  refusals: IndexRefusal[];
  onChange(spec: IndexSpec): void;
  onConfirmDirection(column: string, direction: Direction): Promise<void>;
}

/** Where each refusal is shown: beside its criterion, its rule, the name, or at the top. */
export function placeRefusals(refusals: IndexRefusal[], spec: IndexSpec) {
  const inIndex = new Set(spec.criteria.map((c) => c.column));
  const byColumn = new Map<string, IndexRefusal[]>();
  const name: IndexRefusal[] = [], criteria: IndexRefusal[] = [], screens: IndexRefusal[] = [], general: IndexRefusal[] = [];
  for (const r of refusals) {
    if (r.code === 'name') name.push(r);
    else if (r.code === 'few_criteria') criteria.push(r);
    else if (r.code === 'screen' || (r.code === 'unknown_column' && r.column && !inIndex.has(r.column))) screens.push(r);
    else if (r.column && inIndex.has(r.column)) byColumn.set(r.column, [...(byColumn.get(r.column) ?? []), r]);
    else general.push(r);
  }
  return { byColumn, name, criteria, screens, general };
}

export function Refusals({ items, id }: { items: IndexRefusal[]; id?: string }) {
  if (!items.length) return <div id={id} hidden />;
  return (
    <ul className="yi-refusals" id={id} role="list">
      {items.map((r, i) => (
        <li className="yi-refusal" key={`${r.code}-${i}`}>
          <Icon name="exclamationmark.triangle" size={16} strokeWidth={2} className="yi-refusal__icon" />
          <span>{r.message}</span>
        </li>
      ))}
    </ul>
  );
}

export function Builder({ spec, entries, refusals, onChange, onConfirmDirection }: Props) {
  const placed = placeRefusals(refusals, spec);
  const byName = new Map(entries.map((e) => [e.name, e]));
  const share = shares(spec);
  const inIndex = new Set(spec.criteria.map((c) => c.column));
  const canAdd = entries.filter((e) => !inIndex.has(e.name) && scorable(e).ok);
  const cannot = entries.filter((e) => !scorable(e).ok);

  const setCriterion = (i: number, c: Criterion) => onChange({ ...spec, criteria: spec.criteria.map((x, k) => (k === i ? c : x)) });
  const remove = (i: number) => onChange({ ...spec, criteria: spec.criteria.filter((_, k) => k !== i) });
  const add = (e: ColumnEntry) => {
    const c = newCriterion(e);
    if (c) onChange({ ...spec, criteria: [...spec.criteria, c] });
  };

  return (
    <div className="yi-builder">
      <section className="section yi-section" aria-labelledby="yi-crit-title">
        <div className="section__head">
          <h2 className="section__title" id="yi-crit-title">Columns in Your Index</h2>
          <span className="section__aside num">{spec.criteria.length} chosen</span>
        </div>
        <p className="section__intro">
          Each column earns a site some credit between none and full, by a rule you set. Its weight says how much that credit counts.
          The weights are shared out so they add up to 100%, and the index is out of 100 points.
        </p>
        <Refusals items={placed.criteria} />
        {spec.criteria.length > 0 && (
          <ol className="yi-crit-list" role="list">
            {spec.criteria.map((c, i) => (
              <CriterionCard
                key={c.column}
                c={c}
                entry={byName.get(c.column)}
                share={share[i]}
                refusals={placed.byColumn.get(c.column) ?? []}
                onChange={(next) => setCriterion(i, next)}
                onRemove={() => remove(i)}
              />
            ))}
          </ol>
        )}

        <div className="yi-add">
          <h3 className="yi-h3">Add a Column</h3>
          {canAdd.length ? (
            <ul className="yi-add-list" role="list">
              {canAdd.map((e) => (
                <li className="yi-add-row" key={e.name}>
                  <span className="yi-add-row__text">
                    <span className="yi-add-row__name">{breakable(e.name)}</span>
                    <span className="yi-add-row__meta">{ROLE_WORDS[role(e)]} · {DIRECTION_WORDS[scorableDirection(e)]}</span>
                  </span>
                  <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={() => add(e)} aria-label={`Add ${e.name} to the index`}>
                    <Icon name="plus" size={15} strokeWidth={2.2} />
                    <span className="hig-button__label">Add</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="yi-muted">{spec.criteria.length ? 'Every column that can be scored is in the index.' : 'No column can be scored yet. Confirm a direction below.'}</p>
          )}
        </div>

        {cannot.length > 0 && <CannotScore entries={cannot} onConfirmDirection={onConfirmDirection} />}
      </section>

      <Screens spec={spec} entries={entries} refusals={placed.screens} onChange={onChange} />

      <section className="section yi-section" aria-labelledby="yi-missing-title">
        <h2 className="section__title" id="yi-missing-title">Missing Values</h2>
        <div className="yi-card yi-policy">
          <p><strong>No credit.</strong> A site with no value for a column earns nothing for that column. A blank is never filled in or guessed.</p>
          <p>
            Each site also gets its best case, the score it would have if every missing value earned full credit, so you can see how much the gaps could matter.
            A site with values for under {fmtShare(spec.minCoverage ?? MIN_COVERAGE)} of the columns is listed but not ranked.
          </p>
        </div>
      </section>
    </div>
  );
}

function scorableDirection(e: ColumnEntry): Direction {
  const s = scorable(e);
  return s.ok ? s.direction : 'neither';
}

function CriterionCard({ c, entry, share, refusals, onChange, onRemove }: {
  c: Criterion; entry: ColumnEntry | undefined; share: number; refusals: IndexRefusal[];
  onChange(c: Criterion): void; onRemove(): void;
}) {
  const id = useId();
  const head = `${id}-head`;
  const errs = `${id}-errs`;
  const s = entry ? scorable(entry) : null;
  const kinds: Kind[] = s && s.ok ? s.kinds : [c.value.kind];
  const v = c.value as Record<string, unknown>;
  const numberOf = (k: string) => (typeof v[k] === 'number' ? (v[k] as number) : undefined);
  const setValue = (patch: Record<string, unknown>) => onChange({ ...c, value: { ...c.value, ...patch } as Criterion['value'] });
  const range = entry ? observedRange(entry) : null;
  const reading = entry?.['evsient:reading'];
  const bad = refusals.length > 0;

  return (
    <li className={'yi-card yi-crit' + (bad ? ' is-refused' : '')} aria-labelledby={head}>
      <div className="yi-crit__top">
        <div className="yi-crit__title">
          <h3 className="yi-crit__name" id={head}>{breakable(c.column)}</h3>
          <p className="yi-crit__meta">
            {entry ? ROLE_WORDS[role(entry)] : 'Not in this file'} · {DIRECTION_WORDS[c.direction]}
          </p>
        </div>
        <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={onRemove} aria-label={`Remove ${c.column} from the index`}>
          <Icon name="minus" size={15} strokeWidth={2.2} />
          <span className="hig-button__label">Remove</span>
        </button>
      </div>

      <Refusals items={refusals} id={errs} />

      <div className="yi-weight">
        <label className="yi-weight__slider">
          <span className="yi-field__label">Weight</span>
          <input
            type="range" className="yi-range hig-focus" min={1} max={100} step={1} aria-label={`Weight slider for ${c.column}`}
            value={Math.min(100, Math.max(1, Math.round(c.weight) || 1))}
            aria-valuetext={`${fmtNumber(c.weight)}, which is ${fmtShareFine(share)} of the index`}
            onChange={(e) => onChange({ ...c, weight: Number(e.target.value) })}
          />
        </label>
        <NumberField
          className="yi-weight__num" label={`Weight for ${c.column}`} hiddenLabel value={c.weight} min={0} step="any"
          describedBy={bad ? errs : undefined} invalid={refusals.some((r) => r.code === 'weight')}
          onChange={(w) => onChange({ ...c, weight: w ?? 0 })}
        />
        <output className="yi-weight__share num" aria-live="polite">{fmtShareFine(share)} of the index</output>
      </div>

      <div className="yi-value">
        {kinds.length > 1 && (
          <SelectField label="How Values Earn Credit" value={c.value.kind} onChange={(k) => entry && onChange({ ...c, value: defaultValue(entry, k as Kind, c.direction) })}>
            {kinds.map((k) => <option key={k} value={k}>{KIND_WORDS[k]}</option>)}
          </SelectField>
        )}

        {(c.value.kind === 'linear' || c.value.kind === 'threshold') && (
          <>
            <div className="yi-bounds">
              <NumberField
                label="No Credit At" value={numberOf('worst')} describedBy={bad ? errs : undefined} invalid={bad}
                placeholder={c.value.kind === 'linear' && range ? fmtNumber(c.direction === 'lower_better' ? range.max : range.min) : undefined}
                onChange={(x) => setValue({ worst: x, pinnedFrom: undefined })}
              />
              <NumberField
                label="Full Credit At" value={numberOf('best')} describedBy={bad ? errs : undefined} invalid={bad}
                placeholder={c.value.kind === 'linear' && range ? fmtNumber(c.direction === 'lower_better' ? range.min : range.max) : undefined}
                onChange={(x) => setValue({ best: x, pinnedFrom: undefined })}
              />
            </div>
            <p className="yi-hint">
              {c.value.kind === 'linear'
                ? <>Credit rises in a straight line from none to full between the two values. {range
                    ? <>Leave both empty to use the range in your file, {fmtNumber(range.min)} to {fmtNumber(range.max)}; it is fixed when the index runs, so a rule that leaves sites out never moves it.</>
                    : 'Leave both empty to use the range in your file; it is fixed when the index runs.'}</>
                : <>No credit {c.direction === 'lower_better' ? 'above' : 'below'} the first value, full credit at or {c.direction === 'lower_better' ? 'below' : 'above'} the second, a straight line between.</>}
              {entry && role(entry) === 'flag' && ' Yes counts as 1 and No as 0.'}
            </p>
          </>
        )}

        {c.value.kind === 'target' && (
          <>
            <div className="yi-bounds yi-bounds--three">
              <NumberField label="No Credit Below" value={numberOf('low')} describedBy={bad ? errs : undefined} invalid={bad} onChange={(x) => setValue({ low: x })} />
              <NumberField label="Full Credit At" value={numberOf('target')} describedBy={bad ? errs : undefined} invalid={bad} onChange={(x) => setValue({ target: x })} />
              <NumberField label="No Credit Above" value={numberOf('high')} describedBy={bad ? errs : undefined} invalid={bad} onChange={(x) => setValue({ high: x })} />
            </div>
            <p className="yi-hint">Full credit at the target, falling in a straight line to none at the low and high values.{range ? ` Your file runs from ${fmtNumber(range.min)} to ${fmtNumber(range.max)}.` : ''}</p>
          </>
        )}

        {c.value.kind === 'ordinal' && (
          <fieldset className="yi-map">
            <legend className="yi-field__label">Credit for Each {entry && role(entry) === 'ordinal' ? 'Level, Lowest First' : 'Category'} (0 to 1)</legend>
            <div className="yi-map__grid">
              {(entry ? levels(entry) : Object.keys((v.map as Record<string, number>) ?? {})).map((name) => (
                <NumberField
                  key={name} label={name} min={0} max={1} step={0.05}
                  value={typeof (v.map as Record<string, number> | undefined)?.[name] === 'number' ? (v.map as Record<string, number>)[name] : undefined}
                  describedBy={bad ? errs : undefined} invalid={bad}
                  onChange={(x) => {
                    const map = { ...((v.map as Record<string, number>) ?? {}) };
                    if (x === undefined) delete map[name]; else map[name] = x;
                    setValue({ map });
                  }}
                />
              ))}
            </div>
            <p className="yi-hint">0 is no credit and 1 is full credit.{c.direction !== 'neither' ? ` Credit should not run against "${DIRECTION_WORDS[c.direction].toLowerCase()}".` : ''}</p>
          </fieldset>
        )}
      </div>

      {reading && (
        <p className="yi-crit__missing">
          {reading.missing + reading.unreadable > 0
            ? `${fmtNumber(reading.missing + reading.unreadable)} of ${fmtNumber(reading.cells)} sites have no value here and earn no credit for it.`
            : `Every site has a value here.`}
        </p>
      )}
    </li>
  );
}

function CannotScore({ entries, onConfirmDirection }: { entries: ColumnEntry[]; onConfirmDirection: Props['onConfirmDirection'] }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const waiting = entries.filter((e) => { const s = scorable(e); return !s.ok && s.needsDirection; }).length;
  return (
    <div className={'hig-disclosure hig-disclosure--group yi-cannot' + (open ? ' hig-disclosure--open' : '')}>
      <button type="button" className="hig-disclosure__trigger hig-disclosure__row hig-focus" aria-expanded={open} aria-controls={`${id}-list`} onClick={() => setOpen((o) => !o)}>
        <span className="hig-disclosure__label">
          Columns That Cannot Be Scored Yet <span className="yi-muted">({entries.length}{waiting ? `, ${waiting} waiting for a direction` : ''})</span>
        </span>
        <span className="hig-disclosure__chevron" aria-hidden="true"><Icon name="chevron.right" size={17} strokeWidth={2.4} /></span>
      </button>
      <div className="hig-disclosure__content" id={`${id}-list`} hidden={!open}>
        <p className="yi-hint">
          Only a column whose direction you have confirmed can be scored, so a wrong guess never ranks a site. You can confirm a direction here or in your column settings.
        </p>
        <ul className="yi-cannot__list" role="list">
          {entries.map((e) => <CannotRow key={e.name} e={e} onConfirmDirection={onConfirmDirection} />)}
        </ul>
      </div>
    </div>
  );
}

function CannotRow({ e, onConfirmDirection }: { e: ColumnEntry; onConfirmDirection: Props['onConfirmDirection'] }) {
  const s = scorable(e);
  const options = directionsFor(e);
  const proposed = proposedDirection(e);
  const [choice, setChoice] = useState<Direction | ''>(proposed && options.includes(proposed) ? proposed : options.length === 1 ? options[0] : '');
  const [saving, setSaving] = useState(false);
  const id = useId();
  if (s.ok) return null;
  return (
    <li className="yi-cannot__row">
      <div className="yi-cannot__text">
        <span className="yi-add-row__name">{breakable(e.name)}</span>
        <span className="yi-add-row__meta">{ROLE_WORDS[role(e)]}</span>
        <span className="yi-cannot__why" id={`${id}-why`}>{s.why}</span>
      </div>
      {s.needsDirection && options.length > 0 && (
        <div className="yi-cannot__fix">
          <SelectField label={`Which is better for ${e.name}`} hiddenLabel value={choice} describedBy={`${id}-why`} onChange={(x) => setChoice(x as Direction | '')}>
            <option value="">Choose a Direction</option>
            {options.map((d) => <option key={d} value={d}>{DIRECTION_WORDS[d]}{d === proposed ? ' (suggested)' : ''}</option>)}
          </SelectField>
          <button
            type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable"
            disabled={!choice || saving} aria-label={`Confirm direction for ${e.name}`}
            onClick={async () => { if (!choice) return; setSaving(true); try { await onConfirmDirection(e.name, choice); } finally { setSaving(false); } }}
          >
            <span className="hig-button__label">{saving ? 'Saving' : 'Confirm'}</span>
          </button>
        </div>
      )}
    </li>
  );
}

// ---------- rules that leave sites out ----------

interface RuleRow { key: number; rule: Rule | null; custom?: { logic: unknown; reason: string } }

let nextKey = 1;

function Screens({ spec, entries, refusals, onChange }: { spec: IndexSpec; entries: ColumnEntry[]; refusals: IndexRefusal[]; onChange(spec: IndexSpec): void }) {
  const byName = new Map(entries.map((e) => [e.name, e]));
  const usable = entries.filter((e) => isNumeric(e) || isLabels(e));
  // The rows live here while the planner writes them; only finished rules reach the settings.
  const [rows, setRows] = useState<RuleRow[]>(() => spec.screens.map((s) => {
    const rule = ruleFrom(s.logic);
    return rule ? { key: nextKey++, rule } : { key: nextKey++, rule: null, custom: { logic: s.logic, reason: s.reason } };
  }));

  function commit(next: RuleRow[]) {
    setRows(next);
    const screens = next.flatMap((r) => {
      if (r.custom) return [r.custom];
      if (!r.rule || !ruleComplete(r.rule)) return [];
      return [{ logic: ruleLogic(r.rule), reason: ruleReason(r.rule, byName.get(r.rule.column)) }];
    });
    onChange({ ...spec, screens });
  }

  const addRow = () => {
    const first = usable[0];
    if (!first) return;
    commit([...rows, { key: nextKey++, rule: { column: first.name, op: opsFor(first)[0], value: null } }]);
  };
  const update = (key: number, rule: Rule) => commit(rows.map((r) => (r.key === key ? { ...r, rule } : r)));
  const drop = (key: number) => commit(rows.filter((r) => r.key !== key));

  return (
    <section className="section yi-section" aria-labelledby="yi-screens-title">
      <div className="section__head">
        <h2 className="section__title" id="yi-screens-title">Leave Out Sites</h2>
        <span className="section__aside num">{spec.screens.length} {spec.screens.length === 1 ? 'rule' : 'rules'}</span>
      </div>
      <p className="section__intro">Optional. A site a rule leaves out is not scored; it is listed with the rule's reason. Rules run before any scoring.</p>
      <Refusals items={refusals} />
      {rows.length > 0 && (
        <ul className="yi-rules" role="list">
          {rows.map((r) => r.custom
            ? (
              <li className="yi-card yi-rule" key={r.key}>
                <p className="yi-rule__custom">Rule from a saved file: <strong>{r.custom.reason}</strong></p>
                <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={() => drop(r.key)}>
                  <span className="hig-button__label">Remove Rule</span>
                </button>
              </li>
            )
            : <RuleEditor key={r.key} rule={r.rule!} usable={usable} entry={byName.get(r.rule!.column)} byName={byName} onChange={(x) => update(r.key, x)} onRemove={() => drop(r.key)} />)}
        </ul>
      )}
      <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus hig-pressable yi-add-rule" onClick={addRow} disabled={!usable.length}>
        <Icon name="plus" size={16} strokeWidth={2.2} />
        <span className="hig-button__label">Add a Rule</span>
      </button>
    </section>
  );
}

function RuleEditor({ rule, usable, entry, byName, onChange, onRemove }: {
  rule: Rule; usable: ColumnEntry[]; entry: ColumnEntry | undefined; byName: Map<string, ColumnEntry>;
  onChange(r: Rule): void; onRemove(): void;
}) {
  const id = useId();
  const ops = opsFor(entry);
  const flag = entry && role(entry) === 'flag';
  const numeric = entry && isNumeric(entry) && !flag;
  const labels = entry ? levels(entry) : [];
  const complete = ruleComplete(rule);

  function setColumn(name: string) {
    const e = byName.get(name);
    const nextOps = opsFor(e);
    onChange({ column: name, op: nextOps.includes(rule.op) ? rule.op : nextOps[0], value: null });
  }

  return (
    <li className="yi-card yi-rule" aria-labelledby={`${id}-lead`}>
      <p className="yi-rule__lead" id={`${id}-lead`}>Leave out a site when</p>
      <div className="yi-rule__parts">
        <SelectField label="Column" value={rule.column} onChange={setColumn}>
          {usable.map((e) => <option key={e.name} value={e.name}>{e.name}</option>)}
        </SelectField>
        <SelectField label="Condition" value={rule.op} onChange={(x) => {
          const op = x as RuleOp;
          const value = op === 'in' ? (typeof rule.value === 'string' ? [rule.value] : []) : op === 'missing' ? null : Array.isArray(rule.value) ? (rule.value[0] ?? null) : rule.value;
          onChange({ ...rule, op, value });
        }}>
          {ops.map((op) => <option key={op} value={op}>{OP_WORDS[op]}</option>)}
        </SelectField>
        {rule.op !== 'missing' && rule.op !== 'in' && numeric && (
          <NumberField label="Value" value={typeof rule.value === 'number' ? rule.value : undefined} onChange={(x) => onChange({ ...rule, value: x ?? null })} />
        )}
        {rule.op !== 'missing' && rule.op !== 'in' && !numeric && (
          <SelectField label="Value" value={rule.value === null ? '' : String(rule.value)} onChange={(x) => onChange({ ...rule, value: x === '' ? null : flag ? Number(x) : x })}>
            <option value="">Choose</option>
            {flag
              ? <><option value="1">Yes</option><option value="0">No</option></>
              : labels.map((l) => <option key={l} value={l}>{l}</option>)}
          </SelectField>
        )}
        {rule.op === 'in' && (
          <fieldset className="yi-rule__in">
            <legend className="yi-field__label">Values</legend>
            {labels.map((l) => {
              const chosen = Array.isArray(rule.value) && rule.value.map(String).includes(l);
              return (
                <label className="yi-check" key={l}>
                  <input type="checkbox" checked={chosen} onChange={() => {
                    const now = Array.isArray(rule.value) ? rule.value.map(String) : [];
                    onChange({ ...rule, value: chosen ? now.filter((x) => x !== l) : [...now, l] });
                  }} />
                  <span>{l}</span>
                </label>
              );
            })}
          </fieldset>
        )}
      </div>
      <div className="yi-rule__foot">
        <p className="yi-hint" aria-live="polite">
          {complete
            ? <>Reason shown: <strong>{ruleReason(rule, entry)}</strong>. {missingLeftOut(rule.op) ? 'A site with no value here is left out too.' : 'A site with no value here is kept.'}</>
            : 'Choose a value to finish this rule. Until then it leaves out no site.'}
        </p>
        <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={onRemove} aria-label={`Remove the rule on ${rule.column}`}>
          <span className="hig-button__label">Remove Rule</span>
        </button>
      </div>
    </li>
  );
}
