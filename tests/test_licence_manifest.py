"""The licence manifest must describe the software that is actually shipped.

Two failures, both found by running the packaging workflow's steps by hand rather than trusting
that they would work at release time.

1. **The generator describes whatever interpreter runs it.** Run once from the ambient macOS
   Python it dropped 20 of this project's dependencies, added 12 the project does not use, and
   printed `all licences resolved`. Its docstring claimed the list "cannot silently fall behind
   requirements-lock.txt", which is true only in the environment the lock built. The reverse
   direction is likelier in practice: this repository's own venv had accumulated Markdown,
   markdown-it-py and mdurl, none of which the release artifact carries, and regenerating there
   would have attributed three packages that are not distributed.

2. **The vendored Cognito SDK was attributed by hand in the generated file.** It was never
   added to the generator, so the next run - which the packaging workflow performs on every
   release build - would have deleted the attribution for a 112 KB Apache-2.0 bundle that is
   publicly served. A hand-edit of a generated artifact is not a fix; it is a countdown.

The environment tests are pure - they take an installed set as an argument - so they assert the
same thing on a developer machine, in CI, and on a release runner.

**And the guard's first shape was wrong**, which these tests now pin. It demanded that the
environment *equal* the lock. Both packaging runners install with `pip install -e . -c
requirements-lock.txt`, where the lock is a **constraints** file - it pins versions for what
gets installed rather than installing every line - so a correct release environment carries the
runtime closure and none of the test-only pins. The guard refused, and the first real execution
of the packaging workflow failed on macOS and Windows alike. The rule is a subset, not an
equality, and `test_a_constraints_install_is_accepted_rather_than_called_broken` is the
regression.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "requirements-lock.txt"
MANIFEST_JSON = REPO / "THIRD_PARTY_LICENCES.json"


def _load():
    spec = importlib.util.spec_from_file_location(
        "build_licence_manifest", REPO / "scripts" / "build_licence_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


blm = _load()


def locked_names(applicable_only: bool = False) -> set[str]:
    """Names pinned in the lock.

    With ``applicable_only``, drops pins whose environment marker does not hold here - the lock
    carries `typing-extensions` only below Python 3.13 and `tzdata` only on Windows, and a
    manifest generated on macOS correctly contains neither.
    """
    from packaging.markers import Marker
    out = set()
    for name, marker in blm.locked_requirements(LOCK.read_text()):
        if applicable_only and marker:
            try:
                if not Marker(marker).evaluate():
                    continue
            except Exception:
                pass
        out.add(name)
    return out


# --------------------------------------------------------------------------------------------
# Parsing the lock
# --------------------------------------------------------------------------------------------

def test_the_lock_parses_to_the_pins_it_contains():
    names = locked_names()
    # Spot-checked against the file rather than counted, so adding a pin does not fail this.
    for expected in ("numpy", "pandas", "matplotlib", "jsonschema", "pytest", "segno"):
        assert expected in names, f"{expected} is pinned in the lock but was not parsed out"
    assert "" not in names
    assert not any(n.startswith("#") or n.startswith("-") for n in names)


def test_a_marked_pin_keeps_its_marker():
    """`typing-extensions` installs only below Python 3.13. Dropping the marker would make its
    correct absence on a newer interpreter look like a broken environment."""
    marked = {name: marker for name, marker in blm.locked_requirements(LOCK.read_text())
              if marker}
    assert "typing-extensions" in marked
    assert "python_version" in marked["typing-extensions"]


def test_names_are_normalised_so_underscores_and_hyphens_are_one_package():
    assert blm.normalise("typing_extensions") == blm.normalise("Typing-Extensions") \
        == "typing-extensions"


# --------------------------------------------------------------------------------------------
# The environment guard - both directions
# --------------------------------------------------------------------------------------------

def test_a_declared_runtime_dependency_that_is_absent_is_reported_missing():
    installed = locked_names(applicable_only=True) - {"pandas"}
    missing, unexpected = blm.check_environment(LOCK.read_text(), installed)
    assert "pandas" in missing, "this is not the project's environment and nothing objected"
    assert unexpected == []


def test_a_package_that_is_not_locked_is_reported_unexpected():
    installed = locked_names(applicable_only=True) | {"playwright"}
    missing, unexpected = blm.check_environment(LOCK.read_text(), installed)
    assert missing == []
    assert unexpected == ["playwright"], (
        "the manifest would attribute software the release artifact does not carry")


def test_pip_and_its_siblings_are_not_treated_as_unexpected():
    """pip has always been in this manifest and is present in every environment pip builds."""
    installed = locked_names(applicable_only=True) | {"pip", "setuptools", "wheel"}
    missing, unexpected = blm.check_environment(LOCK.read_text(), installed)
    assert (missing, unexpected) == ([], [])


def test_a_constraints_install_is_accepted_rather_than_called_broken():
    """The regression that failed both packaging runners on their first real execution.

    `pip install -e . -c requirements-lock.txt` uses the lock as CONSTRAINTS: it pins versions
    for what gets installed, it does not install every line. So a correct release environment
    carries the runtime closure and none of the test-only or extra-only pins. The first version
    of this guard demanded equality with the lock and refused - on macOS for 9 missing packages
    and on Windows for the same 9 - turning a working packaging job red.
    """
    runtime_closure = {
        "numpy", "pandas", "matplotlib", "jsonschema", "pillow", "packaging", "contourpy",
        "cycler", "fonttools", "kiwisolver", "pyparsing", "python-dateutil", "six", "attrs",
        "referencing", "rpds-py", "jsonschema-specifications", "typing-extensions", "pip",
    }
    # Only what pip would install HERE. The lock pins `typing-extensions` below Python 3.13
    # only, so on 3.13+ a correct install lacks it, and listing it anyway made this test fail
    # on every developer machine newer than CI's 3.12 - while CI stayed green.
    runtime_closure &= locked_names(applicable_only=True) | {"pip"}
    missing, unexpected = blm.check_environment(LOCK.read_text(), runtime_closure)
    assert (missing, unexpected) == ([], []), (
        f"a lock-constrained release install was rejected: missing={missing} "
        f"unexpected={unexpected}")


def test_the_declared_runtime_dependencies_are_read_from_pyproject():
    declared = blm.declared_runtime_dependencies()
    assert declared == {"numpy", "pandas", "matplotlib", "jsonschema"}, (
        f"the required set no longer matches [project] dependencies: {sorted(declared)}")


def test_a_marker_that_does_not_apply_is_not_an_unexpected_package():
    """On Python 3.13+ `typing-extensions` is correctly absent, and on 3.12 correctly present.
    Neither may be reported as a surprise."""
    lock = 'numpy==2.5.1\ntyping-extensions==4.16.0 ; python_version < "99"\n'
    missing, unexpected = blm.check_environment(
        lock, {"numpy", "typing-extensions"}, required={"numpy"})
    assert (missing, unexpected) == ([], [])


def test_an_unparseable_marker_is_still_permitted_rather_than_dropped():
    """An unreadable marker is treated as applying, so the pin stays permitted. Dropping it
    would make a legitimately installed package look like an unexplained extra."""
    lock = "segno==1.6.6 ; this is not a marker\n"
    _, unexpected = blm.check_environment(lock, {"segno"}, required=set())
    assert unexpected == []


# --------------------------------------------------------------------------------------------
# The committed manifest - checkable without rebuilding an environment
# --------------------------------------------------------------------------------------------

@pytest.mark.skipif(not MANIFEST_JSON.is_file(), reason="manifest not generated yet")
def test_the_committed_manifest_covers_every_locked_dependency():
    payload = json.loads(MANIFEST_JSON.read_text())
    listed = {blm.normalise(e["name"]) for e in payload["python_dependencies"]}
    # Marker-aware: `tzdata` is pinned for Windows only and `typing-extensions` below 3.13.
    # A manifest generated where those markers do not hold correctly omits them, and demanding
    # otherwise would be asserting that the manifest describes a platform it was not built on.
    unlisted = locked_names(applicable_only=True) - listed
    assert not unlisted, (
        f"{sorted(unlisted)} are pinned in requirements-lock.txt, apply on this platform, and "
        f"are absent from the committed licence manifest - the artifact ships them "
        f"unattributed")


@pytest.mark.skipif(not MANIFEST_JSON.is_file(), reason="manifest not generated yet")
def test_the_committed_manifest_attributes_nothing_the_lock_does_not_pin():
    payload = json.loads(MANIFEST_JSON.read_text())
    listed = {blm.normalise(e["name"]) for e in payload["python_dependencies"]}
    extra = listed - locked_names() - blm.ENVIRONMENT_PACKAGES
    assert not extra, (
        f"{sorted(extra)} are attributed in the committed manifest and are not in the lock - "
        f"the manifest was generated somewhere other than the locked environment")


@pytest.mark.skipif(not MANIFEST_JSON.is_file(), reason="manifest not generated yet")
def test_every_tracked_vendored_bundle_is_attributed():
    """The regression this file exists for, in its general form.

    A third-party file committed under a `vendor/` directory is shipped by this repository and
    needs an attribution that survives regeneration - which means it must come from the
    generator's own table, not from an edit to its output.
    """
    vendored = sorted(p for p in REPO.glob("**/vendor/*")
                      if p.is_file()
                      and "venv" not in p.parts
                      and "node_modules" not in p.parts
                      and ".claude" not in p.parts  # local agent worktrees, not this tree
                      and p.suffix in {".js", ".css", ".mjs", ".wasm"})
    if not vendored:
        pytest.skip("nothing vendored")

    declared = json.dumps(blm.NON_PYTHON)
    for path in vendored:
        rel = path.relative_to(REPO).as_posix()
        assert rel in declared, (
            f"{rel} is a vendored third-party bundle that this repository ships and the "
            f"licence GENERATOR does not name it. Adding it to THIRD_PARTY_LICENCES.md by "
            f"hand does not work: the next regeneration deletes it.")


@pytest.mark.skipif(not MANIFEST_JSON.is_file(), reason="manifest not generated yet")
def test_the_manifest_states_the_licence_the_owner_chose():
    """Apache-2.0, chosen by the owner on 2026-10-18. Until then this asserted "NOT STATED":
    the manifest must say what LICENSE says, never something the repository does not hold."""
    payload = json.loads(MANIFEST_JSON.read_text())
    assert payload["this_project_licence"].startswith("Apache-2.0")
    licence = (REPO / "LICENSE").read_text()
    assert "Apache License" in licence and "Version 2.0, January 2004" in licence
    assert payload["unresolved_count"] == len(
        [e for e in payload["python_dependencies"] if e["licence"] == "UNRESOLVED"])


def test_no_licence_is_invented_for_a_distribution_that_states_none():
    """`licence_of` returns UNRESOLVED rather than guessing. Checked directly, because the
    docstring's promise not to guess is the whole reason this file can be trusted."""
    class Meta(dict):
        def get_all(self, key):
            return None

    class Dist:
        metadata = Meta()

    licence, how = blm.licence_of(Dist())
    assert licence == "UNRESOLVED"
    assert "no License-Expression" in how


def test_octave_is_not_claimed_as_a_bundled_dependency():
    """GPL software this project does not distribute must not appear as if it did."""
    payload = json.loads(MANIFEST_JSON.read_text())
    assert "NOT bundled" in payload["octave_note"]
    names = {e["name"].lower() for e in payload["python_dependencies"]}
    names |= {e["name"].lower() for e in payload["other_components"]}
    assert not any(re.fullmatch(r"(gnu )?octave", n) for n in names)
