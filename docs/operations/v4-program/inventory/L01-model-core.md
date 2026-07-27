# LANE L01 — THE MODEL CORE (`src/`)

Repo: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (branch `v4-platform`, HEAD `95e91e0 docs(v4-program): initialize program ledger`).
All 23 assigned files read end to end. Paths below are repo-relative.

**Lane-brief correction up front:** the brief asked me to capture `SUBSCORE_WEIGHTS` and `DRIVERS`
"verbatim" from `scoring.py`. **Those identifiers do not exist anywhere in `repo/`.** A repo-wide grep
(excluding `.git`, `venv`) returns zero hits for `SUBSCORE_WEIGHTS`, `DRIVERS`, `Earned:`, `Forgone:`.
They exist only in the *separate* 3D explorer tree at
`incoming/explorer/fcf-3d/fcf3d/build_sites.py` (lines 92-97, 134+, 238-249) and
`incoming/explorer/fcf-3d/web/app.js`. See finding F-01. In `repo/`, the weights are **inline numeric
literals** inside `enrich_and_score()`; there is no named weight table and no driver-attribution
machinery at all.

---

### src/fcf_m2/__init__.py
- **Role:** Package marker for `fcf_m2`; makes `src/fcf_m2` an importable package for the editable install.
- **Kind:** authored (empty)
- **Reads:** n/a
- **Written by / read by:** Imported implicitly by every `from .x import y` in the package; listed in `src/fcf_m2.egg-info/SOURCES.txt:3`.
- **Key contents:** **0 bytes** (verified with `wc -c`). No `__version__`, no `__all__`, no re-exports.
- **Notes:** The package version lives only in `pyproject.toml` (`version = "3.0.0"`) and `config.MODEL_VERSION`. There is no `fcf_m2.__version__`; any consumer wanting the version must import `config`.

---

### src/fcf_m2/config.py  (167 lines)
- **Role:** Declared single home for every result-changing constant, with a provenance label attached to each.
- **Kind:** authored (data-contract-adjacent: several constants are enforced by `contract.build_schema()`)
- **Reads:** nothing at runtime (pure constants + one helper). No file I/O.
- **Written by / read by:** Imported by `workflow`, `contract`, `scoring`, `queueing`, `peak_wait`, `right_sizing`, `economics`, `emissions`, `demand`, `triggers`, `visuals`. Its values are serialized into `data/contract/v1/assumptions.json` and `contract_manifest.json` by `workflow.run()` / `contract.write_contract()`.
- **Key contents:**
  - Versions (L19-21): `SCHEMA_VERSION = "1.0.0"`, `MODEL_VERSION = "3.0.0"`, `ANCHOR_SET_VERSION = "anchors_v1_2026-07"`.
  - Mode names (L23-24): `MODE_LEGACY = "legacy_v2"`, `MODE_V3 = "milestone2_v3"`.
  - **Horizons (L26-28):** `BASELINE_YEAR = 2026`; `V3_HORIZONS = [2036, 2046, 2056]`; `V3_HORIZON_LABELS = {2026:"now", 2036:"plus10", 2046:"plus20", 2056:"plus30"}`. Canonical convention is respected.
  - `LEGACY_GROWTH_MULTIPLIERS` (L31-37), explicitly marked "accepted V2 baseline; DO NOT CHANGE": `now 1.0`, `2035_base 1.8`, `2035_high 2.5`, `2050_base 3.0`, `2050_high 4.5`. **These are the only 2035/2050 keys and they are correctly scoped to legacy.**
  - `V3_GROWTH_MULTIPLIERS` (L42-50): `(2026,"baseline") 1.0`, `(2036,"base") 1.9`, `(2036,"high") 2.6`, `(2046,"base") 3.0`, `(2046,"high") 4.5`, `(2056,"base") 4.0`, `(2056,"high") 6.0`. `V3_STRESS_EXTRA = 1.15` (L51).
  - `GROWTH_PROVENANCE` (L53-58): "research Report 05 s3 … Status: synthetic_uncalibrated".
  - `EVSE_POWER_KW = 19.2` (L60, AC L2); `CHARGER_EFFICIENCY = 0.92` (L61).
  - Demand (L64-76): `DEMAND_MODEL_STATUS = "synthetic_uncalibrated"`; `DEMAND_COEFFICIENTS = {visitors_day 0.0015, employees_day 0.0006, nearby_jobs_1mi 0.00002, nearby_households_1mi 0.00003}`; `DEMAND_FLOOR_SESSIONS = 0.3`; `DEMAND_COEFFICIENT_PROVENANCE` states "no published derivation exists".
  - Queueing (L79-81): `TARGET_UTILIZATION = 0.70`, `MAX_MEAN_WAIT_MIN = 10.0`, `MAX_PORTS_SEARCH = 20`.
  - Peak/sim (L84-87): `PEAK_WINDOW_SHARE = 0.55`, `PEAK_WINDOW_HOURS = 4.0`, `SIM_RANDOM_SEED = 20260719`, `SIM_N_DAYS = 400`.
  - Energy/emissions (L90-97): `ENERGY_PER_SESSION_KWH = 9.5`; **`GRID_FACTOR_LB_PER_MWH = 596.3`** (L91); `GRID_FACTOR_SOURCE = "EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, total output emission rate CO2e"`; `GRID_FACTOR_VINTAGE = "eGRID2023r2, accessed 2026-07-19"`; `GRID_FACTOR_NEXT_REFRESH = "eGRID2024 …"`; `EV_EFFICIENCY_KWH_PER_MI = 0.30`; `DISPLACED_GASOLINE_G_CO2_PER_MI = 400.0`; `LB_TO_KG = 0.45359237`.
  - `ECON` dict (L100-116), all screening-class: `hardware_usd_per_port 6500.0`, `install_soft_cost_share 0.25`, `pathway_premium_share 0.15`, `retrofit_civil_multiplier 1.8`, `network_fee_usd_per_port_yr 1000.0`, `maintenance_usd_per_port_yr 400.0`, `tariff_usd_per_kwh 0.11`, `demand_charge_usd_per_kw_month 0.0`, `replacement_usd_per_port 2500.0`, `replacement_year_offset 10`, `decommission_usd_per_port 800.0`, `inspection_admin_usd_per_site_yr 300.0`, `contingency_civil_share 0.25`, `discount_rate_real 0.03`, `escalation {low 0.01, base 0.025, high 0.04}`.
  - `TRIGGER_POLICY` (L124-138): `policy_status "proposed_default_pending_team_and_client_adoption"`, `utilization_threshold 0.40`, `wait_threshold_min 10.0`, `reliability_uptime_min 0.97`, `min_observation_months 6`, `equity_override {enabled True, equity_index_percentile_min 0.60, reduced_utilization_threshold 0.25}`, `budget_gate "human_approval_required"`, `pathway_gate "ports_active_plus_step_must_not_exceed_ports_pathway"`.
  - `CAPACITY_BASIS_VALUES` (L140-147): `verified_utility, verified_facility, engineering_estimate, planning_proxy, placeholder, unknown`.
  - `JURISDICTIONS = {"FFX":"fairfax","PWC":"pwc"}` (L149); `RunConfig` dataclass (L152-158); `jurisdiction_for()` (L161-167) returns `"unknown"` for unmatched prefixes.
- **Notes:** The module docstring (L11) claims *"Every result-changing constant lives here with its provenance label."* **That is false** — see finding F-02 for the eight-plus result-changing constants that live in other modules. `jurisdiction_for` can emit `"unknown"`, which would fail the contract schema enum `["fairfax","pwc"]` (`contract.py:85`); harmless today because all 12 site_ids are FFX/PWC.

---

