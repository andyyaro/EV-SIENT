"""The Tableau workbook says what the contract says, and it does not drift.

Gate on the `.twb`, NEVER on the `.twbx` digest
----------------------------------------------
The `.twbx` is **not byte-reproducible**: the embedded Hyper extracts carry non-deterministic
engine state, so building the same spec twice produces different archive digests. The `.twb`
inside it **is** deterministic for an identical spec.

This repository gates generated artifacts on drift, so pinning the package digest would fail
CI on every single run for no reason at all, and the gate would be deleted within a week -
taking the real check with it. **If you are here to "fix" a flaky Tableau digest test: this
is why it gates the `.twb`. Do not add a `.twbx` digest assertion.**

Measured rather than taken on faith. Two consecutive builds from a byte-identical spec,
2026-07-27::

    .twb    f9dbe9f302b7e289…   f9dbe9f302b7e289…   IDENTICAL
    .twbx   48358f1dc468f374…   f8ffa1af7bd6fa4a…   DIFFERENT

What the sheet data must satisfy
--------------------------------
The workbook's whole purpose is to present the contract, so its inputs are checked against
the contract rather than against a snapshot of themselves. A snapshot test would happily
freeze a wrong number - which is exactly what happened to the live published workbook, whose
readiness scores are `legacy_v2` values sitting under a v3 heading.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, contract  # noqa: E402

BUILD = REPO / "dashboard/tableau/build"
DATA = BUILD / "sheets"
TWB = BUILD / "EV_Charging_Site_Readiness_M2_Canonical.twb"
CONTRACT = REPO / "data/contract/v1"
V3_RUN = REPO / "data/outputs/v3_run"


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    return pd.read_csv(CONTRACT / "scenario_table.csv")


def sheet(name: str) -> pd.DataFrame:
    path = DATA / f"sheet_{name}.csv"
    assert path.is_file(), f"{path.relative_to(REPO)} missing; run scripts/build_tableau_workbook.py"
    return pd.read_csv(path)


# ------------------------------------------------------------------ contract agreement

def test_port_totals_match_the_contract(scenarios):
    base = scenarios[(scenarios.horizon_year == config.BASELINE_YEAR) &
                     (scenarios.scenario_name == "baseline")]
    ports = sheet("ports")
    by_series = ports.groupby("series").ports.sum().to_dict()
    assert by_series["Starter ports (2026)"] == int(base.ports_active.sum()) == 25
    assert by_series["Pathway capacity"] == int(base.ports_pathway_capacity.sum()) == 48


def test_horizons_are_canonical_not_the_retired_vocabulary():
    """The live published workbook uses 2035 and 2050. Those are the V2 horizons, retired by
    the V3 restructure. This is the check that would have caught it."""
    years = sorted(sheet("horizons").horizon_year.unique())
    assert years == [config.BASELINE_YEAR, *config.V3_HORIZONS] == [2026, 2036, 2046, 2056]
    for name in ["horizons", "emissions", "costs"]:
        present = set(sheet(name).horizon_year.unique())
        assert not (present & {2035, 2050}), f"sheet_{name} carries a retired horizon"


@pytest.fixture(scope="module", autouse=True)
def _canonical_run_present():
    """`data/outputs/` is gitignored, so a clean checkout has no canonical run. Generate it
    rather than skipping: a test that quietly skips on CI is a test that does not exist."""
    import importlib.util
    loader = importlib.util.spec_from_file_location(
        "_fcf_tab_fixture", REPO / "scripts/build_tableau_workbook.py")
    mod = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mod)
    mod.ensure_v3_run()


@pytest.mark.real_inputs
def test_readiness_is_canonical_v3_not_legacy():
    """The single most consequential check in this file.

    The published workbook and the patch package both carry `legacy_v2` readiness, under
    which FFX002 ranks first at 58.8. Canonically FFX004 ranks first at 53.4. A workbook
    built from the wrong column names the wrong top site.
    """
    r = sheet("readiness").sort_values("model_rank")
    v3 = pd.read_csv(V3_RUN / "site_results_milestone2_v3.csv")
    legacy = pd.read_csv(V3_RUN / "site_results_legacy_v2.csv")

    merged = r.merge(v3[["site_id", "readiness_score", "model_rank"]], on="site_id",
                     suffixes=("_sheet", "_v3"))
    assert (merged.readiness_score_sheet.round(6) == merged.readiness_score_v3.round(6)).all()
    assert (merged.model_rank_sheet == merged.model_rank_v3).all()

    legacy_scores = dict(zip(legacy.site_id, legacy.readiness_score))
    differs = [s for s in r.site_id
               if round(float(r.set_index("site_id").readiness_score[s]), 6)
               != round(float(legacy_scores[s]), 6)]
    assert differs, "the sheet matches legacy_v2 exactly; it is built from the wrong column"

    assert r.iloc[0].site_id == "FFX004", f"top site is {r.iloc[0].site_id}, expected FFX004"
    assert round(float(r.iloc[0].readiness_score), 1) == 53.4


def test_every_site_is_low_confidence():
    """The published workbook tells 1 000+ viewers that 8 of 12 sites are Medium confidence.
    No output of this model produces Medium for any site. All twelve are Low."""
    r = sheet("readiness")
    assert len(r) == 12
    assert set(r.data_confidence.unique()) == {"Low"}


def test_capacity_is_placeholder_everywhere_in_the_map_sheet():
    assert set(sheet("map").capacity_basis.unique()) == {"placeholder"}


def test_every_sheet_declares_its_model_mode():
    """A number whose mode is not stated is a number that gets misread eventually -- which is
    precisely how the legacy scores ended up published under a v3 heading."""
    for name in ["readiness", "ports", "horizons", "costs", "emissions", "waits", "map"]:
        frame = sheet(name)
        assert "model_mode" in frame.columns, f"sheet_{name} does not declare model_mode"
        assert set(frame.model_mode.unique()) == {config.MODE_V3}


def test_emissions_carry_the_grid_factor_provenance():
    e = sheet("emissions")
    assert (e.grid_factor_source == config.GRID_FACTOR_SOURCE).all()
    assert (e.grid_factor_vintage == config.GRID_FACTOR_VINTAGE).all()


def test_map_coordinates_are_in_northern_virginia():
    m = sheet("map")
    assert len(m) == 12
    assert m.lat.between(38.5, 39.1).all() and m.lon.between(-77.8, -77.0).all()


# ------------------------------------------------------------------ drift

@pytest.mark.real_inputs
def test_sheet_data_and_spec_rebuild_identically():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_tableau_workbook.py"), "--check"],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_twb_is_tracked_and_parses_as_xml():
    """Gated on the .twb, deliberately -- see this module's docstring for why the .twbx
    digest is NOT gated and must not be."""
    import xml.etree.ElementTree as ET
    assert TWB.is_file(), "the .twb is not tracked; the workbook cannot be reviewed in a diff"
    root = ET.parse(TWB).getroot()
    assert root.tag == "workbook"


def test_the_twb_declares_every_worksheet_and_the_dashboard():
    import xml.etree.ElementTree as ET
    root = ET.parse(TWB).getroot()
    sheets = {w.get("name") for w in root.iter("worksheet")}
    expected = {"Readiness by Site", "Starter vs Pathway Ports", "Ports Across Horizons",
                "Lifecycle Cost by Horizon", "Net CO2e by Horizon", "Peak Waits by Site",
                "Site Map"}
    assert expected <= sheets, f"missing worksheets: {expected - sheets}"
    dashboards = {d.get("name") for d in root.iter("dashboard")}
    assert "Milestone 2 Overview" in dashboards


def test_the_twb_carries_the_placeholder_caveat_on_every_sheet():
    """A screenshot separated from its workbook must still say what it is."""
    text = TWB.read_text(encoding="utf-8", errors="replace")
    assert "CAPACITY IS A PLACEHOLDER AT ALL 12 SITES" in text
    assert "not evidence of electrical feasibility" in text
    # Every sheet still states its own most important limitation, even though the full
    # caveat now lives once in the dashboard title: repeating three sentences on seven
    # sheets is what pushed the subtitles into overlapping their own titles on the
    # published render.
    for claim in ["LOW data confidence", "capacity_basis is 'placeholder'",
                  "modelled, not measured", "Never a budget"]:
        assert claim in text, f"a sheet lost its own limitation: {claim}"


def test_the_twb_does_not_carry_the_retired_horizons():
    text = TWB.read_text(encoding="utf-8", errors="replace")
    for retired in ("2035", "2050"):
        assert retired not in text, f"the workbook mentions the retired horizon {retired}"


def test_the_twb_names_its_substitutions_rather_than_hiding_them():
    """Every capability gap is declared in the sheet that is affected by it."""
    text = TWB.read_text(encoding="utf-8", errors="replace")
    for declaration in ("not bar-in-bar",
                        "no reference line",
                        "10-minute screening threshold",
                        "not a choropleth"):
        assert declaration in text, f"the workbook does not declare: {declaration}"


def test_horizons_are_a_DIMENSION_not_a_measure():
    """The defect this pins: `horizon_year` is an integer, so type inference made it a
    MEASURE. On the Columns shelf that is a continuous numeric axis -- which drew tick marks
    at 2028, 2030, 2032 between the only four horizons that exist, and left one sheet
    published as a title with no chart under it at all.

    A year is a category here, not a quantity. There is no 2041 to interpolate to. The string
    column `horizon` is what the time-series sheets plot against.
    """
    import json
    spec = json.loads((BUILD / "workbook_spec.json").read_text())
    by_name = {w["name"]: w for w in spec["worksheets"]}
    for name in ["Ports Across Horizons", "Net CO2e by Horizon", "Lifecycle Cost by Horizon"]:
        assert "horizon" in by_name[name]["columns"], (
            f"{name} does not plot against the string `horizon` column; if it is back on "
            f"`horizon_year` the axis is continuous again")

    for sheet_name in ["horizons", "emissions", "costs"]:
        frame = sheet(sheet_name)
        assert "horizon" in frame.columns
        # Every label must contain a LETTER. Writing str(2026) was not enough: the CSV holds
        # a bare 2026, the reader infers integer, and it becomes a measure again -- which is
        # what published two blank charts.
        assert frame.horizon.map(lambda v: any(ch.isalpha() for ch in str(v))).all(), (
            "a horizon label is purely numeric; it will be read back as a measure")
        # ...and it must still lead with its own year, so the axis sorts chronologically.
        assert all(str(v).startswith(str(int(y)))
                   for v, y in zip(frame.horizon, frame.horizon_year))


def test_site_labels_are_short_enough_to_render():
    """Tableau truncated 34-character site names to '01 Fairfa..' on the axis. Anything past
    ~30 characters is a fragment, not a label. The full name stays on the tooltip."""
    for sheet_name in ["readiness", "ports", "waits", "map"]:
        frame = sheet(sheet_name)
        longest = max(len(x) for x in frame.site_ranked)
        assert longest <= 32, f"sheet_{sheet_name} has a {longest}-character axis label"
        assert "site_name" in frame.columns, "the full name must survive for the tooltip"


def test_site_charts_are_horizontal_so_the_labels_have_room():
    """A dimension on ROWS and a measure on COLUMNS is a horizontal bar, which gives each of
    the twelve long site names a whole row instead of a truncated tick."""
    import json
    spec = json.loads((BUILD / "workbook_spec.json").read_text())
    by_name = {w["name"]: w for w in spec["worksheets"]}
    for name in ["Readiness by Site", "Starter vs Pathway Ports", "Peak Waits by Site"]:
        w = by_name[name]
        assert w["rows"][0] == "site_ranked", f"{name} is not a horizontal bar"
        assert isinstance(w["columns"][0], dict), f"{name} has no measure on columns"


def test_two_series_charts_are_grouped_not_stacked():
    """`series` on colour ALONE makes Tableau stack the bars, and the published render showed
    FFX004 as 3 + 8 = 11 ports -- a number that does not exist, because starter and pathway
    are not additive. `series` must also be on rows, which nests and groups them."""
    import json
    spec = json.loads((BUILD / "workbook_spec.json").read_text())
    by_name = {w["name"]: w for w in spec["worksheets"]}
    for name in ["Starter vs Pathway Ports", "Peak Waits by Site"]:
        assert by_name[name]["rows"] == ["site_ranked", "series"], (
            f"{name} has series only on colour, so its bars stack into a false total")


@pytest.mark.real_inputs
def test_no_chart_plots_a_constant_measure():
    """One shipped: peak waits plotted p50 and p90, both 0.0 at all twelve sites, and it
    published as axis labels with no bars. The build now refuses; this pins it."""
    import importlib.util
    spec_file = REPO / "scripts/build_tableau_workbook.py"
    loader = importlib.util.spec_from_file_location("_fcf_tab", spec_file)
    mod = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mod)
    frames = mod.build_sheet_data()
    mod.refuse_uninformative_measures(frames)          # must not raise
    for sheet_name, column in mod.PLOTTED_MEASURES:
        assert frames[sheet_name][column].nunique(dropna=True) > 1, (
            f"{sheet_name}.{column} is constant; a chart of it draws nothing")


def test_the_build_manifest_records_what_was_produced():
    manifest = BUILD / "EV_Charging_Site_Readiness_M2_Canonical.manifest.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text())
    assert data, "manifest is empty"
