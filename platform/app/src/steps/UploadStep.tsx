// Upload: a CSV or Excel file, read in this browser tab. Choose the sheet and the heading row, see
// the first rows as the planner typed them, then the engine says what it found.

import { useId, useRef, useState } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { Progress } from '../components/Progress';
import { StepActions } from '../components/StepActions';
import { plainText, plural, refusalFix } from '../lib/fieldText';
import { ACCEPT, LIMITS, formatBytes } from '../lib/parseTable';
import { stepGate, useSession } from '../state/store';
import { TEMPLATE_URL, useUpload } from './uploadState';

const PREVIEW_ROWS = 5;

function DropZone() {
  const upload = useUpload();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const hintId = useId();
  return (
    <div
      className={'st-drop' + (over ? ' is-over' : '')}
      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) void upload.ingest(f);
      }}
    >
      <Icon name="square.and.arrow.up" size={32} strokeWidth={1.5} className="st-drop__icon" />
      <p className="st-drop__title">Drop Your Spreadsheet Here</p>
      <p id={hintId} className="st-drop__hint">CSV, XLSX, XLS or ODS, up to {formatBytes(LIMITS.bytes)} and {LIMITS.rows.toLocaleString('en-US')} sites. One row per site.</p>
      <button
        type="button"
        className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus"
        onClick={() => input.current?.click()}
        aria-describedby={hintId}
        disabled={upload.reading}
      >
        <span className="hig-button__label">Choose a File</span>
      </button>
      <input
        ref={input}
        type="file"
        accept={ACCEPT}
        className="hig-visually-hidden"
        tabIndex={-1}
        aria-hidden="true"
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void upload.ingest(f); }}
      />
      <p className="st-drop__template">
        No file yet? <a href={TEMPLATE_URL} download="evsient-template.csv">Download the Blank Template</a> with the 32 columns the model reads.
      </p>
    </div>
  );
}

function FileChoices() {
  const upload = useUpload();
  const parsed = upload.parsed!;
  const sheet = parsed.sheets[upload.sheet];
  const headerChoices = sheet ? sheet.cells.slice(0, 10).map((row, i) => ({ i, text: row.filter((v) => v.trim()).slice(0, 4).join(', ') })) : [];
  return (
    <div className="st-fields">
      {parsed.sheets.length > 1 && (
        <label className="st-field">
          <span className="st-field__label">Sheet</span>
          <span className="st-select">
            <select className="hig-focus" value={upload.sheet} onChange={(e) => void upload.chooseSheet(Number(e.target.value))}>
              {parsed.sheets.map((sh, i) => (
                <option key={sh.name} value={i}>{`${sh.name}${sh.cells.length ? '' : ' (empty)'}`}</option>
              ))}
            </select>
            <Icon name="chevron.up.chevron.down" size={13} />
          </span>
        </label>
      )}
      <label className="st-field">
        <span className="st-field__label">Headings Are in</span>
        <span className="st-select">
          <select className="hig-focus" value={upload.headerRow} onChange={(e) => void upload.chooseHeaderRow(Number(e.target.value))}>
            {headerChoices.map(({ i, text }) => (
              <option key={i} value={i}>{`Row ${i + 1}${text ? `: ${text.length > 48 ? text.slice(0, 47) + '...' : text}` : ' (empty)'}`}</option>
            ))}
          </select>
          <Icon name="chevron.up.chevron.down" size={13} />
        </span>
      </label>
    </div>
  );
}

