"""Every displayed number resolves to its lineage, and both tiers say the same thing.

The platform's central promise is that no number appears without its provenance available.
Two ways that promise can fail quietly, and both are pinned here:

1. **A number that cannot be explained renders anyway**, as "unknown" or blank. That looks
   like an answer. `resolve()` raises instead.
2. **The two tiers disagree.** The desktop tier calls `resolve()`; the web tier reads the
   precomputed JSON. If those ever differ, the same number means two things depending on
   which tier you opened - which is worse than either being wrong on its own, because nobody
   would think to check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config, provenance as pv  # noqa: E402

CONTRACT = REPO / "data/contract/v1"
EXPORT = REPO / "site/platform/provenance_v1.json"


@pytest.fixture(scope="module")
def index() -> pv.ContractIndex:
    return pv.ContractIndex.load(CONTRACT)


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    return pd.read_csv(CONTRACT / "scenario_table.csv")


# ------------------------------------------------------------------ it resolves

def test_the_worked_example_resolves_completely(index):
    """ports_active of FFX004 at 2036 base - the example the platform brief must satisfy."""
    p = pv.resolve(index, "FFX004", 2036, "base", "ports_active")
    assert p.value == 4
    assert p.contract_version == config.SCHEMA_VERSION
    assert p.model_mode == config.MODE_V3
    assert p.run_id and p.generated_at
    assert len(p.table_sha256) == 64, "the table hash must be a real SHA-256"
    assert p.data_confidence == "Low"
    assert p.capacity_basis == "placeholder"
    assert p.field_provenance is not None
    assert p.field_provenance.field_group == "parking_and_layout"
    assert p.caveats, "a displayed number with no caveats at all is suspicious"


def test_every_exportable_column_resolves_for_every_row(index, scenarios):
    """No exceptions means no exceptions. If a single cell cannot be explained, the platform
    cannot keep its promise, so this walks all of them."""
    failures = []
    checked = 0
    for row in scenarios.itertuples():
        for column in pv.EXPORTABLE_COLUMNS:
            if column not in scenarios.columns:
                continue
            try:
                pv.resolve(index, row.site_id, int(row.horizon_year), row.scenario_name, column)
                checked += 1
            except pv.ProvenanceError as exc:
                failures.append(f"{row.site_id}/{row.horizon_year}/{row.scenario_name}/{column}: {exc}")
    assert failures == [], failures[:5]
    assert checked == 3720, f"expected 3720 resolvable cells, walked {checked}"


def test_the_engine_is_stated_and_is_never_matlab(index, scenarios):
    """Real MathWorks MATLAB has run this model, but only on a SYNTHETIC fixture - it has
    never seen the real sites. Attributing a contract number to it would be a false claim,
    and GNU Octave is not MATLAB either."""
    for column in ["ports_active", "net_co2e_kg", "lifecycle_cost_npv_usd"]:
        p = pv.resolve(index, "FFX002", 2026, "baseline", column)
        assert p.engine == pv.PRODUCING_ENGINE == "Python (fcf_m2)"
        assert "MATLAB" not in p.engine and "Octave" not in p.engine


# ------------------------------------------------------------------ it refuses

def test_an_unknown_column_is_refused(index):
    with pytest.raises(pv.ProvenanceError, match="not a column"):
        pv.resolve(index, "FFX004", 2036, "base", "ports_2035")


def test_an_unknown_site_is_refused(index):
    with pytest.raises(pv.ProvenanceError, match="no scenario row"):
        pv.resolve(index, "ZZZ999", 2036, "base", "ports_active")


def test_a_directory_that_is_not_a_contract_is_refused(tmp_path):
    with pytest.raises(pv.ProvenanceError, match="not a contract directory"):
        pv.ContractIndex.load(tmp_path)


def test_a_column_with_no_field_group_says_so_rather_than_borrowing_one(index):
    """`run_id` has no provenance field group. It must resolve with None, not with whichever
    group happened to sort first - a number must never borrow another field's credibility."""
    assert "run_id" not in pv.FIELD_GROUP_FOR_COLUMN
    p = pv.resolve(index, "FFX004", 2036, "base", "run_id")
    assert p.field_provenance is None


