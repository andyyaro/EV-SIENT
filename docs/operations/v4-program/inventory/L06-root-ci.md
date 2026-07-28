# LANE L06 — ROOT FILES AND CI (Phase-0 ground-truth inventory)

Repo root: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo`
Branch: `v4-platform` (HEAD `95e91e0` "docs(v4-program): initialize program ledger").
Tracked file count at time of read: **199** (`git ls-files | wc -l`). Working tree clean.
Remote: `https://github.com/andyyaro/Future-City-Fellowship-.git` (repo name genuinely ends in a hyphen).
Local branches: `main`, `v4-platform`. Remote branches: `origin/main`, `origin/archive/pre-milestone2-v3-20260719`,
`origin/milestone2-v3-professional-release`, `origin/v2-expansion-planning`.
Tags: `pre-milestone2-v3-20260719`, `pre-v4-program-20260727`, `v1-demo-scalability-ready`, `v1-review-ready`.

Every file below was read end to end (no skimming, no partial reads).

---

### README.md
- **Role:** The repository's landing page and public claim surface: what the project is, the headline numbers, the architecture diagram, the repo map, key documents, verification claims, standards boundary, known limitations, status, team, license.
- **Kind:** authored
- **Reads:** n/a (prose). It *references* `docs/assets/readme/project-overview.png` as an inline image and 22 internal link targets (all verified to exist on disk — see "Link audit" below).
- **Written by / read by:** Hand-authored. Consumed by humans and by GitHub. `scripts/check_internal_links.py` (run by both `tests.yml` and `scripts/verify.sh`) checks its links; `verify.sh` line 66 names `README.md` explicitly in the optional `lychee` invocation.
- **Key contents:** 152 lines.
  - **Title (L1):** `# Future City Fellowship — Safe, Code-Responsive EV Charging Planning`; scope "**Fairfax City** and **Prince William County**, Virginia" (L3-4).
  - **Badges (L6-8):** tests badge → `https://github.com/andyyaro/Future-City-Fellowship-/actions/workflows/tests.yml/badge.svg`; `python-3.11+`; `MATLAB-R2025b (static checks only)`.
  - **Hero image (L10):** `docs/assets/readme/project-overview.png`, alt text "Staged pilots beat broad buildout at every horizon".
  - **What this project is (L14-19):** "a **planning-support prototype** built by a George Mason University Future City Fellowship team that screens 12 real public candidate sites, right-sizes charger deployments, and models outcomes at 10/20/30-year horizons (2036 / 2046 / 2056 from a 2026 baseline)."
  - **THE HUMAN PROBLEM NARRATIVE — verbatim, L21-26 (Phase 9 leads with this):**
    > **The leading strategy it supports:** *staged, evidence-gated deployment* — start with
    > 25 charging ports at the strongest sites, pre-build expandable civil/electrical pathways
    > for up to 48, and energize more only when observed utilization, wait, and reliability
    > data clear predefined, equity-aware triggers. This is the direct answer to the client's
    > own operating history (a 70-port garage installation that ended with 17 stations
    > decommissioned, and a trenching-driven cost overrun).
  - **"What this is not" blockquote — verbatim, L28-32:**
    > **What this is not.** This is not engineering approval, a permit or code determination,
    > a utility capacity confirmation, an official forecast, or a budget. Site *readiness*
    > is not construction *approval*: **0 of 12 sites have High data confidence, and
    > electrical capacity is a labeled placeholder at all 12 sites** pending utility and
    > facility verification.
  - **HEADLINE RESULTS TABLE (L34-46), header "Headline results (canonical contract v1.0.0, screening values)":**

    | Horizon | Active ports (base → high path) | Staged plan NPC | Broad buildout NPC | Staged avoids | Net CO2e avoided |
    |---|---|---|---|---|---|
    | 2026 | 25 | — | — | — | ≈43 t/yr |
    | 2036 | 44 → 47 | $1.56M | $1.87M | **$0.31M** | ≈82–113 t/yr |
    | 2046 | 47 → 48 | $2.29M | $2.64M | **$0.34M** | ≈130–195 t/yr |
    | 2056 | 47 → 48 (48-port pathway ceiling) | $3.01M | $3.41M | **$0.39M** | ≈173–260 t/yr |

  - L43-46: "Costs are screening-class net present cost (**3% real**, base escalation) — never budgets. Emissions use the EPA **eGRID2023 Rev 2 SRVC** factor (**596.3 lb CO2e/MWh**, refreshed annually) with labeled displacement assumptions. Top-ranked site: **FFX002 — City of Fairfax Regional Library (58.8, Medium confidence)**."
  - **ARCHITECTURE — mermaid `flowchart LR` (L50-58)** and the load-bearing sentence, **verbatim L60-62:**
    > Python is the single producer; MATLAB, Excel, Tableau, and every visual consume the
    > same validated contract, so no two artifacts can disagree about a port count, a year,
    > or whether capacity is a placeholder (`capacity_basis` travels with every row).

    Flow nodes: `A[12-site inputs data/inputs] --> B[Python model src/fcf_m2 · readiness · right-sizing · waits · economics · emissions · triggers] --> C[Canonical data contract data/contract/v1 · site x horizon x case, validated]`, and `C` fans out to `D[MATLAB site-load model matlab/]`, `E[Excel workbook excel/]`, `F[Static dashboard + Tableau patch dashboard/]`, `G[Reports + presentation reports/ · presentation/]`.
  - **Two model modes table (L66-69):** `legacy_v2` = "Bit-exact reproduction of the accepted V2 baseline (golden-tested: FFX002 58.8; 25 starter / 48 pathway ports)"; `milestone2_v3` = "Canonical 2036/2046/2056 horizons, cohort-independent fixed-anchor scoring, typed data confidence, peak-window + discrete-event waits, lifecycle economics, emissions, equity-aware expansion triggers". L71-72: "V3 never silently replaces legacy numbers — see the `[migration guide](docs/migration-from-v2.md)`."
  - **Quick start (L76-83):** `make setup`, `make test` ("80 tests incl. legacy golden tests (coverage gate 80%)"), `make run-legacy`, `make run-v3`, `make validate`, `./scripts/verify.sh`.
  - **Requirements (L85-88):** "Python 3.11+ (verified on 3.12/3.14). MATLAB R2025b for the `matlab/` model (**not required** for anything above — and note that the MATLAB code has been statically checked but never executed; see `[matlab/EXECUTION_STATUS.md](matlab/EXECUTION_STATUS.md)`)."
  - **Repository map (L92-103):** 10 rows → `src/fcf_m2/`→`src/README.md`, `data/`→`data/README.md`, `tests/`→`tests/README.md` ("80-test suite incl. golden legacy fixtures and contract validation"), `matlab/`, `excel/`, `dashboard/` ("Offline static dashboard (9 visuals) + Tableau patch package"), `reports/`, `presentation/`, `docs/`, `scripts/`.
  - **Key documents (L107-112):** final report, deck PDF + speaker notes, gap-closure status ("all 52 fellowship criteria dispositioned"), standards application matrix ("UL 2594 + UL 3600 highlighted; adopted-vs-latest editions"), proposed standard concept ("fellowship design exercise, not a UL/ULSE proposal"), reproduction guide, migration from V2, open human actions.
  - **Verification (L116-120), verbatim:** "`./scripts/verify.sh` runs every gate: the pytest suite with a coverage floor, legacy baseline reproduction, contract rule/schema/hash-chain validation, cross-model reconciliation against the MATLAB input, footer QA on every dashboard visual, secret and local-path scans, size limits, and Markdown link checks. **CI runs the same gates on every push and pull request** (`[tests.yml](.github/workflows/tests.yml)`)."
  - **Standards and safety boundary (L124-129):** governed by **UL 2594** (EVSE safety) and **UL 3600** (circular-economy measurement); supporting: UL 2231, **NEC Article 625 as adopted in Virginia (2020 NEC via the 2021 USBC)**, Virginia SFPC, US Access Board EVSE guidance ("rule at NPRM stage as of July 2026"). "Storage and DC-fast-charging standards are explicitly out of scope (no BESS or DCFC in the plan). All permit, disconnect-placement, access, and code-edition determinations rest with the local AHJ."
  - **KNOWN LIMITATIONS — verbatim, all six, L131-138:**
    > ## Known limitations
    >
    > 1. Electrical capacity is a placeholder at 12/12 sites (`capacity_basis = placeholder`).
    > 2. Demand is synthetic and uncalibrated; growth multipliers are provisional conventions.
    > 3. Costs are screening-class benchmarks; emissions rest on labeled assumptions.
    > 4. MATLAB code is statically checked only — no execution has occurred (no license was available).
    > 5. The Tableau `.twbx` was not rebuilt/verified — the static dashboard is the guaranteed artifact; a complete `[patch package](dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md)` exists for a Tableau Desktop operator.
    > 6. Client, team-adoption, AHJ, utility, and funding steps remain open — see `[open human actions](docs/operations/open-human-actions.md)`.
  - **Project status (L142-144):** "Milestone 2 package complete (July 2026); presentation 2026-07-21. Next phase: client follow-up, utility/facility data requests (which upgrade `capacity_basis` from placeholder), AHJ conversations, and pilot preparation."
  - **Team (L148-150):** "Anna · Laylas · Andy · Adama · Paula — George Mason University Future City Fellowship, in consultation with Prince William County's Office of Sustainability and Fire & Rescue interviewees."
  - **LICENSE POSITION — verbatim, L152:** `*License: not yet selected — all rights reserved by the team until a license is chosen.*`
