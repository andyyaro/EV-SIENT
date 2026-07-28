# LANE L04 — MATLAB tests, docs, legacy archive, canonical CSV, CI workflow

Repo: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (branch `v4-platform`, verified via `git rev-parse --abbrev-ref HEAD`).
All paths below are relative to that repo root unless stated otherwise.
Every file assigned to this lane was read end to end. Read-only; nothing modified.

---

## 0. Lane-level headline facts

| Fact | Value | Evidence |
|---|---|---|
| Canonical CSV rows | 120 data rows + 1 header (file is 121 newline-terminated lines; `wc -l` = 121, line 122 in `Read` is the trailing EOF marker) | `matlab/data/canonical/matlab_scenarios.csv` |
| Canonical CSV columns | 22, in the order listed in §7 | header line 1 |
| Canonical CSV SHA-256 | `9d660917d113569d27e39173cd0a2dbc5932900fad14e6277b05e7be89ef39ed` | `shasum -a 256` |
| Horizons in data | exactly `2026, 2036, 2046, 2056` — canonical convention, no violations | CSV col 4, 4 distinct values |
| Sites | 12: `FFX001..FFX004`, `PWC001..PWC008`; exactly 10 rows each | CSV |
| `capacity_basis` | `placeholder` on all 120 rows (1 distinct value, 0 empty) | CSV col 10 |
| `spare_capacity_kW` / `service_capacity_kW` | **empty on all 120 rows** | CSV cols 8, 9 |
| eGRID factor 596.3 / 590.2 | **appears nowhere in `matlab/` or `.github/`** (grep for `596.3`, `590.2`, `eGRID`, `CO2e` returned zero hits) | grep |
| Secrets / absolute local paths | none. Only `${{ secrets.MLM_LICENSE_TOKEN }}` reference in the workflow, which is a placeholder reference, not a value | grep for `/Users/`, `AKIA`, `arn:aws`, 12-digit IDs, `token`, `api_key` |
| Legacy-year tokens ("Now"/2035/2050) | 5 occurrences total across the lane, **all explicitly labelled legacy** — see §14 | grep |
| `matlab/tests/golden/` | **does not exist** (directory absent). Consistent with EXECUTION_STATUS.md | `ls` |
| `matlab/outputs/.gitkeep` | 0 bytes — confirmed empty | `wc -c` = 0 |

---

## 1. `matlab/tests/test_capacityGuard.m` (145 lines)

- **Role:** MATLAB unittest (function-based) for `src/capacityGuard.m`, the fail-closed capacity provenance gate (backlog item ML-04).
- **Kind:** authored (test source).
- **Reads:** adds `<repo>/matlab/src` to path via `addpath(fullfile(repoRoot,"src"))` (lines 11–13). Reads **no data file** — every fixture is a hand-built struct (`localGuardRow`, lines 137–145).
- **Written by / read by:** run by `runtests('tests')` (README line 131, RUN_ON_LICENSED_MATLAB step 2, `.github/workflows/matlab-manual.yml` `select-by-folder: matlab/tests`). Exercises `capacityGuard.m` only.
- **Key contents — every assertion, verbatim semantics:**

  | Line | Test | Assertion / tolerance |
  |---|---|---|
  | 21–26 | `testFeasibilityFailsClosedOnPlaceholder` | `verifyError(... capacityGuard(row,"Mode","feasibility"), "capacityGuard:notVerified")` |
  | 28–33 | `testFeasibilityFailsClosedOnUnknown` | basis `"unknown"` → same error ID |
  | 35–41 | `testFeasibilityFailsClosedOnEngineeringEstimate` | basis `"engineering_estimate"` → `capacityGuard:notVerified`. Comment line 36: "Even engineer-derived estimates are NOT feasibility-grade." |
  | 43–48 | `testFeasibilityDefaultsToFailClosed` | no `Mode` arg → still `capacityGuard:notVerified` (default mode is feasibility) |
  | 50–55 | `testUnknownVocabularyRejected` | basis `"confirmed_totally"` → `capacityGuard:unknownBasis` |
  | 57–62 | `testMissingBasisFieldRejected` | `rmfield(row,"capacity_basis")` → `capacityGuard:missingBasis` |
  | 68–76 | `testVerifiedUtilityPassesFeasibility` | `service_capacity_kW = 400` → `g.is_verified` true; `g.capacity_kW == 400`; `strlength(g.placeholder_banner) == 0` |
  | 78–84 | `testVerifiedFacilityPassesFeasibility` | `service_capacity_kW = 250` → verified, `g.capacity_kW == 250` |
  | 90–102 | `testPlanningModeCarriesBanner` | `spare_capacity_kW = 153.6` → not verified; `strlength(banner) > 0`; `contains(banner,"PLACEHOLDER","IgnoreCase",true)`; **`g.capacity_kW == 50 + 153.6` with `"RelTol", 1e-12`** (legacy definition = `base_load_mean_kW` + spare) |
  | 104–110 | `testUndefinedCapacityYieldsNaN` | both capacities NaN → `g.capacity_defined` false, `isnan(g.capacity_kW)` true. Comment line 105: "Current adapter CSV state: service and spare both empty." |
  | 112–122 | `testAssumedCapacityIsLabeledAssumption` | `"AssumedSiteCapacity_kW", 200` → `capacity_defined` true, `capacity_kW == 200`, `assumed_capacity_used` true, `is_verified` **false**, banner length > 0 |
  | 124–131 | `testServiceCapacityPreferredOverLegacySum` | basis `"planning_proxy"`, service 300, spare 153.6 → `capacity_kW == 300` ("service_capacity_kW must take precedence over base+spare") |

  Fixture `localGuardRow` (137–145): `scenario_id="TEST_GUARD"`, `site_id="TST001"`, `capacity_basis=string(basis)`, `service_capacity_kW=NaN`, `spare_capacity_kW=NaN`, `base_load_mean_kW=50`.
  Vocabulary exercised: `placeholder`, `unknown`, `engineering_estimate`, `verified_utility`, `verified_facility`, `planning_proxy` — 6 values, matching the DATA_DICTIONARY controlled vocabulary exactly.
- **Notes:** the two tolerances in this file are `RelTol 1e-12` (line 101) and exact equality elsewhere. `153.6 kW` = 8 × 19.2 kW; it is the legacy-V2 spare-capacity number and appears in no canonical data (see §7 and Finding F-05).

---

## 2. `matlab/tests/test_horizons.m` (97 lines)

- **Role:** proves the pipeline is horizon-agnostic (ML-06 / legacy hypothesis H7) — that 2026/2036/2046/2056 run unedited and that an arbitrary new horizon (2070) also works.
- **Kind:** authored.
- **Reads:** `<repo>/matlab/data/canonical/matlab_scenarios.csv` (lines 17–18); `<repo>/matlab/src/*.m` as text via `fileread` (lines 52–54); writes a temp copy `with_2070.csv` into `tempname` dir (lines 19–20, 77–78), removed in `teardownOnce` (23–27).
- **Written by / read by:** run by `runtests('tests')`.
- **Key contents:**

  | Line | Test | Assertion / tolerance |
  |---|---|---|
  | 33–46 | `testAllCanonicalHorizonsRun` | `loadScenarios(csv,"SiteId","FFX002")`; `verifyEqual(sort(horizons(:)).', [2026 2036 2046 2056])` (exact). Then for each horizon runs `runScenario(rows(1,:), "GuardMode","planning_illustration")` and asserts `out.metrics.horizon_year == double(h)` and `out.metrics.peak_unmanaged_kW > 0` |
  | 48–60 | `testNoHardCodedYearListInSources` | static text guard: for every `src/*.m`, `verifyFalse(contains(txt, 'years = ["Now"'))`. Note: scans **only `src/`**, so `legacy_archive/*.m` (which does contain that literal) is correctly out of scope |
  | 62–88 | `testArbitraryNewHorizonRowRuns` | appends a row with `scenario_id="FFX002_2070_base"`, `horizon_year=2070`, `case="base"`, `ports=10`, `sessions_per_day=8.0`; asserts `height(loaded)==1`, `loaded.horizon_year(1)==2070`, `out.metrics.horizon_year==2070`, `out.metrics.energy_requested_kWh > 0` |
  | 90–97 | `testHorizonFilterIsDataDriven` | `loadScenarios(csv,"HorizonYear",1999)` → `verifyError(..., "loadScenarios:noMatch")` |

  Header comment lines 3–5 state the legacy convention explicitly: *"The legacy scripts hard-coded years = ["Now","2035","2050"] (H7). These tests prove the V3 pipeline runs 2036/2046/2056 with no script edits"*.
- **Notes:** the header prose enumerates only "2036/2046/2056" while the assertion (line 37) requires all four including 2026 — cosmetic prose/assert mismatch, not a defect. `ports=10` in the synthetic 2070 row exceeds the canonical `ports` max of 8, but it is synthetic test data, not a portfolio claim.

---

## 3. `matlab/tests/test_loadScenarios.m` (118 lines)

- **Role:** unit tests for `src/loadScenarios.m` (ML-01/ML-06) — CSV load, filtering, and fail-closed validation.
- **Kind:** authored.
- **Reads:** canonical CSV (15–16); writes three mutated temp copies (`missing_col.csv` 81, `blank_basis.csv` 93, `bad_window.csv` 104) under `tempname`, cleaned in `teardownOnce`.
- **Key contents:**

  | Line | Test | Assertion |
  |---|---|---|
  | 31–39 | `testLoadsCanonicalCsv` | `height(T) > 0`; **`verifyEqual(height(T), 120)`** — comment line 34: "Canonical adapter emits 120 rows (12 sites x 10 horizon-case combos)"; `ismember("case_label", T.Properties.VariableNames)` |
  | 41–50 | `testHorizonsComeFromData` | `sort(unique(T.horizon_year)(:)).' == [2026 2036 2046 2056]` and `sort(T.Properties.UserData.horizons_in_data) == [2026 2036 2046 2056]` |
  | 52–59 | `testFilterBySiteHorizonCase` | filter `SiteId="FFX002", HorizonYear=2036, Case="high"` → `height==1`, `site_id=="FFX002"`, `horizon_year==2036`, `case_label=="high"` |
  | 61–66 | `testNoMatchErrors` | `SiteId="NOPE999"` → `loadScenarios:noMatch` |
  | 68–73 | `testMissingFileErrors` | nonexistent path → `loadScenarios:fileNotFound` |
  | 75–85 | `testMissingColumnErrors` | `removevars(T,"capacity_basis")` → `loadScenarios:missingColumns` |
  | 87–97 | `testEmptyCapacityBasisErrors` | `T.capacity_basis(3) = ""` → `loadScenarios:missingCapacityBasis` |
  | 99–108 | `testBadArrivalWindowErrors` | `arrival_end_hr(1) = arrival_start_hr(1)` (zero-width) → `loadScenarios:badArrivalWindow` |
  | 110–118 | `testCapacityBasisIsPlaceholderEverywhere` | `all(string(T.capacity_basis) == "placeholder")` with message *"Adapter CSV is expected to declare placeholder capacity on every row until utility/facility confirmation lands."* |

  No numeric tolerances in this file — all assertions are exact equality or error-ID matches.
