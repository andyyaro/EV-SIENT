# Tableau Implementation Blocker — and the complete workaround package

**Status (2026-07-19): a verified `.twbx` presentation dashboard could NOT be produced in this environment.**

## Why this is blocked

- **Tableau Desktop is not installed** on this machine.
- **Tableau Public** (installed) was deliberately **not used**: it can only save workbooks to
  Tableau's public cloud, which would publish project data externally — prohibited by the
  no-external-side-effects rule of this run.
- Editing the packaged workbook XML blind (unzipping the original legacy workbook
  `EV_Charging_Site_Readiness_Workbook.twbx`, rewriting the XML, and repacking) was
  evaluated and rejected: without Tableau to open the result, a hand-patched `.twbx`
  cannot be verified, and the master prompt forbids claiming a valid workbook that was
  never opened. The original workbook is preserved untouched — it lives in the pre-V3
  archive branch (`archive/pre-milestone2-v3-20260719`), not in this tree.

## What exists instead (fully satisfying the presentation)

1. **Static presentation dashboard** — `dashboard/static/` (9 contract-derived
   visuals + `STATIC_DASHBOARD.pdf`), all offline-openable, all footer-labeled. This is the
   presentation-facing deliverable; the July 18 team decision and the research (static
   visuals, 86.4/100) already selected static assets as the demo strategy.
2. **Complete patch package** — `patch_package/` with contract-derived CSVs and the exact
   build recipe below, so anyone with Tableau Desktop can produce and verify
   `EV_Charging_Site_Readiness_M2_Final.twbx` in under an hour.

## Exact build recipe for a Tableau Desktop operator

Data sources (connect to all six; join nothing on names — join on `site_id`):
`tbl_sites_dimension.csv`, `tbl_canonical_scenarios.csv`, `tbl_readiness_confidence.csv`,
`tbl_portfolio_costs.csv`, `tbl_avoided_evse.csv`, `tbl_peak_waits.csv`

Worksheets (7):
1. *Readiness ranking* — bar, `readiness_score` by `site_id`, color by `data_confidence_level_v3`
   (palette: dark green #1B4332 / tan #B08948); caption: "0 of 12 sites High confidence".
2. *Starter vs pathway* — bar-in-bar, `ports_active` (2026 baseline) inside `ports_pathway_capacity`.
3. *Three horizons* — line, SUM(ports_active) by `horizon_year` for case base vs high;
   reference line y=48 "pathway ceiling".
4. *Lifecycle cost* — side-by-side bar from `tbl_portfolio_costs` (escalation_case=base),
   STG vs OVB NPV by horizon; label avoided cost on STG bars.
5. *Net CO2e* — line, SUM(net_co2e_kg)/1000 by horizon/case; caption MUST carry
   "eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh, accessed 2026-07-19".
6. *Peak waits* — bar, p50 vs peak P90 wait, top-6 sites; reference line 10 min.
7. *Map* — `lat`/`lon` from sites dimension, size by ports_pathway, color top-3.

Dashboard: one 1600×900 dashboard, title "EV Charging Site Readiness — Milestone 2",
worksheets 1/2/4/5 + map; **filters kept minimal** (single horizon-year filter, applied
to worksheets 3–5 only). Story: 8 points in the order of the static dashboard files
01→09. EVERY sheet caption must include source + vintage + the placeholder-capacity
label where capacity appears (`capacity_basis` = placeholder at all 12 sites).

Acceptance: open without errors; every number matches `tbl_canonical_scenarios.csv`;
export dashboard as PNG/PDF and diff against `dashboard/static/`.

## Verification statement

The original workbook (12 worksheets, 13 extracts, no dashboard/story) is byte-identical
to the archive copy. Nothing in this directory claims a working `.twbx` was produced or
verified in this run.
