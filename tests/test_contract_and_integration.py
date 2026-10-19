"""Contract validation, reconciliation, workflow integration, GIS offline, docs drift,
visual footers, package generation."""

import json
from pathlib import Path

import pandas as pd
import pytest

from fcf_m2 import contract, workflow


class TestContractValidation:
    @pytest.fixture()
    def valid(self, v3_outputs):
        out, _ = v3_outputs
        st = pd.read_csv(out / "contract/scenario_table.csv")
        site = pd.read_csv(out / "contract/site_table.csv")
        return st, site

    def test_generated_contract_is_valid(self, valid):
        st, site = valid
        assert contract.validate_scenario_table(st, site) == []

    def test_json_schema_pass(self, valid, v3_outputs):
        st, _ = valid
        out, _ = v3_outputs
        schema = json.loads((out / "contract/schema.json").read_text())
        assert contract.validate_against_json_schema(st, schema) == []

    def test_hash_chain(self, v3_outputs):
        out, _ = v3_outputs
        assert contract.verify_hash_chain(out / "contract") == []

    def test_stale_contract_detected(self, v3_outputs, tmp_path):
        out, _ = v3_outputs
        import shutil
        c = tmp_path / "c"
        shutil.copytree(out / "contract", c)
        st = pd.read_csv(c / "scenario_table.csv")
        st.loc[0, "ports_active"] = st.loc[0, "ports_active"] + 1
        st.to_csv(c / "scenario_table.csv", index=False)
        assert contract.verify_hash_chain(c)  # RT-10 must flag

    def test_invalid_units_fail(self, valid):
        st, site = valid
        bad = st.copy()
        bad.loc[0, "charging_window_hr"] = 30
        assert any("charging_window_hr" in p or "RT-05" in p
                   for p in contract.validate_scenario_table(bad, site))

    def test_unsupported_horizon_fails(self, valid):
        st, site = valid
        bad = st.copy()
        bad.loc[0, "horizon_year"] = 2040
        assert contract.validate_scenario_table(bad, site)

    def test_placeholder_capacity_presented_as_verified_fails(self, valid):
        st, site = valid
        bad = st.copy()
        bad["capacity_confidence"] = "high"  # placeholder rows claiming high confidence
        assert any("RT-07" in p for p in contract.validate_scenario_table(bad, site))

    def test_missing_provenance_fails(self, valid):
        st, site = valid
        bad = st.copy()
        bad["source_id"] = ""
        assert any("provenance" in p for p in contract.validate_scenario_table(bad, site))

    def test_ports_over_pathway_fails(self, valid):
        st, site = valid
        bad = st.copy()
        bad.loc[0, "ports_active"] = int(bad.loc[0, "ports_pathway_capacity"]) + 1
        assert any("RT-03" in p for p in contract.validate_scenario_table(bad, site))

    def test_name_drift_fails(self, valid):
        st, site = valid
        bad = st.copy()
        bad.loc[0, "site_name"] = bad.loc[0, "site_name"] + " Annex"
        assert any("RT-01" in p for p in contract.validate_scenario_table(bad, site))


class TestReconciliation:
    def test_rt04_reference_totals(self, v3_outputs):
        """The official totals are the canonical 25 / 47 (DEC-027); the run still reports the
        earlier legacy_v2 result, 25 / 48, as history."""
        out, result = v3_outputs
        assert result["starter_total_2026"] == 25
        assert result["pathway_total"] == 47
        assert result["plan_ranking"] == "milestone2_v3"
        assert (result["legacy_starter_total"], result["legacy_pathway_total"]) == (25, 47)
        assert (result["legacy_v2_result"]["starter_total"],
                result["legacy_v2_result"]["pathway_total"]) == (25, 48)

    def test_rt06_year_set(self, v3_outputs):
        out, _ = v3_outputs
        st = pd.read_csv(out / "contract/scenario_table.csv")
        assert set(st["horizon_year"]) == {2026, 2036, 2046, 2056}
        matlab = pd.read_csv(out / "matlab_scenarios.csv")
        assert set(matlab["horizon_year"]) == {2026, 2036, 2046, 2056}

    def test_matlab_port_counts_match_contract(self, v3_outputs):
        out, _ = v3_outputs
        st = pd.read_csv(out / "contract/scenario_table.csv")
        matlab = pd.read_csv(out / "matlab_scenarios.csv")
        merged = st.merge(matlab, left_on="scenario_id", right_on="scenario_id")
        assert len(merged) == len(st)
        assert (merged["ports_active"] == merged["ports"]).all()

    def test_capacity_basis_travels_to_matlab(self, v3_outputs):
        out, _ = v3_outputs
        matlab = pd.read_csv(out / "matlab_scenarios.csv")
        assert "capacity_basis" in matlab.columns
        assert matlab["capacity_basis"].notna().all()

    def test_zero_high_confidence_sites_preserved(self, v3_outputs):
        _, result = v3_outputs
        assert result["high_confidence_sites"] == 0

    def test_cost_emissions_reconcile_portfolio(self, v3_outputs):
        out, _ = v3_outputs
        st = pd.read_csv(out / "contract/scenario_table.csv")
        econ = pd.read_csv(out / "lifecycle_costs.csv")
        base_econ = econ[(econ.escalation_case == "base") & (econ.cost_case == "STG")]
        for hy in (2036, 2046, 2056):
            contract_sum = st[(st.horizon_year == hy) & (st.scenario_name == "base")]["lifecycle_cost_npv_usd"].sum()
            econ_sum = base_econ[base_econ.horizon_year == hy]["lifecycle_cost_npv_usd"].sum()
            assert abs(contract_sum - econ_sum) < 1.0

    def test_emissions_have_vintage_everywhere(self, v3_outputs):
        out, _ = v3_outputs
        st = pd.read_csv(out / "contract/scenario_table.csv")
        with_co2 = st[st["net_co2e_kg"].notna() & (st["net_co2e_kg"] != 0)]
        assert (with_co2["grid_factor_vintage"].str.len() > 5).all()
        assert (with_co2["grid_factor_value"] == 596.3).all()


