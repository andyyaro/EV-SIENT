// A number box that lets the planner type freely ("0.", "-", an empty box) and reports a number,
// or undefined while the box is empty or not yet a number.

import { useEffect, useId, useState } from 'react';

interface Props {
  value: number | undefined;
  onChange(value: number | undefined): void;
  label: string;
  /** Shown inside an empty box, e.g. the observed value a blank stands for. */
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number | 'any';
  describedBy?: string;
  invalid?: boolean;
  className?: string;
  /** The label is drawn by the caller (visible elsewhere); this one is for assistive tech only. */
  hiddenLabel?: boolean;
}

const asText = (v: number | undefined) => (v === undefined ? '' : String(v));

export function NumberField({ value, onChange, label, placeholder, min, max, step = 'any', describedBy, invalid, className, hiddenLabel }: Props) {
  const [text, setText] = useState(asText(value));
  const id = useId();
  // Follow a value changed from outside (another control, a reset), but not one this box just set.
  useEffect(() => {
    const parsed = text.trim() === '' ? undefined : Number(text);
    if (parsed !== value && !(parsed !== undefined && Number.isNaN(parsed))) setText(asText(value));
  }, [value]);
  return (
    <div className={'yi-num' + (className ? ` ${className}` : '')}>
      <label htmlFor={id} className={hiddenLabel ? 'hig-visually-hidden' : 'yi-num__label'}>{label}</label>
      <input
        id={id}
        className="yi-num__input hig-focus"
        type="number"
        inputMode="decimal"
        value={text}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        aria-describedby={describedBy}
        aria-invalid={invalid || undefined}
        onChange={(e) => {
          const t = e.target.value;
          setText(t);
          const n = t.trim() === '' ? undefined : Number(t);
          onChange(n === undefined || Number.isNaN(n) ? undefined : n);
        }}
      />
    </div>
  );
}
