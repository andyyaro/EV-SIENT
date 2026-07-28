# MATLAB_LIBERATION.md

Phase 2 of the V4 platform program: getting the MATLAB layer executed, and getting it to run on a
machine with no MATLAB licence.

**Standing rule for this whole document: no result is attributed to an engine that did not produce it.**
`GNU Octave 11.3.0` is not `MathWorks MATLAB R2025b`. Where something has not been run, it says so.

---

## 1. Where this started

`matlab/EXECUTION_STATUS.md` is unambiguous, and Phase 0 confirmed every line of it against the tree:

- 17 `.m` files — 9 in `src/`, 6 in `tests/`, 2 in `legacy_archive/`. **Not one line had ever been executed.**
- `tests/golden/regression_golden.csv` does not exist, because only a real run can create it.
- `matlab/outputs/` is empty by design.
- `.github/workflows/matlab-manual.yml` is a definition that has never run anywhere.

**That was the starting position. It is no longer entirely true — see §4.2:** real MathWorks MATLAB R2025b
has now executed this code. What has *not* changed is the record: `EXECUTION_STATUS.md` is untouched and
stays untouched until a run **passes**. A run that happened and failed is not a run record; it is a finding,
and it is written up in §4.2 rather than smuggled into a status document as progress.

---

## 2. The exposure review, and the adversarial review that overturned it

The program requires the exposure review to be written down **before** any repository goes public. It also
requires every subagent finding to be treated as a lead until independently confirmed. Both mattered here,
because the first review and its adversarial counter-review reached **opposite conclusions**.

### 2.1 First review — *conditional yes*

A field-by-field pass over all 22 columns of `matlab/data/canonical/matlab_scenarios.csv` concluded that a
public harness is possible **only on a synthetic scenario file**, never on the real one, redacted or
otherwise. Synthesis beats redaction because a redacted real file still leaks by column co-occurrence.

Its column classification stands and is genuinely useful. Highlights:

| Column | Class | Why |
|---|---|---|
| `site_id`, `scenario_id`, `site_name` | **IDENTITY** | `site_id` is the join key into a site→facility mapping that is *already public* in the predecessor repo |
| `model_rank`, `electrical_risk_level` | **FINDING** | rankings and risk verdicts are study conclusions |
| `capacity_basis` | **INPUT_SAFE** | `placeholder` on all 120 rows — a disclosure of what is *not* known, and the single most valuable thing to publish as methodology |
| `spare_capacity_kW`, `service_capacity_kW` | **INPUT_SAFE** | empty on all 120 rows; their emptiness is what triggers the fail-closed guard |
| `horizon_year`, `case`, `charger_power_kW` | **INPUT_SAFE** | modelling axes and a generic Level-2 equipment class |
| `base_load_mean_kW`, `base_load_peak_kW`, `ports` | **BORDERLINE** | per-facility characterisations; synthesise, it costs nothing |

It also found a useful structural fact: `loadScenarios.m` requires only 19 of the 22 columns, and the three
optional ones are exactly the three worst offenders — so two FINDING columns can be dropped with zero code
change.

### 2.2 Adversarial review — **NOT SAFE**, and it was right

A second agent tasked with *refuting* the first returned `NOT_SAFE` with specific, reproducible evidence.
The lead re-verified every load-bearing claim before acting. All of them held.

**The first review's central safety assertion was false.** It stated that "the entire real-identity surface
in `src/` + `tests/` is six code lines and one comment, all `FFX002`/`PWC001`". It is not:

| Leak | Verified how |
|---|---|
| `matlab/tests/test_profiles.m:77` — `sessions_per_day = 1.16`, commented **"a real adapter value"** | `1.16` is FFX002's real 2026 baseline value in the canonical CSV |
| `matlab/tests/test_capacityGuard.m:92,101,127` — `spare_capacity_kW = 153.6` | a real per-site value |

Both files were on the first review's *safe to publish, unmodified* list.

