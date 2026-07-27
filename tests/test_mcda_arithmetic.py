"""The provisional MCDA matrix must reproduce from its own scores and weights.

The team is instructed to review and adopt ``docs/human-actions/team_alternatives_session/
02_PROVISIONAL_MCDA.md``, and the facilitator is required to read its equity-crossover
disclosure aloud before the weighting vote. Both were arithmetically wrong when audited:
alternative G's weighted score was published as 37.0 against a computed 40.0, and the
crossover was disclosed at 2x the default equity weight when the matrix puts it at ~2.5x.

Neither is a modelling opinion -- both are arithmetic, so both can be checked. This parses
the published Markdown rather than restating the numbers, so editing the table without
redoing the arithmetic fails here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MCDA = ROOT / "docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md"
ADOPTION = ROOT / "docs/human-actions/team_alternatives_session/04_WEIGHT_ADOPTION_PAGE.md"

CRITERIA = ["Safety", "Demand", "Cost", "Expand", "Equity", "Confidence"]
MAX_SCORE = 5


@pytest.fixture(scope="module")
def weights() -> dict[str, int]:
    """Weights as published in the matrix header row (e.g. '| Alt | ... | Safety 25 | ...')."""
    header = next(line for line in MCDA.read_text().splitlines()
                  if line.startswith("| Alt ") and "Safety" in line)
    found = {}
    for crit in CRITERIA:
        m = re.search(rf"{crit}\s+(\d+)", header)
        assert m, f"no weight published for {crit}"
        found[crit] = int(m.group(1))
    return found


@pytest.fixture(scope="module")
def matrix() -> dict[str, dict]:
    """Parse each alternative row: six scores, the published weighted total, and the rank."""
    rows = {}
    for line in MCDA.read_text().splitlines():
        m = re.match(r"^\|\s*([A-G])\s*\|([^|]*)\|(.+)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(3).split("|")]
        if len(cells) < 8:
            continue
        try:
            scores = [int(c) for c in cells[:6]]
        except ValueError:
            continue
        weighted = float(re.sub(r"[^\d.]", "", cells[6]))
        rank = int(re.sub(r"[^\d]", "", cells[7]))
        rows[m.group(1)] = {"scores": dict(zip(CRITERIA, scores)),
                            "published": weighted, "rank": rank}
    return rows


def weighted(scores: dict[str, int], weights: dict[str, int]) -> float:
    return sum(scores[c] / MAX_SCORE * weights[c] for c in CRITERIA)


class TestMatrixIntegrity:
    def test_weights_total_100(self, weights):
        assert sum(weights.values()) == 100, weights

    def test_all_seven_alternatives_parsed(self, matrix):
        assert sorted(matrix) == list("ABCDEFG"), sorted(matrix)

    def test_scores_are_within_the_stated_anchor_range(self, matrix):
        for alt, row in matrix.items():
            for crit, value in row["scores"].items():
                assert 0 <= value <= MAX_SCORE, f"{alt}/{crit} = {value} outside 0-{MAX_SCORE}"

    @pytest.mark.parametrize("alt", list("ABCDEFG"))
    def test_every_published_score_reproduces(self, alt, matrix, weights):
        row = matrix[alt]
        computed = weighted(row["scores"], weights)
        assert abs(computed - row["published"]) < 0.05, (
            f"Alternative {alt}: published {row['published']}, computes to {computed:.1f}")

    def test_ranks_are_consistent_with_the_scores(self, matrix):
        order = sorted(matrix, key=lambda a: -matrix[a]["published"])
        for position, alt in enumerate(order, 1):
            assert matrix[alt]["rank"] == position, (
                f"{alt} is ranked {matrix[alt]['rank']} but sits at position {position}")


class TestEquityCrossover:
    """The disclosure the facilitator reads aloud must state the real threshold."""

    def crossover(self, matrix, weights) -> int:
        """Lowest integer equity weight at which F is no longer beaten by B,
        reducing the other five weights proportionally."""
        others = {k: v for k, v in weights.items() if k != "Equity"}
        total = sum(others.values())
        for equity in range(weights["Equity"], 101):
            w = {k: v * (100 - equity) / total for k, v in others.items()}
            w["Equity"] = equity
            if weighted(matrix["F"]["scores"], w) >= weighted(matrix["B"]["scores"], w):
                return equity
        raise AssertionError("F never reaches B at any equity weight")

    def test_b_leads_at_the_default_weights(self, matrix, weights):
        assert weighted(matrix["B"]["scores"], weights) > weighted(matrix["F"]["scores"], weights)

    def test_f_does_not_overtake_b_at_double_equity(self, matrix, weights):
        assert self.crossover(matrix, weights) > 2 * weights["Equity"], (
            "the retired 2x claim would be correct after all -- re-check the disclosure")

    def test_crossover_is_about_2_5x_and_the_docs_say_so(self, matrix, weights):
        point = self.crossover(matrix, weights)
        assert point == 25, f"crossover moved to equity {point}; update both documents"
        for doc in (MCDA, ADOPTION):
            text = doc.read_text()
            assert "2.5" in text, f"{doc.name} does not state the 2.5x crossover"
            assert not re.search(r"at roughly \*\*2× the default", text), (
                f"{doc.name} still asserts the superseded 2x crossover")
