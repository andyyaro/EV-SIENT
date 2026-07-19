"""Peak-period and discrete-event wait modeling (PY-04).

Adds to (never replaces) the legacy Erlang-C screen:

1. ``peak_window_wait`` — steady-state Erlang-C evaluated at the peak-window arrival
   rate (a configurable share of daily sessions concentrated into a peak window).
2. ``simulate_waits`` — a seeded discrete-event simulation (M/G/c) with configurable
   arrival, dwell, and session-energy distributions, reporting P10/P50/P90 waits for
   the whole day and for the peak window.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import PEAK_WINDOW_HOURS, PEAK_WINDOW_SHARE, SIM_N_DAYS, SIM_RANDOM_SEED
from .queueing import erlang_c


def peak_window_wait(expected_sessions_day: float, avg_session_hr: float, hours_open: float,
                     ports: int, peak_share: float = PEAK_WINDOW_SHARE,
                     peak_hours: float = PEAK_WINDOW_HOURS):
    """Erlang-C wait evaluated inside the peak window. Returns (wait_min, utilization)."""
    hours_open = max(hours_open, 1.0)
    peak_hours = min(peak_hours, hours_open)
    lam_peak = expected_sessions_day * peak_share / peak_hours
    mu = 1 / max(avg_session_hr, 0.1)
    _, wait_hr, util = erlang_c(lam_peak, mu, ports)
    wait_min = wait_hr * 60 if np.isfinite(wait_hr) else np.inf
    return wait_min, util


@dataclass
class SimResult:
    ports: int
    n_days: int
    mean_wait_min: float
    p10_wait_min: float
    p50_wait_min: float
    p90_wait_min: float
    peak_p90_wait_min: float
    mean_utilization: float
    seed: int


def simulate_waits(expected_sessions_day: float, avg_session_hr: float, hours_open: float,
                   ports: int, n_days: int = SIM_N_DAYS, seed: int = SIM_RANDOM_SEED,
                   peak_share: float = PEAK_WINDOW_SHARE, peak_hours: float = PEAK_WINDOW_HOURS,
                   dwell_cv: float = 0.45) -> SimResult:
    """Discrete-event M/G/c queue simulation, deterministic under a fixed seed.

    Arrivals: non-homogeneous Poisson — `peak_share` of daily sessions inside a
    centered peak window, the rest spread over remaining open hours.
    Dwell: lognormal with mean `avg_session_hr` and coefficient of variation `dwell_cv`.
    """
    rng = np.random.default_rng(seed)
    hours_open = max(hours_open, 1.0)
    peak_hours = min(peak_hours, hours_open)
    off_hours = max(hours_open - peak_hours, 1e-9)
    peak_start = (hours_open - peak_hours) / 2.0

    mean_dwell = max(avg_session_hr, 0.1)
    sigma2 = np.log(1 + dwell_cv ** 2)
    mu_log = np.log(mean_dwell) - sigma2 / 2

    all_waits, peak_waits, busy_time = [], [], 0.0

    for _ in range(n_days):
        n_peak = rng.poisson(expected_sessions_day * peak_share)
        n_off = rng.poisson(expected_sessions_day * (1 - peak_share))
        arr = np.concatenate([
            peak_start + rng.random(n_peak) * peak_hours,
            _off_window_arrivals(rng, n_off, hours_open, peak_start, peak_hours, off_hours),
        ])
        arr.sort()
        dwell = rng.lognormal(mu_log, np.sqrt(sigma2), size=len(arr))

        free_at = np.zeros(ports)
        for t, d in zip(arr, dwell):
            k = int(np.argmin(free_at))
            start = max(t, free_at[k])
            wait = start - t
            free_at[k] = start + d
            all_waits.append(wait * 60)
            if peak_start <= t <= peak_start + peak_hours:
                peak_waits.append(wait * 60)
            busy_time += d

    waits = np.array(all_waits) if all_waits else np.array([0.0])
    pk = np.array(peak_waits) if peak_waits else np.array([0.0])
    return SimResult(
        ports=ports,
        n_days=n_days,
        mean_wait_min=float(waits.mean()),
        p10_wait_min=float(np.percentile(waits, 10)),
        p50_wait_min=float(np.percentile(waits, 50)),
        p90_wait_min=float(np.percentile(waits, 90)),
        peak_p90_wait_min=float(np.percentile(pk, 90)),
        mean_utilization=float(busy_time / (ports * hours_open * n_days)),
        seed=seed,
    )


def _off_window_arrivals(rng, n, hours_open, peak_start, peak_hours, off_hours):
    """Uniform arrivals over open hours excluding the peak window."""
    if n == 0:
        return np.empty(0)
    u = rng.random(n) * off_hours
    before = u < peak_start
    out = np.where(before, u, u + peak_hours)
    return np.clip(out, 0, hours_open)