- **Notes / defects:**
  - **The "Active ports (base → high path)" column does not trace to `data/contract/v1/`.** Summing `ports_active` over the 12 sites in `data/contract/v1/scenario_table.csv` gives base path **25 → 35 → 44 → 44** and high path **25 → 44 → 48 → 48**. The README publishes 44→47 / 47→48 / 47→48. The value **47 appears nowhere** in the contract (no site-row sum produces it; `grep -c ',47,' data/contract/v1/scenario_table.csv` = 0). Every other number in that table reconciles exactly (see below). Same wrong figures propagate to `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:38-40`, `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md:74` ("25 → 44 → 47 → 47 on the base path; 25 → 47 → 48 → 48 on the high path"), and `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:67`.
  - **Everything else in the headline table reconciles**, verified by summing `data/contract/v1/scenario_table.csv`: 2026 baseline ports = 25 ✓, net CO2e 43,365 kg ≈ 43 t ✓; 2036 NPC 1,560,499 → $1.56M ✓, avoided 312,079 → $0.31M ✓, broad = staged+avoided = $1.87M ✓, CO2e 82,385/112,746 kg → "≈82–113 t/yr" ✓; 2046 2,294,469 → $2.29M ✓, 341,169 → $0.34M ✓, $2.64M ✓, 130,089/195,131 → "≈130–195" ✓; 2056 3,014,200 → $3.01M ✓, 393,406 → $0.39M ✓, $3.41M ✓, 173,450/260,179 → "≈173–260" ✓. `ports_pathway_capacity` sums to 48 at every horizon ✓. The identical aggregation holds in `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv` and `matlab/data/canonical/matlab_scenarios.csv`.
  - **"FFX002 … (58.8, Medium confidence)" (L46) sits under a heading that claims canonical-contract provenance, but neither value is in the contract.** `data/contract/v1/scenario_table.csv` has no readiness-score column, and its `data_confidence` is **`Low` in all 120 rows**. 58.8 + "medium" come from the frozen legacy V2 artifacts (`data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2`, `tests/fixture_legacy_v2_right_sizing.csv:2`); the V3 typed confidence for FFX002 is `Low` (`dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2`).
  - **L120 "CI runs the same gates on every push and pull request" is false on both halves.** `tests.yml` omits 4 of `verify.sh`'s 10 gates (docs step-count, dashboard footer QA, local-path scan, 25 MB size limit) — the README even names "footer QA on every dashboard visual", "local-path scans", and "size limits" in the sentence immediately before. And the push trigger is limited to `branches: [main, milestone2-v3-professional-release]` (`tests.yml:4-5`), so pushes to the current `v4-platform` branch run no CI at all.
  - L18 "10/20/30-year horizons" is correctly glossed with the canonical years, matching the prescribed wording in `docs/operations/website-patch-package/PATCH_GUIDE.md:10`. **Not** a horizon violation. But the prose says three horizons while the contract and the README's own table carry **four** horizon years {2026, 2036, 2046, 2056} (asserted in `verify.sh:39` and `tests.yml:45`).
  - eGRID **596.3** at L44 is correct and current.
  - License is explicitly unselected (L152) — relevant before any public deployment in Phase 8.
  - "80 tests" (L78, L96) is consistent: `tests/` has 78 `def test_` functions, one of which is `@pytest.mark.parametrize`d over 3 values (`tests/test_scoring_and_queueing.py:32`) → 77 + 3 = 80 collected. **Not** a defect.
  - "9 visuals" (L99) verified: `ls dashboard/static/0*.png | wc -l` = 9.
  - "all 52 fellowship criteria" (L109) verified against `reports/milestone-2/Milestone_2_Gap_Closure_Status.md:1` and `reports/README.md:10` (29 closed / 11 already complete / 9 ready for human action / 2 partial / 1 blocked).

