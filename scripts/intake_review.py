#!/usr/bin/env python3
"""Show what intake would do with a supplied file. Changes nothing.

Why this is a command and not a function call
---------------------------------------------
The platform's operations registry declares commands, never Python callables, so that what the
platform runs is byte-identical to what a person would type. Intake is the one surface where
that matters most: a mapping proposal is a set of decisions about somebody's data, and a user
who cannot reproduce it from a terminal cannot audit it.

Why it is read-only
-------------------
This prints a proposal. It does not write a canonical frame, does not run the model, and does
not touch the contract. Applying a proposal is a separate, deliberate act - the whole design of
DEC-021 is that a human sees every finding *before* anything happens to their data.

    python scripts/intake_review.py data/intake/fixtures/messy_third_party.csv
    python scripts/intake_review.py <file> --json      # for the platform surface
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from fcf_m2 import confidence, intake  # noqa: E402


def review(path: Path) -> dict:
    frame = pd.read_csv(path)
    proposal = intake.propose(frame)

    payload = {
        "schema": "fcf-intake-review/1",
        "file": path.name,
        "rows": int(len(frame)),
        "supplied_columns": [str(c) for c in frame.columns],
        "refused": proposal.refused,
        "mapped": {k: str(v) for k, v in sorted(proposal.mapping.items())},
        "absent": sorted(proposal.absent),
        "conversions": {k: round(v, 6) for k, v in sorted(proposal.conversions.items())},
        "findings": [
            {"severity": f.severity, "field": f.field, "explain": f.explain, "detail": f.detail}
            for f in proposal.findings
        ],
        "inferred_count": sum(
            1 for canonical, column in proposal.mapping.items()
            if intake._strip_units(column) != intake._strip_units(canonical)),
    }

    # The confidence this file WOULD produce, shown before anyone commits to a run. Reporting
    # it afterwards would be reporting it too late to act on.
    if not proposal.refused:
        canonical_frame, ledger = intake.apply(frame, proposal)
        sites = [str(s) for s in canonical_frame["site_id"]]
        prov = intake.provenance_rows(proposal, sites, reviewer="intake_review",
                                      source_org=path.stem, source_date="unstated")
        as_ingested = confidence.build_confidence(prov, sites)
        accepted = confidence.build_confidence(intake.accept(prov), sites)
        payload["confidence"] = {
            "as_ingested": {
                "score": float(as_ingested["data_confidence_score_v3"].max()),
                "level": str(as_ingested["data_confidence_level_v3"].iloc[0]),
            },
            "if_mapping_accepted": {
                "score": float(accepted["data_confidence_score_v3"].max()),
                "level": str(accepted["data_confidence_level_v3"].iloc[0]),
            },
            # An undated source takes a 10-point staleness penalty by design: a source that
            # cannot be shown to be current is not treated as current. Stated here so the
            # reader is not left wondering why the number is lower than they expected.
            "undated_source_penalty": True,
            "note": ("This file declares no source date, which costs 10 points because a "
                     "source that cannot be shown to be current is not treated as current. "
                     "Accepting the mapping confirms that the columns mean what intake thinks "
                     "they mean. It does not confirm the data itself, so the source class does "
                     "not improve and the rating stays low until this jurisdiction supplies "
                     "provenance for its own figures."),
        }
        payload["ledger"] = [
            {"field": e.canonical_field, "action": e.action, "reason": e.reason,
             "detail": e.detail} for e in ledger
        ]
    return payload


def render(payload: dict) -> str:
    lines = [
        f"Intake review - {payload['file']} ({payload['rows']} rows, "
        f"{len(payload['supplied_columns'])} columns)",
        "",
    ]
    if payload["refused"]:
        lines.append("REFUSED. This file cannot be ingested:")
        for finding in payload["findings"]:
            if finding["severity"] == "refusal":
                lines.append(f"  - {finding['explain']}")
                if finding["detail"]:
                    lines.append(f"      {finding['detail']}")
        lines += ["", "Nothing was changed and no run was started."]
        return "\n".join(lines)

    lines.append(f"  {len(payload['mapped'])} field(s) mapped, "
                 f"{payload['inferred_count']} of them inferred from a column name")
    lines.append(f"  {len(payload['absent'])} field(s) absent: "
                 f"{', '.join(payload['absent']) or 'none'}")
    if payload["conversions"]:
        lines.append(f"  {len(payload['conversions'])} unit conversion(s) would be applied")

    confidence_block = payload.get("confidence")
    if confidence_block:
        lines += [
            "",
            "  Confidence this file would produce:",
            f"    as ingested         {confidence_block['as_ingested']['score']:>6}  "
            f"{confidence_block['as_ingested']['level']}",
            f"    if mapping accepted {confidence_block['if_mapping_accepted']['score']:>6}  "
            f"{confidence_block['if_mapping_accepted']['level']}",
        ]
        if confidence_block.get("undated_source_penalty"):
            lines.append("    (this file states no source date, which costs 10 points: a "
                         "source that")
            lines.append("     cannot be shown to be current is not treated as current)")

    by_severity: dict[str, list[dict]] = {}
    for finding in payload["findings"]:
        by_severity.setdefault(finding["severity"], []).append(finding)
    for severity in ("refusal", "warning", "note"):
        items = by_severity.get(severity, [])
        if not items:
            continue
        lines += ["", f"  {severity.upper()} ({len(items)}):"]
        for finding in items:
            lines.append(f"    - {finding['explain']}")

    lines += ["", "  Nothing has been changed. This is a proposal, not a run."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?",
                        default="data/intake/fixtures/messy_third_party.csv",
                        help="the CSV to review (defaults to the messy fixture)")
    parser.add_argument("--json", action="store_true", help="emit the machine-readable payload")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_absolute():
        path = REPO / path
    if not path.is_file():
        print(f"no such file: {args.file}")
        return 1

    payload = review(path)
    print(json.dumps(payload, indent=2) if args.json else render(payload))
    # A refusal is a legitimate outcome of a review, not a failure of the review.
    return 0


if __name__ == "__main__":
    sys.exit(main())
