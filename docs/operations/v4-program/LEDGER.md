# V4 Platform Program — LEDGER

**Single source of truth for program state.** Re-read this before doing anything else when resuming.
Nothing is `done` until it is `verified` — observed working, not assumed working.

- **Program start (UTC):** 2026-07-27T15:30:20Z
- **Working directory:** `~/Downloads/Future-City-Fellowship-MapUpdate/`
- **Repo clone:** `repo/` — remote `https://github.com/andyyaro/Future-City-Fellowship-` (private, stays private)
- **Integration branch:** `v4-platform` — created off `7626823`; safety tag `pre-v4-program-20260727` pushed
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

#### Horizon references confirmed **legitimate** (the audit must not "fix" these)

The program treats surviving `2035` / `2050` / "10/20/30-year" as defects *unless correctly labelled legacy*.
These were checked individually and are correct as they stand:

| Location | Text | Why it is fine |
|---|---|---|
| `README.md:18` | "10/20/30-year horizons (2036 / 2046 / 2056 from a 2026 baseline)" | the shorthand is expanded to the canonical years in the same breath |
| `README.md:68` | "`legacy_v2` … golden-tested: FFX002 58.8; 25 starter / 48 pathway" | explicitly scoped to the legacy mode |
| `workflow.STEPS[3]` → `docs/WORKFLOW_STEPS.md` | "Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056)" | names both conventions and attributes each to its mode |
| `data/outputs/**/right_sizing_legacy_2035_2050.csv` | filename | a legacy-mode output, correctly named |
| `contract_manifest.json` | `baseline_year: 2026`, `horizons: [2036, 2046, 2056]` | the canonical four = baseline + three horizons; consistent, not a truncation |

By contrast, the 3D explorer's `ports_2035` / `ports_2050` field names (FIND-3D-01) are **not** labelled by mode
and sit beside V3 `horizon_year` values in the same payload. That is the real horizon defect.

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
Unmodified `.m` sources cannot run. **Tier 1 is ruled out.**

**FIND-MATLAB-02 (high) — the `string` type is the real blocker, not `table`.** In Octave a double-quoted
literal is `char`, so `+` is *numeric addition*, not concatenation. Verified directly:
`"abc " + "def"` → `error: operator +: nonconformant arguments (op1 is 1x4, op2 is 1x3)`.

This is not confined to error paths. `capacityGuard.m:111-112` builds `capacityDef` with `+` on a **normal**
execution path, and comparisons like `profiles.mode == "legacy_gaussian"` (`managedCharging.m:121`) compare
strings of *different lengths*, which under `char` is an error rather than `false`. A Tier-2 shim therefore
needs a genuine `string` class with overloaded `plus`, `eq`, and `strlength` — not merely function stubs.
This is the single largest piece of shim work and it must be settled before the tier is fixed.

**FIND-MATLAB-03 (medium, and it *helps*) — `table` is used only as a struct-of-arrays.** Corrects an
earlier reading that put `table` solely at the loading boundary: `makeSessionProfiles.m` also builds the
`sessions` table on the normal path (l.154-161, l.295-302). But every downstream operation on it is
struct-of-arrays shaped — `sessions.max_power_kW(k)`, `sessions.arrival_hr <= tNow`, `height(sessions)`, and
column *addition* by plain assignment (`managedCharging.m:294-299`, `perVehicle.requested_kWh = …`). All of
those work unchanged on an Octave struct with vector fields. No `varfun`, `rowfun`, `join`, or
`T.Properties` access occurs downstream. So the `table` shim can be small: a `table(...)` constructor
honouring `'VariableNames'`, `height`, `istable`, `table2struct`, `struct2table`, `writetable`.

**FIND-MATLAB-04 (medium) — `run_all_scenarios.m` hashes via Java, which this Octave cannot do.**
`localSha256` (l.186-198) uses `java.security.MessageDigest`. Probed directly: `usejava("jvm")` returns
**0** on this install (built with the Java feature, but no JRE resolves at runtime). The shim needs a
pure-Octave SHA-256 or a `shasum` shell-out. Also `version("-release")` (l.128) returns Octave's own
version, so the manifest's `matlab_release:` line would silently record an Octave string in a field whose
name claims MATLAB — exactly the engine conflation the program forbids. Must be handled explicitly.

