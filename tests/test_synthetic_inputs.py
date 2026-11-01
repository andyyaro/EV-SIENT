"""The synthetic input set must be usable, honest, and not a disguised copy of the real one.

Three properties, and the third is the one worth testing hard
------------------------------------------------------------
1. **Usable** - same columns and types as the real inputs, or the model cannot read it.
2. **Honest** - every site is marked synthetic, and its provenance says so in the vocabulary
   the confidence system actually reads.
3. **Not derived** - this is the property a "synthetic" fixture usually fails. Jittering real
   values produces a file that passes any eyeball check and still carries the real
   distribution; with twelve rows and public facility records, that is enough to re-identify
   sites. So the tests below look for *structure* shared with the real data, not just for
   matching strings.

The asymmetry to keep in mind: a false pass here means real facility data was published under
a label saying it was invented. There is no recovering from that, so the checks err toward
failing.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SYNTH = REPO / "data/synthetic"
REAL = REPO / "data/inputs"

pytestmark = pytest.mark.skipif(
    not (SYNTH / "synthetic_sites_v2.csv").is_file(),
    reason="run scripts/build_synthetic_inputs.py first")


def rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open()))


@pytest.fixture(scope="module")
def synthetic():
    return rows(SYNTH / "synthetic_sites_v2.csv")


@pytest.fixture(scope="module")
def real():
    return rows(REAL / "real_sites_v2.csv")


# ---------------------------------------------------------------- usable

@pytest.mark.real_inputs
def test_columns_match_the_real_schema_exactly(synthetic, real):
    """Not a superset or a subset - identical, in order. The model reads by name, but a
    missing column fails at run time rather than here, which is the wrong place to find out."""
    assert list(synthetic[0]) == list(real[0])


@pytest.mark.real_inputs
def test_same_number_of_sites(synthetic, real):
    assert len(synthetic) == len(real) == 12


def test_the_model_can_actually_run_against_it(tmp_path):
    """The point of the whole exercise. A synthetic set the model refuses is no better than no
    synthetic set - the public installer would still be unbuildable."""
    staged = tmp_path / "inputs"
    staged.mkdir()
    for src, dst in [
        (SYNTH / "synthetic_sites_v2.csv", "real_sites_v2.csv"),
        (SYNTH / "synthetic_v2_electrical_risk_summary.csv",
         "legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv"),
        (SYNTH / "synthetic_matlab_site_meta.csv", "legacy_matlab_site_meta.csv"),
    ]:
        (staged / dst).write_bytes(src.read_bytes())
    assert (staged / "real_sites_v2.csv").is_file()
    # Reading it with the same parser the workflow uses is the meaningful check here; a full
    # model run is exercised by the release-artifact gate rather than repeated per test.
    import pandas as pd
    frame = pd.read_csv(staged / "real_sites_v2.csv")
    assert len(frame) == 12
    assert frame["site_type"].isin(["library", "office", "public_safety", "garage"]).all()


# ---------------------------------------------------------------- honest

def test_every_site_id_is_marked_synthetic(synthetic):
    for row in synthetic:
        assert row["site_id"].startswith("SYN"), row["site_id"]


def test_no_row_can_be_mistaken_for_a_real_place(synthetic):
    for row in synthetic:
        assert "SYNTHETIC" in row["notes"].upper()
        assert "not a real place" in row["notes"].lower()


def test_the_electrical_placeholders_are_preserved_not_invented(synthetic):
    """The one direction a fixture must never move.

    `elec_service_rating_amp` and `spare_capacity_kw` are zero in the real data - that is what
    makes `capacity_basis` come out `placeholder` everywhere and what the fail-closed capacity
    guard tests. Inventing capacity here would make a synthetic run report MORE confidence than
    the real study, and someone would eventually quote it.
    """
    for row in synthetic:
        assert row["elec_service_rating_amp"] == "0", row["site_id"]
        assert row["spare_capacity_kw"] == "0", row["site_id"]


def test_provenance_records_every_field_group_as_synthetic():
    prov = rows(SYNTH / "synthetic_field_provenance_v1.csv")
    assert len(prov) == 84, "12 sites x 7 field groups"
    for row in prov:
        assert row["source_class"] == "synthetic_model", row
        assert row["verification_status"] == "unreviewed", row
        assert row["unresolved_flag"] == "1", row


def test_the_matlab_meta_does_not_claim_a_real_provenance():
    for row in rows(SYNTH / "synthetic_matlab_site_meta.csv"):
        text = row["provenance"].upper()
        assert "SYNTHETIC" in text and "INVENTED" in text


# ---------------------------------------------------------------- not derived

@pytest.mark.real_inputs
def test_no_real_site_id_appears_anywhere_in_the_synthetic_set():
    real_ids = {r["site_id"] for r in rows(REAL / "real_sites_v2.csv")}
    for path in SYNTH.glob("*"):
        if not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        for site_id in real_ids:
            assert site_id not in text, f"{path.name} contains the real id {site_id}"


@pytest.mark.real_inputs
def test_no_real_facility_name_address_or_postcode_leaks():
    real = rows(REAL / "real_sites_v2.csv")
    haystack = " ".join(p.read_text(errors="ignore") for p in SYNTH.glob("*") if p.is_file())
    for row in real:
        for field in ("site_name", "address", "zip"):
            value = row[field].strip()
            if len(value) >= 4:
                assert value not in haystack, f"real {field} {value!r} leaked"
        # City names are short and generic enough to collide by accident, so match on the
        # whole token rather than a substring.
        assert row["city"].strip().lower() not in haystack.lower().split(","), row["city"]


@pytest.mark.real_inputs
def test_synthetic_coordinates_are_nowhere_near_the_real_ones(synthetic, real):
    """Coordinates are the most re-identifying field in the file. A degree is roughly 111 km;
    the sets must not be plausibly confusable."""
    real_pts = [(float(r["lat"]), float(r["lon"])) for r in real]
    for row in synthetic:
        lat, lon = float(row["lat"]), float(row["lon"])
        for rlat, rlon in real_pts:
            assert abs(lat - rlat) > 1.0 or abs(lon - rlon) > 1.0, (
                f"{row['site_id']} sits within a degree of a real site")


@pytest.mark.real_inputs
def test_the_synthetic_ordering_is_not_the_real_ordering(synthetic, real):
    """The subtle leak. If a fixture is produced by perturbing real values row by row, the
    RANK ORDER of a column survives the perturbation even when no value matches - and rank
    order over twelve public facilities is re-identifying on its own.
    """
    def ranks(data, column):
        pairs = sorted(range(len(data)), key=lambda i: float(data[i][column]))
        out = [0] * len(data)
        for position, index in enumerate(pairs):
            out[index] = position
        return out

    identical = []
    for column in ("visitors_day", "employees_day", "parking_spaces",
                   "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest",
                   "equity_gap_index", "service_upgrade_cost_usd"):
        if ranks(synthetic, column) == ranks(real, column):
            identical.append(column)
    assert identical == [], (
        f"the synthetic rows preserve the real rank order on {identical}; that survives "
        f"perturbation and re-identifies sites")


@pytest.mark.real_inputs
def test_no_facility_scale_value_matches_a_real_one_row_for_row(synthetic, real):
    """Row-for-row equality on a facility-scale column is the signature of a copy that only
    some columns were randomised in."""
    for column in ("visitors_day", "employees_day", "parking_spaces", "aadt_nearest",
                   "nearby_households_1mi", "nearby_jobs_1mi", "service_upgrade_cost_usd"):
        matches = sum(1 for s, r in zip(synthetic, real) if s[column] == r[column])
        assert matches <= 1, f"{matches}/12 rows share a real {column} value"


def test_the_generator_does_not_read_the_real_inputs():
    """The strongest form of the guarantee: if the generator never opens the real files, no
    amount of cleverness can leak them. Checked against the source, since a value-level test
    can only sample."""
    source = (REPO / "scripts/build_synthetic_inputs.py").read_text()
    body = "\n".join(line for line in source.splitlines()
                     if not line.strip().startswith("#"))
    for forbidden in ["real_sites_v2", "legacy_v2_electrical_risk_summary",
                      "legacy_matlab_site_meta", "field_provenance_v1"]:
        # Docstrings legitimately name these files when explaining the design; what must not
        # exist is a read of them.
        assert f'"{forbidden}' not in body.replace('"""', "\n"), forbidden
    assert "data/inputs" not in body.split('"""')[-1], (
        "the generator must not reference the real input directory in executable code")


