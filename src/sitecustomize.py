"""Automatically apply shared chart styling for repository scripts.

Python imports this module automatically when scripts are run as
`python src/<script>.py`, which is how the V2 workflow executes chart builders.
"""

from __future__ import annotations

try:
    from chart_style import apply_chart_style

    apply_chart_style()
except Exception:
    # Plot scripts should still run even if optional local fonts are unavailable.
    pass