**Link audit — every internal target referenced in README.md exists on disk (0 broken):**
`docs/assets/readme/project-overview.png`, `docs/migration-from-v2.md`, `matlab/EXECUTION_STATUS.md`,
`src/README.md`, `data/README.md`, `tests/README.md`, `matlab/README.md`, `excel/README.md`,
`dashboard/README.md`, `reports/README.md`, `presentation/README.md`, `docs/README.md`, `scripts/README.md`,
`reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`,
`presentation/deck/Future_City_Fellowship_Milestone_2_Final.pdf`,
`presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md`,
`reports/milestone-2/Milestone_2_Gap_Closure_Status.md`,
`docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md`,
`docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md`,
`docs/operations/reproduction-guide.md`, `docs/operations/open-human-actions.md`,
`dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md`, `.github/workflows/tests.yml`.
The two external badge URLs (github.com actions badge, img.shields.io) were not network-checked.

---

### CHANGELOG.md
- **Role:** Single-release changelog for the Milestone 2 V3 publication plus a pointer to pre-V3 git history.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Hand-authored; links to `docs/repository-migration-plan.md` and `docs/migration-from-v2.md` (both exist).
- **Key contents:** 52 lines. One release heading: `## Milestone 2 V3 (2026-07-19)` (L3).
  - **Model (L8-24):** dual-mode model in `src/fcf_m2` (`legacy_v2` bit-for-bit, "golden-tested: FFX002 58.8; 25 starter / 48 pathway ports"; `milestone2_v3` canonical); canonical data contract `data/contract/v1` — "one validated site x horizon x case table (**120 rows**)" with "schema, provenance, assumptions, and a manifest hash chain"; fixed-anchor cohort-independent scoring with typed data confidence — "**0 of 12 sites reach High confidence**, and electrical capacity remains a labeled placeholder at all 12 sites"; peak-window + DES wait models; lifecycle economics.
  - **HORIZON CONVENTION — verbatim, L16-17:**
    > - **Canonical horizons** 2036 / 2046 / 2056 (10/20/30 years from a 2026
    >   baseline), replacing the mixed Now/2035/2050 conventions.
  - **eGRID CORRECTION — verbatim, L22-24, under version heading `## Milestone 2 V3 (2026-07-19)`:**
    > - **Peak-window and discrete-event-simulation wait models**, **lifecycle
    >   economics** (screening-class net present cost, never budgets), and
    >   **emissions** using the EPA eGRID2023 Rev 2 SRVC factor of
    >   **596.3 lb CO2e/MWh** — correcting the 590.2 figure used earlier.
  - **Artifacts (L26-43):** MATLAB V3 rewrite — "Statically checked only — **never executed** (no license was available); see `matlab/EXECUTION_STATUS.md`"; Excel workbook update ("repaired pie chart, labeled proxies, 2056 extension, lifecycle + CO2e sheets, live reconciliation checks"); static dashboard ("9 offline, footer-labeled, contract-derived visuals + combined PDF; Tableau patch package and honest blocker note in `dashboard/tableau/`"); standards package; presentation package; reports + human-action packages + operations docs; "`./scripts/verify.sh` runs every verification gate".
  - **Pre-V3 history (L45-52):** V1/V2 trees preserved in branch `archive/pre-milestone2-v3-20260719` and annotated tag `pre-milestone2-v3-20260719`, plus V1 tags `v1-demo-scalability-ready` and `v1-review-ready`. **All four git refs verified to exist** (`archive/…` as `remotes/origin/archive/pre-milestone2-v3-20260719`).
