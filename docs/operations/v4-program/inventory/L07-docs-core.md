# LANE L07 — CORE DOCUMENTATION (Phase-0 ground-truth inventory)

Repo root: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (git clone, branch `v4-platform`,
HEAD `31b1628 docs(v4-program): AWS and live-site inventory from read-only discovery`).
All paths below are repo-relative unless stated. Read-only lane; nothing was modified.

**Files assigned: 22. Files read end to end: 22.** (18 markdown, 2 hash txt, 1 html, 1 generated md.)

Cross-checks were run against files OUTSIDE this lane (`src/fcf_m2/workflow.py`, `src/fcf_m2/config.py`,
`src/fcf_m2/emissions.py`, `src/fcf_m2/visuals.py`, `Makefile`, `scripts/verify.sh`,
`.github/workflows/tests.yml`, `data/contract/v1/*`, `dashboard/static/footer_log.json`,
`dashboard/tableau/patch_package/*.csv`, root `README.md`,
`reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`) purely to verify claims made by
lane files. Those files belong to other lanes; I did not inventory them.

---

## PART 1 — FILE-BY-FILE INVENTORY

### docs/README.md
- **Role:** Documentation index / hub page routing six reader personas (model users, technical reviewers, standards+safety reviewers, municipal stakeholders, human-action owners, maintainers) to the right document.
- **Kind:** authored
- **Reads:** n/a (pure navigation)
- **Written by / read by:** Hand-maintained. Linked from root `README.md`; every lane doc back-links to it as `[← docs index](../../../README.md)` or `(../README.md)`.
- **Key contents:** 36 lines, 22 outbound relative links. Sections: "Start here" (root README, reproduction guide, migration-from-v2), "For model users" (WORKFLOW_STEPS — *"generated — regenerate with `make docs`"*, `src/`, `data/`, `tests/` guides, current-facts register dated 2026-07-19), "For technical reviewers" (repository-migration-plan, legacy-baseline verification, technical integration architecture + `assets/architecture/integration_architecture.png`), "For standards / safety reviewers" (standards matrix, proposed-standard concept — explicitly *"fellowship design exercise, not a UL/ULSE proposal"*, risk register), "For municipal stakeholders" (3 milestone-2 briefs), "For human-action owners" (open-human-actions — *"the ten things software cannot close"*; human-actions README — *"all drafts, nothing sent"*), "For maintainers" (website patch package — *"nothing deployed"*, scripts guide, CI workflows).
- **Notes:** **All 22 relative links resolve** (verified programmatically). The "ten things" claim matches `open-human-actions.md` exactly (10 numbered rows). The six named human-action packages match the six directories under `docs/human-actions/`. No horizon years appear except the 2026-07-19 verification date. This file is clean.

### docs/WORKFLOW_STEPS.md
- **Role:** Human-readable list of the V3 workflow's 11 steps, emitted from the executable step manifest so the docs cannot drift from the code.
- **Kind:** **generated** — generator is `fcf_m2.workflow.generate_docs()` (`src/fcf_m2/workflow.py:52-59`), invoked by `make docs` → `python -m fcf_m2.workflow docs` → writes `ROOT / "docs/WORKFLOW_STEPS.md"` (`src/fcf_m2/workflow.py:380`).
- **Reads:** `fcf_m2.workflow.STEPS` (`src/fcf_m2/workflow.py:37-49`).
- **Written by / read by:** Written by `make docs`. Read by `scripts/verify.sh` gate *"docs: generated workflow steps match the executable manifest"*, and linked from `docs/README.md:11`.
- **Key contents — RECORDED FOR DRIFT DETECTION:**
  - Header line 1: `# V3 Workflow Steps (generated from fcf_m2.workflow.STEPS — do not edit by hand)`
  - Line 3: **`Step count: **11**`**
  - The exact 11 step names and descriptions currently in the file:
    1. `load_inputs` — Load site table, electrical-risk fixture, provenance, anchors, MATLAB site meta
    2. `score_sites` — Score readiness (legacy min-max or V3 fixed anchors) + Erlang-C port screen
    3. `right_sizing` — Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056)
    4. `confidence` — Structured field-level data confidence (V3) / legacy confidence passthrough
    5. `peak_wait` — Peak-window Erlang and seeded discrete-event wait simulation (P10/P50/P90)
    6. `economics` — Lifecycle NPC: staged vs overbuild vs defer at 2036/2046/2056, low/base/high
    7. `emissions` — Net avoided CO2e with sourced grid factor + avoided-EVSE resource metric
    8. `scenario_table` — Assemble canonical scenario rows (all required contract fields)
    9. `contract` — Validate + write versioned hybrid CSV/JSON contract with manifest hashes
    10. `matlab_adapter` — Generate MATLAB input CSV from the contract (capacity_basis on every row)
    11. `summary` — Write run summary with headline totals and claims-discipline labels
- **Notes:** **Currently in sync.** I diffed the file against `STEPS` at `src/fcf_m2/workflow.py:37-49` line by line — all 11 names and all 11 description strings match byte-for-byte, and `len(STEPS) == 11`.
  **The step-count gate is weaker than the file implies.** `scripts/verify.sh` only asserts the substring `Step count: **11**` is present:
  `'$PY' -c 'from fcf_m2 import workflow; d=open("docs/WORKFLOW_STEPS.md").read(); assert f"Step count: **{len(workflow.STEPS)}**" in d'`
  It does **not** compare step *names* or *descriptions*. Renaming a step or editing a description drifts silently. Phase 1 should strengthen this to `assert generate_docs() == open(...).read()`.
  Step 3's `legacy 2035/2050` is a **legitimate** legacy-mode reference (see horizon audit, Part 3).

### docs/migration-from-v2.md
- **Role:** User-facing V1/V2 → Milestone-2-V3 migration guide: what changed behaviourally, old→new commands, old→new paths, legacy-vs-V3 result differences, breaking changes, and how to reproduce each behaviour. **Phase 4 must write `migration-from-v3.md` to match this structure.**
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Hand-maintained; linked from `docs/README.md:8` and `docs/repository-migration-plan.md:7`.
- **Key contents (74 lines) — STRUCTURE AND SPIRIT FOR PHASE 4 TO MIRROR:**
  - **Title + back-link:** `# Migrating from the V1/V2 prototype to Milestone 2 V3` then `[← docs index](../../../README.md)`.
  - **Opening reassurance paragraph (lines 5-10):** states which branch/tree was replaced, then the load-bearing sentence **"**Nothing was lost:** full history is intact, the pre-restructure state is preserved on branch `archive/pre-milestone2-v3-20260719` and tag `pre-milestone2-v3-20260719`, and the accepted V2 results remain reproducible from this codebase's `legacy_v2` mode (golden-tested)."**
  - **`## What changed`** — a 9-row before/after table with columns `| Area | V1/V2 (before) | V3 (now) |`. Rows: Package, Horizons, Scoring, Data confidence, Waits, Economics/emissions, Cross-model, Tests, GIS. Each cell names the *concrete mechanism*, not a slogan (e.g. Scoring: "cohort-relative min-max (adding a site changed every score)" → "fixed benchmark anchors (`data/anchors/anchor_set_v1.json`), cohort-independent; legacy behavior retained in `legacy_v2` mode").
  - **`## Old commands → new commands`** — 5-row table `| Task | V2 command | V3 command |`: Full run (`python src/run_v2.py` → `make run-v3` or `python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run`), Legacy-equivalent run (→ `make run-legacy`), Output checks (`python src/check_outputs_v2.py` + `compare_v2_to_baseline.py` → `make test` + `./scripts/verify.sh`), Tableau inputs (`python src/build_tableau_exports.py` → contract-derived CSVs in `dashboard/tableau/patch_package/`), Docs of steps ("hand-maintained (drifted)" → `make docs`).
  - **`## Old paths → new paths`** — 5-row `| Old | New |` table, including the honest "not carried" entry for the `.twbx`.
  - **`## Legacy results vs V3 results`** (lines 46-57) — the epistemic core. States legacy reproduces **bit-for-bit** (FFX002 top at 58.8; 25 starter / 48 pathway ports), that V3 anchor scores differ **"*by design*"**, that every rank change is explained in the generated `scoring_migration_report.csv`, that the accepted 25/48 structure is "deliberately retained pending a documented re-baselining decision", and that growth multipliers (**2036: 1.9/2.6 · 2046: 3.0/4.5 · 2056: 4.0/6.0, stress ×1.15**) are "provisional planning conventions, not calibrated forecasts".
  - **`## Known breaking changes`** — 4 numbered items (V2 entry points gone; outputs no longer committed; 2035/2050 column names replaced; hand-built MATLAB adapter CSV gone, regenerated at `data/outputs/v3_run/matlab_scenarios.csv` with tracked copy at `matlab/data/canonical/matlab_scenarios.csv`).
  - **`## How to reproduce each behavior`** — 2 bullets: **Legacy:** `make run-legacy` or check out `archive/pre-milestone2-v3-20260719` / `v2-expansion-planning`; **V3:** `make run-v3 && make validate`.
  - **Spirit:** every claim is falsifiable and points at a command, a test, a branch, or a file. It never says "improved"; it names the mechanism and the guarantee. It preserves the old thing rather than deleting it, and it labels provisional things as provisional.
- **Notes:** **Verified true:** branch `remotes/origin/archive/pre-milestone2-v3-20260719`, `remotes/origin/v2-expansion-planning`, and tag `pre-milestone2-v3-20260719` all exist in the clone. Growth multipliers match `src/fcf_m2/config.py:42-51` exactly (`V3_GROWTH_MULTIPLIERS`, `V3_STRESS_EXTRA = 1.15`). Make targets `run-v3`, `run-legacy`, `test`, `validate`, `docs`, `verify` all exist in `Makefile`. `dashboard/tableau/patch_package/` exists. `data/anchors/anchor_set_v1.json` exists. The 2035/2050 mentions are all correctly framed as before-state/legacy.
  Note for Phase 4: a `pre-v4-program-20260727` tag already exists — the same "nothing was lost" pattern is already set up for the V3→V4 migration.

### docs/repository-migration-plan.md
- **Role:** The mechanical companion to migration-from-v2.md — what happened to every *class* of pre-existing and implementation content when the Milestone-2 implementation workspace was mapped into this repo on 2026-07-19.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Hand-maintained; linked from `docs/README.md:16` and back-referenced by `migration-from-v2.md`.
- **Key contents (61 lines):** Five disposition buckets — **Retain unchanged** (V1 `main` tree + V2 `v2-expansion-planning` branch via history/archive branch/annotated tag; existing tags `v1-demo-scalability-ready`, `v1-review-ready` untouched); **Replace** (root README/docs/`model-check.yml` → new landing page + docs index + `tests.yml`/`matlab-manual.yml`; loose `src/*.py` → `src/fcf_m2/`); **Move** (`repos/python_m2_v3/{src,tests,data,pyproject,lockfile}` → `src/`,`tests/`,`data/`,root · `data_contract/v1` → `data/contract/v1` · `repos/matlab_simulink_m2_v3` → `matlab/` + `.github/workflows/matlab-manual.yml` manual-trigger · reports/standards/risk/briefs → `reports/milestone-2/` + `docs/standards/` · deck → `presentation/deck` + `presentation/assets` · dashboard + Tableau blocker/patch → `dashboard/` · Excel → `excel/` · human-action packages → `docs/human-actions/`, website patch → `docs/operations/website-patch-package/`, open-actions + reproduction guide + legacy-baseline evidence → `docs/operations/` · build scripts `build_excel`/`build_static_dashboard`/`md_to_docx` → `scripts/`, **"rewritten to repo-relative paths (no machine-specific paths remain)"**); **Archive in Git history only**; **Exclude from Git** (`_working/`, `source_snapshots/`, duplicate legacy repo copies, run ledgers/manifests of the Claude implementation process, research working archive, raw interview/transcript sources, send logs, venvs, caches, release ZIPs; full-US TIGER boundary file → filtered extract documented in `data/cache/boundaries/ATTRIBUTION.md`; legacy Tableau `.twbx`); **Include as a release artifact instead of source** — "None at this time", `scripts/build_release_artifact.py` can produce a hash-logged bundle locally.
  Closing `## Selection principles applied` (lines 57-61): "One canonical Python codebase, one MATLAB codebase, one contract, one source of truth per report/chart/dataset; no nested repositories; no generated outputs except small, reviewer-relevant final deliverables (deck, dashboard, workbook, reports); **no secrets, no local paths**, no files near GitHub size limits."
