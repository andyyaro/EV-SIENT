// Check: every row as the model will read it. Rows are Must Fix, Missing Values or Ready; nothing
// is estimated and no row is left out. Warnings and notes are the engine's own sentences.

import { useEffect, useId, useMemo, useState, type MouseEvent } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { Progress } from '../components/Progress';
import { StatusMark } from '../components/StatusMark';
import { StepActions } from '../components/StepActions';
import type { AcceptDetails, CheckRow, Finding, RowStatus } from '../engine/protocol';
import { fieldLabel, listWords, plainText, plural } from '../lib/fieldText';
import { readableFileName } from '../lib/projectName';
import { stepGate, useSession } from '../state/store';

const PAGE = 100;

/** Jump to an element on this page without touching the step address in the URL. */
function jump(e: MouseEvent<HTMLAnchorElement>, id: string) {
  e.preventDefault();
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ block: 'center' });
  el.focus({ preventScroll: true });
}

function ErrorSummary({ refusals, rows }: { refusals: Finding[]; rows: CheckRow[] }) {
  const fields = useSession((s) => s.fields);
  const titleId = useId();
  if (!refusals.length && !rows.length) return null;
  return (
    <div className="st-error-summary" role="alert" aria-labelledby={titleId}>
      <h2 id={titleId} className="st-error-summary__title">
        <Icon name="exclamationmark.triangle" size={22} /> There Is a Problem
      </h2>
      <p className="st-error-summary__lede">The model cannot run until these are fixed in your spreadsheet or in Map Columns.</p>
      <ul className="st-error-summary__list">
        {refusals.map((f, i) => (
          <li key={`f${i}`}><a href="#file-problems" onClick={(e) => jump(e, 'file-problems')}>{plainText(fields, f.explain)}</a></li>
        ))}
        {rows.slice(0, 20).map((r) => r.mustFix.map((m, j) => (
          <li key={`${r.row}-${j}`}><a href={`#row-${r.row}`} onClick={(e) => jump(e, `row-${r.row}`)}>Row {r.row}{r.siteId ? ` (${r.siteId})` : ''}: {m}</a></li>
        )))}
        {rows.length > 20 && <li>and {plural(rows.length - 20, 'more row')} marked Must Fix in the table below.</li>}
      </ul>
    </div>
  );
}