def test_regenerating_is_deterministic(tmp_path):
    """A fixture that changes on every build cannot be reviewed, and its diff is noise."""
    before = {p.name: p.read_bytes() for p in SYNTH.glob("*.csv")}
    result = subprocess.run([sys.executable, "scripts/build_synthetic_inputs.py"],
                            cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    after = {p.name: p.read_bytes() for p in SYNTH.glob("*.csv")}
    assert before == after


@pytest.mark.real_inputs
def test_no_categorical_support_shares_its_SHAPE_with_the_real_one():
    """A set that shares no member can still share its structure.

    This is the leak that survived the first fix. The replacement spare-capacity set
    `[42.0, 63.0, 84.0, 168.0]` shared no value with the real `[38.4, 57.6, 76.8, 153.6]` -
    and was that set scaled by exactly 35/32, every ratio 1.09375, both normalising to the
    multiplier vector {2, 3, 4, 8}. That is perturbation: the relative spacing is preserved
    perfectly, which is what "not perturbed" is supposed to rule out.

    Checking membership alone would pass it. This checks shape.
    """
    import itertools
    real_sites = rows(REAL / "real_sites_v2.csv")
    syn_sites = rows(SYNTH / "synthetic_sites_v2.csv")
    real_meta = rows(REAL / "legacy_matlab_site_meta.csv")
    syn_meta = rows(SYNTH / "synthetic_matlab_site_meta.csv")

    def support(data, column):
        out = []
        for row in data:
            try:
                out.append(float(row[column]))
            except (ValueError, KeyError):
                return []
        return sorted(set(out))

    problems = []
    pairs = [(real_sites, syn_sites, ["avg_dwell_min", "ev_share_local", "ev_registrations_local"]),
             (real_meta, syn_meta, ["arrival_start_hr", "arrival_end_hr",
                                    "spare_capacity_kw_placeholder"])]
    for real_data, syn_data, columns in pairs:
        for column in columns:
            a, b = support(real_data, column), support(syn_data, column)
            if len(a) < 2 or len(b) < 2:
                continue
            if set(a) & set(b):
                problems.append(f"{column}: shares members {sorted(set(a) & set(b))}")
            if len(a) == len(b) and a[0] and b[0]:
                # Uniform elementwise ratio == a pure rescale of the real set.
                ratios = {round(y / x, 6) for x, y in zip(a, b) if x}
                if len(ratios) == 1:
                    problems.append(f"{column}: is the real support scaled by {ratios.pop()}")
                # Same normalised shape == same relative spacing by another route.
                if ([round(v / a[0], 4) for v in a] == [round(v / b[0], 4) for v in b]):
                    problems.append(f"{column}: has the real support's normalised shape")
    assert problems == [], "categorical supports share structure with the real data:\n  " + \
                          "\n  ".join(problems)
