"""Produce the tracked ``data/contract/v3/`` from a new run of the model (DEC-027).

v2 is derived from the frozen v1 and cannot carry a model change (DEC-008). DEC-027 is a
model change: the canonical ``milestone2_v3`` plan follows the fixed-anchor ranking and the
V3 pathway rule, so the reference study's pathway is 47 where v1 and v2 hold the earlier
``legacy_v2`` figure, 48. Per DEC-008, new numbers go into a new run with its own contract
directory and its own ``model_version``. This script makes that run and writes it.

The run is the one ``fcf_m2.workflow.run`` makes; this script does not reimplement any of it.
It puts the run's scenario table into v2's container (``contract_v3.from_run``), applies field
observations exactly as v2 does (today there are none), and writes v3 with its own hash chain.
v1 and v2 are only read, to pin their digests and to describe what changed.

It also regenerates the MATLAB canonical input (``matlab/data/canonical/matlab_scenarios.csv``)
from the v3 rows through the one adapter (``fcf_m2.matlab_adapter``), so MATLAB reads the
authoritative contract and its rows name contract 3.0.0 and v3's run.

The data-confidence date is pinned (``AS_OF``) so the same sources give the same tables on any
day. A rebuild therefore differs from the tracked v3 only in ``run_id`` and ``generated_at``,
which is what ``--check`` ignores.

Usage::

    python scripts/build_contract_v3.py            # write data/contract/v3/
    python scripts/build_contract_v3.py --check    # verify the tracked v3 is current
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, contract, contract_v2, contract_v3, workflow  # noqa: E402
from fcf_m2.matlab_adapter import build_matlab_input  # noqa: E402

V1 = REPO / "data/contract/v1"
V2 = REPO / "data/contract/v2"
V3 = REPO / "data/contract/v3"
MATLAB_CSV = REPO / "matlab/data/canonical/matlab_scenarios.csv"

#: The date data confidence is judged on for this release: the date of DEC-027.
AS_OF = date(2026, 10, 18)

TABLES = ["schema.json", "scenario_table.csv", "site_table.csv", "source_provenance.csv",
          "standards_register.csv", "assumptions.json"]
#: The only scenario fields a rebuild may change: they name the run, not the result.
RUN_STAMP_FIELDS = ["run_id", "generated_at"]


def _observations():
    """The same observation loader v2 uses, not a second one."""
    spec = importlib.util.spec_from_file_location("build_contract_v2", REPO / "scripts/build_contract_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_real_observations()


def _totals(df: pd.DataFrame) -> tuple[int, int]:
    base = df[(df.horizon_year == config.BASELINE_YEAR) & (df.scenario_name == "baseline")]
    return int(base.ports_active.sum()), int(base.ports_pathway_capacity.sum())


def describe_changes(v2: pd.DataFrame, v3: pd.DataFrame) -> str:
    """Per-site account of what differs from v2, worked out from the two tables."""
    key = ["site_id", "horizon_year", "scenario_name"]
    a = v2.sort_values(key).set_index(key)
    b = v3.sort_values(key).set_index(key)
    lines = []
    for sid in sorted(set(a.index.get_level_values(0))):
        old, new = a.loc[sid], b.loc[sid]
        parts = []
        po = int(old.ports_pathway_capacity.iloc[0])
        pn = int(new.ports_pathway_capacity.iloc[0])
        if po != pn:
            parts.append(f"pathway {po} to {pn} ports")
        moved = old.ports_active != new.ports_active
        for (year, case) in moved[moved].index:
            parts.append(f"{year} {case} active {int(old.loc[(year, case), 'ports_active'])} to "
                         f"{int(new.loc[(year, case), 'ports_active'])}")
        if str(old.notes.iloc[0]) != str(new.notes.iloc[0]):
            parts.append(f'plan text now "{new.notes.iloc[0]}"')
        if parts:
            lines.append(f"- `{sid}`: " + "; ".join(parts) + ".")
    return "\n".join(lines) if lines else "- none"


def build(out_dir: Path, matlab_csv: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        result = workflow.run(config.MODE_V3, run_dir, as_of=AS_OF)
        if "cohort" in result:
            raise SystemExit("REFUSING: contract v3 is the reference study's; this run was a cohort")
        cdir = run_dir / "contract"
        run_manifest = json.loads((cdir / "contract_manifest.json").read_text())
        if not run_manifest.get("legacy_totals_checked"):
            raise SystemExit("REFUSING: the run was not held to the reference totals (RT-04)")
        scenario = pd.read_csv(cdir / "scenario_table.csv")
        site_table = pd.read_csv(cdir / "site_table.csv")
        provenance = pd.read_csv(cdir / "source_provenance.csv")
        standards = pd.read_csv(cdir / "standards_register.csv")
        assumptions = json.loads((cdir / "assumptions.json").read_text())
        planned = pd.read_csv(run_dir / "site_results_milestone2_v3.csv")

    scenario_v3 = contract_v3.from_run(scenario)
    upgrades, summaries, decisions = _observations()
    scenario_v3 = contract_v2.apply_observations(scenario_v3, upgrades, summaries, decisions)

    v2_rows = pd.read_csv(V2 / "scenario_table.csv")
    starter, pathway = _totals(scenario_v3)
    old_starter, old_pathway = _totals(v2_rows)
    totals = {
        "official": {"starter": starter, "pathway": pathway, "model_mode": config.MODE_V3,
                     "model_version": config.MODEL_VERSION},
        "earlier_legacy_v2": {
            "starter": old_starter, "pathway": old_pathway,
            "where": "data/contract/v1 and data/contract/v2 (model version "
                     f"{config.MODEL_VERSION_V1_V2}), and legacy_v2 mode",
            "status": "history; not the official figure since DEC-027"},
    }
    assumptions["contract_v3"] = {
        "derivation": f"a new run of model version {config.MODEL_VERSION} on the reference "
                      "study's inputs, put into contract v2's container; not derived from v1 or v2.",
        "plan": "the milestone2_v3 port plan follows the fixed-anchor ranking; the pathway is "
                "the V3 rule over the V3 2036/2046 targets (DEC-027).",
        "data_confidence_as_of": AS_OF.isoformat(),
        "observed_data": (
            f"{len(upgrades)} capacity observation set(s) and {len(summaries)} session "
            f"summary/summaries applied. Zero means no field data has been received; every "
            f"observed_* field is empty and every row reports awaiting_observed_data."),
        "empty_means": "An empty observed_* field means NOT OBSERVED. It never means zero.",
    }
    history = {
        "contract/v1/contract_manifest.json": contract.sha256_file(V1 / "contract_manifest.json"),
        "contract/v2/contract_manifest.json": contract.sha256_file(V2 / "contract_manifest.json"),
    }

    contract_v3.write_contract_v3(
        out_dir, scenario_v3, site_table, provenance, standards, assumptions,
        run_id=run_manifest["run_id"], inputs_hashed=run_manifest["inputs"],
        history=history, totals=totals, changes_md=describe_changes(v2_rows, scenario_v3))

    # The MATLAB input, from the v3 rows, with the plan's ranks (the same join workflow.run makes).
    meta = pd.read_csv(REPO / "data/inputs/legacy_matlab_site_meta.csv")
    site_meta = meta[["site_id", "arrival_start_hr", "arrival_end_hr", "base_load_mean_kw",
                      "base_load_peak_kw"]].merge(
        planned[["site_id", "model_rank", "electrical_risk_level"]], on="site_id")
    written = pd.read_csv(out_dir / "scenario_table.csv")
    build_matlab_input(written, site_meta, matlab_csv)
    return {"rows": len(scenario_v3), "fields": len(scenario_v3.columns),
            "starter": starter, "pathway": pathway,
            "earlier": (old_starter, old_pathway)}


def compare(fresh: Path, tracked: Path) -> list[str]:
    problems = []
    for name in TABLES:
        if name == "scenario_table.csv":
            a = pd.read_csv(fresh / name).drop(columns=RUN_STAMP_FIELDS)
            b = pd.read_csv(tracked / name).drop(columns=RUN_STAMP_FIELDS)
            if not a.equals(b):
                problems.append(f"{name}: tracked v3 differs from a fresh build "
                                f"(beyond {', '.join(RUN_STAMP_FIELDS)})")
        elif contract.sha256_file(fresh / name) != contract.sha256_file(tracked / name):
            problems.append(f"{name}: tracked v3 differs from a fresh build")
    if (fresh / "README.md").read_text() != (tracked / "README.md").read_text():
        problems.append("README.md: tracked v3 differs from a fresh build")
    problems += contract.verify_hash_chain(tracked)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="build into a temp dir and compare; do not write data/contract/v3")
    args = ap.parse_args()

    if args.check:
        if not V3.exists():
            print("contract v3 check FAILED:\n  - data/contract/v3/ is not present; run this "
                  "script without --check")
            return 1
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "v3"
            fresh_matlab = Path(tmp) / "matlab_scenarios.csv"
            build(fresh, fresh_matlab)
            problems = compare(fresh, V3)
            a = pd.read_csv(fresh_matlab).drop(columns=["source_note"])
            b = pd.read_csv(MATLAB_CSV).drop(columns=["source_note"])
            if not a.equals(b):
                problems.append("matlab/data/canonical/matlab_scenarios.csv differs from a fresh build")
            run_id = json.loads((V3 / "contract_manifest.json").read_text())["run_id"]
            notes = pd.read_csv(MATLAB_CSV)["source_note"]
            if not notes.str.contains(f"contract {config.SCHEMA_VERSION_V3} run {run_id}",
                                      regex=False).all():
                problems.append("matlab_scenarios.csv does not name contract v3's run")
        if problems:
            print("contract v3 check FAILED:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("contract v3 check PASSED: tracked v3 matches a fresh run of the model "
              "(run_id and generated_at aside), and its hash chain verifies")
        return 0

    if V3.exists():
        shutil.rmtree(V3)
    stats = build(V3, MATLAB_CSV)
    chain = contract.verify_hash_chain(V3)
    if chain:
        print("v3 hash chain failed:")
        for p in chain:
            print(f"  - {p}")
        return 1
    print(f"wrote {V3.relative_to(REPO)}/ and {MATLAB_CSV.relative_to(REPO)}")
    print(f"  {stats['rows']} rows, {stats['fields']} fields")
    print(f"  official totals: {stats['starter']} starter / {stats['pathway']} pathway")
    print(f"  earlier legacy_v2 totals (v1, v2): {stats['earlier'][0]} / {stats['earlier'][1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
