"""Extract the Simulink model's topology from the committed .slx, for the platform to render.

Why extract rather than screenshot
----------------------------------
A picture of a block diagram is an assertion. The topology read out of the file is checkable:
it comes from the same ``.slx`` that real MathWorks MATLAB produced, and it can be compared
against the source that generated it. So the platform renders the STRUCTURE, from the file.

What this may and may not claim
-------------------------------
The model was **built** and has **never been simulated**. No number in this project derives
from it, and its own docstring says the layer is illustrative rather than load-bearing. Those
two facts travel with the topology, because a block diagram is exactly the kind of artifact a
reader assumes produced something.

Connection counts are deliberately NOT claimed equal to the source. ``buildSimulinkModel.m``
calls ``add_line`` 15 times; the saved file stores 8 ``<Line>`` elements with 12 ``<Branch>``
elements at root plus 4 lines in the subsystem, because Simulink stores one line per source
port and represents fan-out as branches. Those are different encodings of the same graph, and
asserting they are equal without checking the graph itself would be a claim beyond the
evidence.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "site/platform/simulink.json"


def find_slx(allow_missing: bool = False) -> Path | None:
    """The newest committed .slx, or None when this installation has none.

    Returning None rather than raising is the change a public installer forced, and the
    distinction it preserves is the important one: the view must still be built **from a real
    artifact, never from a description of one**. What changed is only what happens when there
    is no artifact at all — previously the build died, which on a public install killed the
    launcher three steps into a first run. Now the surface is emitted empty and says the model
    was never distributed with one.
    """
    candidates = sorted(REPO.glob("matlab/outputs/run-*/simulink/*.slx"))
    if candidates:
        return candidates[-1]
    if not allow_missing:
        # The DEFAULT stays a refusal. In this repository a missing .slx means a broken
        # checkout, and the guard exists so the view can never be generated from a description
        # of an artifact instead of the artifact.
        raise SystemExit(
            "no committed .slx found under matlab/outputs/run-*/simulink/. The Simulink view "
            "must be built from a real CI artifact, never from a description of one.")
    return None


def extract(slx: Path) -> dict:
    with zipfile.ZipFile(slx) as z:
        names = z.namelist()
        systems = {}
        for entry in names:
            if not re.match(r"simulink/systems/system_.*\.xml$", entry):
                continue
            text = z.read(entry).decode("utf-8", "replace")
            blocks = re.findall(r'<Block\s+BlockType="([^"]+)"\s+Name="([^"]+)"', text)
            systems[entry.split("/")[-1]] = {
                "blocks": [{"type": t, "name": n.strip()} for t, n in blocks],
                "lines": len(re.findall(r"<Line\b", text)),
                "branches": len(re.findall(r"<Branch\b", text)),
            }

        release = ""
        if "metadata/mwcorePropertiesReleaseInfo.xml" in names:
            meta = z.read("metadata/mwcorePropertiesReleaseInfo.xml").decode("utf-8", "replace")
            v = re.search(r"<version>([^<]+)</version>", meta)
            r = re.search(r"<release>([^<]+)</release>", meta)
            d = re.search(r"<description>([^<]+)</description>", meta)
            release = " ".join(x.group(1) for x in (v, r, d) if x)

    root = systems.get("system_root.xml", {"blocks": [], "lines": 0, "branches": 0})
    sub = {k: v for k, v in systems.items() if k != "system_root.xml"}

    return {
        "schema": "fcf-simulink/1",
        "model": slx.stem,
        "from_run": slx.parent.parent.name,
        "built_by": release or "release info not recorded in the package",
        "status": "BUILT, NEVER SIMULATED",
        "status_detail": (
            "This diagram was generated from the model source and opened once by real "
            "MathWorks MATLAB. It has never been run. No number anywhere in this project "
            "derives from it — every metric comes from the base pipeline, which needs no "
            "Simulink at all."),
        "root": {
            "blocks": root["blocks"],
            "block_count": len(root["blocks"]),
            "line_elements": root["lines"],
            "branch_elements": root["branches"],
        },
        "subsystems": {
            name: {"block_count": len(s["blocks"]),
                   "blocks": s["blocks"],
                   "line_elements": s["lines"]}
            for name, s in sub.items()
        },
        "topology_note": (
            "Block names and types are read from the .slx itself and match, one for one, the "
            "topology read out of buildSimulinkModel.m by hand during Phase 0 — the source "
            "read confirmed by the artifact."),
        "connections_note": (
            "Connection counts are NOT claimed equal to the source. buildSimulinkModel.m "
            "calls add_line 15 times; the saved file encodes fan-out as branches, so the "
            "counts differ by construction. Asserting they match without checking the graph "
            "would be a claim beyond the evidence."),
    }


def main() -> int:
    allow_missing = "--allow-missing" in sys.argv
    slx = find_slx(allow_missing=allow_missing)
    if slx is None:
        print("no committed .slx in this installation — emitting an empty Simulink view")
        # Same defect as the engine record: this emitted model_available/headline/note/blocks
        # while renderSimulink() reads model/status/status_detail/built_by/from_run/inner, so
        # the "honest empty state" rendered as undefined. The keys now match the real payload.
        #
        # The old note also said the model was "built once against the study's REAL SITES".
        # It was not: it was extracted from the model source and opened once. No Simulink
        # artifact anywhere describes a real facility.
        OUT.write_text(json.dumps({
            "schema": "fcf-simulink/1",
            "model": "not distributed with this installation",
            "from_run": None,
            "built_by": None,
            "status": "NOT DISTRIBUTED",
            "status_detail": ("No Simulink model ships with this installation. The diagram in "
                              "the full repository was generated from the model source and "
                              "opened once by MathWorks MATLAB; it has never been simulated, "
                              "and no number in this project derives from it."),
            "root": {"blocks": [], "block_count": 0, "line_elements": 0, "branch_elements": 0},
            "subsystems": {},
            "topology_note": "No topology is available because no model is distributed here.",
        }, indent=2) + "\n")
        return 0

    slx = find_slx()
    payload = extract(slx)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(f"wrote {OUT.relative_to(REPO)} from {slx.relative_to(REPO)}")
    print(f"  {payload['root']['block_count']} root blocks, "
          f"{len(payload['subsystems'])} subsystem(s)")
    print(f"  built by: {payload['built_by']}")
    print(f"  status:   {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
