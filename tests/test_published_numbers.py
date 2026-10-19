"""Every headline number in a reader-facing document must trace to the contract.

Phase 0 of the V4 program found that the active-port series in README, the final report, the
speaker notes, and the website patch package said 44/47/47/48 where the contract says
35/44/44/48 -- while the cost and emissions columns in the *same table rows* were correct. The
ports column had gone stale and nothing noticed, because no gate compared prose against data.

This is that gate. It recomputes each published figure from the contract and asserts the
documents still say it. It is deliberately literal: if a number changes, these fail, and the
fix is to regenerate the prose from the contract -- never to loosen the assertion.

Since DEC-027 (2026-10-18) there are two contracts to check against, and each document is
checked against exactly one. Current documents (README, the website results content) publish
``data/contract/v3``, the authoritative output: 25 starter / 47 pathway. Dated Milestone 2
deliverables (the final report, the speaker notes) are left as delivered and publish the frozen
``data/contract/v1``, the earlier ``legacy_v2`` plan: 25 / 48.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/contract/v1"
CONTRACT_V3 = ROOT / "data/contract/v3"

BASE_CASES = {"baseline", "base"}
HIGH_CASES = {"baseline", "high"}


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    return pd.read_csv(CONTRACT / "scenario_table.csv")


@pytest.fixture(scope="module")
def scenarios_v3() -> pd.DataFrame:
    return pd.read_csv(CONTRACT_V3 / "scenario_table.csv")


def _ports_by_path(scenarios) -> dict[str, dict[int, int]]:
    out: dict[str, dict[int, int]] = {}
    for label, cases in (("base", BASE_CASES), ("high", HIGH_CASES)):
        totals = {}
        for horizon in sorted(scenarios.horizon_year.unique()):
            rows = scenarios[(scenarios.horizon_year == horizon)
                             & (scenarios.scenario_name.isin(cases))]
            totals[int(horizon)] = int(rows.ports_active.sum())
        out[label] = totals
    return out


@pytest.fixture(scope="module")
def ports_by_path(scenarios) -> dict[str, dict[int, int]]:
    """Portfolio active ports per horizon, on the base and high adoption paths (v1)."""
    return _ports_by_path(scenarios)


@pytest.fixture(scope="module")
def ports_by_path_v3(scenarios_v3) -> dict[str, dict[int, int]]:
    """The same, from the authoritative contract v3."""
    return _ports_by_path(scenarios_v3)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# Documents that publish the active-port series. Current ones quote contract v3; the dated
# Milestone 2 deliverable quotes the frozen v1 it was delivered with.
CURRENT_PORT_TABLE_DOCS = [
    "README.md",
    "docs/operations/website-patch-package/content/results_2036_2046_2056.md",
]
DATED_PORT_TABLE_DOCS = [
    "reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md",
]
PORT_TABLE_DOCS = CURRENT_PORT_TABLE_DOCS + DATED_PORT_TABLE_DOCS


class TestContractGroundTruth:
    """Pin the values the prose is checked against, so a contract change is visible here."""

    def test_expected_port_series(self, ports_by_path):
        assert ports_by_path["base"] == {2026: 25, 2036: 35, 2046: 44, 2056: 44}
        assert ports_by_path["high"] == {2026: 25, 2036: 44, 2046: 48, 2056: 48}

    def test_pathway_ceiling_is_48_in_the_frozen_v1(self, scenarios):
        for horizon in sorted(scenarios.horizon_year.unique()):
            rows = scenarios[(scenarios.horizon_year == horizon)
                             & (scenarios.scenario_name.isin(BASE_CASES))]
            assert int(rows.ports_pathway_capacity.sum()) == 48

    def test_expected_port_series_v3(self, ports_by_path_v3):
        """The official series since DEC-027."""
        assert ports_by_path_v3["base"] == {2026: 25, 2036: 31, 2046: 43, 2056: 43}
        assert ports_by_path_v3["high"] == {2026: 25, 2036: 43, 2046: 47, 2056: 47}

    def test_official_pathway_ceiling_is_47(self, scenarios_v3):
        for horizon in sorted(scenarios_v3.horizon_year.unique()):
            rows = scenarios_v3[(scenarios_v3.horizon_year == horizon)
                                & (scenarios_v3.scenario_name.isin(BASE_CASES))]
            assert int(rows.ports_pathway_capacity.sum()) == 47

    def test_no_site_ever_exceeds_its_pathway(self, scenarios):
        over = scenarios[scenarios.ports_active > scenarios.ports_pathway_capacity]
        assert over.empty, over[["scenario_id", "ports_active", "ports_pathway_capacity"]]


class TestPublishedPortSeries:
    @pytest.mark.parametrize("doc", PORT_TABLE_DOCS)
    def test_documents_do_not_contain_the_superseded_series(self, doc):
        """The pre-Phase-0 series (44/47/47/48) was never a portfolio total in any contract."""
        text = read(doc)
        stale = ["44 → 47", "47 → 48", "44 | 47 |"]
        if doc in DATED_PORT_TABLE_DOCS:
            stale.append("| 47 |")  # 47 is in no v1 column; in v3 it is the pathway
        for s in stale:
            assert s not in text, f"{doc} still publishes the superseded series: {s!r}"

    @pytest.mark.parametrize("doc", CURRENT_PORT_TABLE_DOCS)
    def test_current_documents_publish_the_official_series(self, doc, ports_by_path_v3):
        text = read(doc)
        base, high = ports_by_path_v3["base"], ports_by_path_v3["high"]
        for horizon in (2036, 2046, 2056):
            arrow = f"{base[horizon]} → {high[horizon]}"
            cells = f"| {base[horizon]} | {high[horizon]} |"
            assert arrow in text or cells in text, (
                f"{doc} does not publish {horizon} as {arrow}")

    @pytest.mark.parametrize("doc", CURRENT_PORT_TABLE_DOCS)
    def test_current_documents_name_47_and_label_48_as_history(self, doc):
        text = read(doc)
        assert "47" in text and "legacy_v2" in text, doc
        if "48" in text:
            assert "earlier" in text.lower(), f"{doc} mentions 48 without calling it the earlier result"

    @pytest.mark.parametrize("doc", DATED_PORT_TABLE_DOCS)
    def test_dated_documents_publish_the_contract_series(self, doc, ports_by_path):
        text = read(doc)
        base, high = ports_by_path["base"], ports_by_path["high"]
        for horizon in (2036, 2046, 2056):
            arrow = f"{base[horizon]} → {high[horizon]}"
            cells = f"| {base[horizon]} | {high[horizon]} |"
            assert arrow in text or cells in text, (
                f"{doc} does not publish {horizon} as {arrow}")

    def test_speaker_notes_series(self, ports_by_path):
        text = read("presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md")
        base, high = ports_by_path["base"], ports_by_path["high"]
        expect_base = " → ".join(str(base[h]) for h in (2026, 2036, 2046, 2056))
        expect_high = " → ".join(str(high[h]) for h in (2026, 2036, 2046, 2056))
        assert expect_base in text, f"speaker notes base path should read {expect_base}"
        assert expect_high in text, f"speaker notes high path should read {expect_high}"


class TestPublishedConfidence:
    """No document may claim a confidence level the data does not support."""

    def test_no_site_reaches_medium_or_high(self, scenarios):
        assert set(scenarios.data_confidence.unique()) == {"Low"}

    @pytest.mark.parametrize("doc", ["README.md"] + PORT_TABLE_DOCS[1:])
    def test_no_medium_confidence_claim_for_a_site(self, doc):
        text = read(doc)
        offenders = re.findall(r"\d{2}\.\d\s*,\s*Medium confidence", text)
        assert offenders == [], f"{doc} claims a confidence the data does not support: {offenders}"


# Words that mark a number as history rather than a current value. A correction record is
# the project working as intended -- the CHANGELOG says 596.3 corrected 590.2, and the reports
# explain the supersession. Deleting those would destroy provenance. What must never happen is
# 590.2 appearing as a live figure.
SUPERSEDED_MARKERS = (
    "correct", "supersed", "earlier", "carried", "research package", "research register",
    "previous", "was ", "instead of",
)


class TestPublishedEmissionsFactor:
    def test_contract_carries_only_the_corrected_factor(self, scenarios):
        assert set(scenarios.grid_factor_value.unique()) == {596.3}

    def test_superseded_factor_appears_only_as_labelled_history(self):
        """590.2 may be *described* as corrected; it may never be *used*."""
        offenders = []
        for md in sorted(ROOT.rglob("*.md")):
            if any(part in md.parts for part in (".git", "venv")) or "v4-program" in str(md):
                continue
            for lineno, line in enumerate(md.read_text(encoding="utf-8",
                                                       errors="ignore").splitlines(), 1):
                if "590.2" not in line:
                    continue
                if not any(marker in line.lower() for marker in SUPERSEDED_MARKERS):
                    offenders.append(f"{md.relative_to(ROOT)}:{lineno}: {line.strip()[:120]}")
        assert offenders == [], (
            "590.2 used as a current value rather than labelled as superseded:\n"
            + "\n".join(offenders))

    def test_current_factor_is_published_with_its_vintage(self):
        text = read("README.md")
        assert "596.3" in text
        assert "eGRID2023" in text


@pytest.fixture(scope="module")
def portfolio() -> pd.DataFrame:
    path = ROOT / "data/outputs/v3_run/lifecycle_costs_portfolio.csv"
    if not path.exists():
        pytest.skip("run `make run-v3` to produce portfolio costs")
    return pd.read_csv(path)


class TestPublishedCosts:
    """The README's cost columns are a fresh canonical run's (contract v3's) portfolio."""

    @pytest.mark.parametrize("horizon,staged,broad,avoided", [
        (2036, "$1.49M", "$1.85M", "$0.36M"),
        (2046, "$2.21M", "$2.60M", "$0.38M"),
        (2056, "$2.92M", "$3.36M", "$0.44M"),
    ])
    def test_published_costs_match_the_model(self, portfolio, horizon, staged, broad, avoided):
        def millions(case: str, column: str) -> str:
            row = portfolio[(portfolio.horizon_year == horizon)
                            & (portfolio.cost_case == case)
                            & (portfolio.escalation_case == "base")]
            return f"${row[column].iloc[0] / 1e6:.2f}M"

        assert millions("STG", "lifecycle_cost_npv_usd") == staged
        assert millions("OVB", "lifecycle_cost_npv_usd") == broad
        assert millions("STG", "avoided_overbuild_cost_usd") == avoided
        assert staged in read("README.md")
