// The window: a floating glass sidebar of steps on wide screens, a compact step bar on narrow
// ones, and the current step's screen. Steps 1 to 4 behave as a wizard; Results and Report are
// a workspace the planner moves around in freely once a run exists.

import { useEffect } from 'react';
import { Icon } from './components/Icon';
import { STEPS, stepGate, useSession, type StepKey } from './state/store';
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
        <button type="button" className="nav-brand app-brand" onClick={() => s.go('start')}>
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
            return (
              <li className="hig-sidebar__li" key={step.key}>
                <button
                  type="button"
                  className={'hig-sidebar__row hig-focus hig-pressable' + (current ? ' is-selected' : '')}
                  aria-current={current ? 'step' : undefined}
                  aria-disabled={!gate.open || undefined}
                  title={gate.open ? undefined : gate.reason}
                  onClick={() => s.go(step.key)}
                >
                  <span className="hig-sidebar__icon" aria-hidden="true"><Icon name={step.icon} size="1.15em" strokeWidth={1.6} /></span>
                  <span className="hig-sidebar__text">
                    <span className="hig-sidebar__label">{step.label}</span>
                    {!gate.open && <span className="app-steps__why">Cannot start yet</span>}
                  </span>
                  <span className="hig-visually-hidden">{`, step ${i + 1} of ${STEPS.length}`}</span>
                  {step.key === 'results' && s.staleReason && <span className="hig-sidebar__badge">Out of Date</span>}
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
    <header className="app-compact hig-glass hig-glass--small">
      <span className="app-compact__brand"><Icon name="bolt" size={18} strokeWidth={2} /> EV-SIENT</span>
      <label className="app-compact__step">
        <span className="hig-visually-hidden">Go to Step</span>
        <select value={s.step} onChange={(e) => s.go(e.target.value as StepKey)} className="hig-focus">
          {STEPS.map((step, i) => (
            <option key={step.key} value={step.key} disabled={!stepGate(s, step.key).open}>
              {`${i + 1}. ${step.label}`}
            </option>
          ))}
        </select>
        <Icon name="chevron.up.chevron.down" size={13} />
      </label>
      <span className="app-compact__count" aria-hidden="true">{`${index + 1} of ${STEPS.length}`}</span>
    </header>
  );
}

export function App() {
  const step = useSession((s) => s.step);
  const Screen = SCREENS[step];
  useEffect(() => {
    const label = STEPS.find((x) => x.key === step)?.label ?? '';
    document.title = `${label} · EV-SIENT Planner`;
    document.getElementById('main')?.focus({ preventScroll: true });
  }, [step]);
  return (
    <div className="shell app">
      <a className="skip-link" href="#main">Skip to Content</a>
      <StepNav />
      <CompactBar />
      <main id="main" className="main" tabIndex={-1}>
        <Screen />
      </main>
    </div>
  );
}
