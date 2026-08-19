# Data Dictionary - `data/canonical/matlab_scenarios.csv`

Producer: Python V3 `fcf_m2.matlab_adapter` (canonical contract 1.0.0, run
`milestone2_v3_20260719T052322Z`). 120 rows = 12 sites x {2026 baseline;
2036/2046/2056 x base/high/stress_combined}. **Do not hand-edit; regenerate
via `make run-v3` at the repository root** (writes repo-root
`data/outputs/v3_run/matlab_scenarios.csv`; copy it here - see the README
"Regeneration instructions").

Consumer rules inherited from the data contract v1: join on `site_id` only;
propagate the placeholder label whenever `capacity_basis` is not
`verified_utility`/`verified_facility`; cite contract version + generation
stamp when presenting numbers.

MATLAB note: the CSV column `case` is a MATLAB keyword; `loadScenarios`
exposes it as table variable **`case_label`**.

| Column | Type | Unit | Allowed values / range | Provenance | Notes |
|---|---|---|---|---|---|
| `scenario_id` | string | - | `<site_id>_<horizon>_<case>`, unique | adapter-composed | Primary key of the row |
| `site_id` | string | - | `FFX001..FFX004`, `PWC001..PWC008` | canonical `site_table.csv` | **The only join key.** Never join on names |
| `site_name` | string | - | one canonical spelling per site | canonical `site_table.csv` | Display only |
| `horizon_year` | integer | year | present in data: 2026, 2036, 2046, 2056; any future year row is valid (ML-06) | canonical scenario table | Never hard-code the set; read from data |
| `case` (-> `case_label`) | string | - | `baseline` (2026 only), `base`, `high`, `stress_combined` | canonical scenario table | Demand-case label from the Python model |
| `ports` | integer | count | >= 0 | Python right-sizing model (rank/case-matched) | Recommended charging ports for this scenario |
| `charger_power_kW` | double | kW | > 0 (currently 19.2 on all rows) | planning assumption (Level-2 dual-port class) | Grid-side per-port rating |
| `spare_capacity_kW` | double | kW | **empty on all rows** (else >= 0) | unconfirmed - V2 upload value was rejected as placeholder | Empty by design until facility data lands; empty -> capacity may be undefined |
| `service_capacity_kW` | double | kW | **empty on all rows** (else > 0) | pending utility/facility confirmation | Preferred capacity definition when present |
| `capacity_basis` | string | - | `verified_utility`, `verified_facility`, `engineering_estimate`, `planning_proxy`, `placeholder`, `unknown` (controlled vocabulary, `capacityGuard.m`) | adapter; currently `placeholder` on ALL 120 rows | **Machine-readable provenance gate.** Non-verified => mandatory banner, no feasibility claims |
| `capacity_source` | string | - | free text | adapter | Human-readable provenance for `capacity_basis` |
| `base_load_mean_kW` | double | kW | >= 0 | legacy adapter estimate (constant across horizons - H15) | Daily mean building load; label year-comparisons accordingly |
| `base_load_peak_kW` | double | kW | >= `base_load_mean_kW` | legacy adapter estimate | Daily peak building load |
| `arrival_start_hr` | double | hour (0-24) | < `arrival_end_hr` | Python model site-use profile | Start of the EV arrival window |
| `arrival_end_hr` | double | hour (0-24) | > `arrival_start_hr` | Python model site-use profile | End of the EV arrival window |
| `dwell_hr` | double | hours | > 0 | Python model site-use profile | Vehicle dwell; **consumed** by the session model (legacy H1 fixed) |
| `sessions_per_day` | double | sessions/day | >= 0; fractional allowed (expected value) | Python demand model per horizon/case | Drives session generation; conserved exactly in deterministic mode |
| `energy_per_session_kWh` | double | kWh (battery-side) | >= 0 | Python demand model | Grid-side energy = value / charger efficiency |
| `managed_charging_policy` | string | - | currently `none`; reserved: strategy names of `managedCharging.m` | adapter | Placeholder for a per-site policy assignment; V3 runs all applicable strategies regardless |
| `model_rank` | integer | rank | >= 1 | Python site-ranking model | Portfolio priority rank of the site |
| `electrical_risk_level` | string | - | present in data: `medium`, `high` (vocab may extend: `low`) | Python electrical-risk screen | Qualitative screen, not a measurement |
| `source_note` | string | - | free text | adapter | Carries contract version, run id, and the placeholder-capacity warning; keep with any exported row |

## Empty-value semantics

Empty numeric cells import as `NaN` in MATLAB. `capacityGuard` treats
`NaN` service/spare capacity as "capacity undefined": capacity-limited
strategies refuse to run unless an explicit `AssumedSiteCapacity_kW`
planning assumption is supplied, and that assumption is itself labeled as
placeholder-grade.

## Validation applied on load (`loadScenarios.m`)

- All columns above are required; missing column => error.
- `capacity_basis` non-empty on every row => else error (fail-closed).
- `ports >= 0`, `charger_power_kW > 0`, `dwell_hr > 0`,
  `sessions_per_day >= 0`, `energy_per_session_kWh >= 0`,
  `arrival_end_hr > arrival_start_hr`.
