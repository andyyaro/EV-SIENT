"""The published input schema, its page and its worked example say what the code does.

Why this file exists
--------------------
`data/schema/input_schema_v1.json` and `docs/INPUT_SCHEMA.md` are what someone outside the
project reads before handing over their own sites (F-25). Both are prose about code, which is
how a description goes stale: a field added to intake but not to the schema, a default changed
in the run but not on the page. So every statement here that can be checked is checked
against the module that implements it, and the page's worked example is rerun.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import contract, intake, workflow  # noqa: E402
from fcf_m2.scoring import (  # noqa: E402
    MODE_V3, NO_TOKENS, NUMERIC_FIELDS, TEXT_NULLS, YES_NO_FIELDS, YES_TOKENS,
    enrich_and_score, load_anchor_set,
)

SCHEMA = json.loads((REPO / "data/schema/input_schema_v1.json").read_text())
FIELDS = SCHEMA["properties"]
PAGE = (REPO / "docs/INPUT_SCHEMA.md").read_text()
PROSE = " ".join(PAGE.split())          # the page with its line wrapping undone
EXAMPLE = REPO / "data/intake/example/example_city_facilities.csv"
FLAG_HINT = " Write yes/no, 1/0 or true/false; leave blank if nobody knows."


def fields_table(schema: dict) -> str:
    """The page's field table, rendered from the schema. The page carries this verbatim."""
    lines = ["| Field | Unit | In the score | What it is | If blank or absent |",
             "|---|---|---|---|---|"]
    for name, spec in schema["properties"].items():
        lines.append(f"| `{name}` | {spec['x-unit']} | "
                     f"{'yes' if spec['x-in-readiness-score'] else 'no'} | "
                     f"{spec['description'].replace(FLAG_HINT, '')} | {spec['x-if-absent']} |")
    return "\n".join(lines)


def test_the_schema_is_a_valid_draft_2020_12_schema():
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_the_schema_lists_every_field_intake_reads_in_the_same_order():
    assert list(FIELDS) == intake._all_fields()


def test_the_template_header_is_the_schema():
    with (REPO / "data/intake/template_sites.csv").open() as handle:
        assert next(csv.reader(handle)) == list(FIELDS)


def test_the_cell_vocabularies_are_the_readers():
    assert set(SCHEMA["x-blank-values"]) | {""} == set(TEXT_NULLS)
    assert set(SCHEMA["x-yes-values"]) == set(YES_TOKENS)
    assert set(SCHEMA["x-no-values"]) == set(NO_TOKENS)


def test_the_identifier_rule_and_the_cohort_files_are_the_runs():
    assert FIELDS["site_id"]["pattern"] == contract.COHORT_SITE_ID_PATTERN
    assert SCHEMA["required"] == ["site_id"]
    assert set(SCHEMA["x-cohort-files"]) == set(workflow.COHORT_FILES)


def test_a_field_said_to_be_converted_is_one_intake_converts():
    said = {name for name, spec in FIELDS.items() if "recognised and converted" in spec["description"]}
    assert said == set(intake.UNIT_CONVERSIONS)


def _extremes(name: str) -> tuple[float, float]:
    """A value at or below every anchor of the field, and one at or above it."""
    if name in YES_NO_FIELDS or name in ("ev_share_local", "equity_gap_index"):
        return 0, 1
    return 0, (24 if name == "hours_open" else 10**6)


@pytest.mark.parametrize("name", NUMERIC_FIELDS + YES_NO_FIELDS)
def test_in_the_score_is_true_exactly_when_the_field_moves_the_score(name):
    """Measured, not declared: the field is set low and then high at every site."""
    sites = pd.read_csv(REPO / "data/synthetic/synthetic_sites_v2.csv")
    anchors = load_anchor_set(REPO / "data/anchors/anchor_set_v1.json")
    scores = [enrich_and_score(sites.assign(**{name: value}), mode=MODE_V3, anchor_set=anchors)
              .set_index("site_id")["readiness_score"].sort_index() for value in _extremes(name)]
    moves = not scores[0].equals(scores[1])
    assert FIELDS[name]["x-in-readiness-score"] is moves, (
        f"{name}: the schema says in-score={FIELDS[name]['x-in-readiness-score']}, the code says {moves}")


def test_the_page_carries_the_schemas_field_table():
    assert fields_table(SCHEMA) in PAGE, (
        "docs/INPUT_SCHEMA.md's field table no longer matches data/schema/input_schema_v1.json. "
        "Replace it with tests.test_input_schema.fields_table(SCHEMA).")


def test_the_worked_example_still_says_what_the_page_says(tmp_path, capsys):
    cohort, out = tmp_path / "example-city", tmp_path / "out"
    with pytest.raises(SystemExit) as done:
        workflow.main(["intake", str(EXAMPLE), "--out", str(cohort), "--accept",
                       "--jurisdiction", "Example City", "--source-date", "2026-10-01",
                       "--source-org", "Example City (invented)"])
    assert done.value.code == 0
    summary = "31 of 32 fields mapped, 1 absent, 0 refusal(s), 4 warning(s), 6 note(s)"
    assert summary in capsys.readouterr().out
    assert f"`{summary}`" in PROSE

    result = workflow.run(MODE_V3, out, cohort_dir=cohort)
    totals = (result["starter_total_2026"], result["pathway_total"])
    assert totals == (12, 15)
    assert "**12 starter ports and a 15-port pathway**" in PROSE
    assert result["cohort"]["plan_ranking"] == MODE_V3

    scored = pd.read_csv(out / "site_results_milestone2_v3.csv").set_index("site_id")
    plan = pd.read_csv(out / "right_sizing_v3_canonical.csv").query("horizon_year == 2026").set_index("site_id")
    assert len(scored) == 6
    assert plan.loc["EXC-04", "site_capacity_cap"] == 2                     # parking left blank
    assert scored.loc["EXC-05", "recommendation_tier"].startswith("Low public-priority")
    assert "garage_enclosed" in scored.loc["EXC-05", "absent_fields"]      # 'partial'
    assert plan.loc["EXC-05", "expansion_strategy"] == "do_not_advance_general_public_buildout"
    # The plan follows the ranking the results show, not the cohort-relative legacy one (F-05).
    assert (plan["model_rank"] == scored.loc[plan.index, "model_rank"]).all()
    table = pd.read_csv(out / "contract/scenario_table.csv")
    assert (table["data_confidence"] == "Low").all()
    workflow.main(["validate-contract", str(out / "contract")])
