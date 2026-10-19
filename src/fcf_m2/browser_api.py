"""The planning platform's door into the engine: JSON in, JSON out, nothing else.

The platform (`platform/app/`) runs this package unmodified inside the planner's browser, under
Pyodide in a Web Worker. This module is the only thing the worker calls. It holds one planner
session at a time (the uploaded table, the proposal, the accepted cohort and the last run) in
the in-memory file system, and every function takes and returns a JSON string so the boundary
between JavaScript and Python carries plain data and nothing that could drift.

It adds no model logic. Each call is a thin wrapper over what the command line already does:

    propose   ->  intake.propose            (what intake WOULD do; changes nothing)
    remap     ->  the same checks, on a mapping the planner chose (DEC-023)
    accept    ->  intake.apply + provenance_rows + accept, written as a cohort directory
    run       ->  workflow.run("milestone2_v3", cohort_dir=...), never without a cohort
    explain   ->  the score broken into the weights scoring.py already uses
    provenance -> provenance.resolve, for the one cell the planner opens
    fill      ->  values the planner accepted from the public data hub, for cells their file
                  left empty, recorded with their source (applied by `accept`)

Two rules carry over from intake and matter more here, where no one reads a terminal:

* **Never run without a cohort.** `workflow.run` with no cohort reads the reference study's
  private inputs (DEC-016). The browser bundle does not ship them, and this module refuses to
  ask.
* **Never improve the data silently.** A mapping the planner chose is still a mapping, not a
  source: provenance is written exactly as `workflow intake --accept` writes it (DEC-021). A
  value from the public data hub reaches the model only through `fill`, which the planner calls
  field by field after seeing every value, and it is recorded as derived public data with its
  dataset, vintage and hub release (DEC-025). This module never fetches anything: the browser
  computes the values from the hub's county packs and hands them over.

The protocol this implements is `platform/PROTOCOL.md`; its version is `PROTOCOL_VERSION`.
"""

from __future__ import annotations

import json
import math
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from . import intake
from .scoring import (DRIVER_WEIGHTS, INVERTED_DRIVERS, NUMERIC_FIELDS, SUBSCORE_WEIGHTS,
                      YES_NO_FIELDS)

PROTOCOL_VERSION = 2

#: The engine's own field groups, in the planner's words.
GROUP_LABELS = {
    "address_and_public_access": "Identity and Access",
    "coordinates": "Location",
    "electrical_service": "Electrical Service",
    "equity_and_context": "Surroundings and Equity",
    "parking_and_layout": "Parking and Layout",
    "safety_review_fields": "Safety Review",
    "site_use_and_demand": "How the Site Is Used",
}

