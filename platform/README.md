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
| Results | Ranked sites, a map, why each site scores what it does, compare up to three | `explain` |
| Report | Download the report, tables and the project file | `output_files` |

## Layout

| Path | What it is |
|---|---|
| `app/` | The static single-page app: React 19, Vite 8, TypeScript, styled with the HIG Native design system (the same tokens and components as `site/redesign/`) |
| `app/src/engine/protocol.ts` | The message protocol: every shape `browser_api.py` returns. Python is the source of truth |
| `app/src/engine/mock.ts` | An engine stand-in that answers from recorded Example City outputs, for interface work (`?engine=mock`) |
| `app/public/samples/` | The invented Example City file and the blank template, from `data/intake/` |
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
- **Every number on screen comes from the engine.** The interface explains with fixed wording
  filled from the engine's own numbers; it never computes a score itself.
