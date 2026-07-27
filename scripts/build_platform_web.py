"""Generate the web tier's data files from the canonical contract.

The web tier computes nothing. It reads exactly two generated files, and this writes both:

* ``provenance_v1.json`` -- every displayed number's lineage
  (:func:`fcf_m2.provenance.export_all`)
* ``operations.json`` -- what the platform can do and which tier can do it
  (:func:`fcf_m2.operations.for_tier`)

Keeping the operations list generated rather than hand-written is the point: the registry is
the single definition, so the web tier cannot drift into offering a capability that does not
exist, or quietly omitting one that does.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import operations, provenance  # noqa: E402

OUT = REPO / "site/platform"
CONTRACT = REPO / "data/contract/v1"


def build(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = provenance.export_all(CONTRACT, out_dir / "provenance_v1.json")

    ops = {
        "tier": operations.TIER_BOTH,
        "tier_note": (
            "This is the web tier. It shows results and cannot execute anything. Every "
            "capability is listed, including the ones that need the desktop application, "
            "with the reason -- hiding one would make this page quietly less honest than "
            "the documentation."),
        "operations": operations.for_tier(operations.TIER_BOTH),
    }
    (out_dir / "operations.json").write_text(
        json.dumps(ops, indent=2, allow_nan=False) + "\n")

    return {"entries": len(payload["entries"]), "operations": len(ops["operations"])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the tracked files match a fresh build")
    args = ap.parse_args()

    if args.check:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp)
            build(fresh)
            problems = []
            for name in ["provenance_v1.json", "operations.json"]:
                tracked = OUT / name
                if not tracked.is_file():
                    problems.append(f"missing tracked {name}")
                elif (fresh / name).read_text() != tracked.read_text():
                    problems.append(f"{name} differs from a fresh build")
            if problems:
                print("platform web check FAILED:")
                for p in problems:
                    print(f"  - {p}")
                return 1
            print("platform web check PASSED: tracked data matches a fresh build")
            return 0

    stats = build(OUT)
    print(f"wrote {OUT.relative_to(REPO)}/provenance_v1.json  "
          f"({stats['entries']} entries)")
    print(f"wrote {OUT.relative_to(REPO)}/operations.json      "
          f"({stats['operations']} operations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
