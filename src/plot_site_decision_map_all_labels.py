"""Run the V2 GIS decision-map generator with all 12 sites labeled on the report map.

This wrapper keeps the README map less crowded while forcing the full report map
to label every candidate site.
"""

from __future__ import annotations

import plot_site_decision_map as base

base.MAIN_LABEL_SITE_IDS = {
    "FFX001", "FFX002", "FFX003", "FFX004",
    "PWC001", "PWC002", "PWC003", "PWC004",
    "PWC005", "PWC006", "PWC007", "PWC008",
}

base.LABEL_OFFSETS.update({
    "FFX001": (-84, -14),
    "FFX002": (12, 12),
    "FFX003": (14, -10),
    "FFX004": (-82, 18),
    "PWC001": (-84, 28),
    "PWC002": (-92, 14),
    "PWC003": (12, -26),
    "PWC004": (16, 20),
    "PWC005": (12, 18),
    "PWC006": (-84, -12),
    "PWC007": (18, 18),
    "PWC008": (14, -20),
})


if __name__ == "__main__":
    base.main()
