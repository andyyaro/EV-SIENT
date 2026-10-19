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


def test_provenance_resolves_one_cell_on_demand(no_reference_inputs):
    """The cell the planner opens, resolved when asked, says what provenance.resolve says."""
    from fcf_m2 import provenance as pv

    cell = {"siteId": "EXC-01", "horizonYear": 2036, "scenario": "base", "column": "ports_active"}
    with pytest.raises(ValueError, match="Run the model first"):
        api.provenance(json.dumps(cell))
    _session(EXAMPLE)
    record = _strict(api.provenance(json.dumps(cell)))
    index = pv.ContractIndex.load(api._session.out_dir / "contract")
    expected = pv.resolve(index, "EXC-01", 2036, "base", "ports_active").to_dict()
    assert record == _strict(json.dumps(expected))
    assert record["row_key"] == {"site_id": "EXC-01", "horizon_year": 2036, "scenario_name": "base"}
    assert record["field_provenance"]["field_group"] == "parking_and_layout"

    with pytest.raises(ValueError, match="no scenario row"):
        api.provenance(json.dumps({**cell, "siteId": "EXC-99"}))
    with pytest.raises(ValueError, match="not a column"):
        api.provenance(json.dumps({**cell, "column": "ports_2035"}))
    with pytest.raises(ValueError, match="scenario is missing"):
        api.provenance(json.dumps({**cell, "scenario": ""}))


