# V4 Platform Program — LEDGER

**Single source of truth for program state.** Re-read this before doing anything else when resuming.
Nothing is `done` until it is `verified` — observed working, not assumed working.

- **Program start (UTC):** 2026-07-27T15:30:20Z
- **Working directory:** `~/Downloads/Future-City-Fellowship-MapUpdate/`
- **Repo clone:** `repo/` — remote `https://github.com/andyyaro/Future-City-Fellowship-` (private, stays private)
- **Integration branch:** `v4-platform` (not yet created — Phase 0.2)
- **Ledger created:** Phase 0, before any other work, per standing orders.

---

## STATUS BOARD

| Phase | Name | Gate status | Notes |
|---|---|---|---|
| 0 | Ground truth | **in-progress** | Ledger initialized. |
| 1 | Repair the base | not-started | |
| 2 | Liberate the MATLAB layer | not-started | Front-loaded; runs in background once started. |
| 3 | Integrate the 3D explorer | not-started | |
| 4 | Build V4 | not-started | |
| 5 | NFC field layer | not-started | |
| 6 | Close the Tableau blocker | not-started | |
| 7 | The platform | not-started | |
| 8 | Deploy and ship | not-started | |
| 9 | Make it human | not-started | |
| 10 | Verify and land | not-started | |

Legend: `not-started` / `in-progress` / `blocked` / `done` / `verified`

---

## TASKS

### Phase 0 — Ground Truth

