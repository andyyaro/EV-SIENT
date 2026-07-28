# Drift baseline for `test_regression.m`

`regression_golden.csv` is the summary-metric baseline `testGoldenSummaryMetrics` compares
against. **It was missing from this path for the whole program.**

## Why that mattered

`test_regression.m` is written to bootstrap itself: on a first run with no baseline it *writes*
one, logs that it did, and passes the comparison against what it just wrote. That is the right
behaviour for a first licensed run — and it means the test **cannot fail** until a baseline is
committed here.

The licensed CI run did produce the file. It was committed under
`matlab/outputs/run-30296650057/regression_golden.csv`, alongside the rest of the run
artifacts — but never copied to the path the test actually reads
(`matlab/tests/golden/regression_golden.csv`). So every subsequent run re-bootstrapped, and a
drift test that had run several times had never once compared anything.

## Provenance of this file

Copied verbatim from `matlab/outputs/run-30296650057/regression_golden.csv` on 2026-07-28.
That artifact is **byte-identical** to the one in `run-30291108647`
(sha256 `b7c80d06b5c2…`), so the two licensed runs agree and either would serve.

Produced by real MathWorks MATLAB R2025b Update 5 against a **synthetic fixture** — like every
MATLAB artifact in this repository, it describes no real facility.

**Do not hand-edit.** If a legitimate model change moves these metrics, regenerate on a licensed
machine and commit the new file with its run id, so the change is a reviewable diff.
