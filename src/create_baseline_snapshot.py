"""Create a curated baseline snapshot from generated model outputs.

Run this after a successful model run when the project intentionally wants to
save a new official baseline for comparison.

Example:

    python src/run_all.py
    python src/create_baseline_snapshot.py --label v1_baseline --overwrite

The baseline files are small, curated CSV/JSON files that can be committed to
the repository. This is different from data/outputs/, which stays local and is
ignored by Git.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASELINE_FILES = [
    "site_results.csv",
    "sensitivity_summary.csv",
    "data_quality_report.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a model baseline snapshot.")
    parser.add_argument("--label", default="v1_baseline", help="Baseline folder name to create.")
    parser.add_argument("--source-dir", default="data/outputs", help="Folder containing generated outputs.")
    parser.add_argument("--baseline-root", default="data/baselines", help="Folder where baselines are stored.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing baseline folder.")
    parser.add_argument("--notes", default="", help="Optional note to store in the baseline manifest.")
    return parser.parse_args()


def read_top_site(site_results_path: Path) -> str:
    results = pd.read_csv(site_results_path)
    ranks = pd.to_numeric(results["model_rank"], errors="coerce")
    top_row = results.loc[ranks.idxmin()]
    return str(top_row["site_id"])


def count_quality_errors(data_quality_path: Path) -> int:
    report = pd.read_csv(data_quality_path)
    if "severity" not in report.columns:
        return -1
    return int((report["severity"] == "ERROR").sum())


def main() -> None:
    args = parse_args()

    source_dir = PROJECT_ROOT / args.source_dir
    baseline_dir = PROJECT_ROOT / args.baseline_root / args.label

    missing = [name for name in BASELINE_FILES if not (source_dir / name).exists()]
    if missing:
        raise SystemExit(f"Cannot create baseline. Missing generated output files: {missing}")

    if baseline_dir.exists():
        if not args.overwrite:
            raise SystemExit(
                f"Baseline already exists: {baseline_dir}. Use --overwrite to replace it."
            )
        shutil.rmtree(baseline_dir)

    baseline_dir.mkdir(parents=True, exist_ok=True)

    for file_name in BASELINE_FILES:
        shutil.copy2(source_dir / file_name, baseline_dir / file_name)

    site_results_path = baseline_dir / "site_results.csv"
    data_quality_path = baseline_dir / "data_quality_report.csv"
    site_count = len(pd.read_csv(site_results_path))

    manifest = {
        "baseline_label": args.label,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Curated benchmark snapshot for comparing future model runs.",
        "source_directory": args.source_dir,
        "files": BASELINE_FILES,
        "site_count": site_count,
        "top_site_id": read_top_site(site_results_path),
        "data_quality_error_count": count_quality_errors(data_quality_path),
        "notes": args.notes,
    }

    manifest_path = baseline_dir / "baseline_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Created baseline snapshot: {baseline_dir.relative_to(PROJECT_ROOT)}")
    print(f"Top site: {manifest['top_site_id']}")
    print(f"Data-quality ERROR count: {manifest['data_quality_error_count']}")
    print("Review the baseline files, then commit them if this should become an official baseline.")


if __name__ == "__main__":
    main()
