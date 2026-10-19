import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
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
  plugins: [react(), serviceWorker(fileURLToPath(new URL('./pwa/sw.js', import.meta.url)))],
  base: '/',
  build: {
    target: 'es2022',
    sourcemap: true,
    assetsInlineLimit: 0,
    ...(mode === 'engine-check' ? { rolldownOptions: { input: { check: 'engine-check.html' } } } : {}),
  },
  worker: { format: 'es' },
  server: { port: 5173 },
}));