# ------------------------------------------------------------------ caveats are attached

def test_capacity_columns_always_carry_the_placeholder_caveat(index, scenarios):
    """The headline limitation of the entire study. If it can be displayed without this, the
    platform is misleading in the one place it can least afford to be."""
    for column in ["service_capacity_kw", "spare_capacity_kw", "capacity_basis"]:
        for row in scenarios.head(20).itertuples():
            p = pv.resolve(index, row.site_id, int(row.horizon_year), row.scenario_name, column)
            assert any("PLACEHOLDER" in c for c in p.caveats), (
                f"{column} at {row.site_id} displayed without the placeholder caveat")


def test_cost_columns_carry_the_screening_class_caveat(index):
    p = pv.resolve(index, "FFX004", 2036, "base", "lifecycle_cost_npv_usd")
    assert any("never a quote" in c.lower() or "never a budget" in c.lower() for c in p.caveats)


def test_emissions_carry_the_grid_factor_and_its_vintage(index):
    p = pv.resolve(index, "FFX004", 2036, "base", "net_co2e_kg")
    joined = " ".join(p.caveats)
    assert config.GRID_FACTOR_VINTAGE in joined
    assert str(config.GRID_FACTOR_LB_PER_MWH) in joined
    assert "MODELLED" in joined or "modelled" in joined


def test_every_caveat_key_used_has_text(index):
    """A caveat key with no text renders as nothing, which is a caveat that silently vanished."""
    used = {k for keys in pv.CAVEATS.values() for k in keys}
    missing = sorted(used - set(pv.CAVEAT_TEXT))
    assert missing == [], f"caveat keys with no text: {missing}"


def test_every_field_group_in_the_map_exists_in_the_contract():
    """A mapping to a group that does not exist resolves to None forever, silently."""
    prov = pd.read_csv(CONTRACT / "source_provenance.csv")
    real = set(prov.field_group.unique())
    mapped = set(pv.FIELD_GROUP_FOR_COLUMN.values())
    assert mapped <= real, f"mapped to non-existent group(s): {sorted(mapped - real)}"


def test_every_mapped_column_exists_in_the_contract(scenarios):
    unknown = sorted(set(pv.FIELD_GROUP_FOR_COLUMN) - set(scenarios.columns))
    assert unknown == [], f"mapped columns that are not in the contract: {unknown}"


# ------------------------------------------------------------------ the two tiers agree

@pytest.fixture(scope="module")
def export() -> dict:
    assert EXPORT.is_file(), "run: python -c 'from fcf_m2 import provenance; provenance.export_all(...)'"
    return json.loads(EXPORT.read_text())


def test_the_export_covers_exactly_what_resolve_covers(export, scenarios):
    expected = {
        f"{r.site_id}|{r.horizon_year}|{r.scenario_name}|{c}"
        for r in scenarios.itertuples()
        for c in pv.EXPORTABLE_COLUMNS if c in scenarios.columns
    }
    assert set(export["entries"]) == expected