- **Notes:** `testHorizonsComeFromData` relies on `UserData.horizons_in_data` being computed **after** filtering (`src/loadScenarios.m` line 150 filters, line 165 computes). The test loads unfiltered so it passes, but "horizons_in_data" is semantically "horizons in the returned subset", not "horizons in the file". Worth knowing before any downstream consumer trusts that field on a filtered load.

---

## 4. `matlab/tests/test_managedCharging.m` (225 lines)

- **Role:** unit tests for `src/managedCharging.m` (ML-05) — the three charging strategies and their energy-balance / shortfall / priority / comms-loss invariants.
- **Kind:** authored.
- **Reads:** `src/` via addpath only. **No data file**; all fixtures are hand-built (`localScenarioRow` 173–193, `localTwoVehicleProfiles` 195–225).
- **Key contents — assertions and tolerances:**

  | Line | Test | Assertion / tolerance |
  |---|---|---|
  | 24–30 | `testEnergyBalanceUnmanaged` | balance helper; `curtailed_kWh == 0`; `unmet_kWh == 0` |
  | 32–36 | `testEnergyBalanceClamp` | `SiteCapacity_kW = 60` → balance |
  | 38–42 | `testEnergyBalanceEnergyAwareAmple` | `SiteCapacity_kW = 500` → balance |
  | 44–48 | `testEnergyBalanceEnergyAwareTight` | `SiteCapacity_kW = 75` → balance |
  | 54–61 | `testEnergyAwareMeetsNeedWhenCapacityAllows` | cap 500 → `unmet_kWh < 1e-6`; `all(r.per_vehicle.fully_served)` |
  | 63–73 | `testEnergyAwareReportsShortfallWhenCapacityTight` | cap 72 → `unmet_kWh > 0`; `any(~fully_served)`; **`sum(per_vehicle.unmet_kWh) == unmet_kWh` at `"AbsTol", 1e-9`** |
  | 75–81 | `testEnergyAwareNeverExceedsCap` | cap 90 → `max(r.total_kW) <= cap + 1e-9` |
  | 83–96 | `testDeferredIsNotCurtailed` | cap 95 → `curtailed_kWh == 0`, `deferred_kWh > 0`; clamp at same cap → `curtailed_kWh > 0`, `unmet_kWh == 0` |
  | 98–107 | `testEnergyAwareBeatsClampOnDeliveredEnergy` | cap 95 → `ra.delivered_kWh + 1e-9 >= rc.delivered_kWh` |
  | 109–119 | `testPriorityClassServedFirst` | two-vehicle fixture, `priority_class = [2;1]`, `cap = max(baseLoad)+20` (= 60) → `r.per_vehicle.fully_served(2)` true |
  | 121–134 | `testCommsLossFailSafeProfile` | `"CommsLoss", true, "FailSafeFraction", 0.5` → balance; `r.comms_loss` true; `any(contains(r.notes,"COMMS LOSS"))`; `max(r.ev_kW) <= nSessions * 0.5 * max(max_power_kW.*weight) + 1e-9` |
  | 140–144 | `testCapacityRequiredForClamp` | clamp with no capacity → `managedCharging:capacityUndefined` |
  | 146–153 | `testEnergyAwareRefusesLegacyGaussian` | profiles built in `"Mode","legacy_gaussian"` → `managedCharging:sessionsRequired` |
  | 155–159 | `testUnknownStrategyRejected` | strategy `"magic"` → `managedCharging:badStrategy` |

  **The central energy-balance tolerance** (`localVerifyBalance`, 165–171):
  `tol = 1e-6 * max(1, abs(r.requested_kWh));` then
  `verifyEqual(r.delivered_kWh + r.curtailed_kWh + r.unmet_kWh, r.requested_kWh, "AbsTol", tol, "Energy balance requested = delivered + curtailed + unmet.")`
  — i.e. a **relative** 1e-6 floored at absolute 1e-6. Matches README line 74 ("checked to 1e-6").

  `localScenarioRow` (173–193): `horizon_year = 2036` (canonical), `ports = 6`, `charger_power_kW = 19.2`, `spare/service = NaN`, `capacity_basis = "placeholder"`, `base_load_mean_kW = 50`, `base_load_peak_kW = 70`, `arrival 9→15`, `dwell_hr = 6.0`, `sessions_per_day = 6.0`, `energy_per_session_kWh = 18.0`, `managed_charging_policy = "none"`.
  `localTwoVehicleProfiles` (195–225): `dt_hr = 5/60`, `t_hr = 0:dt:24`, `baseLoad_kW = 40` constant, sessions table columns `["session_id","arrival_hr","departure_hr","dwell_hr","energy_required_kWh","energy_required_grid_kWh","max_power_kW","weight","priority_class"]`, both vehicles 19.2 kW arriving 10.0 departing 12.0, `evRequest_kW = 2*19.2` on `10 <= t < 11`, `mode = "deterministic_sessions"`, `charger_efficiency = 1.0`.
- **Notes:** the fixture uses `dwell_hr = 6.0` with an arrival window of only 6 h (9→15), so sessions can run past hour 21; nothing in the test constrains that. `energy_per_session_kWh = 18.0` here vs `9.5` on every canonical row — deliberately larger so caps bind.

---

## 5. `matlab/tests/test_profiles.m` (164 lines)

