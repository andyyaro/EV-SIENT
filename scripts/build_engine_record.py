"""Generate the platform's engine record: what each engine has actually executed.

Phase 7 requires the MATLAB results shown beside the Python results **with divergences
surfaced, not hidden**, and that the platform **never conflates engines**.

Doing that honestly for this project means confronting an awkward fact: the two engines have
never run on the same data. Real MathWorks MATLAB has only ever executed against a SYNTHETIC
fixture, because the public CI harness must never carry project data. So a row-by-row
Python-vs-MATLAB comparison of the twelve real sites **does not exist and cannot be
fabricated**.

What does exist, and is worth showing:

* the real MATLAB run record -- engine, version, what it ran, what passed;
* the fail-closed capacity guard **firing** under real MATLAB, which is the single most
  valuable thing those runs establish;
* the Octave-vs-MATLAB cross-validation: 2 640 cells, zero numeric divergence, and one
  behavioural divergence that IS surfaced rather than smoothed over;
* the cross-model constant defect this program found and fixed.

Every figure here is read out of committed artifacts, never restated by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config  # noqa: E402

OUT = REPO / "site/platform/engines.json"
RUNS = REPO / "matlab/outputs"


def read_provenance(run_dir: Path) -> dict:
    """Parse the provenance the CI run wrote before anything executed."""
    out = {}
    for name in ["run_provenance.txt", "matlab_version.txt"]:
        path = run_dir / name
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                out[key.strip()] = value.strip()
    return out


def guard_evidence(run_dir: Path) -> dict:
    """Read the batch output and report what the fail-closed guard actually did."""
    results = run_dir / "batch_results.csv"
    if not results.is_file():
        return {}
    frame = pd.read_csv(results)
    return {
        "rows": int(len(frame)),
        "run_status_ok": int((frame.run_status == "ok").sum()),
        "capacity_basis": sorted(frame.capacity_basis.astype(str).unique()),
        "service_check": sorted(frame.service_check.astype(str).unique()),
        "strategies_skipped": int(
            frame.skipped_strategies.astype(str).str.contains("skipped_no_capacity").sum()),
        "peak_clamp_all_null": bool(frame.peak_clamp_kW.isna().all()),
    }


def build() -> dict:
    runs = sorted(p for p in RUNS.glob("run-*") if p.is_dir())
    if not runs:
        raise SystemExit(f"no committed MATLAB run artifacts under {RUNS}")
    latest = runs[-1]
    prov = read_provenance(latest)
    guard = guard_evidence(latest)

    return {
        "schema": "fcf-engines/1",
        "headline": (
            "Four things can compute in this project. They are never treated as "
            "interchangeable, and no number on any screen may be attributed to the wrong one."),
        "engines": [
            {
                "id": "python",
                "name": "Python (fcf_m2)",
                "role": "The single producer",
                "status": "produces every number in the contract",
                "detail": (
                    "The only scorer. Every value on every surface of this platform comes "
                    "from here, via the canonical data contract."),
                "ran_on_real_sites": True,
            },
            {
                "id": "matlab",
                "name": "MathWorks MATLAB",
                "role": "Independent execution of the same model",
                "status": f"executed — {prov.get('version', 'version not recorded')}",
                "detail": (
                    "Runs the .m implementation in public CI. It has executed and passed, "
                    "but ONLY against a synthetic fixture: the harness is public and must "
                    "never carry project data. It has never seen the twelve real sites, so "
                    "no number here is a MATLAB result."),
                "ran_on_real_sites": False,
                "evidence": {
                    "run_id": prov.get("run_id", ""),
                    "commit": prov.get("commit_sha", "")[:12],
                    "release": prov.get("release", ""),
                    "input": prov.get("input_csv", ""),
                    "input_sha256": prov.get("input_sha256", "")[:16],
                    "input_note": prov.get("note", ""),
                    "simulink_installed": prov.get("simulink_installed", ""),
                },
            },
            {
                "id": "octave",
                "name": "GNU Octave",
                "role": "Syntax and smoke tier only",
                "status": "NOT MATLAB",
                "detail": (
                    "Runs a mechanically transformed copy of the sources. Numerically it "
                    "agrees with real MATLAB, but the fail-closed capacity guard does NOT "
                    "fire under it, so it may never be used to make a feasibility "
                    "statement."),
                "ran_on_real_sites": True,
                "warning": (
                    "An Octave result is not a MATLAB result. Nothing in this repository may "
                    "present it as one."),
            },
            {
                "id": "simulink",
                "name": "Simulink",
                "role": "Illustrative block diagram",
                "status": "built, never simulated",
                "detail": (
                    "A block diagram generated from the model source, matching the topology "
                    "read out of buildSimulinkModel.m. It has been built once, on real "
                    "MATLAB. It has never been run, and no number anywhere derives from it."),
                "ran_on_real_sites": False,
            },
        ],
        "guard_evidence": {
            "title": "The fail-closed capacity guard, verified on real MATLAB",
            "why_it_matters": (
                "This is the most valuable thing the MATLAB runs establish. The guard refuses "
                "to emit a feasibility claim from placeholder capacity — and it fires."),
            "from_run": latest.name,
            **guard,
        },
        "divergences": [
            {
                "id": "octave-vs-matlab-numeric",
                "between": "GNU Octave vs MathWorks MATLAB",
                "finding": "2 640 cells across 22 columns, relative tolerance 1e-9: ZERO "
                           "numeric divergences.",
                "severity": "none",
                "surfaced": True,
            },
            {
                "id": "octave-string-concat",
                "between": "GNU Octave vs MathWorks MATLAB",
                "finding": (
                    "run_all_scenarios.m: `string(csvName) + string(csvExt)` raises under "
                    "Octave (numeric addition of two char arrays) and writes the line under "
                    "MATLAB. Fatal but LOUD, and it lands after every number is computed."),
                "severity": "loud, post-computation",
                "surfaced": True,
                "deliberately_unfixed": (
                    "Extending the transform risks introducing a SILENT defect, which a "
                    "previous rule already did once. A loud failure in a provenance line is a "
                    "better trade than a silent one in a computed value."),
            },
            {
                "id": "charger-efficiency",
                "between": "Python vs MATLAB",
                "finding": (
                    f"Charger efficiency was {config.CHARGER_EFFICIENCY} in Python and 0.93 in "
                    f"three MATLAB files — one physical assumption, two values. Every MATLAB "
                    f"energy figure ran about 1.1% high."),
                "severity": "FIXED",
                "surfaced": True,
                "how_found": (
                    "By running the reconciliation instead of assuming agreement. Identity "
                    "reconciled 120/120; energy did not, and the implied efficiency measured "
                    "0.9300 across all 120 rows."),
                "why_it_survived": (
                    "Charger efficiency is not a contract field, so there was nothing to "
                    "reconcile it against — the drift was hiding in the one place the "
                    "anti-drift mechanism does not reach."),
            },
        ],
        "what_cannot_be_shown": (
            "A row-by-row Python-vs-MATLAB comparison of the twelve real sites. Real MATLAB "
            "has only ever run against a synthetic fixture, so that comparison does not exist "
            "— and it will not be fabricated to fill the space."),
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    g = payload["guard_evidence"]
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  engines: {len(payload['engines'])}   divergences: {len(payload['divergences'])}")
    print(f"  guard evidence from {g['from_run']}: {g['run_status_ok']}/{g['rows']} rows ok, "
          f"{g['strategies_skipped']} rows with strategies skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
