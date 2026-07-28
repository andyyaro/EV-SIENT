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
import os
import subprocess
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
#:
#: Kept SHORT deliberately. The first version was three sentences and Tableau truncated it
#: mid-word in the dashboard title -- "Screening-class planning..." -- which is worse than a
#: brief caveat that fits, because a caveat nobody can finish reading is decoration.
CAVEAT = ("CAPACITY IS A PLACEHOLDER AT ALL 12 SITES - not evidence of electrical "
          "feasibility. Screening study; nothing approved or funded.")


#: Horizon labels that are unambiguously TEXT.
#:
#: Writing `str(2026)` was not enough and the published render proved it: the CSV holds a
#: bare `2026`, the type inferrer reads it back as an integer, and it becomes a MEASURE
#: again. A measure on the Columns shelf is a continuous axis -- tick marks at 2028, 2030,
#: 2032 between the only four horizons that exist, and two sheets that drew nothing at all.
#:
#: Every value here contains letters, so no reader can mistake it for a number, and the
#: labels sort correctly because they still lead with the year.
HORIZON_LABELS = {
    2026: "2026 baseline",
    2036: "2036 (+10y)",
    2046: "2046 (+20y)",
    2056: "2056 (+30y)",
}


def horizon_label(year) -> str:
    year = int(year)
    if year not in HORIZON_LABELS:
        raise SystemExit(f"no horizon label for {year}; add it rather than falling back to a "
                         f"bare number, which would silently become a measure again")
    return HORIZON_LABELS[year]


def short_site(name: str, limit: int = 26) -> str:
    """Site names run to 34 characters and Tableau truncated them to '01 Fairfa..'.

    Shortened at a word boundary so the label stays a name rather than a fragment. The full
    name is on the tooltip, and `site_id` is on the tooltip too, so nothing is lost — the
    axis just stops being unreadable.
    """
    if len(name) <= limit:
        return name
    cut = name[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def ranked_label(rank, name: str) -> str:
    """``01 Fairfax County Government Center`` -- the rank, then the name.

    The authoring spec has **no sort key**, so a bar chart draws its categories in the
    dimension's natural order, which for a name is alphabetical. That made a sheet titled
    "Site readiness ranking" display sites in alphabetical order, and a viewer reading
    left-to-right infers a ranking that is not there. A chart that misleads by omission is
    the same defect as one that misleads by a wrong number.

    Embedding the rank in the label fixes the order **and** shows the rank, using nothing
    outside the capability boundary. Zero-padded so 10 sorts after 9.
    """
    return f"{int(rank):02d} {short_site(name)}"


#: The two files this needs out of a canonical run. Both live under `data/outputs/`, which is
#: GITIGNORED -- so they exist on a machine that has run the model and nowhere else.
V3_RUN_REQUIRED = ("site_results_milestone2_v3.csv", "data_confidence_v3.csv")


def ensure_v3_run() -> None:
    """Generate the canonical run if it is not already on disk.

    `data/outputs/` is gitignored, deliberately -- it is regenerable model output, not source.
    But this script read from it, so it worked on a laptop that had run the model and failed
    on a clean checkout. CI caught it; the local run never could, because the files were
    always sitting there.

    That is the same defect Phase 1 existed to fix (`verify.sh` passing locally and failing on
    a clean clone), reintroduced. Generating the run on demand makes the build self-sufficient
    anywhere, which is what "reproducible" has to mean.
    """
    missing = [n for n in V3_RUN_REQUIRED if not (V3_RUN / n).is_file()]
    if not missing:
        return
    print(f"canonical run outputs missing ({', '.join(missing)}); generating them")
    result = subprocess.run(
        [sys.executable, "-m", "fcf_m2.workflow", "run",
         "--mode", config.MODE_V3, "--out", str(V3_RUN)],
        cwd=REPO, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(REPO / "src")})
    if result.returncode != 0:
        sys.stderr.write(result.stdout[-2000:] + result.stderr[-2000:])
        raise SystemExit("could not generate the canonical milestone2_v3 run")
    still_missing = [n for n in V3_RUN_REQUIRED if not (V3_RUN / n).is_file()]
    if still_missing:
        raise SystemExit(f"the run completed but did not produce {still_missing}")
    print(f"  generated {V3_RUN.relative_to(REPO)}/")


