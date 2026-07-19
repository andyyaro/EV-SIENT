"""Unit + property tests: normalization/anchors, Erlang-C, port chooser, cohort invariance."""

import numpy as np
import pandas as pd
import pytest

from fcf_m2.queueing import choose_ports, erlang_c
from fcf_m2.scoring import anchored, bounded_signal, enrich_and_score, minmax


class TestNormalization:
    def test_minmax_bounds(self):
        s = pd.Series([3, 7, 11])
        out = minmax(s)
        assert out.min() == 0 and out.max() == 1

    def test_minmax_constant_series_is_zero(self):
        assert (minmax(pd.Series([5, 5, 5])) == 0).all()

    def test_anchored_clips_and_scales(self):
        s = pd.Series([-10, 0, 50, 100, 500])
        out = anchored(s, 0, 100)
        assert list(out) == [0.0, 0.0, 0.5, 1.0, 1.0]

    def test_anchored_degenerate_range(self):
        assert (anchored(pd.Series([1, 2]), 5, 5) == 0).all()

    def test_bounded_signal(self):
        out = bounded_signal(pd.Series([0.0, 0.05, 0.2]), 0.10)
        assert list(out) == [0.0, 0.5, 1.0]

    @pytest.mark.parametrize("vals", [[0, 1, 2], [10, 20, 30], [0.1, 0.5, 0.9]])
    def test_anchored_property_monotone(self, vals):
        s = pd.Series(vals)
        out = anchored(s, min(vals), max(vals))
        assert out.is_monotonic_increasing


class TestErlang:
    def test_zero_ports_nan(self):
        assert np.isnan(erlang_c(1.0, 1.0, 0)[0])

    def test_overload_infinite_wait(self):
        p_wait, wait, util = erlang_c(10.0, 1.0, 5)
        assert p_wait == 1.0 and np.isinf(wait) and util >= 1

    def test_light_load_low_wait(self):
        p_wait, wait, util = erlang_c(0.1, 0.5, 2)
        assert 0 <= p_wait < 0.2 and wait < 0.5 and util < 0.2

    def test_more_ports_never_worse(self):
        waits = []
        for c in range(1, 6):
            _, w, _ = erlang_c(0.8, 0.5, c)
            waits.append(w if np.isfinite(w) else 1e9)
        assert all(b <= a + 1e-12 for a, b in zip(waits, waits[1:]))


class TestChoosePorts:
    def test_meets_targets(self):
        ports, util, wait = choose_ports(10.0, 1.5, 12)
        assert util <= 0.70 and wait <= 10

    def test_fallback_on_extreme_load(self):
        ports, util, wait = choose_ports(2000.0, 2.0, 8, max_ports=5)
        assert ports == 5  # fallback = max searched

    def test_minimal_demand_single_port(self):
        ports, _, _ = choose_ports(0.3, 2.0, 12)
        assert ports == 1


class TestCohortInvariance:
    """PY-02 acceptance: a site's V3 score is unchanged when the cohort changes."""

    def test_fixed_anchor_scores_survive_cohort_changes(self, sites, anchors):
        full = enrich_and_score(sites, mode="milestone2_v3", anchor_set=anchors)
        subset = enrich_and_score(sites.iloc[:6].copy(), mode="milestone2_v3", anchor_set=anchors)
        merged = full.set_index("site_id").loc[subset["site_id"]]
        assert np.allclose(merged["readiness_score"].values,
                           subset.set_index("site_id")["readiness_score"].values)

    def test_legacy_scores_do_change_with_cohort(self, sites):
        """Documents the legacy defect the anchors fix."""
        full = enrich_and_score(sites, mode="legacy_v2")
        subset = enrich_and_score(sites.iloc[:6].copy(), mode="legacy_v2")
        merged = full.set_index("site_id").loc[subset["site_id"]]
        assert not np.allclose(merged["readiness_score"].values,
                               subset.set_index("site_id")["readiness_score"].values)

    def test_v3_requires_anchor_set(self, sites):
        with pytest.raises(ValueError):
            enrich_and_score(sites, mode="milestone2_v3", anchor_set=None)
