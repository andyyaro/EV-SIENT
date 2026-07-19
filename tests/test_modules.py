"""Unit tests: demand calibration guard, peak/discrete-event sim, confidence,
economics, emissions, triggers."""

import numpy as np
import pandas as pd
import pytest

from fcf_m2 import demand, economics, emissions, peak_wait, triggers
from fcf_m2.confidence import build_confidence, validate_provenance


class TestDemand:
    def test_default_status_uncalibrated(self):
        rec = demand.current_model_record()
        assert rec.status == "synthetic_uncalibrated"
        assert "synthetic" in rec.provenance

    def test_refuses_calibration_with_sparse_data(self, sites):
        obs = pd.DataFrame({
            "site_id": ["FFX002"] * 5, "date": pd.date_range("2026-01-01", periods=5),
            "sessions": [1, 2, 1, 2, 1], "energy_kwh": [9] * 5,
            "mean_dwell_min": [90] * 5, "facility_visitors_day": [300] * 5,
        })
        rec = demand.calibrate(obs, sites)
        assert rec.status == "synthetic_uncalibrated"
        assert rec.calibration_metrics["refused"]

    def test_calibrates_with_sufficient_consistent_data(self, sites):
        rng = np.random.default_rng(1)
        rows = []
        for sid in sites["site_id"]:
            srow = sites[sites["site_id"] == sid].iloc[0]
            # intercept-free ground truth consistent with the model family
            true_rate = max(0.4, 0.002 * float(srow["visitors_day"]) + 0.0005 * float(srow["employees_day"]))
            for d in pd.date_range("2026-01-01", periods=30):
                rows.append({"site_id": sid, "date": d,
                             "sessions": max(0.1, true_rate * (1 + rng.normal(0, 0.05))),
                             "energy_kwh": 9.5, "mean_dwell_min": 90, "facility_visitors_day": srow["visitors_day"]})
        rec = demand.calibrate(pd.DataFrame(rows), sites)
        assert rec.status == "calibrated_observed"
        assert rec.calibration_metrics["holdout_mape"] <= 0.50

    def test_observed_loader_requires_columns(self, tmp_path):
        p = tmp_path / "bad.csv"
        p.write_text("site_id,sessions\nFFX002,1\n")
        with pytest.raises(ValueError):
            demand.load_observed(p)

    def test_presentation_caveat_uncalibrated(self):
        text = demand.presentation_caveat(demand.current_model_record())
        assert "uncalibrated" in text


class TestPeakWait:
    def test_peak_wait_exceeds_daily_average(self):
        pk, _ = peak_wait.peak_window_wait(20, 1.5, 12, ports=3)
        from fcf_m2.queueing import erlang_c
        _, w, _ = erlang_c(20 / 12, 1 / 1.5, 3)
        assert pk >= w * 60 - 1e-9

    def test_simulation_deterministic_under_seed(self):
        a = peak_wait.simulate_waits(8, 1.5, 12, 2, n_days=50, seed=7)
        b = peak_wait.simulate_waits(8, 1.5, 12, 2, n_days=50, seed=7)
        assert a == b

    def test_simulation_percentile_ordering(self):
        r = peak_wait.simulate_waits(15, 1.5, 12, 2, n_days=100)
        assert r.p10_wait_min <= r.p50_wait_min <= r.p90_wait_min

    def test_more_ports_less_wait(self):
        r2 = peak_wait.simulate_waits(15, 1.5, 12, 2, n_days=100)
        r4 = peak_wait.simulate_waits(15, 1.5, 12, 4, n_days=100)
        assert r4.p90_wait_min <= r2.p90_wait_min

    def test_zero_demand_edge(self):
        r = peak_wait.simulate_waits(0.0, 1.5, 12, 2, n_days=20)
        assert r.mean_wait_min == 0.0


class TestConfidence:
    def _prov(self, cls="official_source", unresolved="0"):
        return pd.DataFrame([{
            "site_id": "FFX002", "field_group": "electrical_service", "source_class": cls,
            "verification_status": "spot_checked", "source_org": "x",
            "source_date": "2026-06-24", "reviewer": "t", "assumption_type": "",
            "unresolved_flag": unresolved,
        }])

    def test_note_text_cannot_change_confidence(self):
        """PY-05 acceptance: confidence comes only from typed fields."""
        out1 = build_confidence(self._prov(), ["FFX002"])
        prov2 = self._prov()
        prov2["assumption_type"] = "totally official and confirmed great data"
        out2 = build_confidence(prov2, ["FFX002"])
        assert out1["data_confidence_score_v3"].iloc[0] == out2["data_confidence_score_v3"].iloc[0]

    def test_source_class_drives_score(self):
        hi = build_confidence(self._prov("verified_utility"), ["FFX002"])
        lo = build_confidence(self._prov("unconfirmed", "1"), ["FFX002"])
        assert hi["data_confidence_score_v3"].iloc[0] > lo["data_confidence_score_v3"].iloc[0]

    def test_unknown_source_class_rejected(self):
        bad = self._prov()
        bad["source_class"] = "vibes"
        assert validate_provenance(bad)

    def test_breakdown_present(self):
        out = build_confidence(self._prov(), ["FFX002"])
        assert "electrical_service" in out["confidence_breakdown"].iloc[0]

    def test_missing_group_scores_zero_weighted(self):
        out = build_confidence(self._prov(), ["FFX002"])
        assert out["data_confidence_score_v3"].iloc[0] < 40  # only 1 of 7 groups covered


