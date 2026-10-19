// The report as a Word document, built from the same blocks as the PDF (reportBlocks.ts). Loaded
// only when the planner asks for it, with the `docx` package it needs.
//
// Accessibility: real Heading 1 to 4 styles (Word's navigation pane and a screen reader's heading
// list), a repeating header row on every table, alt text on the plot, the document language and
// title set, and bookmarks so the contents list links to each section.

import {
  AlignmentType, Bookmark, BorderStyle, Document, Footer, HeadingLevel, ImageRun, InternalHyperlink, LevelFormat,
  Packer, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
  type ParagraphChild,
} from 'docx';
import type { Block, Cell, Inline, ReportBlocks } from './reportBlocks';

const FONT = 'Calibri';
const MONO = 'Consolas';
/** Half-points, as Word measures text. */
const SIZE = { body: 21, small: 17, table: 17, wideTable: 15, lead: 23 };
/** The tier marks in the preview, as characters Word can show. */
const TIER_GLYPH: Record<string, string> = { tier1: '●', tier2: '■', tier3: '▬', 'high-review': '◆', special: '▲', other: '■' };

const hex = (c: string) => c.replace(/^#/, '').toUpperCase();

/** Word bookmark names: letters, digits and underscores, starting with a letter, at most 40 characters. */
const bookmarkName = (id: string) => `b_${id.replace(/[^A-Za-z0-9]/g, '_')}`.slice(0, 40);

interface Ctx { r: ReportBlocks; anchors: Set<string>; images: Map<string, Uint8Array> }

function runs(c: Inline[], ctx: Ctx, o: { size?: number; color?: string; bold?: boolean; mono?: boolean } = {}): ParagraphChild[] {
  const base = { size: o.size, color: o.color ? hex(o.color) : undefined, font: o.mono ? MONO : undefined };
  const out: ParagraphChild[] = [];
  for (const i of c) {
    if (i.t === 'text') out.push(new TextRun({ ...base, text: i.s, bold: o.bold || i.bold }));
    else if (i.t === 'br') out.push(new TextRun({ ...base, break: 1 }));
    else if (i.t === 'tier') {
      out.push(new TextRun({ ...base, text: `${TIER_GLYPH[i.shape] ?? TIER_GLYPH.other} `, color: hex(i.color) }));
      out.push(new TextRun({ ...base, text: i.s, bold: o.bold }));
    } else if (i.t === 'link') {
      out.push(ctx.anchors.has(i.to)
        ? new InternalHyperlink({ anchor: bookmarkName(i.to), children: [new TextRun({ ...base, text: i.s, style: 'Hyperlink' })] })
        : new TextRun({ ...base, text: i.s }));
    }
    // Bars are decoration beside a number that is always written out; Word gets the number only.
  }
  return out;
}

const HEADINGS = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4, HeadingLevel.HEADING_5, HeadingLevel.HEADING_6];

function heading(b: Extract<Block, { b: 'heading' }>, ctx: Ctx, pageBreakBefore = false): Paragraph {
  const text = new TextRun(b.s);
  return new Paragraph({
    heading: HEADINGS[Math.min(b.level, 6) - 1],
    pageBreakBefore,
    keepNext: true,
    children: b.id && ctx.anchors.has(b.id) ? [new Bookmark({ id: bookmarkName(b.id), children: [text] })] : [text],
  });
}

function para(b: Extract<Block, { b: 'para' }>, ctx: Ctx): Paragraph {
  const { theme } = ctx.r;
  switch (b.style) {
    case 'eyebrow': return new Paragraph({ children: runs(b.c, ctx, { size: 24, color: theme.secondary, bold: true }), spacing: { after: 40 } });
    case 'meta':
    case 'note': return new Paragraph({ children: runs(b.c, ctx, { size: SIZE.small, color: theme.secondary }) });
    case 'lead': return new Paragraph({ children: runs(b.c, ctx, { size: SIZE.lead }) });
    case 'claims':
      return new Paragraph({
        children: runs(b.c, ctx),
        shading: { type: ShadingType.CLEAR, color: 'auto', fill: hex(theme.soft) },
        spacing: { before: 160, after: 160 },
      });
    case 'callout': {
      const edge = { style: BorderStyle.SINGLE, size: 4, color: hex(theme.separator), space: 4 };
      return new Paragraph({ children: runs(b.c, ctx), border: { top: edge, bottom: edge, left: edge, right: edge } });
    }
    default: return new Paragraph({ children: runs(b.c, ctx) });
  }
}

/** A column that holds only decoration (the driver bars) is left out of the Word table. */
function decorativeColumns(b: Extract<Block, { b: 'table' }>): Set<number> {
  const rows = b.groups.flatMap((g) => g.rows);
  const out = new Set<number>();
  b.head.forEach((_, x) => {
    if (rows.length && rows.every((r) => r[x] && r[x].span === 1 && r[x].c.every((i) => i.t === 'bar'))) out.add(x);
  });
  return out;
}

