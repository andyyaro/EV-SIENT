# Changelog

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