#: One entry per canonical field: a short label, the unit, what it is and what happens when it
#: is missing. The last three are `docs/INPUT_SCHEMA.md`'s field table, word for word, and
#: tests/test_browser_api.py fails if the two drift apart.
FIELDS: list[dict[str, str]] = [
    {"name": "site_id", "label": "Site ID", "unit": "identifier", "what": "A unique, stable identifier for the site. Letters, digits, '.', '_' and '-'.", "if_missing": "the file is refused"},
    {"name": "site_name", "label": "Site Name", "unit": "text", "what": "Display name. Not a model input.", "if_missing": "the site_id is shown instead"},
    {"name": "site_type", "label": "Site Type", "unit": "text", "what": "What the building is, e.g. library, office, recreation, garage. A type containing 'garage' is routed to fire/AHJ review before any normal buildout.", "if_missing": "'unspecified'"},
    {"name": "lat", "label": "Latitude", "unit": "degrees", "what": "Latitude, WGS84 decimal degrees. Projected coordinates are refused, never converted.", "if_missing": "the map surfaces are unavailable; nothing else changes"},
    {"name": "lon", "label": "Longitude", "unit": "degrees", "what": "Longitude, WGS84 decimal degrees.", "if_missing": "the map surfaces are unavailable; nothing else changes"},
    {"name": "employees_day", "label": "Staff per Day", "unit": "people/day", "what": "Staff on site on a typical day. Drives expected charging sessions, not the score.", "if_missing": "counts as 0 expected sessions from staff"},
    {"name": "visitors_day", "label": "Visitors per Day", "unit": "people/day", "what": "Visitors on a typical day. Drives expected charging sessions, not the score.", "if_missing": "counts as 0 expected sessions from visitors"},
    {"name": "fleet_vehicles", "label": "Fleet Vehicles", "unit": "vehicles", "what": "Fleet vehicles based at the site. Read and carried, not used.", "if_missing": "nothing changes"},
    {"name": "parking_spaces", "label": "Parking Spaces", "unit": "spaces", "what": "Parking spaces at the site. Also caps the port plan at 5% of spaces (2 to 12).", "if_missing": "earns no credit, and the port plan is capped at 2"},
    {"name": "hours_open", "label": "Hours Open per Day", "unit": "hours/day", "what": "Hours the site is open on a typical day. A '_min' column is recognised and converted.", "if_missing": "earns no credit; port sizing assumes 8 hours"},
    {"name": "avg_dwell_min", "label": "Average Visit Length", "unit": "minutes", "what": "Average length of a visit. An '_hr' or '_sec' column is recognised and converted.", "if_missing": "earns no credit; port sizing assumes 120 minutes"},
    {"name": "nearby_households_1mi", "label": "Households Within 1 Mile", "unit": "households", "what": "Households within 1 mile.", "if_missing": "earns no credit in the score"},
    {"name": "nearby_jobs_1mi", "label": "Jobs Within 1 Mile", "unit": "jobs", "what": "Jobs within 1 mile.", "if_missing": "earns no credit in the score"},
    {"name": "aadt_nearest", "label": "Daily Traffic Nearby", "unit": "vehicles/day", "what": "Annual average daily traffic on the nearest arterial.", "if_missing": "earns no credit in the score"},
    {"name": "amenities_count_0_5mi", "label": "Amenities Within Half a Mile", "unit": "count", "what": "Amenities (shops, services) within half a mile.", "if_missing": "earns no credit in the score"},
    {"name": "ev_share_local", "label": "Local EV Share", "unit": "fraction", "what": "Share of locally registered vehicles that are electric, as a fraction: 0.03 means 3%.", "if_missing": "earns no credit in the score"},
    {"name": "existing_l2_ports_1mi", "label": "Level 2 Ports Within 1 Mile", "unit": "ports", "what": "Public Level 2 charging ports already within 1 mile. Lower is better.", "if_missing": "earns no credit in the score"},
    {"name": "existing_dcfc_ports_3mi", "label": "DC Fast Ports Within 3 Miles", "unit": "ports", "what": "Public DC fast charging ports already within 3 miles. Lower is better.", "if_missing": "earns no credit in the score"},
    {"name": "equity_gap_index", "label": "Equity Need", "unit": "index 0-1", "what": "Charging-equity need, 0 (least) to 1 (most underserved).", "if_missing": "earns no credit; the contract's equity_indicator is left empty"},
    {"name": "spare_capacity_kw", "label": "Spare Electrical Capacity", "unit": "kW", "what": "Spare electrical capacity at the service. Used in the score, but the contract reports capacity as a placeholder until a utility or facility confirms it. Watts and megawatts are recognised and converted.", "if_missing": "earns no credit in the score"},
    {"name": "distance_to_service_ft", "label": "Distance to Electrical Service", "unit": "feet", "what": "Distance from the parking area to the electrical service. Lower is better. Metres are recognised and converted.", "if_missing": "earns no credit in the score"},
    {"name": "trenching_ft", "label": "Trenching Needed", "unit": "feet", "what": "Trenching needed. Lower is better. Metres are recognised and converted.", "if_missing": "earns no credit, and the site gets no cost figures"},
    {"name": "trench_cost_per_ft", "label": "Trenching Cost per Foot", "unit": "USD/foot", "what": "Trenching cost per foot.", "if_missing": "the install-cost term earns no credit, and the site gets no cost figures"},
    {"name": "service_upgrade_cost_usd", "label": "Service Upgrade Cost", "unit": "USD", "what": "Cost of upgrading the electrical service. Lower is better.", "if_missing": "earns no credit, and the site gets no cost figures"},
    {"name": "elec_service_rating_amp", "label": "Service Rating", "unit": "amps", "what": "Rating of the electrical service. Read and carried, not used.", "if_missing": "nothing changes"},
    {"name": "public_access", "label": "Open to the Public", "unit": "yes/no", "what": "Is the site open to the public?", "if_missing": "treated as not public: demand counts at 65%, the 'Low public-priority' tier, and every port target held to 2"},
    {"name": "ada_layout_possible", "label": "ADA Layout Possible", "unit": "yes/no", "what": "Can an ADA-accessible charging layout be built?", "if_missing": "earns no credit in the score"},
    {"name": "fire_access_ok", "label": "Fire Access Adequate", "unit": "yes/no", "what": "Is fire-service access adequate?", "if_missing": "earns no credit in the score"},
    {"name": "garage_enclosed", "label": "Enclosed Garage", "unit": "yes/no", "what": "Is the parking an enclosed garage? Yes lowers the safety score.", "if_missing": "earns no safety credit, and the site is a 'High-review candidate'"},
    {"name": "emergency_disconnect_visible", "label": "Emergency Disconnect Visible", "unit": "yes/no", "what": "Is an emergency disconnect visible from the charging area?", "if_missing": "earns no credit in the score"},
    {"name": "stormwater_risk", "label": "Stormwater Risk", "unit": "yes/no", "what": "Is there a stormwater or flooding risk? Yes lowers the safety score.", "if_missing": "earns no safety credit"},
    {"name": "battery_storage_flag", "label": "Battery Storage on Site", "unit": "yes/no", "what": "Is battery storage on site? Read and carried, not used.", "if_missing": "nothing changes"},
]

SUBSCORE_LABELS = {
    "demand_subscore": "Demand",
    "feasibility_subscore": "Feasibility",
    "safety_subscore": "Safety",
    "equity_subscore": "Equity",
}

