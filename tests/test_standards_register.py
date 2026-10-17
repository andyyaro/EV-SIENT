"""The frozen standards register is still what `standards.py` writes, and a cohort's is its own.

Why this file exists
--------------------
`data/contract/v1/standards_register.csv` is frozen, and nothing checked that the code still
produces it. The audit of 2026-10-17 regenerated it and found it no longer byte-identical
(F-04): the 2026-08-19 dash pass turned the placeholder em dash (U+2014) into `-` in three
columns of the 24 conditional rows. v1 keeps the em dash forever. That one difference is known
and named here, so that any other is drift and fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import standards  # noqa: E402

V1 = REPO / "data/contract/v1"


def _reference_register() -> pd.DataFrame:
    sites = pd.read_csv(V1 / "site_table.csv")
    flags = pd.read_csv(REPO / "data/inputs/real_sites_v2.csv").set_index("site_id")
    return standards.build_register(
        sites, battery_storage=sites["site_id"].map(flags["battery_storage_flag"]))


def test_the_frozen_register_regenerates_apart_from_its_dashes():
    frozen = (V1 / "standards_register.csv").read_text(encoding="utf-8")
    assert frozen.count("\u2014") == 72, "the known difference changed; re-measure it"
    assert _reference_register().to_csv(index=False) == frozen.replace("\u2014", "-")


def test_a_cohort_register_speaks_about_the_cohort():
    sites = pd.DataFrame({"site_id": ["A-1", "A-2", "A-3"]})
    register = standards.build_register(sites, battery_storage=pd.Series([0, 1, None]),
                                        reference=False)
    storage = register.loc[register["standard_id"] == "UL9540-9540A-NFPA855", "requirement"]
    assert set(storage) == {"Applies ONLY if battery storage enters scope. battery_storage_flag=1 "
                            "at 1 and unrecorded at 1 of 3 sites; confirm whether storage enters "
                            "scope there."}
    text = register.to_csv(index=False)
    assert "Fairfax" not in text and "PWC" not in text and "12 sites" not in text
