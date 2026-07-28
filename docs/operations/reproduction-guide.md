# Reproduction Guide

[← docs index](../README.md)

Every command below was verified on macOS (Apple Silicon) with Python 3.14 on
2026-07-19. Python 3.11+ is supported. All commands run from the **repository
root** unless noted. No internet access is required for any step — GIS
boundaries are cached in `data/cache/`.

## 0. Environment

```bash
make setup      # creates ./venv and installs the package editable with pinned [test] extras
```

## 1. Test suite (expect: all tests pass; coverage gate ≥ 80%)

```bash
make test
```

Includes the legacy golden tests, cohort-invariance tests, contract validation
tests, and offline-GIS tests.

## 2. Legacy baseline (expect: FFX002 58.8; 25 starter / 48 pathway ports)

```bash
make run-legacy      # writes data/outputs/legacy_check/
```

`legacy_v2` mode reproduces the accepted V2 baseline bit-for-bit; the golden
tests in `make test` enforce the same numbers.

## 3. V3 run + contract (expect: contract valid, 120 scenario rows)

```bash
make run-v3          # writes data/outputs/v3_run/ (scores, scenarios, economics,
                     # emissions, contract tables, matlab_scenarios.csv)
make validate        # validates the tracked canonical contract at data/contract/v1
```

## 4. Artifact rebuilds

```bash
make dashboard                                   # = make run-v3 + build_static_dashboard.py
venv/bin/python scripts/build_static_dashboard.py    # 9 visuals + STATIC_DASHBOARD.pdf + footer QA
                                                     # into dashboard/static/
venv/bin/python scripts/build_excel_workbook.py --source "/path/to/Electric Data.xlsx"
```

The Excel rebuild requires the team's original workbook via `--source`; the
original is **not tracked** in this repository (only the updated output,
`excel/Electric_Data_Milestone_2_Updated.xlsx`, is).

To refresh the MATLAB canonical input: run `make run-v3`, then copy
`data/outputs/v3_run/matlab_scenarios.csv` to
`matlab/data/canonical/matlab_scenarios.csv` and re-run `make validate`.

## 5. Full verification (one command)

```bash
./scripts/verify.sh      # every repository gate; exits nonzero on any failure
```

Gates: tests + coverage floor, legacy baseline reproduction (25/48), contract
rules/schema/hash chain, cross-model reconciliation with the MATLAB canonical
CSV, workflow-docs consistency, dashboard footer QA, secret scan, local-path
scan, file-size limit, and Markdown link check. CI runs the same gates
([.github/workflows/tests.yml](../../.github/workflows/tests.yml)).

## 6. MATLAB (requires licensed R2025b — never executed in the authoring environment)

Run from the `matlab/` directory:

```bash
cd matlab
matlab -batch "addpath('src'); run_all_scenarios"
matlab -batch "addpath('src'); results = runtests('tests'); assertSuccess(results)"
```

See [matlab/RUN_ON_LICENSED_MATLAB.md](../../matlab/RUN_ON_LICENSED_MATLAB.md)
for the full first-run procedure and expected outputs, and
[matlab/EXECUTION_STATUS.md](../../matlab/EXECUTION_STATUS.md) for what has
and has not been executed (nothing has — no license was available).

## Expected results summary

| Check | Expected |
|---|---|
| `make test` | all tests pass; coverage ≥ 80% |
| `make run-legacy` | starter_total 25, pathway_total 48 (accepted V2 baseline) |
| `make validate` | contract v1.0.0 passes all rules, JSON Schema, and the manifest hash chain |
| `./scripts/verify.sh` | `ALL REPOSITORY VERIFICATION GATES PASSED` |

## Determinism notes

- All simulations are seeded: `SIM_RANDOM_SEED = 20260719`
  (`src/fcf_m2/config.py`), so repeated runs produce identical numbers.
- The contract `run_id` / `generated_at` are timestamps, and the table hashes
  in `contract_manifest.json` change per run **by design** — the RT-10 hash
  chain exists to prevent quoting a stale contract against fresh tables.
- Every step is fully offline; there is no first-run download.
