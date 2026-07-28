"""Build a frozen, hash-logged milestone archive (PY-10). **INTERNAL — NOT FOR PUBLICATION.**

Creates <out>/fcf_m2_v3_release_<date>.zip containing the source snapshot, generated
outputs, contract, environment record, limitations, and exact reproduction commands,
plus a SHA-256 manifest. Nothing is pushed or published by this script.

Why the warning is this loud
----------------------------
``INCLUDE`` carries ``data/inputs``, which holds ``real_sites_v2.csv`` — facility-level
electrical and occupancy data for twelve named public buildings in Fairfax City and Prince
William County. That is deliberate for an *internal* archive: the point of a milestone
snapshot is that it reproduces the run, and the run needs its inputs.

It is exactly wrong for a *public* artifact. **DEC-016** decided the real input data stays
private and that any public installer ships a synthetic set instead. Nothing about the name
"release artifact" signals which of those two things this produces, so the guard below makes
the distinction explicit rather than relying on whoever runs it next remembering DEC-016.

**There is currently no synthetic counterpart to real_sites_v2.csv**, so the public installer
DEC-016 describes cannot be built yet. ``--public`` therefore refuses rather than quietly
producing an artifact that cannot run.
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

#: Paths carrying real, non-public site data. Named so the refusal below can say WHICH file
#: it is protecting rather than failing with a generic message.
PRIVATE_PATHS = {"data/inputs": "real_sites_v2.csv — twelve named public facilities' "
                                "electrical and occupancy data (DEC-016)"}


def refuse_if_public(public: bool) -> None:
    """A public artifact may not carry the real site inputs, and cannot yet be built without
    them, so it is refused with the reason rather than shipped incomplete."""
    if not public:
        return
    carried = [p for p in INCLUDE if p in PRIVATE_PATHS]
    raise SystemExit(
        "REFUSING to build a public artifact.\n\n"
        + "".join(f"  {p} carries {PRIVATE_PATHS[p]}\n" for p in carried)
        + "\nDEC-016 requires a public installer to ship SYNTHETIC inputs. No synthetic\n"
          "counterpart to real_sites_v2.csv exists in this repository, so a public artifact\n"
          "would either leak the real data or be unable to run the model at all.\n\n"
        "Build the synthetic input set first, then give this script a PUBLIC_INCLUDE list.\n"
        "Without --public this script still builds the INTERNAL archive, which is what it\n"
        "has always produced.")

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


def main(out_dir: str | None = None, public: bool = False) -> Path:
    refuse_if_public(public)
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
    # Parsed explicitly rather than positionally. The first version took sys.argv[1] as the
    # output directory, so `--public` was silently treated as a path and the guard never ran —
    # it cheerfully created a directory literally named "--public".
    args = [a for a in sys.argv[1:] if a != "--public"]
    main(args[0] if args else None, public="--public" in sys.argv[1:])