**And the leak gate it proposed provably could not catch them.** The proposed gate fails the build on
`FFX[0-9]{3}|PWC[0-9]{3}` or real site-name fragments. Run against the two offending files, that regex
returns **no match**. A string gate cannot see `1.16`.

Other confirmed findings:

- **`plotScenario.m` hardcoded a false provenance.** Its mandatory footer asserted
  `Source: data/canonical/matlab_scenarios.csv` regardless of what was actually read, so every figure from
  a synthetic harness run would have carried a fabricated citation — inside the file whose entire purpose
  is provenance labelling.
- **`run_all_scenarios.m` leaked the absolute local path** into `manifest.txt`, and wrote the **SHA-256 of
  the input CSV** into `hashes.txt`. That hash is a confirmation oracle: anyone holding a candidate
  reconstruction of the private input can test it for an exact match.
- **`energy_requested_kWh` inverts exactly to `sessions_per_day`** through the charger efficiency, so
  publishing the output publishes the input.
- **The golden-file hazard was stated backwards.** The real risk is not the harness golden travelling back;
  it is the *private, real* golden travelling **forward** into the public repo, since both trees use the
  identical relative path `tests/golden/regression_golden.csv`.
- The first review mis-stated `sessions_per_day`'s range as 0.3–9.719; it is **0.3–15.73**.
- Its delivered output was **truncated**, so its must-not-publish list was unauditable as delivered.

**Decision: the public repository was not created on the first review's basis.** The approval to proceed had
been given on a summary of the first review; the refuting evidence arrived afterwards and changed the answer,
so it was reported before acting rather than after.

### 2.3 What was fixed, in the private repository

Fixed at source, so the harness inherits clean files rather than being patched downstream:

| Fix | File |
|---|---|
| `sessions_per_day = 1.16` → `1.75` (verified absent from the real data) | `matlab/tests/test_profiles.m` |
| `spare_capacity_kW = 153.6` → `120.0` (verified absent) | `matlab/tests/test_capacityGuard.m` |
| Footer reports the **actual** input file; a `SourceFile` option is threaded from `run_all_scenarios` | `matlab/src/plotScenario.m` |
| Manifest and hashes record file **names**, not absolute paths | `matlab/src/run_all_scenarios.m` |
| Site ids **read from the data**, never named — the same ML-06 discipline already applied to horizons | `test_horizons.m`, `test_loadScenarios.m`, `test_regression.m` |

Re-ran the static checks `EXECUTION_STATUS.md` documents against all 15 files afterwards: block-keyword
balance, bracket balance, function-name match, no tabs, ASCII-only — **all 15 PASS**, matching the recorded
result, so the edits preserved structure. (The first attempt at that checker reported six false failures
because it stripped `%` comments before string literals, eating `sprintf` format specifiers. The checker was
wrong, not the files.)

> **Note on the golden panel.** `test_regression.m`'s panel was `["FFX002", "PWC001"]`; it is now "the first
> two site ids in sorted order", which resolves to `FFX001` and `FFX002`. **This changes what the golden
> file will contain.** It is safe to do precisely because the golden has never been generated — there is no
> baseline to invalidate. Doing it later would have required a deliberate regeneration.

### 2.4 The leak gate that replaced the one that did not work

`scripts/check_harness_exposure.py`. The principle it encodes came out of the evidence:

> **A value identifies a site only if it varies between sites.**

`charger_power_kW = 19.2` and `energy_per_session_kWh = 9.5` are real values, but all 12 sites share them —
they are modelling constants and a fixture may use them freely. `sessions_per_day` takes 120 distinct values
and `base_load_mean_kW` takes 8: those identify. The gate reads the canonical CSV, derives which columns
actually discriminate, and fails on those values.

Matching on the value alone produced false positives — `0.90` is a real `sessions_per_day` value *and* an
RGB component *and* a textbox width. So the gate requires the discriminating value **and** the name of a
column it belongs to on the same line, which is exactly the shape of a real leak (`row.sessions_per_day = 1.16`)
and not the shape of a colour array.

