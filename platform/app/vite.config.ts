import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// A static single-page app: no server, no runtime CDN. The Python runtime and the engine
// archive are served from /runtime/ (see platform/tools/), never bundled.
//
// `vite build --mode engine-check --outDir dist-check` builds only engine-check.html, the
// dev-only harness platform/tools/browser_check.py drives; the production build never does.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
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