/** The page's text width in twips (US Letter less the margins set below). */
const TEXT_WIDTH = 12240 - 2 * 1152;

/**
 * Column widths in twips, sized as a browser sizes an auto-width table: each column's longest cell
 * when there is room, shrunk toward its longest word when there is not. Word reads the widths from
 * here; other readers lay a table out from this grid alone.
 */
function columnWidths(head: Cell[], rows: Cell[][], size: number): number[] {
  const perChar = size * 5.2; // an average character, in twips, at `size` half-points
  const pad = 200;
  const text = (c: Cell) => c.c.map((i) => (i.t === 'br' ? '\n' : 's' in i ? i.s : '')).join('');
  const column = (x: number) => [head[x], ...rows.map((r) => r[x])];
  const longest = (parts: string[]) => Math.max(0, ...parts.map((p) => p.length));
  const natural = head.map((_, x) => longest(column(x).flatMap((c) => text(c).split('\n'))) * perChar + pad);
  // Header words are bold, so they get a little more room.
  const least = head.map((_, x) => Math.max(
    longest(text(head[x]).split(/\s+/)) * perChar * 1.15,
    longest(rows.map((r) => r[x]).flatMap((c) => (c.num ? [text(c)] : text(c).split(/\s+/)))) * perChar,
  ) + pad);
  const sn = natural.reduce((a, b) => a + b, 0);
  const sm = least.reduce((a, b) => a + b, 0);
  let widths: number[];
  if (sn <= TEXT_WIDTH) {
    // Spare room goes to the text columns, as in the preview's full-width tables.
    const grow = head.map((h, x) => (h.num ? 0 : natural[x]));
    const base = grow.reduce((a, b) => a + b, 0);
    widths = natural.map((w, x) => w + (TEXT_WIDTH - sn) * (base ? grow[x] / base : w / sn));
  } else if (sm >= TEXT_WIDTH) {
    widths = least.map((w) => (w * TEXT_WIDTH) / sm);
  } else {
    widths = natural.map((w, x) => least[x] + ((w - least[x]) * (TEXT_WIDTH - sm)) / (sn - sm));
  }
  return widths.map(Math.round);
}

function table(b: Extract<Block, { b: 'table' }>, ctx: Ctx): (Paragraph | Table)[] {
  const { theme } = ctx.r;
  const skip = decorativeColumns(b);
  const n = b.head.length - skip.size;
  const size = b.head.length >= 10 ? SIZE.wideTable : SIZE.table;
  const line = { style: BorderStyle.SINGLE, size: 4, color: hex(theme.separator) };
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const cell = (c: Cell, head = false, span = c.span) => new TableCell({
    columnSpan: span > 1 ? span : undefined,
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    borders: { top: none, left: none, right: none, bottom: head ? { style: BorderStyle.SINGLE, size: 10, color: hex(theme.text) } : line },
    children: [new Paragraph({
      alignment: c.num ? AlignmentType.RIGHT : AlignmentType.LEFT,
      spacing: { before: 0, after: 0, line: 240 },
      children: runs(c.c, ctx, { size, bold: head || c.bold, mono: c.mono, color: head ? theme.secondary : undefined }),
    })],
  });
  const keep = <T,>(r: T[]) => r.filter((_, x) => !skip.has(x));
  const head = keep(b.head);
  const widths = columnWidths(head, b.groups.flatMap((g) => g.rows).filter((r) => r.length === b.head.length).map(keep), size);
  const rows: TableRow[] = [
    new TableRow({ tableHeader: true, cantSplit: true, children: head.map((h) => cell(h, true)) }),
  ];
  for (const g of b.groups) {
    if (g.label) rows.push(new TableRow({ cantSplit: true, children: [cell({ ...g.label, bold: true }, false, n)] }));
    for (const r of g.rows) rows.push(new TableRow({ cantSplit: true, children: keep(r).map((c) => cell(c)) }));
  }
  const out: (Paragraph | Table)[] = [];
  if (b.caption.length) out.push(new Paragraph({ style: 'Caption', keepNext: true, children: runs(b.caption, ctx, { size: SIZE.small, color: theme.secondary }) }));
  out.push(new Table({ rows, width: { size: TEXT_WIDTH, type: WidthType.DXA }, columnWidths: widths }));
  out.push(new Paragraph({ children: [], spacing: { after: 80 } }));
  return out;
}

