"""Equity-aware expansion-trigger policy (PY-20).

The policy is PROPOSED configuration (config.TRIGGER_POLICY) - it is not adopted
municipal policy and every evaluation says so. Trigger decisions are explainable:
each evaluation returns the full rule trace.

No observed utilization exists yet, so the current pipeline emits
``awaiting_observed_data`` for every site; the evaluation function is fully
implemented for when monitoring data arrive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import TRIGGER_POLICY


@dataclass
class ObservedMetrics:
    site_id: str
    months_observed: float
    avg_utilization: float          # 0-1
    p90_wait_min: float
    uptime: float                   # 0-1
    equity_index_percentile: float  # 0-1 within cohort or adopted regional benchmark


@dataclass
class TriggerDecision:
    site_id: str
    outcome: str                    # expand_review_recommended | hold | awaiting_observed_data
    equity_override_applied: bool
    rule_trace: list[str] = field(default_factory=list)
    policy_status: str = TRIGGER_POLICY["policy_status"]


def evaluate(metrics: ObservedMetrics | None, ports_active: int, ports_pathway: int,
             site_id: str = "") -> TriggerDecision:
    p = TRIGGER_POLICY
    trace: list[str] = [f"policy_status={p['policy_status']}"]

    if metrics is None:
        trace.append("no observed monitoring data -> awaiting_observed_data")
        return TriggerDecision(site_id=site_id, outcome="awaiting_observed_data",
                               equity_override_applied=False, rule_trace=trace)

    sid = metrics.site_id
    if metrics.months_observed < p["min_observation_months"]:
        trace.append(f"observation {metrics.months_observed:.1f} mo < minimum {p['min_observation_months']} mo -> hold")
        return TriggerDecision(sid, "hold", False, trace)

    if metrics.uptime < p["reliability_uptime_min"]:
        trace.append(f"uptime {metrics.uptime:.2%} < reliability gate {p['reliability_uptime_min']:.0%} "
                     "-> hold (fix reliability before trusting utilization data)")
        return TriggerDecision(sid, "hold", False, trace)

    if ports_active >= ports_pathway:
        trace.append(f"pathway gate: active {ports_active} >= pathway {ports_pathway} -> hold (no pathway headroom)")
        return TriggerDecision(sid, "hold", False, trace)

    util_gate = p["utilization_threshold"]
    override = False
    eq = p["equity_override"]
    if eq["enabled"] and metrics.equity_index_percentile >= eq["equity_index_percentile_min"]:
        util_gate = eq["reduced_utilization_threshold"]
        override = True
        trace.append(f"equity override: equity percentile {metrics.equity_index_percentile:.2f} >= "
                     f"{eq['equity_index_percentile_min']:.2f} -> utilization gate lowered to {util_gate:.0%}")

    util_met = metrics.avg_utilization >= util_gate
    wait_met = metrics.p90_wait_min >= p["wait_threshold_min"]
    trace.append(f"utilization {metrics.avg_utilization:.0%} {'>=' if util_met else '<'} gate {util_gate:.0%}")
    trace.append(f"p90 wait {metrics.p90_wait_min:.1f} min {'>=' if wait_met else '<'} threshold {p['wait_threshold_min']} min")

    if util_met or wait_met:
        trace.append("demand evidence sustained -> expansion review recommended")
        trace.append(f"budget gate: {p['budget_gate']} (human decision; this tool never authorizes expansion)")
        return TriggerDecision(sid, "expand_review_recommended", override, trace)

    trace.append("demand evidence below gates -> hold")
    return TriggerDecision(sid, "hold", override, trace)


def status_for_contract(has_observed_data: bool = False) -> str:
    if not has_observed_data:
        return "awaiting_observed_data (proposed policy, not adopted)"
    return "policy evaluation available"