- **Notes:** The `Now/2035/2050` mention at L17 is correctly labelled as the *replaced legacy* convention — legitimate, not a defect. The 590.2 mention at L24 is a correction record, not a live value — legitimate. **No entry exists for the V4 platform program**, even though tag `pre-v4-program-20260727` and HEAD commit `95e91e0` (which added `docs/operations/v4-program/LEDGER.md`) are already on `v4-platform`. There is no `[Unreleased]` section and no Keep-a-Changelog scaffolding.

---

### CONTRIBUTING.md
- **Role:** Contributor rules: how to set up/test/verify, the non-negotiable claims-discipline rules, the golden-test freeze rule, and PR expectations.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Hand-authored; links to `docs/operations/reproduction-guide.md` (L14) and `.github/pull_request_template.md` (L46) — both exist.
- **Key contents:** 49 lines.
  - **Setup/test/verify block (L5-12):** same six commands as the README, with `./scripts/verify.sh # every repository gate — must pass before you open a PR` (L11) and `make test # 80 tests incl. legacy golden tests; coverage gate 80%` (L7).
  - **Claims discipline (non-negotiable) (L16-33)** — four bullets plus a MATLAB rule:
    1. "**Never present placeholder capacity as verified.** `capacity_basis` is `placeholder` at all 12 sites; any output showing capacity must carry that label until utility/facility verification upgrades it." (L21-23)
    2. "**Never fabricate client, AHJ, utility, or funding outcomes.** The human-action packages in `docs/human-actions/` are instruments for events that have not happened; blank fields stay blank until the real event is documented." (L24-27)
    3. "**Keep the \"0 of 12 sites High confidence\" finding visible.** Do not bury, reword, or soften it in any README, report, visual, or caption." (L28-29)
    4. "**Screening values are not budgets.** Costs are screening-class net present cost; never present them as budgets, bids, or forecasts." (L30-31)
    5. "MATLAB code is statically checked but has never been executed — do not claim otherwise until `matlab/EXECUTION_STATUS.md` records a licensed run." (L32-33)
  - **Golden-test rule (L35-41):** "The legacy fixtures under `tests/` are **frozen**. They encode the accepted V2 baseline (FFX002 58.8; 25/48 port totals). A golden-test failure means the model changed — investigate it. **Do not regenerate goldens to silence a failure.** A deliberate re-baselining requires a documented migration note and reviewer sign-off, never a quiet fixture update."
  - **Pull requests (L43-49):** use the PR checklist; state results impact; confirm `make test`, `./scripts/verify.sh`, `make validate` pass; "Data updates must state source, date, and provenance class."
- **Notes:** L11 ("must pass before you open a PR") and L48 are **currently unsatisfiable as committed** — two `verify.sh` gates fail on the pristine tree (see the verify.sh entry). `docs/human-actions/` exists. The "0 of 12 sites High confidence" rule is directly load-bearing for Phase 9's rewording work: it forbids softening, so any friendlier framing must preserve that exact finding.

---

### Makefile
- **Role:** The developer entry points — venv setup, tests, the two model runs, contract validation, dashboard build, docs regeneration, and the verify harness.
- **Kind:** authored
- **Reads:** `requirements-lock.txt` (as a pip constraints file), `pyproject.toml` (implicitly via `pip install -e`), `scripts/build_static_dashboard.py`, `scripts/verify.sh`.
- **Written by / read by:** Invoked by humans; the same command strings are quoted in `README.md:76-83`, `CONTRIBUTING.md:5-12`, and `docs/operations/reproduction-guide.md`.
- **Key contents:** 27 lines.
  - `PY ?= venv/bin/python` (L1) — overridable.
  - `.PHONY: setup test run-legacy run-v3 validate dashboard docs verify` (L3).
  - `setup` (L5-6): `python3 -m venv venv && venv/bin/pip install -e ".[test]" -c requirements-lock.txt`
  - `test` (L8-9): `$(PY) -m pytest tests/ -q --cov=fcf_m2 --cov-report=term`
  - `run-legacy` (L11-12): `$(PY) -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/legacy_check`
  - `run-v3` (L14-15): `$(PY) -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run`
  - `validate` (L17-18): `$(PY) -m fcf_m2.workflow validate-contract data/contract/v1`
  - `dashboard: run-v3` (L20-21): `$(PY) scripts/build_static_dashboard.py`
  - `docs` (L23-24): `$(PY) -m fcf_m2.workflow docs`
  - `verify` (L26-27): `./scripts/verify.sh`
- **Notes:** **`make test` has no `--cov-fail-under`.** It only prints a terminal coverage report (L9). So the claim "coverage gate 80%" in `README.md:78`, `CONTRIBUTING.md:7`, and `docs/operations/reproduction-guide.md:16,90` is inaccurate for `make test` — the 80% floor exists only in `scripts/verify.sh:24` and `.github/workflows/tests.yml:28`. `make setup` hard-codes `venv/bin/pip`, so `PY=` override does not affect setup. Workflow CLI surface confirmed here: `python -m fcf_m2.workflow` with subcommands **`run` (`--mode legacy_v2|milestone2_v3`, `--out DIR`)**, **`validate-contract DIR`**, **`docs`**.

