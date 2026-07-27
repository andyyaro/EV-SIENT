"""The platform runs the CLI's commands, and the web tier is honest about what it cannot do.

Two Phase 7 requirements are enforced here, both of which are easy to satisfy on day one and
easy to lose later:

1. **Everything the platform generates is byte-identical to what the CLI generates.** Held by
   construction — an operation *is* a declared command — and checked by actually running one
   both ways and comparing bytes.
2. **The web tier states plainly which capabilities require the desktop app rather than
   hiding or faking them.** So the web tier gets the whole list with reasons, not a filtered
   one.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import operations as ops  # noqa: E402


# ------------------------------------------------------------------ the registry is sound

def test_operation_ids_are_unique():
    ids = [op.id for op in ops.OPERATIONS]
    assert len(ids) == len(set(ids)), f"duplicate operation id(s): {ids}"


def test_every_desktop_operation_states_why():
    """An unexplained disabled control is indistinguishable from a broken one, and the web
    tier is the primary distribution — most readers will only ever see it."""
    for op in ops.OPERATIONS:
        if op.tier == ops.TIER_DESKTOP:
            assert op.desktop_reason, f"{op.id} is desktop-only with no stated reason"
            assert len(op.desktop_reason) > 30, f"{op.id}'s reason is too terse to help"


def test_a_desktop_operation_without_a_reason_is_rejected_at_construction():
    with pytest.raises(ValueError, match="no stated reason"):
        ops.Operation(id="x", label="x", description="x", tier=ops.TIER_DESKTOP, command=[])


def test_an_unknown_tier_is_rejected():
    with pytest.raises(ValueError, match="unknown tier"):
        ops.Operation(id="x", label="x", description="x", tier="cloud", command=[])


def test_every_description_is_written_for_a_reader_not_a_developer():
    for op in ops.OPERATIONS:
        assert len(op.description) > 60, f"{op.id}: description too thin to be useful"
        assert op.label and not op.label.endswith("."), f"{op.id}: label should be a phrase"


def test_every_command_is_runnable_shape():
    """A command referencing a script that does not exist is a button that fails on click."""
    for op in ops.OPERATIONS:
        argv = op.argv()
        assert argv, f"{op.id} has an empty command"
        for part in argv:
            if part.endswith(".py") or part.endswith(".sh"):
                assert (REPO / part).is_file(), f"{op.id} references missing {part}"


def test_no_operation_smuggles_a_credential():
    """Nothing in a shipped artifact may carry a token, key or account id."""
    import re
    suspicious = re.compile(r"(?i)(aws_|secret|token|password|api[_-]?key|[0-9]{12})")
    for op in ops.OPERATIONS:
        joined = " ".join(op.command)
        assert not suspicious.search(joined), f"{op.id} command looks credential-bearing"


# ------------------------------------------------------------------ tier honesty

def test_the_web_tier_sees_every_operation_including_the_ones_it_cannot_run():
    """Filtering the list would be the dishonest option: a reader who cannot see that
    'Run the model' exists cannot know they need the desktop app for it."""
    web = ops.for_tier(ops.TIER_BOTH)
    desktop = ops.for_tier(ops.TIER_DESKTOP)
    assert len(web) == len(desktop) == len(ops.OPERATIONS)
    assert [e["id"] for e in web] == [e["id"] for e in desktop]


def test_the_web_tier_marks_desktop_operations_unavailable_with_a_reason():
    for entry in ops.for_tier(ops.TIER_BOTH):
        op = ops.OPERATIONS_BY_ID[entry["id"]]
        if op.tier == ops.TIER_DESKTOP:
            assert entry["available"] is False
            assert entry["unavailable_reason"] == op.desktop_reason
        else:
            assert entry["available"] is True
            assert entry["unavailable_reason"] == ""


def test_the_desktop_tier_can_run_everything():
    assert all(e["available"] for e in ops.for_tier(ops.TIER_DESKTOP))


def test_read_only_checks_are_available_on_the_web_tier():
    """If the web tier could not even validate the contract, 'view-only' would mean 'trust
    us'. Contract validation is pure reading and must work there."""
    web = {e["id"]: e for e in ops.for_tier(ops.TIER_BOTH)}
    assert web["validate-contract-v1"]["available"] is True
    assert web["validate-contract-v2"]["available"] is True


def test_an_unknown_tier_is_refused():
    with pytest.raises(ValueError, match="unknown tier"):
        ops.for_tier("mobile")


# ------------------------------------------------------------------ byte-equivalence

def test_running_an_operation_matches_running_the_cli_directly(tmp_path):
    """Gate 7's byte-equivalence requirement, checked rather than asserted.

    `validate-contract-v1` is chosen because it is read-only and deterministic: running it
    twice cannot change the repository, so a difference means the two paths genuinely differ
    rather than that one ran second.
    """
    op = ops.OPERATIONS_BY_ID["validate-contract-v1"]

    via_platform = ops.run("validate-contract-v1")

    direct = subprocess.run(op.argv(), cwd=REPO, capture_output=True, text=True)

    assert via_platform.returncode == direct.returncode == 0
    assert via_platform.stdout == direct.stdout, (
        "the platform and the CLI produced different output for the same operation")


def test_the_platform_never_reimplements_the_model():
    """`src/fcf_m2` stays the only scorer. An operation is a COMMAND, never a callable, so
    there is no second code path that could drift from the model."""
    for op in ops.OPERATIONS:
        assert isinstance(op.command, list) and all(isinstance(p, str) for p in op.command)
    source = (REPO / "src/fcf_m2/operations.py").read_text()
    for banned in ["import numpy", "from .scoring", "from .demand", "from .right_sizing",
                   "from .economics", "from .emissions"]:
        assert banned not in source, (
            f"operations.py imports {banned!r}; it orchestrates and must never compute")


def test_an_unknown_operation_is_refused():
    with pytest.raises(KeyError, match="unknown operation"):
        ops.run("drop-database")
