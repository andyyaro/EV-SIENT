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
| Map Columns | Confirm guesses and unit conversions, choose columns for unmatched fields; see how many scored fields the file provides | `remap` |
| Check | See which rows are ready, which have missing values, and anything that must be fixed | `check` |
| Public Data | Optional: look up public values for fields the file lacks, then use or skip each field (DEC-025) | `fill` |
| Run | One button | `accept`, then `run` |
| Results | Ranked sites, a map, why each site scores what it does, its score breakdown and how stable its rank is, compare up to three; the file's other columns as Your Columns (DEC-026) | `explain`; `stability` (docs/methodology/rank_stability.md); `provenance` resolves one number's lineage when it is opened |
| Explore | Descriptive patterns in the file's own columns, with how many were checked and passed; never part of the score (`docs/FLEXIBLE_ANALYSIS.md`) | `columns`, `columns_confirm`, `columns_restore`, `explore` |
| Your Index | The planner's own ranking, a weighted sum of columns they confirm, always labelled as theirs and never official | `index_validate`, `index_run` |
| Report | Download the report (HTML, tagged PDF, Word), the tables and the project file | `output_files` |

The Assistant, opened from any step, is optional: it sees the question and the step, and only the
summaries the planner agrees to share after seeing them (`docs/FLEXIBLE_ANALYSIS.md` section 5).

## Layout

| Path | What it is |
|---|---|
| `app/` | The static single-page app: React 19, Vite 8, TypeScript, styled with the HIG Native design system (the same tokens and components as `site/redesign/`) |
| `app/src/engine/protocol.ts` | The message protocol: every shape `browser_api.py` returns. Python is the source of truth |
| `app/src/engine/mock.ts` | An engine stand-in that answers from recorded Example City outputs, for interface work (`?engine=mock`) |
| `app/src/report/` | The report and its downloads. `ReportDocument.tsx` is the one source: the PDF and Word files are built from its rendered markup (`reportBlocks.ts`), the PDF by Typst in a worker (`report.typ`, `pdf.worker.ts`) |
| `app/src/hub/` | Reads the public data hub: fetches and checks county packs, works out each proposed value |
| `app/src/explore/`, `app/src/yourindex/`, `app/src/columns/` | Explore, Your Index and the column dictionary's cards |
| `app/src/assistant/` | The Assistant panel: consent, the payload preview, the answer |
| `app/public/samples/` | The invented Example City file and the blank template, from `data/intake/` |
| `app/public/manifest.webmanifest`, `app/public/icons/` | The install manifest and its icons (rendered from `icon.svg` by `tools/render_icons.py`) |
| `app/pwa/` | The service worker (`sw.js`) and the Vite plugin that writes it into `dist/` with the build's file lists and hashes |
| `app/public/runtime/` | Built, not committed: the pinned Pyodide subset and the engine archive (see `tools/`) |
| `hub/` | The public data hub builder: pinned public sources to per-county Parquet packs for six states (`hub/README.md`, DEC-028) |
| `assistant/` | The Assistant's proxy: a Lambda behind `/api/assistant/*`, OpenAI `gpt-5.4-mini` by default behind a provider switch, a hard $5 monthly spend cap (`assistant/README.md`, DEC-029 and its addendum) |
| `tools/` | Runtime fetch, engine packaging, parity checks, deploy |
| `infra/` | Hosting configuration for app.futurecity.andyyaro.com |

## Rules the code keeps

- **Nothing the planner uploads leaves the device.** No analytics, no telemetry, no server
  calls with user rows. The only network requests are the app's own files (including, when
  the planner asks, the public data packs for the counties around their sites), on the
  Results map, basemap tiles, and, only when the planner asks the Assistant, their question and
  any summaries they agree to share. Rows, cells, names and coordinates never leave.
- **The engine never runs without a cohort.** A run without one would read the reference
  study's private inputs (DEC-016), which the browser bundle does not contain.
- **Nothing is improved silently.** Intake's findings are shown before anything runs, and a
  mapping the planner chooses is recorded as a choice, not a source (DEC-021, DEC-023). A public
  value is used only for a field the planner accepts, only where the file has none, and is
  recorded as public data with its source and vintage (DEC-025).
