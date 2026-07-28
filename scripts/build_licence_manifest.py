#!/usr/bin/env python3
"""Collect the licences of everything a distributed artifact carries.

Why this is generated rather than hand-listed
---------------------------------------------
A hand-written attribution file is a claim about a dependency set that changes without it. This
reads the **installed distribution metadata** — the same metadata pip resolved — so the list
cannot silently fall behind `requirements-lock.txt`.

That guarantee holds only if the interpreter running this script is the project's. It reads
whatever is installed for `sys.executable` and has no other source of truth, so run from a
system Python it will happily describe a completely different dependency set. That is not
hypothetical: run once from the ambient macOS interpreter it dropped 20 of this project's
dependencies (pandas, matplotlib, pytest, segno, python-docx…), added 12 the project does not
use (playwright, PyQt6-QScintilla, CairoSVG…), printed `all licences resolved`, and exited 0.
A licence manifest that omits shipped dependencies is an attribution failure, not a cosmetic
one, so `check_environment` now refuses to write unless every package the lock requires for
this interpreter is actually present.

What it does NOT do is guess. Modern packaging moved licence information from the `License:`
field to `License-Expression` and `License-File`, and a great many distributions now leave the
old field empty. Reporting those as "unstated" is accurate; inventing "MIT" because the project
is probably MIT would be exactly the fabrication this project refuses. Anything unresolved is
listed as such, loudly, so a human closes it rather than a script papering over it.

Two attributions cannot come from Python metadata at all and are stated explicitly, with the
reason each applies:

* **CesiumJS** — Apache-2.0, vendored into the explorer by `scripts/vendor_cesium.sh`.
* **OpenStreetMap** — ODbL, because the explorer's fallback basemap is OSM-derived.
* **Google Photorealistic 3D Tiles** — Terms of Service, not a licence, and they bind whoever
  supplies the API key rather than this repository. Stated because the explorer can consume
  them, not because it ships them.

**GNU Octave is deliberately NOT listed as a bundled dependency.** `matlab/octave/` holds 19
files of *this project's own* `.m` shims, written to run under Octave — no Octave binary or
source is distributed, so its GPL does not attach to anything here. A user who wants that path
installs Octave themselves. Saying otherwise would over-claim an obligation, which is its own
kind of inaccuracy.

Run: python scripts/build_licence_manifest.py
"""

from __future__ import annotations

import importlib.metadata as metadata
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "THIRD_PARTY_LICENCES.json"
OUT_TEXT = REPO / "THIRD_PARTY_LICENCES.md"
LOCK = REPO / "requirements-lock.txt"

#: Attributions that do not come from Python packaging metadata. Each names why it applies.
NON_PYTHON = [
    {
        "name": "CesiumJS",
        "licence": "Apache-2.0",
        "why": "Vendored into explorer/web/vendor by scripts/vendor_cesium.sh and shipped with "
               "the 3D explorer.",
        "notice": "explorer/web/vendor/LICENSE-CesiumJS.txt (written by the vendoring script)",
    },
    {
        "name": "amazon-cognito-identity-js",
        "licence": "Apache-2.0",
        "why": "**Tracked and publicly shipped** at "
               "`site/www/vendor/amazon-cognito-identity.min.js` (112 KB), used by the "
               "assistant page's sign-in. Its own header declares "
               "`SPDX-License-Identifier: Apache-2.0`, `Copyright Amazon.com, Inc. or its "
               "affiliates`.",
        "notice": "site/www/vendor/amazon-cognito-identity.min.js (SPDX header in the file)",
    },
    {
        "name": "OpenStreetMap data",
        "licence": "ODbL 1.0",
        "why": "The explorer's fallback basemap is OSM-derived. Attribution is required on "
               "display, not merely in a file.",
        "notice": "https://www.openstreetmap.org/copyright",
    },
    {
        "name": "Google Photorealistic 3D Tiles",
        "licence": "Terms of Service (not an open-source licence)",
        "why": "The explorer can consume them when a key is supplied. It ships no key and no "
               "tiles, so the terms bind whoever supplies the key rather than this repository.",
        "notice": "https://developers.google.com/maps/documentation/tile/policies",
    },
    {
        "name": "US Census TIGER/Line",
        "licence": "Public domain (US Government work)",
        "why": "A filtered boundary extract is cached under data/cache/boundaries.",
        "notice": "data/cache/boundaries/ATTRIBUTION.md",
    },
]

