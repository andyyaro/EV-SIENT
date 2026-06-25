# V2 README Visuals Refresh Checkpoint

## Status

The README visuals now point to V2-specific committed preview assets instead of older V1 visuals.

## Added preview assets

```text
docs/assets/charts/v2_readiness_preview.svg
docs/assets/charts/v2_site_map_preview.svg
docs/assets/charts/v2_profile_rank_stability_preview.svg
docs/assets/charts/v2_port_simulation_preview.svg
```

## Updated file

```text
README.md
```

## Why SVG previews were used

The full V2 chart outputs are generated locally under:

```text
data/outputs/charts/
```

Those generated outputs are ignored by Git. To make the GitHub README display V2 visuals consistently, the repo now includes lightweight committed SVG preview assets that summarize the current validated V2 results.

## README visual sections now shown

```text
V2 readiness ranking
V2 candidate site map
V2 rank stability across profiles
V2 port-use simulation and right-sizing validation
```

## Note

The SVG previews are README communication assets. The full generated V2 charts remain available locally after running:

```bash
python src/run_v2.py
```

For detailed review, use the generated charts in:

```text
data/outputs/charts/
data/outputs/deliverable_package_v2/charts/
```
