# Accessibility evidence: how to re-run every check

This folder holds the evidence behind [the Accessibility Conformance Report](../ACR.md): JSON
summaries of each check, no screenshots. Every file records the build commit it was made from
(`assessedCommit`). Re-run everything below after any change to `platform/app`, and in particular
after the Results stability section, the assistant panel and the multi-state public data work are
merged, then compare the new summaries with these and update the report.

## What is here

| File | Made by | What it covers |
|---|---|---|
| `axe-and-keyboard.json` | `platform/tools/a11y_audit.py` | axe-core 4.13.0 on every screen (Start, Upload, Map Columns, Check, Public Data, Run, Results with a site selected and two in Compare, Explore, Report), in Chromium and WebKit, at 1440x900 and 390x844, in light, dark, increased-contrast light and increased-contrast dark: 144 runs against WCAG 2.0, 2.1 and 2.2 A and AA rules plus axe's best practices. Then the whole flow from Start to a downloaded report by keyboard alone. Lists the items axe could not decide ("incomplete") and why |
| `layout-matrix.json` | `platform/tools/matrix.py` | Every screen at 11 window sizes from 320x640 to 1920x1080, portrait and landscape, light and dark, Chromium and WebKit (440 checks): no sideways scroll, no control covered, every control at least 24 by 24 px (2.5.8), primary controls at least 44 px tall, no console errors, no requests to other sites |
| `offline.json` | `platform/tools/offline_check.py` | Installable, and the whole flow runs again with the server stopped, in Chromium and WebKit. Not a WCAG check; kept because it was part of the same release run |
| `wcag-checks.json` | `platform/tools/wcag_checks.py` | The criteria automation misses, on every screen including Your Columns on Map Columns, Results with the map shown (markers by rank, and coloured by one of Your Columns) and Your Index (refused with six sites, and ranked with twelve): see the next table. With `--axe`, also axe-core on every one of those screens (four themes at 1440x900, light at 390x844), which covers the screens `a11y_audit.py` does not reach: Your Columns open, Your Index, Explore with twelve sites and Results with the map shown |
| `documents.json` | `platform/tools/wcag_checks.py` | The downloaded report as HTML, tagged PDF and Word: language, title, headings, tables and header cells, alternative text, the PDF's structure tree and reading order |
| `before-fixes.json` | `platform/tools/wcag_checks.py`, on the builds before this report's fixes (most before the first fix; the map credit's ring on `efcf54d`, just before its own fix) | The measurements the fixes changed, so the change can be checked |

`wcag_checks.py` covers, per screen:

| Check | WCAG | How |
|---|---|---|
| Headings, landmarks, page title, language | 1.3.1, 2.4.2, 2.4.6, 3.1.1 | Read from the page: every heading level and skip, every landmark and labelled section |
| Tables | 1.3.1 | Every table's caption or name, header cells, `scope`, empty cells |
| Names, states, images | 1.1.1, 4.1.2 | Controls with no accessible name, images and SVG without a name, the ARIA states in use |
| Label in name | 2.5.3 | Every control with `aria-label` or `aria-labelledby`: its visible text must be inside its name |
| Input purpose | 1.3.5 | Every field's `autocomplete` |
| Focus order and traps | 2.1.2, 2.4.3 | Tab from the top of the page to the end in all four themes at 1440x900, and at 390x844, 320x256 (1280x1024 at 400%) |
| Focus visible | 2.4.7, 1.4.11 | Each focused control's ring from computed styles and its contrast against what surrounds it, and in light and dark a screenshot of the control focused and not focused: how many pixels change by 3:1 or more |
| Focus not obscured | 2.4.11 | Nine points inside each focused control: is any of it covered by the compact step bar or anything else |
| Non-text contrast | 1.4.11 | From screenshots, in all four themes: the edge of every text field and menu, check boxes, radio buttons, sliders, bordered and filter buttons, tier marks, score bars, chart marks, map markers and map controls |
| Text contrast axe could not judge | 1.4.3 | From screenshots, in all four themes: the sidebar on its translucent background (including the current step), the compact step bar, the rank cells and the selected row of the ranked table, and the note under the report's site plot; placeholder text from computed styles |
| Text spacing | 1.4.12 | The WCAG text-spacing style injected at 1440x900 and 390x844: text cut off by its own box or an ancestor, compared with the page without it |
| Resize and reflow | 1.4.4, 1.4.10 | 1440x900 at 200% (720x450), 1280x1024 at 400% (320x256) and 320x640: page width, cut-off text, how much of the window fixed bars cover |
| Target size | 2.5.8 | Every control under 24 by 24 px, and whether the spacing exception holds |
| Content on hover or focus | 1.4.13 | Every style rule that reveals content on hover or focus, and every `title` tooltip |
| Status messages | 4.1.3 | Every change to a live region during the flow, beside the action that caused it |
| Errors | 3.3.1, 3.3.2, 3.3.3 | Files that cannot be read or run (binary, empty, headings only, plain text, repeated site IDs, impossible coordinates), a project file that is not one, the Site ID left unmatched, an empty Your Index name and equal ends of a scale: what is said, where, with which role, and whether the next step is blocked with the reason attached |
| Dialog | 2.1.2, 2.4.3 | Common Questions: focus moves in, never reaches the page behind, Escape closes, focus returns |
| Change on input | 3.2.2 | The compact step menu (below 1024 px wide) when its value changes |
| Map | 2.1.1, 2.1.2 | Tab leaves the map canvas; the markers are buttons. The map is also checked as two screens of its own (`results-map`, `results-map-colour`) with every per-screen check above |

