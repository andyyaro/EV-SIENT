// HIG Native glyphs as React elements (the same drawing rules as the site's app.js icon()).

import { ICONS, RTL_FLIP } from '../lib/glyphs';

// Glyphs the public site adds on top of the design system's set.
ICONS['chart.bar'] = [['path', { d: 'M5 20V12M10 20V6M15 20v-9M20 20V9' }], ['path', { d: 'M3 20.5h18', sw: 0.8 }]];
ICONS['bolt'] = [['path', { d: 'M13.5 3L5.5 13.5h6l-1 7.5 8-10.5h-6z' }]];
ICONS['map'] = [['path', { d: 'M3.5 6.5l5.5-2.5 6 2.5 5.5-2.5v13.5l-5.5 2.5-6-2.5-5.5 2.5z' }], ['path', { d: 'M9 4v13.5M15 6.5V20' }]];
ICONS['bubble'] = [['path', { d: 'M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8.5a1.5 1.5 0 0 1-1.5 1.5H10l-4.5 3.5V17H5A1.5 1.5 0 0 1 3.5 15.5V7A1.5 1.5 0 0 1 5 5.5z' }]];

interface Props {
  name: string;
  size?: number | string;
  strokeWidth?: number;
  /** Give a title only when the icon carries meaning on its own; otherwise it is hidden from assistive tech. */
  title?: string;
  className?: string;
}

export function Icon({ name, size = 20, strokeWidth = 1.8, title, className }: Props) {
  const shapes = ICONS[name];
  if (!shapes) return null;
  return (
    <svg
      className={'hig-icon' + (className ? ' ' + className : '')}
      viewBox="0 0 24 24" width={size} height={size} focusable="false"
      {...(title ? { role: 'img', 'aria-label': title } : { 'aria-hidden': true })}
      {...(RTL_FLIP.has(name) ? { 'data-rtl-flip': '' } : {})}
    >
      {shapes.map(([tag, a], i) => {
        const { fill, sw, knock, ...rest } = a as Record<string, string | number>;
        if (knock) return null;
        const Tag = tag as 'path';
        return fill
          ? <Tag key={i} {...rest} fill="currentColor" stroke="none" />
          : <Tag key={i} {...rest} fill="none" stroke="currentColor"
              strokeWidth={sw ? strokeWidth * Number(sw) : strokeWidth} strokeLinecap="round" strokeLinejoin="round" />;
      })}
    </svg>
  );
}
