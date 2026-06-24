"""Add a readiness-confidence action matrix to model outputs.

This script reads data/outputs/site_results.csv, adds simple next-action columns,
and writes a small Markdown report.

Run from the repository root after src/ev_charger_model.py:

    python src/add_action_matrix.py
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_REPORT = "data/outputs/action_matrix.md"


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def readiness_band(score: float) -> str:
    if score >= 55:
        return "High readiness"
    if score >= 45:
        return "Medium readiness"
    return "Low readiness"


def confidence_band(score: float) -> str:
    if score >= 75:
        return "High confidence"
    if score >= 50:
        return "Medium confidence"
    return "Low confidence"


def action_for_row(row: pd.Series) -> pd.Series:
    site_id = str(row.get("site_id", ""))
    readiness = float(row.get("readiness_score", 0))
    confidence = float(row.get("data_confidence_score", 0))
    tier = str(row.get("recommendation_tier", ""))
    is_garage = int(float(row.get("garage_enclosed", 0))) == 1
    public_access = int(float(row.get("public_access", 0))) == 1

    readiness_label = readiness_band(readiness)
    confidence_label = confidence_band(confidence)
    matrix_cell = f"{readiness_label} + {confidence_label}"

    if not public_access:
        action_label = "Special-use decision needed"
        action_detail = "Clarify whether this site is public, fleet-only, special-use, or should be removed from the public-candidate list."
    elif is_garage or "High-review" in tier:
        action_label = "Technical review before advancement"
        action_detail = "Keep in planning, but resolve garage, fire/AHJ, access, emergency-disconnect, routing, and electrical questions first."
    elif readiness >= 55 and confidence >= 75:
        action_label = "Advance to next-stage screening"
        action_detail = "Strong candidate with stronger input support. Move toward site screening before any design or procurement step."
    elif readiness >= 55 and confidence >= 50:
        action_label = "Verify key data, then advance"
        action_detail = "Strong candidate, but confirm electrical capacity, site placement, parking, and operations before advancement."
    elif readiness >= 55:
        action_label = "Promising, but fix data first"
        action_detail = "Do not advance yet. Improve the weak or unconfirmed inputs first."
    elif readiness >= 45 and confidence >= 50:
        action_label = "Promising, refine assumptions"
        action_detail = "Keep in the candidate set and improve the data before deciding whether to advance."
    elif readiness >= 45:
        action_label = "Maybe candidate, improve data"
        action_detail = "The site may still be useful, but the current data is too weak for advancement."
    else:
        action_label = "Monitor or deprioritize"
        action_detail = "Keep as lower priority unless new data or a special use case changes the result."

    if site_id == "PWC004":
        action_label = "Promising with timeline caveat"
        action_detail = "Keep as promising, but treat it as future/reopened until the renovation or operating-status caveat is resolved."

    return pd.Series(
        {
            "readiness_band": readiness_label,
            "confidence_band": confidence_label,
            "readiness_confidence_cell": matrix_cell,
            "action_label": action_label,
            "action_detail": action_detail,
        }
    )


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    view = df[columns].copy()
    view.columns = [column.replace("_", " ") for column in view.columns]
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in view.columns) + " |")
    return "\n".join([header, separator] + rows)


def build_report(results: pd.DataFrame) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    ranked = results.sort_values("model_rank")

    return f"""# Readiness-Confidence Action Matrix

Generated: {generated_at}

## Purpose

This report turns the model scores into simple next actions.

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is

action_label = what to do next
```

## Site actions

{markdown_table(ranked, ["model_rank", "site_id", "readiness_score", "data_confidence_score", "readiness_confidence_cell", "action_label"])}

## Action details

{markdown_table(ranked, ["site_id", "action_label", "action_detail"])}

## Simple rule

Do not treat a high-readiness site as ready to build. Use this matrix to decide what data or review is needed next.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Add readiness-confidence action matrix columns.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Action matrix Markdown report.")
    args = parser.parse_args()

    results_path = Path(args.results)
    report_path = Path(args.report)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    results = pd.read_csv(results_path)
    required = {"site_id", "site_name", "model_rank", "readiness_score", "data_confidence_score", "recommendation_tier", "public_access", "garage_enclosed"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    action_columns = results.apply(action_for_row, axis=1)
    enriched = pd.concat([results.drop(columns=[column for column in action_columns.columns if column in results.columns], errors="ignore"), action_columns], axis=1)
    enriched.to_csv(results_path, index=False)

    ensure_parent_dir(report_path)
    report_path.write_text(build_report(enriched), encoding="utf-8")

    print("READINESS-CONFIDENCE ACTION MATRIX")
    print("----------------------------------")
    print(f"Updated results: {results_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
