// Reports are always light. Rather than copy colors, this lifts the design system's own light
// (and light increased-contrast) token blocks out of tokens.css and scopes them: to `.rp` for the
// in-app preview, and to :root for the standalone .html download.

import tokensCss from '../styles/tokens.css?raw';
import reportCss from '../styles/report.css?raw';

function block(selector: string): string {
  const at = tokensCss.indexOf(`${selector} {`);
  if (at < 0) return '';
  const open = tokensCss.indexOf('{', at);
  const close = tokensCss.indexOf('}', open);
  return tokensCss.slice(open + 1, close);
}

const base = block(':root');
const light = block(':root[data-theme="light"]');
const lightHc = block(':root[data-theme="light-hc"]');

/** Light tokens on the preview's root element, so it reads as paper inside a dark window too. */
export const previewThemeCss =
  `.rp-sheet,.rp{${base}${light}color-scheme:light;}\n:root[data-theme$="-hc"] .rp-sheet,:root[data-theme$="-hc"] .rp{${lightHc}}`;

/** Everything the standalone file needs: light tokens, the report's styles and a page base. */
export const standaloneCss = [
  `:root{${base}${light}color-scheme:light;}`,
  `@media (prefers-contrast: more){:root{${lightHc}}}`,
  'html{-webkit-text-size-adjust:100%;text-size-adjust:100%;}*,*::before,*::after{box-sizing:border-box;}',
  'body{margin:0;background:var(--background-primary);color:var(--label-primary);font-family:var(--font-sans);-webkit-font-smoothing:antialiased;}',
  '.hig-visually-hidden{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0;}',
  reportCss,
].join('\n');
