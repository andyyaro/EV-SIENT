"""
Tests for the ChargeReady NOVA 3D pipeline.

The load-bearing test is `test_attribution_reproduces_model_score`: it asserts
that the driver weights this package uses to explain a ranking are the same
weights fcf_m2.scoring used to produce it. If someone reweights the model and
forgets to update fcf3d/build_sites.py, this fails rather than the map quietly
telling planners a wrong story.

Run:  pytest tests/ -q
      FCF_REPO=/path/to/Future-City-Fellowship pytest tests/ -q
"""

from __future__ import annotations

import json
import os
import pathlib
import struct
import sys

import pytest

from fcf3d import build_sites as bs  # noqa: E402
from fcf3d.geometry import (  # noqa: E402
    ADA_STALL_WIDTH,
    CANOPY_HEIGHT,
    Box,
    ada_stall_count,
    build_site,
)
from fcf3d.glb import build_gltf, write_glb  # noqa: E402

# The explorer now lives IN the repository, so its inputs are always present and no
# environment variable is needed. Previously this defaulted to a path on the original
# author's machine, which silently skipped 15 of 46 tests everywhere else -- including
# test_attribution_reproduces_model_score, the one test whose stated purpose is to stop
# the map telling planners a story the model never told. A guard that defaults to not
# running is not a guard.
REPO = os.environ.get("FCF_REPO", str(pathlib.Path(__file__).resolve().parents[1]))
needs_repo = pytest.mark.skipif(
    not os.path.isdir(REPO), reason=f"repository root not found at {REPO}"
)


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def sources():
    return bs.resolve_sources(REPO)


@pytest.fixture(scope="module")
def frames(sources):
    return bs.load(sources)


@pytest.fixture(scope="module")
def result(frames, sources):
    return bs.build(frames, sources)


# ------------------------------------------------------------- source layer


@needs_repo
def test_required_sources_resolve(sources):
    assert "results" in sources and "right_sizing" in sources
    for path in sources.values():
        assert os.path.isfile(path)


def test_missing_repo_raises():
    with pytest.raises(bs.SourceMissing):
        bs.resolve_sources("/nonexistent/path/xyz")


# ------------------------------------------------------ model-weight fidelity


@needs_repo
def test_driver_weights_sum_to_one_per_subscore():
    """Each subscore's driver weights must sum to 1.0, or the attribution
    under- or over-counts that subscore's contribution."""
    totals: dict[str, float] = {}
    for drv in bs.DRIVERS:
        totals[drv.subscore] = totals.get(drv.subscore, 0.0) + drv.weight
    for subscore, total in totals.items():
        assert total == pytest.approx(1.0, abs=1e-9), f"{subscore} weights sum to {total}"


@needs_repo
def test_subscore_weights_sum_to_one():
    assert sum(bs.SUBSCORE_WEIGHTS.values()) == pytest.approx(1.0)


@needs_repo
def test_attribution_reproduces_model_score(frames):
    """The whole point: our decomposition must rebuild the model's own score."""
    res = bs.prepare(frames["results"])
    for _, row in res.iterrows():
        rebuilt = bs.reconstruct_score(row)
        actual = round(float(row["readiness_score"]), 1)
        assert abs(rebuilt - actual) <= 0.15, (
            f"{row['site_id']}: attribution {rebuilt} vs model {actual}"
        )


@needs_repo
def test_build_emits_no_drift_warnings(result):
    drift = [w for w in result.warnings if "attribution" in w]
    assert not drift, drift


@needs_repo
def test_invert_flags_match_scoring_module():
    """These four drivers are the ones fcf_m2.scoring wraps in (1 - x)."""
    inverted = {d.column for d in bs.DRIVERS if d.invert}
    assert inverted == {
        "existing_ports_total_n",
        "distance_to_service_ft_n",
        "install_cost_est_usd_n",
        "trenching_ft_n",
        "garage_enclosed",
        "stormwater_risk",
    }


# ------------------------------------------------------------- output shape


@needs_repo
def test_every_site_becomes_a_feature(result, frames):
    assert len(result.features) == len(frames["results"])


@needs_repo
def test_ranks_are_dense_and_unique(result):
    ranks = sorted(f["properties"]["model_rank"] for f in result.features)
    assert ranks == list(range(1, len(ranks) + 1))


@needs_repo
def test_coordinates_are_in_northern_virginia(result):
    for f in result.features:
        lon, lat = f["geometry"]["coordinates"][:2]
        assert -78.5 < lon < -76.8, f["id"]
        assert 38.4 < lat < 39.2, f["id"]


