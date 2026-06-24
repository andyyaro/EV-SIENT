"""Copy generated chart PNGs into committed Markdown preview assets.

Generated model charts live in:

    data/outputs/charts/

That folder is intentionally ignored by Git because the files are generated.
Markdown preview charts should live in:

    docs/assets/charts/

Run this after `python src/run_all.py` when you want the README and docs to show
the latest generated visuals on GitHub.
"""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "outputs" / "charts"
DESTINATION_DIR = PROJECT_ROOT / "docs" / "assets" / "charts"

CHART_FILES = [
    "site_readiness_map.png",
    "readiness_score_chart.png",
    "data_confidence_chart.png",
    "profile_rank_stability_chart.png",
    "profile_score_heatmap.png",
]


def main() -> None:
    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    copied: list[str] = []

    for filename in CHART_FILES:
        source = SOURCE_DIR / filename
        destination = DESTINATION_DIR / filename

        if not source.exists():
            missing.append(str(source.relative_to(PROJECT_ROOT)))
            continue

        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(PROJECT_ROOT)))

    print("SYNC VISUAL ASSETS")
    print("------------------")
    print(f"Source folder: {SOURCE_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Destination folder: {DESTINATION_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Copied files: {len(copied)}")

    for path in copied:
        print(f"- {path}")

    if missing:
        print()
        print("Missing generated charts:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit("Run `python src/run_all.py` first, then rerun this script.")

    print()
    print("Done. Commit the files under docs/assets/charts/ to update GitHub-rendered visuals.")


if __name__ == "__main__":
    main()
