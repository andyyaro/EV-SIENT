"""One-directional sync: private MATLAB sources -> the public CI harness.

The harness is **downstream**. It exists only to run this model on real MathWorks MATLAB in
GitHub Actions, and it is never hand-edited. A fix made in the harness instead of here would
create two diverging MATLAB layers, which is precisely the failure this project's contract
discipline exists to prevent -- the same reason no consumer of the data contract is allowed
to re-derive a number.

So the relationship is enforced rather than trusted:

* ``--check`` (the gate) fails if any published file differs from its private source, or if
  the harness has grown a file the sync does not know about. It is deliberately symmetric:
  an *extra* file in the harness is as much a divergence as a modified one, because an extra
  file is how a hand-edit arrives.
* ``--push`` writes the private content into a harness checkout and records a manifest.
* Nothing ever reads *from* the harness into this repository. There is no reverse mode, by
  design, and adding one would defeat the point.

Before anything is copied, every file is run through ``check_harness_exposure.py``. The sync
refuses to publish a file that would leak site-identifying data, so the exposure gate cannot
be bypassed by going around it.

Usage
-----
    python scripts/sync_matlab_harness.py --check --harness ../harness
    python scripts/sync_matlab_harness.py --push  --harness ../harness
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "SYNC_MANIFEST.json"

# private path -> harness path. This mapping IS the definition of what may be published.
# Adding a line here is the only way a file reaches the public repository.
SYNCED: dict[str, str] = {
    **{f"matlab/src/{p.name}": f"src/{p.name}" for p in sorted((REPO / "matlab/src").glob("*.m"))},
    **{f"matlab/tests/{p.name}": f"tests/{p.name}" for p in sorted((REPO / "matlab/tests").glob("*.m"))},
    "matlab/data/harness/harness_scenarios_synthetic.csv":
        "data/harness_scenarios_synthetic.csv",
}

# Files the harness owns outright. They are not synced and not policed for drift, because
# they describe the harness itself rather than the model.
HARNESS_OWNED = {
    "README.md", ".gitignore", MANIFEST_NAME,
    ".github/workflows/matlab-ci.yml",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def exposure_clean(paths: list[Path]) -> tuple[bool, str]:
    """Refuse to publish anything the exposure gate rejects."""
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/check_harness_exposure.py"),
         "--files", *[str(p) for p in paths]],
        capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def harness_tracked_files(harness: Path) -> set[str]:
    out = subprocess.run(["git", "ls-files"], cwd=harness,
                         capture_output=True, text=True, check=True).stdout
    return {f for f in out.split() if f}


def check(harness: Path) -> int:
    problems: list[str] = []

    for private_rel, harness_rel in sorted(SYNCED.items()):
        src, dst = REPO / private_rel, harness / harness_rel
        if not src.is_file():
            problems.append(f"private source missing: {private_rel}")
            continue
        if not dst.is_file():
            problems.append(f"harness is missing {harness_rel} (source: {private_rel})")
            continue
        if sha256(src) != sha256(dst):
            problems.append(
                f"DIVERGED: {harness_rel} does not match {private_rel}. "
                f"Fix it in the private repository and re-sync -- never in the harness.")

    # An unexpected file is a divergence too: it is how a hand-edit arrives.
    expected = set(SYNCED.values()) | HARNESS_OWNED
    for tracked in sorted(harness_tracked_files(harness)):
        if tracked not in expected:
            problems.append(
                f"UNTRACKED BY SYNC: {tracked} exists in the harness but is not published "
                f"by this script. Either add it to SYNCED here, or remove it there.")

    if problems:
        print("HARNESS SYNC PROBLEMS:")
        print("\n".join(f"  {p}" for p in problems))
        return 1
    print(f"harness in sync ({len(SYNCED)} files hash-identical to their private sources)")
    return 0


def push(harness: Path) -> int:
    sources = [REPO / rel for rel in SYNCED]
    ok, output = exposure_clean(sources)
    if not ok:
        print("REFUSING TO PUBLISH -- the exposure gate rejected a file:")
        print(output)
        return 1
    print(output.strip())

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": "private (source of truth)",
        "source_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                        capture_output=True, text=True).stdout.strip(),
        "direction": "private -> public, one-directional. Never the reverse.",
        "files": {},
    }
    for private_rel, harness_rel in sorted(SYNCED.items()):
        src, dst = REPO / private_rel, harness / harness_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        manifest["files"][harness_rel] = {"source": private_rel, "sha256": sha256(src)}
        print(f"  synced {private_rel} -> {harness_rel}")

    (harness / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  wrote {MANIFEST_NAME} ({len(manifest['files'])} files)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--harness", required=True, help="path to the harness checkout")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if the harness has diverged")
    mode.add_argument("--push", action="store_true", help="write private content into the harness")
    args = ap.parse_args()

    harness = Path(args.harness).expanduser().resolve()
    if not (harness / ".git").exists():
        print(f"not a git checkout: {harness}", file=sys.stderr)
        return 2
    return check(harness) if args.check else push(harness)


if __name__ == "__main__":
    sys.exit(main())
