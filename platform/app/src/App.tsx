// The window: a floating glass sidebar of steps on wide screens, a compact step bar on narrow
// ones, and the current step's screen. Steps 1 to 4 behave as a wizard; Results and Report are
// a workspace the planner moves around in freely once a run exists.

import { useEffect, useRef } from 'react';
import { Banner } from './components/Banner';
import { Icon } from './components/Icon';
import { STEPS, stepDone, stepGate, useSession, type StepKey } from './state/store';
import { StartStep } from './steps/StartStep';
import { UploadStep } from './steps/UploadStep';
import { MapStep } from './steps/MapStep';
import { CheckStep } from './steps/CheckStep';
import { RunStep } from './steps/RunStep';
import { ResultsView } from './results/ResultsView';
import { ReportView } from './report/ReportView';

const SCREENS: Record<StepKey, () => React.JSX.Element> = {
  start: StartStep, upload: UploadStep, map: MapStep, check: CheckStep, run: RunStep,
  results: ResultsView, report: ReportView,
};

function StepNav() {
  const s = useSession();
  return (
    <nav className="nav-sidebar hig-sidebar hig-sidebar--ios hig-sidebar--floating hig-glass hig-glass--regular" aria-label="Steps">
      <div className="hig-sidebar__top">
        <button type="button" className="nav-brand app-brand hig-focus" onClick={() => s.go('start')}>
          <span className="nav-brand__mark"><Icon name="bolt" size={22} strokeWidth={2} /></span>
          <span className="nav-brand__text">
            <span className="nav-brand__title">EV-SIENT</span>
            <span className="nav-brand__sub">Site Readiness Planner</span>
          </span>
        </button>
      </div>
      <div className="hig-sidebar__section">
        <ol className="hig-sidebar__list app-steps" role="list">
          {STEPS.map((step, i) => {
            const gate = stepGate(s, step.key);
            const current = s.step === step.key;
            const done = !current && gate.open && stepDone(s, step.key);
            const stale = (step.key === 'results' || step.key === 'report') && !!s.run && !!s.staleReason;
            return (
              <li className="hig-sidebar__li" key={step.key}>
                <button
                  type="button"
                  className={'hig-sidebar__row hig-focus hig-pressable' + (current ? ' is-selected' : '')}
                  aria-current={current ? 'step' : undefined}
                  aria-disabled={!gate.open || undefined}
                  onClick={() => s.go(step.key)}
                >
                  <span className="hig-sidebar__icon" aria-hidden="true"><Icon name={step.icon} size="1.15em" strokeWidth={1.6} /></span>
                  <span className="hig-sidebar__text">
                    <span className="hig-sidebar__label">{step.label}</span>
                    {!gate.open && <span className="app-steps__why">Cannot start yet</span>}
                    {stale && <span className="app-steps__why app-steps__why--stale">Out of Date</span>}
                  </span>
                  <span className="hig-visually-hidden">
                    {`, step ${i + 1} of ${STEPS.length}`}
                    {done ? ', done' : ''}
                    {!gate.open && gate.reason ? `. ${gate.reason}` : ''}
                  </span>
                  {done && <span className="app-steps__done" aria-hidden="true"><Icon name="checkmark" size={15} strokeWidth={2.4} /></span>}
                  {stale && <span className="app-steps__stale" aria-hidden="true"><Icon name="clock" size={15} strokeWidth={2} /></span>}
                </button>
              </li>
            );
          })}
        </ol>
      </div>
      <p className="nav-sidebar__foot">Your files stay on this device. Planning support, not engineering advice.</p>
    </nav>
  );
}

function CompactBar() {
  const s = useSession();
  const index = STEPS.findIndex((x) => x.key === s.step);
  return (
    <header className="app-compact hig-glass hig-glass--regular">
      <button type="button" className="app-compact__brand hig-focus" onClick={() => s.go('start')}>
        <span className="app-compact__mark"><Icon name="bolt" size={16} strokeWidth={2} /></span>
        <span>EV-SIENT</span>
      </button>
      <label className="app-compact__step">
        <span className="hig-visually-hidden">Go to Step</span>
        <select value={s.step} onChange={(e) => s.go(e.target.value as StepKey)} className="hig-focus">
          {STEPS.map((step, i) => {
            const gate = stepGate(s, step.key);
            const stale = (step.key === 'results' || step.key === 'report') && !!s.run && !!s.staleReason;
            const suffix = !gate.open ? ' (Cannot Start Yet)' : stale ? ' (Out of Date)' : '';
            return (
              <option key={step.key} value={step.key} disabled={!gate.open}>
                {`${i + 1}. ${step.label}${suffix}`}
              </option>
            );
          })}
        </select>
        <Icon name="chevron.up.chevron.down" size={13} />
      </label>
      <span className="app-compact__count num" aria-hidden="true">{`${index + 1} of ${STEPS.length}`}</span>
      <ol className="app-compact__dots" aria-hidden="true">
        {STEPS.map((step, i) => (
          <li key={step.key} className={i < index ? 'is-past' : i === index ? 'is-current' : ''} />
        ))}
      </ol>
    </header>
  );
}

function Messages() {
  const s = useSession();
  const showStale = !!s.run && !!s.staleReason && s.step !== 'run' && s.step !== 'start';
  const runOpen = stepGate(s, 'run').open;
  return (
    <div className="app-messages">
      {s.error && (
        <Banner tone="error" title="Something Went Wrong" onDismiss={s.clearError}>
          <p>{s.error}</p>
        </Banner>
      )}
      {s.notice && <Banner tone="info" onDismiss={s.clearNotice}><p>{s.notice}</p></Banner>}
      {showStale && (
        <Banner
          tone="stale"
          action={runOpen
            ? <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={() => s.go('run')}>Go to Run</button>
            : undefined}
        >
          <p><strong>Out of Date:</strong> {s.staleReason} Run again.</p>
        </Banner>
      )}
    </div>
  );
}

export function App() {
  const step = useSession((s) => s.step);
  const Screen = SCREENS[step];
  const shownStep = useRef(step);
  useEffect(() => {
    const label = STEPS.find((x) => x.key === step)?.label ?? '';
    document.title = `${label} · EV-SIENT Planner`;
    if (shownStep.current === step) return; // first paint: leave focus where the browser put it
    shownStep.current = step;
    // Move focus to the new screen's heading so keyboard and screen reader users start there.
    const heading = document.querySelector<HTMLElement>('#main h1');
    if (heading) {
      if (!heading.hasAttribute('tabindex')) heading.setAttribute('tabindex', '-1');
      heading.focus({ preventScroll: true });
    } else {
      document.getElementById('main')?.focus({ preventScroll: true });
    }
  }, [step]);
  return (
    <div className="shell app">
      <a className="skip-link" href="#main">Skip to Content</a>
      <StepNav />
      <CompactBar />
      <main id="main" className="main" tabIndex={-1}>
        <Messages />
        <Screen />
      </main>
    </div>
  );
}