### src/fcf_m2/scoring.py  (216 lines)
- **Role:** The single readiness scorer — cohort min-max (`legacy_v2`) or fixed-anchor (`milestone2_v3`) normalization, four subscores, composite readiness, port screen, ranking, tiering.
- **Kind:** authored
- **Reads:** `load_anchor_set()` opens the anchor JSON path handed to it (`workflow` passes `data/anchors/anchor_set_v1.json`). Otherwise operates on the DataFrame it is given.
- **Written by / read by:** Called by `workflow.run()` (`enrich_and_score`, `add_tiers`, `load_anchor_set`) and by `tests/conftest.py::scored_legacy`. Its output columns feed `right_sizing.py`, the migration report, and `site_table`.
- **Key contents (verbatim weights — inline literals, no named table):**
  - `EV_SHARE_HIGH_BENCHMARK = 0.10` (L26) — **hardcoded here, not in config.py.**
  - `YES_NO_FIELDS` (L28-31, 7 fields): `public_access, ada_layout_possible, fire_access_ok, garage_enclosed, emergency_disconnect_visible, stormwater_risk, battery_storage_flag`.
  - `NUMERIC_FIELDS` (L33-40, 20 fields) incl. `employees_day, visitors_day, fleet_vehicles, parking_spaces, hours_open, avg_dwell_min, nearby_households_1mi, nearby_jobs_1mi, aadt_nearest, amenities_count_0_5mi, ev_share_local, existing_l2_ports_1mi, existing_dcfc_ports_3mi, equity_gap_index, spare_capacity_kw, distance_to_service_ft, trenching_ft, trench_cost_per_ft, service_upgrade_cost_usd, elec_service_rating_amp`.
  - `NORMALIZE_COLS` (L42-46, **12 fields**): `nearby_households_1mi, nearby_jobs_1mi, aadt_nearest, amenities_count_0_5mi, parking_spaces, avg_dwell_min, existing_ports_total, spare_capacity_kw, distance_to_service_ft, trenching_ft, install_cost_est_usd, equity_gap_index`.
  - Normalizers: `minmax()` (L58-63, returns all-zeros when max==min), `bounded_signal()` (L66-68, `s/high_benchmark` clipped 0-1), `anchored()` (L82-87, `(s-lo)/(hi-lo)` clipped 0-1, all-zeros if `hi<=lo`).
  - **Fixed-anchor scheme:** `load_anchor_set()` (L71-79) hard-fails with `ValueError` if `anchor_set_version != ANCHOR_SET_VERSION` (`"anchors_v1_2026-07"`). `normalize_fields()` (L90-104) uses the anchor when present, else falls back to cohort `minmax` and appends the column name to `fallback_fields`, surfaced as the `anchor_fallback_fields` output column (L196). **All 12 `NORMALIZE_COLS` have anchors, so `anchor_fallback_fields` is always empty in practice** (verified against `data/anchors/anchor_set_v1.json`).
  - Derived columns (L131-135): `access_adjustment = 1.00 / 0.35`; `readiness_access_adjustment = 1.00 / 0.65` (both keyed on `public_access >= 1`); `install_cost_est_usd = trenching_ft * trench_cost_per_ft + service_upgrade_cost_usd`; `existing_ports_total = existing_l2_ports_1mi + existing_dcfc_ports_3mi`.
  - **`demand_subscore` (L140-151), ×100, weights sum to 1.00:** `nearby_households_1mi_n 0.18` + `nearby_jobs_1mi_n 0.18` + `aadt_nearest_n 0.13` + `amenities_count_0_5mi_n 0.11` + `parking_spaces_n 0.10` + `hours_open.clip(0,24)/24 × 0.08` + `avg_dwell_min_n 0.07` + `ev_share_local_n 0.08` + `(1 - existing_ports_total_n) × 0.07`; then **multiplied by `readiness_access_adjustment`** (L151).
  - **`feasibility_subscore` (L153-158), sum 1.00:** `spare_capacity_kw_n 0.35` + `(1 - distance_to_service_ft_n) 0.25` + `(1 - install_cost_est_usd_n) 0.25` + `(1 - trenching_ft_n) 0.15`.
  - **`safety_subscore` (L160-166), sum 1.00:** `ada_layout_possible 0.35` + `fire_access_ok 0.35` + `(1 - garage_enclosed) 0.15` + `emergency_disconnect_visible 0.10` + `(1 - stormwater_risk) 0.05`.
  - **`equity_subscore` (L168):** `100 × equity_gap_index_n`.
  - **`readiness_score` (L170-175), sum 1.00, rounded to 1 dp:** `0.45×demand + 0.30×feasibility + 0.15×safety + 0.10×equity`.
  - `expected_sessions()` (L107-116): `0.0015×visitors_day + 0.0006×employees_day + 0.00002×nearby_jobs_1mi + 0.00003×nearby_households_1mi×(1+ev_share_local)`, clipped at floor `0.3`.
  - Port screen (L179-190): per row, `avg_session_hr = avg_dwell_min/60` (fallback `2` when dwell<=0), then `queueing.choose_ports()` → `recommended_ports_now`, `estimated_utilization`, `mean_wait_min`.
  - Ranking (L192-196): sort by `readiness_score` desc → `model_rank` 1..n; plus `scoring_mode`, `anchor_set_version` (empty string in legacy), `anchor_fallback_fields`.
  - `recommendation_tier()` (L200-210), evaluated in order: `public_access == 0` → `"Low public-priority / special-use"`; `garage_enclosed == 1` → `"High-review candidate"`; `model_rank <= 2 and readiness_score >= 50` → `"Tier 1 — advance to site screening"`; `readiness_score >= 45` → `"Tier 2 — promising candidate, refine data"`; else `"Tier 3 — lower priority / monitor"`.
- **Notes:**
  - **No `SUBSCORE_WEIGHTS`, no `DRIVERS`, no per-driver "Earned/Forgone" attribution exists here.** The explorer duplicates these numbers independently (F-01).
  - `access_adjustment` (0.35 branch) is computed and shipped in the output CSV but **never used in any formula** (only `readiness_access_adjustment` is). Dead but externally visible — it is a column in `tests/fixture_legacy_v2_site_results.csv`.
  - `spare_capacity_kw` is **0 for all 12 sites** in `data/inputs/real_sites_v2.csv` (verified), so `spare_capacity_kw_n` is identically 0 and **35% of `feasibility_subscore` is structurally dead weight** (F-04).
  - Tier-1 rank cutoff here is `rank <= 2`; `right_sizing.build_strategy` uses `rank <= 3` for the equivalent branch (`right_sizing.py:134`). Two different cutoffs for "top of the list".

---

### src/fcf_m2/workflow.py  (385 lines)
- **Role:** The orchestrator and the single source of truth for the workflow-step manifest; also the CLI entry point.
- **Kind:** authored (generator of `docs/WORKFLOW_STEPS.md`)
- **Reads (all via `ROOT = Path(__file__).resolve().parents[2]`, i.e. repo root):**
  - `data/inputs/real_sites_v2.csv` (L63)
  - `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` (L64)
  - `data/provenance/field_provenance_v1.csv` (L65)
  - `data/inputs/legacy_matlab_site_meta.csv` (L66)
  - `data/anchors/anchor_set_v1.json` (L67)
  - All five exist and all five SHA-256 hashes match `data/contract/v1/contract_manifest.json` (verified).