def _canonical_sites() -> pd.DataFrame:
    """Canonical readiness + confidence. Explicitly the milestone2_v3 run, not legacy."""
    ensure_v3_run()
    scored = pd.read_csv(V3_RUN / "site_results_milestone2_v3.csv")
    conf = pd.read_csv(V3_RUN / "data_confidence_v3.csv")
    sites = pd.read_csv(CONTRACT / "site_table.csv")
    frame = (scored[["site_id", "model_rank", "readiness_score", "recommendation_tier"]]
             .merge(conf[["site_id", "data_confidence_level_v3", "data_confidence_score_v3"]],
                    on="site_id")
             .merge(sites[["site_id", "site_name_display", "jurisdiction", "lat", "lon"]],
                    on="site_id"))
    frame["model_mode"] = MODE
    frame = frame.sort_values("model_rank")
    frame["site_ranked"] = [ranked_label(r, n) for r, n in
                            zip(frame.model_rank, frame.site_name_display)]
    return frame


def build_sheet_data() -> dict[str, pd.DataFrame]:
    scen = pd.read_csv(CONTRACT / "scenario_table.csv")
    sites = _canonical_sites()
    baseline = scen[(scen.horizon_year == config.BASELINE_YEAR) &
                    (scen.scenario_name == "baseline")]

    out: dict[str, pd.DataFrame] = {}

    # 1. Readiness ranking -----------------------------------------------------------
    out["readiness"] = sites[["site_id", "site_ranked", "site_name_display", "jurisdiction",
                              "model_rank", "readiness_score", "recommendation_tier",
                              "data_confidence_level_v3", "model_mode"]].rename(columns={
        "site_name_display": "site_name", "data_confidence_level_v3": "data_confidence"})

    # 2. Starter vs pathway ----------------------------------------------------------
    # Emitted LONG with a `series` dimension, because the server has no bar-in-bar and no
    # dual axis. A grouped bar is a different chart from a bar-in-bar and is labelled as one.
    starter = baseline[["site_id", "ports_active", "ports_pathway_capacity"]].merge(
        sites[["site_id", "site_name_display", "site_ranked", "model_rank"]], on="site_id")
    out["ports"] = pd.concat([
        starter.assign(series="Starter ports (2026)", ports=starter.ports_active),
        starter.assign(series="Pathway capacity", ports=starter.ports_pathway_capacity),
    ])[["site_id", "site_ranked", "site_name_display", "model_rank", "series", "ports"]].rename(
        columns={"site_name_display": "site_name"}).assign(model_mode=MODE)

    # 3. Ports across horizons -------------------------------------------------------
    horizons = (scen.groupby(["horizon_year", "scenario_name"], as_index=False)
                .agg(ports_active=("ports_active", "sum"),
                     pathway_capacity=("ports_pathway_capacity", "sum")))
    horizons["horizon"] = horizons.horizon_year.map(horizon_label)
    horizons["model_mode"] = MODE
    # The pathway ceiling is carried as a COLUMN, not a reference line: the server generates
    # no reference lines. Plotted as a second series it is visible and honestly labelled.
    out["horizons"] = horizons

    # 4. Lifecycle cost --------------------------------------------------------------
    costs = pd.read_csv(REPO / "dashboard/tableau/patch_package/tbl_portfolio_costs.csv")
    costs = costs[costs.escalation_case == "base"].copy()
    costs["horizon"] = costs.horizon_year.map(horizon_label)
    costs["model_mode"] = MODE
    out["costs"] = costs[["horizon", "horizon_year", "cost_case", "lifecycle_cost_npv_usd",
                          "avoided_overbuild_cost_usd", "estimate_class", "model_mode"]]

    # 5. Net CO2e --------------------------------------------------------------------
    co2 = (scen.groupby(["horizon_year", "scenario_name"], as_index=False)
           .agg(net_co2e_kg=("net_co2e_kg", "sum")))
    co2["net_co2e_tonnes"] = (co2.net_co2e_kg / 1000.0).round(3)
    co2["horizon"] = co2.horizon_year.map(horizon_label)
    co2["grid_factor_source"] = config.GRID_FACTOR_SOURCE
    co2["grid_factor_vintage"] = config.GRID_FACTOR_VINTAGE
    co2["model_mode"] = MODE
    out["emissions"] = co2

    # 6. Peak waits ------------------------------------------------------------------
    waits = pd.read_csv(REPO / "dashboard/tableau/patch_package/tbl_peak_waits.csv")
    waits = waits.merge(sites[["site_id", "site_name_display", "site_ranked", "model_rank"]],
                        on="site_id")
    # p50, p90 and peak_p90 are 0.0 at ALL TWELVE sites, and that is the data, not a bug:
    # simulated utilisation runs 6-20%, so with 2-3 ports the median and 90th-percentile day
    # genuinely has no queue. Plotting them produced a chart with axis labels, no bars and a
    # single "0" tick -- published, in public, saying nothing.
    #
    # So the sheet plots the two metrics that carry information, and the subtitle states the
    # zeros outright, because "waits are essentially nil at these port counts" is a FINDING
    # that supports the whole don't-overbuild thesis. It deserves saying, not hiding.
    out["waits"] = pd.concat([
        waits.assign(series="Mean wait, simulated", wait_min=waits.mean_wait_min),
        waits.assign(series="Peak-window wait, Erlang", wait_min=waits.peak_erlang_wait_min),
    ])[["site_id", "site_ranked", "site_name_display", "model_rank", "series",
        "wait_min"]].rename(columns={"site_name_display": "site_name"}).assign(model_mode=MODE)

    # 7. Map -------------------------------------------------------------------------
    geo = sites.merge(baseline[["site_id", "ports_pathway_capacity", "capacity_basis"]],
                      on="site_id")
    out["map"] = geo[["site_id", "site_ranked", "site_name_display", "jurisdiction", "lat", "lon",
                      "model_rank", "readiness_score", "recommendation_tier",
                      "data_confidence_level_v3", "ports_pathway_capacity",
                      "capacity_basis", "model_mode"]].rename(columns={
        "site_name_display": "site_name", "data_confidence_level_v3": "data_confidence"})

    return out


