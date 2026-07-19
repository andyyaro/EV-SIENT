# Repository Migration Plan (executed 2026-07-19)

[← docs index](README.md)

How the completed Milestone 2 implementation was mapped into this repository, and what
happened to every class of pre-existing and implementation content. Companion:
[migration-from-v2.md](migration-from-v2.md) (user-facing behavior changes).

## Dispositions

### Retain unchanged (in history and archive branch, not in the new tree)
- V1 prototype tree (previous `main`) and V2 tree (`v2-expansion-planning` branch) —
  preserved via full git history, branch `archive/pre-milestone2-v3-20260719`, and
  annotated tag `pre-milestone2-v3-20260719`. Existing tags `v1-demo-scalability-ready`
  and `v1-review-ready` untouched.

### Replace (superseded by canonical V3 content)
- Root README, docs set, and workflow (`model-check.yml`) from the V1 tree → new
  landing page, docs index, and `tests.yml`/`matlab-manual.yml`.
- Loose `src/*.py` scripts → `src/fcf_m2/` package (legacy behavior retained via
  `legacy_v2` mode + golden tests).

### Move (implementation workspace → repo, path-normalized)
- `repos/python_m2_v3/{src,tests,data,pyproject,lockfile}` → `src/`, `tests/`, `data/`, root.
- `data_contract/v1` → `data/contract/v1`.
- `repos/matlab_simulink_m2_v3` → `matlab/` (its CI definition → `.github/workflows/matlab-manual.yml`, manual-trigger).
- Reports, standards docs, risk register, briefs → `reports/milestone-2/` + `docs/standards/`.
- Presentation package → `presentation/deck` + `presentation/assets`.
- Static dashboard + Tableau blocker/patch → `dashboard/`.
- Updated Excel workbook → `excel/`.
- Human-action packages → `docs/human-actions/`; website patch → `docs/operations/website-patch-package/`;
  open-actions list + reproduction guide + legacy-baseline evidence → `docs/operations/`.
- Build scripts (`build_excel`, `build_static_dashboard`, `md_to_docx`) → `scripts/`,
  rewritten to repo-relative paths (no machine-specific paths remain).

### Archive in Git history only (not carried into the tree)
- All V1/V2 working files superseded by V3 equivalents (old docs, checkpoint notes,
  generated outputs previously committed, old screenshots).

### Exclude from Git (never published)
- The internal implementation workspace as a workspace: `_working/`, `source_snapshots/`
  extractions, duplicate legacy repo copies, run ledgers/manifests of the Claude
  implementation process, research working archive, raw interview/transcript sources,
  ready-to-send email drafts' send logs (the drafts themselves are published as
  templates with no private contact details), virtual environments, caches, release
  ZIP bundles (already fully represented by tracked sources).
- The full-US TIGER boundary file — replaced by a filtered, simplified extract
  (documented in `data/cache/boundaries/ATTRIBUTION.md`).
- The legacy Tableau `.twbx` — unverifiable without Tableau Desktop; represented by
  the honest blocker + patch recipe instead.

### Include as a release artifact instead of source
- None at this time. `scripts/build_release_artifact.py` can produce a hash-logged
  bundle locally; a GitHub Release may be cut after the PR merges if the team wants a
  frozen download.

## Selection principles applied
One canonical Python codebase, one MATLAB codebase, one contract, one source of truth
per report/chart/dataset; no nested repositories; no generated outputs except small,
reviewer-relevant final deliverables (deck, dashboard, workbook, reports); no secrets,
no local paths, no files near GitHub size limits.
