"""Resolve any displayed number to its full lineage.

The platform's central promise is that **no number appears without its provenance available**.
This module is what makes that promise keepable: given a cell reference - a table, a row key
and a column - it returns everything that can truthfully be said about where that number came
from, and refuses when it cannot.

Architecture-independent on purpose
-----------------------------------
Whatever shell the platform ends up in, this resolves the same way, because it reads only the
tracked contract directory. The desktop tier calls it directly; the web tier serves
``export_all()``'s JSON, precomputed at build time. **Both tiers show identical provenance**,
which they must, or the two tiers disagree about what a number means.

What "truthfully" excludes
--------------------------
* No field-group mapping is guessed. ``FIELD_GROUP_FOR_COLUMN`` is explicit, and a column with
  no mapping resolves with ``field_provenance = None`` and says so, rather than borrowing a
  neighbouring group's credibility.
* No caveat is inferred from a column's name. ``CAVEATS`` is a written table, and a column
  absent from it gets the contract-level caveats only.
* The engine is stated, never assumed. Every value in the contract is produced by the Python
  package; nothing here may be labelled MATLAB output, because MATLAB has never run on the
  real sites (see ``matlab/EXECUTION_STATUS.md``).

The refusal that matters
------------------------
``resolve()`` raises on an unknown column or a row that does not exist. A provenance panel
that renders "unknown" for a number it cannot explain is worse than one that refuses - the
first looks like an answer.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from . import config

#: Which provenance field group governs which contract column.
#:
#: Written out rather than inferred. A column's name is not evidence of its lineage --
#: ``spare_capacity_kw`` and ``service_capacity_kw`` both come from the electrical service
#: record, while ``equity_indicator`` does not, and no naming rule gets that right.
#: A column absent from this map resolves with no field provenance and says so.
FIELD_GROUP_FOR_COLUMN: dict[str, str] = {
    # electrical service -- the group carrying the placeholder capacity
    "service_capacity_kw": "electrical_service",
    "spare_capacity_kw": "electrical_service",
    "base_load_kw": "electrical_service",
    "capacity_basis": "electrical_service",
    "capacity_source": "electrical_service",
    "capacity_confidence": "electrical_service",
    # demand and use
    "sessions_per_day": "site_use_and_demand",
    "energy_per_session_kwh": "site_use_and_demand",
    "energy_required_kwh_day": "site_use_and_demand",
    "average_dwell_hr": "site_use_and_demand",
    "charging_window_hr": "site_use_and_demand",
    "utilization": "site_use_and_demand",
    "peak_factor": "site_use_and_demand",
    "average_wait_minutes": "site_use_and_demand",
    "peak_wait_minutes": "site_use_and_demand",
    "energy_delivered_kwh": "site_use_and_demand",
    "energy_curtailed_kwh": "site_use_and_demand",
    # layout / siting
    "ports_active": "parking_and_layout",
    "ports_pathway_capacity": "parking_and_layout",
    "evse_power_kw": "parking_and_layout",
    # identity and access
    "site_name": "address_and_public_access",
    "public_or_fleet": "address_and_public_access",
    "site_type": "address_and_public_access",
    "jurisdiction": "address_and_public_access",
    # equity
    "equity_indicator": "equity_and_context",
}

#: Caveats that attach to a column wherever it is displayed. Written, not inferred.
CAVEATS: dict[str, list[str]] = {
    "service_capacity_kw": ["capacity_placeholder"],
    "spare_capacity_kw": ["capacity_placeholder"],
    "capacity_basis": ["capacity_placeholder"],
    "capacity_confidence": ["capacity_placeholder"],
    # base_load_kw gets its OWN caveat, not the capacity one.
    #
    # It is the only populated electrical field in the contract -- 120/120, while
    # service_capacity_kw and spare_capacity_kw are honestly null -- so it is the one an
    # unwary reader would take for a measurement. It is not: its source file's own provenance
    # column reads "base loads and spare capacity are UNVERIFIED planning proxies".
    # Showing it the capacity caveat would answer a question nobody asked while leaving the
    # one that matters unanswered.
    "base_load_kw": ["base_load_proxy", "capacity_placeholder"],
    "sessions_per_day": ["demand_modelled"],
    "energy_required_kwh_day": ["demand_modelled"],
    "utilization": ["demand_modelled"],
    "average_wait_minutes": ["demand_modelled", "wait_simulated"],
    "peak_wait_minutes": ["demand_modelled", "wait_simulated"],
    "ports_active": ["screening_only"],
    "ports_pathway_capacity": ["screening_only"],
    "lifecycle_cost_nominal_usd": ["cost_screening_class"],
    "lifecycle_cost_npv_usd": ["cost_screening_class"],
    "avoided_overbuild_cost_usd": ["cost_screening_class"],
    "net_co2e_kg": ["emissions_factor", "demand_modelled"],
    "expansion_trigger_status": ["trigger_policy_proposed"],
    "data_confidence": ["confidence_from_typed_provenance"],
}

#: The caveat texts. One definition, so a caveat cannot drift between surfaces.
CAVEAT_TEXT: dict[str, str] = {
    "base_load_proxy": (
        "Base load is an UNVERIFIED PLANNING PROXY, not a measured value. Nobody has metered "
        "this building. It is the only populated electrical field in the contract, which makes "
        "it the easiest one to mistake for a measurement -- its source is a hand-adapted "
        "planning placeholder carried over from the legacy adapter."),
    "capacity_placeholder": (
        "Electrical capacity is a PLACEHOLDER at all 12 sites. Nobody has confirmed the "
        "service could support chargers. This is not evidence of electrical feasibility, and "
        "the fail-closed guard refuses to emit a feasibility claim from it."),
    "demand_modelled": (
        "Demand is MODELLED, not measured. No charging has been observed at any of these "
        "sites; the figures come from benchmark assumptions applied to site characteristics."),
    # This caveat used to read: "The p50 and p90 are 0.0 at every site because simulated
    # utilisation runs 6-20%." That sentence is TRUE -- of a different statistic, in a
    # different table, at one horizon. It described the discrete-event run in
    # tbl_peak_waits.csv at 2026. It is attached to `average_wait_minutes` and
    # `peak_wait_minutes`, which are Erlang-C estimates across all four horizons and reach
    # 215.35 minutes at 2046. A reader hovering a 215-minute wait was being told waits are
    # zero. Text-versus-meaning again: accurate prose, wrong referent.
    "wait_simulated": (
        # No site is named in this string. It ships inside the public installer, where DEC-016
        # forbids real facility identifiers -- the release gate caught a draft that named two.
        # The reader always knows which site they are looking at, because the caveat is
        # attached to that row.
        # This caveat is attached to BOTH average_wait_minutes and peak_wait_minutes, so every
        # sentence must be true of both. A draft said "it ... reaches 215 minutes ... blank on
        # 5 rows": true of the peak column, false of the average column, which tops out at
        # 68.72 and has no blanks at all. The columns are now named separately.
        "Waits are SIMULATED from modelled demand and have never been observed -- no charging "
        "has happened at any of these sites. These are Erlang-C queueing estimates spanning a "
        "very wide range: effectively nil at one site, which never exceeds 1.31 minutes on any "
        "row and is 0.00 on most of them, and rising steeply elsewhere as fixed port counts "
        "meet growing modelled demand -- the AVERAGE wait reaches about 69 minutes and the "
        "PEAK about 215, at two DIFFERENT sites. The peak column is additionally BLANK on 5 "
        "rows, where the modelled queue never clears and no finite wait exists -- blank there "
        "means unbounded, not unknown, and it is the model's true worst case. A separate "
        "discrete-event run reports p50 and p90 waits of 0.0 at all 12 sites at the 2026 "
        "starter build; that is a different statistic from a different table, and it is not "
        "this number."),
    "screening_only": (
        "A screening-class planning output for comparing sites. It cannot approve, permit or "
        "fund anything, and it is not an engineering design."),
    "cost_screening_class": (
        "Screening-class cost estimate for COMPARISON between options. Never a budget, never "
        "a quote, never a bid."),
    "emissions_factor": (
        f"Grid emissions factor: {config.GRID_FACTOR_SOURCE}, "
        f"{config.GRID_FACTOR_LB_PER_MWH} lb CO2e/MWh, vintage {config.GRID_FACTOR_VINTAGE}."),
    "trigger_policy_proposed": (
        "The expansion-trigger policy is PROPOSED configuration, not adopted municipal "
        "policy, and every evaluation says so."),
    "confidence_from_typed_provenance": (
        "Data confidence is derived only from typed provenance fields -- source class, "
        "verification status and staleness. Prose in a notes field cannot change it."),
}

#: Every contract value is produced by the Python package. Stated, never assumed.
#:
#: This constant exists so no surface can quietly attribute a contract number to MATLAB.
#: Real MathWorks MATLAB has executed (49 tests, a 120-row batch) but only ever against a
#: SYNTHETIC fixture -- it has never seen the real sites. See matlab/EXECUTION_STATUS.md.
PRODUCING_ENGINE = "Python (fcf_m2)"


def _jsonable(value):
    """Convert a pandas/numpy scalar to a native Python type, or refuse.

    ``json.dumps(..., default=str)`` was used here first and it is a footgun: it silently
    stringified every numpy scalar, so the web tier received ``"2"`` where the desktop tier
    had ``2``. The panels looked identical and the types did not, which means a sort or a
    comparison on the web side would order 6 after 10. The two tiers disagreeing about what a
    number *is* is exactly the failure this module exists to prevent.

    Refusing on an unknown type is deliberate: a silent ``str()`` fallback is how the original
    defect got in.
    """
    if value is None:
        return None
    # NaN FIRST. numpy.float64 subclasses float, so an isinstance shortcut lets NaN straight
    # through -- and json.dumps then writes a bare `NaN` literal, which is not valid JSON and
    # which a browser's JSON.parse rejects outright. The whole web tier would fail to load.
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass                                     # not a scalar pandas understands; fall through
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return value
    item = getattr(value, "item", None)          # numpy scalars expose .item()
    if callable(item):
        return item()
    raise TypeError(f"cannot serialise {value!r} ({type(value).__name__}) for the provenance "
                    f"export; add an explicit conversion rather than letting it stringify")


class ProvenanceError(LookupError):
    """A number could not be explained. Never downgraded to a placeholder string."""


@dataclass(frozen=True)
class FieldProvenance:
    """The typed provenance record governing one column at one site."""

    field_group: str
    source_class: str
    verification_status: str
    source_org: str
    source_date: str
    reviewer: str
    assumption_type: str
    unresolved: bool


@dataclass(frozen=True)
class Provenance:
    """Everything that can truthfully be said about one displayed number."""

    # what it is
    value: object
    column: str
    table: str
    row_key: dict[str, object]

    # which run produced it
    contract_version: str
    model_version: str
    model_mode: str
    run_id: str
    generated_at: str
    engine: str

    # what backs it
    table_sha256: str
    source_id: str
    source_date: str
    assumption_flag: str

    # how much to trust it
    data_confidence: str
    capacity_basis: str

    # what the reader must know
    caveats: list[str]
    consumer_rules: list[str]
    field_provenance: FieldProvenance | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        out = asdict(self)
        out["value"] = _jsonable(self.value)
        return out


@dataclass
class ContractIndex:
    """A contract directory loaded once, for repeated resolution.

    The scenario table is indexed by its key ``(site_id, horizon_year, scenario_name)`` the
    first time a cell is resolved. ``resolve()`` used to find its row with a three-column mask
    over the whole table, once per cell, which made ``export_all`` quadratic: 251 s for 600
    sites under Pyodide. The index finds the same row by the same equality, so every answer is
    unchanged. It is built from the table as loaded; replace ``scenarios`` and build a new
    index rather than editing the frame in place.
    """

    directory: Path
    scenarios: pd.DataFrame
    provenance: pd.DataFrame
    manifest: dict
    _by_site: dict[str, dict[str, FieldProvenance]] = field(default_factory=dict)
    _positions: dict[tuple, list[int]] | None = field(default=None, repr=False, compare=False)
    _rows: dict[int, pd.Series] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def load(cls, contract_dir: str | Path, *, text_site_ids: bool = False) -> "ContractIndex":
        """Load a contract directory. ``text_site_ids`` reads ``site_id`` as text, so an
        all-digit ID such as "107" matches the text the platform passes instead of being read
        as the number 107 and matching nothing; the platform asks for it because its site IDs
        are always text."""
        directory = Path(contract_dir)
        manifest_path = directory / "contract_manifest.json"
        if not manifest_path.is_file():
            raise ProvenanceError(f"{directory} has no contract_manifest.json; it is not a "
                                  f"contract directory and nothing here can be attributed")
        dtype = {"site_id": str} if text_site_ids else None
        index = cls(
            directory=directory,
            scenarios=pd.read_csv(directory / "scenario_table.csv", dtype=dtype),
            provenance=pd.read_csv(directory / "source_provenance.csv", dtype=dtype),
            manifest=json.loads(manifest_path.read_text()),
        )
        for row in index.provenance.itertuples():
            index._by_site.setdefault(row.site_id, {})[row.field_group] = FieldProvenance(
                field_group=row.field_group,
                source_class=row.source_class,
                verification_status=row.verification_status,
                source_org=str(row.source_org),
                source_date=str(row.source_date),
                reviewer=str(row.reviewer),
                assumption_type=str(row.assumption_type),
                unresolved=bool(row.unresolved_flag),
            )
        return index

    def field_provenance(self, site_id: str, column: str) -> FieldProvenance | None:
        group = FIELD_GROUP_FOR_COLUMN.get(column)
        if group is None:
            return None
        return self._by_site.get(site_id, {}).get(group)

    def scenario_row(self, site_id: str, horizon_year: int, scenario_name: str) -> pd.Series:
        """The one scenario row with this key, or refuse.

        Matches exactly as a mask on the three columns would: Python equality on the values as
        loaded, so 2036 finds 2036.0 and "001" does not find 1. A key with a missing part is
        never indexed, because a mask never matches a missing value either.
        """
        if self._positions is None:
            positions: dict[tuple, list[int]] = {}
            keys = zip(self.scenarios["site_id"].tolist(),
                       self.scenarios["horizon_year"].tolist(),
                       self.scenarios["scenario_name"].tolist())
            for position, key in enumerate(keys):
                if not any(pd.isna(part) for part in key):
                    positions.setdefault(key, []).append(position)
            self._positions = positions

        try:
            found = self._positions.get((site_id, horizon_year, scenario_name), [])
        except TypeError:                        # an unhashable key matches no row
            found = []
        if not found:
            raise ProvenanceError(
                f"no scenario row for site_id={site_id!r}, horizon_year={horizon_year}, "
                f"scenario_name={scenario_name!r}")
        if len(found) > 1:
            raise ProvenanceError(
                f"{len(found)} rows match ({site_id}, {horizon_year}, {scenario_name}); the "
                f"contract's uniqueness rule is broken and no number here can be attributed")
        position = found[0]
        row = self._rows.get(position)
        if row is None:
            row = self._rows[position] = self.scenarios.iloc[position]
        return row


def resolve(index: ContractIndex, site_id: str, horizon_year: int, scenario_name: str,
            column: str) -> Provenance:
    """Explain one cell of the scenario table, or refuse.

    Refusing is the point. A panel that renders "unknown" for a number it cannot explain looks
    like an answer, and this project's whole discipline is that an unexplained number is worse
    than no number.
    """
    if column not in index.scenarios.columns:
        raise ProvenanceError(
            f"{column!r} is not a column of the scenario table. Known columns: "
            f"{', '.join(sorted(index.scenarios.columns))}")

    row = index.scenario_row(site_id, horizon_year, scenario_name)

    caveat_keys = list(CAVEATS.get(column, []))
    return Provenance(
        value=row[column],
        column=column,
        table="scenario_table.csv",
        row_key={"site_id": site_id, "horizon_year": horizon_year,
                 "scenario_name": scenario_name},
        contract_version=str(index.manifest.get("contract_version", "")),
        model_version=str(index.manifest.get("model_version", "")),
        model_mode=str(row.get("model_mode", "")),
        run_id=str(index.manifest.get("run_id", "")),
        generated_at=str(row.get("generated_at", index.manifest.get("generated_utc", ""))),
        engine=PRODUCING_ENGINE,
        table_sha256=str(index.manifest.get("tables", {}).get("scenario_table.csv", "")),
        source_id=str(row.get("source_id", "")),
        source_date=str(row.get("source_date", "")),
        assumption_flag=str(row.get("assumption_flag", "")),
        data_confidence=str(row.get("data_confidence", "")),
        capacity_basis=str(row.get("capacity_basis", "")),
        caveats=[CAVEAT_TEXT[k] for k in caveat_keys],
        consumer_rules=list(index.manifest.get("consumer_rules", [])),
        field_provenance=index.field_provenance(site_id, column),
        notes=str(row.get("notes", "")),
    )


#: Columns worth precomputing for the web tier. Every numeric column a surface displays.
EXPORTABLE_COLUMNS = [c for c in FIELD_GROUP_FOR_COLUMN] + [
    "lifecycle_cost_nominal_usd", "lifecycle_cost_npv_usd", "avoided_overbuild_cost_usd",
    "net_co2e_kg", "data_confidence", "expansion_trigger_status",
]


def export_all(contract_dir: str | Path, out_path: str | Path) -> dict:
    """Precompute provenance for every (row, exportable column) as NORMALISED JSON.

    This is what the web tier serves. It cannot execute anything, so it must be handed the
    same answers the desktop tier computes - identical by construction, because both come from
    this module.

    **Normalised, not flattened.** The naive form - one self-contained record per cell -
    repeated the caveat prose, the consumer rules and the run metadata across 3 720 entries
    and came to **6.76 MB**, which is a real cost to every visitor for information that is
    identical on every entry. Everything shared is hoisted; an entry carries only what varies,
    plus keys into the shared tables. Nothing is lost: ``entry_to_provenance`` reassembles a
    full record client-side, and a test asserts the round trip.
    """
    index = ContractIndex.load(contract_dir)

    field_prov: dict[str, dict] = {}
    entries: dict[str, dict] = {}
    for row in index.scenarios.itertuples():
        for column in EXPORTABLE_COLUMNS:
            if column not in index.scenarios.columns:
                continue
            p = resolve(index, row.site_id, int(row.horizon_year), row.scenario_name, column)

            fp_key = ""
            if p.field_provenance is not None:
                fp_key = f"{row.site_id}|{p.field_provenance.field_group}"
                if fp_key not in field_prov:     # asdict once per record, not once per cell
                    field_prov[fp_key] = asdict(p.field_provenance)

            entries[f"{row.site_id}|{row.horizon_year}|{row.scenario_name}|{column}"] = {
                "v": _jsonable(p.value),
                "conf": p.data_confidence,
                "basis": p.capacity_basis,
                "mode": p.model_mode,
                "cav": CAVEATS.get(column, []),      # keys into caveat_text
                "fp": fp_key,                        # key into field_provenance
                "flag": p.assumption_flag,
            }

    payload = {
        "schema": "fcf-provenance/1",
        "generated_from": str(Path(contract_dir).name),
        # Shared by EVERY entry -- hoisted, because repeating them is the whole 6.76 MB.
        "shared": {
            "contract_version": index.manifest.get("contract_version"),
            "model_version": index.manifest.get("model_version"),
            "run_id": index.manifest.get("run_id"),
            "generated_utc": index.manifest.get("generated_utc"),
            "table": "scenario_table.csv",
            "table_sha256": index.manifest.get("tables", {}).get("scenario_table.csv", ""),
            "engine": PRODUCING_ENGINE,
            "consumer_rules": list(index.manifest.get("consumer_rules", [])),
        },
        "engine_note": (
            "Every value in this contract was produced by the Python package. Real MathWorks "
            "MATLAB has executed this project's model, but only against a SYNTHETIC fixture "
            "-- it has never seen the real sites. GNU Octave is not MATLAB. No number here "
            "may be attributed to either."),
        "caveat_text": CAVEAT_TEXT,
        "field_provenance": field_prov,
        "entries": entries,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # No `default=` fallback. Everything is converted explicitly by _jsonable, so an
    # unexpected type fails loudly here instead of arriving in the browser as a string.
    # allow_nan=False: emit STRICT JSON or fail here. Python happily writes NaN/Infinity
    # literals that no browser will parse, which would break the web tier silently at build
    # time and loudly at load time, in front of a reader.
    out.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False) + "\n")
    return payload


def entry_to_provenance(payload: dict, key: str) -> dict:
    """Reassemble a full provenance record from the normalised export.

    The reference implementation of what the web tier's JavaScript does. Kept here in Python
    so a test can assert that the normalised export and ``resolve()`` agree - the two tiers
    disagreeing about what a number means is the failure this whole module exists to prevent.
    """
    entry = payload["entries"][key]
    site_id, horizon, scenario, column = key.split("|")
    shared = payload["shared"]
    fp = payload["field_provenance"].get(entry["fp"]) if entry["fp"] else None
    return {
        "value": entry["v"],
        "column": column,
        "table": shared["table"],
        "row_key": {"site_id": site_id, "horizon_year": int(horizon),
                    "scenario_name": scenario},
        "contract_version": shared["contract_version"],
        "model_version": shared["model_version"],
        "model_mode": entry["mode"],
        "run_id": shared["run_id"],
        "engine": shared["engine"],
        "table_sha256": shared["table_sha256"],
        "assumption_flag": entry["flag"],
        "data_confidence": entry["conf"],
        "capacity_basis": entry["basis"],
        "caveats": [payload["caveat_text"][k] for k in entry["cav"]],
        "consumer_rules": shared["consumer_rules"],
        "field_provenance": fp,
    }


__all__ = [
    "FIELD_GROUP_FOR_COLUMN", "CAVEATS", "CAVEAT_TEXT", "PRODUCING_ENGINE",
    "EXPORTABLE_COLUMNS", "ProvenanceError", "FieldProvenance", "Provenance",
    "ContractIndex", "resolve", "export_all", "entry_to_provenance",
]
