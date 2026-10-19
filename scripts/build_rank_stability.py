"""Write the score breakdown and rank-stability checks for the reference study's 12 sites as JSON.

The public site can embed this file so it shows the same numbers the planner app computes
(`fcf_m2.stability`, the method in docs/methodology/rank_stability.md). It runs the model the
way `workflow run --mode milestone2_v3` does, on the reference inputs, and passes the results
and the data-confidence table to `stability.analyse` with the planner app's own labels. No
input value or provenance record is written: only scores, contributions, ranks and ranges.

The output is deterministic for a given judging date (`--as-of`, which data confidence ages
inputs against); the default is the date recorded in the tracked file, so `--check` can tell
whether the tracked file is still what the engine produces.

Usage::

    python scripts/build_rank_stability.py                    # write the tracked JSON
    python scripts/build_rank_stability.py --as-of 2026-10-18 # judge confidence on another date
    python scripts/build_rank_stability.py --check            # fail if the tracked JSON is stale
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import stability, workflow  # noqa: E402
from fcf_m2.browser_api import DRIVER_LABELS, SUBSCORE_LABELS  # noqa: E402

OUT = REPO / "reports/rank-stability/rank_stability_reference_12_sites.json"
DEFAULT_AS_OF = "2026-10-18"


def build(as_of: date) -> dict:
    with tempfile.TemporaryDirectory(prefix="rank-stability-") as tmp:
        out = Path(tmp)
        # The engine prints its own run notes; keep stdout for this script's one line.
        with contextlib.redirect_stdout(sys.stderr):
            summary = workflow.run("milestone2_v3", out, as_of=as_of)
        results = pd.read_csv(out / "site_results_milestone2_v3.csv", dtype={"site_id": str})
        conf = pd.read_csv(out / "data_confidence_v3.csv", dtype={"site_id": str})
    confidence = stability.confidence_from_results(conf)
    analysis = stability.analyse(results, confidence, labels={**SUBSCORE_LABELS, **DRIVER_LABELS})
    return {
        "schema": "evsient-rank-stability/1",
        "what": ("Score breakdown and rank-stability checks for the reference study's sites, "
                 "fixed-anchor (milestone2_v3) scores. " + stability.METHOD_NOTE),
        "method": "docs/methodology/rank_stability.md",
        "mode": summary["mode"],
        "asOf": as_of.isoformat(),
        **analysis,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--as-of", default=None, help="YYYY-MM-DD data confidence is judged on")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="compare with the tracked file instead of writing")
    args = parser.parse_args()
    as_of = args.as_of
    if as_of is None and args.out.exists():
        as_of = json.loads(args.out.read_text()).get("asOf")
    payload = build(date.fromisoformat(as_of or DEFAULT_AS_OF))
    text = json.dumps(payload, indent=1, allow_nan=False) + "\n"
    if args.check:
        current = args.out.read_text() if args.out.exists() else ""
        if current != text:
            print(f"{args.out.relative_to(REPO)} is out of date. Run scripts/build_rank_stability.py.")
            return 1
        print(f"{args.out.relative_to(REPO)} is current.")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    first = payload["sites"][0]
    print(f"Wrote {args.out.relative_to(REPO)}: {len(payload['sites'])} sites; {first['name']} first "
          f"in {first['stability']['pFirst']:.0%} of {payload['rankStability']['draws']} weightings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
