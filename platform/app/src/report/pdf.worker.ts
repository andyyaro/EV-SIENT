// The PDF maker: Typst compiled to WebAssembly, in its own module worker so a long report never
// freezes the page. Started only when the planner asks for a PDF, and kept for the next one.
//
// Everything it loads is the app's own: the compiler's wasm, the report template and the fonts
// are build assets on the app's origin. No package registry and no font CDN are ever contacted:
// the compiler has no package access at all, so `#import "@preview/..."` fails rather than fetching.

import * as Comlink from 'comlink';
import initCompiler, { TypstCompilerBuilder, type TypstCompiler } from '@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler.mjs';
import wasmUrl from '@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler_bg.wasm?url';
import template from './report.typ?raw';
import sansRegular from 'source-sans/OTF/SourceSans3-Regular.otf?url';
import sansItalic from 'source-sans/OTF/SourceSans3-It.otf?url';
import sansSemibold from 'source-sans/OTF/SourceSans3-Semibold.otf?url';
import sansBold from 'source-sans/OTF/SourceSans3-Bold.otf?url';
import monoRegular from 'source-code-pro/OTF/SourceCodePro-Regular.otf?url';

const FONTS = [sansRegular, sansItalic, sansSemibold, sansBold, monoRegular];

let compiler: Promise<TypstCompiler> | null = null;

async function bytes(url: string): Promise<Uint8Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (HTTP ${res.status}).`);
  return new Uint8Array(await res.arrayBuffer());
}

async function start(): Promise<TypstCompiler> {
  await initCompiler({ module_or_path: wasmUrl });
  const builder = new TypstCompilerBuilder();
  builder.set_dummy_access_model();
  for (const font of await Promise.all(FONTS.map(bytes))) await builder.add_raw_font(font);
  const c = await builder.build();
  c.add_source('/report.typ', template);
  return c;
}

/** Typst's diagnostics as one readable line each. */
function describe(diagnostics: unknown): string {
  if (!Array.isArray(diagnostics)) return String(diagnostics);
  return diagnostics.map((d) => (typeof d === 'object' && d ? `${(d as { severity?: string }).severity ?? 'error'}: ${(d as { message?: string }).message ?? JSON.stringify(d)}` : String(d))).join('\n');
}

const api = {
  /** The report JSON (reportBlocks.ts) in, the PDF's bytes out. */
  async pdf(json: string): Promise<Uint8Array> {
    if (!compiler) {
      compiler = start();
      compiler.catch(() => { compiler = null; });
    }
    const c = await compiler;
    c.map_shadow('/report.json', new TextEncoder().encode(json));
    try {
      const out = c.compile('/report.typ', null, 'pdf', 1) as { result?: Uint8Array; diagnostics?: unknown };
      if (!out.result) throw new Error(`The PDF could not be laid out.\n${describe(out.diagnostics)}`);
      return Comlink.transfer(out.result, [out.result.buffer]);
    } finally {
      c.unmap_shadow('/report.json');
    }
  },
};

export type PdfWorkerApi = typeof api;

Comlink.expose(api);