- **Written by / read by:** Produces every model output; consumed by `tests/conftest.py::v3_outputs`, `Makefile`, `scripts/verify.sh`. `docs/WORKFLOW_STEPS.md` is written by the `docs` subcommand.
- **Key contents:**
  - **`STEPS` — exactly 11 entries (L37-49)**, matching `docs/WORKFLOW_STEPS.md` ("Step count: **11**") verbatim:
    1. `load_inputs` — Load site table, electrical-risk fixture, provenance, anchors, MATLAB site meta
    2. `score_sites` — Score readiness (legacy min-max or V3 fixed anchors) + Erlang-C port screen
    3. `right_sizing` — Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056)
    4. `confidence` — Structured field-level data confidence (V3) / legacy confidence passthrough
    5. `peak_wait` — Peak-window Erlang and seeded discrete-event wait simulation (P10/P50/P90)
    6. `economics` — Lifecycle NPC: staged vs overbuild vs defer at 2036/2046/2056, low/base/high
    7. `emissions` — Net avoided CO2e with sourced grid factor + avoided-EVSE resource metric
    8. `scenario_table` — Assemble canonical scenario rows (all required contract fields)
    9. `contract` — Validate + write versioned hybrid CSV/JSON contract with manifest hashes
    10. `matlab_adapter` — Generate MATLAB input CSV from the contract (capacity_basis on every row)
    11. `summary` — Write run summary with headline totals and claims-discipline labels
  - **CLI subcommands (L350-381), 3 total:** `run` (`--mode {legacy_v2, milestone2_v3}` default `milestone2_v3`; `--out`; `--contract-dir`), `validate-contract <contract_dir>`, `docs`. Default out dir: `data/outputs/run_%Y%m%d_%H%M%S` (L363, **local time**, not UTC — inconsistent with `run_id` which is UTC, L97).
  - `validate-contract` runs `contract.validate_scenario_table` + `contract.verify_hash_chain` + `contract.validate_against_json_schema`, exits 1 on failure, else prints `"Contract valid: all rule checks, JSON Schema, and RT-10 hash chain PASS."` (L367-377).
  - `docs` writes `ROOT/docs/WORKFLOW_STEPS.md` (L380).
  - `BASE_LOAD_GROWTH_PER_YEAR = 0.008` (L35) — **result-changing constant living outside `config.py`**, labelled "commercial base-load growth planning proxy".
  - `run_id = f"{mode}_{UTCnow:%Y%m%dT%H%M%SZ}"` (L97).
  - **Deliberate-migration rule (L102-105, 115-125):** right-sizing is *always* driven by `scored_legacy`, never by V3 anchor scores, so RT-04 (25 starter / 48 pathway) reconciles. In V3 mode a `scoring_migration_report.csv` is written with `legacy_score/legacy_rank/v3_anchor_score/v3_anchor_rank/rank_change` plus a fixed `explanation` string.
  - **Output paths:** `site_results_milestone2_v3.csv`, `scoring_migration_report.csv`, `site_results_legacy_v2.csv`, `right_sizing_legacy_2035_2050.csv`, `right_sizing_v3_canonical.csv`, `data_confidence_v3.csv`, `peak_wait_simulation.csv`, `lifecycle_costs.csv`, `lifecycle_costs_portfolio.csv`, `avoided_evse_metric.csv`, `standards_register.csv`, `matlab_scenarios.csv`, `run_summary.json`, and the contract dir (default `<out>/contract`).
  - `_sessions_multiplier` (L71-76): baseline year → 1.0; `stress_combined` → `high × 1.15`; else the table value. `_sessions_by_year` (L79-92) linearly interpolates between horizon anchor points over `range(2026, 2057)` — **`2057` is a hardcoded literal** rather than `economics.END_YEAR + 1`.
  - Scenario-row constants: `capacity_basis = "placeholder"` (L265), `capacity_confidence = "none"` (L268), `managed_charging_policy = "none"` (L269), `energy_curtailed_kwh = 0.0` (L270), `service_capacity_kw`/`spare_capacity_kw` = `None` (L263-264), `source_date = "2026-06-24"` (L281), `source_id = "real_sites_v2+frozen_v2_outputs+anchors_v1"` (L282), `capacity_source` string says **"12/12 sites unconfirmed"** (L266).
  - `peak_factor = PEAK_WINDOW_SHARE / (PEAK_WINDOW_HOURS / max(hours,1))` (L258) = `0.55 × hours_open / 4`.
  - `public_or_fleet` only ever emits `"public"` or `"mixed"` (L244) — the schema also permits `"fleet"`, which is never produced.
  - `assumptions` dict (L293-305) embeds `emissions.net_co2e_kg(1000.0)` — a **1000 kWh sample calculation**, not a portfolio total.
  - Run-summary keys (L334-345): `right_sizing`, `contract_dir`, `scenario_rows`, `matlab_rows`, `starter_total_2026`, `pathway_total`, `legacy_starter_total`, `legacy_pathway_total`, `high_confidence_sites`, `claims_discipline` ("…capacity placeholder at 12/12 sites; demand uncalibrated; costs screening-class; nothing approved.").
- **Notes:**
  - `right_sizing_legacy_2035_2050.csv` is written **unconditionally, in both modes** (L131-132). In `milestone2_v3` runs this produces a 2035/2050-named artifact alongside the canonical one. It is correctly *named* legacy, so it is a labelled-legacy artifact rather than a horizon violation — but downstream consumers must not pick it up by accident.
  - `high_confidence_sites` will be **0** for the frozen contract: all 120 scenario rows carry `data_confidence = Low` (verified in `data/contract/v1/scenario_table.csv`).
  - `V3_HORIZON_LABELS` values `now / plus10 / plus20 / plus30` are the *contract-legal* labels (enum in `contract.py:89`). Any prose that renders these as "10/20/30-year" horizons is describing 2036/2046/2056 correctly; prose that renders them as 2035/2050 is not.

---

### src/fcf_m2/contract.py  (351 lines)
- **Role:** Builds, validates, and hash-seals the canonical cross-model data contract v1.
- **Kind:** authored + data-contract definition
- **Reads:** `sha256_file()` reads any path given; `verify_hash_chain()` reads `<contract_dir>/contract_manifest.json` and every table named in it.
- **Written by / read by:** Called by `workflow.run()` (`write_contract`, `sha256_file`) and `workflow.main()` (`validate_scenario_table`, `verify_hash_chain`, `validate_against_json_schema`). Its outputs in `data/contract/v1/` are consumed by MATLAB, Excel, Tableau, the static dashboard, and the presentation.
- **Key contents:**
  - **Contract file set (docstring L8-15, written L275-311):** `schema.json`, `scenario_table.csv`, `site_table.csv`, `source_provenance.csv`, `standards_register.csv`, `assumptions.json`, `contract_manifest.json`, `README.md`.
  - `REQUIRED_FIELDS` (L45-58): **48 fields**, from `contract_version` through `notes`.
  - `VALID_CASES = {"baseline","base","high","stress_combined"}` (L60); `VALID_HORIZONS = {2026, 2036, 2046, 2056}` (L61, derived from config).
  - **Hash algorithm: SHA-256**, streamed in 65536-byte chunks (`sha256_file`, L64-69).
  - **RT-10 manifest hash chain mechanics:** `write_contract` writes the six tables first, then computes `{name: sha256_file(out/name)}` over the fixed list `["schema.json","scenario_table.csv","site_table.csv","source_provenance.csv","standards_register.csv","assumptions.json"]` (L282-283, 291) and stores them under `manifest["tables"]`. Input hashes (`manifest["inputs"]`) are computed by the caller (`workflow.py:311-318`) over the five source files. `contract_manifest.json` itself is **not** self-hashed (it cannot be). `verify_hash_chain()` (L315-324) re-hashes each table and reports `"RT-10: {name} hash mismatch (stale contract)"`.
  - `build_schema()` (L72-129) — JSON Schema draft 2020-12. Load-bearing constraints: `site_id` pattern `^(FFX|PWC)[0-9]{3}$`; `jurisdiction` enum `["fairfax","pwc"]`; `public_or_fleet` enum `["public","fleet","mixed"]`; `horizon_year` enum `[2026,2036,2046,2056]`; `horizon_label` enum `["now","plus10","plus20","plus30"]`; `ports_active`/`ports_pathway_capacity` integers 0-100; `evse_power_kw` (0,5000]; `energy_per_session_kwh` 0-1000; `charging_window_hr` 0-24; `average_dwell_hr` 0-24; `peak_factor` 0-10; `utilization` 0-2 nullable; `capacity_basis` enum = `CAPACITY_BASIS_VALUES`; `capacity_confidence` enum `["high","medium","low","none"]`; `managed_charging_policy` enum `["none","clamp","energy_aware"]`; **`grid_factor_value` `{"const": 596.3}`**; `grid_factor_units` `{"const": "lb CO2e/MWh"}`; `data_confidence` enum `["High","Medium","Low"]`; `equity_indicator` 0-1 nullable.
  - **Rule validation `validate_scenario_table()` (L138-235):**
    - RT-01 identity: unknown `site_id`s; and `site_name` must equal the canonical `site_name_display` from `site_table`.
    - RT-02 completeness: duplicate `(site_id, horizon_year, scenario_name)`; per-site horizon set must equal `{2026,2036,2046,2056}`; `scenario_name` ⊆ `VALID_CASES`.
    - Unsupported horizon years fail explicitly (L174-176).
    - RT-03: `ports_active > ports_pathway_capacity` fails; `ports_active` must be non-decreasing across horizons within each non-baseline case.
    - **RT-04 hardcoded headline totals (L188-195): baseline `ports_active` sum must equal `25`; baseline `ports_pathway_capacity` sum must equal `48`.** Gated by `expect_legacy_totals=True` (default).
    - RT-05 unit ranges: `evse_power_kw` in (0,5000]; `charging_window_hr` in [0,24]; sessions floor `0.3` on active rows; non-negative `energy_required_kwh_day`.
    - RT-07 placeholder propagation: rows with `capacity_basis ∈ {placeholder, unknown, planning_proxy}` may not carry `capacity_confidence == "high"` and must have `"placeholder"` in `assumption_flag`; `capacity_basis` must be in the controlled vocabulary.
    - RT-08: `energy_delivered_kwh - energy_required_kwh_day×365 > 0.5` fails.
    - RT-09: `grid_factor_vintage` length ≥ 5 on rows with `net_co2e_kg`.
    - Provenance: `source_id` length ≥ 2 and `source_date` length ≥ 8 on every row.
  - `ContractValidationError` (L132-135); `validate_or_raise` (L238-241); `validate_against_json_schema` (L244-259, caps at ~21 problems, converts NaN→None before validating).
  - `write_contract` (L262-312) validates **before** writing anything, then writes tables, then the manifest, then `_write_readme`. Manifest also records `model_version`, `run_id`, `generated_utc`, `producer {package: fcf_m2, module: fcf_m2.contract}`, `grid_factor {source, value_lb_per_mwh: 596.3, vintage}`, `conventions {baseline_year 2026, horizons [2036,2046,2056], cases, discount_rate_real 0.03}`, and 4 `consumer_rules`.
