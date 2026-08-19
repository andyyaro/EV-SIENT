"""Run the model under GNU Octave and diff it, cell by cell, against real MATLAB output.

Why this exists
---------------
``docs/operations/v4-program/MATLAB_LIBERATION.md`` states its own confidence in the Octave
tier as **MODERATE**, with the reason spelled out: the mechanical MATLAB→Octave transform is
audited and its numerics matched an independent NumPy reference, *"but 'moderate' is the
honest word until real MATLAB output exists to compare against."*

Real MATLAB output now exists - ``matlab/outputs/run-*/batch_results.csv``, produced by
MathWorks MATLAB R2025b Update 5 in CI. So the comparison that was owed can be made, and this
script makes it. Until now it could not be: the Octave tier had run against the **real**
canonical CSV while MATLAB ran the **synthetic** fixture, so there were no two runs of the
same input to compare.

**Every divergence is reported.** Not a pass/fail summary - the actual columns, the actual
rows, the actual magnitudes. A cross-validation that prints "OK" is worth nothing; the value
is entirely in what it finds, including finding nothing and saying which cells it checked.

What this can and cannot establish
----------------------------------
Agreement here means the transformed sources compute the same numbers as the MATLAB
originals **on this input**. It does not make Octave an equivalent engine. FIND-MATLAB-09
reproduced a case where the fail-closed capacity guard does **not** fire under Octave while it
does under MATLAB - a safety divergence that no numeric comparison would surface, because
both engines produce numbers, and one of them should have refused.

**GNU Octave is not MathWorks MATLAB. No output of this script may be presented as a MATLAB
result.**

Requirements
------------
* ``octave-cli`` on PATH (tested against GNU Octave 11.3.0)
* the Octave Packages ``datatypes`` package, which supplies ``table``/``string``/``datetime``.
  It is **not** vendored here: it is third-party, ~14 MB, compiles 9 C++ sources, and carries
  a ``NOASSERTION`` license field. Point ``--pkg-prefix`` at an existing install.

Usage::

    python scripts/octave_crossvalidate.py --pkg-prefix <dir> \\
        --matlab-results matlab/outputs/run-30296650057/batch_results.csv
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OCTAVE_DIR = REPO / "matlab/octave"
MATLAB_SRC = REPO / "matlab/src"
FIXTURE = REPO / "matlab/data/harness/harness_scenarios_synthetic.csv"

#: Columns that are expected to differ and why. Each is a run-identity or timestamp field,
#: never a computed quantity. Anything not on this list that differs is a real finding.
EXPECTED_TO_DIFFER = {
    "run_id": "batch run id, embeds the wall-clock time of the run",
    "placeholder_banner": "identical text; compared separately so a wording change is loud",
}

#: Below this, two floating-point results are the same number computed two ways. Above it,
#: they are two different answers. 1e-9 relative is far tighter than anything this model's
#: inputs justify, which is the point: the tolerance must not be able to hide a real gap.
RTOL = 1e-9


def build_octave_tree(work: Path) -> Path:
    """Transform ``matlab/src`` and ``matlab/tests`` into Octave-compatible sources.

    Invokes ``transform.py``'s own CLI rather than reaching into its internals, so the tier is
    reproduced by exactly the tool that produced the original evidence. That tool prints a
    per-rule audit and treats a rule that fired **zero** times as a FAILURE - a transform rule
    that stops matching is how a silent incompatibility creeps back in unnoticed.
    """
    dest = work / "xform"
    (dest / "src").mkdir(parents=True, exist_ok=True)
    (dest / "tests").mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(OCTAVE_DIR / "transform.py"), str(MATLAB_SRC.parent), str(dest)],
        capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stderr[-4000:])
        raise SystemExit("the MATLAB->Octave transform failed")
    if "RULES THAT FIRED ZERO TIMES" in result.stdout:
        raise SystemExit(
            "one or more transform rules matched nothing. Refusing to continue: a rule that "
            "stops firing means the sources changed shape underneath it, and the Octave run "
            "would be validating something other than what it claims to.")
    return dest / "src"


OCTAVE_DRIVER = """
more off;
pkg prefix {prefix} {arch};
pkg local_list {local_list};
pkg load datatypes;
addpath({shim});
addpath({src});
T = loadScenarios({csv});
outDir = run_all_scenarios('CsvFile', {csv}, 'OutputRoot', {outroot});
printf('OCTAVE_BATCH_DIR=%s\\n', outDir);
"""


def run_octave(work: Path, pkg_prefix: Path) -> tuple[Path, list[str]]:
    src = build_octave_tree(work)
    driver = work / "driver.m"
    driver.write_text(OCTAVE_DRIVER.format(
        prefix=f"'{pkg_prefix / 'prefix'}'",
        arch=f"'{pkg_prefix / 'arch'}'",
        local_list=f"'{pkg_prefix / 'octave_packages'}'",
        shim=f"'{OCTAVE_DIR / 'shim'}'",
        src=f"'{src}'",
        csv=f"'{FIXTURE}'",
        outroot=f"'{work / 'out'}'",
    ))
    # $FCF_SCENARIO_CSV is resolveScenarioCsv's documented first-choice override, and it is
    # used here rather than only passing 'CsvFile' because run_all_scenarios declares that
    # parameter as addParameter(p, "CsvFile", resolveScenarioCsv(), ...) -- an EAGER default,
    # so the resolver runs even when the caller supplies an explicit path. In a tree with no
    # default CSV that errors before the supplied path is ever consulted.
    env = {**os.environ, "FCF_SCENARIO_CSV": str(FIXTURE)}
    result = subprocess.run(["octave-cli", "--no-gui", str(driver)],
                            capture_output=True, text=True, cwd=work, env=env)

    # An Octave error is a RESULT, not a reason to abort. This script exists to find where
    # the two engines part company, and "Octave raises here and MATLAB does not" is the most
    # interesting kind of divergence there is -- exiting on it would throw away the finding.
    # The batch writes results.csv before the steps that can fail, so the numeric comparison
    # is usually still possible; both facts get reported.
    errors: list[str] = []
    if result.returncode != 0:
        detail = [ln for ln in result.stderr.splitlines() if ln.strip()]
        errors.append("octave-cli exited %d AFTER producing output. Octave stderr:\n      %s"
                      % (result.returncode, "\n      ".join(detail[-6:])))

    produced = sorted((work / "out").glob("batch_*/results.csv"))
    if not produced:
        sys.stdout.write(result.stdout[-3000:])
        sys.stderr.write(result.stderr[-4000:])
        raise SystemExit("octave produced no results.csv at all; nothing to compare")
    return produced[-1], errors


def compare(octave_csv: Path, matlab_csv: Path, runtime_errors: list[str]) -> int:
    o = pd.read_csv(octave_csv).sort_values("scenario_id").reset_index(drop=True)
    m = pd.read_csv(matlab_csv).sort_values("scenario_id").reset_index(drop=True)

    print(f"\noctave: {len(o)} rows x {len(o.columns)} cols   "
          f"matlab: {len(m)} rows x {len(m.columns)} cols")

    divergences: list[str] = list(runtime_errors)

    only_o = sorted(set(o.columns) - set(m.columns))
    only_m = sorted(set(m.columns) - set(o.columns))
    if only_o:
        divergences.append(f"columns present only in the Octave result: {only_o}")
    if only_m:
        divergences.append(f"columns present only in the MATLAB result: {only_m}")

    if list(o.scenario_id) != list(m.scenario_id):
        divergences.append("the two runs do not cover the same scenarios; nothing below is "
                           "comparable row by row")
        for line in divergences:
            print(f"  DIVERGENCE: {line}")
        return 1

    shared = [c for c in m.columns if c in o.columns and c not in EXPECTED_TO_DIFFER]
    checked_cells = 0
    for column in shared:
        left, right = o[column], m[column]
        if pd.api.types.is_numeric_dtype(right) and pd.api.types.is_numeric_dtype(left):
            both_nan = left.isna() & right.isna()
            close = pd.Series(False, index=left.index)
            valid = ~(left.isna() | right.isna())
            if valid.any():
                denom = right[valid].abs().where(right[valid].abs() > 0, 1.0)
                close[valid] = ((left[valid] - right[valid]).abs() / denom) <= RTOL
            same = both_nan | close
        else:
            same = left.astype(str) == right.astype(str)
        checked_cells += len(same)
        if not bool(same.all()):
            bad = o.index[~same]
            for i in bad[:5]:
                divergences.append(
                    f"{column} @ {m.scenario_id[i]}: octave={left[i]!r}  matlab={right[i]!r}")
            if len(bad) > 5:
                divergences.append(f"{column}: ...and {len(bad) - 5} further row(s)")

    print(f"compared {checked_cells} cells across {len(shared)} columns "
          f"(relative tolerance {RTOL:g})")
    for name, why in EXPECTED_TO_DIFFER.items():
        if name in o.columns and name in m.columns:
            identical = bool((o[name].astype(str) == m[name].astype(str)).all())
            print(f"  not compared - {name}: {why}"
                  f"{'  [text happens to be identical]' if identical else ''}")

    if divergences:
        print(f"\n{len(divergences)} DIVERGENCE(S) - every one is reported, none summarised away:")
        for line in divergences:
            print(f"  {line}")
        return 1

    print("\nNo divergence found in any compared cell, and Octave raised nothing.")
    print("This means the transformed sources compute the same numbers as the MATLAB")
    print("originals ON THIS INPUT. It does NOT make Octave an equivalent engine:")
    print("FIND-MATLAB-09 reproduced the fail-closed capacity guard NOT firing under Octave")
    print("while it does fire under MATLAB - a safety divergence no numeric comparison can")
    print("surface, because both engines produce numbers and one of them should have refused.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pkg-prefix", required=True, type=Path,
                    help="directory holding the Octave 'datatypes' package install "
                         "(expects prefix/, arch/ and octave_packages inside)")
    ap.add_argument("--matlab-results", required=True, type=Path,
                    help="a batch_results.csv produced by real MATLAB on the same fixture")
    ap.add_argument("--keep", action="store_true", help="keep the working directory")
    args = ap.parse_args()

    if shutil.which("octave-cli") is None:
        print("octave-cli not found on PATH. This script does not fall back to anything: a "
              "cross-validation that silently skips the engine it is validating is worse "
              "than no cross-validation.", file=sys.stderr)
        return 2
    if not args.matlab_results.is_file():
        print(f"no MATLAB results at {args.matlab_results}", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="fcf-octave-"))
    try:
        octave_csv, runtime_errors = run_octave(work, args.pkg_prefix)
        return compare(octave_csv, args.matlab_results, runtime_errors)
    finally:
        if args.keep:
            print(f"working directory kept at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