| # | Task | State | Evidence / notes |
|---|---|---|---|
| 0.0 | Initialize `LEDGER.md` | **done** | This file. Committed in Phase 0. |
| 0.1 | Workspace verification (three trees present, no cruft) | **verified** | 198/198/31 files; zero cruft; zero files >25 MB. See below. |
| 0.1b | Build Python 3.12 venv matching CI | **verified** | `repo/venv` on CPython **3.12.6**. Built with `python3.12 -m venv` (not `uv venv` — that omits `pip`, which the Makefile's `setup` target requires). `make test`: **80 passed, 92% coverage**. |
| 0.2 | Safety tag `pre-v4-program-20260727` pushed; branch `v4-platform` created | **verified** | Tag pushed to origin; branch created off `7626823`. |
| 0.3 | Read every line of every file in all three trees | in-progress | 12-lane fleet running (`wf_0ac58ed8-c08`). `buildSimulinkModel.m`, `runScenario.m`, `loadScenarios.m` also read directly by the lead. |
| 0.3b | `INVENTORY.md` written | not-started | Blocked on 0.3. |
| 0.3c | `INVENTORY.md` independently verified by a separate agent | not-started | Coverage verifier is stage 2 of the same workflow. |
| 0.4 | Three-tree reconciliation, file by file | **verified** | **Snapshot ≡ `origin/main`, byte-identical, 198/198.** See RECON-1. |
| 0.4b | `RECONCILIATION.md` written | not-started | Tree 3 (`fcf-3d`) analysis pending lanes L10/L11. |
| 0.5 | AWS read-only discovery (both profiles) | **verified** | Both identities matched expected accounts. Nothing created, modified, or deleted. |
| 0.5b | Website end-to-end mapping (domain → CF → S3 → objects) | **verified** | Full chain mapped; all 16 served objects listed. |
| 0.5c | Read `docs/operations/website-patch-package/` in full | **verified** | README + PATCH_GUIDE + DEPLOYMENT_RUNBOOK read directly; `content/` covered by lane L07. |
| 0.5d | `AWS_INVENTORY.md` written | **done** | Committed `31b1628`. |
| G0 | **Gate 0** | in-progress | Awaiting INVENTORY.md + RECONCILIATION.md + independent verification. |

---

## OBSERVED WORKSPACE FACTS (Phase 0.1, first pass)

Recorded 2026-07-27T15:30Z. Every line here was observed by command, not assumed.

| Fact | Observed value | Masterprompt expectation | Delta |
|---|---|---|---|
| `repo/` tracked files | 198 | "~180 tracked" | Repo has **198** tracked files, not ~180. Prompt's figure was approximate. |
| `incoming/snapshot/Future-City-Fellowship--main-2/` files | 198 | "198 files" | Matches. |
| `incoming/explorer/fcf-3d/` files | 31 | "36 files" | **Delta: 31 vs 36.** Needs explanation before Phase 3. Logged as OPEN-1. |
| `repo/` git status | clean, on `main`, up to date with `origin/main` | fresh clone of origin/main | Matches. |
| `origin/main` HEAD | `7626823` — "Merge pull request #3 from andyyaro/milestone2-v3-professional-release" | — | Recorded as the pre-program baseline SHA. |
| Existing remote branches | `main`, `archive/pre-milestone2-v3-20260719`, `milestone2-v3-professional-release`, `v2-expansion-planning` | — | Never delete any of these. |
| Existing tags | `pre-milestone2-v3-20260719`, `v1-demo-scalability-ready`, `v1-review-ready` | — | Never delete any of these. |

### Toolchain present on this machine (pre-existing, not installed by this program)

| Tool | Version | Path |
|---|---|---|
| python3 (default) | 3.14.6 | `/opt/homebrew/bin/python3` |
| python3.12 | present | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12` |
| uv | 0.11.29 | `/opt/homebrew/bin/uv` |
| node | v25.8.2 | `/opt/homebrew/bin/node` |
| npm | present | `/opt/homebrew/bin/npm` |
| gh | 2.95.0 | `/opt/homebrew/bin/gh` |
| **GNU Octave** | **11.3.0** | `/opt/homebrew/bin/octave` |
| brew | present | `/opt/homebrew/bin/brew` |
| git | present | `/usr/bin/git` |

> **Note for Phase 2:** installed Octave is **11.3.0**, not the 9.x the masterprompt's labeling example assumed
> (`GNU Octave 9.x`). Engine labels must carry the **actual** version observed at run time, so the label will read
> `GNU Octave 11.3.0` unless a different version is deliberately pinned. Logged as DEC candidate.

### Installs performed by this program

*(Clean-clone honesty depends on this table being complete. Append every install.)*

| Date (UTC) | Tool / package | Version | Why | Required for a fresh machine? |
|---|---|---|---|---|
| — | *(none yet)* | | | |

---

## DECISIONS

*Every judgment call, the alternatives rejected, and why. Mirrored into `DECISIONS.md` at landing.*

| # | Decision | Alternatives rejected | Reasoning | Phase |
|---|---|---|---|---|
| DEC-001 | Create `LEDGER.md` at `docs/operations/v4-program/LEDGER.md` inside the **repo clone** (tracked), not in the workspace parent. | (a) Untracked scratch file — rejected: masterprompt names the tracked path explicitly and requires frequent commits. (b) Workspace root — rejected: same reason, and it would not survive a clean clone. | The masterprompt specifies the path and requires it be committed often; it is a program deliverable. | 0 |

---

## OPEN QUESTIONS

| # | Question | Status | Resolution |
|---|---|---|---|
| OPEN-1 | `incoming/explorer/fcf-3d/` contains **31** files; masterprompt says 36. Which is right, and is anything missing? | **likely benign** | Full enumeration shows a coherent tree: 5 Python modules, `blender/build_assets.py`, `tests/test_pipeline.py`, `Makefile`, `README.md`, `CLAUDE.md`, `requirements.txt`, `.gitignore`, 4 web files, 4 `web/data/` files, **all 12 GLBs** (`FFX001-004`, `PWC001-008`). Nothing is obviously absent. The 5-file gap is consistent with the stripped `__pycache__` and macOS cruft noted in the masterprompt's own workspace-prep note. Lanes L10/L11 confirm against the tree's own manifest before this closes. |
| OPEN-2 | The repo has **198** tracked files, not the "~180" the masterprompt estimated. | **resolved — no action** | The masterprompt's figure was explicitly approximate ("~180"); the snapshot figure it gave (198) is exact and matches. No file is missing. |
| OPEN-3 | Does the Octave Packages `datatypes` package supply a `table`/`string`/`datetime` good enough to raise the Phase 2 runtime tier? | open | Evaluate in Phase 2 **before** fixing the tier. Record any install in the installs table. |

---

## FINDINGS NOT YET ACTED ON

*Leads from subagents and scans. Every one is a lead, not a fact, until independently confirmed against the actual files.*

### Reconciliation result (Phase 0.4, trees 1 and 2)

**RECON-1 — the snapshot and `origin/main` are byte-identical.** Confirmed twice, by independent methods:
`cmp` over every tracked file (198 identical, 0 differing) and a SHA-256 set comparison (`diff` of the sorted
hash lists is empty). The file-*name* sets are also identical. **There is no divergence to adjudicate between
trees 1 and 2** — the reconciliation the masterprompt anticipated as a file-by-file arbitration turns out to
be a null result, which is the best possible outcome and must be recorded as evidence rather than assumed.

Tree 3 (`fcf-3d`, never in the repo) remains to be reconciled; that is Phase 3's substance, not a diff.

### Live-surface findings (Phase 0.5) — full detail in `AWS_INVENTORY.md`

| # | Sev | Finding | Confirmed? | Acted on? |
|---|---|---|---|---|
| FIND-AWS-01 | high | The live assistant Lambda reads the repo at `GITHUB_BRANCH=v2-expansion-planning`. That branch holds 220 files and **zero** under `data/contract/v1/`. The public assistant is grounded on the pre-V3 tree and cannot cite the canonical contract. | **yes** — env var read from the function config; branch contents counted via `git ls-tree` on the real remote | Phase 8 |
| FIND-AWS-02 | high | The website patch package was **never applied**. Confirmed against the live site, not from the package's own claim: `privacy.html` and `standards.html` both **403**; no `2036`/`2046`/`2056`; no `0 of 12`; no `VCDPA`/`UL 2594`/`UL 3600`; the 9 static dashboard PNGs are referenced nowhere. | **yes** | Phase 8 |
| FIND-AWS-03 | high | The live site carries **no horizon convention at all** — `2036`/`2046`/`2056` and `2035`/`2050` all appear zero times across five pages and the served PDF. Neither `596.3` nor `590.2` appears anywhere live. `58.8` appears twice and FFX002 is correctly the top candidate. | **yes** | Phase 1 audit / Phase 8 |
| FIND-AWS-04 | med | `/aws/lambda/future-city-assistant-chat` has **no log retention** (never expires). | **yes** | Phase 8 |
| FIND-AWS-05 | high | `index.html` is a 1,270-byte iframe shell around `https://zany-storm-638468.framer.app/`. **The public landing page's content is not in this AWS account or this repo** and cannot be corrected by an S3 sync. | **yes** | Phase 8 |
| FIND-AWS-06 | med | **No AWS Budgets exist** in the account. | **yes** | Phase 8 |
| FIND-AWS-07 | low | **No project resource is tagged** (S3 bucket has no tag set; project distribution has no `Project` tag). | **yes** | Phase 8 |
| FIND-AWS-08 | low | Six byte-identical 1.3 MB PNGs (one shared ETag) = 7.8 MB of 8.2 MB origin data and most of 323 MB/month transfer. | **yes** | Phase 8 |
| FIND-AWS-09 | info | Project distribution has **no custom error responses**; client-routed paths and NFC short links will 403, exactly as `/privacy.html` does today. | **yes** | Phase 8 |

### Repository findings (observed while running the gates — Phase 1 work items)

| # | Sev | Finding | Confirmed? | Acted on? |
|---|---|---|---|---|
| FIND-REPO-01 | high | **`scripts/verify.sh` FAILS on a clean checkout — 8 PASS / 2 FAIL, true exit code 2.** The repo does not currently pass its own verification harness. | **yes** — run directly, exit code captured without a pipe | Phase 1 |
| FIND-REPO-02 | high | **Secret-scan gate diverges between CI and `verify.sh`.** `tests.yml` excludes `':!.github/workflows/tests.yml' ':!scripts/verify.sh'`; `verify.sh` excludes only `':!scripts/verify.sh'`. The regex literal lives in `tests.yml:57`, so the gate self-matches locally and passes in CI. A gate that passes in CI and fails locally is worse than either. | **yes** | Phase 1 |
| FIND-REPO-03 | high | **`dashboard/static/footer_log.json` contains six absolute authoring-machine paths** (`/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/…`). Root cause is the **generator**, not the artifact: `visuals.py:62` does `entry["file"] = str(path)` and `build_static_dashboard.py:18` resolves `REPO` absolutely. Fix the generator and regenerate — never hand-edit a generated artifact. `audit_footer_metadata` only reads `Path(e["file"]).name`, so a repo-relative path is compatible. | **yes** | Phase 1 |
| FIND-REPO-04 | high | **CI runs only 6 of the 10 gates `verify.sh` runs.** Missing from `tests.yml`: generated-workflow-steps drift, dashboard static-asset + footer-log audit, absolute-path hygiene, and the >25 MB file check. | **yes** — gate lists compared line by line | Phase 1 |
| FIND-REPO-05 | med | **Dependency incoherence.** `requirements-lock.txt` header says it was generated from **Python 3.14.6**, CI pins **3.12**, `pyproject.toml` declares **>=3.11**, and CI installs `pip install -e .[test]` with **no `-c requirements-lock.txt`** while the Makefile uses the constraint. CI therefore does not test the locked set. | **yes** | Phase 1 |
| FIND-REPO-06 | med | **CI trigger references a merged feature branch.** `tests.yml` has `on: push: branches: [main, milestone2-v3-professional-release]`. Pushes to `v4-platform` will not trigger CI on push (only via `pull_request`). | **yes** | Phase 1 |
| FIND-REPO-07 | info | Legacy right-sizing output is named `right_sizing_legacy_2035_2050.csv`. This is a **correctly labelled legacy-mode** artifact, not stale text — the horizon audit must not flag it. | **yes** | none needed |

### Octave capability probe (Phase 2 research, run early — evidence for the tier decision)

Run against the **actually installed** `GNU Octave 11.3.0` (Homebrew, aarch64), stock with **no packages installed**.

**ABSENT:** `table`, `readtable`, `detectImportOptions`, `setvartype`, `renamevars`, `string`, `strings`,
`datetime`, `timeseries`, `ismissing`, `struct2table`, `array2table`, `categorical`, `varfun`, `rowfun`.

**PRESENT:** `inputParser`, `containers.Map`, `height`, `width`, `assignin`, `validateattributes`, `isfile`,
`isfolder`, `textscan`, `dlmread`, `strsplit`, `strjoin`, `intersect`, `regexprep`.

**Behavioural:** a double-quoted literal `"abc"` evaluates to class **`char`** in Octave and to class
**`string`** in MATLAB. This is a silent-divergence risk everywhere the sources compare or concatenate
string scalars, which they do constantly.

**FIND-MATLAB-01 (high) — Tier 1 is unreachable, with evidence.** `loadScenarios.m` is the entry point of the
whole pipeline (`run_all_scenarios` → `loadScenarios` → `runScenario`) and is table-centric throughout:
`detectImportOptions` (l.59), `setvartype` (l.68), `readtable` (l.71), `renamevars` (l.75),
`T.Properties.VariableNames` (l.74/89), `height(T)` (l.135), `T(keep,:)` (l.150), and
`T.Properties.Description`/`.UserData` (l.160-166). Every one of those is absent from stock Octave 11.3.0.
Unmodified `.m` sources cannot run.

**Tier 2 looks genuinely reachable, and the reason is architectural:** `runScenario.m` consumes a
`scenarioRow` **struct**, not a table — it uses `s.scenario_id` and `isfield(s, …)` (l.127-132, l.178-185).
The table type is therefore confined to the loading boundary. A shim that reimplements `loadScenarios`
to return a struct array should let the rest of the pipeline run on real `.m` sources. To be proven in
Phase 2, not assumed.

**Lead not yet chased:** Octave's own error text points at an Octave Packages `datatypes` package providing
`string`, `datetime`, and `table`. If it is real and sufficient, it could shrink or remove the shim. Must be
evaluated in Phase 2 before the tier is fixed — and any install recorded in the installs table above.

### Simulink topology (extracted directly from `buildSimulinkModel.m` — feeds Phases 2.5 and 7.2)

The file *constructs* the model in source; there is no `.slx` to parse. Topology is fully knowable and was
read first-hand: **11 blocks** — `Base Load`, `EV Request`, `Capacity Limit` (From Workspace);
`Total Unmanaged`, `Total Managed` (Sum, `++`); `Managed Logic Inputs` (Mux, 3), `Main Scope Signals`
(Mux, 4); `Managed EV Power` (MATLAB Function); `Live Scope: Load Behavior` (Scope);
`toWorkspace_unmanaged`, `toWorkspace_managed` (To Workspace) — and **15 connections** (l.217-232), with
positions and parameters given inline. Model settings: `StopTime` 86400 s, solver `ode3`, fixed step
`dt_sec`.

The docstring states the scope limit in its own words (l.10-16): *"this layer is ILLUSTRATIVE, not
load-bearing. Every metric in this repository … is computed by the plain MATLAB pipeline … which runs in
base MATLAB without Simulink. The Simulink model exists only to visualize signal flow."* The embedded
MATLAB Function block is explicitly an *"Illustrative clamp only — see managedCharging.m for the
authoritative strategies"* (l.187-188). The native view must carry both statements.

### Other findings not yet acted on

| # | Finding | Source | Confirmed? | Acted on? |
|---|---|---|---|---|
| — | *(lane findings land here as the fleet reports)* | | | |

---

## POINTERS TO DETAILED DOCUMENTS

| Document | Path | State |
|---|---|---|
| Ledger | `docs/operations/v4-program/LEDGER.md` | this file |
| Inventory | `docs/operations/v4-program/INVENTORY.md` | not yet written |
| Reconciliation | `docs/operations/v4-program/RECONCILIATION.md` | not yet written |
| Decisions | `docs/operations/v4-program/DECISIONS.md` | not yet written |
| MATLAB liberation | `docs/operations/v4-program/MATLAB_LIBERATION.md` | not yet written |
| AWS inventory | `docs/operations/v4-program/AWS_INVENTORY.md` | not yet written |
| Deployment | `docs/operations/v4-program/DEPLOYMENT.md` | not yet written |
| Verification | `docs/operations/v4-program/VERIFICATION.md` | not yet written |
| Residual risks | `docs/operations/v4-program/RESIDUAL_RISKS.md` | not yet written |

---

## RUNNING LOG

| UTC | Event |
|---|---|
| 2026-07-27T15:30:20Z | Program started. Masterprompt read in full. Ledger initialized before any other work. Baseline `origin/main` = `7626823`, working tree clean. |
| 2026-07-27T15:32Z | Safety tag `pre-v4-program-20260727` created and pushed. Branch `v4-platform` created. Ledger committed (`95e91e0`). |
| 2026-07-27T15:35Z | Phase 0.4 (trees 1-2) closed: snapshot proven byte-identical to `origin/main`, 198/198, by two independent methods. Cruft scan clean; no file >25 MB. |
| 2026-07-27T15:38Z | Phase 0.3 read fleet launched — 12 non-overlapping lanes + an independent coverage verifier (`wf_0ac58ed8-c08`). |
| 2026-07-27T15:40Z | Python 3.12.6 venv built at `repo/venv`. `make test`: 80 passed, 92% coverage. |
| 2026-07-27T15:42Z | Phase 0.5 AWS read-only discovery complete, both identities verified. Nine findings recorded. `AWS_INVENTORY.md` committed (`31b1628`). |
| 2026-07-27T15:44Z | Gate suite run for diagnosis: `run-legacy` = 25/48 exact; `run-v3` = 120 rows, 0 High confidence, 12/12 placeholder; `validate` PASS incl. RT-10 hash chain; **`verify.sh` 8 PASS / 2 FAIL (exit 2)**. Seven repository findings recorded. |
| 2026-07-27T15:47Z | `buildSimulinkModel.m`, `runScenario.m`, `loadScenarios.m` read line by line by the lead. Simulink topology extracted (11 blocks, 15 connections). |
| 2026-07-27T15:49Z | Octave 11.3.0 probed empirically. Tier 1 ruled out with evidence; Tier 2 identified as reachable because the table type is confined to the loading boundary. |