#: The normalised terms the formula reads, named for the planner. `existing_ports_total` and
#: `install_cost_est_usd` are the engine's own sums of supplied fields.
DRIVER_LABELS = {
    "nearby_households_1mi_n": "Households within 1 mile",
    "nearby_jobs_1mi_n": "Jobs within 1 mile",
    "aadt_nearest_n": "Daily traffic nearby",
    "amenities_count_0_5mi_n": "Amenities within half a mile",
    "parking_spaces_n": "Parking spaces",
    "hours_open_n": "Hours open",
    "avg_dwell_min_n": "Visit length",
    "ev_share_local_n": "Local EV share",
    "existing_ports_total_n": "Existing chargers nearby",
    "spare_capacity_kw_n": "Spare electrical capacity",
    "distance_to_service_ft_n": "Distance to electrical service",
    "install_cost_est_usd_n": "Estimated install cost",
    "trenching_ft_n": "Trenching needed",
    "ada_layout_possible": "ADA layout possible",
    "fire_access_ok": "Fire access adequate",
    "garage_enclosed": "Enclosed garage",
    "emergency_disconnect_visible": "Emergency disconnect visible",
    "stormwater_risk": "Stormwater risk",
    "equity_gap_index_n": "Equity need",
}

#: The supplied fields a driver is built from, so a driver can say which input it is missing.
DRIVER_INPUTS = {
    "existing_ports_total_n": ["existing_l2_ports_1mi", "existing_dcfc_ports_3mi"],
    "install_cost_est_usd_n": ["trenching_ft", "trench_cost_per_ft", "service_upgrade_cost_usd"],
}

#: The fields intake reads as values, and so checks and notes when absent (its own rule).
_SCORED = set(NUMERIC_FIELDS) | set(YES_NO_FIELDS)

#: The fields the readiness score actually uses: every driver's inputs, plus public access,
#: which scales demand. Staff, visitors, fleet, service rating and battery storage are read but
#: not scored, as docs/INPUT_SCHEMA.md's "In the score" column says.
_IN_SCORE = {"public_access"} | {
    i for weights in DRIVER_WEIGHTS.values() for d in weights
    for i in DRIVER_INPUTS.get(d, [d[:-2] if d.endswith("_n") else d])}

#: Fields public data can describe: the site's surroundings, never the site itself (its
#: parking, wiring or safety review). The hub fills some of them; `fill` accepts only these.
PUBLIC_FILL_FIELDS = [f for f in NUMERIC_FIELDS
                      if intake.FIELD_GROUP_FOR_INPUT[f] == "equity_and_context"]
#: Of those, the fields whose unit is a share, which cannot exceed 1.
_UNIT_INTERVAL = {"ev_share_local", "equity_gap_index"}
_FILL_SOURCE_KEYS = ("hubVersion", "dataset", "title", "vintage", "sourceDate", "licence", "method")


class _Session:
    """Everything one planner has open. Replaced whole by `reset`."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="evsient-"))
        self.frame: pd.DataFrame | None = None
        self.file_name = ""
        self.proposal: intake.Proposal | None = None
        self.cohort_dir: Path | None = None
        self.out_dir: Path | None = None
        self.results: pd.DataFrame | None = None
        self.contract: Any = None             # the last run's provenance.ContractIndex
        #: Public data the planner accepted (see `fill`); cleared by a new file or mapping.
        self.fills: list[dict] = []


_session = _Session()


# ---------- helpers ----------

def _clean(value: Any) -> Any:
    """Make a value JSON-safe: NaN and NA become null, numpy scalars become Python ones."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return _clean(value.item())
        except (ValueError, AttributeError):
            pass
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def _out(payload: dict) -> str:
    return json.dumps(_clean(payload), allow_nan=False)


def _frame_from(table: dict) -> pd.DataFrame:
    """The uploaded table, every cell kept as the text the planner typed.

    The same rule as `workflow intake`'s `read_csv(dtype=object, keep_default_na=False)`: a
    value is never re-typed on the way in, so "n/a" reaches intake as "n/a" and is reported.
    """
    columns = [str(c) for c in table["columns"]]
    if len(set(columns)) != len(columns):
        raise ValueError("Two columns in this file have the same name. Rename one and upload it again.")
    rows = [["" if cell is None else str(cell) for cell in row] for row in table["rows"]]
    width = len(columns)
    rows = [(row + [""] * width)[:width] for row in rows]
    return pd.DataFrame(rows, columns=columns, dtype=object)


def _column_summaries(frame: pd.DataFrame) -> list[dict]:
    out = []
    for column in frame.columns:
        values = [str(v) for v in frame[column].tolist()]
        filled = [v for v in values if v.strip() != ""]
        samples: list[str] = []
        for v in filled:
            if v not in samples:
                samples.append(v)
            if len(samples) == 5:
                break
        out.append({"name": column, "samples": samples, "blank": len(values) - len(filled),
                    "distinct": len(set(filled))})
    return out


def _match_scores(frame: pd.DataFrame, mapping: dict[str, str]) -> dict[str, float]:
    """The confidence intake would give each mapped pair, by the same rule `propose` uses."""
    scores = {}
    for canonical, column in mapping.items():
        bare_column = intake._strip_units(column)
        bare_canonical = intake._strip_units(canonical)
        score = max(
            intake._similarity(bare_canonical, bare_column),
            max((intake._similarity(intake._strip_units(a), bare_column)
                 for a in intake.ALIASES.get(canonical, [])), default=0.0))
        if intake._normalise(column) == intake._normalise(canonical) or bare_column == bare_canonical:
            score = 1.0
        scores[canonical] = round(score, 4)
    return scores


