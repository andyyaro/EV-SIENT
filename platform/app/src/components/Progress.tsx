// A progress bar with its words. Determinate when a fraction is known, otherwise a sweep.

interface Props {
  label: string;
  /** 0..1, or undefined when the work has no measurable progress. */
  fraction?: number;
  detail?: string;
}

export function Progress({ label, fraction, detail }: Props) {
  const known = typeof fraction === 'number' && Number.isFinite(fraction);
  const pct = known ? Math.round(Math.max(0, Math.min(1, fraction!)) * 100) : undefined;
  return (
    <div className="st-progress hig-progress hig-progress--ios hig-progress--bar hig-progress--labeled">
      <div className="st-progress__row">
        <span className="st-progress__label">{label}</span>
        {known && <span className="st-progress__pct num" aria-hidden="true">{pct}%</span>}
      </div>
      <span
        className="hig-progress__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={known ? 0 : undefined}
        aria-valuemax={known ? 100 : undefined}
        aria-valuenow={pct}
      >
        {known
          ? <span className="hig-progress__fill" style={{ width: `${pct}%` }} />
          : <span className="hig-progress__fill hig-progress__fill--indeterminate" />}
      </span>
      {detail && <span className="st-progress__detail">{detail}</span>}
    </div>
  );
}
