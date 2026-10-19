// Start: begin a project, open a saved .evsient file, or try the invented Example City sample.
// The model starts loading on this device as soon as this screen shows, with honest progress.

import { useEffect, useRef, useState } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { FaqLink } from '../components/FaqLink';
import { LicencesLink } from '../components/LicencesLink';
import { PageHead } from '../components/PageHead';
import { Progress } from '../components/Progress';
import { PROJECT_EXTENSION, readProjectFile } from '../report/projectFile';
import { useSession } from '../state/store';
import { useUpload } from './uploadState';

function EngineStatus() {
  const boot = useSession((s) => s.boot);
  const bootEngine = useSession((s) => s.bootEngine);
  return (
    <section className="st-engine card" aria-labelledby="engine-title">
      <h2 id="engine-title" className="st-card-title">The Model on This Device</h2>
      <div className="st-engine__body" role="status" aria-live="polite">
        {boot.status === 'idle' && <p className="st-muted">Getting ready to load the model.</p>}
        {boot.status === 'booting' && (
          <Progress label={boot.progress.message} fraction={boot.progress.fraction} detail="This happens once per visit. You can carry on while it loads." />
        )}
        {boot.status === 'ready' && (
          <p className="st-engine__ready">
            <Icon name="checkmark.circle.fill" size={20} className="st-engine__ok" />
            <span>Ready. The model is loaded and runs here, in this browser tab.</span>
          </p>
        )}
        {boot.status === 'error' && (
          <div className="st-engine__failed">
            <p className="st-engine__ready">
              <Icon name="exclamationmark.triangle" size={20} className="st-engine__bad" />
              <span>The model could not be loaded.</span>
            </p>
            <p className="st-muted">{boot.message}</p>
          </div>
        )}
      </div>
      {boot.status === 'error' && (
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus st-engine__retry" onClick={() => void bootEngine()}>
          <Icon name="arrow.clockwise" size={17} />
          <span className="hig-button__label">Try Again</span>
        </button>
      )}
    </section>
  );
}

function DataPanel() {
  return (
    <section className="card st-data" aria-labelledby="data-title">
      <h2 id="data-title" className="st-card-title">Where Your Data Goes</h2>
      <ul className="st-bullets">
        <li><strong>Your file stays on this device.</strong> It is read in this browser tab and the model runs here too. Nothing you upload is sent anywhere.</li>
        <li><strong>Nothing is stored for later.</strong> Close the tab and the file and results are gone, unless you save a project file from the Report step.</li>
        <li><strong>The only other network use is optional.</strong> The map on the Results step loads background map tiles. The tile server sees which area the map shows, as with any web map, but never your file or your sites.</li>
      </ul>
    </section>
  );
}

interface ChoiceProps {
  icon: string;
  title: string;
  detail: string;
  onClick: () => void;
  disabled?: boolean;
  tag?: string;
}

function Choice({ icon, title, detail, onClick, disabled, tag }: ChoiceProps) {
  return (
    <li className="hig-list-row hig-list-row--leading hig-list-row--subtitle st-choice">
      <div className="hig-list-row__content">
        <span className="hig-list-row__symbol st-choice__icon" aria-hidden="true"><Icon name={icon} size={24} /></span>
        <span className="hig-list-row__body">
          <span className="hig-list-row__text">
            <button type="button" className="hig-list-row__action hig-list-row__title st-choice__title" onClick={onClick} disabled={disabled}>
              {title}
            </button>
            <span className="hig-list-row__subtitle">{detail}</span>
            {tag && <span className="st-tag">{tag}</span>}
          </span>
          <span className="hig-list-row__trailing">
            <span className="hig-list-row__chevron" aria-hidden="true"><Icon name="chevron.right" size={20} /></span>
          </span>
        </span>
      </div>
    </li>
  );
}

