"""Explore must not report patterns that are not there, and must find the ones that are.

The property under test
-----------------------
An automatic scan runs hundreds of comparisons, so some will look striking by luck. The eight
rules in docs/FLEXIBLE_ANALYSIS.md, section 2 exist to stop those reaching a card. Most of this
file plants known effects in synthetic sites, surrounds them with columns of pure noise, and
checks that the scan finds the planted ones with the right sign and interval while the noise
stays quiet at the panel's stated false discovery rate.

The null bound, and why it is what it is
----------------------------------------
When every pattern in a file is noise, Benjamini-Hochberg at q = 0.10 keeps the chance that
*anything at all* passes at or below 0.10 (for independent or positively dependent tests).
Over 20 independent null files the number with any pass is then at most Binomial(20, 0.10),
which exceeds 4 with probability 4.3%. The test allows at most 4 of 20, so a correct scan
passes it with at least 95% confidence over the choice of seeds, and a scan that forgot the
correction (dozens of raw p < 0.05 per file) fails it every time. The seeds are fixed, so the
test itself is deterministic.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2.flex import explore  # noqa: E402

NULL_SEEDS = range(1, 21)
NULL_MAX_FILES_WITH_A_PASS = 4

COUNTRIES = ["Aland", "Borduria", "Carpania", "Dornia", "Elbonia", "Freedonia"]


# ---------------------------------------------------------------- fixtures

def _entry(name: str, role: str, **extra) -> dict:
    return {"name": name, "evsient:role": role, "evsient:direction": None,
            "evsient:provenance": "inferred", **extra}


def _ordinal_text(values: np.ndarray, labels: list[str]) -> list[str]:
    """Cut a number into len(labels) equal-count levels, as text."""
    edges = np.quantile(values, np.linspace(0, 1, len(labels) + 1)[1:-1])
    return [labels[int(np.searchsorted(edges, v))] for v in values]


def planted(seed: int = 1, n: int = 360, nulls: int = 8) -> tuple[pd.DataFrame, list[dict]]:
    """Sites with known effects among columns of noise. Returns the raw text table and entries.

    Planted: heat ~ visits rho about +0.58; heat ~ cost about -0.48; heat ~ flood (ordinal)
    positive; status shifts footfall; after_dark shifts shade; the 20-site 'Pilot' group of
    'tier' shifts volunteers (and a 5-site 'Rare' group, which must stay hidden, shifts it a
    lot); flood is "Unknown" for half of Aland and almost nowhere else; population is
    computed from visits.
    """
    rng = np.random.default_rng(seed)
    heat = rng.normal(size=n)
    visits = 0.6 * heat + 0.8 * rng.normal(size=n)
    cost = -0.5 * heat + math.sqrt(0.75) * rng.normal(size=n)
    flood = _ordinal_text(heat + 0.8 * rng.normal(size=n), ["Low", "Moderate", "High"])
    country = np.array(COUNTRIES)[np.arange(n) * len(COUNTRIES) // n]
    unknown = np.where(country == "Aland", rng.random(n) < 0.5, rng.random(n) < 0.03)
    flood = ["Unknown" if u else f for f, u in zip(flood, unknown)]
    status = np.array(["Scoping", "Funded", "Open"])[np.arange(n) % 3]
    footfall = np.exp(rng.normal(size=n) + np.where(status == "Open", 1.0, 0.0)) * 100
    after_dark = rng.random(n) < 0.5
    shade = rng.normal(size=n) + 0.9 * after_dark
    tier = np.array(["Standard"] * n, dtype=object)
    chosen = rng.permutation(n)
    tier[chosen[:20]] = "Pilot"
    tier[chosen[20:25]] = "Rare"
    volunteers = rng.normal(size=n) + 1.6 * (tier == "Pilot") + 8.0 * (tier == "Rare")
    population = 2.0 * visits + 1.0

    cols = {
        "site_id": [f"S{i:04d}" for i in range(n)],
        "country": country,
        "heat_risk_0_100": np.round(50 + 15 * heat, 3),
        "expected_visits": np.round(500 + 100 * visits, 3),
        "upgrade_cost_usd": np.round(4e5 + 1e5 * cost, 2),
        "flood_risk": flood,
        "project_status": status,
        "footfall": np.round(footfall, 3),
        "open_after_dark": np.where(after_dark, "Yes", "No"),
        "shade_area_m2": np.round(500 + 100 * shade, 3),
        "tier": tier,
        "volunteers": np.round(30 + 5 * volunteers, 3),
        "service_population": np.round(1000 + 200 * population, 3),
    }
    entries = [
        _entry("site_id", "identifier"), _entry("country", "category"),
        _entry("heat_risk_0_100", "score", **{"evsient:range": [0, 100]}),
        _entry("expected_visits", "count"), _entry("upgrade_cost_usd", "money", **{"evsient:unit": "USD"}),
        _entry("flood_risk", "ordinal", categories=["Low", "Moderate", "High"], categoriesOrdered=True,
               missingValues=["Unknown"]),
        _entry("project_status", "category"), _entry("footfall", "count"),
        _entry("open_after_dark", "flag"), _entry("shade_area_m2", "measure", **{"evsient:unit": "m2"}),
        _entry("tier", "category"), _entry("volunteers", "count"),
        _entry("service_population", "count"),
    ]
    for i in range(nulls):
        cols[f"noise_{i}"] = np.round(rng.normal(size=n), 4)
        entries.append(_entry(f"noise_{i}", "measure"))
    cols["noise_group"] = np.array(["Alpha", "Beta", "Gamma", "Delta"])[rng.integers(0, 4, n)]
    entries.append(_entry("noise_group", "category"))
    cols["noise_level"] = _ordinal_text(rng.normal(size=n), ["1", "2", "3", "4", "5"])
    entries.append(_entry("noise_level", "ordinal", categories=["1", "2", "3", "4", "5"],
                          categoriesOrdered=True))
    raw = pd.DataFrame({k: [str(v) for v in vals] for k, vals in cols.items()}, dtype=object)
    return raw, entries


#: Columns of `planted` whose relationships are noise, so any card joining two of them, or one
#: of them with a planted column, is a false discovery.
def _is_noise(name: str) -> bool:
    return name.startswith("noise_")


def null_table(seed: int, n: int = 360, numbers: int = 24) -> tuple[pd.DataFrame, list[dict]]:
    """Every column independent of every other: whatever passes is a false discovery."""
    rng = np.random.default_rng(10_000 + seed)
    cols: dict[str, list] = {"site_id": [f"N{i:04d}" for i in range(n)]}
    entries = [_entry("site_id", "identifier")]
    cols["country"] = list(np.array(COUNTRIES)[rng.integers(0, len(COUNTRIES), n)])
    entries.append(_entry("country", "category"))
    for i in range(numbers):
        v = np.exp(rng.normal(size=n)) if i % 3 == 0 else rng.normal(size=n)
        text = [f"{x:.4f}" for x in v]
        if i % 4 == 0:  # missing completely at random, so missingness checks run too
            text = ["Unknown" if rng.random() < 0.08 else t for t in text]
        cols[f"n{i}"] = text
        entries.append(_entry(f"n{i}", "measure"))
    for i, k in enumerate((3, 4, 6)):
        cols[f"c{i}"] = list(np.array([f"G{j}" for j in range(k)])[rng.integers(0, k, n)])
        entries.append(_entry(f"c{i}", "category"))
    for i in range(2):
        cols[f"o{i}"] = _ordinal_text(rng.normal(size=n), ["Low", "Moderate", "High"])
        cols[f"o{i}"] = ["Unknown" if rng.random() < 0.1 else t for t in cols[f"o{i}"]]
        entries.append(_entry(f"o{i}", "ordinal", categories=["Low", "Moderate", "High"],
                              categoriesOrdered=True))
    cols["f0"] = list(np.where(rng.random(n) < 0.4, "Yes", "No"))
    entries.append(_entry("f0", "flag"))
    raw = pd.DataFrame(cols, dtype=object)
    return raw, entries


def simpson(seed: int = 3, per: int = 60) -> tuple[pd.DataFrame, list[dict]]:
    """Within each country more x means less y; between countries both rise together."""
    rng = np.random.default_rng(seed)
    rows = []
    for c, name in enumerate(COUNTRIES[:4]):
        x = 3.0 * c + rng.normal(size=per)
        y = 4.0 * c - 0.8 * (x - 3.0 * c) + 0.5 * rng.normal(size=per)
        rows += [(f"{name[:2]}{i}", name, f"{a:.4f}", f"{b:.4f}") for i, (a, b) in enumerate(zip(x, y))]
    raw = pd.DataFrame(rows, columns=["site_id", "country", "shade_m2", "heat_index"], dtype=object)
    entries = [_entry("site_id", "identifier"), _entry("country", "category"),
               _entry("shade_m2", "measure"), _entry("heat_index", "score")]
    return raw, entries


def _scan(raw, entries, **kw):
    kw.setdefault("neighbours", 0)
    return explore.scan(explore.type_table(raw, entries), entries, **kw)


@pytest.fixture(scope="module")
def planted_result():
    raw, entries = planted()
    return _scan(raw, entries, neighbours=5)


def _card(result: dict, card_id: str) -> dict:
    found = [c for c in result["cards"] if c["id"] == card_id]
    assert found, f"no card {card_id}; cards: {[c['id'] for c in result['cards']]}"
    return found[0]


# ---------------------------------------------------------------- the distribution tails

@pytest.mark.parametrize("t, df, p", [(2.228138851986274, 10, 0.05), (2.7764451051977987, 4, 0.05),
                                      (2.0, 10, 0.07338803477074436), (12.706204736174698, 1, 0.05)])
def test_student_t_tail_matches_published_critical_values(t, df, p):
    assert explore._t_two_sided(t, df) == pytest.approx(p, rel=1e-6)


@pytest.mark.parametrize("x, df, p", [(3.841458820694124, 1, 0.05), (18.307038053275146, 10, 0.05),
                                      (5.991464547107979, 2, 0.05), (0.5, 3, 0.9188914369036184),
                                      (100.0, 4, 1.1252025565421357e-20)])
def test_chi_square_tail_matches_published_critical_values(x, df, p):
    assert explore._chi2_sf(x, df) == pytest.approx(p, rel=1e-6)


def test_ranks_average_ties():
    assert explore._ranks(np.array([10.0, 20.0, 20.0, 5.0])).tolist() == [2.0, 3.5, 3.5, 1.0]


def test_bootstrap_ranks_reproduce_ranks_when_every_site_is_drawn_once():
    x = np.array([3.0, 1.0, 2.0, 2.0, 5.0])
    ranks = explore._boot_ranks(np.ones((1, 5)), explore._ties(x))[0]
    assert ranks.tolist() == explore._ranks(x).tolist()


def test_benjamini_hochberg_matches_hand_computation():
    q = explore._bh([0.01, 0.04, 0.03, 0.20])
    assert q == pytest.approx([0.04, 0.04 * 4 / 3, 0.04 * 4 / 3, 0.20])


def test_cliffs_delta_from_rank_sums_counts_pairs():
    y = np.array([5.0, 6.0, 7.0, 1.0, 2.0, 6.0])
    g = np.array([0, 0, 0, 1, 1, 1])
    # pairs (group 0 vs 1): 5>1,5>2,5<6, 6>1,6>2,6=6, 7>1,7>2,7>6 -> 7 greater, 1 less
    assert explore._cliffs_delta(y, g) == pytest.approx((7 - 1) / 9)


# ---------------------------------------------------------------- rule 1 and 2: counting

def test_every_test_is_counted_and_corrected_across_the_whole_scan(planted_result):
    r = planted_result
    assert r["checked"] == len(r["tests"])
    assert r["passed"] == sum(t["passed"] for t in r["tests"])
    pooled = [c for c in r["cards"] if c["kind"] != "within"]
    assert len(pooled) == r["passed"]
    q = explore._bh([t["p"] for t in r["tests"]])
    assert [round(x, 3) for x in q] == pytest.approx([round(t["q"], 3) for t in r["tests"]], abs=2e-3)
    for card in pooled:
        assert card["q"] <= r["fdr"]
        assert card["footer"].endswith(f"of {r['checked']} checked.")


def test_pure_noise_does_not_pass_at_the_stated_false_discovery_rate():
    """See the module docstring for the bound: at most 4 of 20 null files with any pass."""
    with_a_pass, false_cards, raw_hits, checked = 0, 0, 0, []
    for seed in NULL_SEEDS:
        raw, entries = null_table(seed)
        r = _scan(raw, entries, bootstrap=200)
        checked.append(r["checked"])
        false_cards += r["passed"]
        with_a_pass += r["passed"] > 0
        raw_hits += sum(t["p"] < 0.05 for t in r["tests"])
    assert min(checked) > 300, "the null files must give the correction something to do"
    assert raw_hits > 10 * len(NULL_SEEDS), "uncorrected, noise would pass by the dozen"
    assert with_a_pass <= NULL_MAX_FILES_WITH_A_PASS, (with_a_pass, false_cards)


def test_noise_columns_stay_quiet_beside_planted_effects():
    """Across seeds, the share of shown cards that involve a noise column stays under q."""
    shown = false = 0
    for seed in range(1, 11):
        raw, entries = planted(seed=seed, nulls=12)
        r = _scan(raw, entries, bootstrap=200)
        for card in r["cards"]:
            if card["kind"] == "within":
                continue
            shown += 1
            false += any(_is_noise(c) for c in card["columns"])
    assert shown > 50
    assert false / shown <= explore.FDR, (false, shown)


# ---------------------------------------------------------------- rule 3: effect sizes

def test_planted_associations_are_found_with_sign_and_interval(planted_result):
    r = planted_result
    up = _card(r, "assoc:heat_risk_0_100:expected_visits")
    true_up = 6 / math.pi * math.asin(0.6 / 2)  # Spearman's rho for a normal pair with r = 0.6
    assert up["effect"]["name"] == "spearman_rho"
    assert 0 < up["effect"]["low"] < true_up < up["effect"]["high"]
    assert up["sentence"] == "Sites with higher Heat Risk tend to have higher Expected Visits."
    down = _card(r, "assoc:heat_risk_0_100:upgrade_cost_usd")
    true_down = 6 / math.pi * math.asin(-0.5 / 2)
    assert down["effect"]["low"] < true_down < down["effect"]["high"] < 0
    assert down["sentence"] == "Sites with higher Heat Risk tend to have lower Upgrade Cost."


def test_planted_group_differences_are_found(planted_result):
    r = planted_result
    status = _card(r, "group:project_status:footfall")
    assert status["effect"]["name"] == "epsilon_squared" and status["effect"]["low"] > 0
    assert "where it is Open" in status["sentence"]
    dark = _card(r, "group:open_after_dark:shade_area_m2")
    assert dark["effect"]["name"] == "cliffs_delta"
    assert dark["effect"]["value"] > 0 and dark["effect"]["low"] > 0
    assert dark["sentence"].startswith("Sites where Open After Dark is Yes tend to have higher Shade Area")


def test_cards_are_ranked_by_effect_size_not_p_value(planted_result):
    pooled = [c for c in planted_result["cards"] if c["kind"] != "within"]
    strength = [explore._strength(c["effect"]["name"], c["effect"]["value"]) for c in pooled]
    assert strength == sorted(strength, reverse=True)
    for c in pooled:
        assert c["effect"]["low"] <= c["effect"]["value"] <= c["effect"]["high"]


# ---------------------------------------------------------------- rule 4: small groups

def test_groups_under_ten_are_hidden_and_under_thirty_marked(planted_result):
    r = planted_result
    card = _card(r, "group:tier:volunteers")
    assert "Rare" not in card["sentence"] and "Pilot" in card["sentence"]
    assert card["hiddenGroups"] == 1
    assert card["reliability"] == "few sites"
    assert all("Rare" not in c["sentence"] for c in r["cards"])
    tier = next(s for s in r["summaries"] if s["column"] == "tier")
    hidden = {c["level"]: c["hidden"] for c in tier["counts"]}
    assert hidden == {"Standard": False, "Pilot": False, "Rare": True}


def test_a_category_with_no_two_groups_of_ten_is_not_tested():
    raw, entries = planted()
    raw["tiny"] = [f"T{i % 40}" for i in range(len(raw))]
    entries = entries + [_entry("tiny", "category")]
    r = _scan(raw, entries)
    assert not any("tiny" in t["columns"] for t in r["tests"] if t["kind"] != "missingness")
    assert any(s["column"] == "tiny" for s in r["skipped"])


# ---------------------------------------------------------------- rule 5: wording

BANNED = re.compile(r"\b(" + "|".join(re.escape(w) for w in explore.BANNED_WORDS) + r")\b", re.I)


def test_templates_contain_no_causal_words():
    for name, template in explore.TEMPLATES.items():
        assert not BANNED.search(template), name
        assert chr(0x2014) not in template, name  # no em dashes in repo text


def test_every_card_sentence_comes_from_a_template(planted_result):
    patterns = [re.compile("^" + re.sub(r"\\\{[a-z0-9]+\\\}", ".+", re.escape(t)) + "$")
                for t in explore.TEMPLATES.values()]
    for card in planted_result["cards"]:
        assert any(p.match(card["sentence"]) for p in patterns), card["sentence"]
        assert not BANNED.search(card["sentence"]), card["sentence"]
        assert card["footer"].startswith("Association, not cause.")
    for s in planted_result["suppressed"]:
        assert not BANNED.search(s["note"])


# ---------------------------------------------------------------- rule 6: ordinal as ordinal

def test_ordinal_columns_are_ranked_and_reported_as_levels(planted_result):
    r = planted_result
    flood = next(s for s in r["summaries"] if s["column"] == "flood_risk")
    assert [lv["level"] for lv in flood["levels"]] == ["Low", "Moderate", "High"]
    assert flood["median"] in ("Low", "Moderate", "High")
    assert "mean" not in flood
    card = _card(r, "assoc:heat_risk_0_100:flood_risk")
    assert card["effect"]["name"] == "spearman_rho" and card["effect"]["low"] > 0
    assert card["chart"]["type"] == "box" and card["chart"]["x"] == "flood_risk"


def test_ordinal_medians_by_group_are_level_names():
    raw, entries = planted()
    raw["flood_risk"] = np.where(raw["project_status"] == "Open", "High",
                                 np.where(raw["project_status"] == "Funded", "Moderate", "Low"))
    every_third = np.arange((len(raw) + 2) // 3)
    raw.loc[raw.index % 3 == 0, "flood_risk"] = np.where(every_third % 2 == 0, "Low", "Moderate")
    r = _scan(raw, entries)
    card = _card(r, "group:project_status:flood_risk")
    assert re.search(r"the median is '(Low|Moderate|High)'", card["sentence"]), card["sentence"]


def test_the_order_of_levels_comes_from_the_dictionary_not_the_alphabet():
    raw, entries = planted()
    typed = explore.type_table(raw, entries)
    present = typed["flood_risk"].dropna()
    assert set(present.unique()) == {0.0, 1.0, 2.0}
    heat = typed.loc[present.index, "heat_risk_0_100"]
    assert heat[present == 2.0].median() > heat[present == 0.0].median()  # High above Low


# ---------------------------------------------------------------- rule 7: Unknown is missing

def test_unknown_is_missing_and_missingness_by_group_is_checked(planted_result):
    r = planted_result
    flood = next(s for s in r["summaries"] if s["column"] == "flood_risk")
    assert "Unknown" not in [lv["level"] for lv in flood["levels"]]
    assert flood["missing"] > 0
    card = _card(r, "missing:flood_risk:country")
    assert card["kind"] == "missingness"
    assert "where it is Aland" in card["sentence"]
    assert len(card["siteIds"]) == flood["missing"]


def test_unknown_text_in_a_typed_category_is_missing_not_a_group():
    typed = pd.DataFrame({"g": ["A"] * 15 + ["Unknown"] * 15 + ["B"] * 15, "v": np.arange(45.0)})
    entries = [_entry("g", "category"), _entry("v", "measure")]
    r = explore.scan(typed, entries, neighbours=0)
    g = next(s for s in r["summaries"] if s["column"] == "g")
    assert [c["level"] for c in g["counts"]] == ["A", "B"] and g["missing"] == 15


# ---------------------------------------------------------------- rule 8: construction, Simpson

def test_pairs_related_by_construction_are_suppressed_and_not_tested(planted_result):
    r = planted_result
    sup = [s for s in r["suppressed"] if set(s["columns"]) == {"expected_visits", "service_population"}]
    assert sup and abs(sup[0]["value"]) > explore.CONSTRUCTION_RHO
    assert not any("service_population" in t["columns"] for t in r["tests"] if t["kind"] != "missingness")
    assert all("service_population" not in c["columns"] for c in r["cards"])


def test_a_pooled_result_that_reverses_within_countries_shows_the_within_view():
    raw, entries = simpson()
    r = _scan(raw, entries)
    pooled = _card(r, "assoc:shade_m2:heat_index")
    assert pooled["effect"]["value"] > 0 and pooled["within"]["verdict"] == "reverses"
    within = _card(r, "within:country:assoc:shade_m2:heat_index")
    assert within["stratum"]["verdict"] == "reverses" and within["stratum"]["groups"] == 4
    assert within["effect"]["high"] < 0
    assert within["sentence"].startswith("Within each Country, the pattern reverses:")
    ids = [c["id"] for c in r["cards"]]
    assert ids.index(within["id"]) == ids.index(pooled["id"]) + 1


def test_a_result_that_holds_within_countries_gets_no_companion(planted_result):
    up = _card(planted_result, "assoc:heat_risk_0_100:expected_visits")
    assert up["within"]["verdict"] == "holds"
    assert not any(c["id"] == "within:country:" + up["id"] for c in planted_result["cards"])


def test_nested_or_identical_groupings_are_not_tested_against_each_other():
    raw, entries = planted()
    raw["region"] = raw["country"].map({c: f"R{i // 2}" for i, c in enumerate(COUNTRIES)})
    raw["country_code"] = raw["country"].str[:3].str.upper()
    entries = entries + [_entry("region", "category"), _entry("country_code", "category")]
    r = _scan(raw, entries)
    kinds = {tuple(s["columns"]): s["measure"] for s in r["suppressed"]}
    assert kinds[("country", "region")] == "nested"
    assert kinds[("country", "country_code")] == "same"
    assert not any("country_code" in t["columns"] for t in r["tests"])


# ---------------------------------------------------------------- Pareto and similar sites

def test_pareto_set_uses_only_confirmed_directions():
    typed = pd.DataFrame({"id": ["a", "b", "c", "d"], "x": [1.0, 2.0, 3.0, 2.0], "y": [3.0, 2.0, 1.0, 1.0]})
    entries = [_entry("id", "identifier"), _entry("x", "measure"), _entry("y", "measure")]
    assert explore.scan(typed, entries, min_group=2, neighbours=0)["pareto"]["columns"] == []
    for e in entries[1:]:
        e.update({"evsient:direction": "higher_better", "evsient:provenance": "confirmed_by_user"})
    pareto = explore.scan(typed, entries, min_group=2, neighbours=0)["pareto"]
    assert pareto["front"] == ["a", "b", "c"]
    assert pareto["dominatedBy"] == {"d": "b"}


def test_similar_sites_name_the_columns_that_make_them_alike(planted_result):
    sim = planted_result["similar"]
    assert sim["k"] == 5 and len(sim["sites"]) == 360
    first = sim["sites"][0]["like"]
    assert len(first) == 5 and all(set(x["closeOn"]) <= set(sim["columns"]) for x in first)
    assert [x["distance"] for x in first] == sorted(x["distance"] for x in first)
    typed = pd.DataFrame({"id": ["a", "b", "c", "d"], "x": [1.0, 1.0, 9.0, 7.0], "g": ["p", "p", "q", "q"]})
    entries = [_entry("id", "identifier"), _entry("x", "measure"), _entry("g", "category")]
    r = explore.scan(typed, entries, min_group=1, neighbours=1)
    assert r["similar"]["sites"][0]["like"][0] == {"site": "b", "distance": 0.0, "closeOn": ["x", "g"],
                                                   "differsOn": []}


# ---------------------------------------------------------------- summaries

def test_heavy_tailed_money_gets_a_log_scale_suggestion(planted_result):
    footfall = next(s for s in planted_result["summaries"] if s["column"] == "footfall")
    assert footfall["logSuggested"] is True and footfall["skew"] > 1
    heat = next(s for s in planted_result["summaries"] if s["column"] == "heat_risk_0_100")
    assert heat["logSuggested"] is False  # a bounded score is never logged
    assert heat["outOfRange"] >= 0


def test_dates_are_judged_against_the_given_date_not_the_clock():
    typed = pd.DataFrame({"d": ["2020-01-01", "2026-01-01", "2024-06-30", None]})
    entries = [_entry("d", "date")]
    s = explore.scan(typed, entries, neighbours=0, as_of="2026-10-18")["summaries"][0]
    assert (s["stale"], s["missing"], s["asOf"]) == (1, 1, "2026-10-18")
    s = explore.scan(typed, entries, neighbours=0)["summaries"][0]
    assert s["asOf"] == "2026-01-01" and s["asOfFrom"] == "latest date in the column"


# ---------------------------------------------------------------- output contract

def _strict(text: str):
    def bad(token):
        raise ValueError(f"non-strict JSON constant {token}")
    return json.loads(text, parse_constant=bad)


def test_bridge_returns_strict_json_in_the_contract_shape():
    raw, entries = planted(n=120, nulls=2)
    raw.loc[3, "footfall"] = "inf"
    table = {"columns": list(raw.columns), "rows": raw.values.tolist()}
    out = _strict(explore.bridge_scan(json.dumps(table), json.dumps({"fields": entries}),
                                      json.dumps({"neighbours": 2, "bootstrap": 200})))
    assert {"checked", "passed", "fdr", "minGroup", "health", "cards"} <= set(out)
    assert out["fdr"] == 0.10 and out["minGroup"] == 10
    assert set(out["health"]) >= {"rows", "columns", "described", "unknown"}
    card_keys = {"id", "kind", "columns", "sentence", "effect", "n", "q", "reliability", "stratum",
                 "chart", "siteIds", "footer"}
    for card in out["cards"]:
        assert card_keys <= set(card)
        assert set(card["effect"]) == {"name", "value", "low", "high"}


def test_the_same_input_gives_the_same_json():
    raw, entries = planted(n=180, nulls=2)
    table = json.dumps({"columns": list(raw.columns), "rows": raw.values.tolist()})
    a = explore.bridge_scan(table, json.dumps(entries), '{"seed": 7, "neighbours": 3}')
    b = explore.bridge_scan(table, json.dumps(entries), '{"seed": 7, "neighbours": 3}')
    assert a == b


def test_typed_tables_pass_through_the_bridge_unchanged():
    raw, entries = planted(n=120, nulls=1)
    typed = explore.type_table(raw, entries)
    rows = [[None if (isinstance(v, float) and math.isnan(v)) else v for v in row]
            for row in typed.astype(object).values.tolist()]
    via_typed = explore.bridge_scan(json.dumps({"columns": list(typed.columns), "rows": rows, "typed": True}),
                                    json.dumps(entries), '{"neighbours": 0}')
    via_raw = explore.bridge_scan(json.dumps({"columns": list(raw.columns), "rows": raw.values.tolist()}),
                                  json.dumps(entries), '{"neighbours": 0}')
    assert via_typed == via_raw


def test_the_default_scan_never_imports_scipy_or_sklearn():
    code = ("import sys; sys.modules['scipy'] = None; sys.modules['sklearn'] = None\n"
            f"sys.path[:0] = [{str(REPO / 'src')!r}, {str(REPO / 'tests')!r}]\n"
            "import test_flex_explore as t\n"
            "raw, entries = t.planted(n=120, nulls=1)\n"
            "r = t._scan(raw, entries, bootstrap=100)\n"
            "assert r['checked'] > 0\n"
            "print('ok', [m for m in sys.modules if m.startswith(('scipy', 'sklearn')) and sys.modules[m]])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok []"