Current state: **clean — 18 files scanned, 134 site-discriminating values gated.** Mutation-tested by
reinstating both original leaks; the gate catches both.

---

## 3. The in-app runtime tier — Tier 2, established by execution

**Recommendation: Tier 2 — GNU Octave plus a tested compatibility layer.** Not asserted; run.

### 3.1 Tier 1 is not merely unreachable, it is unsafe

`capacityGuard.m:53` declares its controlled vocabulary as a bracketed string-array literal. Under Octave
that is **one 1×85 `char` row**, not a 6-element string array. So `ismember` returns a **per-character
logical vector**, and the fail-closed gate at line 89:

```matlab
if mode == "feasibility" && ~isVerified
```

**does not fire.** Reproduced directly. An unmodified Octave run would emit a feasibility claim from
placeholder capacity, silently, with no error — and all 12 sites carry `capacity_basis = placeholder`, so
that is every row, not a corner case. The out-of-vocabulary check is defeated the same way:
`confirmed_totally` passes.

A run that produces plausible numbers is the worst available outcome here. Tier 1 is ruled out on safety,
not just capability.

### 3.2 The `datatypes` package: it exists, it installs, it does not solve it

Octave's own error messages point at an Octave Packages `datatypes` package. It was evaluated rather than
assumed: version 1.2.7, published **six days** before this evaluation, single maintainer, 8 stars, license
field `NOASSERTION`, requires Octave ≥ 11.1.0, compiles 9 C++ sources so it needs a working toolchain.
Install succeeded in 17.4 s.

It supplies `string`, `datetime` and `table` — but as classdef objects that **base Octave functions reject**:
`sprintf`/`fprintf`/`error` raise *"wrong type argument object"*, and `str2double(string('153.6'))` silently
returns `NaN`. Its `readtable` also silently renames the CSV column `case` to `xCase`, violating the
`"VariableNamingRule","preserve"` contract `loadScenarios.m` depends on.

**Verdict: useful for `table` and `datetime`, but its `string` class must not be relied on.** The
compatibility layer normalises to char/cellstr instead.

### 3.3 What actually executed

Against the real `matlab_scenarios.csv`, GNU Octave 11.3.0 + `datatypes` 1.2.7 + a 15-rule mechanical source
transform + a 16-function shim ran the **full pipeline**:

`loadScenarios` (120 × 22) → `capacityGuard` → `makeSessionProfiles` → `managedCharging`
(unmanaged / clamp / energy_aware) → `electricalEconomics` → `runScenario` → `run_all_scenarios` over all
120 rows, writing `results.csv`, `manifest.txt` and `hashes.txt`.

- All 120 rows: `run_status=ok`, `capacity_basis=placeholder`, `capacity_verified=0`, non-empty
  `placeholder_banner`, `skipped_strategies=none`.
- **Deterministic**: two consecutive 120-row batches differed in zero cells.
- The pure-Octave SHA-256 shim reproduces the correct digest for the input CSV, matching `shasum -a 256`.

**This is an Octave result. It is not a MathWorks MATLAB result, and nothing in this repository may present
it as one.** Cross-validation against real MATLAB is still owed and happens when the harness CI runs.

### 3.4 The silent failure modes, which are the point

Ranked by danger — the loud ones are safe because you find out:

| Construct | Occurrences | Severity | Why it matters |
|---|---|---|---|
| `["a","b"]` collapsing to one char row | 20 | **fatal_silent** | root cause of the gate bypass |
| the fail-closed gate itself | 3 | **fatal_silent** | emits feasibility from placeholder capacity |
| `X == "literal"` elementwise | 10 | **fatal_silent** | per-character vector reaching an `if` |
| `for x = ["a","b"]` | 4 | **fatal_silent** | iterates per character — a 2-site loop ran **12** times |
| `version("-release")` returns empty | 1 | **fatal_silent** | writes a blank `matlab_release:` line — provenance silently lost |
| `struct("f", cellArray)` → struct array | 20 | **fatal_silent** | **introduced by the transform itself** |
| `"abc " + "def"` numeric addition | 62 | fatal_loud | 37 of 38 literal pairs error; **one pair has equal lengths and silently yields a double vector** |
| `string()` via the package | 84 | **fatal_silent** | `str2double` returns `NaN` |
| MATLAB unittest framework | 183 | fatal_loud | the whole test layer cannot execute under Octave |
| `java.security.MessageDigest` | 3 | fatal_loud | `usejava("jvm")` returns 0 |
| Simulink API | 41 | fatal_loud | **no fix needed** — `buildSimulinkModel`'s own guard fires correctly and emits its designed message |

The transform-induced bug deserves emphasis: rule R3 (string arrays → cellstr) *created* a new silent defect,
because `struct("f", cellArray)` expands into a struct array. A mechanical transform is not automatically
faithful, which is why the guard proof below is mandatory rather than advisory.

### 3.5 The mandatory safety gate

`guardproof.m` — 16 assertions across 7 groups, **16/16 passing on transformed sources, with a negative
control proving the suite fails on untransformed sources rather than passing vacuously.** It asserts the
error *identifier*, not merely that something threw, because the untransformed run also throws — with an
empty identifier, for an unrelated reason.

**No Octave result may be trusted, and no Octave path may ship, unless this gate passes.**

### 3.6 Confidence, stated honestly

- **HIGH** that Tier 2 runs the real code end to end — executed, 120 rows, deterministic, twice.
- **HIGH** that the fail-closed guard fires under Tier 2 — 16/16 with a negative control.
- **HIGH** that Tier 1 is impossible — bypass reproduced directly, with and without the package.
- **~~MODERATE~~ → HIGH** that the transformed sources are semantically faithful to the MATLAB originals,
  **on this input**. Superseded 2026-07-27 by the cross-validation below. The original wording is kept
  because the upgrade is only meaningful next to what it replaced.

That last line is the whole reason the harness CI matters.

---

## 3.7 The cross-validation, run

Owed since 3.6 was written, and now possible for the first time: previously the Octave tier had run against
the **real** canonical CSV while MATLAB ran the **synthetic** fixture, so there were never two runs of the
same input to compare.

**Reproduce it:** `python scripts/octave_crossvalidate.py --pkg-prefix <dir> --matlab-results
matlab/outputs/run-30296650057/batch_results.csv`

| | |
|---|---|
| Octave | GNU Octave 11.3.0 + `datatypes` 1.2.7 + the 15-rule transform + the 17-function shim |
| MATLAB | MathWorks MATLAB 25.2.0.3177638 (R2025b) Update 5, CI run `30296650057` |
| Input | `harness_scenarios_synthetic.csv`, the same file, same SHA-256, both engines |
| Compared | **2 640 cells across 22 columns**, relative tolerance **1e-9** |

### Numeric divergences: **zero**

Not one cell of the 2 640 differs beyond 1e-9 relative. Every computed quantity — energy requested, peak
unmanaged, the managed-strategy outputs, the economics columns, the guard fields — agrees between GNU
Octave and MathWorks MATLAB. The transform is faithful on this input, and that is now measured rather than
argued. All 15 transform rules fired; the transform treats a rule that fires **zero** times as a failure,
because a rule that stops matching means the sources moved underneath it.

Two columns are excluded by name and the exclusions are printed on every run: `run_id`, which embeds the
wall-clock time, and `placeholder_banner`, compared separately so a wording change would be loud rather
than absorbed. The banner text is byte-identical between the engines.

### Behavioural divergence: **one, and it is loud**

    run_all_scenarios.m:135
    fprintf(fid, "input_csv: %s\n", string(csvName) + string(csvExt));

    Octave: error: operator +: nonconformant arguments (op1 is 1x27, op2 is 1x4)
    MATLAB: writes "input_csv: harness_scenarios_synthetic.csv"

