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
| 0 | Ground truth | **GREEN — verified** | 229 files inventoried and independently verified; 3+1 trees reconciled; AWS mapped read-only; 200 findings registered. |
| 1 | Repair the base | **GREEN — verified** | Was 8 PASS / 2 FAIL on a clean checkout; now 10 PASS / 0 FAIL locally **and in CI**. 10 repairs, each committed separately. |
| 2 | Liberate the MATLAB layer | **in-progress** | **Harness live and MATLAB executing.** Tier 2 proven by execution. Runs 1-2 failed on portability defects, both fixed; run 3 in flight. `EXECUTION_STATUS.md` untouched until a run *passes*. |
| 3 | Integrate the 3D explorer | **near-complete** | Governing defect fixed and gated; viewer now states its mode and all four caveats. Remaining: vendor Cesium for offline; keyboard access for the site list. |
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
| 0.3 | Read every line of every file in all three trees | **verified** | 12 lanes, **224 files read, 0 not fully read**, 13 agents, 0 errors (`wf_0ac58ed8-c08`). All 9 `matlab/src/*.m` also read line by line by the lead. **200 findings** → `FINDINGS_REGISTER.md`. |
| 0.3b | `INVENTORY.md` written | **done** | 229 files (198 repo + 31 explorer); per-file detail in `inventory/` (12 lane docs, 860 KB). |
| 0.3c | `INVENTORY.md` independently verified by a separate agent | **verified** | Independent verifier: **coverage COMPLETE, zero gaps; accuracy — zero errors in 20+ probes**. See below. |
| 0.4 | Three-tree reconciliation, file by file | **verified** | **Snapshot ≡ `origin/main`, byte-identical, 198/198**, proven twice by different methods. See RECON-1. |
| 0.4b | `RECONCILIATION.md` written | **done** | Includes the fourth tree discovered during discovery (`MATLAB-SIMULINK-`). |
| 0.5 | AWS read-only discovery (both profiles) | **verified** | Both identities matched expected accounts. Nothing created, modified, or deleted. |
| 0.5b | Website end-to-end mapping (domain → CF → S3 → objects) | **verified** | Full chain mapped; all 16 served objects listed. |
| 0.5c | Read `docs/operations/website-patch-package/` in full | **verified** | README + PATCH_GUIDE + DEPLOYMENT_RUNBOOK read directly; `content/` covered by lane L07. |
| 0.5d | `AWS_INVENTORY.md` written | **done** | Committed `31b1628`. |
| G0 | **Gate 0** | **GREEN** | All five conditions met and independently verified. See "Gate 0 — closed" below. |

### Gate 0 — closed 2026-07-27

| Condition | Evidence |
|---|---|
| Inventory complete | `INVENTORY.md` + 12 lane documents cover **229/229** files. 224 files read by lanes end to end, **zero** reported unread; the remaining 5 are the binaries L12 verified by opening rather than reading byte-level. |
| Reconciliation complete | `RECONCILIATION.md`. Trees 1↔2 byte-identical 198/198 proven twice; tree 3 divergence characterised and its resolution decided with alternatives; a fourth tree found and reconciled. |
| AWS inventory complete | `AWS_INVENTORY.md`. Both identities verified, live site mapped end to end, nine findings, costs itemised. **Nothing created, modified, or deleted.** |
| **Independently verified** | A separate agent that did not produce the inventory checked it. Verdict: **"COVERAGE: COMPLETE… GAPS: ZERO"** and **"ACCURACY: NO ERRORS FOUND IN 20+ INDEPENDENT PROBES"**, including line-number citations, a SHA-256 against the manifest, all 12 GLB byte sizes, PNG pixel dimensions, GeoJSON feature ordering, and pytest function counts. Zero WRONG, zero UNVERIFIABLE. |
| Ledger initialised | This file, created before any other work and committed at `95e91e0`. |
| Safety tag pushed | `pre-v4-program-20260727` → `origin`, before any change. |

**Two procedural carry-forwards the verifier raised, both accepted:**

1. **Pin a commit before any further file counting.** The tree was being written to while the verifier
   counted (`git ls-files` returned 200, then 214, then 215 during its run) because this program was
   committing its own documents concurrently. Any future count must state the commit it was taken at.