- **Notes:**
  - **Docstring path is wrong:** L15 says the layout is `data_contract/v1/`; the real directory is **`data/contract/v1/`** (F-05).
  - **RT-06 is never implemented.** The docstring (L140) claims "RT-01..RT-07, RT-09" but the body implements RT-01,02,03,04,05,07,08,09,10 — RT-06 has no check, and RT-08 is implemented despite not being named in the docstring (F-06).
  - RT-02's per-site horizon loop `break`s after the first offending site (L167-168), so only one site is ever reported.
  - **I verified the frozen contract end to end (read-only):** all 6 table hashes match, all 5 input hashes match, 120 rows / 12 sites, baseline starter sum = **25**, pathway sum = **48**, horizons exactly `{2026,2036,2046,2056}`, cases exactly `{baseline,base,high,stress_combined}`, labels `{now,plus10,plus20,plus30}`, `grid_factor_value` uniformly `596.3`, `capacity_basis` uniformly `placeholder`, `data_confidence` uniformly `Low`, `contract_version 1.0.0`, `model_mode milestone2_v3`, single `run_id milestone2_v3_20260719T052322Z`. **The contract is internally consistent and not drifted.**

---

### src/fcf_m2/confidence.py  (131 lines)
- **Role:** Typed, field-level data-confidence scoring; replaces the legacy note-keyword heuristic so prose cannot move a score.
- **Kind:** authored
- **Reads:** consumes the `data/provenance/field_provenance_v1.csv` DataFrame passed in by `workflow._load_inputs()`.
- **Written by / read by:** `workflow.run()` → `data_confidence_v3.csv` and the `data_confidence` column of the scenario table.
- **Key contents:**
  - `SOURCE_CLASS_SCORES` (L22-33): `verified_utility 100`, `verified_facility 100`, `official_source 90`, `official_gis 90`, `public_web_reference 60`, `derived_public_data 55`, `planning_assumption 35`, `synthetic_model 30`, `unconfirmed 15`, `missing 0`.
  - `VERIFICATION_STATUS_ADJ` (L35-39): `reviewed +5`, `spot_checked 0`, `unreviewed -5` (unknown values also get `-5`, L80).
  - `STALENESS_THRESHOLD_DAYS = 730`, `STALENESS_PENALTY = 10` (L41-42). Unparseable/missing `source_date` also incurs the full 10-point penalty (L68-73).
  - Unresolved-flag penalty: **15 points** when `unresolved_flag ∈ {1, true, yes}` (L82).
  - `FIELD_GROUP_WEIGHTS` (L45-53), sums to 1.00: `electrical_service 0.25`, `site_use_and_demand 0.20`, `address_and_public_access 0.10`, `coordinates 0.05`, `parking_and_layout 0.15`, `safety_review_fields 0.15`, `equity_and_context 0.10`.
  - `REQUIRED_COLUMNS` (L55-56, 9): `site_id, field_group, source_class, verification_status, source_org, source_date, reviewer, assumption_type, unresolved_flag`.
  - **Exact thresholds — `level_for()` (L59-64): `score >= 75` → `"High"`; `score >= 50` → `"Medium"`; otherwise `"Low"`.**
  - `score_field()` (L78-83): `clamp(0,100, source_class_score + verification_adj − staleness − unresolved)`.
  - `validate_provenance()` (L86-98) rejects unknown `source_class` / `field_group` values; `build_confidence()` (L101-131) raises `ValueError` on any provenance problem and assigns the `missing` score (0) for any field group absent for a site. Output columns: `site_id`, `data_confidence_score_v3`, `data_confidence_level_v3`, `confidence_breakdown` (`"group=score; …"`).
- **Notes:** `_staleness_penalty` defaults `today` to `date.today()`, so **confidence output is a function of wall-clock time** — re-running the pipeline far enough in the future silently downgrades sites relative to the frozen contract (F-07). Every row in the frozen contract is `Low`, so `workflow`'s `high_confidence_sites` headline is 0.

---

### src/fcf_m2/emissions.py  (85 lines)
- **Role:** Net avoided CO2e per year of delivered energy, plus the avoided-EVSE (M4) resource metric.
- **Kind:** authored
- **Reads:** nothing (pure functions over config constants and a DataFrame).
- **Written by / read by:** `workflow.run()` calls `net_co2e_kg()` per scenario row and `avoided_evse_metric()` → `avoided_evse_metric.csv`; `net_co2e_kg(1000.0)` is embedded in `assumptions.json`.
- **Key contents:**
  - **eGRID factor: `GRID_FACTOR_LB_PER_MWH = 596.3`, imported from `config.py:91`. Sourced as "EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, total output emission rate CO2e", vintage "eGRID2023r2, accessed 2026-07-19".** The module never hardcodes a factor of its own.
  - `annual_energy_delivered_kwh()` (L30-34): `sessions_day × 9.5 × 365`, zero when `active_ports <= 0`.
  - `net_co2e_kg()` (L37-69) — the headline formula:
    - `grid_energy_mwh = (delivered_kwh / 0.92) / 1000`
    - `effective_factor = 596.3 × (1 − renewable_matched_share)`
    - `grid_kg = grid_energy_mwh × effective_factor × 0.45359237`
    - `miles = delivered_kwh / 0.30`
    - `displaced_kg = miles × 400.0 / 1000`
    - `net_co2e_avoided_kg = displaced_kg − grid_kg` — **explicitly never clipped** (docstring L6-7), may be negative.
    - Returns `grid_factor_value/units/source/vintage/next_refresh` and an `assumption_note` naming all four benchmark inputs.
  - `avoided_evse_metric()` (L72-85): `avoided_active_evse_ports = clip(ports_pathway − ports_active, lower=0)`; `avoided_network_fee_usd_yr = avoided_ports × 1000.0`. Note text cites "the client's decommissioning experience (**17 of 70 ports** taken offline)" (L75) and "~$1k/station/yr".
- **Notes:** `1000.0` at L79 duplicates `config.ECON["network_fee_usd_per_port_yr"] = 1000.0` instead of importing it — a silent drift point if the ECON value is ever changed (F-03). The "17 of 70 ports" figure is client anecdote in a docstring; it does not trace to `data/contract/v1/`.

---

