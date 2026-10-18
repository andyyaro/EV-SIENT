"""The platform's engine bridge (src/fcf_m2/browser_api.py), run natively.

The browser runs this module unmodified under Pyodide; platform/tools/parity.mjs holds the two
runtimes to the same answers. These tests hold the module itself to what the app relies on:
its field table is the documented one, each site's explanation adds up to its score, the
order of the steps is enforced, a bad mapping is refused in words, and every answer is JSON
the browser can parse (no NaN, which JSON.parse rejects).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import browser_api as api, workflow  # noqa: E402

EXAMPLE = REPO / "data/intake/example/example_city_facilities.csv"
SYNTHETIC = REPO / "data/synthetic/synthetic_sites_v2.csv"
AS_OF = "2026-10-18"


def _strict(text: str):
    """json.loads, but NaN and Infinity are errors, as they are for JSON.parse."""
    def refuse(token):
        raise AssertionError(f"non-JSON constant {token} in engine output")
    return json.loads(text, parse_constant=refuse)


def _table(path: Path) -> str:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    return json.dumps({"fileName": path.name, "columns": rows[0], "rows": rows[1:]})


def _session(path: Path, run: bool = True) -> dict:
    api.reset()
    out = {"propose": _strict(api.propose(_table(path)))}
    out["check"] = _strict(api.check())
    if run:
        out["accept"] = _strict(api.accept(json.dumps({"sourceDate": "2026-10-01"})))
        out["run"] = _strict(api.run(json.dumps({"asOf": AS_OF})))
    return out


@pytest.fixture(autouse=True)
def fresh_session():
    api.reset()
    yield
    api.reset()


@pytest.fixture(scope="module")
def no_reference_inputs():
    """A browser-path run must never fall through to the reference study (DEC-016)."""
    def refuse():
        raise AssertionError("browser_api read the reference study's private inputs")
    original = workflow._load_inputs
    workflow._load_inputs = refuse
    yield
    workflow._load_inputs = original


def _schema_table() -> list[list[str]]:
    text = (REPO / "docs/INPUT_SCHEMA.md").read_text()
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\| `([a-z0-9_]+)` \| (.*) \|$", line)
        if m:
            cells = [c.strip() for c in m.group(2).split(" | ")]
            if len(cells) == 4:  # unit, in the score, what it is, if blank or absent
                rows.append([m.group(1), *cells])
    return rows


def test_fields_match_input_schema_word_for_word():
    table = _schema_table()
    assert [r[0] for r in table] == [f["name"] for f in api.FIELDS]
    catalogue = {f["name"]: f for f in _strict(api.fields())["fields"]}
    for name, unit, in_score, what, if_missing in table:
        field = catalogue[name]
        assert (field["unit"], field["what"], field["if_missing"]) == (unit, what, if_missing), name
        assert field["scored"] == (in_score == "yes"), name


@pytest.mark.parametrize("path", [EXAMPLE, SYNTHETIC], ids=["example-city", "synthetic-cohort"])
def test_every_explanation_adds_up_to_its_score(path, no_reference_inputs):
    run = _session(path)["run"]
    assert run["sites"], "the run returned no sites"
    for site in run["sites"]:
        x = _strict(api.explain(site["siteId"]))
        total = sum(d["points"] for d in x["drivers"])
        # The score is rounded to one decimal and each driver to four.
        assert abs(total - x["score"]) <= 0.05 + 1e-3, (site["siteId"], total, x["score"])
        assert x["score"] == site["score"]
        assert abs(sum(s["points"] for s in x["subscores"]) - x["score"]) <= 0.05 + 1e-3


def test_run_refuses_before_accept():
    with pytest.raises(ValueError, match="Accept the checked file before running the model"):
        api.run(json.dumps({"asOf": AS_OF}))
    api.propose(_table(EXAMPLE))
    api.check()
    with pytest.raises(ValueError, match="Accept the checked file before running the model"):
        api.run(json.dumps({"asOf": AS_OF}))


def test_remap_refuses_duplicate_columns_and_unknown_fields():
    proposal = _strict(api.propose(_table(EXAMPLE)))
    mapping = dict(proposal["mapping"])
    with pytest.raises(ValueError, match="is chosen for both"):
        api.remap(json.dumps({"mapping": {**mapping, "site_name": mapping["site_id"]}}))
    with pytest.raises(ValueError, match="is not a field this model reads"):
        api.remap(json.dumps({"mapping": {**mapping, "solar_panels": "Fleet"}}))
    with pytest.raises(ValueError, match="is not in this file"):
        api.remap(json.dumps({"mapping": {**mapping, "fleet_vehicles": "No Such Column"}}))
    # The planner's own, valid choice is accepted and marked as chosen.
    again = _strict(api.remap(json.dumps({"mapping": mapping})))
    assert again["mapping"] == mapping
    assert all(again["status"][k] == "matched" for k in mapping)


def test_check_statuses_on_example_city():
    check = _session(EXAMPLE, run=False)["check"]
    statuses = {r["siteId"]: r["status"] for r in check["rows"]}
    assert len(statuses) == 6
    assert sorted(statuses.values()) == ["missing"] * 3 + ["ready"] * 3
    assert check["counts"] == {"total": 6, "ready": 3, "missing": 3, "mustFix": 0, "located": 6}
    for row in check["rows"]:
        assert (row["status"] == "missing") == bool(row["missing"])
        assert row["mustFix"] == []


def test_every_function_returns_strict_json(no_reference_inputs):
    _strict(api.info())
    _strict(api.fields())
    for path in (EXAMPLE, SYNTHETIC):
        s = _session(path)
        proposal = s["propose"]
        _strict(api.remap(json.dumps({"mapping": proposal["mapping"]})))
        _strict(api.check())
        _strict(api.accept("{}"))
        run = _strict(api.run(json.dumps({"asOf": AS_OF})))
        for site in run["sites"]:
            _strict(api.explain(site["siteId"]))
        files = _strict(api.output_files())["files"]
        assert any(k.startswith("results/") for k in files) and any(k.startswith("inputs/") for k in files)
    _strict(api.reset())


def test_as_of_fixes_the_confidence_date(no_reference_inputs):
    first = _session(EXAMPLE)["run"]
    later = _strict(api.run(json.dumps({"asOf": "2031-10-18"})))
    again = _strict(api.run(json.dumps({"asOf": AS_OF})))
    conf = lambda r: [s["confidence"]["score"] for s in r["sites"]]
    assert first["asOf"] == AS_OF and later["asOf"] == "2031-10-18"
    assert conf(again) == conf(first)
    assert conf(later) != conf(first), "a source five years older should cost confidence"