- **The planner's other columns are carried, never scored (DEC-026).** Every column the model
  does not read is kept with its site by the exact site ID (`results/carried.ts`) and shown as
  written, labelled Not in the score, in Results (table columns to add, sort and filter, the
  site's card, Compare, map colours), the CSV and Excel downloads, the report's tenth section
  and the project file (`inputs/your_columns.json`, `evsient-project/3`; /1 and /2 still open).
  None of it is sent to the engine. Map Columns and Check say how many of the scored fields the
  file provides, and warn when fewer than half are there.
- **Site IDs stay text.** A cohort's `sites.csv` is read with its IDs as text, so "007" comes back
  from a run as "007", never 7.
- **Provenance is resolved when asked, one cell at a time.** `provenance.resolve` finds its row
  through an index built once, so even a full `export_all` is linear: 9.0 s for 600 sites under
  Pyodide, where the per-cell mask took 466 s, with byte-identical output (a test pins it).
- **Every score on screen comes from the engine.** The interface explains with fixed wording
  filled from the engine's own numbers; it never computes a score itself. The only numbers it
  works out are the public values it proposes, from the hub's packs, and each is shown with how
  it was worked out before the planner chooses it, and the order, filter and map colours the
  planner asks for from Your Columns.

## Checks before a release

| Command | What it proves |
|---|---|
| `node platform/tools/parity.mjs` | The browser engine and the native package give the same numbers (also in CI) |
| `python3 platform/tools/matrix.py <base-url> <out-dir>` | Every screen at 11 window sizes, light and dark: no sideways scroll, nothing covered, controls large enough, no console errors, no requests to other sites (in CI at three sizes) |
| `python3 platform/tools/a11y_audit.py <base-url> <out-dir> --axe <axe.min.js>` | axe-core on every screen, in all four themes, and the whole flow from Start to a downloaded report by keyboard alone (also in CI) |
| `python3 platform/tools/browser_check.py` | The real engine boots and runs Example City in Chromium and WebKit |
| `python3 platform/tools/wcag_checks.py` | The targeted WCAG checks behind the [Accessibility Conformance Report](../docs/accessibility/ACR.md) that axe-core and `matrix.py` do not make |
| `node --test "platform/assistant/test/*.test.mjs"` | The Assistant proxy: payload rules, the spend ledger, both providers |
| `python3 platform/tools/offline_check.py platform/app/dist` | Installable (manifest, icons, no Chromium installability errors), the service worker holds the shell and, after one run, the runtime stored decoded; then, with the server stopped, the whole flow runs again with the real engine, in Chromium and WebKit (also in CI) |

Both screen scripts walk the flow through `tools/planner_flow.py` and take `--mock` for the stand-in engine.
`a11y_audit.py`, `matrix.py` and `offline_check.py` exit non-zero on any finding and write their findings as JSON (`offline_check.py` with `--json`).

### The same checks as CI, on your machine

The `platform` job in `.github/workflows/tests.yml` runs those three after the app
build, with the real engine, against the build served under the production CSP. Any axe
violation, keyboard problem, failing layout check or offline problem fails the job, and the
findings and screenshots are then uploaded as the `planner-browser-checks` artifact. To run them
the way CI does (ports 5311 and 5312, as there):

```sh
pip install -r platform/tools/requirements-qa.txt     # Playwright 1.63.0, pinned
python -m playwright install --only-shell chromium webkit
curl -fsSL -o /tmp/axe-core.tgz https://registry.npmjs.org/axe-core/-/axe-core-4.13.0.tgz
tar -xzf /tmp/axe-core.tgz -C /tmp package/axe.min.js  # CI checks its SHA-256 first
(cd platform/app && npm run build)                     # after fetch_runtime.mjs and build_engine.py
python platform/tools/serve_csp.py platform/app/dist --port 5311 &
python platform/tools/a11y_audit.py http://127.0.0.1:5311 /tmp/qa/a11y --axe /tmp/package/axe.min.js --shots
python platform/tools/matrix.py http://127.0.0.1:5311 /tmp/qa/matrix --sizes 1440x900,390x844,320x640
python platform/tools/offline_check.py platform/app/dist --port 5312 --json /tmp/qa/offline.json
```

axe-core is not a dependency of the app; CI fetches the 4.13.0 tarball and checks its SHA-256.
The axe audit injects axe as a script, so it bypasses the CSP for that page only; matrix.py and
offline_check.py run under the real policy. CI leaves out `--map`, which needs the map tile host.
`offline_check.py` starts its own server with `--brotli` and needs the `brotli` command. On an
Apple-silicon laptop the three take about 2, 1.5 and 2 minutes.

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
