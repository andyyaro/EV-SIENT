"""The column dictionary must say what every column is, and never read a cell it cannot defend.

The property under test
-----------------------
docs/FLEXIBLE_ANALYSIS.md section 1, and Phase A's exit criterion from the 2026-10-18 report: on
the 360-site test file, every column the model does not use gets either a role with shown
evidence or an explicit `unknown`, with **zero silent coercions**. A silent coercion is a cell
whose reading nobody can see: a "1.234" guessed to be a thousand, an "NA" swallowed as missing,
a 105 on a 0 to 100 scale quietly made 100. So most assertions here are about the reading
report, because that report is what makes a coercion visible.

The 360-site file itself is the owner's and is not committed. `dictionary_360_sample.csv` has its
header and invented rows of the same shapes; set EVSIENT_360_FILE to the real file to run the
golden test on it as well.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import intake  # noqa: E402
from fcf_m2.flex import dictionary as dc  # noqa: E402

FIXTURES = REPO / "tests/fixtures/flex"

#: The role each of the 360-site file's 31 columns is given, which the sample shares.
GOLDEN_ROLES = {
    "site_id": "identifier", "site_name": "name", "latitude": "latitude",
    "longitude": "longitude", "city": "category", "region": "category", "country": "category",
    "site_type": "category", "program_focus": "category", "operating_model": "category",
    "project_status": "category", "service_population": "count", "building_area_m2": "measure",
    "shade_area_m2": "measure", "heat_risk_0_100": "score", "flood_risk": "ordinal",
    "accessibility_1_5": "ordinal", "solar_roof_potential_kw": "measure",
    "battery_capacity_kwh": "measure", "expected_daily_visits": "count",
    "estimated_upgrade_cost_usd": "money", "community_priority_1_5": "ordinal",
    "opening_year": "year", "last_assessed_on": "date", "custom_neighborhood": "category",
    "custom_local_program": "category", "custom_open_after_dark": "flag",
    "custom_partner_name": "name", "custom_volunteer_capacity": "count", "custom_notes": "text",
    "record_origin": "category",
}


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=object, keep_default_na=False)


def _fixture(name: str) -> pd.DataFrame:
    return _read(FIXTURES / f"dictionary_{name}.csv")


def _by_name(entries: list[dict]) -> dict[str, dict]:
    return {e["name"]: e for e in entries}


def _pattern(entry: dict, pattern: str, kind: str | None = None) -> dict:
    found = [p for p in entry["evsient:reading"]["patterns"]
             if p["pattern"] == pattern and (kind is None or p["kind"] == kind)]
    assert len(found) == 1, (pattern, entry["evsient:reading"]["patterns"])
    return found[0]


def _assert_no_silent_coercion(frame: pd.DataFrame, entries: list[dict]) -> None:
    """Every cell is accounted for by a pattern, and every cell `parse` leaves empty is one the
    reading report says was missing, unread, or a state that is neither yes nor no."""
    parsed = dc.parse(frame, entries)
    for entry in entries:
        name, reading = entry["name"], entry["evsient:reading"]
        assert reading["cells"] == len(frame)
        assert reading["read"] + reading["missing"] + reading["unreadable"] == reading["cells"], name
        shown = sum(p["count"] for p in reading["patterns"])
        rest = reading["patternsNotShown"]["cells"] if reading["patternsNotShown"] else 0
        assert shown + rest == reading["cells"], name
        assert len(reading["patterns"]) <= dc.PATTERN_CAP
        not_read = {k: 0 for k in ("missing", "unreadable", "ambiguous", "extra")}
        for p in reading["patterns"]:
            if p["kind"] in not_read:
                not_read[p["kind"]] += p["count"]
        empty = int(parsed[(name, "value")].isna().sum())
        if not reading["patternsNotShown"]:
            assert empty == sum(not_read.values()), name
        assert empty == reading["missing"] + reading["unreadable"] + not_read["extra"], name
        # The raw cells are the frame's own, untouched.
        assert parsed[(name, "raw")].tolist() == frame[name].tolist()


# ---------- the golden test ----------

def _golden(frame: pd.DataFrame) -> None:
    mapping = intake.propose(frame).mapping
    entries = dc.propose(frame, mapping)
    assert [e["name"] for e in entries] == list(frame.columns)
    assert {e["name"]: e["evsient:role"] for e in entries} == GOLDEN_ROLES

    mapped = set(mapping.values())
    unmapped = [e for e in entries if e["name"] not in mapped]
    assert len(mapped) == 7 and len(unmapped) == 24
    for entry in unmapped:
        assert entry["evsient:modelField"] is None
        assert entry["evsient:role"] in dc.ROLES
        if entry["evsient:role"] != "unknown":
            assert any(e["signal"] in ("header", "values", "scale", "range")
                       for e in entry["evsient:evidence"]), entry["name"]
    for entry in entries:
        assert entry["evsient:direction"] is None
        assert entry["evsient:provenance"] == "inferred"
        for item in entry["evsient:evidence"]:
            assert item["match"] and item["text"]
    by = _by_name(entries)
    assert by["latitude"]["evsient:modelField"] == "lat"
    assert by["flood_risk"]["evsient:modelField"] == "stormwater_risk"
    _assert_no_silent_coercion(frame, entries)

    flood = by["flood_risk"]
    assert flood["categories"] == ["Low", "Moderate", "High"]
    assert flood["categoriesOrdered"] is True and flood["missingValues"] == ["Unknown"]
    assert flood["evsient:agreement"] == "agree"
    assert {e["direction"] for e in flood["evsient:evidence"] if e["signal"] == "direction"} == {"lower_better"}
    assert by["accessibility_1_5"]["categories"] == [1, 2, 3, 4, 5]
    assert by["heat_risk_0_100"]["evsient:range"] == [0, 100]
    assert by["solar_roof_potential_kw"]["evsient:unit"] == "kW"
    assert by["battery_capacity_kwh"]["evsient:unit"] == "kW.h"
    assert by["building_area_m2"]["evsient:unit"] == "m2"
    assert by["estimated_upgrade_cost_usd"]["evsient:unit"] == "USD"
    dark = by["custom_open_after_dark"]
    assert dark["categories"] == ["Yes", "No", "Seasonal"] and dark["missingValues"] == ["To be confirmed"]
    json.dumps(entries, allow_nan=False)


def test_golden_on_the_360_site_sample():
    _golden(_fixture("360_sample"))


@pytest.mark.skipif(not os.environ.get("EVSIENT_360_FILE"), reason="EVSIENT_360_FILE not set")
def test_golden_on_the_owners_360_site_file():
    _golden(_read(Path(os.environ["EVSIENT_360_FILE"])))


def test_proposals_are_deterministic():
    frame = _fixture("360_sample")
    assert json.dumps(dc.propose(frame)) == json.dumps(dc.propose(frame.copy()))


# ---------- reading cells ----------

def test_missing_markers_are_the_contracts_visible_list_and_na_stays_a_value():
    assert dc.MISSING_MARKERS == ("", "n/a", "N/A", "NULL", "null", "none", "-", "Unknown",
                                  "unknown", "TBD", "To be confirmed")
    frame = _fixture("namibia")
    by = _by_name(dc.propose(frame))
    country = by["country_code"]
    assert country["evsient:role"] == "category"
    assert "NA" in country["categories"] and country["missingValues"] == []
    assert _pattern(country, "NA")["count"] == 3
    visits = by["daily_visits"]
    assert visits["missingValues"] == ["", "n/a"]
    assert _pattern(visits, "NA")["kind"] == "unreadable"
    _assert_no_silent_coercion(frame, list(by.values()))
    parsed = dc.parse(frame, list(by.values()))
    assert parsed[("country_code", "value")].tolist().count("NA") == 3


def test_a_decimal_comma_column_is_decided_from_cells_that_can_only_be_read_one_way():
    frame = _fixture("decimal_comma")
    entries = dc.propose(frame)
    by = _by_name(entries)
    rain = by["rainfall_mm"]
    assert rain["decimalChar"] == "," and rain["evsient:reading"]["decimalSeparator"] == ","
    assert rain["evsient:reading"]["ambiguous"] == 1
    parsed = dc.parse(frame, entries)
    assert parsed[("rainfall_mm", "value")].tolist()[:5] == [12.5, 3.75, 1234.5, 1.234, 0.5]

    # Every cell could be read two ways and nothing settles it: none is read, all are counted.
    plot = by["plot_area_m2"]
    assert plot["decimalChar"] is None
    assert plot["evsient:reading"]["read"] == 0 and plot["evsient:reading"]["ambiguous"] == 5
    assert _pattern(plot, "9.999")["kind"] == "ambiguous"
    assert parsed[("plot_area_m2", "value")].isna().all()

    # Both marks in one column: each unambiguous cell is read as written, the rest are not.
    mixed = by["mixed_load_kw"]
    assert mixed["decimalChar"] is None and mixed["evsient:agreement"] == "conflict"
    assert parsed[("mixed_load_kw", "value")].tolist()[:2] == [12.5, 3.75]
    assert math.isnan(parsed[("mixed_load_kw", "value")].tolist()[2])
    _assert_no_silent_coercion(frame, entries)


def test_thousands_separators_and_currency_signs_are_read_with_a_pattern_recorded():
    frame = _fixture("thousands")
    entries = dc.propose(frame)
    by = _by_name(entries)
    parsed = dc.parse(frame, entries)
    assert parsed[("estimated_upgrade_cost_usd", "value")].tolist() == [1234567.0, 12500.0, 3400.5, 800.0, 2000.0]
    assert parsed[("budget_eur", "value")].tolist() == [1234567.0, 12500.0, 3400.5, 800.0, 2000.0]
    assert parsed[("catchment_population", "value")].tolist() == [12500.0, 8750.0, 950.0, 1204300.0, 15000.0]
    cost = by["estimated_upgrade_cost_usd"]
    assert "'$' sign is set aside" in _pattern(cost, "$9,999,999")["readAs"]
    assert "separates thousands" in _pattern(cost, "99,999")["readAs"]
    assert by["budget_eur"]["decimalChar"] == "," and by["budget_eur"]["evsient:unit"] == "EUR"
    # Commas alone, with no cell to settle them, are never guessed to be thousands.
    grant = by["grant_amount"]
    assert grant["evsient:role"] == "money" and grant["evsient:unit"] is None
    assert grant["evsient:reading"]["read"] == 0 and grant["evsient:reading"]["ambiguous"] == 4
    _assert_no_silent_coercion(frame, entries)


def test_sentinels_are_flagged_and_never_applied():
    frame = _fixture("sentinels")
    entries = dc.propose(frame)
    by = _by_name(entries)
    parsed = dc.parse(frame, entries)
    population = by["service_population"]
    assert population["evsient:reading"]["sentinels"] == [
        {"value": "-999", "count": 1}, {"value": "9999", "count": 1}, {"value": "99999", "count": 1}]
    assert population["missingValues"] == []
    assert parsed[("service_population", "value")].tolist() == [1200.0, -999.0, 9999.0, 4300.0, 99999.0, 2100.0]
    assert _pattern(population, "-999", "sentinel")["count"] == 1
    assert by["depth_m"]["evsient:reading"]["sentinels"] == [{"value": "-999", "count": 2}]
    # A sentinel outside a declared range is still only flagged, and does not make it conflict.
    heat = by["heat_risk_0_100"]
    assert heat["evsient:agreement"] == "agree" and heat["evsient:reading"]["outOfRange"] == 0
    assert parsed[("heat_risk_0_100", "value")].tolist()[1] == -99.0
    # -99 is a real longitude.
    assert by["longitude"]["evsient:reading"]["sentinels"] == []
    _assert_no_silent_coercion(frame, entries)

    # Marking one missing is the visitor's act, and only then does it read as missing.
    marked = dc.reread(frame, dc.confirm(entries, [{"column": "depth_m", "missingValues": ["-999"]}]))
    assert dc.parse(frame, marked)[("depth_m", "value")].isna().sum() == 2


def test_yes_no_columns_keep_their_extra_states_visible():
    frame = _fixture("yes_no")
    entries = dc.propose(frame)
    by = _by_name(entries)
    dark = by["open_after_dark"]
    assert dark["evsient:role"] == "flag"
    assert dark["categories"] == ["Yes", "No", "Seasonal"]
    assert dark["missingValues"] == ["To be confirmed", "Unknown"]
    assert _pattern(dark, "Seasonal")["kind"] == "extra"
    parsed = dc.parse(frame, entries)
    values = parsed[("open_after_dark", "value")].tolist()
    assert values[:2] == [1.0, 0.0] and math.isnan(values[2])
    assert by["has_parking"]["evsient:agreement"] == "agree"
    assert by["fire_access_ok"]["categories"] == ["Y", "N", "Partial"]
    _assert_no_silent_coercion(frame, entries)


def test_out_of_range_values_and_decimals_on_whole_scales_are_reported_never_clamped():
    frame = _fixture("out_of_range")
    entries = dc.propose(frame)
    by = _by_name(entries)
    parsed = dc.parse(frame, entries)
    heat = by["heat_risk_0_100"]
    assert heat["evsient:agreement"] == "conflict"
    assert heat["evsient:reading"]["outOfRange"] == 2
    assert parsed[("heat_risk_0_100", "value")].tolist() == [45.0, 105.0, -3.0, 88.0, 67.5]
    # A 1 to 5 scale with a 6 and a 2.5 is not read as levels: the values are kept as numbers.
    access = by["accessibility_1_5"]
    assert access["evsient:role"] == "score" and access["evsient:agreement"] == "conflict"
    assert access["evsient:reading"]["outOfRange"] == 1 and access["evsient:reading"]["notWhole"] == 1
    assert _pattern(access, "2.5")["kind"] == "notWhole"
    assert parsed[("accessibility_1_5", "value")].tolist() == [3.0, 6.0, 2.5, 4.0, 1.0]
    assert by["satisfaction_1_5"]["evsient:role"] == "ordinal"
    assert parsed[("satisfaction_1_5", "value")].tolist() == [3.0, 1.0, 4.0, 0.0, 2.0]
    assert by["ev_share_local"]["evsient:role"] == "percentage"
    assert by["ev_share_local"]["evsient:range"] == [0, 1]
    assert by["latitude"]["evsient:agreement"] == "conflict"
    _assert_no_silent_coercion(frame, entries)


def test_dates_take_their_day_and_month_order_from_cells_that_settle_it():
    frame = _fixture("dates")
    entries = dc.propose(frame)
    by = _by_name(entries)
    parsed = dc.parse(frame, entries)
    assert by["assessed_on"]["format"] == "%d/%m/%Y"
    assert by["assessed_on"]["evsient:reading"]["ambiguous"] == 1
    assert [str(d.date()) for d in parsed[("assessed_on", "value")]] == [
        "2026-10-18", "2026-03-05", "2026-04-04", "2025-12-31"]
    assert by["surveyed_on"]["format"] is None
    assert by["surveyed_on"]["evsient:reading"]["read"] == 0
    inspected = by["inspected_date"]
    assert inspected["evsient:agreement"] == "conflict"
    assert _pattern(inspected, "2026-13-01")["kind"] == "unreadable"
    _assert_no_silent_coercion(frame, entries)

    chosen = dc.reread(frame, dc.confirm(entries, [{"column": "surveyed_on", "dateFormat": "%m/%d/%Y"}]))
    assert [str(d.date()) for d in dc.parse(frame, chosen)[("surveyed_on", "value")].dropna()] == [
        "2026-03-04", "2026-04-05", "2026-06-07"]


def test_a_numeric_column_with_text_in_it_is_reported_not_coerced():
    frame = pd.DataFrame({"parking_spaces": ["12", "about 50", "8", "14", "9", "11", "7", "6", "10", "13"]},
                         dtype=object)
    entry = dc.propose(frame)[0]
    assert entry["evsient:role"] == "count"
    assert _pattern(entry, "about 50")["kind"] == "unreadable"
    assert entry["evsient:reading"]["unreadable"] == 1


def test_patterns_are_capped_and_the_rest_counted():
    frame = pd.DataFrame({"notes": [f"note number {i}" for i in range(60)] + ["note number 1"]}, dtype=object)
    entry = dc.propose(frame)[0]
    reading = entry["evsient:reading"]
    assert len(reading["patterns"]) == dc.PATTERN_CAP
    assert reading["patternsNotShown"] == {"patterns": 10, "cells": 10}
    _assert_no_silent_coercion(frame, [entry])


@pytest.mark.parametrize("header,role,unit", [
    ("trench_cost_per_ft", "money", None),
    ("solarRoofKw", "measure", "kW"),
    ("country_code", "category", None),
    ("site_code", "identifier", None),
    ("share_of_ev_pct", "percentage", "%"),
    ("dwell_hr", "measure", "h"),
    ("budget_euros", "money", "EUR"),
    ("fire_access_ok", "flag", None),
    ("postal_code", "address", None),
    ("plan_a", None, None),
    ("years_open", None, None),
    ("opening_year", "year", None),
])
def test_header_grammar(header, role, unit):
    head = dc._read_header(header)
    assert head.role == role and head.unit == unit


def test_direction_words_reach_the_evidence_only():
    entry = dc.propose(pd.DataFrame({"wait_time_min": ["5", "10", "15"]}, dtype=object))[0]
    assert entry["evsient:direction"] is None
    assert [e["direction"] for e in entry["evsient:evidence"] if e["signal"] == "direction"] == ["lower_better"]


def test_model_mapping_must_name_columns_in_the_file():
    frame = _fixture("yes_no")
    with pytest.raises(ValueError, match="not a column in this file"):
        dc.propose(frame, {"public_access": "no_such_column"})


# ---------- confirming ----------

@pytest.fixture()
def proposed() -> list[dict]:
    return dc.propose(_fixture("360_sample"), intake.propose(_fixture("360_sample")).mapping)


def test_confirm_sets_direction_and_provenance_and_changes_nothing_it_was_given(proposed):
    before = json.dumps(proposed)
    out = dc.confirm(proposed, [{"column": "heat_risk_0_100", "direction": "lower_better"},
                                {"column": "city", "confirm": True}])
    assert json.dumps(proposed) == before
    by = _by_name(out)
    assert by["heat_risk_0_100"]["evsient:direction"] == "lower_better"
    assert by["heat_risk_0_100"]["evsient:provenance"] == "confirmed_by_user"
    assert by["heat_risk_0_100"]["evsient:reading"] is not None
    assert by["city"]["evsient:provenance"] == "confirmed_by_user"
    assert by["region"]["evsient:provenance"] == "inferred"
    # A confirmed entry stays confirmed through further changes.
    again = _by_name(dc.confirm(out, [{"column": "heat_risk_0_100", "direction": None}]))
    assert again["heat_risk_0_100"]["evsient:provenance"] == "confirmed_by_user"


def test_marking_a_state_missing_moves_it_out_of_the_levels(proposed):
    frame = _fixture("360_sample")
    out = dc.confirm(proposed, [{"column": "custom_open_after_dark",
                                 "missingValues": ["To be confirmed", "Seasonal"]}])
    dark = _by_name(out)["custom_open_after_dark"]
    assert dark["categories"] == ["Yes", "No"]
    assert dark["evsient:reading"] is None
    dark = _by_name(dc.reread(frame, out))["custom_open_after_dark"]
    assert _pattern(dark, "Seasonal")["kind"] == "missing"
    # Unmarking it brings it back as a state.
    back = _by_name(dc.confirm(out, [{"column": "custom_open_after_dark",
                                      "missingValues": ["To be confirmed"]}]))
    assert back["custom_open_after_dark"]["categories"] == ["Yes", "No", "Seasonal"]


def test_reordering_an_ordinal(proposed):
    out = _by_name(dc.confirm(proposed, [{"column": "flood_risk", "categories": ["High", "Moderate", "Low"]}]))
    assert out["flood_risk"]["categories"] == ["High", "Moderate", "Low"]
    assert out["flood_risk"]["categoriesOrdered"] is True


def test_making_a_category_ordinal_needs_an_order(proposed):
    with pytest.raises(ValueError, match="need an order"):
        dc.confirm(proposed, [{"column": "project_status", "role": "ordinal"}])
    out = _by_name(dc.confirm(proposed, [{"column": "project_status", "role": "ordinal",
                                          "categories": ["Idea", "Scoping", "Feasibility", "Design"]}]))
    assert out["project_status"]["evsient:role"] == "ordinal"
    assert out["project_status"]["categoriesOrdered"] is True


@pytest.mark.parametrize("change,message", [
    ({"column": "nope", "confirm": True}, "no column called 'nope'"),
    ({"column": "city", "role": "banana"}, "not a kind of column"),
    ({"column": "heat_risk_0_100", "direction": "up"}, "must be higher_better"),
    ({"column": "city", "direction": "higher_better"}, "cannot be better"),
    ({"column": "flood_risk", "categories": ["Low", "High"]}, "cannot be dropped"),
    ({"column": "flood_risk", "categories": ["Low", "Moderate", "High", "Severe"]}, "not a value"),
    ({"column": "flood_risk", "missingValues": []}, "Say where 'Unknown' sits"),
    ({"column": "estimated_upgrade_cost_usd", "unit": "XYZ"}, "not a currency code"),
    ({"column": "city", "unit": "kW"}, "has no unit"),
    ({"column": "heat_risk_0_100", "range": [100, 0]}, "lowest first"),
    ({"column": "heat_risk_0_100", "decimalSeparator": ";"}, "must be '.' or ','"),
    ({"column": "city", "colour": "red"}, "not something that can be changed"),
    ({"column": "city", "role": "flag", "categories": ["Bayview", "Hillcrest", "Lakeside", "Riverton"]},
     "read as yes or no"),
])
def test_confirm_refuses_what_the_dictionary_cannot_hold(proposed, change, message):
    with pytest.raises(ValueError, match=message):
        dc.confirm(proposed, [change])


def test_a_direction_cannot_be_smuggled_into_an_inferred_entry(proposed):
    entry = dict(_by_name(proposed)["heat_risk_0_100"], **{"evsient:direction": "lower_better"})
    with pytest.raises(ValueError, match="never confirmed"):
        dc.to_table_schema([entry])


# ---------- the project file ----------

def test_table_schema_round_trips_exactly(proposed):
    confirmed = dc.confirm(proposed, [{"column": "heat_risk_0_100", "direction": "lower_better"},
                                      {"column": "flood_risk", "direction": "lower_better"}])
    for entries in (proposed, confirmed):
        schema = dc.to_table_schema(entries)
        text = json.dumps(schema, allow_nan=False)
        assert dc.from_table_schema(json.loads(text)) == entries
    schema = dc.to_table_schema(confirmed)
    assert schema["$schema"] == dc.TABLE_SCHEMA_PROFILE
    fields = {f["name"]: f for f in schema["fields"]}
    assert "categories" not in fields["heat_risk_0_100"]
    assert fields["flood_risk"]["categories"] == ["Low", "Moderate", "High"]
    assert fields["flood_risk"]["type"] == "string"
    assert fields["accessibility_1_5"]["type"] == "integer"
    assert fields["last_assessed_on"]["type"] == "date" and fields["opening_year"]["type"] == "year"
    assert all(k.startswith("evsient:") or k in ("name", "type", "format", "categories",
                                                 "categoriesOrdered", "missingValues", "decimalChar")
               for f in schema["fields"] for k in f)


@pytest.mark.parametrize("name", ["360_sample", "decimal_comma", "sentinels", "namibia", "thousands",
                                  "yes_no", "out_of_range", "dates"])
def test_every_proposal_is_one_the_project_file_can_hold(name):
    entries = dc.propose(_fixture(name))
    assert dc.from_table_schema(json.loads(json.dumps(dc.to_table_schema(entries)))) == entries


def test_empty_columns_are_proposed_without_inventing_states():
    frame = pd.DataFrame({"has_parking": ["", "", ""], "city": ["", "n/a", "-"],
                          "rating_1_5": ["", "", ""], "cost_usd": ["", "", ""]}, dtype=object)
    by = _by_name(dc.propose(frame))
    assert by["has_parking"]["evsient:role"] == "unknown"
    assert by["city"]["evsient:role"] == "unknown"
    assert by["cost_usd"]["evsient:role"] == "money"
    assert all(e["evsient:agreement"] == "unknown" for e in by.values())
    assert all(e["evsient:reading"]["missing"] == 3 for e in by.values())
    dc.to_table_schema(list(by.values()))


def test_a_damaged_or_newer_project_file_is_refused(proposed):
    schema = dc.to_table_schema(proposed)
    with pytest.raises(ValueError, match="version"):
        dc.from_table_schema({**schema, "evsient:dictionaryVersion": 2})
    del schema["fields"][0]["evsient:role"]
    with pytest.raises(ValueError, match="missing evsient:role"):
        dc.from_table_schema(schema)


# ---------- typed values ----------

def test_parse_types_each_role(proposed):
    frame = _fixture("360_sample")
    parsed = dc.parse(frame, proposed)
    assert list(parsed.columns.names) == ["column", "part"]
    flood = parsed[("flood_risk", "value")]
    expected = {"Low": 0.0, "Moderate": 1.0, "High": 2.0}
    for raw, value in zip(frame["flood_risk"], flood):
        assert (math.isnan(value) if raw == "Unknown" else value == expected[raw])
    assert parsed[("city", "value")].dtype.name == "category"
    assert str(parsed[("last_assessed_on", "value")].dtype).startswith("datetime64")
    assert parsed[("service_population", "value")].dtype == "float64"
    assert parsed[("site_id", "value")].tolist() == frame["site_id"].tolist()


# ---------- the browser door ----------

def test_bridge_functions_match_the_native_ones():
    frame = _fixture("360_sample")
    mapping = intake.propose(frame).mapping
    table = {"columns": list(frame.columns), "rows": frame.values.tolist()}
    got = json.loads(dc.bridge_propose(json.dumps(table), json.dumps({"mapping": mapping})))
    assert got["entries"] == json.loads(json.dumps(dc.propose(frame, mapping)))
    changes = {"changes": [{"column": "flood_risk", "direction": "lower_better"}]}
    confirmed = json.loads(dc.bridge_confirm(json.dumps(got), json.dumps(changes)))["entries"]
    assert _by_name(confirmed)["flood_risk"]["evsient:direction"] == "lower_better"
    reread = json.loads(dc.bridge_reread(json.dumps(table), json.dumps({"entries": confirmed})))
    assert reread["entries"] == json.loads(json.dumps(dc.reread(frame, confirmed)))
