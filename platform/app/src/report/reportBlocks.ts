// The report as plain blocks (headings, paragraphs, lists, tables, a figure) for the PDF and Word
// downloads. They are read from the rendered report (ReportDocument), the markup the preview, the
// printout and the .html file already show, so every format carries the same words and the same
// engine numbers, and none of them formats or computes anything of its own.
//
// Colors come from the report's own light tokens as the browser resolved them, flattened onto the
// white page, so the PDF matches the preview without copying a palette.

import type { TierKey } from '../results/format';
import type { ReportModel } from './reportModel';

export type Inline =
  | { t: 'text'; s: string; bold?: boolean }
  | { t: 'link'; s: string; to: string }
  | { t: 'br' }
  /** A tier with its shape mark (circle, square, bar, diamond or triangle), as in the preview. */
  | { t: 'tier'; s: string; shape: TierKey; color: string }
  /** A decorative bar: track and fill as fractions of the full width. */
  | { t: 'bar'; track: number; fill: number; absent: boolean; color: string; trackColor: string; edge: string };

export type ParaStyle = 'body' | 'eyebrow' | 'meta' | 'lead' | 'note' | 'callout' | 'claims';

export interface Cell { c: Inline[]; th: boolean; num: boolean; bold: boolean; mono: boolean; span: number }

export interface TableGroup { label: Cell | null; rows: Cell[][] }

export type Block =
  | { b: 'heading'; level: number; id: string; s: string; outlined: boolean }
  | { b: 'para'; style: ParaStyle; c: Inline[] }
  | { b: 'list'; ordered: boolean; items: Inline[][] }
  | { b: 'terms'; style: 'totals' | 'plain'; items: { term: Inline[]; desc: Inline[] }[] }
  | { b: 'table'; caption: Inline[]; compact: boolean; head: Cell[]; groups: TableGroup[] }
  | { b: 'figure'; svg: string; alt: string; caption: Inline[]; width: number; height: number }
  | { b: 'contents'; title: string; items: { to: string; s: string }[] }
  | { b: 'group'; style: 'cover' | 'panel' | 'columns' | 'profile' | 'plain'; c: Block[] };

export interface Theme { text: string; secondary: string; separator: string; link: string; soft: string }

export interface ReportBlocks {
  title: string;
  lang: string;
  place: string;
  /** Who made the file, for the document properties. */
  creator: string;
  theme: Theme;
  blocks: Block[];
  /** Every heading ID, so a link is made only to a heading that exists. */
  anchors: string[];
}

/** The fonts the PDF embeds, named once for the Typst template and the plot's SVG. */
export const PDF_FONT = 'Source Sans 3';

const PARA_STYLE: Record<string, ParaStyle> = {
  'rp-eyebrow': 'eyebrow', 'rp-meta': 'meta', 'rp-lead': 'lead', 'rp-note': 'note', 'rp-callout': 'callout',
  'rp-claims': 'claims', 'rp-profile__meta': 'meta',
};

const GROUP_STYLE: Record<string, 'cover' | 'panel' | 'columns' | 'profile'> = {
  'rp-cover': 'cover', 'rp-decision': 'panel', 'rp-cols': 'columns', 'rp-profile': 'profile',
};

// ---------- Colors ----------

/** A computed CSS color as opaque #rrggbb, laid over the white page. */
function hex(css: string, fallback: string): string {
  const m = css.match(/^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/);
  if (!m) return fallback;
  const a = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]);
  const ch = (v: string) => Math.round(parseFloat(v) * a + 255 * (1 - a)).toString(16).padStart(2, '0');
  return `#${ch(m[1])}${ch(m[2])}${ch(m[3])}`;
}

function themeOf(article: HTMLElement): Theme {
  const style = (sel: string) => {
    const el = article.querySelector(sel);
    return el ? getComputedStyle(el) : null;
  };
  return {
    text: hex(getComputedStyle(article).color, '#000000'),
    secondary: hex(style('.rp-eyebrow')?.color ?? '', '#6c6c70'),
    separator: hex(style('.rp-h2')?.borderBottomColor ?? '', '#c6c6c8'),
    link: hex(style('.rp-toc a')?.color ?? '', '#0068da'),
    soft: hex(style('.rp-claims')?.backgroundColor ?? '', '#fafafa'),
  };
}

// ---------- Inline content ----------

const isHidden = (el: Element) => el.getAttribute('aria-hidden') === 'true';

function tierInline(el: Element): Inline {
  const mark = el.querySelector('.rp-tier__mark');
  const shape = ([...el.classList].find((c) => c.startsWith('rp-tier--'))?.slice('rp-tier--'.length) ?? 'other') as TierKey;
  return { t: 'tier', s: (el.textContent ?? '').trim(), shape, color: hex(mark ? getComputedStyle(mark).backgroundColor : '', '#8e8e93') };
}

