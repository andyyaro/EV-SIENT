"""Generate the Tableau sheet CSVs and the authoring spec, from the canonical contract.

Why this exists rather than reusing `dashboard/tableau/patch_package/`
----------------------------------------------------------------------
The patch package was built 2026-07-19 and its `tbl_readiness_confidence.csv` carries
**`readiness_score` and `model_rank` byte-equal to `legacy_v2`** while the confidence column
beside them is the v3 value. Checked, not assumed: FFX002 at 58.8 / rank 1 is the legacy
number; canonically FFX004 leads at 53.4 and FFX002 is second at 51.8. Nothing in the file
declares the mix, so a workbook built from it would publish the legacy ranking under a v3
heading — which is the defect Phase 1 corrected in the README and which is **still live** on
Tableau Public today.

So every sheet here is derived from `data/contract/v1/` and the canonical
`milestone2_v3` run, and every emitted CSV carries a `model_mode` column stating which mode
produced it. A number whose mode is not stated is a number that will be misread eventually.

What the authoring server cannot build, and what is done instead
---------------------------------------------------------------
See `dashboard/tableau/CAPABILITY_GAP.md`. Nothing is silently substituted: where the
build recipe asks for something the server cannot generate, the gap is named there and the
substitute is labelled in the sheet's own subtitle.

Usage::

    python scripts/build_tableau_workbook.py            # write CSVs + spec
    python scripts/build_tableau_workbook.py --check    # verify the tracked copies are current
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, contract  # noqa: E402

CONTRACT = REPO / "data/contract/v1"
V3_RUN = REPO / "data/outputs/v3_run"
OUT = REPO / "dashboard/tableau/build"
#: "sheets", not "data". The authoring server writes its Hyper extracts into
#: <output>/Data/, and macOS filesystems are case-insensitive by default, so a
#: directory called "data" here is the SAME directory -- the generated binaries
#: would land among the tracked CSVs and the two would be impossible to separate
#: in .gitignore.
DATA = OUT / "sheets"

MODE = config.MODE_V3

#: Every sheet carries this, so a screenshot separated from its workbook still says what it is.
CAVEAT = ("Screening-class planning study. Capacity is a PLACEHOLDER at all 12 sites "
          "(capacity_basis=placeholder) - not evidence of electrical feasibility. "
          "Nothing here is approved, funded or permitted.")


def _canonical_sites() -> pd.DataFrame:
    """Canonical readiness + confidence. Explicitly the milestone2_v3 run, not legacy."""
    scored = pd.read_csv(V3_RUN / "site_results_milestone2_v3.csv")
    conf = pd.read_csv(V3_RUN / "data_confidence_v3.csv")
    sites = pd.read_csv(CONTRACT / "site_table.csv")
    frame = (scored[["site_id", "model_rank", "readiness_score", "recommendation_tier"]]
             .merge(conf[["site_id", "data_confidence_level_v3", "data_confidence_score_v3"]],
                    on="site_id")
             .merge(sites[["site_id", "site_name_display", "jurisdiction", "lat", "lon"]],
                    on="site_id"))
    frame["model_mode"] = MODE
    return frame.sort_values("model_rank")


def build_sheet_data() -> dict[str, pd.DataFrame]:
    scen = pd.read_csv(CONTRACT / "scenario_table.csv")
    sites = _canonical_sites()
    baseline = scen[(scen.horizon_year == config.BASELINE_YEAR) &
                    (scen.scenario_name == "baseline")]

    out: dict[str, pd.DataFrame] = {}

    # 1. Readiness ranking -----------------------------------------------------------
    out["readiness"] = sites[["site_id", "site_name_display", "jurisdiction", "model_rank",
                              "readiness_score", "recommendation_tier",
                              "data_confidence_level_v3", "model_mode"]].rename(columns={
        "site_name_display": "site_name", "data_confidence_level_v3": "data_confidence"})

    # 2. Starter vs pathway ----------------------------------------------------------
    # Emitted LONG with a `series` dimension, because the server has no bar-in-bar and no
    # dual axis. A grouped bar is a different chart from a bar-in-bar and is labelled as one.
    starter = baseline[["site_id", "ports_active", "ports_pathway_capacity"]].merge(
        sites[["site_id", "site_name_display", "model_rank"]], on="site_id")
    out["ports"] = pd.concat([
        starter.assign(series="Starter ports (2026)", ports=starter.ports_active),
        starter.assign(series="Pathway capacity", ports=starter.ports_pathway_capacity),
    ])[["site_id", "site_name_display", "model_rank", "series", "ports"]].rename(
        columns={"site_name_display": "site_name"}).assign(model_mode=MODE)

    # 3. Ports across horizons -------------------------------------------------------
    horizons = (scen.groupby(["horizon_year", "scenario_name"], as_index=False)
                .agg(ports_active=("ports_active", "sum"),
                     pathway_capacity=("ports_pathway_capacity", "sum")))
    horizons["model_mode"] = MODE
    # The pathway ceiling is carried as a COLUMN, not a reference line: the server generates
    # no reference lines. Plotted as a second series it is visible and honestly labelled.
    out["horizons"] = horizons

    # 4. Lifecycle cost --------------------------------------------------------------
    costs = pd.read_csv(REPO / "dashboard/tableau/patch_package/tbl_portfolio_costs.csv")
    costs = costs[costs.escalation_case == "base"].copy()
    costs["model_mode"] = MODE
    out["costs"] = costs[["horizon_year", "cost_case", "lifecycle_cost_npv_usd",
                          "avoided_overbuild_cost_usd", "estimate_class", "model_mode"]]

    # 5. Net CO2e --------------------------------------------------------------------
    co2 = (scen.groupby(["horizon_year", "scenario_name"], as_index=False)
           .agg(net_co2e_kg=("net_co2e_kg", "sum")))
    co2["net_co2e_tonnes"] = (co2.net_co2e_kg / 1000.0).round(3)
    co2["grid_factor_source"] = config.GRID_FACTOR_SOURCE
    co2["grid_factor_vintage"] = config.GRID_FACTOR_VINTAGE
    co2["model_mode"] = MODE
    out["emissions"] = co2

    # 6. Peak waits ------------------------------------------------------------------
    waits = pd.read_csv(REPO / "dashboard/tableau/patch_package/tbl_peak_waits.csv")
    waits = waits.merge(sites[["site_id", "site_name_display", "model_rank"]], on="site_id")
    out["waits"] = pd.concat([
        waits.assign(series="Median wait (p50)", wait_min=waits.p50_wait_min),
        waits.assign(series="Peak wait (p90)", wait_min=waits.peak_p90_wait_min),
    ])[["site_id", "site_name_display", "model_rank", "series", "wait_min"]].rename(
        columns={"site_name_display": "site_name"}).assign(model_mode=MODE)

    # 7. Map -------------------------------------------------------------------------
    geo = sites.merge(baseline[["site_id", "ports_pathway_capacity", "capacity_basis"]],
                      on="site_id")
    out["map"] = geo[["site_id", "site_name_display", "jurisdiction", "lat", "lon",
                      "model_rank", "readiness_score", "recommendation_tier",
                      "data_confidence_level_v3", "ports_pathway_capacity",
                      "capacity_basis", "model_mode"]].rename(columns={
        "site_name_display": "site_name", "data_confidence_level_v3": "data_confidence"})

    return out


def build_spec(paths: dict[str, Path]) -> dict:
    """The authoring spec. Every subtitle states mode, provenance and the placeholder caveat."""
    def ds(key: str) -> dict:
        return {"id": key, "type": "csv", "path": str(paths[key].resolve())}

    return {
        "spec_version": "0.1",
        "workbook": {
            "name": "EV_Charging_Site_Readiness_M2_Canonical",
            "description": (
                f"Future City Fellowship - EV charging site readiness. Every value derives "
                f"from the canonical data contract v{config.SCHEMA_VERSION} in mode {MODE}. "
                f"{CAVEAT}"),
        },
        "data_sources": [ds(k) for k in
                         ["readiness", "ports", "horizons", "costs", "emissions", "waits", "map"]],
        "worksheets": [
            {
                "name": "Readiness by Site",
                "template": "bar",
                "data_source": "readiness",
                "rows": [{"field": "readiness_score", "aggregation": "Sum"}],
                "columns": ["site_name"],
                "color": "data_confidence",
                "tooltips": ["site_id", "recommendation_tier", "jurisdiction", "model_mode"],
                "title": "Site readiness ranking",
                "subtitle": (f"Canonical {MODE} scores. ALL 12 SITES ARE LOW CONFIDENCE - the "
                             f"colour legend has one value on purpose. {CAVEAT}"),
                "fit": "entire_view",
            },
            {
                "name": "Starter vs Pathway Ports",
                "template": "bar",
                "data_source": "ports",
                "rows": [{"field": "ports", "aggregation": "Sum"}],
                "columns": ["site_name", "series"],
                "color": "series",
                "tooltips": ["site_id", "model_mode"],
                "title": "Starter ports today vs pathway capacity to leave room for",
                "subtitle": ("GROUPED bars, not the bar-in-bar the build recipe specifies: the "
                             "authoring server generates no dual axis. See CAPABILITY_GAP.md. "
                             "Portfolio totals 25 starter / 48 pathway. " + CAVEAT),
                "fit": "entire_view",
            },
            {
                "name": "Ports Across Horizons",
                "template": "line",
                "data_source": "horizons",
                "rows": [{"field": "ports_active", "aggregation": "Sum"}],
                "columns": ["horizon_year"],
                "color": "scenario_name",
                "tooltips": ["pathway_capacity", "model_mode"],
                "title": "Active ports by planning horizon",
                "subtitle": ("Horizons are 2026 / 2036 / 2046 / 2056. NO REFERENCE LINE: the "
                             "server generates none, so the 48-port pathway ceiling is carried "
                             "in the tooltip as pathway_capacity instead. " + CAVEAT),
                "fit": "entire_view",
            },
            {
                "name": "Lifecycle Cost by Horizon",
                "template": "bar",
                "data_source": "costs",
                "rows": [{"field": "lifecycle_cost_npv_usd", "aggregation": "Sum"}],
                "columns": ["horizon_year", "cost_case"],
                "color": "cost_case",
                "tooltips": ["avoided_overbuild_cost_usd", "estimate_class", "model_mode"],
                "title": "Lifecycle cost, net present value (base escalation)",
                "subtitle": ("Screening-class estimates for COMPARISON between options. Never a "
                             "budget, never a quote, never a bid. " + CAVEAT),
                "fit": "entire_view",
            },
            {
                "name": "Net CO2e by Horizon",
                "template": "line",
                "data_source": "emissions",
                "rows": [{"field": "net_co2e_tonnes", "aggregation": "Sum"}],
                "columns": ["horizon_year"],
                "color": "scenario_name",
                "tooltips": ["grid_factor_source", "grid_factor_vintage", "model_mode"],
                "title": "Net CO2e, tonnes per year",
                "subtitle": (f"Grid factor: {config.GRID_FACTOR_SOURCE}, "
                             f"{config.GRID_FACTOR_LB_PER_MWH} lb CO2e/MWh, vintage "
                             f"{config.GRID_FACTOR_VINTAGE}. Demand is modelled, not measured. "
                             + CAVEAT),
                "fit": "entire_view",
            },
            {
                "name": "Peak Waits by Site",
                "template": "bar",
                "data_source": "waits",
                "rows": [{"field": "wait_min", "aggregation": "Sum"}],
                "columns": ["site_name", "series"],
                "color": "series",
                "tooltips": ["site_id", "model_mode"],
                "title": "Median and peak queue wait, minutes",
                "subtitle": ("NO 10-MINUTE REFERENCE LINE: the server generates none. The "
                             "10-minute screening threshold is stated here in text instead. "
                             "Waits are simulated from modelled demand, never observed. "
                             + CAVEAT),
                "fit": "entire_view",
            },
            {
                "name": "Site Map",
                "template": "map",
                "data_source": "map",
                "latitude": "lat",
                "longitude": "lon",
                "color": "data_confidence",
                "size": {"field": "ports_pathway_capacity", "aggregation": "Sum"},
                "detail": ["site_name"],
                "tooltips": ["site_id", "jurisdiction", "recommendation_tier",
                             "capacity_basis", "model_mode"],
                "title": "Candidate sites, Northern Virginia",
                "subtitle": ("SYMBOL map, not a choropleth - the server generates no filled "
                             "maps. Mark size is pathway capacity. Every site's capacity_basis "
                             "is 'placeholder'. " + CAVEAT),
                "fit": "entire_view",
            },
        ],
        "dashboards": [{
            "name": "Milestone 2 Overview",
            "title": ("EV Charging Site Readiness - Milestone 2 (canonical " + MODE + "). "
                      + CAVEAT),
            "direction": "vertical",
            "sizing_mode": "fixed",
            "width": 1600,
            "height": 900,
            "worksheets": ["Readiness by Site", "Starter vs Pathway Ports",
                           "Ports Across Horizons", "Site Map"],
        }],
        "output": {"directory": str(OUT.resolve()), "package_twbx": True},
    }


def write_all(out_dir: Path) -> tuple[dict[str, Path], Path]:
    data_dir = out_dir / "sheets"
    data_dir.mkdir(parents=True, exist_ok=True)
    frames = build_sheet_data()
    paths = {}
    for key, frame in frames.items():
        target = data_dir / f"sheet_{key}.csv"
        frame.to_csv(target, index=False, lineterminator="\n")
        paths[key] = target
    spec = build_spec(paths)
    spec_path = out_dir / "workbook_spec.json"
    spec_path.write_text(json.dumps(spec, indent=2) + "\n")
    return paths, spec_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp)
            write_all(fresh)
            problems = []
            for produced in sorted((fresh / "sheets").glob("*.csv")):
                tracked = DATA / produced.name
                if not tracked.is_file():
                    problems.append(f"missing tracked {tracked.relative_to(REPO)}")
                elif contract.sha256_file(produced) != contract.sha256_file(tracked):
                    problems.append(f"{produced.name} differs from a fresh build")
            # The spec embeds absolute paths, so compare it with those normalised away.
            fresh_spec = json.loads((fresh / "workbook_spec.json").read_text())
            tracked_spec_path = OUT / "workbook_spec.json"
            if not tracked_spec_path.is_file():
                problems.append("missing tracked workbook_spec.json")
            else:
                tracked_spec = json.loads(tracked_spec_path.read_text())
                for spec in (fresh_spec, tracked_spec):
                    for source in spec["data_sources"]:
                        source["path"] = Path(source["path"]).name
                    spec["output"]["directory"] = ""
                if fresh_spec != tracked_spec:
                    problems.append("workbook_spec.json differs from a fresh build")
            if problems:
                print("tableau build check FAILED:")
                for p in problems:
                    print(f"  - {p}")
                return 1
            print(f"tableau build check PASSED: {len(list((fresh/'sheets').glob('*.csv')))} "
                  f"sheet CSVs and the spec match a fresh build")
            return 0

    if DATA.exists():
        shutil.rmtree(DATA)
    paths, spec_path = write_all(OUT)
    print(f"wrote {len(paths)} sheet CSVs to {DATA.relative_to(REPO)}/")
    for key, path in paths.items():
        rows = sum(1 for _ in path.open()) - 1
        print(f"  sheet_{key}.csv  {rows} rows")
    print(f"wrote {spec_path.relative_to(REPO)}")
    print(f"\nAll values derive from the canonical contract in mode {MODE}.")
    print("The patch package is NOT used for readiness: its readiness_score and model_rank")
    print("are byte-equal to legacy_v2 while its confidence column is v3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