@needs_repo
def test_output_is_strict_json(result, tmp_path):
    """No NaN/Infinity — those are valid Python but invalid JSON, and they
    silently break JSON.parse in the browser."""
    paths = bs.write(result, str(tmp_path))
    with open(paths["geojson"]) as fh:
        text = fh.read()
    assert "NaN" not in text and "Infinity" not in text
    json.loads(text)  # strict by default


@needs_repo
def test_all_expected_keys_present(result):
    required = {
        "site_id", "site_name", "model_rank", "readiness_score", "subscores",
        "recommendation_tier", "strengths", "constraints", "driver_attribution",
        "data_needed_next", "asset", "scenarios",
    }
    for f in result.features:
        missing = required - set(f["properties"])
        assert not missing, f"{f['id']} missing {missing}"


@needs_repo
def test_asset_ports_are_sane(result):
    for f in result.features:
        asset = f["properties"]["asset"]
        assert asset["ports"] >= 1
        assert asset["pathway_ports"] >= asset["ports"]


@needs_repo
def test_strengths_and_constraints_are_ordered(result):
    for f in result.features:
        p = f["properties"]
        earned = [s["points_earned"] for s in p["strengths"]]
        assert earned == sorted(earned, reverse=True), p["site_id"]
        forgone = [c["points_forgone"] for c in p["constraints"] if "points_forgone" in c]
        assert forgone == sorted(forgone, reverse=True), p["site_id"]


@needs_repo
def test_writes_inline_bundle(result, tmp_path):
    paths = bs.write(result, str(tmp_path))
    text = open(paths["inline"]).read()
    assert text.startswith("/* generated")
    assert "window.__FCF_SITES__" in text


# ---------------------------------------------------------------- utilities


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("a; b; c", ["A", "B", "C"]),
        ("only one.", ["Only one"]),
        ("", []),
        (None, []),
        (float("nan"), []),
    ],
)
def test_split_sentences(raw, expected):
    assert bs.split_sentences(raw) == expected


@pytest.mark.parametrize(
    "tier,expected",
    [
        ("Tier 1 — advance to site screening", 1),
        ("Tier 2 — promising candidate, refine data", 2),
        ("Tier 3 — lower priority / monitor", 3),
        ("High-review candidate", 2),
        ("Low public-priority / special-use", 4),
        ("something else", 9),
    ],
)
def test_tier_key(tier, expected):
    assert bs.tier_key(tier) == expected


def test_clean_strips_non_finite():
    assert bs._clean(float("nan")) is None
    assert bs._clean(float("inf")) is None
    assert bs._clean(3.14159265) == 3.141593


# ----------------------------------------------------------------- geometry


@pytest.mark.parametrize(
    "stalls,expected", [(0, 0), (1, 1), (8, 1), (25, 1), (26, 2), (50, 2), (51, 3)]
)
def test_ada_stall_count(stalls, expected):
    assert ada_stall_count(stalls) == expected


def test_build_site_scales_with_ports():
    small = build_site("S", ports_now=2, ports_pathway=2)
    large = build_site("L", ports_now=2, ports_pathway=8)
    assert large.part_count > small.part_count
    assert large.footprint_m[0] > small.footprint_m[0]


def test_pathway_stalls_are_translucent():
    site = build_site("X", ports_now=2, ports_pathway=6)
    stalls = [b for b in site.boxes if b.name.startswith("stall_")]
    future = [b for b in stalls if b.material == "stall_future"]
    assert len(future) == 4  # 6 pathway - 2 energised


def test_first_stall_is_ada_width():
    site = build_site("X", ports_now=4, ports_pathway=4)
    first = next(b for b in site.boxes if b.name == "stall_00")
    assert first.size[0] == pytest.approx(ADA_STALL_WIDTH - 0.12)


def test_ports_pathway_never_below_ports_now():
    site = build_site("X", ports_now=6, ports_pathway=2)
    assert site.ports_pathway == 6


def test_canopy_sits_above_every_dispenser():
    site = build_site("X", ports_now=4, ports_pathway=4)
    canopy = next(b for b in site.boxes if b.name == "canopy_deck")
    canopy_underside = canopy.center[2] - canopy.size[2] / 2
    for box in site.boxes:
        if box.name.startswith("dispenser"):
            assert box.center[2] + box.size[2] / 2 < canopy_underside
    assert canopy_underside == pytest.approx(CANOPY_HEIGHT)


