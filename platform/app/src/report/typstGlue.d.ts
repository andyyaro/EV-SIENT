// pdf.worker.ts imports the Typst compiler's glue directly, not the package's entry, which adds a
// Node-only loader built with `new Function`. The glue's types are the package's own.
declare module '@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler.mjs' {
  export * from '@myriaddreamin/typst-ts-web-compiler';
  export { default } from '@myriaddreamin/typst-ts-web-compiler';
}