def test_provenance_keeps_site_ids_as_text(tmp_path, no_reference_inputs):
    """Site IDs that are all digits arrive from `run` as text ("107"). Read back as numbers they
    would match nothing, and every cell of those sites would be refused."""
    with open(SYNTHETIC, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    at = rows[0].index("site_id")
    for i, row in enumerate(rows[1:], 1):
        row[at] = str(100 + i)
    path = tmp_path / "numbered.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    ids = [s["siteId"] for s in _session(path)["run"]["sites"]]
    assert "107" in ids
    record = _strict(api.provenance(json.dumps(
        {"siteId": "107", "horizonYear": 2026, "scenario": "baseline", "column": "ports_active"})))
    assert record["row_key"]["site_id"] == "107"
    assert record["field_provenance"] is not None, "the site's own provenance, found by its text ID"


# ---------- public data fills (DEC-025) ----------

SOURCE = {
    "hubVersion": "2026-10-18.1", "dataset": "lodes-wac-va", "title": "Census LODES 8.4, 2023 jobs",
    "vintage": "LODES 8.4, 2023 jobs", "sourceDate": "2025-12-18", "licence": "Public domain",
    "method": "Jobs at 2020 blocks within 1 mile.", "url": "https://lehd.ces.census.gov/data/",
}


def _table_without(path: Path, drop: set[str], blank: dict[str, str] | None = None) -> str:
    """The file as a planner might have it: some columns missing, some cells left empty."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    keep = [i for i, c in enumerate(rows[0]) if c not in drop]
    out = [[r[i] for i in keep] for r in rows]
    for site, column in (blank or {}).items():
        j = out[0].index(column)
        for r in out[1:]:
            if r[0] == site:
                r[j] = ""
    return json.dumps({"fileName": path.name, "columns": out[0], "rows": out[1:]})


def _fill(field: str, values: dict, **source) -> str:
    return json.dumps({"fills": [{"field": field, "values": values, "source": {**SOURCE, **source}}]})


def _cohort_file(name: str) -> str:
    return _strict(api.output_files())["files"][f"inputs/{name}"]


def test_check_gives_coordinates_and_no_fills_by_default():
    check = _session(EXAMPLE, run=False)["check"]
    for row in check["rows"]:
        assert isinstance(row["lat"], float) and isinstance(row["lon"], float)
        assert row["filled"] == []
    assert check["publicFill"]["filled"] == {}
    assert "nearby_jobs_1mi" in check["publicFill"]["fields"]
    assert "parking_spaces" not in check["publicFill"]["fields"]


def test_fill_an_absent_field_is_recorded_as_derived_public_data(no_reference_inputs):
    api.propose(_table_without(SYNTHETIC, {"nearby_jobs_1mi"}))
    before = _strict(api.check())
    assert "nearby_jobs_1mi" in before["absentFromFile"]
    sites = [r["siteId"] for r in before["rows"]]
    values = {sid: 1000.0 + 10 * i for i, sid in enumerate(sites[:-1])}  # the last site is not filled
    after = _strict(api.fill(_fill("nearby_jobs_1mi", values)))
    filled = {r["siteId"]: r["filled"] for r in after["rows"]}
    assert all(filled[s] == ["nearby_jobs_1mi"] for s in values) and filled[sites[-1]] == []
    assert after["publicFill"]["filled"] == {"nearby_jobs_1mi": len(values)}
    assert after["publicFill"]["sources"]["nearby_jobs_1mi"]["hubVersion"] == "2026-10-18.1"

    accepted = _strict(api.accept(json.dumps({"sourceDate": "2026-10-01", "sourceOrg": "Facilities"})))
    assert accepted["publicCells"] == len(values)
    entry = [e for e in accepted["ledger"] if e["action"].startswith("filled from public data")]
    assert len(entry) == 1 and entry[0]["canonical_field"] == "nearby_jobs_1mi"
    assert "Census LODES 8.4, 2023 jobs" in entry[0]["reason"] and "2026-10-18.1" in entry[0]["reason"]
    _strict(api.run(json.dumps({"asOf": AS_OF})))

    by_id = {r["site_id"]: r for r in csv.DictReader(_cohort_file("sites.csv").splitlines())}
    for sid, v in values.items():
        assert float(by_id[sid]["nearby_jobs_1mi"]) == v
    assert by_id[sites[-1]]["nearby_jobs_1mi"] == "", "a site the planner did not fill stays absent"

    prov = {(r["site_id"], r["field_group"]): r
            for r in csv.DictReader(_cohort_file("provenance.csv").splitlines())}
    filled_row = prov[(sites[0], "equity_and_context")]
    assert filled_row["source_class"] == "derived_public_data"
    assert filled_row["source_date"] == "2025-12-18"
    assert filled_row["source_org"] == "EV-SIENT public data hub 2026-10-18.1: Census LODES 8.4, 2023 jobs"
    assert "nearby_jobs_1mi" in filled_row["assumption_type"]
    assert prov[(sites[-1], "equity_and_context")]["source_class"] == "missing"
    # Other groups keep the planner's own source.
    assert prov[(sites[0], "parking_and_layout")]["source_org"] == "Facilities"

    cells = list(csv.DictReader(_cohort_file("public_data_fills.csv").splitlines()))
    assert len(cells) == len(values)
    assert {c["dataset"] for c in cells} == {"lodes-wac-va"}
    assert {c["hub_version"] for c in cells} == {"2026-10-18.1"}


def test_a_filled_value_scores_the_same_but_is_trusted_less(no_reference_inputs):
    """Filling earns the value's credit, but its provenance is weaker than the planner's own."""
    measured = _session(SYNTHETIC)["run"]
    with open(SYNTHETIC, encoding="utf-8-sig", newline="") as f:
        jobs = {r["site_id"]: float(r["nearby_jobs_1mi"]) for r in csv.DictReader(f)}
    api.reset()
    api.propose(_table_without(SYNTHETIC, {"nearby_jobs_1mi"}))
    api.fill(_fill("nearby_jobs_1mi", jobs))
    api.accept(json.dumps({"sourceDate": "2026-10-01"}))
    filled = _strict(api.run(json.dumps({"asOf": AS_OF})))
    score = lambda r: {s["siteId"]: s["score"] for s in r["sites"]}
    conf = lambda r: {s["siteId"]: s["confidence"]["score"] for s in r["sites"]}
    assert score(filled) == score(measured), "the same numbers must score the same"
    assert all(conf(filled)[s] <= conf(measured)[s] for s in jobs)
    assert any(conf(filled)[s] < conf(measured)[s] for s in jobs)
    for site in filled["sites"]:
        x = _strict(api.explain(site["siteId"]))
        assert abs(sum(d["points"] for d in x["drivers"]) - x["score"]) <= 0.05 + 1e-3


def test_fill_takes_a_blank_cell_but_never_replaces_a_value():
    api.propose(_table_without(SYNTHETIC, set(), blank={"SYN001": "existing_l2_ports_1mi"}))
    row = next(r for r in _strict(api.check())["rows"] if r["siteId"] == "SYN001")
    assert row["missing"] == ["existing_l2_ports_1mi"]
    after = _strict(api.fill(_fill("existing_l2_ports_1mi", {"SYN001": 3}, dataset="afdc-stations")))
    row = next(r for r in after["rows"] if r["siteId"] == "SYN001")
    assert row["missing"] == [] and row["filled"] == ["existing_l2_ports_1mi"] and row["status"] == "ready"
    with pytest.raises(ValueError, match="already has a value for existing_l2_ports_1mi at SYN002"):
        api.fill(_fill("existing_l2_ports_1mi", {"SYN002": 3}))


@pytest.mark.parametrize("item, message", [
    ({"field": "parking_spaces", "values": {"EXC-01": 10}}, "cannot be filled from public data"),
    ({"field": "amenities_count_0_5mi", "values": {"NOPE": 1}}, "There is no site NOPE"),
    ({"field": "amenities_count_0_5mi", "values": {"EXC-01": -1}}, "out of range"),
    ({"field": "amenities_count_0_5mi", "values": {"EXC-01": "12"}}, "is not a number"),
    ({"field": "amenities_count_0_5mi", "values": {"EXC-01": True}}, "is not a number"),
    ({"field": "amenities_count_0_5mi", "values": {}}, "No values were given"),
])
def test_fill_refuses_in_words(item, message):
    api.propose(_table(EXAMPLE))
    with pytest.raises(ValueError, match=message):
        api.fill(json.dumps({"fills": [{**item, "source": SOURCE}]}))


def test_fill_refuses_a_share_above_one_and_an_unsourced_value():
    api.propose(_table_without(EXAMPLE, {"Equity Index"}))
    with pytest.raises(ValueError, match="out of range"):
        api.fill(_fill("equity_gap_index", {"EXC-01": 1.5}))
    with pytest.raises(ValueError, match="do not say their vintage, licence"):
        api.fill(_fill("equity_gap_index", {"EXC-01": 0.5}, vintage="", licence=""))
    with pytest.raises(ValueError, match="not a date"):
        api.fill(_fill("equity_gap_index", {"EXC-01": 0.5}, sourceDate="2025"))
    twice = json.loads(_fill("equity_gap_index", {"EXC-01": 0.5}))
    twice["fills"] *= 2
    with pytest.raises(ValueError, match="listed twice"):
        api.fill(json.dumps(twice))


def test_a_new_mapping_or_file_clears_the_fills():
    proposal = _strict(api.propose(_table(EXAMPLE)))
    _strict(api.fill(_fill("amenities_count_0_5mi", {"EXC-01": 4})))
    _strict(api.remap(json.dumps({"mapping": proposal["mapping"]})))
    assert _strict(api.check())["publicFill"]["filled"] == {}
    _strict(api.fill(_fill("amenities_count_0_5mi", {"EXC-01": 4})))
    _strict(api.propose(_table(EXAMPLE)))
    assert _strict(api.check())["publicFill"]["filled"] == {}
    # And an empty list removes them on purpose.
    _strict(api.fill(_fill("amenities_count_0_5mi", {"EXC-01": 4})))
    assert _strict(api.fill(json.dumps({"fills": []})))["publicFill"]["filled"] == {}


def test_without_fills_the_cohort_is_what_intake_writes(no_reference_inputs):
    """No fills: no public_data_fills.csv, and provenance identical to the command line's."""
    from fcf_m2 import intake
    _session(SYNTHETIC)
    assert "inputs/public_data_fills.csv" not in _strict(api.output_files())["files"]
    applied = api._applied()
    args = dict(reviewer="r", source_org="o", source_date="2026-10-01", applied=applied)
    plain = intake.provenance_rows(api._session.proposal, list(applied["site_id"]), **args)
    empty = intake.provenance_rows(api._session.proposal, list(applied["site_id"]), **args, public_fills={})
    assert plain.equals(empty)
