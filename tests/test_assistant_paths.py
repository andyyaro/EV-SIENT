"""The public assistant reads only public files, and never passes an identifier to the model.

Why this is a test and not a convention
---------------------------------------
The assistant needs no sign-in and reads a private repository with a token, so its path rule
is the whole boundary between the two. The first version was a blocklist. A live probe on
2026-10-17 showed what that costs: it named `data/inputs/` but not `tests/fixture_*.csv`,
which carry the same facility rows, and an allowlisted login email came back verbatim from a
script. These tests run the deployed function's own rule over the real tracked tree.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "infra/assistant/lambda_function.py"

spec = importlib.util.spec_from_file_location("assistant_lambda", SOURCE)
assistant = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assistant)

TRACKED = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True,
                         check=True).stdout.split()
READABLE = [p for p in TRACKED if assistant._is_allowed_repo_path(p)]

#: Placeholder addresses that are part of a public page's markup, not anyone's identity.
PLACEHOLDER_EMAILS = {"name@agency.gov"}


@pytest.mark.parametrize("path", [
    "data/inputs/real_sites_v2.csv",
    "tests/fixture_milestone2_v3_site_results.csv",
    "tests/fixture_legacy_v2_site_results.csv",
    "data/provenance/field_provenance_v1.csv",
    "infra/edge-auth/index.mjs",
    "scripts/verify_deployment.py",
    "scripts/deploy_platform.py",
    "docs/operations/v4-program/DECISIONS.md",
    "docs/operations/v4-program/LEDGER.md",
    "site/platform/index.html",
    "explorer/web/data/sites.geojson",
    "matlab/data/canonical/matlab_scenarios.csv",
])
def test_private_paths_are_unreadable(path):
    assert not assistant._is_allowed_repo_path(path), f"the public assistant can read {path}"


def test_nothing_under_a_private_directory_is_readable():
    private = ("tests/", "infra/", "data/inputs/", "data/provenance/", "site/platform/",
               "docs/human-actions/", ".github/", "presentation/", "excel/")
    leaks = [p for p in READABLE if p.lower().startswith(private)]
    assert leaks == [], leaks
    operations = [p for p in READABLE if p.lower().startswith("docs/operations/")]
    assert operations in ([], ["docs/operations/reproduction-guide.md"]), operations


def test_an_unknown_directory_is_unreadable_until_someone_decides_it_is_public():
    """The property a blocklist lacks: a new folder fails closed."""
    assert not assistant._is_allowed_repo_path("newfolder/notes.md")
    assert not assistant._is_allowed_repo_path("data/new_real_inputs/sites.csv")


def test_the_files_the_assistant_is_told_to_prefer_are_still_readable():
    """An allowlist that starves the assistant of its own source-of-truth files fails silently,
    as vague answers rather than as an error - so it is checked here."""
    named = set(assistant.SOURCE_OF_TRUTH_FILES) | set(assistant.BROAD_OVERVIEW_FILES) \
        | set(assistant.TABLEAU_EXPORT_FILES) | set(assistant.SCORING_METHOD_FILES)
    for _, paths in assistant.TOPIC_FILE_HINTS:
        named.update(paths)
    tracked = set(TRACKED)
    missing = sorted(p for p in named if p in tracked and not assistant._is_allowed_repo_path(p))
    assert missing == [], missing


def test_no_readable_file_carries_an_email_address():
    """Belt and braces: redaction would catch one anyway, but none should be there to catch."""
    found = {}
    for path in READABLE:
        try:
            text = (REPO / path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        emails = set(assistant.EMAIL_PATTERN.findall(text)) - PLACEHOLDER_EMAILS
        if emails:
            found[path] = sorted(emails)
    assert found == {}, f"readable files carry email addresses: {sorted(found)}"


def test_identifiers_are_removed_from_every_excerpt():
    text = ("granted: someone@example.org, sub 00000000-0000-4000-8000-000000000001; "
            "a@b.co.uk")
    for path in ("notes.md", "page.html", "data.json"):
        cleaned = assistant._normalize_text_for_context(path, text)
        assert "@" not in cleaned, cleaned
        assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", cleaned), cleaned
        assert "[email removed]" in cleaned and "[id removed]" in cleaned
