"""Build a clean shareable deliverable package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from project_config import load_output_manifest, require_dict_of_lists, require_list

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = "data/outputs/deliverable_package"
OUTPUT_MANIFEST = load_output_manifest(PROJECT_ROOT)
SUCCESS_MARKER = str(OUTPUT_MANIFEST.get("success_marker", "data/outputs/workflow_success.json"))
PACKAGE_GROUPS = require_dict_of_lists(OUTPUT_MANIFEST, "package_groups")
GENERATED_GROUPS = set(require_list(OUTPUT_MANIFEST, "generated_package_groups"))
PACKAGE_REVIEW_ORDER = require_list(OUTPUT_MANIFEST, "package_review_order")


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
    ]

    for number, path in enumerate(PACKAGE_REVIEW_ORDER, start=1):
        lines.append(f"{number}. `{path}`")

    lines.extend(["", "## Included files", ""])

    for item in copied:
        lines.append(f"- `{item['destination']}`")
    lines.append("")

    if missing:
        lines.extend(["## Missing files", ""])
        for item in missing:
            lines.append(f"- `{item['source']}`")
        lines.append("")

    lines.extend(
        [
            "## Source of package file lists",
            "",
            "Package contents are defined in `data/config/output_manifest_v1.json`.",
            "",
            "## Limitation",
            "",
            "This package is for planning communication only.",
            "",
        ]
    )
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
        "source_manifest": "data/config/output_manifest_v1.json",
        "files": manifest,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    copied_count = sum(1 for item in manifest if item["status"] == "copied")
    missing_count = sum(1 for item in manifest if item["status"] == "missing")

    print("DELIVERABLE PACKAGE")
    print("-------------------")
    print(f"Package folder: {package_dir.relative_to(PROJECT_ROOT)}")
    print("Source manifest: data/config/output_manifest_v1.json")
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