**FIND-MATLAB-05 (low) — `plotScenario.m` is the least portable file and the least load-bearing.** It needs
`tiledlayout`, `nexttile`, `subtitle`, `xticks`, `xtickangle`, `categorical`, `reordercats`,
`exportgraphics`, `strlength`, and `datetime`. Figures are presentation artifacts, not numbers, so this file
can be excluded from the Octave runtime path and left to the harness CI's real MATLAB, which is where the
committed figures should come from anyway.

**Working conclusion (to be proven in Phase 2, not assumed):** Tier 2 — Octave plus a thin, tested
compatibility shim — is the realistic target, and the shim's centre of gravity is a `string` class, not
table emulation. `capacityGuard.m` and `makeSessionProfiles.m` both already accept *either* a one-row table
*or* a struct (`localRowToStruct`), which is a deliberate seam the shim can use.

**Lead not yet chased:** Octave's own error text points at an Octave Packages `datatypes` package providing
`string`, `datetime`, and `table`. If it is real and sufficient, it could shrink or remove the shim. Must be
evaluated in Phase 2 before the tier is fixed — and any install recorded in the installs table above.

> **Coverage note.** All **9** files in `matlab/src/` have now been read line by line by the lead, not
> skimmed and not delegated: `buildSimulinkModel.m`, `runScenario.m`, `loadScenarios.m`, `capacityGuard.m`,
> `makeSessionProfiles.m`, `managedCharging.m`, `electricalEconomics.m`, `run_all_scenarios.m`,
> `plotScenario.m`. Lane L03 covers the same files independently; its findings are cross-checked against
> this reading rather than substituted for it. The 6 `matlab/tests/*.m` files and the 2 `legacy_archive`
> `.m` files are lane L04's, and still owed a lead read before Gate 2.

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

### 3D explorer findings (Phase 3 — verified first-hand by the lead, ahead of lane L10)

**FIND-3D-01 (high) — the governing finding holds, and it is a *hybrid*, which is worse than described.**
`fcf3d/build_sites.py` `SOURCES` (l.47-55) reads **both** conventions at once:

- scoring detail ← `tests/fixture_legacy_v2_site_results.csv` (**legacy_v2**)
- ports trajectory ← `tests/fixture_legacy_v2_right_sizing.csv` (**legacy_v2**)
- electrical risk ← `data/inputs/legacy_v2_electrical_risk_summary_frozen_*.csv` (**legacy_v2**)
- per-horizon scenarios ← `data/contract/v1/scenario_table.csv` (**milestone2_v3**)
- plus three `dashboard/tableau/patch_package/` CSVs and `data/provenance/site_coordinate_sources.csv`

and emits `ports_2035` / `ports_2050` (l.436-437) plus `ports_2035_base|high` / `ports_2050_base|high`
(l.463-466), while `build_scenarios` (l.278-302) simultaneously emits V3 `horizon_year` values from the
contract. A single feature therefore carries **both** horizon conventions side by side. The brief anticipated
"superseded numbers under a V3 repository"; the reality is superseded *and* canonical numbers in the same
payload, which is harder for a reader to detect.

**FIND-3D-02 (high) — 15 of 46 explorer tests silently skip on any machine but the original author's.**
`tests/test_pipeline.py` sets `REPO = os.environ.get("FCF_REPO", os.path.expanduser("~/fcf/Future-City-Fellowship--main-2"))`
and gates 16 tests on `needs_repo = pytest.mark.skipif(not os.path.isdir(REPO), …)`. That path does not
exist here. Observed directly:

- without `FCF_REPO`: **31 passed, 15 skipped**
- with `FCF_REPO` pointing at the real repo: **46 passed**

The skipped set **includes `test_attribution_reproduces_model_score`** — the one test whose stated purpose is
to stop "the map quietly telling planners a wrong story." A guard that defaults to not running is not a
guard. Phase 3 fixes this by resolving the path from the integrated repo root, so no environment variable is
needed.

**FIND-3D-03 (info, and it is good news) — the mirrored weights are currently correct.** Re-derived line by
line against `src/fcf_m2/scoring.py:140-175`. All four subscore weights (0.45 / 0.30 / 0.15 / 0.10) and all
19 driver weights match exactly, each subscore's drivers summing to 1.00. The `invert` flags match the six
terms the model wraps in `(1 - x)`. The one apparent mismatch — the explorer's `hours_open_n` against the
model's inline `df["hours_open"].clip(0,24)/24` — is **deliberately** reconciled in
`build_sites.py::prepare()` (l.318-323), which recreates the column with a comment saying exactly that.
No drift exists today.

