#!/usr/bin/env python3
"""Is the live public site the commit it says it is? Byte for byte, file by file.

Why this exists
---------------
The 2026-10-17 audit found production matching no commit at all (F-14). Five pages were a July
commit plus a CSS rule added by hand, the results page carried photos no commit had, and the
assistant page carried a patch made on the live copy. The next deploy from `main` would have
silently undone all three, and nothing would have said so, because nothing compared the two.

This compares them. For every file `deploy_platform.py` publishes to the main bucket, it fetches
the live copy and checks it against the same path at a git ref (default `origin/main`). It also
reads `deployed.json`, which every `--apply` writes, and checks that it names that ref's commit.
It only reads.

What it cannot see: objects in the bucket that no tracked folder produces, and anything behind
the platform gate, which `scripts/verify_deployment.py` covers.

Usage
-----
    python scripts/check_live_vs_main.py                  # live vs origin/main
    python scripts/check_live_vs_main.py --ref HEAD       # live vs this checkout's commit
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE = "https://futurecityfellowship.andyyaro.com"


def deploy_module():
    """The deploy script, for its table of what is published where. One table, so the check
    cannot drift from the deploy."""
    spec = importlib.util.spec_from_file_location("deploy_platform", REPO / "scripts/deploy_platform.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, check=True).stdout


def expected_files(ref: str, trees: dict[str, str]) -> dict[str, tuple[str, bytes]]:
    """URL path -> (repository path, bytes at ref), for every file the deploy publishes."""
    files = {}
    for local, prefix in trees.items():
        for path in git("ls-tree", "-r", "--name-only", ref, "--", local).decode().splitlines():
            files["/" + prefix + path[len(local) + 1:]] = (path, git("show", f"{ref}:{path}"))
    return files


def fetch(url: str, timeout: int = 25) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "fcf-live-check/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def compare(expected: dict[str, tuple[str, bytes]], fetcher) -> list[str]:
    """One line per difference. Empty when every file is live exactly as it is at the ref."""
    problems = []
    for url_path, (repo_path, want) in sorted(expected.items()):
        status, got = fetcher(url_path)
        if status != 200:
            problems.append(f"{url_path}: HTTP {status}, expected {repo_path}")
        elif got != want:
            problems.append(f"{url_path}: live is {len(got)} bytes ({digest(got)}), "
                            f"{repo_path} is {len(want)} bytes ({digest(want)})")
    return problems


def marker_commit(status: int, body: bytes) -> str | None:
    """The commit the live marker names, or None when there is no readable marker."""
    if status != 200:
        return None
    try:
        named = json.loads(body).get("commit")
    except (ValueError, AttributeError):
        return None
    return named if isinstance(named, str) else None


def published_trees_equal(a: str, b: str, trees) -> bool | None:
    """Whether two commits publish the same files; None when this checkout lacks one of them.
    A ref that moved on with docs or code only still has the deployed site."""
    code = subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", a, b, "--", *trees],
                          capture_output=True).returncode
    return {0: True, 1: False}.get(code)


def marker_problem(named: str | None, commit: str, ref: str, key: str, trees) -> str | None:
    """A sentence when the marker does not account for the ref; None when it does."""
    if named is None:
        return f"/{key}: missing or unreadable, so nothing says which commit is live"
    if named == commit:
        return None
    same = published_trees_equal(named, commit, trees)
    if same is None:
        return f"/{key}: names {named[:7]}, a commit this checkout does not have"
    if not same:
        return f"/{key}: names {named[:7]}, and published files changed between it and {ref} ({commit[:7]})"
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", default="origin/main", help="the git ref live should equal")
    ap.add_argument("--site", default=SITE)
    args = ap.parse_args(argv)

    commit = git("rev-parse", args.ref).decode().strip()
    dp = deploy_module()
    expected = expected_files(args.ref, dp.public_trees())

    def fetcher(path: str) -> tuple[int, bytes]:
        return fetch(args.site + urllib.parse.quote(path))

    problems = compare(expected, fetcher)
    named = marker_commit(*fetcher("/" + dp.MARKER_KEY))
    problem = marker_problem(named, commit, args.ref, dp.MARKER_KEY, dp.public_trees())
    if problem:
        problems.append(problem)

    print(f"{len(expected)} published file(s) and /{dp.MARKER_KEY} checked against "
          f"{args.ref} ({commit[:7]}) at {args.site}")
    if named and named != commit and not problem:
        print(f"  deployed from {named[:7]}; {args.ref} has moved on without changing a published file")
    for line in problems:
        print(f"  DIFFERS  {line}")
    print(f"live == {args.ref}" if not problems else f"{len(problems)} difference(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
