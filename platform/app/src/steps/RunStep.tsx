// Run: what will run, one button, honest progress with Cancel, then Results.

import { useState, type ReactNode } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { Progress } from '../components/Progress';
import { StatusMark } from '../components/StatusMark';
import { StepActions } from '../components/StepActions';
import { plural } from '../lib/fieldText';
import { readableFileName } from '../lib/projectName';
import { CONFIGURATION, publicNeeds, stepGate, today, useSession } from '../state/store';

function Row({ title, children }: { title: string; children: ReactNode }) {
  return (
    <li className="hig-list-row hig-list-row--detail">
      <div className="hig-list-row__content">
        <span className="hig-list-row__body">
          <span className="hig-list-row__text"><span className="hig-list-row__title">{title}</span></span>
          <span className="hig-list-row__trailing"><span className="hig-list-row__detail">{children}</span></span>
        </span>
      </div>
    </li>
  );
}

export function RunStep() {
  const s = useSession();
  const gate = stepGate(s, 'run');
  const [started, setStarted] = useState(false);
  const running = s.busy === 'accept' || s.busy === 'run';

  if (!gate.open) {
    return (
      <div className="page page--narrow st-page">
        <PageHead title="Run" lede={gate.reason} />
        <StepActions onBack={() => s.go('check')} />
      </div>
    );
  }

  const check = s.check!;
  const p = s.proposal!;
  const total = s.fields?.fields.length ?? Object.keys(p.status).length;
  const matched = Object.keys(p.mapping).length;
  const d = s.details;
  const asOf = today();
  const back = () => s.go(Object.keys(publicNeeds(s)).length || s.publicFills.length ? 'fill' : 'check');
  const publicCells = s.publicFills.reduce((n, f) => n + Object.keys(f.values).length, 0);

  async function run() {
    setStarted(true);
    const before = useSession.getState().run;
    await useSession.getState().runModel({ asOf });
    const after = useSession.getState();
    setStarted(false);
    if (after.run && after.run !== before && !after.error) after.go('results');
  }

  return (
    <div className="page page--narrow st-page">
      <PageHead title="Run" lede="The model runs here, on this device. It takes a few seconds for most files." />

      {s.run && s.staleReason && (
        <Banner tone="stale" title="Out of Date">
          <p>{s.staleReason} Run again to update the results.</p>
        </Banner>
      )}
      {s.run && !s.staleReason && !running && (
        <div className="st-fresh"><StatusMark kind="fresh" /> <span className="st-muted">The results match these inputs.</span></div>
      )}

      <section className="section" aria-labelledby="what-title">
        <h2 id="what-title" className="section__title">What Will Run</h2>
        <div className="hig-list hig-list--ios hig-list--insetGrouped st-list">
          <div className="hig-list-section">
            <ul className="hig-list-section__rows">
              <Row title="File">{s.table?.fileName}</Row>
              <Row title="Sites"><span className="num">{check.counts.total.toLocaleString('en-US')}</span></Row>
              <Row title="Rows With Missing Values"><span className="num">{check.counts.missing.toLocaleString('en-US')}</span></Row>
              <Row title="Fields Matched"><span className="num">{matched} of {total}</span></Row>
              <Row title="Values From Public Data">
                {publicCells
                  ? <span className="num">{`${plural(publicCells, 'value')} in ${plural(s.publicFills.length, 'field')}`}</span>
                  : 'None'}
              </Row>
              <Row title="Configuration">{CONFIGURATION}</Row>
              <Row title="Data Confidence Judged On"><span className="num">{asOf}</span></Row>
            </ul>
            <div className="hig-list-section__footer">
              The model weighs demand, feasibility, safety and equity as the reference study did. Other configurations are not available yet.
            </div>
          </div>
          <div className="hig-list-section">
            <ul className="hig-list-section__rows">
              <Row title="Jurisdiction or Organisation">{d.jurisdiction || `Not given (${s.table ? readableFileName(s.table.fileName) : 'the file name'} is used)`}</Row>
              <Row title="Data Supplied By">{d.sourceOrg || 'Not given'}</Row>
              <Row title="Date of the Data">{d.sourceDate || 'Not given (lowers data confidence)'}</Row>
              <li className="hig-list-row hig-list-row--actionable">
                <div className="hig-list-row__content">
                  <span className="hig-list-row__body">
                    <span className="hig-list-row__text">
                      <button type="button" className="hig-list-row__action hig-list-row__title st-link-row" onClick={() => s.go('check')}>Change Source Details</button>
                    </span>
                    <span className="hig-list-row__trailing"><span className="hig-list-row__chevron" aria-hidden="true"><Icon name="chevron.right" size={20} /></span></span>
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section className="section st-run" aria-label="Run the model">
        {!running && (
          <button type="button" className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus st-run__button" onClick={() => void run()}>
            <Icon name="play.fill" size={17} />
            <span className="hig-button__label">{s.run ? 'Run the Model Again' : 'Run the Model'}</span>
          </button>
        )}
        <div role="status" aria-live="polite" className="st-run__status">
          {running && (
            <Progress
              label={s.busy === 'accept' ? 'Step 1 of 2: Preparing your sites for the model' : 'Step 2 of 2: Running the model'}
              detail={s.busy === 'accept' ? 'Applying your column matches and recording where each value came from.' : `Scoring ${plural(check.counts.total, 'site')} and sizing chargers.`}
            />
          )}
          {!running && started && 'Finished.'}
        </div>
        {running && (
          <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-button--destructive hig-focus" onClick={() => { s.cancelRun(); setStarted(false); }}>
            Cancel
          </button>
        )}
      </section>

      <StepActions
        onBack={back}
        onNext={s.run ? () => s.go('results') : undefined}
        nextLabel={s.staleReason ? 'See Earlier Results' : 'See Results'}
      />
    </div>
  );
}
