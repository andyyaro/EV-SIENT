# LANE L02 — TESTS AND SCRIPTS (Phase-0 ground-truth inventory)

Repo root: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (git clone, branch `v4-platform`, HEAD `95e91e0 docs(v4-program): initialize program ledger`).
All paths below are repo-relative unless stated. Every file assigned to this lane was read end-to-end.

**Verification actually executed during this inventory (read-only; `git status --porcelain` confirmed empty after each):**
- `venv/bin/python -m pytest tests/ -q` → **80 passed, 0 failed, 0 skipped**.
- with `--cov=fcf_m2 --cov-fail-under=80` → **TOTAL 92.15 %**, "Required test coverage of 80% reached."
- `scripts/check_internal_links.py` → `internal links OK` (exit 0).
- `verify.sh` gate 5 (docs) → PASS. Gate 6 (dashboard footers) → PASS. Gate 9 (25 MB) → PASS.
- **`verify.sh` gate 7 (secrets) → FAIL. `verify.sh` gate 8 (absolute paths) → FAIL.** (Details in the `verify.sh` entry.)
- A full V3 workflow run into the scratchpad (`--out <scratchpad>/v3run`) to compare generated vs tracked artifacts. Nothing was written inside the repo.

---

## tests/

### tests/conftest.py
- **Role:** pytest session fixtures — puts `src/` on `sys.path` and supplies the shared input frames, anchor set, frozen golden fixtures, a scored legacy frame and one shared full V3 run.
- **Kind:** authored
- **Reads:** `ROOT/src` (sys.path insert, line 8); `data/inputs/real_sites_v2.csv` (line 13); `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` (line 18); `data/anchors/anchor_set_v1.json` (line 24); `tests/fixture_legacy_v2_site_results.csv` (line 29); `tests/fixture_legacy_v2_right_sizing.csv` (line 34).
- **Written by / read by:** authored by hand; consumed implicitly by all four test modules.
- **Key contents:**
  - `ROOT = Path(__file__).resolve().parents[1]` (line 7).
  - Session-scoped fixtures: `sites`, `risk`, `anchors`, `golden_site_results`, `golden_right_sizing`, `scored_legacy`, `v3_outputs`.
  - `anchors` calls `fcf_m2.scoring.load_anchor_set`.
  - `scored_legacy` (lines 38-42) = `enrich_and_score(sites, mode="legacy_v2")` merged with `risk[["site_id","electrical_risk_level"]]` on `site_id`, then `add_tiers(...)`.
  - `v3_outputs` (lines 46-51) = `workflow.run("milestone2_v3", tmp_path_factory.mktemp("v3run"))`; returns `(out_dir, result_dict)`.
- **Notes:** the V3 integration run is written to a pytest tmp dir, never into the repo — that is why `data/outputs/` can stay gitignored/absent and the suite still passes. The electrical-risk input is a **frozen** file with the freeze date `2026-07-19` baked into the filename; renaming/refreshing it silently changes the legacy golden.

### tests/README.md
- **Role:** one-page guide to the verification suite.
- **Kind:** authored
- **Reads:** n/a
- **Written by / read by:** linked from the repo root README via `[← repository root](../README.md)` (line 3, resolves).
- **Key contents:**
  - Line 5: "80 pytest tests; CI enforces a coverage floor of 80% (actual ≈92%)." — **verified accurate**: 78 `def test_` functions, one of which is `@pytest.mark.parametrize` with 3 cases → 80 collected; measured coverage 92.15 %.
  - Per-file coverage table (lines 7-12) naming: bit-exact legacy reproduction, cohort invariance, demand-calibration refusal, DES determinism/percentiles, typed confidence, "staged < overbuild at every horizon", emissions vintage, trigger policy incl. equity override, contract rule/schema/hash-chain with deliberate corruption, cross-model reconciliation, offline GIS, chart-footer QA, doc-drift.
  - Line 14: `make test` or `python -m pytest tests/ -q`.
  - Lines 15-17: the golden fixtures are the frozen outputs of the accepted V2 baseline run (**2026-07-19**); "do not regenerate them to make a failure disappear."
- **Notes:** the stated `make test` target does **not** apply the coverage floor (`Makefile:9` uses `--cov-report=term` with no `--cov-fail-under`); only `scripts/verify.sh:24` and `.github/workflows/tests.yml:28` enforce 80.

### tests/test_legacy_golden.py — 38 lines, 4 tests
- **Role:** locks `legacy_v2` mode to the frozen V2 baseline bit-for-bit.
- **Kind:** authored
- **Reads:** the `scored_legacy`, `golden_site_results`, `golden_right_sizing` fixtures; imports `fcf_m2.right_sizing.run_right_sizing_legacy`.
- **Written by / read by:** consumes the two `tests/fixture_legacy_v2_*.csv` files.
- **Key contents / golden values:**
  - `test_scores_match_frozen_baseline` (line 6): tolerance `abs(...) < 1e-9` on rounded-to-6dp columns `readiness_score, demand_subscore, feasibility_subscore, safety_subscore, equity_subscore, expected_sessions_day`.
  - `test_ranks_and_ports_match` (line 14): exact equality on `model_rank` and `recommended_ports_now`.
  - `test_right_sizing_matches_frozen_baseline` (line 21): exact equality on `ports_now, ports_2035_base, ports_2035_high, ports_2050_base, ports_2050_high, future_ready_capacity, site_capacity_cap, expansion_strategy`.
  - `test_headline_totals` (lines 31-38): **`rs["ports_now"].sum() == 25`**, **`rs["future_ready_capacity"].sum() == 48`**, top-ranked `site_id == "FFX002"`, **`abs(readiness_score - 58.8) < 0.05`**.
- **Notes:** the `2035`/`2050` column names on lines 25-26 are **correctly-labelled legacy** — the module docstring says "legacy_v2 mode must reproduce the frozen V2 baseline exactly" and the function is `run_right_sizing_legacy`. Not a horizon-convention defect. This is the only place in the lane where 2035/2050 appear.

### tests/test_scoring_and_queueing.py — 93 lines, 16 test functions (18 collected after parametrize)
- **Role:** unit + property tests for normalization/anchors, Erlang-C, the port chooser, and the PY-02 cohort-invariance acceptance.
- **Kind:** authored
- **Reads:** `fcf_m2.queueing.{choose_ports, erlang_c}`, `fcf_m2.scoring.{anchored, bounded_signal, enrich_and_score, minmax}`; fixtures `sites`, `anchors`.
- **Key contents / golden values:**
  - `TestNormalization`: `minmax([3,7,11])` bounds 0/1; constant series → all 0; `anchored([-10,0,50,100,500],0,100) == [0.0,0.0,0.5,1.0,1.0]`; degenerate range `anchored(...,5,5)` → 0; `bounded_signal([0.0,0.05,0.2], 0.10) == [0.0,0.5,1.0]`.
  - `@pytest.mark.parametrize("vals", [[0,1,2],[10,20,30],[0.1,0.5,0.9]])` (line 32) → the only parametrized test; +2 collected tests.
  - `TestErlang`: `erlang_c(1.0,1.0,0)[0]` is NaN; overload `erlang_c(10.0,1.0,5)` → `p_wait == 1.0`, `inf` wait, `util >= 1`; light load `erlang_c(0.1,0.5,2)` → `0 <= p_wait < 0.2`, `wait < 0.5`, `util < 0.2`; monotone "more ports never worse" across c=1..5 at λ=0.8, μ=0.5.
  - `TestChoosePorts`: `choose_ports(10.0,1.5,12)` must satisfy **`util <= 0.70` and `wait <= 10`** (the `TARGET_UTILIZATION`/`MAX_MEAN_WAIT_MIN` screen); `choose_ports(2000.0,2.0,8,max_ports=5) == 5` (fallback = max searched); `choose_ports(0.3,2.0,12) == 1`.
  - `TestCohortInvariance` (line 73, "PY-02 acceptance"): V3 fixed-anchor scores identical on full cohort vs `sites.iloc[:6]`; **legacy scores must NOT be close** (`test_legacy_scores_do_change_with_cohort`, line 83 — "Documents the legacy defect the anchors fix"); `enrich_and_score(sites, mode="milestone2_v3", anchor_set=None)` raises `ValueError`.