### src/fcf_m2/economics.py  (180 lines)
- **Role:** Lifecycle net-present-cost model: overbuild vs staged vs defer, per site, over 2026-2056.
- **Kind:** authored
- **Reads:** nothing; operates on `SiteCostInputs` dataclasses assembled by `workflow.run()`.
- **Written by / read by:** `workflow.run()` → `lifecycle_costs.csv`, `lifecycle_costs_portfolio.csv`, and the `lifecycle_cost_nominal_usd` / `lifecycle_cost_npv_usd` / `avoided_overbuild_cost_usd` columns of the scenario table (taken from the `escalation_case == "base"`, `cost_case == "STG"` rows, `workflow.py:206, 231-234`).
- **Key contents:**
  - **Horizons: `END_YEAR = 2056` (L26), `YEARS = range(2026, 2057)` (L27).** NPC reported at `V3_HORIZONS` = 2036/2046/2056 only.
  - Three cases (docstring L5-8): `OVB` = energize full pathway in 2026; `STG` = starter now, pathway pre-built, energize on horizon targets; `DEF` = pathway only, zero active ports.
  - **ROI is deliberately not computed** (docstring L10-12: "no honest revenue line exists for free/low-fee public charging").
  - `SiteCostInputs` (L30-41): `site_id, ports_now, ports_pathway, staged_targets{2036,2046,2056}, trenching_ft, trench_cost_per_ft, service_upgrade_cost_usd, sessions_day_by_year`.
  - `civil_cost()` (L43-48): `(trenching_ft × trench_cost_per_ft + service_upgrade_cost_usd) × 1.25` (contingency), `× 1.8` if retrofit, `× (1+esc)^offset`.
  - `hardware_cost()` (L51-53): `n_ports × 6500 × 1.25 × (1+esc)^offset`.
  - `active_ports_profile()` (L56-73): **STG ramps to each horizon target 2 years early** (`year == hy - 2`, i.e. 2034 / 2044 / 2054), capped at pathway.
  - `annual_cash_flows()` (L76-132): baseline-year civil for all cases (STG/DEF additionally pay the **15% pathway premium**, L91); hardware on port additions; STG expansions after 2026 add **0.2 × a fresh civil run** as "pathway expansion install" (L103); replacement at `t == 10` (2036) of `active_ports × 2500 × (1+esc)^10`; opex = `active × (1000 + 400)` + `300` site admin when active + `sessions × 9.5 × 365 × $0.11/kWh`, all escalated by `(1+esc)^t`; OVB pays decommissioning in 2056 for `max(0, ports_pathway − staged_targets[2056])` ports at `$800` each.
  - `npc_at_horizons()` (L135-144): cumulative nominal and `Σ total/(1+0.03)^t` for `year <= hy`.
  - `compare_cases()` (L147-170): emits 9 rows per site per escalation case (3 horizons × 3 cost cases) with `avoided_overbuild_cost_usd = NPV(OVB) − NPV(STG)` attributed to the STG row only, and `estimate_class = "screening_planning_estimate"` on every row. Escalation cases run in `workflow` are `low 0.01 / base 0.025 / high 0.04`.
  - `portfolio_summary()` (L173-180): groupby `horizon_year × cost_case × escalation_case`, summed and rounded.
- **Notes:**
  - **Only one electronics replacement is modeled over a 30-year life** (`t == 10` exactly, L107). With `replacement_year_offset = 10` a 2026-2056 horizon should plausibly see refreshes at t=10, 20 and 30; modeling only t=10 systematically compresses the OVB-vs-STG gap that the whole "avoided overbuild" headline rests on (F-08).
  - `staged_targets.get(2056, …)` at L123 hardcodes the terminal year instead of using `V3_HORIZONS[-1]`.
  - `import numpy as np` (L21) is unused.
  - `active_ports_profile` for `STG` re-checks `year == hy - 2` inside a loop over all horizons each year; correct, but the 2-year lead is an undocumented "trigger-year proxy" that no doc I read in this lane states as a policy.

---

### src/fcf_m2/right_sizing.py  (284 lines)
- **Role:** Starter-port vs future-ready-pathway sizing, in both the legacy 2035/2050 form and the canonical V3 2026/2036/2046/2056 scenario grid.
- **Kind:** authored
- **Reads:** nothing; operates on the scored DataFrame.
- **Written by / read by:** `workflow.run()` → `right_sizing_legacy_2035_2050.csv` and `right_sizing_v3_canonical.csv`; `run_right_sizing_v3` internally calls `run_right_sizing_legacy` to fix the pathway (L209).
- **Key contents:**
  - `even_ceiling(value, minimum=2, maximum=12)` (L44-50): ceil, round up to even, clamp to [2,12].
  - `site_capacity_cap()` (L61-65): `even_ceiling(parking_spaces × 0.05, 2, 12)`; **returns 6 when `parking_spaces <= 0`.**
  - `ports_for_sessions()` (L53-58): sessions × multiplier → `queueing.choose_ports`, floor of 2.
  - `apply_strategy_floors()` (L68-113), legacy floor machinery keyed `h1_base/h1_high/h2_base/h2_high`:
    - `public_access < 1` → every target capped at **2**, return immediately.
    - Tier 1 → floors `h1_base>=4, h1_high>=6, h2_base>=6, h2_high>=8`.
    - elif `score >= 50 and rank <= 6 and "garage" not in site_type` → `4/4/4/6`.
    - elif Tier 2 → `h1_high>=4, h2_base>=4, h2_high>=4`.
    - `existing_ports_total >= 50 and score < 45` → caps `2/4/4/4`.
    - `electrical_risk_level == "high"` → caps `ports_now<=2, h1_base<=4, h1_high<=4, h2_base<=4, h2_high<=6`.
  - `build_strategy()` (L116-144), ordered: `do_not_advance_general_public_buildout` (non-public) → `electrical_review_before_expansion` (high risk) → `garage_review_before_buildout` ("garage" in site_type) → `install_now_and_make_future_ready` (Tier 1 **or `rank <= 3 and score >= 50`**) → `starter_install_with_expandable_design` (score >= 45) → `monitor_due_to_nearby_supply` (existing_ports >= 50) → `monitor_or_small_pilot`.
  - `_future_ready()` (L158-162): `max(ports_now, h1_high, h2_base)`, raised to `min(h2_high, cap)` for Tier 1, then capped at `cap`. **This is what produces the 48-port pathway total.**
  - `run_right_sizing_legacy()` (L165-197): multipliers `h1_base 1.8, h1_high 2.5, h2_base 3.0, h2_high 4.5`; output columns `site_id, site_name, model_rank, readiness_score, recommendation_tier, electrical_risk_level, expected_sessions_day_now, model_recommended_ports_now, ports_now, ports_2035_base, ports_2035_high, ports_2050_base, ports_2050_high, site_capacity_cap, future_ready_capacity, expansion_strategy, right_sizing_reason`. **2035/2050 appear only here and are correctly scoped to `legacy_v2`.**
  - `run_right_sizing_v3()` (L200-271): pathway and `ports_now` are taken from the legacy result (L215-216); horizon targets use V3 multipliers mapped `2036→h1`, `2046→h2`; 2056 computed directly and floored at the 2046 value; `stress_combined` = `high × 1.15` floored at the corresponding high value; everything capped at `site_capacity_cap`. Then **monotonic non-decreasing enforcement across horizons per case (RT-03) followed by saturation cap at `max(pathway, ports_now)`** (L246-254). Output rows: `site_id, site_name, model_rank, horizon_year, case, ports_active, ports_pathway, site_capacity_cap, expansion_strategy, right_sizing_reason`; grid is 2026(baseline) + 3 horizons × 3 cases = 10 rows/site → 120 rows (matches the frozen contract).
  - `_merge_risk_defaults()` (L274-284): defaults `electrical_risk_level` to `"medium"`, reconstructs `existing_ports_total` if absent.
- **Notes:** `run_right_sizing_v3` recomputes the entire legacy right-sizing internally (L209) even though `workflow` already computed it (L131) — duplicated work, and a divergence risk if the two are ever fed different frames. The `parking_spaces <= 0 → cap 6` branch is an unexplained magic default.

---

### src/fcf_m2/queueing.py  (55 lines)
- **Role:** The legacy-exact Erlang-C screen and port chooser; deliberately frozen.
- **Kind:** authored (declared "exact port of the accepted legacy V2 implementation", L1)
- **Reads:** nothing.
- **Written by / read by:** `scoring.choose_ports`, `right_sizing.ports_for_sessions`, `peak_wait.peak_window_wait`, `workflow` (direct `erlang_c` call at L220).
- **Key contents:**
  - `erlang_c(lambda_hr, mu_hr, ports)` (L17-32): returns `(nan,nan,nan)` when `ports<=0 or mu<=0`; `(1.0, inf, utilization)` when `utilization >= 1`; otherwise standard Erlang-C with `utilization = λ/(c·μ)`, `traffic_load = λ/μ`, `wait_hours = P(wait)/(c·μ − λ)`.
  - `choose_ports(...)` (L35-55): scans `ports` 1..**20** (`MAX_PORTS_SEARCH`), returns the first count with finite wait, `utilization <= 0.70` and `wait_minutes <= 10.0`; otherwise returns the last (20-port) tuple as fallback.
  - `arrivals_per_hour = sessions_day / max(hours_open, 1)`; `service_rate = 1 / max(avg_session_hr, 0.1)`.