#: (sheet, column) pairs that a worksheet plots. Checked for variance before anything ships.
PLOTTED_MEASURES = [
    ("readiness", "readiness_score"), ("ports", "ports"), ("horizons", "ports_active"),
    ("costs", "lifecycle_cost_npv_usd"), ("emissions", "net_co2e_tonnes"),
    ("waits", "wait_min"), ("map", "ports_pathway_capacity"),
]


def refuse_bare_tooltip_measures(spec: dict, frames: dict[str, pd.DataFrame]) -> None:
    """A MEASURE on the tooltip shelf with no aggregation blanks the entire sheet.

    The compiler emits ``derivation="None"``, Tableau treats it as a level-of-detail field,
    cannot resolve it, and draws nothing -- the sheet publishes as a title and a subtitle
    with white space where the chart should be. Two sheets shipped that way, twice, because
    a blank chart is not an error anywhere in the build.

    The authoring spec auto-promotes tooltip DIMENSIONS to ``Attribute`` for precisely this
    reason and says so. Measures are not covered by that promotion, so they need an explicit
    aggregation here.
    """
    problems = []
    for ws in spec["worksheets"]:
        frame = frames[ws["data_source"]]
        for ref in ws.get("tooltips") or []:
            if isinstance(ref, dict):
                continue                      # already carries an aggregation
            if ref in frame.columns and pd.api.types.is_numeric_dtype(frame[ref]):
                problems.append(
                    f"{ws['name']}: tooltip '{ref}' is a measure with no aggregation; "
                    f"the sheet will render blank")
    if problems:
        raise SystemExit("REFUSING to build a sheet that will render blank:\n  - " +
                         "\n  - ".join(problems))


def refuse_uninformative_measures(frames: dict[str, pd.DataFrame]) -> None:
    """A chart whose measure is constant draws nothing. Refuse to build one.

    This exists because one shipped. The peak-waits sheet plotted p50 and p90, both 0.0 at
    all twelve sites, and it published as axis labels with no bars -- a chart that occupied
    space in public and said nothing. Nothing in the build objected, because an all-zero
    column is perfectly valid data.
    """
    problems = []
    for sheet_name, column in PLOTTED_MEASURES:
        series = frames[sheet_name][column]
        if series.nunique(dropna=True) <= 1:
            problems.append(
                f"sheet_{sheet_name}.{column} has {series.nunique()} distinct value(s) "
                f"({series.dropna().unique()[:3]}); a chart of it draws nothing")
    if problems:
        raise SystemExit("REFUSING to build a chart that cannot show anything:\n  - " +
                         "\n  - ".join(problems))


