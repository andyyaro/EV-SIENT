// Messages across the top of the content: errors (role=alert), plain notices (role=status) and the
// Out of Date line, which appears on every step once inputs change after a run.

import type { ReactNode } from 'react';
import { Icon } from './Icon';

interface Props {
  tone: 'error' | 'info' | 'stale';
  title?: string;
  children: ReactNode;
  onDismiss?: () => void;
  action?: ReactNode;
}

export function Banner({ tone, title, children, onDismiss, action }: Props) {
  const icon = tone === 'error' ? 'exclamationmark.triangle' : tone === 'stale' ? 'clock' : 'info.circle';
  return (
    <div className={`st-banner st-banner--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon name={icon} size={20} strokeWidth={1.9} className="st-banner__icon" />
      <div className="st-banner__body">
        {title && <p className="st-banner__title">{title}</p>}
        <div className="st-banner__text">{children}</div>
        {action && <div className="st-banner__action">{action}</div>}
      </div>
      {onDismiss && (
        <button type="button" className="st-banner__close hig-focus" onClick={onDismiss} aria-label="Dismiss">
          <Icon name="xmark" size={16} strokeWidth={2} />
        </button>
      )}
    </div>
  );
}
