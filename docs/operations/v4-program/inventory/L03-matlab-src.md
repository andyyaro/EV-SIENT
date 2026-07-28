# LANE L03 — MATLAB SOURCE (`matlab/src/`)

Ground-truth inventory. All 9 assigned files read end-to-end (2001 lines total).
Repo root for all relative paths below: `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo`.

Line counts as read:

| file | lines |
|---|---|
| `matlab/src/buildSimulinkModel.m` | 239 |
| `matlab/src/capacityGuard.m` | 199 |
| `matlab/src/electricalEconomics.m` | 158 |
| `matlab/src/loadScenarios.m` | 184 |
| `matlab/src/makeSessionProfiles.m` | 303 |
| `matlab/src/managedCharging.m` | 307 |
| `matlab/src/plotScenario.m` | 228 |
| `matlab/src/run_all_scenarios.m` | 198 |
| `matlab/src/runScenario.m` | 185 |

`matlab/src/` is flat — no `+namespace` directories, no `@class` directories, no subfolders
(verified: directory holds exactly the 9 `.m` files).

**Global context that governs this whole lane:** `matlab/EXECUTION_STATUS.md:3` declares
`## Status: BLOCKED - no MATLAB available`, and `:9-10` state "**No simulation has been executed.**
Not one line of the MATLAB code in `src/` or `tests/` has been run." Every behavioural claim in
this inventory is therefore a claim about *authored source*, never about observed output.

---

### matlab/src/loadScenarios.m

- **Role:** Reads the canonical adapter CSV into a validated MATLAB table and applies fail-closed
  column/value validation plus optional site/horizon/case/scenario filtering.
- **Kind:** authored
- **Reads:** `csvFile` (first positional arg). Callers pass
  `matlab/data/canonical/matlab_scenarios.csv` (default constructed in
  `run_all_scenarios.m:45-47`). No other file I/O.
- **Written by / read by:** Read by `matlab/src/run_all_scenarios.m:76` and by
  `matlab/tests/test_loadScenarios.m`, `test_horizons.m`, `test_regression.m` (test names observed
  in `matlab/tests/`, not read in this lane). Consumes the CSV produced by the Python
  `fcf_m2.matlab_adapter` (per docstring `:5-6`, `:52-53`, `:93-94`).
- **Key contents:**
  - Signature: `function T = loadScenarios(csvFile, varargin)` (`:1`).
  - `inputParser` with 4 `addParameter`s (`:37-43`): `SiteId` (default `string.empty`, validator
    `@(v) isstring(string(v))`), `HorizonYear` (default `[]`, `@(v) isnumeric(v)`), `Case`
    (default `string.empty`), `ScenarioId` (default `string.empty`).
  - File-existence guard `:49-54` → error id `loadScenarios:fileNotFound`.
  - Import: `detectImportOptions(csvFile, "TextType","string", "VariableNamingRule","preserve")`
    (`:59-60`); string columns forced via `setvartype` (`:66-69`).
  - `stringCols` (`:62-65`) = `["scenario_id","site_id","site_name","case","capacity_basis",
    "capacity_source","managed_charging_policy","electrical_risk_level","source_note"]` (9 names).
  - Column `case` renamed to `case_label` (`:74-76`) via `renamevars` because `case` is a MATLAB
    keyword. Documented at `:56-58`.
  - `requiredCols` (`:81-87`), 19 names: `scenario_id, site_id, site_name, horizon_year,
    case_label, ports, charger_power_kW, spare_capacity_kW, service_capacity_kW, capacity_basis,
    capacity_source, base_load_mean_kW, base_load_peak_kW, arrival_start_hr, arrival_end_hr,
    dwell_hr, sessions_per_day, energy_per_session_kWh, managed_charging_policy`.
  - Error ids emitted: `loadScenarios:fileNotFound`, `:missingColumns`, `:missingCapacityBasis`,
    `:badArrivalWindow`, `:noMatch`, `:columnType`, `:badValue` (7 distinct).
  - Numeric sanity predicates (`:113-120`): `ports >= 0`, `charger_power_kW > 0`, `dwell_hr > 0`,
    `sessions_per_day >= 0`, `energy_per_session_kWh >= 0`; plus
    `arrival_end_hr > arrival_start_hr` (`:122-130`). NaN values are *exempt* — `:176`
    `ok = isnan(v) | predicate(v)`.
  - Provenance metadata attached (`:160-166`): `T.Properties.Description =
    "Canonical MATLAB scenario table (auto-generated adapter)"`; `T.Properties.UserData` struct with
    `source_csv`, `loaded_utc` (UTC ISO8601), `horizons_in_data`, `cases_in_data`.
  - Local function `localAssertNumeric(T, colName, predicate, message)` (`:169`).
- **Notes:**
  - Docstring `:11-14` states explicitly "Horizons are read FROM THE DATA; no year list is
    hard-coded anywhere in this repository (ML-06)". Verified true — zero hard-coded years appear
    anywhere in the 9 files (grep for 2026/2030/2035/2036/2040/2046/2050/2056 returns nothing).
  - The actual CSV (`matlab/data/canonical/matlab_scenarios.csv`, header row read) has **22**
    columns; the 19 required are all present, plus `model_rank`, `electrical_risk_level`,
    `source_note`. 120 data rows. Distinct `horizon_year` values in the file: **2026, 2036, 2046,
    2056** — canonical, no violation.
  - `T.Properties.UserData` is set but **no consumer in `src/` ever reads it** (`run_all_scenarios`
    recomputes `unique(T.horizon_year)` itself at `:81`). Dead provenance channel.

---

### matlab/src/capacityGuard.m

- **Role:** Fail-closed capacity-provenance gate; normalizes `capacity_basis`, decides
  verified/not-verified, derives a numeric site capacity or NaN, and manufactures the mandatory
  placeholder banner text.
- **Kind:** authored
- **Reads:** one scenario row (one-row table or struct). No file I/O.
- **Written by / read by:** Called by `matlab/src/runScenario.m:67-69`. Its output struct is
  consumed by `managedCharging.m` (`Guard` option), `electricalEconomics.m` (`Guard` option),
  `plotScenario.m` (`out.guard`), `buildSimulinkModel.m` (`out.guard`). Tested by
  `matlab/tests/test_capacityGuard.m`.
- **Key contents:**
  - Signature: `function guard = capacityGuard(scenarioRow, varargin)` (`:1`).
  - **Controlled vocabulary** `allowedBases` (`:53-55`), 6 values in this exact order:
    `verified_utility`, `verified_facility`, `engineering_estimate`, `planning_proxy`,
    `placeholder`, `unknown`.
  - VERIFIED set = `["verified_utility","verified_facility"]` only (`:84`).
  - Options (`:57-63`): `Mode` (default `"feasibility"`, validator restricts to
    `["feasibility","planning_illustration"]`), `AssumedSiteCapacity_kW` (default `NaN`, numeric
    scalar).
  - **Fail-closed rule** `:89-96`: in `feasibility` mode, any non-verified basis raises
    `capacityGuard:notVerified`.
  - Capacity derivation order (`:106-129`), exactly 4 branches:
    1. `service_capacity_kW` finite → `capacity_kW = serviceCap`,
       def `"service_capacity_kW (service definition)"`.
    2. `spare_capacity_kW` and `base_load_mean_kW` both finite →
       `capacity_kW = base_load_mean_kW + spare_capacity_kW`,
       def `"base_load_mean_kW + spare_capacity_kW (legacy definition - NOT a service rating)"`.
    3. `AssumedSiteCapacity_kW` finite → that value; def
       `sprintf("assumed planning capacity %.1f kW (explicit user assumption; treated as placeholder)")`;
       `assumedUsed = true`; and **provenance is downgraded**: `:119-124` forces
       `isVerified = false; basis = "placeholder"`.
    4. else `capacity_kW = NaN`, def
       `"undefined - service_capacity_kW and spare_capacity_kW are both empty in the canonical CSV"`.
  - Banner (`:134-141`), emitted whenever not verified:
    `"CAPACITY IS A PLANNING PLACEHOLDER (capacity_basis=%s). Illustrates managed-charging behavior
    only; NOT evidence of electrical feasibility. Utility/facility confirmation pending."`
  - Output struct fields (`:143-153`), 10 in this order: `scenario_id`, `capacity_basis`,
    `is_verified`, `mode`, `capacity_kW`, `capacity_defined` (= `isfinite(capacity_kW)`),
    `capacity_definition`, `placeholder_banner`, `assumed_capacity_used`, `allowed_bases`.
  - Error ids: `capacityGuard:unknownBasis`, `:notVerified`, `:oneRowRequired`, `:badInput`,
    `:missingBasis` (5).
  - Locals: `localRowToStruct(scenarioRow)` (`:160`), `localNumericOrNaN(s, fieldName)` (`:184`).
- **Notes:**
  - Docstring `:12-13` asserts placeholder is "the current adapter CSV state for **ALL 12 sites**".
    This is a headline number in prose. Not verified in this lane (site count lives in the CSV /
    `data/contract/v1/`); flagged as a finding for cross-check.
  - Docstring's "Returned struct fields" list (`:33-42`) omits `scenario_id` and `allowed_bases`,
    which the code does return (`:144`, `:153`). Minor doc drift.
  - `localNumericOrNaN` accepts char/string and parses with `str2double` — so a text `"250"` in the
    CSV still yields a numeric capacity. Silent type coercion; worth knowing for a Python port.

---

### matlab/src/makeSessionProfiles.m

- **Role:** Builds the 24-hour base-building load curve and the session-derived aggregate EV
  *request* curve for one scenario, plus the per-session table the energy-aware scheduler needs.
- **Kind:** authored
- **Reads:** one scenario row (one-row table or struct). No file I/O.
- **Written by / read by:** Called by `matlab/src/runScenario.m:74-78`. Output consumed by
  `managedCharging.m` (all strategies), `plotScenario.m`, `buildSimulinkModel.m`. Tested by
  `matlab/tests/test_profiles.m`.
