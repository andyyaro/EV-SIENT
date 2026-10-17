# `data/intake/example/` - a worked example you can run

[← data/](../../README.md) · [the input guide](../../../docs/INPUT_SCHEMA.md)

`example_city_facilities.csv` is six **invented** sites in an "Example City" that does not
exist. No value in it describes a real building, and its coordinates were chosen to fall
nowhere near the reference study. It is written the way real files arrive, so that every
part of intake has something to do:

| Fault in the file | Where | What intake does |
|---|---|---|
| Spaced, capitalised column names (`Facility ID`, `Daily Visitors`) | every column | matched to the canonical names |
| Distances in metres (`Service Distance (m)`, `Trench Length (m)`) | two columns | multiplied by 3.28084, with a warning |
| Visit length in hours (`Dwell (hr)`) | one column | multiplied by 60, with a warning |
| `1,400` visitors and a `$45,000` cost | `EXC-01` | read as numbers, with a note |
| `n/a` staff and an `unknown` stormwater risk | `EXC-03` | left absent, with a note |
| A blank parking count | `EXC-04` | left absent; the port plan is capped at 2 |
| A garage marked `partial` | `EXC-05` | not yes or no, so left absent, with a warning |
| No amenities column at all | the whole file | the field is absent at every site, with a note |

Run it from the repository root:

```bash
python -m fcf_m2.workflow intake data/intake/example/example_city_facilities.csv \
    --out cohorts/example-city --accept --jurisdiction "Example City" \
    --source-date 2026-10-01 --source-org "Example City (invented)"
python -m fcf_m2.workflow run --cohort cohorts/example-city
```

What it should print, and what each result means, is in the
[worked example](../../../docs/INPUT_SCHEMA.md#worked-example).
`tests/test_input_schema.py` reruns it on every test run.
