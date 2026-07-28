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

The synthetic counterpart now exists (DEC-020): four files under ``data/synthetic/`` are
substituted for the real inputs, and ``--public`` builds a complete, runnable artifact. It
still refuses — loudly, deleting the archive — if the finished bundle is found to contain any
real facility identifier, which is a check on the OUTPUT rather than a refusal to try.

*(This paragraph previously said no synthetic set existed and that ``--public`` refused
outright. Both were true when written and both were false for weeks afterwards.)*
"""

from __future__ import annotations

import csv
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


#: A public artifact ships the MODEL and SYNTHETIC INPUTS ONLY.
#:
#: Swapping the four input files was the obvious approach and it is not close to sufficient.
#: Inspecting a built artifact showed **87 files leaking 36 distinct real facility
#: identifiers** — not from the inputs, which had been substituted correctly, but from every
#: derived artifact: model outputs under data/outputs, the test fixtures, the NFC placement
#: cards and tag payloads, the contract, and the docs. The real site identities are woven
#: through everything the study has ever produced.
#:
#: So the public artifact carries no derived results at all. The recipient runs the model
#: against the synthetic inputs and generates their own. `src/` and `data/anchors/` were
#: verified to contain zero real identifiers; five scripts do contain them and are excluded
#: by the allowlist below rather than by hoping.
PUBLIC_INCLUDE = [
    "src", "data/anchors", "pyproject.toml", "requirements-lock.txt",
    # The platform's hand-written sources. Each was checked for real identifiers before being
    # added; app.js carried one, in a comment showing a deep-link example, and now uses the
    # synthetic id space. The GENERATED surfaces (provenance_v1.json, the contract copies, the
    # explorer and dashboard) are deliberately absent — they are built from real data. A
    # recipient generates their own by running the model on the synthetic inputs.
    "site/platform/index.html", "site/platform/app.js",
    "site/platform/styles.css", "site/platform/field_validate.js",
]

#: Only the scripts a recipient needs to run the model and rebuild the synthetic set.
PUBLIC_SCRIPTS = [
    "scripts/build_synthetic_inputs.py",
    "scripts/verify.sh",
    # What `fcf-platform` runs to build the surfaces it needs. Without these the launcher
    # correctly refuses to start, which is honest but leaves the recipient with a CLI and no
    # platform.
    "scripts/build_platform_web.py",
    "scripts/build_field_schema.py",
    "scripts/build_engine_record.py",
    "scripts/build_simulink_view.py",
    "scripts/build_platform_surfaces.py",
]

PUBLIC_SUBSTITUTIONS = {
    "data/inputs/real_sites_v2.csv":
        "data/synthetic/synthetic_sites_v2.csv",
    "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv":
        "data/synthetic/synthetic_v2_electrical_risk_summary.csv",
    "data/inputs/legacy_matlab_site_meta.csv":
        "data/synthetic/synthetic_matlab_site_meta.csv",
    "data/provenance/field_provenance_v1.csv":
        "data/synthetic/synthetic_field_provenance_v1.csv",
}


def resolve_public(public: bool) -> tuple[dict, list[str]]:
    """Return (substitutions, problems) for a public build.

    Refuses rather than degrades. A public artifact that silently omitted an input would ship
    an installer that starts and fails on first run — the recipient would conclude the model
    was broken rather than absent, which is the worse of the two misunderstandings.
    """
    if not public:
        return {}, []
    problems = []
    for synth_rel in PUBLIC_SUBSTITUTIONS.values():
        if not (ROOT / synth_rel).is_file():
            problems.append(f"  {synth_rel} is missing; run scripts/build_synthetic_inputs.py")
    for private, what in PRIVATE_PATHS.items():
        if not any(k.startswith(private) for k in PUBLIC_SUBSTITUTIONS):
            problems.append(f"  {private} has no synthetic substitute ({what})")
    return dict(PUBLIC_SUBSTITUTIONS), problems


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

#: Written into the INTERNAL archive, which carries tests/.
REPRO = """\
Reproduction (fresh environment):
  python3 -m venv venv && venv/bin/pip install -e .[test] -c requirements-lock.txt
  venv/bin/python -m pytest tests/ -q                      # all tests must pass
  venv/bin/python -m fcf_m2.workflow run --mode legacy_v2   --out data/outputs/legacy_check
  venv/bin/python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run
  venv/bin/python -m fcf_m2.workflow validate-contract data/outputs/v3_run/contract
"""

#: Written into the PUBLIC archive, which does NOT carry tests/. The internal text above was
#: being written into every archive unconditionally, so a public recipient was told to run
#: `pytest tests/` against a bundle with no tests directory -- their first instruction failed.
REPRO_PUBLIC = """\
Reproduction (fresh environment):
  python3 -m venv venv && venv/bin/pip install -e . -c requirements-lock.txt
  venv/bin/python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run
  venv/bin/python -m fcf_m2.workflow validate-contract data/outputs/v3_run/contract

