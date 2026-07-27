"""Repository-hygiene gates that protect tracked artifacts from machine-specific state.

These guard two defects found during the V4 program's Phase 0 audit:

* ``dashboard/static/footer_log.json`` shipped nine absolute paths from the authoring
  machine, because the generator stringified an already-resolved path. That leaked a local
  directory layout into a tracked artifact and failed ``scripts/verify.sh``.
* ``scripts/check_internal_links.py`` matched link syntax inside code spans and fenced code
  blocks, so any document that *quotes* a Markdown link failed the link gate while lychee --
  which parses Markdown properly -- passed it. The two checkers must agree, or local and CI
  results diverge.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_internal_links import LINK, broken_links, strip_code  # noqa: E402

from fcf_m2.visuals import log_path_for  # noqa: E402


@pytest.fixture(scope="module")
def entries() -> list[dict]:
    return json.loads((ROOT / "dashboard/static/footer_log.json").read_text())


class TestFooterLogPortability:
    """The footer log is tracked, so it must never record an absolute path."""

    def test_every_entry_has_a_file(self, entries):
        assert entries, "footer log is empty"
        assert all(e.get("file") for e in entries)

    def test_no_absolute_paths(self, entries):
        offenders = [e["file"] for e in entries if Path(e["file"]).is_absolute()]
        assert offenders == [], f"absolute paths in a tracked artifact: {offenders}"

    def test_no_home_directory_leak(self, entries):
        offenders = [e["file"] for e in entries if "/Users/" in e["file"] or "\\Users\\" in e["file"]]
        assert offenders == [], f"authoring-machine paths leaked: {offenders}"

    def test_paths_resolve_from_the_repository_root(self, entries):
        missing = [e["file"] for e in entries if not (ROOT / e["file"]).exists()]
        assert missing == [], f"logged charts that do not exist: {missing}"

    def test_one_entry_per_chart_no_duplicates(self, entries):
        """A rebuild must not append to the previous run's log."""
        files = [e["file"] for e in entries]
        assert len(files) == len(set(files)), f"duplicate footer-log entries: {files}"
        charts = sorted(p.name for p in (ROOT / "dashboard/static").glob("0*.png"))
        assert sorted(Path(f).name for f in files) == charts

    def test_log_path_for_makes_paths_relative(self, tmp_path):
        target = tmp_path / "dashboard" / "static" / "chart.png"
        target.parent.mkdir(parents=True)
        target.touch()
        assert log_path_for(target, tmp_path) == "dashboard/static/chart.png"

    def test_log_path_for_falls_back_to_the_filename_outside_the_repo(self, tmp_path):
        outside = tmp_path / "elsewhere.png"
        outside.touch()
        assert log_path_for(outside, tmp_path / "nested") == "elsewhere.png"

    def test_log_path_for_never_returns_an_absolute_path(self, tmp_path):
        outside = tmp_path / "elsewhere.png"
        outside.touch()
        for base in (None, tmp_path, tmp_path / "nested"):
            assert not Path(log_path_for(outside, base)).is_absolute()


class TestLinkCheckerIgnoresCode:
    """Quoting link syntax is not linking. The checker must agree with lychee."""

    @pytest.mark.parametrize("text,expected", [
        ("a real link [x](target.md) here", ["target.md"]),
        ("quoted `[x](nope.md)` in a code span", []),
        ("```\n[x](nope.md)\n```\n", []),
        ("~~~\n[x](nope.md)\n~~~\n", []),
        ("``a `[x](nope.md)` b``", []),
        ("![img](real.png) and `![img](fake.png)`", ["real.png"]),
        ("mixed `code` then [live](live.md)", ["live.md"]),
        ("```python\ncode = '[x](nope.md)'\n```\ntail [ok](ok.md)", ["ok.md"]),
    ])
    def test_masking(self, text, expected):
        assert LINK.findall(strip_code(text)) == expected

    def test_masking_preserves_offsets(self):
        """Blanking must not shift line numbers, or reported positions would be wrong."""
        for src in ("a\n`[x](y)`\nb", "```\nq\n```\nz", "plain text"):
            masked = strip_code(src)
            assert len(masked) == len(src)
            assert masked.count("\n") == src.count("\n")

    def test_repository_has_no_broken_relative_links(self):
        assert broken_links() == []
