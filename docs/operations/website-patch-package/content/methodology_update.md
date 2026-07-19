## V3 methodology (July 2026 update)

The model now runs in two permanent modes:

- **`legacy_v2` (accepted baseline):** the reviewed V2 workflow, reproduced bit-for-bit
  (12 sites; FFX002 top at 58.8; 25 starter / 48 pathway ports; 38 REVIEW + 12 INFO data
  findings; 0 High-confidence sites).
- **`milestone2_v3`:** the same evidence base extended with (1) canonical 10/20/30-year
  horizons — 2036/2046/2056 from a 2026 baseline; (2) cohort-independent fixed-anchor
  scoring (versioned anchor set, migration report published); (3) typed field-level data
  confidence — wording changes can no longer move confidence scores; (4) peak-window and
  discrete-event wait modeling with P10/P50/P90 bands; (5) a lifecycle-cost layer
  (net present cost, staged vs broad vs defer); (6) a net-CO2e layer with sourced grid
  factor; (7) one canonical cross-model data contract consumed by every downstream
  artifact (Excel, MATLAB, Tableau, this site).

**Demand remains synthetic and uncalibrated** (`demand_model_status = synthetic_uncalibrated`).
The V3 code includes an observed-data import format and a calibration routine that refuses
to label itself calibrated without sufficient data and acceptable holdout error; it will be
exercised when pilot monitoring data exist.

Growth multipliers (2036: 1.9×/2.6×; 2046: 3.0×/4.5×; 2056: 4.0×/6.0× with pathway
saturation) are **provisional planning conventions pending calibration**, adopted for
horizon consistency across all artifacts.