This is the `"abc " + "def"` failure mode catalogued in 3.4, reaching a pair the transform does not cover:
R2 rewrites `literal + expr` and `expr + literal`, and this is `expr + expr`. Under Octave's shim both
operands are char arrays, so `+` is numeric addition and the lengths (27 and 4) do not conform.

**Severity: fatal_loud, and it lands after every number is computed.** `results.csv` is already written when
it fires; only the manifest's `input_csv` line and `hashes.txt` are lost. It cannot corrupt a value.

**Deliberately not fixed, and the reasoning is the point.** Extending the transform to cover
`fcf_str(a) + fcf_str(b)` is a dozen lines. It is not being done because §3.4 records that rule R3 *created*
a new silent defect — `struct("f", cellArray)` expanding into a struct array — while removing a loud one.
Trading a loud failure in a provenance line for the risk of a silent one in a computed value is a bad trade
in a repository whose entire premise is that a wrong number is worse than no number. The divergence is
recorded here with its exact location, and `octave_crossvalidate.py` reports it on every run rather than
tolerating it.

### What this does and does not establish

**Does:** the transformed sources compute the same numbers as the MATLAB originals on this input, to 1e-9.

**Does not:** make Octave an equivalent engine. FIND-MATLAB-09 reproduced the fail-closed capacity guard
**not firing** under Octave while it **does** fire under real MATLAB — verified in run `30296650057`, where
all 120 rows carry `service_capacity_unknown` and both managed strategies report
`skipped_no_capacity_defined`. No numeric comparison can surface a divergence of that kind, because both
engines produce numbers and one of them should have refused. **GNU Octave remains a syntax and smoke tier
that may never be used to make a feasibility statement.**

---

## 4. The harness repository, and the first real MATLAB execution

**`https://github.com/andyyaro/fcf-matlab-ci` — public, created 2026-07-27.** Nine model sources, six
test files, one synthetic fixture, a CI workflow, a README, and a `.gitignore`. No licence, matching
upstream. Created only after §2 was written down and every leak in it was closed.

### 4.1 One-directional sync

`scripts/sync_matlab_harness.py`. `--check` fails if any published file differs from its private source
**and** fails if the harness holds a file the sync does not publish, because an extra file is how a
hand-edit arrives. `--push` copies private → public and writes `SYNC_MANIFEST.json` with the source commit
and a SHA-256 per file. There is **no reverse mode**. Every file passes the exposure gate before it can be
copied, so the gate cannot be bypassed by going around it.

Exercised in both directions on the live harness: `--check` correctly reported five divergences after a
fix landed privately, `--push` resolved them, `--check` then reported all 17 files hash-identical.

### 4.2 The runs — **the code executed, and it failed, which is the valuable part**

`MathWorks MATLAB R2025b`, harness run **#1**. **35 passed, 14 failed, 11 incomplete.**

Every one of the 14 failures had a single cause, and none reached any model logic:

```
Error using loadScenarios (line 50)
Canonical scenario CSV not found:
  /home/runner/work/fcf-matlab-ci/fcf-matlab-ci/data/canonical/matlab_scenarios.csv
```

The sources hard-coded the canonical adapter path. That file exists privately, where the Python producer
generates it, and deliberately does not exist in the harness, which carries a synthetic fixture. So the
sources were not portable between the two trees — a defect that could only ever have been found by running
them somewhere other than where they were written.

**Fixed upstream, not in the harness.** `matlab/src/resolveScenarioCsv.m` checks `$FCF_SCENARIO_CSV`, then
the canonical CSV, then the harness fixture. The real file wins when both exist, so the private repository
can never silently test against synthetic data. Patching the harness copy instead would have been exactly
the divergence the sync exists to prevent.

**What run #1 established, which was not known before:** 35 tests passed on real MathWorks MATLAB. Until
that moment nobody could say whether these files were even syntactically acceptable to the MATLAB parser —
`EXECUTION_STATUS.md` records that not one line had ever been executed. They parse, and most of the suite
passes.

