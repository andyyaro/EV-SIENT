// Map Columns: which column in the planner's file holds each field the model reads. The engine's
// guesses and unit conversions are shown with sample values and must be confirmed; nothing is
// matched silently. Every change sends the whole mapping to the engine (store.remap).

import { useEffect, useMemo, useState } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { StatusMark } from '../components/StatusMark';
import { StepActions } from '../components/StepActions';
import type { FieldInfo } from '../engine/protocol';
import { fieldLabel, plainText, plural, sentence } from '../lib/fieldText';
import { recall, remember, type RememberedMapping } from '../lib/rememberedMappings';
import { fullMapping, matchStatus, pendingMatches, stepGate, useSession } from '../state/store';

const NOT_IN_FILE = '';

function FieldRow({ field, announce }: { field: FieldInfo; announce: (message: string) => void }) {
  const s = useSession();
  const p = s.proposal!;
  const status = matchStatus(s, field.name);
  const column = p.mapping[field.name] ?? null;
  const summary = column ? p.columns.find((c) => c.name === column) : undefined;
  const conversion = p.conversions[field.name];
  const finding = conversion != null
    ? p.findings.find((f) => f.field === field.name && /multiplied by/.test(f.explain))
    : undefined;
  const unreadable = p.unreadable?.[field.name] ?? 0;
  const usedBy = useMemo(() => {
    const out = new Map<string, string>();
    for (const [f, c] of Object.entries(p.mapping)) if (c) out.set(c, f);
    return out;
  }, [p.mapping]);
  const selectId = `col-${field.name}`;
  const busy = s.busy === 'remap';

  async function choose(value: string) {
    const chosen = value === NOT_IN_FILE ? null : value;
    const from = await s.chooseColumn(field.name, chosen);
    if (useSession.getState().error) return;
    const label = fieldLabel(s.fields, field.name);
    announce(from
      ? `${chosen} now fills ${label}. It was matched to ${fieldLabel(s.fields, from)}, which is now Not in This File.`
      : chosen ? `${label} now reads from ${chosen}.` : `${label} is set to Not in This File.`);
    // The row may have moved to another group; keep focus on its column choice.
    requestAnimationFrame(() => {
      const target = document.getElementById(selectId)
        ?? document.querySelector<HTMLElement>('#grp-matched-title ~ button, section[aria-labelledby="grp-matched-title"] .section__head button');
      target?.focus();
    });
  }

  function confirm() {
    s.confirmMatch(field.name);
    announce(`Confirmed: ${field.label} reads from ${column}.`);
    requestAnimationFrame(() => {
      const next = document.querySelector<HTMLElement>('.st-map-row--check .st-map-row__ask button')
        ?? document.querySelector<HTMLElement>('.st-actions__next button');
      next?.focus();
    });
  }

  return (
    <li className={`st-map-row st-map-row--${status}`} id={`field-${field.name}`}>
      <div className="st-map-row__top">
        <div className="st-map-row__text">
          <h3 className="st-map-row__label">
            {field.label}
            {field.required && <span className="st-map-row__req"> (required)</span>}
          </h3>
          <p className="st-map-row__unit">{field.unit} · {field.groupLabel}</p>
        </div>
        <StatusMark kind={status} />
      </div>
      <p className="st-map-row__what">{plainText(s.fields, field.what)}</p>

      <div className="st-map-row__choose">
        <label htmlFor={selectId} className="st-map-row__select-label">Column in Your File</label>
        <span className="st-select st-select--wide">
          <select id={selectId} className="hig-focus" value={column ?? NOT_IN_FILE} disabled={busy} onChange={(e) => void choose(e.target.value)}>
            <option value={NOT_IN_FILE}>Not in This File</option>
            {p.columns.map((c) => {
              const other = usedBy.get(c.name);
              const note = other && other !== field.name ? ` (now ${fieldLabel(s.fields, other)})` : '';
              return <option key={c.name} value={c.name}>{c.name + note}</option>;
            })}
          </select>
          <Icon name="chevron.up.chevron.down" size={13} />
        </span>
      </div>

      {summary && (
        <div className="st-samples">
          <span className="st-samples__label">Sample values</span>
          <ul className="st-samples__list" aria-label={`Sample values from ${summary.name}`}>
            {summary.samples.length
              ? summary.samples.slice(0, 5).map((v, i) => <li key={i} className="st-chip num">{v}</li>)
              : <li className="st-chip st-chip--empty">every cell is blank</li>}
          </ul>
          {summary.blank > 0 && <span className="st-samples__blank num">{plural(summary.blank, 'blank cell')}</span>}
        </div>
      )}

      {status === 'check' && (
        <div className="st-map-row__ask">
          <p>
            {finding
              ? <><strong>Unit conversion.</strong> {plainText(s.fields, finding.explain)} Is that right for this column?</>
              : unreadable > 0
              ? <><strong>Values do not fit.</strong> {`${unreadable} of ${p.rowCount} cells in this column cannot be read as ${field.kind === 'flag' ? 'yes or no' : 'a number'}, so those sites would be scored as missing for ${field.label}. Confirm to use it anyway, or choose Not in This File.`}</>
              : <><strong>Close match.</strong> The column name is close to {field.label} but not the same. Is this the right column?</>}
          </p>
          <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered-prominent hig-focus" onClick={confirm}>
            <Icon name="checkmark" size={16} strokeWidth={2.2} />
            <span className="hig-button__label">Confirm</span>
          </button>
        </div>
      )}
      {status === 'matched' && conversion != null && finding && (
        <p className="st-map-row__note"><Icon name="info.circle" size={16} /> {plainText(s.fields, finding.explain)}</p>
      )}

      <p className="st-map-row__missing">
        <span className="st-map-row__missing-label">If this is missing:</span> {sentence(field.if_missing)}
      </p>
    </li>
  );
}