- **Notes:** **The "no machine-specific paths remain" / "no local paths" claim is FALSE as of HEAD.** Tracked file `dashboard/static/footer_log.json` contains nine `"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/*.png"` entries (lines 7, 14, 21, 28, 35, 42, 49, 56, 59). See Finding F-02. All other referenced targets verified to exist (`scripts/build_release_artifact.py`, `matlab/`, `excel/`, `presentation/deck`, `.github/workflows/matlab-manual.yml`, `data/cache/boundaries/ATTRIBUTION.md`).

### docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md
- **Role:** Narrative technical architecture — the utility→governance chain, the eight interfaces that must be explained, the responsibility register, and the failure-mode headline for the presentation.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:18` alongside `docs/assets/architecture/integration_architecture.png`.
- **Key contents (52 lines):** Header block gives Project / **Date: 2026-07-19** / **Status: "Design intent pending AHJ/utility confirmation. Service capacity is unconfirmed at 12/12 candidate sites; nothing here is an as-built description."** / Basis: *Report 07*, `rankings/FAILURE_MITIGATION_OPTIONS.csv`, EX16 (protocols), EX12 (Dominion programs) / Companion visual `../assets/architecture/integration_architecture.png`.
  **§1 System context** — 8 numbered layers: (1) Dominion service→transformer/feeder→service entrance (both jurisdictions Dominion territory, EX12; Dominion L2 make-ready program includes interconnection review); (2) service entrance/panel→metering + submetering (**2020 NEC as adopted via the 2021 USBC**); (3) load management / CMS with documented default-safe curtailment profile above hardwired overcurrent protection; (4) EVSE ports (**UL 2594-listed, UL 2231 personnel protection embedded**), **AC Level 2 only**; (5) communications — **OCPP** charger↔backend, **ISO 15118 / J1772** vehicle↔charger, "supporting industry protocols, not ULSE standards (EX16)"; (6) users — **11 surface-lot sites and one commuter garage (PWC002 Neabsco)**, county fleet hub coordination-only; (7) emergency disconnect + responder access (proposed-standard Module 1, Fire Marshal pre-plan walkthrough); (8) monitoring/decision-support layer feeding expansion triggers.
  **§2 Interface register** — 8 rows `| # | Interface | What crosses it | Owner | Failure question |`. Interface 1 flags **"Unconfirmed at 12/12 sites — the highest-value single data request in the project"**. Interface 8 asks "Who owns the stop/go call?".
  **§3 Responsibility register** — 9 rows `| Element | Design responsibility | Operating responsibility | Approval / oversight authority |`. Includes **"NEVI 97% uptime as benchmark practice"** and marks *Board of County Supervisors / City Council via CIP* as **"the human stop/go authority"**.
  **§4 Failure-mode headline** — three client-resonant failure modes: **overbuild/underuse (Neabsco decommissioning)**, **cost blowout via trenching distance (McCoart)**, **inaccessible/unclear shutdown (Adams interview)**. Top-5 mitigations ranked: (1) default-safe curtailment on comms loss; (2) verified/labeled/illuminated emergency disconnect at commissioning; (3) service-capacity confirmation before design freeze; (4) dual-path utilization logging; (5) ADA-first site layout. Closes: "Every mitigation is design intent pending AHJ/utility confirmation."
- **Notes:** **Dead reference:** `rankings/FAILURE_MITIGATION_OPTIONS.csv` (line 5) and `FAILURE_MITIGATION_OPTIONS.csv` (line 52) — **this file does not exist anywhere in the repo** (`find . -iname "*FAILURE_MITIGATION*"` returns nothing). The doc says the full mitigation ranking lives there and is "carried into `RISK_REGISTER.csv`"; only `reports/milestone-2/RISK_REGISTER.csv` exists. See Finding F-04. The companion PNG *does* exist (`docs/assets/architecture/integration_architecture.png`, 397 KB). No horizon-year issues. No headline numbers requiring contract trace.