**FIND-3D-04 (medium) — but there is nothing to drift-gate *against*.** The model holds these weights as
**inline numeric literals inside the formula** (`scoring.py:171-174` and the subscore blocks); there is no
`SUBSCORE_WEIGHTS` or `DRIVERS` constant in `fcf_m2.scoring` to import. The explorer's own
`test_subscore_weights_sum_to_one` only checks its *own* dict sums to 1.0 — it never compares against the
model. So today's agreement is a coincidence maintained by hand. Phase 3 should extract named constants in
`scoring.py`, use them in the formula (changing no numbers), and have the explorer import them, turning a
hand-maintained match into an enforced one.

### Numeric-consistency findings (Phase 1 — traced by the lead against the contract)

Method: recompute each headline number from `data/contract/v1/` and the fresh run outputs, then compare
against every document that states it. Confirmations matter as much as defects, so both are recorded.

**Verified as tracing exactly to the contract** (no action needed):

| Claim | Documents | Contract value | Result |
|---|---|---|---|
| Portfolio NPC, staged | README, Final Report, patch package | 2036 `$1,560,499` · 2046 `$2,294,469` · 2056 `$3,014,200` | **matches** $1.56M / $2.29M / $3.01M |
| Portfolio NPC, broad buildout | same | 2036 `$1,872,578` · 2046 `$2,635,638` · 2056 `$3,407,606` | **matches** $1.87M / $2.64M / $3.41M |
| Staged avoids | same | `$312,079` · `$341,169` · `$393,406` | **matches** $0.31M / $0.34M / $0.39M |
| Net CO2e avoided | same | 2026 `43.4` t · 2036 `82.4→112.7` · 2046 `130.1→195.1` · 2056 `173.4→260.2` | **matches** ≈43 / ≈82–113 / ≈130–195 / ≈173–260 t/yr |
| eGRID factor | README, footer log, contract | `596.3 lb CO2e/MWh`, `eGRID2023r2, accessed 2026-07-19` | **matches**; `590.2` found **nowhere** in the repo or on the live site |
| Legacy golden | README, tests | `25` starter / `48` pathway; FFX002 `58.8` | **matches**, and `README.md:68` labels it correctly as `legacy_v2` |
| Contract shape | — | 120 rows, horizons `{2026, 2036, 2046, 2056}`, 12 site IDs `FFX001-004`+`PWC001-008` | **matches** |
| RT-10 hash chain | `contract_manifest.json` | every SHA-256 recomputed by the lead: **5 inputs + 6 tables = 11/11 PASS, 0 FAIL** | **verified independently**, not just via `make validate` |
| Generated-doc drift | `docs/WORKFLOW_STEPS.md` | regenerated with `make docs`; `diff` is empty; step count gate `Step count: **11**` matches `len(workflow.STEPS) == 11` | **no drift** |
| Capacity placeholder | README limitation #1 | `capacity_basis = placeholder` on **120/120** rows | **matches** 12/12 sites |
| 0 of 12 High confidence | README | `data_confidence` = `Low` on **120/120**; `data_confidence_level_v3` = `Low` for all 12 (score `33.8`) | **true, and understated** — 0 of 12 reach even *Medium*; all 12 are Low |

**FIND-NUM-01 (high) — the active-port counts do not trace to the contract, in four documents.**
Every other column in the same tables does.

| Horizon | Documents claim (base → high) | Contract actually says | |
|---|---|---|---|
| 2026 | 25 | 25 | ok |
| 2036 | **44 → 47** | **35 → 44** | **wrong** |
| 2046 | **47 → 48** | **44 → 48** | **wrong** |
| 2056 | **47 → 48** | **44 → 48** | **wrong** |

The value **47 does not occur anywhere** in the contract as a portfolio total — the only portfolio totals
are `{25, 35, 44, 48}`, and site-level `ports_active` only ever takes `{2, 3, 4, 6, 8}`.

What makes this diagnosable rather than ambiguous: the **CO2e cell in the same table row** is also labelled
"base → high" and *does* match base→high exactly (2036 → 82.4/112.7 t). So the row is unambiguously meant to
be base→high, and the ports cell in that row disagrees with its own row. The most consistent explanation is
that port counts were revised at some point and the cost and emissions columns were regenerated while the
ports column was not.

