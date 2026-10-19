"""A visitor's own index (src/fcf_m2/flex/index.py), held to docs/FLEXIBLE_ANALYSIS.md section 3.

The index is the visitor's, never the readiness model's, but it is read the same way, so these
tests hold it to the same promises: each site's drivers add up to its score; anchors are pinned,
so taking rows away never changes another site's score; screens remove sites with a reason and
refuse what they cannot run; every gate fires on a fixture built to trip it and stays quiet on a
clean one; the robustness draws repeat exactly from a seed; "what would change the rank" is
checked against brute force; refusals are sentences; and every answer is strict JSON.

The fixtures (tests/fixtures/flex/index_*) are invented sites. The column dictionary is written
out by hand in index_entries.json, so these tests do not depend on fcf_m2.flex.dictionary.
"""

from __future__ import annotations

import copy
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2.flex import index  # noqa: E402

FIX = REPO / "tests/fixtures/flex"
ENTRIES = json.loads((FIX / "index_entries.json").read_text())


def _strict(text: str):
    """json.loads, but NaN and Infinity are errors, as they are for JSON.parse."""
    def refuse(token):
        raise AssertionError(f"non-JSON constant {token} in index output")
    return json.loads(text, parse_constant=refuse)


def _table(name: str) -> dict:
    with open(FIX / name, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return {"columns": rows[0], "rows": rows[1:]}


def _frames(table: dict, entries: list[dict]):
    return index.frames(table, entries)


def _run(table: dict, entries: list[dict], spec: dict, **kw) -> dict:
    raw, typed, name_column = _frames(table, entries)
    return index.run(typed, raw, spec, entries=entries, name_column=name_column, **kw)


def _criterion(column, direction, weight, **value):
    return {"column": column, "direction": direction, "weight": weight, "value": value}


def _spec(criteria, **extra) -> dict:
    return {"pack": "evsient-custom-index", "packVersion": "1.0.0", "name": "Test index",
            "criteria": criteria, **extra}


CLEAN_SPEC = _spec([
    _criterion("heat_risk_0_100", "higher_better", 3, kind="linear", worst=0, best=100),
    _criterion("flood_risk", "lower_better", 3, kind="ordinal",
               map={"Low": 1.0, "Moderate": 0.5, "High": 0.0}),
    _criterion("solar_kw", "higher_better", 2.5, kind="threshold", worst=20, best=240),
    _criterion("access_1_5", "higher_better", 2.5, kind="linear"),
], robustness={"draws": 400, "spread": 0.25, "seed": 1})

ADVERSARIAL_SPEC = _spec([
    _criterion("need", "higher_better", 0.5, kind="linear", worst=0, best=100),
    _criterion("need_again", "higher_better", 0.3, kind="linear", worst=0, best=100),
    _criterion("sparse", "higher_better", 0.1, kind="linear", worst=0, best=100),
    _criterion("heavy_tail", "higher_better", 0.05, kind="linear"),
    _criterion("tiny", "higher_better", 0.05, kind="linear", worst=0, best=100),
], robustness={"draws": 400, "spread": 0.25, "seed": 1})

HEAT_REFUGE = _spec([
    _criterion("heat_risk_0_100", "higher_better", 0.4, kind="linear", worst=0, best=100),
    _criterion("flood_risk", "lower_better", 0.3, kind="ordinal",
               map={"Low": 1.0, "Moderate": 0.5, "High": 0.0}),
    _criterion("solar_kw", "higher_better", 0.3, kind="threshold", worst=50, best=200),
], screens=[{"logic": {"!=": [{"var": "flood_risk"}, "High"]}, "reason": "High flood risk"}],
    missing="no_credit", minCoverage=0.65,
    robustness={"draws": 500, "spread": 0.25, "seed": 1})


@pytest.fixture(scope="module")
def clean() -> dict:
    return _run(_table("index_clean.csv"), ENTRIES["clean"], CLEAN_SPEC,
                population_column="population")


@pytest.fixture(scope="module")
def adversarial() -> dict:
    return _run(_table("index_adversarial.csv"), ENTRIES["adversarial"], ADVERSARIAL_SPEC,
                population_column="population")


def _with_blanks(table: dict, column: str, every: int) -> dict:
    """The same table with every `every`-th cell of a column left empty."""
    out = copy.deepcopy(table)
    j = out["columns"].index(column)
    for i, row in enumerate(out["rows"]):
        if i % every == 0:
            row[j] = ""
    return out


# ---------- the score is the sum of its drivers ----------

class TestDriversSumToScore:
    def _check(self, result):
        sites = result["sites"] + result["unranked"]
        assert sites
        for s in sites:
            total = math.fsum(d["points"] for d in s["drivers"])
            assert abs(total - s["score"]) < 1e-9, s["siteId"]
            for d in s["drivers"]:
                assert 0.0 <= d["value"] <= 1.0
                assert abs(d["points"] - 100 * d["weight"] * d["value"]) < 1e-9
                assert abs(d["max"] - 100 * d["weight"]) < 1e-9
                assert d["absent"] == (d["column"] in s["missing"])
            gained = math.fsum(d["max"] for d in s["drivers"] if d["absent"])
            assert s["bounds"]["worst"] == s["score"]
            assert abs(s["bounds"]["best"] - (s["score"] + gained)) < 1e-9
            assert 0.0 <= s["score"] <= 100.0
            present = sum(not d["absent"] for d in s["drivers"])
            assert s["completeness"] == present / len(s["drivers"])

    def test_clean(self, clean):
        self._check(clean)

    def test_adversarial_with_missing_values(self, adversarial):
        assert any(s["missing"] for s in adversarial["sites"])
        self._check(adversarial)

    def test_unranked_sites_are_scored_but_not_ranked(self):
        table = _table("index_clean.csv")
        for column in ("heat_risk_0_100", "solar_kw"):
            table = _with_blanks(table, column, 4)
        result = _run(table, ENTRIES["clean"], CLEAN_SPEC)
        assert result["unranked"], "sites missing half their criteria should be unranked"
        for s in result["unranked"]:
            assert "rank" not in s and s["completeness"] < 0.65
            assert "under the 65%" in s["reason"]
        self._check(result)

    def test_weights_are_normalised_and_shown(self, clean):
        weights = [f["weight"] for f in clean["formula"]]
        assert abs(math.fsum(weights) - 1) < 1e-12
        assert [f["weightGiven"] for f in clean["formula"]] == [3, 3, 2.5, 2.5]
        assert clean["formula"][0]["weight"] == 3 / 11

    def test_ranks_follow_scores_and_ties_share_a_rank(self, clean):
        scores = [s["score"] for s in clean["sites"]]
        assert scores == sorted(scores, reverse=True)
        for s in clean["sites"]:
            assert s["rank"] == 1 + sum(t["score"] > s["score"] for t in clean["sites"])


# ---------- value functions and pinned anchors ----------

class TestAnchors:
    def test_linear_anchors_default_to_the_observed_range_and_are_stored(self, clean):
        access = next(c for c in clean["spec"]["criteria"] if c["column"] == "access_1_5")
        assert access["value"] == {"kind": "linear", "worst": 1.0, "best": 5.0,
                                   "pinnedFrom": "observed range"}

    def test_filtering_rows_never_changes_another_sites_score(self, clean):
        table = _table("index_clean.csv")
        pinned = clean["spec"]
        before = {s["siteId"]: s["score"] for s in clean["sites"]}
        # Drop the sites holding the extremes of every column, and a block of others.
        drop = {clean["sites"][0]["siteId"], clean["sites"][-1]["siteId"]}
        for column in ("access_1_5", "heat_risk_0_100", "solar_kw"):
            j = table["columns"].index(column)
            values = [float(r[j]) for r in table["rows"]]
            for target in (min(values), max(values)):
                drop |= {r[0] for r in table["rows"] if float(r[j]) == target}
        subset = dict(table, rows=[r for r in table["rows"] if r[0] not in drop][:25])
        after = _run(subset, ENTRIES["clean"], pinned)
        assert not after["refused"]
        assert len(after["sites"]) == 25
        for s in after["sites"]:
            assert s["score"] == before[s["siteId"]], s["siteId"]
        # Unpinned anchors would have moved: the subset's own access range is narrower or equal.
        assert after["spec"] == pinned

    def test_value_functions_are_bounded_with_anchors_pinned(self):
        x = np.array([-50.0, 0.0, 25.0, 100.0, 150.0, np.nan])
        linear = index._value_of({"kind": "linear", "worst": 0, "best": 100}, x)
        assert linear[:5].tolist() == [0.0, 0.0, 0.25, 1.0, 1.0] and np.isnan(linear[5])
        reverse = index._value_of({"kind": "threshold", "worst": 100, "best": 0}, x)
        assert reverse[:5].tolist() == [1.0, 1.0, 0.75, 0.0, 0.0]
        target = index._value_of({"kind": "target", "low": 0, "target": 25, "high": 125}, x)
        assert target[:5].tolist() == [0.0, 0.0, 1.0, 0.25, 0.0]


# ---------- screens ----------

class TestScreens:
    def test_screens_exclude_with_reasons_before_scoring(self):
        table = _table("index_clean.csv")
        result = _run(table, ENTRIES["clean"], HEAT_REFUGE)
        high = [r[0] for r in table["rows"] if r[3] == "High"]
        assert [e["siteId"] for e in result["excluded"]] == high
        for e in result["excluded"]:
            assert e["reasons"] == [{"screen": 1, "reason": "High flood risk", "missing": []}]
            assert e["name"].startswith("Clean Site")
        assert not {s["siteId"] for s in result["sites"]} & set(high)
        assert result["summary"]["excluded"] == len(high)

    def test_a_missing_value_never_passes_a_numeric_screen_silently(self):
        table = _with_blanks(_table("index_clean.csv"), "solar_kw", 7)
        spec = dict(CLEAN_SPEC, screens=[{"logic": {">=": [{"var": "solar_kw"}, 30]},
                                          "reason": "Too little roof for solar"}])
        result = _run(table, ENTRIES["clean"], spec)
        blank = [r[0] for i, r in enumerate(table["rows"]) if i % 7 == 0]
        excluded = {e["siteId"]: e["reasons"][0] for e in result["excluded"]}
        for site in blank:
            assert excluded[site]["missing"] == ["solar_kw"]

    def test_a_screen_can_read_a_column_the_index_does_not_score(self):
        spec = dict(CLEAN_SPEC, screens=[{"logic": {"==": [{"var": "open_late"}, 1]},
                                          "reason": "Not open late"}])
        result = _run(_table("index_clean.csv"), ENTRIES["clean"], spec)
        table = _table("index_clean.csv")
        late = table["columns"].index("open_late")
        closed = {r[0] for r in table["rows"] if r[late] != "Yes"}
        assert {e["siteId"] for e in result["excluded"]} == closed

    @pytest.mark.parametrize("logic, data, expected", [
        ({"==": [{"var": "a"}, 1]}, {"a": 1.0}, True),
        ({"==": [{"var": "a"}, "1"]}, {"a": 1.0}, True),
        ({"==": [{"var": "a"}, "Low"]}, {"a": "low"}, False),
        ({"!=": [{"var": "a"}, "High"]}, {"a": None}, True),
        ({"<": [{"var": "a"}, 5]}, {"a": 4}, True),
        ({"<": [1, {"var": "a"}, 5]}, {"a": 5}, False),
        ({"<=": [1, {"var": "a"}, 5]}, {"a": 5}, True),
        ({">": [{"var": "a"}, 5]}, {"a": None}, False),
        ({">=": [{"var": "a"}, 5]}, {"a": "text"}, False),
        ({"and": [{">": [{"var": "a"}, 1]}, {"<": [{"var": "a"}, 3]}]}, {"a": 2}, True),
        ({"or": [{"==": [{"var": "a"}, "x"]}, {"==": [{"var": "b"}, "y"]}]},
         {"a": "q", "b": "y"}, True),
        ({"!": [{"var": "a"}]}, {"a": None}, True),
        ({"!": {"var": "a"}}, {"a": "Yes"}, False),
        ({"in": [{"var": "a"}, ["Low", "Moderate"]]}, {"a": "Low"}, True),
        ({"in": [{"var": "a"}, ["Low", "Moderate"]]}, {"a": "High"}, False),
        ({"in": ["Lib", {"var": "a"}]}, {"a": "Library"}, True),
        ({"missing": ["a", "b"]}, {"a": 1, "b": None}, ["b"]),
        ({"var": ["a", 7]}, {"a": None}, 7),
        ({"==": [{"var": "a"}, "__import__('os').system('true')"]}, {"a": "x"}, False),
    ])
    def test_the_jsonlogic_subset(self, logic, data, expected):
        index._logic_nodes(logic)
        assert index.evaluate(logic, data) == expected

    @pytest.mark.parametrize("logic, words", [
        ({"+": [1, 2]}, 'uses "+", which screens do not support'),
        ({"map": [[1], {"var": ""}]}, 'uses "map"'),
        ({"==": [1]}, 'gives "==" 1 argument(s)'),
        ({"==": [1, 2], "!=": [1, 2]}, "more than one operator"),
        ({"var": ""}, 'has a "var" without a column name'),
        ({"==": [{"var": "a"}, {"x": 1}]}, 'uses "x"'),
    ])
    def test_unknown_operators_and_bad_shapes_are_refused(self, logic, words):
        spec = dict(CLEAN_SPEC, screens=[{"logic": logic, "reason": "Bad rule"}])
        out = index.validate(spec, ENTRIES["clean"])
        assert not out["ok"]
        messages = [r["message"] for r in out["refusals"]]
        assert any(m.startswith('The screen "Bad rule" ') and words in m
                   for m in messages), messages

    def test_deep_nesting_is_refused_not_recursed(self):
        logic: dict = {"var": "flood_risk"}
        for _ in range(200):
            logic = {"!": [logic]}
        spec = dict(CLEAN_SPEC, screens=[{"logic": logic, "reason": "Deep"}])
        out = index.validate(spec, ENTRIES["clean"])
        assert "too long or too deeply nested" in out["refusals"][0]["message"]

    def test_a_screen_on_an_unknown_column_is_refused(self):
        spec = dict(CLEAN_SPEC, screens=[{"logic": {"==": [{"var": "zone"}, "A"]},
                                          "reason": "Zone A only"}])
        out = index.validate(spec, ENTRIES["clean"])
        assert out["refusals"] == [{"code": "unknown_column", "column": "zone", "message":
                                    'The screen "Zone A only" reads zone, and there is no column '
                                    "called that in this file."}]


# ---------- gates ----------

class TestGates:
    def test_a_clean_index_trips_no_gate(self, clean):
        assert clean["gates"] == []
        assert clean["gatesChecked"] == list(index.GATES)

    def test_every_gate_fires_on_the_adversarial_fixture(self, adversarial):
        fired = {(g["id"], tuple(g["columns"])): g for g in adversarial["gates"]}
        assert set(g["id"] for g in adversarial["gates"]) == set(index.GATES) - {"minimum_data"}
        coverage = fired[("coverage", ("sparse",))]
        assert coverage["numbers"]["coverage"] == 0.5 and coverage["numbers"]["threshold"] == 0.65
        outliers = fired[("outliers", ("heavy_tail",))]
        n = outliers["numbers"]
        assert n["kurtosis"] > 10 and abs(n["skewness"]) > 2
        assert n["winsorise"]["cappedHigh"] == 3 and n["winsorise"]["resolves"]
        assert n["winsorise"]["cap"] < 100
        assert fired[("dominance", ("need",))]["numbers"]["correlation"] > 0.95
        for column in ("sparse", "heavy_tail", "tiny"):
            r = fired[("barely_counts", (column,))]["numbers"]["correlation"]
            assert -0.3 < r < 0.3
        assert fired[("size_bias", ("population",))]["numbers"]["spearman"] > 0.6
        double = fired[("double_counting", ("need", "need_again"))]
        assert double["level"] == "strong" and double["numbers"]["spearman"] > 0.9
        assert double["numbers"]["weightShare"] == pytest.approx(0.8)

    def test_gate_messages_are_fixed_sentences(self, adversarial):
        for g in adversarial["gates"]:
            assert g["message"].endswith(".") and "\u2014" not in g["message"]
            assert g["message"].startswith(tuple(g["columns"]) + ("The index",))
        message = next(g["message"] for g in adversarial["gates"] if g["id"] == "dominance")
        assert message == ("need correlates 0.99 with the index, above 0.95: the index is mostly "
                           "this one column, whatever the other weights say.")

    def test_double_counting_warns_between_0_8_and_0_9(self):
        rng = np.random.default_rng(3)
        n = 80
        a = rng.uniform(0, 100, n)
        b = np.clip(a + rng.normal(0, 18, n), 0, 100)
        c = rng.uniform(0, 100, n)
        typed = pd.DataFrame({"a": a, "b": b, "c": c}, index=[f"S{i}" for i in range(n)])
        spec = _spec([_criterion(k, "higher_better", 1, kind="linear", worst=0, best=100)
                      for k in "abc"], robustness={"draws": 0})
        result = index.run(typed, pd.DataFrame(index=typed.index), spec)
        double = [g for g in result["gates"] if g["id"] == "double_counting"]
        assert len(double) == 1 and double[0]["level"] == "warn"
        assert 0.8 < double[0]["numbers"]["spearman"] <= 0.9

    def test_size_bias_is_checked_only_with_a_population_column(self):
        result = _run(_table("index_adversarial.csv"), ENTRIES["adversarial"], ADVERSARIAL_SPEC)
        assert "size_bias" not in result["gatesChecked"]
        assert not any(g["id"] == "size_bias" for g in result["gates"])

    @pytest.mark.parametrize("change, code, words", [
        (lambda s: s["criteria"].append(_criterion("constant", "higher_better", 0.1,
                                                   kind="linear", worst=0, best=10)),
         "constant", "constant is 7 for every site left after the screens"),
        (lambda s: s["criteria"].__delitem__(slice(1, None)), "few_criteria",
         "An index needs at least 2 criteria; this one has 1."),
        (lambda s: s["criteria"][0].update(direction=None), "unconfirmed_direction",
         "Confirm whether higher or lower need is better before it goes into an index."),
        (lambda s: s.update(screens=[{"logic": {"<": [{"var": "need"}, 15]},
                                      "reason": "Low need"}]),
         "few_sites", "are left after the screens."),
    ])
    def test_minimum_data_refuses_with_its_gate(self, change, code, words):
        spec = copy.deepcopy(ADVERSARIAL_SPEC)
        change(spec)
        result = _run(_table("index_adversarial.csv"), ENTRIES["adversarial"], spec)
        assert result["refused"] and result["official"] is False
        assert any(r["code"] == code and words in r["message"] for r in result["refusals"]), \
            result["refusals"]
        assert [g["id"] for g in result["gates"]] == ["minimum_data"]
        numbers = result["gates"][0]["numbers"]
        assert numbers["minCriteria"] == 2 and numbers["minSites"] == 10

    def test_fewer_than_ten_sites_in_the_file(self):
        table = _table("index_clean.csv")
        result = _run(dict(table, rows=table["rows"][:9]), ENTRIES["clean"], CLEAN_SPEC)
        assert result["refused"]
        assert result["refusals"][-1]["message"] == ("An index needs at least 10 sites to rank; "
                                                     "this file has 9.")


# ---------- robustness ----------

class TestRobustness:
    def test_draws_repeat_exactly_from_a_seed(self):
        table = _table("index_clean.csv")
        first = index._out(_run(table, ENTRIES["clean"], CLEAN_SPEC))
        second = index._out(_run(table, ENTRIES["clean"], CLEAN_SPEC))
        assert first == second
        other = dict(CLEAN_SPEC, robustness={"draws": 400, "spread": 0.25, "seed": 2})
        third = _run(table, ENTRIES["clean"], other)
        assert [s["robustness"] for s in third["sites"]] != \
            [s["robustness"] for s in json.loads(first)["sites"]]

    def test_rank_bands_and_top_shares(self, clean):
        k = clean["summary"]["k"]
        assert k == 6  # 10% of 60 sites
        for s in clean["sites"]:
            r = s["robustness"]
            assert 1 <= r["rankLow"] <= r["rankHigh"] <= len(clean["sites"])
            assert 0.0 <= r["topShare"] <= 1.0
            assert r["neverTopK"] == (r["topShare"] == 0.0)
        assert clean["robustness"]["ordinalMapsNudged"] == ["flood_risk"]  # Moderate moves
        assert clean["robustness"]["draws"] == 400

    def test_without_spread_the_bands_collapse_to_the_rank(self):
        spec = dict(CLEAN_SPEC, robustness={"draws": 50, "spread": 0, "seed": 1,
                                            "ordinalSpread": 0})
        result = _run(_table("index_clean.csv"), ENTRIES["clean"], spec)
        for s in result["sites"]:
            assert s["robustness"]["rankLow"] == s["rank"] == s["robustness"]["rankHigh"]
            assert s["robustness"]["topShare"] == (1.0 if s["rank"] <= 6 else 0.0)

    def test_ordinal_maps_are_nudged_between_their_neighbours(self):
        criterion = _criterion("flood_risk", "lower_better", 1, kind="ordinal",
                               map={"Low": 1.0, "Moderate": 0.5, "High": 0.0})
        cats, base, lo, hi = index._ordinal_plan(criterion)
        assert cats == ["Low", "Moderate", "High"]
        assert lo.tolist() == [1.0, 0.0, 0.0] and hi.tolist() == [1.0, 1.0, 0.0]

    def test_the_spread_sets_the_typical_relative_move(self):
        weights = np.array([0.4, 0.3, 0.3])
        kappa = index._concentration(weights, 0.25)
        draws = np.random.default_rng(0).dirichlet(kappa * weights, size=20000)
        relative = (draws.std(axis=0) / weights).mean()
        assert abs(relative - 0.25) < 0.01


# ---------- what would change the rank ----------

def _shifted(weights: list[float], j: int, t: float) -> list[float]:
    rest = 1 - weights[j]
    return [w + t if i == j else w * (1 - weights[j] - t) / rest for i, w in enumerate(weights)]


def _score(weights, values) -> float:
    return 100 * math.fsum(w * v for w, v in zip(weights, values))


@pytest.fixture(scope="module")
def small():
    table = _table("index_clean.csv")
    table = dict(table, rows=table["rows"][:12])
    return table, _run(table, ENTRIES["clean"], CLEAN_SPEC)


class TestRankChanges:
    def test_every_adjacent_pair_is_covered(self, small):
        _, result = small
        pairs = [(c["above"], c["below"]) for c in result["rankChanges"]]
        ids = [s["siteId"] for s in result["sites"]]
        assert pairs == list(zip(ids, ids[1:]))

    def test_weight_shifts_swap_the_pair_exactly(self, small):
        _, result = small
        weights = [c["weight"] for c in result["spec"]["criteria"]]
        columns = [c["column"] for c in result["spec"]["criteria"]]
        by_id = {s["siteId"]: [d["value"] for d in s["drivers"]] for s in result["sites"]}
        checked = 0
        for change in result["rankChanges"]:
            a, b = by_id[change["above"]], by_id[change["below"]]
            listed = {s["column"]: s["shift"] for s in change["weightShifts"]}
            for j, column in enumerate(columns):
                # Brute force: scan the criterion's weight from 0 to 1 for where the pair swaps.
                grid = np.linspace(0, 1, 2001)
                gaps = [_score(_shifted(weights, j, w - weights[j]), a)
                        - _score(_shifted(weights, j, w - weights[j]), b) for w in grid]
                crosses = any(g < -1e-9 for g in gaps)
                if column not in listed:
                    assert not crosses, (change["above"], change["below"], column)
                    continue
                t = listed[column]
                at = _shifted(weights, j, t)
                assert abs(_score(at, a) - _score(at, b)) < 1e-9
                step = 1e-6 if t > 0 else -1e-6
                if 0 <= weights[j] + t + step <= 1:
                    past = _shifted(weights, j, t + step)
                    assert _score(past, b) > _score(past, a)
                    assert crosses
                checked += 1
            if change["weightShifts"]:
                best = change["weightShifts"][0]
                assert abs(best["shift"]) == min(abs(t) for t in listed.values())
        assert checked > 10

    def test_value_changes_swap_the_pair_when_applied(self, small):
        table, result = small
        pinned = result["spec"]
        applied = 0
        for change in result["rankChanges"][:6]:
            for vc in change["valueChanges"]:
                edited = copy.deepcopy(table)
                j = edited["columns"].index(vc["column"])
                row = next(r for r in edited["rows"] if r[0] == change["below"])
                if isinstance(vc["to"], str):
                    row[j] = vc["to"]
                else:
                    direction = next(c["direction"] for c in pinned["criteria"]
                                     if c["column"] == vc["column"])
                    nudge = 1e-6 if direction == "higher_better" else -1e-6
                    row[j] = repr(vc["to"] + nudge)
                after = _run(edited, ENTRIES["clean"], pinned)
                scores = {s["siteId"]: s["score"] for s in after["sites"]}
                if vc["ties"]:
                    assert scores[change["below"]] >= scores[change["above"]] - 1e-9
                else:
                    assert scores[change["below"]] > scores[change["above"]]
                applied += 1
        assert applied >= 6

    def test_sentences_name_the_sites_and_the_change(self, small):
        _, result = small
        said = [s for c in result["rankChanges"] for s in c["sentences"]]
        assert all(s.endswith(".") and "\u2014" not in s for s in said)
        assert any(s.startswith("Giving ") and " would lift Clean Site " in s for s in said)
        assert any(" would pass Clean Site " in s for s in said)
        for c in result["rankChanges"]:
            if not c["weightShifts"] and not c["valueChanges"]:
                assert c["sentences"] == [f"No single weight shift or change to one value lifts "
                                          f"{c['below'].replace('C0', 'Clean Site ')} above "
                                          f"{c['above'].replace('C0', 'Clean Site ')}."]

    def test_a_tie_needs_no_change(self):
        rows = [[f"T{i:02d}", f"Tie {i:02d}", str(10 * i), "Low", "100", str(1 + i % 5), "1000",
                 "Yes"] for i in range(10)]
        rows.append(["T99", "Tie 99", "90", "Low", "100", "5", "1000", "Yes"])
        table = {"columns": _table("index_clean.csv")["columns"], "rows": rows}
        spec = _spec([_criterion("heat_risk_0_100", "higher_better", 1, kind="linear",
                                 worst=0, best=100),
                      _criterion("access_1_5", "higher_better", 1, kind="linear", worst=1,
                                 best=5)], robustness={"draws": 0})
        result = _run(table, ENTRIES["clean"], spec)
        tie = result["rankChanges"][0]
        assert tie["tied"] and tie["gap"] == 0
        assert result["sites"][0]["rank"] == result["sites"][1]["rank"] == 1
        assert {result["sites"][0]["siteId"], result["sites"][1]["siteId"]} == {"T09", "T99"}
        assert tie["sentences"] == ["Tie 99 and Tie 09 are tied."]
        assert all(s["shift"] == 0 for s in tie["weightShifts"]) and tie["valueChanges"] == []


# ---------- refusals ----------

class TestRefusals:
    def _messages(self, spec, entries=ENTRIES["clean"]):
        out = index.validate(spec, entries)
        assert not out["ok"] and out["spec"] is None
        return [r["message"] for r in out["refusals"]]

    def test_unconfirmed_direction(self):
        spec = _spec([_criterion("open_late", "higher_better", 1, kind="linear", worst=0, best=1),
                      CLEAN_SPEC["criteria"][0]])
        assert self._messages(spec) == ["Confirm whether higher or lower open_late is better "
                                        "before it goes into an index."]

    def test_direction_that_disagrees_with_the_confirmed_one(self):
        spec = copy.deepcopy(CLEAN_SPEC)
        spec["criteria"][0]["direction"] = "lower_better"
        spec["criteria"][0]["value"] = {"kind": "linear", "worst": 100, "best": 0}
        assert self._messages(spec) == ["The index treats heat_risk_0_100 as lower is better, but "
                                        "you confirmed higher is better. Change one so they agree."]

    def test_unknown_column(self):
        spec = copy.deepcopy(CLEAN_SPEC)
        spec["criteria"][0]["column"] = "shade_m2"
        assert self._messages(spec) == ["There is no column called shade_m2 in this file."]

    @pytest.mark.parametrize("criterion, message", [
        (_criterion("heat_risk_0_100", "higher_better", 1, kind="linear", worst=100, best=0),
         "For heat_risk_0_100, higher is better, so its best value (0) must be above its worst "
         "(100)."),
        (_criterion("heat_risk_0_100", "higher_better", 1, kind="threshold", worst=40, best=40),
         "The worst and best values for heat_risk_0_100 are both 40. Set them apart."),
        (_criterion("heat_risk_0_100", "higher_better", 1, kind="target", low=0, target=50,
                    high=100),
         "A target suits a column where neither direction is better, but you said higher is "
         "better for heat_risk_0_100. Use a linear or threshold value function."),
        (_criterion("heat_risk_0_100", "higher_better", 1, kind="threshold", worst=10),
         "Give heat_risk_0_100 both a worst and a best value, as numbers."),
        (_criterion("flood_risk", "lower_better", 1, kind="ordinal",
                    map={"Low": 0.0, "Moderate": 0.5, "High": 1.0}),
         "For flood_risk, lower is better, so credit must not rise along Low < Moderate < High."),
        (_criterion("flood_risk", "lower_better", 1, kind="linear", worst=0, best=1),
         "flood_risk is a set of categories, not numbers. Give each category a value between 0 "
         "and 1 with an ordinal map."),
    ])
    def test_value_function_inconsistent_with_direction(self, criterion, message):
        spec = _spec([criterion, CLEAN_SPEC["criteria"][2]])
        assert self._messages(spec) == [message]

    def test_ordinal_map_missing_a_category(self):
        spec = _spec([_criterion("flood_risk", "lower_better", 1, kind="ordinal",
                                 map={"Low": 1.0, "High": 0.0}), CLEAN_SPEC["criteria"][0]])
        assert self._messages(spec) == ['The scale for flood_risk gives no value for "Moderate". '
                                        "Give every category a value between 0 and 1."]

    def test_ordinal_map_missing_a_label_found_in_the_data(self):
        typed = pd.DataFrame({"risk": ["Low", "High", "Severe"] * 4,
                              "x": [float(i) for i in range(12)]},
                             index=[f"S{i}" for i in range(12)])
        spec = _spec([_criterion("risk", "lower_better", 1, kind="ordinal",
                                 map={"Low": 1.0, "High": 0.0}),
                      _criterion("x", "higher_better", 1, kind="linear")])
        result = index.run(typed, pd.DataFrame(index=typed.index), spec)
        assert result["refused"]
        assert result["refusals"][0]["message"] == ('The scale for risk gives no value for '
                                                    '"Severe". Give every category a value '
                                                    "between 0 and 1.")

    @pytest.mark.parametrize("weight", [0, -1, None, "high", float("nan"), True])
    def test_weights_not_positive(self, weight):
        spec = copy.deepcopy(CLEAN_SPEC)
        spec["criteria"][1]["weight"] = weight
        messages = self._messages(spec)
        assert len(messages) == 1
        assert messages[0].startswith("The weight on flood_risk is ")
        assert "None" not in messages[0] and "'" not in messages[0]
        assert messages[0].endswith("Every weight must be a number above 0; take the criterion "
                                    "out instead.")

    def test_fewer_than_two_criteria(self):
        assert self._messages(_spec(CLEAN_SPEC["criteria"][:1])) == [
            "An index needs at least 2 criteria; this one has 1."]

    def test_constant_criterion(self):
        typed = pd.DataFrame({"a": [5.0] * 12, "b": [float(i) for i in range(12)]},
                             index=[f"S{i}" for i in range(12)])
        spec = _spec([_criterion("a", "higher_better", 1, kind="linear"),
                      _criterion("b", "higher_better", 1, kind="linear")])
        result = index.run(typed, pd.DataFrame(index=typed.index), spec)
        assert [r["message"] for r in result["refusals"]] == [
            "a is 5 for every site, so it cannot separate them. Take it out of the index."]

    def test_text_where_numbers_are_needed(self):
        typed = pd.DataFrame({"a": ["High", "Low"] * 6, "b": [float(i) for i in range(12)]},
                             index=[f"S{i}" for i in range(12)])
        spec = _spec([_criterion("a", "higher_better", 1, kind="linear", worst=0, best=1),
                      _criterion("b", "higher_better", 1, kind="linear")])
        result = index.run(typed, pd.DataFrame(index=typed.index), spec)
        assert result["refusals"][0]["message"].startswith('a holds text such as "High"')

    def test_pack_version_name_and_policies(self):
        spec = dict(CLEAN_SPEC, pack="other", packVersion="2.0.0", name=" ", missing="mean",
                    minCoverage=1.5, robustness={"draws": -1, "spread": 3, "seed": "x"})
        messages = self._messages(spec)
        assert messages == [
            'These settings are for "other", not for an index built here (evsient-custom-index).',
            "This index was saved as version 2.0.0; this planner reads version 1.",
            "Give the index a name, so it is never mistaken for the readiness score.",
            'Missing values can only earn no credit here ("no_credit"), not "mean".',
            "The share of criteria a site needs before it is ranked must be above 0 and at most "
            "1, not 1.5.",
            "The number of draws must be a whole number from 0 to 20000, not -1.",
            "The weight spread must be from 0 to 1, not 3.",
            'The seed must be a whole number of 0 or more, not "x".',
        ]

    def test_every_refusal_is_a_sentence_without_internal_names(self):
        specs = [
            _spec([]), dict(CLEAN_SPEC, pack=None), _spec([{"column": ""}, {"weight": 1}]),
            _spec([_criterion("heat_risk_0_100", "sideways", 1, kind="linear"),
                   _criterion("solar_kw", "higher_better", 1, kind="spline")]),
        ]
        for spec in specs:
            for message in self._messages(spec):
                assert message.endswith("."), message
                first = message.split()[0]
                assert first[0].isupper() or first in ("heat_risk_0_100", "solar_kw"), message
                for jargon in ("evsient:", "KeyError", "Traceback", "NoneType", "\u2014"):
                    assert jargon not in message

    def test_a_valid_spec_comes_back_normalised(self):
        out = index.validate(CLEAN_SPEC, ENTRIES["clean"])
        assert out["ok"] and out["refusals"] == []
        spec = out["spec"]
        assert spec["missing"] == "no_credit" and spec["minCoverage"] == 0.65
        assert spec["robustness"] == {"draws": 400, "spread": 0.25, "seed": 1,
                                      "ordinalSpread": 0.2}
        assert abs(math.fsum(c["weight"] for c in spec["criteria"]) - 1) < 1e-12


# ---------- strict JSON, the bridge and the comparison ----------

class TestBridge:
    def test_bridge_run_is_strict_json_and_never_official(self):
        table = _with_blanks(_table("index_adversarial.csv"), "tiny", 5)
        text = index.bridge_run(json.dumps(table), json.dumps(ENTRIES["adversarial"]),
                                json.dumps(ADVERSARIAL_SPEC),
                                json.dumps({"populationColumn": "population"}))
        out = _strict(text)
        assert out["official"] is False and out["name"] == "Test index"
        assert out["badge"] == "Not an official EV-SIENT score"
        assert out["sites"][0]["name"].startswith("Adversarial Site")
        assert "NaN" not in text and "Infinity" not in text

    def test_refusals_are_strict_json_too(self):
        spec = dict(ADVERSARIAL_SPEC, criteria=ADVERSARIAL_SPEC["criteria"][:1])
        out = _strict(index.bridge_run(json.dumps(_table("index_adversarial.csv")),
                                       json.dumps(ENTRIES["adversarial"]), json.dumps(spec)))
        assert out["refused"] and out["official"] is False

    def test_repeated_or_blank_site_ids_are_refused(self):
        table = _table("index_clean.csv")
        table["rows"][5][0] = table["rows"][4][0]
        out = _strict(index.bridge_run(json.dumps(table), json.dumps(ENTRIES["clean"]),
                                       json.dumps(CLEAN_SPEC)))
        assert out["refusals"][0]["message"] == ("Two sites share the id C005. Give every site "
                                                 "its own id.")
        table["rows"][5][0] = " "
        out = _strict(index.bridge_run(json.dumps(table), json.dumps(ENTRIES["clean"]),
                                       json.dumps(CLEAN_SPEC)))
        assert out["refusals"][0]["message"] == "Some sites have no id. Give every site its own id."

    def test_bridge_validate_reads_a_table_schema_too(self):
        schema = {"fields": ENTRIES["clean"]}
        out = _strict(index.bridge_validate(json.dumps(CLEAN_SPEC), json.dumps(schema)))
        assert out["ok"]

    def test_unreadable_json_is_refused_in_words(self):
        with pytest.raises(ValueError, match="The index settings could not be read."):
            index.bridge_validate("{nope", "[]")

    def test_the_comparison_with_the_readiness_score(self, clean):
        ids = [s["siteId"] for s in clean["sites"]]
        same = {s["siteId"]: s["score"] / 2 for s in clean["sites"]}
        out = index.comparison(clean, same)
        assert out["official"] is False and out["spearman"] == pytest.approx(1.0)
        assert all(r["shift"] == 0 for r in out["sites"])
        reversed_ = {sid: float(i) for i, sid in enumerate(ids)}
        reversed_["NOT-IN-INDEX"] = 50.0
        out = index.comparison(clean, reversed_)
        assert out["spearman"] < -0.99
        assert out["notInIndex"] == ["NOT-IN-INDEX"]
        top = out["disagreements"][0]
        assert abs(top["shift"]) == max(abs(r["shift"]) for r in out["sites"])
        assert len(out["disagreements"]) == 10

    def test_bridge_adds_the_comparison_when_given_readiness_scores(self):
        table = _table("index_clean.csv")
        readiness = {r[0]: float(i % 17) for i, r in enumerate(table["rows"])}
        out = _strict(index.bridge_run(json.dumps(table), json.dumps(ENTRIES["clean"]),
                                       json.dumps(CLEAN_SPEC),
                                       json.dumps({"readinessScores": readiness})))
        assert out["comparison"]["n"] == 60 and out["comparison"]["official"] is False

    def test_read_typed(self):
        raw = pd.DataFrame({"n": ["1.5", " 2 ", "n/a", "abc", "inf"],
                            "r": ["low", "MODERATE", "Unknown", "High", "Severe"],
                            "f": ["Yes", "no", "TBD", "1", "maybe"]},
                           index=list("abcde"), dtype=object)
        entries = [{"name": "n", "evsient:role": "measure"},
                   {"name": "r", "evsient:role": "ordinal",
                    "categories": ["Low", "Moderate", "High"]},
                   {"name": "f", "evsient:role": "flag"}]
        typed = index.read_typed(raw, entries)
        assert typed["n"].tolist()[:2] == [1.5, 2.0]
        assert typed["n"].isna().tolist() == [False, False, True, True, True]
        assert typed["r"].tolist() == ["Low", "Moderate", None, "High", None]
        assert typed["f"].tolist()[:2] == [1.0, 0.0] and typed["f"].tolist()[3] == 1.0
        assert typed["f"].isna().tolist() == [False, False, True, False, True]