### docs/methodology/current-facts-source-register.md
- **Role:** Primary-source verification register (IM-01…IM-10) for every time-sensitive fact embedded in final artifacts. **This is the authoritative source for the eGRID factor.**
- **Kind:** authored (data-contract-adjacent — it is the citation of record for `data/contract/v1/contract_manifest.json:grid_factor`)
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:13`; cited by ID from `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md` (IM-02/03/04/05/10) and `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` (IM-02, IM-03, IM-09).
- **Key contents (16 lines, 10 rows). Verified 2026-07-19. Continues the research package's EX register (EX01–EX16); IM = implementation-run verification. Per master prompt §4.5.**
  - **IM-01 — grid emissions factor, SRVC:** **596.3 lb CO2e/MWh** (total output emission rate, CO2e), **eGRID2023 Rev 2** (data year 2023; initial release 2025-01-15, Rev 2 2025-06-12). Source: EPA eGRID summary data, epa.gov/egrid/summary-data. **Correction note:** "research register EX10 carried ≈**590.2**; EPA's published CO2e total output rate for SRVC is **596.326** lb/MWh. All implementation artifacts use 596.3 with vintage. eGRID2024 preliminary data exists via API (≈−1.8% CO2e avg) but is not the official release; annual refresh field included in model."
  - **IM-02 — Access Board EVSE accessibility rule:** still at **NPRM** (published 2024-09-03, comments closed 2024-11-04); **no final rule as of 2026-07-19**; DOJ rulemaking would follow.
  - **IM-03 — Virginia building code:** **2021 USBC effective 2024-01-18** (2020 NEC basis; VCC §406.2.7 EV provisions); permits solely under 2021 USBC since 2025-01-18; **2024 code-development cycle underway** (NOIRA approved 2025-03-10; proposals due 2025-10-01; **expected conclusion ≈2027**).
  - **IM-04 — UL 2594:** 3rd edition, **2022-12-15** (AC EVSE ≤1000 V), current.
  - **IM-05 — UL 3600:** published **2023-01-09** (ANSI/UL 3600, Measuring and Reporting Circular Economy Aspects of Products, Sites and Organizations).
  - **IM-06 — NEVI:** FY2026 **$885M** apportioned (Oct 2025 FHWA); Aug 2025 interim guidance in force; **Virginia among states anticipated to release solicitations Q1 2026**; history volatile (Feb 2025 freeze → June 2025 court-ordered release). Sources FHWA/USDOT, AFDC law 12744, GAO B-337137. "Present only with volatility caveat."
  - **IM-07 — Dominion Level 2 Charging Program:** **50%** upfront make-ready incentive, remainder on-bill over 10 years; **100%** for disadvantaged-community participants; Fleet Charging Program + EV Charging Access Program also active. Sources dominionenergy.com, AFDC 13363.
  - **IM-08 — FY2027 budgets:** Fairfax City GF ≈**$207.5M** (adopted 2026-05-05); PWC GF revenues ≈**$1.955B** (adopted 2026-04-21). From research register EX13; "line-item fund for a pilot unconfirmed."
  - **IM-09 — Fellowship requirements:** Phase 2 = CM2 content, 2+ alternatives, **two aspects at 10/20/30-year timelines**, ≥2 highlighted ULSE standards + 1 proposed standard with tests (EX01, verbatim PDF extraction).
  - **IM-10 — conditional standards:** UL 2231 2021 eds; UL 2202 2022 ed (DC only); UL 9540A 5th ed 2025-03-12 (6th-ed activity 2026); NFPA 855 2026 ed — all conditional on BESS/DCFC entering scope, **currently out of scope, `battery_storage_flag=0` at all 12 sites**. "Conditional standards must not be presented as active scope."
- **Notes:** **596.3 confirmed as the live value:** `src/fcf_m2/config.py:91 GRID_FACTOR_LB_PER_MWH = 596.3`; `data/contract/v1/contract_manifest.json` `grid_factor.value_lb_per_mwh = 596.3`, `vintage = "eGRID2023r2, accessed 2026-07-19"`, `source = "EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, total output emission rate CO2e"`; `data/contract/v1/assumptions.json:64 "grid_factor_value": 596.3`. **590.2 survives nowhere as a live value** — a repo-wide grep finds it only in four explicit correction notes (`CHANGELOG.md:24`, this file line 7, `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22`, `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`) plus one Phase-0 discovery note (`docs/operations/v4-program/AWS_INVENTORY.md:140`). All correct.
  IM-09's "10/20/30-year timelines" is the *fellowship's own requirement wording* and is the origin of the 2026→2036/2046/2056 convention, not a horizon violation.
  Staleness watch for later phases: IM-02 (rule status), IM-03 (2024 VA cycle ≈2027), IM-06 (NEVI Q1-2026 solicitations — that date is now past relative to today, 2026-07-27), IM-01 (eGRID2024 may have become official).

### docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md
- **Role:** The narrative rendering of the machine standards register — which standards apply, at what edition, in what role, at every lifecycle stage, and who decides.
- **Kind:** authored (explicitly declares itself the prose twin of a data-contract file)
- **Reads:** n/a, but declares consistency with `data/contract/v1/standards_register.csv`
- **Written by / read by:** Linked from `docs/README.md:21`; summarised for the public site by `docs/operations/website-patch-package/content/standards_summary.md`.
- **Key contents (159 lines):** Header: Date **2026-07-19**; **Status: "Design intent only — no permit has been applied for, no equipment has been procured, and nothing in this matrix constitutes achieved compliance."** **Consistency note (line 5): "This matrix is the narrative rendering of the machine register `data/contract/v1/standards_register.csv` (identical standards set, roles, editions, and applicability flags for all 12 candidate sites)."** Evidence: EX01, EX03–EX09, EX16 + IM-02/03/04/05/10.
  **§1 Standards set at a glance** — 9 rows `| Standard / instrument | Role in this plan | Adopted / governing edition (Virginia, 2026-07-19) | Latest published edition | Applicability at the 12 candidate sites |`:
  - **UL 2594** — *highlighted safety standard* — 3rd ed. 2022-12-15 — Active, governs AC Level 2.
  - **UL 3600** — *highlighted sustainability standard (voluntary)* — 1st ed. 2023-01-09 — Active, program-level circularity frame.
  - UL 2231-1/-2 — essential supporting (embedded in EVSE listing) — 2021 eds.
  - **NEC Article 625 (NFPA 70) as adopted in Virginia** — **2020 NEC via 2021 USBC, effective 2024-01-18**; "2023 NEC published; **not adopted in Virginia**".
  - Virginia USBC / SFPC — 2021 eds effective 2024-01-18; permits solely under 2021 USBC since 2025-01-18; 2024 cycle ≈2027.
  - US Access Board EVSE accessibility guidance — TA doc 2022; rule at NPRM 2024-09-03, no final rule as of 2026-07-19.
  - **OCPP + ISO 15118** — "supporting interoperability **protocols — explicitly NOT ULSE standards** (EX16)".
  - UL 2202 — **conditional**, out of scope (no DCFC).
  - UL 9540 / 9540A + NFPA 855 — **conditional**, out of scope, `battery_storage_flag=0` at all 12 sites.
  **Adopted-vs-latest discipline (line 24, "must be stated in every presentation"):** Virginia enforces the 2020 NEC through the 2021 USBC; the 2023 NEC "is not law in Virginia; designing or presenting to a non-adopted edition invites AHJ rejection."
  **§2 Lifecycle application matrix** — eight subsections §2.1–§2.8, each an 11-row stage table (Design, Procurement, Certification, Installation, Commissioning, Operation, Emergency response, End of life, Evidence of adherence, Deciding authority, Open questions). §2.4 names the deciding authorities as *Fairfax City Code Administration; PWC Building Development Division*; §2.5 names *Fairfax City Fire Marshal; PWC Fire Marshal's Office* and flags **PWC002 Neabsco as "the single enclosed candidate"**. §2.8 is the conditional-standards table.
  **§3** — decisions that remain with AHJ/Fire Marshal. **§4 Value proposition** — "the client's ADA-driven fleet-hub redesign cost a full year (EX09)"; "**the county has already decommissioned 17 stations**"; "Framed as avoided-redesign and avoided-incident exposure, **not quantified ROI** — no defensible local incident-cost data exists (Report 06, §5)."
- **Notes:** `data/contract/v1/standards_register.csv` exists, so the consistency claim is at least addressable — **I did not diff the two** (the CSV is another lane's file); Phase 1 should verify the "identical standards set, roles, editions, and applicability flags" claim row by row. Cited reports ("Report 06", "Report 07", "Report 10") are research-package documents not present in this repo — they are cited as external evidence, not as repo paths, so this is not a broken link. No horizon-convention issues. No numbers requiring contract trace.

### docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md
- **Role:** The fellowship's required "one proposed standard with tests" — a site-level (not product-level) municipal EV charging readiness and emergency-access standard concept, with 7 test modules, 3 conformance levels, and inspection intervals.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:22`; summarised in `docs/operations/website-patch-package/content/standards_summary.md` (which is required by `PATCH_GUIDE.md:36` to keep the disclaimer label verbatim).
- **Key contents (111 lines):**
  - **Mandatory label, stated twice (lines 3 and 111):** "This is a **Future City Fellowship design exercise, not an official UL/ULSE proposal.** It has no regulatory force. Every provisional parameter marked **TBV** requires validation by ULSE, the manufacturer, the adopted code, or the local AHJ before any real-world use."
  - **Integrity rule (line 7):** "**No numeric safety limit is invented in this document.** Sourced parameters cite the adopted code by name and edition; everything else is marked **TBV**."
  - **§1 Purpose:** the four documented failure classes — responders who cannot find/operate a disconnect (Adams interview), sites overbuilt then decommissioned (**Neabsco; 17 stations removed**), ADA layouts reworked after design freeze (**fleet hub, one year lost**), undocumented comms-loss behaviour. "UL 2594 certifies the *equipment*; this concept addresses the *site*."
  - **§2 Scope:** covered = publicly owned/operated municipal sites, new + retrofit, **AC Level 1/2**. Reserved annexes = DCFC (UL 2202), BESS (UL 9540/9540A + NFPA 855), private/residential, fleet-only depots. Lifecycle: site selection → design → commissioning → operations/monitoring → expansion → decommissioning.
  - **§3 Seven modules**, each a `| Test category | Verification method | Parameter basis |` table:
    - **M1 Emergency access and disconnect (flagship)** — apparatus approach (sourced: 2021 VA SFPC eff. 2024-01-18); disconnect location/labeling (sourced: NEC 625 as adopted, 2020 NEC via 2021 USBC; legibility distance **TBV**); disconnect operation timed drill by non-specialist (**target time TBV**; responder time-study literature is a named research gap); illumination (**level TBV** — "reference existing egress-lighting practice in the adopted code, **do not invent a lux value**"); responder placard (content sourced from fire-department pre-plan practice, format TBV).
    - **M2 Expandability and right-sizing documentation** — pathway capacity declaration; utilization monitoring via OCPP ("**not a ULSE standard**"; minimums TBV, benchmark NEVI); **expansion triggers with an equity override** ("trigger values are **municipality-set**, not standard-set"); overload protection coordination (sourced: NEC load-calc as adopted).
    - **M3 Accessibility and site conditions** — accessible route/space/reach by reference to Access Board TA 2022 / NPRM 2024-09-03 (still NPRM as of 2026-07-19, IM-02) + VA USBC ADA; impact protection; enclosure/garage trigger (**one enclosed candidate: PWC002 Neabsco**); stormwater/firewater (sourced: VSMP-delegated local program).
    - **M4 Monitoring and expansion triggers** — dual-path logging (network + independent local meter, monthly export to municipality-owned storage; retention TBV); trigger evidence chain; **data staleness control** ("Every published figure carries source date; refresh checklist executed"; annual minimum recommended for grid factors).
    - **M5 Managed-charging fail-safe** — comms-loss default-safe profile (**never exceeding the NEC-calculated circuit limit**); hardwired protection independence ("sourced: NEC baseline requirement — **non-negotiable**"); local fallback service.
    - **M6 Commissioning and evidence package** — listing verification (UL 2594 3rd ed. 2022-12-15; UL 2231-1/-2 2021 eds.); inspection records (2021 VA USBC/SFPC); module test records M1–M5; fire-department pre-plan walkthrough.
    - **M7 Materials, take-back, end of life** — circularity disclosure (sourced framing: **UL 3600 1st ed. 2023-01-09**); take-back/recycling route; replacement planning (**~10-year electronics refresh horizon**, EX15 class, exact interval TBV); decommissioning plan (template: "the county's own 17-station decommissioning experience").
  - **§4 Conformance levels:** **Ready-Basic** (M1 + M3 + M6) → **Ready-Expandable** (+ M2, M7) → **Ready-Managed** (+ M4, M5 demonstrated). "The staged pilot targets **Ready-Managed** at pilot sites."
  - **§5 Inspection intervals (provisional — TBV):** Commissioning = all modules; Annually = M1 labels/lighting/access + M4 data-continuity + M7 circularity; On any expansion event = M2 re-verification; **On code-edition change (e.g. conclusion of Virginia's 2024 code cycle ≈2027, or Access Board final rule) = M3 cross-references re-checked**.
  - **§6 Research still needed:** (1) adopted-edition citation compilation per jurisdiction; (2) responder time-study literature; (3) monitoring-data minimums vs NEVI; (4) ULSE Standards Academy feedback — "**as a fellowship learning exercise, not a submission.**"
  - Basis line cites appendix `PROPOSED_STANDARD_RESEARCH_SPECIFICATION.md` (a research-package document, not in this repo).
- **Notes:** Discipline is excellent — every non-sourced parameter is marked TBV and the doc explicitly refuses to invent a lux value or a response time. The "~10-year electronics refresh horizon" is an *equipment* interval, not a planning horizon; **not** a horizon-convention violation. Module 4's "data staleness control" is effectively the project's own self-imposed rule that later phases must honour (every figure carries a source date).

### docs/operations/legacy-baseline/BASELINE_VERIFICATION.md
- **Role:** Frozen evidence that the V1 and V2 legacy code were actually re-run and reproduced the accepted numbers — the provenance for the golden fixtures this repo is tested against.
- **Kind:** authored (evidence record)
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:17`; the numbers it freezes are enforced by `tests/test_legacy_golden.py`, `Makefile:run-legacy`, `scripts/verify.sh`, and `.github/workflows/tests.yml`.
- **Key contents (36 lines):** Reproduced on **disposable copies** of V1/V2 legacy code in the pre-publication implementation workspace, **Python 3.14.6**, dedicated legacy venv (unpinned legacy requirements + GIS extras). Full run logs (`legacy_v1_run.log`, `legacy_v2_run.log`) were retained *in that workspace* and are **not tracked here**; only the hashes are.
  - **Python V1** (`Future-City-Fellowship--main`): `src/run_all.py` completed; `src/check_outputs.py` **Result: PASSED**; sanity check PASSED.
  - **Python V2** (`Future-City-Fellowship--2-expansion-planning`): `src/run_v2.py` **all 25 steps completed (exit 0)**, including GIS decision map (online TIGER + basemap download); `src/check_outputs_v2.py` **Status: PASSED** (12/12 sites, package hash-synced); `src/compare_v2_to_baseline.py` all guardrails **PASS**; `build_tableau_exports.py` + `check_tableau_exports.py` **15/15 exports, 12/12 sites, PASSED**.
  - **Headline metrics table (10 rows, "all match expected values exactly"):** Sites **12/12**; Top site **FFX002 ≈58.8** → "FFX002 City of Fairfax Regional Library 58.8 (Medium confidence)"; High-confidence sites **0/0**; Starter ports **25/25**; Future-ready pathway ports **48/48**; **2035 base / 2035 high / 2050 base / 2050 high = 35 / 44 / 44 / 54** (both columns); Data-quality findings **38 REVIEW + 12 INFO**; Tableau exports **15/15**; Deliverable package files **35/35**.
  - **Offline behavior:** first full run required internet (TIGER county boundary + basemap tiles at runtime); a later `plot_site_decision_map.py` run with all HTTP(S) proxies at a dead port **succeeded** because the boundary zip was cached; "**Cold offline environments still fail** — confirming the PY-06 finding that the fix is shipping cached boundaries + a documented offline mode."
  - **MATLAB/Simulink** (`MATLAB-SIMULINK--main-2`): "**No MATLAB installation available in this environment. No simulation was executed and none is claimed.**" Static inspection only; `.slx` verification **blocked**; commands for a licensed runner in `matlab/RUN_ON_LICENSED_MATLAB.md`.
  - **Output hash freeze:** `v1_output_hashes.txt` (**14 files**), `v2_output_hashes.txt` (**71 files**) — SHA-256 of all CSV/JSON/MD outputs.
- **Notes:** File counts verified — `v1_output_hashes.txt` has exactly 14 lines, `v2_output_hashes.txt` exactly 71 lines. ✓ The 2035/2050 row (line 22) is legitimate legacy content in a document whose title and every section are about the legacy baseline; it is *not* labelled with the literal token `legacy_v2` though — see horizon audit note H-1. The `src/run_*.py` backticked paths do not exist in this tree **by design** (migration-from-v2.md documents their removal). This is the origin of the **35 / 44 / 44 / 54** legacy port figures, which are distinct from and must not be confused with the V3 contract's **35 / 44 / 44 / 48** structure.

### docs/operations/legacy-baseline/v1_output_hashes.txt
- **Role:** Frozen SHA-256 manifest of the 14 output files produced by the reproduced V1 legacy run.
- **Kind:** generated (produced by hashing the reproduced V1 run outputs in the pre-publication workspace; the generating script is not in this repo)
- **Reads:** n/a
- **Written by / read by:** Referenced by `BASELINE_VERIFICATION.md:36`. Nothing in the repo appears to *verify* against it — the paths it names (`data/outputs/*`) are gitignored and regenerated, so these hashes are historical evidence, not an active gate.
- **Key contents:** 14 lines, `sha256  path` format, all under `data/outputs/`: `action_matrix.md`, `baseline_comparison.csv`, `baseline_comparison.md`, `data_quality_report.csv`, `model_run_summary.md`, `profile_comparison.md`, `profile_rank_summary.csv`, `profile_results.csv`, `README.md`, `results_interpretation.md`, `sensitivity_results.csv`, `sensitivity_summary.csv`, `site_results.csv`, `workflow_success.json`. Example: `a3817a131805bceebc2c42069ebb9765c732fa185412f8dbf2e6b5bab70304da  data/outputs/site_results.csv`.
- **Notes:** Line count (14) matches the claim in `BASELINE_VERIFICATION.md:36`. No file listed here exists in the current tree — expected, since `data/outputs/` is gitignored per `migration-from-v2.md:42`. These hashes can only be re-checked by re-running the V1 code from the archive branch. Not currently enforced by any CI gate.

### docs/operations/legacy-baseline/v2_output_hashes.txt
- **Role:** Frozen SHA-256 manifest of the 71 output files produced by the reproduced V2 legacy run.
- **Kind:** generated (same provenance as v1_output_hashes.txt)
- **Reads:** n/a
- **Written by / read by:** Referenced by `BASELINE_VERIFICATION.md:36`. Not enforced by any repo gate.
- **Key contents:** 71 lines. Three groups: (a) `data/outputs/deliverable_package_v2/…` — inputs/, manifests/, package_manifest.json, README.md, 11 reports/, 12 tables/ (lines 1-28); (b) `data/outputs/tableau/…` — **15 tableau_*.csv exports** (lines 30-44), matching the "15/15 exports" claim; (c) `data/outputs/v2_*.{md,csv,json}` — 27 top-level V2 outputs (lines 45-71).
  Notable internal consistency: several hashes appear twice because the deliverable package copies the top-level file, e.g. `b596e8436e4dde7b91ea95fd30ebe739d30bcd1a2eb69f7c74d67d5f74a04402` is both `deliverable_package_v2/reports/v2_action_matrix.md` (line 6) and `v2_action_matrix.md` (line 45); likewise `4a370756862cea…` (lines 14 & 63), `a677940cef3f…` (lines 26 & 66), `7417df8d181d…` (lines 17 & 48), `5b0ea53aa444…` (8 & 49), `064b6fdc5afe…` (18 & 50), `d39d0620ba5a…` (19 & 52), `9367de63363c…` (9 & 53), `a1ab922d8a79…` (10 & 54), `5477630a50cc…` (20 & 55), `72b438bbc84c…` (21 & 56), `78fec52e2094…` (11 & 57), `aadf69e9f5b6…` (22 & 58), `6c5f28797db4…` (12 & 59), `9ba694ecf38f…` (23 & 60), `d3bcf95c0c16…` (24 & 61), `808cb7b9b187…` (13 & 62), `2753b3f5da07…` (15 & 65), `b2d3260b5efc…` (16 & 67), `c53f5e1fce04…` (27 & 69), `a66cbe115c94…` (28 & 70), `3d8b395b125f…` (3 & 71).
  Deliberate non-duplicates: `data/outputs/README.md` (line 29, `8c9c3aaf…`) differs from `deliverable_package_v2/README.md` (line 5, `a48ce036…`); `v2_baseline_comparison.md` (line 47, `b2ca7524…`) differs from the packaged copy (line 7, `1bc564d0…`).
- **Notes:** Line count (71) matches `BASELINE_VERIFICATION.md:36`. ✓ The "**35** package files" claim in BASELINE_VERIFICATION line 25 refers to the deliverable package's own file count; the hash file lists 28 `deliverable_package_v2/*` entries (only CSV/JSON/MD were hashed — PNG/other files in the package were not), so the two counts are not expected to match and this is **not** a contradiction. Same caveat as v1: not enforced by any gate.

### docs/operations/open-human-actions.md
- **Role:** The definitive list of the ten things software cannot close — each with a ready-to-use package, the gap IDs it closes, and the acceptance evidence required.
- **Kind:** authored (governance register)
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:31`. Row 9 is the entry point for the website-patch-package; row 7 for MATLAB; row 8 for Tableau.
- **Key contents (21 lines).** Header (lines 3-4): "**Every action has a complete, ready-to-use package; none has been executed — no email was sent, no meeting held, no data received.**" Table `| # | Action | Who | Package | Closes | Acceptance evidence |`:
  1. Client Meeting #2 follow-up to **[client contact]**; 30-min call or structured email **before July 21** → `docs/human-actions/client_meeting_2/` → closes **A1–A4, G5**.
  2. 60–90-min team alternatives session; adopt/amend provisional MCDA; **adopt year convention**, standards pair, peer question; assign Paula's role → `docs/human-actions/team_alternatives_session/` → closes **A5–A8, B7, F2** → evidence: signed decision record + adopted matrix + **dissent log**.
  3. Fellowship clarification email to **DiscoverE** (CM2 classification; scheduled-CM2 acceptability; **exact years vs intervals**; one-vs-two ULSE standards) → `docs/human-actions/fellowship_confirmation/` → closes interpretation risk on **A1/B3/C2**.
  4. Utility + facility data requests for **FFX002 / FFX004 / PWC006** → `docs/human-actions/utility_facility_data/` → closes **D1** and every electrical field; "upgrades `capacity_basis`" → evidence: responses logged + **model re-run with verified capacity**.
  5. Fire Marshal/AHJ conversations in both jurisdictions → `docs/human-actions/ahj_fire_marshal/` → closes **C7** validation.
  6. Rehearse twice to **≤13 minutes** → `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md` → closes **H2**.
  7. Run MATLAB batch + tests on licensed **R2025b** → `matlab/RUN_ON_LICENSED_MATLAB.md` → evidence: results.csv + green `runtests` + golden file created.
  8. Build + verify the Tableau workbook from the patch recipe (**optional**; static dashboard already satisfies the presentation) → `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md` → closes **PY-15 twbx portion**.
  9. **Apply the website/assistant patch and deploy per runbook** → `docs/operations/website-patch-package/` → closes **PY-16 deployment portion** → evidence: **live acceptance checklist passed; rollback snapshot stored**.
  10. Field public-engagement instruments (Phase 3) → `docs/human-actions/public_engagement/` → closes **G3** fielding; equity evidence for **PY-20**.
  **Standing integrity rule (lines 19-21):** "closing any row requires the real event and its documentation. Retroactive relabeling (e.g., calling the first [client contact] interview 'CM2') violates the project's evidence discipline and the fellowship's intent."
- **Notes:** All ten package paths exist. Row 2's "adopt year convention" is the human decision that the 2026/2036/2046/2056 convention is still *pending* — worth remembering when Phase 4/9 describe the horizons as settled. Row 1's "before July 21" deadline is **past** relative to today (2026-07-27), so row 1 is now overdue-or-stale as written. **Row 9 is the Phase-8 hook: the website patch is formally recorded as NOT applied.**

### docs/operations/reproduction-guide.md
- **Role:** The verified command-by-command reproduction path for the whole repository. **This is the script the Phase-10 clean-clone test follows.**
- **Kind:** authored
- **Reads:** n/a (it *prescribes* reads)
- **Written by / read by:** Linked from `docs/README.md:7`. It is the human-readable mirror of `Makefile` + `scripts/verify.sh`.
- **EVERY COMMAND IT TELLS A READER TO RUN (in order, all from the repository root unless noted):**
  | § | Command | Stated expectation |
  |---|---|---|
  | 0 | `make setup` | creates `./venv`, installs the package editable with pinned `[test]` extras |
  | 1 | `make test` | **80 tests pass; coverage gate ≥ 80%** |
  | 2 | `make run-legacy` | writes `data/outputs/legacy_check/`; **FFX002 58.8; 25 starter / 48 pathway ports**; reproduces V2 bit-for-bit |
  | 3 | `make run-v3` | writes `data/outputs/v3_run/` (scores, scenarios, economics, emissions, contract tables, matlab_scenarios.csv) |
  | 3 | `make validate` | validates the tracked canonical contract at `data/contract/v1`; **contract valid, 120 scenario rows** |
  | 4 | `make dashboard` | `= make run-v3 + build_static_dashboard.py` |
  | 4 | `venv/bin/python scripts/build_static_dashboard.py` | **9 visuals + STATIC_DASHBOARD.pdf + footer QA** into `dashboard/static/` |
  | 4 | `venv/bin/python scripts/build_excel_workbook.py --source "/path/to/Electric Data.xlsx"` | requires the team's original workbook; original **not tracked**; only `excel/Electric_Data_Milestone_2_Updated.xlsx` is |
  | 4 | (manual) `make run-v3`, then copy `data/outputs/v3_run/matlab_scenarios.csv` → `matlab/data/canonical/matlab_scenarios.csv`, then `make validate` | refreshes the MATLAB canonical input |
  | 5 | `./scripts/verify.sh` | every repository gate; exits nonzero on any failure; prints **`ALL REPOSITORY VERIFICATION GATES PASSED`** |
  | 6 | `cd matlab` | — |
  | 6 | `matlab -batch "addpath('src'); run_all_scenarios"` | **requires licensed R2025b — never executed in the authoring environment** |
  | 6 | `matlab -batch "addpath('src'); results = runtests('tests'); assertSuccess(results)"` | same |
- **Other key contents:** Environment claim (lines 5-8): "verified on macOS (Apple Silicon) with **Python 3.14** on **2026-07-19**. Python 3.11+ is supported. … **No internet access is required for any step** — GIS boundaries are cached in `data/cache/`."
  §5 gate list (lines 65-69): "tests + coverage floor, legacy baseline reproduction (25/48), contract rules/schema/hash chain, cross-model reconciliation with the MATLAB canonical CSV, workflow-docs consistency, dashboard footer QA, secret scan, **local-path scan**, file-size limit, and Markdown link check. **CI runs the same gates** ([.github/workflows/tests.yml])."
  §6 links `matlab/RUN_ON_LICENSED_MATLAB.md` and `matlab/EXECUTION_STATUS.md` "for what has and has not been executed (**nothing has — no license was available**)".
  **Expected results summary table** (lines 88-93): `make test` → 80 tests, coverage ≥80%; `make run-legacy` → starter_total 25, pathway_total 48; `make validate` → contract v1.0.0 passes all rules, JSON Schema, and the manifest hash chain; `./scripts/verify.sh` → `ALL REPOSITORY VERIFICATION GATES PASSED`.
  **Determinism notes** (lines 96-102): `SIM_RANDOM_SEED = 20260719` in `src/fcf_m2/config.py`; contract `run_id` / `generated_at` are timestamps and table hashes in `contract_manifest.json` **change per run by design** — "the RT-10 hash chain exists to prevent quoting a stale contract against fresh tables"; "Every step is fully offline; there is no first-run download."
- **Notes / verification:**
  - **`make setup` uses `python3 -m venv venv && venv/bin/pip install -e ".[test]" -c requirements-lock.txt`** — confirmed in `Makefile`. All 7 make targets named by the guide exist.
  - **80 tests: consistent.** `tests/` has 78 `def test_*` functions; `tests/test_scoring_and_queueing.py:32` carries `@pytest.mark.parametrize("vals", [[0,1,2],[10,20,30],[0.1,0.5,0.9]])` (3 cases), giving 78 − 1 + 3 = **80** collected. ✓
  - **120 scenario rows: confirmed.** `data/contract/v1/scenario_table.csv` has 121 lines = header + **120** rows (12 sites × 10 horizon/case combinations). ✓
  - **9 visuals: confirmed.** `dashboard/static/` contains exactly 9 `*.png` plus `STATIC_DASHBOARD.pdf` and `footer_log.json`. ✓
  - **`SIM_RANDOM_SEED = 20260719`: confirmed** at `src/fcf_m2/config.py:86`. ✓
  - **`--source` flag: confirmed** — `scripts/build_excel_workbook.py:20` `_ap.add_argument("--source", required=True, …)`. ✓
  - **Python version inconsistency (low):** the guide says verified on **Python 3.14**; `BASELINE_VERIFICATION.md:3` says the legacy runs used **Python 3.14.6**; but `.github/workflows/tests.yml` pins **`python-version: "3.12"`**. Not contradictory (3.11+ is claimed supported) but Phase 10 should pick one for the clean-clone test.
  - **⚠ `./scripts/verify.sh` will NOT print `ALL REPOSITORY VERIFICATION GATES PASSED` at HEAD.** The gate *"hygiene: no local absolute paths in code/config"* runs `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'`, and tracked `dashboard/static/footer_log.json` contains nine `/Users/andyyaro/Documents/...` strings. I reproduced the exact grep: it returns 9 matches, so the gate inverts to FAIL. See Finding F-02.
  - **⚠ "CI runs the same gates" is false.** `.github/workflows/tests.yml` runs only 6 of verify.sh's 10 gates: test suite + coverage, legacy baseline, contract validation, cross-model reconciliation, internal Markdown links, secret scan. It **omits** the workflow-docs consistency gate, the dashboard footer-QA gate, the local-absolute-path gate, and the 25 MB file-size gate. See Finding F-03. (Also: `tests.yml` triggers on push only for branches `[main, milestone2-v3-professional-release]` — **not** `v4-platform`, so nothing in this lane is being CI-checked on the current working branch.)

### docs/operations/website-patch-package/README.md
- **Role:** Index and governance contract for the offline website/AI-assistant update package.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Linked from `docs/README.md:35` and `open-human-actions.md` row 9.
- **Key contents (38 lines).** Opening declaration (lines 3-8): "**Nothing in this package has been deployed. No AWS resource, DNS entry, or live page was touched in this run.** The website (**`futurecityfellowship.andyyaro.com`**: landing, dashboard, results, methodology, and authenticated AI Assistant pages on **S3/CloudFront + Cognito + API Gateway/Lambda/DynamoDB**) is maintained outside the repository, so this package provides **precise patch content and a file-by-file implementation guide** (per Task 10's source-absent path) rather than modified source files."
  Contents table maps all 10 package files to purposes (see Part 2).
  **Governance rules embedded (PY-16), 7 numbered items:** (1) assistant remains **explanation-only**; formal public comments go through accountable municipal channels; (2) no unnecessary personal data; no PII to read any page; (3) privacy notice + authority disclaimers site-wide; (4) **every results figure carries the source vintage (contract v1.0.0, generated 2026-07-19; eGRID2023 Rev 2 SRVC factor)**; (5) no secrets/credentials/internal infrastructure identifiers in this package or in assistant-readable content; (6) **Cognito authentication boundary preserved — nothing here makes the assistant public**; (7) accessibility: alt text on all new figures, heading hierarchy, contrast ≥ **WCAG AA**.
- **Notes:** The contents table lists `content/privacy_notice.md` as mirroring `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md` (that file's directory exists; I did not diff the two — Phase 8 should). No secrets, no bucket names, no distribution IDs, no account IDs appear — rule 5 is honoured. The domain `futurecityfellowship.andyyaro.com` is the only infrastructure identifier and is public DNS, not a secret.

### docs/operations/website-patch-package/DEPLOYMENT_RUNBOOK.md
- **Role:** Exact deploy / verify / rollback procedure for the site maintainer.
- **Kind:** authored (runbook)
- **Reads:** n/a
- **Written by / read by:** Referenced by `README.md` of the package and by `PATCH_GUIDE.md:2` ("deploy per DEPLOYMENT_RUNBOOK.md").
- **Key contents (24 lines):** Title carries the status: "**(maintainer-executed; NOT run in this implementation)**".
  **Preconditions:** AWS CLI configured with the maintainer's credentials (**"never stored in this repo"**); S3 origin bucket name + CloudFront distribution ID **"kept outside this package by design — see PY-18/PY-16 no-secrets rule"**.
  **Deploy (5 steps):**
  1. Stage the patched bundle locally; run the acceptance checklist in PATCH_GUIDE.md.
  2. `aws s3 sync s3://<bucket> ./site_backup_$(date +%Y%m%d)/`
  3. `aws s3 sync ./site_patched/ s3://<bucket> --delete --dryrun` → review → re-run without `--dryrun`.
  4. `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`
  5. Verify live: privacy page loads; results numbers spot-checked against contract; assistant still behind Cognito; no mixed-content warnings.
  **Rollback (3 steps):** `aws s3 sync ./site_backup_<date>/ s3://<bucket> --delete`; re-invalidate CloudFront; record the rollback and reason in the decision log.
  **Assistant config rollback:** export the prior system prompt/config before editing; restoring is a single config write + cache flush.
- **Notes:** No AWS account ID, bucket name, distribution ID, or credential appears — clean. Phase 8 will need to supply `<bucket>` and `<ID>` from AWS discovery. Deploy step 5's "results numbers spot-checked against contract" is exactly the check that would have caught Finding F-01.

### docs/operations/website-patch-package/PATCH_GUIDE.md
- **Role:** The file-by-file / page-by-page instruction set the site maintainer executes. **The single most load-bearing file in this lane for Phase 8.**
- **Kind:** authored (patch specification)
- **Reads:** the eight `content/*` files, plus `dashboard/static/` and `data/contract/v1/scenario_table.csv` as authorities.
- **Written by / read by:** Entry point from `open-human-actions.md` row 9 and the package README.
- **Key contents:** 9 numbered patches + a 6-item acceptance checklist. Fully enumerated in **Part 2** below.
- **Notes:** Prerequisite line (line 3): maintainer needs "access to the deployed site bundle (S3 origin) and the assistant's prompt/config store". Standing rule (lines 4-5): "Apply in order; deploy per DEPLOYMENT_RUNBOOK.md. **Do not remove any existing limitation text — only extend or supersede as directed.**"

### docs/operations/website-patch-package/content/authority_disclaimer.md
- **Role:** The no-engineering-authority block to be rendered under the hero on every page footer and in the assistant.
- **Kind:** authored (patch content — verbatim text)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §1 (landing page, under hero).
- **Key contents:** 6 lines, a single blockquote. Full text in Part 2, Patch 1.
- **Notes:** No numbers, no dates, no horizons. Safe to apply unchanged.

### docs/operations/website-patch-package/content/methodology_update.md
- **Role:** The V3 methodology section to append to `methodology.html`.
- **Kind:** authored (patch content)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §4.
- **Key contents:** 24 lines. Describes two permanent modes and the seven V3 extensions; states demand is `demand_model_status = synthetic_uncalibrated`; lists growth multipliers. Full text in Part 2, Patch 4.
- **Notes:** **All numbers verified against the repo.** `legacy_v2` figures (12 sites; FFX002 58.8; 25 starter / 48 pathway; 38 REVIEW + 12 INFO; 0 High-confidence) match `BASELINE_VERIFICATION.md` exactly. Growth multipliers (2036 1.9×/2.6×; 2046 3.0×/4.5×; 2056 4.0×/6.0×) match `src/fcf_m2/config.py:42-50` exactly. `demand_model_status = synthetic_uncalibrated` matches `src/fcf_m2/config.py:64 DEMAND_MODEL_STATUS = "synthetic_uncalibrated"`. The "10/20/30-year horizons — 2036/2046/2056 from a 2026 baseline" phrasing is the **correct** bridge form.

### docs/operations/website-patch-package/content/results_2036_2046_2056.md
- **Role:** The three-horizon results content to insert as the lead section of `results.html`. Claims to be contract-derived.
- **Kind:** authored (patch content) — **but it asserts data-contract provenance it does not fully have**
- **Reads:** claims all values come from canonical contract v1.0.0 (generated 2026-07-19) · **Consumed by:** PATCH_GUIDE §3.
- **Key contents:** 30 lines: Aspect-1 ports table, Aspect-2 lifecycle cost table, environmental outcome paragraph. Full text and per-number verification in Part 2, Patch 3.
- **Notes:** **⚠ The Aspect-1 ports table does not match `data/contract/v1/scenario_table.csv` (Finding F-01), and it contradicts the file's own closing sentence.** Every other number in the file traces correctly. Details in Part 2 and Part 4.

### docs/operations/website-patch-package/content/standards_summary.md
- **Role:** Public-facing standards summary for a new `standards.html`.
- **Kind:** authored (patch content)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §6.
- **Key contents:** 24 lines. Full text in Part 2, Patch 6.
- **Notes:** Faithful compression of `FINAL_STANDARDS_APPLICATION_MATRIX.md` + `PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md`. Editions match the matrix (UL 2594 3rd ed. 2022; UL 3600 2023; 2020 NEC via 2021 USBC eff. 2024-01-18). Keeps the "not ULSE standards" flag on OCPP/ISO 15118 and the conditional status of UL 2202 / UL 9540. Carries the required "fellowship design concept — not an official UL/ULSE proposal" label. Says "rule at NPRM stage as of **July 2026**" — consistent with IM-02's 2026-07-19 verification.

### docs/operations/website-patch-package/content/limitations_update.md
- **Role:** The replacement limitations block wherever `MODEL_LIMITATIONS` content is surfaced.
- **Kind:** authored (patch content)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §7.
- **Key contents:** 15 lines, 8 numbered limitations. Full text in Part 2, Patch 7.
- **Notes:** Item 5 carries the **eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh** factor — correct current value. Item 1's "0 of 12 sites have High data confidence" is confirmed by the contract (all 120 rows have `data_confidence = Low`). Item 2's `capacity_basis = placeholder` is confirmed (all 120 rows `capacity_basis = placeholder`). Item 7 "no resilience claim is made — the plan includes no battery storage" matches `FINAL_STANDARDS_APPLICATION_MATRIX.md:149`. Item 8 is the honest MATLAB caveat.

### docs/operations/website-patch-package/content/privacy_notice.md
- **Role:** New `privacy.html` page; VCDPA-aware.
- **Kind:** authored (patch content)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §5.
- **Key contents:** 15 lines, 5 bullets. Full text in Part 2, Patch 5.
- **Notes:** Names **Cognito** as the assistant's gate and the **Virginia Consumer Data Protection Act (VCDPA)** posture (data minimization, purpose limitation, time-limited retention of technical logs). "We do not sell or share any visitor data. No advertising or cross-site tracking is used." Package README says this mirrors `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md` — not diffed.

### docs/operations/website-patch-package/content/assistant_boundaries.md
- **Role:** Assistant scope/limitation text for above the chat window, **and** the "Answer rules" that must be appended to the assistant's system prompt/config.
- **Kind:** authored (patch content + prompt-config source)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §8 (page + config).
- **Key contents:** 20 lines. "It will not (and must not)" — 4 prohibitions; "Answer rules" — 4 numbered rules. Full text in Part 2, Patch 8.
- **Notes:** Rule 3 requires quoting **canonical contract values (v1.0.0, generated 2026-07-19)** with assumption labels (uncalibrated demand, screening-class costs, placeholder capacity, eGRID2023r2 emissions factor). This is the governance hook that makes Finding F-01 consequential: an assistant told to quote contract values while the results page shows non-contract ports numbers will contradict itself.

### docs/operations/website-patch-package/content/source_vintage_footer.html
- **Role:** The site-wide footer HTML snippet carrying contract version, generation date, input date, and eGRID vintage.
- **Kind:** authored (patch content — the only HTML file in the package)
- **Reads:** n/a · **Consumed by:** PATCH_GUIDE §1 ("Add footer include"). Acceptance checklist requires it "on every page".
- **Key contents:** 5 lines. `<footer class="fcf-vintage" style="font-size:0.75rem;color:#4b4b4b;border-top:1px solid #d8cdb6;padding:0.5rem 1rem;">` containing: `Data: canonical contract v1.0.0 (generated 2026-07-19) · site inputs 2026-06-24 · emissions factor EPA eGRID2023 Rev 2, SRVC, 596.3 lb CO2e/MWh (accessed 2026-07-19; refreshed annually) · Planning-support prototype — nothing on this site is an approval or an official forecast.`
- **Notes:** All four vintage facts verified: contract_version `1.0.0` and `generated_utc 2026-07-19T05:23:22.507266+00:00` in `data/contract/v1/contract_manifest.json`; `site inputs 2026-06-24` matches `dashboard/static/footer_log.json` `"source_date": "inputs 2026-06-24; eGRID2023r2; verified 2026-07-19"`; 596.3 matches the manifest `grid_factor`. Uses inline styles only — no external CSS dependency, safe to paste. Colors `#4b4b4b` on white and `#d8cdb6` border; the text color meets WCAG AA on white (rule 7 of the package governance).

---

## PART 2 — DEDICATED PATCH REGISTER (for Phase 0.5 and Phase 8)

Source of truth: `docs/operations/website-patch-package/PATCH_GUIDE.md` (61 lines) + the 8 `content/` files.
**Standing rule (PATCH_GUIDE lines 4-5):** "Apply in order; deploy per DEPLOYMENT_RUNBOOK.md. Do not remove any existing limitation text — only extend or supersede as directed."
**Target site:** `futurecityfellowship.andyyaro.com` — S3/CloudFront + Cognito + API Gateway/Lambda/DynamoDB, maintained outside this repo.
**Declared status: NOTHING DEPLOYED** (package README lines 3-4; DEPLOYMENT_RUNBOOK title; open-human-actions row 9 open).

### Patch 1 — Landing page `index.html`
Three sub-changes (PATCH_GUIDE lines 7-13):

**1a. ADD** the authority-disclaimer block, rendered, **directly under the hero section**.
New text (verbatim, `content/authority_disclaimer.md`, entire file):
> **What this site is — and is not.** This website presents a Future City Fellowship
> planning-support prototype. It is **not** engineering advice, a permit or code-compliance
> determination, a utility capacity confirmation, an official forecast, or a procurement or
> construction authorization. Every siting decision remains subject to electrical, ADA,
> fire/AHJ, stormwater, and permitting review by the responsible authorities. No site shown
> here is approved.

**1b. REPLACE** — the only explicit old-text→new-text substitution in the whole package:
- **OLD:** any `"2035/2050"` wording
- **NEW:** `"10/20/30-year horizons (2036 / 2046 / 2056 from a 2026 baseline)"`

**1c. ADD** footer include `content/source_vintage_footer.html`.
New text (verbatim, entire file):
```html
<footer class="fcf-vintage" style="font-size:0.75rem;color:#4b4b4b;border-top:1px solid #d8cdb6;padding:0.5rem 1rem;">
  Data: canonical contract v1.0.0 (generated 2026-07-19) · site inputs 2026-06-24 ·
  emissions factor EPA eGRID2023 Rev 2, SRVC, 596.3 lb CO2e/MWh (accessed 2026-07-19; refreshed annually) ·
  Planning-support prototype — nothing on this site is an approval or an official forecast.
</footer>
```
**Numbers this patch changes/introduces:** 2035→2036, 2050→2046+2056, baseline 2026; contract v1.0.0; 2026-07-19; 2026-06-24; **596.3 lb CO2e/MWh**.
**Phase-8 detection test:** does `index.html` contain the string `596.3`, `2036`, or `No site shown here is approved`?

### Patch 2 — Dashboard page `dashboard.html`
(PATCH_GUIDE lines 14-19) Three sub-changes:
**2a. REPLACE** embedded charts with **the 9 static assets from `dashboard/static/`** (repository-relative; already footer-labeled; **keep filenames**).
The 9 filenames (verified present): `01_readiness_ranking.png`, `02_starter_vs_pathway.png`, `03_ports_three_horizons.png`, `04_lifecycle_cost.png`, `05_net_co2e.png`, `06_avoided_evse.png`, `07_peak_wait.png`, `08_limitations.png`, `09_site_map_offline.png`.
**2b. ADD** caption under any capacity-related visual, verbatim new text: `"Electrical capacity is a planning placeholder at all 12 sites pending utility/facility confirmation."`
**2c. ADD** alt text per image — "describe the chart takeaway, not the chart type".
**Numbers this patch changes:** 12 sites; whatever numbers the 9 PNGs carry.
**Phase-8 detection test:** are any of the 9 exact filenames served by the site? Does the page contain the caption string?

### Patch 3 — Results page `results.html`
(PATCH_GUIDE lines 20-25) Three sub-changes:
**3a. INSERT** `content/results_2036_2046_2056.md` (rendered) **as the lead section**.
**3b. RULE:** "Every number on this page must trace to `data/contract/v1/scenario_table.csv`; **remove any figure that does not**."
**3c. KEEP** the `"0 of 12 sites High confidence"` line prominent.

**New text inserted (verbatim, `content/results_2036_2046_2056.md`, entire file):**

Heading: `## Results at 10 / 20 / 30 years (2036 · 2046 · 2056)`
Lead: "All values from canonical contract v1.0.0 (generated 2026-07-19); screening estimates with labeled assumptions — not forecasts, budgets, or approvals."

`### Aspect 1 — ports and service capacity (base → high adoption paths)`
| Horizon | Active ports (base) | Active ports (high) | Pathway ceiling |
|---|---|---|---|
| 2026 (baseline) | 25 | 25 | 48 |
| 2036 | **44** | **47** | 48 |
| 2046 | **47** | 48 | 48 |
| 2056 | **47** | 48 | 48 |

Then: "Activation is trigger-gated: ports energize only when observed utilization, wait, and reliability evidence (with an equity override) clears a proposed policy that itself requires human approval."

`### Aspect 2 — lifecycle cost (portfolio NPV, screening, base escalation)`
| Horizon | Staged plan | Broad buildout now | Staged avoids |
|---|---|---|---|
| 2036 | $1.56M | $1.87M | **$0.31M** |
| 2046 | $2.29M | $2.64M | **$0.34M** |
| 2056 | $3.01M | $3.41M | **$0.39M** |

`### Environmental outcome (attached to Aspect 2)`
"Net avoided CO2e grows from **≈43 t/yr** (2026 baseline) to **≈173 t/yr** (2056 base path; **≈260 t/yr** high path), computed with the EPA eGRID2023 Rev 2 SRVC factor (**596.3 lb CO2e/MWh**, refreshed annually) and labeled displacement assumptions. The staged plan also avoids energizing **13–23 pathway ports** that current demand does not justify — the resource-management lesson of the county's own decommissioning experience."

**Per-number trace against `data/contract/v1/scenario_table.csv` (I aggregated all 120 rows by horizon × scenario_name):**

| Doc claim | Contract actual | Verdict |
|---|---|---|
| 2026 ports 25 / 25, pathway 48 | 25, pathway 48 | ✅ |
| **2036 base ports 44** | **35** | ❌ **WRONG** |
| **2036 high ports 47** | **44** | ❌ **WRONG** |
| **2046 base ports 47** | **44** | ❌ **WRONG** |
| 2046 high ports 48 | 48 | ✅ |
| **2056 base ports 47** | **44** | ❌ **WRONG** |
| 2056 high ports 48 | 48 | ✅ |
| Pathway ceiling 48 at every horizon | 48 at every horizon | ✅ |
| Staged NPV 2036 $1.56M / 2046 $2.29M / 2056 $3.01M | 1.560M / 2.294M / 3.014M | ✅ |
| Broad buildout 2036 $1.87M / 2046 $2.64M / 2056 $3.41M | staged+avoided = 1.872M / 2.635M / 3.407M | ✅ |
| Staged avoids $0.31M / $0.34M / $0.39M | 0.312M / 0.341M / 0.393M | ✅ |
| ≈43 t/yr at 2026 | 43.4 t | ✅ |
| ≈173 t/yr 2056 base | 173.4 t | ✅ |
| ≈260 t/yr 2056 high | 260.2 t | ✅ |
| 596.3 lb CO2e/MWh | manifest `grid_factor.value_lb_per_mwh = 596.3` | ✅ |
| "avoids energizing 13–23 pathway ports" | `tbl_avoided_evse.csv`: 2026 baseline **23**, 2036 base **13**, 2046 base **4**, 2056 base **4** | ⚠ true only for 2026/2036; overstates 2046/2056 |

**Numbers this patch changes:** the six ports values above, six cost values, three avoided-cost values, three CO2e values, the grid factor, and the 13–23 avoided-port range.
**Phase-8 detection test:** does `results.html` contain `$1.56M`, `$0.31M`, `≈173`, `596.3`, or the phrase "Activation is trigger-gated"?

### Patch 4 — Methodology page `methodology.html`
(PATCH_GUIDE lines 26-29)
**APPEND** `content/methodology_update.md` as a new section headed **"V3 (July 2026)"**; **KEEP** the existing V2 section, relabeled **"V2 (accepted baseline)"**.
**New text (verbatim, entire file):** heading `## V3 methodology (July 2026 update)`, then "The model now runs in two permanent modes:"
- **`legacy_v2` (accepted baseline):** "the reviewed V2 workflow, reproduced bit-for-bit (**12 sites; FFX002 top at 58.8; 25 starter / 48 pathway ports; 38 REVIEW + 12 INFO data findings; 0 High-confidence sites**)."
- **`milestone2_v3`:** seven numbered extensions — (1) **canonical 10/20/30-year horizons — 2036/2046/2056 from a 2026 baseline**; (2) cohort-independent fixed-anchor scoring (versioned anchor set, migration report published); (3) typed field-level data confidence — "wording changes can no longer move confidence scores"; (4) peak-window and discrete-event wait modeling with **P10/P50/P90** bands; (5) lifecycle-cost layer (net present cost, staged vs broad vs defer); (6) net-CO2e layer with sourced grid factor; (7) "one canonical cross-model data contract consumed by every downstream artifact (Excel, MATLAB, Tableau, this site)."
Then: "**Demand remains synthetic and uncalibrated** (`demand_model_status = synthetic_uncalibrated`). The V3 code includes an observed-data import format and a calibration routine that refuses to label itself calibrated without sufficient data and acceptable holdout error; it will be exercised when pilot monitoring data exist."
Then: "Growth multipliers (**2036: 1.9×/2.6×; 2046: 3.0×/4.5×; 2056: 4.0×/6.0×** with pathway saturation) are **provisional planning conventions pending calibration**, adopted for horizon consistency across all artifacts."
**Numbers this patch changes:** 12; 58.8; 25/48; 38+12; 0; 2036/2046/2056; 1.9/2.6/3.0/4.5/4.0/6.0. **All verified correct** against `BASELINE_VERIFICATION.md` and `src/fcf_m2/config.py:42-50`.
**Phase-8 detection test:** does `methodology.html` contain `synthetic_uncalibrated`, `1.9×`, `P10/P50/P90`, or the heading `V3 (July 2026)`?

### Patch 5 — New privacy page `privacy.html`
(PATCH_GUIDE lines 30-32)
**CREATE** from `content/privacy_notice.md`; **LINK from every page footer**.
**New text (verbatim, entire file):** heading `# Privacy Notice (July 2026)`, then 5 bullets:
1. "**Reading this site requires no personal information.** We do not require registration, and we collect no personal data beyond standard, short-lived technical logs."
2. "**The AI Assistant is restricted to approved, authenticated users** (Cognito). It is an *explanation tool* for the project's methods and documents. Assistant conversations may be logged for quality and security; they are not used for any other purpose and are not shared."
3. "**Formal public comments do not belong here.** To make your voice count in an official process, use the accountable municipal channels listed on our engagement page; we will never treat website or assistant activity as formal public input."
4. "**Virginia Consumer Data Protection Act (VCDPA) posture:** we practice data minimization, purpose limitation, and time-limited retention of technical logs. Questions or requests: use the contact route on the engagement page."
5. "We do not sell or share any visitor data. No advertising or cross-site tracking is used."
**Numbers this patch changes:** none.
**Phase-8 detection test:** does `/privacy.html` (or equivalent) exist and return 200? Does it contain `VCDPA`?

### Patch 6 — New standards page/section `standards.html`
(PATCH_GUIDE lines 33-36)
**CREATE** from `content/standards_summary.md`. **Hard requirement:** "the proposed-standard section must keep the **'fellowship design concept — not an official UL/ULSE proposal'** label **verbatim**."
**New text (verbatim, entire file):** heading `## Standards that govern our design intent`, then:
- **Highlighted ULSE standards:** **UL 2594** (EVSE, 3rd ed. 2022) — "safety standard for the exact equipment class proposed (AC Level 2). Procurement will require UL 2594-listed equipment; commissioning verifies listings and personnel protection." **UL 3600** (Measuring and Reporting Circular Economy Aspects, 2023) — "sustainability standard anchoring vendor circularity disclosure, annual circularity reporting, and end-of-life/take-back planning."
- **Essential supporting requirements:** UL 2231-1/-2 personnel protection; **NEC Article 625 as adopted in Virginia (2020 NEC via the 2021 USBC, effective 2024-01-18)**; Virginia USBC/SFPC; US Access Board EVSE accessibility guidance (**rule at NPRM stage as of July 2026**; VA USBC ADA provisions govern today); **OCPP and ISO 15118 as supporting interoperability protocols (not ULSE standards)**. "UL 2202 (DC charging) and UL 9540/9540A + NFPA 855 (storage) apply **only if** DC fast charging or battery storage enter scope — neither is in the current plan."
- **Proposed standard (fellowship design concept — not an official UL/ULSE proposal):** *Municipal EV Charging Site Readiness and Emergency Access Standard* — "a site-level readiness framework with test modules for emergency access/disconnect, expandability documentation, accessibility cross-references, monitoring/triggers, managed-charging fail-safe, commissioning evidence, and end-of-life. Unsourced parameters are marked TBV for ULSE/AHJ/manufacturer validation."
**Numbers/versions this patch changes:** UL 2594 3rd ed. 2022; UL 3600 2023; 2020 NEC; 2021 USBC eff. 2024-01-18; NPRM July 2026.
**Phase-8 detection test:** does the site contain the string `not an official UL/ULSE proposal` or `UL 3600`?

### Patch 7 — Limitations (wherever `MODEL_LIMITATIONS` content is surfaced)
(PATCH_GUIDE lines 37-39)
**REPLACE** the existing limitations content with `content/limitations_update.md`.
**New text (verbatim, entire file):** heading `## Limitations (July 2026 — read before using any number)`, then 8 numbered items:
1. "**0 of 12 sites have High data confidence.** Every electrical field (service rating, spare capacity, disconnect visibility) is unconfirmed at all 12 sites."
2. "**Capacity is a placeholder** everywhere (`capacity_basis = placeholder`) until utility/facility data arrive; no feasibility claim is permitted on placeholder capacity."
3. "**Demand is synthetic and uncalibrated**; growth multipliers are provisional conventions."
4. "**Costs are screening-class benchmarks** — not budgets, quotes, or engineering estimates."
5. "**Emissions use labeled benchmark assumptions** and the eGRID2023 Rev 2 SRVC factor (**596.3 lb CO2e/MWh**); the factor changes annually and results must be recomputed."
6. "**No approvals exist**: no client endorsement, AHJ acceptance, utility confirmation, or funding award is implied anywhere on this site."
7. "**No resilience claim is made** — the plan includes no battery storage."
8. "**MATLAB/Simulink results shown are illustrative** under placeholder capacity; no new simulation execution is claimed beyond what was actually run."
**Numbers this patch changes:** 0 of 12; 12 sites; **596.3 lb CO2e/MWh**.
**Note:** this is the only patch that *replaces* rather than adds — but PATCH_GUIDE line 4 forbids removing limitation text, so the replacement must be a superset. Items 1-8 do appear to supersede rather than shrink.
**Phase-8 detection test:** does the site contain `capacity_basis = placeholder`, `596.3`, or `0 of 12 sites`?

### Patch 8 — AI Assistant page + config
(PATCH_GUIDE lines 40-49) Three sub-changes:
**8a. PAGE:** insert `content/assistant_boundaries.md` **above the chat window**; add the privacy link; **keep the Cognito gate unchanged**.
**8b. CONFIG:** append the boundary rules from `content/assistant_boundaries.md` §"Answer rules" to the assistant system prompt/config (explanation-only; no approval, engineering, permitting, or budget advice; cite doc + vintage; direct formal comments to municipal channels).
**8c. CORPUS:** update the assistant's document corpus to include **the V3 README, contract README, and limitations update**; **EXCLUDE any internal working files, credentials, or infrastructure notes.**
**New text (verbatim, `content/assistant_boundaries.md`, entire file):**
Heading `# About this Assistant`. Lead: "The assistant explains this project's methodology, data, results, and limitations. It is **explanation-only**."
`## It will not (and must not)` — 4 bullets:
- "approve, endorse, or recommend construction, procurement, or permits;"
- "state that any site is electrically adequate (capacity is a planning placeholder at all 12 sites pending utility/facility confirmation);"
- "provide engineering, legal, or code-compliance determinations;"
- "collect personal information or accept formal public comments."
`## Answer rules (also applied in the assistant's configuration)` — 4 numbered:
1. "Answer from project documents; cite the document and its vintage."
2. "When asked for a decision or approval, state the boundary above and point to the responsible human authority (building official, Fire Marshal, utility, governing board)."
3. "When asked about results, quote canonical contract values (**v1.0.0, generated 2026-07-19**) and include the relevant assumption labels (uncalibrated demand, screening-class costs, placeholder capacity, **eGRID2023r2** emissions factor)."
4. "Direct formal feedback to the municipal channels on the engagement page."
**Numbers this patch changes:** 12 sites; contract v1.0.0; 2026-07-19.
**Phase-8 detection test:** does the assistant page contain `explanation-only`? Does the assistant's answer to "is FFX002 approved?" state the boundary? Is Cognito still enforced?

### Patch 9 — Accessibility pass (all pages)
(PATCH_GUIDE lines 50-53)
alt text on all new images; **one `h1` per page**; visible focus states on new links; contrast of new text blocks **≥ WCAG AA**.
**Numbers this patch changes:** none.

### Acceptance checklist (PATCH_GUIDE lines 55-61) — 6 items, verbatim
- [ ] Privacy + authority disclaimers reachable from every page
- [ ] All results numbers match contract v1.0.0 values
- [ ] Source-vintage footer on every page
- [ ] Assistant answers state explanation-only boundary when asked for decisions
- [ ] No secrets/credentials introduced (grep bundle for `AKIA`, `secret`, `apikey` before upload)
- [ ] Cognito authentication still required for the assistant

**⚠ Checklist item 2 cannot pass as the package currently stands** — the ports table in `content/results_2036_2046_2056.md` does not match contract v1.0.0. Fixing Finding F-01 is a precondition for any honest application of this patch package.

### Was the patch ever applied? — evidence available in-repo
1. **Package's own declaration:** "Nothing in this package has been deployed. No AWS resource, DNS entry, or live page was touched in this run." (`website-patch-package/README.md:3-4`); DEPLOYMENT_RUNBOOK title "**NOT run in this implementation**".
2. **Governance register:** `docs/operations/open-human-actions.md` row 9 is **open** ("Apply the website/assistant patch and deploy per runbook"), and the file's header states "none has been executed".
3. **Independent corroboration from the current program's own discovery pass** (I did not inventory `docs/operations/v4-program/`, per lane scope, but a repo-wide grep surfaced these two lines and they are directly load-bearing for Phase 8):
   - `docs/operations/v4-program/AWS_INVENTORY.md:140`: "The eGRID factor is equally absent: **neither `596.3` nor `590.2` appears anywhere on the live site or in the** …"
   - `docs/operations/v4-program/LEDGER.md:139`: "FIND-AWS-03 | high | The live site carries **no horizon convention at all** — `2036`/`2046`/`2056` and `2035`/`2050` all appear zero times across five pages and the served PDF. Neither `596.3` nor `590.2` appears anywhere live. `58.8` appears twice and FFX002 is correctly the top candidate."
   → **Conclusion: Patches 1, 3, 4, 7 (and by inference the whole package) were never applied to the live site.** The live site carries neither the new horizons nor the emissions factor — the two most distinctive strings the patch introduces. Phase 8 should treat the entire package as unapplied and re-verify Patches 2, 5, 6, 8, 9 directly against the live site.

---

## PART 3 — HORIZON-YEAR AUDIT (every mention across the 22 lane files)

Canonical convention: **2026 baseline + 2036 / 2046 / 2056**. Occurrences of 2035, 2050, "Now", or "10/20/30-year" are defects **unless** explicitly and correctly framed as legacy/legacy_v2.

| # | File:line | Text | Verdict |
|---|---|---|---|
| H-1 | `docs/WORKFLOW_STEPS.md:7` | "right_sizing — … (**legacy 2035/2050** or V3 2026/2036/2046/2056)" | ✅ **legitimate** — word "legacy" adjacent; generated verbatim from `workflow.py:40` |
| H-2 | `docs/migration-from-v2.md:17` | "**2035/2050 labels (Python), 2026–2046 (Excel), Now/2035/2050 (MATLAB) — three truths**" (in the "V1/V2 (before)" column) → "one canonical set: 2026 baseline + **2036/2046/2056**" | ✅ **legitimate** — explicit before/after table; the whole point of the row |
| H-3 | `docs/migration-from-v2.md:56` | "2036: 1.9/2.6 · 2046: 3.0/4.5 · 2056: 4.0/6.0, stress ×1.15" | ✅ canonical; matches `config.py:42-51` |
| H-4 | `docs/migration-from-v2.md:64` | "The **2035/2050 column names** are replaced by horizon-year columns in the contract." | ✅ **legitimate** — breaking-change note |
| H-5 | `docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:22` | "\| **2035 base / 2035 high / 2050 base / 2050 high** \| 35 / 44 / 44 / 54 \| 35 / 44 / 44 / 54 \|" | ⚠ **legitimate-by-context, weakly labelled** — the document is titled "Legacy Baseline Verification (frozen 2026-07-19)" and every section is about V1/V2, but the row itself never carries the token `legacy_v2`. Low-severity; recommend adding "(legacy_v2 mode)" to the row label so a copied fragment stays self-labelling. |
| H-6 | `PATCH_GUIDE.md:10-11` | REPLACE `"2035/2050"` → `"10/20/30-year horizons (2036 / 2046 / 2056 from a 2026 baseline)"` | ✅ **correct** — this is the instruction that *removes* the stale convention, and the replacement text uses the approved bridge form |
| H-7 | `content/methodology_update.md:8-9` | "canonical **10/20/30-year** horizons — **2036/2046/2056 from a 2026 baseline**" | ✅ **correct bridge form** |
| H-8 | `content/methodology_update.md:22` | "2036: 1.9×/2.6×; 2046: 3.0×/4.5×; 2056: 4.0×/6.0×" | ✅ canonical |
| H-9 | `content/results_2036_2046_2056.md:1` | "## Results at **10 / 20 / 30 years (2036 · 2046 · 2056)**" | ✅ **correct bridge form** |
| H-10 | `content/results_2036_2046_2056.md:9-12, 21-23` | horizon rows 2026 / 2036 / 2046 / 2056 | ✅ canonical years (but see F-01 for the *values*) |
| H-11 | `docs/methodology/current-facts-source-register.md:15` (IM-09) | "two aspects at **10/20/30-year timelines**" | ✅ **legitimate** — verbatim quotation of the DiscoverE fellowship requirement (EX01); this is the *origin* of the convention, correctly recorded as a requirement rather than as a model horizon |
| H-12 | `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md:82` | "~**10-year** electronics refresh horizon documented (industry practice benchmark, EX15 class)" | ✅ **not a planning horizon** — an equipment replacement interval, marked TBV by manufacturer |
| H-13 | `docs/WORKFLOW_STEPS.md:10` | "economics — … at **2036/2046/2056**" | ✅ canonical |

**No stale/unlabelled 2035, 2050, or bare "Now" horizon usage was found in any lane file.** The lane is horizon-clean.

**Adjacent observation for later phases (data layer, not this lane):** the contract's own `horizon_label` column carries the literal value **`now`** for 2026 (`data/contract/v1/scenario_table.csv`; defined at `src/fcf_m2/config.py:28 V3_HORIZON_LABELS = {2026: "now", 2036: "plus10", 2046: "plus20", 2056: "plus30"}`). This is a machine label for the 2026 baseline, not a legacy horizon, but any grep-based "no 'Now' horizons" check will hit it. Worth deciding once, in Phase 1, whether to rename it `baseline`.

---

## PART 4 — HEADLINE-NUMBER REGISTER (every number in the lane, and whether it traces)

| Number | Where it appears in this lane | Traces to | Verdict |
|---|---|---|---|
| **596.3 lb CO2e/MWh** (eGRID2023 Rev 2, SRVC) | `current-facts-source-register.md:7` (IM-01); `content/source_vintage_footer.html:3`; `content/results_2036_2046_2056.md:28`; `content/limitations_update.md:9-10` | `data/contract/v1/contract_manifest.json` `grid_factor.value_lb_per_mwh = 596.3`; `data/contract/v1/assumptions.json:64`; `src/fcf_m2/config.py:91` | ✅ **correct, current** |
| **590.2** | `current-facts-source-register.md:7` only, as an explicit superseded-value correction ("research register EX10 carried ≈590.2 … EPA's published … is 596.326 lb/MWh") | — | ✅ **correctly quarantined**; survives nowhere as a live value |
| **12 sites** | 8 lane files | `data/contract/v1/scenario_table.csv` (12 distinct site_ids) | ✅ |
| **FFX002 58.8 (Medium)** | `BASELINE_VERIFICATION.md:18`; `migration-from-v2.md:48`; `reproduction-guide.md:25`; `content/methodology_update.md:6` | `tests/test_legacy_golden.py` + frozen fixtures; enforced by `make run-legacy`/CI | ✅ |
| **25 starter / 48 pathway ports** | `BASELINE_VERIFICATION.md:20-21`; `migration-from-v2.md:48-49,56`; `reproduction-guide.md:25,91`; `content/methodology_update.md:6`; `content/results_2036_2046_2056.md:9` | contract 2026 baseline: ports_active sum **25**, ports_pathway_capacity sum **48**; `verify.sh` + CI grep `"starter_total": 25` / `"pathway_total": 48` | ✅ |
| **0 High-confidence sites** | `BASELINE_VERIFICATION.md:19`; `content/methodology_update.md:6`; `content/limitations_update.md:3`; `PATCH_GUIDE.md:25` | contract: all 120 rows `data_confidence = Low` | ✅ |
| **38 REVIEW + 12 INFO** | `BASELINE_VERIFICATION.md:23`; `content/methodology_update.md:6` | legacy V2 reproduction (evidence record) | ✅ internally consistent |
| **35 / 44 / 44 / 54** (2035b/2035h/2050b/2050h) | `BASELINE_VERIFICATION.md:22` | legacy V2 run; distinct from the V3 contract | ✅ legacy-only |
| **15 Tableau exports · 35 package files · 25 steps · 12/12 sites** | `BASELINE_VERIFICATION.md:9-25` | legacy V2 run evidence; 15 `tableau_*.csv` lines confirmed in `v2_output_hashes.txt:30-44` | ✅ |
| **14 / 71 hash-file entries** | `BASELINE_VERIFICATION.md:36` | `v1_output_hashes.txt` = 14 lines; `v2_output_hashes.txt` = 71 lines | ✅ |
| **80 tests · coverage ≥ 80%** | `reproduction-guide.md:16,90` | 78 `def test_*` + one 3-way `@pytest.mark.parametrize` = 80; `--cov-fail-under=80` in `Makefile`, `verify.sh`, `tests.yml` | ✅ |
| **120 scenario rows** | `reproduction-guide.md:34` | `data/contract/v1/scenario_table.csv` = 120 data rows; asserted in `verify.sh` and `tests.yml` (`assert len(mg) == len(st) == 120`) | ✅ |
| **9 visuals** | `reproduction-guide.md:46`; `PATCH_GUIDE.md:16` | 9 PNGs in `dashboard/static/`; `verify.sh` asserts `ls dashboard/static/0*.png \| wc -l -eq 9` | ✅ |
| **SIM_RANDOM_SEED = 20260719** | `reproduction-guide.md:97` | `src/fcf_m2/config.py:86` | ✅ |
| **contract v1.0.0, generated 2026-07-19** | package README:31; footer html:2; assistant_boundaries:18; results content:3 | manifest `contract_version 1.0.0`, `generated_utc 2026-07-19T05:23:22.507266+00:00`, `run_id milestone2_v3_20260719T052322Z` | ✅ |
| **site inputs 2026-06-24** | `content/source_vintage_footer.html:2` | `dashboard/static/footer_log.json` `"source_date": "inputs 2026-06-24; …"` | ✅ (attributed, though not to the contract itself) |
| **Growth multipliers 1.9/2.6, 3.0/4.5, 4.0/6.0, stress ×1.15** | `migration-from-v2.md:56`; `content/methodology_update.md:22` | `src/fcf_m2/config.py:42-51` | ✅ |
| **NPV $1.56M/$2.29M/$3.01M · broad $1.87M/$2.64M/$3.41M · avoided $0.31M/$0.34M/$0.39M** | `content/results_2036_2046_2056.md:21-23` | contract sums: 1.560/2.294/3.014; staged+avoided 1.872/2.635/3.407; avoided 0.312/0.341/0.393 | ✅ |
| **≈43 → ≈173 t/yr base, ≈260 t/yr high** | `content/results_2036_2046_2056.md:26-27` | contract net_co2e_kg sums: 43.4 / 173.4 / 260.2 t | ✅ |
| **Ports 44→47 (2036), 47→48 (2046), 47→48 (2056)** | `content/results_2036_2046_2056.md:10-12` | contract: **35→44, 44→48, 44→48** | ❌ **DOES NOT TRACE — Finding F-01** |
| **"13–23 pathway ports" not energized** | `content/results_2036_2046_2056.md:29` | `dashboard/tableau/patch_package/tbl_avoided_evse.csv`: 2026 **23**, 2036 base **13**, 2046 base **4**, 2056 base **4** | ⚠ true for 2026/2036 only; and it *contradicts the same file's own ports table* |
| **$885M NEVI FY2026 · $207.5M Fairfax GF · $1.955B PWC GF · 50%/100% Dominion incentive** | `current-facts-source-register.md:12-14` (IM-06, IM-07, IM-08) | external primary sources, cited with URLs and access dates; **not contract-derived and not claimed to be** | ✅ correctly attributed to sources, not the contract |
| **17 stations decommissioned · one year of ADA redesign** | `FINAL_STANDARDS_APPLICATION_MATRIX.md:159`; `PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md:13,83` | client interview evidence (EX09, Adams/Neabsco), not the contract; framed as qualitative | ✅ correctly attributed |
| **NEVI 97% uptime** | `TECHNICAL_INTEGRATION_ARCHITECTURE.md:44` | cited as "benchmark practice", not a project result | ✅ |
| **11 surface lots + 1 commuter garage = 12** | `TECHNICAL_INTEGRATION_ARCHITECTURE.md:19` | consistent with 12 sites; PWC002 Neabsco named as the single enclosed candidate in 3 lane files | ✅ internally consistent |

---

## PART 5 — FINDINGS (detail; the structured return carries the same list)

### F-01 (HIGH) — The three-horizon ports table does not trace to the contract, and contradicts its own file
`docs/operations/website-patch-package/content/results_2036_2046_2056.md:10-12` publishes
`2036 = 44 base / 47 high`, `2046 = 47 / 48`, `2056 = 47 / 48`.
Aggregating all 120 rows of `data/contract/v1/scenario_table.csv` by `horizon_year` × `scenario_name` gives
`2036 = 35 / 44`, `2046 = 44 / 48`, `2056 = 44 / 48`. Independently confirmed against
`dashboard/tableau/patch_package/tbl_canonical_scenarios.csv` (identical sums).
The same file's line 3 asserts "**All values from canonical contract v1.0.0**", and `PATCH_GUIDE.md:23-24`
mandates "Every number on this page must trace to `data/contract/v1/scenario_table.csv`; remove any figure
that does not."
**Internal contradiction inside the same file:** line 29 says the staged plan "avoids energizing **13–23**
pathway ports". With a 48-port ceiling, 13 avoided ports implies 35 active at 2036 — the *contract* value —
not the 44 printed two tables above. The prose is right; the table is wrong.
**Blast radius (same wrong figures, outside this lane):**
- `README.md:38-40` (root, "Headline results (canonical contract v1.0.0, screening values)"): `44 → 47`, `47 → 48`, `47 → 48`
- `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:36-39`: identical
- `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:67`: "Spot-check numbers against the deck's canonical set: … `44→47 & 47→48` …" — i.e. the *spot-check list itself* enshrines the wrong values
Notably, in the very same table rows the CO2e ranges (`≈82–113`, `≈130–195`, `≈173–260 t/yr`) **do** match the
contract's base→high pairs exactly, so the error is isolated to the ports column.
**No existing gate catches this.** `verify.sh` and CI validate the contract's internal rules and the
MATLAB reconciliation, but nothing asserts that prose headline numbers equal contract aggregates.
**Phase 1 must:** correct all four locations to `35 → 44 / 44 → 48 / 44 → 48`, and add a
prose-vs-contract assertion to `verify.sh`.

### F-02 (HIGH) — `./scripts/verify.sh` cannot pass at HEAD; two docs claim it does
`scripts/verify.sh` gate *"hygiene: no local absolute paths in code/config"* runs
`! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'`.
Tracked file `dashboard/static/footer_log.json` contains nine absolute local paths of the form
`"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/01_readiness_ranking.png"` (lines 7, 14, 21, 28, 35, 42, 49, 56, 59).
I ran the exact grep: **9 matches**, so the gate fails and `verify.sh` exits nonzero.
This contradicts, in this lane:
- `docs/operations/reproduction-guide.md:93` — "`./scripts/verify.sh` → `ALL REPOSITORY VERIFICATION GATES PASSED`"
- `docs/operations/reproduction-guide.md:62` — "every repository gate; exits nonzero on any failure"
- `docs/repository-migration-plan.md:34` — build scripts "rewritten to repo-relative paths (**no machine-specific paths remain**)"
- `docs/repository-migration-plan.md:61` — "**no secrets, no local paths**"
It is also a genuine information leak (the author's local directory structure) and the exact class of defect
Phase 0 was told to hunt. The generator is `scripts/build_static_dashboard.py` via
`src/fcf_m2/visuals.py`, which records `Path(...)` as given; regenerating in a clean clone would write
repo-relative paths. `src/fcf_m2/visuals.py: audit_footer_metadata` only compares `Path(e["file"]).name`,
so the footer-QA gate still passes — the leak is invisible to every gate except the one CI does not run.

### F-03 (MEDIUM) — "CI runs the same gates" is false
`docs/operations/reproduction-guide.md:68-69` states: "Gates: tests + coverage floor, legacy baseline
reproduction (25/48), contract rules/schema/hash chain, cross-model reconciliation with the MATLAB canonical
CSV, workflow-docs consistency, dashboard footer QA, secret scan, local-path scan, file-size limit, and
Markdown link check. **CI runs the same gates** ([.github/workflows/tests.yml])."
`.github/workflows/tests.yml` runs **6** steps: pytest+coverage, legacy baseline, contract validation,
cross-model reconciliation, internal Markdown links, secret scan. It **omits 4** of the 10:
workflow-docs consistency, dashboard footer QA, local-absolute-path scan, and the 25 MB file-size limit.
The omitted local-path gate is precisely the one that fails (F-02) — so the drift in the doc has been
masking a real failure.
Also: `tests.yml` `on.push.branches: [main, milestone2-v3-professional-release]` — the current working
branch `v4-platform` gets no push-triggered CI (PRs still trigger).

### F-04 (MEDIUM) — Dead reference: `FAILURE_MITIGATION_OPTIONS.csv` does not exist
`docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md:5` lists
"`rankings/FAILURE_MITIGATION_OPTIONS.csv`" as one of three bases for the document, and line 52 says
"full ranking in `FAILURE_MITIGATION_OPTIONS.csv`, carried into `RISK_REGISTER.csv`".
`find . -iname "*FAILURE_MITIGATION*"` over the whole repo returns **nothing**. Only
`reports/milestone-2/RISK_REGISTER.csv` and `.md` exist. The five ranked mitigations in §4 therefore have no
in-repo ranking evidence. (The path is backticked rather than a Markdown link, so `check_internal_links.py`
does not catch it — which is why it survived.)
Phase 1 should either carry the CSV in, or restate the reference as external research-package evidence
the way "Report 06/07/10" and the EX register are cited.

### F-05 (MEDIUM) — The workflow-docs gate checks only the step *count*, not the step *names*
`docs/WORKFLOW_STEPS.md` declares itself generated and "do not edit by hand", and `scripts/verify.sh`
carries a gate named "docs: generated workflow steps match the executable manifest". The gate body is:
`assert f"Step count: **{len(workflow.STEPS)}**" in d`.
It never compares names or descriptions. Renaming `peak_wait` → something else, or editing any of the 11
description strings, drifts the doc silently as long as the count stays 11. (The file is in sync today —
I diffed all 11 pairs against `src/fcf_m2/workflow.py:37-49`.) Phase 1 should replace the assertion with a
full-text equality check against `workflow.generate_docs()`. This gate is also one of the four CI omits (F-03).

### F-06 (LOW) — "13–23 pathway ports" overstates the later horizons
`content/results_2036_2046_2056.md:29`. `dashboard/tableau/patch_package/tbl_avoided_evse.csv` aggregates to
23 avoided ports at the 2026 baseline and 13 at 2036 base, but only **4** at 2046 base and **4** at 2056 base.
The sentence sits under a "10 / 20 / 30 years" heading, so a reader takes 13–23 as the range *across the
three horizons*, which is wrong. Restate as "23 today, 13 at 2036" or give the true per-horizon values.

### F-07 (LOW) — Legacy horizon row not self-labelling
`docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:22` renders
"| 2035 base / 2035 high / 2050 base / 2050 high | 35 / 44 / 44 / 54 | 35 / 44 / 44 / 54 |". The document as a
whole is unambiguously about the legacy baseline, so this is legitimate, but the row itself carries no
`legacy_v2` token and would read as a horizon violation if quoted out of context (and the numbers 35/44/44
collide visually with the V3 contract's 35/44/44). Recommend prefixing the row label with "legacy_v2 mode:".

### F-08 (LOW) — Python version stated three ways
`docs/operations/reproduction-guide.md:5-6` says verified on **Python 3.14** (3.11+ supported);
`docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:3` says the legacy runs used **Python 3.14.6**;
`.github/workflows/tests.yml` pins **3.12**. Not strictly contradictory, but Phase 10's clean-clone test
needs one pinned answer.

### F-09 (INFO) — Two time-anchored statements are now past
`docs/operations/open-human-actions.md:8` row 1 requires the Client Meeting #2 exchange "**before July 21**";
today is 2026-07-27, so the action is overdue as written and needs re-dating rather than silent carry-over.
`docs/methodology/current-facts-source-register.md:12` (IM-06) says Virginia is "anticipated to release
solicitations **Q1 2026**" — that window has closed and the fact needs re-verification. IM-01 also flags
eGRID2024 preliminary data (≈−1.8% CO2e); if EPA has since made it official, the 596.3 factor becomes the
next thing to re-verify (the model already carries an annual-refresh field).

### F-10 (INFO) — Lane is clean on secrets and (in-lane) local paths
I grepped all 22 lane files for `/Users/`, `AKIA`, `aws_secret`, `arn:aws`, and 12-digit account-ID patterns.
Zero true positives. The only hits were 12-hex-character substrings inside SHA-256 digests in
`v2_output_hashes.txt` and the literal word "AKIA" inside `PATCH_GUIDE.md:60`'s own instruction to grep for
it. `DEPLOYMENT_RUNBOOK.md` correctly parameterises `<bucket>` and `<ID>` and states credentials are "never
stored in this repo". The absolute-path leak in F-02 is in `dashboard/static/footer_log.json`, outside this
lane.

### F-11 (INFO) — All 22 Markdown links in the lane resolve
Verified programmatically across all 22 files. The only backticked paths that do not exist on disk are
intentional: git branch names (`archive/pre-milestone2-v3-20260719` — confirmed to exist as
`remotes/origin/archive/pre-milestone2-v3-20260719`), pre-migration workspace paths (`repos/…`,
`data_contract/v1`), and deliberately-removed legacy scripts (`src/run_v2.py`, `src/check_outputs_v2.py`, …)
whose removal `migration-from-v2.md:61-62` documents. The one genuine dead reference is F-04.