### 4.3 Runs #2 and #3 — a defect in the loader, and a wrong guess corrected

Run #2 failed differently: **every required column reported missing**. That is not a content problem — it
means `readtable` returned variable names bearing no relation to the header.

I formed a hypothesis (the generator wrote CRLF where the Python producer writes LF) and **could not test it**:
Octave has no `detectImportOptions`, so MATLAB's parsing cannot be reproduced locally. Rather than guess
across CI round trips, run #3 shipped the LF fix *together with a diagnostic step* that printed what MATLAB
itself sees.

**The diagnostic showed the hypothesis was wrong**, which is precisely why it was worth adding:

```
has CR: 0                      <- line endings were NOT the cause
detected 51 variables          <- should be 22
VariableNamesLine: 2           <- should be 1
table: 119 rows x 51 vars      <- should be 120 x 22
```

`detectImportOptions` **guessed the delimiter, and guessed wrong.** The first data row carries more spaces
(50) than commas (21) because of its free-text columns, so MATLAB concluded the delimiter was whitespace,
took line 2 as the header, and lost a row. `loadScenarios` then reported every required column missing —
a confusing way to be told the file was never parsed as a CSV at all.

**FIND-MATLAB-10 (high) — the loader did not say what it was loading.** `loadScenarios.m` specified no
delimiter, no header line and no data-line range, relying entirely on detection for a file whose format is
known exactly: the Python producer writes comma-separated data with a header on line 1. All three are now
stated explicitly.

**This is a latent defect in the model code, not a property of the synthetic fixture.** The canonical file
carries 35 spaces against 21 commas on its first data row, so it is exposed to the same misdetection. It
simply had never been executed against, by anything.

### 4.4 What three runs bought

| Run | Outcome | Defect found |
|---|---|---|
| #1 | 35 pass / 14 fail | Hardcoded canonical CSV path — the sources were not portable between the two trees |
| #2 | 35 pass / 14 fail | Every column "missing" — surfaced the loader problem without explaining it |
| #3 | 35 pass / 14 fail | **Diagnostic identified the cause**: delimiter auto-detection picking whitespace |

Three real defects in three runs, none of which static review had caught in the months this code sat in the
repository — and one of them (`plotScenario`'s fabricated provenance footer) was found by the adversarial
exposure review rather than by execution. That is the argument for this phase, stated in outcomes rather
than in principle.

## 5. Status

| Item | State |
|---|---|
| Exposure review, field by field | **done** — and overturned by adversarial review, and re-done |
| Leaks found and fixed at source | **done** — 5 fixes, each verified |
| Automated leak gate | **done** — mutation-tested; a `verify.sh` gate |
| Public harness repository | **live** — `andyyaro/fcf-matlab-ci` |
| One-directional hash-gated sync | **done** — exercised in both directions |
| Runtime tier chosen with evidence | **done** — Tier 2, by execution, 120/120 rows |
| Fail-closed guard proof | **done** — 16/16 with a negative control |
| **Real MathWorks MATLAB executed** | **YES — 49 passed / 0 failed** on R2025b Update 5 (run #1 was 35/14/11; the defect below was fixed and it was re-run) |
| First-run defect found and fixed | **done** — non-portable CSV path |
| CI run fully green | **done** |
| `regression_golden.csv` generated | **done** — committed under `matlab/outputs/run-30291108647/` |
| `.slx` built by CI | **done** — `run-30296650057`, 11 blocks; **built, never simulated** |
| `EXECUTION_STATUS.md` updated | **done** — the BLOCKED banner is kept verbatim below the new one rather than deleted |
| Python/MATLAB cross-validation | **done** — 2 640 cells, **zero** numeric divergences at 1e-9 (under Octave; see the tier note) |

> **Corrected 2026-07-28.** Every row above except the first two read "not yet" or "no" long
> after each had been completed. Found by the DEC-014 line-by-line audit. A status table that
> under-reports is still a status table that lies.
