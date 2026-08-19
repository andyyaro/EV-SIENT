# RECONCILIATION.md - the three-tree diff and every resolution

**Phase 0.4 deliverable.** Three trees were in play at program start. This records what each one is, how
they differ, and how every divergence was resolved. The governing rule: *nothing on `origin/main` may be
silently dropped because it is absent from the snapshot, and nothing in the snapshot may be silently
discarded because `main` disagrees.*

| Tree | Path | What it is | Files |
|---|---|---|---|
| **1** | `repo/` (= `origin/main`) | the published private repository | 198 tracked |
| **2** | `incoming/snapshot/Future-City-Fellowship--main-2/` | a snapshot - provenance and recency stated as unknown | 198 |
| **3** | `incoming/explorer/fcf-3d/` | the standalone 3D explorer, never in the repository | 31 |

Baseline: `origin/main` at **`7626823`** ("Merge pull request #3 from andyyaro/milestone2-v3-professional-release"),
working tree clean. Safety tag `pre-v4-program-20260727` pushed before any change.

---

## 1. Trees 1 and 2 - a null result, established by two independent methods

**Result: byte-identical, 198 of 198. There is no divergence to adjudicate.**

The masterprompt anticipated a file-by-file arbitration using content, generated-at timestamps, run IDs,
contract hashes, and git history. None of that was needed, but the *absence* of divergence is itself a
finding that had to be proven rather than assumed - so it was proven twice, deliberately using different
mechanisms so that a bug in one could not produce a false pass in both.

**Method A - name-set comparison.** `git ls-files` on tree 1 versus `find -type f` on tree 2, both sorted
and diffed. The only difference reported was `docs/operations/v4-program/LEDGER.md`, which this program had
just created. Every one of the 198 pre-existing paths appears in both trees, with identical relative paths.

**Method B - byte comparison, then hash comparison.** `cmp` was run over every tracked file pairwise:
**198 identical, 0 differing.** Independently, SHA-256 was computed for all 198 files in each tree, the two
hash lists were sorted, and `diff` returned empty - *"SHA256 SETS IDENTICAL - 198/198"*.

### Resolution

**No file was dropped, preferred, merged, or discarded, because no file differed.** Tree 2 is a faithful
copy of tree 1 and carries no unique content. It is retained as received and is **not** enumerated in
`INVENTORY.md`, which would have duplicated 198 rows to no purpose; `INVENTORY.md` documents tree 1 and
tree 3, and this document is the record of why that is complete.

### What this does *not* mean

It does not mean the snapshot was pointless to check. Had it diverged, every difference would have needed a
logged decision, and the cost of *not* checking would have been silently building on a stale tree. The check
was cheap and the answer is now evidence rather than assumption.

It also does not mean the repository is correct - only that the two copies agree. Trees 1 and 2 agree on a
number of things that are **wrong**, and those are recorded as findings in `LEDGER.md` (notably the
active-port counts, which disagree with the contract in four documents).

---

## 2. Tree 3 - the 3D explorer, which is not a diff problem

`fcf-3d` was **never in the repository**, so there is no "which side is newer" question to answer. Its
reconciliation is a question of *convention*, not of vintage, and its substance is Phase 3's work rather
than Phase 0's. What Phase 0 establishes is the exact nature of the mismatch, verified first-hand.

### 2.1 Tree 3's contents

31 files: 5 Python modules (`fcf3d/`), `blender/build_assets.py`, `tests/test_pipeline.py`, `Makefile`,
`README.md`, `CLAUDE.md`, `requirements.txt`, `.gitignore`, 4 web files (`index.html`, `app.js`,
`style.css`, plus `web/data/manifest.json`), 3 further built data files (`sites.geojson`, `sites.json`,
`sites.inline.js`), and **all 12 GLB models** (`FFX001-004`, `PWC001-008`).

> **On the "36 files" figure.** The masterprompt describes this tree as 36 files; it is **31**. The tree is
> internally coherent and nothing appears missing - every module the `Makefile` and `README` reference is
> present, and all 12 GLBs exist. The gap is consistent with the workspace preparation the masterprompt
> itself describes, which stripped `__pycache__` and macOS cruft. Recorded as resolved-benign.
>
> Confirmed during this program: running the explorer's test suite recreated `.pytest_cache` and two
> `__pycache__` directories, which were **removed** to restore the tree to as-received (31 files). Those
> patterns are never committed.

### 2.2 The divergence: tree 3 reads tree 1's *superseded* baseline

Verified by reading `fcf3d/build_sites.py` directly. Its `SOURCES` map (l.47-55) reads **both** conventions:

| What | Source it reads | Convention |
|---|---|---|
| scoring detail | `tests/fixture_legacy_v2_site_results.csv` | **legacy_v2** |
| ports trajectory | `tests/fixture_legacy_v2_right_sizing.csv` | **legacy_v2** |
| electrical risk | `data/inputs/legacy_v2_electrical_risk_summary_frozen_*.csv` | **legacy_v2** |
| per-horizon scenarios | `data/contract/v1/scenario_table.csv` | **milestone2_v3** |
| coordinate provenance | `data/provenance/site_coordinate_sources.csv` | shared |
| waits, avoided EVSE, readiness confidence | 3 × `dashboard/tableau/patch_package/*.csv` | shared |

It emits `ports_2035` / `ports_2050` (l.436-437) and `ports_2035_base|high` / `ports_2050_base|high`
(l.463-466), while `build_scenarios` (l.278-302) simultaneously emits V3 `horizon_year` values.