def _proposal_payload(proposal: intake.Proposal, frame: pd.DataFrame,
                      chosen: set[str] | None = None) -> dict:
    scores = _match_scores(frame, proposal.mapping)
    chosen = chosen or set()
    status = {}
    for f in FIELDS:
        name = f["name"]
        if name not in proposal.mapping:
            status[name] = "unmatched"
        elif name in chosen or (scores.get(name, 0) >= 1.0 and name not in proposal.conversions):
            status[name] = "matched"
        else:
            status[name] = "check"
    return {
        "rowCount": proposal.row_count,
        "columns": _column_summaries(frame),
        "mapping": dict(proposal.mapping),
        "conversions": dict(proposal.conversions),
        "matchScore": scores,
        "status": status,
        "absent": list(proposal.absent),
        "findings": [vars(f) for f in proposal.findings],
        "refused": proposal.refused,
        "completeness": proposal.completeness,
        "summary": proposal.summary(),
    }


def _applied() -> pd.DataFrame:
    """The canonical frame intake would materialise now, with site IDs as the model reads them."""
    applied, _ = intake.apply(_session.frame, _session.proposal)
    applied["site_id"] = applied["site_id"].astype(str).str.strip()
    return applied


def _filled_at() -> dict[str, dict[str, float]]:
    """{field: {site_id: value}} for every public value the planner accepted."""
    return {f["field"]: f["values"] for f in _session.fills}


def _apply_fills(applied: pd.DataFrame, ledger: list) -> tuple[dict, list[dict]]:
    """Write the accepted public values into the empty cells they fill, and say so.

    Returns the per-site sources `intake.provenance_rows` reads, and one row per filled cell for
    `public_data_fills.csv`.
    """
    position = {sid: i for i, sid in enumerate(applied["site_id"])}
    sources: dict[str, dict[str, dict[str, str]]] = {}
    cells = []
    for fill in _session.fills:
        field, src = fill["field"], fill["source"]
        org = f"EV-SIENT public data hub {src['hubVersion']}: {src['title']}"
        note = f"{src['title']}, {src['vintage']}"
        # A field the file lacked is an all-NA column; as numbers it writes the same empty cells.
        column = pd.to_numeric(applied[field], errors="coerce").astype("float64")
        for site_id, value in fill["values"].items():
            column.iloc[position[site_id]] = value
            sources.setdefault(field, {})[site_id] = {"source_org": org, "source_date": src["sourceDate"],
                                                      "note": note}
            cells.append({"site_id": site_id, "field": field, "value": value, "dataset": src["dataset"],
                          "title": src["title"], "vintage": src["vintage"], "source_date": src["sourceDate"],
                          "licence": src["licence"], "hub_version": src["hubVersion"],
                          "method": src["method"], "url": src.get("url", "")})
        applied[field] = column
        ledger.append(intake.LedgerEntry(
            field, f"filled from public data ({len(fill['values'])} cell(s))",
            f"empty in the file; the planner accepted values from {src['title']} ({src['vintage']}), "
            f"public data hub {src['hubVersion']}: {src['method']}",
            detail="site(s) " + ", ".join(sorted(fill["values"]))))
    return sources, cells


# ---------- protocol ----------

def info() -> str:
    """What is loaded, for the about panel and the project file's manifest."""
    import platform
    import sys

    import numpy
    from importlib import metadata
    packages = {"pandas": pd.__version__, "numpy": numpy.__version__}
    try:
        # jsonschema.__version__ is deprecated and warns on every boot; the metadata is not.
        packages["jsonschema"] = metadata.version("jsonschema")
    except metadata.PackageNotFoundError:
        pass
    return _out({
        "protocol": PROTOCOL_VERSION,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
    })


def fields() -> str:
    """The canonical fields, grouped, with what each is and what its absence costs."""
    out = []
    for f in FIELDS:
        name = f["name"]
        group = intake.FIELD_GROUP_FOR_INPUT[name]
        kind = ("flag" if name in YES_NO_FIELDS else "coordinate" if name in ("lat", "lon")
                else "number" if name in NUMERIC_FIELDS else "text")
        out.append({**f, "group": group, "groupLabel": GROUP_LABELS[group], "kind": kind,
                    "scored": name in _IN_SCORE, "required": name == "site_id"})
    return _out({"fields": out, "groups": GROUP_LABELS})


def reset() -> str:
    global _session
    _session = _Session()
    return _out({"ok": True})


def propose(table_json: str) -> str:
    """Read an uploaded table and say what intake would do with it. Changes nothing."""
    table = json.loads(table_json)
    frame = _frame_from(table)
    proposal = intake.propose(frame)
    _session.frame, _session.file_name, _session.proposal = frame, table.get("fileName", ""), proposal
    _session.cohort_dir = _session.out_dir = None
    _session.results = None
    _session.fills = []
    return _out(_proposal_payload(proposal, frame))


