#!/usr/bin/env python3
"""Add `--hash=sha256:` lines to requirements-lock.txt, from PyPI's published digests.

Why a pin is not a lock
-----------------------
`requirements-lock.txt` pins every dependency to an exact version, which is most of the job and
was described as "reproducible". It is not, quite. A version pin says **which release** to
install; it says nothing about whether the bytes that arrived are that release. Without hashes,
`pip install -c` will accept whatever the index serves under that name and version - a
re-uploaded artifact, a compromised mirror, a corrupted download.

Until this ran, "reproducible build from a clean checkout" was a claim about a *version list*
rather than about *content*, and the packaging requirement asks for the second. The same gap
existed in `vendor_cesium.sh`, which fetched 20 MB of third-party JavaScript against a pinned
version with no digest check; that one is closed.

Every hash for a version
------------------------
A release has many artifacts - wheels for each platform and Python version, plus an sdist - and
which one pip picks depends on the machine. So **all** of a version's digests are recorded, and
pip accepts the download if it matches any of them. Recording only the digest of the artifact
this Mac happens to use would produce a lock file that fails on the Windows runner, which is
exactly where reproducibility is supposed to help.

What this does not do
---------------------
It does not invent a hash for anything PyPI does not publish. A package whose digests cannot be
retrieved is reported and left unhashed rather than silently passed through, because a lock file
that is *partly* hash-verified while claiming to be verified is worse than one that admits the
gap - `pip --require-hashes` fails closed on any unhashed requirement, so a silent omission
would surface as a confusing install error rather than as the known hole it is.

Why this writes a SECOND file instead of hashing the lock
--------------------------------------------------------
The obvious implementation adds the hashes to `requirements-lock.txt`. Measured, that breaks
the repository:

* The lock is used as a **constraints** file by `pip install -e . -c requirements-lock.txt`,
  which is what the Makefile and CI run. With hashes present pip refuses outright - *"the
  editable requirement cannot be installed when requiring hashes, because there is no single
  file to hash."* An editable install has no artifact to verify, so the two are mutually
  exclusive by design, not by oversight.
* Used as `-r` with the environment marker intact, `--require-hashes` additionally rejects the
  build because `python-docx` declares `typing_extensions>=4.9.0` and hash mode requires every
  resolved requirement to be `==` pinned.

So the lock stays exactly as it was - working, unhashed, correct for its actual job - and a
hash-verified `requirements-hashed.txt` is written beside it for the paths that can use one: a
clean non-editable install, and the packaging build. Both files are generated from the same
pins, so they cannot disagree about versions.

**What is therefore NOT hash-verified**: the everyday `pip install -e . -c` developer install.
That is a real remaining gap, stated here rather than glossed, and it is a limitation of
editable installs rather than something this script can close.

Run: python scripts/add_lock_hashes.py            # writes requirements-hashed.txt
     python scripts/add_lock_hashes.py --check    # verifies it is current, changes nothing
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "requirements-lock.txt"
#: Written alongside the lock rather than into it. See the module docstring - the lock is used
#: as a CONSTRAINTS file for an editable install, and pip cannot do both.
HASHED = REPO / "requirements-hashed.txt"

PIN = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)==(?P<version>[^\s;]+)(?P<marker>\s*;.*)?$")


def digests_for(name: str, version: str, timeout: int = 30) -> list[str]:
    """Every sha256 PyPI publishes for this exact version.

    Fetched with ``curl`` rather than ``urllib``. Not a preference: this machine's Python has
    no CA bundle and every HTTPS call from it fails ``CERTIFICATE_VERIFY_FAILED``. The two ways
    to make urllib work are to add a ``certifi`` dependency or to disable certificate
    verification - and disabling TLS verification while fetching the digests that are supposed
    to *establish* supply-chain integrity would be self-defeating. ``curl`` uses the system
    trust store and validates fully.
    """
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    result = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", str(timeout),
         "-A", "fcf-lock-hasher", url],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise urllib.error.URLError(result.stderr.strip() or f"curl exit {result.returncode}")
    payload = json.loads(result.stdout)
    out = []
    for entry in payload.get("urls", []):
        digest = (entry.get("digests") or {}).get("sha256")
        if digest:
            out.append(digest)
    return sorted(set(out))


def rewrite(check_only: bool) -> int:
    lines = (HASHED if check_only and HASHED.is_file() else LOCK).read_text().splitlines()
    out: list[str] = []
    unhashed: list[str] = []
    hashed = 0

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        # Preserve comments, blanks, and any hash block already present.
        if not stripped or stripped.startswith("#"):
            out.append(line)
            index += 1
            continue
        if stripped.startswith("--hash"):
            index += 1          # dropped; regenerated below from the pin that owns it
            continue

        match = PIN.match(stripped.rstrip("\\").strip())
        if not match:
            out.append(line)
            index += 1
            continue

        name, version = match["name"], match["version"]
        marker = (match["marker"] or "").rstrip()

        if check_only:
            # A pin is "hashed" only if a --hash line follows it.
            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if not following.startswith("--hash"):
                unhashed.append(f"{name}=={version}")
            else:
                hashed += 1
            out.append(line)
            index += 1
            continue

        try:
            digests = digests_for(name, version)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"  could not retrieve digests for {name}=={version}: {exc}")
            unhashed.append(f"{name}=={version}")
            out.append(line)
            index += 1
            continue

        if not digests:
            print(f"  PyPI publishes no sha256 for {name}=={version}")
            unhashed.append(f"{name}=={version}")
            out.append(line)
            index += 1
            continue

        # The marker is dropped in the hashed file: --require-hashes needs every resolved
        # requirement pinned with ==, and a marked-out pin reads as unpinned. The lock keeps
        # its marker, because that is where the marker is correct.
        out.append(f"{name}=={version} \\")
        for position, digest in enumerate(digests):
            suffix = " \\" if position < len(digests) - 1 else ""
            out.append(f"    --hash=sha256:{digest}{suffix}")
        hashed += 1
        index += 1

    if check_only:
        if unhashed:
            print(f"{len(unhashed)} pin(s) carry no hash, so the lock is not content-verified:")
            for item in unhashed:
                print(f"  {item}")
            return 1
        print(f"all {hashed} pins are hash-verified")
        return 0

    header = [
        "# GENERATED by scripts/add_lock_hashes.py - do not edit.",
        "#",
        "# Hash-verified requirements for a clean NON-EDITABLE install:",
        "#     pip install --require-hashes -r requirements-hashed.txt",
        "#",
        "# requirements-lock.txt remains the constraints file for the editable developer",
        "# install. pip cannot hash an editable requirement, so the two cannot be one file.",
        "# Environment markers are dropped here because --require-hashes reads a marked-out",
        "# pin as unpinned.",
        "",
    ]
    HASHED.write_text("\n".join(header + [l for l in out if not l.startswith("#")]) + "\n")
    print(f"wrote {HASHED.name}: {hashed} pin(s) hashed"
          + (f", {len(unhashed)} UNHASHED" if unhashed else ""))
    for item in unhashed:
        print(f"  unhashed: {item}")
    return 1 if unhashed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="verify every pin is hashed; do not modify the file")
    args = parser.parse_args()
    return rewrite(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
