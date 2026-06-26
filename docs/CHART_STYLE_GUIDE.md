# Chart Style Guide

## Font

All generated Matplotlib charts are configured to use:

```text
Libre Caslon Condensed
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

The chart style first tries to register local Libre Caslon Condensed font files from these locations:

```text
fonts/
assets/fonts/
docs/assets/fonts/
data/fonts/
```

It also checks common operating-system font folders such as:

```text
~/Library/Fonts
/Library/Fonts
~/.local/share/fonts
/usr/local/share/fonts
/usr/share/fonts
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

The generated charts should now render with Libre Caslon Condensed when the font is available on the local machine.
