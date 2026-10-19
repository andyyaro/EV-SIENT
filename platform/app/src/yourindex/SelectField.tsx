// A labelled select whose name is only its label (the label is tied by id, not wrapped around the
// select, so a screen reader does not read the chosen option twice).

import { useId, type ReactNode } from 'react';
import { Icon } from '../components/Icon';

interface Props {
  label: string;
  value: string;
  onChange(value: string): void;
  children: ReactNode;
  hiddenLabel?: boolean;
  hint?: ReactNode;
  describedBy?: string;
  className?: string;
}

export function SelectField({ label, value, onChange, children, hiddenLabel, hint, describedBy, className }: Props) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const described = [describedBy, hintId].filter(Boolean).join(' ') || undefined;
  return (
    <div className={'yi-field' + (className ? ` ${className}` : '')}>
      <label htmlFor={id} className={hiddenLabel ? 'hig-visually-hidden' : 'yi-field__label'}>{label}</label>
      <span className="st-select">
        <select id={id} className="hig-focus" value={value} aria-describedby={described} onChange={(e) => onChange(e.target.value)}>
          {children}
        </select>
        <Icon name="chevron.up.chevron.down" size={13} />
      </span>
      {hint && <span className="yi-hint" id={hintId}>{hint}</span>}
    </div>
  );
}
