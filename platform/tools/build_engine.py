"""Package the engine for the browser: public/runtime/engine/engine-<sha12>.zip and engine.json.

The archive holds `src/fcf_m2/*.py` and the data files a browser run reads, laid out as the
repository is, so `ROOT = Path(__file__).parents[2]` in the engine resolves inside it once the
worker unpacks it to /work/pkgroot. Nothing else goes in.

Which data files a browser run reads is measured, not assumed: the script runs browser_api
natively (propose, check, accept, run, explain, stability, output_files) on Example City and on the
12-site synthetic cohort with an audit hook recording every file opened, and refuses to build
if that set is not exactly ALLOWED_DATA. Real study inputs must never reach the bundle
(DEC-016), so anything under PRIVATE_PREFIXES fails the build even if it is allowlisted.

The zip is deterministic (sorted entries, fixed timestamps and modes), so the same sources give
the same SHA-256 and the same immutable file name.

Usage: venv/bin/python platform/tools/build_engine.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "platform/app/public/runtime/engine"

#: Every data file the browser run path may read. A change to the engine that reads another
#: file fails the build until the file is reviewed and added here.
ALLOWED_DATA = ["data/anchors/anchor_set_v1.json"]

#: The reference study's real inputs and everything derived from them.
PRIVATE_PREFIXES = ("data/inputs/", "data/provenance/", "data/contract/", "data/observed/",
                    "data/outputs/", "data/cache/")

#: What the trace runs through browser_api: invented sites only.
TRACE_TABLES = ["data/intake/example/example_city_facilities.csv",
                "data/synthetic/synthetic_sites_v2.csv"]

FIXED_TIME = (1980, 1, 1, 0, 0, 0)

_TRACE = r"""
import csv, json, sys
from pathlib import Path

repo = Path(sys.argv[1])
tables = []
for rel in sys.argv[2:]:
    with open(repo / rel, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    tables.append({"fileName": Path(rel).name, "columns": rows[0], "rows": rows[1:]})

opened = set()
def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, Path)):
        opened.add(str(Path(args[0]).resolve()))
sys.addaudithook(hook)

from fcf_m2 import browser_api as api
for table in tables:
    api.reset()
    if json.loads(api.propose(json.dumps(table)))["refused"]:
        sys.exit(f"{table['fileName']} was refused by intake")
    api.check()
    api.accept("{}")
    run = json.loads(api.run(json.dumps({"asOf": "2026-10-18"})))
    for site in run["sites"]:
        api.explain(site["siteId"])
    api.stability("{}")
    api.output_files()
print(json.dumps(sorted(opened)))
"""


def traced_data_files() -> list[str]:
    """Repository files (other than the engine's own modules) a browser-path run opens."""
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    out = subprocess.run([sys.executable, "-c", _TRACE, str(REPO), *TRACE_TABLES], env=env,
                         capture_output=True, text=True, cwd=REPO / "platform")
    if out.returncode:
        sys.exit(f"The trace run failed:\n{out.stderr}")
    opened = json.loads(out.stdout.strip().splitlines()[-1])
    found = set()
    for path in map(Path, opened):
        try:
            rel = path.relative_to(REPO).as_posix()
        except ValueError:
            continue  # the session's temp directory, the interpreter's own files
        if rel.startswith(("venv/", ".venv/")) or "__pycache__" in rel:
            continue
        if rel.startswith("src/fcf_m2/") and rel.endswith(".py"):
            continue
        found.add(rel)
    return sorted(found)


def engine_sources() -> list[str]:
    return sorted(p.relative_to(REPO).as_posix() for p in (REPO / "src/fcf_m2").rglob("*.py")
                  if "__pycache__" not in p.parts)


def version() -> str:
    pkg = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
    git = lambda *a: subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()
    sha = git("rev-parse", "--short=7", "HEAD") or "nogit"
    dirty = git("status", "--porcelain", "--", "src/fcf_m2", *ALLOWED_DATA)
    return f"{pkg}+{sha}{'.dirty' if dirty else ''}"


def main() -> None:
    traced = traced_data_files()
    unexpected = sorted(set(traced) - set(ALLOWED_DATA))
    unused = sorted(set(ALLOWED_DATA) - set(traced))
    if unexpected:
        sys.exit("A browser run read files that are not in ALLOWED_DATA. Review them and add "
                 "them, or stop the engine reading them:\n  " + "\n  ".join(unexpected))
    if unused:
        sys.exit("ALLOWED_DATA lists files a browser run no longer reads; remove them:\n  "
                 + "\n  ".join(unused))

    files = engine_sources() + sorted(ALLOWED_DATA)
    private = [f for f in files if f.startswith(PRIVATE_PREFIXES)]
    if private:
        sys.exit("Refusing to package private study files (DEC-016):\n  " + "\n  ".join(private))

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "engine.zip.tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            info = zipfile.ZipInfo(rel, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            zf.writestr(info, (REPO / rel).read_bytes())
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    name = f"engine-{digest[:12]}.zip"
    for old in OUT.glob("engine-*.zip"):
        old.unlink()
    tmp.rename(OUT / name)
    manifest = {"version": version(), "file": name, "sha256": digest, "files": files}
    (OUT / "engine.json").write_text(json.dumps(manifest, indent=2) + "\n")
    size = (OUT / name).stat().st_size
    print(f"{name}: {len(files)} files, {size / 1024:.1f} KB, version {manifest['version']}")
    print("Data files: " + ", ".join(ALLOWED_DATA))


if __name__ == "__main__":
    main()
