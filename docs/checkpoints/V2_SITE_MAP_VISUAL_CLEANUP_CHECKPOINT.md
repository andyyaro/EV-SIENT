# V2 Site Map Visual Cleanup Checkpoint

## Status

The V2 site-readiness map script has been cleaned up to produce a more presentation-ready visual.

## Updated file

```text
src/plot_site_map.py
```

## What changed

The map still keeps the same analytical structure:

```text
overview panel
Fairfax-area zoom panel
Prince William County zoom panel
recommendation-tier legend
readiness-score colorbar
```

But the visual is now less crowded.

## Cleanup details

```text
Removed floating cluster labels from the overview panel.
Reduced overview labels to the top three sites plus key special-case sites.
Kept detailed labels in the regional zoom panels.
Changed point labels to a compact one-line format: rank, site ID, score.
Replaced the dense all-12 ranked text block with a compact key-takeaways panel.
Shortened the subtitle.
Shortened the footer disclaimer.
Reduced marker and label clutter while keeping tier, score, and top-site encodings.
```

## Overview labeling rule

The overview panel now labels:

```text
top 3 ranked sites
PWC002 high-review garage candidate
PWC003 special-use / public-access decision site
PWC008 nearby-supply monitor site
```

The zoom panels still label all regional sites.

## Validation command

After pulling this update, regenerate the map through the full workflow:

```bash
make run-v2
make check-v2
```

Or regenerate only the map after V2 outputs already exist:

```bash
python src/plot_site_map.py \
  --input data/inputs/real_sites_v2.csv \
  --results data/outputs/v2_site_results.csv \
  --sensitivity data/outputs/v2_sensitivity_summary.csv \
  --profile-results data/outputs/v2_profile_results.csv \
  --output data/outputs/charts/v2_site_readiness_map.png
```

## README refresh note

The README uses a copied chart asset. After regenerating the map, refresh the README image with:

```bash
cp data/outputs/charts/v2_site_readiness_map.png docs/assets/charts/v2_site_readiness_map.png
```

Then commit the refreshed PNG only if the new visual looks good.
