# Canonical data contract v3

**The authoritative output.** Produced by a new model run (model version 3.1.0)
under DEC-027, 2026-10-18. v1 and v2 are frozen history and are never regenerated.

## Why it exists

The reference study's official future-ready (pathway) total is the one the canonical
`milestone2_v3` rules produce: **25 starter ports and a 47-port
pathway**. v1 and v2 hold **25 / 48**, the earlier `legacy_v2`
result: until DEC-027 the V3 plan kept the cohort-relative legacy ranking and the legacy
pathway rule so that 48 survived. A reviewer noted that the project published two
output versions without saying which one counts. This one counts; the others are history.

`legacy_v2` mode still reproduces 25 / 48 bit-exactly.

## What is different from v2

Same 60 fields, same order, same meaning, same validation rules. The values
differ only where the plan changed: the canonical plan follows the fixed-anchor ranking the
results show, and the pathway is the V3 rule (`right_sizing._future_ready` over the 2036/2046
V3 targets). Per site, against v2:

- `FFX001`: 2036 base active 4 to 2.
- `FFX003`: pathway 4 to 2 ports; 2036 high active 4 to 2; 2036 stress_combined active 4 to 2; 2046 base active 4 to 2; 2046 high active 4 to 2; 2046 stress_combined active 4 to 2; 2056 base active 4 to 2; 2056 high active 4 to 2; 2056 stress_combined active 4 to 2; plan text now "Lower current readiness suggests a small pilot or monitoring approach before larger investment.".
- `PWC001`: pathway 3 to 4 ports; 2036 high active 3 to 4; 2036 stress_combined active 3 to 4; 2046 base active 3 to 4; 2046 high active 3 to 4; 2046 stress_combined active 3 to 4; 2056 base active 3 to 4; 2056 high active 3 to 4; 2056 stress_combined active 3 to 4.
- `PWC006`: plan text now "Promising candidate; install starter ports and preserve room or conduit for about 4 future-ready ports.".
- `PWC007`: 2036 base active 4 to 2.

Energy and emissions do not depend on port counts and are unchanged. Outside the scenario
table, the one difference is typographic: `standards_register.csv` writes a hyphen where the
frozen v1 and v2 registers carry an em dash (the generator was corrected after v1 was frozen).

## Read with care

`lifecycle_cost_nominal_usd`, `lifecycle_cost_npv_usd` and `avoided_overbuild_cost_usd` keep
v1's meaning: each site's base-case staged trajectory only. The `high` and `stress_combined`
rows of a horizon repeat its `base` value; they are not the cost of those scenarios.

**Zero real observations.** Every `observed_*` field is empty and every row reports
`awaiting_observed_data`. An empty `observed_*` field means NOT OBSERVED. It never means zero.

## Provenance

Own hash chain in `contract_manifest.json`, same construction as v1 and v2. The manifest pins
the v1 and v2 manifest digests under `history`. Rebuild with
`python scripts/build_contract_v3.py`; check with `--check`; validate with
`python -m fcf_m2.workflow validate-contract data/contract/v3`.