Affected, all carrying the same wrong figures:
1. `README.md:39-41`
2. `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:38-40`
3. `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md:74` — *"active ports 25 → 44 → 47 → 47 on the base path; 25 → 47 → 48 → 48 on the high path"*
4. `docs/operations/website-patch-package/content/results_2036_2046_2056.md:7-12` — which asserts *"All values from canonical contract v1.0.0"* directly above the wrong table

Plus the `.docx` / `.pdf` / `.pptx` renderings derived from (2) and (3), to be confirmed by lane L12.
Consequence worth stating plainly: item (4) is the file that would have **published** these numbers to the
public website. That the patch package was never applied (FIND-AWS-02) accidentally prevented it.

Also flagged for the Phase 1 detailed trace, not yet resolved: the same patch-package file claims the staged
plan *"avoids energizing 13–23 pathway ports"*. Against the contract, `48 − ports_active` gives
`13 / 4 / 4 / 0 / 4 / 0` across the base and high paths — `13` appears, `23` does not.

**FIND-NUM-02 (high) — README's headline site claim is untraceable and self-contradicting.**
`README.md:45-46`, under the heading *"Headline results (canonical contract v1.0.0, screening values)"*:

> Top-ranked site: **FFX002 — City of Fairfax Regional Library (58.8, Medium confidence)**.

Three problems in one sentence, under a heading that claims canonical provenance:

1. **`58.8` is the `legacy_v2` score.** The canonical `milestone2_v3` score for FFX002 is **51.8**.
2. **FFX002 is not the top-ranked site under the canonical mode.** V3 ranks **FFX004 first at 53.4**;
   FFX002 is second. FFX002 is top-ranked only in `legacy_v2`.
3. **"Medium confidence" traces to nothing.** `data_confidence_level_v3` is `Low` for all 12 sites,
   `data_confidence` is `Low` on all 120 contract rows, and `capacity_confidence` is `none` on all 120.
   No output in the repository produces "Medium" for FFX002. It also **contradicts the limitation box 15
   lines above it** in the same README, which says 0 of 12 sites have High data confidence — the true
   position is weaker still.

This is the honesty-critical case the program's standing orders name: a caveat quietly upgraded into a
better-evidenced-sounding claim. `README.md:68` shows the project's own correct idiom — it labels the same
58.8 explicitly as the `legacy_v2` golden — so the fix is to apply that discipline at line 45.

**FIND-NUM-03 (medium) — the live site publishes the legacy top-ranked site as the current headline.**
`results.html` states *"Top overall candidate FFX002 · City of Fairfax Regional Library"*. That matches
`legacy_v2`, not the canonical V3 ranking (FFX004). Compounds FIND-AWS-01/02/03. Phase 8.

**FIND-REPO-08 (medium) — README overstates CI.** `README.md:119-120` says *"CI runs the same gates on
every push and pull request."* Neither half holds: CI runs 6 of `verify.sh`'s 10 gates (FIND-REPO-04), and
`on: push` is restricted to `main` and `milestone2-v3-professional-release` (FIND-REPO-06). Phase 1 should
make the statement true by converging the gates, rather than weakening the sentence.

### `EXECUTION_STATUS.md` provenance claims — checked, because Phase 2 depends on this file

The document's core claim is **confirmed and must be preserved**: no MATLAB has executed, `outputs/` is empty
by design, `tests/golden/regression_golden.csv` does not exist, and `.github/workflows/matlab-manual.yml`
has never run. Verified against the tree. Nothing here may be updated until a genuine run happens.

Its "static checks performed" section makes two *verifiable* provenance claims. Both were checked.

**FIND-MATLAB-06 (medium) — `matlab_scenarios.csv` cannot be byte-identical across runs, so the claim as
worded can never hold again.** Item 7 says the tracked `matlab/data/canonical/matlab_scenarios.csv` is
"byte-identical" to the producer output at `data/outputs/v3_run/matlab_scenarios.csv`. Regenerated it with
`make run-v3` and compared:

- headers identical; shapes identical (120 × 22); **21 of 22 columns bit-identical across all 120 rows**
- the only difference is `source_note`, which embeds the producing run id:
  tracked `…run milestone2_v3_20260719T052322Z…` vs fresh `…run milestone2_v3_20260727T154305Z…`

