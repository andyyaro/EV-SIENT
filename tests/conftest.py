import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="session")
def sites():
    return pd.read_csv(ROOT / "data/inputs/real_sites_v2.csv")


@pytest.fixture(scope="session")
def risk():
    return pd.read_csv(ROOT / "data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv")


@pytest.fixture(scope="session")
def anchors():
    from fcf_m2.scoring import load_anchor_set
    return load_anchor_set(ROOT / "data/anchors/anchor_set_v1.json")


@pytest.fixture(scope="session")
def golden_site_results():
    return pd.read_csv(ROOT / "tests/fixture_legacy_v2_site_results.csv")


@pytest.fixture(scope="session")
def golden_right_sizing():
    return pd.read_csv(ROOT / "tests/fixture_legacy_v2_right_sizing.csv")


@pytest.fixture(scope="session")
def scored_legacy(sites, risk):
    from fcf_m2.scoring import add_tiers, enrich_and_score
    df = enrich_and_score(sites, mode="legacy_v2")
    df = df.merge(risk[["site_id", "electrical_risk_level"]], on="site_id", how="left")
    return add_tiers(df)


@pytest.fixture(scope="session")
def v3_outputs(tmp_path_factory):
    """One full V3 run shared by integration tests."""
    from fcf_m2 import workflow
    out = tmp_path_factory.mktemp("v3run")
    result = workflow.run("milestone2_v3", out)
    return out, result
