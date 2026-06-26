# Chart Style Guide

## Font

All generated Matplotlib charts are configured to use the Libre Caslon family, with this priority order:

```text
Libre Caslon Text
Libre Caslon Display
Libre Caslon
Georgia
Times New Roman
DejaVu Serif
```

The shared style lives in:

```text
src/chart_style.py
src/sitecustomize.py
```

`src/sitecustomize.py` is loaded automatically when repository scripts are run with commands such as:

```bash
python src/run_v2.py
python src/plot_readiness_score_chart.py
python src/plot_site_decision_map_all_labels.py
```

## How the font is found

The chart style registers local font files matching:

```text
*Libre*Caslon*.otf
*Libre*Caslon*.ttf
LibreCaslon*.otf
LibreCaslon*.ttf
```

It checks these local project folders first:

```text
fonts/
assets/fonts/
docs/assets/fonts/
data/fonts/
```

It also checks common operating-system font folders, including the default user font folder on macOS:

```text
~/Library/Fonts
/Library/Fonts
/System/Library/Fonts
~/.local/share/fonts
/usr/local/share/fonts
/usr/share/fonts
```

For Andy's Mac, fonts stored here should be found automatically:

```text
/Users/andyyaro/Library/Fonts
```

You can also point the workflow to a custom local font folder:

```bash
export FCF_FONT_DIRS="$HOME/Library/Fonts"
python src/run_v2.py
```

Multiple folders can be separated with the normal OS path separator.

## Repository rule

Font files are local-only and should not be committed to the repository. The `.gitignore` file ignores local font folders and `.otf` / `.ttf` files.

## Validation

After installing or placing the font locally, regenerate the outputs:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

The generated charts should now render with Libre Caslon when the font is available on the local machine.