function Preview() {
  const build = useUpload((u) => u.build);
  const table = build?.table;
  if (!table) return null;
  const rows = table.rows.slice(0, PREVIEW_ROWS);
  return (
    <section className="section" aria-labelledby="preview-title">
      <div className="section__head">
        <h2 id="preview-title" className="section__title">First Rows</h2>
        <span className="section__aside num">{plural(table.rows.length, 'row')} · {plural(table.columns.length, 'column')}</span>
      </div>
      <div className="st-table-wrap" role="region" aria-labelledby="preview-title" tabIndex={0}>
        <table className="st-table st-table--preview">
          <caption className="hig-visually-hidden">The first {rows.length} rows of {table.fileName}, as written in the file</caption>
          <thead>
            <tr>{table.columns.map((c, j) => <th key={j} scope="col">{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>{r.map((v, j) => <td key={j}>{v === '' ? <span className="st-blank">blank</span> : v}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      {(build.skippedBlankRows > 0 || build.skippedBlankColumns > 0) && (
        <p className="footnote st-gap-top">
          {[
            build.skippedBlankRows ? `${plural(build.skippedBlankRows, 'empty row')} left out` : '',
            build.skippedBlankColumns ? `${plural(build.skippedBlankColumns, 'empty column')} with no heading left out` : '',
          ].filter(Boolean).join(' · ')}. Nothing else was changed.
        </p>
      )}
    </section>
  );
}

function Detection() {
  const s = useSession();
  const p = s.proposal;
  if (!p) return null;
  const total = s.fields?.fields.length ?? Object.keys(p.status).length;
  const matched = Object.keys(p.mapping).length;
  const located = s.check?.counts.located;
  const hasCoords = !!p.mapping.lat && !!p.mapping.lon;
  const parts = [plural(p.rowCount, 'site'), `${matched} of ${total} fields matched`];
  if (!p.refused && s.check && hasCoords) {
    parts.push(located === p.rowCount ? 'coordinates in every row' : `coordinates in ${located} of ${p.rowCount} rows`);
  } else if (!hasCoords) {
    parts.push('no coordinates');
  }
  const refusals = p.findings.filter((f) => f.severity === 'refusal');
  return (
    <section className="section" aria-labelledby="found-title">
      <h2 id="found-title" className="section__title">What the Model Found</h2>
      <p className="st-detect num" role="status">{parts.join(' · ')}</p>
      {refusals.length > 0 && (
        <div className="st-refusals">
          <Banner tone="error" title="This File Cannot Be Run Yet">
            <p>The model will not guess at these, so each needs a fix.</p>
          </Banner>
          <ul className="st-refusal-list">
            {refusals.map((f, i) => (
              <li key={i} className="card st-refusal">
                <p className="st-refusal__why">{plainText(s.fields, f.explain)}</p>
                {f.detail && <p className="footnote">{plainText(s.fields, f.detail)}</p>}
                <p className="st-refusal__fix"><strong>What to do:</strong> {refusalFix(f)}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

export function UploadStep() {
  const s = useSession();
  const upload = useUpload();
  const table = s.table;
  const proposing = s.busy === 'propose';
  const booting = s.boot.status === 'booting';
  const gate = stepGate(s, 'map');
  // The file on screen is the one the engine has: a newly chosen file that failed does not count.
  const current = upload.replacing ? false
    : upload.parsed ? !!upload.build?.table && s.table === upload.build.table
    : !!table;
  const blockedReason = !current
    ? (upload.parsed && !upload.replacing ? 'Fix the problems above, or choose a different file.' : 'Choose a file first.')
    : !gate.open ? 'Wait for the model to read the file.' : null;

  return (
    <div className="page st-page">
      <PageHead
        title="Upload"
        lede="Choose the spreadsheet of sites you want to rank. It is read here, in this browser tab, and is not uploaded anywhere."
      />

      {upload.sample && !upload.replacing && (
        <Banner tone="info" title="Example City Is Invented Data">
          <p>The six sites, their values and the city are made up, to show how the planner works. Do not use these results for decisions.</p>
        </Banner>
      )}

      {upload.parsed && !upload.replacing ? (
        <section className="card st-file" aria-label="Your file">
          <div className="st-file__head">
            <Icon name="doc" size={28} strokeWidth={1.5} className="st-file__icon" />
            <div className="st-file__text">
              <p className="st-file__name">{upload.parsed.fileName}</p>
              <p className="st-muted num">{formatBytes(upload.parsed.size)}{upload.parsed.sheets.length > 1 ? ` · ${plural(upload.parsed.sheets.length, 'sheet')}` : ''}</p>
            </div>
            <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => upload.clear()}>
              Choose a Different File
            </button>
          </div>
          <FileChoices />
        </section>
      ) : table && !upload.replacing ? (
        <section className="card st-file" aria-label="Your file">
          <div className="st-file__head">
            <Icon name="doc" size={28} strokeWidth={1.5} className="st-file__icon" />
            <div className="st-file__text">
              <p className="st-file__name">{table.fileName}</p>
              <p className="st-muted num">{plural(table.rows.length, 'row')} · {plural(table.columns.length, 'column')}{table.sheet ? ` · sheet ${table.sheet}` : ''}</p>
            </div>
            <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => upload.clear()}>
              Choose a Different File
            </button>
          </div>
        </section>
      ) : (
        <>
          <DropZone />
          {table && (
            <p className="st-keep">
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => upload.cancelReplace()}>
                Keep {table.fileName}
              </button>
            </p>
          )}
        </>
      )}

      <div role="status" aria-live="polite" className="st-inline-status">
        {upload.reading && <Progress label="Reading your file" />}
        {proposing && (booting
          ? <Progress label={`Waiting for the model: ${s.boot.status === 'booting' ? s.boot.progress.message : ''}`} fraction={s.boot.status === 'booting' ? s.boot.progress.fraction : undefined} />
          : <Progress label="The model is reading the columns" />)}
      </div>

      {upload.readError && (
        <Banner tone="error" title="This File Cannot Be Read">
          <p>{upload.readError}</p>
        </Banner>
      )}
      {upload.build && upload.build.problems.length > 0 && (
        <Banner tone="error" title="Fix This in Your Spreadsheet">
          <ul className="st-plain-list">{upload.build.problems.map((p, i) => <li key={i}>{p}</li>)}</ul>
        </Banner>
      )}

      {!upload.replacing && <Preview />}
      {current && !proposing && <Detection />}

      <StepActions
        onBack={() => s.go('start')}
        onNext={() => s.go('map')}
        nextLabel="Continue to Map Columns"
        busy={proposing || upload.reading}
        blockedReason={blockedReason}
      />
    </div>
  );
}
