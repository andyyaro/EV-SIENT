// Back and Continue at the foot of each wizard step. A disabled Continue always says why.

import { useId } from 'react';
import { Icon } from './Icon';

interface Props {
  onBack?: () => void;
  backLabel?: string;
  onNext?: () => void;
  nextLabel?: string;
  /** When set, Continue is disabled and this sentence explains what is needed first. */
  blockedReason?: string | null;
  busy?: boolean;
}

export function StepActions({ onBack, backLabel = 'Back', onNext, nextLabel = 'Continue', blockedReason, busy }: Props) {
  const reasonId = useId();
  const blocked = !!blockedReason;
  return (
    <div className="st-actions">
      {onBack && (
        <button type="button" className="hig-button hig-button--ios hig-button--large hig-button--bordered hig-focus st-actions__back" onClick={onBack}>
          <Icon name="chevron.left" size={17} strokeWidth={2.2} />
          <span className="hig-button__label">{backLabel}</span>
        </button>
      )}
      {onNext && (
        <div className="st-actions__next">
          <button
            type="button"
            className="hig-button hig-button--ios hig-button--large hig-button--bordered-prominent hig-focus"
            onClick={onNext}
            disabled={blocked || busy}
            aria-describedby={blocked ? reasonId : undefined}
          >
            <span className="hig-button__label">{nextLabel}</span>
            <Icon name="chevron.right" size={17} strokeWidth={2.2} />
          </button>
          {blocked && <p id={reasonId} className="st-actions__why">{blockedReason}</p>}
        </div>
      )}
    </div>
  );
}
