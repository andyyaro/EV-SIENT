"""The public artifact must have the same shape on every operating system.

Found by downloading what CI actually published, on the packaging workflow's first successful
run, and opening both archives instead of reading the green tick.

**The macOS artifact was correct and the Windows one was broken**, from the same commit, in the
same run. `str(p.relative_to(ROOT))` yields backslashes on Windows, and the result was compared
against the forward-slash keys of `PUBLIC_SUBSTITUTIONS`. That comparison could never match, so
the substitution silently did not happen: the Windows archive shipped the synthetic inputs at
their own `data/synthetic/...` paths, **none of the four paths the model reads existed**, and a
recipient's first run would have found no inputs at all. The same `str()` put backslashes into
**58 of the 60** RELEASE_MANIFEST keys, which then matched none of the names in the archive
beside them.

Nothing leaked — both archives were clean of all real facility identifiers — so this is an
availability failure, not a disclosure one. It is in this file because no test in the repository
could see it: they all run where the path separator is `/`.

The two unit tests below therefore feed Windows-shaped strings directly, so they fail on any
machine. The integration tests assert the invariant on a real build.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "build_release_artifact", REPO / "scripts" / "build_release_artifact.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bra = _load()


# --------------------------------------------------------------------------------------------
# The unit tests that would have caught it, on any OS
# --------------------------------------------------------------------------------------------

def test_a_windows_shaped_path_still_matches_a_substitution():
    """The exact failure. A backslash path must resolve to the REAL name, not pass through."""
    subs = bra.PUBLIC_SUBSTITUTIONS
    for real_rel, synth_rel in subs.items():
        windows_shaped = synth_rel.replace("/", "\\")
        # The archive name is computed from a POSIX-normalised relative path, so the caller
        # normalises first; this asserts the normalisation is what makes the match possible.
        assert bra.substituted_name(windows_shaped.replace("\\", "/"), subs) == real_rel
        assert bra.substituted_name(synth_rel, subs) == real_rel, (
            f"{synth_rel} must be stored as {real_rel}, or the model finds no inputs")


def test_a_file_with_no_substitute_keeps_its_own_name():
    assert bra.substituted_name("src/fcf_m2/model.py", bra.PUBLIC_SUBSTITUTIONS) == \
        "src/fcf_m2/model.py"


def test_archive_path_is_always_posix():
    sample = REPO / "src" / "fcf_m2" / "__init__.py"
    if not sample.is_file():
        pytest.skip("sample source file absent")
    rel = bra.archive_path(sample)
    assert "\\" not in rel, f"archive_path returned a backslash path: {rel!r}"
    assert rel == "src/fcf_m2/__init__.py"


def test_every_substitution_target_is_a_path_the_model_reads():
    """A substitution that writes to the wrong name is the same failure with extra steps."""
    for real_rel in bra.PUBLIC_SUBSTITUTIONS:
        assert "/" in real_rel and "\\" not in real_rel
        assert not real_rel.startswith("data/synthetic/"), (
            f"{real_rel} is a synthetic source path, not a path the model reads")


# --------------------------------------------------------------------------------------------
# The invariant, asserted on a real build
# --------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def public_archive(tmp_path_factory):
    out = tmp_path_factory.mktemp("public")
    # `main`, not `build`. The first version of this fixture guessed the name, caught
    # AttributeError and skipped — three green-looking skips that asserted nothing about the
    # artifact. A test that cannot run is not a passing test.
    try:
        zpath = bra.main(str(out), public=True)
    except SystemExit as exc:
        pytest.fail(f"the public build refused, which is itself the thing under test: {exc}")
    return Path(zpath)


def test_the_public_archive_stores_only_posix_names(public_archive):
    with zipfile.ZipFile(public_archive) as z:
        names = z.namelist()
    bad = [n for n in names if "\\" in n]
    assert not bad, f"{len(bad)} archive entries carry backslashes: {bad[:5]}"


def test_the_public_archive_carries_every_input_the_model_reads(public_archive):
    with zipfile.ZipFile(public_archive) as z:
        names = set(z.namelist())
    missing = [real for real in bra.PUBLIC_SUBSTITUTIONS if real not in names]
    assert not missing, (
        f"the public artifact is missing {missing} — these are the paths the model reads, and "
        f"without them a recipient's first run finds no inputs")


#: Extensions the recipient's tooling will read as text. Binary members are skipped rather than
#: guessed at.
TEXT_SUFFIXES = {".py", ".csv", ".json", ".md", ".txt", ".html", ".js", ".css", ".toml", ".sh"}


def test_every_text_file_in_the_public_archive_is_valid_utf8(public_archive):
    """The third Windows defect from the same green run.

    `path.open("w")` uses the interpreter's LOCALE encoding, which is cp1252 on a Windows
    runner. Every synthetic row carries the note "SYNTHETIC FIXTURE — invented facility", and
    the Windows artifact shipped that em dash as the single byte `0x97`. The file was not valid
    UTF-8, so a recipient reading it the ordinary way — `pandas.read_csv`, which defaults to
    UTF-8 — would have hit a UnicodeDecodeError on their first run. The macOS artifact from the
    same commit was fine, because the locale there is UTF-8.

    This asserts the property a recipient depends on, rather than the call that produces it.
    """
    bad = []
    with zipfile.ZipFile(public_archive) as z:
        for info in z.infolist():
            if info.is_dir() or Path(info.filename).suffix not in TEXT_SUFFIXES:
                continue
            try:
                z.read(info.filename).decode("utf-8")
            except UnicodeDecodeError as exc:
                bad.append(f"{info.filename}: {exc}")
    assert not bad, ("the public artifact ships text that is not UTF-8; a recipient reading it "
                     f"with default settings gets a decode error:\n  " + "\n  ".join(bad[:5]))


def test_the_synthetic_writers_never_rely_on_the_platform_encoding():
    """Structural companion to the test above.

    The property test only fails where the locale differs, which is precisely the machine this
    suite usually does not run on. This one fails everywhere the moment a writer goes back to
    the default, so the two together cover the case rather than one of them pretending to.

    The source is PARSED, not searched. The first version of this test grepped for
    `.open("w"` and flagged the sentence in `write_csv`'s own docstring that explains the bug —
    matching text where meaning was intended, which is the single most common defect this
    repository has produced. An AST walk cannot make that mistake: a docstring is a string
    constant, not a call.
    """
    tree = ast.parse((REPO / "scripts" / "build_synthetic_inputs.py").read_text())
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        if name not in ("open", "write_text"):
            continue
        if name == "open":
            mode = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) \
                else ""
            if "w" not in str(mode) and "a" not in str(mode):
                continue
        if not any(kw.arg == "encoding" for kw in node.keywords):
            offenders.append(f"line {node.lineno}: {name}() with no encoding=")
    assert not offenders, (
        "these writes use the interpreter's locale encoding, which is cp1252 on Windows:\n  "
        + "\n  ".join(offenders))


def test_the_manifest_keys_match_the_archive_names(public_archive):
    """A manifest that names files the archive does not contain cannot verify anything. The
    Windows artifact had 58 such keys and nothing objected."""
    with zipfile.ZipFile(public_archive) as z:
        names = set(z.namelist())
        manifest = json.loads(z.read("RELEASE_MANIFEST.json"))
    listed = set(manifest["files"])
    # The manifest records source files; substituted entries appear under their synthetic name
    # in one and their real name in the other, so compare after applying the substitution.
    resolved = {bra.substituted_name(k, bra.PUBLIC_SUBSTITUTIONS) for k in listed}
    orphans = sorted(resolved - names)
    assert not orphans, (
        f"{len(orphans)} manifest entries name files the archive does not contain: "
        f"{orphans[:5]}")
    assert not [k for k in listed if "\\" in k], "manifest keys carry backslashes"
