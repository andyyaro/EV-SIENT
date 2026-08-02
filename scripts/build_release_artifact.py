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
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INCLUDE = ["src", "tests", "scripts", "data/inputs", "data/anchors", "data/observed", "data/provenance",
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
#: against the synthetic inputs and generates their own. Five scripts do contain real
#: identifiers and are excluded by the allowlist below rather than by hoping.
#:
#: This paragraph used to add that "`src/` and `data/anchors/` were verified to contain zero
#: real identifiers". That was false when written and stayed false: `src/fcf_m2/economics.py`
#: carried a comment naming one of the study's real commuter garages, and it shipped inside
#: every public archive while the build printed "verified: no real facility identifier appears
#: in the archive". The whole-string search could not see a distinctive fragment of a name.
#: The claim is removed rather than repaired, because the guarantee does not come from any
#: directory having been audited once — it comes from `assert_no_real_identifiers` inspecting
#: the finished archive on every build, which is the only form of it that cannot go stale.
PUBLIC_INCLUDE = [
    "src", "data/anchors", "data/observed", "pyproject.toml", "requirements-lock.txt",
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
    # scripts/verify.sh is NOT here, and was until a pre-release audit ran it inside a built
    # installer: it failed 36 of its 40 gates with 35 "No such file or directory" lines,
    # because its gates reach for tests/, docs/, matlab/ and data/contract/ — none of which
    # this bundle contains, by design. Nothing in the bundle tells a recipient to run it, so
    # its only possible effect was to make someone who found it conclude the software was
    # broken. An honest absence beats a check that cannot pass.
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


def archive_path(path: Path) -> str:
    """A repo-relative path with forward slashes, on every operating system.

    `str(p.relative_to(ROOT))` returns backslashes on Windows, and both places this script used
    it were then compared against, or written as, the forward-slash keys of
    `PUBLIC_SUBSTITUTIONS`. Neither comparison could ever match on a Windows runner.

    Measured on the packaging workflow's first successful run: the Windows artifact shipped the
    synthetic inputs at their own `data/synthetic/...` paths instead of at the four paths the
    model reads, so a recipient's first run would have found no inputs at all — and 58 of its 60
    RELEASE_MANIFEST entries carried backslash keys that matched none of the names in the
    archive beside them. The macOS artifact from the same run was correct, which is exactly why
    building on one platform and assuming the other proves nothing.
    """
    return path.relative_to(ROOT).as_posix()


def substituted_name(rel: str, substitutions: dict) -> str:
    """The name a file is stored under: its own, unless a synthetic file stands in for a real
    one, in which case the REAL name so the model reads it unchanged.

    Split out from the archive loop so it can be tested against Windows-shaped input on any
    machine. The bug it exists for was invisible to every test in this repository, because none
    of them ran where the path separator differs.
    """
    for real_rel, synth_rel in substitutions.items():
        if rel == synth_rel:
            return real_rel
    return rel


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
Reproduction (fresh environment). Requires Python 3.11 or newer.

macOS / Linux:
  python3 -m venv venv && venv/bin/pip install -e . -c requirements-lock.txt
  venv/bin/python -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run
  venv/bin/python -m fcf_m2.workflow validate-contract data/outputs/v3_run/contract

Windows (PowerShell or cmd):
  python -m venv venv
  venv\Scripts\pip install -e . -c requirements-lock.txt
  venv\Scripts\python -m fcf_m2.workflow run --mode milestone2_v3 --out data\outputs\v3_run
  venv\Scripts\python -m fcf_m2.workflow validate-contract data\outputs\v3_run\contract

(The Windows lines were missing until 2026-08-02. Half the artifacts this project
builds are for Windows, and the only reproduction instructions shipped in them
could not be run there.)

This public bundle ships SYNTHETIC site inputs (DEC-020) and no test suite, so the
numbers it produces describe invented sites and cannot be compared with the study.
"""



#: Words that appear in facility names and identify nothing. Kept explicit and short: every
#: entry here is a hole in the guard, so each one has to be a word that could not name a place.
GENERIC_NAME_WORDS = {
    "the", "and", "of", "at", "center", "centre", "library", "garage", "commuter", "park",
    "community", "regional", "county", "city", "government", "public", "branch", "station",
    "school", "high", "middle", "elementary", "recreation", "district", "north", "south",
    "east", "west", "central", "main", "street", "road", "avenue", "drive", "lane", "plaza",
    "building", "complex", "facility", "office", "annex", "hall", "municipal", "services",
    # Added after the token rule fired on ("safety_subscore", "Safety") in
    # src/fcf3d/build_sites.py -- a scoring-dimension label with no facility in it.
    "safety", "training", "potomac",
}


def jurisdiction_words(rows) -> set[str]:
    """Words naming a place rather than a building, derived from the data.

    Deliberately NOT protected, and the reasoning is the same one already recorded below for
    city and state: the study is openly about Fairfax City, Fairfax County and Prince William
    County — it says so in its README, its title and its public website. DEC-016 protects
    *which buildings were assessed and what was found about them*. A jurisdiction reveals
    neither, and searching for one fires on sentences like `config.py`'s "invented data must
    not be able to claim Fairfax City or Prince William County", which is a comment enforcing
    DEC-016 rather than breaking it.

    Derived from the `city` column plus the two county names, so it tracks the data instead of
    being a hand-list that goes stale.
    """
    words = {"prince", "william", "fairfax", "virginia"}
    for row in rows:
        for token in re.split(r"[^A-Za-z]+", row.get("city") or ""):
            if token:
                words.add(token.lower())
    return words


def distinctive_tokens(names, jurisdictions=frozenset()) -> set[str]:
    """Name fragments that identify one facility and only one.

    A token qualifies if it is at least five characters, is not a generic place-word, is not a
    jurisdiction, and appears in exactly one facility name.

    `Neabsco` qualifies. `Commuter`, `Garage` and `Regional` must not, and neither must
    `Safety` or `Training` — `("safety_subscore", "Safety")` in `build_sites.py` is a scoring
    label with no facility in it. A guard that fires on ordinary English gets exemptions bolted
    onto it until it stops guarding anything, so the bar for a token is that it could only be a
    name.

    **Known limit, stated rather than papered over:** a facility whose name is built entirely
    from jurisdiction and generic words — `Prince William County Public Safety Training Center`
    is exactly that — has no distinctive token at all, so token-level protection does nothing
    for it. It is still covered by the full-name, site-id and address searches. This function
    narrows the gap; it does not close it.
    """
    split = {}
    for name in names:
        for token in re.split(r"[^A-Za-z]+", name or ""):
            low = token.lower()
            if len(token) >= 5 and low not in GENERIC_NAME_WORDS and low not in jurisdictions:
                split.setdefault(token, set()).add(name)
    return {token for token, owners in split.items() if len(owners) == 1}


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
    # Whole strings are not enough, and the gap was live in a built artifact.
    #
    # This searched only the FULL site_name, so `src/fcf_m2/economics.py` shipped the comment
    # "(client's Neabsco pattern)" while the build printed "verified: no real facility
    # identifier appears in the archive (36 searched)". `Neabsco` is the distinctive half of
    # PWC002's real name, `Neabsco-Potomac Commuter Garage`, and README.md spells the full name
    # out — joining the two is trivial for anyone who has both. The check said the archive was
    # clean and it was not.
    #
    # So DISTINCTIVE TOKENS of each facility name are searched too. "Distinctive" is doing real
    # work: a facility name is mostly generic words — Library, Center, Garage, Community,
    # Regional, Park — and searching those would fire on ordinary prose and train whoever hits
    # it to add exemptions, which is how a guard dies. A token counts only if it is long enough
    # to be a name and appears in no more than one facility.
    real_rows = list(csv.DictReader((ROOT / "data/inputs/real_sites_v2.csv").open()))
    needles = ({r["site_id"] for r in real_rows}
               | {r["site_name"] for r in real_rows}
               | {r["address"] for r in real_rows})
    needles = {n.strip() for n in needles if len(n.strip()) >= 5}
    needles |= distinctive_tokens((r["site_name"] for r in real_rows),
                                  jurisdiction_words(real_rows))

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
        "files": {archive_path(p): sha256(p) for p in sorted(files)},
    }

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            # The synthetic file is written under the REAL file's name so the model reads it
            # unchanged. Its own contents announce that every value is invented.
            z.write(p, substituted_name(archive_path(p), substitutions))
        z.writestr("RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
        z.writestr("LIMITATIONS.txt", LIMITATIONS)
        z.writestr("REPRODUCTION.txt", REPRO_PUBLIC if public else REPRO)

    if public:
        assert_no_real_identifiers(zpath)

    # newline="\n": see the note in .github/workflows/package.yml. A checksum file with
    # CRLF endings cannot be verified with `shasum -c`, and this one had the same defect
    # waiting for the first person to build on Windows.
    (out / f"fcf_m2_v3_release_{stamp}.sha256").write_text(
        sha256(zpath) + f"  {zpath.name}\n", encoding="utf-8", newline="\n")
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