function render(blocks: Block[], ctx: Ctx): (Paragraph | Table)[] {
  const out: (Paragraph | Table)[] = [];
  const firstProfile = blocks.findIndex((b) => b.b === 'group' && b.style === 'profile');
  blocks.forEach((b, k) => {
    if (b.b === 'heading') out.push(heading(b, ctx));
    else if (b.b === 'para') out.push(para(b, ctx));
    else if (b.b === 'list') {
      for (const item of b.items) {
        out.push(new Paragraph({ children: runs(item, ctx), ...(b.ordered ? { numbering: { reference: 'ordered', level: 0 } } : { bullet: { level: 0 } }) }));
      }
    } else if (b.b === 'terms') {
      for (const it of b.items) {
        out.push(new Paragraph({ children: [...runs(it.term, ctx, { color: ctx.r.theme.secondary }), new TextRun(': '), ...runs(it.desc, ctx, { bold: b.style === 'totals' })] }));
      }
    } else if (b.b === 'table') out.push(...table(b, ctx));
    else if (b.b === 'figure') {
      const png = ctx.images.get(b.svg);
      if (png) {
        const width = 600;
        out.push(new Paragraph({
          keepNext: true,
          children: [new ImageRun({
            type: 'png',
            data: png,
            transformation: { width, height: Math.round((width * b.height) / b.width) },
            altText: { name: 'Site locations', title: 'Site locations', description: b.alt },
          })],
        }));
      }
      out.push(new Paragraph({ style: 'Caption', children: runs(b.caption, ctx, { size: SIZE.small, color: ctx.r.theme.secondary }) }));
    } else if (b.b === 'contents') {
      out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun(b.title)] }));
      for (const i of b.items) {
        out.push(new Paragraph({ numbering: { reference: 'ordered', instance: 1, level: 0 }, children: runs([{ t: 'link', s: i.s.replace(/^\d+\.\s*/, ''), to: i.to }], ctx) }));
      }
    } else if (b.b === 'group') {
      const inner = render(b.c, ctx);
      // Each site profile starts on a new page, as in the printout.
      if (b.style === 'profile' && k !== firstProfile && inner[0] instanceof Paragraph) {
        const first = b.c[0];
        if (first?.b === 'heading') inner[0] = heading(first, ctx, true);
      }
      out.push(...inner);
    }
  });
  return out;
}

/** The plot's SVG drawn to a PNG at twice its size, since Word shows SVG only with a PNG beside it. */
async function svgToPng(svg: string, width: number, height: number): Promise<Uint8Array> {
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const canvas = document.createElement('canvas');
    canvas.width = width * 2;
    canvas.height = height * 2;
    const g = canvas.getContext('2d');
    if (!g) throw new Error('This browser cannot draw the site plot.');
    g.fillStyle = '#ffffff';
    g.fillRect(0, 0, canvas.width, canvas.height);
    g.drawImage(img, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('This browser cannot draw the site plot.');
    return new Uint8Array(await blob.arrayBuffer());
  } finally {
    URL.revokeObjectURL(url);
  }
}

function figures(blocks: Block[]): Extract<Block, { b: 'figure' }>[] {
  return blocks.flatMap((b) => (b.b === 'figure' ? [b] : b.b === 'group' ? figures(b.c) : []));
}

export async function docxBlob(r: ReportBlocks): Promise<Blob> {
  const images = new Map<string, Uint8Array>();
  for (const f of figures(r.blocks)) images.set(f.svg, await svgToPng(f.svg, f.width, f.height));
  const ctx: Ctx = { r, anchors: new Set(r.anchors), images };
  const lang = r.lang === 'en' ? 'en-US' : r.lang;
  const color = hex(r.theme.text);
  const headingStyle = (size: number, before: number) => ({
    run: { font: FONT, size, bold: true, color },
    paragraph: { spacing: { before, after: 120 }, keepNext: true },
  });
  const doc = new Document({
    title: r.title,
    creator: r.creator,
    description: `${r.title}. Made on the planner's own device from the EV-SIENT model's results.`,
    styles: {
      default: {
        document: { run: { font: FONT, size: SIZE.body, color, language: { value: lang } }, paragraph: { spacing: { after: 120, line: 264 } } },
        heading1: headingStyle(44, 0),
        heading2: headingStyle(30, 360),
        heading3: headingStyle(25, 280),
        heading4: headingStyle(21, 200),
        hyperlink: { run: { color: hex(r.theme.link), underline: {} } },
      },
      paragraphStyles: [
        { id: 'ReportFooter', name: 'Report Footer', basedOn: 'Normal', run: { size: 16, color: hex(r.theme.secondary) }, paragraph: { spacing: { after: 0 } } },
        { id: 'Caption', name: 'Caption', basedOn: 'Normal', next: 'Normal', run: { size: SIZE.small, color: hex(r.theme.secondary) }, paragraph: { spacing: { before: 120, after: 60 } } },
      ],
    },
    numbering: {
      config: [{ reference: 'ordered', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.START, style: { paragraph: { indent: { left: 360, hanging: 360 } } } }] }],
    },
    sections: [{
      properties: { page: { margin: { top: 1080, bottom: 1080, left: 1152, right: 1152 } } },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            style: 'ReportFooter',
            children: [
              new TextRun(`${r.title}    Page `),
              new TextRun({ children: [PageNumber.CURRENT] }),
              new TextRun(' of '),
              new TextRun({ children: [PageNumber.TOTAL_PAGES] }),
            ],
          })],
        }),
      },
      children: render(r.blocks, ctx),
    }],
  });
  return Packer.toBlob(doc);
}
