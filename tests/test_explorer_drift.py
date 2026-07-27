"""The 3D map's arithmetic must be the model's arithmetic, in both modes.

`fcf-3d/CLAUDE.md` names the failure this guards against: *the map telling planners a story
the model never told*. Two ways that happened before integration:

* The explorer kept its own copy of the scoring weights. They matched only because someone
  maintained them by hand, and the explorer's own test merely checked its copy summed to 1.0
  -- never that it equalled the model's. `fcf_m2.scoring` now owns the weights and the
  explorer imports them, so this file's job is to prove the import is real and complete.
* The ETL read the `legacy_v2` fixtures while emitting field names in a horizon convention
  `milestone2_v3` had retired, and emitted V3 horizons alongside them in the same payload.
  A field name must never carry a horizon its data does not have.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fcf3d import build_sites as bs
from fcf_m2 import scoring

ROOT = Path(__file__).resolve().parents[1]
WEB_DATA = ROOT / "explorer/web/data"

RETIRED_HORIZONS = ("2035", "2050")
CANONICAL_HORIZONS = ("2026", "2036", "2046", "2056")


class TestWeightsAreImportedNotCopied:
    def test_subscore_weights_are_the_same_object(self):
        assert bs.SUBSCORE_WEIGHTS is scoring.SUBSCORE_WEIGHTS

    def test_subscore_weights_sum_to_one(self):
        assert sum(scoring.SUBSCORE_WEIGHTS.values()) == pytest.approx(1.0)

    def test_each_subscore_driver_block_sums_to_one(self):
        for subscore, weights in scoring.DRIVER_WEIGHTS.items():
            assert sum(weights.values()) == pytest.approx(1.0), subscore

    @pytest.mark.parametrize("driver", bs.DRIVERS, ids=lambda d: d.column)
    def test_every_driver_weight_matches_the_model(self, driver):
        model_weight = scoring.DRIVER_WEIGHTS[driver.subscore].get(driver.column)
        assert model_weight is not None, f"{driver.column} is not a model driver"
        assert driver.weight == pytest.approx(model_weight)

    @pytest.mark.parametrize("driver", bs.DRIVERS, ids=lambda d: d.column)
    def test_every_invert_flag_matches_the_model(self, driver):
        assert driver.invert == (driver.column in scoring.INVERTED_DRIVERS)

    def test_the_explorer_covers_every_model_driver(self):
        """A driver the model weights but the map ignores would silently under-explain."""
        explorer = {d.column for d in bs.DRIVERS}
        model = {c for weights in scoring.DRIVER_WEIGHTS.values() for c in weights}
        assert model - explorer == set(), f"model drivers missing from the map: {model - explorer}"
        assert explorer - model == set(), f"map drivers unknown to the model: {explorer - model}"


class TestModeSeparation:
    def test_both_modes_declare_sources_and_horizons(self):
        assert set(bs.MODE_SOURCES) == set(bs.MODES) == set(bs.MODE_HORIZONS)
        assert bs.DEFAULT_MODE == bs.MODE_V3, "the canonical mode must be the default"

    @pytest.mark.parametrize("mode", bs.MODES)
    def test_each_mode_resolves_and_builds(self, mode):
        sources = bs.resolve_sources(str(ROOT), mode)
        result = bs.build(bs.load(sources), sources, mode)
        assert len(result.features) == 12
        assert result.manifest["mode"] == mode

    def test_legacy_mode_emits_only_its_own_horizons(self):
        sources = bs.resolve_sources(str(ROOT), bs.MODE_LEGACY)
        result = bs.build(bs.load(sources), sources, bs.MODE_LEGACY)
        props = result.features[0]["properties"]
        leaked = [k for k in props if any(h in k for h in CANONICAL_HORIZONS)]
        assert leaked == [], f"legacy_v2 leaked canonical horizon fields: {leaked}"

    def test_canonical_mode_never_emits_a_retired_horizon(self):
        """The defect this phase exists to fix: a ports_2050 field under a V3 repository."""
        sources = bs.resolve_sources(str(ROOT), bs.MODE_V3)
        result = bs.build(bs.load(sources), sources, bs.MODE_V3)
        for feature in result.features:
            props = feature["properties"]
            leaked = [k for k in props if any(h in k for h in RETIRED_HORIZONS)]
            assert leaked == [], f"{props['site_id']} carries retired horizons: {leaked}"
            rs = props.get("right_sizing") or {}
            leaked_rs = [k for k in rs if any(h in k for h in RETIRED_HORIZONS)]
            assert leaked_rs == [], f"{props['site_id']} right_sizing retired: {leaked_rs}"

    def test_the_two_modes_disagree_about_the_top_site(self):
        """Not a defect -- the reason mode must be visible. Pin it so it stays visible."""
        tops = {}
        for mode in bs.MODES:
            sources = bs.resolve_sources(str(ROOT), mode)
            result = bs.build(bs.load(sources), sources, mode)
            tops[mode] = result.features[0]["properties"]["site_id"]
        assert tops[bs.MODE_V3] == "FFX004"
        assert tops[bs.MODE_LEGACY] == "FFX002"


@pytest.fixture(scope="module")
def committed() -> dict:
    return json.loads((WEB_DATA / "sites.geojson").read_text())


class TestCommittedArtifacts:
    """The built payload is committed, so it must match a fresh build of the default mode."""

    def test_manifest_states_the_active_mode(self):
        manifest = json.loads((WEB_DATA / "manifest.json").read_text())
        assert manifest["mode"] == bs.DEFAULT_MODE
        assert manifest["mode_is_canonical"] is True
        assert manifest["horizons"] == list(CANONICAL_HORIZONS)

    def test_committed_geojson_matches_a_fresh_build(self, committed):
        sources = bs.resolve_sources(str(ROOT), bs.DEFAULT_MODE)
        fresh = bs.build(bs.load(sources), sources, bs.DEFAULT_MODE)
        assert len(fresh.features) == len(committed["features"])
        for built, on_disk in zip(fresh.features, committed["features"]):
            assert built["properties"]["site_id"] == on_disk["properties"]["site_id"]
            assert built["properties"]["readiness_score"] == on_disk["properties"]["readiness_score"]
            assert built["geometry"] == on_disk["geometry"]

    def test_committed_payload_carries_no_retired_horizon(self, committed):
        blob = json.dumps(committed)
        for retired in ("ports_2035", "ports_2050"):
            assert retired not in blob, f"committed payload still carries {retired}"

    def test_site_ids_are_exactly_the_twelve(self, committed):
        ids = sorted(f["properties"]["site_id"] for f in committed["features"])
        expected = sorted([f"FFX{n:03d}" for n in range(1, 5)]
                          + [f"PWC{n:03d}" for n in range(1, 9)])
        assert ids == expected

    def test_every_coordinate_is_in_northern_virginia(self, committed):
        for feature in committed["features"]:
            lon, lat = feature["geometry"]["coordinates"][:2]
            assert -77.8 <= lon <= -77.0, f"{feature['properties']['site_id']} lon {lon}"
            assert 38.5 <= lat <= 39.1, f"{feature['properties']['site_id']} lat {lat}"
