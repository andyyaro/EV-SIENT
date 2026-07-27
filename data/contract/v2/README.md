# Canonical data contract v2

**Additive over v1. v1 is frozen and is never regenerated.**

Every one of v1's 48 fields appears here with identical
semantics and identical values for the same run, so a consumer written against v1 reads a v2
row and gets the same answers. v2 adds 12 fields carrying what the V4
field-data loop produces — information v1 had nowhere to put, because when v1 was written
there was no way to observe anything.

## What v2 adds

| Field | What it carries |
|---|---|
| `observed_months` | months of charger operating data behind the trigger decision |
| `observed_utilization` | measured average utilisation, 0-1; empty when unobserved |
| `observed_uptime` | measured availability, 0-1; the gate the policy checks first |
| `observed_p90_wait_min` | measured p90 wait, minutes; empty when unobserved |
| `observed_source_system` | which system reported it, for provenance |
| `capacity_observed_date` | when the capacity value was confirmed; empty while placeholder |
| `capacity_method` | how it was established (utility record, panel schedule, walkthrough...) |
| `capacity_conflict` | text of any unresolved disagreement between sources; empty when none |
| `data_confidence_reason` | why the confidence level is what it is, not merely what it is |
| `trigger_outcome` | evaluated decision: expand_review_recommended | hold | awaiting_observed_data |
| `trigger_rule_trace` | the rules that produced that outcome, in order |
| `trigger_equity_override` | whether the equity override lowered the utilisation gate |

## The one correction

`horizon_label` used `now` for the baseline year. v2 uses `baseline`. `now` is
time-relative text frozen into a dated artifact: read a year later it is simply false, and it
is the one horizon word this program names as prohibited. **v1 keeps `now` forever**, because
v1 is frozen — which is precisely the situation an immutable contract plus an additive
successor exists to handle.

## What is in it today

**Zero real observations.** Every `observed_*` field is empty and every row reports
`awaiting_observed_data`. That is the correct state until a facility manager or the utility
sends something. A site whose capacity is a placeholder still says `placeholder`, exactly as
loudly as in v1.

**An empty `observed_*` field means NOT OBSERVED. It never means zero.** A defaulted uptime
of 1.0 would walk straight past the reliability gate that exists to catch exactly that.

## Rules enforced by validation, not merely stated

1. `contract_version` is `2.0.0` on every row.
2. The retired `now` vocabulary may not appear.
3. A row reporting `awaiting_observed_data` may not carry an observed value — that would be
   a number with no observation behind it.
4. A `verified_*` capacity basis must name the date it was verified. Verification with no
   date is not verification.
5. Every v1 rule still applies, because `validate_v2` runs them first.

## Provenance

Own hash chain in `contract_manifest.json`, same construction as v1: SHA-256 over every
table plus every hashed input. Verify with `fcf_m2.contract.verify_hash_chain`.