2. **L12's orphan findings must be judged against *pre-*Phase-0 references.** `docs/assets/readme/site-map.png`
   and `three-horizons.png` were genuine orphans when L12 ran; they are now cited by `INVENTORY.md` and
   `FINDINGS_REGISTER.md`. They remain orphans in any functional sense — no code and no reader-facing
   document references them — and a later re-run must not "discover" that the orphan finding was wrong.

**One honest note the verifier recorded about itself**, worth keeping because it is the doctrine working:
it initially believed lane L05 was wrong about FFX002's confidence, having looked for a confidence column in
`site_table.csv` where none exists. L05 was right — it had correctly located `data_confidence` in
`scenario_table.csv` and correctly distinguished `electrical_risk_level = medium` from
`data_confidence = Low`. The verifier corrected itself rather than filing a false finding. It also had to
correct its own gap-detection method twice (naive path grep produced a false 47-file gap) before concluding
the coverage was complete.

### Phase 1 — Repair the Base

Starting state: **`verify.sh` 8 PASS / 2 FAIL, exit 2** on a clean checkout. Current state:
**10 PASS / 0 FAIL, exit 0**, and CI runs the same ten gates.

| # | Repair | Commit | State | Evidence |
|---|---|---|---|---|
| 1.1 | Footer log logged absolute authoring-machine paths; a rebuild duplicated every entry | `e5164fb` | **verified** | Fixed in the generator, not the artifact. 8 of 9 PNGs regenerate byte-identical. Hygiene gate passes. |
| 1.2 | Link checker linkified quoted link syntax, disagreeing with lychee | `f4fae26` | **verified** | Masks code spans and fenced blocks; 8 unit cases; offsets preserved. Fixed the 12 broken links it then found in the Phase 0 docs. |
| 1.3 | Secret gate matched credential *names*, so it flagged CI's own workflow | `024dab7` | **verified** | Value-matching patterns, shared by both gates, extended to AWS account IDs. **32 tests, both directions.** |
| 1.4 | CI ran 6 of 10 gates; push trigger covered 2 branches; installed without the lock | `d4373b4` | **verified** | CI now invokes `verify.sh`. Lock completed with 4 missing transitive pins; a fresh 3.12 env now matches it exactly. |
| 1.5 | Port series and headline site claim wrong in 4 documents | `162ce9c` | **verified** | Recomputed from the contract. New gate `test_published_numbers.py`, mutation-tested on 3 regression classes. |
| 1.6 | All 4 `.docx` and the client PDF stale against their Markdown | `fa1baf3` | **verified** | Measured with a real PDF extractor before and after. `python-docx` declared; `make reports` added. |
| 1.7 | Three wrong docstring claims; a duplicated config constant | `c43e9b1` | **verified** | Full pipeline re-run: every numeric output byte-identical. |
| 1.8 | Two MCDA arithmetic errors in the matrix the team is asked to adopt | `f945749` | **verified** | G published 37.0 vs computed 40.0 (rank unchanged); crossover 2× → ~2.5×. New gate parses the published table. |
| 1.9 | README CI claim + CHANGELOG | `c95affd` | **verified** | The claim is now true, so it was made precise rather than weakened. |
| 1.10 | Deprecated Node 20 action versions | `4b5e1f8` | **verified** | checkout v4→v7, setup-python v5→v6. Run is now annotation-free. |
| G1 | **Gate 1** | — | **GREEN** | **`verify.sh`: 10 PASS / 0 FAIL, exit 0** on a clean checkout. **CI green on the pushed branch**, run `30285417343`, all ten gates observed passing in the log on Python 3.12.13. Every repair committed separately with its reasoning. |

**Repairs deliberately NOT made, with reasons:**

| Finding | Why not fixed in Phase 1 |
|---|---|
| `horizon_label` = `now`/`plus10`/`plus20`/`plus30` (FIND-NUM-04) | `data/contract/v1` becomes **immutable** at Phase 4. Changing a contract v1 value now would break the hash chain and the frozen baseline. The fix belongs in the **contract v2** schema, noted in the migration document. |
| 35% of `feasibility_subscore` weights `spare_capacity_kw`, which is `0` at all 12 sites, so that weight contributes nothing | This is a **model-design observation, not a defect**. "Fixing" it would move every readiness score and break the `legacy_v2` golden, which the repository treats as a permanent obligation. It is an honest limitation to surface in Phase 9, and it is a direct consequence of limitation #1 (capacity unconfirmed at 12/12) — the moment real capacity data arrives via the Phase 4 loop, this weight starts doing work. |
| `09_site_map_offline.png` is not byte-reproducible across machines | Real, but a **gate design constraint** rather than a repair. Recorded for Phase 3 so that a "committed artifacts match a fresh build" gate does not go flaky on this one file. |
| Tableau `tbl_peak_waits.csv` columns are `0.0` on all 12 rows | **Phase 6** owns it. Building the specified worksheet would produce twelve zero-height bars, which is a finding to declare, not to paper over. |
| `src/fcf_m2.egg-info/SOURCES.txt` is stale build metadata | Regenerated on every build; tracking it at all is the questionable choice. Left alone rather than churning a generated file for no functional gain. |

