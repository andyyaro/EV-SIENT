# MATLAB/Simulink Site-Grid Behavior Model - Milestone 2 V3

Site-level, 24-hour EV-charging load-behavior model for the Future City
Fellowship (GMU) Milestone 2 portfolio: 12 sites (FFX/PWC), horizons
2026/2036/2046/2056, cases baseline/base/high/stress_combined, driven by the
canonical scenario table auto-generated from the Python V3 model.

This is the V3 rewrite that closes backlog items ML-01..ML-12 from the
research-phase MATLAB/Simulink improvement backlog (a pre-V3 research
artifact, not tracked in this repository). The two legacy scripts are
archived unchanged in `legacy_archive/` with a full migration note.

> **EXECUTION STATUS - READ FIRST**: this repository was authored in an
> environment with **no MATLAB installation** (2026-07-19). All code is
> statically written and reviewed; **no simulation, test run, or figure in
> this repo has been executed or generated**. `EXECUTION_STATUS.md` records
> exactly what was and was not verified, and
> `RUN_ON_LICENSED_MATLAB.md` gives the exact commands for the first
> execution on a licensed machine.

## Requirements

| Component | Requirement |
|---|---|
| MATLAB | **R2025b** (release used by the legacy `.slx` provenance; earliest intentionally supported release; string/`tiledlayout`/`exportgraphics`/`renamevars` APIs used throughout) |
| Simulink | **Optional.** Only `src/buildSimulinkModel.m` uses it, and that layer is illustrative. The entire quantitative pipeline (profiles, strategies, economics, batch runner, tests) runs in **base MATLAB** |
| Other toolboxes | None. Stochastic draws use base-MATLAB `rng`/`rand` (Poisson via Knuth's algorithm - no Statistics Toolbox). Hashing uses `java.security.MessageDigest` (base MATLAB) |

## Repository layout

```
data/canonical/matlab_scenarios.csv   canonical input (auto-generated - do not hand-edit)
src/                                  the pipeline (base MATLAB)
tests/                                MATLAB unittest suite (function-based)
outputs/                              batch run outputs (created at run time)
legacy_archive/                       unchanged legacy scripts + MIGRATION_NOTE.md
../.github/workflows/matlab-manual.yml  CI definition, manual-trigger (not yet executed anywhere)
DATA_DICTIONARY.md                    every input column: type, unit, allowed values, provenance
RUN_ON_LICENSED_MATLAB.md             exact commands for the licensed runner
EXECUTION_STATUS.md                   what has and has NOT been executed
```

## Model purpose

A planning-level illustrator of how site electrical load behaves over a
24-hour day when EV charging is added, and of how much a managed-charging
controller changes that behavior. It supports stakeholder conversations and
scenario comparison. It is **not** a feeder study, an interconnection
screen, or an engineering design tool, and it can make **no feasibility
claim** while capacity data is a placeholder (see the guard below).

Pipeline per scenario row:

```
loadScenarios -> capacityGuard -> makeSessionProfiles -> managedCharging
   (CSV)         (fail-closed)     (session demand)      (3 strategies)
                                        -> electricalEconomics -> metrics/plots
```

- **`loadScenarios`** - reads/validates the canonical CSV; filters by
  `site_id` / `horizon_year` / `case`; horizons are discovered from the
  data, never hard-coded (ML-06). The CSV column `case` is exposed in
  MATLAB as `case_label` (keyword clash).
- **`makeSessionProfiles`** - session-based demand (ML-03): sessions/day,
  arrival window, dwell actually consumed, energy per session, charger
  power, charger efficiency, diversity. Modes: `deterministic_sessions`
  (default), `stochastic` (Monte Carlo, seeded), `legacy_gaussian`
  (presentation continuity only, clearly labeled).
- **`capacityGuard`** - controlled `capacity_basis` vocabulary; fail-closed
  feasibility gate; mandatory placeholder banner (ML-04).
- **`managedCharging`** - `unmanaged`, legacy `clamp`, and `energy_aware`
  deferral scheduler with per-vehicle energy/deadline accounting, priority
  classes, and a comms-loss fail-safe (ML-05). Strict invariant:
  `requested = delivered + curtailed + unmet` (checked to 1e-6).
- **`electricalEconomics`** - efficiency, power factor, service check,
  demand-charge economics **only when a tariff struct is supplied**;
  otherwise labeled `tariff_not_supplied` - never invented (ML-11).
- **`buildSimulinkModel`** - optional illustrative Simulink layer; builds
  once, never deletes/rebuilds, version-stamped, parameters externalized
  (ML-07).

## Units

kW (power), kWh (energy), hours (time, 0-24 local), USD (costs, only when
a tariff is supplied). `energy_per_session_kWh` is battery-side; grid-side
values are efficiency-adjusted inside `makeSessionProfiles`.

## Inputs

Single input: `data/canonical/matlab_scenarios.csv` - 120 rows = 12 sites
x {2026 baseline; 2036/2046/2056 x base/high/stress_combined}. It is
**auto-generated** by the Python adapter (`fcf_m2.matlab_adapter`) from
canonical contract 1.0.0; column-by-column detail in `DATA_DICTIONARY.md`.

**Current data state (important):** `capacity_basis` is `placeholder` on
**all** rows and `service_capacity_kW`/`spare_capacity_kW` are **empty**.
Consequences, by design:

- Feasibility mode errors for every row (fail-closed).
- Capacity-limited strategies (`clamp`, `energy_aware`) run only when you
  pass an explicit, labeled planning assumption
  (`AssumedSiteCapacity_kW`), which itself forces placeholder labeling.

## Run commands

Single scenario (interactive):

```matlab
addpath('src');
T   = loadScenarios('data/canonical/matlab_scenarios.csv', ...
        'SiteId','FFX002', 'HorizonYear',2036, 'Case','base');
out = runScenario(T(1,:), 'GuardMode','planning_illustration', ...
        'AssumedSiteCapacity_kW',200);   % labeled planning assumption
plotScenario(out, 'SaveFigure',true, 'OutputFolder','outputs/adhoc');
```

Batch over the whole portfolio (headless, ML-08):

```bash
matlab -batch "addpath('src'); run_all_scenarios"
```

Writes `outputs/batch_<UTC>/results.csv` + `manifest.txt` + `hashes.txt`
(SHA-256 of input and results). Options (tariff, seed, profile mode,
assumed capacity, per-scenario plots) are name-value pairs on
`run_all_scenarios`.

Tests:

```bash
matlab -batch "addpath('src'); results = runtests('tests'); assertSuccess(results)"
```

Optional Simulink layer (requires Simulink; illustrative only):

```matlab
buildSimulinkModel(out);   % builds simulink/<model>.slx ONCE if absent
```

## Output interpretation

`results.csv` columns of note:

| Column | Meaning |
|---|---|
| `peak_unmanaged_kW` | daily peak of base + uncontrolled EV request |
| `peak_clamp_kW` / `curtailed_clamp_kWh` | legacy clamp: peak and energy refused (never rescheduled) |
| `peak_energy_aware_kW` / `unmet_energy_aware_kWh` / `deferred_energy_aware_kWh` | scheduler: peak, energy not delivered by departure, energy shifted later and recovered |
| `capacity_basis` / `capacity_verified` | provenance of any capacity number used |
| `placeholder_banner` | non-empty text that MUST accompany the row wherever it is shown |
| `service_check` | `within_service` / `exceeds_service` / `service_capacity_unknown` - labeled non-verified unless basis is verified |
| `cost_status` | `computed` only when a tariff was supplied, else `tariff_not_supplied` |
| `skipped_strategies` | strategies not run and why (e.g. no capacity defined) |

Reading the comparison: `curtailed` (clamp) means vehicles simply got less
energy; `deferred` (energy-aware) means energy was moved later within the
dwell window; `unmet` means the scheduler could not meet a vehicle's need
before departure - a real service failure that the legacy model could not
even express.

## Presentation-use rules (mandatory)

1. **Placeholder-capacity caption is mandatory.** Any slide, figure, or
   table showing a capacity line or a capacity-relative result for a row
   whose `capacity_basis` is not `verified_utility`/`verified_facility`
   MUST carry the banner text (the guard emits it; `plotScenario` renders
   it automatically and cannot be told not to). Suggested caption wording:
   *"Illustrates managed-charging behavior; capacity is a planning
   placeholder pending utility/facility confirmation."*
2. Port counts shown on MATLAB visuals must come from this canonical CSV
   so they match the Python/report tables (closes the H14 mismatch).
3. Cite the run: `run_id` + `generated_utc` from the batch `manifest.txt`.
4. `legacy_gaussian` figures must be labeled as legacy-shape continuity
   visuals, not as the session-based model.
5. Never present a Simulink screenshot as evidence of simulation that was
   not run; `EXECUTION_STATUS.md` is authoritative on what has been run.

## Production restrictions

- **No feasibility, adequacy, or headroom claims** while
  `capacity_basis=placeholder` - the code enforces this (fail-closed
  guard), and prose must respect it too.
- Outputs are planning-support values only: not engineering, permitting,
  budget, or procurement values (data-contract rule).
- Costs are computed only from a user-supplied tariff struct; there is no
  built-in tariff and none may be assumed.
- Do not hand-edit `data/canonical/matlab_scenarios.csv`.

## Regeneration instructions

1. **Input CSV**: regenerate from the Python V3 model (producer of the
   canonical contract): run `make run-v3` at the repository root — the
   `fcf_m2.matlab_adapter` writes `data/outputs/v3_run/matlab_scenarios.csv`
   (repo root); copy it to `matlab/data/canonical/matlab_scenarios.csv`.
   Validate with `make validate` at the repository root.
2. **Results**: `matlab -batch "addpath('src'); run_all_scenarios"`.
3. **Golden regression baseline**: first licensed run of
   `runtests('tests')` writes `tests/golden/regression_golden.csv`;
   commit it (see `test_regression.m` header).
4. **Simulink model**: delete `simulink/*.slx` only as a deliberate,
   reviewed action; `buildSimulinkModel` will then rebuild once and
   re-stamp the version.

## Limitations

- 24-hour single-day model; no seasonality, no multi-day billing peaks
  (demand-charge math assumes the modeled day sets the monthly peak -
  stated simplification).
- Base-load day-shape is the legacy Gaussian family (continuity choice),
  scaled mean-to-peak from the CSV; it is not metered interval data.
- Session energy and counts are planning inputs from the Python model,
  not telematics.
- No voltage/phase/thermal modeling; `electricalEconomics` covers
  efficiency, power factor, and a service-limit comparison only.
- The Simulink layer models only the legacy clamp for illustration.
