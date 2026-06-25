"""Build a clean V2 deliverable package folder."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_FILES = [
    ("data/outputs/v2_executive_site_summary.csv", "tables/v2_executive_site_summary.csv"),
    ("data/outputs/v2_executive_site_summary.md", "reports/v2_executive_site_summary.md"),
    ("data/outputs/v2_right_sizing_validation.csv", "tables/v2_right_sizing_validation.csv"),
    ("data/outputs/v2_right_sizing_validation_report.md", "reports/v2_right_sizing_validation_report.md"),
    ("data/outputs/v2_site_results.csv", "tables/v2_site_results.csv"),
    ("data/outputs/v2_action_matrix.md", "reports/v2_action_matrix.md"),
    ("data/outputs/v2_sensitivity_summary.csv", "tables/v2_sensitivity_summary.csv"),
    ("data/outputs/v2_profile_results.csv", "tables/v2_profile_results.csv"),
    ("data/outputs/v2_profile_rank_summary.csv", "tables/v2_profile_rank_summary.csv"),
    ("data/outputs/v2_profile_comparison.md", "reports/v2_profile_comparison.md"),
    ("data/outputs/v2_right_sizing_scenarios.csv", "tables/v2_right_sizing_scenarios.csv"),
    ("data/outputs/v2_right_sizing_report.md", "reports/v2_right_sizing_report.md"),
    ("data/outputs/v2_port_utilization_simulation.csv", "tables/v2_port_utilization_simulation.csv"),
    ("data/outputs/v2_port_utilization_simulation_report.md", "reports/v2_port_utilization_simulation_report.md"),
    ("data/outputs/v2_electrical_risk_summary.csv", "tables/v2_electrical_risk_summary.csv"),
    ("data/outputs/v2_electrical_feasibility_report.md", "reports/v2_electrical_feasibility_report.md"),
    ("data/outputs/v2_data_quality_report.csv", "tables/v2_data_quality_report.csv"),
    ("data/outputs/v2_results_interpretation.md", "reports/v2_results_interpretation.md"),
    ("data/outputs/v2_run_summary.md", "reports/v2_run_summary.md"),
    ("data/outputs/v2_baseline_comparison.json", "manifests/v2_baseline_comparison.json"),
    ("data/outputs/v2_baseline_comparison.md", "reports/v2_baseline_comparison.md"),
    ("data/outputs/v2_workflow_success.json", "manifests/v2_workflow_success.json"),
    ("data/outputs/charts/v2_polished_readiness_score_chart.png", "charts/v2_polished_readiness_score_chart.png"),
    ("data/outputs/charts/v2_data_confidence_chart.png", "charts/v2_data_confidence_chart.png"),
    ("data/outputs/charts/v2_profile_score_heatmap.png", "charts/v2_profile_score_heatmap.png"),
    ("data/outputs/charts/v2_profile_rank_stability_chart.png", "charts/v2_profile_rank_stability_chart.png"),
    ("data/outputs/charts/v2_site_readiness_map.png", "charts/v2_site_readiness_map.png"),
    ("data/outputs/charts/v2_site_decision_map.png", "charts/v2_site_decision_map.png"),
    ("data/outputs/charts/v2_port_utilization_simulation.png", "charts/v2_port_utilization_simulation.png"),
]

DEFAULT_PACKAGE_DIR = Path("data/outputs/deliverable_package_v2")
SAFE_OUTPUT_ROOT = Path("data/outputs")


def copy_file(source: Path, destination: Path) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists() or source.stat().st_size == 0:
        return {
            "source": str(source),
            "destination": str(destination),
            "copied": False,
            "size_bytes": 0,
        }
    shutil.copy2(source, destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "copied": True,
        "size_bytes": destination.stat().st_size,
    }


def is_safe_package_dir(package_dir: Path) -> bool:
    """Return True when it is safe for this script to delete the package folder."""
    try:
        resolved_package = package_dir.resolve()
        resolved_root = SAFE_OUTPUT_ROOT.resolve()
        return resolved_package == DEFAULT_PACKAGE_DIR.resolve() or resolved_root in resolved_package.parents
    except OSError:
        return False


def clean_package_dir(package_dir: Path) -> bool:
    """Delete the old package folder so stale copied files cannot survive rebuilds."""
    if not package_dir.exists():
        return False
    if not is_safe_package_dir(package_dir):
        raise ValueError(
            f"Refusing to clean package directory outside {SAFE_OUTPUT_ROOT}: {package_dir}. "
            "Use a path under data/outputs or run with --no-clean."
        )
    if not package_dir.is_dir():
        raise ValueError(f"Package output path exists but is not a directory: {package_dir}")
    shutil.rmtree(package_dir)
    return True


def build_readme(package_dir: Path, manifest: dict[str, object]) -> str:
    copied = [item for item in manifest["files"] if item["copied"]]
    missing = [item for item in manifest["files"] if not item["copied"]]
    copied_lines = "\n".join(f"- `{Path(item['destination']).relative_to(package_dir)}`" for item in copied)
    missing_lines = "\n".join(f"- `{item['source']}`" for item in missing) if missing else "None"
    return f"""# V2 Deliverable Package