- **Notes:** `test_legacy_scores_do_change_with_cohort` is an *inverted* assertion — it will start failing if anyone "fixes" legacy scoring to be anchor-based. Deliberate; keep.

### tests/test_modules.py — 227 lines, 34 tests
- **Role:** unit tests for demand calibration, peak-wait/DES, typed confidence, economics, emissions, triggers.
- **Kind:** authored
- **Reads:** `fcf_m2.{demand, economics, emissions, peak_wait, triggers}`, `fcf_m2.confidence.{build_confidence, validate_provenance}`; fixture `sites`.
- **Key contents / golden values:**
  - `TestDemand`: default `demand.current_model_record().status == "synthetic_uncalibrated"` and `"synthetic" in rec.provenance`; sparse data (5 rows, one site) → refusal with `rec.calibration_metrics["refused"]`; 30 days × 12 sites of intercept-free synthetic truth (`rng = np.random.default_rng(1)`, `true_rate = max(0.4, 0.002*visitors_day + 0.0005*employees_day)`, noise `N(0,0.05)`) → `status == "calibrated_observed"` and **`holdout_mape <= 0.50`**; `load_observed` on a 2-column CSV raises `ValueError`; `presentation_caveat` contains "uncalibrated".
  - `TestPeakWait`: peak-window wait ≥ daily-average Erlang wait ×60; `simulate_waits(8,1.5,12,2,n_days=50,seed=7)` deterministic; percentile ordering `p10 <= p50 <= p90` at `n_days=100`; 4 ports ≤ 2 ports on `p90_wait_min`; zero demand → `mean_wait_min == 0.0`.
  - `TestConfidence` (PY-05): note text cannot change score (`assumption_type` set to "totally official and confirmed great data" leaves `data_confidence_score_v3` unchanged); `verified_utility` > `unconfirmed`+unresolved; unknown `source_class == "vibes"` is rejected by `validate_provenance`; breakdown mentions `electrical_service`; **one covered group of 7 → score `< 40`** (line 113).
  - `_cost_inputs()` (lines 116-122): `site_id="TST001", ports_now=2, ports_pathway=8, staged_targets={2036:4, 2046:6, 2056:8}, trenching_ft=100, trench_cost_per_ft=150, service_upgrade_cost_usd=20000, sessions_day_by_year={y: 2.0 for y in range(2026, 2057)}` — **canonical horizons throughout**.
  - `TestEconomics`: STG < OVB at 2036/2046/2056; `avoided_overbuild_cost_usd > 0` on STG rows only; DEF ≤ STG; low-escalation nominal < high-escalation nominal at 2056; every row `estimate_class == "screening_planning_estimate"`; cumulative nominal cost monotone per case.
  - `TestEmissions`: **`out["grid_factor_value"] == 596.3`** (line 170) and `"eGRID2023"` present in vintage or source; net positive for this grid; `renewable_matched_share=-8.0` gives a **negative** result that is deliberately *not* clipped; renewable matching improves net; `annual_energy_delivered_kwh(5.0, 0) == 0.0`.
  - `TestTriggers`: baseline `ObservedMetrics(site_id="FFX002", months_observed=8, avg_utilization=0.45, p90_wait_min=12, uptime=0.99, equity_index_percentile=0.3)`; `evaluate(None, 2, 8, site_id="FFX002")` → `"awaiting_observed_data"`; sustained demand → `"expand_review_recommended"` with `"human"` in the rule trace; equity override at `avg_utilization=0.30, p90_wait_min=2, equity_index_percentile=0.8` → override applied + expand; same metrics at percentile 0.2 → `"hold"`; `uptime=0.90` → hold (reliability gate); `evaluate(metrics, 8, 8)` → hold (pathway gate: active == pathway); `months_observed=2` → hold; `len(rule_trace) >= 3` and `policy_status.startswith("proposed")`.
- **Notes:** the 596.3 assertion here is the strongest anchor in the repo against a 590.2 regression. `TestEmissions.test_dirty_grid_can_go_negative_is_not_clipped` is an epistemics test, not a physics test — the comment on line 173 says "hypothetical".

### tests/test_contract_and_integration.py — 195 lines, 24 tests
- **Role:** end-to-end integration against one shared V3 run: contract rules, JSON Schema, RT-10 hash chain, deliberate-corruption failures, cross-model reconciliation, docs drift, offline GIS, chart-footer QA.
- **Kind:** authored
- **Reads:** via `v3_outputs`: `<out>/contract/scenario_table.csv`, `<out>/contract/site_table.csv`, `<out>/contract/schema.json`, `<out>/matlab_scenarios.csv`, `<out>/lifecycle_costs.csv`, `<out>/scoring_migration_report.csv`, `<out>/peak_wait_simulation.csv`. Also `docs/`-free: `workflow.generate_docs()` is compared in-memory (not against `docs/WORKFLOW_STEPS.md`).
- **Key contents / golden values:**
  - `TestContractValidation`: valid contract → `validate_scenario_table(...) == []`; JSON-Schema pass; `verify_hash_chain(out/"contract") == []`; **stale-contract detection (RT-10)** by bumping `ports_active` by 1 in a copied tree; `charging_window_hr = 30` → RT-05/unit failure; **`horizon_year = 2040` → failure** (line 55, deliberate negative test, not a convention violation); `capacity_confidence = "high"` on placeholder rows → **RT-07**; blank `source_id` → "provenance" failure; `ports_active = ports_pathway_capacity + 1` → **RT-03**; site-name drift → **RT-01**.
  - `TestReconciliation` (`test_rt04_legacy_totals`, line 84): **`starter_total_2026 == 25`, `pathway_total == 48`, `legacy_starter_total == 25`, `legacy_pathway_total == 48`**.
  - `test_rt06_year_set` (line 91): **`set(scenario_table.horizon_year) == {2026, 2036, 2046, 2056}`** and the same set for `matlab_scenarios.csv` — this is the canonical-horizon guard.
  - MATLAB `ports` must equal contract `ports_active` row-for-row after merge on `scenario_id`; `capacity_basis` present and non-null in the MATLAB CSV.
  - **`result["high_confidence_sites"] == 0`** (line 114) — the "0 of 12 High confidence" claim is machine-checked.
  - Cost reconciliation: contract `lifecycle_cost_npv_usd` (scenario_name == "base") equals `lifecycle_costs.csv` (escalation base, cost_case STG) within **$1.00** at 2036/2046/2056.
  - `test_emissions_have_vintage_everywhere` (line 126): every row with non-zero `net_co2e_kg` has `len(grid_factor_vintage) > 5` and **`grid_factor_value == 596.3`**.
  - `TestWorkflowAndDocs`: `f"Step count: **{len(workflow.STEPS)}**"` must appear in `workflow.generate_docs()` and every step name must appear (PY-09); `workflow.run("legacy_v2", ...)` → `starter_total == 25 and pathway_total == 48`; `scoring_migration_report.csv` has `{legacy_score, v3_anchor_score, legacy_rank, v3_anchor_rank, rank_change, explanation}` and **12 rows**; `peak_wait_simulation.csv` has `{p10_wait_min, p50_wait_min, p90_wait_min, peak_p90_wait_min, seed}` and **12 rows**.
  - `TestGisOffline` (PY-06, line 161): sets `FCF_OFFLINE=1`, `HTTPS_PROXY`/`HTTP_PROXY` to `http://127.0.0.1:9`, then asserts the PNG exists and is **> 10000 bytes**.
  - `TestVisualFooters` (PY-17): a footer-stamped chart passes `audit_footer_metadata`; an un-logged `rogue.png` is detected.
