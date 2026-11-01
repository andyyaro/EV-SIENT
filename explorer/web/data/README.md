# Explorer site data

`build_sites.py` (`src/fcf3d/`) writes the explorer's site data here: `sites.json`,
`sites.geojson` and `sites.inline.js`. They are built from the study's private inputs, and each
site's score breakdown shows every input's raw value, so this public copy does not carry them
(DEC-016, DEC-031). `manifest.json` is kept.

To build them, copy the private inputs and the two result fixtures into `data/inputs/` and
`tests/`, then run `make explorer` (or `python -m fcf3d.build_sites --repo . --mode
milestone2_v3 --out explorer/web/data`). `.gitignore` keeps the results out of commits.
