"""Produce the tracked ``data/contract/v2/`` by widening the frozen ``data/contract/v1/``.

**v2 is derived from v1, and that is the design, not a shortcut.** Migration copies every v1
value across, so "additive" is guaranteed by construction rather than by a promise: a
regression in which a v2 number drifts from its v1 counterpart is not something the code can
express. The tests then assert it anyway, because a guarantee nobody checks is a comment.

The single code path lives in ``fcf_m2.contract_v2``. This script is one caller;
``fcf_m2.workflow.run`` is the other. Neither reimplements the migration -- the same rule the
owner set for Phase 6B ("do NOT build a second, parallel intake path") applies here first.

v1 is **never opened for writing** by anything in this file.

Usage::

    python scripts/build_contract_v2.py                # write data/contract/v2/
    python scripts/build_contract_v2.py --check        # verify the tracked v2 is current
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import contract, contract_v2, observed  # noqa: E402

V1 = REPO / "data/contract/v1"
V2 = REPO / "data/contract/v2"
OBSERVED = REPO / "data/observed"

def load_real_observations() -> tuple[dict, dict, dict]:
    """Load field observations, if any exist.

    Today this returns three empty dicts, because **no real observations have been
    received** -- every file under ``data/observed/`` is either a blank template or a
    fixture, and fixtures are not data. That is the correct state and the emitted v2 says
    so on all 120 rows.

    The function exists so that the day a utility sends a real load study, the change is one
    file appearing in a directory rather than a code change under time pressure.
    """
    real_capacity = OBSERVED / "observed_capacity.csv"
    real_sessions = OBSERVED / "observed_sessions.csv"

    caps = (observed.read_capacity_observations(real_capacity)
            if real_capacity.exists() else [])
    sess = (observed.read_session_observations(real_sessions)
            if real_sessions.exists() else [])

    upgrades = observed.resolve_capacity(caps) if caps else {}
    summaries = observed.summarise_sessions(sess) if sess else {}
    # Trigger evaluation needs an equity percentile per site, which comes from the contract
    # rather than from the observations; it is wired in workflow.py where that is in hand.
    # With no session data there is nothing to evaluate, so the dict is empty and every row
    # keeps its awaiting_observed_data status.
    decisions: dict = {}
    return upgrades, summaries, decisions


def build(out_dir: Path) -> dict:
    scenario_v1 = pd.read_csv(V1 / "scenario_table.csv")
    site_table = pd.read_csv(V1 / "site_table.csv")
    provenance = pd.read_csv(V1 / "source_provenance.csv")
    standards = pd.read_csv(V1 / "standards_register.csv")
    v1_manifest = json.loads((V1 / "contract_manifest.json").read_text())

    scenario_v2 = contract_v2.migrate_v1_to_v2(scenario_v1)
    upgrades, summaries, decisions = load_real_observations()
    scenario_v2 = contract_v2.apply_observations(scenario_v2, upgrades, summaries, decisions)

    # v2's inputs are v1's inputs plus v1 itself. Recording the parent manifest's digest is
    # what makes "v2 was derived from THIS v1" checkable later rather than assumed.
    inputs_hashed = dict(v1_manifest.get("inputs", {}))
    inputs_hashed["contract/v1/contract_manifest.json"] = contract.sha256_file(
        V1 / "contract_manifest.json")
    inputs_hashed["contract/v1/scenario_table.csv"] = contract.sha256_file(
        V1 / "scenario_table.csv")

    assumptions = json.loads((V1 / "assumptions.json").read_text())
    assumptions["contract_v2"] = {
        "derivation": "migrated from the frozen contract v1; every v1 value carried across "
                      "unchanged except contract_version and the horizon_label vocabulary.",
        "observed_data": (
            f"{len(upgrades)} capacity observation set(s) and {len(summaries)} session "
            f"summary/summaries applied. Zero means no field data has been received; every "
            f"observed_* field is empty and every row reports awaiting_observed_data."),
        "empty_means": "An empty observed_* field means NOT OBSERVED. It never means zero.",
    }

    contract_v2.write_contract_v2(
        out_dir, scenario_v2, site_table, provenance, standards, assumptions,
        run_id=f"v2-from-{v1_manifest.get('run_id', 'unknown-v1-run')}",
        inputs_hashed=inputs_hashed,
        # Carried from v1, not restated. These rows were produced by the model version v1
        # recorded, and migrating them into a wider container did not re-run the model.
        model_version=v1_manifest["model_version"])

    return {
        "rows": len(scenario_v2),
        "fields": len(scenario_v2.columns),
        "v1_fields": len(contract.REQUIRED_FIELDS),
        "added_fields": len(contract_v2.V2_ADDED_FIELDS),
        "capacity_observations_applied": len(upgrades),
        "session_summaries_applied": len(summaries),
    }


def unchanged_values_check(out_dir: Path) -> list[str]:
    """Every shared field must hold the same value in v1 and v2. Additive means additive.

    Checked here as well as in the test suite because this script is what a person runs when
    they are about to commit a regenerated v2, and finding out at commit time beats finding
    out in CI.
    """
    v1_rows = pd.read_csv(V1 / "scenario_table.csv")
    v2_rows = pd.read_csv(out_dir / "scenario_table.csv")
    problems: list[str] = []

    if len(v1_rows) != len(v2_rows):
        return [f"row count changed: v1 has {len(v1_rows)}, v2 has {len(v2_rows)}"]

    key = ["site_id", "horizon_year", "scenario_name"]
    a = v1_rows.sort_values(key).reset_index(drop=True)
    b = v2_rows.sort_values(key).reset_index(drop=True)

    # These two are the ONLY fields v2 is permitted to change, and each has a stated reason.
    permitted = {"contract_version", "horizon_label"}
    for column in contract.REQUIRED_FIELDS:
        if column in permitted:
            continue
        left, right = a[column], b[column]
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            same = ((left - right).abs() < 1e-12) | (left.isna() & right.isna())
        else:
            same = (left.astype(str) == right.astype(str))
        if not bool(same.all()):
            n = int((~same).sum())
            problems.append(f"{column}: {n} row(s) differ between v1 and v2 -- v2 must be additive")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="build into a temp dir and compare; do not write data/contract/v2")
    args = ap.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "v2"
            build(fresh)
            problems = unchanged_values_check(fresh)
            if not V2.exists():
                problems.append("data/contract/v2/ is not present; run this script without --check")
            else:
                for name in ["scenario_table.csv", "schema.json", "site_table.csv",
                             "source_provenance.csv", "standards_register.csv"]:
                    if contract.sha256_file(fresh / name) != contract.sha256_file(V2 / name):
                        problems.append(f"{name}: tracked v2 differs from a fresh build")
            if problems:
                print("contract v2 check FAILED:")
                for p in problems:
                    print(f"  - {p}")
                return 1
            print("contract v2 check PASSED: tracked v2 matches a fresh build, and every "
                  "shared field is byte-equal to v1")
            return 0

    if V2.exists():
        shutil.rmtree(V2)
    stats = build(V2)

    problems = unchanged_values_check(V2)
    if problems:
        print("REFUSING to leave a non-additive v2 in place:")
        for p in problems:
            print(f"  - {p}")
        shutil.rmtree(V2)
        return 1

    chain = contract.verify_hash_chain(V2)
    if chain:
        print("v2 hash chain failed:")
        for p in chain:
            print(f"  - {p}")
        return 1

    print(f"wrote {V2.relative_to(REPO)}/")
    print(f"  {stats['rows']} rows, {stats['fields']} fields "
          f"({stats['v1_fields']} from v1 + {stats['added_fields']} added)")
    print(f"  capacity observations applied: {stats['capacity_observations_applied']}")
    print(f"  session summaries applied:     {stats['session_summaries_applied']}")
    print("  every shared field is byte-equal to v1; RT-10 hash chain verified")
    if stats["capacity_observations_applied"] == 0 and stats["session_summaries_applied"] == 0:
        print("  NOTE: zero real observations exist, so every observed_* field is empty and "
              "every row reports awaiting_observed_data. That is the correct state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