function Group({ id, title, intro, fields, open, onToggle, announce }: {
  id: string; title: string; intro: string; fields: FieldInfo[]; open: boolean; onToggle?: () => void;
  announce: (message: string) => void;
}) {
  if (!fields.length) return null;
  return (
    <section className="section st-group" aria-labelledby={`${id}-title`}>
      <div className="section__head">
        <h2 id={`${id}-title`} className="section__title">{title} <span className="st-count num">{fields.length}</span></h2>
        {onToggle && (
          <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" aria-expanded={open} aria-controls={`${id}-list`} onClick={onToggle}>
            {open ? 'Hide' : 'Show All'}
          </button>
        )}
      </div>
      <p className="section__intro">{intro}</p>
      {open && <ul id={`${id}-list`} className="st-map-list">{fields.map((f) => <FieldRow key={f.name} field={f} announce={announce} />)}</ul>}
    </section>
  );
}

export function MapStep() {
  const s = useSession();
  const p = s.proposal;
  const [showMatched, setShowMatched] = useState(false);
  const [remembered, setRemembered] = useState<RememberedMapping | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [announcement, setAnnouncement] = useState('');

  // Offer choices made before for a file with exactly these headings.
  useEffect(() => {
    if (!s.table || !p) return;
    const saved = recall(s.table.columns);
    if (!saved) return;
    const now = fullMapping(s);
    const differs = Object.entries(saved.mapping).some(([f, c]) => (now[f] ?? null) !== c);
    setRemembered(differs ? saved : null);
    // Only when the file changes, not on every remap.
  }, [s.table]);

  if (!p || !s.fields) {
    return (
      <div className="page st-page">
        <PageHead title="Map Columns" lede="Upload a file first." />
      </div>
    );
  }

  const fields = s.fields.fields;
  const byStatus = { check: [] as FieldInfo[], matched: [] as FieldInfo[], unmatched: [] as FieldInfo[] };
  for (const f of fields) byStatus[matchStatus(s, f.name)].push(f);
  const pending = pendingMatches(s);
  const gate = stepGate(s, 'check');

  function next() {
    if (s.table) remember(s.table.columns, fullMapping(s));
    s.go('check');
  }

  return (
    <div className="page st-page">
      <PageHead
        title="Map Columns"
        lede="Tell the model which column in your file holds each thing it reads. It never fills a gap with a default: a field you leave out is scored as absent and earns no credit."
      />

      {remembered && !dismissed && (
        <Banner
          tone="info"
          title="Use Your Earlier Choices?"
          onDismiss={() => setDismissed(true)}
          action={
            <div className="st-banner-buttons">
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered-prominent hig-focus"
                onClick={async () => { await s.applyMapping(remembered.mapping); setRemembered(null); }}>
                Use Those Choices
              </button>
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => setDismissed(true)}>
                Not Now
              </button>
            </div>
          }
        >
          <p>You matched columns for a file with exactly these headings on {new Date(remembered.savedAt).toLocaleDateString('en-US', { dateStyle: 'medium' })}. Only the headings and your choices were kept on this device, never any values.</p>
        </Banner>
      )}

      <div className="st-map-summary card">
        <ul className="st-map-counts" aria-label="Match summary">
          <li><StatusMark kind="matched" label={`${byStatus.matched.length} Matched`} /></li>
          <li><StatusMark kind="check" label={`${byStatus.check.length} Check This Match`} /></li>
          <li><StatusMark kind="unmatched" label={`${byStatus.unmatched.length} Not Matched`} /></li>
        </ul>
        {pending.length > 0 && (
          <div className="st-map-summary__all">
            <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => { const n = pending.length; s.confirmAll(); setAnnouncement(`Confirmed ${plural(n, 'match', 'matches')}.`); }}>
              Accept All Matched
            </button>
            <p className="footnote">Confirms every suggested match below as shown, including the unit conversions they describe.</p>
          </div>
        )}
      </div>

      <div role="status" aria-live="polite" className="st-inline-status">
        {s.busy === 'remap' ? 'Updating the matches.' : announcement}
      </div>

      <Group id="grp-check" title="Check This Match" open
        intro="The model made a guess here, or will convert the units. Look at the sample values, then confirm or choose another column."
        fields={byStatus.check} announce={setAnnouncement} />
      <Group id="grp-unmatched" title="Not Matched" open
        intro="No column in your file was matched to these. Choose one if your file has it; otherwise each is scored as absent."
        fields={byStatus.unmatched} announce={setAnnouncement} />
      <Group id="grp-matched" title="Matched" open={showMatched || byStatus.matched.length <= 6} onToggle={byStatus.matched.length > 6 ? () => setShowMatched((v) => !v) : undefined}
        intro="These columns match the field names exactly, or you chose or confirmed them. You can still change any of them."
        fields={byStatus.matched} announce={setAnnouncement} />

      <StepActions
        onBack={() => s.go('upload')}
        onNext={next}
        nextLabel="Continue to Check"
        busy={s.busy === 'remap'}
        blockedReason={pending.length
          ? `Confirm or change the ${pending.length === 1 ? 'match' : `${pending.length} matches`} marked Check This Match to continue.`
          : !gate.open ? gate.reason : null}
      />
      {p.refused && (
        <p className="footnote st-gap-top">
          This file has {plural(p.findings.filter((f) => f.severity === 'refusal').length, 'item')} marked Must Fix. Check lists {p.findings.length > 1 ? 'them' : 'it'}; some can be fixed here, for example by choosing the column that holds the site ID.
        </p>
      )}
    </div>
  );
}