def remap(mapping_json: str) -> str:
    """Apply the planner's choices to the mapping and run every check again (DEC-023).

    The input is `{"mapping": {canonical: column or null}}`, the WHOLE mapping as the planner
    now wants it. Unit conversions are re-detected from the chosen column's name exactly as
    `propose` detects them, so choosing `trench_length_m` still converts metres to feet and
    says so. A field set to null is absent. The planner's choice clears the "is this a guess"
    question but not where the numbers came from: provenance still records a renamed column as
    inferred from its name (DEC-021).
    """
    if _session.frame is None:
        raise ValueError("Upload a file first.")
    request = json.loads(mapping_json)
    wanted: dict[str, str | None] = request.get("mapping", {})
    frame = _session.frame
    known = {f["name"] for f in FIELDS}
    columns = set(frame.columns)
    used: dict[str, str] = {}
    for canonical, column in wanted.items():
        if canonical not in known:
            raise ValueError(f"{canonical} is not a field this model reads.")
        if column is None:
            continue
        if column not in columns:
            raise ValueError(f"The column '{column}' is not in this file.")
        if column in used:
            raise ValueError(f"The column '{column}' is chosen for both {used[column]} and "
                             f"{canonical}. Choose it for one field only.")
        used[column] = canonical

    proposal = intake.Proposal(row_count=len(frame))
    for f in FIELDS:
        canonical = f["name"]
        column = wanted.get(canonical)
        if column is None:
            proposal.absent.append(canonical)
            continue
        proposal.mapping[canonical] = column
        conversion = intake._detect_conversion(canonical, column)
        if conversion:
            factor, unit = conversion
            proposal.conversions[canonical] = factor
            proposal.findings.append(intake.Finding(
                "warning", canonical,
                f"{canonical} appears to be supplied in {unit} and every value will be "
                f"multiplied by {factor:g} to reach the unit the model expects.",
                detail=f"from column '{column}'"))
    for canonical in proposal.absent:
        if canonical in _SCORED:
            consequence = intake.ABSENCE_CONSEQUENCE.get(
                canonical, " rather than being substituted with a default")
            proposal.findings.append(intake.Finding(
                "note", canonical,
                f"{canonical} is not present in this file, so it will be scored as an absence "
                f"and will lower this jurisdiction's data confidence{consequence}."))
    intake._check_identity(frame, proposal)
    intake._check_coordinates(frame, proposal)
    intake._check_values(frame, proposal)
    proposal.findings.sort(key=lambda f: (intake.SEVERITY_ORDER[f.severity], f.field))
    _session.proposal = proposal
    _session.cohort_dir = _session.out_dir = None
    _session.results = None
    # A new mapping can change which cells are empty, so earlier public values no longer apply.
    _session.fills = []
    return _out(_proposal_payload(proposal, frame, chosen=set(proposal.mapping)))


def check() -> str:
    """Row by row: which sites are ready, which have missing values, and why any must be fixed.

    Each row also carries the site's coordinates as the model reads them (for the public data
    step, which works its values out in the browser) and the fields filled there from public
    data, which no longer count as missing.
    """
    frame, proposal = _session.frame, _session.proposal
    if frame is None or proposal is None:
        raise ValueError("Upload a file first.")
    refusals = [vars(f) for f in proposal.findings if f.severity == "refusal"]
    rows = []
    id_column = proposal.mapping.get("site_id")
    if proposal.refused:
        applied = None
    else:
        applied, _ = intake.apply(frame, proposal)
    ids = frame[id_column].astype(str).str.strip().tolist() if id_column else [""] * len(frame)
    duplicated = pd.Series(ids).duplicated(keep=False).tolist()
    filled_at = _filled_at()
    for i in range(len(frame)):
        must_fix = []
        if not id_column or ids[i] in ("", "nan", "None"):
            must_fix.append("This row has no site identifier.")
        elif duplicated[i]:
            must_fix.append(f"The site identifier '{ids[i]}' appears more than once.")
        missing, lat, lon = [], None, None
        filled = [f["name"] for f in FIELDS if ids[i] in filled_at.get(f["name"], {})]
        if applied is not None:
            missing = [f["name"] for f in FIELDS
                       if f["name"] in _SCORED and f["name"] in proposal.mapping
                       and f["name"] not in filled
                       and pd.isna(applied[f["name"]].iloc[i])]
            lat, lon = applied["lat"].iloc[i], applied["lon"].iloc[i]
        name_column = proposal.mapping.get("site_name")
        rows.append({
            "row": i + 2,
            "siteId": ids[i],
            "siteName": str(frame[name_column].iloc[i]) if name_column else "",
            "status": "must_fix" if must_fix else ("missing" if missing else "ready"),
            "mustFix": must_fix,
            "missing": missing,
            "filled": filled,
            "lat": None if pd.isna(lat) else float(lat),
            "lon": None if pd.isna(lon) else float(lon),
        })
    absent_scored = [name for name in proposal.absent if name in _SCORED]
    located = 0
    if applied is not None:
        located = int((applied["lat"].notna() & applied["lon"].notna()).sum())
    return _out({
        "rows": rows,
        "refusals": refusals,
        "counts": {
            "total": len(rows),
            "ready": sum(r["status"] == "ready" for r in rows),
            "missing": sum(r["status"] == "missing" for r in rows),
            "mustFix": sum(r["status"] == "must_fix" for r in rows),
            "located": located,
        },
        "absentFromFile": absent_scored,
        "publicFill": {
            "fields": PUBLIC_FILL_FIELDS,
            "filled": {f["field"]: len(f["values"]) for f in _session.fills},
            "sources": {f["field"]: f["source"] for f in _session.fills},
        },
    })


