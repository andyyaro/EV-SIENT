"""Small helpers for loading project configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUTPUT_MANIFEST_PATH = "data/config/output_manifest_v1.json"


def load_output_manifest(project_root: Path, relative_path: str = OUTPUT_MANIFEST_PATH) -> dict[str, Any]:
    """Load the shared output manifest.

    The manifest is the single source of truth for expected generated outputs,
    required checker outputs, and deliverable package contents.
    """
    path = project_root / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Missing output manifest: {relative_path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return data


def require_list(manifest: dict[str, Any], key: str) -> list[str]:
    """Return a required manifest list as strings."""
    value = manifest.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Output manifest key must be a list: {key}")
    return [str(item) for item in value]


def require_dict_of_lists(manifest: dict[str, Any], key: str) -> dict[str, list[str]]:
    """Return a required manifest dictionary of string lists."""
    value = manifest.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Output manifest key must be an object: {key}")

    result: dict[str, list[str]] = {}
    for group_name, group_files in value.items():
        if not isinstance(group_files, list):
            raise ValueError(f"Output manifest group must be a list: {key}.{group_name}")
        result[str(group_name)] = [str(item) for item in group_files]
    return result