---

### pyproject.toml
- **Role:** Package metadata and build config for the `fcf-m2` distribution (the `fcf_m2` package under `src/`), plus pytest defaults.
- **Kind:** authored (data-contract-ish: it is the dependency contract)
- **Reads:** `src/` as the package root.
- **Written by / read by:** Consumed by `pip install -e` in `Makefile:6` and `.github/workflows/tests.yml:25`; mirrored by the tracked generated metadata in `src/fcf_m2.egg-info/`.
- **Key contents:** 27 lines.
  - `[build-system]` requires `setuptools>=68`, backend `setuptools.build_meta` (L1-3).
  - `[project]` name = **`fcf-m2`**, version = **`3.0.0`** (L6-7).
  - Description (L8): "Future City Fellowship Milestone 2 V3 planning-support model: site readiness, right-sizing, canonical cross-model contract, lifecycle economics, and emissions. **Planning prototype only - not an engineering, permitting, or procurement tool.**"
  - `requires-python = ">=3.11"` (L9).
  - Core deps (L10-15): `numpy>=1.26`, `pandas>=2.1`, `matplotlib>=3.8`, `jsonschema>=4.20`.
  - Extras (L17-20): `gis` = geopandas>=0.14, contextily>=1.5, xyzservices>=2024.0; `test` = pytest>=8.0, pytest-cov>=4.1; `presentation` = pillow>=10.0, reportlab>=4.0.
  - `[tool.setuptools.packages.find] where = ["src"]` (L22-23).
  - `[tool.pytest.ini_options] testpaths = ["tests"]`, `addopts = "-q"` (L25-27).
- **Notes:** No `[project.license]`, no `license` field, no classifiers — consistent with README L152 ("License: not yet selected"). No `[project.scripts]` console entry point; everything goes through `python -m fcf_m2.workflow`. No lint/format tooling config (no ruff/black/mypy sections) and none in CI.

---

