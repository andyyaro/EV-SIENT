"""
build_assets.py — headless Blender asset factory for ChargeReady NOVA.

Builds the proposed EV charging infrastructure for every candidate site and
exports one glTF-Binary per site, ready for CesiumJS to place at real-world
coordinates.

Run WITHOUT opening Blender's UI:

    blender --background --factory-startup --python blender/build_assets.py -- \
        --sites web/data/sites.geojson --out web/models

or via the wrapper, which is what the Makefile does:

    python -m fcf3d.build_models --blender /Applications/Blender.app/Contents/MacOS/Blender

Why this exists alongside fcf3d/glb.py
--------------------------------------
`fcf3d.glb` writes the same massing with no dependencies, so CI can build and
test the pipeline on a runner with no Blender. This script is the presentation
path: it adds bevels, real PBR materials, smoothed shading, named collections,
and gives you a .blend you can open and art-direct by hand. Both read their
geometry from `fcf3d.geometry`, so they cannot drift apart.

Blender is an AUTHORING tool here, not the viewer. It never ships to the
browser — it produces glTF, and CesiumJS does the delivery.
"""

from __future__ import annotations

import json
import math
import os
import sys

import bpy  # noqa: F401  (only resolvable inside Blender)
import bmesh

# --- make the repo's fcf3d package importable inside Blender's Python --------
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from fcf3d.geometry import MATERIALS, build_site  # noqa: E402

BEVEL_WIDTH = 0.015


# ---------------------------------------------------------------------------
# Scene management
# ---------------------------------------------------------------------------


def reset_scene() -> None:
    """Empty the file completely — --factory-startup still ships a default cube."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for item in list(block):
            block.remove(item)


def get_material(name: str):
    """Create (or fetch) a Principled BSDF material from the shared palette."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    colour, metallic, roughness = MATERIALS.get(name, ((0.8, 0.8, 0.8, 1.0), 0.0, 0.8))
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if colour[3] < 1.0:
        # translucent "pathway capacity" stalls
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = colour[3]
        mat.blend_method = "BLEND"
    return mat


def make_box(box, collection) -> "bpy.types.Object":
    """Create one bevelled box object from a geometry.Box, in Blender's Z-up ENU."""
    mesh = bpy.data.meshes.new(box.name)
    obj = bpy.data.objects.new(box.name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=box.size, verts=bm.verts)
    if BEVEL_WIDTH > 0:
        smallest = min(box.size)
        width = min(BEVEL_WIDTH, smallest * 0.2)
        if width > 1e-4:
            bmesh.ops.bevel(
                bm,
                geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                offset=width,
                segments=2,
                profile=0.7,
                affect="EDGES",
            )
    bm.to_mesh(mesh)
    bm.free()

    obj.location = box.center
    obj.rotation_euler = (0.0, 0.0, math.radians(box.yaw_deg))
    obj.data.materials.append(get_material(box.material))
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def build_blender_site(site_id: str, ports_now: int, ports_pathway: int):
    """Populate the current scene with one site's proposed build."""
    spec = build_site(site_id, ports_now=ports_now, ports_pathway=ports_pathway)

    root = bpy.data.collections.new(f"{site_id}_build")
    bpy.context.scene.collection.children.link(root)

    groups: dict[str, "bpy.types.Collection"] = {}
    for box in spec.boxes:
        group_name = box.name.split("_")[0]
        if group_name not in groups:
            sub = bpy.data.collections.new(f"{site_id}_{group_name}")
            root.children.link(sub)
            groups[group_name] = sub
        make_box(box, groups[group_name])

    return spec


def export_glb(path: str, spec) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_yup=True,             # glTF is Y-up; Blender converts from Z-up
        export_apply=True,           # bake modifiers
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        use_selection=False,
    )
    print(
        f"[blender] {spec.site_id}: {spec.part_count} parts, "
        f"{spec.ports_now} energised / {spec.ports_pathway} pathway ports "
        f"-> {path} ({os.path.getsize(path):,} bytes)"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> dict:
    """Blender passes script args after a bare `--`."""
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    args = {"sites": "web/data/sites.geojson", "out": "web/models", "blend": None}
    it = iter(argv)
    for token in it:
        if token in ("--sites", "--out", "--blend"):
            args[token[2:]] = next(it, None)
    return args


def main() -> None:
    args = parse_args(sys.argv)

    with open(args["sites"]) as fh:
        data = json.load(fh)
    features = data["features"] if "features" in data else data

    for feature in features:
        props = feature.get("properties", feature)
        sid = props["site_id"]
        asset = props.get("asset", {})
        ports_now = int(asset.get("ports") or props.get("ports_now") or 2)
        ports_pathway = int(asset.get("pathway_ports") or props.get("ports_2050") or ports_now)

        reset_scene()
        spec = build_blender_site(sid, ports_now, ports_pathway)
        export_glb(os.path.join(args["out"], f"{sid}.glb"), spec)

        if args["blend"]:
            os.makedirs(args["blend"], exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args["blend"], f"{sid}.blend"))

    print(f"[blender] done: {len(features)} sites -> {args['out']}")


if __name__ == "__main__":
    main()