- **Key contents:**
  - Signature: `function profiles = makeSessionProfiles(scenarioRow, varargin)` (`:1`).
  - Options (`:65-79`), 6 `addParameter`s with these defaults and validators:
    | name | default | validator |
    |---|---|---|
    | `Mode` | `"deterministic_sessions"` | member of `["deterministic_sessions","stochastic","legacy_gaussian"]` |
    | `ArrivalDistribution` | `"uniform"` | member of `["uniform","triangular"]` |
    | `Seed` | `42` | numeric scalar `>= 0` |
    | `ChargerEfficiency` | `0.93` | numeric scalar in `(0,1]` |
    | `DiversityFactor` | `1.0` | numeric scalar in `(0,1]` |
    | `TimeStepMinutes` | `5` | numeric scalar `> 0` |
  - **Time axis** (`:87-89`): `dt_hr = TimeStepMinutes/60` (= 1/12 h at default);
    `t_hr = (0:dt_hr:24).'` → **289 points** at the default 5-minute step.
  - **Base-load shape constants** (`:95-101`) — these are the load-bearing magic numbers:
    - daytime: `exp(-0.5*((t-14)/4.5)^2)`
    - morning: `0.25 * exp(-0.5*((t-8)/1.7)^2)`
    - evening: `0.15 * exp(-0.5*((t-19)/2.0)^2)`
    - `shape = (sum) / max(sum)`; then
      `baseLoad_kW = base_load_mean_kW + (base_load_peak_kW - base_load_mean_kW) * shape`.
    Consequence: `min(baseLoad) == base_load_mean_kW` and `max(baseLoad) == base_load_peak_kW`,
    i.e. the "mean" column is used as the *floor*, not the mean. Documented at `:92-94` only as
    "mean -> peak scaling".
  - **legacy_gaussian mode** (`:112-120`): `center = (arrival_start+arrival_end)/2`,
    `width = max((arrival_end-arrival_start)/2, 0.5)`, normalized Gaussian scaled to
    `ports * charger_power_kW` at peak. No session table produced (stays the zero-row table), which
    is what makes `managedCharging`'s `energy_aware` refuse it.
  - **deterministic_sessions** (`:132-144`): `nSessions = max(1, ceil(sessions_per_day))`, forced to
    0 when `sessions_per_day <= 0`; `weights = sessions_per_day / nSessions` (fractional
    sessions conserved exactly); arrivals = midpoints of `nSessions` equal bins across the window
    (`localEvenArrivals`, `:266-270`).
  - **stochastic** (`:123-129`): `rng(Seed, "twister")`; `nSessions ~ Poisson(sessions_per_day)`
    via Knuth (`localPoissonDraw`, `:231-245`); weights all 1; arrivals from `localDrawArrivals`
    (`:247-264`) — uniform, or symmetric triangular with `c = 0.5` by inverse-CDF; sorted ascending.
  - **Session table schema** (`:154-161` and the empty-table twin `:293-303`), 9 columns in order:
    `session_id, arrival_hr, departure_hr, dwell_hr, energy_required_kWh,
    energy_required_grid_kWh, max_power_kW, weight, priority_class`.
    - `departure = min(arrival + dwell_hr, 24)` (`:149`) — clipped at midnight.
    - `dwell_hr` column is `departure - arrivals` (post-clip), not the raw input.
    - `energy_required_kWh` = battery side; `energy_required_grid_kWh = eBatt / eta` (`:151`).
    - `priority_class` is hard-set to `1` for every session (`:157` `ones(nSessions,1)`) — the
      priority tier in the scheduler is therefore inert in the current code.
  - **Request construction** (`:166-175`): per session,
    `chargeDuration = min(eGrid/pMax, departure-arrival)`; the pulse target energy is
    `eGrid * min(1, (departure-arrival)*pMax / max(eGrid, eps))` = `min(eGrid, dwell*pMax)`;
    rasterized by `localPulseProfile` and multiplied by `weights(k)`.
  - `localPulseProfile(t_hr, dt_hr, tOn, tOff, p_kW, eTarget_kWh)` (`:272-291`): per-step overlap
    fraction `overlap/dt_hr` times `p_kW`, then **rescaled** so `trapz(t_hr, prof) == eTarget_kWh`.
  - Diversity applied last, to the aggregate only (`:180`): `evRequest_kW = evRequest_kW * DiversityFactor`.
  - Output struct fields (`:185-196`), 10: `t_hr, dt_hr, baseLoad_kW, evRequest_kW, sessions,
    energyRequested_kWh (= trapz(t_hr, evRequest_kW)), mode, params (the inputParser Results echo),
    scenario (the row as struct), charger_efficiency, label`. (11 with `label`.)
    `label = sprintf("%s | %s | mode=%s", scenario_id, site_id, mode)`.
  - Error ids: `makeSessionProfiles:oneRowRequired`, `:badInput`, `:missingFields` (3).
  - `requiredFields` for the row (`:219-222`), 11: `scenario_id, site_id, ports, charger_power_kW,
    base_load_mean_kW, base_load_peak_kW, arrival_start_hr, arrival_end_hr, dwell_hr,
    sessions_per_day, energy_per_session_kWh`.
- **Notes:**
  - The energy-conservation rescale in `localPulseProfile` (`:287-289`) makes the discretized pulse
    integrate to exactly the intended energy, but as a side effect the **plateau power exceeds
    `p_kW`** by roughly `m/(m-1)` where `m` is the number of covered steps (trapz under-counts the
    two half-edges). At the 5-min step and a 6-hour charge that is ~1.4 %. Consequence:
    `peak_ev_kW` / `peak_unmanaged_kW` can exceed the physical `ports × charger_power_kW` ceiling.
    These are headline metrics, so it matters.
  - `DiversityFactor` scales the aggregate curve but **not** the `sessions` table. See the
    cross-file defect noted under `managedCharging.m`.
  - `ports` is a *required* field but is only used in `legacy_gaussian` mode (`:120`). In the
    session-based modes the number of concurrent chargers is never enforced — nothing caps
    simultaneous sessions at `ports`. This is a real modelling gap for a Python reimplementation.

---

### matlab/src/managedCharging.m

- **Role:** Applies one of three charging-control strategies to the profiles and does strict
  energy accounting with a hard balance invariant.
- **Kind:** authored
- **Reads:** the `profiles` struct from `makeSessionProfiles`. No file I/O.
- **Written by / read by:** Called three times per scenario from `matlab/src/runScenario.m:86`,
  `:90`, `:96`. Results consumed by `electricalEconomics.m`, `plotScenario.m`, and the metrics
  block of `runScenario.m`. Tested by `matlab/tests/test_managedCharging.m`.
- **Key contents:**
  - Signature: `function result = managedCharging(profiles, strategy, varargin)` (`:1`).
  - `validStrategies = ["unmanaged","clamp","energy_aware"]` (`:57`); unknown → error id
    `managedCharging:badStrategy` (`:60`).
  - Options (`:65-74`): `SiteCapacity_kW` (default `NaN`, numeric scalar), `Guard`
    (default `struct.empty`, `isstruct`), `CommsLoss` (default `false`, logical scalar),
    `FailSafeFraction` (default `0.5`, numeric in `(0,1]`).
  - Capacity resolution (`:84-88`): explicit `SiteCapacity_kW` wins; otherwise `Guard.capacity_kW`.
  - **unmanaged** (`:95-102`): `ev_kW = evRequest_kW`; `requested = delivered = trapz(t, request)`;
    `curtailed = unmet = deferred = 0`.
  - **clamp** (`:105-116`): `headroom = max(siteCap - baseLoad, 0)`;
    `ev = min(request, headroom)`; `curtailed = max(requested - delivered, 0)`; `unmet = 0`;
    `deferred = 0`. Note at `:114-116` labels it H4 legacy behaviour.
  - **energy_aware** (`:119-146`): refuses `legacy_gaussian` or zero sessions →
    `managedCharging:sessionsRequired`. Delegates to `localEnergyAwareSchedule`. Then
    `requested = sum(perVehicle.requested_kWh)`, `delivered = sum(perVehicle.delivered_kWh)`,
    `unmet = sum(perVehicle.unmet_kWh)`, `curtailed = 0`,
    `deferred = max(max(cumtrapz(request) - cumtrapz(ev), [], "omitnan"), 0)`.
  - **Energy-balance invariant** (`:154-163`):
    `requested = delivered + curtailed + unmet`, tolerance `1e-6 * max(1, abs(requested))`,
    violation → error id `managedCharging:energyBalance`. `deferred_kWh` is deliberately outside
    the balance (docstring `:28-30`).
  - Result struct fields (`:171-190`), 18 in order: `strategy, t_hr, ev_kW, total_kW,
    site_capacity_kW, requested_kWh, delivered_kWh, curtailed_kWh, unmet_kWh, deferred_kWh,
    balance_error_kWh, peak_total_kW, peak_ev_kW, max_overload_kW, overload_kW, per_vehicle,
    comms_loss, notes, guard` (19 counting `guard`).
  - `overload_kW = max(total - siteCap, 0)` when capacity finite, else `nan(nT,1)` (`:165-169`).
  - Error ids: `:badStrategy`, `:sessionsRequired`, `:energyBalance`, `:capacityUndefined` (4).
  - `localRequireCapacity(siteCap_kW, strategy)` (`:197-208`) — clamp and energy_aware refuse to
    run without a finite capacity.
  - **`localEnergyAwareSchedule(sessions, t_hr, dt_hr, baseLoad_kW, siteCap_kW, commsLoss,
    failSafeFraction)`** (`:210`) returns `[ev_kW, perVehicle, notes]`:
    - Per-session request basis (`:230-236`):
      `reqPerSession(k) = weight(k) * min(energy_required_grid_kWh(k),
      (departure_hr(k)-arrival_hr(k)) * max_power_kW(k))` — **identical basis to the pulse target
      in `makeSessionProfiles:172-174`**, which is why the two `requested_kWh` numbers agree.
    - Active set per step (`:251-253`):
      `arrival_hr <= tNow & departure_hr > tNow & remaining_kWh > 1e-12`.
    - Normal path (`:268-288`): `headroom = max(siteCap - baseLoad(i), 0)`; queue sorted by
      `sortrows([priority_class, departure_hr, arrival_hr])` — priority ascending (1 = highest),
      then earliest departure (EDF), then earliest arrival; grant
      `p = min([max_power_kW*weight, headroom, remaining/dt_hr])`; break when
      `headroom <= 1e-12`.
    - Comms-loss path (`:258-267`): static per-vehicle limit
      `failSafeFraction * max_power_kW * weight`, **no headroom enforcement at all** — site cap is
      deliberately not applied (note text at `:242-246`).
    - `perVehicle` = the sessions table plus 4 appended columns: `requested_kWh`, `delivered_kWh`,
      `unmet_kWh`, `fully_served` (`:294-299`). `fully_served` threshold:
      `unmet < max(1e-6, 1e-6*max(reqPerSession))`.
    - Shortfall note (`:301-306`): `"%d of %d session(s) depart with unmet energy
      (capacity-limited); see per_vehicle table."`