#: Named here rather than inferred. Each is a dependency whose metadata does not state a
#: licence; the value is taken from the project's own published licence and the source is
#: recorded so the claim is checkable.
KNOWN_UNSTATED = {
    "numpy": ("BSD-3-Clause", "numpy/LICENSE.txt in the sdist"),
    "jsonschema": ("MIT", "python-jsonschema/jsonschema COPYING"),
    "pillow": ("MIT-CMU", "python-pillow/Pillow LICENSE"),
    "pytest": ("MIT", "pytest-dev/pytest LICENSE"),
}


def normalise(name: str) -> str:
    """PEP 503 name normalisation, so `typing_extensions` and `typing-extensions` are one."""
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def locked_requirements(lock_text: str) -> list[tuple[str, str | None]]:
    """(normalised name, environment marker) for every pin in a hashed lock file.

    Hash continuation lines, comments and blank lines are skipped. The marker is kept rather
    than dropped because at least one pin legitimately does not install everywhere:
    `referencing` needs `typing-extensions` only below Python 3.13, so on a newer interpreter
    its absence is correct and must not be reported as a broken environment.
    """
    out: list[tuple[str, str | None]] = []
    for raw in lock_text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "--", "-r")):
            continue
        line = line.split(" \\")[0].strip()
        if not line or "==" not in line:
            continue
        spec, _, marker = line.partition(";")
        name = spec.split("==")[0].split("[")[0].strip()
        if name:
            out.append((normalise(name), marker.strip() or None))
    return out


#: Present in every environment pip builds and in none of them by request. They are reported —
#: `pip` has always been in this manifest — but their presence is not evidence of anything, so
#: they are not treated as an unexplained extra.
ENVIRONMENT_PACKAGES = {"pip", "setuptools", "wheel"}


def check_environment(lock_text: str, installed: set[str]) -> tuple[list[str], list[str]]:
    """(missing, unexpected) — how this interpreter differs from `requirements-lock.txt`.

    Both directions matter and they fail differently.

    *Missing* is an attribution failure: a dependency the artifact ships would go unlisted.
    *Unexpected* is the opposite error and it is just as wrong — a manifest naming software the
    artifact does not carry is a false statement about what was distributed, and it is the
    likelier one in practice because a working venv accumulates tools. This repository's own
    venv had picked up Markdown, markdown-it-py and mdurl, none of which the release artifact
    contains and all of which a regeneration would have added.

    Both empty means the environment equals the lock, so the manifest is reproducible: anyone
    with the lock gets the same file, which is the only property that makes a generated
    artifact checkable at all.
    """
    try:
        from packaging.markers import Marker
    except ImportError:  # packaging is itself a locked dependency
        return (["packaging (import failed — this is not the project environment)"], [])

    expected = set()
    missing = []
    for name, marker in locked_requirements(lock_text):
        if marker is not None:
            try:
                if not Marker(marker).evaluate():
                    continue
            except Exception:
                pass  # an unparseable marker is treated as applying, which fails closed
        expected.add(name)
        if name not in installed:
            missing.append(name)
    unexpected = sorted(installed - expected - ENVIRONMENT_PACKAGES)
    return missing, unexpected


