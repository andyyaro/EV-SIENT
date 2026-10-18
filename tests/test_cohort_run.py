"""Another jurisdiction's sites run end to end, and are held to their own numbers, not ours.

Why this file exists
--------------------
Until 2026-10-17 `workflow.run` read four fixed files. Measured on a six-site Chicago-shaped
cohort, the only way in - overwriting those files - failed twice: `KeyError: 'LIB-01'` because
MATLAB site meta was required for every site, and, once that was fabricated, `RT-04: baseline
starter total 12 != 25`, because the Northern Virginia study's golden totals were asserted
against every non-synthetic run (F-18, F-06). These tests run cohorts through the same code a
user would: `intake --accept`, then `run --cohort`.

The RT-04 golden totals still guard the reference study. They now key on the digests of its
inputs, and the first test pins those digests to the files, so an edit to the real inputs
fails here instead of quietly switching the check off.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import contract, standards, workflow  # noqa: E402

MESSY = REPO / "data/intake/fixtures/messy_third_party.csv"
SYNTHETIC = REPO / "data/synthetic"


def _intake(source: Path, out: Path, *extra: str) -> int:
    with pytest.raises(SystemExit) as done:
        workflow.main(["intake", str(source), "--out", str(out), *extra])
    return done.value.code


def _validate(contract_dir: Path) -> None:
    workflow.main(["validate-contract", str(contract_dir)])   # exits non-zero on any problem


def test_the_reference_digests_are_the_files_in_data_inputs():
    """Editing a real input must be a deliberate re-baseline, never a silent opt-out of RT-04."""
    for name, digest in contract.REFERENCE_INPUTS.items():
        assert contract.sha256_file(REPO / "data/inputs" / name) == digest, (
            f"data/inputs/{name} changed. If that is intended, re-baseline RT-04 and update "
            f"contract.REFERENCE_INPUTS in the same commit.")


def test_a_messy_file_goes_from_intake_to_a_valid_contract(tmp_path):
    cohort = tmp_path / "example-county"
    assert _intake(MESSY, cohort) == 0
    assert not cohort.exists(), "without --accept, intake must write nothing"
    assert _intake(MESSY, cohort, "--accept", "--jurisdiction", "Example County",
                   "--source-date", "2026-09-30") == 0
    declared = json.loads((cohort / "cohort.json").read_text())
    assert declared["jurisdiction"] == "example-county"
    assert declared["source_sha256"] == contract.sha256_file(MESSY)

    result = workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)
    assert result["scenario_rows"] == 3 * 10
    assert result["cohort"]["reference_totals_apply"] is False
    manifest = json.loads((tmp_path / "out/contract/contract_manifest.json").read_text())
    assert manifest["legacy_totals_checked"] is False
    assert manifest["cohort"]["jurisdiction"] == "example-county"
    table = pd.read_csv(tmp_path / "out/contract/scenario_table.csv")
    assert set(table["jurisdiction"]) == {"example-county"}, "a cohort must never claim fairfax or pwc"
    assert set(table["source_date"]) == {"2026-09-30"}
    _validate(tmp_path / "out/contract")


def test_intake_refuses_to_overwrite_a_cohort(tmp_path):
    cohort = tmp_path / "c"
    assert _intake(MESSY, cohort, "--accept") == 0
    before = (cohort / "sites.csv").read_bytes()
    assert _intake(MESSY, cohort, "--accept") == 1
    assert (cohort / "sites.csv").read_bytes() == before


def test_every_default_a_cohort_used_is_written_down(tmp_path):
    """Only sites.csv is required. Whatever stands in for the rest is a sentence in the
    manifest, and the stand-ins invent nothing: base load stays unknown."""
    cohort = tmp_path / "bare"
    cohort.mkdir()
    shutil.copy(SYNTHETIC / "synthetic_sites_v2.csv", cohort / "sites.csv")
    result = workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)
    defaults = " ".join(result["cohort"]["defaults"])
    for subject in ("electrical risk", "site meta", "provenance"):
        assert subject in defaults
    table = pd.read_csv(tmp_path / "out/contract/scenario_table.csv")
    assert table["base_load_kw"].isna().all(), "an unknown base load must not be invented"
    assert (table["data_confidence"] == "Low").all()


def test_a_site_missing_a_cost_input_gets_no_cost_figures(tmp_path):
    """Costed with the gap as 0, it would look cheaper than a site that was measured."""
    cohort = tmp_path / "gap"
    cohort.mkdir()
    sites = pd.read_csv(SYNTHETIC / "synthetic_sites_v2.csv")
    sites["trenching_ft"] = sites["trenching_ft"].astype(object)
    sites.loc[0, "trenching_ft"] = ""
    sites.to_csv(cohort / "sites.csv", index=False)
    result = workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)
    gap = sites.loc[0, "site_id"]
    assert result["costs_withheld_for_missing_inputs"] == [gap]
    table = pd.read_csv(tmp_path / "out/contract/scenario_table.csv")
    assert table.loc[table["site_id"] == gap, "lifecycle_cost_nominal_usd"].isna().all()
    assert table.loc[table["site_id"] != gap, "lifecycle_cost_nominal_usd"].notna().any()
    costs = pd.read_csv(tmp_path / "out/lifecycle_costs.csv")
    assert gap not in set(costs["site_id"])


def test_the_reference_study_run_as_a_cohort_is_still_held_to_25_and_48(tmp_path):
    """RT-04 keys on the inputs, not on how they arrived."""
    cohort = tmp_path / "nova"
    cohort.mkdir()
    shutil.copy(REPO / "data/inputs/real_sites_v2.csv", cohort / "sites.csv")
    shutil.copy(REPO / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv",
                cohort / "electrical_risk.csv")
    shutil.copy(REPO / "data/inputs/legacy_matlab_site_meta.csv", cohort / "site_meta.csv")
    shutil.copy(REPO / "data/provenance/field_provenance_v1.csv", cohort / "provenance.csv")
    result = workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)
    assert result["cohort"]["reference_totals_apply"] is True
    assert result["plan_ranking"] == result["cohort"]["plan_ranking"] == "legacy_v2"
    assert (result["starter_total_2026"], result["pathway_total"]) == (25, 48)
    manifest = json.loads((tmp_path / "out/contract/contract_manifest.json").read_text())
    assert manifest["legacy_totals_checked"] is True


@pytest.mark.parametrize("change,message", [
    (lambda s: s.assign(site_id=["DUP"] * len(s)), "unique"),
    (lambda s: s.assign(site_id=["has space"] + list(s["site_id"][1:])), "not usable"),
    (lambda s: s.drop(columns=["site_id"]), "no site_id"),
])
def test_a_cohort_that_cannot_be_told_apart_is_refused_in_a_sentence(tmp_path, change, message):
    cohort = tmp_path / "bad"
    cohort.mkdir()
    change(pd.read_csv(SYNTHETIC / "synthetic_sites_v2.csv")).to_csv(cohort / "sites.csv", index=False)
    with pytest.raises(workflow.CohortError, match=message):
        workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)


def test_an_unknown_risk_level_is_refused(tmp_path):
    cohort = tmp_path / "risk"
    cohort.mkdir()
    sites = pd.read_csv(SYNTHETIC / "synthetic_sites_v2.csv")
    sites.to_csv(cohort / "sites.csv", index=False)
    pd.DataFrame({"site_id": sites["site_id"], "electrical_risk_level": "severe"}).to_csv(
        cohort / "electrical_risk.csv", index=False)
    with pytest.raises(workflow.CohortError, match="severe"):
        workflow.run("milestone2_v3", tmp_path / "out", cohort_dir=cohort)


def test_the_reference_run_is_unchanged_by_any_of_this(tmp_path):
    """No --cohort: the same inputs, digests, schema and golden totals as before."""
    result = workflow.run("milestone2_v3", tmp_path / "out")
    assert "cohort" not in result
    assert (result["starter_total_2026"], result["pathway_total"]) == (25, 48)
    assert result["plan_ranking"] == "legacy_v2"
    manifest = json.loads((tmp_path / "out/contract/contract_manifest.json").read_text())
    assert "cohort" not in manifest and manifest["legacy_totals_checked"] is True
    assert set(contract.REFERENCE_INPUTS.items()) <= set(manifest["inputs"].items())


def _public_layout(root: Path) -> Path:
    """The public bundle's inputs: each synthetic file at the reference path it ships under."""
    spec = importlib.util.spec_from_file_location(
        "build_release_artifact", REPO / "scripts/build_release_artifact.py")
    bra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bra)
    for real, synthetic in bra.PUBLIC_SUBSTITUTIONS.items():
        (root / real).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / synthetic, root / real)
    (root / "data/anchors").mkdir(parents=True)
    shutil.copy(REPO / "data/anchors/anchor_set_v1.json", root / "data/anchors")
    return root


