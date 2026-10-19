"""Small, checkable geometry on longitude and latitude. No projection library.

Distances are great-circle on a sphere of the mean Earth radius, the same formula the app uses
in the browser (platform/app/src/hub/compute.ts), so a radius means the same thing at build time
and at fill time. Distances to a boundary use a flat approximation around each point, which is
accurate to well under 1% at the few miles this needs.
"""

from __future__ import annotations

import math

import numpy as np

EARTH_RADIUS_MI = 3958.7613
MI_PER_DEGREE = EARTH_RADIUS_MI * math.pi / 180.0
METRES_PER_MILE = 1609.344


def haversine_mi(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles. Takes scalars or numpy arrays (broadcast)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_MI * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def simplify_ring(ring: np.ndarray, tolerance_m: float) -> np.ndarray:
    """Douglas-Peucker on one closed ring of (lon, lat), keeping its first and last point.

    Works in a flat frame around the ring's mean latitude. Iterative, so a ring of a few hundred
    thousand vertices does not hit the recursion limit.
    """
    if len(ring) <= 4:
        return ring
    lat0 = math.radians(float(np.mean(ring[:, 1])))
    xy = np.column_stack([ring[:, 0] * math.cos(lat0), ring[:, 1]]) * MI_PER_DEGREE * METRES_PER_MILE
    keep = np.zeros(len(ring), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    while stack:
        first, last = stack.pop()
        if last - first < 2:
            continue
        a, b = xy[first], xy[last]
        seg = xy[first + 1:last]
        ab = b - a
        length2 = float(ab @ ab)
        if length2 == 0.0:
            d = np.hypot(*(seg - a).T)
        else:
            t = np.clip(((seg - a) @ ab) / length2, 0.0, 1.0)
            d = np.hypot(*(seg - (a + np.outer(t, ab))).T)
        i = int(np.argmax(d))
        if d[i] > tolerance_m:
            k = first + 1 + i
            keep[k] = True
            stack.append((first, k))
            stack.append((k, last))
    return ring[keep]


def point_in_rings(lon: float, lat: float, rings: list[np.ndarray]) -> bool:
    """Even-odd rule over every ring, so islands count and holes do not."""
    inside = False
    for ring in rings:
        x, y = ring[:, 0], ring[:, 1]
        x2, y2 = np.roll(x, -1), np.roll(y, -1)
        crosses = (y > lat) != (y2 > lat)
        with np.errstate(divide="ignore", invalid="ignore"):
            xs = x + (lat - y) * (x2 - x) / (y2 - y)
        inside ^= bool(np.count_nonzero(crosses & (lon < xs)) % 2)
    return inside


def _segments(rings: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    starts = np.concatenate([r[:-1] for r in rings])
    ends = np.concatenate([r[1:] for r in rings])
    return starts, ends


def distance_to_rings_mi(lons: np.ndarray, lats: np.ndarray, rings: list[np.ndarray],
                         chunk: int = 256) -> np.ndarray:
    """Each point's distance in miles to the nearest edge of any ring."""
    starts, ends = _segments(rings)
    out = np.empty(len(lons))
    for i in range(0, len(lons), chunk):
        lo, la = lons[i:i + chunk, None], lats[i:i + chunk, None]
        k = np.cos(np.radians(la))
        ax, ay = (starts[:, 0] - lo) * k, starts[:, 1] - la
        bx, by = (ends[:, 0] - lo) * k, ends[:, 1] - la
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(length2 > 0, -(ax * dx + ay * dy) / length2, 0.0)
        t = np.clip(t, 0.0, 1.0)
        px, py = ax + t * dx, ay + t * dy
        out[i:i + chunk] = np.sqrt(np.min(px * px + py * py, axis=1)) * MI_PER_DEGREE
    return out


def nearest_index(lons: np.ndarray, lats: np.ndarray, to_lons: np.ndarray, to_lats: np.ndarray,
                  chunk: int = 64) -> np.ndarray:
    """For each point, the index of the nearest point in the second set (flat frame per point)."""
    out = np.empty(len(lons), dtype=np.int64)
    for i in range(0, len(lons), chunk):
        lo, la = lons[i:i + chunk, None], lats[i:i + chunk, None]
        dx = (to_lons[None, :] - lo) * np.cos(np.radians(la))
        dy = to_lats[None, :] - la
        out[i:i + chunk] = np.argmin(dx * dx + dy * dy, axis=1)
    return out