## How to re-run

From the repository root, on macOS or Linux. The app is built and served exactly as CI does
(`.github/workflows/tests.yml`, job `platform`); see also `platform/README.md`.

```sh
# 1. Tools: a virtual environment with the model's packages, the QA pins and two readers
python3 -m venv venv
venv/bin/pip install -r requirements-lock.txt -r platform/tools/requirements-qa.txt
venv/bin/pip install pillow==12.0.0 pdfplumber==0.11.7    # wcag_checks.py only
venv/bin/python -m playwright install --only-shell chromium webkit
# pdfinfo (poppler) and brotli on the PATH: brew install poppler brotli

# 2. axe-core 4.13.0, checked against the SHA-256 CI uses
curl -fsSL -o /tmp/axe-core.tgz https://registry.npmjs.org/axe-core/-/axe-core-4.13.0.tgz
echo "096912f6e77b4b695fc9304b7be65091db42d98de054da674ae222a11cb33f70  /tmp/axe-core.tgz" | shasum -a 256 -c -
tar -xzf /tmp/axe-core.tgz -C /tmp package/axe.min.js

# 3. Build the runtime, the engine and the app
(cd platform/app && npm ci --ignore-scripts --no-audit --no-fund)
node platform/tools/fetch_runtime.mjs
venv/bin/python platform/tools/build_engine.py
(cd platform/app && npm run build)

# 4. Serve the build under the production Content Security Policy
python3 platform/tools/serve_csp.py platform/app/dist --port 5321 &

# 5. The checks (about 4, 3, 4 and 40 minutes on an Apple-silicon laptop). Run them one at a time:
#    run together, WebKit can time out loading the model and the run fails for that reason alone.
venv/bin/python platform/tools/a11y_audit.py http://127.0.0.1:5321 /tmp/qa/a11y --axe /tmp/package/axe.min.js
venv/bin/python platform/tools/matrix.py http://127.0.0.1:5321 /tmp/qa/matrix --no-shots
venv/bin/python platform/tools/offline_check.py platform/app/dist --port 5322 --json /tmp/qa/offline.json
venv/bin/python platform/tools/wcag_checks.py http://127.0.0.1:5321 /tmp/qa/wcag --axe /tmp/package/axe.min.js

# 6. The summaries in this folder
venv/bin/python platform/tools/a11y_evidence.py --a11y /tmp/qa/a11y/a11y.json \
  --matrix /tmp/qa/matrix/matrix.json --offline /tmp/qa/offline.json --wcag /tmp/qa/wcag/wcag.json \
  --commit "$(git rev-parse --short HEAD)" --out docs/accessibility/evidence
```

Notes:

- `a11y_audit.py` injects axe as a script, and `wcag_checks.py` adds its own style and script, so
  both open the page with the Content Security Policy bypassed for that page only. `matrix.py` and
  `offline_check.py` run under the real policy.
- `wcag_checks.py` shows the Results map, which loads basemap tiles from tiles.openfreemap.org. Pass
  `--no-map` to stay offline; the map's keyboard check is then skipped.
- `wcag_checks.py` reports; it does not fail. Read `wcag.json` (or the summary) and compare it with
  the report. The other three exit non-zero on any finding.
- Contrast from screenshots takes the most common colour around a control as its background and
  the strongest colour in it (or on its edge, for fields and buttons) as the control. It does not
  model a person's judgement of which part identifies the control; the report says where that
  judgement was made.

## What none of this covers

- **Screen readers.** No screen reader was run. VoiceOver can only be driven from a script on macOS
  after "Allow VoiceOver to be controlled with AppleScript" is turned on, which was not done on the
  machine used, and it would have taken over that machine's screen and sound. The checks above
  read names, roles, states and live regions from the page, which is what a screen reader is given,
  but not what each one then says. Test, at least: NVDA with Firefox and with Chrome on Windows,
  JAWS with Chrome or Edge on Windows, VoiceOver with Safari on macOS and on iOS, and TalkBack with
  Chrome on Android. The steps to follow are in the report's known issues.
- Windows High Contrast (forced colours), speech recognition (Dragon, Voice Control) and screen
  magnifiers.
- Firefox, which the planner does not test.
- People. No one with a disability has used the planner for this report.
