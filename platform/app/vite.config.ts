import { fileURLToPath } from 'node:url';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { serviceWorker } from './pwa/plugin';

// A static single-page app: no server, no runtime CDN. The Python runtime and the engine
// archive are served from /runtime/ (see platform/tools/), never bundled.
//
// A production build also writes dist/sw.js, the service worker that makes the planner
// installable and usable offline (pwa/sw.js, filled in by pwa/plugin.ts).
//
// `vite build --mode engine-check --outDir dist-check` builds only engine-check.html, the
// dev-only harness platform/tools/browser_check.py drives; the production build never does.
export default defineConfig(({ mode }) => ({
  plugins: [react(), typstGlueWithoutEval(), serviceWorker(fileURLToPath(new URL('./pwa/sw.js', import.meta.url)))],
  base: '/',
  build: {
    target: 'es2022',
    sourcemap: true,
    assetsInlineLimit: 0,
    ...(mode === 'engine-check' ? { rolldownOptions: { input: { check: 'engine-check.html' } } } : {}),
  },
  worker: { format: 'es', plugins: () => [typstGlueWithoutEval()] },
  // Served as written, so the plugin below patches the glue in development too.
  optimizeDeps: { exclude: ['@myriaddreamin/typst-ts-web-compiler'] },
  server: { port: 5173 },
}));

// The Typst compiler's wasm-bindgen glue (@myriaddreamin/typst-ts-web-compiler 0.7.0) builds five
// fixed functions with `new Function(source)` when a compiler is built, which the app's CSP forbids
// (no 'unsafe-eval'). This swaps each for the same function written as a closure, and makes any
// other source throw. The build fails if the glue no longer has the two calls it expects, so an
// upgrade is checked by hand rather than silently allowed to need eval.
function typstGlueWithoutEval(): Plugin {
  const GLUE = /@myriaddreamin\/typst-ts-web-compiler\/pkg\/typst_ts_web_compiler\.mjs$/;
  const CALLS = [
    ['new Function(getStringFromWasm0(arg0, arg1))', '__evsientKnownFunction(getStringFromWasm0(arg0, arg1))'],
    ['new Function(getStringFromWasm0(arg0, arg1), getStringFromWasm0(arg2, arg3))', '__evsientKnownFunction(getStringFromWasm0(arg0, arg1), getStringFromWasm0(arg2, arg3))'],
  ];
  const KNOWN = `
const __evsientKnown = new Map([
  ['return 0', () => () => 0],
  ['return true', () => () => true],
  ['path\\u0000return path', () => (path) => path],
  ["throw new Error('Dummy AccessModel, please initialize compiler with withAccessModel()')", () => () => { throw new Error('Dummy AccessModel, please initialize compiler with withAccessModel()'); }],
  ["throw new Error('Dummy Registry, please initialize compiler with withPackageRegistry()')", () => () => { throw new Error('Dummy Registry, please initialize compiler with withPackageRegistry()'); }],
]);
function __evsientKnownFunction(...parts) {
  const make = __evsientKnown.get(parts.join('\\u0000'));
  if (!make) throw new Error('The Typst compiler asked to build a function from source, which this app does not allow: ' + JSON.stringify(parts));
  return make();
}
`;
  return {
    name: 'evsient-typst-glue-without-eval',
    enforce: 'pre',
    transform(code, id) {
      if (!GLUE.test(id.split('?')[0])) return null;
      let out = code;
      for (const [from, to] of CALLS) {
        if (out.split(from).length !== 2) throw new Error(`Typst glue changed: expected one "${from}" in ${id}. Check the new glue for eval before upgrading.`);
        out = out.replace(from, to);
      }
      if (/new Function|\beval\(/.test(out)) throw new Error(`Typst glue changed: ${id} still builds a function from source.`);
      return { code: out + KNOWN, map: null };
    },
  };
}
