# V2 Enhancement — Port Simulation Checkpoint

## Status

The V2 port simulation enhancement is now wired into the main V2 workflow and output checker.

## Added or updated

```text
src/run_port_utilization_simulation.py
src/run_v2.py
src/check_outputs_v2.py
```

## New outputs

```text
data/outputs/v2_port_utilization_simulation.csv
data/outputs/v2_port_utilization_simulation_report.md
data/outputs/charts/v2_port_utilization_simulation.png
```

## New workflow step

```text
13. Run V2 port-use simulation
```

## What it tests

The simulation compares multiple charging-port counts against current, 2035, and 2050 demand cases. It reports utilization, wait-time screening, queue risk, and capacity status.

## Validation command

```bash
make run-v2
make check-v2
```

The checker now expects the port simulation CSV, report, and chart.
