# LANE L12 - BINARY VERIFICATION (Phase-0 ground truth)

**Repo:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (branch `v4-platform`, single commit `c089bd4b125d9be369ab533eb4e7c6189498deb0`, 2026-07-27 11:51:52 -0400)
**Explorer:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/incoming/explorer/fcf-3d`
**Method:** temp venv at `/private/tmp/.../scratchpad/venv` (openpyxl 3.1.x, Pillow, pypdf, python-docx, python-pptx). Nothing installed into, written to, or modified inside either tree. `file(1)`, `md5`, `shasum -a 256`, `python+zipfile`, `python+struct` for GLB chunk walking.

**Verdict up front:** all 38 binaries exist, decode cleanly, and are structurally non-corrupt. Zero corrupt files. The defects are *provenance and reference* defects, not integrity defects: 4 DOCX are stale against their Markdown sources (and the report PDF inherits the staleness), 7 binaries are orphaned, 1 documented path (`presentation/static_visuals/`) does not exist, and a tracked JSON sidecar leaks the authoring machine's home directory in a way that makes `scripts/verify.sh` fail.

---

## 1. PDFs (4)

### dashboard/static/STATIC_DASHBOARD.pdf
- **Role:** The single-file, offline, print-ready bundle of the nine contract-derived dashboard visuals - the team's fail-safe presentation asset.
- **Kind:** generated (`scripts/build_static_dashboard.py`, function `combined_pdf()` at lines 217–221, via `PIL.Image.save(..., save_all=True, append_images=...)`)
- **Reads:** n/a (binary). Its generator reads `data/contract/v1/scenario_table.csv`, `data/contract/v1/site_table.csv`, `data/outputs/v3_run` (`scripts/build_static_dashboard.py:29–31`).
- **Written by / read by:** written by `scripts/build_static_dashboard.py:221`. Referenced by `dashboard/README.md`, `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md:21`, `docs/operations/reproduction-guide.md:46`, `scripts/build_static_dashboard.py`.
- **Key contents:** 9 pages, 1,190,401 bytes. Not encrypted. Metadata: `/Title = "STATIC_DASHBOARD"`, `/CreationDate = D:20260719054022Z`, `/ModDate` identical. **No `/Producer` and no `/Creator`** (PIL writes neither). Page sizes are per-page and equal the source PNG pixel dimensions in points: p1 2750×1131, p2 2336×1131, p3 2503×1131, p4 2464×1131, p5 2750×1131, p6 2372×1044, p7 2653×1044, p8 1773×1090, p9 2185×1309.
- **First page text:** **empty - there is no text layer at all.** Total extractable text across all 9 pages is 0 characters. Each page holds exactly one embedded raster: XObject `image.jpg`, mode RGB, at the page's full pixel dimensions.
- **Notes:**
  - **In sync with its PNGs - verified.** I decoded each page's JPEG and pixel-differenced it against the corresponding `dashboard/static/0*.png`: sizes match exactly on all 9, mean absolute pixel difference 0.34–1.08 / 255. That is pure JPEG re-encode noise. The PDF has **not** drifted from the PNGs.
  - The generator globs `OUT.glob("0*.png")` (line 219), which is why `10_mcda_provisional.png` is deliberately excluded - but that glob is also why the PDF silently tracks whatever `0*.png` files happen to be present.
  - RGBA PNGs are flattened to RGB and lossily JPEG-compressed by PIL. Chart text in the PDF is therefore softer than in the PNGs, and the document is **not searchable or screen-reader accessible**. If this is the "fail-safe" artifact, that is a real accessibility limitation worth recording.

### presentation/deck/Future_City_Fellowship_Milestone_2_Final.pdf
- **Role:** Offline fail-safe render of the 17-slide Milestone 2 deck (the runbook calls it "the fail-safe").
- **Kind:** generated (LibreOffice Impress export of the sibling `.pptx`)
- **Reads:** n/a
- **Written by / read by:** no script in the repo produces it (LibreOffice was run by hand). Referenced by `README.md:108` and `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:4,63`.
- **Key contents:** 17 pages, 1,490,222 bytes. Metadata: `/Creator = "Impress"`, `/Producer = "LibreOffice 26.2.4.2 (AARCH64)"`, `/CreationDate = D:20260719015455-04'00'`. **No `/Title`.** Page size 959.981102 × 540 pt (13.33 × 7.5 in, 16:9).
- **First page text:** `FUTURE CITY FELLOWSHIP · MILESTONE 2 · JULY 21, 2026` / `A Staged, Future-Ready Public EV Charging Plan` / `Fairfax City + Prince William County, Virginia - 12 candidate sites, 25 starter ports on a 48-port future-ready pathway` / `Team: Anna · Laylas · Andy · Adama · Paula` / `Target 13 minutes · static visuals only (all images open offline)` / `All model figures are screening-class outputs of canonical contract v1.0.0 (2026-07-19); nothing in this deck is a budget, permit, or client endorsement.`
- **Notes:**
  - **Byte-for-byte in sync with the PPTX at the text level.** I compared page count (17 = 17) and each page's first text line to the corresponding slide's first text line: **17/17 identical**, including the non-breaking spaces in the banner. No drift.
  - Horizon hygiene is **clean**: token scan over the full 14,243 extracted characters finds `2026`×27, `2036`×3, `2046`×3, `2056`×3, and **zero** occurrences of `2035`, `2050`, or `590.2`. `596.3` appears 5×.

### presentation/deck/Future_City_Fellowship_Milestone_2_QA_Backup.pdf
- **Role:** Anticipated-question pack with evidence-grounded answers; not presented, used only if asked.
- **Kind:** generated (LibreOffice Impress export)
- **Reads:** n/a
- **Written by / read by:** **no `.pptx` source exists in the repo** - this PDF has no editable ancestor and no generator. Referenced by `presentation/README.md` and `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:4`.
- **Key contents:** 11 pages, 156,985 bytes. `/Creator = "Impress"`, `/Producer = "LibreOffice 26.2.4.2 (AARCH64)"`, `/CreationDate = D:20260719015721-04'00'`. **No `/Title`.** 959.981102 × 540 pt.
- **First page text:** `FUTURE CITY FELLOWSHIP · MILESTONE 2 · JULY 21, 2026` / `Q&A Backup Pack` / `Anticipated questions with evidence-grounded answers - not presented; used only if asked.` / `Every answer traces to canonical contract v1.0.0 (2026-07-19) or a named project artifact. If an answer is not known: say so, and name the artifact or request that will resolve it.` / `Claims discipline: no client endorsement, no compliant CM2 held yet, no funding applied for, capacity placeholder at 12/12 sites, MCDA provisional`
- **Notes:**
  - Token scan (9,087 chars): `2026`×9, `2036`×1, `2046`×2, `2056`×1, zero `2035`/`2050`/`590.2`. The one `10-year` and one `30-year` are at page 9: *"How would your team keep a 30-year electrification model honest when the client's own 10-year sustainability goals are already off-track?"* - this is a **peer question about the client's sustainability goals and model duration**, not a horizon label. **Legitimate, not a horizon violation.**
  - Reproducibility gap: the Final deck can be re-exported from `Future_City_Fellowship_Milestone_2_Final.pptx`; this one cannot be regenerated or edited from anything in the repo.

### reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf
- **Role:** Print rendering of the Milestone 2 Final Report.
- **Kind:** generated (LibreOffice Writer export of `Future_City_Fellowship_Milestone_2_Final_Report.docx`, which is itself python-docx output)
- **Reads:** n/a
- **Written by / read by:** **ORPHAN - zero files in the repo reference this filename.**
- **Key contents:** 7 pages, 188,391 bytes. Metadata: `/Author = "python-docx"` (the tell-tale that it came through the DOCX), `/Creator = "Writer"`, `/Producer = "LibreOffice 26.2.4.2 (AARCH64)"`, `/CreationDate = D:20260719014905-04'00'`. **No `/Title`.** US Letter 612 × 792 pt.
- **First page text (verbatim opening):** title `Future City Fellowship - Milestone 2 Final Report`; subtitle `Safe, Code-Responsive Electrification for Fairfax City and Prince William County`; `Team: Anna · Laylas · Andy · Adama · Paula (George Mason University Future City Fellowship)`; `Client contact: [client contact], Green Buildings Manager, Prince William County Office of Sustainability`; `Prepared: 2026-07-19 (for the Milestone 2 presentation, Tuesday 2026-07-21)`; `Supersedes: Future_City_Fellowship_Milestone_2_Phase_Report.md (July 2026)`; a "Standing discipline" paragraph stating *"0 of 12 candidate sites have High data confidence; electrical capacity is a placeholder at all 12 sites"*; then `1. Executive summary`, which carries the headline numbers **85/100** (staged distributed pilots), **81/100** (hybrid portfolio), **~35-station** county fleet hub, **FFX002 top at 58.8**, **25 starter / 48 pathway ports**, **38 REVIEW + 12 INFO findings**, **15 Tableau exports**, **35-file package**.
- **Notes:**
  - **Inherits every stale path from the DOCX** (see §3): `data_contract/v1`×1, `human_actions/`×8, `reports/RISK_REGISTER`×1, `repos/matlab_simulink_m2_v3`×1, `visuals/static_dashboard`×1, `website_patch_package`×1. None of those directories exist in `v4-platform`.
  - `590.2` appears **once**, at the correction sentence: *"a net-CO2e layer with a corrected, sourced grid factor (EPA eGRID2023 Rev 2, SRVC, 596.3 lb CO2e/MWh, accessed 2026-07-19 - the research package's 590.2 figure was superseded by direct EPA verification)"*. This is an explicit, correctly-labelled supersession note, not a live figure. Flagged for Phase 1 to adjudicate against the "must survive NOWHERE" rule.
  - `2050` appears **once**, describing a defect that was fixed: *"The MATLAB adapter is now generated (PY-14), eliminating the hand-built CSV and its 2050-base/high port mismatch."* Contextual, not a live horizon.
  - `10/20/30` appears once and is **correctly reconciled**: *"The official requirement - two aspects modeled at 10/20/30-year timelines - is satisfied with the canonical convention 2036/2046/2056 from a stated 2026 baseline."*
  - `legacy_v2` appears twice, both correctly labelled as the V3 bit-exact reproduction mode.

---

## 2. PPTX (1)

### presentation/deck/Future_City_Fellowship_Milestone_2_Final.pptx
- **Role:** The editable 17-slide Milestone 2 final deck.
- **Kind:** generated (python-pptx; `docProps/core.xml` carries `<dc:description>generated using python-pptx</dc:description>`)
- **Reads:** n/a
- **Written by / read by:** **no build script in the repo produces it** - the generating python-pptx code is not tracked. Referenced by `presentation/README.md`, `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:4,62,64`, `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md`.
- **Key contents:** valid OOXML zip, `testzip()` returns `None` (no bad members), 117 entries, 1,621,618 bytes. Slide size 12,191,695 × 6,858,000 EMU = 13.333 × 7.5 in (16:9). **17 slides.** 10 media images, all PNG. Every slide has a notes slide (56–128 chars each). **No slide uses a title placeholder** - `slide.shapes.title` is `None` on all 17, so titles below are the first text-frame line (the section banner).

  | # | Banner / title | Pictures | Notes chars |
  |---|---|---|---|
  | 1 | `FUTURE CITY FELLOWSHIP  ·  MILESTONE 2  ·  JULY 21, 2026` (title slide: "A Staged, Future-Ready Public EV Charging Plan") | 0 | 91 |
  | 2 | `01 · THE PROBLEM WE CARRIED FORWARD FROM PHASE 1` | 0 | 93 |
  | 3 | `02 · WHAT THE CLIENT'S OWN EXPERIENCE TELLS US` | 0 | 128 |
  | 4 | `03 · CLIENT MEETING #2 - WHERE IT HONESTLY STANDS` | 0 | 95 |
  | 5 | `04 · SEVEN GENUINELY DIFFERENT WAYS TO DO THIS` | 0 | 56 |
  | 6 | `05 · WEIGHTED COMPARISON - PROVISIONAL, PENDING TEAM ADOPTION` | 1 | 104 |
  | 7 | `06 · HOW THE STAGED SOLUTION ACTUALLY WORKS` | 0 | 85 |
  | 8 | `07 · CURRENT MODEL RESULTS - AND THEIR CONFIDENCE` | 1 | 107 |
  | 9 | `07 · CURRENT MODEL RESULTS - THE PORTFOLIO SHAPE` | 2 | 95 |
  | 10 | `08 · TWO MODELED ASPECTS ACROSS THREE HORIZONS` | 0 | 121 |
  | 11 | `08 · THE SAME TWO ASPECTS, AS PICTURES` | 2 | 96 |
  | 12 | `09 · THE STANDARDS PACKAGE - ADOPTED EDITIONS, NOT LATEST` | 0 | 125 |
  | 13 | `10 · TECHNICAL INTEGRATION AND WHAT COULD FAIL` | 1 | 90 |
  | 14 | `11 · THE ECONOMIC, ENVIRONMENTAL, AND STAKEHOLDER CASE` | 2 | 119 |
  | 15 | `12 · LIMITATIONS - WHAT WE STILL DO NOT KNOW` | 1 | 81 |
  | 16 | `13 · OUR QUESTION FOR THE PEER TEAMS - AND WHAT WE DO NEXT` | 0 | 102 |
  | 17 | `CLOSING` ("Speaking roster - July 21, 2026 · target 13:00") | 0 | 81 |

