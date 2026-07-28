"""The desktop launcher: builds what is derivable, refuses what is not.

The distinction this file exists to pin
---------------------------------------
A launcher that rebuilds everything on every start makes "the numbers changed and I do not
know why" routine. A launcher that refuses to start because a *derived* file is absent is
pedantry. The line between those is the whole design: **generated artifacts are built if
missing and never rebuilt if present; missing source inputs stop the launch and are named.**
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import launcher  # noqa: E402


def test_every_generated_artifact_names_a_real_build_script():
    """An artifact whose producer does not exist would fail at the worst moment — mid-launch,
    after the user has been told a build is starting."""
    for path, command in launcher.GENERATED:
        script = REPO / command[0]
        assert script.is_file(), f"{path} claims to be built by {command[0]}, which is missing"


def test_required_sources_all_exist_in_a_healthy_checkout():
    assert launcher.missing_sources() == []


def test_generated_and_source_lists_do_not_overlap():
    """A file cannot be both regenerable and irreplaceable. If one appeared in both lists the
    launcher would refuse to start over something it could have rebuilt."""
    generated = {p for p, _ in launcher.GENERATED}
    assert generated & set(launcher.REQUIRED_SOURCES) == set()


def test_check_mode_reports_without_serving(capsys):
    assert launcher.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Nothing would be rebuilt" in out or "would build them" in out


def test_a_missing_source_stops_the_launch_and_names_it(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "REQUIRED_SOURCES",
                        ["data/contract/v1/contract_manifest.json", "not/a/real/file.csv"])
    assert launcher.main([]) == 1
    out = capsys.readouterr().out
    assert "not/a/real/file.csv" in out
    assert "no build step" in out, "it must say WHY it cannot simply build the thing"


def test_a_missing_generated_file_is_built_not_refused(monkeypatch, capsys):
    """The other half of the rule: derived files are the launcher's problem, not the user's."""
    calls = []
    monkeypatch.setattr(launcher, "GENERATED", [("nope.json", ["scripts/build_field_schema.py"])])
    monkeypatch.setattr(launcher, "build", lambda commands, python=None: calls.append(commands))
    monkeypatch.setattr(launcher, "missing_sources", lambda: [])

    # Stop before the server starts; we are testing the decision, not the socket.
    class Stop(Exception):
        pass

    def explode(*_a, **_k):
        raise Stop
    monkeypatch.setitem(sys.modules, "fcf_m2.server", type("M", (), {"serve": staticmethod(explode)}))
    with pytest.raises(Stop):
        launcher.main([])
    assert calls == [[["scripts/build_field_schema.py"]]]


def test_it_never_rebuilds_something_that_already_exists(monkeypatch):
    monkeypatch.setattr(launcher, "GENERATED",
                        [("site/platform/index.html", ["scripts/build_platform_web.py"])])
    assert launcher.missing_generated() == [], (
        "an artifact that is present must not be queued for rebuild")


def test_the_entry_point_is_declared_in_packaging():
    """`fcf-platform` has to exist as a console script or the documented command is fiction."""
    text = (REPO / "pyproject.toml").read_text()
    assert "[project.scripts]" in text
    assert 'fcf-platform = "fcf_m2.launcher:main"' in text


def test_build_surfaces_the_real_output_when_a_step_fails(tmp_path, capsys):
    """A launcher that swallows a build failure and serves a half-built page is worse than one
    that stops."""
    with pytest.raises(SystemExit) as excinfo:
        launcher.build([["scripts/definitely_not_a_script.py"]])
    assert "definitely_not_a_script" in str(excinfo.value)
