# V2 Enhancement — Port Simulation Executive Integration Checkpoint

## Status

The V2 port-simulation results are now integrated into the main executive site summary table.

## Updated files

```text
src/build_v2_executive_summary.py
src/run_v2.py
src/check_outputs_v2.py
```

## Executive summary input change

`src/build_v2_executive_summary.py` now accepts:

```text
--port-simulation data/outputs/v2_port_utilization_simulation.csv
```

## Added executive summary columns

```text
sim_min_ports_current
sim_utilization_current_at_ports_now
sim_wait_current_at_ports_now
sim_queue_risk_current_at_ports_now
sim_min_ports_2035_high
sim_min_ports_2050_high
sim_status_2050_high_at_future_ready
```

## Workflow change

`src/run_v2.py` now passes the port-simulation CSV into the executive summary builder.

The relevant sequence is:

```text
13. Run V2 port-use simulation
14. Build V2 executive site summary
```

## Checker change

`src/check_outputs_v2.py` now checks that the executive CSV contains the new simulation-backed columns.

## Validation command

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

After validation, open:

```text
data/outputs/v2_executive_site_summary.csv
```

The main decision table should now include the port simulation summary fields.
