"""The hashed requirements file must stay in step with the lock, and must actually verify.

Why there are two files at all
------------------------------
`requirements-lock.txt` is used as a **constraints** file by `pip install -e . -c ...`, which is
what the Makefile and CI run. Adding hashes to it breaks that outright - measured: *"the
editable requirement cannot be installed when requiring hashes, because there is no single file
to hash."* An editable install has no artifact to verify, so the two are mutually exclusive by
design.

So the lock stays unhashed and correct for its job, and `requirements-hashed.txt` exists for
the paths that can use hashes. Both are generated from the same pins, and the test below is
what stops them drifting into disagreement about versions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "requirements-lock.txt"
HASHED = REPO / "requirements-hashed.txt"

PIN = re.compile(r"^([A-Za-z0-9._-]+)==([^\s;\\]+)")


def pins(path: Path) -> dict[str, str]:
    found = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "--hash")):
            continue
        match = PIN.match(stripped)
        if match:
            found[match.group(1).lower().replace("_", "-")] = match.group(2)
    return found


pytestmark = pytest.mark.skipif(not HASHED.is_file(), reason="run scripts/add_lock_hashes.py")


def test_the_two_files_pin_identical_versions():
    """Two files generated from one source must never disagree about a version. If they do,
    one of the two install paths is building something different from the other."""
    assert pins(LOCK) == pins(HASHED)


def test_every_pin_in_the_hashed_file_carries_at_least_one_hash():
    lines = HASHED.read_text().splitlines()
    for index, line in enumerate(lines):
        if not PIN.match(line.strip()) or line.strip().startswith("#"):
            continue
        following = lines[index + 1].strip() if index + 1 < len(lines) else ""
        assert following.startswith("--hash=sha256:"), f"{line.strip()} has no hash"


def test_the_lock_itself_stays_unhashed():
    """Hashing the lock breaks `pip install -e . -c`, which is the everyday developer command.
    This is the guard against someone helpfully 'finishing the job'."""
    assert "--hash" not in LOCK.read_text(), (
        "requirements-lock.txt is a CONSTRAINTS file for an editable install; pip refuses "
        "hashes there. The hashed variant is requirements-hashed.txt.")


def test_hashes_are_full_length_sha256():
    """A truncated digest would be silently weaker rather than obviously broken."""
    for digest in re.findall(r"--hash=sha256:([0-9a-f]+)", HASHED.read_text()):
        assert len(digest) == 64, f"digest is {len(digest)} chars, not 64"


def test_packages_with_many_artifacts_list_many_hashes():
    """pip accepts a download matching ANY listed digest, so all of a version's artifacts must
    be recorded. Recording only the one this machine uses produces a file that fails on the
    Windows runner - precisely where reproducibility is meant to help.

    This is also the shape that made an early tamper test meaningless: corrupting one digest of
    several still installs, correctly. Only corrupting all of them proves verification runs.
    """
    text = HASHED.read_text()
    multi = [block for block in text.split("\n") if block.strip().startswith("numpy==")]
    if multi:
        start = text.index("numpy==")
        segment = text[start:start + 4000].split("\n")
        count = sum(1 for line in segment[1:] if line.strip().startswith("--hash"))
        assert count > 1, "numpy ships wheels for many platforms; one digest cannot be right"