### Phase 3 — Integrate the 3D Explorer

| # | Task | State | Evidence |
|---|---|---|---|
| 3.1 | Explorer moved in as a first-class citizen | **verified** | ETL at `src/fcf3d/` beside `fcf_m2`; assets at `explorer/`; tests folded into the repo's pytest run. One dependency story, one Makefile, one `.gitignore`. |
| 3.2 | **Horizon/data-source mismatch resolved** | **verified** | Dual-mode ETL. `milestone2_v3` (default) emits only 2026/2036/2046/2056; `legacy_v2` emits only now/2035/2050. Verified neither leaks the other's fields. |
| 3.3 | Committed V3 fixtures | **verified** | The contract carries no readiness score, so V3 needed frozen fixtures mirroring how `legacy_v2` was already handled. Gated against a fresh build. |
| 3.4 | Mirrored weights re-derived and **drift-gated** | **verified** | `fcf_m2.scoring` now owns named constants; the explorer **imports** them. 19 drivers + 6 invert flags checked. Extraction moved **no number** — proven byte-for-byte. |
| 3.5 | Guard test actually runs | **verified** | Was 31 passed / 15 skipped by default; now **46 passed, 0 skipped**, plus 53 new. |
| 3.6 | Built artifacts committed and drift-gated | **verified** | `explorer/web/data` + 12 GLBs committed; `.gitignore` note explains why. |
| 3.7 | Cesium pinned | **verified** | 1.128, both refs. `scripts/check_cdn_pins.py` enforces pinning and the ≥1.124 floor; both failure modes mutation-tested. |
| 3.8 | New gates in `verify.sh` **and** CI | **verified** | 4 added → **14 gates, all green locally and in CI**. |
| 3.9 | `CLAUDE.md` constraints folded into repo docs | **done** | `docs/architecture/3d-explorer-constraints.md`, with an enforcement table naming the gate for each constraint. |
| 3.10 | Viewer UI: surface the active mode; add the 2 missing disclaimers | **verified** | Mode badge in the header, styled by state — canonical reads as chrome, legacy reads as a warning with a `SUPERSEDED` prefix. `manifest.json` is now read; a missing manifest reads as **unknown**, never as canonical. All four standing caveats in the rail footer. Gated by exact wording + mutation-tested. |
| 3.11 | Vendor Cesium for offline use | **not-started** | Pinned, not yet vendored. |
| 3.12 | Keyboard accessibility of the site list | **not-started** | L11: the primary interaction is mouse-only. Phase 9 owns accessibility, but this is the explorer's own defect. |
| G3 | **Gate 3** | **open** | 3.11 (vendor Cesium) and 3.12 (keyboard access) outstanding. **15 verify.sh gates green** locally and in CI. |

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
| 2026-07-27 | `python-docx` (+ `lxml`) into `repo/venv` | 1.2.0 / 6.1.1 | `scripts/md_to_docx.py` needs it to regenerate the report DOCX; previously undeclared, which is why those artifacts had drifted | **Only for `make reports`.** Declared as the `[reports]` extra and pinned in `requirements-lock.txt`. |
| 2026-07-27 | Octave `datatypes`, via `pkg install "https://github.com/pr0m1th3as/datatypes/releases/download/release-1.2.7/datatypes-1.2.7.tar.gz"` | 1.2.7 | supplies `table`/`datetime` for the Phase 2 Tier-2 Octave runtime. **Compiles 9 C++ sources**, so it needs `mkoctfile` and a toolchain; ~20 s | **Only for the in-app Octave runtime.** Not needed for any Python gate, the test suite, or CI. Its `string` class is deliberately *not* relied on — see `MATLAB_LIBERATION.md` §3.2. |
| 2026-07-27 | `pyyaml`, `pypdf` — **installed then uninstalled** | — | one-off validation of workflow YAML and PDF text extraction | **No.** Removed so `repo/venv` still matches `requirements-lock.txt` exactly. |

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

