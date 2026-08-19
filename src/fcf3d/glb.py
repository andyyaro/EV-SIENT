"""
glb.py - write a SiteBuild to a binary glTF 2.0 (.glb) file.

Zero dependencies, pure stdlib. This exists so the pipeline is runnable and
testable in CI without a Blender install; `blender/build_assets.py` produces
the higher-fidelity version of the same geometry for presentation work.

Output conforms to glTF 2.0: one mesh, one primitive per material, indexed
TRIANGLES, flat-shaded (each face gets its own vertices so normals are crisp),
Y-up as the spec requires.
"""

from __future__ import annotations

import base64
import json
import struct
from collections import defaultdict

from .geometry import MATERIALS, Box, SiteBuild

# glTF component / accessor constants
FLOAT = 5126
UNSIGNED_INT = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963
TRIANGLES = 4

# the six faces of a unit box, as indices into corners_enu()'s ordering
# corners_enu emits in the order (sx, sy, sz) with sx outer, sz inner:
#   0:(-,-,-) 1:(-,-,+) 2:(-,+,-) 3:(-,+,+) 4:(+,-,-) 5:(+,-,+) 6:(+,+,-) 7:(+,+,+)
FACES = [
    (4, 6, 7, 5),  # +X east
    (2, 0, 1, 3),  # -X west
    (6, 2, 3, 7),  # +Y north
    (0, 4, 5, 1),  # -Y south
    (1, 5, 7, 3),  # +Z up
    (2, 6, 4, 0),  # -Z down
]


def _normal(a, b, c) -> tuple[float, float, float]:
    ux, uy, uz = (b[i] - a[i] for i in range(3))
    vx, vy, vz = (c[i] - a[i] for i in range(3))
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
    return (nx / length, ny / length, nz / length)


def _tessellate(box: Box) -> tuple[list[tuple], list[tuple], list[int]]:
    """Return (positions_gltf, normals, indices) for one box, flat shaded."""
    corners = [Box.enu_to_gltf(p) for p in box.corners_enu()]
    positions: list[tuple] = []
    normals: list[tuple] = []
    indices: list[int] = []
    for quad in FACES:
        a, b, c, d = (corners[i] for i in quad)
        n = _normal(a, b, c)
        base = len(positions)
        positions.extend([a, b, c, d])
        normals.extend([n, n, n, n])
        indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])
    return positions, normals, indices


def _pad4(data: bytes, fill: bytes = b"\x00") -> bytes:
    return data + fill * ((4 - len(data) % 4) % 4)


def build_gltf(site: SiteBuild, *, name: str | None = None) -> tuple[dict, bytes]:
    """Return (gltf_json, binary_buffer) for a SiteBuild."""
    by_material: dict[str, list[Box]] = defaultdict(list)
    for box in site.boxes:
        by_material[box.material].append(box)

    material_names = list(by_material.keys())
    materials = []
    for mat in material_names:
        colour, metallic, roughness = MATERIALS.get(
            mat, ((0.8, 0.8, 0.8, 1.0), 0.0, 0.8)
        )
        entry = {
            "name": mat,
            "pbrMetallicRoughness": {
                "baseColorFactor": list(colour),
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
            "doubleSided": False,
        }
        if colour[3] < 1.0:
            entry["alphaMode"] = "BLEND"
        materials.append(entry)

    buffer = bytearray()
    buffer_views: list[dict] = []
    accessors: list[dict] = []
    primitives: list[dict] = []

    def add_view(payload: bytes, target: int) -> int:
        nonlocal buffer
        offset = len(buffer)
        buffer.extend(payload)
        buffer.extend(b"\x00" * ((4 - len(buffer) % 4) % 4))
        buffer_views.append(
            {"buffer": 0, "byteOffset": offset, "byteLength": len(payload), "target": target}
        )
        return len(buffer_views) - 1

    for mat_index, mat in enumerate(material_names):
        positions: list[tuple] = []
        normals: list[tuple] = []
        indices: list[int] = []
        for box in by_material[mat]:
            p, n, idx = _tessellate(box)
            offset = len(positions)
            positions.extend(p)
            normals.extend(n)
            indices.extend(i + offset for i in idx)

        pos_bytes = b"".join(struct.pack("<3f", *v) for v in positions)
        nrm_bytes = b"".join(struct.pack("<3f", *v) for v in normals)
        idx_bytes = b"".join(struct.pack("<I", i) for i in indices)

        pos_view = add_view(pos_bytes, ARRAY_BUFFER)
        nrm_view = add_view(nrm_bytes, ARRAY_BUFFER)
        idx_view = add_view(idx_bytes, ELEMENT_ARRAY_BUFFER)

        mins = [min(v[i] for v in positions) for i in range(3)]
        maxs = [max(v[i] for v in positions) for i in range(3)]

        accessors.append(
            {
                "bufferView": pos_view,
                "componentType": FLOAT,
                "count": len(positions),
                "type": "VEC3",
                "min": mins,
                "max": maxs,
            }
        )
        pos_acc = len(accessors) - 1
        accessors.append(
            {
                "bufferView": nrm_view,
                "componentType": FLOAT,
                "count": len(normals),
                "type": "VEC3",
            }
        )
        nrm_acc = len(accessors) - 1
        accessors.append(
            {
                "bufferView": idx_view,
                "componentType": UNSIGNED_INT,
                "count": len(indices),
                "type": "SCALAR",
            }
        )
        idx_acc = len(accessors) - 1

        primitives.append(
            {
                "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc},
                "indices": idx_acc,
                "material": mat_index,
                "mode": TRIANGLES,
            }
        )

    mesh_name = name or f"{site.site_id}_evse_build"
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "fcf3d.glb (Future City Fellowship / ChargeReady NOVA)",
        },
        "scene": 0,
        "scenes": [{"nodes": [0], "name": mesh_name}],
        "nodes": [{"mesh": 0, "name": mesh_name}],
        "meshes": [{"name": mesh_name, "primitives": primitives}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(buffer)}],
        "extras": {
            "site_id": site.site_id,
            "ports_now": site.ports_now,
            "ports_pathway": site.ports_pathway,
            "ada_stalls": site.ada_stalls,
            "footprint_m": list(site.footprint_m),
            "part_count": site.part_count,
            "note": "Screening-level massing for siting discussion. Not a design.",
        },
    }
    return gltf, bytes(buffer)


def write_glb(site: SiteBuild, path: str) -> str:
    """Write a SiteBuild to `path` as a .glb. Returns the path."""
    gltf, binary = build_gltf(site)
    json_chunk = _pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    bin_chunk = _pad4(binary)

    total = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, total))
        fh.write(struct.pack("<I4s", len(json_chunk), b"JSON"))
        fh.write(json_chunk)
        fh.write(struct.pack("<I4s", len(bin_chunk), b"BIN\x00"))
        fh.write(bin_chunk)
    return path


def to_data_uri(site: SiteBuild) -> str:
    """Embed a SiteBuild as a base64 data URI (handy for single-file demos)."""
    gltf, binary = build_gltf(site)
    gltf["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(
        binary
    ).decode("ascii")
    return "data:model/gltf+json;base64," + base64.b64encode(
        json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
