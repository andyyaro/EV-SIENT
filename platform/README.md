# EV-SIENT Planner (app.futurecity.andyyaro.com)

A browser app that lets a planner rank their own candidate EV charging sites with the EV-SIENT
model, without installing anything and without sending their file anywhere. The model is the
unmodified `fcf_m2` package from `src/`, running in the planner's browser under Pyodide in a
Web Worker. The plan this follows is the 2026-10-18 build plan (kept outside the repository).

## The flow

| Step | What the planner does | Engine call (`src/fcf_m2/browser_api.py`) |
|---|---|---|
| Start | New project, open a `.evsient` file, or try the Example City sample | `info`, `fields` |
| Upload | A CSV or Excel file; choose the sheet | `propose` |
| Map Columns | Confirm guesses and unit conversions, choose columns for unmatched fields | `remap` |
| Check | See which rows are ready, which have missing values, and anything that must be fixed | `check` |
| Run | One button | `accept`, then `run` |
| Results | Ranked sites, a map, why each site scores what it does, compare up to three | `explain`; `provenance` resolves one number's lineage when it is opened |
| Report | Download the report (HTML, tagged PDF, Word), the tables and the project file | `output_files` |

## Layout

| Path | What it is |
|---|---|
| `app/` | The static single-page app: React 19, Vite 8, TypeScript, styled with the HIG Native design system (the same tokens and components as `site/redesign/`) |
| `app/src/engine/protocol.ts` | The message protocol: every shape `browser_api.py` returns. Python is the source of truth |
| `app/src/engine/mock.ts` | An engine stand-in that answers from recorded Example City outputs, for interface work (`?engine=mock`) |
| `app/src/report/` | The report and its downloads. `ReportDocument.tsx` is the one source: the PDF and Word files are built from its rendered markup (`reportBlocks.ts`), the PDF by Typst in a worker (`report.typ`, `pdf.worker.ts`) |
| `app/public/samples/` | The invented Example City file and the blank template, from `data/intake/` |
| `app/public/manifest.webmanifest`, `app/public/icons/` | The install manifest and its icons (rendered from `icon.svg` by `tools/render_icons.py`) |
| `app/pwa/` | The service worker (`sw.js`) and the Vite plugin that writes it into `dist/` with the build's file lists and hashes |
| `app/public/runtime/` | Built, not committed: the pinned Pyodide subset and the engine archive (see `tools/`) |
| `tools/` | Runtime fetch, engine packaging, parity checks, deploy |
| `infra/` | Hosting configuration for app.futurecity.andyyaro.com |

## Rules the code keeps

- **Nothing the planner uploads leaves the device.** No analytics, no telemetry, no server
  calls with user rows. The only network requests are the app's own files and, on the
  Results map, basemap tiles.
- **The engine never runs without a cohort.** A run without one would read the reference
  study's private inputs (DEC-016), which the browser bundle does not contain.
- **Nothing is improved silently.** Intake's findings are shown before anything runs, and a
  mapping the planner chooses is recorded as a choice, not a source (DEC-021, DEC-023).
- **Provenance is resolved when asked, one cell at a time.** `provenance.resolve` finds its row
  through an index built once, so even a full `export_all` is linear: 9.0 s for 600 sites under
  Pyodide, where the per-cell mask took 466 s, with byte-identical output (a test pins it).
- **Every number on screen comes from the engine.** The interface explains with fixed wording
  filled from the engine's own numbers; it never computes a score itself.

## Checks before a release

| Command | What it proves |
|---|---|
| `node platform/tools/parity.mjs` | The browser engine and the native package give the same numbers (also in CI) |
| `python3 platform/tools/matrix.py <base-url> <out-dir>` | Every screen at 11 window sizes, light and dark: no sideways scroll, nothing covered, controls large enough |
| `python3 platform/tools/a11y_audit.py <base-url> <out-dir> --axe <axe.min.js>` | axe-core on every screen, in all four themes |
| `python3 platform/tools/browser_check.py` | The real engine boots and runs Example City in Chromium and WebKit |
| `python3 platform/tools/offline_check.py platform/app/dist` | Installable (manifest, icons, no Chromium installability errors), the service worker holds the shell and, after one run, the runtime stored decoded; then, with the server stopped, the whole flow runs again with the real engine, in Chromium and WebKit |

Both screen scripts walk the flow through `tools/planner_flow.py` and take `--mock` for the stand-in engine.

`npm run build` first runs `tools/build_licences.mjs`, which writes `public/licences.txt` (every
bundled package, the Pyodide runtime and its Python wheels, with their licence texts).

## Installing and working offline

The planner is an installable web app. `npm run build` writes `dist/sw.js` from `app/pwa/sw.js`, a
small hand-written service worker, with this build's file lists and their SHA-256 hashes. No new
dependency: the worker does four things and each one can be read in one file, where vite-plugin-pwa
would bring Workbox's runtime and build chain into the bundle and the licence notices for them.

| What | How |
|---|---|
| App shell | Installed with the worker: `index.html`, the hashed bundles, the files from `public/` and `runtime/engine/engine.json`, each checked against its build-time hash. A worker that arrives before its `index.html` (a deploy in progress) fails to install and the browser tries again later |
| Runtime | The Pyodide files and the engine archive are kept the first time the model loads (the page asks once it is ready), not at install, so a visitor who never runs the model is not sent 14 MB |
| Serving | Shell and runtime from the cache first; anything on another site (map tiles) is never touched |
| Brotli | CloudFront serves the largest files with `Content-Encoding: br`. The browser gives the worker decoded bytes, so each response is stored without its `Content-Encoding` and `Content-Length` |
| Updates | A new version installs in the background and waits. The app shows "Update Available" with a Reload button (warning that a reload closes an open project) and never reloads by itself. The old shell is deleted when the new one takes over |

`tools/deploy.sh` already serves `sw.js` and `*.webmanifest` as `no-cache` and the runtime as
immutable, and the existing Content Security Policy needs no change (`worker-src 'self'`; the
manifest falls under `default-src 'self'`). `tools/serve_csp.py --brotli` sends large files
Brotli-encoded the way CloudFront does, to test that case locally.
