#!/usr/bin/env python3
"""Emit the field-entry schema the platform's forms are built from.

Why this is generated rather than written
-----------------------------------------
``observed.py`` refuses observations it cannot trust: an unattributed record, a capacity row
that confirms nothing, availability that exceeds what was possible. Those refusals are the
V4 loop's whole point - they are why a site cannot become "verified" on evidence nobody
checked.

A hand-written browser form is a **second copy of those rules**, and a second copy drifts. It
drifts in one direction in particular: the form ends up *more permissive* than the model, so a
field worker fills in a row the page accepts and the ingest step later rejects - or worse, the
form is stricter and quietly discourages a legitimate observation.

So the vocabularies, the columns and the rules are read out of ``observed.py`` here and
rendered as data. The browser interprets that data; it does not restate it. Parity between the
two interpreters is then a *testable* claim rather than a hope, and
``tests/test_field_schema_parity.py`` tests it by running the same candidate rows through both.

This is the same move the rest of the program already makes: the contract is generated from
its source, an operation *is* the CLI command rather than a description of one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2.confidence import VERIFICATION_STATUS_ADJ           # noqa: E402
from fcf_m2.observed import (                                    # noqa: E402
    CAPACITY_COLUMNS, CAPACITY_METHOD_PRECEDENCE, METHOD_TO_BASIS, SESSION_COLUMNS,
)

OUT = REPO / "site/platform/field_schema.json"

#: The rule vocabulary both interpreters understand. Kept deliberately tiny - every entry is
#: a rule that exists in ``observed.py``'s ``__post_init__``, and nothing here is a rule the
#: model does not enforce. Adding a rule the model lacks would make the form lie about what
#: will be accepted.
#:
#:   non_empty        field must be non-blank after trimming
#:   at_least_one_of  at least one of the named fields must be present
#:   non_negative     if present, must be a finite number >= 0
#:   positive         must be a finite number > 0
#:   not_greater_than must be <= the named field
#:   enum             must be one of the listed values


def capacity_form() -> dict:
    return {
        "id": "capacity",
        "label": "Electrical capacity confirmation",
        "explains": (
            "One confirmation of a site's electrical service. This is the observation that can "
            "move a site off the placeholder capacity every site currently carries."
        ),
        "csv_columns": CAPACITY_COLUMNS,
        "fields": [
            {"name": "site_id", "label": "Site", "type": "site", "required": True},
            {"name": "observed_date", "label": "Date observed", "type": "date", "required": True},
            {"name": "method", "label": "How it was established", "type": "enum",
             "required": True, "values": CAPACITY_METHOD_PRECEDENCE,
             "value_notes": {m: f"establishes at most: {b}" for m, b in METHOD_TO_BASIS.items()},
             "help": ("Ordered strongest first. The method caps how strong a claim the value "
                      "can support - it can never establish more than what is listed.")},
            {"name": "service_capacity_kw", "label": "Service capacity (kW)", "type": "number",
             "required": False},
            {"name": "spare_capacity_kw", "label": "Spare capacity (kW)", "type": "number",
             "required": False},
            {"name": "measured_peak_kw", "label": "Measured peak (kW)", "type": "number",
             "required": False},
            {"name": "source_org", "label": "Source organisation", "type": "text", "required": True},
            {"name": "source_document", "label": "Source document", "type": "text",
             "required": True,
             "help": "Name the document or record. An observation nobody can trace back cannot "
                     "upgrade anything, so this is refused rather than accepted and ignored."},
            {"name": "observer", "label": "Observed by", "type": "text", "required": True},
            {"name": "verification_status", "label": "Verification status", "type": "enum",
             "required": True, "values": sorted(VERIFICATION_STATUS_ADJ),
             "default": "reviewed"},
            {"name": "notes", "label": "Notes", "type": "textarea", "required": False},
        ],
        "rules": [
            {"rule": "non_empty", "field": "source_document",
             "message": "An observation with no source document cannot establish provenance, "
                        "so it cannot upgrade capacity_basis."},
            {"rule": "non_empty", "field": "observer",
             "message": "An observation with no observer cannot establish provenance, so it "
                        "cannot upgrade capacity_basis."},
            {"rule": "at_least_one_of",
             "fields": ["service_capacity_kw", "spare_capacity_kw"],
             "message": "This row carries neither service capacity nor spare capacity, so "
                        "there is nothing to confirm."},
            {"rule": "non_negative", "field": "service_capacity_kw",
             "message": "Service capacity must be a finite value of 0 kW or more."},
            {"rule": "non_negative", "field": "spare_capacity_kw",
             "message": "Spare capacity must be a finite value of 0 kW or more."},
            {"rule": "non_negative", "field": "measured_peak_kw",
             "message": "Measured peak must be a finite value of 0 kW or more."},
            {"rule": "enum", "field": "method", "values": sorted(METHOD_TO_BASIS),
             "message": "Unknown method."},
            {"rule": "enum", "field": "verification_status",
             "values": sorted(VERIFICATION_STATUS_ADJ),
             "message": "Unknown verification status."},
        ],
    }


def session_form() -> dict:
    return {
        "id": "session",
        "label": "Charger operating day",
        "explains": (
            "One site-day of charger operation. Enough of these make a site's expansion "
            "trigger evaluable instead of unanswerable."
        ),
        "csv_columns": SESSION_COLUMNS,
        "fields": [
            {"name": "site_id", "label": "Site", "type": "site", "required": True},
            {"name": "date", "label": "Date", "type": "date", "required": True},
            {"name": "sessions", "label": "Charging sessions", "type": "number", "required": True},
            {"name": "energy_kwh", "label": "Energy delivered (kWh)", "type": "number",
             "required": True},
            {"name": "mean_dwell_min", "label": "Mean dwell (minutes)", "type": "number",
             "required": True},
            {"name": "ports_in_service", "label": "Ports in service", "type": "integer",
             "required": True},
            {"name": "port_hours_available", "label": "Port-hours available", "type": "number",
             "required": True},
            {"name": "port_hours_possible", "label": "Port-hours possible", "type": "number",
             "required": True,
             "help": "Ports in service × hours in the day. Availability cannot exceed this."},
            {"name": "facility_visitors_day", "label": "Facility visitors", "type": "number",
             "required": False},
            {"name": "sessions_delayed", "label": "Sessions delayed", "type": "integer",
             "required": False},
            {"name": "wait_p90_min", "label": "90th-percentile wait (min)", "type": "number",
             "required": False},
            {"name": "observer", "label": "Observed by", "type": "text", "required": False},
            {"name": "source_system", "label": "Source system", "type": "text", "required": False},
        ],
        "rules": [
            {"rule": "positive", "field": "ports_in_service",
             "message": "Ports in service must be greater than zero."},
            {"rule": "positive", "field": "port_hours_possible",
             "message": "Port-hours possible must be greater than zero."},
            {"rule": "not_greater_than", "field": "port_hours_available",
             "than": "port_hours_possible",
             "message": "Port-hours available exceeds port-hours possible; uptime cannot "
                        "exceed 1."},
            {"rule": "non_negative", "field": "sessions",
             "message": "Sessions must be zero or more."},
            {"rule": "non_negative", "field": "energy_kwh",
             "message": "Energy must be zero or more."},
            {"rule": "non_negative", "field": "mean_dwell_min",
             "message": "Mean dwell must be zero or more."},
        ],
    }


def build() -> dict:
    return {
        "generated_by": "scripts/build_field_schema.py",
        "source_of_truth": "src/fcf_m2/observed.py",
        "note": ("Generated from the model's own refusals. The browser interprets these rules; "
                 "it does not restate them. Parity is asserted by "
                 "tests/test_field_schema_parity.py."),
        "method_to_basis": METHOD_TO_BASIS,
        "forms": [capacity_form(), session_form()],
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    forms = ", ".join(f"{f['id']} ({len(f['fields'])} fields, {len(f['rules'])} rules)"
                      for f in payload["forms"])
    print(f"wrote {OUT.relative_to(REPO)}  - {forms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