def test_enu_to_gltf_conversion():
    # ENU east/north/up -> glTF x=east, y=up, z=south
    assert Box.enu_to_gltf((1, 0, 0)) == (1, 0, 0)      # east
    assert Box.enu_to_gltf((0, 1, 0)) == (0, 0, -1)     # north -> -z
    assert Box.enu_to_gltf((0, 0, 1)) == (0, 1, 0)      # up   -> +y


def test_box_corners_count_and_yaw():
    box = Box(center=(0, 0, 0), size=(2, 2, 2), material="stall", yaw_deg=90)
    corners = box.corners_enu()
    assert len(corners) == 8
    for x, y, z in corners:
        assert abs(x) == pytest.approx(1, abs=1e-6)
        assert abs(y) == pytest.approx(1, abs=1e-6)
        assert abs(z) == pytest.approx(1, abs=1e-6)


# --------------------------------------------------------------------- glb


def test_gltf_structure_is_valid():
    site = build_site("T", ports_now=2, ports_pathway=4)
    gltf, buf = build_gltf(site)

    assert gltf["asset"]["version"] == "2.0"
    assert len(gltf["meshes"]) == 1
    assert gltf["meshes"][0]["primitives"], "no primitives"
    assert len(gltf["materials"]) == len(gltf["meshes"][0]["primitives"])
    assert gltf["buffers"][0]["byteLength"] == len(buf)

    for prim in gltf["meshes"][0]["primitives"]:
        pos = gltf["accessors"][prim["attributes"]["POSITION"]]
        nrm = gltf["accessors"][prim["attributes"]["NORMAL"]]
        idx = gltf["accessors"][prim["indices"]]
        assert pos["count"] == nrm["count"]
        assert idx["count"] % 3 == 0
        assert pos["count"] % 24 == 0  # 6 faces x 4 verts per box
        assert len(pos["min"]) == 3 and len(pos["max"]) == 3

    for view in gltf["bufferViews"]:
        assert view["byteOffset"] + view["byteLength"] <= len(buf)


def test_glb_header_is_well_formed(tmp_path):
    site = build_site("T", ports_now=3, ports_pathway=6)
    path = write_glb(site, str(tmp_path / "t.glb"))
    raw = open(path, "rb").read()

    magic, version, length = struct.unpack("<4sII", raw[:12])
    assert magic == b"glTF"
    assert version == 2
    assert length == len(raw)

    json_len, json_type = struct.unpack("<I4s", raw[12:20])
    assert json_type == b"JSON"
    assert json_len % 4 == 0
    doc = json.loads(raw[20 : 20 + json_len].decode("utf-8"))
    assert doc["extras"]["site_id"] == "T"

    bin_off = 20 + json_len
    bin_len, bin_type = struct.unpack("<I4s", raw[bin_off : bin_off + 8])
    assert bin_type == b"BIN\x00"
    assert bin_len % 4 == 0
    assert bin_off + 8 + bin_len == len(raw)


def test_translucent_material_gets_blend_mode():
    site = build_site("T", ports_now=1, ports_pathway=4)
    gltf, _ = build_gltf(site)
    future = next(m for m in gltf["materials"] if m["name"] == "stall_future")
    assert future["alphaMode"] == "BLEND"
    assert future["pbrMetallicRoughness"]["baseColorFactor"][3] < 1.0


def test_normals_are_unit_length():
    import math

    site = build_site("T", ports_now=1, ports_pathway=1)
    gltf, buf = build_gltf(site)
    prim = gltf["meshes"][0]["primitives"][0]
    acc = gltf["accessors"][prim["attributes"]["NORMAL"]]
    view = gltf["bufferViews"][acc["bufferView"]]
    data = buf[view["byteOffset"] : view["byteOffset"] + view["byteLength"]]
    for i in range(acc["count"]):
        x, y, z = struct.unpack_from("<3f", data, i * 12)
        assert math.sqrt(x * x + y * y + z * z) == pytest.approx(1.0, abs=1e-5)


@needs_repo
def test_end_to_end(tmp_path, result):
    """ETL -> models, the way `make all` runs it."""
    from fcf3d.build_models import load_sites, run_pure_python

    data_dir = tmp_path / "data"
    model_dir = tmp_path / "models"
    bs.write(result, str(data_dir))

    sites = load_sites(str(data_dir / "sites.geojson"))
    written = run_pure_python(sites, str(model_dir))

    assert len(written) == len(result.features)
    for _sid, path, size in written:
        assert size > 1000
        assert open(path, "rb").read(4) == b"glTF"
