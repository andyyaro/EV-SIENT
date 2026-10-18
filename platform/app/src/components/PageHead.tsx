// A screen's title. The heading takes focus when the screen changes (App.tsx), so a screen reader
// announces where the planner now is.

import type { ReactNode } from 'react';

interface Props {
  title: string;
  eyebrow?: string;
  lede?: ReactNode;
  children?: ReactNode;
}

export function PageHead({ title, eyebrow, lede, children }: Props) {
  return (
    <header className="page-head">
      {eyebrow && <span className="page-head__eyebrow">{eyebrow}</span>}
      <h1 className="page-head__title" tabIndex={-1}>{title}</h1>
      {lede && <p className="page-head__lede">{lede}</p>}
      {children}
    </header>
  );
}