- **Notes:**
  - **Integration-basis mismatch.** `delivered_kWh` in `energy_aware` is a left-Riemann sum
    (`p_kW * dt_hr`, `:265`/`:286`), while `unmanaged`/`clamp` use `trapz` (`:97`,`:109-110`) and
    the plotted `ev_kW` curve is integrated with `cumtrapz` for `deferred_kWh` (`:144-146`). The
    area under the plotted energy-aware curve therefore does **not** equal the reported
    `delivered_kWh`. Self-consistent inside the balance check, inconsistent against the visual and
    against the other two strategies.
  - **`DiversityFactor` is silently bypassed by `energy_aware`.** `makeSessionProfiles:180` scales
    `evRequest_kW` only; the `sessions` table is unscaled. With `DiversityFactor < 1`,
    `energy_aware.requested_kWh` (session basis) exceeds `unmanaged.requested_kWh` (curve basis)
    by `1/DiversityFactor`, and `deferred_kWh` (`:144-146`) compares a scaled request against an
    unscaled dispatch, making it meaningless. Default is `1.0`, so the shipped batch is unaffected,
    but the option is exposed all the way up through `runScenario` (`:56-57`).
  - `priority_class` is always 1 (set in `makeSessionProfiles:157`), so the first sort key never
    discriminates — the scheduler is effectively pure EDF today.
  - Docstring's result-field list (`:50-53`) omits `site_capacity_kW`, `peak_ev_kW`,
    `max_overload_kW`, `comms_loss`. Doc drift.

---

### matlab/src/electricalEconomics.m

- **Role:** Compares an unmanaged and a managed result: apparent power, a service/transformer
  constraint verdict with provenance labelling, and demand-charge/energy cost — only if a tariff is
  actually supplied.
- **Kind:** authored
- **Reads:** two `managedCharging` result structs. No file I/O.
- **Written by / read by:** Called once per scenario from `matlab/src/runScenario.m:119-122`.
  Three of its fields (`service_check`, `cost_status`, `demand_charge_savings_usd_month`) reach
  the batch results table via `runScenario.m:157-160`.
- **Key contents:**
  - Signature: `function econ = electricalEconomics(resultUnmanaged, resultManaged, varargin)` (`:1`).
  - Options (`:52-62`), 5: `PowerFactor` (default **0.95**, numeric in `(0,1]`),
    `ChargerEfficiency` (default **0.93**, `(0,1]`, *reporting echo only* per `:17-18`),
    `ServiceCapacity_kW` (default `NaN`), `Guard` (default `struct.empty`),
    `Tariff` (default `struct.empty`).
  - `kVA = kW / powerFactor` (`:77-78`).
  - Service check (`:99-118`): three verdicts — `"service_capacity_unknown"` (capacity not finite),
    `"within_service"` (`peakMg <= cap`), `"exceeds_service"`. `service_check_note` is
    `"Checked against VERIFIED service capacity."` only when `Guard.is_verified`; otherwise
    `"Checked against NON-VERIFIED capacity (placeholder/proxy). Planning illustration only - no
    feasibility claim."`
  - Tariff gate (`:124-128`): requires the struct to be non-empty AND to have numeric
    `demand_charge_usd_per_kw_month` AND numeric `energy_usd_per_kwh`. If not,
    every cost field is `NaN` and `cost_status = "tariff_not_supplied"` (`:150-156`).
  - Cost formulas (`:137-145`): `demand_charge_usd_month_* = peak_kW * demand_charge_usd_per_kw_month`;
    `demand_charge_savings_usd_month = (peakUn - peakMg) * dc`;
    `energy_cost_usd_day_* = delivered_kWh * energy_usd_per_kwh`.
  - Output struct fields (in assignment order `:71-157`), 20:
    `strategy_unmanaged, strategy_managed, power_factor, charger_efficiency, peak_kW_unmanaged,
    peak_kW_managed, peak_kVA_unmanaged, peak_kVA_managed, peak_reduction_kW,
    service_capacity_kW, service_check, service_check_note, banner,
    demand_charge_usd_month_unmanaged, demand_charge_usd_month_managed,
    demand_charge_savings_usd_month, energy_cost_usd_day_unmanaged,
    energy_cost_usd_day_managed, cost_status, tariff`.
  - No `error()` calls at all — this is the one non-fail-closed module.
- **Notes:**
  - `PowerFactor` is **not exposed by `runScenario` or `run_all_scenarios`** — the batch always uses
    0.95, and neither `peak_kVA_*` nor `peak_reduction_kW` nor the absolute demand-charge figures
    reach `results.csv` (only `demand_charge_savings_usd_month` does, `runScenario.m:159-160`).
    The ML-11 apparent-power work is computed and then dropped on the floor at batch level.
  - Demand-charge simplification is stated at `:134-136`: "assumes the modeled day sets the billing
    peak - stated simplification, see README limitations". Any downstream $ claim inherits it.
  - `0.93` charger efficiency and `0.95` power factor are the only two economics constants; both
    are hard defaults, neither traces to `data/contract/v1/` from inside this file.

---

### matlab/src/runScenario.m

- **Role:** Single-scenario end-to-end orchestrator: guard → profiles → strategies → economics →
  flat metrics row.
- **Kind:** authored
- **Reads:** one scenario row. No file I/O.
- **Written by / read by:** Called per row by `matlab/src/run_all_scenarios.m:90-95`. Its `out`
  struct is the input to `plotScenario.m` and `buildSimulinkModel.m`.
