import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// A static single-page app: no server, no runtime CDN. The Python runtime and the engine
// archive are served from /runtime/ (see platform/tools/), never bundled.
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: { target: 'es2022', sourcemap: true, assetsInlineLimit: 0 },
  worker: { format: 'es' },
  server: { port: 5173 },
});
