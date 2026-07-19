"""Build a frozen, hash-logged milestone release artifact (PY-10).

Creates <out>/fcf_m2_v3_release_<date>.zip containing the source snapshot, generated
outputs, contract, environment record, limitations, and exact reproduction commands,
plus a SHA-256 manifest. Nothing is pushed or published.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INCLUDE = ["src", "tests", "scripts", "data/inputs", "data/anchors", "data/provenance",
           "data/cache/boundaries", "docs", "pyproject.toml", "requirements-lock.txt",
           "README.md", "Makefile"]
OUTPUTS = ["data/outputs/v3_run", "data/outputs/legacy_check"]

LIMITATIONS = """\
Release limitations (read before use):
- Planning-support prototype. Not an engineering, permitting, budget, or procurement tool.
- Capacity is a placeholder at 12/12 sites (capacity_basis=placeholder) pending utility/facility data.
- Demand model is synthetic and uncalibrated; growth multipliers are provisional conventions.
- Costs are screening-class benchmarks; emissions use labeled benchmark assumptions
  (grid factor eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh, refresh annually).
- 0 of 12 sites have High data confidence.
- Expansion-trigger policy is proposed configuration, not adopted municipal policy.
"""

REPRO = """\
Reproduction (fresh environment):
  python3 -m venv venv && venv/bin/pip install -e .[test] -c requirements-lock.txt
  venv/bin/python -m pytest tests/ -q                      # all tests must pass
  venv/bin/python -m fcf_m2.workflow run --mode legacy_v2   --out data/outputs/legacy_check
  venv/bin/python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run
  venv/bin/python -m fcf_m2.workflow validate-contract data/outputs/v3_run/contract
"""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(out_dir: str | None = None) -> Path:
    out = Path(out_dir) if out_dir else ROOT / "release"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    zpath = out / f"fcf_m2_v3_release_{stamp}.zip"

    files: list[Path] = []
    for item in INCLUDE + OUTPUTS:
        p = ROOT / item
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(q for q in p.rglob("*") if q.is_file() and "__pycache__" not in str(q))

    manifest = {
        "release": f"fcf_m2 v3.0.0 ({stamp})",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "files": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(files)},
    }

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT))
        z.writestr("RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
        z.writestr("LIMITATIONS.txt", LIMITATIONS)
        z.writestr("REPRODUCTION.txt", REPRO)

    (out / f"fcf_m2_v3_release_{stamp}.sha256").write_text(sha256(zpath) + f"  {zpath.name}\n")
    print(f"release artifact: {zpath} ({zpath.stat().st_size/1e6:.1f} MB, {len(files)} files)")
    return zpath


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
