"""The score breakdown and rank-stability checks (src/fcf_m2/stability.py).

Pinned on the fixed-anchor fixture, the reference study's 12 sites: FFX004 first at 53.4 and
FFX002 second at 51.8. The numbers below were worked out independently of the module (by hand
from the subscores and weights) before it was written, and the module is held to them.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import browser_api as api, stability as st  # noqa: E402
from fcf_m2.scoring import SUBSCORE_WEIGHTS  # noqa: E402

FIXTURE = REPO / "tests/fixture_milestone2_v3_site_results.csv"
SYNTHETIC = REPO / "data/synthetic/synthetic_sites_v2.csv"


@pytest.fixture(scope="module")
def results() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, dtype={"site_id": str})


def _case(sens: dict, subscore: str, change: float) -> dict:
    return next(c for c in sens["cases"] if c["subscore"] == subscore and c["change"] == change)


# ---------- breakdown ----------

@pytest.mark.real_inputs
def test_shown_contributions_add_up_exactly_to_the_published_score(results):
    for site in st.breakdown(results):
        target = round(site["score"] * 10)
        assert sum(round(s["shown"] * 10) for s in site["subscores"]) == target, site["siteId"]
        assert sum(round(d["shown"] * 100) for d in site["drivers"]) == target * 10, site["siteId"]
        assert round(site["total"], 1) == site["score"]
        assert sum(s["points"] for s in site["subscores"]) == pytest.approx(site["total"], abs=1e-9)
        assert sum(d["points"] for d in site["drivers"]) == pytest.approx(site["total"], abs=1e-9)


@pytest.mark.real_inputs
def test_the_drivers_reproduce_each_subscore_before_any_rescaling(results):
    """The rescale in breakdown() only absorbs float noise; the recomputed drivers ARE the subscores."""
    df = st._ordered(results)
    terms = st._driver_terms(df)
    for subscore, weight in SUBSCORE_WEIGHTS.items():
        recomputed = sum(t["points"] for t in terms if t["subscore"] == subscore)
        np.testing.assert_allclose(recomputed, weight * df[subscore].to_numpy(), atol=1e-6)


@pytest.mark.real_inputs
def test_a_driver_earning_nothing_is_never_shown_as_earning_something(results):
    for site in st.breakdown(results):
        for d in site["drivers"]:
            if d["points"] == 0:
                assert d["shown"] == 0, (site["siteId"], d["key"])
            assert abs(d["shown"] - d["points"]) < 0.01 + 1e-9


@pytest.mark.real_inputs
def test_the_top_two_break_down_as_published(results):
    by = {s["siteId"]: s for s in st.breakdown(results)}
    assert by["FFX004"]["score"] == 53.4 and by["FFX002"]["score"] == 51.8
    assert [s["shown"] for s in by["FFX004"]["subscores"]] == [25.3, 12.6, 13.5, 2.0]
    assert [s["shown"] for s in by["FFX002"]["subscores"]] == [17.4, 14.3, 13.5, 6.6]
    # Electrical capacity is a placeholder (0 kW) everywhere, so it adds nothing anywhere.
    assert all(d["points"] == 0 for s in by.values() for d in s["drivers"] if d["key"] == "spare_capacity_kw_n")


@pytest.mark.real_inputs
def test_the_access_adjustment_scales_demand_drivers(results):
    pwc003 = next(s for s in st.breakdown(results) if s["siteId"] == "PWC003")
    assert pwc003["accessAdjustment"] == 0.65
    demand_max = sum(d["max"] for d in pwc003["drivers"] if d["subscore"] == "demand")
    assert demand_max == pytest.approx(45 * 0.65)


@pytest.mark.real_inputs
def test_seven_sites_share_one_feasibility_subscore(results):
    """The placeholder capacity leaves feasibility identical wherever the other inputs match."""
    assert int((results["feasibility_subscore"].round(4) == 41.9167).sum()) == 7


# ---------- one weight at a time ----------

@pytest.mark.real_inputs
def test_five_more_points_of_equity_puts_ffx002_first(results):
    case = _case(st.weight_sensitivity(results), "equity", 5.0)
    assert case["top"] == "FFX002" and case["topChanged"]
    assert sum(case["weights"].values()) == pytest.approx(1.0)
    assert case["weights"]["equity"] == pytest.approx(0.15)
    # The others are scaled down in proportion: 45:30:15 is kept.
    assert case["weights"]["demand"] / case["weights"]["feasibility"] == pytest.approx(1.5, rel=1e-4)


@pytest.mark.real_inputs
def test_five_fewer_points_of_demand_leaves_ffx004_first_by_a_tenth(results):
    case = _case(st.weight_sensitivity(results), "demand", -5.0)
    assert case["top"] == "FFX004" and not case["topChanged"]
    assert [(x["siteId"], x["score"]) for x in case["leaders"][:2]] == [("FFX004", 53.1), ("FFX002", 53.0)]


@pytest.mark.real_inputs
def test_every_case_keeps_the_weights_summing_to_one(results):
    sens = st.weight_sensitivity(results)
    assert len(sens["cases"]) == 8
    for c in sens["cases"]:
        assert sum(c["weights"].values()) == pytest.approx(1.0)


@pytest.mark.real_inputs
def test_the_smallest_flip_is_three_points_of_equity(results):
    sens = st.weight_sensitivity(results)
    flip = sens["smallestFlip"]
    assert (flip["subscore"], flip["direction"], flip["newTop"]) == ("equity", "up", "FFX002")
    assert flip["to"] == pytest.approx(12.96, abs=0.01)
    # It really is the threshold: just below it FFX004 leads, just above FFX002 does.
    S = st._subscores(st._ordered(results))
    w = st._weights()
    for at, leader in ((flip["to"] / 100 - 1e-4, 0), (flip["to"] / 100 + 1e-4, 1)):
        assert int(np.argmax(S @ st.reweight(w, 3, at))) == leader
    assert "rises from 10 to about 13.0 points" in sens["sentence"]
    assert "City of Fairfax Regional Library moves to first" in sens["sentence"]


@pytest.mark.real_inputs
def test_a_tie_at_the_end_of_the_range_is_not_a_flip(results):
    """At 100 points of safety every site with safety 90 ties; first place does not change hands."""
    flips = st.weight_sensitivity(results)["flips"]
    assert not any(f["subscore"] == "safety" and f["direction"] == "up" for f in flips)
    assert all(f["newTop"] != "FFX004" for f in flips)


def test_a_site_far_ahead_never_flips():
    df = pd.DataFrame({"site_id": ["A", "B"], "site_name": ["A", "B"], "model_rank": [1, 2],
                       "readiness_score": [90.0, 10.0],
                       "demand_subscore": [90.0, 10.0], "feasibility_subscore": [90.0, 10.0],
                       "safety_subscore": [90.0, 10.0], "equity_subscore": [90.0, 10.0]})
    sens = st.weight_sensitivity(df)
    assert sens["smallestFlip"] is None and sens["flips"] == []
    assert "stays first whatever any one weight is set to" in sens["sentence"]


# ---------- many weightings ----------

@pytest.mark.real_inputs
def test_dirichlet_draws_give_the_known_shares_of_first_place(results):
    stab = st.rank_stability(results)
    by = {s["siteId"]: s for s in stab["sites"]}
    assert by["FFX004"]["pFirst"] == pytest.approx(0.71, abs=0.02)
    assert by["FFX002"]["pFirst"] == pytest.approx(0.19, abs=0.02)
    assert by["PWC002"]["pFirst"] == pytest.approx(0.10, abs=0.02)
    assert sum(s["pFirst"] for s in stab["sites"]) == pytest.approx(1.0)
    assert sum(s["pTop3"] for s in stab["sites"]) == pytest.approx(3.0)
    for s in stab["sites"]:
        assert 1 <= s["rankLow"] <= s["rankMedian"] <= s["rankHigh"] <= len(results)


@pytest.mark.real_inputs
def test_rank_percentiles_are_numpys_inverted_cdf(results):
    """The module reads percentiles from one sort; numpy's own quantile must agree."""
    stab = st.rank_stability(results)
    S = st._subscores(st._ordered(results))
    W = np.random.default_rng(st.DEFAULT_SEED).dirichlet(st.DEFAULT_CONCENTRATION * st._weights(), size=st.DEFAULT_DRAWS)
    scores = W @ S.T
    ranks = np.argsort(np.argsort(-scores, axis=1, kind="stable"), axis=1) + 1
    q = np.quantile(ranks, [0.05, 0.5, 0.95], axis=0, method="inverted_cdf")
    for k, s in enumerate(stab["sites"]):
        assert (s["rankLow"], s["rankMedian"], s["rankHigh"]) == tuple(int(x) for x in q[:, k])
        assert s["pFirst"] == pytest.approx(float(np.mean(ranks[:, k] == 1)))


