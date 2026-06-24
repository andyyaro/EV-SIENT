"""Build a clean shareable deliverable package."""

from __future__ import annotations

import argparse
import hashlib
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
        "data/outputs/charts/data_confidence_chart.png",
        "data/outputs/charts/profile_rank_stability_chart.png",
        "data/outputs/charts/profile_score_heatmap.png",
    ],
    "run_outputs": [
        "data/outputs/workflow_success.json",
        "data/outputs/model_run_summary.md",
        "data/outputs/results_interpretation.md",
        "data/outputs/action_matrix.md",
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
        "START_HERE.md",
        "docs/REPO_MAP.md",
        "docs/PROJECT_STATUS.md",
        "docs/MODEL_FINDINGS_BRIEF.md",
        "docs/MODEL_FINDINGS_REPORT.md",
        "docs/PRESENTATION_OUTLINE.md",
        "docs/RESULTS_INTERPRETATION.md",
        "docs/READINESS_MAP_GUIDE.md",
        "docs/DATA_CONFIDENCE_SCORE.md",
        "docs/SITE_SCREENING_CHECKLIST.md",
        "docs/ADDING_NEW_SITES_GUIDE.md",
        "docs/STAKEHOLDER_DATA_REQUEST.md",
        "docs/STAKEHOLDER_CONTACT_PLAN.md",
        "docs/DATA_DICTIONARY.md",
        "docs/DATA_SOURCES.md",
    ],
    "expansion_inputs": [
        "data/inputs/new_sites_template.csv",
        "data/source_extracts/site_screening_checklist.csv",
    ],
    "stakeholder_inputs": [
        "data/source_extracts/stakeholder_data_request_fields.csv",
        "data/source_extracts/stakeholder_response_tracker.csv",
    ],
}

GENERATED_GROUPS = {"charts", "run_outputs", "data_tables"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local deliverable package.")
    parser.add_argument("--output-dir", default=DEFAULT_PACKAGE_DIR, help="Package output folder.")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete the existing package folder first.")
    parser.add_argument("--skip-success-check", action="store_true", help="Skip the workflow success check.")
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
        raise SystemExit(f"Missing workflow success marker: {SUCCESS_MARKER}. Run `python src/run_all.py` first.")

    marker_mtime = marker_path.stat().st_mtime
    newer_outputs = [
        path.relative_to(PROJECT_ROOT)
        for path in generated_sources()
        if path.exists() and path != marker_path and path.stat().st_mtime > marker_mtime
    ]
    if newer_outputs:
        joined = ", ".join(str(path) for path in newer_outputs)
        raise SystemExit(f"Generated outputs are newer than the success marker. Re-run `python src/run_all.py`. Newer outputs: {joined}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def copy_file(source_relative: str, package_dir: Path, group_name: str) -> dict[str, str]:
    source = PROJECT_ROOT / source_relative
    destination_dir = package_dir / group_name
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    copied_at = datetime.now().isoformat(timespec="seconds")

    if not source.exists():
        return {
            "source": source_relative,
            "destination": str(destination.relative_to(PROJECT_ROOT)),
            "status": "missing",
            "copied_at": copied_at,
        }

    source_sha256 = sha256_file(source)
    source_modified_at = iso_mtime(source)
    shutil.copyfile(source, destination)
    destination_sha256 = sha256_file(destination)
    destination_modified_at = iso_mtime(destination)

    if source_sha256 != destination_sha256:
        raise SystemExit(f"Copied file hash mismatch: {source_relative}")

    return {
        "source": source_relative,
        "destination": str(destination.relative_to(PROJECT_ROOT)),
        "status": "copied",
        "source_modified_at": source_modified_at,
        "destination_modified_at": destination_modified_at,
        "copied_at": copied_at,
        "sha256": source_sha256,
    }


def build_package_readme(manifest: list[dict[str, str]]) -> str:
    copied = [item for item in manifest if item["status"] == "copied"]
    missing = [item for item in manifest if item["status"] == "missing"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = [
        "# EV Charging Site-Readiness Deliverable Package",
        "",
        f"Generated: {generated_at}",
        "",
        "## Recommended review order",
        "",
        "1. `reports/START_HERE.md`",
        "2. `reports/REPO_MAP.md`",
        "3. `run_outputs/model_run_summary.md`",
        "4. `run_outputs/results_interpretation.md`",
        "5. `run_outputs/action_matrix.md`",
        "6. `charts/site_readiness_map.png`",
        "7. `charts/readiness_score_chart.png`",
        "8. `charts/data_confidence_chart.png`",
        "9. `charts/profile_rank_stability_chart.png`",
        "10. `reports/MODEL_FINDINGS_BRIEF.md`",
        "11. `reports/DATA_DICTIONARY.md`",
        "12. `reports/DATA_SOURCES.md`",
        "13. `reports/STAKEHOLDER_DATA_REQUEST.md`",
        "14. `reports/STAKEHOLDER_CONTACT_PLAN.md`",
        "15. `stakeholder_inputs/stakeholder_response_tracker.csv`",
        "",
        "## Included files",
        "",
    ]

    for item in copied:
        lines.append(f"- `{item['destination']}`")
    lines.append("")

    if missing:
        lines.extend(["## Missing files", ""])
        for item in missing:
            lines.append(f"- `{item['source']}`")
        lines.append("")

    lines.extend(["## Limitation", "", "This package is for planning communication only.", ""])
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
    readme_path.write_text(build_package_readme(manifest), encoding="utf-8")

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
