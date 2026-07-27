"""
build_models.py — generate one proposed-build GLB per candidate site.

Reads web/data/sites.geojson (produced by fcf3d.build_sites), and for each
site emits web/models/<SITE_ID>.glb sized to that site's own right-sizing
result: energised ports now, plus translucent stalls for the pathway capacity
the model says to reserve.

    python -m fcf3d.build_models --sites web/data/sites.geojson --out web/models

Use --blender /path/to/blender to route through blender/build_assets.py
instead, which produces the higher-fidelity presentation assets.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from .geometry import build_site
from .glb import write_glb


def load_sites(path: str) -> list[dict]:
    with open(path) as fh:
        data = json.load(fh)
    return data["features"] if "features" in data else data


def run_pure_python(sites: list[dict], out_dir: str) -> list[tuple[str, str, int]]:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for feature in sites:
        props = feature["properties"] if "properties" in feature else feature
        sid = props["site_id"]
        asset = props.get("asset", {})
        build = build_site(
            sid,
            ports_now=asset.get("ports", props.get("ports_now") or 2),
            ports_pathway=asset.get("pathway_ports", props.get("ports_2050") or 2),
        )
        path = os.path.join(out_dir, f"{sid}.glb")
        write_glb(build, path)
        written.append((sid, path, os.path.getsize(path)))
    return written


def run_blender(blender: str, sites_path: str, out_dir: str) -> int:
    script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blender", "build_assets.py")
    cmd = [
        blender, "--background", "--factory-startup", "--python", script,
        "--", "--sites", sites_path, "--out", out_dir,
    ]
    print("[fcf3d] " + " ".join(cmd))
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites", default="web/data/sites.geojson")
    ap.add_argument("--out", default="web/models")
    ap.add_argument("--blender", default=None, help="path to a Blender executable")
    args = ap.parse_args(argv)

    if args.blender:
        return run_blender(args.blender, args.sites, args.out)

    sites = load_sites(args.sites)
    written = run_pure_python(sites, args.out)
    total = sum(size for _, _, size in written)
    print(f"[fcf3d] {len(written)} models -> {args.out} ({total:,} bytes total)")
    for sid, path, size in written:
        print(f"  {sid}  {os.path.basename(path):16s} {size:>8,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
