"""Erlang-C queueing screen - exact port of the accepted legacy V2 implementation.

The steady-state M/M/c screen is intentionally preserved unchanged (PY-04 requires
adding peak modeling alongside it, not replacing it). See peak_wait.py for the
peak-window and discrete-event additions.
"""

from __future__ import annotations

import math

import numpy as np

from .config import MAX_MEAN_WAIT_MIN, MAX_PORTS_SEARCH, TARGET_UTILIZATION


def erlang_c(lambda_hr: float, mu_hr: float, ports: int):
    """Legacy-exact queueing approximation (probability of wait, wait hours, utilization)."""
    if ports <= 0 or mu_hr <= 0:
        return np.nan, np.nan, np.nan

    utilization = lambda_hr / (ports * mu_hr)
    if utilization >= 1:
        return 1.0, np.inf, utilization

    traffic_load = lambda_hr / mu_hr
    sum_terms = sum((traffic_load ** n) / math.factorial(n) for n in range(ports))
    last_term = ((traffic_load ** ports) / math.factorial(ports)) * (1 / (1 - utilization))
    p0 = 1.0 / (sum_terms + last_term)
    probability_wait = last_term * p0
    wait_hours = probability_wait / (ports * mu_hr - lambda_hr)
    return probability_wait, wait_hours, utilization


def choose_ports(
    expected_sessions_day: float,
    avg_session_hr: float,
    hours_open: float,
    max_ports: int = MAX_PORTS_SEARCH,
    target_utilization: float = TARGET_UTILIZATION,
    max_mean_wait_min: float = MAX_MEAN_WAIT_MIN,
):
    """Legacy-exact port chooser: smallest port count meeting utilization + wait targets."""
    arrivals_per_hour = expected_sessions_day / max(hours_open, 1)
    service_rate_per_hour = 1 / max(avg_session_hr, 0.1)
    fallback = None

    for ports in range(1, max_ports + 1):
        _, wait_hours, utilization = erlang_c(arrivals_per_hour, service_rate_per_hour, ports)
        wait_minutes = wait_hours * 60 if np.isfinite(wait_hours) else np.inf
        if np.isfinite(wait_minutes) and utilization <= target_utilization and wait_minutes <= max_mean_wait_min:
            return ports, utilization, wait_minutes
        fallback = (ports, utilization, wait_minutes)

    return fallback
