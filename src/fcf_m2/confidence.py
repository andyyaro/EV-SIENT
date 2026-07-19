"""Structured, typed data-confidence scoring (PY-05).

Replaces the legacy note-keyword heuristics ('official' +5 / 'unconfirmed' -6) with
field-level provenance records. Confidence derives ONLY from typed fields — changing
prose in `notes` cannot change a confidence score.

Provenance input: ``data/provenance/field_provenance_v1.csv`` with one row per
(site_id, field_group):
    site_id, field_group, source_class, verification_status, source_org, source_date,
    reviewer, assumption_type, unresolved_flag

Controlled vocabularies below. The overall site confidence is a weighted average of
field-group scores; the field-level breakdown is preserved in the output.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

SOURCE_CLASS_SCORES = {
    "verified_utility": 100,
    "verified_facility": 100,
    "official_source": 90,
    "official_gis": 90,
    "public_web_reference": 60,
    "derived_public_data": 55,
    "planning_assumption": 35,
    "synthetic_model": 30,
    "unconfirmed": 15,
    "missing": 0,
}

VERIFICATION_STATUS_ADJ = {
    "reviewed": +5,
    "spot_checked": 0,
    "unreviewed": -5,
}

STALENESS_THRESHOLD_DAYS = 730   # >2 years old → stale penalty
STALENESS_PENALTY = 10

# Field-group weights: electrical fields dominate because they gate feasibility.
FIELD_GROUP_WEIGHTS = {
    "electrical_service": 0.25,
    "site_use_and_demand": 0.20,
    "address_and_public_access": 0.10,
    "coordinates": 0.05,
    "parking_and_layout": 0.15,
    "safety_review_fields": 0.15,
    "equity_and_context": 0.10,
}

REQUIRED_COLUMNS = ["site_id", "field_group", "source_class", "verification_status",
                    "source_org", "source_date", "reviewer", "assumption_type", "unresolved_flag"]


def level_for(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _staleness_penalty(source_date: str, today: date | None = None) -> int:
    if not source_date or pd.isna(source_date):
        return STALENESS_PENALTY
    try:
        d = datetime.fromisoformat(str(source_date)).date()
    except ValueError:
        return STALENESS_PENALTY
    today = today or date.today()
    return STALENESS_PENALTY if (today - d).days > STALENESS_THRESHOLD_DAYS else 0


def score_field(row: pd.Series, today: date | None = None) -> float:
    base = SOURCE_CLASS_SCORES.get(str(row["source_class"]), 0)
    adj = VERIFICATION_STATUS_ADJ.get(str(row["verification_status"]), -5)
    stale = _staleness_penalty(row.get("source_date"), today)
    unresolved = 15 if str(row.get("unresolved_flag", "")).lower() in {"1", "true", "yes"} else 0
    return max(0.0, min(100.0, base + adj - stale - unresolved))


def validate_provenance(prov: pd.DataFrame) -> list[str]:
    problems = []
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in prov.columns]
    if missing_cols:
        problems.append(f"missing columns: {missing_cols}")
        return problems
    bad_class = sorted(set(prov["source_class"]) - set(SOURCE_CLASS_SCORES))
    if bad_class:
        problems.append(f"unknown source_class values: {bad_class}")
    bad_group = sorted(set(prov["field_group"]) - set(FIELD_GROUP_WEIGHTS))
    if bad_group:
        problems.append(f"unknown field_group values: {bad_group}")
    return problems


def build_confidence(prov: pd.DataFrame, site_ids: list[str], today: date | None = None) -> pd.DataFrame:
    """Return per-site confidence with field-level breakdown. Sites missing provenance
    rows for a field group receive the 'missing' score for that group."""
    problems = validate_provenance(prov)
    if problems:
        raise ValueError(f"Provenance validation failed: {problems}")

    prov = prov.copy()
    prov["field_score"] = prov.apply(lambda r: score_field(r, today), axis=1)

    rows = []
    for sid in site_ids:
        site_prov = prov[prov["site_id"] == sid].set_index("field_group")
        total, breakdown = 0.0, {}
        for group, weight in FIELD_GROUP_WEIGHTS.items():
            if group in site_prov.index:
                entry = site_prov.loc[group]
                if isinstance(entry, pd.DataFrame):
                    entry = entry.iloc[0]
                s = float(entry["field_score"])
            else:
                s = float(SOURCE_CLASS_SCORES["missing"])
            breakdown[group] = round(s, 1)
            total += weight * s
        rows.append({
            "site_id": sid,
            "data_confidence_score_v3": round(total, 1),
            "data_confidence_level_v3": level_for(total),
            "confidence_breakdown": "; ".join(f"{g}={v}" for g, v in breakdown.items()),
        })
    return pd.DataFrame(rows)
