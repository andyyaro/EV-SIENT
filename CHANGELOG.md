# Changelog

## Unreleased — V4 platform program, Phase 4: contract v2

Contract **v2** at `data/contract/v2/`, additive over a now-frozen v1. See
[docs/migration-from-v3.md](docs/migration-from-v3.md).

### Added
- **12 fields** carrying what the V4 field-data loop produces: the measured values behind a
  trigger decision and the decision's own rule trace, when and how a capacity was confirmed,
  any unresolved conflict between sources, and **why** a site's data confidence is what it is.
  v1 had nowhere to put any of it, because when v1 was written there was no way to observe
  anything.
- `scripts/build_contract_v2.py` — builds and `--check`s v2. Refuses to leave a non-additive
  v2 on disk.
- `observed.CapacityUpgrade.method` — a verified capacity now records *how* it was verified
  as a controlled value, not only inside a prose source string.
- Two gates in `verify.sh` (15 → 17): v2 rebuilds byte-identically from v1 with every shared
  field unchanged, and the tracked v2 passes v1 rules + v2 rules + JSON Schema + RT-10.

### Changed
- **`horizon_label`: `now` → `baseline` in v2.** The one change that can break a consumer:
  a filter on `horizon_label == "now"` silently matches nothing and drops the baseline row
  without erroring. Filter on `horizon_year == 2026` instead. `now` is time-relative text
  frozen into a dated artifact — read in 2036 it is simply false. **v1 keeps `now` forever.**
- `validate-contract` is version-aware, reading the version from the artifact's manifest
  rather than a flag, so a v2 directory cannot be checked under v1's weaker rules.

### Frozen
- **`data/contract/v1/` is immutable.** `tests/test_contract_v2.py` pins its manifest
  SHA-256; anything that regenerates or edits v1 fails that test. The correct response is to
  revert or route the change into v2 — never to update the constant.

### Enforced, not documented
- A row cannot carry an observed value while reporting `awaiting_observed_data`.
- A `verified_*` capacity basis must name the date it was verified.
- **An empty `observed_*` field means NOT OBSERVED. It never means zero.** Do not `fillna(0)`;
  a defaulted uptime of 1.0 walks straight past the reliability gate.

### Fixed (both would have fired the day real data arrived, not today)
- The empty state was `""` in memory but `NaN` from disk, and `astype(str)` renders a missing
  value as the **non-empty** string `"<NA>"`. The orphaned-observation rule would have fired
  on all 120 correct rows. Empty is now `None` end to end and the emptiness test is NaN-aware.
- A column of nothing but empty cells reads back from CSV as `float64`, so writing
  `"2026-05-04"` into it raises instead of upcasting — the run receiving the project's first
  real utility record would have been the run that crashed.

### Unchanged
- **Zero real observations.** Every `observed_*` field is empty, every row reports
  `awaiting_observed_data`, capacity is `placeholder` at all twelve sites. Nothing in v2 is
  more certain than anything in v1.
- `model_version` stays **`3.0.0`**. The contract version and the model version are separate
  facts; the bump to `4.0.0` waits until V4 is genuinely complete.
- `legacy_v2` still reproduces 25 starter / 48 pathway. All published totals identical.

---

## Unreleased — V4 platform program, Phase 1: repair the base

Defects found by a full audit of the repository and fixed before any new work was
built on top. No model logic changed and no number moved except where a published
figure disagreed with the contract, in which case the contract won.

### Corrected numbers
- **Active-port series** in `README.md`, the final report, the speaker notes, and the
  website patch package said 25 / 44→47 / 47→48 / 47→48. The contract sums to
  **25 / 35→44 / 44→48 / 44→48**; the value 47 was never a portfolio total at any
  horizon. The cost and emissions columns in the same table rows were already correct.
- **The headline site claim.** `README.md` named FFX002 top-ranked at 58.8 with
  "Medium confidence" under a heading asserting canonical provenance. 58.8 is the
  `legacy_v2` score; canonically FFX004 leads at 53.4 and FFX002 is second at 51.8.
  No output produces "Medium" for any site — **all 12 are Low**.
- **Avoided pathway ports** were published as "13–23"; the metric gives 23 at the 2026
  baseline, 13 by 2036, and 4 by 2046 and 2056.
- **MCDA arithmetic** (`docs/human-actions/team_alternatives_session/`): alternative G
  published 37.0 against a computed 40.0 (rank unchanged), and the equity-crossover
  disclosure read aloud before the weighting vote stated 2× the default equity weight
  where the matrix puts it at ~2.5×.

