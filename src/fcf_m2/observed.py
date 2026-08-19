"""Observed field data: the V4 loop that lets reality correct the model.

V3 is a frozen screening study. Its largest weakness is that **electrical capacity is a
placeholder at 12 of 12 sites** and **0 of 12 reach High data confidence**; everything
downstream inherits that. Meanwhile ``data/observed/`` sat unused and ``triggers.py``
implemented an expansion policy that had never been evaluated against anything.

This module is the path in. Two record types, because two different things are observed by
two different people for two different purposes:

``CapacityObservation``
    What a facility manager or the utility confirms about the electrical service. This is
    what moves ``capacity_basis`` off ``placeholder`` and closes limitation #1. The fields
    mirror ``docs/human-actions/utility_facility_data/02_DATA_REQUEST_FACILITY_MANAGERS.md``
    so that what is asked for is what can be ingested.

``SessionObservation``
    What the chargers report. This is what feeds ``triggers.evaluate``.

Why the session schema is wider than the shipped template
---------------------------------------------------------
``data/observed/observed_sessions_template.csv`` offers six fields: site, date, sessions,
energy, mean dwell, visitors. The trigger policy in ``assumptions.json`` gates on average
utilisation, p90 wait, uptime and equity percentile - and ``triggers.evaluate`` checks
**uptime first**, refusing to trust utilisation until reliability clears. Of those four,
utilisation is only derivable if port count and open hours are joined in, p90 wait needs
per-session timing rather than a daily dwell mean, and uptime has no corresponding field at
all. The one metric the policy consults first is the one the template cannot supply.

So the template is extended rather than reinterpreted. Every added field is something a
networked EVSE actually reports.

The guardrail
-------------
**This module ships the pipeline, not data.** ``data/observed/`` contains templates and
clearly-marked synthetic fixtures and **zero real observations**. Every surface that would
display observed data says so honestly. A site whose capacity is still a placeholder still
says ``placeholder``, loudly, and no code path here can change that without a record that
names a source, a date and a method.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .config import CAPACITY_BASIS_VALUES
from .confidence import SOURCE_CLASS_SCORES, VERIFICATION_STATUS_ADJ

# --------------------------------------------------------------------------- vocabularies

#: How a capacity value was established. Ordered by precedence, strongest first, per
#: docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md rule 1.
CAPACITY_METHOD_PRECEDENCE = [
    "utility_service_record",     # -> verified_utility
    "utility_load_study",         # -> verified_utility
    "facility_panel_schedule",    # -> verified_facility
    "facility_walkthrough",       # -> verified_facility
    "engineering_calculation",    # -> engineering_estimate
    "comparable_site_proxy",      # -> planning_proxy
]

#: Which capacity_basis each method may justify. A method can never justify a stronger
#: basis than the evidence supports, and an assumption can never upgrade provenance.
#: capacity_basis -> the provenance class it may claim. Written out, because the two weak
#: bases have no same-named entry in SOURCE_CLASS_SCORES and a fallback silently promoted
#: them to `official_source`. An engineering calculation and a comparable-site proxy are
#: both planning assumptions: they are reasoning, not measurement.
BASIS_TO_SOURCE_CLASS = {
    "verified_utility": "verified_utility",       # 100
    "verified_facility": "verified_facility",     # 100
    "engineering_estimate": "planning_assumption",  # 35 -- a calculation, not a measurement
    "planning_proxy": "planning_assumption",        # 35 -- another site's number
}

METHOD_TO_BASIS = {
    "utility_service_record": "verified_utility",
    "utility_load_study": "verified_utility",
    "facility_panel_schedule": "verified_facility",
    "facility_walkthrough": "verified_facility",
    "engineering_calculation": "engineering_estimate",
    "comparable_site_proxy": "planning_proxy",
}

CAPACITY_COLUMNS = [
    "site_id", "observed_date", "method", "service_capacity_kw", "spare_capacity_kw",
    "measured_peak_kw", "source_org", "source_document", "observer",
    "verification_status", "notes",
]

SESSION_COLUMNS = [
    # as shipped in observed_sessions_template.csv
    "site_id", "date", "sessions", "energy_kwh", "mean_dwell_min", "facility_visitors_day",
    # added so the trigger policy can actually be evaluated - see the module docstring
    "ports_in_service", "port_hours_available", "port_hours_possible",
    "sessions_delayed", "wait_p90_min", "observer", "source_system",
]


class ObservationError(ValueError):
    """Raised when an observation cannot be trusted. Never downgraded to a warning."""


# --------------------------------------------------------------------------- records

@dataclass(frozen=True)
class CapacityObservation:
    """One confirmation of a site's electrical service. Carries its own provenance."""

    site_id: str
    observed_date: date
    method: str
    source_org: str
    source_document: str
    observer: str
    verification_status: str = "reviewed"
    service_capacity_kw: float | None = None
    spare_capacity_kw: float | None = None
    measured_peak_kw: float | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not str(self.site_id).strip():
            # An observation that names no site cannot be attributed to one. Left unchecked it
            # does not fail - `resolve_capacity` groups by site_id, so it quietly creates a
            # phantom site keyed on the empty string, whose "confirmed" capacity belongs to
            # nowhere. Refused for the same reason as a missing source document.
            raise ObservationError(
                "a capacity observation with no site_id cannot be attributed to a site.")
        if self.method not in METHOD_TO_BASIS:
            raise ObservationError(
                f"{self.site_id}: unknown method {self.method!r}. "
                f"Expected one of {sorted(METHOD_TO_BASIS)}.")
        if self.verification_status not in VERIFICATION_STATUS_ADJ:
            raise ObservationError(
                f"{self.site_id}: unknown verification_status {self.verification_status!r}.")
        if not str(self.source_document).strip() or not str(self.observer).strip():
            # Rule 3 of the data-flow document: capacity_source must name the document or
            # person and the date for every non-placeholder value. An unattributed
            # observation cannot upgrade anything, so it is refused at the door rather
            # than accepted and quietly ignored later.
            raise ObservationError(
                f"{self.site_id}: an observation with no source_document and observer "
                f"cannot establish provenance, so it cannot upgrade capacity_basis.")
        if self.service_capacity_kw is None and self.spare_capacity_kw is None:
            raise ObservationError(
                f"{self.site_id}: observation carries neither service_capacity_kw nor "
                f"spare_capacity_kw, so there is nothing to confirm.")
        for name in ("service_capacity_kw", "spare_capacity_kw", "measured_peak_kw"):
            value = getattr(self, name)
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ObservationError(f"{self.site_id}: {name}={value!r} is not a valid kW value.")

    @property
    def implied_basis(self) -> str:
        """The strongest capacity_basis this evidence supports. Never more."""
        return METHOD_TO_BASIS[self.method]

    @property
    def capacity_source(self) -> str:
        """The provenance string that travels with the value into the contract."""
        return (f"{self.implied_basis} via {self.method}: {self.source_document} "
                f"({self.source_org}), recorded by {self.observer} on "
                f"{self.observed_date.isoformat()}")


