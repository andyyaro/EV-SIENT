# CI run 30291108647 — the first execution of this MATLAB code, ever

Downloaded from the public harness `andyyaro/fcf-matlab-ci` and committed unmodified. Nothing
in this directory was produced on a developer machine, edited by hand, or reformatted.

## Read this before quoting any number here

> **The input was a SYNTHETIC fixture. Not one row corresponds to any real facility.**

Site ids are `SYN001`–`SYN012`. They are structurally valid, deliberately obvious, and match
nothing. The values were fabricated by `scripts/make_harness_fixture.py` to reproduce the real
file's *structure* — row count, the horizon × case grid, the value ranges, and specifically
the branch-selecting edge cases — while sharing none of its per-site values.

A number in `batch_results.csv` is evidence that **the code computes**. It is not evidence
about a site, a jurisdiction, or a charger.

## Provenance

| Field | Value |
|---|---|
| Engine | **MathWorks MATLAB** — not GNU Octave, not a Python reimplementation |
| Version | `25.2.0.3177638 (R2025b) Update 5` |
| Runner | GitHub-hosted `ubuntu-24.04` |
| Repository | `andyyaro/fcf-matlab-ci` (public harness) |
| Commit | `b56c6b68c138ea4f2dc499488830634b155bb524` |
| CI run | `30291108647`, 2026-07-27T17:51:15Z |
| Input | `harness_scenarios_synthetic.csv`, SHA-256 `8e869e112e6cf201ed5ead2d8aa86d2408d2daa70a85aafb5c121cbe63b99220` |
| Tests | **49 passed, 0 failed, 0 incomplete** |

## Files

| File | What it is |
|---|---|
| `batch_results.csv` | The 120-row batch. `run_status = ok` on every row. |
| `batch_manifest.txt` | Batch run id, seed, profile mode, and the placeholder note, as MATLAB wrote them. |
| `batch_hashes.txt` | SHA-256 of the input and the output, written by the run itself. |
| `regression_golden.csv` | The golden baseline as this run created it. **NOT superseded** — see the caveat below; the table previously said the opposite of the section it points to. Byte-identical to `run-30296650057`'s copy, and now also committed at `matlab/tests/golden/` where `test_regression.m` actually reads it. |
| `matlab_version.txt` | `version()`, `version('-release')`, and the Simulink license test. |
| `run_provenance.txt` | Engine, release, repository, commit, run id, input hash, written *before* anything executed. |

## Two honest caveats about these specific files

**1. `regression_golden.csv` is NOT superseded — an earlier note here said it was, and that
was wrong.** The fixture did change after this run (it carried `sessions_per_day = 0.9`,
which is one real site's value and no other's, so the generator was corrected and three cells
moved to `0.91`), and the expectation was that any golden built from the old fixture would
stop matching. It was checked rather than left as an expectation, and it does still match:
run `30296650057`'s golden is **byte-identical** to this one. The reason is that the golden
panel is built from `SYN001` and `SYN002`, and the three corrected cells are in `SYN004`,
`SYN008` and `SYN012`. The change never touched the panel.

**The same check produced a determinism result worth more than the correction.** Comparing
this run's 120-row batch against run `30296650057`'s, run on a different commit days apart:
**exactly 3 rows differ, and they are exactly the 3 rows the fixture change touched, in
exactly the 2 columns that depend on `sessions_per_day`.** The other 117 rows are identical
cell for cell. Two independent CI runs on real MATLAB agree completely on unchanged input.

**2. `matlab_version.txt` says `simulink_licensed: 1` on a run whose Simulink build failed.**
Both statements are true and the field was badly named: `license('test',...)` answers *could a
license be checked out*, which is not *is the product installed and usable*. The workflow now
records `simulink_license_test` and `simulink_installed` separately. The build failure was
caused by a defect in `buildSimulinkModel`'s own availability guard, not by anything missing
on the runner — see `matlab/EXECUTION_STATUS.md`.

## The most valuable thing in this directory

`batch_results.csv`, on all 120 rows:

- `capacity_basis = placeholder`
- `service_check = service_capacity_unknown`
- `skipped_strategies = clamp: skipped_no_capacity_defined; energy_aware: skipped_no_capacity_defined`
- `peak_clamp_kW` — **NaN**, i.e. no number was invented to fill the gap
- the mandatory planning-placeholder banner present on every row

**The fail-closed capacity guard fires on real MATLAB.** That matters because FIND-MATLAB-09
reproduced the same guard *not* firing under GNU Octave 11.3.0. The guard is sound on
MathWorks MATLAB and unsafe on Octave — which is why Octave is documented as a syntax and
smoke tier only, and may never be used to make a feasibility statement.