def fill(fills_json: str) -> str:
    """Record the public values the planner accepted, then check every row again.

    The input is `{"fills": [{"field", "values": {site_id: number}, "source": {...}}]}`, the
    WHOLE set as the planner now wants it (an empty list removes them all). Each `source` names
    the hub release, dataset, title, vintage, sourceDate (YYYY-MM-DD), licence and method, and
    is written beside every value. Nothing reaches the model until `accept`.

    A value is taken only where the planner's file has none: a field the file lacks, or a cell
    it left empty or unreadable. A public value never replaces the planner's own (DEC-021), and
    only fields about a site's surroundings can be filled (`PUBLIC_FILL_FIELDS`).
    """
    frame, proposal = _session.frame, _session.proposal
    if frame is None or proposal is None:
        raise ValueError("Upload a file first.")
    if proposal.refused:
        raise ValueError("Fix the items marked Must Fix before filling values from public data.")
    request = json.loads(fills_json or "{}")
    applied = _applied()
    position = {sid: i for i, sid in enumerate(applied["site_id"])}
    fills, seen = [], set()
    for item in request.get("fills", []):
        field = item.get("field")
        if field not in PUBLIC_FILL_FIELDS:
            raise ValueError(f"{field} cannot be filled from public data; only a site's surroundings can.")
        if field in seen:
            raise ValueError(f"{field} is listed twice. Send each field once.")
        seen.add(field)
        source = item.get("source") or {}
        lacking = [k for k in _FILL_SOURCE_KEYS if not str(source.get(k) or "").strip()]
        if lacking:
            raise ValueError(f"The public values for {field} do not say their {', '.join(lacking)}, "
                             f"so they cannot be recorded.")
        try:
            date.fromisoformat(str(source["sourceDate"]))
        except ValueError:
            raise ValueError(f"The source date for {field} is not a date (YYYY-MM-DD).") from None
        values = item.get("values") or {}
        if not values:
            raise ValueError(f"No values were given for {field}.")
        clean: dict[str, float] = {}
        for site_id, value in values.items():
            site_id = str(site_id).strip()
            if site_id not in position:
                raise ValueError(f"There is no site {site_id} in this file.")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"The public value for {field} at {site_id} is not a number.")
            if value < 0 or (field in _UNIT_INTERVAL and value > 1):
                raise ValueError(f"The public value for {field} at {site_id} is out of range.")
            if not pd.isna(applied[field].iloc[position[site_id]]):
                raise ValueError(f"Your file already has a value for {field} at {site_id}. Public data "
                                 f"never replaces your own values.")
            clean[site_id] = float(value)
        fills.append({"field": field, "values": clean,
                      "source": {k: str(v) for k, v in source.items() if isinstance(v, (str, int, float))}})
    _session.fills = fills
    _session.cohort_dir = _session.out_dir = None
    _session.results = None
    return check()