@dataclass(frozen=True)
class SessionObservation:
    """One site-day of charger operation."""

    site_id: str
    date: date
    sessions: float
    energy_kwh: float
    mean_dwell_min: float
    ports_in_service: int
    port_hours_available: float
    port_hours_possible: float
    facility_visitors_day: float | None = None
    sessions_delayed: int = 0
    wait_p90_min: float | None = None
    observer: str = ""
    source_system: str = ""

    def __post_init__(self) -> None:
        if not str(self.site_id).strip():
            raise ObservationError(
                f"a session observation for {self.date} names no site_id, so it cannot be "
                f"attributed to a site.")
        if self.ports_in_service <= 0:
            raise ObservationError(f"{self.site_id} {self.date}: ports_in_service must be > 0.")
        if self.port_hours_possible <= 0:
            raise ObservationError(f"{self.site_id} {self.date}: port_hours_possible must be > 0.")
        if self.port_hours_available > self.port_hours_possible + 1e-9:
            raise ObservationError(
                f"{self.site_id} {self.date}: port_hours_available "
                f"({self.port_hours_available}) exceeds port_hours_possible "
                f"({self.port_hours_possible}); uptime cannot exceed 1.")
        for name in ("sessions", "energy_kwh", "mean_dwell_min"):
            if getattr(self, name) < 0:
                raise ObservationError(f"{self.site_id} {self.date}: {name} must be >= 0.")

    @property
    def uptime(self) -> float:
        """Availability, 0-1. The gate triggers.evaluate consults first."""
        return self.port_hours_available / self.port_hours_possible

    @property
    def utilization(self) -> float:
        """Share of available port-hours actually delivering energy, 0-1."""
        if self.port_hours_available <= 0:
            return 0.0
        occupied_hours = self.sessions * (self.mean_dwell_min / 60.0)
        return min(occupied_hours / self.port_hours_available, 1.0)


