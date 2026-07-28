"""The browser's field-entry rules must never accept what the model will reject.

The asymmetry this tests, and why it is not symmetric
----------------------------------------------------
Two ways the form and the model can disagree, and they are not equally bad:

* **The form accepts, the model rejects.** This is the serious one. A field worker fills in an
  observation, the page says it is fine, and the row dies later at ingestion — or, worse, is
  quietly dropped. The person believes they recorded something they did not. **Any instance of
  this fails the test.**
* **The form rejects, the model accepts.** Less serious but not free: it blocks a legitimate
  observation. Each instance must appear in ``FORM_IS_STRICTER`` with a stated reason, so the
  set stays small and deliberate rather than growing by accident.

Testing the real pipeline, not the dataclass
--------------------------------------------
The Python side writes a CSV and calls ``read_capacity_observations`` /
``read_session_observations`` — the functions the actual ingest step calls. Constructing the
dataclass directly would test a layer the CSV never touches, and would miss the parsing that
happens on the way in. That distinction is not academic: several of the asymmetries recorded
below live in the CSV layer, not in ``__post_init__``.

The JS side evaluates ``site/platform/field_validate.js`` — the same bytes the browser loads,
via ``node:vm``. Not a port of it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2.observed import (  # noqa: E402
    read_capacity_observations, read_session_observations,
)

SCHEMA_PATH = REPO / "site/platform/field_schema.json"
VALIDATOR = REPO / "site/platform/field_validate.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is required to run the browser validator")


#: Cases where the FORM refuses something the MODEL would accept. Each needs a reason.
#: Every entry here is also a note for the Phase 10 audit: it marks a place where the Python
#: is more permissive than it probably should be.
#: Currently empty, and that is the interesting part.
#:
#: The first run of this test had three entries — places where the browser refused a row the
#: model would happily ingest. Every one turned out to be a defect in the *model*, not an
#: over-strict form, and the most serious of them (blank attribution surviving as the string
#: "nan") had been live for the entire life of the V4 loop. They were fixed rather than
#: documented, so the list emptied itself.
#:
#: If an entry ever needs adding back, it must carry a reason. `test_documented_asymmetries_
#: are_still_real` deletes stale ones by failing, so this cannot quietly become a list of
#: excuses.
FORM_IS_STRICTER: dict[tuple[str, str], str] = {}


def load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        pytest.skip("run scripts/build_field_schema.py first")
    return json.loads(SCHEMA_PATH.read_text())


def form(schema: dict, form_id: str) -> dict:
    return next(f for f in schema["forms"] if f["id"] == form_id)


# ---------------------------------------------------------------- candidate rows

def capacity_base() -> dict:
    return {
        "site_id": "FFX001", "observed_date": "2026-07-01",
        "method": "utility_load_study",
        "service_capacity_kw": "400", "spare_capacity_kw": "120",
        "measured_peak_kw": "180", "source_org": "Dominion Energy",
        "source_document": "Load study LS-2026-114", "observer": "A. Yaro",
        "verification_status": "reviewed", "notes": "",
    }


def session_base() -> dict:
    return {
        "site_id": "FFX001", "date": "2026-07-01", "sessions": "12",
        "energy_kwh": "180", "mean_dwell_min": "45", "ports_in_service": "2",
        "port_hours_available": "44", "port_hours_possible": "48",
        "facility_visitors_day": "300", "sessions_delayed": "1",
        "wait_p90_min": "5", "observer": "A. Yaro", "source_system": "ChargePoint",
    }


def mutate(base: dict, **changes) -> dict:
    row = dict(base)
    row.update(changes)
    return row


def capacity_candidates() -> list[tuple[str, dict]]:
    b = capacity_base()
    return [
        ("valid", b),
        ("blank site_id", mutate(b, site_id="")),
        ("blank observed_date", mutate(b, observed_date="")),
        ("unknown method", mutate(b, method="i_reckon")),
        ("blank method", mutate(b, method="")),
        ("weakest legal method", mutate(b, method="comparable_site_proxy")),
        ("blank source_document", mutate(b, source_document="")),
        ("whitespace source_document", mutate(b, source_document="   ")),
        ("blank observer", mutate(b, observer="")),
        ("neither capacity value", mutate(b, service_capacity_kw="", spare_capacity_kw="")),
        ("only spare capacity", mutate(b, service_capacity_kw="")),
        ("negative service capacity", mutate(b, service_capacity_kw="-1")),
        ("zero service capacity", mutate(b, service_capacity_kw="0")),
        ("non-numeric service_capacity_kw", mutate(b, service_capacity_kw="four hundred")),
        ("unknown verification_status", mutate(b, verification_status="vibes")),
        ("negative measured peak", mutate(b, measured_peak_kw="-5")),
    ]


def session_candidates() -> list[tuple[str, dict]]:
    b = session_base()
    return [
        ("valid", b),
        ("blank site_id", mutate(b, site_id="")),
        ("zero ports_in_service", mutate(b, ports_in_service="0")),
        ("negative ports_in_service", mutate(b, ports_in_service="-2")),
        ("zero port_hours_possible", mutate(b, port_hours_possible="0")),
        ("available exceeds possible", mutate(b, port_hours_available="60",
                                              port_hours_possible="48")),
        ("available equals possible", mutate(b, port_hours_available="48",
                                             port_hours_possible="48")),
        ("negative sessions", mutate(b, sessions="-1")),
        ("negative energy", mutate(b, energy_kwh="-10")),
        ("negative dwell", mutate(b, mean_dwell_min="-3")),
        ("zero sessions is legitimate", mutate(b, sessions="0", energy_kwh="0")),
    ]


# ---------------------------------------------------------------- the two verdicts

def python_accepts(form_id: str, row: dict, columns: list[str]) -> bool:
    """Run the row through the function the real ingest step calls."""
    reader = read_capacity_observations if form_id == "capacity" else read_session_observations
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as handle:
        handle.write(",".join(columns) + "\n")
        handle.write(",".join(f'"{str(row.get(c, ""))}"' for c in columns) + "\n")
        path = handle.name
    try:
        reader(path)
        return True
    except Exception:
        return False
    finally:
        Path(path).unlink(missing_ok=True)


def js_verdicts(schema: dict, cases: dict[str, list[dict]]) -> dict[str, list[bool]]:
    """Evaluate the real validator file in node and return accept/reject per row."""
    runner = f"""
      import {{ readFileSync }} from "node:fs";
      import vm from "node:vm";
      const sandbox = {{ console }};
      vm.createContext(sandbox);
      vm.runInContext(readFileSync({json.dumps(str(VALIDATOR))}, "utf8"), sandbox);
      const schema = JSON.parse(readFileSync({json.dumps(str(SCHEMA_PATH))}, "utf8"));
      const cases = JSON.parse(readFileSync(process.argv[2], "utf8"));
      const out = {{}};
      for (const [formId, rows] of Object.entries(cases)) {{
        const form = schema.forms.find((f) => f.id === formId);
        out[formId] = rows.map((r) => sandbox.FieldValidate.validateRow(form, r).length === 0);
      }}
      process.stdout.write(JSON.stringify(out));
    """
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as rf:
        rf.write(runner)
        runner_path = rf.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as cf:
        json.dump(cases, cf)
        cases_path = cf.name
    try:
        proc = subprocess.run(["node", runner_path, cases_path],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise AssertionError(f"validator runner failed:\n{proc.stderr}")
        return json.loads(proc.stdout)
    finally:
        Path(runner_path).unlink(missing_ok=True)
        Path(cases_path).unlink(missing_ok=True)


# ---------------------------------------------------------------- the tests

@pytest.fixture(scope="module")
def verdicts():
    schema = load_schema()
    candidates = {"capacity": capacity_candidates(), "session": session_candidates()}
    cases = {k: [row for _name, row in v] for k, v in candidates.items()}
    js = js_verdicts(schema, cases)
    out = {}
    for form_id, entries in candidates.items():
        columns = form(schema, form_id)["csv_columns"]
        out[form_id] = [
            (name, js[form_id][i], python_accepts(form_id, row, columns))
            for i, (name, row) in enumerate(entries)
        ]
    return out


def test_the_form_never_accepts_what_the_model_rejects(verdicts):
    """The one that matters. A person must never be told an observation was recorded when the
    ingest step is going to refuse it."""
    violations = []
    for form_id, rows in verdicts.items():
        for name, js_ok, py_ok in rows:
            if js_ok and not py_ok:
                violations.append(f"{form_id}: {name!r} — form ACCEPTS, model REJECTS")
    assert violations == [], (
        "The browser form is more permissive than the model. Someone would fill this in, be "
        "told it is fine, and have it refused later:\n  " + "\n  ".join(violations))


def test_every_case_where_the_form_is_stricter_is_documented(verdicts):
    """The lesser failure, kept deliberate. An undocumented instance means the form has quietly
    started blocking legitimate observations."""
    undocumented = []
    for form_id, rows in verdicts.items():
        for name, js_ok, py_ok in rows:
            if py_ok and not js_ok and (form_id, name) not in FORM_IS_STRICTER:
                undocumented.append(f"{form_id}: {name!r}")
    assert undocumented == [], (
        "The form refuses these, the model accepts them, and no reason is recorded. Either "
        "justify each in FORM_IS_STRICTER or relax the form:\n  " + "\n  ".join(undocumented))


def test_a_valid_row_is_accepted_by_both(verdicts):
    """Guards against the cheapest way to pass the test above: refuse everything."""
    for form_id, rows in verdicts.items():
        name, js_ok, py_ok = rows[0]
        assert name == "valid"
        assert js_ok, f"{form_id}: the form rejects its own valid baseline row"
        assert py_ok, f"{form_id}: the model rejects the valid baseline row"


def test_the_candidates_actually_exercise_rejection(verdicts):
    """A parity test where nothing is rejected proves nothing. Both sides must be refusing a
    substantial share of the deliberately-broken rows."""
    for form_id, rows in verdicts.items():
        js_rejects = sum(1 for _n, js_ok, _p in rows if not js_ok)
        py_rejects = sum(1 for _n, _j, py_ok in rows if not py_ok)
        assert js_rejects >= 5, f"{form_id}: form only rejected {js_rejects} candidates"
        assert py_rejects >= 4, f"{form_id}: model only rejected {py_rejects} candidates"


def test_documented_asymmetries_are_still_real(verdicts):
    """If the Python is fixed, its entry here must go. A stale exemption is a blind spot that
    looks like a decision."""
    observed = {(form_id, name)
                for form_id, rows in verdicts.items()
                for name, js_ok, py_ok in rows if py_ok and not js_ok}
    stale = sorted(set(FORM_IS_STRICTER) - observed)
    assert stale == [], (
        f"These asymmetries no longer occur and their exemptions should be deleted: {stale}")


def test_the_schema_is_generated_from_the_model_not_hand_written():
    schema = load_schema()
    assert schema["source_of_truth"] == "src/fcf_m2/observed.py"
    from fcf_m2.observed import METHOD_TO_BASIS
    assert schema["method_to_basis"] == METHOD_TO_BASIS, (
        "field_schema.json has drifted from observed.py — re-run scripts/build_field_schema.py")