def test_the_web_tier_and_the_desktop_tier_say_the_same_thing(index, export, scenarios):
    """The failure this prevents: the same number meaning two different things depending on
    which tier you opened. Nobody would think to check, so it is checked here."""
    mismatches = []
    for row in scenarios.head(30).itertuples():
        for column in ["ports_active", "spare_capacity_kw", "net_co2e_kg", "data_confidence"]:
            if column not in scenarios.columns:
                continue
            key = f"{row.site_id}|{row.horizon_year}|{row.scenario_name}|{column}"
            desktop = pv.resolve(index, row.site_id, int(row.horizon_year),
                                 row.scenario_name, column).to_dict()
            web = pv.entry_to_provenance(export, key)
            for field_name in ["column", "contract_version", "model_version", "model_mode",
                               "run_id", "engine", "table_sha256", "data_confidence",
                               "capacity_basis", "caveats", "consumer_rules"]:
                if desktop[field_name] != web[field_name]:
                    mismatches.append(f"{key}.{field_name}: desktop={desktop[field_name]!r} "
                                      f"web={web[field_name]!r}")
            dv, wv = desktop["value"], web["value"]
            if not (dv == wv or (pd.isna(dv) and wv is None)):
                mismatches.append(f"{key}.value: desktop={dv!r} web={wv!r}")
    assert mismatches == [], mismatches[:5]


def test_the_export_states_the_engine_and_never_claims_matlab(export):
    assert export["shared"]["engine"] == pv.PRODUCING_ENGINE
    note = export["engine_note"]
    assert "SYNTHETIC" in note and "never seen the real sites" in note
    assert "GNU Octave is not MATLAB" in note


def test_the_export_stays_small_enough_to_serve(export):
    """It was 6.76 MB before normalising, which is a real cost to every visitor for data that
    is identical on all 3 720 entries."""
    size_kb = EXPORT.stat().st_size / 1024
    assert size_kb < 2048, f"provenance export is {size_kb:.0f} KB; normalise it further"
    assert len(export["field_provenance"]) == 60, "12 sites x 5 mapped groups"


def test_the_export_is_STRICT_json_that_a_browser_can_parse():
    """The defect this pins: 281 bare `NaN` tokens.

    numpy.float64 subclasses float, so an isinstance shortcut let NaN through, and json.dumps
    happily wrote `NaN` literals. Python re-reads them without complaint. A browser's
    JSON.parse rejects them outright - so the entire web tier would have failed to load, and
    every Python-side check would have said the file was fine.

    `parse_constant` is how you make Python as strict as a browser.
    """
    def reject(literal):
        raise ValueError(f"invalid JSON literal {literal!r}; a browser cannot parse this")

    json.loads(EXPORT.read_text(), parse_constant=reject)

    raw = EXPORT.read_text()
    for token in ("NaN", "Infinity", "-Infinity"):
        assert f":{token}" not in raw and f",{token}" not in raw, (
            f"the export contains a bare {token} literal")


def test_a_missing_value_is_null_not_a_string(export):
    """spare_capacity_kw is absent at every site. It must export as JSON null - not as the
    string "nan", which reads as a value, and not as a bare NaN, which will not parse."""
    entry = export["entries"]["FFX004|2036|base|spare_capacity_kw"]
    assert entry["v"] is None


def test_numbers_export_as_numbers_not_strings(export):
    """`default=str` stringified every numpy scalar, so the web tier got "2" where the desktop
    tier had 2. Both panels looked right; a sort would put 6 after 10."""
    for key, expect in [("FFX004|2036|base|ports_active", int),
                        ("FFX004|2036|base|net_co2e_kg", float)]:
        value = export["entries"][key]["v"]
        assert isinstance(value, expect) and not isinstance(value, str), (
            f"{key} exported as {type(value).__name__}: {value!r}")


def test_the_export_is_reproducible(tmp_path, export):
    fresh = tmp_path / "p.json"
    pv.export_all(CONTRACT, fresh)
    assert json.loads(fresh.read_text()) == export
    assert fresh.read_bytes() == EXPORT.read_bytes(), "the published export must not change by a byte"


# ------------------------------------------------------------------ indexed, and the same answers

