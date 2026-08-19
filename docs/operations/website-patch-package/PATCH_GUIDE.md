# File-by-File Patch Guide (website + assistant)

Maintainer prerequisite: access to the deployed site bundle (S3 origin) and the assistant's
prompt/config store. Apply in order; deploy per DEPLOYMENT_RUNBOOK.md. Do not remove any
existing limitation text - only extend or supersede as directed.

## 1. Landing page (`index.html`)
- Add the authority-disclaimer block (`content/authority_disclaimer.md`, rendered) directly
  under the hero section.
- Replace any "2035/2050" wording with "10/20/30-year horizons (2036 / 2046 / 2056 from a
  2026 baseline)".
- Add footer include `content/source_vintage_footer.html`.

## 2. Dashboard page (`dashboard.html`)
- Replace embedded charts with the 9 static assets from
  `dashboard/static/` (repository-relative; already footer-labeled; keep filenames).
- Add caption under any capacity-related visual: "Electrical capacity is a planning
  placeholder at all 12 sites pending utility/facility confirmation."
- Add alt text per image (describe the chart takeaway, not the chart type).

## 3. Results page (`results.html`)
- Insert `content/results_2036_2046_2056.md` (rendered) as the lead section.
- Every number on this page must trace to `data/contract/v1/scenario_table.csv`; remove
  any figure that does not.
- Keep the "0 of 12 sites High confidence" line prominent.

## 4. Methodology page (`methodology.html`)
- Append `content/methodology_update.md` as a new "V3 (July 2026)" section; keep the V2
  section labeled "V2 (accepted baseline)".

## 5. New privacy page (`privacy.html`)
- Create from `content/privacy_notice.md`; link from every page footer.

## 6. New standards page or section (`standards.html`)
- Create from `content/standards_summary.md`; the proposed-standard section must keep the
  "fellowship design concept - not an official UL/ULSE proposal" label verbatim.

## 7. Limitations (wherever `MODEL_LIMITATIONS` content is surfaced)
- Replace with `content/limitations_update.md`.

## 8. AI Assistant page + config
- Page: insert `content/assistant_boundaries.md` above the chat window; add the privacy
  link; keep the Cognito gate unchanged.
- Assistant system prompt/config: append the boundary rules from
  `content/assistant_boundaries.md` §"Answer rules" (explanation-only; no approval,
  engineering, permitting, or budget advice; cite doc + vintage; direct formal comments
  to municipal channels).
- Update the assistant's document corpus to include the V3 README, contract README, and
  limitations update; EXCLUDE any internal working files, credentials, or infrastructure notes.

## 9. Accessibility pass (all pages)
- alt text on all new images; one h1 per page; visible focus states on new links;
  contrast of new text blocks ≥ WCAG AA.

## Acceptance checklist
- [ ] Privacy + authority disclaimers reachable from every page
- [ ] All results numbers match contract v1.0.0 values
- [ ] Source-vintage footer on every page
- [ ] Assistant answers state explanation-only boundary when asked for decisions
- [ ] No secrets/credentials introduced (grep bundle for AKIA, secret, apikey before upload)
- [ ] Cognito authentication still required for the assistant
