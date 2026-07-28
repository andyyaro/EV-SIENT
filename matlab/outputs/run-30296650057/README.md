# CI run 30296650057 — the first Simulink model this project has ever built

Downloaded from the public harness `andyyaro/fcf-matlab-ci` and committed unmodified.

## Read this before quoting any number here

> **The input was a SYNTHETIC fixture. Not one row corresponds to any real facility.**

Site ids are `SYN001`–`SYN012`. A number in `batch_results.csv` is evidence that the code
computes. It is not evidence about a site, a jurisdiction, or a charger.

## Provenance

| Field | Value |
|---|---|
| Engine | **MathWorks MATLAB** — not GNU Octave, not a reimplementation |
| Version | `25.2.0.3177638 (R2025b) Update 5` |
| Simulink | `simulink_license_test: 1`, `simulink_installed: 1` — recorded separately now, see below |
| Runner | GitHub-hosted `ubuntu-24.04` |
| Commit | `343f1983275ceb55fdae4647f5295d3b3e3dc00f` |
| CI run | `30296650057` (run number 9), 2026-07-27T19:06:44Z |
| Input | `harness_scenarios_synthetic.csv`, SHA-256 `ab1f6584…07d5fb` — the **corrected** fixture |
| Tests | **49 passed, 0 failed, 0 errors, 0 skipped** (from `junit.xml`) |
| Batch | 120 rows, `run_status = ok` on every row |
| Simulink build | **SUCCEEDED** |

## What is new in this run

### The Simulink model exists

`simulink/site_grid_behavior_ev_charging_v3.slx` is a real Simulink package — a 24-entry zip
whose `metadata/mwcorePropertiesReleaseInfo.xml` records `25.2.0.3177638 / R2025b / Update 5`.

Until this run, `buildSimulinkModel.m` gated itself on `exist("new_system", "file") ~= 2`.
`new_system` is a Simulink **built-in**, and `exist(name,"file")` returns **0** for a built-in,
so the guard could never pass and this layer had **never been reachable on any installation** —
its "Simulink is not available" message had never once been true when printed. It failed
*closed*, which is why it read as caution rather than as a defect.

The topology in the built file matches, block for block, the topology read from
`buildSimulinkModel.m` by hand in Phase 0 — **11 root blocks**, same names, same types:

| Block | Type |
|---|---|
| `Base Load`, `EV Request`, `Capacity Limit` | FromWorkspace |
| `Total Unmanaged`, `Total Managed` | Sum |
| `Managed Logic Inputs`, `Main Scope Signals` | Mux |
| `Managed EV Power` | SubSystem (the MATLAB Function block) |
| `Live Scope: Load Behavior` | Scope |
| `toWorkspace_unmanaged`, `toWorkspace_managed` | ToWorkspace |

Connections are **not** claimed to match a count. The source calls `add_line` 15 times; the
saved file stores 8 `<Line>` elements with 12 `<Branch>` elements at root plus 4 lines in the
subsystem, because Simulink stores one line per source port and represents fan-out as
branches. Those are different encodings of the same graph, and asserting they are equal
without checking the graph itself would be a claim beyond the evidence.

### A figure was generated

`figures/scenario_SYN001_2026_baseline_*.png` — 24-hour load profile, EV request versus
managed output, and summary metrics, carrying the mandatory placeholder banner.

**The figure in this directory has a known rendering defect and is kept as the record of it.**
MATLAB text defaults to the TeX interpreter, which reads `_` as "subscript the next
character", so this figure states its own source file as `harness_scenarios_ynthetic.csv` —
the `s` subscripted out of the name — and renders the banner's `CAPACITY_BASIS` with the `B`
dropped below the line. That is a provenance defect rather than a typographical one: the
figure names a source file that does not exist, in a repository whose claim is that every
number is traceable. Fixed in `plotScenario.m` by setting `Interpreter` to `none`. It was
found by downloading the PNG and looking at it.

### The provenance field that was lying is now two fields

Run 6 recorded `simulink_licensed: 1` in the same artifact set whose Simulink step had just
failed. Both were true: `license('test',…)` answers *could a license be checked out*, which
is not *is the product installed and usable*. Now recorded as `simulink_license_test` and
`simulink_installed` separately.

## Determinism, measured rather than assumed

Comparing this run's 120-row batch against run `30291108647`'s — a different commit, a
separate runner, hours apart:

**Exactly 3 rows differ. They are exactly the 3 rows the fixture correction touched
(`SYN004`, `SYN008`, `SYN012` at `2036_high`), in exactly the 2 columns that depend on
`sessions_per_day`.** The other 117 rows are identical cell for cell.

`regression_golden.csv` here is **byte-identical** to run 6's, because the golden panel is
built from `SYN001` and `SYN002` and the correction never touched them.

## The fail-closed guard, again

On all 120 rows: `capacity_basis = placeholder`, `service_check = service_capacity_unknown`,
both managed strategies `skipped_no_capacity_defined`, and the placeholder banner present.
The guard fires on real MATLAB. Under GNU Octave 11.3.0 the same guard does **not** fire
(FIND-MATLAB-09), which is why Octave is a syntax and smoke tier that may never be used to
make a feasibility statement.

## Still not claimed

The Simulink model was **built**. It was **not simulated**, and no result anywhere derives
from it. The docstring's own framing stands: this layer is illustrative, not load-bearing —
every metric comes from the base-MATLAB pipeline, which runs without Simulink at all.
