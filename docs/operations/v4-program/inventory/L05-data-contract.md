# LANE L05 — DATA AND THE CANONICAL CONTRACT

Repo root: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (branch `v4-platform`, HEAD `95e91e0 docs(v4-program): initialize program ledger`).
All paths below are relative to that root. **Read-only lane — nothing was modified.**

Files assigned: 18 (17 under `data/`, plus the `tl_2024_va_counties.geojson` parse/count check).
Files read end-to-end: 17 of 17 text files. The 18th (`tl_2024_va_counties.geojson`, 172 KB of coordinate arrays) was
programmatically parsed and structurally characterised per instruction ("do not dump it") — see its entry.

---

## 0. HEADLINE ANSWERS (the things Phase 1 needs first)

### 0.1 The manifest hash chain — INDEPENDENTLY VERIFIED, 11/11 PASS

**How the chain is actually constructed** (generator read at `src/fcf_m2/contract.py`, outside this lane but
required to answer the question precisely):

- `sha256_file(path)` at `src/fcf_m2/contract.py:64-69` is a **plain SHA-256 of the raw file bytes**, streamed in
  65536-byte chunks. There is **no normalisation whatsoever** — no line-ending canonicalisation, no key sorting,
  no whitespace stripping, no encoding step.
- It is **NOT a linked chain / Merkle tree.** Each entry is an *independent* flat digest of one file. Nothing hashes
  the previous hash. Calling it a "chain" is generous; it is a hash *manifest*.
- `tables` are hashed in a fixed literal order defined at `src/fcf_m2/contract.py:282-283`:
  `["schema.json", "scenario_table.csv", "site_table.csv", "source_provenance.csv", "standards_register.csv", "assumptions.json"]`,
  each hashed **after** it was written to the contract dir (`contract.py:275-280`), so the digest covers the exact
  emitted bytes (`pandas.DataFrame.to_csv(index=False)` for CSVs, `json.dumps(..., indent=2)` for JSON).
- `inputs` is **not computed by `write_contract` at all** — it is passed in by the caller as `inputs_hashed`
  (`contract.py:264, 290`), hashed at the inputs' own on-disk locations.
- `contract_manifest.json` does not hash itself (expected; self-reference impossible).
- Ordering within the emitted JSON is Python dict insertion order, preserved by `json.dumps`.

**Verification run** (`shasum -a 256`, 2026-07-27):

| # | Group | Manifest key | Path hashed | Algorithm | Manifest value | Computed | Result |
|---|---|---|---|---|---|---|---|
| 1 | inputs | `real_sites_v2.csv` | `data/inputs/real_sites_v2.csv` | SHA-256 | `582e0b375fe3a078972fe77ad602bd1837b26679e09bf1b9072ffed30678a748` | identical | **PASS** |
| 2 | inputs | `legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` | `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` | SHA-256 | `064b6fdc5afe41e9a5e3a1480206c06195ffcaa6077ae4f7f081932024e3597c` | identical | **PASS** |
| 3 | inputs | `field_provenance_v1.csv` | `data/provenance/field_provenance_v1.csv` | SHA-256 | `9a07aa1e0dc4bca43e160459db7a0985bc99a08454fe51437481bb2f7af4d482` | identical | **PASS** |
| 4 | inputs | `anchor_set_v1.json` | `data/anchors/anchor_set_v1.json` | SHA-256 | `a0a3968b2861e78134c2376b0c577224ff8c9cf08febb68b6b16293a4b26fb2e` | identical | **PASS** |
| 5 | inputs | `legacy_matlab_site_meta.csv` | `data/inputs/legacy_matlab_site_meta.csv` | SHA-256 | `1b4255976b75429beb5fbd23c90b40ae480c5557564bf12e262e4fbd9831ff5a` | identical | **PASS** |
| 6 | tables | `schema.json` | `data/contract/v1/schema.json` | SHA-256 | `fb08b84ad2fd038ed82e3afacc251260b48bfebdfc4bc7621a5ef84e90cb0814` | identical | **PASS** |
| 7 | tables | `scenario_table.csv` | `data/contract/v1/scenario_table.csv` | SHA-256 | `a40358883265eb25649c0047b62ad6fad21eaf4936205a25a3814771f2e86aef` | identical | **PASS** |
| 8 | tables | `site_table.csv` | `data/contract/v1/site_table.csv` | SHA-256 | `0ed5e4ec7078f9cc9316827d48b86f4fab4b946b87a683b1f0f65977ee517790` | identical | **PASS** |
| 9 | tables | `source_provenance.csv` | `data/contract/v1/source_provenance.csv` | SHA-256 | `2d346861cf6216fb9b1f5c4500f8fe30c65411204d9c18fd1bbfd047a0efd875` | identical | **PASS** |
| 10 | tables | `standards_register.csv` | `data/contract/v1/standards_register.csv` | SHA-256 | `943f5b8fd60349c0a2eb9104162e49d18a00a53dc2f4489e5e0e3f07fac327fc` | identical | **PASS** |
| 11 | tables | `assumptions.json` | `data/contract/v1/assumptions.json` | SHA-256 | `0ef70e9b59727eb27ccc1358fe577610b116fc6f1a5b5c332a03cb61350e1289` | identical | **PASS** |

**11 of 11 PASS. Zero drift.** The committed contract byte-for-byte matches the manifest recorded at run
`milestone2_v3_20260719T052322Z`. This is the strongest artifact in the repository.

**But note the gap:** `verify_hash_chain()` (`src/fcf_m2/contract.py:315-324`) iterates **only `manifest["tables"]`**.
The five `inputs` hashes are recorded but **never re-verified by RT-10**. Input drift is silently undetectable by
`make validate`. (I verified them by hand here; the tooling does not.)

### 0.2 The 58.8 headline — DOES NOT TRACE TO `data/contract/v1/`

Exhaustive `grep` for `58.8` across `data/` returns exactly **one** hit:

```
data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2:
FFX002,City of Fairfax Regional Library,1,58.8,medium,6.0,1,1,1,57.8,55.8,52.8,0,...
```

Column mapping for that line: `base_rank=1`, **`base_readiness_score=58.8`**, `electrical_risk_level=medium`,
`electrical_risk_points=6.0`, `optimistic_rank=1`, `expected_rank=1`, `conservative_rank=1`,
`optimistic_score=57.8`, `expected_score=55.8`, `conservative_score=52.8`, `worst_case_rank_change=0`.

- **There is no `readiness_score` column anywhere in `data/contract/v1/`.** Not in `scenario_table.csv`
  (48 columns, all enumerated below), not in `site_table.csv` (9 columns), not in `schema.json`'s 48 required fields.
- 58.8 therefore originates in a **frozen legacy_v2 output** carried as a tracked *input*, and is re-published in a
  *generated dashboard artifact* (`dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2`), which also
  carries the subscore decomposition: `demand_subscore=42.73769092061847`, `feasibility_subscore=60.0`,
  `safety_subscore=90.0`, `equity_subscore=81.14186851211073`,
  `recommendation_tier="Tier 1 — advance to site screening"`.
