"""Golden tests: legacy_v2 mode must reproduce the frozen V2 baseline exactly."""

import pandas as pd


def test_scores_match_frozen_baseline(scored_legacy, golden_site_results):
    mine = scored_legacy.set_index("site_id")
    gold = golden_site_results.set_index("site_id")
    for col in ["readiness_score", "demand_subscore", "feasibility_subscore",
                "safety_subscore", "equity_subscore", "expected_sessions_day"]:
        assert (mine[col].round(6) - gold[col].round(6)).abs().max() < 1e-9, col


def test_ranks_and_ports_match(scored_legacy, golden_site_results):
    mine = scored_legacy.set_index("site_id")
    gold = golden_site_results.set_index("site_id")
    assert (mine["model_rank"] == gold["model_rank"]).all()
    assert (mine["recommended_ports_now"] == gold["recommended_ports_now"]).all()


def test_right_sizing_matches_frozen_baseline(scored_legacy, golden_right_sizing):
    from fcf_m2.right_sizing import run_right_sizing_legacy
    mine = run_right_sizing_legacy(scored_legacy).set_index("site_id")
    gold = golden_right_sizing.set_index("site_id")
    for col in ["ports_now", "ports_2035_base", "ports_2035_high", "ports_2050_base",
                "ports_2050_high", "future_ready_capacity", "site_capacity_cap",
                "expansion_strategy"]:
        assert (mine[col] == gold[col]).all(), col


def test_headline_totals(scored_legacy, golden_right_sizing):
    from fcf_m2.right_sizing import run_right_sizing_legacy
    rs = run_right_sizing_legacy(scored_legacy)
    assert rs["ports_now"].sum() == 25
    assert rs["future_ready_capacity"].sum() == 48
    top = scored_legacy.sort_values("readiness_score", ascending=False).iloc[0]
    assert top["site_id"] == "FFX002"
    assert abs(top["readiness_score"] - 58.8) < 0.05