- **Role:** unit tests for `src/makeSessionProfiles.m` (ML-03) — dwell actually matters, peak derives from sessions not ports, energy conservation, seeded reproducibility, legacy-shape mode.
- **Kind:** authored.
- **Reads:** `src/` via addpath. No data file; fixture `localSyntheticRow` (142–164).
- **Key contents:**

  | Line | Test | Assertion / tolerance |
  |---|---|---|
  | 23–40 | `testDwellMateriallyChangesProfile` | `dwell 4.0` vs `dwell 0.25` → `max(abs(diff of evRequest_kW)) > 0.5`; short dwell strictly reduces `energyRequested_kWh`. Comment line 24: "Legacy H1: dwell_hr was loaded but unused." |
  | 42–56 | `testPeakDerivesFromSessionsNotPorts` | `ports=8`, `sessions_per_day=2.0`; `theoreticalMax = 8*19.2 = 153.6 kW`; asserts `max(evRequest_kW) < 0.5*theoreticalMax` (i.e. < 76.8 kW) and `> 0`. Comment line 43: "Legacy H2: request peaked at ports x charger kW regardless of demand." |
  | 58–74 | `testEnergyConservationDeterministic` | `eta = 0.93`; `gridPerSession = 9.5/0.93`; `deliverable = min(gridPerSession, dwell_hr*charger_power_kW)`; `expected = sessions_per_day * deliverable`; **`verifyEqual(p.energyRequested_kWh, expected, "RelTol", 1e-6)`** |
  | 76–88 | `testFractionalSessionsConserved` | `sessions_per_day = 1.16` ("a real adapter value" — it is FFX002_2026_baseline's value, CSV line 2) → `energyRequested_kWh == 1.16*deliverable` at `"RelTol", 1e-6` |
  | 90–98 | `testEfficiencyIncreasesGridEnergy` | `eta 0.90` grid energy > `eta 1.0` grid energy |
  | 100–114 | `testLegacyGaussianModeReproducesLegacyShape` | `p.mode == "legacy_gaussian"`; `max(evRequest_kW) == ports*charger_power_kW` at `"RelTol", 1e-9`; peak time at window centre `(9+17)/2 = 13` at `"AbsTol", p.dt_hr + 1e-12`; `height(p.sessions) == 0` ("Legacy mode must not fabricate a session list") |
  | 116–127 | `testStochasticModeReproducibleWithSeed` | seed 7 twice → identical `evRequest_kW`; seed 8 → differs by > 1e-9 somewhere **or** different session count |
  | 129–136 | `testBaseLoadHitsMeanToPeakRange` | `max(baseLoad_kW) == base_load_peak_kW` at `"RelTol", 1e-9`; `min(baseLoad_kW) >= base_load_mean_kW - 1e-9` |

  `localSyntheticRow` (142–164): `scenario_id="TEST_2036_base"`, `horizon_year = 2036`, `ports = 4`, `charger_power_kW = 19.2`, `capacity_basis = "placeholder"`, `capacity_source = "test fixture"`, `base_load_mean_kW = 50`, `base_load_peak_kW = 70`, `arrival 9→17`, `dwell_hr = 2.0`, `sessions_per_day = 2.0`, `energy_per_session_kWh = 9.5` (matches the canonical value on every row).
- **Notes:** `testDwellMateriallyChangesProfile` mutates `dwell_hr` to 4.0 on a row whose window is 9→17; combined with `energy_per_session_kWh = 9.5` and 19.2 kW, `deliverable` is never dwell-truncated at dwell 4.0 — hence the "unless dwell-truncated; the base row is not truncated" caveat at line 95.

---

## 6. `matlab/tests/test_regression.m` (141 lines)

- **Role:** golden summary-metric regression harness (ML-09). Runs a fixed 8-scenario panel and compares against `tests/golden/regression_golden.csv`.
- **Kind:** authored. The golden CSV it depends on is a **data-contract/fixture that does not exist**.
- **Reads:** canonical CSV (26–27); `tests/golden/regression_golden.csv` (28–29) — **absent from the repo**.
- **Writes (at run time, on a licensed machine):** creates `tests/golden/` and writes `regression_golden.csv` on first run (45–53).
- **Key contents:**
  - Fixed constants (`setupOnce`, 22–33):
    - `testCase.TestData.seed = 42;` — comment: `% fixed forever`
    - `testCase.TestData.assumedCap_kW = 200;` — `% fixed planning cap`
    - `testCase.TestData.relTol = 1e-6;` — `% deterministic panel`
  - **What it expects from `tests/golden/regression_golden.csv`:**
    - a readable CSV (`readtable(goldenFile, "TextType","string")`, line 55)
    - a `scenario_id` column, row-for-row identical to the current panel and **in the same order** (line 66–68, message `"Panel ordering/composition changed."`)
    - identical row count (line 57, message `"Panel size changed - regenerate the golden deliberately."`)
    - seven numeric metric columns (lines 60–63):
      `energy_requested_kWh`, `peak_unmanaged_kW`, `peak_clamp_kW`, `curtailed_clamp_kWh`, `peak_energy_aware_kW`, `unmet_energy_aware_kWh`, `deferred_energy_aware_kWh`
    - each compared with **`"RelTol", 1e-6`**, except NaN golden values which require the current value to also be NaN (lines 72–81)
  - **Self-baselining behaviour** (45–53): if the golden file is missing it is created via `writetable(current, goldenFile)`, logged as `"GOLDEN CREATED at %s - commit this file; subsequent runs will compare against it."`, and the comparison then trivially passes.
  - `testPanelIsDeterministic` (86–96): computes the panel twice and requires `"AbsTol", 0` (bit-for-bit) equality on `energy_requested_kWh`, `peak_unmanaged_kW`, `peak_clamp_kW`, `peak_energy_aware_kW`.
  - **Panel composition** (`localComputePanel`, 102–141): sites `["FFX002","PWC001"]` × every horizon in the data, taking `sortrows(sub,"scenario_id")` row 1 per horizon ⇒ **8 rows**: `FFX002_2026_baseline`, `FFX002_2036_base`, `FFX002_2046_base`, `FFX002_2056_base`, `PWC001_2026_baseline`, `PWC001_2036_base`, `PWC001_2046_base`, `PWC001_2056_base` (derived from the CSV; `base` sorts before `high` and `stress_combined`).
  - Each panel row runs `runScenario(row, "GuardMode","planning_illustration", "ProfileMode","deterministic_sessions", "Seed", 42, "AssumedSiteCapacity_kW", 200)`.
  - Cross-checked against `src/runScenario.m` lines 129–153: all seven metric names plus `scenario_id` and `horizon_year` are emitted by `runScenario`. No name drift.
- **Notes / header claim (lines 10–14, verbatim):** *"FIRST RUN on a licensed machine: the golden file does not exist yet (it can only be produced by executing MATLAB, and none was available when this repository was authored - see EXECUTION_STATUS.md). The harness then WRITES the golden file, logs that fact, and passes the comparison against the freshly written baseline. Commit the golden file; every later run compares against it and fails on drift."* This is internally honest, but see Finding **F-01** — the CI workflow makes the "commit the golden file" step impossible.

---

## 7. `matlab/data/canonical/matlab_scenarios.csv` (header + 120 data rows)

- **Role:** the single input to the whole MATLAB pipeline — one row per (site × horizon × case).
- **Kind:** **generated** by `src/fcf_m2/matlab_adapter.py` (`build_matlab_input`, which writes `MATLAB_COLUMNS` at lines 14–20 and `df.to_csv(out_path, index=False)` at line 71).
- **Reads:** n/a (data).
- **Written by / read by:** written by `fcf_m2.matlab_adapter` (README lines 191–194, DATA_DICTIONARY lines 3–8). Read by `src/loadScenarios.m` (only reader), and by `tests/test_loadScenarios.m`, `tests/test_horizons.m`, `tests/test_regression.m`.
- **Generator-drift check: PASS.** `MATLAB_COLUMNS` in `src/fcf_m2/matlab_adapter.py` lines 15–19 matches the CSV header exactly — same 22 names, same order.
- **Provenance strings embedded in every row:** `capacity_source` = `"legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)"` (1 distinct value across 120 rows); `source_note` = `"Generated from canonical contract 1.0.0 run milestone2_v3_20260719T052322Z. CAPACITY IS A PLANNING PLACEHOLDER - no feasibility claim permitted. Do not hand-edit; regenerate via fcf_m2.matlab_adapter."` (1 distinct value across 120 rows). Both match DATA_DICTIONARY lines 3–4.

### 7.1 Every column, in order, with observed range — and the **Phase 2.2 publication classification**

Classification key: **INPUT** = a modelling input or provenance label, safe to publish in a public harness repo. **RESULT** = a study finding/conclusion (ranking, readiness, risk verdict, cost), must NOT be published. **IDENTITY** = reveals the client/stakeholder.

| # | Column | Type | Observed values / range (all 120 rows) | Class | Rationale |
|---|---|---|---|---|---|
| 1 | `scenario_id` | string | 120 distinct, `<site_id>_<horizon>_<case>` | **IDENTITY (derived)** | Embeds `site_id`, so it inherits the FFX/PWC prefix problem. Publishable only if `site_id` is re-keyed. |
| 2 | `site_id` | string | 12 distinct: `FFX001–FFX004`, `PWC001–PWC008` | **IDENTITY** | `FFX` = Fairfax County, `PWC` = Prince William County. The prefix alone names both client jurisdictions. Must be re-keyed (e.g. `SITE_A01`) for public release. |
| 3 | `site_name` | string | 12 distinct real facility names (e.g. `City of Fairfax Regional Library`, `Fairfax County Government Center`, `PWC McCoart Government Center`, `Prince William County Public Safety Training Center`, `Neabsco-Potomac Commuter Garage`, `Bull Run Library`, `Chinn Park Regional Library`, `Pohick Regional Library`, `Potomac Library`, `Haymarket Gainesville Library`, `Central Library`, `Fairfax City Hall or municipal building`) | **IDENTITY — hardest blocker** | These are named, geolocatable public buildings belonging to the two client jurisdictions. No addresses or lat/lon are present, but the names are unambiguous. Must be dropped or pseudonymised. |
| 4 | `horizon_year` | integer | 2026, 2036, 2046, 2056 (4 distinct) | **INPUT** | Canonical horizon convention. Safe. |
| 5 | `case` | string | `baseline` (2026 only), `base`, `high`, `stress_combined` | **INPUT** | Demand-case label. Safe. |
| 6 | `ports` | integer | min 2, max 8; distinct {2,3,4,6,8} | **RESULT** | This is the **output of the Python right-sizing model** (DATA_DICTIONARY line 25: "Python right-sizing model (rank/case-matched) — Recommended charging ports for this scenario"). A per-site recommended port count is a study conclusion, not an input. Do not publish site-attributed. |
| 7 | `charger_power_kW` | double | 19.2 on all 120 rows | **INPUT** | Level-2 dual-port planning assumption. Safe. |
| 8 | `spare_capacity_kW` | double | **empty on all 120 rows** | **INPUT (currently null)** | Nothing to disclose today. If real facility spare capacity ever lands here it becomes sensitive facility data — re-classify then. |
| 9 | `service_capacity_kW` | double | **empty on all 120 rows** | **INPUT (currently null)** | Same as above. Real utility service capacity would be **RESULT/sensitive**. |
| 10 | `capacity_basis` | string | `placeholder` on all 120 rows | **INPUT** | Provenance gate label. Safe and in fact important to keep. |
| 11 | `capacity_source` | string | 1 distinct string containing **"12/12 sites unconfirmed"** | **RESULT (portfolio status)** | The literal string discloses that the client's entire 12-site portfolio has unconfirmed electrical capacity — a portfolio readiness statement about a named client. Sanitise for public release. |
| 12 | `base_load_mean_kW` | double | 50.2 – 115.0 (8 distinct) | **RESULT (site-attributed facility data)** | Per-facility electrical load estimates for named public buildings. DATA_DICTIONARY line 31 calls it a "legacy adapter estimate", but it is still an estimated operating characteristic of an identified client building. Safe only if de-identified. |
| 13 | `base_load_peak_kW` | double | 66.3 – 151.8 (8 distinct) | **RESULT (site-attributed facility data)** | Same as above. |
| 14 | `arrival_start_hr` | double | 7.0, 8.0, 10.0 (3 distinct) | **INPUT** | Use-profile assumption. Safe. |
| 15 | `arrival_end_hr` | double | 11.0, 16.0, 17.0 (3 distinct) | **INPUT** | Safe. Three window archetypes: (7,11) garage, (8,16) government, (10,17) library. |
| 16 | `dwell_hr` | double | 1.5, 2.0, 3.0, 4.0 | **INPUT** | Safe. |
| 17 | `sessions_per_day` | double | 0.3 – 15.73, **120 distinct values** (one per row) | **RESULT** | The per-site/horizon/case demand forecast — the core quantitative output of the Python demand model. Do not publish site-attributed. |
| 18 | `energy_per_session_kWh` | double | 9.5 on all 120 rows | **INPUT** | Constant planning assumption. Safe. |
| 19 | `managed_charging_policy` | string | `none` on all 120 rows | **INPUT** | Reserved field. Safe. |
| 20 | `model_rank` | integer | 1 – 12, one distinct rank per site | **RESULT — the single clearest blocker** | This is the **portfolio priority ranking of the client's sites** (DATA_DICTIONARY line 39: "Python site-ranking model — Portfolio priority rank of the site"). Joined with `site_name` it publishes a rank-ordered list of which client facilities the study prioritises. Absolutely must not be published site-attributed. Observed mapping: 1 = City of Fairfax Regional Library, 2 = Fairfax County Government Center, 3 = Bull Run Library, 4 = Fairfax City Hall or municipal building, 5 = Neabsco-Potomac Commuter Garage, 6 = Central Library, 7 = Chinn Park Regional Library, 8 = Pohick Regional Library, 9 = Potomac Library, 10 = PWC McCoart Government Center, 11 = Haymarket Gainesville Library, 12 = Prince William County Public Safety Training Center. |
| 21 | `electrical_risk_level` | string | `medium` (9 sites), `high` (3 sites: PWC002, PWC001, PWC003) | **RESULT — blocker** | A qualitative readiness/risk verdict attached to named client facilities. DATA_DICTIONARY line 40 hedges it as "Qualitative screen, not a measurement", but publishing "Prince William County Public Safety Training Center = high electrical risk" is a study finding about a client asset. |
| 22 | `source_note` | string | 1 distinct string naming contract `1.0.0` and run `milestone2_v3_20260719T052322Z` | **INPUT (provenance)** | Contains no client identity and no result. Safe and should be retained — it is the citation string. |

**Bottom line for Phase 2.2:** the canonical CSV as it stands **cannot be published as-is**. Four of the 22 columns are outright study results attached to named client facilities (`model_rank`, `electrical_risk_level`, `ports`, `sessions_per_day`), two more are site-attributed facility load estimates (`base_load_mean_kW`, `base_load_peak_kW`), one leaks portfolio status text (`capacity_source`), and three carry client identity (`site_id`, `site_name`, `scenario_id`).

**Do the `site_id` values themselves reveal client identity?** Yes. `FFX###` and `PWC###` are transparent abbreviations for Fairfax County and Prince William County, and both prefixes are additionally spelled out in full inside `site_name` (`Fairfax County Government Center`, `Prince William County Public Safety Training Center`) and in `capacity_source`/`README` prose. Re-keying `site_id` alone is not sufficient while `site_name` remains.

**No addresses, coordinates, parcel IDs, contact names, or emails appear in this CSV** — the identity exposure is entirely via facility names and county prefixes.

**Recommended shape for a public harness repo:** ship a synthetic or de-identified fixture (`SITE_A01..SITE_A12`, generic names, jittered load values, and either drop `model_rank`/`electrical_risk_level` or replace them with constants), keep all INPUT columns and `capacity_basis`/`source_note` so the guard logic and provenance discipline stay exercisable, and keep the real CSV in the private repo.

### 7.2 Structural facts worth carrying forward

- Exactly 10 rows per site (verified: `Counter` over `site_id` gives 10 for all 12 sites) = 1 × `2026 baseline` + 3 horizons × 3 cases. Confirms README line 90–91 and DATA_DICTIONARY line 4.
- `base_load_mean_kW` / `base_load_peak_kW` / `arrival_*` / `dwell_hr` are **constant across all 10 rows of a site** — they come from `site_meta`, not from the scenario table (matlab_adapter.py lines 51–54). This is hypothesis H15 in the DATA_DICTIONARY ("constant across horizons - H15", line 31); it means year-over-year base-load growth is **not** modelled.
- `peak/mean` ratio is a constant 1.3209… for every site (e.g. 67.9/51.4, 151.8/115.0, 66.3/50.2) — the peak column is a fixed multiple of the mean, not an independent estimate.
- Ports are non-monotonic with horizon in places (e.g. FFX002: 2046_base = 6, 2056_base = 6, but 2046_high = 8 and 2056_base = 6 < 2046_high = 8) and `sessions_per_day` for FFX002 drops from 6.001 (2046 stress) to 4.639 (2056 base) — expected, since case dominates horizon.
- Line endings: LF only. No BOM. No quoting needed (no embedded commas).

---

## 8. `matlab/README.md` (215 lines)

- **Role:** the entry-point document for the MATLAB layer — purpose, requirements, layout, pipeline, run commands, output interpretation, presentation rules, restrictions, regeneration, limitations.
- **Kind:** authored (prose).
- **Reads:** n/a. **References:** `data/canonical/matlab_scenarios.csv`, `src/`, `tests/`, `outputs/`, `legacy_archive/`, `../.github/workflows/matlab-manual.yml`, `DATA_DICTIONARY.md`, `RUN_ON_LICENSED_MATLAB.md`, `EXECUTION_STATUS.md`. **All of these exist** (verified by `ls`); the `../.github/...` relative path resolves correctly from `matlab/`.
- **Key contents:**
  - Line 3–6: scope — *"12 sites (FFX/PWC), horizons 2026/2036/2046/2056, cases baseline/base/high/stress_combined"*. Canonical horizons; matches data.
  - Lines 13–19: the EXECUTION STATUS banner — *"this repository was authored in an environment with **no MATLAB installation** (2026-07-19) … **no simulation, test run, or figure in this repo has been executed or generated**"*.
  - Line 25: `MATLAB | **R2025b**` — "release used by the legacy `.slx` provenance; earliest intentionally supported release; string/`tiledlayout`/`exportgraphics`/`renamevars` APIs used throughout". **Verified:** `tiledlayout` at `src/plotScenario.m:62`, `exportgraphics` at `src/plotScenario.m:207`, `renamevars` at `src/loadScenarios.m:75`.
  - Line 26–27: Simulink optional; no toolboxes beyond base MATLAB; "Poisson via Knuth's algorithm - no Statistics Toolbox"; "Hashing uses `java.security.MessageDigest`".
  - Lines 31–41: repository layout block (accurate).
  - Lines 52–58: pipeline diagram `loadScenarios -> capacityGuard -> makeSessionProfiles -> managedCharging -> electricalEconomics -> metrics/plots`.
  - Line 74: `requested = delivered + curtailed + unmet` "(checked to 1e-6)" — matches `test_managedCharging.m` line 166.
  - Lines 90–92: "120 rows = 12 sites x {2026 baseline; 2036/2046/2056 x base/high/stress_combined}" — verified against data.
  - Lines 95–102: "**Current data state (important):** `capacity_basis` is `placeholder` on **all** rows and `service_capacity_kW`/`spare_capacity_kW` are **empty**" — verified against data.
  - Lines 108–138: exact run commands (single scenario, batch `matlab -batch "addpath('src'); run_all_scenarios"`, tests `runtests('tests')`, `buildSimulinkModel(out)`).
  - Line 123: batch writes `outputs/batch_<UTC>/results.csv` + `manifest.txt` + `hashes.txt` (SHA-256).
  - Lines 142–153: `results.csv` column glossary — includes `placeholder_banner`, `service_check` (`within_service`/`exceeds_service`/`service_capacity_unknown`), `cost_status` (`computed` / `tariff_not_supplied`), `skipped_strategies`.
  - Lines 161–176: **five mandatory presentation-use rules**, including the suggested caption *"Illustrates managed-charging behavior; capacity is a planning placeholder pending utility/facility confirmation."* and rule 5: "Never present a Simulink screenshot as evidence of simulation that was not run".
  - Lines 178–187: production restrictions — no feasibility/adequacy/headroom claims; "not engineering, permitting, budget, or procurement values"; no built-in tariff; do not hand-edit the CSV.
  - Lines 189–202: regeneration — `make run-v3` at repo root writes `data/outputs/v3_run/matlab_scenarios.csv`, copy to `matlab/data/canonical/`; `make validate`; golden baseline from first licensed `runtests`.
  - Lines 204–215: limitations — 24-hour single-day only, base-load shape is the legacy Gaussian family, session inputs are planning not telematics, no voltage/phase/thermal modelling, Simulink layer models only the legacy clamp.
- **Notes:** every headline number in this file (120 rows, 12 sites, 19.2 kW, four horizons, 1e-6 tolerance) traces to the canonical CSV or to a test file. No untraceable figures. The `make run-v3` / `make validate` targets both exist (`Makefile` lines 14 and 17).

---

## 9. `matlab/EXECUTION_STATUS.md` (98 lines)

- **Role:** the authoritative record of what has and has not been executed. README line 176 designates it as authoritative.
- **Kind:** authored (status record).
- **Reads:** n/a. References `src/`, `tests/`, `tests/golden/regression_golden.csv`, `outputs/`, `.github/workflows/matlab-manual.yml`, `RUN_ON_LICENSED_MATLAB.md`, `matlab_static_check.py`.

### 9.1 Verbatim claims about execution, with line numbers

| Line(s) | Verbatim quote |
|---|---|
| 3 | `## Status: BLOCKED - no MATLAB available` |
| 5–7 | "On **2026-07-19**, the implementation environment for this repository (macOS, Milestone 2 gap-closure workspace) had **no licensed MATLAB or Simulink installation**. Therefore:" |
| 9–10 | "- **No simulation has been executed.** Not one line of the MATLAB code in `src/` or `tests/` has been run." |
| 11–13 | "- **No test has been run.** The MATLAB unittest suite is authored and statically reviewed only; `tests/golden/regression_golden.csv` does not exist yet because only an actual MATLAB run can create it." |
| 14–16 | "- **No figure, results table, batch output, or `.slx` file in this repository was generated by execution.** The `outputs/` folder is empty by design." |
| 17–18 | "- The CI workflow (`.github/workflows/matlab-manual.yml` at the repository root, manual-trigger) is a definition only; it has never run anywhere." |
| 20–23 | "Nothing in this repository, its documentation, or any presentation built from it may claim an executed simulation until the procedure in `RUN_ON_LICENSED_MATLAB.md` has been completed on a licensed machine and this file has been updated with the run record (step 7 of that document)." |
| 27–31 | "All code was authored as complete, syntactically careful MATLAB (R2025b-style APIs), reviewed statically against the legacy scripts, the Report 13 findings (H1-H15), the improvement backlog (ML-01..ML-12), and the canonical data contract. The exact verification commands await a licensed runner (`RUN_ON_LICENSED_MATLAB.md`)." |
| 33–35 | "## Static checks performed (2026-07-19, Python-based, no MATLAB) — Checker: `matlab_static_check.py` (session scratchpad). Per-file checks on all 9 `src/*.m` and 6 `tests/*.m` files, after stripping comments and string/char literals:" |
| 39–40 | "1. **UTF-8 readability, no TAB characters, ASCII-only content** - PASS for all 15 files." |
| 41–46 | "2. **Block-keyword balance** - count of block openers (`function/if/for/while/switch/try/parfor/arguments`) equals count of `end` keywords at bracket depth 0 (so `x(end)` indexing is excluded) - PASS for all 15 files:" (table at lines 47–62) |
| 63–64 | "3. **Parenthesis/bracket/brace balance** (final depth 0, never negative) - PASS for all 15 files." |
| 65–67 | "4. **First declared function name matches file name** - PASS for all 15 files (required for MATLAB function files and for `runtests` discovery)." |
| 68–70 | "5. **Test harness form** - every `tests/test_*.m` contains `functiontests(localfunctions)` - PASS (6/6)." |
| 71–73 | "6. **Error-identifier cross-check** - every error ID expected by a `verifyError` call in the tests (11 distinct IDs) is defined by an `error(...)` call in `src/` - PASS, zero missing." |
| 74–79 | "7. **Data/legacy fidelity** - `data/canonical/matlab_scenarios.csv` is byte-identical to the Python producer copy (repository-root `data/outputs/v3_run/matlab_scenarios.csv`, regenerated via `make run-v3`), and both `legacy_archive/*.m` files are byte-identical to the original legacy scripts (preserved in the pre-V3 archive branch `archive/pre-milestone2-v3-20260719`) - PASS." |
| 81–83 | "These checks are text-level sanity only. They are **not** a substitute for MATLAB parsing, `runtests`, or simulation, and no such substitution is claimed." |
| 85–93 | "## Known verification gaps (to be closed by the licensed run)" — MATLAB parser acceptance (`detectImportOptions` name-value combinations, `renamevars`, string/table dot-access forms); numerical behavior of the energy-aware scheduler on the full 120-row portfolio; creation of the golden regression baseline; Simulink model build. |
| 95–98 | "## Run record — *(empty - to be filled by the first licensed run per `RUN_ON_LICENSED_MATLAB.md`, step 7)*" |

### 9.2 Independent verification of the static-check claims (done this lane)

- **Claim 2 (block balance table, lines 47–62): REPRODUCES EXACTLY.** I re-implemented the described algorithm (strip comments and string/char literals, count openers, count `end` at bracket depth 0) and got, for the 6 test files: `test_capacityGuard` 15, `test_horizons` 10, `test_loadScenarios` 13, `test_managedCharging` 19, `test_profiles` 11, `test_regression` 14 — identical to the table. Also reproduced all 9 `src/` counts (8, 16, 9, 15, 21, 19, 15, 9, 7).
- **Claim 1 (no tabs, ASCII-only): CONFIRMED** for all 15 files.
- **Claim 5 (`functiontests(localfunctions)` in all 6 test files): CONFIRMED** (6/6, grep).
- **Claim 6 (11 distinct error IDs, zero missing): CONFIRMED.** The tests' `verifyError` IDs are exactly: `capacityGuard:notVerified`, `capacityGuard:unknownBasis`, `capacityGuard:missingBasis`, `loadScenarios:noMatch`, `loadScenarios:fileNotFound`, `loadScenarios:missingColumns`, `loadScenarios:missingCapacityBasis`, `loadScenarios:badArrivalWindow`, `managedCharging:capacityUndefined`, `managedCharging:sessionsRequired`, `managedCharging:badStrategy` = 11. All 11 appear in `error("<id>", ...)` calls in `src/`.
- **Claim 7 part 1 (byte-identical to `data/outputs/v3_run/matlab_scenarios.csv`): NOT VERIFIABLE from this clone.** `data/outputs/` does not exist here; `.gitignore` line 11 excludes `data/outputs/`. This is expected for a generated artifact but means the claim rests on a state that no longer exists in the tree. See Finding F-04.
- **Claim 7 part 2 (legacy scripts byte-identical to the archive branch): partially checkable.** The branch `remotes/origin/archive/pre-milestone2-v3-20260719` **does exist** (`git branch -a`). I did not diff against it. Current hashes: `build_and_run_site_grid_behavior_model.m` = `5ecd5b16b841ea287d7a803d852e7ffa42a9caeb82d881831c43c7699882e96c`, `untitled.m` = `71c0a735b95b2d8e8c379b39e05c5feb213cbf8f65a1f8dd714cbe3940d48382`.
- **`outputs/` empty (line 16): CONFIRMED** — only `.gitkeep`, 0 bytes.
- **`tests/golden/regression_golden.csv` absent (line 12): CONFIRMED** — the `tests/golden/` directory does not exist.

- **Notes:** this file is unusually honest and self-consistent. It is the anchor for the repo's "nothing ran" position and every other document defers to it (README line 176, RUN_ON_LICENSED_MATLAB lines 3–4 and 125, MIGRATION_NOTE line 3, workflow comment lines 5–6). Nothing anywhere in this lane contradicts it.

---

## 10. `matlab/RUN_ON_LICENSED_MATLAB.md` (125 lines)

- **Role:** the copy-paste procedure Phase 2.3 must follow to perform the first execution on licensed MATLAB R2025b.
- **Kind:** authored (runbook).
- **Reads:** n/a. References `EXECUTION_STATUS.md`, `data/canonical/matlab_scenarios.csv`, `src/`, `tests/`, `outputs/`, `legacy_archive/`, and the archive branch `archive/pre-milestone2-v3-20260719` (exists).
- **Preamble (lines 3–8):** authored without MATLAB; "MATLAB **R2025b**, base MATLAB is sufficient for everything except step 6"; "All commands are run from the `matlab/` directory of the repository."

### 10.1 Full step enumeration

| Step | Title (line) | Command | Stated expectation |
|---|---|---|---|
| **1** | Smoke check (seconds) — line 10 | `matlab -batch "addpath('src'); T = loadScenarios('data/canonical/matlab_scenarios.csv'); disp(height(T)); disp(unique(T.horizon_year)')"` (line 13) | Line 16: "Expected: `120`, then `2026 2036 2046 2056`. Any error here is a data or path problem - fix before proceeding." |
| **2** | Test suite (expected ~1-3 minutes) — line 19 | `matlab -batch "addpath('src'); results = runtests('tests'); disp(table(results)); assertSuccess(results)"` (line 22) | Lines 26–33: all tests in `test_loadScenarios`, `test_profiles`, `test_capacityGuard`, `test_managedCharging`, `test_horizons` pass; `test_regression` **creates** `tests/golden/regression_golden.csv` on this first run (logged as "GOLDEN CREATED") and passes; "**Commit that file** - it becomes the drift baseline for every later run." Line 32–33: "If any test fails, stop and report the failure verbatim; do not regenerate goldens to make a failure disappear." |
| **3** | Full batch run (~1-5 min for 120 scenarios) — line 35 | `matlab -batch "addpath('src'); outDir = run_all_scenarios(); disp(outDir)"` (line 39); optional `run_all_scenarios('AssumedSiteCapacity_kW',200)` (line 54) | Lines 42–48: `outputs/batch_<UTCstamp>Z/results.csv` (120 rows, `run_status=ok`, `capacity_basis=placeholder`, non-empty `placeholder_banner` on all rows, `skipped_strategies` says clamp/energy_aware skipped), `manifest.txt`, `hashes.txt` (SHA-256 of input CSV and results.csv). Lines 57–59: with the assumed cap the five capacity-limited metrics populate, "still placeholder-labeled". |
| **4** | Per-scenario figures — line 61 | `matlab -batch "addpath('src'); run_all_scenarios('AssumedSiteCapacity_kW',200,'SavePlots',true)"` (line 64) | Lines 66–70: PNG names follow `scenario_<id>_<site>_<horizon>_<UTC>.png` (ML-12); every figure must visibly show (a) the orange placeholder banner across the top and (b) the source/date footer — "if either is missing, that is a bug; report it." |
| **5** | Comparing against the committed legacy PNGs — line 71 | MATLAB block lines 81–88: `loadScenarios(..., 'SiteId','FFX002','HorizonYear',2026)`; `runScenario(T(1,:), 'GuardMode','planning_illustration', 'ProfileMode','legacy_gaussian', 'AssumedSiteCapacity_kW',205)`; `plotScenario(out,'SaveFigure',true,'OutputFolder','outputs/legacy_compare')` | Lines 90–102: qualitative match with the legacy "Now" PNG — capacity line near **205 kW (legacy 51.4 + 153.6)**, base-load curve identical in shape, EV request peaking at ports × 19.2 kW mid-window. Expected differences: V3 adds banner/basis label/footer; horizon label is **2026, not "Now"**; port counts come from the canonical CSV (H14 fix). "Do **not** expect numeric identity with the legacy year-comparison PNG - the legacy CSV's ports column mixed Python scenario columns (H14) and its horizons were Now/2035/2050." Lines 100–102: the default session-based profile "will look materially different from the legacy PNGs - lower, wider EV demand. That difference is the ML-03 fix, not a regression." |
| **6** | Optional Simulink layer (requires Simulink license) — line 104 | Lines 106–112: `buildSimulinkModel(out); sim('site_grid_behavior_ev_charging_v3');` | Lines 114–118: model builds only if absent (second call prints "NOT rebuilt"); `simulink/site_grid_behavior_ev_charging_v3_params.mat` (and `.sldd` when the dictionary API succeeds) hold externalized parameters; Description carries version/scenario/build stamp; "This layer is illustrative - do not quote numbers from the scope; quote `results.csv`." |
| **7** | Record the run — line 120 | (no command) | See verbatim quote below. |

### 10.2 Step 7 in full (verbatim, lines 120–125) — Phase 2.3 must follow this

```
## 7. Record the run

Append the outcome (date, machine, MATLAB `version`, test summary, batch
`run_id`) to `EXECUTION_STATUS.md`, replacing its BLOCKED banner with an
executed-verification section. Until that happens, no simulation may be
claimed anywhere.
```

- **Notes:**
  - Step 5 references legacy PNG files `professional_site_load_..._Now.png` and `professional_year_comparison_....png` and states explicitly (lines 75–78) they are "preserved in the pre-V3 archive branch … **not in this tree**". I confirmed no such files exist anywhere in the working tree — the document is accurate, not broken.
  - The "old 36-row CSV" (line 79) is consistent with 12 sites × 3 legacy years (Now/2035/2050).
  - `205` in step 5 = `51.4` (FFX002 `base_load_mean_kW`, CSV line 2 — traceable) `+ 153.6` (legacy V2 spare capacity — **not traceable to any current data**; `spare_capacity_kW` is empty on all 120 rows). It is correctly labelled "(legacy 51.4 + 153.6)". See Finding F-05.
  - Step 6's model name `site_grid_behavior_ev_charging_v3` differs from the legacy `site_grid_behavior_ev_charging` (legacy_archive scripts) — the `_v3` suffix is the version stamp, consistent with MIGRATION_NOTE line 54.

---

## 11. `matlab/DATA_DICTIONARY.md` (57 lines)

- **Role:** column-by-column contract for `data/canonical/matlab_scenarios.csv`.
- **Kind:** data-contract (documentation of a generated artifact).
- **Reads:** n/a. References `make run-v3`, `data/outputs/v3_run/matlab_scenarios.csv`, `capacityGuard.m`, `loadScenarios.m`, `managedCharging.m`, canonical `site_table.csv`, README "Regeneration instructions".
- **Header facts (lines 3–8):** "Producer: Python V3 `fcf_m2.matlab_adapter` (canonical contract **1.0.0**, run **`milestone2_v3_20260719T052322Z`**). **120 rows** = 12 sites x {2026 baseline; 2036/2046/2056 x base/high/stress_combined}. **Do not hand-edit; regenerate via `make run-v3`**". Both the contract version and run id match the `source_note` string embedded in all 120 CSV rows.
- **Consumer rules (lines 10–13):** "join on `site_id` only; propagate the placeholder label whenever `capacity_basis` is not `verified_utility`/`verified_facility`; cite contract version + generation stamp when presenting numbers."
- **MATLAB note (lines 15–16):** the CSV column `case` is a MATLAB keyword; `loadScenarios` exposes it as `case_label`. Verified at `src/loadScenarios.m:75`.

### 11.1 Every field defined (all 22, lines 20–41) — type | unit | allowed values | provenance | notes

| Field | Type | Unit | Allowed values / range | Provenance | Notes (verbatim gist) |
|---|---|---|---|---|---|
| `scenario_id` | string | – | `<site_id>_<horizon>_<case>`, unique | adapter-composed | "Primary key of the row" |
| `site_id` | string | – | `FFX001..FFX004`, `PWC001..PWC008` | canonical `site_table.csv` | "**The only join key.** Never join on names" |
| `site_name` | string | – | one canonical spelling per site | canonical `site_table.csv` | "Display only" |
| `horizon_year` | integer | year | present in data: 2026, 2036, 2046, 2056; **any future year row is valid (ML-06)** | canonical scenario table | "Never hard-code the set; read from data" |
| `case` (→ `case_label`) | string | – | `baseline` (2026 only), `base`, `high`, `stress_combined` | canonical scenario table | "Demand-case label from the Python model" |
| `ports` | integer | count | `>= 0` | "Python right-sizing model (rank/case-matched)" | "Recommended charging ports for this scenario" |
| `charger_power_kW` | double | kW | `> 0` (currently 19.2 on all rows) | "planning assumption (Level-2 dual-port class)" | "Grid-side per-port rating" |
| `spare_capacity_kW` | double | kW | **empty on all rows** (else `>= 0`) | "unconfirmed - V2 upload value was rejected as placeholder" | "Empty by design until facility data lands; empty -> capacity may be undefined" |
| `service_capacity_kW` | double | kW | **empty on all rows** (else `> 0`) | "pending utility/facility confirmation" | "Preferred capacity definition when present" |
| `capacity_basis` | string | – | `verified_utility`, `verified_facility`, `engineering_estimate`, `planning_proxy`, `placeholder`, `unknown` (controlled vocabulary, `capacityGuard.m`) | adapter; **currently `placeholder` on ALL 120 rows** | "**Machine-readable provenance gate.** Non-verified => mandatory banner, no feasibility claims" |
| `capacity_source` | string | – | free text | adapter | "Human-readable provenance for `capacity_basis`" |
| `base_load_mean_kW` | double | kW | `>= 0` | "legacy adapter estimate (constant across horizons - H15)" | "Daily mean building load; label year-comparisons accordingly" |
| `base_load_peak_kW` | double | kW | `>= base_load_mean_kW` | legacy adapter estimate | "Daily peak building load" |
| `arrival_start_hr` | double | hour (0-24) | `< arrival_end_hr` | Python model site-use profile | "Start of the EV arrival window" |
| `arrival_end_hr` | double | hour (0-24) | `> arrival_start_hr` | Python model site-use profile | "End of the EV arrival window" |
| `dwell_hr` | double | hours | `> 0` | Python model site-use profile | "Vehicle dwell; **consumed** by the session model (legacy H1 fixed)" |
| `sessions_per_day` | double | sessions/day | `>= 0`; fractional allowed (expected value) | "Python demand model per horizon/case" | "Drives session generation; conserved exactly in deterministic mode" |
| `energy_per_session_kWh` | double | kWh (battery-side) | `>= 0` | Python demand model | "Grid-side energy = value / charger efficiency" |
| `managed_charging_policy` | string | – | currently `none`; reserved: strategy names of `managedCharging.m` | adapter | "Placeholder for a per-site policy assignment; V3 runs all applicable strategies regardless" |
| `model_rank` | integer | rank | `>= 1` | "Python site-ranking model" | "Portfolio priority rank of the site" |
| `electrical_risk_level` | string | – | present in data: `medium`, `high` (vocab may extend: `low`) | "Python electrical-risk screen" | "Qualitative screen, not a measurement" |
| `source_note` | string | – | free text | adapter | "Carries contract version, run id, and the placeholder-capacity warning; keep with any exported row" |

- **Empty-value semantics (lines 43–49):** "Empty numeric cells import as `NaN` in MATLAB. `capacityGuard` treats `NaN` service/spare capacity as 'capacity undefined': capacity-limited strategies refuse to run unless an explicit `AssumedSiteCapacity_kW` planning assumption is supplied, and that assumption is itself labeled as placeholder-grade."
- **Validation applied on load (lines 51–57):** all columns required (missing ⇒ error); `capacity_basis` non-empty on every row (fail-closed); `ports >= 0`, `charger_power_kW > 0`, `dwell_hr > 0`, `sessions_per_day >= 0`, `energy_per_session_kWh >= 0`, `arrival_end_hr > arrival_start_hr`.
- **Verification against `src/loadScenarios.m`:** the required-column list at `loadScenarios.m:81–87` contains 19 names and **omits `model_rank`, `electrical_risk_level`, `source_note`** — so the dictionary's "All columns above are required" (line 53) is slightly stronger than the code. The five numeric predicates at `loadScenarios.m:113–120` and the window check at 122 match the dictionary exactly. Minor doc/code mismatch, low severity — see Finding F-06.
- **Notes:** every observed CSV value conforms to this dictionary. No range violations.

---

## 12. `matlab/legacy_archive/MIGRATION_NOTE.md` (69 lines)

- **Role:** explains what the two archived legacy scripts were, why two existed, and how each legacy local function maps to a V3 `src/` module (backlog item ML-02).
- **Kind:** authored (migration record).
- **Reads:** n/a. References `../EXECUTION_STATUS.md`, `../src/*`, `file1_phase2/`, archive branch `archive/pre-milestone2-v3-20260719` (branch exists on origin).
- **Key contents:**
  - Line 3: "Date: 2026-07-19 (static authoring; no MATLAB execution - see `../EXECUTION_STATUS.md`)".
  - Lines 11–16: `build_and_run_site_grid_behavior_model.m` = "The documented 'starter' script (matches the legacy `README.txt`)"; `untitled.m` = "The diverged copy that actually generated the committed professional PNGs and the animated GIF".
  - Lines 17–18: "The originals remain **unchanged** in the pre-V3 archive branch for provenance. **Nothing in this archive is on the MATLAB path and nothing here is executed by the V3 pipeline.**"
  - Lines 20–36 (hypothesis H13, CONFIRMED): `untitled.m` began as a copy and diverged; core math identical; `untitled.m` added the multi-tile professional plot pipeline, a `uifigure` dashboard with slider/play, an animated GIF exporter (`createLoadAnimation`), a figure save pipeline (`exportgraphics` into `outputs/`), a CSV path fallback (`data/` subfolder), and a friendlier site-not-found error. Line 35–36: "That left **two sources of truth**".
  - Lines 44–56 — the legacy→V3 mapping table (10 rows): `loadScenario`→`src/loadScenarios.m`; `makeProfiles`→`src/makeSessionProfiles.m` (H1/H2/H5); capacity line inside `makeProfiles`→`src/capacityGuard.m` (H3); managed clamp inside `makeProfiles`→`src/managedCharging.m` (H4); (absent)→`src/electricalEconomics.m` (ML-11/H6); top-level script body→`src/runScenario.m` (H9); `runAllYearsAfter` loop→`src/run_all_scenarios.m` (ML-08/ML-12) "replaces the hard-coded `["Now","2035","2050"]` loop (H7)"; `plotScenario`/`plotYearComparison`/styling→`src/plotScenario.m`; `buildModel`→`src/buildSimulinkModel.m` "(never delete/rebuild - reverses H8)"; `createDashboard`/`createLoadAnimation`→**not migrated** ("Report 13: 'adds motion, not information'").
  - Lines 58–69 — four behavioural differences: (1) default EV request is no longer ports × charger kW; (2) capacity may legitimately be undefined — "The canonical CSV ships with empty `service_capacity_kW`/`spare_capacity_kW` and `capacity_basis=placeholder` on all 120 rows"; (3) no feasibility claims; (4) the Simulink model is optional.
- **Notes:** all 9 named V3 `src/` files exist. The one legacy year-list reference (line 52) is explicitly framed as "replaces the hard-coded … loop (H7)" — legitimate legacy labelling, not stale text.

---

## 13. The two archived legacy scripts

### 13.1 `matlab/legacy_archive/build_and_run_site_grid_behavior_model.m` (326 lines)

- **Role:** the documented pre-V3 "starter" script — reads a site/year CSV, builds 24-h base + EV profiles, programmatically builds a Simulink model, runs it, and prints/plots a summary.
- **Kind:** vendored history (byte-preserved legacy source). LF line endings. SHA-256 `5ecd5b16…82e96c`.
- **Reads:** `site_year_scenarios_from_andy_v2.csv` — **hard-coded at line 26, and this file exists nowhere in the repo** (`find` returned nothing). Not a defect: the script is archived history, never executed.
- **Written by / read by:** **nothing live references it.** A repo-wide grep for `build_and_run_site_grid_behavior_model` returns only `matlab/RUN_ON_LICENSED_MATLAB.md` (prose), `matlab/legacy_archive/MIGRATION_NOTE.md` (prose), and the two archive files themselves. It is **pure history**, not on the MATLAB path, not invoked by `src/`, `tests/`, or the CI workflow.
- **Key contents:**
  - USER SETTINGS (lines 26–36): `csvFile = "site_year_scenarios_from_andy_v2.csv"`; `selectedSite = "City of Fairfax Regional Library"` (**hard-coded client site name — H9**); `selectedYear = "Now"`; `runAllYearsAfter = true`.
  - Line 63–64: **`years = ["Now","2035","2050"];`** — the legacy horizon list (H7). This is the exact literal that `test_horizons.m:56` guards against reappearing in `src/`.
  - `loadScenario` (78–102): `detectImportOptions`, `setvartype(["scenario_id","site_name","year"],"string")`, **matches on `site_name`** (line 83) — the anti-pattern that DATA_DICTIONARY now forbids ("Never join on names").
  - `makeProfiles` (104–175): time axis `dt_min = 5`, `t_hr = (0:dt_min/60:24)'`; base load shape = `exp(-0.5*((t-14)/4.5)^2) + 0.25*exp(-0.5*((t-8)/1.7)^2) + 0.15*exp(-0.5*((t-19)/2.0)^2)`, normalised, then `mean + (peak-mean)*shape`; **`fullEV_kW = s.ports * s.charger_power_kW`** (line 124 — hypothesis H2); Gaussian arrival shape centred at `(start+end)/2` with `width = max((end-start)/2, 0.5)`; **`capacity_kW = s.base_load_mean_kW + s.spare_capacity_kW`** (line 138 — the "legacy definition" that `test_capacityGuard.m:101` still reproduces); clamp rule `evManaged = min(evRequest, max(capacity - baseLoad, 0))`; energies by `trapz`; `curtailedEnergy_kWh = max(requested - deliveredManaged, 0)`.
  - **`dwell_hr` is loaded (line 101) and never used** — hypothesis H1, exactly as MIGRATION_NOTE and `test_profiles.m:24` describe.
  - `buildModel` (177–257): `if isfile(modelName + ".slx") delete(...)` at lines 182–184 — the **delete-and-rebuild** behaviour that is hypothesis H8 and is reversed in V3. Model name `site_grid_behavior_ev_charging`; `StopTime 86400`, `Solver ode3`, `FixedStep 300`; blocks From Workspace ×3, Sum ×2, Mux ×2, MATLAB Function (Stateflow EMChart with script `available = max(u(2)-u(3),0); y = min(u(1),available);`), Scope, To Workspace ×2 (`sim_total_unmanaged`, `sim_total_managed`, "Structure With Time").
  - `plotScenario` (259–271), `printSummary` (273–291), `plotYearComparison` (293–310), `printYearComparison` (312–326) — the last prints the header `"\nNOW / 2035 / 2050 COMPARISON\n"` (line 313).
- **Notes:** no capacity banner, no basis label, no footer, no provenance — precisely the gaps V3 closes. Contains one client facility name in plain text (line 29).

### 13.2 `matlab/legacy_archive/untitled.m` (981 lines)

- **Role:** the diverged copy of the starter script that actually produced the committed professional PNGs and the animated GIF. Read in full.
- **Kind:** vendored history. **CRLF line endings** (the only CRLF file in this lane). SHA-256 `71c0a735…0d48382`.
- **Reads:** `site_year_scenarios_from_andy_v2.csv` (line 25) with a fallback to `fullfile("data", "site_year_scenarios_from_andy_v2.csv")` (lines 27–32) — neither exists in the repo. Writes into `fullfile(pwd,"outputs")` (line 39).
- **Written by / read by:** **nothing live references it.** Same grep result as §13.1 — only prose mentions in `RUN_ON_LICENSED_MATLAB.md` and `MIGRATION_NOTE.md`. **Pure history.**
- **Key contents (beyond the shared core, which is identical):**
  - Header docstring (lines 1–20) is titled `%% build_and_run_site_grid_behavior_model.m` — the smoking gun for H13 (it began as a copy; the header was never renamed).
  - Settings (lines 34–42): same hard-coded `selectedSite = "City of Fairfax Regional Library"`, `selectedYear = "Now"`; plus `outputFolder`, `saveFigures = true`, `createInteractiveDashboard = true`, `createAnimatedGIF = true`.
  - Line 87: **`years = ["Now","2035","2050"];`** — second occurrence of the legacy horizon list.
  - `loadScenario` (102–133): adds an `isfile` guard and, on no match, prints `unique(tbl.site_name)` before erroring (the "friendlier site-not-found error listing available sites" of MIGRATION_NOTE line 33–34). Still matches on `site_name`.
  - `makeProfiles` (135–193): **mathematically identical** to the starter script — same shape constants (14/4.5, 8/1.7 ×0.25, 19/2.0 ×0.15), same `fullEV_kW = ports*charger_power_kW`, same `capacity = base_load_mean + spare`, same clamp, same `trapz` energies. Confirms MIGRATION_NOTE's "core math is identical in both".
  - `buildModel` (195–292): same delete-and-rebuild, same blocks/wiring, slightly different block Positions, chart script carries explanatory comments, plus a `try Simulink.BlockDiagram.arrangeSystem(modelName); catch end` (286–289).
  - `plotScenario` (294–482): the professional 2×2 `tiledlayout`; palette `cBase [0.12 0.32 0.65]`, `cUnmanaged [0.82 0.20 0.16]`, `cManaged [0.13 0.55 0.36]`, `cCapacity [0.32 0.22 0.55]`, `cEV [0.95 0.58 0.16]`, `cGray [0.35 0.35 0.35]`; figure `Position [80 60 1450 820]`; overload shading via `fill`; summary bar tile with categories `["Peak unmanaged","Peak managed","Max overload","Curtailed energy"]`; **an auto-generated conclusion annotation** (lines 452–473) with three branches — "Result: unmanaged charging exceeds site capacity, while managed charging keeps total load within the modeled limit." / "Result: both unmanaged and managed charging show overload risk; site may need capacity upgrades or fewer ports." / "Result: this scenario stays within modeled site capacity. No overload is observed under current assumptions." Saves to `professional_site_load_<site>_<year>.png`.
  - `plotYearComparison` (484–622): colours `cNow`, `c2035`, `c2050`; subtitle literal `siteLabel + " | Now / 2035 / 2050 scenarios"` (line 507); tiles for managed load across years, recommended port count bar, and peak/overload grouped bars. Saves `professional_year_comparison_<site>.png`.
  - `createDashboard` (624–783): `uifigure` 1250×760, `uiaxes` main + EV, `uislider` limits `[0 24]` value 12 with MajorTicks `0:4:24` / MinorTicks `0:1:24`, a "Play 24-hour animation" `uibutton`, nested `updateDashboard`/`playDashboard` (`linspace(0,24,120)`, `pause(0.03)`).
  - `createLoadAnimation` (785–905): GIF exporter, `frameStep = 3`, `DelayTime 0.06`, `LoopCount Inf`, output `animated_site_load_<site>_<year>.gif`.
  - `printSummary` (907–925) / `printYearComparison` (927–947): the latter prints `"\nNOW / 2035 / 2050 COMPARISON\n"` (line 928).
  - Helpers: `formatAxes` (949–958), `saveFigure` (960–977, `exportgraphics` at 300 dpi with `saveas` fallback), `safeName` (979–981, `regexprep(..., '[^a-zA-Z0-9]+', '_')`).
- **Notes:**
  - The `printSummary` label differs between the two scripts: starter line 278 says `"Ports from Python/right-sizing model: %.0f"`, `untitled.m` line 912 says `"Ports from right-sizing model: %.0f"` — a small divergence confirming the copy-and-drift story.
  - The auto-generated "Result:" annotation is exactly the kind of unlabelled feasibility conclusion that V3's `capacityGuard` fail-closed design exists to prevent — worth citing when explaining why the guard is there.
  - Both legacy scripts contain the client facility name `"City of Fairfax Regional Library"` in plain text; a public harness repo must either exclude `legacy_archive/` or scrub those two lines (starter line 29, untitled line 34) plus the `printYearComparison`/`plotYearComparison` prose. No addresses, coordinates, or contacts appear.

---

## 14. Octave-compatibility inventory for the 6 test files

Same construct list as lane L03. **Verdict: none of the six test files is Octave-runnable, and the blockers are structural, not cosmetic.** Even the newest Octave lacks the `matlab.unittest` framework and the `table` type; there is no drop-in shim.

| Construct | Octave status | Occurrences | Files |
|---|---|---|---|
| `functiontests(localfunctions)` harness | **Not available** — `matlab.unittest` function-based test framework has no Octave equivalent | 6 files, 1 each | all 6 |
| `verifyEqual` / `verifyTrue` / `verifyFalse` / `verifyError` / `verifyGreaterThan(OrEqual)` / `verifyLessThan(OrEqual)` | **Not available** (TestCase qualification methods) | 92 calls total (36 / 15 / 4 / 15 / 13+2 / 5+2) | all 6 |
| `"RelTol"` / `"AbsTol"` name-value on `verifyEqual` | Not available (part of the above) | 6 `RelTol`, 4 `AbsTol` | capacityGuard, profiles, regression, managedCharging |
| `setupOnce` / `teardownOnce` / `testCase.TestData` | Not available | 6 / 2 / 65 | all 6 (teardownOnce only in horizons, loadScenarios) |
| `log(testCase, 1, ...)` (unittest diagnostic logging) | Not available | 1 | test_regression.m:50 |
| `table` type, `readtable`, `writetable`, `height()`, `removevars`, `sortrows` on tables, `struct2table` | **Not in core Octave** (`readtable`/`writetable` only partially exist in recent Octave; `table` objects, `removevars`, `renamevars`, `struct2table` do not) | readtable 5, writetable 5, height 9, removevars 1, sortrows 1, struct2table 1, `table(...)` ctor 12 | horizons, loadScenarios, regression, managedCharging |
| `detectImportOptions` + `"TextType","string"` + `"VariableNamingRule","preserve"` | **Not available** | 4 calls (TextType 5, VariableNamingRule 4) | horizons, loadScenarios |
| `T.Properties.VariableNames` / `T.Properties.UserData` | Not available (table metadata) | 1 / 1 | loadScenarios |
| Table dynamic field access `T.(name)` and `newRow.("case")` | Not available | 5 | horizons (2), regression (3) |
| `string` scalar type: `string()`, `strlength`, `contains(...,"IgnoreCase",true)`, `"a" + "b"` concatenation | Octave has no `string` class; double quotes produce char arrays and `+` performs **numeric addition on char codes**, silently wrong rather than erroring | `string(` 10, `strlength` 3, `contains(` 3, `"a" + ...` 2 (loadScenarios:116, regression:50) | capacityGuard, loadScenarios, regression, managedCharging, horizons |
| Double-quoted literals used as strings throughout | Semantics differ (char vs string) | ~550 quote characters across the 6 files (108/66/90/130/70/84) | all 6 |
| `for x = ["A","B"]` over a string array | In Octave `["FFX002","PWC001"]` concatenates into one char row vector → loop body runs once with the whole concatenation | 1 (`test_regression.m:111`) | regression |
| `mfilename("fullpath")` | Available in Octave but with double-quoted-arg char semantics — works | 7 | all 6 |
| `rmfield`, `unique`, `ismember`, `sprintf`, `fileread`, `tempname`, `isfile`, `trapz`, `dir`, `fileparts`, `fullfile`, `addpath`, `mkdir`, `rmdir(...,"s")` | Available in Octave | rmfield 1, unique 3, ismember 1, sprintf 4, fileread 1, tempname 2, isfile 1, trapz 1 | various |
| `%#ok<AGROW>` mlint pragma | Harmless comment in Octave | 1 (`test_regression.m:116`) | regression |
| `categorical` | not used in the tests | 0 | — |

**Practical implication for Phase 2:** an Octave-based CI path for these tests would require a full rewrite of the harness (assertions → a plain assert helper, tables → structs/cell arrays, `readtable` → `csvread`/`textscan`, string arrays → cellstr) — that is a port, not a compatibility patch. The `src/` modules carry the same table/string dependencies (`renamevars`, `T.Properties.UserData`, `detectImportOptions`), so porting only the tests would not help.

---

## 15. `matlab/outputs/.gitkeep`

- **Role:** placeholder that keeps the empty `outputs/` directory in git.
- **Kind:** fixture (empty sentinel).
- **Reads:** n/a. **Confirmed 0 bytes.**
- **Written by / read by:** kept alive by `.gitignore` lines 13–15: `matlab/outputs/*` is ignored with `!matlab/outputs/.gitkeep` re-included. `run_all_scenarios` writes `outputs/batch_<UTC>Z/` here at run time (README line 123, RUN_ON_LICENSED_MATLAB step 3).
- **Notes:** consistent with EXECUTION_STATUS.md line 16 ("The `outputs/` folder is empty by design").

---

## 16. `.github/workflows/matlab-manual.yml` (53 lines)

- **Role:** manual-trigger GitHub Actions workflow that would run the MATLAB unit tests and a batch smoke run on a licensed runner (ML-09).
- **Kind:** authored (CI config). Never executed (EXECUTION_STATUS.md lines 17–18).
- **Reads:** the repo checkout; `matlab/src`, `matlab/tests`; consumes the repository secret `MLM_LICENSE_TOKEN`.
- **Key contents, line by line:**
  - Lines 1–7 (header comment): "MATLAB verification for the Milestone 2 V3 site-grid behavior model (ML-09). MANUAL TRIGGER ONLY: MATLAB batch licensing in CI requires the MLM_LICENSE_TOKEN secret (see matlab-actions/setup-matlab docs). Until that secret is configured, MATLAB code in this repo is statically checked only — no execution is claimed anywhere (see matlab/EXECUTION_STATUS.md). The core pipeline needs base MATLAB only; Simulink is optional and not exercised by the tests."
  - Line 9: `name: matlab-manual`; lines 11–12: `on: workflow_dispatch:` (no push/PR triggers).
  - Lines 14–17: job `test`, name "Run MATLAB unit tests + batch smoke run", `runs-on: ubuntu-latest`.
  - Lines 19–20: `actions/checkout@v4`.
  - Lines 22–28: `matlab-actions/setup-matlab@v2` with `release: R2025b`, `products: MATLAB` (no Simulink), `env: MLM_LICENSE_TOKEN: ${{ secrets.MLM_LICENSE_TOKEN }}`.
  - Lines 30–35: `matlab-actions/run-tests@v2` with `source-folder: matlab/src`, `select-by-folder: matlab/tests`, `test-results-junit: matlab/test-results/results.xml`.
  - Lines 37–44: `matlab-actions/run-command@v2` running `cd matlab; addpath('src'); outDir = run_all_scenarios(); disp(outDir);`.
  - Lines 46–53: `actions/upload-artifact@v4`, `if: always()`, name `matlab-results`, paths `matlab/test-results/` and `matlab/outputs/`.
- **Notes:**
  - `MLM_LICENSE_TOKEN` is a secret *reference*, not a value — no credential is committed.
  - The batch step runs `run_all_scenarios()` with **no** `AssumedSiteCapacity_kW`, so clamp and energy_aware are skipped and only the unmanaged metrics populate — consistent with RUN_ON_LICENSED_MATLAB step 3's stated expectation.
  - See Finding **F-01**: the artifact upload does not include `matlab/tests/golden/`, so the golden baseline that `test_regression` creates in CI is generated and then discarded on every run.

---

## 17. Findings (ranked)

### F-01 — CI workflow makes `test_regression` permanently self-baselining; the golden file it creates is discarded (**HIGH**)
`matlab/tests/test_regression.m:45–53` writes `tests/golden/regression_golden.csv` whenever it is absent and then passes against its own fresh output. `RUN_ON_LICENSED_MATLAB.md:29–30` correctly says "**Commit that file** - it becomes the drift baseline for every later run." But `.github/workflows/matlab-manual.yml:50–53` uploads only `matlab/test-results/` and `matlab/outputs/` — **not** `matlab/tests/golden/`. Because a CI checkout never contains the golden file (it is not in the repo) and the run's copy is never uploaded or committed, every CI invocation of `matlab-manual` would create a fresh baseline, pass trivially, and throw it away. The regression harness can therefore never detect drift when driven from CI. Fix: add `matlab/tests/golden/` to the upload paths, and/or have CI fail when the golden is missing rather than self-creating.

### F-02 — `matlab/tests/golden/regression_golden.csv` does not exist; `test_regression.m` is the only consumer and creates it (**MEDIUM, expected but load-bearing**)
The directory `matlab/tests/golden/` is absent (`ls` error). `test_regression.m:28–29` and `:45` depend on it. EXECUTION_STATUS.md:12–13 and RUN_ON_LICENSED_MATLAB.md:28–30 both correctly disclose this. Not a contradiction — but Phase 2.3 must actually commit the file after the licensed run or the regression suite has no teeth. This is item 7 on `docs/operations/open-human-actions.md:14`.

### F-03 — Phase 2.2 exposure: the canonical CSV cannot be published as-is (**HIGH, gating**)
`matlab/data/canonical/matlab_scenarios.csv` carries, per site: real facility names (`site_name`, 12 named public buildings in Fairfax County and Prince William County), county-revealing IDs (`site_id` = `FFX###`/`PWC###`), a **portfolio priority ranking** (`model_rank`, 1–12, one per site), a **qualitative electrical-risk verdict** (`electrical_risk_level`: 3 sites `high`, 9 `medium`), the right-sizing model's **recommended port counts** (`ports`, 2–8), the demand model's **per-scenario session forecasts** (`sessions_per_day`, 120 distinct values), and per-facility **load estimates** (`base_load_mean_kW` 50.2–115.0, `base_load_peak_kW` 66.3–151.8). `capacity_source` additionally states "12/12 sites unconfirmed". Full column-by-column classification in §7.1. A public harness repo needs a de-identified or synthetic fixture.

### F-04 — EXECUTION_STATUS.md's byte-identity claim references a file that does not exist in the tree (**LOW/INFO**)
`matlab/EXECUTION_STATUS.md:74–79` asserts the canonical CSV "is byte-identical to the Python producer copy (repository-root `data/outputs/v3_run/matlab_scenarios.csv`…)". `data/outputs/` does not exist in this clone and is gitignored (`.gitignore:11`). The claim is therefore unverifiable from the repo alone. Not a fabrication — the producer path is a generated artifact by design — but Phase 1 should either soften the wording or add a `make`-driven re-verification step. (I did independently verify the *schema* has not drifted: `src/fcf_m2/matlab_adapter.py:15–19` `MATLAB_COLUMNS` matches the CSV header exactly, 22 names in the same order.)

### F-05 — `205 kW` / `153.6 kW` in RUN_ON_LICENSED_MATLAB step 5 and `test_capacityGuard.m:92,101` trace only to rejected V2 data (**LOW, correctly labelled**)
`RUN_ON_LICENSED_MATLAB.md:86,90–91` instructs `'AssumedSiteCapacity_kW',205` and explains "capacity line near 205 kW (legacy 51.4 + 153.6)". `51.4` is FFX002's `base_load_mean_kW` (CSV line 2, traceable). `153.6` is a legacy spare-capacity value that appears in **no** current data — `spare_capacity_kW` is empty on all 120 rows, and DATA_DICTIONARY:27 records that "V2 upload value was rejected as placeholder". The same number appears as a test fixture at `test_capacityGuard.m:92` and as `theoreticalMax = 8 * 19.2` at `test_profiles.m:51`. Every occurrence is explicitly labelled legacy or synthetic, so this is **not** a horizon/number violation — but anyone reusing `205` outside that labelled context would be publishing a rejected placeholder.

### F-06 — DATA_DICTIONARY says "All columns above are required" but `loadScenarios` requires only 19 of 22 (**LOW**)
`matlab/DATA_DICTIONARY.md:53` — "All columns above are required; missing column => error." `src/loadScenarios.m:81–87` lists 19 required names and omits `model_rank`, `electrical_risk_level`, and `source_note`. A CSV missing those three would load without error, contradicting the dictionary. Trivially fixable in either direction; note that keeping them optional is actually *helpful* for a de-identified public fixture (see F-03).

### F-07 — `spare_capacity_kW` / `service_capacity_kW` are never type-forced on import; their MATLAB type on the real CSV is unverified (**LOW/INFO, unverified because MATLAB never ran**)
`src/loadScenarios.m:59–69` forces `string` type on 9 text columns but relies on `detectImportOptions` heuristics for the numeric ones. Both capacity columns are **empty on all 120 rows**, and `detectImportOptions` may well type an all-empty column as text rather than `double`. `loadScenarios`'s `localAssertNumeric` is not applied to either column (lines 113–120), so no error would fire there. `src/capacityGuard.m:184–192` (`localNumericOrNaN`) does defend, converting via `str2double` when the value is not numeric — so the failure is contained. `test_capacityGuard.m` cannot catch this because its fixture hardcodes `NaN` (lines 142–143). Flagging so Phase 2.3 watches for it during step 1/2 of the licensed run; EXECUTION_STATUS.md:87 already lists "`detectImportOptions` name-value combinations" as a known gap.

### F-08 — Horizon-convention check: **clean** (**INFO, no defect**)
All five occurrences of legacy-year tokens in this lane are explicitly and correctly framed as legacy: `test_horizons.m:3` (docstring describing the legacy hard-code), `test_horizons.m:56` (the static guard string literal itself), `MIGRATION_NOTE.md:52` ("replaces the hard-coded `["Now","2035","2050"]` loop (H7)"), `RUN_ON_LICENSED_MATLAB.md:90,94,98` (explicitly "horizon label is 2026, not 'Now'" and "its horizons were Now/2035/2050"). The two `legacy_archive/*.m` files contain the literal `years = ["Now","2035","2050"]` (starter line 64, untitled line 87) but are byte-preserved archive material that MIGRATION_NOTE.md:17–18 states is "not on the MATLAB path and nothing here is executed by the V3 pipeline" — verified: nothing live references them. No `2035`, `2050`, `"Now"`, or `10/20/30-year` framing appears in `matlab/README.md`, `EXECUTION_STATUS.md`, `DATA_DICTIONARY.md`, the six test files' assertions, or the CI workflow.

### F-09 — eGRID emissions factor: **clean** (**INFO, no defect**)
`596.3`, `590.2`, `eGRID`, `lb CO2`, and `CO2e` appear **nowhere** in `matlab/` or `.github/`. The MATLAB layer models power and energy only; emissions are not in scope for any file in this lane.

### F-10 — Secrets / absolute paths: **clean** (**INFO, no defect**)
No `/Users/`, `/home/`, `AKIA*`, `arn:aws:*`, 12-digit AWS account IDs, API keys, or passwords in any assigned file. The single credential-adjacent token is `${{ secrets.MLM_LICENSE_TOKEN }}` at `.github/workflows/matlab-manual.yml:28`, which is a reference, not a value.

### F-11 — Cosmetic/minor observations (**INFO**)
- `matlab/legacy_archive/untitled.m` is the only **CRLF**-line-ending file in the lane. Preserved deliberately (byte-identical archive), but it will make any future diff noisy.
- `test_horizons.m:3–5` prose says the tests prove "2036/2046/2056" run, while the assertion at line 37 requires all four including 2026 — prose narrower than code.
- `src/loadScenarios.m` computes `UserData.horizons_in_data` **after** filtering (line 150 filters, line 165 computes), so the field means "horizons in the returned subset", not "horizons in the file". `test_loadScenarios.m:47–49` only exercises the unfiltered case.
- Legacy `printSummary` label drifted between the two archived scripts: starter line 278 "Ports from Python/right-sizing model" vs untitled line 912 "Ports from right-sizing model" — corroborating evidence for H13.
- `legacy_archive/untitled.m:452–473` auto-generates unlabelled feasibility conclusions ("Result: this scenario stays within modeled site capacity…"). This is the concrete artifact that V3's fail-closed `capacityGuard` exists to prevent; useful to cite when defending the guard.