function barInline(svg: SVGSVGElement): Inline {
  const W = svg.viewBox.baseVal?.width || 96;
  const track = svg.querySelector('.rp-bar__track');
  const fill = svg.querySelector('.rp-bar__fill');
  const width = (r: Element | null) => (r ? Math.min(1, (Number(r.getAttribute('width')) + 1) / W) : 0);
  return {
    t: 'bar',
    track: width(track),
    fill: width(fill),
    absent: !!track?.classList.contains('rp-bar__track--absent'),
    color: hex(fill ? getComputedStyle(fill).fill : '', '#0068da'),
    trackColor: hex(track ? getComputedStyle(track).fill : '', '#f6f6f7'),
    edge: hex(track ? getComputedStyle(track).stroke : '', '#c4c4c7'),
  };
}

function inlines(root: Element): Inline[] {
  const out: Inline[] = [];
  const walk = (node: Node, bold: boolean) => {
    if (node.nodeType === Node.TEXT_NODE) {
      out.push({ t: 'text', s: node.textContent ?? '', ...(bold ? { bold } : {}) });
      return;
    }
    if (!(node instanceof Element)) return;
    if (node.classList.contains('rp-tier')) { out.push(tierInline(node)); return; }
    if (node instanceof SVGSVGElement && node.classList.contains('rp-bar')) { out.push(barInline(node)); return; }
    if (isHidden(node)) return;
    const tag = node.tagName.toLowerCase();
    if (tag === 'br') { out.push({ t: 'br' }); return; }
    if (tag === 'a' && node.getAttribute('href')?.startsWith('#')) {
      out.push({ t: 'link', s: node.textContent ?? '', to: node.getAttribute('href')!.slice(1) });
      return;
    }
    // A span laid out as its own line (a site's ID under its name) starts a new line.
    if (out.length && getComputedStyle(node).display === 'block') out.push({ t: 'br' });
    const strong = bold || tag === 'strong' || tag === 'b';
    node.childNodes.forEach((c) => walk(c, strong));
  };
  root.childNodes.forEach((c) => walk(c, false));
  return tidy(out);
}

/** Collapse white space as HTML does, trim each line's ends and merge neighbouring text runs. */
function tidy(raw: Inline[]): Inline[] {
  const out: Inline[] = [];
  for (const it of raw) {
    if (it.t !== 'text') { out.push(it); continue; }
    const s = it.s.replace(/\s+/g, ' ');
    const prev = out[out.length - 1];
    if (prev?.t === 'text' && !!prev.bold === !!it.bold) prev.s += s;
    else out.push({ ...it, s });
  }
  for (let i = 0; i < out.length; i++) {
    const it = out[i];
    if (it.t !== 'text') continue;
    const before = out[i - 1], after = out[i + 1];
    if (!before || before.t === 'br') it.s = it.s.replace(/^ /, '');
    if (!after || after.t === 'br') it.s = it.s.replace(/ $/, '');
    if (before?.t === 'text' && before.s.endsWith(' ')) it.s = it.s.replace(/^ /, '');
  }
  return out.filter((it) => it.t !== 'text' || it.s !== '');
}

const textOf = (el: Element) => (el.textContent ?? '').replace(/\s+/g, ' ').trim();

// ---------- Blocks ----------

function cellOf(el: HTMLTableCellElement): Cell {
  const cls = el.classList;
  return {
    c: inlines(el),
    th: el.tagName === 'TH',
    num: cls.contains('rp-num'),
    bold: cls.contains('rp-strong'),
    mono: cls.contains('rp-mono'),
    span: el.colSpan || 1,
  };
}

function tableOf(table: HTMLTableElement): Block {
  const head = table.tHead ? [...table.tHead.rows[0].cells].map(cellOf) : [];
  const groups: TableGroup[] = [...table.tBodies].map((body) => {
    const rows = [...body.rows];
    const first = rows[0]?.cells[0];
    const label = first && first.getAttribute('scope') === 'rowgroup' ? cellOf(first) : null;
    return { label, rows: (label ? rows.slice(1) : rows).map((r) => [...r.cells].map(cellOf)) };
  });
  return {
    b: 'table',
    caption: table.caption ? inlines(table.caption) : [],
    compact: table.classList.contains('rp-table--compact'),
    head,
    groups,
  };
}

/** The plot as a standalone SVG: the stylesheet's colors and sizes written onto each element. */
function standaloneSvg(svg: SVGSVGElement): string {
  const copy = svg.cloneNode(true) as SVGSVGElement;
  const from = [svg, ...svg.querySelectorAll('*')];
  const to = [copy, ...copy.querySelectorAll('*')];
  from.forEach((el, i) => {
    const cs = getComputedStyle(el);
    const target = to[i];
    if (el.tagName.toLowerCase() === 'text') {
      target.setAttribute('font-family', `'${PDF_FONT}', -apple-system, Helvetica, Arial, sans-serif`);
      target.setAttribute('font-size', cs.fontSize);
      target.setAttribute('font-weight', cs.fontWeight);
    }
    if (el !== svg) {
      target.setAttribute('fill', cs.fill === 'none' ? 'none' : hex(cs.fill, '#000000'));
      target.setAttribute('stroke', cs.stroke === 'none' ? 'none' : hex(cs.stroke, '#000000'));
      target.setAttribute('stroke-width', cs.strokeWidth);
    }
    target.removeAttribute('class');
  });
  copy.removeAttribute('role');
  copy.removeAttribute('aria-labelledby');
  copy.removeAttribute('focusable');
  copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  copy.setAttribute('width', String(svg.viewBox.baseVal.width));
  copy.setAttribute('height', String(svg.viewBox.baseVal.height));
  return new XMLSerializer().serializeToString(copy);
}

