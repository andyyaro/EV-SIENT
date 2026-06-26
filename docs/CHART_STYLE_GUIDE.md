# Chart Style Guide

## Font

All generated Matplotlib charts are configured to use **Times New Roman** so the V2 visual outputs have one consistent report-style typography.

Fallback order:

```text
Times New Roman
Times
Nimbus Roman
Liberation Serif
DejaVu Serif
```

The shared style lives in:

```text
src/chart_style.py
src/sitecustomize.py
sitecustomize.py
```

The chart style is applied automatically when repository scripts are run from the project, including:

```bash
python src/run_v2.py
python src/plot_readiness_score_chart.py
python src/plot_site_decision_map_all_labels.py
```

## Diagnostic check

Use this command to confirm which font Matplotlib selected:

```bash
python src/check_chart_font.py
```

Expected output on macOS is usually:

```text
Selected chart font: Times New Roman
```

If Times New Roman is not visible to Matplotlib, the workflow falls back to the next available serif font in the fallback list.

## Regenerating charts

After changing the style, regenerate the outputs:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

The generated chart files and deliverable package copies should then use the same Times New Roman chart style.

## Basemap note

Text that is part of the map background tiles cannot be restyled by Matplotlib. Generated chart text, labels, legends, axes, titles, and dashboard text can be controlled by the project font style.