export function StartStep() {
  const s = useSession();
  const upload = useUpload();
  const fileInput = useRef<HTMLInputElement>(null);
  const [opening, setOpening] = useState(false);
  const [openError, setOpenError] = useState<string | null>(null);
  const [confirmNew, setConfirmNew] = useState(false);

  useEffect(() => { void useSession.getState().bootEngine(); }, []);

  const hasProject = !!s.table;

  async function startNew() {
    if (hasProject && !confirmNew) { setConfirmNew(true); return; }
    setConfirmNew(false);
    if (hasProject) await s.newProject();
    upload.clear();
    useSession.getState().go('upload');
  }

  async function trySample() {
    if (hasProject) await s.newProject();
    upload.clear();
    useSession.getState().go('upload');
    await useUpload.getState().loadSample();
  }

  async function openProject(file: File) {
    setOpenError(null);
    setOpening(true);
    try {
      const snapshot = await readProjectFile(file);
      upload.clear(false);
      await useSession.getState().restoreProject(snapshot);
    } catch (e) {
      setOpenError(e instanceof Error ? e.message : String(e));
    } finally {
      setOpening(false);
    }
  }

  const restoring = opening || s.busy === 'restore';

  return (
    <div className="page page--narrow st-page">
      <PageHead
        eyebrow="EV-SIENT Planner"
        title="Rank Your Candidate Charging Sites"
        lede="Bring a spreadsheet of the sites you are considering. The planner matches its columns, checks it with you, and runs the EV-SIENT model on this device."
      />

      {hasProject && (
        <div className="st-continue">
          <Banner tone="info" title="Your Project Is Still Open">
            <p>{s.table!.fileName}{s.run ? ', with results' : ''}.</p>
          </Banner>
          <button type="button" className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus" onClick={() => s.go(s.run ? 'results' : 'upload')}>
            <span className="hig-button__label">{s.run ? 'Back to Results' : 'Continue Your Project'}</span>
          </button>
        </div>
      )}

      <section className="section" aria-labelledby="choices-title">
        <h2 id="choices-title" className="section__title">How Would You Like to Begin?</h2>
        <div className="hig-list hig-list--ios hig-list--insetGrouped st-list">
          <div className="hig-list-section">
            <ul className="hig-list-section__rows">
              <Choice
                icon="plus.circle"
                title="Start a New Project"
                detail="Upload a CSV or Excel file of your sites. One row per site."
                onClick={() => void startNew()}
              />
              <Choice
                icon="folder"
                title="Open a Project File"
                detail={`Reopen a ${PROJECT_EXTENSION} file you saved earlier. The model runs again on this device.`}
                onClick={() => fileInput.current?.click()}
                disabled={opening}
              />
              <Choice
                icon="doc"
                title="Try the Example City Sample"
                detail="Six invented sites in a made-up city, to see how the planner works."
                tag="Invented data"
                onClick={() => void trySample()}
              />
            </ul>
          </div>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept={`${PROJECT_EXTENSION},application/zip`}
          className="hig-visually-hidden"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void openProject(f); }}
        />
        {confirmNew && (
          <div className="st-confirm" role="group" aria-labelledby="confirm-new-title">
            <p id="confirm-new-title" className="st-confirm__text">
              Starting a new project closes {s.table!.fileName}{s.run ? ' and its results' : ''}. Save a project file from the Report step first if you want to keep {s.run ? 'them' : 'it'}.
            </p>
            <div className="st-confirm__buttons">
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-button--destructive hig-focus" onClick={() => void startNew()}>Close It and Start New</button>
              <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => setConfirmNew(false)}>Cancel</button>
            </div>
          </div>
        )}
        <div role="status" aria-live="polite" className="st-inline-status">
          {(opening || restoring) && <Progress label="Opening the project and running the model again" />}
        </div>
        {openError && (
          <Banner tone="error" title="This Project File Cannot Be Opened" onDismiss={() => setOpenError(null)}>
            <p>{openError}</p>
          </Banner>
        )}
      </section>

      <div className="section grid st-start-panels">
        <DataPanel />
        <EngineStatus />
      </div>

      <p className="footnote st-smallprint">
        Planning support, not engineering advice. The planner and the EV-SIENT model are open source under the Apache License 2.0.{' '}
        <FaqLink /> · <LicencesLink />
      </p>
    </div>
  );
}