- Every prose citation of 58.8 (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/migration-from-v2.md`,
  `docs/operations/reproduction-guide.md`, `docs/operations/legacy-baseline/BASELINE_VERIFICATION.md`,
  `docs/operations/website-patch-package/content/methodology_update.md`, `.github/pull_request_template.md`,
  `presentation/deck/*Speaker_Notes.md`, `presentation/deck/*Timing_Runbook.md`,
  `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`, `scripts/build_static_dashboard.py`,
  `tests/fixture_legacy_v2_*.csv`, `tests/test_legacy_golden.py`) therefore quotes a **legacy_v2 number**, not a
  contract number — even though `data/contract/v1/README.md:20` and `contract_manifest.json:48` instruct consumers to
  quote contract values only. **This is the single largest traceability defect in the lane.**

### 0.3 FFX002 confidence — the expected "Medium" is NOT what the data says

- In `data/contract/v1/scenario_table.csv`, **all 10 FFX002 rows carry `data_confidence=Low`**. So do all 120 rows.
- In `dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2`, FFX002 is
  `data_confidence_score_v3=33.8`, **`data_confidence_level_v3=Low`**.
- The only "medium" attached to FFX002 anywhere in the data layer is
  `electrical_risk_level=medium` (with `electrical_risk_points=6.0`) in the frozen legacy file.
- **Conclusion:** the brief's "expect Medium" is a *different variable* (electrical risk level), not data confidence.
  If any prose says "FFX002 … Medium confidence" it is conflating electrical-risk-level with data-confidence and is
  a defect. Contract truth: FFX002 data confidence = **Low**.

### 0.4 The two program-critical claims — BOTH CONFIRMED

| Claim | Verdict | Actual count | Evidence |
|---|---|---|---|
| `capacity_basis == placeholder` at 12 of 12 sites | **CONFIRMED** | **12 / 12** (and 120/120 rows) | `scenario_table.csv` col 29 has exactly one distinct value: `placeholder` |
| 0 of 12 sites reach `High` data_confidence | **CONFIRMED, and stronger than claimed** | **0 / 12 High; 0 / 12 Medium; 12 / 12 Low** | `scenario_table.csv` col 42 distinct value set = `{'Low'}` |

Reinforcing evidence, all independently confirmed:
- `capacity_confidence` distinct set = `{'none'}` (120/120).
- `service_capacity_kw` blank on **all 120 rows**; `spare_capacity_kw` blank on **all 120 rows**.
- `capacity_source` is the same string on all 120 rows:
  `"legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)"`.
- `assumptions.json:86`: `"capacity": "service/spare capacity NULL with capacity_basis=placeholder at all 12 sites until utility/facility confirmation"`.
- `real_sites_v2.csv`: `elec_service_rating_amp` and `spare_capacity_kw` are `0` at all 12 sites.
- `field_provenance_v1.csv` / `source_provenance.csv`: `electrical_service` = `unconfirmed`, `unresolved_flag=1` at all 12 sites.

### 0.5 eGRID / CO2e factors — every occurrence in the data layer

| Value | Units | Where (file:line) | Context |
|---|---|---|---|
| **596.3** | lb CO2e/MWh | `data/contract/v1/contract_manifest.json:27` | `grid_factor.value_lb_per_mwh` |
| **596.3** | lb CO2e/MWh | `data/contract/v1/schema.json:266` | `grid_factor_value` declared as JSON-Schema **`const`** — hard-locked |
| **596.3** | lb CO2e/MWh | `data/contract/v1/assumptions.json:64` | `emissions.grid_factor_value` |
| **596.3** | lb CO2e/MWh | `data/contract/v1/scenario_table.csv` col 38 | identical on **all 120 rows** |
| 294.0 | kg | `assumptions.json:60` | `emissions.grid_emissions_kg` for a 1000 kWh reference block |
| 1333.3 | kg | `assumptions.json:61` | `emissions.displaced_tailpipe_kg` |
| 1039.3 | kg | `assumptions.json:62` | `emissions.net_co2e_avoided_kg` |
| 0.3 kWh/mi | — | `assumptions.json:69` | EV efficiency benchmark |
| 400.0 gCO2/mi | — | `assumptions.json:69` | displaced gasoline LDV fleet-average benchmark |
| 0.92 | — | `assumptions.json:69` | charger efficiency |
| 0.0 | share | `assumptions.json:63` | `renewable_matched_share` |

Source string, identical in `contract_manifest.json:26` and `assumptions.json:66`:
`"EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, total output emission rate CO2e"`.
Vintage, identical in `contract_manifest.json:28`, `assumptions.json:67`, and all 120 `grid_factor_vintage` cells:
`"eGRID2023r2, accessed 2026-07-19"`. Units string is `"lb CO2e/MWh"` everywhere, locked as `const` in `schema.json:269`.

**590.2 does NOT appear anywhere under `data/`.** Repo-wide it survives in 4 documentation locations, and in all four
it is explicitly narrated *as the superseded value* (`CHANGELOG.md:24`, `docs/methodology/current-facts-source-register.md:7`,
`reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`,
`reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22`). Those are correction notes, not live values — but the brief's
standard is "must survive NOWHERE", so Phase 1 must make an explicit keep-or-scrub decision. The data layer is clean.

### 0.6 Horizon convention — data layer is CLEAN

- `scenario_table.csv` `horizon_year` distinct set = **`{2026, 2036, 2046, 2056}`** — exactly canonical.
  Counts: 2026 ×12 (baseline only), 2036 ×36, 2046 ×36, 2056 ×36.
- `schema.json:90-97` locks `horizon_year` to the enum `[2026, 2036, 2046, 2056]`.
- `contract_manifest.json:31-36`: `baseline_year: 2026`, `horizons: [2036, 2046, 2056]`.
- Programmatic scan for standalone `2035` / `2050` tokens across all 120 × 48 cells: **zero hits.** The apparent
  `grep` hits were decimals (`utilization=0.2035` at `scenario_table.csv:44`, etc.).
- The **only** `2035`/`2050` occurrence in `data/` is `assumptions.json:11`, and it is a **correctly labelled legacy
  reference**, not stale text:
  `"2036 re-anchors the legacy 2035 cases; 2046 inherits the legacy 2050 cases on the evidence that regional adoption is front-loaded; 2056 extends with saturation capped by pathway capacity."`
  This is legitimate and should be preserved.
- **Caveat (low severity):** `horizon_label` carries relative-offset naming `now / plus10 / plus20 / plus30`
  (`schema.json:98-105`; `scenario_table.csv` col 10). Anchored on 2026 these are arithmetically consistent
  (2026+10=2036 etc.), so it is not a convention violation — but the token `now` and the 10/20/30 offsets are exactly
  the shapes the program is trying to purge from prose. Any downstream artifact that surfaces `horizon_label` raw to
  a reader will render "Now / +10 / +20 / +30" instead of absolute years. Phase 1 should decide whether to keep the
  column or force absolute-year display.

### 0.7 Secrets / absolute paths

Scanned all `data/` text files for `/Users/`, `/home/`, `AKIA`, `aws_secret`, `api_key`, `password`, `secret`,
`token`, `arn:aws`, and 12-digit account IDs. **Zero matches.** Consistent with `data/README.md:27-28`
("no personal data, credentials, or private stakeholder contact details are tracked anywhere in this repository").
No PII: the site set is public civic facilities; the only addresses are public building addresses.

---

## 1. FILE-BY-FILE INVENTORY

### `data/README.md`
- **Role:** Classification index for the `data/` tree — declares which subtrees are tracked inputs, tracked reference, or gitignored generated output, and states the contract in one paragraph.
- **Kind:** authored (Markdown, 29 lines).
- **Reads:** n/a (prose).
- **Written by / read by:** Hand-authored. Read by humans; linked from repo-root `README.md` via `[← repository root](../../../../README.md)` (line 3 — **link target verified to exist**).
- **Key contents:** Classification table (lines 7-17) covering 9 paths. `inputs/real_sites_v2.csv` = "12 candidate sites, 40 fields (team snapshot 2026-06-24)" — **both numbers verified: exactly 12 rows, exactly 40 columns.** `anchors/anchor_set_v1.json` flagged "changing this changes scores". `contract/v1/` labelled "**the canonical cross-model contract**". `outputs/` = "generated output — **no (gitignored)**", reproduce with `make run-legacy` / `make run-v3`. Contract paragraph (lines 21-25): "120 rows = 12 sites × {2026 baseline; 2036/2046/2056 × base/high/stress}" — **arithmetic verified: 12 × (1 + 3×3) = 120 ✓**. "`capacity_basis` is `placeholder` on every row — machine-readable proof that no electrical capacity has been verified" — **verified**. "Validate any time with `make validate` (rules, JSON Schema, and the RT-10 manifest hash chain)."
- **Notes:** All referenced artifacts verified to exist: `data/outputs/` is genuinely absent and genuinely gitignored (`.gitignore:11`); Makefile targets `run-legacy` (line 11), `run-v3` (line 14), `validate` (line 17) all exist. Uses canonical horizons only. **One omission:** the table does not mention `data/observed/`'s sibling status vs `data/provenance/site_coordinate_sources.csv` and `v2_source_confidence_tracker.csv`, which are lumped under a single `provenance/` row; those two files are materially incomplete (see their entries) and the README's flat "tracked reference — typed field-level provenance driving data confidence" oversells them.

### `data/anchors/anchor_set_v1.json`
- **Role:** Versioned fixed scoring anchors (lo/hi bounds per normalised field) so that adding or removing a candidate site cannot change an existing site's score.
- **Kind:** data-contract (hand-curated reference; hashed as manifest input #4).
- **Reads:** n/a (leaf reference data).
- **Written by / read by:** Hand-authored. Consumed by the V3 scoring path in `fcf_m2`; hashed into `contract_manifest.json:14`.
- **Key contents:** `anchor_set_version = "anchors_v1_2026-07"` (line 2); `created = "2026-07-19"` (line 3); `status = "proposed_v3_baseline (adopted inside the implementation package; team ratification recorded in decision log)"` (line 4). Method (line 5): fixed benchmarks derived from the frozen 2026-07 12-site cohort, **rounded OUTWARD** so every current site scores inside [0,1] and cohort membership cannot shift scores. `fallback_rule` (line 6): missing anchor ⇒ fall back to cohort min-max and emit `anchor_fallback_fields`; "Fallback use is a validation warning, not a silent default." **13 anchors** (lines 8-20), all `lo: 0`:
  | field | hi | stated cohort note |
  |---|---|---|
  | `nearby_households_1mi` | 12000 | cohort max 9866 |
  | `nearby_jobs_1mi` | 40000 | cohort max 31611 |
  | `aadt_nearest` | 60000 | cohort max 51000 |
  | `amenities_count_0_5mi` | 8 | cohort max 6 |
  | `parking_spaces` | 1500 | cohort max 1400 (garage) |
  | `avg_dwell_min` | 300 | cohort max 240 |
  | `existing_ports_total` | 130 | cohort max 122 combined |
  | `spare_capacity_kw` | 200 | all cohort values 0 (unconfirmed) |
  | `distance_to_service_ft` | 300 | cohort range 75-150 |
  | `trenching_ft` | 250 | cohort range 50-125 |
  | `install_cost_est_usd` | 100000 | cohort max 63750 (derived field) |
  | `equity_gap_index` | 1.0 | index already 0-1 constructed |
  | `ev_share_local` | 0.10 | legacy fixed benchmark `EV_SHARE_HIGH_BENCHMARK` retained |
- **Notes:** **I cross-checked all 13 cohort claims against `real_sites_v2.csv` and 12 of 13 are exactly right** — households 9866 (FFX004), jobs 31611 (FFX004), AADT 51000 (PWC001), amenities 6, parking 1400 (PWC002), dwell 240 (PWC002), ports 62+60=122 (PWC002), spare capacity all 0, distance 75-150, trenching 50-125, equity max 0.769 ≤ 1.0, ev_share max 0.023 ≤ 0.10. The 13th (`install_cost_est_usd` max 63750) is a **derived** field not present in `real_sites_v2.csv`, so it is unverifiable from the data layer alone — label uncertain. This file is unusually well-disciplined. Status line 4 is a *soft* adoption claim ("proposed_v3_baseline … team ratification recorded in decision log") — a later phase should confirm that decision-log entry actually exists.

### `data/contract/v1/README.md`
- **Role:** Consumer-facing spec for the canonical contract directory — names producer, consumers, files, and the four binding consumer rules.
- **Kind:** **generated** — emitted verbatim by `_write_readme()` at `src/fcf_m2/contract.py:327+`. Not hand-editable without regenerating.
- **Reads:** n/a.
- **Written by / read by:** Written by `fcf_m2.contract.write_contract` → `_write_readme`. Read by MATLAB/Excel/Tableau/presentation integrators.
- **Key contents:** Producer `fcf_m2` (Python V3); consumers "MATLAB/Simulink V3, Excel workbook, Tableau exports, static visuals, presentation" (line 3). File table (lines 7-14). Line 9 states the grid explicitly: "site x horizon (**2026/2036/2046/2056**) x case (baseline/base/high/stress_combined)" — canonical. Four consumer rules (lines 17-20): (1) "Join on `site_id` only — never on names."; (2) capacity placeholder-vs-verified label MUST propagate unless basis is `verified_utility`/`verified_facility`; (3) "Presentation numbers cite `contract_version` + `generated_utc` from the manifest."; (4) validation command `python -m fcf_m2.workflow validate-contract <dir>`. Closing disclaimer (line 22): "All values are planning-support outputs. Nothing here is an engineering, permitting, budget, or procurement value."
- **Notes:** The CLI at line 20 **exists and is wired**: `src/fcf_m2/workflow.py:5` (docstring), `:357` (`sub.add_parser("validate-contract")`), `:367` (dispatch). Rule 3 is the rule the 58.8 headline violates (§0.2) — the contract has no readiness score to cite, yet the whole program quotes one. Rule 1 is honoured by the data: I verified `site_name` matches between `site_table.site_name_display` and `scenario_table.site_name` for **all 12 sites**, so a name-join would coincidentally work today — but the rule exists because that is fragile.

### `data/contract/v1/assumptions.json`
- **Role:** Every labelled modelling assumption with its value, status, and provenance — the epistemics ledger of the model.
- **Kind:** generated (`json.dumps(assumptions, indent=2)` at `src/fcf_m2/contract.py:280`); hashed as table #6.
- **Reads:** n/a.
- **Written by / read by:** Written by `fcf_m2.contract.write_contract`; read by consumers and quoted by reports.
- **Key contents:**
  - **`growth_multipliers`** (lines 2-10): `2026_baseline 1.0`, `2036_base 1.9`, `2036_high 2.6`, `2046_base 3.0`, `2046_high 4.5`, `2056_base 4.0`, `2056_high 6.0`.
  - **`growth_provenance`** (line 11): "Provisional planning convention (research Report 05 s3): 2036 re-anchors the **legacy 2035** cases; 2046 inherits the **legacy 2050** cases on the evidence that regional adoption is front-loaded; 2056 extends with saturation capped by pathway capacity. Status: **synthetic_uncalibrated** — pending team adoption and observed-data calibration." *(This is the legitimate labelled-legacy horizon reference — keep it.)*
  - **`stress_extra_multiplier`** = `1.15` (line 12).
  - **`demand_model`** (13-27): `status = "synthetic_uncalibrated"`; coefficients `visitors_day 0.0015`, `employees_day 0.0006`, `nearby_jobs_1mi 2e-05`, `nearby_households_1mi 3e-05`; `floor_sessions 0.3`; provenance: "Coefficients are synthetic screening values chosen by the team for the V2 prototype; **no published derivation exists. They must not be presented as calibrated.** Calibration path: `fcf_m2.demand.calibrate()` with observed session data."; **`calibrated_at: null`, `calibration_metrics: null`, `n_observed_rows: 0`, `n_observed_sites: 0`.**
  - **`base_load_growth_per_year`** = `0.008` (line 29), labelled a planning proxy pending facility interval data.
  - **`energy_per_session_kwh`** = `9.5` (line 33), "benchmark assumption (typical public L2 session), TBV with observed data".
  - **`economics`** (36-56): `hardware_usd_per_port 6500.0`, `install_soft_cost_share 0.25`, `pathway_premium_share 0.15`, `retrofit_civil_multiplier 1.8`, `network_fee_usd_per_port_yr 1000.0`, `maintenance_usd_per_port_yr 400.0`, `tariff_usd_per_kwh 0.11`, `demand_charge_usd_per_kw_month 0.0`, `replacement_usd_per_port 2500.0`, `replacement_year_offset 10`, `decommission_usd_per_port 800.0`, `inspection_admin_usd_per_site_yr 300.0`, `contingency_civil_share 0.25`, `discount_rate_real 0.03`, `escalation {low 0.01, base 0.025, high 0.04}`. Provenance: "screening/planning benchmarks (AFDC/NREL cost classes + client operating evidence). **None are quotes, budgets, or engineering estimates.** Site quotes, the Dominion tariff, and vendor fee schedules are required before any budget use."
  - **`emissions`** (58-70): see §0.5. Assumption note (line 69) ends "**No observed baseline exists yet — values are screening estimates, not measured reductions.**"
  - **`trigger_policy`** (71-85): `policy_status = "proposed_default_pending_team_and_client_adoption"`; `utilization_threshold 0.4`; `wait_threshold_min 10.0`; `reliability_uptime_min 0.97`; `min_observation_months 6`; `equity_override {enabled: true, equity_index_percentile_min 0.6, reduced_utilization_threshold 0.25}`; `budget_gate "human_approval_required"`; `pathway_gate "ports_active_plus_step_must_not_exceed_ports_pathway"`.
  - **`capacity`** (line 86): the 12-site placeholder statement quoted in §0.4.
- **Notes:** `discount_rate_real 0.03` appears **twice** and agrees: `assumptions.json:50` and `contract_manifest.json:43`. Consistent. **Phase-4 hook:** `n_observed_rows: 0` / `n_observed_sites: 0` / `calibrated_at: null` is the machine-readable statement that **calibration has never run** — any later claim that the demand model is calibrated contradicts this file. **Phase-3/6 hook:** `utilization_threshold 0.4` vs observed utilisation in the contract, which peaks at only `0.2035` (PWC002 2036_high) — no site anywhere in the 120-row table reaches the expansion trigger, which is coherent with `expansion_trigger_status = "awaiting_observed_data (proposed policy, not adopted)"` on all 120 rows.

### `data/contract/v1/contract_manifest.json`
- **Role:** Version stamp, provenance, hash manifest, grid factor, horizon/case conventions, and consumer rules for the contract directory.
- **Kind:** generated (`src/fcf_m2/contract.py:284-310`).
- **Reads:** Records digests of 5 input files and 6 table files (see §0.1).
- **Written by / read by:** Written by `write_contract`; read by `verify_hash_chain()` (RT-10) and by every consumer that must cite `contract_version` + `generated_utc`.
- **Key contents:** `contract_version "1.0.0"`; `model_version "3.0.0"`; `run_id "milestone2_v3_20260719T052322Z"`; `generated_utc "2026-07-19T05:23:22.507266+00:00"`; `producer {package: "fcf_m2", module: "fcf_m2.contract"}`. `inputs` = 5 SHA-256s; `tables` = 6 SHA-256s (all listed and all PASS in §0.1). `grid_factor` = 596.3 lb/MWh, eGRID2023r2, SRVC. `conventions` = `baseline_year 2026`, `horizons [2036, 2046, 2056]`, `cases ["base","baseline","high","stress_combined"]`, `discount_rate_real 0.03`. `consumer_rules` = 4 strings (lines 46-49) including "MATLAB refuses feasibility claims when capacity_basis is not verified_utility/verified_facility."
- **Notes:** (a) **File has no trailing newline** (ends `}` at line 51 with no `\n`) — cosmetic, but any tool that appends will corrupt it. (b) `generated_utc` = `...05:23:22.507266Z` while `scenario_table.generated_at` = `...05:23:22.201169Z` — a 306 ms gap, expected (table built first, manifest stamped last). Not a defect, but they are **different fields with different values**, so an artifact citing "generated at" must say which. (c) RT-10 verifies `tables` only, never `inputs` — see §0.1. (d) `cases` is `sorted(VALID_CASES)`, which is why `"baseline"` sorts between `"base"` and `"high"` rather than appearing first — harmless but reads oddly.

### `data/contract/v1/schema.json`
- **Role:** JSON Schema (draft 2020-12) for a single `scenario_table` row — the machine-enforced type/constraint contract.
- **Kind:** generated (`build_schema()` at `src/fcf_m2/contract.py:72+`, written line 275); hashed as table #1.
- **Reads:** n/a.
- **Written by / read by:** Written by `write_contract`; enforced by `validate_against_json_schema` before the contract is allowed to be written (`contract.py:271-273` raises `ContractValidationError`).
- **Key contents:** `title = "FCF M2 canonical scenario row"`, `type: object`. **48 required fields** (lines 5-54) — exactly matching the 48 CSV columns, in the same order. Full field/type/constraint list:

  | # | field | type / constraint |
  |---|---|---|
  | 1 | `contract_version` | `const: "1.0.0"` |
  | 2 | `run_id` | string, `minLength: 8` |
  | 3 | `generated_at` | string |
  | 4 | `site_id` | string, `pattern: "^(FFX\|PWC)[0-9]{3}$"` |
  | 5 | `site_name` | string, `minLength: 3` |
  | 6 | `jurisdiction` | enum `["fairfax","pwc"]` |
  | 7 | `site_type` | string |
  | 8 | `public_or_fleet` | enum `["public","fleet","mixed"]` |
  | 9 | `horizon_year` | enum `[2026, 2036, 2046, 2056]` |
  | 10 | `horizon_label` | enum `["now","plus10","plus20","plus30"]` |
  | 11 | `scenario_id` | string, `minLength: 5` |
  | 12 | `scenario_name` | string |
  | 13 | `model_mode` | enum `["legacy_v2","milestone2_v3"]` |
  | 14 | `ports_active` | integer, 0-100 |
  | 15 | `ports_pathway_capacity` | integer, 0-100 |
  | 16 | `evse_power_kw` | number, `exclusiveMinimum: 0`, max 5000 |
  | 17 | `sessions_per_day` | number, min 0 |
  | 18 | `energy_per_session_kwh` | number, 0-1000 |
  | 19 | `energy_required_kwh_day` | number, min 0 |
  | 20 | `charging_window_hr` | number, 0-24 |
  | 21 | `average_dwell_hr` | number, 0-24 |
  | 22 | `peak_factor` | number, 0-10 |
  | 23 | `utilization` | number\|null, 0-2 |
  | 24 | `average_wait_minutes` | number\|null, min 0 |
  | 25 | `peak_wait_minutes` | number\|null, min 0 |
  | 26 | `base_load_kw` | number\|null, 0-5000 |
  | 27 | `service_capacity_kw` | number\|null, 0-5000 |
  | 28 | `spare_capacity_kw` | number\|null, 0-5000 |
  | 29 | `capacity_basis` | enum `["verified_utility","verified_facility","engineering_estimate","planning_proxy","placeholder","unknown"]` |
  | 30 | `capacity_source` | string, `minLength: 3` |
  | 31 | `capacity_confidence` | enum `["high","medium","low","none"]` *(lowercase)* |
  | 32 | `managed_charging_policy` | enum `["none","clamp","energy_aware"]` |
  | 33 | `energy_delivered_kwh` | number, min 0 |
  | 34 | `energy_curtailed_kwh` | number, min 0 |
  | 35 | `lifecycle_cost_nominal_usd` | number\|null, min 0 |
  | 36 | `lifecycle_cost_npv_usd` | number\|null, min 0 |
  | 37 | `avoided_overbuild_cost_usd` | number\|null *(no bound — may be negative)* |
  | 38 | `grid_factor_value` | **`const: 596.3`** |
  | 39 | `grid_factor_units` | **`const: "lb CO2e/MWh"`** |
  | 40 | `grid_factor_vintage` | string, `minLength: 5` |
  | 41 | `net_co2e_kg` | number\|null |
  | 42 | `data_confidence` | enum `["High","Medium","Low"]` *(Capitalised)* |
  | 43 | `equity_indicator` | number\|null, 0-1 |
  | 44 | `expansion_trigger_status` | string |
  | 45 | `source_date` | string, `minLength: 8` |
  | 46 | `source_id` | string, `minLength: 2` |
  | 47 | `assumption_flag` | string |
  | 48 | `notes` | string |
- **Notes:** (a) **`grid_factor_value` as `const: 596.3` is the single strongest guard in the repo** — any attempt to reintroduce 590.2 into the contract fails schema validation at write time. Phase 1 should point at `schema.json:266` as the enforcement mechanism. (b) **Casing inconsistency, load-bearing for consumers:** `capacity_confidence` uses lowercase `high/medium/low/none` while `data_confidence` uses capitalised `High/Medium/Low`. Two different casing conventions for the same concept in adjacent columns — a naive consumer comparing `== "Low"` against `capacity_confidence`, or `== "low"` against `data_confidence`, silently fails. (c) `avoided_overbuild_cost_usd` is deliberately unbounded and **is negative in real data** (e.g. `-11145.0` for PWC002 2036_high at `scenario_table.csv:44`) — meaning overbuild avoidance can be a net *cost*; any dashboard rendering this as a "savings" bar will mislead. (d) `model_mode` enum admits `legacy_v2`, but no row in the contract uses it (all 120 are `milestone2_v3`) — the legacy lane is schema-reachable but unpopulated. (e) `horizon_label` enum `now/plus10/plus20/plus30` — see §0.6 caveat.

### `data/contract/v1/scenario_table.csv`
- **Role:** THE canonical fact table — site × horizon × case, the single source of truth consumed by MATLAB, Excel, Tableau, the dashboard, and the presentation.
- **Kind:** generated (`scenario_table.to_csv(..., index=False)` at `src/fcf_m2/contract.py:276`); hashed as table #2.
- **Reads:** derived from `real_sites_v2.csv` + frozen legacy v2 outputs + `anchor_set_v1.json` (per its own `source_id` column).
- **Written by / read by:** Written by `fcf_m2.contract.write_contract`. Read by every downstream consumer.
- **Key contents:**
  - **121 lines = 1 header + exactly 120 data rows.** ✅ **CONFIRMED 120.** LF line endings, trailing newline present.
  - **48 columns, in this exact order:** `contract_version`, `run_id`, `generated_at`, `site_id`, `site_name`, `jurisdiction`, `site_type`, `public_or_fleet`, `horizon_year`, `horizon_label`, `scenario_id`, `scenario_name`, `model_mode`, `ports_active`, `ports_pathway_capacity`, `evse_power_kw`, `sessions_per_day`, `energy_per_session_kwh`, `energy_required_kwh_day`, `charging_window_hr`, `average_dwell_hr`, `peak_factor`, `utilization`, `average_wait_minutes`, `peak_wait_minutes`, `base_load_kw`, `service_capacity_kw`, `spare_capacity_kw`, `capacity_basis`, `capacity_source`, `capacity_confidence`, `managed_charging_policy`, `energy_delivered_kwh`, `energy_curtailed_kwh`, `lifecycle_cost_nominal_usd`, `lifecycle_cost_npv_usd`, `avoided_overbuild_cost_usd`, `grid_factor_value`, `grid_factor_units`, `grid_factor_vintage`, `net_co2e_kg`, `data_confidence`, `equity_indicator`, `expansion_trigger_status`, `source_date`, `source_id`, `assumption_flag`, `notes`.
  - **12 distinct `site_id`, 10 rows each:** `FFX001, FFX002, FFX003, FFX004, PWC001, PWC002, PWC003, PWC004, PWC005, PWC006, PWC007, PWC008`.
  - **Horizons:** `2026 ×12`, `2036 ×36`, `2046 ×36`, `2056 ×36`. ✅ **CONFIRMED 2026/2036/2046/2056.**
  - **`horizon_label`:** `now ×12`, `plus10 ×36`, `plus20 ×36`, `plus30 ×36`.
  - **`scenario_name` (cases):** `baseline ×12`, `base ×36`, `high ×36`, `stress_combined ×36`.
  - **`model_mode`:** `milestone2_v3` ×120 (single value — **no legacy_v2 rows exist**).
  - **`scenario_id`:** 120 distinct, pattern `{site_id}_{year}_{case}`.
  - **Constant-across-all-120 columns:** `contract_version 1.0.0`; `run_id milestone2_v3_20260719T052322Z`; `generated_at 2026-07-19T05:23:22.201169+00:00`; `energy_per_session_kwh 9.5`; `capacity_basis placeholder`; `capacity_source` (the 12/12-unconfirmed string); `capacity_confidence none`; `managed_charging_policy none`; `energy_curtailed_kwh 0.0`; `grid_factor_value 596.3`; `grid_factor_units "lb CO2e/MWh"`; `grid_factor_vintage "eGRID2023r2, accessed 2026-07-19"`; `data_confidence Low`; `expansion_trigger_status "awaiting_observed_data (proposed policy, not adopted)"`; `source_date 2026-06-24`; `source_id "real_sites_v2+frozen_v2_outputs+anchors_v1"`; `assumption_flag "growth multipliers provisional; demand synthetic_uncalibrated; capacity placeholder; costs screening-class; emissions benchmark assumptions"`.
  - **Always blank:** `service_capacity_kw` (120/120), `spare_capacity_kw` (120/120).
  - **Blank on the 12 baseline rows only:** `lifecycle_cost_nominal_usd`, `lifecycle_cost_npv_usd`, `avoided_overbuild_cost_usd` (all 12 blanks are `horizon_year == 2026`).
  - **`jurisdiction`:** `pwc ×80`, `fairfax ×40`. **`site_type`:** `library ×70`, `office ×30`, `garage ×10`, `public_safety ×10`. **`public_or_fleet`:** `public ×110`, `mixed ×10` (the `mixed` decade is PWC003, the public-safety site).
  - **All 10 FFX002 rows** (traced in full for the 58.8 investigation):

    | scenario_id | horizon | label | case | ports_active | pathway | evse_kw | sessions/day | kWh/day | util | avg_wait | peak_wait | base_load_kw | energy_delivered | LC nominal | LC NPV | avoided_overbuild | net_co2e_kg | equity | data_conf |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    | FFX002_2026_baseline | 2026 | now | baseline | 2 | 8 | 19.2 | 1.16 | 11.02 | 0.0936 | 0.8 | 1.31 | 51.4 | 4022.3 | *(blank)* | *(blank)* | *(blank)* | 4180.5 | 0.66 | Low |
    | FFX002_2036_base | 2036 | plus10 | base | 4 | 8 | 19.2 | 2.203 | 20.93 | 0.0889 | 0.01 | 0.03 | 55.7 | 7639.4 | 151901.0 | 133641.0 | 113561.0 | 7939.9 | 0.66 | Low |
    | FFX002_2036_high | 2036 | plus10 | high | 6 | 8 | 19.2 | 3.015 | 28.64 | 0.0811 | 0.0 | 0.0 | 55.7 | 10453.6 | 151901.0 | 133641.0 | 113561.0 | 10864.8 | 0.66 | Low |
    | FFX002_2036_stress_combined | 2036 | plus10 | stress_combined | 6 | 8 | 19.2 | 3.468 | 32.94 | 0.0933 | 0.0 | 0.0 | 55.7 | 12023.1 | 151901.0 | 133641.0 | 113561.0 | 12496.0 | 0.66 | Low |
    | FFX002_2046_base | 2046 | plus20 | base | 6 | 8 | 19.2 | 3.479 | 33.05 | 0.0936 | 0.0 | 0.0 | 60.3 | 12063.2 | 304075.0 | 227176.0 | 136940.0 | 12537.7 | 0.66 | Low |
    | FFX002_2046_high | 2046 | plus20 | high | 8 | 8 | 19.2 | 5.219 | 49.58 | 0.1053 | 0.0 | 0.0 | 60.3 | 18096.7 | 304075.0 | 227176.0 | 136940.0 | 18808.6 | 0.66 | Low |
    | FFX002_2046_stress_combined | 2046 | plus20 | stress_combined | 8 | 8 | 19.2 | 6.001 | 57.01 | 0.1211 | 0.0 | 0.0 | 60.3 | 20808.6 | 304075.0 | 227176.0 | 136940.0 | 21627.1 | 0.66 | Low |
    | FFX002_2056_base | 2056 | plus30 | base | 6 | 8 | 19.2 | 4.639 | 44.07 | 0.1248 | 0.0 | 0.01 | 65.3 | 16085.5 | 497500.0 | 317887.0 | 163058.0 | 16718.2 | 0.66 | Low |
    | FFX002_2056_high | 2056 | plus30 | high | 8 | 8 | 19.2 | 6.958 | 66.1 | 0.1404 | 0.0 | 0.0 | 65.3 | 24126.5 | 497500.0 | 317887.0 | 163058.0 | 25075.6 | 0.66 | Low |
    | FFX002_2056_stress_combined | 2056 | plus30 | stress_combined | 8 | 8 | 19.2 | 8.002 | 76.02 | 0.1615 | 0.0 | 0.0 | 65.3 | 27747.3 | 497500.0 | 317887.0 | 163058.0 | 28838.8 | 0.66 | Low |

    All 10 share: `site_name "City of Fairfax Regional Library"`, `jurisdiction fairfax`, `site_type library`, `public_or_fleet public`, `charging_window_hr 7.0`, `average_dwell_hr 1.5`, `peak_factor 1.277375`, `service/spare_capacity blank`, `capacity_basis placeholder`, `capacity_confidence none`, `equity_indicator 0.66`, and the note *"Strong ranking supports installing starter ports now while preparing pathway capacity for about 8 ports."*
- **Notes:** (a) **`58.8` appears nowhere in this file** — there is no readiness/score column at all. See §0.2. (b) **`data_confidence` is `Low` on all 10 FFX002 rows**, contradicting any "Medium" claim — see §0.3. (c) **A real modelling oddity that Phase 1 should look at: FFX002_2056_base has *fewer* ports (6) than FFX002_2046_high (8) and lower sessions/day (4.639) than 2046_high (5.219).** The base multiplier goes 2046→2056 as 3.0→4.0, so base demand does rise; but the 2046 *high* case (4.5×) exceeds the 2056 *base* case (4.0×). This is arithmetically correct but produces a non-monotonic-looking ports series when read down a single column, and will look like a bug on a chart that plots ports vs year without holding the case fixed. (d) The `notes` string is constant per site across all 10 rows, i.e. it is a *site-level* recommendation stored redundantly at scenario grain — a consumer that de-duplicates on `notes` gets 12 values, one per site. (e) `peak_factor 1.277375` is suspiciously high-precision for a planning proxy. (f) `utilization` never exceeds `0.2035` anywhere in the table, against a `utilization_threshold` of `0.4` — no site triggers expansion under the proposed policy.

### `data/contract/v1/site_table.csv`
- **Role:** Identity dimension — one canonical spelling and one canonical coordinate per site; the join key table.
- **Kind:** generated (`site_table.to_csv(..., index=False)` at `src/fcf_m2/contract.py:277`); hashed as table #3.
- **Reads:** derived from `real_sites_v2.csv`.
- **Written by / read by:** Written by `write_contract`; the mandated join target for all consumers (rule 1).
- **Key contents:** **9 columns:** `site_id, site_name_display, site_name_safe, jurisdiction, lat, lon, site_type, public_access, garage_enclosed`. **12 data rows** (lines 2-13), plus a trailing newline (line 14 empty). Rows are **not** in site_id order — file order is FFX004, FFX002, PWC002, PWC006, PWC007, FFX001, PWC004, PWC001, FFX003, PWC008, PWC005, PWC003 (this is descending readiness-rank order from the legacy file, i.e. the table is *sorted by a score it does not contain*).

  | line | site_id | site_name_display | jurisdiction | lat | lon | site_type | public_access | garage_enclosed |
  |---|---|---|---|---|---|---|---|---|
  | 2 | FFX004 | Fairfax County Government Center | fairfax | 38.85404 | -77.35706 | office | 1.0 | 0.0 |
  | 3 | FFX002 | City of Fairfax Regional Library | fairfax | 38.847072 | -77.30363 | library | 1.0 | 0.0 |
  | 4 | PWC002 | Neabsco-Potomac Commuter Garage | pwc | 38.631185 | -77.288802 | garage | 1.0 | **1.0** |
  | 5 | PWC006 | Bull Run Library | pwc | 38.78694 | -77.520529 | library | 1.0 | 0.0 |
  | 6 | PWC007 | Central Library | pwc | 38.768783 | -77.454823 | library | 1.0 | 0.0 |
  | 7 | FFX001 | Fairfax City Hall or municipal building | fairfax | 38.840974 | -77.308103 | office | 1.0 | 0.0 |
  | 8 | PWC004 | Chinn Park Regional Library | pwc | 38.67034 | -77.333127 | library | 1.0 | 0.0 |
  | 9 | PWC001 | PWC McCoart Government Center | pwc | 38.679705 | -77.352905 | office | 1.0 | 0.0 |
  | 10 | FFX003 | Pohick Regional Library | fairfax | 38.7749268 | -77.2680915 | library | 1.0 | 0.0 |
  | 11 | PWC008 | Potomac Library | pwc | 38.632723 | -77.2806337 | library | 1.0 | 0.0 |
  | 12 | PWC005 | Haymarket Gainesville Library | pwc | 38.836588 | -77.632135 | library | 1.0 | 0.0 |
  | 13 | PWC003 | Prince William County Public Safety Training Center | pwc | 38.663726 | -77.585658 | public_safety | **0.0** | 0.0 |

  `site_name_safe` is the underscore-slugged `site_name_display` for every row (e.g. `City_of_Fairfax_Regional_Library`).
- **Notes:** **THE BRIEF'S PREMISE IS WRONG HERE, and this matters.** `site_table.csv` contains **no `capacity_basis` column and no `data_confidence` column.** It is a pure identity dimension. Those two fields live at *scenario grain* in `scenario_table.csv` (cols 29 and 42). Both program claims are still fully confirmed (§0.4) — just from `scenario_table.csv`, not from `site_table.csv`. Any Phase-1 document that says "see `site_table.csv` for capacity_basis" is citing the wrong file. Other notes: (a) coordinate precision is wildly uneven — FFX003 and PWC008 carry 7 decimals (~1 cm), FFX004 carries 5 (~1 m) — reflecting mixed sourcing, not measurement. (b) `public_access = 0.0` only for PWC003, matching its `public_or_fleet = mixed` in `scenario_table` and its "public-access/use case is not fully confirmed" legacy risk reason. (c) `garage_enclosed = 1.0` only for PWC002, matching the `UL2202`/garage AHJ flags. (d) Booleans are stored as floats (`1.0`/`0.0`), a pandas round-trip artifact.

### `data/contract/v1/source_provenance.csv`
- **Role:** Field-level provenance with typed source classes — the machine-readable basis of the data-confidence story, published inside the contract.
- **Kind:** generated (`provenance.to_csv(..., index=False)` at `src/fcf_m2/contract.py:278`); hashed as table #4.
- **Reads:** derived from `data/provenance/field_provenance_v1.csv`.
- **Written by / read by:** Written by `write_contract`; read by consumers computing/ displaying data confidence.
- **Key contents:** **9 columns:** `site_id, field_group, source_class, verification_status, source_org, source_date, reviewer, assumption_type, unresolved_flag`. **84 data rows = 12 sites × 7 field_groups.** The 7 field groups, with their (identical-for-every-site) values:

  | field_group | source_class | source_org | assumption_type | unresolved_flag |
  |---|---|---|---|---|
  | `electrical_service` | `unconfirmed` | facility (pending) | electrical capacity unverified | **1** |
  | `safety_review_fields` | `unconfirmed` | team site assessment | "site-visit screening, not AHJ determination" | **1** |
  | `site_use_and_demand` | `derived_public_data` | facility pages / ACS / LODES extracts | public-data derivation | 0 |
  | `address_and_public_access` | `official_source` | facility/branch official pages | *(blank)* | 0 |
  | `coordinates` | `public_web_reference` | public web mapping (replace with official GIS) | *(blank)* | 0 |
  | `parking_and_layout` | `planning_assumption` | imagery/site visit count | unverified count | 0 |
  | `equity_and_context` | `derived_public_data` | ACS/LODES-derived equity index | *(blank)* | 0 |

  `verification_status` = `spot_checked` on **all 84 rows**. `source_date` = `2026-06-24` on all 84. `reviewer` = `team_v2_snapshot` on all 84. Site order: PWC001-004, FFX001-004, PWC005-008.
- **Notes:** (a) **This file is byte-different but content-identical to `data/provenance/field_provenance_v1.csv`.** I diffed them: the *only* difference is line endings — `field_provenance_v1.csv` is **CRLF** (85 CR bytes, 11470 bytes), `source_provenance.csv` is **LF** (0 CR bytes, 11385 bytes); 11470 − 11385 = 85 = the line count. After `tr -d '\r'` they are identical. So the same 84 facts are hashed **twice under two different digests** (`9a07aa1e…` as an input, `2d346861…` as a table). Duplication is by design (input snapshot vs published table) but the CRLF/LF divergence means the two hashes can never be compared, and a naive "did the provenance change?" check comparing digests will always report a difference. (b) **`verification_status` is `spot_checked` at 100 % uniformity across 84 rows** — it carries zero information and cannot distinguish a well-sourced site from a poorly-sourced one. (c) **`coordinates` is `public_web_reference` for all 12 sites here, which directly contradicts `data/provenance/site_coordinate_sources.csv`**, where 6 sites are marked `Official` with GIS-verified coordinates. See that file's entry.

### `data/contract/v1/standards_register.csv`
- **Role:** Standards applicability matrix — which standard applies to which site at which lifecycle stage, with adopted vs latest edition, required evidence, the responsible authority, and the open AHJ question.
- **Kind:** generated (`standards_register.to_csv(..., index=False)` at `src/fcf_m2/contract.py:279`); hashed as table #5.
- **Reads:** n/a (curated register expanded across the 12-site cohort).
- **Written by / read by:** Written by `write_contract`; read by the compliance/standards views in the dashboard and report.
- **Key contents:** **12 columns:** `site_id, standard_id, standard_title, role, stage, requirement, adopted_edition, latest_edition, applicability, evidence_required, authority, open_ahj_question`. **444 data rows = 12 sites × 37 rows per site** (identical 37-row block replicated verbatim for every site — I verified the per-site count is exactly 37 for all 12).
  - **9 distinct `standard_id`** (row counts across the whole file): `UL2594 ×72` (6 stages), `ACCESS-BOARD-EVSE ×60`, `NEC625 ×60`, `OCPP-ISO15118 ×60`, `UL3600 ×60`, `VA-USBC-SFPC ×60` (5 stages each), `UL2231 ×48` (4 stages), `UL2202 ×12`, `UL9540-9540A-NFPA855 ×12` (1 row each).
  - **5 distinct `role`:** `supporting_essential ×228`, `highlighted_safety ×72` (UL2594), `highlighted_sustainability ×60` (UL3600), `supporting_protocol ×60` (OCPP/ISO15118), `conditional ×24`.
  - **8 distinct `stage`:** `commissioning ×84`, `design ×84`, `operation ×72`, `procurement ×60`, `emergency_response ×48`, `installation ×48`, `end_of_life ×24`, `n/a ×24`.
  - **`applicability`: `active ×420`, `conditional_out_of_scope ×24`** (the 24 = UL2202 and UL9540/9540A/NFPA855, 12 sites each).
  - **Editions (adopted → latest), the compliance-risk core:**
    | standard | adopted_edition | latest_edition |
    |---|---|---|
    | UL2594 | `3rd ed., 2022-12-15` | `3rd ed., 2022-12-15 (revision activity through 2025)` |
    | UL3600 | `1st ed., 2023-01-09` | `1st ed., 2023-01-09` |
    | UL2231 | `2021 editions` | `2021 editions` |
    | NEC625 | `2020 NEC (2021 USBC, effective 2024-01-18)` | **`2023 NEC published (NOT adopted in Virginia)`** |
    | VA-USBC-SFPC | `2021 editions, effective 2024-01-18 (2024 cycle in development, ~2027)` | `2021 (2024 development cycle underway)` |
    | ACCESS-BOARD-EVSE | `VA USBC ADA provisions (in force); Access Board rule at NPRM stage as of 2026-07-19` | **`NPRM 2024-09-03; final rule NOT issued as of 2026-07-19; DOJ rulemaking to follow`** |
    | OCPP-ISO15118 | `current industry versions` | `current industry versions` |
    | UL2202 | `2022 edition` | `2022 edition` |
    | UL9540-9540A-NFPA855 | `UL 9540A 5th ed. 2025-03-12; NFPA 855 2026 ed.` | `UL 9540A 6th-ed. activity 2026` |
  - **8 distinct `authority`:** `Manufacturer listing (NRTL) + local building official ×72`; `Building official + ADA coordinator; future DOJ standards ×60`; `Building official / electrical inspector (Fairfax City / PWC) ×60`; `City/County building official + Fire Marshal ×60`; `Program owner (sustainability office); voluntary standard ×60`; `Program owner / vendor contract ×60`; `NRTL listing + electrical inspector ×48`; `—` (em-dash) `×24`.
  - **Representative `requirement` / `open_ahj_question` values** (verified by dumping all 37 FFX002 rows): NEC625 design = "Load calculations, disconnect provisions, circuit design", evidence "Permit + passed electrical inspection", open AHJ question "Disconnect location and labeling acceptance at each site". VA-USBC-SFPC design = "Building/fire review lanes; EV-ready provisions (VCC 406.2.7 class)", open question "Fire access geometry; garage/enclosure conditions; 'sufficient EV charging' interpretation". ACCESS-BOARD-EVSE design = "ADA-first layout at site screening (documented local cost/schedule driver)", open question "Treatment of EV-space ADA counts at small installations (rule status must be re-checked at design time)". OCPP procurement = "Require OCPP compliance to avoid network lock-in; no-app payment capability". UL2202 = "Applies ONLY if DC fast charging enters scope. **No DCFC in the current plan.**" UL9540 = "Applies ONLY if battery storage enters scope. **battery_storage_flag=0 at all 12 sites.**"
- **Notes:** (a) The register is **site-invariant**: the identical 37-row block is repeated for all 12 sites with no per-site variation in any column except `site_id`. That means the "per-site standards applicability" framing is nominal — PWC002 (the enclosed garage) gets *exactly the same* rows as every open-lot library, despite `garage_enclosed=1.0` and its `high` electrical risk with "garage or enclosed-structure context adds fire/AHJ review risk" in the legacy file. **This is a genuine gap: garage-specific fire/AHJ obligations are asserted in the risk file but not reflected in the standards register.** (b) The UL9540 row's justification "`battery_storage_flag=0` at all 12 sites" **is independently verified true** in `real_sites_v2.csv` (distinct set `{'0'}`) — good cross-file integrity. (c) The two "NOT adopted / NOT issued" latest-edition strings are date-stamped `2026-07-19` and will go stale; ACCESS-BOARD-EVSE explicitly says "rule status must be re-checked at design time". (d) `authority` uses a literal em-dash `—` as a null marker on the 24 out-of-scope rows, while `evidence_required` and `open_ahj_question` use `—` too — a non-empty-string null convention that will render as a visible dash in any table.

### `data/inputs/legacy_matlab_site_meta.csv`
- **Role:** Arrival windows and base-load / spare-capacity planning proxies hand-adapted from the legacy MATLAB adapter; feeds the V3 simulation's load model.
- **Kind:** fixture / tracked input (labelled planning proxies); hashed as manifest input #5.
- **Reads:** n/a.
- **Written by / read by:** Hand-adapted (per its own `provenance` column). Hashed into `contract_manifest.json:15`; its `base_load_mean_kw` flows into `scenario_table.base_load_kw`.
- **Key contents:** **7 columns:** `site_id, arrival_start_hr, arrival_end_hr, base_load_mean_kw, base_load_peak_kw, spare_capacity_kw_placeholder, provenance`. **12 rows.** `provenance` is the same string on all 12: *"hand-adapted planning placeholder from legacy MATLAB adapter (2026-07); base loads and spare capacity are **UNVERIFIED planning proxies**"*.

  | site_id | arrival window | base_load_mean_kw | base_load_peak_kw | spare_capacity_kw_placeholder |
  |---|---|---|---|---|
  | FFX002 | 10-17 | 51.4 | 67.9 | 153.6 |
  | FFX004 | 8-16 | 115.0 | 151.8 | 153.6 |
  | PWC006 | 10-17 | 51.0 | 67.4 | 76.8 |
  | FFX001 | 8-16 | 73.0 | 96.3 | 76.8 |
  | PWC002 | 7-11 | 65.5 | 86.5 | 57.6 |
  | PWC007 | 10-17 | 51.0 | 67.4 | 76.8 |
  | PWC004 | 10-17 | 51.0 | 67.4 | 76.8 |
  | FFX003 | 10-17 | 50.2 | 66.3 | 76.8 |
  | PWC008 | 10-17 | 51.0 | 67.4 | 38.4 |
  | PWC001 | 8-16 | 90.5 | 119.5 | 57.6 |
  | PWC005 | 10-17 | 50.2 | 66.3 | 38.4 |
  | PWC003 | 8-16 | 82.8 | 109.3 | 38.4 |
- **Notes:** (a) **FFX002's `base_load_mean_kw = 51.4` matches `scenario_table` FFX002_2026_baseline `base_load_kw = 51.4` exactly** — the input→contract lineage is clean and traceable. Later horizons grow it (55.7 / 60.3 / 65.3), consistent with `base_load_growth_per_year = 0.008` compounded (51.4 × 1.008^10 = 55.66 ≈ 55.7 ✓; ×1.008^20 = 60.27 ≈ 60.3 ✓; ×1.008^30 = 65.27 ≈ 65.3 ✓). **The base-load model is fully reproducible from the assumptions file.** (b) **The `spare_capacity_kw_placeholder` column is NOT propagated into the contract** — `scenario_table.spare_capacity_kw` is blank on all 120 rows. This is the *correct* behaviour (a placeholder must not masquerade as a value), but it means a nonzero-looking column exists in a tracked input that must never be lifted. Any future integrator who "helpfully" wires it up would silently break the placeholder guarantee the whole program rests on. **Flag this loudly for Phase 2/4.** (c) The values are quantised to 38.4 / 57.6 / 76.8 / 153.6 kW — i.e. 0.8 × {48, 72, 96, 192} A at 480 V — synthetic, not measured. (d) `base_load_peak_kw` is exactly `1.321 ×` mean for every row (67.9/51.4 = 1.3210, 151.8/115.0 = 1.3200, …) — a single multiplier, not per-site observation. (e) PWC002's arrival window 7-11 (commuter garage) is the only morning-peak site; all libraries are 10-17, all offices 8-16.

### `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv`
- **Role:** Frozen legacy-V2 output: readiness scores, ranks, electrical-risk levels, and rank-stability bands per site. **This is where the 58.8 headline actually lives.**
- **Kind:** fixture / tracked input (frozen legacy output; provenance in filename); hashed as manifest input #2.
- **Reads:** n/a (frozen snapshot).
- **Written by / read by:** Produced by the legacy V2 model on 2026-07-19 and frozen. Hashed into `contract_manifest.json:12`; its `electrical_risk_level` is consumed by V3 right-sizing (per `data/README.md:10`). Re-published in `dashboard/tableau/patch_package/tbl_readiness_confidence.csv` and quoted by ~13 prose files.
- **Key contents:** **15 columns:** `site_id, site_name, base_rank, base_readiness_score, electrical_risk_level, electrical_risk_points, optimistic_rank, expected_rank, conservative_rank, optimistic_score, expected_score, conservative_score, worst_case_rank_change, electrical_risk_reason, electrical_data_needed_next`. **12 rows.**

  | site_id | base_rank | **base_readiness_score** | electrical_risk_level | risk_points | opt/exp/cons rank | opt/exp/cons score | worst_case_rank_change |
  |---|---|---|---|---|---|---|---|
  | FFX002 | 1 | **58.8** | medium | 6.0 | 1/1/1 | 57.8/55.8/52.8 | 0 |
  | FFX004 | 2 | 54.4 | medium | 6.0 | 2/2/2 | 53.4/51.4/48.4 | 0 |
  | PWC006 | 3 | 52.1 | medium | 6.0 | 3/3/3 | 51.1/49.1/46.1 | 0 |
  | FFX001 | 4 | 51.0 | medium | 6.0 | 4/4/4 | 50.0/48.0/45.0 | 0 |
  | PWC007 | 6 | 50.2 | medium | 6.0 | 5/5/5 | 49.2/47.2/44.2 | −1 |
  | PWC004 | 7 | 48.6 | medium | 6.0 | 7/6/6 | 47.6/45.6/42.6 | −1 |
  | PWC002 | 5 | 50.3 | **high** | 11.0 | 6/7/8 | 48.3/44.3/38.3 | **+3** |
  | FFX003 | 8 | 46.8 | medium | 6.0 | 8/8/7 | 45.8/43.8/40.8 | −1 |
  | PWC008 | 9 | 40.1 | medium | 6.0 | 9/9/9 | 39.1/37.1/34.1 | 0 |
  | PWC005 | 11 | 36.9 | medium | 6.0 | 11/10/10 | 35.9/33.9/30.9 | −1 |
  | PWC001 | 10 | 39.8 | **high** | 9.0 | 10/11/11 | 37.8/33.8/27.8 | **+1** |
  | PWC003 | 12 | 29.6 | **high** | 9.0 | 12/12/12 | 27.6/23.6/17.6 | 0 |

  `electrical_risk_reason` for the 9 `medium` sites is uniform: *"electrical service rating unknown; spare capacity unknown; emergency disconnect visibility not confirmed"*. PWC002 adds *"garage or enclosed-structure context adds fire/AHJ review risk; moderate service-distance assumption; high service-upgrade cost assumption"*; PWC001 adds *"moderate service-distance assumption; moderate trenching assumption; moderate service-upgrade cost assumption"*; PWC003 adds *"public-access/use case is not fully confirmed; public-safety facility context may limit implementation"*. `electrical_data_needed_next` is the same three-item ask everywhere (*confirm service rating; confirm spare capacity or upgrade need; confirm emergency disconnect location and visibility*), plus *"confirm garage fire/AHJ requirements"* for PWC002.
- **Notes:** (a) **This is the sole data-layer origin of 58.8.** It is a *legacy_v2 frozen input*, not a contract table, and it is not covered by RT-10's table-hash verification. See §0.2. (b) The `worst_case_rank_change` column is the honest part of this file: PWC002 can drop **3 ranks** (5→8) once electrical risk is priced in, and its conservative score (38.3) falls below PWC008's base (40.1). Any presentation that shows a static ranking without the conservative band overstates certainty. (c) **Rank/score inconsistency worth checking:** `base_rank` is not a clean sort of `base_readiness_score` — PWC002 (50.3) is `base_rank 5` while PWC007 (50.2) is `base_rank 6`, which is correct, but PWC001 (39.8) is `base_rank 10` while PWC005 (36.9) is `base_rank 11` and PWC008 (40.1) is `base_rank 9` — that ordering is consistent too. Verified: `base_rank` *is* a correct descending sort of `base_readiness_score`. No defect; the apparent scrambling in the file is just row order (the file is written in *expected_rank* order, not base_rank order). (d) `electrical_risk_level` uses lowercase `medium`/`high`, a **third** casing convention alongside `capacity_confidence` (lowercase) and `data_confidence` (capitalised). (e) This file is the reason "FFX002 … medium" exists anywhere; conflating it with data confidence produces the false "Medium confidence" claim (§0.3).

### `data/inputs/real_sites_v2.csv`
- **Role:** The primary site-attribute input — 12 candidate sites × 40 fields, the team's 2026-06-24 snapshot from which every downstream score and scenario derives.
- **Kind:** tracked input (authored/curated); hashed as manifest input #1.
- **Reads:** n/a.
- **Written by / read by:** Curated by the team. Hashed into `contract_manifest.json:11`; consumed by `fcf_m2` scoring/demand/contract build; the basis of `site_table.csv`.
- **Key contents:** **40 columns** (verified programmatically), **12 rows** (verified). Columns in order: `site_id, site_name, site_type, address, city, state, zip, lat, lon, public_access, employees_day, visitors_day, fleet_vehicles, parking_spaces, hours_open, avg_dwell_min, nearby_households_1mi, nearby_jobs_1mi, aadt_nearest, amenities_count_0_5mi, ev_registrations_local, ev_share_local, existing_l2_ports_1mi, existing_dcfc_ports_3mi, equity_gap_index, elec_service_voltage, elec_service_rating_amp, spare_capacity_kw, distance_to_service_ft, trenching_ft, trench_cost_per_ft, service_upgrade_cost_usd, ada_layout_possible, fire_access_ok, garage_enclosed, emergency_disconnect_visible, stormwater_risk, battery_storage_flag, battery_storage_kwh, notes`.
  - **Columns that are a single constant across all 12 sites** (i.e. carry zero discriminating information): `elec_service_voltage = 480`; `elec_service_rating_amp = 0`; `spare_capacity_kw = 0`; `fleet_vehicles = 0`; `ada_layout_possible = 1`; `fire_access_ok = 1`; `emergency_disconnect_visible = 0`; `stormwater_risk = 0`; `battery_storage_flag = 0`; `battery_storage_kwh = 0`; `trench_cost_per_ft = 150`.
  - **Discriminating values:** `employees_day` 0-1000; `visitors_day` 80-700; `parking_spaces` 63-1400; `hours_open` 7.29-24; `avg_dwell_min` 90-240; `nearby_households_1mi` 58-9866; `nearby_jobs_1mi` 33-31611; `aadt_nearest` 490-51000; `amenities_count_0_5mi` 0-6; `ev_share_local` ∈ {0.005, 0.018, 0.023}; `equity_gap_index` 0.191-0.769; `distance_to_service_ft` 75-150; `trenching_ft` 50-125; `service_upgrade_cost_usd` 15000-45000.
  - **FFX002 row (line 7)** — the source of the headline site: `library, 10360 North Street, Fairfax VA 22030-2514, lat 38.847072, lon -77.303630, public_access 1, employees_day 30, visitors_day 450, parking_spaces 199, hours_open 9.29, avg_dwell_min 90, nearby_households_1mi 4964, nearby_jobs_1mi 15718, aadt_nearest 12000, amenities 6, ev_registrations_local 500, ev_share_local 0.023, existing_l2_ports_1mi 14, existing_dcfc_ports_3mi 23, equity_gap_index 0.660` (→ matches `scenario_table.equity_indicator 0.66`), `distance_to_service_ft 75, trenching_ft 75, service_upgrade_cost_usd 15000`.
  - **`notes`** is a long per-site provenance narrative. Recurring caveats: "electrical service rating spare capacity and emergency disconnect remain unconfirmed" (all sites); "V2 public-data upgrade applied 2026-06-25: households use ACS B11001 + TIGER centroid-in-buffer estimate; jobs use LODES workplace jobs + TIGER; AADT uses nearest VDOT Bidirectional Traffic Volume segment and should be treated as **screening-level traffic, not final site-access validation**"; "EV adoption remains a documented proxy because **no current official locality EV registration source was found**"; amenities from `amenities_0_5mi_v4_osm_reviewed.csv`.
- **Notes:** (a) **`data/README.md:9`'s "12 candidate sites, 40 fields (team snapshot 2026-06-24)" is exactly correct** — verified. (b) **A live operational caveat buried in a notes cell (line 5, PWC004):** *"official library page currently lists **Chinn Park Library as closed for renovation** so operating status remains a caveat"* — PWC004 nonetheless ranks 7th and carries a full 10-row scenario decade in the contract as though operating. Nothing downstream flags it. **This should surface in Phase 1.** (c) **`notes` cites two files that do not exist in this repository:** `amenities_0_5mi_v4_osm_reviewed.csv` (cited for 9 sites), `v2c003_model_row_assumptions.csv` (line 8), `v2c007_model_row_assumptions.csv` (line 9). I searched the whole tree; none are present. These are dangling provenance references to an external working set. (d) `source_date` in the contract is `2026-06-24`, but seven `notes` cells say the public-data upgrade was applied `2026-06-25` and AFDC exports are dated `Jun 25 2026` — **the contract's stamped source date precedes some of the data it describes by one day.** Minor, but it means `source_date` is the snapshot label, not a max-of-inputs date. (e) `ev_share_local` takes only 3 distinct values across 12 sites (0.005 / 0.018 / 0.023) — it is a jurisdiction-level proxy applied site-wide, not a site measurement, consistent with the "documented proxy" note. (f) `hours_open = 24` for PWC002 (commuter garage) vs 7.29-9.29 for libraries — the libraries' fractional values are weekly-average hours per the FFX002 note, so **`hours_open` mixes two different units across rows** (daily hours for the garage, weekly-average daily hours for libraries). Worth confirming in Phase 1.

### `data/observed/observed_sessions_template.csv`
- **Role:** Import-format template for future observed-session data — the on-ramp for calibrating the currently `synthetic_uncalibrated` demand model. **Phase 4 builds on this.**
- **Kind:** fixture / template (example row, not real data).
- **Reads:** n/a.
- **Written by / read by:** Hand-authored. Intended input to `fcf_m2.demand.calibrate()` (named in `assumptions.json:22`). **Not hashed in the manifest.**
- **Key contents:** 102 bytes, quoted in full:
  ```
  site_id,date,sessions,energy_kwh,mean_dwell_min,facility_visitors_day
  FFX002,2026-08-01,2,19.0,95,310
  ```
  **6 columns:** `site_id, date, sessions, energy_kwh, mean_dwell_min, facility_visitors_day`. **1 example row.**
- **Notes:** (a) **Phase-4 critical:** this 6-column shape is the entire observed-data contract. Note what it does **not** capture: no charger/port id, no session start/end timestamps, no utilisation, no uptime/reliability, no curtailment. But `assumptions.json:71-85` defines the expansion trigger on `utilization_threshold 0.4`, `wait_threshold_min 10.0`, **and `reliability_uptime_min 0.97`** — **uptime cannot be computed from this template at all**, and utilisation/wait can only be approximated. **The observed-data template is structurally insufficient to evaluate the trigger policy it is meant to feed.** This is the most consequential design gap in the lane for Phase 4/5. (b) `19.0 kWh / 2 sessions = 9.5 kWh/session`, exactly the `energy_per_session_kwh` benchmark in `assumptions.json:33` — the example row is synthetic and constructed *from* the assumption it would be used to test. (c) `mean_dwell_min = 95` vs FFX002's `avg_dwell_min = 90` in `real_sites_v2.csv`; `facility_visitors_day = 310` vs `visitors_day = 450`. Illustrative only, but a reader could mistake these for observations. (d) `date 2026-08-01` is in the future relative to the run stamp (2026-07-19) and — per `n_observed_rows: 0` — **no observed data has ever been ingested.** (e) Not covered by the hash chain, so its shape can drift from any consumer without detection.

### `data/provenance/field_provenance_v1.csv`
- **Role:** Typed field-level provenance per site — the tracked *input* form of the provenance table, driving the data-confidence computation.
- **Kind:** authored / tracked reference; hashed as manifest input #3.
- **Reads:** n/a.
- **Written by / read by:** Hand-authored. Hashed into `contract_manifest.json:13`; republished (LF-normalised) as `data/contract/v1/source_provenance.csv`.
- **Key contents:** Identical schema and content to `source_provenance.csv` — 9 columns, **84 rows = 12 sites × 7 field_groups**, values as tabulated in that entry. Header line 1; data lines 2-85. **CRLF line endings.**
- **Notes:** (a) **Content-identical to `data/contract/v1/source_provenance.csv` modulo CRLF→LF** (verified by `diff <(tr -d '\r' …)`), yet carries a *different* SHA-256 (`9a07aa1e…` vs `2d346861…`). See the `source_provenance.csv` entry. (b) **Direct contradiction with `data/provenance/site_coordinate_sources.csv`:** here, `coordinates` is `public_web_reference` / *"public web mapping (replace with official GIS)"* for **all 12 sites** including PWC001-004 and FFX001-002 — while `site_coordinate_sources.csv` marks exactly those 6 sites `Official`, sourced from *"Prince William County GIS Premise Addresses"* and *"City of Fairfax GeoHub Addresses"*, with the note *"address and coordinates verified from countywide address point layer"*. **One of these two files is wrong, and the wrong one is the one that feeds the contract.** If the coordinate sourcing really was upgraded to Official for 6 sites, the contract's data-confidence is understated and this file is stale; if not, `site_coordinate_sources.csv` overstates. **High-priority Phase-1 reconciliation.** (c) The only CRLF file in the entire `data/` tree.

### `data/provenance/site_coordinate_sources.csv`
- **Role:** Records the authoritative GIS dataset, owner, and quality tier behind each site's address and coordinates.
- **Kind:** authored / tracked reference. **Not hashed in the manifest.**
- **Reads:** n/a.
- **Written by / read by:** Hand-authored. **No consumer found** — it is not referenced by the contract, not hashed, and its `source_quality` is not reflected in `field_provenance_v1.csv`.
- **Key contents:** **12 columns:** `site_id, site_name, address, city, state, zip, lat, lon, source_dataset, source_owner, source_quality, notes`. **Only 6 data rows** (lines 2-7): PWC001, PWC002, PWC003, PWC004 (dataset *"Prince William County GIS Premise Addresses"*, owner *"Prince William County Department of Information Technology GIS Division"*), and FFX001, FFX002 (dataset *"City of Fairfax GeoHub Addresses"*, owner *"City of Fairfax Virginia"*). **`source_quality = Official` on all 6.** Notes: *"address and coordinates verified from countywide address point layer"* (PWC) / *"address and coordinates verified from authoritative feature service"* (FFX).
- **Notes:** (a) **Covers 6 of 12 sites. Missing entirely: FFX003, FFX004, PWC005, PWC006, PWC007, PWC008.** The file has no row saying "no official source found" for them — they are simply absent, which is indistinguishable from an oversight. (b) **Contradicts `field_provenance_v1.csv` / `source_provenance.csv`** for all 6 sites it does cover (see above). (c) Coordinates here match `site_table.csv` exactly for all 6 sites (spot-checked FFX002 38.847072/-77.303630 ✓, PWC001 38.679705/-77.352905 ✓), so the *values* are consistent — only the *quality label* conflicts. (d) Being unhashed and unconsumed, this file is pure documentation that can drift silently. `data/README.md:13` folds it under "tracked reference — typed field-level provenance **driving data confidence**", which overstates its role: it drives nothing.

### `data/provenance/v2_source_confidence_tracker.csv`
- **Role:** Per-site, per-field-group upgrade tracker — current source status, the concrete upgrade path, priority, and whether a stakeholder is needed.
- **Kind:** authored / tracked reference. **Not hashed in the manifest.**
- **Reads:** n/a.
- **Written by / read by:** Hand-authored. **No programmatic consumer found.**
- **Key contents:** **8 columns:** `site_id, site_name, field_group, current_status, upgrade_path, priority, stakeholder_needed_later, notes`. **Only 20 data rows, covering only 2 sites: FFX003 and FFX004** (10 field_groups each: `address_and_public_access, coordinates, hours_and_parking, nearby_EV_supply, households_jobs_traffic, amenities, equity, EV_adoption, visitors_and_employees, electrical_and_site_layout`).
  - `current_status` values seen: `official_source`, `public_web_reference`, `public_dataset`, `official_derived`, `open_gis_support_reviewed`, `documented_proxy`, `planning_assumption`, `unconfirmed_placeholder`.
  - `priority`: `low`, `medium`, `high`, `later`. `stakeholder_needed_later`: `no`, `possible`, `yes`.
  - **`electrical_and_site_layout`** for both sites: `current_status = unconfirmed_placeholder`, `upgrade_path = replace_with_facility_or_utility_review`, `priority = later`, `stakeholder_needed_later = yes`, note *"Do not treat as implementation-ready until confirmed"*.
  - **FFX004 is flagged hardest:** `address_and_public_access` and `coordinates` are both `public_web_reference` with `priority = high` (*"Should be upgraded because this is a county civic site"*, *"Better coordinate source needed before baseline"*), and `hours_and_parking` is a `planning_assumption` at `priority = high` (*"Large planning assumption affects score and interpretation"*).
  - FFX003 is milder: `address_and_public_access` and `hours_and_parking` are `official_source` at `priority = low`; only `coordinates` (medium) and `households_jobs_traffic`/`equity` (high, but already upgraded and marked `keep`) need attention.
  - Recurring notes: *"Upgraded 2026-06-25 with ACS households, LODES jobs, and nearest VDOT traffic segment. Traffic remains screening-level nearest-segment value, not final site-access validation."*; *"Open-data support, not official local government inventory."*; *"Kept as documented proxy because no current official locality EV registration extract was found."*
- **Notes:** (a) **Covers 2 of 12 sites (17 %).** Its filename and its `data/README.md:13` classification ("typed field-level provenance driving data confidence") both imply cohort-wide coverage; it is in fact a two-site pilot that was never extended. **This is the weakest link in the provenance story and should be either completed or explicitly relabelled in Phase 1.** (b) Its `field_group` vocabulary (10 groups) **does not match** `field_provenance_v1.csv`'s (7 groups). Overlapping-but-different taxonomies: this file has `hours_and_parking`, `nearby_EV_supply`, `households_jobs_traffic`, `amenities`, `equity`, `EV_adoption`, `visitors_and_employees`, `electrical_and_site_layout`; the contract file has `electrical_service`, `safety_review_fields`, `site_use_and_demand`, `address_and_public_access`, `coordinates`, `parking_and_layout`, `equity_and_context`. Only `address_and_public_access` and `coordinates` are shared verbatim. **The two provenance systems cannot be joined.** (c) FFX004's `hours_and_parking = planning_assumption, priority high` is notable because FFX004 ranks **2nd** (54.4) and its `parking_spaces = 1200` and `employees_day = 1000` are the largest in the cohort — a high-priority unverified assumption is doing heavy lifting in a top-2 ranking. (d) Unhashed and unconsumed, so it can drift silently.

### `data/cache/boundaries/ATTRIBUTION.md`
- **Role:** Attribution and provenance note for the cached Census boundary GeoJSON, plus disclosure of the filtering/simplification applied for repo size.
- **Kind:** authored (Markdown, 8 lines).
- **Reads:** n/a; describes `tl_2024_va_counties.geojson` (sibling file — **verified to exist**).
- **Written by / read by:** Hand-authored. Read by humans; referenced from `data/README.md:14`.
- **Key contents:** Line 2: `tl_2024_va_counties.geojson` = Virginia county boundaries from US Census TIGER/Line 2024 (`tl_2024_us_county.zip`, public domain), **filtered to `STATEFP=51`**. Line 3: source URL `https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip`, downloaded `2026-07-19` during the legacy baseline run. Line 4: cached so the GIS map step runs **fully offline (PY-06)**; attribution "U.S. Census Bureau TIGER/Line Shapefiles, 2024". Lines 6-8 (repo-publication note, 2026-07-19): filtered to counties **within 0.5° of the candidate-site extent** and **geometry-simplified (tolerance 0.0005°)** to keep the repository small; *"This affects only map context outlines, not any model computation."*
- **Notes:** (a) Every claim here is **independently verified against the file** (see next entry): STATEFP is uniformly `51`, the extract is 25 features (not all 133 VA county-equivalents), and geometry is simplified. (b) The 0.0005° tolerance ≈ 45-55 m at this latitude — visible at street zoom but irrelevant at county-outline zoom, consistent with the stated caveat. (c) Requirement tag `PY-06` is referenced without a local definition; it presumably resolves in the requirements doc (outside this lane).

### `data/cache/boundaries/tl_2024_va_counties.geojson`
- **Role:** Cached, filtered, simplified county-boundary polygons providing offline map context for GIS/dashboard views.
- **Kind:** vendored (US Census TIGER/Line 2024, public domain) + generated (filtered & simplified derivative).
- **Reads:** n/a (leaf data).
- **Written by / read by:** Derived from `tl_2024_us_county.zip` on 2026-07-19. Consumed by the offline GIS map step (PY-06). **Not hashed in the manifest.**
- **Key contents (structural characterisation — file not dumped, per instruction):**
  - **PARSES AS VALID JSON: YES.**
  - `type = "FeatureCollection"`; top-level keys `["type", "name", "crs", "features"]`.
  - **FEATURE COUNT: 25.**
  - `crs = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4269"}}` (NAD83).
  - Per-feature keys `["type", "properties", "geometry"]`; **property keys `["GEOID", "NAME", "NAMELSAD", "STATEFP"]`** (4 attributes only — the full TIGER attribute set was stripped).
  - Geometry types present: `{"Polygon", "MultiPolygon"}`.
  - `STATEFP` distinct set = **`{"51"}`** — Virginia only, as claimed.
  - `NAME` values (25, in file order): Stafford, Alexandria, Rappahannock, Essex, **Falls Church**, Orange, Madison, Fauquier, **Fairfax**, **Prince William**, Manassas Park, Arlington, Clarke, Westmoreland, Fredericksburg, King George, Louisa, **Fairfax**, Loudoun, Culpeper, Warren, Manassas, Spotsylvania, Frederick, Caroline.
  - File size 171 997 bytes.
- **Notes:** (a) **`"Fairfax"` appears twice** (positions 9 and 18). This is *correct* TIGER behaviour, not a duplicate: Virginia has both Fairfax **County** and the independent **City of Fairfax**, distinguished by `GEOID`/`NAMELSAD`, not by `NAME`. **Any consumer that joins or labels on `NAME` alone will collide or double-count.** The `NAMELSAD` field exists precisely to disambiguate — Phase 3 (3D explorer) and Phase 6 (Tableau) must join on `GEOID`. Same trap applies to Manassas/Manassas Park and to the independent cities generally. (b) The extract is a **regional** cut (25 features), not statewide (VA has 133 county-equivalents) — consistent with the ATTRIBUTION note's 0.5°-buffer claim, and confirming the file name `tl_2024_va_counties` slightly overpromises ("va_counties" reads as all-of-Virginia). (c) EPSG:4269 (NAD83), not EPSG:4326 (WGS84) — visually indistinguishable at this scale (sub-metre in CONUS) but a strict web-mapping library expecting 4326 should be told. (d) Unhashed, so silent drift is possible. (e) No coordinates were dumped; only structure was inspected.

---

## 2. CROSS-FILE CONSISTENCY CHECKS I RAN

| Check | Result |
|---|---|
| 11 manifest hashes recomputed with `shasum -a 256` | **11/11 PASS** |
| `scenario_table.csv` row count == 120 | **PASS** (121 lines = header + 120) |
| `horizon_year` ⊆ {2026, 2036, 2046, 2056} | **PASS** (exactly, with 12/36/36/36 split) |
| `schema.json` required list length == CSV column count == 48, same order | **PASS** |
| `capacity_basis` == `placeholder` on 120/120 rows, 12/12 sites | **PASS** |
| `data_confidence` High count | **0/12** (all Low) |
| `grid_factor_value` == 596.3 on 120/120 rows | **PASS** |
| `590.2` anywhere under `data/` | **ABSENT** (clean) |
| Standalone `2035`/`2050` tokens in `scenario_table.csv` cells | **0 hits** |
| `2035`/`2050` in `data/` | 1 hit, `assumptions.json:11`, **correctly labelled legacy** |
| Secrets / absolute paths / AWS IDs in `data/` | **0 hits** |
| `site_name` agrees between `site_table.site_name_display` and `scenario_table.site_name` | **12/12 match** |
| `site_id` set identical across `real_sites_v2`, `legacy_matlab_site_meta`, `legacy_v2_electrical_risk_summary`, `field_provenance_v1`, `site_table`, `scenario_table`, `standards_register` | **12/12 identical in all 7** |
| FFX002 `base_load_kw` chain: `legacy_matlab_site_meta 51.4` → `scenario_table 2026 baseline 51.4` → grown at 0.008/yr → 55.7/60.3/65.3 | **reproduces exactly** |
| `field_provenance_v1.csv` vs `source_provenance.csv` | **content-identical modulo CRLF/LF**, different digests |
| Anchor cohort claims vs `real_sites_v2.csv` | **12 of 13 verified exact**; `install_cost_est_usd` derived, unverifiable here |
| `battery_storage_flag = 0` claim in `standards_register` UL9540 row | **verified true** in `real_sites_v2.csv` |
| `data/README.md` "12 sites, 40 fields" | **verified exact** |
| `make run-legacy` / `run-v3` / `validate` targets exist | **PASS** (`Makefile:11,14,17`) |
| `python -m fcf_m2.workflow validate-contract` exists | **PASS** (`workflow.py:357,367`) |
| `../README.md` link from `data/README.md:3` | **PASS** (target exists) |
| `data/outputs/` absent and gitignored | **PASS** (`.gitignore:11`) |
| `tl_2024_va_counties.geojson` parses as JSON | **PASS**, 25 features |
| Files cited in `real_sites_v2.notes` (`amenities_0_5mi_v4_osm_reviewed.csv`, `v2c003_…`, `v2c007_model_row_assumptions.csv`) | **ALL THREE ABSENT from the repo** |