# --------------------------------------------------------------------------- ingestion

def _optional_float(row: pd.Series, name: str) -> float | None:
    value = row.get(name)
    if value is None or (isinstance(value, float) and math.isnan(value)) or value == "":
        return None
    return float(value)


def _as_text(row: pd.Series, name: str, default: str = "") -> str:
    """Read a text cell, treating a missing/blank cell as empty - never as the word "nan".

    This exists because of a defect that defeated the project's central provenance guarantee
    for as long as the V4 loop has existed.

    ``CapacityObservation.__post_init__`` refuses an observation whose ``source_document`` or
    ``observer`` is blank, because an unattributed record must not be able to upgrade a site's
    ``capacity_basis``. That refusal is correct and it **never fired**: pandas reads a blank CSV
    cell as ``NaN``, and the readers did ``str(row[name]).strip()``, so ``NaN`` arrived at the
    check as the four-character string ``'nan'``. Non-empty. Check passes.

    The consequence was not cosmetic. A row with no attribution at all was accepted, reported
    ``implied_basis == 'verified_utility'`` - the strongest basis available - and produced the
    provenance string ``"verified_utility via utility_load_study: nan (...), recorded by nan
    on 2026-07-01"``. That is precisely the state the fail-closed capacity guard exists to
    prevent: a feasibility claim resting on evidence nobody supplied.

    Found by ``tests/test_field_schema_parity.py`` while checking a *browser form* against the
    model - the form refused the blank row, the model accepted it, and the disagreement was the
    signal. Nothing was looking for this.
    """
    value = row.get(name, default)
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    text = str(value).strip()
    return text if text else default


def _as_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def read_capacity_observations(path: str | Path) -> list[CapacityObservation]:
    """Load capacity confirmations. Raises on the first unusable row.

    Fail-closed on purpose: a half-ingested capacity file is how a site ends up
    described as verified on evidence nobody checked.
    """
    frame = pd.read_csv(path)
    missing = [c for c in CAPACITY_COLUMNS if c not in frame.columns]
    if missing:
        raise ObservationError(f"{path}: missing required column(s): {', '.join(missing)}")

    out: list[CapacityObservation] = []
    for index, row in frame.iterrows():
        out.append(CapacityObservation(
            site_id=_as_text(row, "site_id"),
            observed_date=_as_date(row["observed_date"]),
            method=_as_text(row, "method"),
            source_org=_as_text(row, "source_org"),
            source_document=_as_text(row, "source_document"),
            observer=_as_text(row, "observer"),
            verification_status=_as_text(row, "verification_status", "reviewed"),
            service_capacity_kw=_optional_float(row, "service_capacity_kw"),
            spare_capacity_kw=_optional_float(row, "spare_capacity_kw"),
            measured_peak_kw=_optional_float(row, "measured_peak_kw"),
            notes=_as_text(row, "notes"),
        ))
    return out


def read_session_observations(path: str | Path) -> list[SessionObservation]:
    """Load charger operating data. Raises on the first unusable row."""
    frame = pd.read_csv(path)
    missing = [c for c in SESSION_COLUMNS if c not in frame.columns]
    if missing:
        raise ObservationError(
            f"{path}: missing required column(s): {', '.join(missing)}. "
            f"The six-column template that shipped with V3 predates the trigger policy and "
            f"cannot supply uptime or p90 wait. See data/observed/README.md for what each "
            f"added column is and why the policy needs it.")

    out: list[SessionObservation] = []
    for _, row in frame.iterrows():
        out.append(SessionObservation(
            site_id=_as_text(row, "site_id"),
            date=_as_date(row["date"]),
            sessions=float(row["sessions"]),
            energy_kwh=float(row["energy_kwh"]),
            mean_dwell_min=float(row["mean_dwell_min"]),
            ports_in_service=int(row["ports_in_service"]),
            port_hours_available=float(row["port_hours_available"]),
            port_hours_possible=float(row["port_hours_possible"]),
            facility_visitors_day=_optional_float(row, "facility_visitors_day"),
            sessions_delayed=int(row.get("sessions_delayed", 0) or 0),
            wait_p90_min=_optional_float(row, "wait_p90_min"),
            observer=_as_text(row, "observer"),
            source_system=_as_text(row, "source_system"),
        ))
    return out