def licence_of(dist: metadata.Distribution) -> tuple[str, str]:
    """Return (licence, how it was determined). Never guesses."""
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return expression, "License-Expression metadata"
    stated = meta.get("License")
    if stated and len(stated) <= 60 and "\n" not in stated:
        return stated, "License metadata field"
    classifiers = [c for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")]
    if classifiers:
        return classifiers[-1].split("::")[-1].strip(), "trove classifier"
    name = (meta.get("Name") or "").lower()
    if name in KNOWN_UNSTATED:
        licence, source = KNOWN_UNSTATED[name]
        return licence, f"not in metadata; taken from {source}"
    return "UNRESOLVED", "no License-Expression, License field, or classifier"


def main() -> int:
    entries = []
    seen_names: set[str] = set()
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        # This project is not a third-party dependency of itself. It appeared twice — once as
        # the editable install and once as its dist-info — and as UNRESOLVED, which was true
        # but reported in the wrong section: the repository has no licence, and that is a
        # decision for its owner, not a gap in a dependency audit.
        if name.lower().replace("_", "-") == "fcf-m2":
            continue
        if name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        licence, how = licence_of(dist)
        entries.append({
            "name": name,
            "version": dist.version,
            "licence": licence,
            "determined_from": how,
        })
    entries.sort(key=lambda e: e["name"].lower())

    # Refuse BEFORE writing. A wrong manifest on disk is worse than none: it looks generated,
    # it is dated, and nothing downstream can tell it apart from a correct one.
    missing, unexpected = check_environment(
        LOCK.read_text(), {normalise(e["name"]) for e in entries})
    if missing or unexpected:
        print(f"REFUSING to write a licence manifest from this interpreter.\n"
              f"  {sys.executable}", file=sys.stderr)
        if missing:
            print(f"  {len(missing)} package(s) requirements-lock.txt requires are NOT "
                  f"installed here: {', '.join(sorted(missing))}\n"
                  f"    -> the manifest would omit dependencies the artifact ships.",
                  file=sys.stderr)
        if unexpected:
            print(f"  {len(unexpected)} package(s) installed here are NOT in the lock: "
                  f"{', '.join(unexpected)}\n"
                  f"    -> the manifest would attribute software the artifact does not carry.",
                  file=sys.stderr)
        print("  Build an environment from requirements-lock.txt and re-run. The manifest is "
              "reproducible only from the locked set.", file=sys.stderr)
        return 1

    unresolved = [e for e in entries if e["licence"] == "UNRESOLVED"]

    payload = {
        "schema": "fcf-licences/1",
        "note": ("Generated from installed distribution metadata. Nothing here is guessed: a "
                 "dependency whose licence the metadata does not state is reported UNRESOLVED "
                 "rather than assumed."),
        "octave_note": ("GNU Octave is NOT bundled. matlab/octave/ contains this project's own "
                        ".m shims written to run under Octave; no Octave binary or source is "
                        "distributed, so its GPL does not attach to any artifact here."),
        "python_dependencies": entries,
        "other_components": NON_PYTHON,
        "unresolved_count": len(unresolved),
        "this_project_licence": ("NOT STATED. The repository declares no licence and one has "
                                 "deliberately not been invented — choosing it is the owner's "
                                 "decision. Until it is chosen, no artifact should claim a "
                                 "licence for this project's own code."),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Third-party licences",
        "",
        "Generated by `scripts/build_licence_manifest.py` from installed distribution",
        "metadata. **Nothing here is guessed** — a dependency whose licence the metadata does",
        "not state is reported `UNRESOLVED` rather than assumed to be permissive.",
        "",
        "**GNU Octave is not bundled.** `matlab/octave/` holds this project's own `.m` shims,",
        "written to run under Octave. No Octave binary or source is distributed, so its GPL",
        "does not attach to anything here.",
        "",
        "**This project's own licence is not stated anywhere and has not been invented.**",
        "Choosing one is the owner's decision, not a packaging detail.",
        "",
        "## Components that are not Python packages",
        "",
        "| Component | Licence | Why it applies |",
        "|---|---|---|",
    ]
    for item in NON_PYTHON:
        lines.append(f"| {item['name']} | {item['licence']} | {item['why']} |")
    lines += ["", "## Python dependencies", "",
              "| Package | Version | Licence | Determined from |", "|---|---|---|---|"]
    for entry in entries:
        lines.append(f"| {entry['name']} | {entry['version']} | {entry['licence']} "
                     f"| {entry['determined_from']} |")
    if unresolved:
        lines += ["", f"## {len(unresolved)} unresolved", "",
                  "These state no licence in their metadata. Each needs a human to check the",
                  "project's own LICENSE file before an artifact carrying them is published.",
                  ""]
        for entry in unresolved:
            lines.append(f"- **{entry['name']} {entry['version']}**")
    OUT_TEXT.write_text("\n".join(lines) + "\n")

    print(f"wrote {OUT_JSON.name} and {OUT_TEXT.name}")
    print(f"  {len(entries)} Python dependencies, {len(NON_PYTHON)} other components")
    print(f"  {len(unresolved)} UNRESOLVED" if unresolved else "  all licences resolved")
    for entry in unresolved:
        print(f"    unresolved: {entry['name']} {entry['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
