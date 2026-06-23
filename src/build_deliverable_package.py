"""Build a clean shareable deliverable package.

This script collects the most useful generated outputs and reporting documents
into one local folder that can be shared with mentors, reviewers, or
stakeholders.

Run from the repository root after the full model pipeline:

    python src/run_all.py
    python src/build_deliverable_package.py

Default output folder:

    data/outputs/deliverable_package/

The package folder is generated locally and ignored by Git.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = "data/outputs/deliverable_package"
SUCCESS_MARKER = "data/outputs/workflow_success.json"

PACKAGE_GROUPS = {
    "charts": [
        "data/outputs/charts/site_readiness_map.png",
        "data/outputs/charts/readiness_score_chart.png",
    ],
    "run_outputs": [
        "data/outputs/model_run_summary.md",
        "data/outputs/results_interpretation.md",
        "data/outputs/profile_comparison.md",
        "data/outputs/baseline_comparison.md",
    ],
    "data_tables": [
        "data/outputs/site_results.csv",
        "data/outputs/sensitivity_summary.csv",
        "data/outputs/profile_rank_summary.csv",
        "data/outputs/data_quality_report.csv",
    ],
    "reports": [
        "docs/PROJECT_STATUS.md",
        "docs/MODEL_FINDINGS_BRIEF.md",
        "docs/MODEL_FINDINGS_REPORT.md",
        "docs/PRESENTATION_OUTLINE.md",
        "docs/RESULTS_INTERPRETATION.md",
        "docs/READINESS_MAP_GUIDE.md",
        "docs/STAKEHOLDER_DATA_REQUEST.md",
        "docs/DATA_DICTIONARY.md",
        "docs/DATA_SOURCES.md",
    ],
}

GENERATED_GROUPS = {"charts", "run_outputs", "data_tables"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local deliverable package.")
    parser.add_argument("--output-dir", default=DEFAULT_PACKAGE_DIR, help="Package output folder.")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete the existing package folder first.")
    parser.add_argument(
        "--skip-success-check",
        action="store_true",
        help="Allow package creation without checking that the full workflow completed successfully.",
    )
    return parser.parse_args()


def generated_sources() -> list[Path]:
    paths: list[Path] = []
    for group_name, files in PACKAGE_GROUPS.items():
        if group_name in GENERATED_GROUPS:
            paths.extend(PROJECT_ROOT / relative_path for relative_path in files)
    return paths


def validate_success_marker() -> None:
    marker_path = PROJECT_ROOT / SUCCESS_MARKER
    if not marker_path.exists():
        raise SystemExit(
            f"Missing workflow success marker: {SUCCESS_MARKER}. "
            "Run `python src/run_all.py` successfully before building the deliverable package."
        )

    marker_mtime = marker_path.stat().st_mtime
    newer_outputs = [
        path.relative_to(PROJECT_ROOT)
        for path in generated_sources()
        if path.exists() and path.stat().st_mtime > marker_mtime
    ]
    if newer_outputs:
        joined = ", ".join(str(path) for path in newer_outputs)
        raise SystemExit(
            "Some generated outputs are newer than the latest successful workflow marker. "
            "This can happen after a failed or partial run. Re-run `python src/run_all.py` successfully first. "
            f"Newer outputs: {joined}"
        )


def copy_file(source_relative: str, package_dir: Path, group_name: str) -> dict[str, str]:
    source = PROJECT_ROOT / source_relative
    destination_dir = package_dir / group_name
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name

    if not source.exists():
        return {
            "source": source_relative,
            "destination": str(destination.relative_to(PROJECT_ROOT)),
            "status": "missing",
        }

    shutil.copy2(source, destination)
    return {
        "source": source_relative,
        "destination": str(destination.relative_to(PROJECT_ROOT)),
        "status": "copied",
    }


def build_package_readme(package_dir: Path, manifest: list[dict[str, str]]) -> str:
    copied = [item for item in manifest if item["status"] == "copied"]
    missing = [item for item in manifest if item["status"] == "missing"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []
    lines.append("# EV Charging Site-Readiness Deliverable Package")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("This folder collects the main files needed to review or present the current model run.")
    lines.append("")
    lines.append("## Recommended review order")
    lines.append("")
    lines.append("1. `reports/PROJECT_STATUS.md`")
    lines.append("2. `reports/MODEL_FINDINGS_BRIEF.md`")
    lines.append("3. `charts/site_readiness_map.png`")
    lines.append("4. `run_outputs/results_interpretation.md`")
    lines.append("5. `run_outputs/model_run_summary.md`")
    lines.append("6. `run_outputs/profile_comparison.md`")
    lines.append("7. `reports/PRESENTATION_OUTLINE.md`")
    lines.append("8. `reports/STAKEHOLDER_DATA_REQUEST.md`")
    lines.append("")
    lines.append("## Dynamic vs static files")
    lines.append("")
    lines.append("Files under `run_outputs/` are generated from the latest local model run. Files under `reports/` are static project documents that explain the project story, methodology, current status, and next data needs.")
    lines.append("")
    lines.append("## Included files")
    lines.append("")
    for item in copied:
        lines.append(f"- `{item['destination']}`")
    lines.append("")

    if missing:
        lines.append("## Missing files")
        lines.append("")
        lines.append("These files were expected but not found. Run `python src/run_all.py` and rebuild the package.")
        lines.append("")
        for item in missing:
            lines.append(f"- `{item['source']}`")
        lines.append("")

    lines.append("## Important limitation")
    lines.append("")
    lines.append("This package is for planning communication only. It does not replace utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, or stakeholder approval.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    package_dir = PROJECT_ROOT / args.output_dir

    if not args.skip_success_check:
        validate_success_marker()

    if package_dir.exists() and not args.no_clean:
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []
    for group_name, files in PACKAGE_GROUPS.items():
        for source_relative in files:
            manifest.append(copy_file(source_relative, package_dir, group_name))

    readme_path = package_dir / "README.md"
    readme_path.write_text(build_package_readme(package_dir, manifest), encoding="utf-8")

    manifest_path = package_dir / "package_manifest.json"
    manifest_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "package_dir": str(package_dir.relative_to(PROJECT_ROOT)),
        "files": manifest,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    copied_count = sum(1 for item in manifest if item["status"] == "copied")
    missing_count = sum(1 for item in manifest if item["status"] == "missing")

    print("DELIVERABLE PACKAGE")
    print("-------------------")
    print(f"Package folder: {package_dir.relative_to(PROJECT_ROOT)}")
    print(f"Copied files: {copied_count}")
    print(f"Missing files: {missing_count}")
    print(f"Saved: {readme_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {manifest_path.relative_to(PROJECT_ROOT)}")

    if missing_count:
        print()
        print("Missing expected files:")
        for item in manifest:
            if item["status"] == "missing":
                print(f"- {item['source']}")
        raise SystemExit(1)

    print()
    print("Done. The deliverable package is ready to review or share.")


if __name__ == "__main__":
    main()