### requirements-lock.txt
- **Role:** Pinned dependency set used as a pip **constraints** file for `make setup`, recording the environment in which V3 verification was run.
- **Kind:** generated (produced by a pip freeze-style step on the author's machine; no generator script is tracked)
- **Reads:** n/a
- **Written by / read by:** Consumed only by `Makefile:6` (`-c requirements-lock.txt`). **Not** used by CI.
- **Key contents:** 21 lines. Header, verbatim L1:
  `# Lock generated 2026-07-19 from Python 3.14.6 arm64 venv used for all V3 verification runs`
  Pins (L2-21): `attrs==26.1.0`, `contourpy==1.3.3`, `coverage==7.15.2`, `cycler==0.12.1`, `fonttools==4.63.0`, `iniconfig==2.3.0`, `jsonschema==4.26.0`, `kiwisolver==1.5.0`, `matplotlib==3.11.1`, `numpy==2.5.1`, `packaging==26.2`, `pandas==3.0.3`, `pillow==12.3.0`, `pluggy==1.6.0`, `pyparsing==3.3.2`, `pytest==9.1.1`, `pytest-cov==7.1.0`, `python-dateutil==2.9.0.post0`, `referencing==0.37.0`, `six==1.17.0`.
- **Notes / COHERENCE QUESTION (explicitly assigned):**
  - The lock header says the verification environment was **Python 3.14.6 arm64**. `.github/workflows/tests.yml:21` pins **`python-version: "3.12"`** on **`ubuntu-latest`** (x86-64). `pyproject.toml:9` allows `>=3.11`. `README.md:85` says "Python 3.11+ (verified on 3.12/3.14)". So the three statements are reconcilable in intent, but **the environment the lock describes is not the environment CI runs**, and CI is x86-64 Linux while the lock is arm64 macOS.
  - Worse: **CI never applies the lock.** `tests.yml:25` runs `pip install -e .[test]` with no `-c requirements-lock.txt`, so CI resolves whatever versions pip picks that day, while `Makefile:6` constrains to the lock. The two supported install paths can therefore produce different dependency sets, and the lock is never exercised by CI.
  - The lock is **incomplete as a lock** (fine as a constraints file, misleading as a name): it omits `rpds-py` and `jsonschema-specifications` (runtime deps of jsonschema 4.26), `tzdata` (pandas), and `setuptools` (the build requirement declared in `pyproject.toml:2`). Marked **uncertain** — I did not resolve dependency trees offline; the omission is inferred from the standard dep graphs.
  - All pinned versions are plausible for a 2026-07 environment (pandas 3.0.3, numpy 2.5.1, pytest 9.1.1); none is knowably fabricated, but I could not verify their existence offline.

---

### .gitignore
- **Role:** Ignore rules for environments, generated model outputs, MATLAB run outputs, OS noise, and local release bundles.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** git. Referenced implicitly by `README.md` L79-80 (outputs reproduced by `make run-v3` / `run-legacy`).
- **Key contents:** 26 lines. **Every pattern, in file order:**
  - `# environments` (L1): `venv/` (L2), `.venv/` (L3), `__pycache__/` (L4), `*.pyc` (L5), `.pytest_cache/` (L6), `.coverage` (L7), `htmlcov/` (L8)
  - `# generated model outputs (reproduce with make run-v3 / run-legacy)` (L10): `data/outputs/` (L11)
  - `# MATLAB run outputs (regenerated by run_all_scenarios on a licensed machine)` (L13): `matlab/outputs/*` (L14), `!matlab/outputs/.gitkeep` (L15), `matlab/simulink/` (L16), `*.slxc` (L17), `*.asv` (L18)
  - `# OS noise` (L20): `.DS_Store` (L21), `Thumbs.db` (L22)
  - `# local release bundles` (L24): `release/` (L25), `*.zip` (L26)
- **Coverage answers (as asked):** `venv/` **YES** (L2, plus `.venv/` L3) · `__pycache__` **YES** (L4) · `.DS_Store` **YES** (L21) · `._*` (macOS AppleDouble) **NO** · `node_modules` **NO**.
- **Notes:** There is exactly one `.gitignore` in the repo (no nested ones) and `.git/info/exclude` is stock. Additional gaps that matter for the V4 work: `*.egg-info/` is **not** ignored — and `src/fcf_m2.egg-info/` is in fact **tracked** (5 files: PKG-INFO, SOURCES.txt, dependency_links.txt, requires.txt, top_level.txt), i.e. a build artifact is committed. Also missing: `dist/`, `build/`, `.env`, `*.log`, `.idea/`, `.vscode/`, `.ruff_cache/`, `node_modules/`, `._*`. The absent `node_modules` / `._*` / `dist` patterns are directly relevant to Phase 3 (the incoming 3D explorer at `incoming/explorer/fcf-3d` is a JS project) and Phase 8 (deploy bundles). `matlab/outputs/.gitkeep` exists on disk, so the negation on L15 is live. `*.zip` (L26) would silently ignore any zipped release bundle placed anywhere in the tree.

---

### .github/pull_request_template.md
- **Role:** GitHub PR checklist enforcing the claims-discipline and verification rules from CONTRIBUTING.md.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** GitHub; referenced by `CONTRIBUTING.md:46`.
- **Key contents:** 29 lines.
  - `## Summary` (L1-3) with an HTML-comment prompt.
  - `## Type of change` (L5-10): four checkboxes — "Model/code change (may alter results — describe below)", "Data update (state source, date, and provenance class)", "Documentation", "CI / tooling".
  - `## Results impact` (L12-17), comment verbatim L14-17: "If any number a reviewer might quote changes, say which and why. Legacy baseline (**25 starter / 48 pathway, FFX002 58.8**) must remain reproducible in `legacy_v2` mode unless a deliberate re-baselining is documented in a migration note."
  - `## Verification` (L19-23): `make test` passes locally · `./scripts/verify.sh` passes locally · "Contract still validates (`make validate`) if data changed".
  - `## Claims discipline` (L25-29): "No placeholder capacity presented as verified" · "No screening estimate presented as a budget/forecast" · "No client/AHJ/utility approval implied that has not occurred".
- **Notes:** The `./scripts/verify.sh passes locally` checkbox (L22) cannot honestly be ticked today — see the verify.sh gate failures below. No `CODEOWNERS`, no issue templates, no Dependabot config in `.github/`.

---

### .github/workflows/tests.yml
- **Role:** The only automatic CI workflow: Python tests, contract validation, cross-model reconciliation, link check, secret scan.
- **Kind:** authored
- **Reads:** the repo checkout; specifically `data/contract/v1/scenario_table.csv` and `matlab/data/canonical/matlab_scenarios.csv` in the reconciliation step, and `scripts/check_internal_links.py`.
- **Written by / read by:** GitHub Actions; the README badge (L6) points at this workflow's status.
- **Key contents:** 57 lines. **Name:** `tests` (L1).
  - **TRIGGERS (L3-7):** `push` restricted to `branches: [main, milestone2-v3-professional-release]`; `pull_request` (unrestricted — all branches); `workflow_dispatch`.
  - **Jobs:** exactly **one**, `python` (L10), display name "**Python tests, contract, reconciliation, links**" (L11), **`runs-on: ubuntu-latest`** (L12). No matrix, no service containers, no caching, no concurrency group, no permissions block, no timeout.
  - **Steps (7 total):**
    1. `Check out repository` — `actions/checkout@v4` (L14-15).
    2. `Set up Python` — `actions/setup-python@v5` with **`python-version: "3.12"`** (L17-21).
    3. `Install package with test extras` (L22-25): `python -m pip install --upgrade pip` then `pip install -e .[test]` (**no lock/constraints**).
    4. `Run test suite with coverage gate` (L27-28): `python -m pytest tests/ -q --cov=fcf_m2 --cov-fail-under=80`.
    5. `Legacy baseline reproduction (25 starter / 48 pathway)` (L30-34): `python -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/ci_legacy`, then `grep -q '"starter_total": 25' data/outputs/ci_legacy/run_summary.json` and `grep -q '"pathway_total": 48' …`.
    6. `Validate tracked canonical contract (rules + schema + hash chain)` (L36-37): `python -m fcf_m2.workflow validate-contract data/contract/v1`.
    7. `Cross-model reconciliation (contract vs MATLAB canonical CSV)` (L39-50) — inline heredoc Python: reads `data/contract/v1/scenario_table.csv` and `matlab/data/canonical/matlab_scenarios.csv`; asserts `set(st.horizon_year) == set(m.horizon_year) == {2026, 2036, 2046, 2056}`; merges on `scenario_id` and asserts `len(mg) == len(st) == 120`; asserts `(mg.ports_active == mg.ports).all()`; asserts `mg.capacity_basis_y.notna().all()`; prints "cross-model OK".
    8. `Internal Markdown links` (L52-53): `python scripts/check_internal_links.py`.
    9. `Secret scan (pattern-based)` (L55-57): `! git grep -nIiE 'AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}' -- . ':!.github/workflows/tests.yml' ':!scripts/verify.sh'`.
    (Counting the two named blocks in step 5 as one step gives 9 named steps; 7 of them run commands.)
- **Notes:** The `{2026, 2036, 2046, 2056}` assertion at L45 is the **machine-enforced canonical horizon set** — this is the strongest in-repo definition of the horizon convention. The push trigger does not include `v4-platform`, so the current working branch gets CI only via pull requests or manual dispatch. `main` is included; `milestone2-v3-professional-release` still listed although it has been merged (PR #3, commit `7626823`). No MATLAB, no dashboard, no docs, no hygiene gates here.

---

### .github/workflows/matlab-manual.yml  *(not on my assigned list, but read in full for CI completeness)*
- **Role:** Manual-only MATLAB verification workflow (MATLAB unit tests + a headless batch smoke run).
- **Kind:** authored
- **Reads:** `matlab/src`, `matlab/tests`; writes `matlab/test-results/results.xml` and `matlab/outputs/`.
- **Key contents:** 54 lines. Header comment L1-7, verbatim in part: "**MANUAL TRIGGER ONLY:** MATLAB batch licensing in CI requires the `MLM_LICENSE_TOKEN` secret (see matlab-actions/setup-matlab docs). Until that secret is configured, MATLAB code in this repo is statically checked only — no execution is claimed anywhere (see `matlab/EXECUTION_STATUS.md`). The core pipeline needs base MATLAB only; Simulink is optional and not exercised by the tests." Name `matlab-manual` (L9); `on: workflow_dispatch` only (L11-12); job `test` on `ubuntu-latest` (L15-17); steps: checkout@v4; `matlab-actions/setup-matlab@v2` with `release: R2025b`, `products: MATLAB`, `env: MLM_LICENSE_TOKEN: ${{ secrets.MLM_LICENSE_TOKEN }}` (L22-28); `matlab-actions/run-tests@v2` with `source-folder: matlab/src`, `select-by-folder: matlab/tests`, `test-results-junit: matlab/test-results/results.xml` (L30-35); `matlab-actions/run-command@v2` running `cd matlab; addpath('src'); outDir = run_all_scenarios(); disp(outDir);` (L37-44); `actions/upload-artifact@v4` `if: always()` uploading `matlab/test-results/` and `matlab/outputs/` (L46-53).
- **Notes:** Secret name `MLM_LICENSE_TOKEN` is referenced but no secret value appears in the repo — clean. This is the file Phase 2 will most likely replace or supplement (the program ledger records GNU Octave 11.3.0 as the toolchain actually present). Note the workflow uploads `matlab/outputs/`, which `.gitignore:14` excludes from the repo — consistent.

---

## verify.sh vs tests.yml — GATE PARITY TABLE (assigned deliverable)

`scripts/verify.sh` was read in full (73 lines) for this comparison only; lane L02 owns its detailed inventory.
Harness shape: `set -u` (L5, note: **no `-e`**), `PY="${VENV_PY:-$REPO/venv/bin/python}"` (L7), a `gate()` helper that
runs each command, tees output to the fixed path `/tmp/fcf_verify_out.txt` (L13) and tails 6 lines on failure (L17);
results printed at the end and `exit $FAIL` (L70-73).

| # | Gate | `scripts/verify.sh` | `.github/workflows/tests.yml` | Converged? |
|---|---|---|---|---|
| 1 | pytest suite + **coverage floor 80** | L23-24 · `'$PY' -m pytest tests/ -q --cov=fcf_m2 --cov-fail-under=80` | L27-28 · identical command | **YES — identical** |
| 2 | legacy_v2 baseline reproduces 25 starter / 48 pathway | L26-27 · `--out data/outputs/verify_legacy`, then two `grep -q` on `run_summary.json` | L30-34 · `--out data/outputs/ci_legacy`, same two greps | **YES** (output dir differs only) |
| 3 | contract validation (rules + JSON Schema + RT-10 hash chain) | L29-30 · `validate-contract data/contract/v1` | L36-37 · identical | **YES** |
| 4 | cross-model reconciliation (contract ↔ MATLAB CSV) | L32-44 · heredoc; asserts horizon set `{2026,2036,2046,2056}`, 120-row merge on `scenario_id`, `ports_active == ports`, `capacity_basis_y.notna()` | L39-50 · byte-equivalent asserts | **YES** |
| 5 | docs: `docs/WORKFLOW_STEPS.md` step count == `len(workflow.STEPS)` | L46-47 · asserts the literal `Step count: **{n}**` appears in the doc | **ABSENT** | **NO — CI gap** |
| 6 | dashboard: exactly 9 `dashboard/static/0*.png` + every PNG footer-logged via `fcf_m2.visuals.audit_footer_metadata` | L49-54 | **ABSENT** | **NO — CI gap** |
| 7 | secret scan (AKIA / aws_secret_access_key / PRIVATE KEY / ghp_ / sk-) | L56-57 · excludes **only** `':!scripts/verify.sh'` | L55-57 · excludes `':!.github/workflows/tests.yml'` **and** `':!scripts/verify.sh'` | **NO — different exclude sets; verify.sh's version currently FAILS** |
| 8 | hygiene: no `/Users/andyyaro` in `*.py *.sh *.toml *.yml *.json` | L59-60 · excludes `':!scripts/verify.sh'` | **ABSENT** | **NO — CI gap; and this gate currently FAILS locally** |
| 9 | hygiene: no tracked file > 25 MB | L62-63 · `git ls-files -z \| xargs -0 -I{} find {} -size +25M` | **ABSENT** | **NO — CI gap** |
| 10 | markdown links | L65-66 · `lychee --offline` over `README.md docs reports presentation dashboard excel matlab src tests scripts data` **if installed**, else `scripts/check_internal_links.py` | L52-53 · always `scripts/check_internal_links.py` | **PARTIAL — verify.sh is machine-dependent/nondeterministic** |
| — | Python interpreter | `venv/bin/python` (whatever `make setup` built; lock header says 3.14.6 arm64) or `$VENV_PY` | pinned `3.12` on `ubuntu-latest` | **NO** |
| — | Dependency resolution | `pip install -e ".[test]" -c requirements-lock.txt` (`Makefile:6`) | `pip install -e .[test]` — **no constraints** | **NO** |
| — | MATLAB | none | separate `matlab-manual.yml`, `workflow_dispatch` only | n/a |

**Two `verify.sh` gates fail on the pristine committed tree** (verified by re-running the exact `git grep` expressions read-only):
- **Gate 7 (secrets)** — `git grep -nIiE '…|aws_secret_access_key|…' -- . ':!scripts/verify.sh'` matches `.github/workflows/tests.yml:57`, because CI's own pattern string contains the literal `aws_secret_access_key` and `verify.sh` does not exclude the workflow file the way the workflow excludes itself. `git grep` exits 0 (match found) → the `!` gate fails.
- **Gate 8 (local paths)** — `git grep -nI '/Users/andyyaro' -- '*.json' …` matches `dashboard/static/footer_log.json` at lines **7, 14, 21, 28, 35, 42, 49, 56, 59**, each of the form `"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/0N_*.png"`.
Consequence: `README.md:116-120`, `CONTRIBUTING.md:11`, `CHANGELOG.md:43` and `.github/pull_request_template.md:22` all assert that this harness passes / must pass. It does not, and CI is green anyway because CI omits gate 8 and self-excludes on gate 7. **This is the single clearest "claims something works that the repo elsewhere contradicts" defect in my lane.**

Note on the footer-log paths: `fcf_m2.visuals.audit_footer_metadata` (`src/fcf_m2/visuals.py:76`) keys on `Path(e["file"]).name`, i.e. basename only, so the stale absolute paths do **not** break gate 6 — they are pure leakage of the author's `~/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/` build directory, which is not this repo, evidence the dashboard was generated outside the tree.

---

## Cross-cutting checks run for this lane (read-only)

- **eGRID 590.2 sweep (repo-wide `git grep`):** 590.2 appears in exactly **4** tracked files, all as an explicit *correction record*, never as a live value — `CHANGELOG.md:24`, `docs/methodology/current-facts-source-register.md:7` ("research register EX10 carried ≈590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh"), `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22`, `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`. **No stale 590.2 survives as a used factor.** 596.3 appears in 27 files including all 120 rows of `data/contract/v1/scenario_table.csv` and of `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv`, and in `src/fcf_m2/config.py`.
- **Horizon-convention sweep of the root/CI files:** the only hits are `CHANGELOG.md:16-17` and `README.md:18`, both correctly labelled (see per-file notes). No `2035`, `2050`, or bare "Now" anywhere in `Makefile`, `pyproject.toml`, `requirements-lock.txt`, `.gitignore`, `tests.yml`, `matlab-manual.yml`, or `pull_request_template.md`. Repo-wide, all remaining `2035/2050` hits are inside explicitly legacy contexts (`src/fcf_m2/config.py` LEGACY_GROWTH_MULTIPLIERS, `src/fcf_m2/right_sizing.py`, `matlab/legacy_archive/*`, `docs/migration-from-v2.md`) — other lanes own the detail.
- **Contract `horizon_label` values are `now / plus10 / plus20 / plus30`** (`data/contract/v1/scenario_table.csv`). So the canonical contract itself still uses the token `now` for 2026, while `CHANGELOG.md:17` says the "mixed **Now**/2035/2050 conventions" were replaced. Defensible (2026 *is* the baseline) but worth a Phase-1 decision, since the instruction treats bare "Now" as suspect.
- **Secrets / credentials:** no AWS account IDs, access keys, tokens, or private keys found in any tracked file (CI's own scan pattern is the only self-match). The only secret *reference* is `${{ secrets.MLM_LICENSE_TOKEN }}` in `matlab-manual.yml:28`.
- **Generated artifacts committed:** `src/fcf_m2.egg-info/` (PKG-INFO, SOURCES.txt, requires.txt, top_level.txt, dependency_links.txt) is tracked. Contents currently **match** `pyproject.toml` (name `fcf-m2`, version `3.0.0`, identical Requires-Dist set), so no drift today — but it is a generated build artifact under version control with no ignore rule, and it regenerates on every `pip install -e`.
- **`docs/WORKFLOW_STEPS.md:3` says `Step count: **11**`** and `src/fcf_m2/workflow.py` `STEPS` has exactly 11 entries (`load_inputs`, `score_sites`, `right_sizing`, `confidence`, `peak_wait`, `economics`, `emissions`, `scenario_table`, `contract`, `matlab_adapter`, `summary`) — `verify.sh` gate 5 would pass. Recorded here because CI never checks it.