function FindingList({ title, findings, id }: { title: string; findings: Finding[]; id: string }) {
  const fields = useSession((s) => s.fields);
  if (!findings.length) return null;
  return (
    <section className="st-findings" aria-labelledby={id}>
      <h3 id={id} className="st-subtitle">{title} <span className="st-count num">{findings.length}</span></h3>
      <ul className="st-finding-list">
        {findings.map((f, i) => (
          <li key={i} className="st-finding">
            <p className="st-finding__field">{fieldLabel(fields, f.field)}</p>
            <p className="st-finding__text">{plainText(fields, f.explain)}</p>
            {f.detail && <p className="st-finding__detail num">{plainText(fields, f.detail)}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}

function DetailsForm() {
  const s = useSession();
  // Taken from the session once, when the screen opens; edits are saved back on leaving a field.
  const [draft, setDraft] = useState<AcceptDetails>(() => s.details);
  const save = () => s.setDetails({
    jurisdiction: draft.jurisdiction?.trim() ?? '',
    sourceOrg: draft.sourceOrg?.trim() ?? '',
    sourceDate: draft.sourceDate ?? '',
  });
  const fallbackName = s.table ? readableFileName(s.table.fileName) : 'the file name';
  const field = (key: keyof AcceptDetails, label: string, type: 'text' | 'date', placeholder?: string) => (
    <label className="st-inset-field">
      <span className="st-inset-field__label">{label}</span>
      <input
        type={type}
        value={draft[key] ?? ''}
        placeholder={placeholder}
        max={type === 'date' ? new Date().toLocaleDateString('en-CA') : undefined}
        autoComplete={type === 'date' ? 'off' : 'organization'}
        onChange={(e) => { const v = e.target.value; setDraft((d) => ({ ...d, [key]: v })); }}
        onBlur={save}
      />
    </label>
  );
  return (
    <section className="section" aria-labelledby="details-title">
      <h2 id="details-title" className="section__title">Where the Data Came From</h2>
      <p className="section__intro">
        Optional. These are written into the results and the report so a reader knows the source. Leave the name empty and {fallbackName} is used.
      </p>
      <div className="card st-details">
        <div className="st-inset-fields">
          {field('jurisdiction', 'Jurisdiction or Organisation', 'text', 'For example, City of Example')}
          {field('sourceOrg', 'Data Supplied By', 'text', 'For example, Facilities Department')}
          {field('sourceDate', 'Date of the Data', 'date')}
        </div>
        <p className="footnote st-gap-top">
          {draft.sourceDate
            ? 'Data confidence takes the age of the data into account.'
            : 'No date given: the data is recorded as undated, which lowers data confidence for every site.'}
        </p>
      </div>
    </section>
  );
}

const FILTERS: { key: 'all' | RowStatus; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'must_fix', label: 'Must Fix' },
  { key: 'missing', label: 'Missing Values' },
  { key: 'ready', label: 'Ready' },
];

function RowsTable() {
  const s = useSession();
  const check = s.check!;
  const [filter, setFilter] = useState<'all' | RowStatus>(check.counts.mustFix ? 'must_fix' : 'all');
  const [limit, setLimit] = useState(PAGE);
  const rows = useMemo(() => (filter === 'all' ? check.rows : check.rows.filter((r) => r.status === filter)), [check.rows, filter]);
  const shown = rows.slice(0, limit);
  const counts: Record<string, number> = { all: check.counts.total, must_fix: check.counts.mustFix, missing: check.counts.missing, ready: check.counts.ready };
  return (
    <section className="section" aria-labelledby="rows-title">
      <div className="section__head">
        <h2 id="rows-title" className="section__title">Every Row</h2>
      </div>
      <div className="st-filter" role="group" aria-label="Show rows">
        {FILTERS.map((f) => (
          <button key={f.key} type="button" className={'st-filter__btn hig-focus' + (filter === f.key ? ' is-on' : '')} aria-pressed={filter === f.key}
            onClick={() => { setFilter(f.key); setLimit(PAGE); }}>
            {f.label} <span className="num">{counts[f.key]}</span>
          </button>
        ))}
      </div>
      {/* Explicit table roles: on narrow screens the rows are laid out as stacked cards (steps.css),
          and the roles keep the table's meaning for screen readers whatever the CSS display. */}
      <div className="st-table-wrap st-table-wrap--rows" role="region" aria-label="Every row table" tabIndex={0}>
        <table className="st-table st-table--rows" role="table">
          <caption className="hig-visually-hidden">Rows in your file and their status. Row numbers are as in your spreadsheet, with the headings in row 1.</caption>
          <thead role="rowgroup">
            <tr role="row">
              <th scope="col" role="columnheader" className="st-num-col">Row</th>
              <th scope="col" role="columnheader">Site ID</th>
              <th scope="col" role="columnheader">Site Name</th>
              <th scope="col" role="columnheader">Status</th>
              <th scope="col" role="columnheader">Details</th>
            </tr>
          </thead>
          <tbody role="rowgroup">
            {shown.map((r) => (
              <tr key={r.row} id={`row-${r.row}`} tabIndex={-1} role="row" className={`st-row st-row--${r.status}`}>
                <td role="cell" className="st-num-col st-cell-row num"><span className="st-cell-label" aria-hidden="true">Row </span>{r.row}</td>
                <td role="cell" className="st-mono st-cell-id"><span className="st-cell-label" aria-hidden="true">Site ID </span>{r.siteId || <span className="st-blank">blank</span>}</td>
                <td role="cell" className="st-cell-name">{r.siteName || <span className="st-blank">none</span>}</td>
                <td role="cell" className="st-cell-status"><StatusMark kind={r.status} /></td>
                <td role="cell" className="st-wrap st-cell-details">
                  {r.mustFix.map((m, i) => <p key={i}>{m}</p>)}
                  {r.missing.length > 0 && <p>No value for {listWords(r.missing.map((m) => fieldLabel(s.fields, m)))}.</p>}
                  {!r.mustFix.length && !r.missing.length && <span className="st-muted">Every matched field has a value.</span>}
                </td>
              </tr>
            ))}
            {!shown.length && <tr role="row" className="st-row-empty"><td role="cell" colSpan={5} className="st-muted">No rows with this status.</td></tr>}
          </tbody>
        </table>
      </div>
      {rows.length > shown.length && (
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus st-gap-top" onClick={() => setLimit(limit + PAGE)}>
          Show {Math.min(PAGE, rows.length - shown.length)} More of {rows.length - shown.length}
        </button>
      )}
    </section>
  );
}

export function CheckStep() {
  const s = useSession();
  const gate = stepGate(s, 'check');
  const runGate = stepGate(s, 'run');

  useEffect(() => {
    const now = useSession.getState();
    if (stepGate(now, 'check').open && !now.check && !now.busy) void now.runCheck();
  }, [s.proposal]);

  if (!gate.open) {
    return (
      <div className="page st-page">
        <PageHead title="Check" lede={gate.reason} />
      </div>
    );
  }

  const check = s.check;
  const p = s.proposal!;
  const fileRefusals = check ? check.refusals : p.findings.filter((f) => f.severity === 'refusal');
  const mustFixRows = check ? check.rows.filter((r) => r.status === 'must_fix') : [];
  const warnings = p.findings.filter((f) => f.severity === 'warning');
  // Fields absent from the whole file are summarised in one notice above, not one note each.
  const absent = new Set(check?.absentFromFile ?? []);
  const notes = p.findings.filter((f) => f.severity === 'note' && !absent.has(f.field));

  return (
    <div className="page st-page">
      <PageHead title="Check" lede="Every row, as the model will read it. Nothing has been estimated and no row is left out." />

      <div role="status" aria-live="polite" className="st-inline-status">
        {s.busy === 'check' && <Progress label="Checking every row" />}
      </div>

      {check && (
        <>
          <ErrorSummary refusals={fileRefusals} rows={mustFixRows} />

          <p className="st-coverage num">
            {p.refused
              ? plural(check.counts.total, 'site')
              : `${check.counts.located} of ${plural(check.counts.total, 'site')} ${check.counts.total === 1 ? 'has' : 'have'} a usable location`}
            {' · '}{check.counts.ready} Ready · {check.counts.missing} Missing Values · {check.counts.mustFix} Must Fix
          </p>

          <div className="st-principle">
            <Icon name="info.circle" size={20} className="st-principle__icon" />
            <p><strong>Missing values never raise a score.</strong> A blank or unreadable value is scored as absent: it earns no credit and lowers data confidence. Nothing is estimated and no row is left out.</p>
          </div>

          {check.absentFromFile.length > 0 && (
            <Banner tone="info" title={`${plural(check.absentFromFile.length, 'Scored Field Is', 'Scored Fields Are')} Not in This File`}>
              <p>{listWords(check.absentFromFile.map((f) => fieldLabel(s.fields, f)))}. Every site is scored as if {check.absentFromFile.length === 1 ? 'it is' : 'they are'} absent, and data confidence is lower. If your file has {check.absentFromFile.length === 1 ? 'this' : 'any of these'}, match {check.absentFromFile.length === 1 ? 'it' : 'them'} in Map Columns.</p>
            </Banner>
          )}

          {fileRefusals.length > 0 && (
            <section id="file-problems" tabIndex={-1} className="section" aria-labelledby="file-problems-title">
              <h2 id="file-problems-title" className="section__title">Must Fix in the File</h2>
              <ul className="st-refusal-list">
                {fileRefusals.map((f, i) => (
                  <li key={i} className="card st-refusal">
                    <StatusMark kind="must_fix" />
                    <p className="st-refusal__why">{plainText(s.fields, f.explain)}</p>
                    {f.detail && <p className="footnote num">{plainText(s.fields, f.detail)}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <RowsTable />

          {(warnings.length > 0 || notes.length > 0) && (
            <section className="section" aria-labelledby="findings-title">
              <h2 id="findings-title" className="section__title">What the Model Noticed</h2>
              <p className="section__intro">The model's own words about how it will read your values. None of these stops a run.</p>
              <div className="card st-findings-card">
                <FindingList id="warn-title" title="Warnings" findings={warnings} />
                <FindingList id="note-title" title="Notes" findings={notes} />
              </div>
            </section>
          )}

          <DetailsForm />
        </>
      )}

      <StepActions
        onBack={() => s.go('map')}
        onNext={() => s.go('run')}
        nextLabel="Continue to Run"
        busy={s.busy === 'check'}
        blockedReason={runGate.open ? null : runGate.reason}
      />
    </div>
  );
}
