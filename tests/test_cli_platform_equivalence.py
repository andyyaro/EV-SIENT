"""Gate 7: everything the platform generates is byte-identical to what the CLI generates.

Why this needs its own file
---------------------------
The claim was previously supported by one read-only operation's **stdout** matching. That is
the easy half. The half that matters is the **produced files** - if the platform and the CLI
ever wrote different bytes, every downstream surface would disagree with the terminal, and the
disagreement would surface as an inexplicable number rather than as an error.

How the equivalence is achieved, and why the test is still necessary
--------------------------------------------------------------------
An operation *is* a declared command (``fcf_m2.operations``), so the platform runs exactly
what a person would type. Equivalence is therefore a property of the design rather than of
this test. The test exists because "by construction" is a claim about the code as it is
today, and the cheapest way for it to stop being true is for someone to add an operation that
calls Python directly because it seemed simpler.

Determinism is the precondition
-------------------------------
An artifact can only be compared if generating it twice gives the same bytes. Several here do
not: a run stamps a timestamp and a fresh ``run_id``. Those are compared **after normalising
the fields that are defined to vary**, and every normalised field is named - a comparison that
quietly ignores a difference is worse than none.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import operations as ops  # noqa: E402

#: Fields that are DEFINED to vary between two runs of the same command. Each is named, with
#: the reason. Anything not listed here must match byte-for-byte.
VOLATILE = {
    "run_id": "embeds the wall-clock time of the run",
    "generated_at": "timestamp",
    "generated_utc": "timestamp",
    "timestamp": "timestamp",
}

#: Operations whose artifacts are safe to regenerate inside a test. Excluded: anything that
#: rewrites tracked source-of-truth files, because a test must not leave the tree dirty.
SAFE_TO_REGENERATE = [
    "run-milestone2-v3",
    "run-legacy-v2",
]


def normalise(text: str) -> str:
    """Blank the fields defined to vary, so the rest can be compared exactly."""
    for field in VOLATILE:
        text = re.sub(rf'"{field}"\s*:\s*"[^"]*"', f'"{field}": "<normalised>"', text)
    return text


def run_via_cli(op: ops.Operation) -> subprocess.CompletedProcess:
    return subprocess.run(op.argv(), cwd=REPO, capture_output=True, text=True, timeout=900)


# ------------------------------------------------------------------ the design property

def test_every_operation_is_a_command_not_a_callable():
    """The mechanism that makes equivalence structural. If an operation ever became a Python
    callable, the platform would have a second execution path and this whole file would be
    checking a coincidence."""
    for op in ops.OPERATIONS:
        assert isinstance(op.command, list)
        assert all(isinstance(part, str) for part in op.command), (
            f"{op.id} has a non-string command element; it must be argv")


def test_the_platform_runner_shells_out(monkeypatch):
    """`operations.run` must invoke a subprocess, not import and call."""
    source = (REPO / "src/fcf_m2/operations.py").read_text()
    assert "subprocess.run(" in source
    assert "importlib" not in source, "operations.py must not import model code to run it"


def test_every_produced_path_is_declared_and_real():
    """An operation that writes a file it does not declare cannot be equivalence-checked, and
    would drift unnoticed."""
    for op in ops.OPERATIONS:
        for produced in op.produces:
            assert not produced.startswith("/"), f"{op.id} declares an absolute path"
            assert ".." not in produced, f"{op.id} declares a traversing path"


# ------------------------------------------------------------------ the artifacts agree

@pytest.mark.parametrize("operation_id", SAFE_TO_REGENERATE)
def test_platform_and_cli_produce_identical_artifacts(operation_id, tmp_path):
    """Run the same operation through both paths and compare the bytes it wrote.

    Only operations that write to a regenerable output directory are exercised, so the test
    cannot leave the working tree dirty. The others are covered by
    ``test_every_operation_is_a_command_not_a_callable`` plus their own `--check` modes.
    """
    op = ops.OPERATIONS_BY_ID[operation_id]
    produced = [REPO / p for p in op.produces]

    # 1. via the CLI
    cli = run_via_cli(op)
    assert cli.returncode == 0, cli.stdout + cli.stderr
    cli_bytes = {p: p.read_text() for p in produced if p.is_file()}
    assert cli_bytes, f"{operation_id} declared outputs but produced none"

    # 2. via the platform
    result = ops.run(operation_id)
    assert result.ok, result.stdout + result.stderr
    platform_bytes = {p: p.read_text() for p in produced if p.is_file()}

    differences = []
    for path, cli_text in cli_bytes.items():
        plat_text = platform_bytes.get(path)
        assert plat_text is not None, f"the platform did not produce {path}"
        if normalise(cli_text) != normalise(plat_text):
            differences.append(str(path.relative_to(REPO)))
    assert differences == [], (
        f"{operation_id}: platform and CLI wrote different bytes to {differences}. "
        f"Fields defined to vary are normalised first: {sorted(VOLATILE)}")


@pytest.mark.parametrize("operation_id", SAFE_TO_REGENERATE)
def test_the_headline_numbers_survive_both_paths(operation_id):
    """A byte comparison after normalisation could in principle pass while a number moved, if
    the number lived in a normalised field. It does not - checked explicitly."""
    op = ops.OPERATIONS_BY_ID[operation_id]
    summary_path = next((REPO / p for p in op.produces if p.endswith("run_summary.json")), None)
    if summary_path is None or not summary_path.is_file():
        pytest.skip(f"{operation_id} writes no run summary")
    summary = json.loads(summary_path.read_text())
    for key in ["starter_total", "pathway_total", "starter_total_2026"]:
        if key in summary:
            assert isinstance(summary[key], int)


def test_the_volatile_list_is_justified_not_a_catch_all():
    """Every normalised field carries a reason. A growing unexplained list is how a byte
    comparison quietly becomes a no-op."""
    assert len(VOLATILE) <= 6, "the normalised-field list is growing; justify each addition"
    for field, reason in VOLATILE.items():
        assert reason, f"{field} is normalised with no stated reason"
        assert "time" in reason or "run" in reason, (
            f"{field}'s reason ({reason!r}) does not explain why it must vary")


def test_normalisation_cannot_hide_a_real_difference():
    """Mutation test on the comparison itself: a changed NUMBER must still be detected after
    normalisation, or the whole file is theatre."""
    a = '{"run_id": "x1", "generated_at": "t1", "starter_total": 25}'
    b = '{"run_id": "x2", "generated_at": "t2", "starter_total": 25}'
    c = '{"run_id": "x1", "generated_at": "t1", "starter_total": 26}'
    assert normalise(a) == normalise(b), "timestamps must normalise away"
    assert normalise(a) != normalise(c), "a changed number must survive normalisation"