- **Embedded-image provenance - all 10 verified byte-identical (SHA-256) to on-disk PNGs:**
  | media part | bytes | used by | on-disk twin |
  |---|---|---|---|
  | image1.png | 162,772 | slide6 | `presentation/assets/10_mcda_provisional.png` |
  | image2.png | 183,217 | slide8 | `dashboard/static/01_readiness_ranking.png` |
  | image3.png | 188,500 | slide9 | `dashboard/static/09_site_map_offline.png` |
  | image4.png | 100,749 | slide9 | `dashboard/static/02_starter_vs_pathway.png` |
  | image5.png | 129,672 | slide11 | `dashboard/static/03_ports_three_horizons.png` |
  | image6.png | 106,219 | slide11 | `dashboard/static/04_lifecycle_cost.png` |
  | image7.png | 397,317 | slide13 | `docs/assets/architecture/integration_architecture.png` |
  | image8.png | 136,745 | slide14 | `dashboard/static/05_net_co2e.png` |
  | image9.png | 105,655 | slide14 | `dashboard/static/06_avoided_evse.png` |
  | image10.png | 170,757 | slide15 | `dashboard/static/08_limitations.png` |

- **Notes:**
  - **The deck's images have NOT drifted.** All 10 hash-match current repo PNGs. This is the strongest single sync signal in the lane.
  - `dashboard/static/07_peak_wait.png` is the only one of the nine dashboard visuals **not** used in the deck.
  - Content claims that check out: slide 8 says *"FFX002 City of Fairfax Regional Library leads at 58.8"*, *"38 REVIEW + 12 INFO findings"*; slide 9 says *"12 sites · 25 starter ports · 48-port future-ready pathway"*; five slides carry the footer *"eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh, accessed 2026-07-19"*. **No `590.2` anywhere.**
  - Horizon hygiene: slide 2 says *"over 10 / 20 / 30 years (2036 / 2046 / 2056)"* - correctly reconciled, not a violation. Slide 10 is *"08 · TWO MODELED ASPECTS ACROSS THREE HORIZONS … at 2036 · 2046 · 2056"*.
  - **`docProps/core.xml` is the unmodified python-pptx default template stub:** `<dc:title/>` empty, `<dc:creator/>` empty, `<cp:lastModifiedBy>Steve Canny</cp:lastModifiedBy>` (python-pptx's author), `<dcterms:created>2013-01-27T09:14:16Z</dcterms:created>`. `docProps/app.xml` likewise says `<PresentationFormat>On-screen Show (4:3)</PresentationFormat>` and `<Slides>0</Slides>` - both **wrong** (the deck is 16:9 with 17 slides). Cosmetic, but a reviewer opening file properties sees a 2013 4:3 deck by "Steve Canny".
  - **Slide 17 text contains a dead path:** *"every image in this deck opens offline from `presentation/static_visuals/`"* - that directory does not exist (see §7).

---

## 3. DOCX (4)

All four are valid OOXML (`testzip()` → `None`), all four carry the python-docx default template stub in `docProps/core.xml`: `<dc:title/>` empty, `<dc:creator>python-docx</dc:creator>`, `<dc:description>generated by python-docx</dc:description>`, `<dcterms:created>2013-12-23T23:15:00Z</dcterms:created>`, `<Application>Microsoft Macintosh Word</Application>`, `<Template>Normal.dotm</Template>`, `<Pages>1</Pages>`, `<Words>0</Words>`. None contains any `word/media/`. **All four are orphans - zero files in the repo reference any of these four filenames.**

**Generator check method:** I re-ran `scripts/md_to_docx.py` on each Markdown source into the scratchpad (never into the repo) and diffed paragraph-by-paragraph on `(style name, text)` plus all table cells and table styles.

### reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx
- **Role:** Word deliverable of the Milestone 2 Final Report.
- **Kind:** generated (`scripts/md_to_docx.py`)
- **Reads:** n/a; its generator reads `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
- **Written by / read by:** written by `scripts/md_to_docx.py` (invoked manually - no Makefile target, no mention in `docs/operations/reproduction-guide.md`). Read by nothing.
- **Key contents:** 48,076 bytes, 82 paragraphs, 4 tables (5×6, 6×2, 8×2, 7×2). Styles: `Title`, `Heading 1`, `List Bullet`, `List Number`, `Normal`.
  **Section headings in order:** `[Title] Future City Fellowship - Milestone 2 Final Report`; `[H1] Safe, Code-Responsive Electrification for Fairfax City and Prince William County`; `[H1] 1. Executive summary`; `2. Verified baseline (what this report stands on)`; `3. Client evidence and the honest Client Meeting #2 status`; `4. Alternatives and convergence (prepared for team adoption)`; `5. Two aspects at 2036 / 2046 / 2056`; `6. Canonical contract and cross-model integration`; `7. Model integrity upgrades (V3)`; `8. Standards and the proposed standard`; `9. Technical integration, risk, environment, funding, stakeholders`; `10. Artifact status`; `11. Limitations (unchanged in force)`; `12. Next human actions (highest priority first)`; `13. Peer-team question`.
- **Twin:** yes, `Future_City_Fellowship_Milestone_2_Final_Report.md` in the same directory.
- **Generated from the md by `md_to_docx.py`?** **Yes** - style mapping, heading levels, list styles, and table style all reproduce exactly.
- **In sync?** **NO - STALE.** Same paragraph count (112 dumped lines both sides) but 57 diff lines. Every difference is a **pre-reorganisation path that the `.md` has since updated and the `.docx` never picked up**:
  | docx says (stale) | md says (current) |
  |---|---|
  | `data_contract/v1/` | `data/contract/v1/` |
  | `human_actions/…` (×8) | `docs/human-actions/…` |
  | `repos/matlab_simulink_m2_v3/` | `matlab/` |
  | `tableau/` | `dashboard/tableau/` |
  | `visuals/static_dashboard/` | `dashboard/static/` |
  | `website_patch_package/` | `docs/operations/website-patch-package/` |
  | `reports/RISK_REGISTER.md/.csv` | `reports/milestone-2/RISK_REGISTER.md/.csv` |
  | `reports/REGULATORY_STAKEHOLDER_MAP.md` | `reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md` |
  Plus a handful of trailing-whitespace-only paragraph diffs.
- **Notes:** the `.pdf` sibling was exported from this stale DOCX and carries the same stale paths. Regenerating the DOCX must be followed by re-exporting the PDF.

### reports/milestone-2/Milestone_2_Gap_Closure_Status.docx
- **Role:** Word deliverable of the 52-criterion gap-closure reassessment.
- **Kind:** generated (`scripts/md_to_docx.py`)
- **Reads:** n/a; generator reads `reports/milestone-2/Milestone_2_Gap_Closure_Status.md`
- **Written by / read by:** written by `scripts/md_to_docx.py`; read by nothing.
- **Key contents:** 43,485 bytes, 16 paragraphs, 2 tables: a 7×2 summary and the **53×8 full criterion table** (header + 52 criteria). Styles: `Title`, `Heading 1`, `List Bullet`, `Normal`.
  **Section headings:** `[Title] Milestone 2 Gap-Closure Status - Final Reassessment of All 52 Criteria`; `[H1] Summary`; `[H1] Full 52-criterion table`; `[H1] What must never be claimed until the humans act`.
  Big-table header row: `ID | Requirement (short) | Prior | Final status | Evidence produced this run | Owner | Next action | Acceptance evidence when done`.
- **Twin:** yes, same directory.
- **Generated from the md by `md_to_docx.py`?** **Yes.**
- **In sync?** **NO - STALE**, but only mildly: 7 diff lines, one substantive. Row `A1` still says `(human_actions/client_meeting_2/)` where the `.md` says `(docs/human-actions/client_meeting_2/)`.
- **Notes:** token scan finds `10-year`, `20-year`, `30-year`, `10/20/30` (one each) - these sit in the criterion text describing the fellowship requirement, alongside the 2036/2046/2056 reconciliation. Not violations.

### reports/milestone-2/FINAL_STANDARDS_APPLICATION_MATRIX.docx
- **Role:** Word deliverable of the standards application matrix (which standard applies at which lifecycle stage, adopted editions vs latest).
- **Kind:** generated - but **by an older/different converter, not the current `scripts/md_to_docx.py`**
- **Reads:** n/a; source Markdown is `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md` (**different directory** from the docx)
- **Written by / read by:** read by nothing. The deck (slide 12) and other prose cite `FINAL_STANDARDS_APPLICATION_MATRIX.md`, never the `.docx`.
- **Key contents:** 43,786 bytes, 33 paragraphs, 9 tables - dims `(10,5), (12,2), (12,2), (12,2), (12,2), (12,2), (12,2), (12,2), (3,3)`. Styles: `Heading 1/2/3`, `Normal`. Table style: **`Table Grid`**.
  **Section headings in order:** `[H1] Final Standards Application Matrix`; `[H2] 1. Standards set at a glance`; `[H2] 2. Lifecycle application matrix`; `[H3] 2.1 UL 2594 (highlighted safety standard)`; `[H3] 2.2 UL 3600 (highlighted sustainability standard - voluntary)`; `[H3] 2.3 UL 2231-1/-2 (essential supporting - personnel protection)`; `[H3] 2.4 NEC Article 625 as adopted in Virginia (2020 NEC via 2021 USBC)`; `[H3] 2.5 Virginia USBC / SFPC (2021 editions)`; `[H3] 2.6 US Access Board EVSE accessibility (TA 2022; NPRM 2024-09-03) + VA USBC ADA provisions`; `[H3] 2.7 OCPP + ISO 15118 (supporting protocols - NOT ULSE standards)`; `[H3] 2.8 Conditional standards (out of current scope - must not be presented as active)`; `[H2] 3. Decisions that remain with the AHJ / Fire Marshal`; `[H2] 4. Value proposition (why adherence is cheap insurance)`.
  First table header: `Standard / instrument | Role in this plan | Adopted / governing edition (Virginia, 2026-07-19) | Latest published edition | Applicability at the 12 candidate sites`.
- **Twin:** **no `.md` twin in the same directory** - the source lives at `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md`.
- **Generated from the md by `md_to_docx.py`?** **No - the current script does not reproduce it.** 97 diff lines, three systematic structural differences:
  1. **Heading levels are shifted by one.** Current `md_to_docx.py` maps `# `→`add_heading(level=0)` = `Title`, `## `→`Heading 1`, `### `→`Heading 2` (lines 68–76). The committed docx has `Heading 1 / Heading 2 / Heading 3` - i.e. an older mapping of `#`→level 1.
  2. **Table style is `Table Grid`; the current script hardcodes `table.style = "Light Grid Accent 3"`** (`scripts/md_to_docx.py:57`).
  3. **Horizontal rules render differently.** Current script turns `---` into `doc.add_paragraph("_" * 60)` (line 87); the committed docx has empty paragraphs there.
- **In sync content-wise?** Also stale: contains `data_contract/v1/standards_register.csv` where the `.md` now says `data/contract/v1/standards_register.csv`.
- **Notes:** the two structural facts together mean this file cannot be reproduced by any code in the repo. Regenerating it with the current script will silently restyle it.

### reports/milestone-2/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx
- **Role:** Word deliverable of the fellowship's proposed (non-official) municipal EV charging standard concept.
- **Kind:** generated - **same older/different converter as the matrix above**
- **Reads:** n/a; source is `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md`
- **Written by / read by:** read by nothing.
- **Key contents:** 42,890 bytes, 38 paragraphs, 9 tables - dims `(6,3), (5,3), (5,3), (4,3), (4,3), (5,3), (5,3), (4,2), (5,2)`. Styles: `Heading 1/2/3`, `List Bullet`, `List Number`, `Normal`. Table style `Table Grid`.
  **Section headings in order:** `[H1] Proposed Standard Concept - "Municipal EV Charging Site Readiness and Emergency Access Standard"`; `[H2] 1. Purpose and rationale`; `[H2] 2. Scope and applicability`; `[H2] 3. Modules and test/verification tables`; `[H3] Module 1 - Emergency access and disconnect (flagship)`; `[H3] Module 2 - Expandability and right-sizing documentation`; `[H3] Module 3 - Accessibility and site-condition cross-references`; `[H3] Module 4 - Monitoring and expansion triggers`; `[H3] Module 5 - Managed-charging fail-safe`; `[H3] Module 6 - Commissioning and evidence package`; `[H3] Module 7 - Materials, take-back, and end of life`; `[H2] 4. Conformance levels`; `[H2] 5. Inspection intervals (provisional - TBV by ULSE/AHJ)`; `[H2] 6. Research still needed before this concept could mature`.
  First table header: `Test category | Verification method | Parameter basis`. Carries a repeated required label: *"This is a Future City Fellowship design exercise, not an official UL/ULSE proposal."*
- **Twin:** **no `.md` twin in the same directory** - source is in `docs/standards/`.
- **Generated from the md by `md_to_docx.py`?** **No** - 96 diff lines, identical structural signature to the matrix docx (heading levels shifted by one, `Table Grid` vs `Light Grid Accent 3`, `---` rendered as blank rather than underscores).
- **In sync content-wise?** Text matches the `.md` - **no stale paths found** (token scan: only one `10-year`, in module text). The drift here is purely structural/stylistic.

---

## 4. XLSX (1)

### excel/Electric_Data_Milestone_2_Updated.xlsx
- **Role:** The Milestone 2 update of the team's Dominion/PJM grid-context workbook, extended with the canonical contract import, lifecycle-cost and CO2e layers, and live reconciliation checks against the Python model.
- **Kind:** generated (`scripts/build_excel_workbook.py`) - but only *partly*: the script `shutil.copy(SRC, OUT)` from an untracked source workbook and then mutates it, so sheets 1–3 are inherited source data.
- **Reads:** n/a (data file). Its generator reads the team's original `Electric Data.xlsx` (**not tracked in this repository** - `scripts/build_excel_workbook.py:20–22`, `--source` is a required arg) plus `data/contract/v1/`.
- **Written by / read by:** written by `scripts/build_excel_workbook.py:27` (`OUT = REPO / "excel/Electric_Data_Milestone_2_Updated.xlsx"`). Referenced by `excel/README.md`, `scripts/README.md`, `docs/operations/reproduction-guide.md`, `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`.
- **Appears generated by `scripts/build_excel_workbook.py`?** **Yes - high confidence.** `docProps/app.xml` says `<Application>Microsoft Excel Compatible / Openpyxl 3.1.5</Application>`. `docProps/core.xml` shows `<dc:creator>Anna Parsons</dc:creator>` (the original author, carried over by the copy), `created 2026-07-09T17:48:56Z` (original workbook), `modified 2026-07-19T05:35:57Z` (the build run). Every string the script writes is present verbatim in the cells (e.g. the `dash["A3"]` planning-scenario notice).
- **Key contents:** 56,112 bytes, valid zip (`testzip()` → `None`), 32 entries. **9 sheets, in order:**

  | # | Sheet | `dimensions` | rows × cols | freeze | header row (verbatim) |
  |---|---|---|---|---|---|
  | 1 | `Dashboard` | `A1:O29` | 29 × 15 | - | R1: `Prince William County Grid Logistics and Forecasting Dashboard`, …, J1/K1 `Select Data Center Growth` / `Aggressive Growth` |
  | 2 | `Table012 (Page 39)` | `A1:C15` | 15 × 3 | - | R1: `Column1, Column2, Column3`; R3 real header `Generation Resource Type, Net Summer Capacity\n(MW), Percentage of Net Summer\nCapacity` |
  | 3 | `Electrification Engine` | `A1:O45` | 45 × 15 | - | R2: `Generation Resource Type, Net Summer Capacity (MW), Percentage of Net Summer Capacity, -, Unit Name, Location, Unit Class, Primary Fuel Type, C.O.D., MW Summer, -, -, YEAR, MONTH, PEAK_MW` |
  | 4 | `Canonical Scenarios (M2)` | `A1:R124` | 124 × 18 | `A5` | R4: `site_id, site_name, jurisdiction, horizon_year, scenario_name, ports_active, ports_pathway_capacity, sessions_per_day, energy_required_kwh_day, utilization, average_wait_minutes, peak_wait_minutes, capacity_basis, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd, net_co2e_kg, data_confidence, equity_indicator` |
  | 5 | `Lifecycle Costs` | `A1:G328` | 328 × 7 | `A5` | R4: `site_id, horizon_year, cost_case, escalation_case, lifecycle_cost_nominal_usd, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd` |
  | 6 | `Portfolio Cost Summary` | `A1:F13` | 13 × 6 | - | R4: `escalation_case, horizon_year, NPC STG (USD), NPC OVB (USD), NPC DEF (USD), Avoided cost OVB-STG (USD)` |
  | 7 | `Net CO2e` | `A1:E14` | 14 × 5 | - | R7: `horizon_year, case, energy_delivered_MWh_yr, net_CO2e_avoided_t_yr, avoided_active_EVSE_ports` |
  | 8 | `Assumptions & Sources` | `A1:D24` | 24 × 4 | - | R3: `Item, Value, Class, Source / vintage` |
  | 9 | `Reconciliation vs Python` | `A1:D10` | 10 × 4 | - | R4: `Check, Workbook value, Python/contract expectation, Status` |

- **Load-bearing specifics:**
  - **eGRID factor is correct and fully cited.** `Net CO2e!A4/B4` = `Grid factor (lb CO2e/MWh)` / **`596.3`**; `A5/B5` = `Factor vintage` / `eGRID2023r2 SRVC, accessed 2026-07-19`. Row 2 notice: *"596.3 lb CO2e/MWh - EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, accessed 2026-07-19. Refresh annually (eGRID2024 pending). Displacement assumptions: 9.5 kWh/session, 0.30 kWh/mi EV efficiency, 400 gCO2/mi displaced gasoline LDV."* **`590.2` appears nowhere in the workbook.**
  - **Horizons are canonical.** `Canonical Scenarios` `horizon_year` values are 2026 / 2036 / 2046 / 2056; `Portfolio Cost Summary` rows are (low|base|high) × (2036, 2046, 2056). No `2035`, no `2050`.
  - **Reconciliation checks (live formulas, 4 visible rows R5–R8, README claims six):** `2026 baseline starter ports` expects **25**; `2026 pathway ports` expects **48**; `Scenario rows` expects **120**; `Sites` expects **12**. Each `Status` cell is `=IF(ABS(Bn-Cn)<1,"PASS","FAIL")`.
  - Scenario table is 120 data rows (R5:R124) - matches the contract's stated 120 rows. `capacity_basis` column is present and reads `placeholder` on the rows I sampled (FFX002 2026/2036 base/high/stress_combined).
  - FFX002 2026 baseline row: `ports_active=2, ports_pathway_capacity=8, sessions_per_day=1.16, energy_required_kwh_day=11.02, utilization=0.0936, average_wait_minutes=0.8, peak_wait_minutes=1.31, net_co2e_kg=4180.5, data_confidence=Low, equity_indicator=0.66`.
  - Lifecycle discount/escalation constants in the R2 notice: *"NPC = net present cost, real discount rate 3.0% (planning assumption). Escalation cases: low 1% / base 2.5% / high 4%."* Cost cases `OVB` / `STG` / `DEF`.
  - `Dashboard!K2` holds the live selector formula `=IF(K1="Low Growth", 200, IF(K1="Medium Growth", 600, IF(K1="Aggressive Growth", 1200, 0)))`; K1 is currently `Aggressive Growth`.
  - `Assumptions & Sources` records `PWC share of zone peak = 6.5%` (planning proxy), `2047-2056 baseline = CAGR extrapolation (cell Engine!L14)` labelled extrapolation.
- **Notes:**
  - **Not reproducible from the repo alone.** `build_excel_workbook.py` hard-requires `--source <original "Electric Data.xlsx">`, and both `excel/README.md` and `scripts/README.md` state the original is not tracked. Anyone re-running the pipeline from a clean clone cannot rebuild this file.
  - `excel/README.md` says the Reconciliation sheet has **six** live checks; the sheet's used range is `A1:D10` with checks starting at R4/R5 - I read R4–R8 (header + 4 checks). Rows 9–10 exist within the dimension; I did not enumerate them, so the "six" claim is **unverified, not disproven**. Flagged as low-confidence.
  - Sheet 2 `Table012 (Page 39)` still has literal `Column1/Column2/Column3` in row 1 - an untidied import artifact inherited from the source workbook.

---

## 5. PNGs (14) - all decode cleanly

Every file opened and `.load()`-ed without error via Pillow. **All 14 are `format=PNG`, `mode=RGBA`, `dpi=(199.9996, 199.9996)`** and all carry a matplotlib provenance marker (`Software: Matplotlib version3.11.1, https://matplotlib.org/`, or the same string inside an XMP `xmp:CreatorTool` block).

| Path | px | mode | bytes | provenance chunk | referenced by |
|---|---|---|---|---|---|
| `dashboard/static/01_readiness_ranking.png` | 2750×1131 | RGBA | 183,217 | `Software` text chunk | `footer_log.json`, `scripts/build_static_dashboard.py`, PPTX slide 8 |
| `dashboard/static/02_starter_vs_pathway.png` | 2336×1131 | RGBA | 100,749 | `Software` | same + PPTX slide 9 |
| `dashboard/static/03_ports_three_horizons.png` | 2503×1131 | RGBA | 129,672 | `Software` | same + PPTX slide 11 |
| `dashboard/static/04_lifecycle_cost.png` | 2464×1131 | RGBA | 106,219 | `Software` | same + PPTX slide 11 |
| `dashboard/static/05_net_co2e.png` | 2750×1131 | RGBA | 136,745 | `Software` | same + PPTX slide 14 |
| `dashboard/static/06_avoided_evse.png` | 2372×1044 | RGBA | 105,655 | `Software` | same + PPTX slide 14 |
| `dashboard/static/07_peak_wait.png` | 2653×1044 | RGBA | 86,989 | `Software` | `footer_log.json`, generator, PDF - **not used in the deck** |
| `dashboard/static/08_limitations.png` | 1773×1090 | RGBA | 170,757 | `Software` | same + PPTX slide 15 |
| `dashboard/static/09_site_map_offline.png` | 2185×1309 | RGBA | 188,500 | `Software` | same + PPTX slide 9 + Timing_Runbook:65 |
| `docs/assets/architecture/integration_architecture.png` | 2928×1871 | RGBA | 397,317 | `Software` | `docs/README.md:18`, `docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md:6`, PPTX slide 13 |
| `docs/assets/readme/project-overview.png` | 1400×642 | RGBA | 126,246 | XMP + EXIF + sRGB | `README.md:10` |
| `docs/assets/readme/site-map.png` | 1200×719 | RGBA | 157,117 | XMP + EXIF + sRGB | **NOTHING - orphan** |
| `docs/assets/readme/three-horizons.png` | 1200×542 | RGBA | 117,473 | XMP + EXIF + sRGB | **NOTHING - orphan** |
| `presentation/assets/10_mcda_provisional.png` | 2700×1120 | RGBA | 162,772 | `Software` | filename referenced by nothing; **embedded in PPTX slide 6** (hash-verified); described only by directory in `presentation/README.md` |

- **Role (dashboard/static/01–09):** the nine contract-derived, footer-labelled, offline-openable presentation visuals. 01 readiness ranking, 02 starter vs pathway ports, 03 ports across the three horizons, 04 lifecycle cost, 05 net CO2e, 06 avoided EVSE, 07 peak wait, 08 limitations panel, 09 offline-rendered site map.
- **Kind:** generated. 01–08 by `scripts/build_static_dashboard.py` via `visuals.save(fig, OUT / "<name>.png", LOG)` (lines 53, 69, 90, 114, 135, 155, 173, 201); 09 by `gis_offline.build_site_map(s, OUT / "09_site_map_offline.png")` (line 209).
- **Kind (the other five):** `integration_architecture.png`, the three `docs/assets/readme/*.png`, and `10_mcda_provisional.png` are matplotlib output but **no script in the repo generates them.** I grepped every `*.py`, `*.sh`, `Makefile`, `*.yml` for writes to `docs/assets`, `presentation/assets`, `architecture/integration`, or `readme/` - zero hits. Only `make dashboard` → `scripts/build_static_dashboard.py` regenerates anything under this heading.
- **Notes:**
  - The three `docs/assets/readme/*.png` are the only PNGs carrying EXIF + XMP + `srgb` chunks and non-matplotlib-round dimensions (1400×642, 1200×719, 1200×542) - they were post-processed/resized after rendering. Consistent with hand-produced README hero images.
  - Nothing in the repo makes a size claim about any individual PNG, so there is no size claim to check against. (`scripts/verify.sh:62` only enforces "no tracked file over 25 MB"; the largest here is 397 KB.)

---

## 6. GLBs (12) - `incoming/explorer/fcf-3d/web/models/`

**All 12 pass full binary glTF 2.0 validation.** For each: magic `b'glTF'`, `version == 2`, **declared length == actual file size**, chunk walk yields exactly `[JSON, BIN]`, and the JSON chunk parses as valid UTF-8 JSON. `file(1)` independently agrees (`glTF binary model, version 2, length N bytes`). All 12 have distinct MD5/SHA-256 - no byte-identical duplicates.

- **Role:** one proposed-build massing model per candidate site - energised stalls now plus translucent "reserved" stalls for the pathway capacity the right-sizing model says to hold.
- **Kind:** generated. `asset.generator` on all 12 is `"fcf3d.glb (Future City Fellowship / ChargeReady NOVA)"`, `asset.version` `"2.0"`. Produced by `python -m fcf3d.build_models` → `fcf3d/geometry.py:build_site()` → `fcf3d/glb.py:write_glb()`.
- **Reads:** n/a. Their generator reads `web/data/sites.geojson` (`fcf3d/build_models.py:38–46`).
- **Written by / read by:** written by `fcf3d/build_models.py:45`. Read at runtime by `web/app.js:315` (`uri: \`models/${p.site_id}.glb\``) and surfaced in the detail panel at `web/app.js:642`. Cleaned by `Makefile:119`. Documented in `README.md:59` and `CLAUDE.md:21`. **They are `.gitignore`d - `fcf-3d/.gitignore:8` is `web/models/*.glb`. These are build outputs, not tracked assets.**

| file | bytes | JSON chunk | BIN chunk | node / mesh name | meshes | nodes | materials | primitives | accessors | bufferViews | buffers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FFX001.glb | 19,648 | 6,660 | 12,960 | `FFX001_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| FFX002.glb | 29,732 | 6,664 | 23,040 | `FFX002_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| FFX003.glb | 19,648 | 6,660 | 12,960 | `FFX003_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| FFX004.glb | 29,732 | 6,664 | 23,040 | `FFX004_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC001.glb | 18,180 | 6,632 | 11,520 | `PWC001_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC002.glb | 18,180 | 6,632 | 11,520 | `PWC002_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC003.glb | 15,296 | 5,908 | 9,360 | `PWC003_evse_build` | 1 | 1 | **8** | **8** | 24 | 24 | 1 |
| PWC004.glb | 19,648 | 6,660 | 12,960 | `PWC004_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC005.glb | 15,296 | 5,908 | 9,360 | `PWC005_evse_build` | 1 | 1 | **8** | **8** | 24 | 24 | 1 |
| PWC006.glb | 19,648 | 6,660 | 12,960 | `PWC006_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC007.glb | 19,648 | 6,660 | 12,960 | `PWC007_evse_build` | 1 | 1 | 9 | 9 | 27 | 27 | 1 |
| PWC008.glb | 15,296 | 5,908 | 9,360 | `PWC008_evse_build` | 1 | 1 | **8** | **8** | 24 | 24 | 1 |

- **Materials (identical PBR definitions across all files; the 8-material files simply omit `stall_future` because pathway == now):**
  `stall_ada` baseColor `[0.086,0.353,0.639,1.0]` metallic 0.0 rough 0.85 · `stripe` `[0.933,0.941,0.949,1.0]` 0.0/0.85 · `stall` `[0.18,0.196,0.22,1.0]` 0.0/0.9 · `stall_future` `[0.784,0.639,0.243,0.45]` 0.0/0.8 (**alpha 0.45 = the translucent reserved-capacity stalls**) · `pedestal` `[0.086,0.478,0.408,1.0]` 0.2/0.4 · `canopy` `[0.847,0.859,0.878,1.0]` 0.35/0.55 · `column` `[0.635,0.663,0.694,1.0]` 0.6/0.45 · `cabinet` `[0.31,0.345,0.396,1.0]` 0.45/0.5 · `transformer` `[0.502,0.522,0.545,1.0]` 0.55/0.6.
  `extensionsUsed` and `extensionsRequired` are **absent on all 12** - plain core glTF 2.0, maximum viewer compatibility. One scene, `scene: 0`, one node, one mesh, one buffer per file. No textures, no images, no animations, no cameras, no skins.
- **Content cross-check against `web/data/sites.geojson` - 12/12 CONSISTENT.** All 12 geojson `site_id`s have a GLB and every GLB has a geojson feature (empty symmetric difference). Per-site box counts decoded from POSITION accessor counts (24 verts per box) match `fcf3d/geometry.py`'s rules exactly - ADA stall count `max(1, ceil(n_total/25))` (line 113–119) and one wheel-stop stripe per stall (lines 167–176):

  | site | ports_now | pathway | stall_ada | stall | stall_future | stripe | pedestal | column |
  |---|---|---|---|---|---|---|---|---|
  | FFX001 | 2 | 4 | 1 | 2 | 3 | 4 | 1 | 4 |
  | FFX002 | 2 | 8 | 1 | 2 | 9 | 8 | 1 | 8 |
  | FFX003 | 2 | 4 | 1 | 2 | 3 | 4 | 1 | 4 |
  | FFX004 | 3 | 8 | 1 | 3 | 7 | 8 | 2 | 8 |
  | PWC001 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 4 |
  | PWC002 | 2 | 3 | 1 | 2 | 2 | 3 | 1 | 4 |
  | PWC003 | 2 | 2 | 1 | 2 | 0 | 2 | 1 | 4 |
  | PWC004 | 2 | 4 | 1 | 2 | 3 | 4 | 1 | 4 |
  | PWC005 | 2 | 2 | 1 | 2 | 0 | 2 | 1 | 4 |
  | PWC006 | 2 | 4 | 1 | 2 | 3 | 4 | 1 | 4 |
  | PWC007 | 2 | 4 | 1 | 2 | 3 | 4 | 1 | 4 |
  | PWC008 | 2 | 2 | 1 | 2 | 0 | 2 | 1 | 4 |

  **Column sums: ports_now = 25, pathway = 48.** The two headline portfolio numbers in the deck, the report, and the Excel reconciliation sheet are **independently confirmed by the 3D geometry**.
- **Geometry is metric and plausible:** canopy top at y 4.30–4.58 m, columns 0→4.30 m, cabinet 0→2.0 m, transformer 0→1.8 m, pad thickness 0.06 m, stripe at 0.06–0.16 m. `ADA_STALL_WIDTH = 4.90` m, standard stall narrower (`geometry.py:34`). FFX002/FFX004 (8 pathway stalls) span x −12.6→+12.6 m; PWC003/005/008 (2 stalls) span −4.4→+4.4 m.
- **Notes:**
  - Files with equal byte length have **identical geometry** (same accessor counts and bounding boxes) and differ only in the embedded node/mesh name string - e.g. FFX001 / FFX003 / PWC004 / PWC006 / PWC007 are all 19,648 bytes with byte-identical accessor min/max. That is expected: the massing is a pure function of `(ports_now, ports_pathway)`. Not a defect, but it means the models carry no site-specific site-plan information - only stall arithmetic. **They must not be presented as site plans.**
  - `web/data/manifest.json`: `schema_version "fcf3d/1.0.0"`, `generated_at "2026-07-26T04:27:14.192759+00:00"`, `site_count 12`, `score_min 29.6`, `score_max 58.8` (matches the deck's "FFX002 leads at 58.8"), `warnings []`, and a disclaimer stating *"Electrical service capacity is unconfirmed for all sites pending utility/facility review."* Source CSVs listed: `fixture_legacy_v2_site_results.csv`, `fixture_legacy_v2_right_sizing.csv`, `tbl_peak_waits.csv`, `tbl_avoided_evse.csv`, `scenario_table.csv`, `site_coordinate_sources.csv`, `tbl_readiness_confidence.csv`, `legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv`.
  - **Horizon violation in the model-build code path:** `fcf3d/build_models.py:43` falls back to `props.get("ports_2050")`, and `fcf3d/build_sites.py:437,465,466,473` read `recommended_ports_2050`, `ports_2050_base`, `ports_2050_high`. `2050` is not a canonical horizon and these are not labelled `legacy_v2`. (`docs/operations/v4-program/LEDGER.md:247` already notes `build_sites.py` `SOURCES` reads both conventions.) The currently committed GLBs are unaffected because `asset.ports`/`asset.pathway_ports` take precedence, but the fallback is live code.

---

## 7. Reference audit - orphans and dead references

### Orphans (binary exists; nothing in the repo names it)
| Binary | Status |
|---|---|
| `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf` | **0 referrers** |
| `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx` | **0 referrers** |
| `reports/milestone-2/Milestone_2_Gap_Closure_Status.docx` | **0 referrers** |
| `reports/milestone-2/FINAL_STANDARDS_APPLICATION_MATRIX.docx` | **0 referrers** |
| `reports/milestone-2/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx` | **0 referrers** |
| `docs/assets/readme/site-map.png` | **0 referrers, no generator** - true orphan |
| `docs/assets/readme/three-horizons.png` | **0 referrers, no generator** - true orphan |
| `presentation/assets/10_mcda_provisional.png` | **0 filename referrers**, but embedded in PPTX slide 6 (hash-verified) and described by directory in `presentation/README.md` - *soft* orphan, not dead |

The five `reports/milestone-2/` deliverables are the notable cluster: the Markdown twins are cited throughout the repo, the Word/PDF renderings are cited nowhere, and no Makefile target or reproduction-guide step rebuilds them.

### Dead reference (documented path that does not exist)
- `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:65` - *"Open all 11 files in `static_visuals/` directly"*. **`presentation/static_visuals/` does not exist**; `presentation/` contains only `assets/`, `deck/`, `README.md`. Post-reorg the 11 files are split: 9 PNGs + `STATIC_DASHBOARD.pdf` in `dashboard/static/`, and `10_mcda_provisional.png` in `presentation/assets/` (9+1+1 = 11, which is exactly the count the runbook still quotes). The same dead path is baked into the **PPTX slide 17 body text** and therefore into the exported deck PDF, where it cannot be fixed without rebuilding the deck.
- Because it is inside backticks rather than a Markdown link, `scripts/check_internal_links.py` cannot catch it.
- Related: runbook line 62 says *"Copy the whole `presentation/` folder to the presentation machine"*, but 9 of the deck's 10 source images now live outside `presentation/`. Harmless for rendering (images are embedded), but the instruction no longer means what it says.

### No reference points at a missing binary
Every binary path referenced in the repo resolves to a file that exists. No broken binary links found.

---

## 8. Cross-cutting findings

1. **`dashboard/static/footer_log.json` leaks the authoring machine's home directory - 9 times - and this makes `scripts/verify.sh` fail.**
   Each of the 9 entries has `"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png"` (lines 7, 14, 21, 28, 35, 42, 49, 56, 59).
   `scripts/verify.sh:59-60` defines the gate `hygiene: no local absolute paths in code/config` as `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'`. The pathspec **includes `*.json`**. I ran it: **9 hits, all in `dashboard/static/footer_log.json`. The gate fails today.**
   `docs/operations/reproduction-guide.md:93` nonetheless promises `./scripts/verify.sh` → `ALL REPOSITORY VERIFICATION GATES PASSED`. Direct contradiction.
   `docs/operations/v4-program/LEDGER.md:153` (FIND-REPO-03) already records this - but says **"six absolute authoring-machine paths"**. The true count is **nine**. LEDGER undercounts by 3.
   The path is also *stale* independently of being absolute: it names `visuals/static_dashboard/`, the pre-reorg directory. The current generator (`scripts/build_static_dashboard.py:24` `OUT = REPO / "dashboard/static"`, `src/fcf_m2/visuals.py:61` `entry["file"] = str(path)`) would today emit `…/repo/dashboard/static/…`. So `footer_log.json` is a **generated artifact that has drifted from its generator in two ways at once** and has never been regenerated since the repository reorganisation.
   The footer audit itself still passes because `audit_footer_metadata` only compares `Path(e["file"]).name`.
   Also note entry 9 (`09_site_map_offline.png`) has a different shape from entries 1–8 - it carries only `file`, `source`, `source_date`, with no `scenario` or `assumption` key.

2. **All four `reports/milestone-2/*.docx` are stale against their Markdown sources, and the report PDF inherits it.** See §3. The staleness is entirely the pre-reorg → post-reorg path rename set. No Makefile target, no CI step, and no line in `docs/operations/reproduction-guide.md` rebuilds these, so nothing would ever have caught it.

3. **Two of the four DOCX cannot be reproduced by the tracked converter at all.** `FINAL_STANDARDS_APPLICATION_MATRIX.docx` and `PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx` use `Heading 1/2/3` and table style `Table Grid`; the current `scripts/md_to_docx.py` emits `Title/Heading 1/Heading 2` and `Light Grid Accent 3` (lines 57, 68–76). Their `.md` sources also live in a **different directory** (`docs/standards/`) from the `.docx` outputs (`reports/milestone-2/`), so the twin relationship is non-obvious.

4. **The eGRID factor is clean everywhere it matters.** `596.3` is present in the PPTX (5 slides), the deck PDF (5×), the Excel `Net CO2e` sheet (`B4 = 596.3`, vintage `eGRID2023r2 SRVC, accessed 2026-07-19`), and `dashboard/static/footer_log.json` entry 5. **`590.2` occurs in exactly one place across all 38 binaries** - the Final Report DOCX/PDF, and only inside the sentence that records it as superseded. Phase 1 should decide whether that historical citation is permitted; it is not a live figure.

5. **Horizon convention is clean in the binaries.** `2036/2046/2056` from a `2026` baseline throughout the deck, the report, and the workbook. The only `2050` in any binary is the Final Report's note about a *fixed* MATLAB-adapter defect. The `10/20/30-year` phrasings I found are all explicit reconciliations to the canonical years, or are about model/goal duration rather than horizon labels. The one genuine convention problem is in **live explorer code**, not a binary: `ports_2050` / `recommended_ports_2050` / `ports_2050_base` / `ports_2050_high` in `fcf3d/build_models.py:43` and `fcf3d/build_sites.py:437,465,466,473`.

6. **Two artifacts have no editable ancestor in the repo.** `Future_City_Fellowship_Milestone_2_QA_Backup.pdf` has no `.pptx`. `Future_City_Fellowship_Milestone_2_Final.pptx` was made by python-pptx but the generating script is not tracked. Neither can be regenerated or edited from a clean clone.

7. **The workbook cannot be rebuilt from a clean clone.** `scripts/build_excel_workbook.py` requires `--source <original "Electric Data.xlsx">`, explicitly not tracked (`excel/README.md`, `scripts/README.md`).

8. **The GLBs are gitignored build outputs.** `fcf-3d/.gitignore:8` = `web/models/*.glb`. Any Phase 3 integration plan that assumes they travel with the repo is wrong; they must be rebuilt via `python -m fcf3d.build_models`.

9. **Office metadata is uniformly the library default.** All four DOCX say creator `python-docx`, created `2013-12-23`; the PPTX says lastModifiedBy `Steve Canny`, created `2013-01-27`, and app.xml claims 4:3 / 0 slides. Three of the four PDFs have no `/Title`. Cosmetic, but visible to any recipient who opens document properties on a client-facing deliverable.

---

## 9. Method notes / limits

- I did **not** read these files byte-by-byte (the lane explicitly says not to); I opened each with a format-aware parser and validated structure, metadata, and content, then cross-checked against the repo's own generators and data.
- PDF page-1 text is verbatim `pypdf` extraction. `STATIC_DASHBOARD.pdf` genuinely has no text layer - that is a property of the file, not an extraction failure (I confirmed by enumerating page XObjects and finding one full-page JPEG per page and nothing else).
- The DOCX in/out-of-sync judgement is from a real regeneration + structural diff, not inspection. Regenerated copies were written only to the scratchpad.
- `excel/README.md`'s claim of **six** reconciliation checks is unverified: I enumerated the header plus four checks (rows 4–8) within the `A1:D10` used range and did not read rows 9–10. Labelled uncertain.
- Reference counting used `grep -rIl --exclude-dir=.git -F <basename>` over the whole repo, so a referrer that constructs a path dynamically would be missed. The PPTX/PDF embedded-image check was done by SHA-256, which is exact.