- **Notes:**
  - The docs-drift test compares `generate_docs()` to **itself**, not to the committed `docs/WORKFLOW_STEPS.md`. Only `verify.sh` gate 5 checks the committed file. So a stale `docs/WORKFLOW_STEPS.md` passes CI (CI does not run gate 5) and only fails under `./scripts/verify.sh`. Currently consistent: `docs/WORKFLOW_STEPS.md:3` says `Step count: **11**` and `workflow.STEPS` has 11 entries.
  - The GIS test's own docstring admits the network isolation is nominal: "module makes no network calls; env var set to assert intent".
  - `test_unsupported_horizon_fails` uses `2040` — a deliberately invalid year, correct behaviour, **not** a horizon-convention defect.

### tests/fixture_legacy_v2_site_results.csv
- **Role:** frozen full legacy-V2 scoring output for the 12 candidate sites — the golden the scorer must reproduce.
- **Kind:** fixture (frozen generated output of the accepted V2 baseline run, 2026-07-19)
- **Reads:** n/a
- **Written by / read by:** read by `tests/conftest.py:29` (`golden_site_results`) → `tests/test_legacy_golden.py`. **Also read directly by the 3D explorer's ETL**: `incoming/explorer/fcf-3d/fcf3d/build_sites.py:47` maps `"results": "tests/fixture_legacy_v2_site_results.csv"`.
- **Key contents:**
  - **13 lines = header + 12 data rows; 83 columns.**
  - Site IDs in rank order: `FFX002, FFX004, PWC006, FFX001, PWC002, PWC007, PWC004, FFX003, PWC008, PWC001, PWC005, PWC003`.
  - Column list (83): `site_id, site_name, site_type, address, city, state, zip, lat, lon, public_access, employees_day, visitors_day, fleet_vehicles, parking_spaces, hours_open, avg_dwell_min, nearby_households_1mi, nearby_jobs_1mi, aadt_nearest, amenities_count_0_5mi, ev_registrations_local, ev_share_local, existing_l2_ports_1mi, existing_dcfc_ports_3mi, equity_gap_index, elec_service_voltage, elec_service_rating_amp, spare_capacity_kw, distance_to_service_ft, trenching_ft, trench_cost_per_ft, service_upgrade_cost_usd, ada_layout_possible, fire_access_ok, garage_enclosed, emergency_disconnect_visible, stormwater_risk, battery_storage_flag, battery_storage_kwh, notes, access_adjustment, readiness_access_adjustment, install_cost_est_usd, existing_ports_total, nearby_households_1mi_n, nearby_jobs_1mi_n, aadt_nearest_n, amenities_count_0_5mi_n, parking_spaces_n, avg_dwell_min_n, existing_ports_total_n, spare_capacity_kw_n, distance_to_service_ft_n, trenching_ft_n, install_cost_est_usd_n, equity_gap_index_n, ev_share_local_n, demand_subscore, feasibility_subscore, safety_subscore, equity_subscore, readiness_score, expected_sessions_day, recommended_ports_now, recommended_ports_2035, recommended_ports_2050, estimated_utilization, mean_wait_min, ahj_review_flag, review_reason, model_rank, recommendation_tier, planning_recommendation, priority_reason, data_needed_next, data_confidence_score, data_confidence_level, data_confidence_reason, readiness_band, confidence_band, readiness_confidence_cell, action_label, action_detail`.
  - Readiness scores, rank 1→12: **58.8, 54.4, 52.1, 51.0, 50.3, 50.2, 48.6, 46.8, 40.1, 39.8, 36.9, 29.6**.
  - **FFX002** (row 2): `readiness_score 58.8`, `demand_subscore 42.73769092061847`, `feasibility_subscore 60.0`, `safety_subscore 90.0`, `equity_subscore 81.14186851211073`, `expected_sessions_day 1.15970516`, `recommended_ports_now 2`, `estimated_utilization 0.0936252820236814`, `mean_wait_min 0.7958889274064201`, `data_confidence_score 53.0`, **`data_confidence_level Medium`**, `readiness_band "High readiness"`, `confidence_band "Medium confidence"`, `readiness_confidence_cell "High readiness + Medium confidence"`, `action_label "Verify key data, then advance"`.
  - `data_confidence_level` distribution: Medium for FFX002, FFX004, PWC006, PWC007, PWC004, FFX003, PWC008; Low for FFX001, PWC002, PWC001, PWC003. **No site is "High"** — consistent with the "0 of 12 High" claim, but note these are *legacy V2* confidence values, not V3.
  - Every row has `ahj_review_flag 1` and `review_reason` containing "Emergency disconnect visibility not confirmed"; `elec_service_rating_amp 0` and `spare_capacity_kw 0` at all 12 sites (this is what drives the "12/12 electrical unconfirmed" claim and `build_field_provenance.py`'s rule).
  - `PWC003` (Public Safety Training Center) is the only `public_access 0.0` row, with `access_adjustment 0.35`, `readiness_access_adjustment 0.65`.
  - `PWC002` is the only `garage_enclosed 1.0` row; `hours_open 24.0`, `avg_dwell_min 240`.
- **Notes:**
  - Columns `recommended_ports_2035` / `recommended_ports_2050` are **legacy horizon names**, legitimate here (file name says `legacy_v2`) but they are what the 3D explorer surfaces to users as `ports_2035` / `ports_2050` — see Findings.
  - The `notes` field on several rows contains long provenance prose with dates `2026-06-24`, `2026-06-25` and references to files that are NOT in this repo: `amenities_0_5mi_v4_osm_reviewed.csv`, `v2c007_model_row_assumptions.csv`, `v2c003_model_row_assumptions.csv`.
  - `PWC004` note says the branch "is closed for renovation" — a live operational caveat carried in data, not just prose.

### tests/fixture_legacy_v2_right_sizing.csv
- **Role:** frozen legacy right-sizing output — starter ports, 2035/2050 trajectories, capacity cap, expansion strategy.
- **Kind:** fixture (frozen generated output, 2026-07-19)
- **Reads:** n/a
- **Written by / read by:** `tests/conftest.py:34` (`golden_right_sizing`) → `tests/test_legacy_golden.py`. **Also read by the 3D explorer ETL**: `incoming/explorer/fcf-3d/fcf3d/build_sites.py:48`.
- **Key contents:**
  - **13 lines = header + 12 data rows; 17 columns**, same 12 site IDs and same rank order as the site-results fixture.
  - Columns: `site_id, site_name, model_rank, readiness_score, recommendation_tier, electrical_risk_level, expected_sessions_day_now, model_recommended_ports_now, ports_now, ports_2035_base, ports_2035_high, ports_2050_base, ports_2050_high, site_capacity_cap, future_ready_capacity, expansion_strategy, right_sizing_reason`.
  - **`ports_now` sums to 25** and **`future_ready_capacity` sums to 48** — these two sums are the "25 starter / 48 pathway" headline. Per-site `ports_now`: FFX002 2, FFX004 3, PWC006 2, FFX001 2, PWC002 2, PWC007 2, PWC004 2, FFX003 2, PWC008 2, PWC001 2, PWC005 2, PWC003 2 = 25. Per-site `future_ready_capacity`: 8, 8, 4, 4, 3, 4, 4, 4, 2, 3, 2, 2 = 48.
  - `electrical_risk_level`: `high` at PWC002, PWC001, PWC003; `medium` at the other nine. (Sourced from the frozen risk CSV, merged in `conftest.scored_legacy`.)
  - `site_capacity_cap` values: 10, 12, 8, 6, 12, 4, 12, 8, 8, 12, 6, 6.
  - Five distinct `expansion_strategy` values: `install_now_and_make_future_ready` (FFX002, FFX004, PWC006), `starter_install_with_expandable_design` (FFX001, PWC007, PWC004, FFX003), `electrical_review_before_expansion` (PWC002, PWC001), `monitor_due_to_nearby_supply` (PWC008), `monitor_or_small_pilot` (PWC005), `do_not_advance_general_public_buildout` (PWC003).
  - `recommendation_tier` strings include commas and are therefore quoted, e.g. `"Tier 2 — promising candidate, refine data"`.
- **Notes:** `expected_sessions_day_now` here (e.g. FFX002 `1.16`) is the **rounded** form of the site-results `expected_sessions_day` (`1.15970516`) — the two fixtures are consistent but at different precisions; do not join on it.

---

## scripts/

### scripts/README.md
- **Role:** index of the seven scripts.
- **Kind:** authored
- **Reads:** n/a
- **Key contents:** table mapping each script to a purpose (lines 5-13); line 15-16 claims "All scripts use repo-relative paths and write generated outputs to gitignored locations except the deliverables they intentionally refresh."
- **Notes:**
  - Line 10 documents the `--source` requirement for `build_excel_workbook.py` but **omits the `make run-v3` prerequisite** that the script actually has (it reads `data/outputs/v3_run/lifecycle_costs.csv` at line 140 and `avoided_evse_metric.csv` at line 208). `excel/README.md:20-21` states the prerequisite correctly, so the two READMEs disagree in completeness.
  - The "repo-relative paths" claim is contradicted by the committed `dashboard/static/footer_log.json`, whose nine `file` entries are absolute paths under `/Users/andyyaro/Documents/...` — see Findings.

### scripts/verify.sh — 73 lines, executable (`-rwxr-xr-x`)
- **Role:** the repository verification harness; ten gates, PASS/FAIL tally, exits with the failure count.
- **Kind:** authored
- **Reads:** `$REPO/venv/bin/python` (overridable via `VENV_PY`, line 7); `data/contract/v1/scenario_table.csv`; `matlab/data/canonical/matlab_scenarios.csv`; `docs/WORKFLOW_STEPS.md`; `dashboard/static/0*.png` + `dashboard/static/footer_log.json`; the git index.
- **Writes:** `/tmp/fcf_verify_out.txt` (per-gate captured output, line 13) and — gate 2 — `data/outputs/verify_legacy/` inside the repo (gitignored via `.gitignore:11`).
- **Key contents — the ten gates, in execution order, with exact commands:**

  | # | line | gate name | command |
  |---|---|---|---|
  | 1 | 23-24 | `python: test suite with coverage gate (incl. legacy golden + cohort invariance + contract + offline GIS)` | `cd $REPO && $PY -m pytest tests/ -q --cov=fcf_m2 --cov-fail-under=80` |
  | 2 | 26-27 | `python: legacy_v2 mode reproduces the accepted baseline (25 starter / 48 pathway)` | `$PY -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/verify_legacy >/dev/null && grep -q '"starter_total": 25' data/outputs/verify_legacy/run_summary.json && grep -q '"pathway_total": 48' data/outputs/verify_legacy/run_summary.json` |
  | 3 | 29-30 | `contract: tracked data/contract/v1 passes all rules + JSON Schema + RT-10 hash chain` | `$PY -m fcf_m2.workflow validate-contract data/contract/v1` |
  | 4 | 32-44 | `cross-model: MATLAB canonical CSV reconciles with the contract (ports, horizons, capacity_basis)` | inline python heredoc: asserts `set(st.horizon_year) == set(m.horizon_year) == {2026, 2036, 2046, 2056}`, `len(mg) == len(st) == 120`, `(mg.ports_active == mg.ports).all()`, `mg.capacity_basis_y.notna().all()` |
  | 5 | 46-47 | `docs: generated workflow steps match the executable manifest` | `$PY -c 'from fcf_m2 import workflow; d=open("docs/WORKFLOW_STEPS.md").read(); assert f"Step count: **{len(workflow.STEPS)}**" in d'` |
  | 6 | 49-54 | `dashboard: static assets present + every chart footer-logged` | `[ $(ls dashboard/static/0*.png \| wc -l) -eq 9 ] && $PY -c "…audit_footer_metadata('dashboard/static/footer_log.json','dashboard/static'); assert p == []"` |
  | 7 | 56-57 | `secrets: no keys/tokens/private material in tracked files` | `! git grep -nIiE 'AKIA[0-9A-Z]{16}\|aws_secret_access_key\|BEGIN [A-Z ]*PRIVATE KEY\|ghp_[A-Za-z0-9]{20,}\|sk-[A-Za-z0-9]{20,}' -- . ':!scripts/verify.sh'` |
  | 8 | 59-60 | `hygiene: no local absolute paths in code/config` | `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'` |
  | 9 | 62-63 | `hygiene: no tracked file over 25 MB` | `[ -z "$(git ls-files -z \| xargs -0 -I{} find {} -size +25M 2>/dev/null)" ]` |
  | 10 | 65-66 | `links: markdown links resolve (lychee if installed, else internal-link check)` | `if command -v lychee …; then lychee --offline --no-progress README.md docs reports presentation dashboard excel matlab src tests scripts data; else $PY scripts/check_internal_links.py; fi` |

  - Coverage threshold: **80**, hard-coded at line 24 (and duplicated at `.github/workflows/tests.yml:28`). Not in `pyproject.toml` (`[tool.pytest.ini_options]` has only `testpaths` and `addopts = "-q"`).
  - `set -u` only (no `set -e`); footer prints `PASS: n FAIL: n` and `exit $FAIL`.
- **Notes / defects:** gates 7 and 8 **fail on the tree as committed** — see Findings F1 and F2. Also: gate 2 is the only gate that writes inside the repo, and it writes to a directory (`data/outputs/verify_legacy`) that differs from both the Makefile's (`data/outputs/legacy_check`) and CI's (`data/outputs/ci_legacy`) — three names for the same check. `/tmp/fcf_verify_out.txt` is a fixed, non-unique temp path (concurrent runs clobber each other).

### scripts/check_internal_links.py — 32 lines
- **Role:** offline relative-Markdown-link checker.
- **Kind:** authored
- **Reads:** every `*.md` under the repo via `REPO.rglob("*.md")`, skipping paths containing `.git`, `venv`, or `data/outputs`.
- **Written by / read by:** invoked by `scripts/verify.sh:66` (fallback branch) and `.github/workflows/tests.yml:53`.
- **Key contents:** `LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")` (line 12); skips `http://`, `https://`, `mailto:`, `#`; strips `#anchor` from the target; resolves relative to the markdown file's parent; prints `BROKEN RELATIVE LINKS:` and `sys.exit(1)` on failure, else `internal links OK (<repo>)`.
- **Notes:** currently **passes** (exit 0). It only validates *relative* links and only in `.md` files — HTML links, links inside notebooks/CSVs, and all external URLs are unchecked. Anchors (`#section`) are never validated, so a link to a heading that no longer exists still passes.

### scripts/build_field_provenance.py — 82 lines
- **Role:** regenerate `data/provenance/field_provenance_v1.csv` from the site table using documented, deterministic derivation rules.
- **Kind:** authored generator
- **Reads:** `data/inputs/real_sites_v2.csv` (line 27).
- **Writes:** `data/provenance/field_provenance_v1.csv` (line 28) — **committed** (`git ls-files` shows it tracked).
- **Key contents:**
  - `SOURCE_DATE = "2026-06-24"` (line 30) — "repo export date of the V2 data snapshot".
  - Seven field groups per site: `electrical_service, safety_review_fields, site_use_and_demand, address_and_public_access, coordinates, parking_and_layout, equity_and_context` → 7 × 12 = **84 rows**.
  - Output columns: `site_id, field_group, source_class, verification_status, source_org, source_date, reviewer, assumption_type, unresolved_flag`.
  - `verification_status` is hard-coded `"spot_checked"` for every row; `reviewer` is hard-coded `"team_v2_snapshot"`.
  - Rules (docstring lines 5-15 + code): `elec_service_rating_amp <= 0 or spare_capacity_kw <= 0` → `unconfirmed` + `unresolved_flag=1` ("this is the audited truth: 12/12 unconfirmed"); `emergency_disconnect_visible` in `{"0","0.0","no","n"}` → `unconfirmed`; visitors/employees present → `derived_public_data`; address → `official_source`; coordinates → `public_web_reference`; parking → `planning_assumption`; equity → `derived_public_data`.
  - `source_class` vocabulary used: `unconfirmed, verified_facility, planning_assumption, derived_public_data, official_source, public_web_reference` (matched against `fcf_m2.confidence.validate_provenance`, which rejects unknown classes — tested in `test_modules.py:102`).
- **Notes:** because all 12 sites have `elec_service_rating_amp == 0` and `spare_capacity_kw == 0` in the fixture/input, the `verified_facility` branch (line 55) is **dead code today**. `verification_status` never being anything but `spot_checked` means the confidence model can never see a "verified" verification status from this generator.

### scripts/build_release_artifact.py — 88 lines
- **Role:** build a frozen, SHA-256-manifested milestone release ZIP (PY-10). Local only; nothing published.
- **Kind:** authored generator
- **Reads:** `INCLUDE` (line 20-22) = `src, tests, scripts, data/inputs, data/anchors, data/provenance, data/cache/boundaries, docs, pyproject.toml, requirements-lock.txt, README.md, Makefile`; `OUTPUTS` (line 23) = `data/outputs/v3_run, data/outputs/legacy_check`.
- **Writes:** `<out>/fcf_m2_v3_release_<YYYYMMDD>.zip` and `<out>/fcf_m2_v3_release_<YYYYMMDD>.sha256`; default `out` = `ROOT/release` (line 55). `release/` and `*.zip` are gitignored (`.gitignore:25-26`), so **nothing is committed**.
- **Key contents:**
  - `sha256()` streams 65536-byte chunks (line 49).
  - Manifest keys: `release` (`f"fcf_m2 v3.0.0 ({stamp})"` — matches `pyproject.toml` `version = "3.0.0"`), `generated_utc`, `environment.python`, `environment.platform`, `files` (path → sha256).
  - Injected `LIMITATIONS.txt` (lines 25-34): "Planning-support prototype…"; "Capacity is a placeholder at 12/12 sites (capacity_basis=placeholder)"; "Demand model is synthetic and uncalibrated"; "**grid factor eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh, refresh annually**"; "**0 of 12 sites have High data confidence**"; "Expansion-trigger policy is proposed configuration, not adopted municipal policy."
  - Injected `REPRODUCTION.txt` (lines 36-43): venv creation with `-c requirements-lock.txt`, `pytest tests/ -q`, `workflow run --mode legacy_v2 --out data/outputs/legacy_check`, `--mode milestone2_v3 --out data/outputs/v3_run`, `validate-contract data/outputs/v3_run/contract`. These match `Makefile` targets `run-legacy`/`run-v3` exactly.
  - `__pycache__` is excluded from the file walk (line 66).
- **Notes:** both `OUTPUTS` directories are **absent** from the working tree (gitignored, never generated here). If the script is run without first running `make run-v3` / `make run-legacy` it silently produces a release with zero output files — no check, no warning. The reproduction text says `pip install -e .[test]` which does **not** install `openpyxl`, `python-docx`, `reportlab` or the `gis` extras, so a recipient following REPRODUCTION.txt cannot rebuild the Excel workbook or the DOCX reports.

### scripts/build_static_dashboard.py — 233 lines
- **Role:** rebuild the nine-chart static presentation dashboard plus the combined PDF from the canonical contract.
- **Kind:** authored generator (top-level script: no `if __name__ == "__main__"` guard — importing it runs the whole build).
- **Reads:** `data/contract/v1/scenario_table.csv` (line 28); `data/contract/v1/site_table.csv` (line 29, loaded as `sites_dim` but **never used**); `data/outputs/v3_run/site_results_legacy_v2.csv` (31); `data/outputs/v3_run/data_confidence_v3.csv` (32); `data/outputs/v3_run/lifecycle_costs_portfolio.csv` (33); `data/outputs/v3_run/peak_wait_simulation.csv` (34); `data/outputs/v3_run/avoided_evse_metric.csv` (35). Prerequisite `make run-v3` (docstring line 3, `Makefile:20`).
- **Writes:** `dashboard/static/{01..09}*.png`, `dashboard/static/footer_log.json`, `dashboard/static/STATIC_DASHBOARD.pdf` — **all committed** (verified with `git ls-files dashboard/static`).
- **Key contents:**
  - `CONTRACT_SRC = "canonical contract v1.0.0 (fcf_m2 V3 run 2026-07-19)"` (line 37); `VINTAGE = "inputs 2026-06-24; eGRID2023r2; verified 2026-07-19"` (line 38).
  - Nine builders run in order (line 225-227): `c1_ranking, c2_ports, c3_three_horizons, c4_costs, c5_co2e, c6_avoided_evse, c7_peak_wait, c8_limitations, c9_map`, then `combined_pdf()`, then `visuals.audit_footer_metadata(LOG, OUT)`.
  - Headline strings baked into titles:
    - c1 line 48: `"Site readiness ranking — FFX002 leads at 58.8 (Medium confidence)"`.
    - c2 lines 61/65: `"Future-ready pathway (48 total)"`, `"Starter ports 2026 (25 total)"`, title `"Start small, stay expandable: 25 starter ports inside a 48-port pathway"`.
    - c3 lines 82-86: `axhline(48)` labelled `"48-port pathway ceiling (saturation)"`; title `"Aspect 1 — ports and utilization capacity at 2036 / 2046 / 2056"`; `years = [2026, 2036, 2046, 2056]`.
    - c4 line 110: `"Aspect 2 — lifecycle cost: staged beats broad at every horizon"`; footer `"base escalation, 3% real discount"`.
    - c5 line 129: `"Net avoided CO2e — grows to ≈173–260 t/yr by 2056 (screening)"`; footer source `"eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh + contract energy"`, assumptions `"9.5 kWh/session, 0.30 kWh/mi, 400 gCO2/mi displaced"`.
    - c6 line 149/154: `"≈${int(v)}k/yr fees avoided"`, footer `"fee frame ~$1k/port/yr from client operating evidence (screening)"`.
    - c7 lines 165-171: `axhline(10)` labelled `"10-min service target"`; footer `"2026 baseline, seeded discrete-event simulation (400 days)"`.
    - c8 lines 180-192 (limitations panel, verbatim bullets): `"0 of 12 sites have High data confidence"`, `"Capacity is a PLACEHOLDER at 12/12 sites"`, `"Demand model is synthetic and uncalibrated"`, `"Costs are screening-class benchmarks"`, `"No site is approved: electrical, ADA, fire, stormwater, and AHJ gates all remain"`, `"Client Meeting #2 follow-up is prepared but not yet held"`, `"No MATLAB simulation results are claimed (no licensed execution available)"`.
  - c9 sets `os.environ["FCF_OFFLINE"] = "1"` (line 207) and appends its own footer-log entry manually (lines 211-214) with `source "TIGER 2024 cached + sites"`, `source_date "2026-06-24"`.
  - Scenario-name convention used everywhere: `"baseline"` at 2026, `"base"`/`"high"` at 2036/2046/2056.
- **Numbers I traced to the contract (all check out):** 2026 baseline `ports_active` sum = **25**, `ports_pathway_capacity` sum = **48**; net CO2e by horizon (t/yr) = 2026 baseline 43.4; 2036 base 82.4 / high 112.7; 2046 base 130.1 / high 195.1; **2056 base 173.4 / high 260.2** → the "≈173–260 t/yr by 2056" claim is exact. `grid_factor_value` is 596.3 on all 120 contract rows; `grid_factor_vintage` is `"eGRID2023r2, accessed 2026-07-19"` on all rows.
- **Notes:**
  - Line 21 imports `gis_offline` at module scope but c9 re-imports it locally at line 208 — the module-scope import is dead.
  - `sites_dim` (line 29) is loaded and never used.
  - The c1 title's "(Medium confidence)" is a **legacy V2** confidence label, while the per-bar annotations on line 49 use `data_confidence_level_v3`. I ran the V3 workflow: **all 12 sites are `Low` in V3** (FFX002 `data_confidence_score_v3` = 33.8). So the chart's title and its own annotations disagree. See Finding F4.
  - `combined_pdf()` globs `OUT.glob("0*.png")` — adding a tenth chart named `10_*.png` would silently drop it from the PDF.

### scripts/build_excel_workbook.py — 301 lines
- **Role:** rebuild `excel/Electric_Data_Milestone_2_Updated.xlsx` from the team's untracked original workbook (Task 4: pie repair, citations, proxy labels, 2056 extension, canonical import, cost/CO2e sheets, assumptions register, reconciliation).
- **Kind:** authored generator (top-level; `argparse` runs at import, `--source` **required**).
- **Reads:** `--source <original Electric Data.xlsx>` (not tracked); `data/contract/v1/scenario_table.csv` (line 117); `data/outputs/v3_run/lifecycle_costs.csv` (line 140); `data/outputs/v3_run/avoided_evse_metric.csv` (line 208).
- **Writes:** `excel/Electric_Data_Milestone_2_Updated.xlsx` (line 24) — **committed**. The original is copied first (`shutil.copy`, line 34) and "never modified".
- **Key contents:**
  - Style constants: `BEIGE "F5F0E6"`, `GREEN "1B4332"`, note fill `"FFF3D6"`, note font colour `"7A5B00"`.
  - Existing sheets touched: `Dashboard`, `Electrification Engine`, `Table012 (Page 39)`. Sheets created: **`Canonical Scenarios (M2)`, `Lifecycle Costs`, `Portfolio Cost Summary`, `Net CO2e`, `Assumptions & Sources`, `Reconciliation vs Python`** — I confirmed all six exist in the committed xlsx (read via `unzip -p … xl/workbook.xml`), alongside `Dashboard`, `Table012 (Page 39)`, `Electrification Engine`, `ExternalData_1`.
  - Pie repair: deletes every existing `PieChart`, rebuilds from `Engine!B3:B11` with categories `A3:A11`, titled `"2024 Capacity Resource Mix by Unit Type"`, placed at `A5`.
  - Labels: `Dashboard!A3` "PLANNING SCENARIO — NOT AN OFFICIAL FORECAST… Milestone 2 (July 2026)"; `Dashboard!J3` "the selected +MW value (200/600/1,200) is a flat data-center load-growth scenario input chosen by the team — not a Dominion or PJM forecast"; `Dashboard!A29` source note ("PWC share (6.5%) is a planning proxy"); `Engine!E12` "zone peak x 6.5% PWC PLANNING PROXY".
  - **2056 extension** (lines 84-96): `Engine!L14 = "=(F35/F30)^(1/5)-1"` (2041-2046 CAGR); rows 36-45 for years **2047-2056**, `F/G` compounded, `H/I = F*0.065 + Dashboard!K2`; `Engine!J13` labels 2047-2056 as extrapolation. Bar chart rebuilt: `"PWC Peak Demand Scenario 2026-2056 (6.5% proxy share + DC scenario; 2047+ extrapolated)"`.
  - Canonical import (lines 117-137): 18 columns `site_id, site_name, jurisdiction, horizon_year, scenario_name, ports_active, ports_pathway_capacity, sessions_per_day, energy_required_kwh_day, utilization, average_wait_minutes, peak_wait_minutes, capacity_basis, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd, net_co2e_kg, data_confidence, equity_indicator` — **all 18 exist in the tracked scenario_table.csv (verified)**. Header row 4, data from row 5, `freeze_panes = "A5"`.
  - `Lifecycle Costs` sheet header (line 148): `site_id, horizon_year, cost_case, escalation_case, lifecycle_cost_nominal_usd, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd`. Note text: "real discount rate 3.0%… Escalation cases: low 1% / base 2.5% / high 4%".
  - `Portfolio Cost Summary`: live `SUMIFS` over the detail sheet; rows 5-13 = (low, base, high) × (2036, 2046, 2056); columns C/D/E = STG/OVB/DEF, column F = `=D{row}-C{row}` avoided cost.
  - `Net CO2e` sheet: `B4 = 596.3`, `B5 = "eGRID2023r2 SRVC, accessed 2026-07-19"`; note text (line 197-200) cites "EPA eGRID2023 Rev 2 (data year 2023, released 2025-06-12), SRVC subregion, accessed 2026-07-19. Refresh annually (eGRID2024 pending)" and "9.5 kWh/session, 0.30 kWh/mi EV efficiency, 400 gCO2/mi displaced gasoline LDV".
  - `Assumptions & Sources` register (lines 233-256), 21 data rows. Values cross-checked against `src/fcf_m2/config.py` — **all match**: PWC share 6.5 %; DC growth 200/600/1,200 MW; baseline 2026-2046; 2047-2056 CAGR; resource mix 2024; growth multipliers "2036: 1.9/2.6 · 2046: 3.0/4.5 · 2056: 4.0/6.0 (+stress x1.15)" (= `V3_GROWTH_MULTIPLIERS` + `V3_STRESS_EXTRA = 1.15`); demand "synthetic linear, floor 0.3 sessions/day" (= `DEMAND_FLOOR_SESSIONS`); EVSE 19.2 kW (= `EVSE_POWER_KW`); 9.5 kWh/session; $6,500/port +25 % soft; $1,000/port/yr network ("[client contact] interview (~$1k/station/yr)"); $400/port/yr maintenance; $0.11/kWh tariff placeholder; 3.0 % real discount; 1 %/2.5 %/4 % escalation; **grid factor 596.3 lb CO2e/MWh**; 0.30 kWh/mi; 400 gCO2/mi; capacity PLACEHOLDER at all 12; "Data confidence 0 of 12 sites High"; **"FY2027 budgets — Fairfax City ≈$207.5M GF; PWC ≈$1.955B GF revenues, adopted budgets 2026-05-05 / 2026-04-21"**.
  - `Reconciliation vs Python` — six live checks (lines 275-283): 2026 baseline starter ports = **25**; 2026 pathway ports = **48**; scenario rows = `len(scen)` (**120**); distinct sites = **12**; `'Portfolio Cost Summary'!C10` vs the Python STG/base/2056 NPV sum; `'Portfolio Cost Summary'!F10 > 0`. Status formula `=IF(ABS(B-C)<1,"PASS","FAIL")`.
- **Notes:**
  - **`openpyxl` is an undeclared dependency** — not in `pyproject.toml` (deps: numpy, pandas, matplotlib, jsonschema; extras `gis`/`test`/`presentation`), not in `requirements-lock.txt`, and **not installed in the repo's `venv`** (I confirmed `ModuleNotFoundError: No module named 'openpyxl'`). Combined with the untracked `--source` workbook and the ungenerated `data/outputs/v3_run`, the committed xlsx **cannot be regenerated in this repo as it stands**.
  - Chart-range bug at line 186: `Reference(wp, min_col=3, max_col=4, min_row=4, max_row=10)` spans header + rows 5-10 (that is *low* 2036/2046/2056 **and** *base* 2036/2046/2056 = 6 points) while `cats = Reference(wp, min_col=2, min_row=8, max_row=10)` supplies only the 3 base-case horizons. The chart is titled "base case" but plots six values against three categories.
  - `dash["J2"]`/`J3` describe the DC growth term but the formulas reference `Dashboard!K2` — the label and the referenced cell are one column apart; may be intentional (label in J, value in K), unverified.
  - The Assumptions register lists FY2027 budget figures ($207.5M / $1.955B) that do not come from any file in `data/`; they are hand-entered prose numbers in a generator.

### scripts/md_to_docx.py — 99 lines
- **Role:** Markdown → styled Word converter used for the report deliverables.
- **Kind:** authored generator (CLI: `python scripts/md_to_docx.py <in.md> <out.docx>`, line 99).
- **Reads:** `sys.argv[1]` (a markdown file); no repo paths hard-coded.
- **Writes:** `sys.argv[2]`. The committed products that look like its output are `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx`, `.../Milestone_2_Gap_Closure_Status.docx`, `.../FINAL_STANDARDS_APPLICATION_MATRIX.docx`, `.../PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx` — **all committed**.
- **Key contents:**
  - Palette: `GREEN = RGBColor(0x1B,0x43,0x32)`, `BLACK = 0x1A1A1A`, `GOLD = 0x7A5B00` — same identity as `build_excel_workbook.py` and `fcf_m2.visuals`.
  - `add_inline()` splits on `(\*\*.*?\*\*|\*.*?\*|`.*?`)` handling bold, inline code (Courier New) and italic; default size 10.5 pt.
  - `convert()`: 0.7 in left/right margins; table detection requires a separator row whose characters are a subset of `"-: "`; table style `"Light Grid Accent 3"`; header cells bold + green; font 8 pt when >5 columns else 9.5 pt. Headings `# / ## / ###` → levels 0/1/2 at 20/15/12.5 pt green. `> ` → gold italic indented 0.3 in. `- `/`* ` → `List Bullet`; `^\d+\. ` → `List Number`; `---`/`***` → 60 underscores.
- **Notes:** **`python-docx` is an undeclared dependency** — absent from `pyproject.toml`, `requirements-lock.txt`, the Makefile and CI, and `import docx` fails in the repo `venv`. The DOCX deliverables in `reports/` therefore cannot be regenerated from this repo. Parser limitations worth knowing before re-running it: no fenced-code-block handling (``` lines are emitted as literal paragraphs), no nested lists, no image support (`![](...)` is rendered as text), and `rows.pop(1)` assumes the separator is always the second row.

---

## Findings

**F1 (high) — `verify.sh` gate 8 "hygiene: no local absolute paths in code/config" FAILS as committed.**
`dashboard/static/footer_log.json` is a tracked `.json` file containing nine absolute paths of the form `/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/0X_*.png` (lines 7, 14, 21, 28, 35, 42, 49, 56, 59). The gate's pathspec `'*.json'` matches it. I ran the exact gate command: exit 1 (FAIL). `git grep -lI '/Users/' -- .` returns exactly two files: `dashboard/static/footer_log.json` and `scripts/verify.sh` (the latter is excluded by the gate's own `':!scripts/verify.sh'`).

**F2 (high) — `verify.sh` gate 7 "secrets" FAILS as committed, on a false positive it should have excluded.**
`.github/workflows/tests.yml:57` contains the literal string `aws_secret_access_key` inside its own scan pattern. CI's copy of the scan excludes itself (`':!.github/workflows/tests.yml' ':!scripts/verify.sh'`) but `scripts/verify.sh:57` only excludes `':!scripts/verify.sh'`. I ran the exact gate command: exit 1 (FAIL). So `./scripts/verify.sh` currently reports 2 FAIL / 8 PASS even though nothing is actually wrong with the secrets, and CI passes. Any claim that "all repository verification gates pass" is currently false.

**F3 (high) — `dashboard/static/footer_log.json` is a generated artifact that has drifted from its generator's provenance.**
`scripts/build_static_dashboard.py` writes the log to `REPO/dashboard/static/footer_log.json` with `file` paths under that directory. The committed log's paths point at a completely different tree (`~/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/`), i.e. the committed PNGs/PDF were produced in the pre-repo project directory and copied in, not produced by `scripts/build_static_dashboard.py` in this repo. The footer-QA gate does not catch this because `fcf_m2.visuals.audit_footer_metadata` (src/fcf_m2/visuals.py:76) compares only `Path(e["file"]).name`.

**F4 (medium) — internal contradiction inside chart 01: "Medium confidence" in the title vs "Low" on every bar.**
`scripts/build_static_dashboard.py:48` hard-codes `"Site readiness ranking — FFX002 leads at 58.8 (Medium confidence)"`, but line 49 annotates each bar with `data_confidence_level_v3` from `data/outputs/v3_run/data_confidence_v3.csv`. I executed the V3 workflow (into scratchpad): **all 12 sites are `Low`; FFX002's `data_confidence_score_v3` is 33.8**. The "Medium" is the *legacy V2* `data_confidence_level` from `tests/fixture_legacy_v2_site_results.csv` row 2 (`53.0,Medium`). The title mixes a V2 confidence label onto a V3 confidence chart.

**F5 (medium) — `openpyxl` and `python-docx` are undeclared, uninstalled dependencies of committed deliverable generators.**
`scripts/build_excel_workbook.py` needs `openpyxl`; `scripts/md_to_docx.py` needs `python-docx`. Neither is in `pyproject.toml` (lines 10-20), `requirements-lock.txt` (21 pinned packages, neither present), the Makefile, or CI, and neither imports in the repo `venv`. `excel/Electric_Data_Milestone_2_Updated.xlsx` and four `reports/milestone-2/*.docx` are committed products of these scripts and cannot currently be regenerated. `build_release_artifact.py`'s embedded REPRODUCTION.txt (`pip install -e .[test]`) reproduces this gap for any recipient.

**F6 (medium) — the CI `push` trigger does not cover the current branch.**
`.github/workflows/tests.yml:5` fires on push to `[main, milestone2-v3-professional-release]`. HEAD is on **`v4-platform`**. Only `pull_request` and `workflow_dispatch` will run the suite for V4 work.

**F7 (medium) — the doc-drift test does not test the committed doc.**
`tests/test_contract_and_integration.py:135-140` compares `workflow.generate_docs()` against itself. The committed `docs/WORKFLOW_STEPS.md` is only checked by `scripts/verify.sh:47`, which CI never runs. They agree today (`Step count: **11**` vs `len(workflow.STEPS) == 11`) but nothing in CI keeps them agreeing.

**F8 (low) — three different output directory names for the same legacy-reproduction check.**
`scripts/verify.sh:27` → `data/outputs/verify_legacy`; `Makefile:12` → `data/outputs/legacy_check`; `.github/workflows/tests.yml:32` → `data/outputs/ci_legacy`. `build_release_artifact.py:23` packages only `data/outputs/legacy_check` and `data/outputs/v3_run`, so a release built after `./scripts/verify.sh` (rather than `make run-legacy`) silently ships no legacy output.

**F9 (low) — the coverage threshold lives in two hard-coded places and not in `pyproject.toml`.**
`80` appears at `scripts/verify.sh:24` and `.github/workflows/tests.yml:28`. `pyproject.toml` `[tool.pytest.ini_options]` (lines 25-27) has only `testpaths` and `addopts = "-q"`. `make test` (`Makefile:9`) runs coverage **without** a floor. Measured coverage is 92.15 %, so there is 12 points of headroom; per-module lows are `workflow.py 83 %`, `confidence.py 84 %`, `demand.py 84 %`, `contract.py 86 %`.

**F10 (low) — `scripts/README.md:10` omits the `make run-v3` prerequisite for `build_excel_workbook.py`** (it reads `data/outputs/v3_run/lifecycle_costs.csv` and `avoided_evse_metric.csv`), while `excel/README.md:20-21` states it. Also `scripts/README.md:15-16` claims "All scripts use repo-relative paths", contradicted by F1/F3.

**F11 (low) — `build_field_provenance.py` has a dead branch and a constant verification status.**
Because all 12 sites carry `elec_service_rating_amp == 0` and `spare_capacity_kw == 0`, the `verified_facility` branch (line 55) can never execute, and `verification_status` is hard-coded to `"spot_checked"` for all 84 rows regardless of the source class.

**F12 (low) — `build_release_artifact.py` produces a silently empty-output release.**
Neither `data/outputs/v3_run` nor `data/outputs/legacy_check` exists in the working tree (both gitignored via `.gitignore:11`). The script has no existence check.

**F13 (info) — `build_excel_workbook.py:186` portfolio chart range/category mismatch** (6 data points, 3 categories; title says "base case" but data spans low + base). Cosmetic in a committed deliverable.

**F14 (info) — `requirements-lock.txt:1` says the lock was generated from a "Python 3.14.6 arm64 venv", but CI pins Python 3.12 (`.github/workflows/tests.yml:20`) and the repo `venv` reports 3.12.6.** Not my lane's file, but it is the file `build_release_artifact.py` ships as the reproduction constraint.

**F15 (info, no defect) — 590.2 does not appear anywhere in this lane's files.** Repo-wide, `git grep '590\.2'` finds four occurrences, all explicitly framed as the *superseded* value being corrected: `CHANGELOG.md:24`, `docs/methodology/current-facts-source-register.md:7`, `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22`, `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`. 596.3 is asserted in `tests/test_modules.py:170` and `tests/test_contract_and_integration.py:131`, and is present on all 120 contract rows. Flagging so a later phase makes a deliberate call on whether correction-history prose may retain the number.

**F16 (info, no defect) — horizon convention is clean in this lane.** The only 2035/2050 tokens are `tests/test_legacy_golden.py:25-26` and the two `fixture_legacy_v2_*.csv` column names, all inside explicitly legacy-labelled artefacts. `2040` at `tests/test_contract_and_integration.py:55` is a deliberate "unsupported horizon fails" negative test. Everything else uses 2026/2036/2046/2056. No "Now", "10-year/20-year/30-year", or "10/20/30-year" strings appear in any assigned file.

---

## Cross-checks I ran that came back CLEAN (useful negative results for later phases)

- **Tracked artifacts are NOT drifted from their generators.** I ran `workflow run --mode milestone2_v3` into the scratchpad and hashed the outputs against the tracked ones:
  - `contract/site_table.csv` — byte-identical (`0ed5e4ec7078`).
  - `contract/schema.json` — byte-identical (`fb08b84ad2fd`).
  - `contract/scenario_table.csv` — differs **only** in `run_id` and `generated_at`; all other 46 columns identical across all 120 rows.
  - `matlab/data/canonical/matlab_scenarios.csv` — differs **only** in `source_note`, which embeds the run id. Tracked run id: **`milestone2_v3_20260719T052322Z`**. All 22 columns otherwise identical across 120 rows.
- `data/contract/v1/scenario_table.csv`: 120 rows × 48 cols, 12 sites, horizons `{2026, 2036, 2046, 2056}`, scenario names `{baseline, base, high, stress_combined}` (12 rows each per horizon/scenario; 2026 has only `baseline`). 2026 baseline `ports_active` = 25, `ports_pathway_capacity` = 48.
- Cross-model merge on `scenario_id` gives 120 rows, `ports_active == ports` everywhere, `capacity_basis_y` never null — verify.sh gate 4 and CI's copy both hold.
- Every relative Markdown link in the repo resolves (`check_internal_links.py` exit 0).
- No tracked file exceeds 25 MB.
- No test in the suite is skipped, xfailed, or conditionally disabled. The only `pytest.mark` in the tree is the single `parametrize` at `tests/test_scoring_and_queueing.py:32`.