def _cost_inputs():
    return economics.SiteCostInputs(
        site_id="TST001", ports_now=2, ports_pathway=8,
        staged_targets={2036: 4, 2046: 6, 2056: 8},
        trenching_ft=100, trench_cost_per_ft=150, service_upgrade_cost_usd=20000,
        sessions_day_by_year={y: 2.0 for y in range(2026, 2057)},
    )


class TestEconomics:
    def test_staged_cheaper_than_overbuild_at_every_horizon(self):
        df = economics.compare_cases(_cost_inputs())
        for hy in (2036, 2046, 2056):
            stg = df[(df.horizon_year == hy) & (df.cost_case == "STG")]["lifecycle_cost_npv_usd"].iloc[0]
            ovb = df[(df.horizon_year == hy) & (df.cost_case == "OVB")]["lifecycle_cost_npv_usd"].iloc[0]
            assert stg < ovb

    def test_avoided_cost_positive_and_on_stg_rows_only(self):
        df = economics.compare_cases(_cost_inputs())
        stg = df[df.cost_case == "STG"]
        assert (stg["avoided_overbuild_cost_usd"] > 0).all()
        assert (df[df.cost_case != "STG"]["avoided_overbuild_cost_usd"] == 0).all()

    def test_defer_is_cheapest(self):
        df = economics.compare_cases(_cost_inputs())
        for hy in (2036, 2046, 2056):
            sub = df[df.horizon_year == hy].set_index("cost_case")
            assert sub.loc["DEF", "lifecycle_cost_npv_usd"] <= sub.loc["STG", "lifecycle_cost_npv_usd"]

    def test_escalation_cases_ordered(self):
        lo = economics.compare_cases(_cost_inputs(), "low")
        hi = economics.compare_cases(_cost_inputs(), "high")
        v = lambda d: d[(d.horizon_year == 2056) & (d.cost_case == "STG")]["lifecycle_cost_nominal_usd"].iloc[0]
        assert v(lo) < v(hi)

    def test_labels_screening(self):
        df = economics.compare_cases(_cost_inputs())
        assert (df["estimate_class"] == "screening_planning_estimate").all()

    def test_monotone_cumulative_costs(self):
        df = economics.compare_cases(_cost_inputs())
        for case in ("OVB", "STG", "DEF"):
            seq = df[df.cost_case == case].sort_values("horizon_year")["lifecycle_cost_nominal_usd"].tolist()
            assert seq == sorted(seq)


class TestEmissions:
    def test_vintage_always_attached(self):
        out = emissions.net_co2e_kg(10000)
        assert "eGRID2023" in out["grid_factor_vintage"] or "eGRID2023" in out["grid_factor_source"]
        assert out["grid_factor_value"] == 596.3

    def test_net_positive_for_this_grid(self):
        out = emissions.net_co2e_kg(10000)
        assert out["net_co2e_avoided_kg"] > 0

    def test_dirty_grid_can_go_negative_is_not_clipped(self):
        # simulate a very dirty effective grid by renewable_matched_share < 0 (hypothetical)
        out = emissions.net_co2e_kg(10000, renewable_matched_share=-8.0)
        assert out["net_co2e_avoided_kg"] < 0  # counterintuitive result stays visible

    def test_renewable_matching_improves_net(self):
        base = emissions.net_co2e_kg(10000)["net_co2e_avoided_kg"]
        matched = emissions.net_co2e_kg(10000, renewable_matched_share=0.5)["net_co2e_avoided_kg"]
        assert matched > base

    def test_zero_ports_zero_energy(self):
        assert emissions.annual_energy_delivered_kwh(5.0, 0) == 0.0


class TestTriggers:
    def _metrics(self, **kw):
        base = dict(site_id="FFX002", months_observed=8, avg_utilization=0.45,
                    p90_wait_min=12, uptime=0.99, equity_index_percentile=0.3)
        base.update(kw)
        return triggers.ObservedMetrics(**base)

    def test_no_data_awaiting(self):
        d = triggers.evaluate(None, 2, 8, site_id="FFX002")
        assert d.outcome == "awaiting_observed_data"

    def test_expansion_recommended_with_sustained_demand(self):
        d = triggers.evaluate(self._metrics(), 2, 8)
        assert d.outcome == "expand_review_recommended"
        assert any("human" in t for t in d.rule_trace)

    def test_equity_override_lowers_gate(self):
        m = self._metrics(avg_utilization=0.30, p90_wait_min=2, equity_index_percentile=0.8)
        d = triggers.evaluate(m, 2, 8)
        assert d.equity_override_applied and d.outcome == "expand_review_recommended"

    def test_without_override_same_metrics_hold(self):
        m = self._metrics(avg_utilization=0.30, p90_wait_min=2, equity_index_percentile=0.2)
        d = triggers.evaluate(m, 2, 8)
        assert d.outcome == "hold"

    def test_reliability_gate(self):
        d = triggers.evaluate(self._metrics(uptime=0.90), 2, 8)
        assert d.outcome == "hold"

    def test_pathway_gate(self):
        d = triggers.evaluate(self._metrics(), 8, 8)
        assert d.outcome == "hold"

    def test_min_observation_gate(self):
        d = triggers.evaluate(self._metrics(months_observed=2), 2, 8)
        assert d.outcome == "hold"

    def test_decisions_are_explainable(self):
        d = triggers.evaluate(self._metrics(), 2, 8)
        assert len(d.rule_trace) >= 3
        assert d.policy_status.startswith("proposed")
