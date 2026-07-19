"""Demand model status, provenance, and calibration path (PY-03).

The screening demand model is the legacy linear formula (see scoring.expected_sessions).
Its status is ``synthetic_uncalibrated`` and the model refuses to call itself calibrated
unless observed data with acceptable fit metrics are supplied.

Observed-data import format: ``data/observed/observed_sessions_template.csv`` with columns
    site_id, date, sessions, energy_kwh, mean_dwell_min, facility_visitors_day
One row per site per day. ``calibrate()`` fits the linear coefficients against the
site attributes, reports holdout metrics, and writes a calibration record. Until that
happens, every output carries the uncalibrated label.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DEMAND_COEFFICIENTS, DEMAND_COEFFICIENT_PROVENANCE, DEMAND_FLOOR_SESSIONS, DEMAND_MODEL_STATUS

MIN_OBSERVED_ROWS = 60         # at least ~2 months of daily data across sites
MIN_SITES_OBSERVED = 3
MAX_ACCEPTABLE_MAPE = 0.50     # screening-grade acceptance; team may tighten

OBSERVED_COLUMNS = ["site_id", "date", "sessions", "energy_kwh", "mean_dwell_min", "facility_visitors_day"]


@dataclass
class DemandModelRecord:
    status: str
    coefficients: dict
    floor_sessions: float
    provenance: str
    calibrated_at: str | None = None
    calibration_metrics: dict | None = None
    n_observed_rows: int = 0
    n_observed_sites: int = 0


def current_model_record() -> DemandModelRecord:
    return DemandModelRecord(
        status=DEMAND_MODEL_STATUS,
        coefficients=dict(DEMAND_COEFFICIENTS),
        floor_sessions=DEMAND_FLOOR_SESSIONS,
        provenance=DEMAND_COEFFICIENT_PROVENANCE,
    )


def load_observed(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in OBSERVED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Observed-session file missing columns: {missing}")
    df["date"] = pd.to_datetime(df["date"])
    return df


def calibrate(observed: pd.DataFrame, sites: pd.DataFrame, validation_split: float = 0.25,
              seed: int = 0) -> DemandModelRecord:
    """Fit linear demand coefficients against observed mean daily sessions per site.

    Refuses to return a 'calibrated' record when data are insufficient or fit is poor.
    """
    if len(observed) < MIN_OBSERVED_ROWS or observed["site_id"].nunique() < MIN_SITES_OBSERVED:
        record = current_model_record()
        record.n_observed_rows = len(observed)
        record.n_observed_sites = observed["site_id"].nunique()
        record.calibration_metrics = {
            "refused": True,
            "reason": f"insufficient observed data (rows={len(observed)}, sites={observed['site_id'].nunique()}; "
                      f"need >={MIN_OBSERVED_ROWS} rows across >={MIN_SITES_OBSERVED} sites)",
        }
        return record

    per_site = observed.groupby("site_id")["sessions"].mean().rename("observed_sessions_day")
    X_cols = ["visitors_day", "employees_day", "nearby_jobs_1mi", "nearby_households_1mi"]
    data = sites.set_index("site_id")[X_cols + ["ev_share_local"]].join(per_site, how="inner").dropna()
    if len(data) < MIN_SITES_OBSERVED:
        record = current_model_record()
        record.calibration_metrics = {"refused": True, "reason": "observed sites do not match model sites"}
        return record

    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(data))
    n_hold = max(1, int(len(data) * validation_split))
    hold_idx, fit_idx = idx[:n_hold], idx[n_hold:]
    fit, hold = data.iloc[fit_idx], data.iloc[hold_idx]

    X = fit[X_cols].to_numpy(dtype=float)
    X[:, 3] = X[:, 3] * (1 + fit["ev_share_local"].to_numpy(dtype=float))
    y = fit["observed_sessions_day"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    coef = np.clip(coef, 0, None)  # keep coefficients physical (non-negative)

    Xh = hold[X_cols].to_numpy(dtype=float)
    Xh[:, 3] = Xh[:, 3] * (1 + hold["ev_share_local"].to_numpy(dtype=float))
    pred = np.clip(Xh @ coef, DEMAND_FLOOR_SESSIONS, None)
    actual = hold["observed_sessions_day"].to_numpy(dtype=float)
    mape = float(np.mean(np.abs(pred - actual) / np.clip(actual, 1e-6, None)))
    p10, p50, p90 = (float(np.percentile(pred, q)) for q in (10, 50, 90))

    metrics = {"holdout_mape": round(mape, 3), "n_fit": len(fit), "n_holdout": len(hold),
               "pred_p10": p10, "pred_p50": p50, "pred_p90": p90}

    if mape > MAX_ACCEPTABLE_MAPE:
        record = current_model_record()
        record.calibration_metrics = {**metrics, "refused": True,
                                      "reason": f"holdout MAPE {mape:.2f} exceeds acceptance {MAX_ACCEPTABLE_MAPE}"}
        return record

    return DemandModelRecord(
        status="calibrated_observed",
        coefficients={
            "visitors_day": float(coef[0]),
            "employees_day": float(coef[1]),
            "nearby_jobs_1mi": float(coef[2]),
            "nearby_households_1mi": float(coef[3]),
        },
        floor_sessions=DEMAND_FLOOR_SESSIONS,
        provenance=f"Calibrated against {len(observed)} observed site-days "
                   f"({observed['site_id'].nunique()} sites) on {datetime.now(timezone.utc).date()}",
        calibrated_at=datetime.now(timezone.utc).isoformat(),
        calibration_metrics=metrics,
        n_observed_rows=len(observed),
        n_observed_sites=observed["site_id"].nunique(),
    )


def write_record(record: DemandModelRecord, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(record), f, indent=2)


def presentation_caveat(record: DemandModelRecord) -> str:
    if record.status == "calibrated_observed":
        return (f"Demand model calibrated against observed data ({record.n_observed_sites} sites, "
                f"{record.n_observed_rows} site-days); holdout MAPE "
                f"{record.calibration_metrics['holdout_mape']:.0%}.")
    return ("Demand estimates use a synthetic, uncalibrated screening formula. "
            "No observed charging sessions exist yet; values are planning inputs, not forecasts.")
