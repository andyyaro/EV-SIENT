"""Repository-wide Python startup hook for chart styling.

When commands are run from the repository root, Python imports this file during
startup. That makes the Libre Caslon Matplotlib style available before chart
scripts import pyplot.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    SRC_DIR = Path(__file__).resolve().parent / "src"
    if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from chart_style import apply_chart_style

    apply_chart_style()
except Exception:
    # Never block normal script execution because of optional local font setup.
    pass
