"""One command that starts the desktop tier: ``fcf-platform``.

Why a launcher is the last piece rather than a packaged application
-------------------------------------------------------------------
DEC-015 chose a Python-native local server over a Tauri/Electron shell, so "the desktop app"
is not an app in the sense of a signed bundle you drag to Applications. It is this: a command
that makes sure the bundle is built, starts the loopback server, and opens a browser at it.

That leaves one honest gap, and this module's job is to close it *without pretending*. Before
this existed the instruction was `python -m fcf_m2.server` — which works only if you have
already built the generated surfaces, and fails with a bare traceback if you have not. A
person following the README got an error that named a missing directory rather than the step
they had skipped.

What it will and will not do for you
------------------------------------
It **builds** generated artifacts that are missing, because those are reproducible by
definition — that is what "generated" means, and refusing to run because a derived file is
absent is pedantry rather than rigour.

It **refuses** to run when a *source* input is missing, and says which one. The difference
matters: a missing generated file is an inconvenience, a missing input is a different study.

It never regenerates something that already exists. A launcher that quietly rebuilt the
contract on every start would make "the numbers changed and I do not know why" a routine
experience.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: (path in the bundle, the declared command that produces it). Every entry is built by
#: running the same script a person would run — never by importing and calling, for the same
#: reason the operations registry declares commands rather than callables.
GENERATED = [
    # The contract comes first because every surface below is built from it. It was previously
    # listed as a REQUIRED SOURCE, which made the launcher refuse to start on a fresh install
    # over a file the model produces in one command — exactly the pedantry this module's
    # docstring warns against. On a public installer, where the real contract is deliberately
    # absent, that refusal made the platform unreachable.
    ("data/contract/v1/contract_manifest.json",
     # --contract-dir is not optional here. Without it the contract lands under --out, and
     # build_platform_web.py reads data/contract/v1 — so the launcher would run the model
     # successfully and then fail on the next step claiming the contract did not exist. The
     # declared output path and what the command actually produces have to be the same file.
     ["-m", "fcf_m2.workflow", "run", "--mode", "milestone2_v3",
      "--out", "data/outputs/v3_run", "--contract-dir", "data/contract/v1"]),
    ("site/platform/provenance_v1.json", ["scripts/build_platform_web.py"]),
    ("site/platform/operations.json", ["scripts/build_platform_web.py"]),
    ("site/platform/field_schema.json", ["scripts/build_field_schema.py"]),
    ("site/platform/engines.json", ["scripts/build_engine_record.py", "--allow-missing"]),
    ("site/platform/simulink.json", ["scripts/build_simulink_view.py", "--allow-missing"]),
    ("site/platform/surfaces.json", ["scripts/build_platform_surfaces.py"]),
    ("site/platform/explorer/index.html", ["scripts/build_platform_surfaces.py"]),
]

#: Source files that cannot be regenerated. If one of these is gone, something is wrong that a
#: build step cannot fix, and guessing would be worse than stopping.
REQUIRED_SOURCES = [
    "site/platform/index.html",
    "site/platform/app.js",
    "site/platform/field_validate.js",
]


def missing_sources() -> list[str]:
    return [p for p in REQUIRED_SOURCES if not (REPO / p).is_file()]


def missing_generated() -> list[tuple[str, list[str]]]:
    return [(path, cmd) for path, cmd in GENERATED if not (REPO / path).exists()]


def build(commands: list[list[str]], python: str | None = None) -> None:
    """Run each build script once, in declaration order, reporting as it goes."""
    interpreter = python or sys.executable
    seen: set[tuple[str, ...]] = set()
    for command in commands:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        print(f"  building: {' '.join(command)}")
        result = subprocess.run([interpreter, *command], cwd=REPO,
                                capture_output=True, text=True)
        if result.returncode != 0:
            # Show the real output. A launcher that swallows a build failure and then serves a
            # half-built page is worse than one that stops.
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(f"\n  build step failed: {' '.join(command)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fcf-platform",
        description="Start the Future City Fellowship platform on this machine.")
    parser.add_argument("--port", type=int, default=0,
                        help="0 (the default) asks the operating system for a free port")
    parser.add_argument("--no-browser", action="store_true",
                        help="print the URL instead of opening it")
    parser.add_argument("--check", action="store_true",
                        help="report what would be built, then exit without serving")
    args = parser.parse_args(argv)

    print("Future City Fellowship — platform, desktop tier\n")

    absent = missing_sources()
    if absent:
        print("  Cannot start. These are source files, not generated ones, so no build step\n"
              "  can recreate them:\n")
        for path in absent:
            print(f"    missing: {path}")
        print("\n  This usually means an incomplete checkout. `git status` will say.")
        return 1

    pending = missing_generated()
    if args.check:
        if pending:
            print(f"  {len(pending)} generated artifact(s) missing; starting would build them:")
            for path, command in pending:
                print(f"    {path}  <- {' '.join(command)}")
        else:
            print("  Everything the platform needs is present. Nothing would be rebuilt.")
        return 0

    if pending:
        print(f"  {len(pending)} generated artifact(s) missing — building them once.")
        print("  (Existing artifacts are never rebuilt: numbers that change without a reason\n"
              "   you asked for are the thing this project is trying hardest to avoid.)\n")
        build([command for _path, command in pending])
        print()

    # Imported here rather than at module scope so `--check` works even if the bundle is
    # incomplete — server.py raises at import time if the web root is absent.
    from . import server

    httpd, url, _token = server.serve(port=args.port, open_browser=False)
    print(f"  serving  {url}")
    print("  bound to loopback only; the token in that URL is required for every API call")
    print("  this tier can RUN the model — the web tier can only read what it produced")
    print("\n  Ctrl-C to stop")

    if not args.no_browser:
        webbrowser.open(url)

    import threading
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n  stopping")
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