# --------------------------------------------------------------------------- aggregation

@dataclass
class SiteObservationSummary:
    """What a site's observations add up to, with the gaps named."""

    site_id: str
    days_observed: int = 0
    months_observed: float = 0.0
    avg_utilization: float | None = None
    p90_wait_min: float | None = None
    uptime: float | None = None
    total_sessions: float = 0.0
    total_energy_kwh: float = 0.0
    missing_for_triggers: list[str] = field(default_factory=list)

    @property
    def sufficient_for_triggers(self) -> bool:
        return not self.missing_for_triggers


def summarise_sessions(observations: list[SessionObservation]) -> dict[str, SiteObservationSummary]:
    """Aggregate site-days into the shape ``triggers.evaluate`` consumes.

    Where a metric cannot be derived it is left ``None`` and named in
    ``missing_for_triggers``, rather than defaulted. A defaulted uptime of 1.0 would
    walk straight past the reliability gate that exists to stop exactly that.
    """
    by_site: dict[str, list[SessionObservation]] = {}
    for obs in observations:
        by_site.setdefault(obs.site_id, []).append(obs)

    summaries: dict[str, SiteObservationSummary] = {}
    for site_id, rows in sorted(by_site.items()):
        summary = SiteObservationSummary(site_id=site_id, days_observed=len(rows))
        summary.months_observed = round(len(rows) / 30.44, 2)
        summary.total_sessions = float(sum(r.sessions for r in rows))
        summary.total_energy_kwh = float(sum(r.energy_kwh for r in rows))

        possible = sum(r.port_hours_possible for r in rows)
        available = sum(r.port_hours_available for r in rows)
        summary.uptime = (available / possible) if possible > 0 else None
        if summary.uptime is None:
            summary.missing_for_triggers.append("uptime")

        utilisations = [r.utilization for r in rows if r.port_hours_available > 0]
        summary.avg_utilization = (sum(utilisations) / len(utilisations)) if utilisations else None
        if summary.avg_utilization is None:
            summary.missing_for_triggers.append("avg_utilization")

        waits = [r.wait_p90_min for r in rows if r.wait_p90_min is not None]
        if waits:
            # The site-level p90 of daily p90s is an approximation, and it is labelled as
            # one wherever it surfaces. A true p90 needs per-session waits, which the
            # daily aggregate does not carry.
            ordered = sorted(waits)
            summary.p90_wait_min = ordered[min(int(0.9 * len(ordered)), len(ordered) - 1)]
        else:
            summary.missing_for_triggers.append("p90_wait_min")

        summaries[site_id] = summary
    return summaries


# --------------------------------------------------------------------------- upgrades

@dataclass
class CapacityUpgrade:
    """One site's capacity provenance, before and after."""

    site_id: str
    previous_basis: str
    new_basis: str
    service_capacity_kw: float | None
    spare_capacity_kw: float | None
    capacity_source: str
    observed_date: date
    #: The observation method that WON, carried separately from ``capacity_source`` so a
    #: consumer can filter on it without parsing prose. ``capacity_source`` is a sentence
    #: for a human; this is the controlled value from ``METHOD_TO_BASIS``.
    method: str = ""
    conflicts: list[str] = field(default_factory=list)

    @property
    def upgraded(self) -> bool:
        return self.new_basis != self.previous_basis


def _precedence(basis: str) -> int:
    """Higher is stronger. Unknown values sort lowest, so they can never win."""
    order = ["unknown", "placeholder", "planning_proxy", "engineering_estimate",
             "verified_facility", "verified_utility"]
    return order.index(basis) if basis in order else -1