@pytest.mark.real_inputs
def test_the_same_seed_gives_the_same_answer_and_another_seed_a_close_one(results):
    a = st.rank_stability(results)
    assert a == st.rank_stability(results)
    b = st.rank_stability(results, seed=7)
    for x, y in zip(a["sites"], b["sites"]):
        assert abs(x["pFirst"] - y["pFirst"]) < 0.05


@pytest.mark.real_inputs
def test_drawn_weights_centre_on_the_defaults(results):
    spread = st.rank_stability(results)["weightSpread"]
    for s in spread:
        assert s["low"] < s["weight"] < s["high"]
    demand = next(s for s in spread if s["key"] == "demand")
    assert 0.30 < demand["low"] < 0.38 and 0.52 < demand["high"] < 0.60


def test_six_hundred_sites_run_well_under_a_second():
    rng = np.random.default_rng(1)
    n = 600
    df = pd.DataFrame({"site_id": [f"S{i}" for i in range(n)], "model_rank": range(1, n + 1),
                       **{k: rng.uniform(0, 100, n) for k in SUBSCORE_WEIGHTS}})
    df["readiness_score"] = sum(w * df[k] for k, w in SUBSCORE_WEIGHTS.items()).round(1)
    df = df.sort_values("readiness_score", ascending=False)
    df["model_rank"] = range(1, n + 1)
    started = time.perf_counter()
    st.analyse(df)
    assert time.perf_counter() - started < 1.0


