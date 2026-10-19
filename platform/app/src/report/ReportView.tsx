// The Report screen: the downloads, then the report itself as a light, print-ready page. The
// preview's markup is what the .html download contains and what Print sends to the printer.

import { useMemo, useRef, useState } from 'react';
import { Icon } from '../components/Icon';
import { useSession } from '../state/store';
import { useAllExplains, useOutputFiles } from '../results/data';
import { ReportDocument } from './ReportDocument';
import { buildModel, fileName, type ReportModel } from './reportModel';
import { outputsZip, reportDocx, reportHtml, reportPdf, saveBlob, sitesCsv, workbook } from './exports';
import { buildProjectFile } from './projectFile';
import { previewThemeCss } from './reportTheme';
import '../styles/report.css';

type Job = 'html' | 'pdf' | 'docx' | 'csv' | 'xlsx' | 'zip' | 'project';

export function ReportView() {
  const run = useSession((s) => s.run);
  const boot = useSession((s) => s.boot);
  const details = useSession((s) => s.details);
  const fields = useSession((s) => s.fields);
  const table = useSession((s) => s.table);
  const stale = useSession((s) => s.staleReason);
  const go = useSession((s) => s.go);
  const explains = useAllExplains(run);
  const files = useOutputFiles(run);
  const paper = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState<Job | null>(null);
  const [status, setStatus] = useState('');

  const info = boot.status === 'ready' ? boot.info : null;
  const model: ReportModel | null = useMemo(() => {
    if (!run || explains.status !== 'ready' || files.status !== 'ready') return null;
    return buildModel({ run, explains: explains.value, files: files.value, info, details, fields, table });
  }, [run, explains, files, info, details, fields, table]);

  if (!run) {
    return (
      <div className="page">
        <header className="page-head"><h1 className="page-head__title">Report</h1></header>
        <p className="prose">Run the model first. The report is built from the run's results.</p>
      </div>
    );
  }

  const failed = explains.status === 'error' ? explains.message : files.status === 'error' ? files.message : null;

  async function save(job: Job) {
    if (!model || busy) return;
    setBusy(job);
    setStatus('Preparing the file');
    try {
      let out: { blob: Blob; name: string };
      if (job === 'html' || job === 'pdf' || job === 'docx') {
        const article = paper.current?.querySelector<HTMLElement>('.rp');
        if (!article) throw new Error('The report is not ready yet.');
        if (job === 'pdf') setStatus('Preparing the PDF. The first one loads the PDF maker, and a report with many sites can take a minute.');
        out = job === 'html' ? reportHtml(model, article) : job === 'pdf' ? await reportPdf(model, article) : await reportDocx(model, article);
      } else if (job === 'csv') out = sitesCsv(model);
      else if (job === 'xlsx') out = await workbook(model);
      else if (job === 'zip') out = await outputsZip(model);
      else out = { blob: await buildProjectFile(), name: fileName(model, 'project', 'evsient') };
      saveBlob(out.blob, out.name);
      setStatus(`Saved ${out.name}.`);
    } catch (e) {
      setStatus(`That file could not be made: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(null);
    }
  }

  const items: { job: Job | 'print'; icon: string; title: string; detail: string; action: string }[] = [
    { job: 'html', icon: 'doc', title: 'Report', detail: 'One accessible web page with everything below. Opens in any browser, offline.', action: 'Download .html' },
    { job: 'pdf', icon: 'document.on.document', title: 'Accessible PDF', detail: 'The same report as a tagged PDF with bookmarks, for screen readers, sharing and print.', action: 'Download .pdf' },
    { job: 'docx', icon: 'square.and.pencil', title: 'Word Document', detail: 'The same report as an editable Word file, with heading styles and table header rows.', action: 'Download .docx' },
    { job: 'print', icon: 'printer', title: 'Print', detail: 'Opens your browser\'s print dialog for a paper copy. For a PDF to share, use the Accessible PDF above.', action: 'Print' },
    { job: 'csv', icon: 'list.bullet', title: 'Ranked Sites', detail: 'One row per site with every number in the ranked table and site profiles.', action: 'Download .csv' },
    { job: 'xlsx', icon: 'chart.bar', title: 'Excel Workbook', detail: 'Sites, Scenarios and Data Confidence sheets. Values only, no formulas.', action: 'Download .xlsx' },
    { job: 'zip', icon: 'archivebox', title: 'All Model Outputs', detail: 'Every file the engine wrote for this run, with the accepted inputs.', action: 'Download .zip' },
    { job: 'project', icon: 'folder', title: 'Project File', detail: 'Open it later in the planner to rebuild these results on any device.', action: 'Download .evsient' },
  ];

  return (
    <div className="page page--wide rp-screen">
      <div className="rp-noprint">
        <header className="page-head">
          <h1 className="page-head__title">Report</h1>
          <p className="page-head__lede">A report for a council packet or a grant file, built on this device from the engine's results. Download it, print it, or take the tables and outputs.</p>
        </header>

        {stale && (
          <div className="notice rp-stale" role="status">
            <span className="notice__icon" aria-hidden="true"><Icon name="exclamationmark.triangle" size={20} /></span>
            <div className="rp-stale__body">
              <p className="notice__title">Out of Date</p>
              <p className="notice__body">{stale} This report shows the last run. Run the model again before sharing it.</p>
            </div>
            <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable" onClick={() => go('run')}>
              <span className="hig-button__label">Go to Run</span>
            </button>
          </div>
        )}

        <section aria-labelledby="rp-dl-title" className="rp-downloads">
          <h2 className="section__title" id="rp-dl-title">Downloads</h2>
          <ul className="rp-dl-list" role="list">
            {items.map((it) => (
              <li className="rp-dl-row" key={it.job}>
                <span className="rp-dl-row__icon" aria-hidden="true"><Icon name={it.icon} size={22} /></span>
                <span className="rp-dl-row__text">
                  <span className="rp-dl-row__title">{it.title}</span>
                  <span className="rp-dl-row__detail">{it.detail}</span>
                </span>
                <button
                  type="button"
                  className="hig-button hig-button--ios hig-button--small hig-button--bordered hig-focus hig-pressable rp-dl-row__btn"
                  disabled={!model || (busy !== null && busy !== it.job)}
                  aria-busy={busy === it.job || undefined}
                  aria-label={`${it.action}: ${it.title}`}
                  onClick={() => (it.job === 'print' ? window.print() : save(it.job))}
                >
                  <span className="hig-button__label">{busy === it.job ? 'Preparing' : it.action}</span>
                </button>
              </li>
            ))}
          </ul>
          <p className="footnote rp-dl-foot" role="status" aria-live="polite">{status || (model ? 'Every file is made on this device. Nothing is uploaded.' : 'Preparing the report')}</p>
        </section>

        <h2 className="section__title rp-preview-title">Preview</h2>
      </div>

      <style>{previewThemeCss}</style>
      <div className="rp-sheet" ref={paper}>
        {failed && <p className="rp-noprint" role="alert">The report could not be built: {failed}</p>}
        {!failed && !model && <p className="rp-loading" role="status">Reading every site's breakdown from the engine</p>}
        {model && <ReportDocument m={model} />}
      </div>
    </div>
  );
}
