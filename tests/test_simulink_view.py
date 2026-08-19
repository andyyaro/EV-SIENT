"""The Simulink view shows the real model's topology, and says what it never did.

A block diagram is exactly the kind of artifact a reader assumes produced something. This one
did not: it was built once and never simulated, and no number in this project derives from it.
That fact has to travel with the diagram, or the diagram is a misleading object.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
VIEW = REPO / "site/platform/simulink.json"


@pytest.fixture(scope="module")
def view() -> dict:
    return json.loads(VIEW.read_text())


def test_it_leads_with_what_the_model_never_did(view):
    assert view["status"] == "BUILT, NEVER SIMULATED"
    assert "never been run" in view["status_detail"]
    assert "No number anywhere in this project derives from it" in view["status_detail"]


def test_it_comes_from_a_real_committed_artifact(view):
    """Extracted from the .slx, never described from memory."""
    slx = list(REPO.glob(f"matlab/outputs/{view['from_run']}/simulink/*.slx"))
    assert slx, f"{view['from_run']} has no committed .slx; the view cites a missing artifact"
    assert zipfile.is_zipfile(slx[0]), "the .slx is not a real Simulink package"


def test_it_records_which_matlab_built_it(view):
    assert "R2025b" in view["built_by"]
    assert "25.2" in view["built_by"]


def test_the_topology_matches_the_source_that_generated_it(view):
    """Phase 0 read buildSimulinkModel.m by hand and recorded 11 blocks with these names.
    The artifact confirms the source read - that is the point of extracting rather than
    screenshotting."""
    names = {b["name"] for b in view["root"]["blocks"]}
    expected = {
        "Base Load", "EV Request", "Capacity Limit",
        "Total Unmanaged", "Total Managed",
        "Managed Logic Inputs", "Main Scope Signals",
        "Managed EV Power", "Live Scope: Load Behavior",
        "toWorkspace_unmanaged", "toWorkspace_managed",
    }
    assert names == expected, f"topology drifted: {names ^ expected}"
    assert view["root"]["block_count"] == 11


def test_block_types_are_carried_not_just_names(view):
    types = {b["name"]: b["type"] for b in view["root"]["blocks"]}
    assert types["Base Load"] == "FromWorkspace"
    assert types["Total Managed"] == "Sum"
    assert types["Live Scope: Load Behavior"] == "Scope"
    assert types["Managed EV Power"] == "SubSystem"


def test_connection_counts_are_explicitly_NOT_claimed_equal(view):
    """buildSimulinkModel.m calls add_line 15 times; the file encodes fan-out as branches, so
    the counts differ by construction. Claiming they match would exceed the evidence."""
    note = view["connections_note"]
    assert "NOT claimed equal" in note
    assert "add_line 15 times" in note
    assert "beyond the evidence" in note
    # And the raw counts are still carried, so a reader can check the reasoning.
    assert view["root"]["line_elements"] > 0
    assert view["root"]["branch_elements"] > 0


def test_the_view_rebuilds_from_the_artifact():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_simulink_view.py")],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_it_refuses_when_no_slx_is_committed(tmp_path, monkeypatch):
    """The view must never be generated from a description of an artifact."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_fcf_sim", REPO / "scripts/build_simulink_view.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO", tmp_path)
    with pytest.raises(SystemExit, match="never from a description"):
        mod.find_slx()