- **Notes:** Uses `math.factorial(n)` in a Python loop — fine at c<=20. The fallback path silently returns a 20-port result that may violate both targets; callers do not distinguish "met targets" from "fell back".

---

### src/fcf_m2/peak_wait.py  (113 lines)
- **Role:** Peak-window Erlang-C and a seeded discrete-event M/G/c simulation producing P10/P50/P90 waits. Additive to (never replacing) the legacy screen.
- **Kind:** authored
- **Reads:** nothing.
- **Written by / read by:** `workflow.run()` → `peak_wait_simulation.csv` (columns `site_id, ports, mean_wait_min, p10_wait_min, p50_wait_min, p90_wait_min, peak_p90_wait_min, peak_erlang_wait_min, sim_utilization, seed`) and the `peak_wait_minutes` scenario column.
- **Key contents:**
  - `peak_window_wait()` (L22-32): `λ_peak = sessions_day × 0.55 / min(4.0, hours_open)`, `μ = 1/max(avg_session_hr, 0.1)`, then `erlang_c`. Returns `(wait_min, utilization)`, `inf` when saturated.
  - `SimResult` dataclass (L35-45): `ports, n_days, mean_wait_min, p10/p50/p90_wait_min, peak_p90_wait_min, mean_utilization, seed`.
  - `simulate_waits()` (L48-103): **`n_days = 400`, `seed = 20260719`, `peak_share = 0.55`, `peak_hours = 4.0`, `dwell_cv = 0.45`** (the CV default is hardcoded here, not in config). Non-homogeneous Poisson arrivals (Poisson counts for peak and off-peak separately), lognormal dwell with `σ² = ln(1+cv²)`, `μ_log = ln(mean) − σ²/2`, greedy assignment to the earliest-free port. `mean_utilization = busy_time / (ports × hours_open × n_days)`.
  - `_off_window_arrivals()` (L106-113): uniform over open hours excluding the peak window, clipped to `[0, hours_open]`.
- **Notes:** Reproducible only because the seed is fixed; the same seed is reused for every site (`workflow.py:172` never varies it), so per-site draws are correlated. `simulate_waits` is called with the default `n_days=400` for all 12 sites on every run — the main runtime cost of the pipeline.

---

### src/fcf_m2/demand.py  (146 lines)
- **Role:** Demand-model status record, provenance, and the calibration path with explicit refusal logic.
- **Kind:** authored
- **Reads:** `load_observed(path)` reads a CSV; the documented location is `data/observed/observed_sessions_template.csv` (exists, 102 bytes — template only).
- **Written by / read by:** `workflow.run()` serializes `current_model_record().__dict__` into `assumptions.json` under `demand_model`. `calibrate()` and `write_record()` are **not called anywhere in the pipeline** — they are the forward path.
- **Key contents:**
  - Acceptance gates (L26-28): `MIN_OBSERVED_ROWS = 60` ("~2 months of daily data"), `MIN_SITES_OBSERVED = 3`, `MAX_ACCEPTABLE_MAPE = 0.50` ("screening-grade acceptance; team may tighten").
  - `OBSERVED_COLUMNS` (L30): `site_id, date, sessions, energy_kwh, mean_dwell_min, facility_visitors_day`.
  - `DemandModelRecord` (L33-42): `status, coefficients, floor_sessions, provenance, calibrated_at, calibration_metrics, n_observed_rows, n_observed_sites`.
  - `current_model_record()` (L45-51): status `"synthetic_uncalibrated"`, the four config coefficients, floor `0.3`, and the "no published derivation exists" provenance string.
  - `calibrate()` (L63-131): non-negative least squares (`np.linalg.lstsq` then `np.clip(coef, 0, None)`) on `[visitors_day, employees_day, nearby_jobs_1mi, nearby_households_1mi×(1+ev_share_local)]`; 25% holdout, `seed=0`; **refuses** (returns the uncalibrated record with `calibration_metrics["refused"]=True`) on insufficient rows/sites, on site mismatch, or when holdout MAPE > 0.50. On success returns status `"calibrated_observed"` with `holdout_mape, n_fit, n_holdout, pred_p10/p50/p90`.
  - `presentation_caveat()` (L140-146): the uncalibrated string is *"Demand estimates use a synthetic, uncalibrated screening formula. No observed charging sessions exist yet; values are planning inputs, not forecasts."*
- **Notes:** The refusal design is genuinely load-bearing for claims discipline and Phase 4 should preserve it. Note the model is fit **without an intercept** and against **mean daily sessions per site**, so 3 sites can fit 4 coefficients — an underdetermined system that `lstsq` will happily solve; `MIN_SITES_OBSERVED = 3 < 4 coefficients` is a latent overfit hazard.

---

### src/fcf_m2/triggers.py  (88 lines)
- **Role:** The proposed equity-aware expansion-trigger policy, with an explainable rule trace. **Phase 4 will run `evaluate()` against observed data.**
- **Kind:** authored
- **Reads:** nothing; reads `config.TRIGGER_POLICY` only.
- **Written by / read by:** `workflow.run()` calls only `status_for_contract(False)` (L280), which sets `expansion_trigger_status` on every scenario row. `evaluate()` is currently **unused by the pipeline**.
- **Key contents:**
  - `ObservedMetrics` (L19-27): `site_id, months_observed, avg_utilization (0-1), p90_wait_min, uptime (0-1), equity_index_percentile (0-1)`.
  - `TriggerDecision` (L29-35): `site_id, outcome, equity_override_applied, rule_trace, policy_status` (defaults to `"proposed_default_pending_team_and_client_adoption"`).
  - **`evaluate()` gate order (L38-82):**
    1. `metrics is None` → `awaiting_observed_data`.
    2. `months_observed < 6` → `hold`.
    3. `uptime < 0.97` → `hold` ("fix reliability before trusting utilization data").
    4. `ports_active >= ports_pathway` → `hold` (pathway gate, no headroom).
    5. **Equity override:** if enabled and `equity_index_percentile >= 0.60`, the utilization gate drops from **0.40 to 0.25** and `equity_override_applied = True`.
    6. `avg_utilization >= util_gate` **OR** `p90_wait_min >= 10.0` → `expand_review_recommended`, with a trace line recording `budget_gate = human_approval_required` and "this tool never authorizes expansion".
    7. else → `hold`.
  - `status_for_contract()` (L85-88): returns `"awaiting_observed_data (proposed policy, not adopted)"` when there is no observed data.
- **Notes:** Outcome vocabulary is exactly `{expand_review_recommended, hold, awaiting_observed_data}`. The equity override is OR-ed with the wait threshold, so a high-equity site can trigger on wait alone even below 25% utilization. Trigger outcomes are never written to a CSV today — only the frozen `awaiting_observed_data` string reaches the contract.

---

### src/fcf_m2/matlab_adapter.py  (75 lines)
- **Role:** Projects the canonical contract onto the MATLAB input schema; replaces the hand-built `site_year_scenarios_from_andy_v2.csv`.
- **Kind:** authored (generator of `matlab_scenarios.csv`)
- **Reads:** the in-memory `scenario_table` and a `site_meta` frame; writes to the path given by `workflow` (`<out>/matlab_scenarios.csv`).
- **Written by / read by:** Called at `workflow.py:330-331`. `site_meta` is assembled at `workflow.py:322-329` from `data/inputs/legacy_matlab_site_meta.csv` joined to `scored_legacy[["site_id","model_rank"]]` and the risk fixture's `electrical_risk_level`.
- **Key contents — exactly what is exported (`MATLAB_COLUMNS`, L14-20, 22 columns in this order):**
  `scenario_id, site_id, site_name, horizon_year, case, ports, charger_power_kW, spare_capacity_kW, service_capacity_kW, capacity_basis, capacity_source, base_load_mean_kW, base_load_peak_kW, arrival_start_hr, arrival_end_hr, dwell_hr, sessions_per_day, energy_per_session_kWh, managed_charging_policy, model_rank, electrical_risk_level, source_note`.
  - Renames: contract `scenario_name` → `case`; `ports_active` → `ports`; `evse_power_kw` → `charger_power_kW`; `average_dwell_hr` → `dwell_hr`. Note the **kW/kWh columns use MATLAB-style capitalisation** while the contract uses lowercase `_kw`.
  - NaN capacity is exported as the **empty string** `""` (L47-48), not `NaN` — deliberate, so MATLAB reads a missing value rather than a number.
  - **Placeholder guard (L36-38, 61-66):** `placeholder = capacity_basis not in ("verified_utility","verified_facility")`; each row's `source_note` becomes `"Generated from canonical contract {contract_version} run {run_id}. CAPACITY IS A PLANNING PLACEHOLDER - no feasibility claim permitted. Do not hand-edit; regenerate via fcf_m2.matlab_adapter."` (or "Capacity verified. " when not placeholder).
  - Prints to stdout when any row is non-verified: `"WARNING: {warned}/{len(df)} MATLAB scenario rows carry non-verified capacity_basis - placeholder captions are mandatory on every capacity visual."` (L73-74). For the frozen contract this is **120/120**.