This folder contains the cleanest outputs from the V2 EV charging site-readiness and right-sizing workflow.

## Package status

```text
Status: {manifest['status']}
Copied files: {manifest['copied_count']}/{manifest['expected_count']}
Generated at UTC: {manifest['generated_at_utc']}
Clean rebuild: {manifest['clean_rebuild']}
Previous package removed: {manifest['previous_package_removed']}
```

## Included files

{copied_lines}

## Missing or empty files

{missing_lines}

## Suggested review order

```text
1. reports/v2_executive_site_summary.md
2. tables/v2_executive_site_summary.csv
3. reports/v2_right_sizing_validation_report.md
4. charts/v2_site_decision_map.png
5. reports/v2_run_summary.md
6. reports/v2_action_matrix.md
7. reports/v2_profile_comparison.md
8. tables/v2_sensitivity_summary.csv
9. charts/v2_polished_readiness_score_chart.png
10. charts/v2_site_readiness_map.png
11. charts/v2_profile_rank_stability_chart.png
```

## Notes

This is a planning prototype deliverable package. It is not an engineering design, procurement package, utility approval, or permitting approval.
"""


def build_package(package_dir: Path, clean: bool = True) -> dict[str, object]:
    removed_existing_package = clean_package_dir(package_dir) if clean else False
    package_dir.mkdir(parents=True, exist_ok=True)

    copied_records = []
    for source_text, destination_text in PACKAGE_FILES:
        copied_records.append(copy_file(Path(source_text), package_dir / destination_text))
    missing = [record["source"] for record in copied_records if not record["copied"]]
    manifest = {
        "package": "v2_deliverable_package",
        "status": "complete" if not missing else "incomplete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package_dir": str(package_dir),
        "clean_rebuild": clean,
        "previous_package_removed": removed_existing_package,
        "expected_count": len(copied_records),
        "copied_count": len(copied_records) - len(missing),
        "missing_or_empty_sources": missing,
        "files": copied_records,
    }
    (package_dir / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (package_dir / "README.md").write_text(build_readme(package_dir, manifest), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the V2 deliverable package folder.")
    parser.add_argument("--output-dir", default=str(DEFAULT_PACKAGE_DIR))
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove the existing package folder before copying outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package_dir = Path(args.output_dir)
    manifest = build_package(package_dir, clean=not args.no_clean)
    print("V2 DELIVERABLE PACKAGE")
    print("----------------------")
    print(f"Status: {manifest['status']}")
    print(f"Package dir: {package_dir}")
    print(f"Clean rebuild: {manifest['clean_rebuild']}")
    print(f"Previous package removed: {manifest['previous_package_removed']}")
    print(f"Copied files: {manifest['copied_count']}/{manifest['expected_count']}")
    print(f"Manifest: {package_dir / 'package_manifest.json'}")
    print(f"Readme: {package_dir / 'README.md'}")
    if manifest["missing_or_empty_sources"]:
        print("Missing or empty sources:")
        for source in manifest["missing_or_empty_sources"]:
            print(f"- {source}")


if __name__ == "__main__":
    main()
