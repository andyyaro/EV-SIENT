// A status as a word with a shape beside it, so it never relies on color alone.
// Rows: Must Fix / Missing Values / Ready. Mapping: Matched / Check This Match / Not Matched.
// Results: Up to Date / Out of Date.

import { Icon } from './Icon';

export type StatusKind =
  | 'must_fix' | 'missing' | 'ready'
  | 'matched' | 'check' | 'unmatched'
  | 'fresh' | 'stale';

const LOOK: Record<StatusKind, { label: string; icon: string; tone: string }> = {
  must_fix: { label: 'Must Fix', icon: 'exclamationmark.triangle', tone: 'red' },
  missing: { label: 'Missing Values', icon: 'minus', tone: 'orange' },
  ready: { label: 'Ready', icon: 'checkmark.circle.fill', tone: 'green' },
  matched: { label: 'Matched', icon: 'checkmark.circle.fill', tone: 'green' },
  check: { label: 'Check This Match', icon: 'questionmark.circle', tone: 'orange' },
  unmatched: { label: 'Not Matched', icon: 'circle', tone: 'gray' },
  fresh: { label: 'Up to Date', icon: 'checkmark.circle.fill', tone: 'green' },
  stale: { label: 'Out of Date', icon: 'clock', tone: 'orange' },
};

export function statusLabel(kind: StatusKind): string {
  return LOOK[kind].label;
}

export function StatusMark({ kind, label }: { kind: StatusKind; label?: string }) {
  const look = LOOK[kind];
  return (
    <span className={`st-status st-status--${look.tone}`}>
      <Icon name={look.icon} size={16} strokeWidth={2} className="st-status__icon" />
      <span>{label ?? look.label}</span>
    </span>
  );
}
