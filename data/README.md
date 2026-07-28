# `data/` — inputs, reference data, and the canonical contract

[← repository root](../README.md)

## Classification

| Path | Class | Tracked? | Notes |
|---|---|---|---|
| `inputs/real_sites_v2.csv` | tracked input | yes | 12 candidate sites, 40 fields (team snapshot 2026-06-24) |
| `inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` | tracked input (frozen legacy output) | yes | electrical-risk levels consumed by right-sizing; provenance in filename |
| `inputs/legacy_matlab_site_meta.csv` | tracked input (labeled planning proxies) | yes | arrival windows + base loads from the legacy MATLAB adapter — UNVERIFIED proxies |
| `anchors/anchor_set_v1.json` | tracked reference | yes | versioned fixed scoring anchors (V3); changing this changes scores |
| `provenance/` | tracked reference | yes | typed field-level provenance driving data confidence |
| `cache/boundaries/` | tracked reference (external cache) | yes | US Census TIGER 2024 county boundaries, filtered+simplified for offline maps (see ATTRIBUTION.md) |
| `contract/v1/` | tracked reference — **the canonical cross-model contract, FROZEN** | yes | site × horizon × case table + schema + manifest with hash chain; every downstream artifact quotes these values. Frozen at Phase 4: its values never change, and its manifest digest is pinned so a change is detected. |
| `contract/v2/` | tracked reference — **additive over v1** | yes | every v1 field carried across byte-identically, plus the observed-data fields (`observed_*`, capacity confirmation, trigger outcome). Gated to rebuild byte-identically from v1, so v2 cannot silently restate a v1 value. |
| `synthetic/` | tracked reference (fabricated) | yes | the invented site set shipped with the public installer (DEC-020). Every value is fabricated and labelled; a run against it declares `synthetic_inputs: true`. |
| `observed/observed_sessions_template.csv` | example/template | yes | import format for future observed-session calibration |
| `outputs/` | generated output | **no (gitignored)** | reproduce with `make run-legacy` / `make run-v3` |

## The contract in one paragraph

`contract/v1/scenario_table.csv` (120 rows = 12 sites × {2026 baseline; 2036/2046/2056 ×
base/high/stress}) is the single source of truth consumed by MATLAB, Excel, the
dashboard, and the presentation. `capacity_basis` is `placeholder` on every row —
machine-readable proof that no electrical capacity has been verified. Validate any
time with `make validate` (rules, JSON Schema, and the RT-10 manifest hash chain).

Private data policy: no personal data, credentials, or private stakeholder contact
details are tracked anywhere in this repository.