So the *data* claim is true and the *byte* claim is not, and cannot be — the artifact stamps a timestamp
into every row. This is the same trap the program flags for the Tableau `.twbx` in Phase 6: **a drift gate
on this file would fail on every run for no real reason.** Phase 1/3 must either compare modulo `run_id` or
move the run id to a sidecar manifest. Recording it now so nobody later "fixes" a spurious red gate by
weakening the comparison.

**FIND-MATLAB-07 (medium) — the legacy-archive provenance claim is unverifiable as written.** The same item
says both `matlab/legacy_archive/*.m` files are "byte-identical to the original legacy scripts (preserved in
the pre-V3 archive branch `archive/pre-milestone2-v3-20260719`)". That branch holds 100 files and **zero
`.m` files** — `git ls-tree` finds neither `untitled.m` nor
`build_and_run_site_grid_behavior_model.m` on it. Searched every remote ref: the two files exist only on
`main` and `milestone2-v3-professional-release`.

The claim is not necessarily *false* — the originals may simply have come from the author's machine rather
than that branch — but it names a source that cannot corroborate it. Phase 2 should correct the citation to
whatever can actually be checked, or state plainly that the originals are not independently preserved. This
matters because `legacy_archive/` is the only record of what the V3 rewrite replaced.

**Useful for Phase 2.3 — what the golden file will actually contain.** Read from `test_regression.m`
directly: the panel is sites `FFX002` and `PWC001` × every horizon in the data (4), taking the first case
per horizon in `scenario_id` sort order → **8 rows**; fixed `Seed = 42`, `AssumedSiteCapacity_kW = 200`,
`RelTol = 1e-6`; columns `energy_requested_kWh`, `peak_unmanaged_kW`, `peak_clamp_kW`,
`curtailed_clamp_kWh`, `peak_energy_aware_kW`, `unmet_energy_aware_kWh`, `deferred_energy_aware_kWh`.
On first run the harness **writes** the golden file and passes (l.45-53), so the CI workflow must be built
to *collect that file as an artifact* — otherwise the one thing Phase 2 exists to produce is created inside
the runner and thrown away.

### FIND-MATLAB-08 (high, and it changes Phase 2) — a real `.slx` for this project already exists, publicly

Found while checking `gh` scopes for the Phase 2 harness: the account already owns a **public** repository
**`andyyaro/MATLAB-SIMULINK-`** (created 2026-07-09, last pushed the same day, 10 files). It contains:

| File | Size | What it is |
|---|---|---|
| `site_grid_behavior_ev_charging.slx` | 100,077 B | **a real Simulink model**, authored in **MathWorks R2025b** (25.2.0.2998904) |
| `site_grid_behavior_ev_charging.slxc` | 5,163 B | its compiled cache |
| `build_and_run_site_grid_behavior_model.m` | 13,256 B | **byte-identical** to the private `matlab/legacy_archive/` copy |
| `untitled.m` | 22,012 B | **differs** from the private copy (32,967 B) — the private one is later/larger |
| `site_year_scenarios.csv` | 770 B | legacy scenario inputs |
| `site_year_scenarios_from_andy_v2.csv` | 15,278 B | a larger scenario set |
| two `.png` figures | ~560 KB | rendered outputs |
| `README.md`, `README.txt` | | run instructions |

**Provenance, confirmed by the project owner (2026-07-27):** this repository is the **predecessor** of the
current model — the legacy work that V3 was built *from*. It is old and superseded. That is consistent with
everything observed: its `build_and_run_site_grid_behavior_model.m` is byte-identical to the private
`legacy_archive/` copy, its README uses the retired "Now / 2035 / 2050" convention, and `buildSimulinkModel.m`
describes itself as reproducing "the same topology as the reviewed legacy model." It is **not** a second
live MATLAB layer and must not be treated as one.

**The masterprompt's premise "there is no `.slx` to import" is true of the private repository and false of
the wider project.** A genuine, MathWorks-authored model of this system's direct ancestor is already public.
Being superseded does not reduce its value as a **topology reference**, precisely because V3 was derived
from it and reproduces it exactly (verified below). It does mean the `.slx` is evidence about the *legacy*
model, not about V3's numerics — no V3 result may ever be attributed to it.

**The V3 source reproduces it exactly.** Unpacked the `.slx` (it is a zip of XML) and compared its topology
against `buildSimulinkModel.m` line by line:

