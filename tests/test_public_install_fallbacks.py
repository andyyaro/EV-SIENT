"""A public install's "honest empty state" must render, not print `undefined`.

Two builders have an `--allow-missing` branch for installations that carry no MATLAB or
Simulink artifacts. Both docstrings describe that branch as the honest alternative to dying:
the surface is emitted empty and says so. Neither branch produced a payload the renderer could
read.

* `build_engine_record.py` emitted `engine` / `badge` / `role` / `executed` while
  `site/platform/app.js` reads `id` / `name` / `status` / `detail` / `ran_on_real_sites`, and
  the top-level key was `cannot_show` against a renderer reading `what_cannot_be_shown`.
* `build_simulink_view.py` emitted `model_available` / `headline` / `note` / `blocks` while
  `renderSimulink()` reads `model`, `status`, `status_detail`, `built_by`, `from_run`,
  `root.block_count`, `root.blocks` and `subsystems`.

Nothing caught it because the branch never runs in this repository — the artifacts are present
here, so only a recipient of the public installer would have seen it, and only as silent
`undefined` text rather than an error.

These tests exercise the fallback directly and compare its shape to the real payload. The
comparison is against the REAL FILE rather than a hardcoded key list, so adding a field to the
live surface fails here until the empty state grows it too.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable

ENGINES = REPO / "site/platform/engines.json"
SIMULINK = REPO / "site/platform/simulink.json"


def build_fallback(script: str, target: Path, hide: Path | None = None) -> dict:
    """Run a builder's --allow-missing branch and return the payload, restoring everything.

    `hide` is required in practice: both builders take the empty branch only when the artifact
    they look for is absent, and in THIS repository it is present. Passing `--allow-missing`
    alone therefore builds the real payload and tests nothing — which is exactly why the
    defect survived. The artifact is moved aside for the duration and always moved back.
    """
    saved = target.read_text() if target.is_file() else None
    hidden = None
    if hide is not None and hide.exists():
        hidden = hide.parent / (hide.name + ".hidden-for-test")
        hide.rename(hidden)
    try:
        subprocess.run([PY, str(REPO / "scripts" / script), "--allow-missing"],
                       cwd=REPO, capture_output=True, text=True, check=False)
        return json.loads(target.read_text())
    finally:
        if hidden is not None:
            hidden.rename(hide)
        if saved is not None:
            target.write_text(saved)


#: What each builder looks for. Hiding it is what forces the empty branch.
MATLAB_RUNS = REPO / "matlab/outputs"


def leaf_keys(node, prefix=""):
    """Key paths in a payload, so a nested field is not missed.

    Lists are sampled at element 0 only: these payloads are homogeneous arrays (every engine
    row has the same shape), so the first element is representative. A key present ONLY in a
    later element would be missed -- stated because the previous docstring claimed "every key
    path", which is stronger than what this does.
    """
    out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(f"{prefix}{k}")
            out |= leaf_keys(v, f"{prefix}{k}.")
    elif isinstance(node, list) and node:
        out |= leaf_keys(node[0], prefix)
    return out


@pytest.mark.skipif(not ENGINES.is_file(), reason="engines.json absent")
def test_the_empty_engine_record_has_the_shape_the_renderer_reads():
    real = json.loads(ENGINES.read_text())
    empty = build_fallback("build_engine_record.py", ENGINES, hide=MATLAB_RUNS)

    missing = leaf_keys(real) - leaf_keys(empty)
    # ONLY `divergences` is exempt -- it is a genuine list, and an empty list has no children.
    #
    # `guard_evidence` used to be exempt too, on the assumption that it was also an empty
    # list. It is an OBJECT, and renderEngines() dereferences `guard_evidence.capacity_basis`
    # and calls .join() on it. So this exemption was hiding precisely the field that made the
    # public install throw. An exemption is a claim about the data, and this one was false.
    missing = {k for k in missing if not k.startswith("divergences.")}
    assert not missing, (
        f"the public-install engine record omits {sorted(missing)}, which the platform "
        f"renders — a recipient sees 'undefined' where the honest empty state should be")


@pytest.mark.skipif(not ENGINES.is_file(), reason="engines.json absent")
def test_the_empty_engine_record_does_not_claim_a_real_site_run():
    empty = build_fallback("build_engine_record.py", ENGINES, hide=MATLAB_RUNS)
    for engine in empty["engines"]:
        assert engine["ran_on_real_sites"] is False, (
            "a public installation runs on synthetic inputs; no engine in it ran on real sites")


@pytest.mark.skipif(not SIMULINK.is_file(), reason="simulink.json absent")
def test_the_empty_simulink_view_has_the_shape_the_renderer_reads():
    real = json.loads(SIMULINK.read_text())
    slx = next(iter(REPO.glob("matlab/outputs/**/*.slx")), None)
    empty = build_fallback("build_simulink_view.py", SIMULINK, hide=slx)

    required = {"model", "status", "status_detail", "built_by", "from_run",
                "subsystems", "root.block_count", "root.blocks"}
    have = leaf_keys(empty)
    assert not (required - have), (
        f"the public-install Simulink view omits {sorted(required - have)}, which "
        f"renderSimulink() dereferences")
    assert set(real) - set(empty) - {"connections_note", "topology_note"} == set(), (
        "the real payload has top-level keys the empty one lacks")


@pytest.mark.skipif(not SIMULINK.is_file(), reason="simulink.json absent")
def test_the_empty_simulink_view_does_not_claim_the_model_touched_real_sites():
    """The old note said the diagram records a model 'built once against the study's real
    sites'. It does not: it was extracted from the model source. No Simulink artifact anywhere
    describes a real facility."""
    slx = next(iter(REPO.glob("matlab/outputs/**/*.slx")), None)
    empty = build_fallback("build_simulink_view.py", SIMULINK, hide=slx)
    text = json.dumps(empty).lower()
    assert "real site" not in text, "the empty Simulink view claims a real-site model"
    assert "never been simulated" in text or "never simulated" in text, (
        "the empty view must still say the model was never simulated")
