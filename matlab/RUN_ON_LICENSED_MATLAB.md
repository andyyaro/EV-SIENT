# Running on a Licensed MATLAB Machine

> **This page is preserved as the first-run procedure. Its opening sentence was true
> when written and is no longer.** The suite has since been executed on licensed MathWorks
> R2025b Update 5 — **49 passed / 0 failed** — against a synthetic fixture. See
> `EXECUTION_STATUS.md` for the run record. The procedure below remains correct for anyone
> running it themselves.

This repository was authored without any MATLAB installation. This page is
the exact, copy-paste procedure for a licensed run: MATLAB
**R2025b**, base MATLAB is sufficient for everything except step 6.

All commands are run from the `matlab/` directory of the repository.

## 1. Smoke check (seconds)

```bash
matlab -batch "addpath('src'); T = loadScenarios('data/canonical/matlab_scenarios.csv'); disp(height(T)); disp(unique(T.horizon_year)')"
```

Expected: `120`, then `2026 2036 2046 2056`. Any error here is a data or
path problem - fix before proceeding.

## 2. Test suite (expected ~1-3 minutes)

```bash
matlab -batch "addpath('src'); results = runtests('tests'); disp(table(results)); assertSuccess(results)"
```

Expected:
- All tests in `test_loadScenarios`, `test_profiles`, `test_capacityGuard`,
  `test_managedCharging`, `test_horizons` pass.
- `test_regression` **creates** `tests/golden/regression_golden.csv` on
  this first run (logged as "GOLDEN CREATED") and passes. **Commit that
  file** - it becomes the drift baseline for every later run.

If any test fails, stop and report the failure verbatim; do not regenerate
goldens to make a failure disappear.

## 3. Full batch run (expected ~1-5 minutes for 120 scenarios; the
pipeline is vectorized per scenario and has no Simulink dependency)

```bash
matlab -batch "addpath('src'); outDir = run_all_scenarios(); disp(outDir)"
```

Expected outputs under `outputs/batch_<UTCstamp>Z/`:
- `results.csv` - 120 rows; every row has `run_status=ok`;
  `capacity_basis=placeholder` and a non-empty `placeholder_banner` on all
  rows; `skipped_strategies` says clamp/energy_aware were skipped
  (no capacity defined in the CSV).
- `manifest.txt` - run metadata incl. MATLAB release.
- `hashes.txt` - SHA-256 of the input CSV and of `results.csv`.

To exercise the capacity-limited strategies portfolio-wide with a labeled
planning assumption (example: 200 kW):

```bash
matlab -batch "addpath('src'); run_all_scenarios('AssumedSiteCapacity_kW',200)"
```

Then `peak_clamp_kW`, `curtailed_clamp_kWh`, `peak_energy_aware_kW`,
`unmet_energy_aware_kWh`, `deferred_energy_aware_kWh` populate, still
placeholder-labeled.

## 4. Per-scenario figures

```bash
matlab -batch "addpath('src'); run_all_scenarios('AssumedSiteCapacity_kW',200,'SavePlots',true)"
```

PNG names follow `scenario_<id>_<site>_<horizon>_<UTC>.png` (ML-12). Every
figure must visibly show (a) the orange placeholder banner across the top
and (b) the source/date footer - if either is missing, that is a bug;
report it.

## 5. Comparing against the committed legacy PNGs

The legacy MATLAB workspace (preserved in the pre-V3 archive branch
`archive/pre-milestone2-v3-20260719`, not in this tree; the scripts
themselves are in `legacy_archive/`) contains
`professional_site_load_..._Now.png` and
`professional_year_comparison_....png` produced by `untitled.m` from the
old 36-row CSV. To reproduce a comparable visual:

```matlab
addpath('src');
T = loadScenarios('data/canonical/matlab_scenarios.csv', ...
      'SiteId','FFX002', 'HorizonYear',2026);
out = runScenario(T(1,:), 'GuardMode','planning_illustration', ...
      'ProfileMode','legacy_gaussian', 'AssumedSiteCapacity_kW',205);
plotScenario(out, 'SaveFigure',true, 'OutputFolder','outputs/legacy_compare');
```

Expected qualitative match with the legacy "Now" PNG: capacity line near
205 kW (legacy 51.4 + 153.6), base-load curve identical in shape, EV
request peaking at ports x 19.2 kW mid-window. Expected differences: the
V3 figure adds the placeholder banner, the capacity-basis label, and the
footer; horizon label is 2026, not "Now"; port counts come from the
canonical CSV, so they match the Python tables (H14 fix). Do **not**
expect numeric identity with the legacy year-comparison PNG - the legacy
CSV's ports column mixed Python scenario columns (H14) and its horizons
were Now/2035/2050.

The default (session-based) profile will look materially different from
the legacy PNGs - lower, wider EV demand. That difference is the ML-03
fix, not a regression.

## 6. Optional Simulink layer (requires Simulink license)

```matlab
addpath('src');
T = loadScenarios('data/canonical/matlab_scenarios.csv','SiteId','FFX002','HorizonYear',2036,'Case','base');
out = runScenario(T(1,:),'GuardMode','planning_illustration','AssumedSiteCapacity_kW',200);
buildSimulinkModel(out);          % creates simulink/*.slx ONCE
sim('site_grid_behavior_ev_charging_v3');
```

Expected: model builds only if absent (second call prints "NOT rebuilt");
`simulink/site_grid_behavior_ev_charging_v3_params.mat` (and `.sldd` when
the dictionary API succeeds) hold the externalized parameters; the model
Description carries version/scenario/build stamp. This layer is
illustrative - do not quote numbers from the scope; quote `results.csv`.

## 7. Record the run

Append the outcome (date, machine, MATLAB `version`, test summary, batch
`run_id`) to `EXECUTION_STATUS.md`, replacing its BLOCKED banner with an
executed-verification section. Until that happens, no simulation may be
claimed anywhere.