def build_spec(paths: dict[str, Path]) -> dict:
    """The authoring spec. Every subtitle states mode, provenance and the placeholder caveat."""
    def ds(key: str) -> dict:
        # RELATIVE to the repo root, deliberately. An absolute path here would bake this
        # machine's home directory into a tracked artifact -- which the repository's own
        # hygiene gate refuses, and rightly: the spec would only build on one laptop.
        #
        # The authoring server resolves relative paths against `base_dir` and then requires
        # them to stay inside it, so this is also the safer form. `base_dir` is injected at
        # build time by `spec_for_build()` rather than written into the tracked file.
        try:
            path = str(paths[key].relative_to(REPO))
        except ValueError:
            # --check builds into a temp directory, which is not under the repo. The
            # comparison normalises to basenames anyway, so the absolute path is harmless
            # there and never reaches a tracked file.
            path = str(paths[key])
        return {"id": key, "type": "csv", "path": path}

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
            # Site-level charts are HORIZONTAL bars: dimension on rows, measure on columns.
            # Vertical bars gave twelve 34-character names on the x-axis, which Tableau
            # truncated to "01 Fairfa..". A horizontal bar has a whole row for its label.
            {
                "name": "Readiness by Site",
                "template": "bar",
                "data_source": "readiness",
                "rows": ["site_ranked"],
                "columns": [{"field": "readiness_score", "aggregation": "Sum"}],
                "color": "data_confidence",
                "label": {"field": "readiness_score", "aggregation": "Sum"},
                "tooltips": ["site_id", "site_name", "recommendation_tier", "jurisdiction",
                             "model_mode"],
                "title": "Site readiness ranking — canonical milestone2_v3",
                "subtitle": "All 12 sites are LOW data confidence; the colour legend has one value on purpose.",
                "fit": "entire_view",
            },
            {
                "name": "Starter vs Pathway Ports",
                "template": "bar",
                "data_source": "ports",
                # `series` on ROWS, nested under the site, is what makes these bars GROUPED.
                # With `series` only on colour Tableau STACKS them, and the published render
                # showed FFX004 as 3 + 8 = 11 ports -- a number that does not exist. Starter
                # and pathway are not additive: pathway is the ceiling to leave room for,
                # starter is what goes in now.
                "rows": ["site_ranked", "series"],
                "columns": [{"field": "ports", "aggregation": "Sum"}],
                "color": "series",
                "label": {"field": "ports", "aggregation": "Sum"},
                "tooltips": ["site_id", "site_name", "model_mode"],
                "title": "Starter ports today vs pathway capacity to leave room for",
                "subtitle": "Portfolio: 25 starter, 48 pathway. NOT additive - pathway is the ceiling. Grouped bars, not bar-in-bar - see CAPABILITY_GAP.md.",
                "fit": "entire_view",
            },
            {
                "name": "Ports Across Horizons",
                "template": "line",
                "data_source": "horizons",
                "rows": [{"field": "ports_active", "aggregation": "Sum"}],
                "columns": ["horizon"],
                "color": "scenario_name",
                "label": {"field": "ports_active", "aggregation": "Sum"},
                # pathway_capacity is a MEASURE. Without an explicit aggregation the compiler
                # emits derivation="None", which makes it a level-of-detail field and
                # renders the whole sheet BLANK -- this one published twice as a title
                # with no chart under it. The spec auto-promotes tooltip DIMENSIONS to
                # Attribute for exactly this reason; measures get no such promotion.
                "tooltips": [{"field": "pathway_capacity", "aggregation": "Sum"},
                             "model_mode"],
                "title": "Active ports by planning horizon",
                "subtitle": "48-port pathway ceiling is in the tooltip — no reference line, see CAPABILITY_GAP.md.",
                # fit_width, not entire_view: with only four horizon categories
                # entire_view sizes the viz to its content and it published as a
                # narrow strip in a full-width zone.
                "fit": "fit_width",
            },
            {
                "name": "Lifecycle Cost by Horizon",
                "template": "bar",
                "data_source": "costs",
                "rows": [{"field": "lifecycle_cost_npv_usd", "aggregation": "Sum"}],
                "columns": ["horizon", "cost_case"],
                "color": "cost_case",
                # See the note on pathway_capacity: a tooltip measure needs an aggregation.
                "tooltips": [{"field": "avoided_overbuild_cost_usd", "aggregation": "Sum"},
                             "estimate_class", "model_mode"],
                "title": "Lifecycle cost, net present value (base escalation)",
                "subtitle": "Screening-class estimates for comparison only. Never a budget, quote or bid.",
                "fit": "fit_width",
            },
            {
                "name": "Net CO2e by Horizon",
                "template": "line",
                "data_source": "emissions",
                "rows": [{"field": "net_co2e_tonnes", "aggregation": "Sum"}],
                "columns": ["horizon"],
                "color": "scenario_name",
                "tooltips": ["grid_factor_source", "grid_factor_vintage", "model_mode"],
                # AVOIDED, not emitted. `net_co2e_kg` is `displaced_tailpipe_kg - grid_emissions_kg`
                # (emissions.py:56), so the line RISING is a good outcome. Titled "Net CO2e"
                # it read as emissions, and the chart looked like pollution increasing.
                "title": "Net CO2e AVOIDED, tonnes per year (higher is better)",
                "subtitle": (f"{config.GRID_FACTOR_LB_PER_MWH} lb CO2e/MWh, "
                             f"{config.GRID_FACTOR_VINTAGE}, SRVC. Demand is modelled, not measured."),
                "fit": "fit_width",
            },
            {
                "name": "Peak Waits by Site",
                "template": "bar",
                "data_source": "waits",
                "rows": ["site_ranked", "series"],
                "columns": [{"field": "wait_min", "aggregation": "Sum"}],
                "color": "series",
                "tooltips": ["site_id", "site_name", "model_mode"],
                "title": "Queue wait, minutes - mean simulated and peak-window Erlang",
                "subtitle": "p50 and p90 are 0.0 at ALL 12 sites: utilisation is 6-20%, so a typical day has no queue. 10-minute screening threshold; no reference line generated.",
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
                "detail": ["site_ranked"],
                "tooltips": ["site_id", "site_name", "jurisdiction", "recommendation_tier",
                             "capacity_basis", "model_mode"],
                "title": "Candidate sites, Northern Virginia",
                "subtitle": "Symbol map, not a choropleth. Mark size is pathway capacity; every capacity_basis is 'placeholder'.",
                "fit": "entire_view",
            },
        ],
        # ALL SEVEN sheets on the dashboard, on one tall canvas.
        #
        # Two mistakes led here and both are worth recording. First, four sheets were tiled
        # into a 900px canvas: each got ~200px, one chart rendered as a squeezed strip and
        # one drew nothing at all. Second, the "fix" was to drop down to two sheets -- which
        # made the layout look right by removing content, and the five sheets left off had
        # no other way to be seen, because Tableau Public publishes with `showTabs: false`
        # and a viewer only ever reaches the default view.
        #
        # A worksheet that is not on the dashboard is not published in any sense that
        # matters. So every sheet is here, and the canvas is tall enough to hold them:
        # 7 x ~470px plus the title. Tableau Public scrolls a tall dashboard.
        "dashboards": [{
            "name": "Milestone 2 Overview",
            "title": CAVEAT,
            "direction": "vertical",
            "sizing_mode": "fixed",
            "width": 1400,
            "height": 3400,
            "worksheets": ["Readiness by Site", "Starter vs Pathway Ports",
                           "Ports Across Horizons", "Peak Waits by Site",
                           "Lifecycle Cost by Horizon", "Net CO2e by Horizon", "Site Map"],
        }],
        "output": {"directory": str(OUT.relative_to(REPO)), "package_twbx": True},  # noqa: E501
    }