def test_synthetic_inputs_at_the_reference_paths_are_not_the_reference_study(tmp_path, monkeypatch):
    """The public bundle ships its synthetic inputs under the reference study's file names
    (DEC-016). Until 2026-10-17 a run without a cohort was taken for the reference study
    whatever it read, so the bundle planned its invented sites on the ranking only the real
    study keeps, 24 / 42, and named Fairfax City / PWC as their permitting authority. Run as a
    cohort, the same sites got 24 / 38 and a generic authority. The layout must not matter."""
    cohort = tmp_path / "synthetic"
    cohort.mkdir()
    for source, name in [("synthetic_sites_v2.csv", "sites.csv"),
                         ("synthetic_v2_electrical_risk_summary.csv", "electrical_risk.csv"),
                         ("synthetic_matlab_site_meta.csv", "site_meta.csv"),
                         ("synthetic_field_provenance_v1.csv", "provenance.csv")]:
        shutil.copy(SYNTHETIC / source, cohort / name)
    as_cohort = workflow.run("milestone2_v3", tmp_path / "cohort_out", cohort_dir=cohort)

    monkeypatch.setattr(workflow, "ROOT", _public_layout(tmp_path / "public"))
    public = workflow.run("milestone2_v3", tmp_path / "public_out")

    assert public["plan_ranking"] == as_cohort["plan_ranking"] == "milestone2_v3"
    for total in ("starter_total_2026", "pathway_total", "legacy_starter_total", "legacy_pathway_total"):
        assert public[total] == as_cohort[total], total
    plans = [pd.read_csv(out / "right_sizing_v3_canonical.csv")
             .sort_values(["site_id", "horizon_year", "case"]).reset_index(drop=True)
             for out in (tmp_path / "public_out", tmp_path / "cohort_out")]
    pd.testing.assert_frame_equal(*plans)
    register = pd.read_csv(tmp_path / "public_out/standards_register.csv")
    assert not register["authority"].str.contains(standards.REFERENCE_AUTHORITY_AREA, regex=False).any()
    manifest = json.loads((tmp_path / "public_out/contract/contract_manifest.json").read_text())
    assert manifest["legacy_totals_checked"] is False
    _validate(tmp_path / "public_out/contract")