function figureOf(fig: HTMLElement): Block | null {
  const svg = fig.querySelector('svg');
  const cap = fig.querySelector('figcaption');
  if (!svg) return null;
  return {
    b: 'figure',
    svg: standaloneSvg(svg),
    alt: cap ? textOf(cap) : '',
    caption: cap ? inlines(cap) : [],
    width: svg.viewBox.baseVal.width,
    height: svg.viewBox.baseVal.height,
  };
}

function termsOf(dl: Element): Block {
  const items: { term: Inline[]; desc: Inline[] }[] = [];
  // Each term and its description, whether wrapped in a <div> (as the report writes them) or not.
  for (const holder of [dl, ...dl.querySelectorAll(':scope > div')]) {
    const dts = holder.querySelectorAll(':scope > dt');
    dts.forEach((dt) => {
      const dd = dt.nextElementSibling;
      items.push({ term: inlines(dt), desc: dd && dd.tagName === 'DD' ? inlines(dd) : [] });
    });
  }
  return { b: 'terms', style: dl.classList.contains('rp-totals') ? 'totals' : 'plain', items };
}

function blocksOf(parent: Element, out: Block[]): void {
  for (const el of parent.children) {
    if (isHidden(el)) continue;
    const tag = el.tagName.toLowerCase();
    const cls = el.classList;
    const groupStyle = [...cls].map((c) => GROUP_STYLE[c]).find(Boolean);
    if (/^h[1-6]$/.test(tag)) {
      out.push({ b: 'heading', level: Number(tag[1]), id: el.id, s: textOf(el), outlined: false });
    } else if (tag === 'p') {
      const style = [...cls].map((c) => PARA_STYLE[c]).find(Boolean) ?? 'body';
      out.push({ b: 'para', style, c: inlines(el) });
    } else if (tag === 'ul' || tag === 'ol') {
      out.push({ b: 'list', ordered: tag === 'ol', items: [...el.children].map((li) => inlines(li)) });
    } else if (tag === 'dl') {
      out.push(termsOf(el));
    } else if (tag === 'table') {
      out.push(tableOf(el as HTMLTableElement));
    } else if (tag === 'figure') {
      const fig = figureOf(el as HTMLElement);
      if (fig) out.push(fig);
    } else if (tag === 'nav') {
      const links = [...el.querySelectorAll('a[href^="#"]')];
      const title = el.querySelector('h1, h2, h3');
      out.push({ b: 'contents', title: title ? textOf(title) : 'Contents', items: links.map((a) => ({ to: a.getAttribute('href')!.slice(1), s: textOf(a) })) });
    } else if (groupStyle === 'columns') {
      const c = [...el.children].map((col): Block => {
        const inner: Block[] = [];
        blocksOf(col, inner);
        return { b: 'group', style: 'plain', c: inner };
      });
      out.push({ b: 'group', style: 'columns', c });
    } else if (groupStyle) {
      const inner: Block[] = [];
      blocksOf(el, inner);
      out.push({ b: 'group', style: groupStyle, c: inner });
    } else {
      blocksOf(el, out);
    }
  }
}

function headings(blocks: Block[]): Extract<Block, { b: 'heading' }>[] {
  return blocks.flatMap((b) => (b.b === 'heading' ? [b] : b.b === 'group' ? headings(b.c) : []));
}

export function reportBlocks(m: ReportModel, article: HTMLElement): ReportBlocks {
  const blocks: Block[] = [];
  blocksOf(article, blocks);
  // The headings the contents list links to (the numbered sections) are the ones it lists.
  const contents = blocks.find((b) => b.b === 'contents');
  const listed = new Set(contents?.b === 'contents' ? contents.items.map((i) => i.to) : []);
  const all = headings(blocks);
  for (const h of all) h.outlined = listed.has(h.id);
  const title = article.querySelector('.rp-eyebrow');
  return {
    title: `${title ? textOf(title) : 'EV Charging Site Readiness Report'}: ${m.place}`,
    lang: article.lang || document.documentElement.lang || 'en',
    place: m.place,
    creator: 'EV-SIENT Planner',
    theme: themeOf(article),
    blocks,
    anchors: all.map((h) => h.id).filter(Boolean),
  };
}

