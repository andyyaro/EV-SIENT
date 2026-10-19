# EV-SIENT Planner Accessibility Conformance Report

WCAG Edition, based on the ITI VPAT® 2.5 template

**This report is self-assessed by the project team, not independently audited.** No outside
accessibility specialist has reviewed the planner or this report, no screen reader was used to test
it, and no person with a disability has used it for this report. Read every "Supports" below as
"the project team's checks found no failure", with the evidence named in its remarks.

## Product information

| | |
|---|---|
| Name of product | EV-SIENT Planner (EV Charging Site Readiness Planner) |
| Version | App 0.1.0, engine 3.0.0 (the build's `runtime/engine/engine.json` reads `3.0.0+6333b56`) |
| Build assessed | Commit `5f87c8e` of this repository (branch `worktree-agent-a7adeada9dc600a37`), built with `npm run build` in `platform/app`. Later commits on the branch only add this report's text and evidence |
| Address | https://app.futurecity.andyyaro.com |
| Report date | 2026-10-18 |
| Product description | A planner that runs in the browser. A user uploads a spreadsheet of candidate sites, matches its columns, checks and fills the data, and runs a readiness model on their own device (Python in WebAssembly, in a Web Worker). Results come as a ranked table, a map, side-by-side comparison and an optional index of the user's own columns, and as a report to download in HTML, tagged PDF and Word |
| Contact information | andyyaro25@gmail.com |
| Notes | The planner is a single web app with ten screens: Start, Upload, Map Columns (with Your Columns), Check, Public Data, Run, Results (table, map and Compare), Explore, Your Index and Report. All of them, and the three downloads, are covered here. Other work on `platform/app` (a Results stability section, an assistant panel and multi-state public data) was under way when this report was written and is not covered; see "Re-testing after other changes" |
| Evaluation methods used | See the next section |

## Evaluation methods used

All testing was on the production build, served locally under the production Content Security
Policy (`platform/tools/serve_csp.py`), on macOS with Playwright 1.63.0, Chromium 153 and WebKit 26.6
(the Safari engine). The evidence is in [`evidence/`](evidence/), and
[`evidence/README.md`](evidence/README.md) says how to re-run every check.

1. **Automated rules.** axe-core 4.13.0 (the version and checksum CI pins), with the WCAG 2.0, 2.1
   and 2.2 A and AA rules and axe's best practices, on every screen, in Chromium and WebKit, at
   1440x900 and 390x844, in four colour themes: light, dark, increased-contrast light and
   increased-contrast dark (`platform/tools/a11y_audit.py`). axe also ran inside the per-screen
   checks below, on 14 screen states (the ten screens; Results with the map shown, and with its
   markers coloured by a column; and Your Index and Explore with a twelve-site file, so that the
   index ranks and the charts fill), in four themes at 1440x900 and in light at 390x844: 70 runs.
2. **Keyboard.** The whole flow, from Start to a downloaded report, by keyboard alone
   (`a11y_audit.py`); then on each screen, Tab from the top of the page to the end in all four
   themes and at three window sizes, recording every stop, its focus ring and whether anything
   covers it (`platform/tools/wcag_checks.py`).
3. **Layout.** Every screen at 11 window sizes from 320x640 to 1920x1080, portrait and landscape,
   light and dark, in both browsers (`platform/tools/matrix.py`); and zoom to 200% and 400% and
   the WCAG text-spacing values (`wcag_checks.py`).
4. **Targeted manual checks** written as scripts in `wcag_checks.py`, so they can be repeated:
   contrast of focus rings, field edges, check boxes, chart marks, map markers and other non-text
   content measured from screenshots in all four themes; hover and focus content; target size;
   label in name; input purpose; error messages for bad files and bad settings; status messages;
   the Common Questions dialog; change of context on the compact step menu.
5. **Generated documents.** The report downloaded as HTML, PDF and Word, read with pdfinfo,
   pdfplumber (the PDF structure tree in reading order) and the Word document's XML.
6. **Judgement.** Where a measurement falls below a threshold, a person looked at the screen and
   decided whether the criterion applies. Each such decision is named in the remarks.
7. **Not done.** No screen reader (VoiceOver could not be driven from a script on the test
   machine), no Windows High Contrast, no speech recognition or screen magnifier, no Firefox, no
   testing by people with disabilities.

## Applicable standards and guidelines

| Standard or guideline | Included in report |
|---|---|
| [Web Content Accessibility Guidelines 2.1](https://www.w3.org/TR/WCAG21/) | Level A (Yes), Level AA (Yes), Level AAA (No) |
| [Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/) | Level A (Yes), Level AA (Yes), Level AAA (No). Only the criteria added in 2.2 are listed separately; the rest are the 2.1 tables |

## Terms

- **Supports**: the functionality of the product has at least one method that meets the criterion
  without known defects, or meets it with equivalent facilitation.
- **Partially Supports**: some functionality of the product does not meet the criterion.
- **Does Not Support**: the majority of product functionality does not meet the criterion.
- **Not Applicable**: the criterion is not relevant to the product.

Where the web app and the downloaded documents differ, the remarks give each one, as
"Web:" and "Documents:", and the level is the lower of the two.

## Summary

| Result | WCAG 2.1 A | WCAG 2.1 AA | WCAG 2.2 additions (A and AA) | Total |
|---|---|---|---|---|
| Supports | 19 | 16 | 4 | 39 |
| Partially Supports | 5 | 1 | 1 | 7 |
| Does Not Support | 0 | 0 | 0 | 0 |
| Not Applicable | 6 | 3 | 1 | 10 |
| Total | 30 | 20 | 6 | 56 |

Partially Supports: 1.3.1 (PDF row headers), 1.4.1 (map marker colours), 1.4.12 (Your Index chart
labels), 2.4.2 (PDF window title), 2.5.1 and 2.5.7 (map panning), 3.2.2 (compact step menu).
Details are in "Known issues and remediation plans".

## Table 1: Success Criteria, Level A (WCAG 2.1)

| Criteria | Conformance Level | Remarks and Explanations |
|---|---|---|
| 1.1.1 Non-text Content | Supports | Web: no control or image lacks a text alternative on any screen (axe, and `wcag_checks.py` lists unnamed images, SVG and controls: none). Icons beside text are hidden from assistive technology. Charts (score bars, the Explore and Your Index charts) have a text name and the same values in a table. The map canvas has a name that says how to use it, and each marker is a button named with its rank and site. Documents: the PDF's one figure (the site positions plot) has alternative text, as has the Word document's one image; the HTML report's charts are inline SVG with names. |
| 1.2.1 Audio-only and Video-only (Prerecorded) | Not Applicable | No audio or video. |
| 1.2.2 Captions (Prerecorded) | Not Applicable | No video. |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | Not Applicable | No video. |
| 1.3.1 Info and Relationships | Partially Supports | Web: one h1 per screen and no skipped heading levels (the Report screen also shows the report preview's own h1, inside its own labelled region), landmarks (banner, navigation, main), every data table with a caption and `th` cells with `scope` for columns and, where rows have names, rows; form fields have labels, groups of fields have a group name, required fields are marked in text. Read from the page on every screen; axe found no failure. Not confirmed with a screen reader. Documents: the HTML report has the same structure. The Word document has heading styles 1 to 4 in order and a header row on every table (19 of 19), but no table captions. The PDF is tagged, with H1 to H4 in order, lists, a table of contents, and Table, THead, TBody and TH for column headers; but the row headers (the first cell of each row, `th scope="row"` in the HTML) are tagged as ordinary TD cells. See known issue 5. |
| 1.3.2 Meaningful Sequence | Supports | The reading order of every screen is its visual order: the Tab order on every screen follows the page from top to bottom in all four themes and at 1440x900, 390x844 and 320x256 (`wcag_checks.py` focus order). The PDF's structure tree reads in page order (`documents.json`, headings in order). |
| 1.3.3 Sensory Characteristics | Supports | Instructions name things by their label, not by shape, colour or position (for example "Confirm or change the matches marked Check This Match"). Reviewed by reading every instruction on every screen. |
| 1.4.1 Use of Color | Partially Supports | Web: status (Must Fix, Missing Values, Ready), tiers and Compare tags are written as text beside any colour; links in text are underlined. On the Results map, Colour Markers By shows one of the user's own columns as marker colour only, with a legend; the value is in each marker's accessible name but is not visible on the map. See known issue 1. Documents: no colour-only information. |
| 1.4.2 Audio Control | Not Applicable | No audio. |
| 2.1.1 Keyboard | Supports | The whole flow, from Start to a downloaded report, done by keyboard alone in Chromium and WebKit (`axe-and-keyboard.json`). Every control is a native button, link, field or menu. The map pans with the arrow keys and zooms with plus and minus when the canvas has focus, and every marker is a button; every site is also in the table. File upload works from the keyboard through the Choose a File button. |
| 2.1.2 No Keyboard Trap | Supports | On every screen Tab runs from the top of the page and leaves the page at the end, in all four themes (`wcag_checks.py`). Focus enters and leaves the map canvas with Tab. In the Common Questions dialog, Tab never reaches the page behind it, Escape closes it and focus returns to the link that opened it. |
| 2.1.4 Character Key Shortcuts | Supports | No single-character shortcuts. The map's plus and minus keys only work while the map has focus, which the criterion allows. |
| 2.2.1 Timing Adjustable | Not Applicable | No time limits. Nothing is removed or submitted after a delay. |
| 2.2.2 Pause, Stop, Hide | Supports | Nothing moves, blinks or scrolls on its own except the progress bar and spinner while the model loads or runs, which show progress and stop when it is done. Spinners slow down when the system asks for reduced motion. No content updates automatically except status text that follows the user's own actions. |
| 2.3.1 Three Flashes or Below Threshold | Supports | Nothing flashes. |
| 2.4.1 Bypass Blocks | Supports | A Skip to Content link is the first stop on every screen and moves focus to the main content; landmarks and headings also allow skipping. When the screen changes, focus moves to the new screen's h1. |
| 2.4.2 Page Titled | Partially Supports | Web: each screen has its own title, "<Step> · EV-SIENT Planner" (for example "Check · EV-SIENT Planner"). Documents: the HTML and Word reports have the title "EV Charging Site Readiness Report: <place>". The PDF has the same title in its metadata but does not ask the reader to show it instead of the file name (DisplayDocTitle is not set), so most PDF readers show the file name. See known issue 5. |
| 2.4.3 Focus Order | Supports | Tab order follows the visual order on every screen, in all four themes and at three window sizes (`wcag_checks.py`). Changing screens moves focus to the new h1. The Common Questions dialog takes focus when it opens and returns it when it closes. Report preview: focus follows the report's reading order. |
| 2.4.4 Link Purpose (In Context) | Supports | Every link says where it goes in its text, or with the sentence it is in ("Download the Blank Template", "Licences", "Accessibility Conformance Report (opens in a new tab)"). Links that open a new tab say so. |
| 2.5.1 Pointer Gestures | Partially Supports | Everything except the map works with a single tap or click. On a touch screen, panning the map needs two fingers (one finger scrolls the page past the map, as the map says). Its zoom buttons are single taps, and every site can be reached from the table and the markers, so no information depends on panning; but panning itself has no single-pointer alternative. See known issue 2. |
| 2.5.2 Pointer Cancellation | Supports | Controls act on release (native click). Dragging a file onto the drop area can be cancelled by dropping it outside. |
| 2.5.3 Label in Name | Supports | Every control whose name comes from `aria-label` or `aria-labelledby` contains its visible text (`wcag_checks.py`, label in name: no mismatches on any screen). |
| 2.5.4 Motion Actuation | Not Applicable | Nothing responds to device motion. |
| 3.1.1 Language of Page | Supports | `lang="en"` on every screen and on the HTML report; the PDF declares English and the Word document en-US. |
| 3.2.1 On Focus | Supports | Focusing a control never changes the screen: every focus walk ran from the top of its screen to the end without leaving it, in all four themes and three window sizes. |
| 3.2.2 On Input | Partially Supports | Choosing an option in a menu, ticking a box or typing never changes the screen, except one control: below 1024 px wide, the compact step menu at the top goes to the chosen step as soon as its value changes (`wcag_checks.py`, step menu). It is labelled as navigation and the screen change is announced, but the user is not warned in advance. See known issue 3. Choosing a file starts reading it, which is the expected result of choosing a file. |
| 3.3.1 Error Identification | Supports | Tested with six bad files (binary data, an empty file, headings only, a plain-text file, repeated site IDs, impossible coordinates), a file that is not a project, the Site ID left unmatched, an empty Your Index name and a scale with equal ends. Each error is described in text, in an alert or next to the field it concerns, with `aria-invalid` and `aria-describedby` on Your Index fields; when Continue is unavailable, the reason is written beside it and attached to it (`wcag-checks.json`, errors). |
| 3.3.2 Labels or Instructions | Supports | Every field has a visible label (none unlabelled on any screen), required fields say so, and each group of fields has an instruction. |
| 4.1.1 Parsing | Supports | WCAG 2.1 errata (and WCAG 2.2) treat this criterion as always met for HTML. No duplicate IDs were found by axe. |
| 4.1.2 Name, Role, Value | Supports | Native controls throughout (buttons, links, check boxes, menus, text and number fields, sliders). Custom parts have names, roles and states, read from the page on every screen (`wcag-checks.json`, `states`): the current step (`aria-current`), disclosure buttons (`aria-expanded`), filter and toggle buttons (`aria-pressed`), sortable column headers (`aria-sort`), the Common Questions link that opens a dialog (`aria-haspopup`), fields in error (`aria-invalid` and `aria-describedby`), and map markers, which are buttons named with their rank, site and, when markers are coloured, the value. axe found no failure. Not confirmed with a screen reader. |

## Table 2: Success Criteria, Level AA (WCAG 2.1)

| Criteria | Conformance Level | Remarks and Explanations |
|---|---|---|
| 1.2.4 Captions (Live) | Not Applicable | No live audio or video. |
| 1.2.5 Audio Description (Prerecorded) | Not Applicable | No video. |
| 1.3.4 Orientation | Supports | Works in portrait and landscape at every tested size (`layout-matrix.json`). |
| 1.3.5 Identify Input Purpose | Supports | The only field that asks for information about the user is Jurisdiction or Organisation on the Check step, which has `autocomplete="organization"`. The other fields describe sites, settings and index weights, not the user. |
| 1.4.3 Contrast (Minimum) | Supports | axe found no contrast failure in any of the four themes, in either browser, at either size. The text axe could not judge (text on the sidebar's translucent background, the compact step bar, the ranked table's rank cells and selected row, the note under the report's site plot) was measured from screenshots in all four themes: lowest 4.99:1, the selected row's rank in dark (`wcag-checks.json`, `undecidedText`). On the first visit to Results the script read that one cell at 1.3:1 to 2.8:1 while the screen was still settling; the same cell measured on the next two visits, and by a separate direct check, is 5.16:1 (light), 4.99:1 (dark) and 7.39:1 (increased-contrast light). Placeholder text, measured from computed styles, is at least 4.5:1 in all four themes after this report's two fixes (it was 1.7:1 in light and 2.4:1 in dark, and the first fix had missed the increased-contrast themes; `before-fixes.json`). |
| 1.4.4 Resize Text | Supports | At 200% zoom (1440x900 shown as 720x450) every screen keeps all text and controls with no text cut off and no sideways scrolling (`wcag_checks.py`, zoom). |
| 1.4.5 Images of Text | Supports | No images of text. The logo is a symbol; the product name beside it is text. |
| 1.4.10 Reflow | Supports | At 320 CSS px wide (1280x1024 at 400%, and 320x640) no screen scrolls sideways (`wcag_checks.py` zoom, on every screen including Results with the map shown, and `layout-matrix.json`). Wide data tables (ranked sites, comparison, the Upload preview, the report's tables) scroll inside their own region, which the criterion allows for two-dimensional data. The compact step bar takes 62 px of the 256 px high window at 320x256. Before this report's fix, a map shown on a wide window kept its width when the window narrowed or the page was zoomed, and the Results page then scrolled sideways (`4ad9ec4`); and the basemap error's long address did not wrap (`207ed5c`). The check records how far the page can actually be scrolled sideways, not only its scroll width. |
| 1.4.11 Non-text Contrast | Supports | Measured from screenshots in all four themes. Focus rings: every focus stop on every screen has a ring of at least 3:1 against its surround, in all four themes (lowest 3.09:1 in light, on the map screens). The links in the map's credit had a ring of 1.29:1 in dark and 1.38:1 in increased-contrast dark (`before-fixes.json`), because MapLibre draws the credit on a half-white box over the tiles; this report's fix gives the box the card's colour (`5f87c8e`). Text fields and menus: a 1px edge of at least 3:1 after this report's fix (it was 1.2:1 to 1.4:1 before). The text fields inset in a Check row sit inside a group whose edge is at least 5.22:1. Check boxes 6.39:1, sliders 6.47:1, the Your Index chart's marks 5.98:1, map markers 3.97:1 and the map's controls 9.01:1, at their lowest. Below 3:1 and judged not required: bordered buttons (1.15:1) and filter buttons (1.16:1), identified by their text, which meets 1.4.3; status icons (1.72:1) and tier marks (2.16:1), each beside its text; and the track of score bars (1.85:1), with the score written beside the bar. Details are in `wcag-checks.json` under each screen's `nonTextContrast`. |
| 1.4.12 Text Spacing | Partially Supports | With the WCAG text-spacing values applied, no text is cut off on any screen at 1440x900 or 390x844, and the page does not scroll sideways, except on Your Index: some labels on the rank-change chart (an SVG) are cut off at the chart's edge. The same names and ranks are in the table beside the chart. See known issue 4. The Upload preview's long values used to be cut off; they now wrap (this report's fix, `6e42290`). |
| 1.4.13 Content on Hover or Focus | Supports | No content appears on hover or focus except native `title` tooltips on tier names, which the browser controls, and those repeat text already on screen. The style rules that reveal content on hover all belong to unused design-system parts, apart from the map's popup, which is not used. |
| 2.4.5 Multiple Ways | Supports | The planner is a process of steps, which the criterion exempts. Even so, every step can be reached from the step list (the sidebar, or the compact step menu below 1024 px). |
| 2.4.6 Headings and Labels | Supports | Headings name their section and labels name their field; reviewed on every screen (the headings are listed in `wcag-checks.json`). |
| 2.4.7 Focus Visible | Supports | Every focus stop on every screen has a visible focus ring in all four themes (`wcag_checks.py`: no stop without one). |
| 3.1.2 Language of Parts | Supports | All text is English. Site names from the user's own file are shown as given. |
| 3.2.3 Consistent Navigation | Supports | The step list (the sidebar, or the compact step bar below 1024 px) and the step buttons (Back, Continue) are in the same place and order on every screen. |
| 3.2.4 Consistent Identification | Supports | The same functions have the same names and icons throughout (for example "Back", "Continue to ...", "Download .pdf"). |
| 3.3.3 Error Suggestion | Supports | Each error says what to do, for example "Give each row its own site ID in your spreadsheet and upload it again", "Export the coordinates from your mapping software as latitude and longitude in decimal degrees (WGS84)", "The worst and best values for Staff are both 10. Set them apart." |
| 3.3.4 Error Prevention (Legal, Financial, Data) | Not Applicable | The planner makes no legal or financial commitment, stores nothing on a server and submits nothing. Everything runs and stays in the browser tab. |
| 4.1.3 Status Messages | Supports | Status messages are in live regions without taking focus: model loading progress, reading a file, matching columns, run progress, the site chosen, Compare changes and table sorting are polite status messages; problems are alerts (`wcag-checks.json`, statusMessages, which logs every live-region change beside the action that caused it). Not confirmed with a screen reader. |

## Table 3: Success Criteria added in WCAG 2.2, Levels A and AA

WCAG 2.2 removes 4.1.1 Parsing. Every other WCAG 2.1 A and AA criterion is in Tables 1 and 2.

| Criteria | Conformance Level | Remarks and Explanations |
|---|---|---|
| 2.4.11 Focus Not Obscured (Minimum) (Level AA) | Supports | Below 1024 px wide a step bar is fixed at the top. No focus stop on any screen, the map's markers included, is fully hidden by it or by anything else, at 390x844 or 320x256, measured at nine points inside every focused control (`wcag-checks.json`). Three fixes for this report made that so: controls scrolled into view by Tab no longer end up under the step bar (`2c9e6a8`); a map marker that takes focus outside the visible part of the map brings the map round to it; and the message shown when the basemap cannot load sits below the map instead of over markers (`7a2f8f2`); on a short window, a marker the map has just brought round is also scrolled into view (`207ed5c`). Some controls are partly covered at times (for example a table's scroll region under the step bar), which this criterion allows. |
| 2.5.7 Dragging Movements (Level AA) | Partially Supports | Nothing needs dragging except panning the map. Files can be chosen with a button instead of dropped, the map zooms with buttons, and every site can be chosen from the table; but panning the map has no single-pointer alternative. See known issue 2. |
| 2.5.8 Target Size (Minimum) (Level AA) | Supports | Every control is at least 24 by 24 CSS px, or has the spacing the exception requires, on every screen at every tested size (`layout-matrix.json` and `wcag_checks.py` targets). Links inside sentences are exempt. |
| 3.2.6 Consistent Help (Level A) | Supports | At 1024 px wide and above, Common Questions is in the same place on every screen, at the foot of the sidebar. Below 1024 px the sidebar gives way to the compact step bar, and Common Questions is only at the foot of the Start screen. The criterion only asks that help which is repeated stays in the same place, so this meets it, but a link in the compact bar would help people on phones. |
| 3.3.7 Redundant Entry (Level A) | Supports | Nothing the user has entered is asked for again. Column matches, fills and settings carry through the steps, and a saved project file reopens them all. |
| 3.3.8 Accessible Authentication (Minimum) (Level AA) | Not Applicable | No sign-in. |

## Known issues and remediation plans

1. **Map marker colours (1.4.1).** With Colour Markers By set to one of the user's columns, a
   marker's colour is the only visible cue to its value. *Plan:* show the value next to the rank
   on the marker label when a column is chosen (or in the selected site's card), and give the
   legend's ranges a shape or pattern as well as a colour. Small change in `SiteMap.tsx`.
2. **Map panning (2.5.1, 2.5.7).** Panning needs a drag, or two fingers on touch. *Plan:* add
   four pan buttons and a "Fit All Sites" button to the map's controls, beside zoom. The table and
   markers already make every site reachable, so this is about the map itself.
3. **Compact step menu (3.2.2).** Below 1024 px wide, choosing a step in the menu goes there at
   once. *Plan:* replace the select with a menu button that opens a list of step buttons (each a
   normal button press), or add a Go button beside the select. Small change in `App.tsx`.
4. **Your Index chart labels with wider text spacing (1.4.12).** The rank-change chart's SVG
   labels have fixed margins, so wider letter and word spacing pushes some past the edge. *Plan:*
   measure the labels and size the margins from them, or draw the labels as HTML beside the SVG.
5. **PDF report (1.3.1, 2.4.2).** Row headers are tagged as TD, and DisplayDocTitle is not set.
   The PDF also does not claim PDF/UA. Both come from the Typst compiler in the browser
   (`@myriaddreamin/typst-ts-web-compiler` 0.7.0 with Typst 0.14.2), whose `compile` call has no
   option for either. *Plan:* upgrade when a version supports PDF/UA output, or post-process the
   PDF in the browser to set `/ViewerPreferences << /DisplayDocTitle true >>` and change the
   first cell of each body row from TD to TH with `/Scope /Row`. Until then, the HTML and Word
   reports are the accessible versions, and the Report screen offers all three.
6. **Screen readers not tested.** Not a known failure, but the largest gap in the evidence.
   *Plan:* before giving this report to an agency, test the full flow with NVDA and Firefox, NVDA
   and Chrome, JAWS and Chrome or Edge, VoiceOver and Safari on macOS and iOS, and TalkBack and
   Chrome on Android. Focus on: moving between steps (focus to the h1 and the announcement),
   the Map Columns rows and their menus, the Check filter buttons and row table, the ranked
   table's sorting and Compare check boxes, the map markers, the Your Index settings and their
   errors, and status messages while the model loads and runs. Update 1.3.1, 4.1.2 and 4.1.3 with
   what is found.

## Fixes made for this report

Each is a separate commit, made up to and including the assessed build. The app's own code
changed only in these eight commits; the others add the checks and the statement.

| Commit | Criterion | Change |
|---|---|---|
| `f4d8f49` | 1.4.11, 1.4.3 | Text fields and menus get a 1px edge in the system grey (light) or secondary label colour (dark), at least 3:1 against the page in all four themes; it was 1.2:1 to 1.4:1. Placeholder text uses the secondary label colour, at least 4.5:1; it was 1.7:1 (light) and 2.4:1 (dark). A border, so it also shows in forced colours. `platform/app/src/styles/legibility.css` |
| `2c9e6a8` | 2.4.11 | Below 1024 px wide, focusable elements have `scroll-margin-top` a little more than the step bar's height, so a control scrolled into view by Tab is never under the bar. `platform/app/src/styles/app.css` |
| `6e42290` | 1.4.12, 1.4.10 | The Upload preview's cells wrap long values instead of cutting them off with an ellipsis. `platform/app/src/styles/steps.css` |
| `7a2f8f2` | 2.4.7, 2.4.11 | A map marker that takes keyboard focus outside the visible part of the map brings the map round to it (no animation when reduced motion is asked for). The message shown when the basemap cannot load moves from over the map to below it, where it cannot hide a marker. `SiteMap.tsx`, `results.css` |
| `4ad9ec4` | 1.4.10 | The map's box may shrink below its canvas's width, so a map shown on a wide window follows the column when the window narrows or the page is zoomed; before, the Results page scrolled sideways (the map stayed 458 px wide at 390 px). `results.css` |
| `207ed5c` | 2.4.11, 1.4.10 | On a short window, a marker the map has just brought round is also scrolled into view. The basemap error's long address now wraps; it made the page scroll sideways at 320 px. `SiteMap.tsx`, `results.css` |
| `f4d953a` | 1.4.3 | The placeholder fix in `f4d8f49` did not reach the increased-contrast themes, which set the same token with a more specific selector inside `@media (prefers-contrast: more)`; placeholders stayed at 1.7:1 and 2.4:1 there. The rule now outranks it. `legibility.css` |
| `5f87c8e` | 1.4.11 | The map's credit (OpenFreeMap and OpenStreetMap) sits on a solid box in the card's colour, with the theme's label colours, instead of MapLibre's half-white box over the tiles. The focus ring on its links was 1.29:1 (dark) and 1.38:1 (increased-contrast dark). `results.css` |
| `ca230a3`, `22d9952`, `3f982bb`, `59f6b64`, `0e93c00`, `77f4e3b`, `efcf54d` | (evidence) | `platform/tools/wcag_checks.py` and `platform/tools/a11y_evidence.py`, the checks and summariser behind this report |
| `0786138` | (statement) | `platform/app/public/accessibility.html`, a short public version of this report, linked from Common Questions ("Is the planner accessible?") |

## Results of automated testing on the assessed build

All runs were on build `5f87c8e`, one check at a time, finishing early on 2026-10-19.

- **axe-core:** 144 runs (9 screens, 4 themes, 2 window sizes, 2 browsers) with 0 violations
  (`axe-and-keyboard.json`), and 70 more runs on 14 screen states inside the per-screen checks, also
  with 0 violations (`wcag-checks.json`). axe left two kinds of result for a person to decide. Colour
  contrast (1,448 results across the runs, most of them text over a translucent or gradient background, or with
  generated content beside it): that text was measured from screenshots instead (1.4.3). Table
  header cells with no data cells (112, on Results and Report): these are the header rows that
  group columns in the Compare and score-breakdown tables, which do have data cells below them
  in the columns they span.
- **Keyboard flow:** Start to a downloaded report by keyboard alone, through Upload, Check, Public
  Data, Results (a site chosen and two sites compared by keyboard) and Report: 63 Tab stops, 0
  problems (Chromium, 1280x900; the skip link comes first and shows). The per-screen focus walks:
  every screen left by Tab at the end, no stop without a visible ring, no ring under 3:1 by style,
  none entirely hidden.
- **Layout matrix:** 440 screen checks (11 window sizes, light and dark, two browsers), 0 failing:
  no sideways scrolling, no control covered by the step bar or anything else, no target under
  24 px, primary controls at least 44 px tall, no requests to other sites and no console errors
  (`layout-matrix.json`).
- **Offline:** OK in Chromium and WebKit: the service worker installs, and the planner then starts
  and runs the model with the network off (`offline.json`). Not a WCAG check.

## Other observations

- If any basemap request fails before the map has finished loading, the map shows an alert, "The
  basemap could not load", with the technical error and the failing address, even when most of the
  map then draws. In several test runs on a busy machine a single failed request caused it. It is
  honest but can be alarming, and the address means little to most readers; consider a quieter
  status message unless the whole basemap fails, and leaving the address out. Not a WCAG failure.
- Running the checks on a heavily loaded machine made the model take minutes to start, and the
  scripts then time out (WebKit most often). Such a run fails for that reason alone; run the
  checks one at a time on a quiet machine.
- The Report screen shows two h1 headings: the screen's and the report preview's. The preview is
  in its own labelled region and is the document the user will download, so this was judged
  correct, but a screen-reader user may want to check it.
- The Word report's tables have header rows but no captions; the heading above each table names it.

## Re-testing after other changes

Other work was being merged into `platform/app` while this report was written: a Results stability
section, an assistant panel and multi-state public data. After those merges, re-run every check in
[`evidence/README.md`](evidence/README.md) on the merged build and compare the summaries with the
ones here. In particular:

- **Results stability section:** headings and table structure (1.3.1), any chart's text
  alternative (1.1.1) and contrast of its marks (1.4.11), reflow at 320 px (1.4.10), text spacing
  (1.4.12), status messages if it updates as settings change (4.1.3).
- **Assistant panel:** keyboard access and focus order into and out of the panel (2.1.1, 2.1.2,
  2.4.3), focus visible and not hidden (2.4.7, 2.4.11), its input's label (3.3.2), new replies
  announced as status messages without moving focus (4.1.3), whether it covers content at 320 px
  or at 400% zoom (1.4.10, 2.4.11), and content on hover (1.4.13). A chat panel is also the place
  most likely to need screen-reader testing.
- **Multi-state public data:** the Public Data step's new controls (labels, 3.3.2; input purpose,
  1.3.5; change on input when a state is chosen, 3.2.2), any new tables (1.3.1) and the reports'
  data sources sections in all three formats.
- **Everything:** axe in four themes, the keyboard flow, the layout matrix and the per-screen
  focus walks, since the shell and the step list may change.

Then update this report's assessed commit, the summary and any remarks that change.

---

"Voluntary Product Accessibility Template" and "VPAT" are registered service marks of the
Information Technology Industry Council (ITI).