def _mask_row(index: pv.ContractIndex, site_id, horizon_year, scenario_name) -> pd.Series:
    """How resolve() found its row until 2026-10-18: a three-column mask over the whole table
    for every cell, which made export_all quadratic (251 s for 600 sites under Pyodide). Kept
    as the reference the index must agree with, refusals included."""
    s = index.scenarios
    rows = s[(s.site_id == site_id) & (s.horizon_year == horizon_year) &
             (s.scenario_name == scenario_name)]
    if rows.empty:
        raise pv.ProvenanceError(
            f"no scenario row for site_id={site_id!r}, horizon_year={horizon_year}, "
            f"scenario_name={scenario_name!r}")
    if len(rows) > 1:
        raise pv.ProvenanceError(
            f"{len(rows)} rows match ({site_id}, {horizon_year}, {scenario_name}); the "
            f"contract's uniqueness rule is broken and no number here can be attributed")
    return rows.iloc[0]


@pytest.fixture(scope="module")
def larger_contract(tmp_path_factory) -> Path:
    """The 12 synthetic sites three times over, with new IDs: a 36-site contract made by a real
    cohort run. Synthetic only, so nothing private is read (DEC-016)."""
    from fcf_m2 import workflow

    root = tmp_path_factory.mktemp("larger")
    cohort = root / "cohort"
    cohort.mkdir()
    synthetic = REPO / "data/synthetic"
    for source, name in [("synthetic_sites_v2.csv", "sites.csv"),
                         ("synthetic_v2_electrical_risk_summary.csv", "electrical_risk.csv"),
                         ("synthetic_matlab_site_meta.csv", "site_meta.csv"),
                         ("synthetic_field_provenance_v1.csv", "provenance.csv")]:
        frame = pd.read_csv(synthetic / source, dtype={"site_id": str})
        copies = []
        for k in range(3):
            copy = frame.copy()
            copy["site_id"] = copy["site_id"] + f"-R{k}"
            copies.append(copy)
        pd.concat(copies, ignore_index=True).to_csv(cohort / name, index=False)
    workflow.run("milestone2_v3", root / "out", cohort_dir=cohort)
    return root / "out/contract"


def test_the_index_and_the_mask_export_the_same_bytes(larger_contract, tmp_path, monkeypatch):
    indexed, masked = tmp_path / "indexed.json", tmp_path / "masked.json"
    payload = pv.export_all(larger_contract, indexed)
    assert len(payload["entries"]) == 36 * 10 * 31, "every cell of the 36-site table"
    monkeypatch.setattr(pv.ContractIndex, "scenario_row", _mask_row)
    pv.export_all(larger_contract, masked)
    assert indexed.read_bytes() == masked.read_bytes()


def test_the_index_and_the_mask_resolve_and_refuse_alike(larger_contract):
    index = pv.ContractIndex.load(larger_contract)
    cells = [("SYN003-R2", 2046, "high", "ports_active"),
             ("SYN012-R0", 2026, "baseline", "spare_capacity_kw"),
             ("SYN007-R1", 2036.0, "stress_combined", "net_co2e_kg")]
    for cell in cells:
        indexed = pv.resolve(index, *cell).to_dict()
        with pytest.MonkeyPatch.context() as m:
            m.setattr(pv.ContractIndex, "scenario_row", _mask_row)
            masked = pv.resolve(index, *cell).to_dict()
        assert indexed == masked, cell

    # A key that is absent, or present twice, is refused by both, in the same words.
    doubled = pv.ContractIndex(directory=index.directory, manifest=index.manifest,
                               provenance=index.provenance,
                               scenarios=pd.concat([index.scenarios, index.scenarios.head(1)],
                                                   ignore_index=True))
    first = doubled.scenarios.iloc[0]
    for target, key in [(index, ("SYN999-R0", 2036, "base")), (index, ("SYN001-R0", "2036", "base")),
                        (doubled, (first.site_id, int(first.horizon_year), first.scenario_name))]:
        with pytest.raises(pv.ProvenanceError) as by_index:
            target.scenario_row(*key)
        with pytest.raises(pv.ProvenanceError) as by_mask:
            _mask_row(target, *key)
        assert str(by_index.value) == str(by_mask.value), key
