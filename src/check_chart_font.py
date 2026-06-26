"""Print the font family Matplotlib will use for generated charts."""

from __future__ import annotations

import matplotlib as mpl

from chart_style import apply_chart_style, available_chart_fonts

selected = apply_chart_style()
print("CHART FONT CHECK")
print("----------------")
print(f"Selected chart font: {selected}")
print(f"Matplotlib font.family: {mpl.rcParams.get('font.family')}")
print("Visible preferred chart fonts:")
fonts = available_chart_fonts()
if fonts:
    for font in fonts:
        print(f"- {font}")
else:
    print("- none found")