class TestWorkflowAndDocs:
    def test_docs_match_steps_manifest(self):
        """PY-09: generated docs always match the executable step manifest."""
        docs = workflow.generate_docs()
        assert f"Step count: **{len(workflow.STEPS)}**" in docs
        for name, _ in workflow.STEPS:
            assert name in docs
        # And the committed copy is that output: it is regenerated, never edited by hand.
        assert (workflow.ROOT / "docs/WORKFLOW_STEPS.md").read_text() == docs, (
            "docs/WORKFLOW_STEPS.md is stale: run `python -m fcf_m2.workflow docs`")

    def test_legacy_mode_runs(self, tmp_path):
        result = workflow.run("legacy_v2", tmp_path / "leg")
        assert result["starter_total"] == 25 and result["pathway_total"] == 48

    def test_migration_report_written(self, v3_outputs):
        out, _ = v3_outputs
        mig = pd.read_csv(out / "scoring_migration_report.csv")
        assert {"legacy_score", "v3_anchor_score", "legacy_rank", "v3_anchor_rank",
                "rank_change", "explanation"} <= set(mig.columns)
        assert len(mig) == 12

    def test_peak_wait_outputs_exist(self, v3_outputs):
        out, _ = v3_outputs
        pw = pd.read_csv(out / "peak_wait_simulation.csv")
        assert {"p10_wait_min", "p50_wait_min", "p90_wait_min", "peak_p90_wait_min", "seed"} <= set(pw.columns)
        assert len(pw) == 12


class TestGisOffline:
    def test_offline_map_builds_without_network(self, sites, tmp_path, monkeypatch):
        """PY-06: map generation with networking conceptually disabled (module makes
        no network calls; env var set to assert intent)."""
        monkeypatch.setenv("FCF_OFFLINE", "1")
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
        from fcf_m2 import gis_offline
        s = sites.copy()
        s["model_rank"] = range(1, len(s) + 1)
        out = gis_offline.build_site_map(s, tmp_path / "map.png")
        assert out.exists() and out.stat().st_size > 10000


class TestVisualFooters:
    def test_every_chart_carries_footer(self, tmp_path):
        """PY-17 acceptance: automated QA finds no unlabeled chart."""
        import matplotlib.pyplot as plt
        from fcf_m2 import visuals
        log = tmp_path / "footer_log.json"
        fig, ax = plt.subplots()
        visuals.style_axes(ax)
        ax.bar(["a", "b"], [1, 2])
        visuals.footer(fig, "test source", "2026-07-19", "unit test")
        visuals.save(fig, tmp_path / "chart.png", log_path=log)
        assert visuals.audit_footer_metadata(log, tmp_path) == []

    def test_unlabeled_chart_detected(self, tmp_path):
        import matplotlib.pyplot as plt
        from fcf_m2 import visuals
        fig, ax = plt.subplots()
        ax.plot([1, 2])
        fig.savefig(tmp_path / "rogue.png")
        plt.close(fig)
        problems = visuals.audit_footer_metadata(tmp_path / "nolog.json", tmp_path)
        assert any("rogue" in p for p in problems)