def resolve_capacity(observations: list[CapacityObservation],
                     current_basis: str = "placeholder") -> dict[str, CapacityUpgrade]:
    """Apply the precedence rules to per-site capacity observations.

    Rule 1 of the data-flow document: ``verified_utility`` > ``verified_facility`` >
    ``placeholder``. Where facility and utility disagree, **both are kept in the source
    string, the more conservative value is used for screening, and the conflict is
    flagged** rather than silently resolved.
    """
    by_site: dict[str, list[CapacityObservation]] = {}
    for obs in observations:
        by_site.setdefault(obs.site_id, []).append(obs)

    upgrades: dict[str, CapacityUpgrade] = {}
    for site_id, rows in sorted(by_site.items()):
        strongest = max(rows, key=lambda o: (_precedence(o.implied_basis), o.observed_date))
        winner_basis = strongest.implied_basis

        conflicts: list[str] = []
        service_values = [(o, o.service_capacity_kw) for o in rows if o.service_capacity_kw is not None]
        if len({round(v, 3) for _, v in service_values}) > 1:
            detail = ", ".join(
                f"{o.implied_basis}={v:g} kW ({o.source_document})" for o, v in service_values)
            conflicts.append(f"service_capacity_kw disagreement: {detail}")

        chosen_service = min((v for _, v in service_values), default=None)
        spare_values = [o.spare_capacity_kw for o in rows if o.spare_capacity_kw is not None]
        chosen_spare = min(spare_values, default=None)

        source = strongest.capacity_source
        if conflicts:
            source += (" | CONFLICT, unresolved: " + "; ".join(conflicts)
                       + " | conservative value used for screening")

        if _precedence(winner_basis) <= _precedence(current_basis):
            winner_basis = current_basis

        upgrades[site_id] = CapacityUpgrade(
            site_id=site_id,
            previous_basis=current_basis,
            new_basis=winner_basis,
            service_capacity_kw=chosen_service,
            spare_capacity_kw=chosen_spare,
            capacity_source=source,
            observed_date=strongest.observed_date,
            method=strongest.method,
            conflicts=conflicts,
        )
    return upgrades


def observation_provenance_rows(observations: list[CapacityObservation]) -> pd.DataFrame:
    """Provenance records in the shape ``confidence.build_confidence`` already consumes.

    Reusing the existing typed-provenance format rather than inventing a parallel one is
    the point: confidence still derives only from typed fields, so an observation can
    raise a site's confidence only through the same rubric everything else goes through.
    """
    rows = []
    for obs in observations:
        source_class = BASIS_TO_SOURCE_CLASS.get(obs.implied_basis)
        if source_class is None:
            # Refuse rather than default. The previous fallback sent any unrecognised basis
            # to "official_source" (90/100) -- and the two bases that fall through are
            # `engineering_estimate` and `planning_proxy`, i.e. the two WEAKEST methods. A
            # comparable-site guess scored 95 while a real utility record scored 100. That is
            # exactly the inversion this module's own rule at the top of METHOD_TO_BASIS
            # forbids: "an assumption can never upgrade provenance."
            raise ObservationError(
                f"no source class is defined for capacity basis {obs.implied_basis!r} "
                f"(method {obs.method!r}); refusing to score it rather than guessing")
        rows.append({
            "site_id": obs.site_id,
            "field_group": "electrical_service",
            "source_class": source_class,
            "verification_status": obs.verification_status,
            "source_org": obs.source_org,
            "source_date": obs.observed_date.isoformat(),
            "reviewer": obs.observer,
            "assumption_type": "" if obs.implied_basis.startswith("verified") else obs.method,
            "unresolved_flag": 0,
        })
    return pd.DataFrame(rows, columns=[
        "site_id", "field_group", "source_class", "verification_status", "source_org",
        "source_date", "reviewer", "assumption_type", "unresolved_flag"])


__all__ = [
    "CAPACITY_BASIS_VALUES", "CAPACITY_COLUMNS", "SESSION_COLUMNS",
    "CapacityObservation", "SessionObservation", "SiteObservationSummary",
    "CapacityUpgrade", "ObservationError",
    "read_capacity_observations", "read_session_observations",
    "summarise_sessions", "resolve_capacity", "observation_provenance_rows",
    "METHOD_TO_BASIS", "CAPACITY_METHOD_PRECEDENCE",
]