**FIND-MATLAB-09 (CRITICAL) — under Octave the fail-closed capacity guard silently fails to fire.**
Raised by lane L03, then reproduced directly by the lead. This is the most consequential finding of Phase 0.

`capacityGuard.m:53-55` builds its controlled vocabulary as a bracketed string-array literal. In MATLAB that
is a 1×6 `string` array. In Octave it is **one 1×85 `char` row**:

```
class(allowedBases) = char
size                = 1x85
value               = "verified_utilityverified_facilityengineering_estimateplanning_proxyplaceholderunknown"
numel               = 85          (MATLAB: 6)
```

Consequently `ismember(basis, ["verified_utility","verified_facility"])` at line 84 returns a **1×11 logical
vector** — one element per character of `"placeholder"` — instead of scalar `false`:

```
ismember returns class=logical size=1x11
  0  1  1  1  1  0  0  1  1  1  1
```

Feeding that into the fail-closed gate at line 89, `if mode == "feasibility" && ~isVerified`, and running it:

```
RESULT: gate DID NOT FIRE   <-- silent safety failure
```

**Read plainly: an unmodified Octave run would emit a feasibility claim from placeholder capacity, which is
exactly what this guard exists to make impossible, and it would do so without any error or warning.** All 12
sites are `capacity_basis = placeholder`, so this is not a corner case — it is every row.

Three consequences that bind Phase 2:

1. **Tier 1 is not merely unreachable, it is unsafe to attempt.** "It ran and produced numbers" would be the
   worst possible outcome here, because the numbers would be wrong in the specific direction the project's
   honesty discipline is built to prevent.
2. **A function-level shim cannot fix this.** `["a", "b"]` is *syntax*, not a call — there is no function to
   override. Overloading `horzcat` on a `string` class does not help either, because a double-quoted literal
   in Octave is already `char` before any user code sees it. The realistic Tier-2 route is a **deterministic,
   tested, auditable build-time source transformation** (bracketed string-array literals → `cellstr`; `+`
   concatenation → `strcat`/`sprintf`) whose output is diffed against the source. Verified that the cellstr
   form behaves correctly: `ismember("placeholder", {"verified_utility","verified_facility"})` → scalar `0`.
3. **Whatever tier is chosen, it ships with a test that proves the fail-closed guard fires.** Any Octave
   result is otherwise untrustworthy regardless of how the numbers look.

**Working conclusion (to be proven in Phase 2, not assumed):** Tier 2 remains the target, but its centre of
gravity is now clear — a source-transformation step plus `string`/`table` support, not a thin function shim.
`capacityGuard.m` and `makeSessionProfiles.m` both already accept *either* a one-row table *or* a struct
(`localRowToStruct`), which is a deliberate seam the transformation can use. If the transformation cannot be
made provably faithful, Tier 3 with permanent visible labelling is the honest answer, and this finding is the
evidence for saying so.

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

### Lane findings the lead re-checked first-hand (subagent doctrine: a finding is a lead until confirmed)

Full register of all 200 in [`FINDINGS_REGISTER.md`](FINDINGS_REGISTER.md). These are the ones re-verified
directly, because each changes a later phase's design. Where the lead's severity differs from the lane's,
the difference and the reason are recorded — accepting a rating uncritically would defeat the doctrine.

**FIND-V4-01 (high, and it blocks Phase 4 as specified) — the observed-data template cannot feed the
trigger evaluation it exists to feed.** Raised by L05; confirmed by reading both files.

`data/observed/observed_sessions_template.csv` offers exactly six fields:

```
site_id, date, sessions, energy_kwh, mean_dwell_min, facility_visitors_day
```

`triggers.evaluate()` consumes an `ObservedMetrics` of four values (`triggers.py:23-26`):

| Required by the trigger policy | Derivable from the template? |
|---|---|
| `avg_utilization` (0-1) | **partly** — only if port count and open hours are joined in from the contract |
| `p90_wait_min` | **no** — needs per-session arrival/start/end times; the template has one aggregate dwell mean per day |
| `uptime` (0-1) | **no** — needs charger availability or fault records; nothing in the template touches it |
| `equity_index_percentile` | yes — comes from the model, not from observations |