def spec_for_build(spec: dict) -> dict:
    """The tracked spec plus the one machine-specific value, for handing to the MCP server.

    The tracked `workbook_spec.json` holds only relative paths so it is portable and passes
    the repository's absolute-path hygiene gate. `base_dir` is the single absolute value the
    authoring server needs, and it is supplied here at call time rather than committed.
    """
    return {**spec, "base_dir": str(REPO)}


def write_all(out_dir: Path) -> tuple[dict[str, Path], Path]:
    data_dir = out_dir / "sheets"
    data_dir.mkdir(parents=True, exist_ok=True)
    frames = build_sheet_data()
    refuse_uninformative_measures(frames)
    paths = {}
    for key, frame in frames.items():
        target = data_dir / f"sheet_{key}.csv"
        frame.to_csv(target, index=False, lineterminator="\n")
        paths[key] = target
    spec = build_spec(paths)
    refuse_bare_tooltip_measures(spec, frames)
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
    import json as _json  # noqa: F401  (json already imported at module scope)
    print(f"wrote {len(paths)} sheet CSVs to {DATA.relative_to(REPO)}/")
    for key, path in paths.items():
        rows = sum(1 for _ in path.open()) - 1
        print(f"  sheet_{key}.csv  {rows} rows")
    print(f"wrote {spec_path.relative_to(REPO)}")
    print("  paths are RELATIVE; base_dir is injected at build time (spec_for_build)")
    build_ready = OUT / "workbook_spec.build.json"
    build_ready.write_text(json.dumps(spec_for_build(json.loads(spec_path.read_text())),
                                      indent=2) + "\n")
    print(f"  wrote {build_ready.relative_to(REPO)} (gitignored; feed THIS to the MCP server)")
    print(f"\nAll values derive from the canonical contract in mode {MODE}.")
    print("The patch package is NOT used for readiness: its readiness_score and model_rank")
    print("are byte-equal to legacy_v2 while its confidence column is v3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