- **Notes:** Creates parent directories itself (L70). It is the ML-04 counterpart guard; the MATLAB side is expected to refuse feasibility claims on the same field (see `contract.py:305` consumer rule).

---

### src/fcf_m2/standards.py  (224 lines)
- **Role:** Standards traceability register — site × standard × lifecycle stage, with adopted vs latest edition and open AHJ questions.
- **Kind:** authored (hand-curated reference data embedded in code)
- **Reads:** nothing; `build_register()` takes the `site_table` frame.
- **Written by / read by:** `workflow.run()` → `standards_register.csv` in the run dir and in the contract.
- **Key contents:**
  - `STANDARDS` (L15-178), **9 entries**. Active (7): `UL2594` (highlighted_safety, 3rd ed. 2022-12-15), `UL3600` (highlighted_sustainability, 1st ed. 2023-01-09), `UL2231` (supporting_essential, 2021 editions), `NEC625` (supporting_essential, **2020 NEC via 2021 USBC, effective 2024-01-18; 2023 NEC published but NOT adopted in Virginia**), `VA-USBC-SFPC` (2021 editions, 2024 cycle ~2027), `ACCESS-BOARD-EVSE` (**NPRM 2024-09-03; final rule NOT issued as of 2026-07-19**), `OCPP-ISO15118` (supporting_protocol, explicitly "NOT ULSE standards").
    Conditional / out of scope (2): `UL2202` (DCFC — "No DCFC in the current plan"), `UL9540-9540A-NFPA855` (UL 9540A 5th ed. 2025-03-12; NFPA 855 2026 ed. — "**battery_storage_flag=0 at all 12 sites**").
  - `STAGES` (L180-181, 7): `design, procurement, installation, commissioning, operation, emergency_response, end_of_life`.
  - `build_register()` (L184-224): conditional standards emit exactly one `stage="n/a"` row per site with `applicability="conditional_out_of_scope"`; active standards emit one row per stage whose requirement is not the em-dash placeholder `"—"`. Output columns: `site_id, standard_id, standard_title, role, stage, requirement, adopted_edition, latest_edition, applicability, evidence_required, authority, open_ahj_question`.
- **Notes:** **Dead reference:** the docstring (L8) says "Editions verified 2026-07-19 (see `research/CURRENT_FACTS_SOURCE_REGISTER.md`)". **`research/` does not exist in this repo** — the live file is `docs/methodology/current-facts-source-register.md` (F-09). All edition dates are as-of 2026-07-19 and will go stale; the Access Board rule status in particular is time-sensitive and is flagged in-file ("rule status must be re-checked at design time", L134).

---

### src/fcf_m2/visuals.py  (81 lines)
- **Role:** The single choke point for chart provenance footers, plus the automated footer-audit hook (PY-17).
- **Kind:** authored
- **Reads:** `audit_footer_metadata()` reads a footer-log JSON and globs `*.png` in a chart dir.
- **Written by / read by:** Used by `gis_offline.py`; the repo's `dashboard/static/footer_log.json` is the corresponding artifact. Not called from `workflow.py`.
- **Key contents:**
  - Palette (L22-26): `BEIGE "#F5F0E6"`, `DARK_GREEN "#1B4332"`, `MID_GREEN "#40694F"`, `BLACK "#1A1A1A"`, `ACCENT "#B08948"`. Backend forced to `Agg` (L22 of imports).
  - `footer()` (L43-53) stamps `"Source: … · Vintage: … · Scenario: … · Model: fcf_m2 v{MODEL_VERSION} / contract v{SCHEMA_VERSION}"` plus an optional `"Assumption: …"`, at figure coords (0.01, 0.005), fontsize 6.2, and appends the entry to the module-global `_FOOTER_LOG`.
  - `save()` (L56-68): `dpi=200`, `bbox_inches="tight"`, closes the figure, attaches **`_FOOTER_LOG[-1]`** to the saved path and optionally appends to a log JSON.
  - `audit_footer_metadata()` (L71-81): returns `"unlabeled chart (no footer log entry): {name}"` for every PNG not in the log.
- **Notes:** `save()` blindly takes the **last** footer entry, so calling `save()` without a preceding `footer()` mislabels the file with a previous chart's provenance. The `_FOOTER_LOG` global also means footer state leaks across figures within a process.

---

### src/fcf_m2/gis_offline.py  (80 lines)
- **Role:** Offline-reproducible candidate-site map from cached boundaries; no network access on any code path.
- **Kind:** authored
- **Reads:** `ROOT/data/cache/boundaries/tl_2024_va_counties.geojson` (L29) — **exists**, 171,997 bytes, with `data/cache/boundaries/ATTRIBUTION.md` alongside it. Also reads `FCF_OFFLINE` from the environment (L74).
- **Written by / read by:** Not called from `workflow.py`; invoked by the dashboard/visual scripts. Depends on `visuals.py` for palette, styling, footer, and save.
- **Key contents:**
  - `build_site_map(sites, out_path, title="Candidate Site Readiness Map")` (L44-80).
  - Dual path: `geopandas` if importable (`gdf.boundary.plot`), else `_plot_boundary_pure()` (L32-41) which parses the GeoJSON with the stdlib `json` module and plots each ring with matplotlib at `linewidth=0.4, alpha=0.6`.
  - Top-3 sites (`nsmallest(3, "model_rank")`) rendered at `s=140` in `DARK_GREEN`; others `s=60` in `ACCENT`; each annotated with `site_id`. Axis padding `0.15` degrees.
  - Footer: `source="US Census TIGER/Line 2024 (cached in repo) + real_sites_v2.csv"`, `source_date="TIGER 2024 / sites 2026-06-24"`, `scenario="site map, {mode}"` where mode is `"offline (FCF_OFFLINE set)"` or `"offline-capable (cached boundaries)"`, `assumption="no basemap tiles in offline mode"`.
- **Notes:** The docstring says "attribution in `ATTRIBUTION.md`" (L5) without a path; the file is at `data/cache/boundaries/ATTRIBUTION.md`, **not** at the repo root — a reader following the reference literally will not find it. `FCF_OFFLINE` is purely cosmetic: it only changes the footer string, it does not assert or enforce anything (the docstring admits this, L11-13).

---

### src/README.md  (31 lines)
- **Role:** Navigation and one-line responsibility table for the `fcf_m2` package.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** Linked from the repo root README (`[← repository root](../README.md)`, L3); links out to `../README.md`, `../tests/README.md`, `../scripts/README.md`, `../scripts/verify.sh`. **All four link targets exist** (verified).
- **Key contents:** A 15-row module table (L8-24) covering `config, scoring, queueing, peak_wait, right_sizing, demand, confidence, economics, emissions, standards, triggers, contract, matlab_adapter, visuals/gis_offline, workflow`; run command `python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run` (L26); statement that outputs land in `data/outputs/` (gitignored — confirmed in `.gitignore`); and a closing "Limitations that ship with the code: demand uncalibrated, capacity placeholder at all sites, screening-class costs".
- **Notes:** Line 14 says right_sizing covers "legacy 2035/2050 and canonical 2026/2036/2046/2056" — **a correct, explicitly-labelled legacy reference**, not a horizon violation. Accurate against the code as read; no stale claims found. `__init__.py` is (correctly) not listed.

---