This public bundle ships SYNTHETIC site inputs (DEC-020) and no test suite, so the
numbers it produces describe invented sites and cannot be compared with the study.
"""



def assert_no_real_identifiers(zip_path: Path) -> None:
    """Open the finished archive and prove it carries nothing real. Delete it if it does.

    This is the check the requirement actually asks for — *verified by inspecting the built
    package, not by assuming*. It exists because the assumption failed: an artifact whose
    inputs had been correctly substituted still shipped 36 real facility identifiers through
    files nobody had thought of.

    Deleting the archive rather than merely warning is deliberate. A leaking artifact that
    exists on disk is one command away from being attached to a release.
    """
    # Building-level identifiers only: the site id, the facility name, the street address.
    #
    # City and state are deliberately NOT searched. The first version included them and fired
    # on `"Building official / electrical inspector (Fairfax City / PWC)"` in standards.py —
    # which names the permitting authority for a jurisdiction, not a facility. The study is
    # openly about Fairfax City and Prince William County; that is in its README, its title and
    # its public website. What DEC-016 protects is *which buildings were assessed and what was
    # found about them*, and a jurisdiction name reveals neither.
    real_rows = list(csv.DictReader((ROOT / "data/inputs/real_sites_v2.csv").open()))
    needles = ({r["site_id"] for r in real_rows}
               | {r["site_name"] for r in real_rows}
               | {r["address"] for r in real_rows})
    needles = {n.strip() for n in needles if len(n.strip()) >= 5}

    found: dict[str, list[str]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            try:
                text = archive.read(info.filename).decode("utf-8", errors="ignore")
            except Exception:
                continue
            for needle in needles:
                if needle in text:
                    found.setdefault(needle, []).append(info.filename)

    if found:
        zip_path.unlink(missing_ok=True)
        lines = [f"  {needle!r} in {files[:3]}" for needle, files in list(found.items())[:10]]
        raise SystemExit(
            f"REFUSING: the built public artifact contains {len(found)} real facility "
            f"identifier(s).\n" + "\n".join(lines)
            + f"\n\nThe archive has been deleted. DEC-016 forbids publishing this data.")
    print(f"  verified: no real facility identifier appears in the archive "
          f"({len(needles)} searched)")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(out_dir: str | None = None, public: bool = False) -> Path:
    substitutions, problems = resolve_public(public)
    if problems:
        raise SystemExit("REFUSING to build a public artifact:\n" + "\n".join(problems)
                         + "\n\nDEC-016 requires a public installer to ship SYNTHETIC inputs.")
    out = Path(out_dir) if out_dir else ROOT / "release"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    zpath = out / f"fcf_m2_v3_release_{stamp}.zip"

    files: list[Path] = []
    wanted = (PUBLIC_INCLUDE + PUBLIC_SCRIPTS) if public else (INCLUDE + OUTPUTS)
    for item in wanted:
        p = ROOT / item
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(q for q in p.rglob("*") if q.is_file() and "__pycache__" not in str(q))

    if public:
        # The synthetic files are added explicitly, under the names the model expects.
        for real_rel in PUBLIC_SUBSTITUTIONS:
            files.append(ROOT / PUBLIC_SUBSTITUTIONS[real_rel])

    manifest = {
        "release": f"fcf_m2 v3.0.0 ({stamp})",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "files": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(files)},
    }

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = str(p.relative_to(ROOT))
            # The synthetic file is written under the REAL file's name so the model reads it
            # unchanged. Its own contents announce that every value is invented.
            target = rel
            for real_rel, synth_rel in substitutions.items():
                if rel == synth_rel:
                    target = real_rel      # written under the name the model reads
            z.write(p, target)
        z.writestr("RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
        z.writestr("LIMITATIONS.txt", LIMITATIONS)
        z.writestr("REPRODUCTION.txt", REPRO_PUBLIC if public else REPRO)

    if public:
        assert_no_real_identifiers(zpath)

    (out / f"fcf_m2_v3_release_{stamp}.sha256").write_text(sha256(zpath) + f"  {zpath.name}\n")
    kind = "PUBLIC (synthetic inputs)" if public else "INTERNAL (real inputs - DO NOT PUBLISH)"
    print(f"release artifact [{kind}]: {zpath} "
          f"({zpath.stat().st_size/1e6:.1f} MB, {len(files)} files)")
    for real_rel, synth_rel in substitutions.items():
        print(f"  substituted {synth_rel} -> {real_rel}")
    return zpath


if __name__ == "__main__":
    # Parsed explicitly rather than positionally. The first version took sys.argv[1] as the
    # output directory, so `--public` was silently treated as a path and the guard never ran —
    # it cheerfully created a directory literally named "--public".
    args = [a for a in sys.argv[1:] if a != "--public"]
    main(args[0] if args else None, public="--public" in sys.argv[1:])