**So the explorer is a hybrid, not simply stale**: a single map feature carries the retired 2035/2050
convention *and* canonical V3 horizons side by side. That is harder for a reader to detect than a uniformly
superseded payload, and it is exactly the failure `fcf-3d/CLAUDE.md` names as unacceptable - the map telling
planners a story the model never told. A **third** convention appears in the explorer's own README
("2026 → 2036 → 2050"), and a **fourth** in the public predecessor repo's README ("Now / 2035 / 2050").

### 2.3 Resolution - deferred to Phase 3, with the decision recorded now

**Decision: resolve in the repository's own dual-mode idiom rather than by deleting the legacy path.**

- The ETL sources the **canonical contract** for `milestone2_v3` and retains a **faithful `legacy_v2` path**.
- Field names carry their horizon honestly - no `ports_2050` ever holds a 2046 number.
- The viewer displays its active mode prominently and unambiguously.
- `test_attribution_reproduces_model_score` is preserved and extended to guard **both** modes.

*Alternatives rejected:* (a) repoint the ETL at the contract and delete the legacy path - rejected, it
would break bit-exact reproduction of the accepted V2 baseline, which the repository treats as a permanent
obligation; (b) leave the ETL alone and add a disclaimer - rejected, a label does not stop a superseded
number being read as current; (c) rename the fields but keep the legacy source - rejected, cosmetic.

### 2.4 Two further tree-3 findings that reconciliation surfaced

**The mirrored scoring weights are currently correct - and nothing enforces that.** Re-derived line by line
against `src/fcf_m2/scoring.py:140-175`: all four subscore weights (0.45 / 0.30 / 0.15 / 0.10) and all 19
driver weights match exactly, each subscore summing to 1.00, with the six `invert` flags matching the terms
the model wraps in `(1 - x)`. The one apparent mismatch - the explorer's `hours_open_n` against the model's
inline `hours_open.clip(0,24)/24` - is deliberately reconciled in `build_sites.py::prepare()` (l.318-323).
But the model holds these weights as **inline literals inside the formula**; there is no constant to import,
and the explorer's own `test_subscore_weights_sum_to_one` only checks its own dict. The agreement is
maintained by hand. Phase 3 extracts named constants in `scoring.py` (changing no numbers) so the match
becomes enforced.

**The guard test does not run by default.** `tests/test_pipeline.py` resolves
`FCF_REPO` to `~/fcf/Future-City-Fellowship--main-2`, a path that exists only on the original author's
machine, and gates 16 tests on its presence. Measured both ways: **31 passed / 15 skipped** with no
environment variable, **46 passed** when pointed at the real repo. The skipped set includes
`test_attribution_reproduces_model_score`. Phase 3 resolves the path from the integrated repo root so no
environment variable is needed.

---

## 3. A fourth tree, discovered during Phase 0

Not among the three named trees, and found while verifying `gh` scopes: the account owns a **public**
repository **`andyyaro/MATLAB-SIMULINK-`** (created 2026-07-09). The project owner confirms it is the
**superseded predecessor** that the current V3 MATLAB layer was built from.

**Reconciliation against tree 1:**

| File | Result |
|---|---|
| `build_and_run_site_grid_behavior_model.m` | **byte-identical** to `matlab/legacy_archive/` (13,256 B) |
| `untitled.m` | **differs** - public 22,012 B vs private 32,967 B; the private copy is later/larger |
| `site_grid_behavior_ev_charging.slx` | **has no counterpart in tree 1** - a real MathWorks R2025b Simulink model |

**Resolution: treat as a read-only historical and topology reference. Do not sync to it, publish to it, or
adopt it as the Phase 2 harness.** It is hand-maintained, superseded, has no sync gate, and mixes legacy
inputs with rendered figures; adopting it would create the two-diverging-MATLAB-layers failure that Phase 2
exists to prevent. Its `.slx` is nonetheless valuable - see `LEDGER.md` FIND-MATLAB-08, where its topology
is shown to match `buildSimulinkModel.m` exactly (11 blocks, 15 connections, identical function-block
logic), giving Phase 2.5 a MathWorks ground-truth reference immediately.

It also carries a real exposure consequence for Phase 2.2, recorded as FIND-EXPOSURE-01: the `site_id` →
real-site-name mapping and per-site electrical inputs have been **public since 2026-07-09**. No study
finding is exposed there. Prior exposure is not a licence to publish more; it means the harness exposure
review must be written against reality.

---

## 4. Summary of resolutions

| # | Divergence | Resolution | Phase |
|---|---|---|---|
| R-01 | Trees 1 vs 2 | **None exists.** Byte-identical 198/198, proven twice. Tree 2 retained as received, not enumerated separately. | 0 - closed |
| R-02 | Tree 3 file count 31 vs "36" | Benign; tree is coherent and complete. Test-generated caches removed to restore as-received state. | 0 - closed |
| R-03 | Tree 3 reads legacy_v2 while emitting V3 horizons | Dual-mode idiom: contract for V3, faithful legacy path retained, honest field names, visible mode, both modes guarded. | 3 |
| R-04 | Mirrored weights hand-maintained | Extract named constants in `fcf_m2.scoring`; explorer imports them; drift becomes gated. | 3 |
| R-05 | 15 of 46 explorer tests skip by default | Resolve repo path from the integrated root; no env var. | 3 |
| R-06 | Fourth tree (`MATLAB-SIMULINK-`, public) | Read-only historical/topology reference. Not a sync target. Exposure recorded, not unilaterally changed. | 2 / residual |

**Nothing was dropped from any tree.** No file was deleted, overwritten, or discarded during reconciliation.