### Gates
- `scripts/verify.sh` **failed on a clean checkout** (8 PASS / 2 FAIL). Both causes fixed;
  it now reports 10 PASS / 0 FAIL.
- **CI ran 6 of the 10 gates** and its push trigger covered only two branches. CI now
  invokes `verify.sh` itself, so parity holds by construction, and triggers on all branches.
- **The secret scan matched credential *names*, not values**, so it flagged CI's own
  workflow file and any document discussing it. It now requires the value, is shared by both
  gates, and additionally catches AWS account IDs, session tokens, Slack tokens, and SSH keys.
- **The Markdown link checker linkified quoted link syntax**, disagreeing with lychee. It now
  ignores code spans and fenced blocks.
- New gates: published numbers traced to the contract, footer-log portability, MCDA arithmetic.

### Generated artifacts
- `dashboard/static/footer_log.json` carried nine absolute authoring-machine paths, and a
  rebuild duplicated every entry. Fixed in the generator; 8 of 9 charts regenerate
  byte-identical.
- All four `reports/milestone-2/*.docx` and the client-facing PDF were stale against their
  Markdown, carrying a pre-reorganisation directory layout. `python-docx` was undeclared, so
  they could not be rebuilt; it is now a `[reports]` extra with a `make reports` target.
- `requirements-lock.txt` was missing four transitive dependencies, including one required
  only on the Python version CI pins.

### Documentation accuracy
- `contract.py` pointed at a contract directory that does not exist, and both its RT-coverage
  claims were wrong in opposite directions. RT-06 is implemented nowhere; that is now stated.
- `config.py` claimed every result-changing constant lives in it; several do not, and they
  are now named.
- `emissions.py` duplicated the network-fee constant instead of reading it from config.

## Milestone 2 V3 (2026-07-19)

The full Milestone 2 publication of the EV-charging planning platform for
Fairfax City and Prince William County.

### Model
- **Dual-mode model** (`src/fcf_m2`): `legacy_v2` reproduces the accepted V2
  baseline bit-for-bit (golden-tested: FFX002 58.8; 25 starter / 48 pathway
  ports); `milestone2_v3` is the canonical Milestone 2 model.
- **Canonical data contract** (`data/contract/v1`): one validated
  site x horizon x case table (120 rows) consumed by MATLAB, Excel, the
  dashboard, reports, and the deck — with schema, provenance, assumptions,
  and a manifest hash chain.
- **Canonical horizons** 2036 / 2046 / 2056 (10/20/30 years from a 2026
  baseline), replacing the mixed Now/2035/2050 conventions.
- **Fixed-anchor readiness scoring** (cohort-independent) with **typed data
  confidence** per site — 0 of 12 sites reach High confidence, and
  electrical capacity remains a labeled placeholder at all 12 sites.
- **Peak-window and discrete-event-simulation wait models**, **lifecycle
  economics** (screening-class net present cost, never budgets), and
  **emissions** using the EPA eGRID2023 Rev 2 SRVC factor of
  **596.3 lb CO2e/MWh** — correcting the 590.2 figure used earlier.

### Artifacts
- **MATLAB V3 rewrite** (`matlab/`): session-based site-load model with
  capacity guard and managed charging, driven by the contract-generated CSV.
  Statically checked only — **never executed** (no license was available);
  see `matlab/EXECUTION_STATUS.md`.
- **Excel workbook update** (`excel/`): repaired pie chart, labeled proxies,
  2056 extension, lifecycle + CO2e sheets, live reconciliation checks.
- **Static dashboard** (`dashboard/static/`): 9 offline, footer-labeled,
  contract-derived visuals + combined PDF; Tableau patch package and honest
  blocker note in `dashboard/tableau/`.
- **Standards package** (`docs/standards/`): final standards application
  matrix (UL 2594 + UL 3600 highlighted) and a proposed municipal EV
  standard concept (fellowship design exercise, not a UL/ULSE proposal).
- **Presentation package** (`presentation/`): final deck, speaker notes,
  timing runbook, Q&A backup.
- Reports (`reports/milestone-2/`), human-action packages
  (`docs/human-actions/`), and operations docs (`docs/operations/`)
  complete the record; `./scripts/verify.sh` runs every verification gate.

## Pre-V3 history

The V1 prototype and V2 expansion-planning trees are preserved unchanged in
git history: branch `archive/pre-milestone2-v3-20260719` and annotated tag
`pre-milestone2-v3-20260719`, plus the original V1 tags
`v1-demo-scalability-ready` and `v1-review-ready`. See
[docs/repository-migration-plan.md](docs/repository-migration-plan.md) and
[docs/migration-from-v2.md](docs/migration-from-v2.md).
