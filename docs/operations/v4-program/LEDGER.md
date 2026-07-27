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
| 0.1 | Workspace verification (three trees present, no cruft) | in-progress | See "Observed workspace facts" below. |
| 0.1b | Build Python 3.12 venv matching CI | not-started | Machine default is 3.14; `python3.12` present at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12`. |
| 0.2 | Safety tag `pre-v4-program-YYYYMMDD` pushed; branch `v4-platform` created | not-started | |
| 0.3 | Read every line of every file in all three trees | not-started | MATLAB `.m` files (17, ~2,891 lines) are load-bearing — no skimming. |
| 0.3b | `INVENTORY.md` written | not-started | |
| 0.3c | `INVENTORY.md` independently verified by a separate agent | not-started | |
| 0.4 | Three-tree reconciliation, file by file | not-started | |
| 0.4b | `RECONCILIATION.md` written | not-started | |
| 0.5 | AWS read-only discovery (both profiles) | not-started | Change nothing. |
| 0.5b | Website end-to-end mapping (domain → CF → S3 → objects) | not-started | |
| 0.5c | Read `docs/operations/website-patch-package/` in full | not-started | |
| 0.5d | `AWS_INVENTORY.md` written | not-started | |
| G0 | **Gate 0** | not-started | Inventory + reconciliation + AWS inventory complete and independently verified; ledger initialized; safety tag pushed. |

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
| OPEN-1 | `incoming/explorer/fcf-3d/` contains **31** files; masterprompt says 36. Which is right, and is anything missing? | open | Resolve during Phase 0.3/0.4 by full enumeration + comparison against `fcf-3d`'s own manifest/docs. Do not assume files are missing until the tree is fully read. |

---

## FINDINGS NOT YET ACTED ON

*Leads from subagents and scans. Every one is a lead, not a fact, until independently confirmed against the actual files.*

| # | Finding | Source | Confirmed? | Acted on? |
|---|---|---|---|---|
| — | *(none yet)* | | | |

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
