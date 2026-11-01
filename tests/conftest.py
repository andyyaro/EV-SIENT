import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fcf_m2.workflow import have_real_inputs  # noqa: E402

#: Files built from the private inputs that carry them: the study's results, which hold the inputs
#: column for column, and the 3D explorer's site data, whose score breakdown shows each input's
#: raw value. They are private too (DEC-016).
REAL_FIXTURES = ("tests/fixture_legacy_v2_site_results.csv", "tests/fixture_milestone2_v3_site_results.csv",
                 "explorer/web/data/sites.json", "explorer/web/data/sites.geojson",
                 "explorer/web/data/sites.inline.js")

#: Whether this checkout holds the reference study's private inputs. The public repository does
#: not, and runs everything that does not need them on the synthetic set (DEC-020).
HAVE_REAL_INPUTS = have_real_inputs() and all((ROOT / f).is_file() for f in REAL_FIXTURES)
NEEDS_REAL_INPUTS = ("needs the study's private inputs (data/inputs/, DEC-016), which this "
                     "checkout does not hold; it runs on the synthetic set instead (DEC-020)")

#: Fixtures that read the private inputs; a test that asks for one needs them.
REAL_INPUT_FIXTURES = {"sites", "risk", "golden_site_results", "scored_legacy"}

requires_real_inputs = pytest.mark.skipif(not HAVE_REAL_INPUTS, reason=NEEDS_REAL_INPUTS)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_inputs: needs the study's private inputs; skipped where they are absent")


def pytest_collection_modifyitems(config, items):
    if HAVE_REAL_INPUTS:
        return
    skip = pytest.mark.skip(reason=NEEDS_REAL_INPUTS)
    for item in items:
        if item.get_closest_marker("real_inputs") or REAL_INPUT_FIXTURES & set(item.fixturenames):
            item.add_marker(skip)


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
