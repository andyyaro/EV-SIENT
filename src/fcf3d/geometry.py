"""
geometry.py - parametric geometry for proposed EV charging infrastructure.

This module is the single source of truth for what a "proposed site build"
looks like in 3D. It is imported by BOTH:

  blender/build_assets.py   -> renders it with bpy (production assets)
  fcf3d/glb.py              -> writes it straight to GLB (no Blender needed)

so the two paths can never drift. It has no dependencies at all.

Coordinate convention (ENU, metres):
    +X = East    +Y = North    +Z = Up
    origin = ground level, centre of the stall row

Cesium places glTF using an east-north-up frame, and glTF itself is Y-up.
`Box.to_gltf()` handles that conversion (ENU x,y,z -> glTF x, z, -y) so callers
never have to think about it. Blender is natively Z-up ENU, so the Blender
path uses the ENU values directly and lets Blender's glTF exporter convert.

Dimensions follow common US surface-lot practice for a screening-level massing
study. They are illustrative geometry for siting discussions, NOT a design.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- dimensional constants (metres) ------------------------------------------

STALL_WIDTH = 2.75
STALL_LENGTH = 5.50
ADA_STALL_WIDTH = 4.90  # stall + access aisle, ADA van-accessible
AISLE_CLEAR = 1.50

CANOPY_HEIGHT = 4.30
CANOPY_THICKNESS = 0.28
CANOPY_OVERHANG = 0.55

COLUMN_SIDE = 0.30
PEDESTAL = (0.50, 0.34, 1.45)  # width, depth, height - L2/DCFC dispenser
CABINET = (1.60, 0.90, 2.00)  # DCFC power cabinet
TRANSFORMER = (2.10, 1.60, 1.80)  # pad-mount transformer
PAD_THICKNESS = 0.06

# --- materials ---------------------------------------------------------------
# (name, base colour RGBA, metallic, roughness)
MATERIALS: dict[str, tuple[tuple[float, float, float, float], float, float]] = {
    "canopy":      ((0.847, 0.859, 0.878, 1.00), 0.35, 0.55),
    "column":      ((0.635, 0.663, 0.694, 1.00), 0.60, 0.45),
    "pedestal":    ((0.086, 0.478, 0.408, 1.00), 0.20, 0.40),  # ChargeReady green
    "cabinet":     ((0.310, 0.345, 0.396, 1.00), 0.45, 0.50),
    "transformer": ((0.502, 0.522, 0.545, 1.00), 0.55, 0.60),
    "stall":       ((0.180, 0.196, 0.220, 1.00), 0.00, 0.90),
    "stall_ada":   ((0.086, 0.353, 0.639, 1.00), 0.00, 0.85),
    "stall_future":((0.784, 0.639, 0.243, 0.45), 0.00, 0.80),  # pathway capacity
    "stripe":      ((0.933, 0.941, 0.949, 1.00), 0.00, 0.85),
}


@dataclass(frozen=True)
class Box:
    """An axis-aligned box in ENU metres, optionally yawed about +Z."""

    center: tuple[float, float, float]
    size: tuple[float, float, float]
    material: str
    yaw_deg: float = 0.0
    name: str = "part"

    def corners_enu(self) -> list[tuple[float, float, float]]:
        cx, cy, cz = self.center
        hx, hy, hz = (s / 2.0 for s in self.size)
        c, s = math.cos(math.radians(self.yaw_deg)), math.sin(math.radians(self.yaw_deg))
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    x, y, z = sx * hx, sy * hy, sz * hz
                    pts.append((cx + x * c - y * s, cy + x * s + y * c, cz + z))
        return pts

    @staticmethod
    def enu_to_gltf(p: tuple[float, float, float]) -> tuple[float, float, float]:
        """ENU (east, north, up) -> glTF (x=east, y=up, z=south)."""
        x, y, z = p
        return (x, z, -y)


@dataclass(frozen=True)
class SiteBuild:
    """The full proposed build for one site."""

    site_id: str
    ports_now: int
    ports_pathway: int
    boxes: list[Box]
    footprint_m: tuple[float, float]
    ada_stalls: int

    @property
    def part_count(self) -> int:
        return len(self.boxes)


def _stall_x_positions(n: int, width: float) -> list[float]:
    """Centre X for n stalls in a row, centred on the origin."""
    total = n * width
    return [-total / 2 + width * (i + 0.5) for i in range(n)]


def ada_stall_count(total_stalls: int) -> int:
    """ADA EV-stall provision, screening rule of thumb: at least one, and one
    per 25 stalls thereafter. Confirm against the AHJ's adopted accessibility
    code before using in design."""
    if total_stalls <= 0:
        return 0
    return max(1, math.ceil(total_stalls / 25))


def build_site(
    site_id: str,
    ports_now: int,
    ports_pathway: int | None = None,
    *,
    with_canopy: bool = True,
    with_transformer: bool = True,
) -> SiteBuild:
    """Compose the parametric massing for one candidate site.

    ports_now      energised ports recommended for immediate install
    ports_pathway  total pathway (future-ready) capacity; the difference is
                   drawn as translucent "reserved" stalls
    """
    ports_now = max(1, int(ports_now))
    ports_pathway = max(ports_now, int(ports_pathway if ports_pathway is not None else ports_now))
    future = ports_pathway - ports_now

    n_total = ports_pathway
    n_ada = ada_stall_count(n_total)
    boxes: list[Box] = []

    # stall widths: first n_ada stalls get the wider ADA footprint
    widths = [ADA_STALL_WIDTH if i < n_ada else STALL_WIDTH for i in range(n_total)]
    xs, cursor = [], -sum(widths) / 2.0
    for w in widths:
        xs.append(cursor + w / 2.0)
        cursor += w

    # --- stall pads ---
    for i, (x, w) in enumerate(zip(xs, widths)):
        if i >= ports_now:
            mat = "stall_future"
        elif i < n_ada:
            mat = "stall_ada"
        else:
            mat = "stall"
        boxes.append(
            Box(
                center=(x, 0.0, PAD_THICKNESS / 2),
                size=(w - 0.12, STALL_LENGTH, PAD_THICKNESS),
                material=mat,
                name=f"stall_{i:02d}",
            )
        )
        # wheel-stop stripe at the head of the stall
        boxes.append(
            Box(
                center=(x, STALL_LENGTH / 2 - 0.35, PAD_THICKNESS + 0.05),
                size=(w - 0.5, 0.14, 0.10),
                material="stripe",
                name=f"stripe_{i:02d}",
            )
        )

    # --- dispensers: one pedestal serves two adjacent stalls ---
    for i in range(0, n_total, 2):
        pair = xs[i : i + 2]
        px = sum(pair) / len(pair)
        energised = i < ports_now
        boxes.append(
            Box(
                center=(px, STALL_LENGTH / 2 + 0.55, PEDESTAL[2] / 2),
                size=PEDESTAL,
                material="pedestal" if energised else "stall_future",
                name=f"dispenser_{i // 2:02d}",
            )
        )

    span = sum(widths)

    # --- canopy + columns ---
    if with_canopy:
        cw = span + CANOPY_OVERHANG * 2
        cd = STALL_LENGTH + CANOPY_OVERHANG * 2
        boxes.append(
            Box(
                center=(0.0, 0.0, CANOPY_HEIGHT + CANOPY_THICKNESS / 2),
                size=(cw, cd, CANOPY_THICKNESS),
                material="canopy",
                name="canopy_deck",
            )
        )
        for sx in (-1, 1):
            for sy in (-1, 1):
                boxes.append(
                    Box(
                        center=(
                            sx * (cw / 2 - COLUMN_SIDE),
                            sy * (cd / 2 - COLUMN_SIDE),
                            CANOPY_HEIGHT / 2,
                        ),
                        size=(COLUMN_SIDE, COLUMN_SIDE, CANOPY_HEIGHT),
                        material="column",
                        name=f"column_{'w' if sx < 0 else 'e'}{'s' if sy < 0 else 'n'}",
                    )
                )
        # mid columns for long runs
        if span > 16:
            for x in (-span / 4, span / 4):
                for sy in (-1, 1):
                    boxes.append(
                        Box(
                            center=(x, sy * (cd / 2 - COLUMN_SIDE), CANOPY_HEIGHT / 2),
                            size=(COLUMN_SIDE, COLUMN_SIDE, CANOPY_HEIGHT),
                            material="column",
                            name=f"column_mid_{x:+.0f}_{sy:+d}",
                        )
                    )

    # --- power cabinet + transformer, set back behind the stall head ---
    equip_y = STALL_LENGTH / 2 + AISLE_CLEAR + 1.20
    boxes.append(
        Box(
            center=(span / 2 + 1.20, equip_y, CABINET[2] / 2),
            size=CABINET,
            material="cabinet",
            name="power_cabinet",
        )
    )
    if with_transformer:
        boxes.append(
            Box(
                center=(span / 2 + 3.40, equip_y, TRANSFORMER[2] / 2),
                size=TRANSFORMER,
                material="transformer",
                name="pad_transformer",
            )
        )
        boxes.append(
            Box(
                center=(span / 2 + 3.40, equip_y, PAD_THICKNESS / 2),
                size=(TRANSFORMER[0] + 1.5, TRANSFORMER[1] + 1.5, PAD_THICKNESS),
                material="stall",
                name="transformer_pad",
            )
        )

    footprint = (span + CANOPY_OVERHANG * 2 + 5.0, STALL_LENGTH + AISLE_CLEAR + 4.0)
    return SiteBuild(
        site_id=site_id,
        ports_now=ports_now,
        ports_pathway=ports_pathway,
        boxes=boxes,
        footprint_m=footprint,
        ada_stalls=n_ada,
    )
