"""The official pathway total, recomputed without the model's code (DEC-027).

The owner's decision of 2026-10-18 makes 47 the official future-ready total: the one the
canonical ``milestone2_v3`` rules give. A number that only the model's own functions can
reproduce is checked by nothing but itself, so this file rebuilds it from the published site
results with its own arithmetic:

* the wait screen is Erlang C computed through the Erlang B recursion, not the model's
  factorial sum;
* the port chooser, the strategy floors, the parking cap and the future-ready rule are
  restated here from their written description, not imported.

It reads only ``tests/fixture_*_site_results.csv`` (scores, ranks, tiers and the site fields)
and ``config``'s published constants. It then checks both readings: on the fixed-anchor
ranking with the V3 multipliers the total is 47, per site as in contract v3; on the legacy
ranking with the legacy multipliers it is the earlier 48, per site as in contract v1.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fcf_m2 import config  # noqa: E402  (constants only)


def erlang_c_wait_minutes(arrivals_hr: float, service_hr: float, servers: int) -> tuple[float, float]:
    """Mean wait (minutes) and utilisation for M/M/c, via the Erlang B recursion."""
    load = arrivals_hr / service_hr
    rho = load / servers
    if rho >= 1:
        return math.inf, rho
    b = 1.0
    for k in range(1, servers + 1):
        b = load * b / (k + load * b)
    c = b / (1 - rho * (1 - b))
    return 60 * c / (servers * service_hr - arrivals_hr), rho


def smallest_ports(sessions_day: float, dwell_min: float, hours_open: float) -> int:
    """Fewest ports with utilisation <= 70% and mean wait <= 10 min; 2 at least."""
    arrivals = sessions_day / max(hours_open, 1)
    service = 1 / max(dwell_min / 60, 0.1)
    chosen = config.MAX_PORTS_SEARCH
    for ports in range(1, config.MAX_PORTS_SEARCH + 1):
        wait, rho = erlang_c_wait_minutes(arrivals, service, ports)
        if rho <= config.TARGET_UTILIZATION and wait <= config.MAX_MEAN_WAIT_MIN:
            chosen = ports
            break
    return max(2, chosen)


def parking_cap(spaces: float) -> int:
    """5% of the spaces, up to the next even number, between 2 and 12; 2 if uncounted."""
    if not spaces or spaces <= 0 or math.isnan(spaces):
        return 2
    n = math.ceil(spaces * 0.05)
    n += n % 2
    return min(12, max(2, n))


def pathway(site: pd.Series, h1: tuple[float, float], h2: tuple[float, float]) -> int:
    """The future-ready rule, restated: floors, then cap, then the larger of the starter
    ports, the first horizon's high case and the second horizon's base case (a Tier 1 site
    also reserves its second-horizon high case), capped by the lot."""
    def q(mult: float) -> int:
        return smallest_ports(site.expected_sessions_day * mult, site.avg_dwell_min, site.hours_open)

    now = max(2, int(round(site.recommended_ports_now)))
    t = {"h1b": q(h1[0]), "h1h": q(h1[1]), "h2b": q(h2[0]), "h2h": q(h2[1])}
    tier, rank, score = str(site.recommendation_tier), int(site.model_rank), float(site.readiness_score)
    if site.public_access < 1:
        t = {k: min(v, 2) for k, v in t.items()}
        now = min(now, 2)
    else:
        if tier.startswith("Tier 1"):
            floor = {"h1b": 4, "h1h": 6, "h2b": 6, "h2h": 8}
        elif score >= 50 and rank <= 6 and "garage" not in str(site.site_type).lower():
            floor = {"h1b": 4, "h1h": 4, "h2b": 4, "h2h": 6}
        elif tier.startswith("Tier 2"):
            floor = {"h1b": 0, "h1h": 4, "h2b": 4, "h2h": 4}
        else:
            floor = {}
        t = {k: max(v, floor.get(k, 0)) for k, v in t.items()}
        if site.existing_ports_total >= 50 and score < 45:
            t = {k: min(v, {"h1b": 2}.get(k, 4)) for k, v in t.items()}
        if str(site.electrical_risk_level).lower() == "high":
            now = min(now, 2)
            t = {k: min(v, {"h2h": 6}.get(k, 4)) for k, v in t.items()}
    cap = parking_cap(site.parking_spaces)
    t = {k: min(v, cap) for k, v in t.items()}
    ready = max(now, t["h1h"], t["h2b"])
    if tier.startswith("Tier 1"):
        ready = max(ready, min(t["h2h"], cap))
    return min(ready, cap)


V3_MULT = ((config.V3_GROWTH_MULTIPLIERS[(2036, "base")], config.V3_GROWTH_MULTIPLIERS[(2036, "high")]),
           (config.V3_GROWTH_MULTIPLIERS[(2046, "base")], config.V3_GROWTH_MULTIPLIERS[(2046, "high")]))
LEGACY_MULT = ((config.LEGACY_GROWTH_MULTIPLIERS["2035_base"], config.LEGACY_GROWTH_MULTIPLIERS["2035_high"]),
               (config.LEGACY_GROWTH_MULTIPLIERS["2050_base"], config.LEGACY_GROWTH_MULTIPLIERS["2050_high"]))


def _pathways(fixture: str, mult) -> dict[str, int]:
    sites = pd.read_csv(ROOT / "tests" / fixture)
    if "electrical_risk_level" not in sites.columns:
        risk = pd.read_csv(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv")
        sites = sites.merge(risk[["site_id", "electrical_risk_level"]], on="site_id", how="left")
    return {row.site_id: pathway(row, *mult) for row in sites.itertuples(index=False)}


def _contract_pathways(version: str) -> dict[str, int]:
    table = pd.read_csv(ROOT / f"data/contract/{version}/scenario_table.csv")
    base = table[table.horizon_year == config.BASELINE_YEAR]
    return dict(zip(base.site_id, base.ports_pathway_capacity.astype(int)))


def test_the_erlang_b_route_agrees_with_the_textbook_value():
    """Sanity of the independent screen: M/M/2 with load 1 waits P=1/3, Wq=1/3 hour at mu=1."""
    wait, rho = erlang_c_wait_minutes(1.0, 1.0, 2)
    assert rho == pytest.approx(0.5)
    assert wait == pytest.approx(20.0)


@pytest.mark.real_inputs
def test_the_official_pathway_is_47_on_the_canonical_rules():
    mine = _pathways("fixture_milestone2_v3_site_results.csv", V3_MULT)
    assert sum(mine.values()) == 47
    assert mine == _contract_pathways("v3"), "per-site pathway differs from contract v3"


@pytest.mark.real_inputs
def test_the_earlier_legacy_v2_pathway_is_48():
    mine = _pathways("fixture_legacy_v2_site_results.csv", LEGACY_MULT)
    assert sum(mine.values()) == 48
    assert mine == _contract_pathways("v1"), "per-site pathway differs from the frozen v1"


@pytest.mark.real_inputs
def test_the_difference_is_the_ranking_not_the_multipliers():
    """Both multiplier sets give 47 on the fixed-anchor ranking and 48 on the legacy one: the
    one-port difference is which sites the plan treats as Tier 2 and Tier 3."""
    assert sum(_pathways("fixture_milestone2_v3_site_results.csv", LEGACY_MULT).values()) == 47
    assert sum(_pathways("fixture_legacy_v2_site_results.csv", V3_MULT).values()) == 48