# ---------- inputs not yet confirmed ----------

@pytest.mark.real_inputs
def test_the_confidence_breakdown_is_read_from_the_results(results):
    conf = st.confidence_from_results(results)
    assert conf["FFX004"]["electrical_service"] == 0.0
    assert conf["FFX004"]["address_and_public_access"] == 90.0


@pytest.mark.real_inputs
def test_capacity_alone_could_move_nine_sites_into_first(results):
    unc = st.input_uncertainty(results)
    assert unc["done"]
    cap = next(s for s in unc["scenarios"] if s["key"] == "capacity")
    for site in cap["sites"]:
        assert site["drivers"] == ["spare_capacity_kw_n"]
        # It earns nothing now, so the low end is the score and the high end adds its 10.5 points.
        assert site["high"] - site["low"] == pytest.approx(0.30 * 0.35 * 100)
    assert len(cap["couldBeFirst"]) == 9
    assert "PWC003" not in cap["couldBeFirst"]


@pytest.mark.real_inputs
def test_every_unconfirmed_input_could_reorder_all_twelve(results):
    unc = st.input_uncertainty(results)
    allin = next(s for s in unc["scenarios"] if s["key"] == "unconfirmed")
    assert len(allin["couldBeFirst"]) == 12
    for site in allin["sites"]:
        assert site["low"] <= site["high"]
        assert site["bestRank"] <= site["worstRank"]


@pytest.mark.real_inputs
def test_without_confidence_the_input_check_says_why_it_was_not_done(results):
    bare = results.drop(columns=["data_confidence_reason"])
    unc = st.input_uncertainty(bare)
    assert unc["done"] is False and unc["scenarios"] == []
    assert "do not say how well each group of inputs is sourced" in unc["reason"]


# ---------- the bridge ----------

def _table(path: Path) -> str:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    return json.dumps({"fileName": path.name, "columns": rows[0], "rows": rows[1:]})


def test_the_bridge_answers_after_a_run_and_refuses_before():
    api.reset()
    with pytest.raises(ValueError, match="Run the model first"):
        api.stability("{}")
    api.propose(_table(SYNTHETIC))
    api.accept(json.dumps({"sourceDate": "2026-10-01"}))
    run = json.loads(api.run(json.dumps({"asOf": "2026-10-18"})))
    out = json.loads(api.stability("{}"))
    assert [s["siteId"] for s in out["sites"]] == [s["siteId"] for s in run["sites"]]
    assert [s["score"] for s in out["sites"]] == [s["score"] for s in run["sites"]]
    assert out["inputUncertainty"]["done"] is True
    assert out["rankStability"]["draws"] == st.DEFAULT_DRAWS
    for site in out["sites"]:
        explained = json.loads(api.explain(site["siteId"]))
        mine = {d["key"]: d["points"] for d in site["drivers"]}
        for d in explained["drivers"]:
            assert mine[d["key"]] == pytest.approx(d["points"], abs=1e-3)
    with pytest.raises(ValueError, match="between 1 and 20,000"):
        api.stability(json.dumps({"draws": 0}))
    api.reset()


def test_the_method_is_documented_as_planning_support_not_a_probability():
    text = (REPO / "docs/methodology/rank_stability.md").read_text()
    assert "not a probability that a site is actually" in text
    assert str(st.DEFAULT_DRAWS) in text.replace(",", "") and str(st.DEFAULT_SEED) in text
    assert "\u2014" not in text