And `assumptions.json` `trigger_policy` gates on all of them: `utilization_threshold` 0.4,
`wait_threshold_min` 10.0, `reliability_uptime_min` 0.97, `min_observation_months` 6, plus the equity
override. `triggers.py:53` refuses to proceed when uptime fails the gate — so the **one metric the policy
checks first is the one the template cannot supply at all**.

So Phase 4's headline loop — observations enter, confidence upgrades, re-score, re-evaluate triggers —
cannot be built on this template as it stands. Phase 4 must extend the observed schema (per-charger id,
session start/end timestamps rather than a daily dwell mean, and an availability/fault record), which is a
design decision to log with alternatives, not a silent addition. Doing this *without* inventing data is
still straightforward: the extended schema ships empty with labelled synthetic fixtures.

**FIND-NUM-04 (medium — lane rated it high; the lead disagrees, with reasons) — the contract labels its own
horizons `now` / `plus10` / `plus20` / `plus30`.** Confirmed: on rows whose `model_mode` is
`milestone2_v3`, `horizon_label` takes exactly those four values for 2026/2036/2046/2056 respectively, and
the 3D explorer surfaces `horizon_label` to readers (`build_sites.py:288`).

Downgraded from the lane's **high** to **medium**, deliberately:

- These are **not** the retired 2035/2050 convention. They are *relative* labels and they are *arithmetically
  correct* against `baseline_year: 2026` — `plus10` really is 2036. Nothing here is superseded or wrong.
- `horizon_year` sits in the same row carrying the absolute year, so no consumer is forced to rely on the label.

But it is not nothing, which is why it is not `info`:

- **`now` is time-relative text frozen into a dated artifact.** Read in 2036, "now" is simply false, and it
  is the one horizon word the program explicitly names as prohibited phrasing. `baseline` would say the same
  thing without decaying.
- It surfaces to readers through the explorer, so it is reader-facing vocabulary, not an internal key.

Phase 1 records it; changing a contract v1 value is **out of scope** because `data/contract/v1` becomes
immutable at Phase 4 — the right home for the fix is the **contract v2** schema, with v1 left untouched and
a note in the migration document.

### Other findings not yet acted on

See [`FINDINGS_REGISTER.md`](FINDINGS_REGISTER.md) for all 200 with evidence. The register's `Confirmed`
column tracks which have been re-checked by the lead; the remainder are carried into the phase that owns
them and confirmed before any code changes on their account.

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
| 2026-07-27T15:55Z | All 9 `matlab/src/*.m` read line by line by the lead. Simulink topology extracted. FIND-MATLAB-02/03/04/05 recorded. |
| 2026-07-27T16:00Z | Every headline number traced to the contract. Costs, CO2e, eGRID, goldens, contract shape all **match**; **ports** and the **FFX002 headline** do not (FIND-NUM-01/02). RT-10 chain independently recomputed: **11/11 PASS**. `WORKFLOW_STEPS.md`: no drift. |
| 2026-07-27T16:05Z | Public predecessor repo `MATLAB-SIMULINK-` found. Its real `.slx` matches `buildSimulinkModel.m` exactly (11 blocks, 15 connections, identical function-block logic). Provenance confirmed by the project owner. FIND-MATLAB-08, FIND-EXPOSURE-01. |
| 2026-07-27T16:12Z | Read fleet complete: 13 agents, 0 errors, 224 files, **200 findings**. `INVENTORY.md`, `RECONCILIATION.md`, `FINDINGS_REGISTER.md` written. |
| 2026-07-27T16:20Z | **FIND-MATLAB-09 (critical)** reproduced: under Octave the fail-closed capacity guard does not fire. Tier 1 reclassified from unreachable to unsafe. |
| 2026-07-27T16:25Z | Independent coverage verifier: **coverage COMPLETE, zero gaps; zero errors in 20+ probes**. **Gate 0 GREEN.** |
| 2026-07-27T16:30Z | Phase 2 front-loaded: exposure review + Octave tier + harness CI design launched (`wf_c89b4289-b6c`). |
| 2026-07-27T16:20-17:00Z | Phase 1: ten repairs committed separately. `verify.sh` goes 8/2 → **10/0**. Four published numbers corrected against the contract; four new gates added, each mutation-tested. |
| 2026-07-27T17:05Z | Branch pushed. **CI green, run `30285417343`** — all ten gates observed passing in the log. **Gate 1 GREEN.** |
