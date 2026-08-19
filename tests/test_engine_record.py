"""The platform never conflates engines, and surfaces divergences rather than hiding them.

Two Phase 7 rules are enforced here:

  "The platform never conflates engines. Python, Octave, real MATLAB, and the native
   Simulink view are always distinguishable on screen."
  "MATLAB runner - results shown beside the Python results with divergences SURFACED,
   not hidden."

The awkward fact this has to handle honestly: the two engines have never run on the same
data. Real MATLAB has only ever executed against a synthetic fixture, because the public
harness must never carry project data. So a row-by-row comparison of the twelve real sites
does not exist - and the record must say so rather than quietly showing something else.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config  # noqa: E402

RECORD = REPO / "site/platform/engines.json"


@pytest.fixture(scope="module")
def rec() -> dict:
    return json.loads(RECORD.read_text())


def test_all_four_engines_are_present_and_distinct(rec):
    ids = [e["id"] for e in rec["engines"]]
    assert ids == ["python", "matlab", "octave", "simulink"]
    assert len(set(ids)) == 4


def test_only_python_and_octave_have_run_on_the_real_sites(rec):
    """MATLAB and Simulink have not, and every surface must say so."""
    by_id = {e["id"]: e for e in rec["engines"]}
    assert by_id["python"]["ran_on_real_sites"] is True
    assert by_id["matlab"]["ran_on_real_sites"] is False
    assert by_id["simulink"]["ran_on_real_sites"] is False


def test_octave_is_explicitly_not_matlab(rec):
    octave = next(e for e in rec["engines"] if e["id"] == "octave")
    assert "NOT MATLAB" in octave["status"]
    assert "not a MATLAB result" in octave["warning"]
    assert "does NOT fire" in octave["detail"], (
        "the capacity-guard difference is the reason Octave may not make a feasibility claim")


def test_matlab_says_it_ran_only_on_synthetic_data(rec):
    matlab = next(e for e in rec["engines"] if e["id"] == "matlab")
    assert "synthetic" in matlab["detail"].lower()
    assert "never seen the twelve real sites" in matlab["detail"]
    assert "SYNTHETIC" in matlab["evidence"]["input_note"]


def test_simulink_was_built_but_never_simulated(rec):
    sim = next(e for e in rec["engines"] if e["id"] == "simulink")
    assert "never simulated" in sim["status"]
    assert "no number anywhere derives from it" in sim["detail"]


def test_the_evidence_comes_from_a_real_committed_run(rec):
    """Every figure is read out of an artifact, never restated by hand."""
    matlab = next(e for e in rec["engines"] if e["id"] == "matlab")
    ev = matlab["evidence"]
    assert ev["run_id"].isdigit() and len(ev["run_id"]) >= 8
    assert len(ev["commit"]) == 12
    assert ev["input_sha256"], "the input hash must be carried"
    run_dir = REPO / "matlab/outputs" / f"run-{ev['run_id']}"
    assert run_dir.is_dir(), f"{run_dir} is not committed; the evidence cannot be checked"


def test_the_guard_evidence_shows_the_guard_firing(rec):
    """The single most valuable thing the MATLAB runs establish."""
    g = rec["guard_evidence"]
    assert g["rows"] == 120 and g["run_status_ok"] == 120
    assert g["capacity_basis"] == ["placeholder"]
    assert g["service_check"] == ["service_capacity_unknown"]
    assert g["strategies_skipped"] == 120, "the guard must have skipped both strategies"
    assert g["peak_clamp_all_null"] is True, "no number may be invented for a skipped strategy"


def test_every_divergence_is_marked_surfaced(rec):
    assert rec["divergences"], "an empty divergence list would be a claim, not a record"
    for d in rec["divergences"]:
        assert d["surfaced"] is True, f"{d['id']} is not surfaced"
        assert d["finding"] and d["severity"]


def test_the_unfixed_divergence_states_why_it_is_unfixed(rec):
    unfixed = [d for d in rec["divergences"] if "deliberately_unfixed" in d]
    assert unfixed, "the known unfixed divergence must still be listed"
    for d in unfixed:
        assert len(d["deliberately_unfixed"]) > 60, "the reason must be a reason"


def test_the_charger_efficiency_divergence_records_the_real_values(rec):
    d = next(x for x in rec["divergences"] if x["id"] == "charger-efficiency")
    assert str(config.CHARGER_EFFICIENCY) in d["finding"]
    assert "0.93" in d["finding"]
    assert d["severity"] == "FIXED"
    assert "not a contract field" in d["why_it_survived"]


def test_it_states_what_CANNOT_be_shown(rec):
    """The comparison that does not exist must be named, not left as an absence a reader
    might mistake for an oversight."""
    text = rec["what_cannot_be_shown"]
    assert "row-by-row" in text
    assert "will not be fabricated" in text


def test_the_record_rebuilds_from_the_committed_artifacts(tmp_path):
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_engine_record.py")],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(RECORD.read_text())["schema"] == "fcf-engines/1"