### src/fcf_m2.egg-info/PKG-INFO  (19 lines)
- **Role:** setuptools-generated distribution metadata for the editable install.
- **Kind:** generated (setuptools, from `pyproject.toml`)
- **Reads:** n/a
- **Written by / read by:** Written by `pip install -e .` / `setuptools`; read by pip/importlib.metadata.
- **Key contents:** `Metadata-Version: 2.4`, `Name: fcf-m2`, **`Version: 3.0.0`**, `Requires-Python: >=3.11`, core deps `numpy>=1.26, pandas>=2.1, matplotlib>=3.8, jsonschema>=4.20`, extras `gis` (geopandas>=0.14, contextily>=1.5, xyzservices>=2024.0), `test` (pytest>=8.0, pytest-cov>=4.1), `presentation` (pillow>=10.0, reportlab>=4.0). Summary ends "Planning prototype only - not an engineering, permitting, or procurement tool."
- **Notes:** **Consistent with `pyproject.toml`** — name, version 3.0.0, python floor, all four core deps and all three extras match exactly. Version also matches `config.MODEL_VERSION = "3.0.0"`. No drift.

---

### src/fcf_m2.egg-info/SOURCES.txt  (27 lines, no trailing newline)
- **Role:** setuptools file manifest for the sdist.
- **Kind:** generated (setuptools)
- **Reads:** n/a
- **Written by / read by:** Written by setuptools; not read by the model.
- **Key contents:** `README.md`, `pyproject.toml`, all 17 `src/fcf_m2/*.py`, the 5 egg-info files, and 4 test modules: `tests/test_contract_and_integration.py`, `tests/test_legacy_golden.py`, `tests/test_modules.py`, `tests/test_scoring_and_queueing.py`.
- **Notes:** **Stale.** The `tests/` directory actually contains 8 entries — `conftest.py`, `README.md`, `fixture_legacy_v2_right_sizing.csv`, `fixture_legacy_v2_site_results.csv` plus the 4 test modules. `conftest.py` is absent from the manifest even though `git log` shows it was committed in the **same commit** (`252099f`) as the egg-info, meaning the metadata was generated from an earlier working-tree state and then committed as-is (F-10). Harmless for an editable install; misleading as a manifest.

---

### src/fcf_m2.egg-info/requires.txt  (17 lines)
- **Role:** setuptools dependency manifest.
- **Kind:** generated (setuptools, from `pyproject.toml`)
- **Reads:** n/a
- **Written by / read by:** setuptools/pip.
- **Key contents:** base `numpy>=1.26, pandas>=2.1, matplotlib>=3.8, jsonschema>=4.20`; `[gis]` geopandas>=0.14, contextily>=1.5, xyzservices>=2024.0; `[presentation]` pillow>=10.0, reportlab>=4.0; `[test]` pytest>=8.0, pytest-cov>=4.1.
- **Notes:** Exact match to `pyproject.toml` (extras alphabetised by setuptools). No drift. Note `geopandas` is genuinely optional — `gis_offline.py` has a working pure-matplotlib fallback.

---

### src/fcf_m2.egg-info/top_level.txt  (1 line)
- **Role:** Declares the top-level importable package name.
- **Kind:** generated (setuptools)
- **Reads:** n/a
- **Written by / read by:** setuptools/pip.
- **Key contents:** `fcf_m2`
- **Notes:** Correct — matches `[tool.setuptools.packages.find] where = ["src"]`. Note the *distribution* name is `fcf-m2` (hyphen) while the *import* name is `fcf_m2` (underscore).

---

### src/fcf_m2.egg-info/dependency_links.txt  (1 byte)
- **Role:** Legacy setuptools external-download-URL list.
- **Kind:** generated (setuptools)
- **Reads:** n/a
- **Written by / read by:** setuptools; obsolete in modern pip.
- **Key contents:** A single newline character (`od -c` → `\n`). Empty.
- **Notes:** Vestigial. Its only significance is that all five egg-info files are **tracked in git** (`git ls-files` confirms) while `.gitignore` never excludes `*.egg-info/` — build artifacts committed to VCS.

---

## Cross-cutting notes for later phases

**Horizon-convention audit of this lane: clean.** Every occurrence of 2035 or 2050 inside `src/` sits
inside an explicitly legacy-scoped construct: `config.LEGACY_GROWTH_MULTIPLIERS` keys
(`2035_base`/`2035_high`/`2050_base`/`2050_high`, `config.py:31-37`), `right_sizing.run_right_sizing_legacy`
output columns (`ports_2035_base` … `ports_2050_high`, `right_sizing.py:188-191`), the
`right_sizing_legacy_2035_2050.csv` filename (`workflow.py:132`), and three docstring/README lines that
name them as the legacy mode. No `"Now"` / `"10-year"` / `"20-year"` / `"30-year"` prose appears in `src/`;
the V3 labels are the contract-legal enum `now / plus10 / plus20 / plus30`.

**eGRID audit of this lane: clean.** `596.3` appears once, in `config.py:91`, and flows to `emissions.py`,
`contract.build_schema()` (as a JSON-Schema `const`), and `contract_manifest.json`. **`590.2` appears
nowhere in `src/`.** Repo-wide it survives only in four explicit correction notes (`CHANGELOG.md:24`,
`docs/methodology/current-facts-source-register.md:7`, and two report files) — see F-11.

**Numbers that DO trace to `data/contract/v1/` (verified by direct read of the frozen artifacts):**
25 starter ports, 48 pathway ports, 120 scenario rows, 12 sites, horizons {2026,2036,2046,2056},
596.3 lb CO2e/MWh, contract_version 1.0.0, model_version 3.0.0, discount rate 0.03,
`capacity_basis = placeholder` on 120/120 rows, `data_confidence = Low` on 120/120 rows.

**Numbers that do NOT trace to `data/contract/v1/`** (they are code constants or docstring anecdotes):
`BASE_LOAD_GROWTH_PER_YEAR 0.008`, `EV_SHARE_HIGH_BENCHMARK 0.10`, `dwell_cv 0.45`,
`MIN_OBSERVED_ROWS 60` / `MIN_SITES_OBSERVED 3` / `MAX_ACCEPTABLE_MAPE 0.50`,
the confidence score table and thresholds (75/50), `STALENESS_THRESHOLD_DAYS 730`,
`even_ceiling` bounds 2/12, `parking_spaces × 0.05`, the `parking_spaces<=0 → 6` default,
and the "**17 of 70 ports**" client decommissioning anecdote in `emissions.py:75`.

---

## Findings index

- **F-01** — `SUBSCORE_WEIGHTS` / `DRIVERS` / "Earned:/Forgone:" exist only in the explorer, not in the repo scorer; the explorer independently re-implements the weights. (high)
- **F-02** — `config.py` docstring claims it holds every result-changing constant; at least eight live elsewhere. (medium)
- **F-03** — `emissions.py:79` hardcodes `1000.0` instead of `ECON["network_fee_usd_per_port_yr"]`. (medium)
- **F-04** — 35% of `feasibility_subscore` is weighted on `spare_capacity_kw`, which is 0 at all 12 sites. (medium)
- **F-05** — `contract.py:15` documents the contract at `data_contract/v1/`; the real path is `data/contract/v1/`. (medium)
- **F-06** — RT-06 is never implemented; the `validate_scenario_table` docstring misstates the implemented rule set. (medium)
- **F-07** — `confidence.py` staleness uses `date.today()`, making confidence output wall-clock-dependent and non-reproducible. (medium)
- **F-08** — `economics.py` models only one electronics replacement (t=10) across a 30-year lifecycle. (medium)
- **F-09** — `standards.py:8` cites `research/CURRENT_FACTS_SOURCE_REGISTER.md`, which does not exist. (medium)
- **F-10** — `SOURCES.txt` omits `tests/conftest.py` though both were committed together; egg-info is stale build metadata tracked in git. (low)
- **F-11** — `590.2` survives in four documents, all as explicitly-labelled correction notes. (info)
- **F-12** — `scoring.access_adjustment` is computed and exported but never used in any formula. (low)
- **F-13** — `anchor_set_v1.json` declares an `ev_share_local` anchor the code never reads. (low)
- **F-14** — Tier-1 rank cutoff differs between `scoring.recommendation_tier` (`rank<=2`) and `right_sizing.build_strategy` (`rank<=3`). (low)
- **F-15** — `workflow.main` default out dir uses local time while `run_id` uses UTC. (low)
