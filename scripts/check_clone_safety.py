#!/usr/bin/env python3
"""Every file the repository's declared surfaces depend on must exist in a fresh clone.

Why this gate exists
--------------------
`verify.sh` checks the tree it is run in. It has no way to notice that a file it depends on
is untracked or gitignored, because that file is sitting right there on the developer's disk.
The result is a suite that is green locally and broken for everyone else, and this repository
has now produced that exact failure **three times**:

* **Phase 1** - `verify.sh` green locally, broken on a clean clone.
* **FIND-CI-01 root cause A** (2026-07-28T00:45Z) - the Tableau build read `data/outputs/`,
  which is gitignored: present on a machine that had run the model, absent everywhere else.
  CI was red for five consecutive commits while gates were reported green.
* **DEC-021** (2026-07-28T02:10Z) - the commit landed `intake.py`, its tests and its gate, but
  not `scripts/intake_review.py` or the two files registering it. All 38 gates passed against
  the working tree while the repository declared an operation whose script did not exist in it.

The third one is what this gate is shaped around, because it is the cheapest to check
mechanically: **a declared operation is a promise that a command will run.** If the script that
command invokes is not in git, the promise is false for every clone.

What it checks
--------------
1. Every path-like argument of every declared operation, and every repository script referenced
   by `verify.sh`, resolves to a file **tracked by git**.
2. Untracked is a failure. Gitignored-but-present is a failure, and a nastier one - the file
   exists, so nothing local complains.
3. Output paths (`--out <dir>`, `data/outputs/...`) are exempt: they are *written*, not read.
   Their absence in a clone is correct.

What it does NOT check
----------------------
It does not run the gates against an actual fresh clone, which is the only complete answer.
It catches the specific, recurring, mechanically-detectable case: a declared dependency that is
not in version control. A dependency introduced through an import chain or read at runtime from
a path this script cannot see statically will still slip through.

    python scripts/check_clone_safety.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2.operations import OPERATIONS  # noqa: E402

#: Written by a run, not read by one. Their absence from a clone is the correct state.
OUTPUT_PREFIXES = ("data/outputs/",)

#: Looks like a repository-relative path: has a directory component and a file extension.
PATH_ARG = re.compile(r"^[A-Za-z0-9._/-]+/[A-Za-z0-9._-]+$")


def tracked_files() -> set[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"],
                         capture_output=True, text=True, check=True)
    return set(out.stdout.split("\n")) - {""}


def is_output(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in OUTPUT_PREFIXES)


def candidates_from_operations() -> list[tuple[str, str]]:
    """(source, path) for every path-like argument of every declared operation."""
    found: list[tuple[str, str]] = []
    for operation in OPERATIONS:
        skip_next = False
        for arg in operation.command:
            if skip_next:                      # the value of --out
                skip_next = False
                continue
            if arg == "--out":
                skip_next = True
                continue
            if not PATH_ARG.match(arg) or is_output(arg):
                continue
            found.append((f"operation {operation.id!r}", arg))
    return found


def candidates_from_verify() -> list[tuple[str, str]]:
    """Repository scripts invoked by verify.sh.

    Deliberately narrow: only `scripts/…` and `tests/…` paths, matched literally. A broader
    regex over a shell script produces false positives from strings inside python -c blocks,
    and a gate that cries wolf gets deleted.
    """
    text = (REPO / "scripts/verify.sh").read_text()
    found: list[tuple[str, str]] = []
    for match in re.finditer(r"\b((?:scripts|tests)/[A-Za-z0-9._/-]+\.(?:py|sh|m))\b", text):
        found.append(("verify.sh", match.group(1)))
    return found


def main() -> int:
    tracked = tracked_files()
    problems: list[str] = []
    checked = 0

    seen: set[tuple[str, str]] = set()
    for source, path in candidates_from_operations() + candidates_from_verify():
        if (source, path) in seen:
            continue
        seen.add((source, path))
        checked += 1

        if path in tracked:
            continue
        # A directory argument (`validate-contract data/contract/v1`) is never itself a
        # `git ls-files` entry. It is present in a clone if anything under it is tracked.
        if (REPO / path).is_dir() and any(t.startswith(path + "/") for t in tracked):
            continue

        on_disk = (REPO / path).exists()
        if on_disk:
            # The dangerous case. It works here and nowhere else.
            ignored = subprocess.run(
                ["git", "-C", str(REPO), "check-ignore", "-q", path]).returncode == 0
            why = "gitignored" if ignored else "untracked"
            problems.append(
                f"{source} depends on {path}, which exists on this machine but is {why}. "
                f"A fresh clone does not have it.")
        else:
            problems.append(
                f"{source} depends on {path}, which is neither tracked nor present.")

    if problems:
        print(f"{len(problems)} declared dependency/dependencies would be missing from a clone:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"clone-safety: all {checked} declared dependencies are tracked in git")
    return 0


if __name__ == "__main__":
    sys.exit(main())