- **Blocks: 11 vs 11, same names, same types** — `Base Load`, `EV Request`, `Capacity Limit` (FromWorkspace);
  `Total Unmanaged`, `Total Managed` (Sum); `Managed Logic Inputs`, `Main Scope Signals` (Mux);
  `Managed EV Power` (SubSystem — how a MATLAB Function block is stored); `Live Scope: Load Behavior`
  (Scope); `toWorkspace_unmanaged`, `toWorkspace_managed` (ToWorkspace).
- **Connections: all 15 match**, port for port. Every `add_line` at `buildSimulinkModel.m:217-232` has an
  exact counterpart in `system_root.xml`. Example: `Base Load` fans out to `Total Unmanaged/1`,
  `Managed Logic Inputs/3`, `Total Managed/1`, `Main Scope Signals/1` — identical in both.
- **The embedded function block matches.** `simulink/stateflow/chart_7.xml` contains
  `available = max(u(2) - u(3), 0); y = min(u(1), available);` — the same computation the V3 source writes at
  `buildSimulinkModel.m:189-190`, which adds comments and changes nothing else.

**Why this matters:** Phase 2.5 requires the native block diagram to be "verified against the CI-built `.slx`
when that exists." A real one exists **now**. The native renderer can be validated against MathWorks ground
truth immediately, independent of whether the harness CI ever succeeds — which de-risks Gate 2 substantially.
It also independently corroborates the V3 source's own claim to use "the same topology as the reviewed
legacy model."

**It also partly resolves FIND-MATLAB-07.** The legacy original *is* independently preserved — as a public
byte-identical copy of `build_and_run_site_grid_behavior_model.m`, not on the archive branch that
`EXECUTION_STATUS.md` cites. `untitled.m` differs, so that half of the claim remains uncorroborated.

### FIND-EXPOSURE-01 (high) — site identity and some electrical inputs are **already public**

This is the most important input to the Phase 2.2 exposure review, and it was not knowable from the private
repo alone. `MATLAB-SIMULINK-` has been public since **2026-07-09** and already discloses:

- the **`site_id` → real site name mapping**: `FFX002 = City_of_Fairfax_Regional_Library`,
  `PWC002 = Neabsco_Commuter_Garage`, `FFX004 = Community_Center_Demo`
- per-site **electrical planning inputs**: `spare_capacity_kW` (90 / 105 / 140), base load mean and peak,
  ports, charger power, arrival windows, dwell
- two figures whose **filenames name a real site** (`…City_of_Fairfax_Regional_Library…`)
- the legacy horizon convention "Now / 2035 / 2050" in its README — a **fourth** convention in circulation

What is **not** exposed there: readiness scores, rankings, tiers, cost conclusions, CO2e results, or any
study finding. So the existing exposure is **inputs and identity, not findings**.

**How this changes Phase 2.2, and how it must not.** The question "do the `site_id` values reveal client
identity?" is already answered *yes, publicly*. But prior exposure is **not** a licence to publish more:
the harness still publishes methodology and never findings, and the review still goes field by field. What
changes is that the review must be written against reality — it cannot claim the harness would be the first
disclosure of site identity, because it would not be.

**Deliberately not acted on.** Changing or deleting a pre-existing public repository is an outward-facing,
hard-to-reverse action on something this program did not create and was not asked to touch. It is recorded
here and carried to `RESIDUAL_RISKS.md` as a decision for the team, with options (leave as is / add a
clarifying README / make private), not taken unilaterally.

The owner's note that it is old and superseded is a point *for* keeping it, not against: it is the historical
record of what V3 was built from, and this project's whole discipline is about not losing provenance. The
residual-risk entry should therefore frame the choice as "leave it public, but make its status legible" —
a short README line saying it is the superseded predecessor of a later model and that its numbers are not
current — rather than as a deletion question. Deleting it would destroy the only public evidence of the
lineage that `legacy_archive/` and `buildSimulinkModel.m` both refer back to.

### DEC candidate — how the program uses this repository

**Use it as a read-only historical and topology reference. Never sync to it, never publish to it, never
treat it as the harness.** The Phase 2.2 harness remains a **new** repository built by one-directional,
hash-gated sync from the private source. Reasons: this one is hand-maintained and superseded, has no sync
gate, and mixes legacy inputs with figures; adopting it would create exactly the two-diverging-MATLAB-layers
failure Phase 2.2 exists to prevent.

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
