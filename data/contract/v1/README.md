# Canonical Cross-Model Data Contract v1

Producer: `fcf_m2` (Python V3). Consumers: MATLAB/Simulink V3, Excel workbook, Tableau exports, static visuals, presentation.

## Files
| File | Purpose |
|---|---|
| `schema.json` | JSON Schema for scenario_table rows |
| `scenario_table.csv` | site x horizon (2026/2036/2046/2056) x case (baseline/base/high/stress_combined) |
| `site_table.csv` | identity dimension - one canonical spelling per site; join on `site_id` only |
| `source_provenance.csv` | field-level provenance (typed source classes) |
| `standards_register.csv` | standards applicability per site/stage |
| `assumptions.json` | every labeled assumption with provenance |
| `contract_manifest.json` | version, input/table SHA-256 hashes, generation stamp |

## Consumer rules
1. Join on `site_id` only — never on names.
2. `capacity_basis` is machine-readable placeholder-vs-verified provenance: any consumer using capacity MUST propagate the placeholder label when basis is not `verified_utility`/`verified_facility`.
3. Presentation numbers cite `contract_version` + `generated_utc` from the manifest.
4. Validation: `python -m fcf_m2.workflow validate-contract <dir>` re-runs all rules and the RT-10 hash chain.

All values are planning-support outputs. Nothing here is an engineering, permitting, budget, or procurement value.