- **Key contents:**
  - Signature: `function out = runScenario(scenarioRow, varargin)` (`:1`).
  - Options (`:44-61`), 8: `GuardMode` (default **`"planning_illustration"`** — note this is the
    *opposite* of `capacityGuard`'s own default of `"feasibility"`), `AssumedSiteCapacity_kW`
    (`NaN`), `ProfileMode` (`"deterministic_sessions"`), `Seed` (`42`), `ChargerEfficiency`
    (`0.93`), `DiversityFactor` (`1.0`), `Tariff` (`struct.empty`), `CommsLoss` (`false`).
  - Pipeline order, exactly (`:67-122`): `capacityGuard` → `makeSessionProfiles` →
    `managedCharging("unmanaged")` → if `guard.capacity_defined`: `managedCharging("clamp")` and
    (unless `ProfileMode == "legacy_gaussian"`) `managedCharging("energy_aware")` →
    `electricalEconomics`.
  - Skip reasons (exact strings): `"energy_aware: skipped_legacy_gaussian_mode"` (`:94`),
    `"clamp: skipped_no_capacity_defined"` (`:103`),
    `"energy_aware: skipped_no_capacity_defined"` (`:104`).
  - Managed-result selection for economics (`:111-117`): `energy_aware` if present, else `clamp`,
    else `unmanaged`-vs-itself (zero reduction).
  - **`metrics` struct — 21 fields, this is the `results.csv` schema** (`:128-165`):
    `scenario_id, site_id, horizon_year, case_label, profile_mode, capacity_basis,
    capacity_verified, capacity_kW, energy_requested_kWh, peak_base_kW, peak_unmanaged_kW,
    peak_clamp_kW, curtailed_clamp_kWh, peak_energy_aware_kW, unmet_energy_aware_kWh,
    deferred_energy_aware_kWh, service_check, cost_status, demand_charge_savings_usd_month,
    placeholder_banner, skipped_strategies`.
    `skipped_strategies` becomes the literal `"none"` when nothing was skipped (`:163-165`).
    `energy_requested_kWh` always comes from the **unmanaged** result (`:137`).
  - `out` fields (`:167-175`), 8: `scenario, guard, profiles, results, econ, metrics,
    skipped_strategies, options`.
  - Local: `localFieldOr(s, fieldName, defaultValue)` (`:178`).
  - No `error()` calls of its own — all errors bubble up from the callees.
- **Notes:**
  - The default `GuardMode` flip to `"planning_illustration"` means the *default* path never
    fail-closes. Fail-closed only happens if a caller explicitly asks for `"feasibility"`. This is
    documented at `:16-18` but is a genuine footgun worth calling out.
  - `out.options` stores the raw `inputParser` Results struct — carries `Tariff` verbatim, so a
    tariff with sensitive commercial terms would end up in any saved `out`.

---

### matlab/src/run_all_scenarios.m

- **Role:** Batch runner over every CSV row; writes `results.csv`, `manifest.txt`, `hashes.txt`
  into a timestamped run folder.
- **Kind:** authored
- **Reads:** `CsvFile` default `<matlab>/data/canonical/matlab_scenarios.csv` (`:45-47`);
  hashes both the input CSV and its own `results.csv` (`:144-147`).
- **Written by / read by:** Top-level entry point. Documented headless invocation (`:10`):
  `matlab -batch "addpath('src'); run_all_scenarios"`. Its outputs are what
  `matlab/tests/test_regression.m` would compare against (`tests/golden/regression_golden.csv`,
  which `EXECUTION_STATUS.md:12-13` says does not exist).
- **Key contents:**
  - Signature: `function outDir = run_all_scenarios(varargin)` (`:1`).
  - Options (`:43-59`), 7: `CsvFile`, `OutputRoot` (default `<matlab>/outputs`), `ProfileMode`
    (`"deterministic_sessions"`), `Seed` (`42`), `Tariff` (`struct.empty`),
    `AssumedSiteCapacity_kW` (`NaN`), `SavePlots` (`false`).
  - Path derivation (`:40-41`): `thisDir = fileparts(mfilename("fullpath"))`;
    `repoRoot = fileparts(thisDir)`. **`repoRoot` is `matlab/`, not the git repo root** — the
    variable name is misleading but the resolved paths (`matlab/data/canonical/…`,
    `matlab/outputs/`) are correct and both exist.
  - `run_id = "batch_" + <UTC yyyyMMdd'T'HHmmss'Z'>` (`:65-67`); output dir
    `<OutputRoot>/<run_id>`.
  - Per-row call **hard-codes** `"GuardMode", "planning_illustration"` (`:91`) — there is no way to
    run the batch in feasibility mode. Deliberate, and it is why every batch row carries the
    placeholder banner.
  - Failure handling (`:103-106`): a throwing scenario is caught and recorded, never dropped;
    `localErrorMetricsRow` produces the same 23-field set with `service_check = "run_failed"`,
    `cost_status = "run_failed"`, `skipped_strategies = "all"`, `run_status = "error"`,
    `run_error = ME.message`.
  - `orderfields` (`:110`) normalizes field order so success and error rows concatenate; final
    table via `struct2table([metricRows{:}].')` (`:115`).
  - `results.csv` columns = the 21 `metrics` fields **plus** `run_status`, `run_error`, `run_id`
    = **24 columns**, alphabetized by `orderfields`.
  - `manifest.txt` keys, in order (`:126-138`): `run_id`, `generated_utc`, `matlab_release`
    (`version("-release")`), `input_csv`, `scenario_rows`, `profile_mode`, `seed`,
    `tariff_supplied`, `assumed_site_capacity_kW`, then a 3-line `note:` block ending
    `"of this run is a feasibility claim."`
  - `hashes.txt`: two lines, `<sha256>  <path>` for the input CSV then `results.csv`.
  - `localSha256(filePath)` (`:186-198`): `java.security.MessageDigest.getInstance("SHA-256")`,
    `typecast(md.digest(),"uint8")`, `lower(string(reshape(dec2hex(digest,2).',1,[])))`.
  - Console format string (`:111`): `"  [%3d/%3d] %-32s %s\n"`.
- **Notes:**
  - The SHA-256 path depends on the **Java bridge**. `matlab -nojvm` would break it, and Octave
    has no `java.*` by default. This is a named Tier-2 blocker.
  - `matlab/outputs/` contains only `.gitkeep` — no batch has ever produced output, consistent with
    `EXECUTION_STATUS.md:14-16`.
  - The manifest records `assumed_site_capacity_kW` but not `ChargerEfficiency`,
    `DiversityFactor`, `PowerFactor`, or `CommsLoss` — the run record is not sufficient to
    reproduce a run that varied those (they are not even exposed here).

---

### matlab/src/plotScenario.m

- **Role:** Renders the presentation figure for one `runScenario` output, with a mandatory
  placeholder banner and a mandatory source/date footer.
- **Kind:** authored
- **Reads:** the `out` struct. Writes a PNG only when `SaveFigure=true`.
- **Written by / read by:** Called from `matlab/src/run_all_scenarios.m:100-101` when `SavePlots`
  is true. Not called by `runScenario`.
- **Key contents:**
  - Signature: `function figHandle = plotScenario(out, varargin)` (`:1`).
  - Options (`:31-37`), 3: `OutputFolder` (default `""`), `SaveFigure` (`false`), `Visible` (`true`).
  - **Palette RGB triples** (`:46-51`): `cBase = [0.12 0.32 0.65]`, `cUnmanaged = [0.82 0.20 0.16]`,
    `cClamp = [0.90 0.43 0.14]`, `cEnergyAware = [0.13 0.55 0.36]`, `cCapacity = [0.32 0.22 0.55]`,
    `cEV = [0.95 0.58 0.16]`.
  - Figure: name `"Site-Level EV Charging Analysis (V3)"`, white, `Position [80 60 1450 860]` (`:58-60`).
  - Layout: `tiledlayout(figHandle, 2, 2, "TileSpacing","compact","Padding","compact")` (`:62-63`);
    tile 1 spans `[1 2]` (`:76`).
  - Titles: `"EV Charging Site-Load Behavior (Session-Based V3 Model)"` FontSize 18 (`:65-66`);
    subtitle template `"%s | %s | horizon %d | case %s | %d ports x %.1f kW | profile mode: %s"`
    (`:67-71`).
  - Tile titles: `"24-Hour Site Load Profile"`, `"EV Request vs Managed Output"`,
    `"Scenario Summary Metrics"`.
  - **Capacity-line rule** (`:94-101`): the legend entry is always
    `sprintf("Capacity limit [basis: %s]", guard.capacity_basis)` — provenance is baked into the
    label, cannot be suppressed.
  - **Mandatory banner** (`:164-173`): rendered whenever `strlength(guard.placeholder_banner) > 0`;
    `annotation("textbox", [0.05 0.955 0.90 0.040])`, text uppercased,
    background `[1.00 0.92 0.80]`, edge `[0.80 0.45 0.10]`, FontSize 10 bold, centered.
    There is **no option to disable it** (docstring `:16-18`).
  - **Mandatory footer** (`:178-187`): `"Source: data/canonical/matlab_scenarios.csv
    (auto-generated adapter) | scenario %s | capacity basis: %s | generated %s | Milestone 2 V3
    MATLAB model"`, `annotation("textbox", [0.02 0.001 0.96 0.028])`, FontSize 8,
    colour `[0.35 0.35 0.35]`.
  - Summary-bar labels (`:139-152`): `"Peak unmanaged (kW)"`, `"Peak clamp (kW)"`,
    `"Curtailed, clamp (kWh)"`, `"Peak energy-aware (kW)"`, `"Unmet, energy-aware (kWh)"`.
  - Save name (`:203-206`): `sprintf("scenario_%s_%s_%d_%s.png", safe(scenario_id), safe(site_id),
    horizon_year, <UTC yyyyMMdd'T'HHmmss'Z'>)`; `exportgraphics(..., "Resolution", 200)` (`:207`).
  - Error id: `plotScenario:noOutputFolder` (`:195`).
  - Locals: `localFieldOr` (`:216`), `localSafeName` (`:224`, regex `'[^a-zA-Z0-9]+' → '_'`).
- **Notes:**
  - The footer hard-codes the source path string `data/canonical/matlab_scenarios.csv` (`:180`)
    rather than echoing the actual `CsvFile` that was used. If a batch is run with a different
    `CsvFile`, **every figure will state a source it did not use.** That is a provenance defect in
    a file whose entire stated purpose is provenance labelling.
  - The bar chart mixes kW and kWh on one axis (`ylabel "kW / kWh"`, `:157`) — dimensionally
    incoherent by design; if these figures are reused in the platform, this should not be copied.
  - Uses `tiledlayout`/`nexttile`/`subtitle`/`exportgraphics`/`reordercats` — the most
    MATLAB-locked file in the lane.

---

### matlab/src/buildSimulinkModel.m

- **Role:** Optional, explicitly illustrative Simulink visualization layer; builds the `.slx` once
  and never rebuilds, and externalizes scenario parameters to a data dictionary and a `.mat`.
- **Kind:** authored (its *product*, the `.slx`, would be generated — and does not exist)
- **Reads:** the `out` struct from `runScenario`. Writes
  `<ModelFolder>/<ModelName>_params.mat` (always), `<ModelFolder>/<ModelName>_params.sldd`
  (best-effort), `<ModelFolder>/<ModelName>.slx` (once). Assigns 3 timeseries into the **base
  workspace**.
- **Written by / read by:** Not called by any other file in `matlab/src/`. Entry point is manual.
- **Key contents:**
  - Signature: `function modelPath = buildSimulinkModel(out, varargin)` (`:1`).
  - `MODEL_VERSION = "3.0.0"` (`:38`).
  - Options (`:40-50`), 2: `ModelName` (default `"site_grid_behavior_ev_charging_v3"`),
    `ModelFolder` (default `fullfile(repoRoot,"simulink")` where `repoRoot = matlab/`, i.e.
    `matlab/simulink` — **this directory does not exist in the repo**, consistent with the model
    never having been built).
  - Availability guard (`:55-61`): `exist("new_system","file") ~= 2 || ~license("test","Simulink")`
    → error id `buildSimulinkModel:simulinkUnavailable`.
  - `params` struct written to `.mat`/`.sldd` (`:75-90`), 11 fields: `model_version, scenario_id,
    site_id, horizon_year, capacity_basis, capacity_kW, charger_power_kW, ports, profile_mode,
    dt_sec (= dt_hr*3600 = 300 at default), stop_time_sec (= 24*3600 = 86400), built_utc, note`
    (13 counting `built_utc` and `note`).
    `params.note = "Illustrative Simulink layer; metrics are computed by the base-MATLAB pipeline,
    not by this model."`
  - Data-dictionary path is best-effort inside `try/catch`; failure only warns
    (`buildSimulinkModel:dictionarySkipped`, `:113`).
  - Base-workspace variables (`:122-131`): `baseLoad_ts`, `evRequest_ts`, `capacity_ts` —
    `timeseries` objects on `t_sec = t_hr*3600`. When `~guard.capacity_defined`, `capacity_ts`
    is **NaN-filled on purpose** (`:126-130`) so the scope shows the absence rather than implying a
    limit.
  - **Build-once policy** (`:136-141`): if the `.slx` exists, print and `return` — never delete,
    never rebuild. Docstring `:6-8` says this "reverses the legacy delete/rebuild behavior,
    hypothesis H8, which destroyed traceability on every run."
  - Model params: `StopTime = "86400"`, `Solver = "ode3"`, `FixedStep = "300"` (`:147-149`).
  - Full block/line topology: see **SIMULINK TOPOLOGY** below.
- **Notes:**
  - `exist("new_system","file") ~= 2` is a fragile availability test — `exist(...,"file")` does not
    reliably return 2 for built-ins/P-code, so this can produce a false "Simulink unavailable"
    error on a properly licensed machine. **Uncertain** (untestable without MATLAB), but it is the
    single gate on the whole file and should be checked on the first licensed run.
  - `assignin("base", ...)` writes three variables into the user's base workspace as a side effect.

---

## SIMULINK TOPOLOGY

Extracted verbatim from `matlab/src/buildSimulinkModel.m`. This is the complete, exact set — there
are **11 blocks, 15 lines, and 0 annotation objects**.

### Verbatim scope statement (illustrative, not load-bearing)

`matlab/src/buildSimulinkModel.m`, lines **10-16**:

```
%   IMPORTANT SCOPE STATEMENT: this layer is ILLUSTRATIVE, not
%   load-bearing. Every metric in this repository (profiles, strategies,
%   energy balance, economics, batch results) is computed by the plain
%   MATLAB pipeline (makeSessionProfiles / managedCharging /
%   electricalEconomics), which runs in base MATLAB without Simulink.
%   The Simulink model exists only to visualize signal flow for
%   presentations and stakeholder walkthroughs.
```

Two corroborating statements in the same file:
- `:58-60` (error text): `"This layer is OPTIONAL and illustrative only - all metrics come from the
  base-MATLAB pipeline (runScenario / run_all_scenarios), which you can use without Simulink."`
- `:89-90` (`params.note`): `"Illustrative Simulink layer; metrics are computed by the
  base-MATLAB pipeline, not by this model."`
- `:155-156` (model Description): `"All quantitative results come from the MATLAB pipeline
  (runScenario), not from this model."`

And in `matlab/src/runScenario.m:10-12`: `"Everything runs in base MATLAB; Simulink is NOT required
(the optional Simulink layer in buildSimulinkModel.m is illustrative and not load-bearing)."`

### Model-level parameters (`set_param` on the model)

| param | value | source line |
|---|---|---|
| `StopTime` | `"86400"` (`num2str(24*3600)`) | `:147` (value from `:86`) |
| `Solver` | `"ode3"` | `:148` |
| `FixedStep` | `"300"` (`num2str(dt_hr*3600)`, 5-min default) | `:149` (value from `:85`) |
| `Description` | `sprintf("Site-level EV charging behavior - ILLUSTRATIVE LAYER.\nVersion %s \| built %s \| scenario %s \| capacity_basis %s.\nAll quantitative results come from the MATLAB pipeline (runScenario), not from this model.", MODEL_VERSION, params.built_utc, params.scenario_id, params.capacity_basis)` | `:152-158` |

Default model name: `site_grid_behavior_ev_charging_v3` (`:42`). Model version: `3.0.0` (`:38`).

### Blocks (in creation order)

| # | Block name (path suffix) | Library path | Position `[x1 y1 x2 y2]` | Parameters set | Source lines |
|---|---|---|---|---|---|
| 1 | `Base Load` | `simulink/Sources/From Workspace` | `[40 70 160 100]` | `VariableName = "baseLoad_ts"` | `:161-163` |
| 2 | `EV Request` | `simulink/Sources/From Workspace` | `[40 160 160 190]` | `VariableName = "evRequest_ts"` | `:164-166` |
| 3 | `Capacity Limit` | `simulink/Sources/From Workspace` | `[40 250 160 280]` | `VariableName = "capacity_ts"` | `:167-169` |
| 4 | `Total Unmanaged` | `simulink/Math Operations/Sum` | `[240 115 285 160]` | `Inputs = "++"` | `:171-173` |
| 5 | `Managed Logic Inputs` | `simulink/Signal Routing/Mux` | `[240 215 250 295]` | `Inputs = "3"` | `:175-177` |
| 6 | `Managed EV Power` | `simulink/User-Defined Functions/MATLAB Function` | `[320 230 455 280]` | (no add_block params; `Script` set afterwards, see below) | `:179-191` |
| 7 | `Total Managed` | `simulink/Math Operations/Sum` | `[530 160 575 205]` | `Inputs = "++"` | `:193-195` |
| 8 | `Main Scope Signals` | `simulink/Signal Routing/Mux` | `[665 85 675 250]` | `Inputs = "4"` | `:197-199` |
| 9 | `Live Scope: Load Behavior` | `simulink/Sinks/Scope` | `[760 115 900 210]` | (none) | `:201-203` |
| 10 | `toWorkspace_unmanaged` | `simulink/Sinks/To Workspace` | `[665 300 815 330]` | `VariableName = "sim_total_unmanaged"`, `SaveFormat = "Structure With Time"` | `:205-209` |
| 11 | `toWorkspace_managed` | `simulink/Sinks/To Workspace` | `[665 350 815 380]` | `VariableName = "sim_total_managed"`, `SaveFormat = "Structure With Time"` | `:210-214` |

Block 6's embedded MATLAB Function code, set via
`rt = sfroot; chart = rt.find("-isa","Stateflow.EMChart","Path",[modelName '/Managed EV Power']);`
(`:182-184`) then `chart.Script = ...` (`:185-191`). Verbatim script body (`%%` in the source
is an escaped `%` for `sprintf`, so the rendered comments start with a single `%`):

```matlab
function y = fcn(u)
% u(1) = EV request, u(2) = capacity, u(3) = base load
% Illustrative clamp only - see managedCharging.m for the
% authoritative strategies incl. the energy-aware scheduler.
available = max(u(2) - u(3), 0);
y = min(u(1), available);
end
```

### Lines / connections (in creation order)

| # | Source block / port | Destination block / port | Source line |
|---|---|---|---|
| 1 | `Base Load` / 1 | `Total Unmanaged` / 1 | `:217` |
| 2 | `EV Request` / 1 | `Total Unmanaged` / 2 | `:218` |
| 3 | `EV Request` / 1 | `Managed Logic Inputs` / 1 | `:219` |
| 4 | `Capacity Limit` / 1 | `Managed Logic Inputs` / 2 | `:220` |
| 5 | `Base Load` / 1 | `Managed Logic Inputs` / 3 | `:221` |
| 6 | `Managed Logic Inputs` / 1 | `Managed EV Power` / 1 | `:222` |
| 7 | `Base Load` / 1 | `Total Managed` / 1 | `:223` |
| 8 | `Managed EV Power` / 1 | `Total Managed` / 2 | `:224` |
| 9 | `Base Load` / 1 | `Main Scope Signals` / 1 | `:225` |
| 10 | `Total Unmanaged` / 1 | `Main Scope Signals` / 2 | `:226` |
| 11 | `Total Managed` / 1 | `Main Scope Signals` / 3 | `:227` |
| 12 | `Capacity Limit` / 1 | `Main Scope Signals` / 4 | `:228` |
| 13 | `Main Scope Signals` / 1 | `Live Scope: Load Behavior` / 1 | `:229-230` |
| 14 | `Total Unmanaged` / 1 | `toWorkspace_unmanaged` / 1 | `:231` |
| 15 | `Total Managed` / 1 | `toWorkspace_managed` / 1 | `:232` |

Fan-out summary (useful for layout): `Base Load` drives 4 destinations (lines 1, 5, 7, 9);
`EV Request` drives 2 (lines 2, 3); `Capacity Limit` drives 2 (lines 4, 12);
`Total Unmanaged` drives 2 (lines 10, 14); `Total Managed` drives 2 (lines 11, 15);
`Managed Logic Inputs` drives 1; `Managed EV Power` drives 1; `Main Scope Signals` drives 1.

Mux input ordering is semantically load-bearing:
- `Managed Logic Inputs` (3-wide) = `[EV request, capacity, base load]`, matching the
  `u(1)/u(2)/u(3)` comment in the chart script.
- `Main Scope Signals` (4-wide) = `[base load, total unmanaged, total managed, capacity]`.

### Annotations

**None.** There is no `add_block(".../Note")`, no `Simulink.Annotation`, and no
`set_param(..., "Annotation", ...)` anywhere in the file. The only free text attached to the model
is the model-level `Description` (`:152-158`) listed above. Any renderer that wants an on-canvas
caption must synthesize it from the `Description` string or from the scope statement at `:10-16`.

### Model workspace inputs the diagram needs

| base-workspace variable | contents | source line |
|---|---|---|
| `baseLoad_ts` | `timeseries(prof.baseLoad_kW, t_hr*3600)` | `:122` |
| `evRequest_ts` | `timeseries(prof.evRequest_kW, t_hr*3600)` | `:123` |
| `capacity_ts` | `timeseries(capVec, t_hr*3600)`, where `capVec` is a constant `guard.capacity_kW` when defined, else all-NaN | `:124-131` |

---

## OCTAVE COMPATIBILITY INVENTORY

Counted mechanically across all 9 files. Counts are **occurrences**, not lines, unless stated.

### 1. `arguments` validation blocks (R2019b+, unsupported by Octave)

**0 occurrences in all 9 files.** `grep -n '^\s*arguments\b' *.m` returns nothing. Every function
uses `inputParser` instead. This is the single biggest piece of good news for portability.

### 2. `inputParser`

| file | `p = inputParser` | `addParameter` calls |
|---|---|---|
| `capacityGuard.m` | 1 (`:57`) | 2 |
| `loadScenarios.m` | 1 (`:37`) | 4 |
| `electricalEconomics.m` | 1 (`:52`) | 5 |
| `buildSimulinkModel.m` | 1 (`:40`) | 2 |
| `managedCharging.m` | 1 (`:65`) | 4 |
| `run_all_scenarios.m` | 1 (`:43`) | 7 |
| `plotScenario.m` | 1 (`:31`) | 3 |
| `makeSessionProfiles.m` | 1 (`:65`) | 6 |
| `runScenario.m` | 1 (`:44`) | 8 |
| **total** | **9** | **41** |

Octave **does** ship `inputParser` in core (Octave ≥ 4.0), including `addParameter`,
`FunctionName`, and `Results`. **Not a blocker** — but every validator is an anonymous function
that itself uses `string()`/`ismember` on string arrays (see §4), so the validators break for the
reasons below, not because of `inputParser`.

### 3. The `table` type — Octave has **no** table type at all

| construct | occurrences | file:line |
|---|---|---|
| `table(` constructor | 3 | `makeSessionProfiles.m:154`, `:295`; `managedCharging.m:91` |
| `'VariableNames'` name-value in `table()` | 2 | `makeSessionProfiles.m:158`, `:299` |
| `istable` | 2 | `capacityGuard.m:161`; `makeSessionProfiles.m:205` |
| `height(` | 10 | `capacityGuard.m:162,165`; `loadScenarios.m:135,152`; `makeSessionProfiles.m:206,209`; `managedCharging.m:122,127,224`; `run_all_scenarios.m:77` |
| `table2struct` | 2 | `capacityGuard.m:167`; `makeSessionProfiles.m:211` |
| `struct2table` | 1 | `run_all_scenarios.m:115` |
| `readtable` | 1 | `loadScenarios.m:71` |
| `writetable` | 1 | `run_all_scenarios.m:121` |
| `detectImportOptions` | 1 | `loadScenarios.m:59` |
| `setvartype` | 1 | `loadScenarios.m:68` |
| `opts.VariableNames` | 1 | `loadScenarios.m:66` |
| `renamevars` | 1 | `loadScenarios.m:75` |
| `T.Properties.VariableNames` | 2 | `loadScenarios.m:74`, `:89` |
| `T.Properties.Description` | 1 | `loadScenarios.m:160` |
| `T.Properties.UserData` | 1 | `loadScenarios.m:161` |
| table row-subscript `T(idx, :)` | 2 | `loadScenarios.m:150`; `run_all_scenarios.m:88` |
| `T.Var` dot-access on a table | **~45** across `loadScenarios.m` (`:99,107,122,122,128,129,129,138,141,144,147,165,166,171,181`), `managedCharging.m` (`:122,127,131,137,138,139,232,233,233,234,235,251,251,261,261,272,273,274,281,281,295,296,297,298,301`), `run_all_scenarios.m` (`:112,161,162,163,164,166`) | |
| new-column-by-assignment on a table | 4 | `managedCharging.m:295,296,297,298` |
| `rowfun` / `varfun` | **0** | — |
| `sortrows` | 1 (`managedCharging.m:272`) — applied to a **numeric matrix**, not a table; Octave supports this form | |

`table` appears in **6 of 9 files** (`loadScenarios`, `capacityGuard`, `makeSessionProfiles`,
`managedCharging`, `run_all_scenarios`; `plotScenario`/`runScenario` touch tables only indirectly
via `profiles.sessions` / `out`). `buildSimulinkModel` and `electricalEconomics` are table-free.

### 4. String arrays and double-quoted literals

Octave *does* accept double-quoted literals, but they are **char arrays with C escape processing**,
not `string` objects. This is the most dangerous category because most of it fails **silently with
a wrong answer**, not with an error.

| construct | count | notes |
|---|---|---|
| `"` characters, all files | 1422 total (1364 outside pure-comment lines) → **~711 literals (~682 in code)** | per-file: buildSimulinkModel 264/262, capacityGuard 134/128, electricalEconomics 62/48, loadScenarios 188/174, makeSessionProfiles 122/110, managedCharging 86/86, plotScenario 314/314, run_all_scenarios 152/148, runScenario 100/94 |
| `string(` conversions | **74** | buildSimulinkModel 6, capacityGuard 9, electricalEconomics 1, loadScenarios 19, makeSessionProfiles 5, managedCharging 1, plotScenario 10, run_all_scenarios 16, runScenario 7 |
| `strings(0,1)` (empty string array) | 3 | `runScenario.m:84`; `managedCharging.m:90`, `:226` |
| `string.empty` | 3 | `loadScenarios.m:39,41,42` |
| `struct.empty` | 6 | `electricalEconomics.m:60,61,156`; `managedCharging.m:69`; `runScenario.m:58`; `run_all_scenarios.m:54` |
| `isstring` | 9 | `capacityGuard.m:191`; `buildSimulinkModel.m:43,47`; `plotScenario.m:33`; `loadScenarios.m:39,41,42`; `run_all_scenarios.m:47,49` |
| **`+` string concatenation** | **57** | capacityGuard 13, electricalEconomics 4, buildSimulinkModel 10, loadScenarios 10, managedCharging 16, plotScenario 3, run_all_scenarios 1 (`makeSessionProfiles` 0, `runScenario` 0). In Octave `"a" + "b"` is **elementwise numeric addition of char codes** — silent garbage, or a size-mismatch error when the operand lengths differ. Every one of these 57 sites is inside an `error()`/`sprintf()`/`fprintf()`/assignment. |
| **`["a","b", ...]` string-array literals** | **14** | `capacityGuard.m:53,60,84`; `loadScenarios.m:62,81`; `makeSessionProfiles.m:68,71,158,219,299`; `managedCharging.m:57`; `run_all_scenarios.m:51`; `runScenario.m:47,51`. In Octave these become a **single concatenated char row** — e.g. `allowedBases` at `capacityGuard.m:53` becomes one 100-ish-char string, so `ismember(basis, allowedBases)` at `:76` compares characters and the entire controlled-vocabulary gate collapses. **Silent wrong answer, in the fail-closed safety gate.** |
| **`== "literal"` string equality** | **9** | `loadScenarios.m:100`; `capacityGuard.m:73,89`; `makeSessionProfiles.m:112,123`; `plotScenario.m:194`; `managedCharging.m:121`; `runScenario.m:93,163`. With char arrays these are elementwise comparisons: `basis == ""` yields `[]` (falsy) and `mode == "feasibility"` errors on length mismatch. |
| `ismember(...)` with string args | 14 lines | `makeSessionProfiles.m:68,71`; `capacityGuard.m:60,76,84`; `runScenario.m:47,51`; `loadScenarios.m:74,138,141,144,147`; `managedCharging.m:59`; `run_all_scenarios.m:51` |
| `setdiff` / `intersect` on strings | 3 | `loadScenarios.m:66,89`; `makeSessionProfiles.m:223` |
| `strjoin` on **string arrays** (Octave's `strjoin` requires cellstr) | 6 | `capacityGuard.m:81`; `managedCharging.m:62`; `makeSessionProfiles.m:227`; `loadScenarios.m:95`; `runScenario.m:162`; `run_all_scenarios.m:81` |
| `strlength` (no Octave equivalent) | 1 | `plotScenario.m:164` |
| `ismissing` (no Octave equivalent) | 2 | `capacityGuard.m:73`; `loadScenarios.m:100` |
| `end+1` growth on a string array | 15 | `managedCharging.m:102,114,242,303`; `runScenario.m:94,103,104`; `plotScenario.m:142,144,148,150` (labels) and `:143,145,149,151` (values, numeric) |
| **`\n` inside double quotes** | **26 lines** | `buildSimulinkModel.m:139,143,153,154,237`; `plotScenario.m:208`; `loadScenarios.m:51`; `run_all_scenarios.m:78,80,111,126,127,128,129,130,131,132,133,134,136,137,138,144,146,150,151`. In MATLAB `"...\n"` is a literal backslash-n that `fprintf` later interprets; in Octave the parser converts it to a real newline immediately. For `fprintf` the visible result usually matches, but for the **`set_param(..., "Description", ...)`** string at `buildSimulinkModel.m:153-154` and any string stored rather than printed, the stored value differs. |
| single-quoted char literals in code | present and intentional in `buildSimulinkModel.m` (block-path building `[modelName '/Base Load']` etc., `:162-214`), `makeSessionProfiles.m:158,299` (`'VariableNames'`), `plotScenario.m:227` (regex) | these are the *portable* ones |

### 5. `containers.Map`

**0 occurrences.**

### 6. Everything else Octave lacks or differs on

| construct | count | file:line | Octave status |
|---|---|---|---|
| `datetime(` | 5 | `buildSimulinkModel.m:87`; `loadScenarios.m:163`; `plotScenario.m:178,201`; `run_all_scenarios.m:65` | **No `datetime` class.** All 5 use `"TimeZone","UTC"` + a `"Format"` string. Shimmable with `strftime`/`datestr`, but the `'T'`/`'Z'` literal-quoting syntax is MATLAB-specific. |
| `categorical` / `reordercats` | 2 | `plotScenario.m:154,155` | **No categorical type.** |
| `cellstr` | 1 | `plotScenario.m:155` | available |
| `timetable` | 0 | — | — |
| `validateattributes` | 0 | — | — |
| `mustBe*` validators | 0 | — | — |
| `classdef` | 0 | — | — |
| `+namespace` dirs | 0 | flat `src/` | — |
| `arrayfun` / `cellfun` / `UniformOutput` | 0 | — | — |
| `~` output suppression `[~, x] = ...` | 1 | `managedCharging.m:272` | supported |
| `.'` transpose | 9 | `makeSessionProfiles.m:88,155,268`; `managedCharging.m:260,277`; `loadScenarios.m:165,166`; `run_all_scenarios.m:115,197` | supported |
| `...` line continuation | pervasive (every file) | — | supported |
| struct dynamic field `s.(name)` | 4 | `capacityGuard.m:188`; `loadScenarios.m:171`; `plotScenario.m:218`; `runScenario.m:181` | supported |
| local functions in a function file | 12 locals across 7 files | `capacityGuard` 2, `loadScenarios` 1, `makeSessionProfiles` 5, `managedCharging` 2, `plotScenario` 2, `runScenario` 1, `run_all_scenarios` 2 | supported (all files are function files, not scripts) |
| `trapz` / `cumtrapz` | 5 / 2 | `makeSessionProfiles.m:190,287`; `managedCharging.m:97,109,110,144,145` | both available |
| `max(A,[],"omitnan")` nanflag | 1 | `managedCharging.m:146` | Octave's `max` does **not** accept a nanflag string; needs rewrite |
| `rng(seed,"twister")` | 1 | `makeSessionProfiles.m:124` | `rng` only in very recent Octave; older needs `rand("twister", seed)` |
| `orderfields` | 1 | `run_all_scenarios.m:110` | available |
| `isfile` | 3 | `loadScenarios.m:49`; `buildSimulinkModel.m:98,136` | available (Octave ≥ 5) |
| `version("-release")` | 1 | `run_all_scenarios.m:128` | Octave's `version` takes no `-release` flag |
| **`java.security.MessageDigest`** | 1 | `run_all_scenarios.m:194` | **No Java bridge in stock Octave.** Hard blocker for `hashes.txt`. |
| `typecast`, `dec2hex`, `reshape` | 3 | `run_all_scenarios.m:196-197` | available |
| `mfilename("fullpath")` | 2 | `buildSimulinkModel.m:44`; `run_all_scenarios.m:40` | available |
| `assignin("base", ...)` | 3 | `buildSimulinkModel.m:122,123,131` | available |
| `timeseries(` | 3 | `buildSimulinkModel.m:122,123,131` | **No `timeseries` class.** |
| `license("test","Simulink")`, `new_system`, `set_param`, `add_block`, `add_line`, `save_system`, `close_system`, `sfroot`, `Simulink.data.dictionary.*` | 24 call sites across `buildSimulinkModel.m:55-235` | — | **No Simulink. No equivalent. Not shimmable.** |
| `tiledlayout` / `nexttile` / `subtitle` / `exportgraphics` / `xtickangle` / `annotation` / `xticks` | 12 | `plotScenario.m:62,67,76,113,106,130,136,159,165,184,207` | Octave has **none** of `tiledlayout`, `nexttile`, `subtitle`, `exportgraphics`; `annotation` is absent/incomplete; `xticks`/`xtickangle` only in recent versions |
| `struct("field", <string array>)` | 1 | `capacityGuard.m:143-153` (`"allowed_bases", allowedBases`) | In MATLAB this stores a 1×6 string in a 1×1 struct. Under a cellstr-based Octave shim, `struct()` would **replicate into a 1×6 struct array** and the guard would silently return the wrong shape. Named shim hazard. |
| implicit expansion | used at `makeSessionProfiles.m:100-101` (scalar + vector) and `managedCharging.m:107,149,166` | — | Octave supports broadcasting; no issue |

### REASONED VERDICT

**Tier 1 (run the unmodified `.m` files under Octave): NOT reachable.** Evidence, in order of
severity:

1. **`readtable` / `writetable` / `detectImportOptions` / `setvartype` / `renamevars` /
   `T.Properties.*` do not exist in Octave.** `loadScenarios.m` is the sole ingestion path and it
   is built entirely on the table type (`:59-75`, `:160-166`). Nothing downstream can start.
2. **`java.security.MessageDigest`** at `run_all_scenarios.m:194` — no Java bridge in stock
   Octave, so `hashes.txt`, an explicitly named deliverable (`run_all_scenarios.m:19-21`), cannot
   be produced.
3. **14 `["a","b"]` string-array literals** silently degrade to single concatenated char rows.
   `capacityGuard.m:53` (`allowedBases`) and `managedCharging.m:57` (`validStrategies`) are the two
   worst: the capacity-provenance vocabulary check at `capacityGuard.m:76` and the strategy check
   at `managedCharging.m:59` would both compare against a mangled value. These are the
   safety-critical fail-closed gates of the whole repo, and they would fail **silently**, not
   loudly.
4. **57 `+` string concatenations** become numeric char-code addition or a size-mismatch error.
5. **9 `== "literal"` comparisons** change semantics (`basis == ""` → `[]` → falsy; length-mismatch
   errors elsewhere).
6. `datetime` (5), `categorical`/`reordercats` (2), `timeseries` (3), `strlength` (1),
   `ismissing` (2), `max(...,"omitnan")` (1), `version("-release")` (1) — none exist.
7. `plotScenario.m` and `buildSimulinkModel.m` are wholesale unrunnable (tiledlayout family;
   Simulink API).

**Tier 2 (Octave + a thin shim): reachable for the numeric core only, and "thin" is the wrong
word.** What *is* genuinely portable is meaningful and should be stated: `arguments` blocks are
**zero**, `containers.Map` is **zero**, `classdef` is **zero**, `validateattributes`/`mustBe*` are
**zero**, `arrayfun`-with-`UniformOutput` is **zero**, `+namespaces` are **zero**, and
`inputParser` (9 instances, 41 parameters) is supported natively by Octave. The numerics —
`trapz`, `cumtrapz`, `linspace`, `sortrows` on a numeric matrix, broadcasting, `.'`, `[~,x]=`,
dynamic fields, local functions — all work. The algorithmic content of `makeSessionProfiles`,
`managedCharging`, `capacityGuard`, and `electricalEconomics` is plain array math.

But a shim would have to supply, at minimum: (a) a `string` class or a global rewrite of ~711
double-quoted literals plus 57 `+` concatenations, 14 array literals and 9 `==` comparisons —
which is a *source rewrite*, not a shim; (b) a `table` replacement covering constructor,
`height`, `istable`, `table2struct`, `struct2table`, `readtable`, `writetable`,
`detectImportOptions`, `setvartype`, `renamevars`, `Properties.{VariableNames,Description,UserData}`,
row-subscripting and ~45 dot-access sites plus 4 new-column-by-assignment sites; (c) `datetime`,
`categorical`, `timeseries`, `strlength`, `ismissing`, `ismember`-on-strings; (d) a non-Java
SHA-256. Realistically that is **Tier 2 for `capacityGuard` + `makeSessionProfiles` +
`managedCharging` + `electricalEconomics` if and only if the string/table surface is rewritten
first** (i.e. Tier 2 costs a mechanical but repo-wide edit of ~800 sites), and it is **never Tier 2
for `plotScenario.m` or `buildSimulinkModel.m`**.

**Tier 3 (Python reimplementation): the only tier that reaches the full pipeline including plots.**
And the cost is lower than it looks — the whole numeric core is ~700 lines of array math over a
289-point time grid and a 9-column session table, with no toolboxes (the code deliberately avoids
Statistics Toolbox: `localPoissonDraw` at `makeSessionProfiles.m:231-245` implements Knuth's
algorithm by hand precisely so it stays base-MATLAB). pandas/numpy/matplotlib map onto
table/array/tiledlayout one-for-one, and `hashlib` replaces the Java call in one line.

**Recommendation for Phase 2:** treat Tier 1 as ruled out by evidence (not by assumption); treat
Tier 2 as viable only as "Octave-compatible fork of the four numeric modules", which requires a
mechanical string/table de-MATLAB-ification pass and still leaves visuals and Simulink behind; and
size Tier 3 as the default for anything the platform must render itself. The decisive datum is
that **the code has never been executed at all** (`matlab/EXECUTION_STATUS.md:9-10`), so there is
no observed-behaviour baseline to preserve — a Python reference implementation has nothing to
regress against except the source semantics documented here.

---

## COMPUTATIONAL PIPELINE

Complete call graph and data contracts, sufficient to write a Python reference implementation
without reading the `.m` files.

### Entry point: `run_all_scenarios([Name,Value]...)` → `outDir` (string)

```
run_all_scenarios
  ├─ loadScenarios(CsvFile)                       -> T : table, 120 rows x 22 cols (19 required)
  ├─ for i = 1:height(T)
  │    row = T(i,:)                               -> one-row table
  │    try
  │      out = runScenario(row, GuardMode="planning_illustration",
  │                             ProfileMode=..., Seed=..., Tariff=...,
  │                             AssumedSiteCapacity_kW=...)
  │      m = out.metrics ; m.run_status="ok" ; m.run_error=""
  │      if SavePlots: plotScenario(out, OutputFolder=outDir,
  │                                 SaveFigure=true, Visible=false)
  │    catch ME
  │      m = localErrorMetricsRow(row, ME)        -> same 23-field struct, NaN-filled
  │    m.run_id = runId ; metricRows{i} = orderfields(m)
  ├─ results = struct2table([metricRows{:}].')    -> 120 x 24 table
  ├─ writetable(results, outDir/results.csv)
  ├─ manifest.txt  (9 keys + 3 note lines)
  └─ hashes.txt    (sha256 of input CSV, sha256 of results.csv)
```

`runId = "batch_" + UTC yyyyMMddTHHmmssZ`; `outDir = <OutputRoot>/<runId>`.

### `loadScenarios(csvFile, ...)` → `T`

- Input: CSV path. Output: table with the `case` column renamed to `case_label`, string-typed
  metadata columns, `Properties.UserData = {source_csv, loaded_utc, horizons_in_data, cases_in_data}`.
- Hard errors on: missing file, any of the 19 required columns missing, any empty `capacity_basis`,
  `ports < 0`, `charger_power_kW <= 0`, `dwell_hr <= 0`, `sessions_per_day < 0`,
  `energy_per_session_kWh < 0`, `arrival_end_hr <= arrival_start_hr`, zero rows after filtering.
  NaN values are exempt from the numeric predicates.

### `runScenario(row, ...)` → `out`

Five sequential stages. Data flowing between them:

**Stage 1 — `capacityGuard(row, Mode, AssumedSiteCapacity_kW)` → `guard`**

Input: the one-row table (or an equivalent struct with at least `capacity_basis`; `scenario_id`
defaults to `"unspecified_scenario"` if absent).
Output `guard` (10 fields): `scenario_id, capacity_basis, is_verified, mode, capacity_kW,
capacity_defined, capacity_definition, placeholder_banner, assumed_capacity_used, allowed_bases`.

Logic:
```
basis = lower(strip(capacity_basis));  if empty -> "unknown"
if basis not in {verified_utility, verified_facility, engineering_estimate,
                 planning_proxy, placeholder, unknown}: ERROR
is_verified = basis in {verified_utility, verified_facility}
if Mode == "feasibility" and not is_verified: ERROR (fail-closed)
if isfinite(service_capacity_kW):            capacity_kW = service_capacity_kW
elif isfinite(spare) and isfinite(base_mean): capacity_kW = base_mean + spare
elif isfinite(AssumedSiteCapacity_kW):        capacity_kW = assumed
                                              is_verified = False; basis = "placeholder"
else:                                         capacity_kW = NaN
capacity_defined = isfinite(capacity_kW)
placeholder_banner = "" if is_verified else <banner template with basis interpolated>
```

**Stage 2 — `makeSessionProfiles(row, Mode, Seed, ChargerEfficiency, DiversityFactor)` → `profiles`**

Input: the same row. Output `profiles` (11 fields): `t_hr, dt_hr, baseLoad_kW, evRequest_kW,
sessions, energyRequested_kWh, mode, params, scenario, charger_efficiency, label`.

```
dt_hr  = TimeStepMinutes/60                       # default 5/60
t_hr   = arange(0, 24+dt, dt)  as a column        # 289 points at default

shape  = exp(-0.5*((t-14)/4.5)^2)
       + 0.25*exp(-0.5*((t-8)/1.7)^2)
       + 0.15*exp(-0.5*((t-19)/2.0)^2)
shape /= max(shape)
baseLoad_kW = base_load_mean_kW + (base_load_peak_kW - base_load_mean_kW)*shape

eta = ChargerEfficiency                            # default 0.93

if Mode == "legacy_gaussian":
    center = (arrival_start_hr + arrival_end_hr)/2
    width  = max((arrival_end_hr - arrival_start_hr)/2, 0.5)
    g = exp(-0.5*((t-center)/width)^2); g /= max(g)
    evRequest_kW = ports * charger_power_kW * g
    sessions = <empty 9-column table>
else:
    if Mode == "stochastic":
        seed_rng(Seed)                             # Mersenne twister
        n = Poisson(sessions_per_day)              # Knuth: L=exp(-lam); multiply U(0,1) until < L
        weights = ones(n)
        arrivals = sorted( uniform(start,end,n)  |  triangular(start,end,peak=midpoint,n) )
    else:  # deterministic_sessions
        n = 0 if sessions_per_day <= 0 else max(1, ceil(sessions_per_day))
        weights = full(n, sessions_per_day / n)
        edges = linspace(start, end, n+1); arrivals = (edges[:-1]+edges[1:])/2

    dwell     = full(n, dwell_hr)
    departure = minimum(arrivals + dwell, 24)
    eBatt     = full(n, energy_per_session_kWh)
    eGrid     = eBatt / eta
    pMax      = full(n, charger_power_kW)
    priority  = ones(n)                            # ALWAYS 1 in the current code

    sessions = table[session_id, arrival_hr, departure_hr,
                     dwell_hr(=departure-arrival), energy_required_kWh(=eBatt),
                     energy_required_grid_kWh(=eGrid), max_power_kW(=pMax),
                     weight(=weights), priority_class(=priority)]

    evRequest_kW = 0
    for k in range(n):
        chargeDuration = min(eGrid[k]/pMax[k], departure[k]-arrivals[k])
        eTarget        = eGrid[k] * min(1, (departure[k]-arrivals[k])*pMax[k]/max(eGrid[k],eps))
                       # == min(eGrid[k], dwell*pMax[k])
        pulse = pulse_profile(t, dt, tOn=arrivals[k], tOff=arrivals[k]+chargeDuration,
                              p=pMax[k], eTarget=eTarget)
        evRequest_kW += weights[k] * pulse

evRequest_kW *= DiversityFactor                   # aggregate only; sessions NOT scaled
energyRequested_kWh = trapz(t_hr, evRequest_kW)

# pulse_profile(t, dt, tOn, tOff, p, eTarget):
#   if tOff <= tOn or p <= 0: return zeros
#   overlap = clip(min(t+dt, tOff) - max(t, tOn), 0, None)
#   prof = p * overlap/dt
#   eNow = trapz(t, prof)
#   if eNow > 0 and eTarget > 0: prof *= eTarget/eNow      # exact energy pinning
```

**Stage 3 — `managedCharging(profiles, strategy, SiteCapacity_kW, Guard, CommsLoss, FailSafeFraction)`
→ `result` (called 1-3 times)**

Call order in `runScenario`:
1. always `managedCharging(profiles, "unmanaged", Guard=guard)`
2. if `guard.capacity_defined`: `managedCharging(profiles, "clamp",
   SiteCapacity_kW=guard.capacity_kW, Guard=guard)`
3. if `guard.capacity_defined` and `ProfileMode != "legacy_gaussian"`:
   `managedCharging(profiles, "energy_aware", SiteCapacity_kW=guard.capacity_kW,
   Guard=guard, CommsLoss=...)`

Otherwise the skip reason strings listed under `runScenario.m` above are recorded.

Output `result` (19 fields): `strategy, t_hr, ev_kW, total_kW, site_capacity_kW, requested_kWh,
delivered_kWh, curtailed_kWh, unmet_kWh, deferred_kWh, balance_error_kWh, peak_total_kW,
peak_ev_kW, max_overload_kW, overload_kW, per_vehicle, comms_loss, notes, guard`.

```
unmanaged:  ev = evRequest
            requested = delivered = trapz(t, evRequest); curtailed = unmet = deferred = 0

clamp:      require isfinite(siteCap) else ERROR
            headroom  = maximum(siteCap - baseLoad, 0)
            ev        = minimum(evRequest, headroom)
            requested = trapz(t, evRequest); delivered = trapz(t, ev)
            curtailed = max(requested - delivered, 0); unmet = 0; deferred = 0

energy_aware: require isfinite(siteCap) else ERROR
              require mode != "legacy_gaussian" and len(sessions) > 0 else ERROR
              ev, per_vehicle, notes = energy_aware_schedule(...)
              requested = sum(per_vehicle.requested_kWh)
              delivered = sum(per_vehicle.delivered_kWh)
              unmet     = sum(per_vehicle.unmet_kWh)
              curtailed = 0
              deferred  = max(max(cumtrapz(t,evRequest) - cumtrapz(t,ev)), 0)

total_kW        = baseLoad + ev
balance_error   = requested - (delivered + curtailed + unmet)
assert abs(balance_error) <= 1e-6*max(1, abs(requested))          # hard ERROR otherwise
overload_kW     = maximum(total - siteCap, 0) if isfinite(siteCap) else full(nT, nan)
peak_total_kW   = max(total_kW); peak_ev_kW = max(ev); max_overload_kW = max(overload_kW)
```

`energy_aware_schedule(sessions, t, dt, baseLoad, siteCap, commsLoss, failSafeFraction)`:

```
req[k] = weight[k] * min(energy_required_grid_kWh[k],
                         (departure_hr[k]-arrival_hr[k]) * max_power_kW[k])
remaining = req.copy(); delivered = zeros(nS); ev = zeros(nT)

for i in range(nT):
    tNow   = t[i]
    active = [k for k if arrival_hr[k] <= tNow < departure_hr[k] and remaining[k] > 1e-12]
    if not active: continue

    if commsLoss:
        # NO site-capacity enforcement, by design
        for k in active:                                # original session order
            pMax = failSafeFraction * max_power_kW[k] * weight[k]
            p    = min(pMax, remaining[k]/dt)
            ev[i] += p; delivered[k] += p*dt; remaining[k] -= p*dt
    else:
        headroom = max(siteCap - baseLoad[i], 0)
        queue    = sorted(active, key=(priority_class, departure_hr, arrival_hr))   # EDF
        for k in queue:
            if headroom <= 1e-12: break
            p = min(max_power_kW[k]*weight[k], headroom, remaining[k]/dt)
            ev[i] += p; headroom -= p; delivered[k] += p*dt; remaining[k] -= p*dt

unmet = maximum(req - delivered, 0)
per_vehicle = sessions + columns[requested_kWh=req, delivered_kWh=delivered,
                                unmet_kWh=unmet,
                                fully_served = unmet < max(1e-6, 1e-6*max(req))]
```

Note the integration asymmetry to reproduce faithfully: `delivered` accumulates `p*dt`
(left-Riemann), while `requested_kWh` for `unmanaged`/`clamp` uses `trapz`. The energy balance
closes because `req[k]` and the pulse `eTarget` use the *same* `min(eGrid, dwell*pMax)` formula
(`makeSessionProfiles.m:172-174` vs `managedCharging.m:232-235`) and `pulse_profile` pins each
pulse's trapz energy exactly to that value.

**Stage 4 — `electricalEconomics(results.unmanaged, managedResult, ChargerEfficiency, Guard, Tariff)`
→ `econ`**

`managedResult` = `energy_aware` if present, else `clamp`, else `unmanaged` (self-comparison).

```
pf = PowerFactor (default 0.95, NOT exposed by runScenario)
peak_kVA_* = peak_kW_* / pf
peak_reduction_kW = peak_unmanaged - peak_managed

serviceCap = ServiceCapacity_kW  (default NaN) ; if NaN and Guard has capacity_kW: use Guard's
if not isfinite(serviceCap): service_check = "service_capacity_unknown"
elif peak_managed <= serviceCap: service_check = "within_service"
else: service_check = "exceeds_service"
service_check_note = VERIFIED-wording iff Guard.is_verified else NON-VERIFIED wording
banner = Guard.placeholder_banner

if Tariff has numeric demand_charge_usd_per_kw_month AND energy_usd_per_kwh:
    demand_charge_usd_month_{unmanaged,managed} = peak_kW_* * dc
    demand_charge_savings_usd_month             = (peakUn - peakMg) * dc
    energy_cost_usd_day_{unmanaged,managed}     = delivered_kWh_* * ec
    cost_status = "computed"
else:
    all five cost fields = NaN ; cost_status = "tariff_not_supplied"
```

**Stage 5 — flat `metrics` (21 fields)** — see the `runScenario.m` entry above for the exact list
and order. This is the `results.csv` schema (plus `run_status`, `run_error`, `run_id`, then
alphabetized by `orderfields`).

### Side branches (not in the metric path)

- `plotScenario(out, ...)` — pure rendering; called only from `run_all_scenarios` when
  `SavePlots=true`. Reads `out.scenario`, `out.guard`, `out.profiles`, `out.results`.
- `buildSimulinkModel(out, ...)` — never called from anywhere in `src/`; manual entry point;
  reads `out.scenario`, `out.profiles`, `out.guard`. Illustrative only (see topology section).

### Constants a Python reference must carry

| constant | value | source |
|---|---|---|
| profile time step | 5 minutes → `dt_hr = 1/12`, 289 samples over `[0,24]` | `makeSessionProfiles.m:77, 87-89` |
| charger efficiency | `0.93` (grid-side draw = battery energy / eta) | `makeSessionProfiles.m:73`, `electricalEconomics.m:56`, `runScenario.m:54` |
| diversity factor | `1.0` | `makeSessionProfiles.m:75`, `runScenario.m:56` |
| power factor | `0.95` | `electricalEconomics.m:54` |
| fail-safe fraction | `0.5` of charger power under comms loss | `managedCharging.m:72` |
| RNG seed | `42`, Mersenne twister | `makeSessionProfiles.m:72,124`; `runScenario.m:53`; `run_all_scenarios.m:53` |
| base-load shape | daytime `μ=14, σ=4.5`; morning `0.25 × μ=8, σ=1.7`; evening `0.15 × μ=19, σ=2.0`; normalized to peak | `makeSessionProfiles.m:95-99` |
| legacy Gaussian width floor | `0.5` h | `makeSessionProfiles.m:117` |
| energy-balance tolerance | `1e-6 * max(1, |requested|)` kWh | `managedCharging.m:156` |
| active-session energy epsilon | `1e-12` kWh | `managedCharging.m:253, 278` |
| fully-served threshold | `max(1e-6, 1e-6*max(req))` kWh | `managedCharging.m:298-299` |
| priority classes | always `1` | `makeSessionProfiles.m:157` |
| Simulink model version | `"3.0.0"`, solver `ode3`, fixed step `300 s`, stop `86400 s` | `buildSimulinkModel.m:38, 147-149` |

**No emissions factor, no eGRID value, no CO2 coefficient, and no horizon-year literal appears
anywhere in these 9 files.** Confirmed by grep for `596.3`, `590.2`, `egrid`, `co2`, `emission`,
and for `2026|2030|2035|2036|2040|2046|2050|2056`, `10-year`, `20-year`, `30-year`, `"Now"` — all
return zero matches in `matlab/src/`. Horizons are read from the CSV column `horizon_year`
(`loadScenarios.m:141, 165`; `run_all_scenarios.m:81`), and the CSV contains exactly
2026 / 2036 / 2046 / 2056.

---

## MISCELLANEOUS CROSS-CHECKS PERFORMED

- **No absolute local paths** (`/Users/...`) anywhere in the 9 files. All paths are derived from
  `mfilename("fullpath")`.
- **No secrets, tokens, AWS account IDs, or API keys** in the 9 files.
- **Backlog-item coverage:** `ML-01, ML-03, ML-04, ML-05, ML-06, ML-07, ML-08, ML-11, ML-12` are
  referenced in `src/`. **`ML-02`, `ML-09`, `ML-10` are never referenced in `src/`** — either they
  live in `tests/`/docs or they are uncovered. Flagged for Phase 1 cross-check.
- **Hypothesis references:** `H1`, `H2`, `H5` (`makeSessionProfiles.m:9`, `:165`), `H3`
  (`capacityGuard.m:2`), `H4` (`managedCharging.m:12`, `:115`), `H8` (`buildSimulinkModel.m:8`).
  `EXECUTION_STATUS.md:29` references "H1-H15" — H6, H7, H9-H15 are not referenced from `src/`.
- **`EXECUTION_STATUS.md` static-check table spot-verified.** Its claimed block-opener counts of
  16 for `capacityGuard.m` and 7 for `run_all_scenarios.m` were independently recounted by hand
  and both match. The static-check artifact does not appear to have drifted from the source.
- **Referenced paths that exist:** `matlab/data/canonical/matlab_scenarios.csv` ✔,
  `matlab/outputs/` ✔ (contains only `.gitkeep`).
  **Referenced paths that do not exist:** `matlab/simulink/` (default `ModelFolder`,
  `buildSimulinkModel.m:46`) — created on demand at `:63-65`, so not a defect, and its absence
  corroborates that no model was ever built.
