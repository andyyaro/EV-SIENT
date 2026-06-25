# V2 Enhancement — Right-Sizing Validation Checkpoint

## Status

The V2 workflow now validates right-sizing recommendations against the port-use simulation.

## Added or updated

```text
src/validate_right_sizing_with_simulation.py
src/run_v2.py
src/build_v2_executive_summary.py
src/check_outputs_v2.py
```

## New outputs

```text
data/outputs/v2_right_sizing_validation.csv
data/outputs/v2_right_sizing_validation_report.md
```

## New workflow step

```text
14. Validate V2 right-sizing with simulation
```

The executive summary is now step 15 and receives the validation file through:

```text
--right-sizing-validation data/outputs/v2_right_sizing_validation.csv
```

## New executive-summary fields

```text
current_alignment
future_alignment
simulation_supported_strategy
right_sizing_validation_note
```

## Purpose

This layer checks whether:

```text
ports_now agrees with simulated current-demand need
future_ready_capacity agrees with simulated 2050 high-growth need
the right-sizing strategy is aligned, conservative, or needs review
```

## Validation command

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```