def accept(details_json: str) -> str:
    """Write the accepted cohort, exactly as `workflow intake --accept` would.

    `details` carries `jurisdiction`, `sourceOrg` and `sourceDate` (YYYY-MM-DD or empty), all
    optional, and `reviewer` for the provenance trail.

    Public values the planner accepted (`fill`) are written into the cells they fill, each with a
    ledger entry, `derived_public_data` provenance at its site, and a row in
    `public_data_fills.csv` naming its dataset, vintage and hub release. With none, the cohort
    is exactly what `workflow intake --accept` writes.
    """
    from . import contract

    frame, proposal = _session.frame, _session.proposal
    if frame is None or proposal is None:
        raise ValueError("Upload a file first.")
    if proposal.refused:
        raise ValueError("This file cannot be run until every item marked Must Fix is fixed.")
    details = json.loads(details_json or "{}")
    applied, ledger = intake.apply(frame, proposal)
    applied["site_id"] = applied["site_id"].astype(str).str.strip()
    site_ids = list(applied["site_id"])
    public_sources, public_cells = _apply_fills(applied, ledger)
    source_date = (details.get("sourceDate") or "").strip() or "unstated"
    stem = Path(_session.file_name or "uploaded").stem
    source_org = (details.get("sourceOrg") or "").strip() or stem
    jurisdiction = (details.get("jurisdiction") or "").strip() or stem
    provenance = intake.accept(intake.provenance_rows(
        proposal, site_ids, reviewer=details.get("reviewer") or "planner, in the platform",
        source_org=source_org, source_date=source_date, applied=applied,
        public_fills=public_sources or None))

    cohort = _session.root / "cohort"
    if cohort.exists():
        import shutil
        shutil.rmtree(cohort)
    cohort.mkdir(parents=True)
    applied.to_csv(cohort / "sites.csv", index=False)
    provenance.to_csv(cohort / "provenance.csv", index=False)
    pd.DataFrame([vars(e) for e in ledger]).to_csv(cohort / "intake_ledger.csv", index=False)
    (cohort / "intake_findings.json").write_text(json.dumps([vars(f) for f in proposal.findings], indent=2))
    if public_cells:
        pd.DataFrame(public_cells).to_csv(cohort / "public_data_fills.csv", index=False)
    source = cohort / "source_upload.csv"
    frame.to_csv(source, index=False)
    from .workflow import _slug
    (cohort / "cohort.json").write_text(json.dumps({
        "schema": "fcf-cohort/1",
        "cohort_id": _slug(details.get("cohortId") or jurisdiction),
        "jurisdiction": _slug(jurisdiction),
        "source_date": source_date,
        "source_org": source_org,
        "source_file": _session.file_name,
        "source_sha256": contract.sha256_file(source),
        "accepted_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    source.unlink()
    _session.cohort_dir = cohort
    _session.out_dir = None
    _session.results = None
    return _out({
        "siteCount": len(site_ids),
        "ledger": [vars(e) for e in ledger],
        "summary": proposal.summary(),
        "publicCells": len(public_cells),
    })


def run(options_json: str = "{}") -> str:
    """Run the model on the accepted cohort and return what the results screens need."""
    from . import workflow

    if _session.cohort_dir is None:
        # Never fall through to workflow.run without a cohort: that reads the reference
        # study's private inputs (DEC-016).
        raise ValueError("Accept the checked file before running the model.")
    options = json.loads(options_json or "{}")
    out = _session.root / "run"
    if out.exists():
        import shutil
        shutil.rmtree(out)
    started = datetime.now(timezone.utc)
    kwargs: dict[str, Any] = {"cohort_dir": _session.cohort_dir}
    as_of = options.get("asOf")
    if as_of:
        kwargs["as_of"] = date.fromisoformat(as_of)
    summary = workflow.run("milestone2_v3", out, **kwargs)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    _session.out_dir = out
    _session.contract = None

    results = pd.read_csv(out / "site_results_milestone2_v3.csv", dtype={"site_id": str})
    confidence = pd.read_csv(out / "data_confidence_v3.csv", dtype={"site_id": str})
    sizing = pd.read_csv(out / "right_sizing_v3_canonical.csv", dtype={"site_id": str})
    _session.results = results

    conf_by = confidence.set_index("site_id")
    base = sizing[(sizing["horizon_year"] == sizing["horizon_year"].min()) & (sizing["case"] == "baseline")]
    base_by = base.set_index("site_id")
    sites = []
    for _, row in results.sort_values("model_rank").iterrows():
        sid = row["site_id"]
        c = conf_by.loc[sid] if sid in conf_by.index else None
        breakdown = {}
        if c is not None and isinstance(c["confidence_breakdown"], str):
            for part in c["confidence_breakdown"].split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    breakdown[k] = float(v)
        b = base_by.loc[sid] if sid in base_by.index else None
        absent = [a.strip() for a in str(row.get("absent_fields") or "").split(";")
                  if a.strip() and a.strip() != "nan"]
        sites.append({
            "siteId": sid,
            "name": row.get("site_name") if isinstance(row.get("site_name"), str) else sid,
            "type": row.get("site_type") if isinstance(row.get("site_type"), str) else "unspecified",
            "lat": row.get("lat"),
            "lon": row.get("lon"),
            "rank": int(row["model_rank"]),
            "score": row["readiness_score"],
            "tier": row["recommendation_tier"],
            "subscores": {k.replace("_subscore", ""): row[k] for k in SUBSCORE_WEIGHTS},
            "confidence": {
                "score": None if c is None else c["data_confidence_score_v3"],
                "level": None if c is None else c["data_confidence_level_v3"],
                "breakdown": breakdown,
            },
            "portsNow": None if b is None else b["ports_active"],
            "pathwayPorts": None if b is None else b["ports_pathway"],
            "capacityCap": None if b is None else b["site_capacity_cap"],
            "plan": None if b is None else b["right_sizing_reason"],
            "expectedSessionsDay": row.get("expected_sessions_day"),
            "utilization": row.get("estimated_utilization"),
            "meanWaitMin": row.get("mean_wait_min"),
            "installCostUsd": row.get("install_cost_est_usd"),
            "electricalRisk": row.get("electrical_risk_level"),
            "absentFields": absent,
        })
    horizons = []
    for _, r in sizing.iterrows():
        horizons.append({
            "siteId": r["site_id"], "year": int(r["horizon_year"]), "case": r["case"],
            "portsActive": r["ports_active"], "portsPathway": r["ports_pathway"],
            "capacityCap": r["site_capacity_cap"], "strategy": r["expansion_strategy"],
        })
    cohort = summary.get("cohort") or {}
    return _out({
        "runId": summary["run_id"],
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "asOf": as_of or date.today().isoformat(),
        "mode": summary["mode"],
        "elapsedSec": round(elapsed, 3),
        "totals": {
            "sites": len(sites),
            "starterPorts2026": summary["starter_total_2026"],
            "pathwayPorts": summary["pathway_total"],
            "highConfidenceSites": summary["high_confidence_sites"],
        },
        "claims": summary["claims_discipline"],
        "defaults": cohort.get("defaults", []),
        "notes": cohort.get("notes", []),
        "costsWithheld": summary.get("costs_withheld_for_missing_inputs", []),
        "subscoreWeights": SUBSCORE_WEIGHTS,
        "sites": sites,
        "horizons": horizons,
    })


def explain(site_id: str) -> str:
    """One site's score as the sum of its parts, in readiness points.

    readiness = sum over subscores of (subscore weight x subscore), and each subscore is 100 x
    the sum of (driver weight x credit), where credit is the normalised value, or 1 minus it for
    a "lower is better" term, and 0 for a value nobody recorded (DEC-011). So each driver adds
    `subscore weight x 100 x driver weight x credit` points, and the drivers add up to the score
    before its rounding to one decimal. `max` is what the driver would add at full credit.

    One multiplier sits outside the weights: a site not recorded as open to the public has its
    whole demand subscore counted at 65% (`readiness_access_adjustment`), so its demand drivers
    are scaled by it here too, and the factor is returned so the reader is told why.
    """
    results = _session.results
    if results is None:
        raise ValueError("Run the model first.")
    match = results[results["site_id"].astype(str) == str(site_id)]
    if match.empty:
        raise ValueError(f"No site {site_id} in these results.")
    row = match.iloc[0]
    absent = {a.strip() for a in str(row.get("absent_fields") or "").split(";") if a.strip()}
    access = float(row.get("readiness_access_adjustment", 1.0))
    drivers = []
    for subscore, weights in DRIVER_WEIGHTS.items():
        sw = SUBSCORE_WEIGHTS[subscore]
        for driver, w in weights.items():
            raw = row.get(driver)
            inverted = driver in INVERTED_DRIVERS
            if raw is None or (isinstance(raw, float) and math.isnan(raw)):
                credit = 0.0
            else:
                credit = (1 - float(raw)) if inverted else float(raw)
            scale = access if subscore == "demand_subscore" else 1.0
            inputs = DRIVER_INPUTS.get(driver, [driver[:-2] if driver.endswith("_n") else driver])
            drivers.append({
                "key": driver,
                "label": DRIVER_LABELS.get(driver, driver),
                "subscore": subscore.replace("_subscore", ""),
                "weight": round(sw * w, 6),
                "credit": round(credit, 6),
                "inverted": inverted,
                "points": round(sw * 100 * w * credit * scale, 4),
                "max": round(sw * 100 * w, 4),
                "absent": any(i in absent for i in inputs),
                "inputs": inputs,
            })
    subscores = [{
        "key": k.replace("_subscore", ""), "label": SUBSCORE_LABELS[k], "weight": w,
        "value": row[k], "points": round(w * row[k], 4), "max": round(w * 100, 4),
    } for k, w in SUBSCORE_WEIGHTS.items()]
    return _out({
        "siteId": str(site_id),
        "name": row.get("site_name") if isinstance(row.get("site_name"), str) else str(site_id),
        "score": row["readiness_score"],
        "rank": int(row["model_rank"]),
        "accessAdjustment": access,
        "subscores": subscores,
        "drivers": drivers,
    })


def provenance(cell_json: str) -> str:
    """Where one number in the run's scenario table came from, resolved only when asked.

    The input is `{"siteId", "horizonYear", "scenario", "column"}`, one cell of the contract's
    `scenario_table.csv`. The answer is `provenance.resolve()`'s record, the same one the
    desktop tier shows. Resolving every cell up front took minutes at 600 sites, so the
    platform asks for the cell the planner opens. A cell that cannot be explained is refused in
    words, never answered with "unknown".
    """
    from . import provenance as pv

    if _session.out_dir is None:
        raise ValueError("Run the model first.")
    cell = json.loads(cell_json)
    missing = [k for k in ("siteId", "horizonYear", "scenario", "column") if cell.get(k) in (None, "")]
    if missing:
        raise ValueError(f"Say which number to explain: {', '.join(missing)} is missing.")
    try:
        horizon = int(cell["horizonYear"])
    except (TypeError, ValueError):
        raise ValueError(f"{cell['horizonYear']!r} is not a horizon year.") from None
    if _session.contract is None:
        _session.contract = pv.ContractIndex.load(_session.out_dir / "contract", text_site_ids=True)
    try:
        record = pv.resolve(_session.contract, str(cell["siteId"]), horizon,
                            str(cell["scenario"]), str(cell["column"]))
    except pv.ProvenanceError as e:
        raise ValueError(str(e)) from None
    return _out(record.to_dict())


def output_files() -> str:
    """Every file the last run wrote, as {path: text}, for the report and the project file."""
    if _session.out_dir is None:
        raise ValueError("Run the model first.")
    files = {}
    for base, prefix in ((_session.out_dir, "results/"), (_session.cohort_dir, "inputs/")):
        for path in sorted(base.rglob("*")):
            if path.is_file():
                files[prefix + path.relative_to(base).as_posix()] = path.read_text()
    return _out({"files": files})
