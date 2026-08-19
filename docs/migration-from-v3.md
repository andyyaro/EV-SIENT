# Migrating from contract v1 to contract v2

[← docs index](README.md) · [previous migration: V1/V2 → V3](migration-from-v2.md)

**Short version: you probably do not have to do anything.**

Contract v2 is additive. Every one of v1's 48 fields is present in v2 with identical
semantics and - for the same run - identical values. A consumer written against v1 that
reads a v2 row gets the same answers. If your code reads columns by name and ignores ones it
does not recognise, it already works.

Two things changed, and one of them can bite. Both are below.

---

## Why v2 exists at all

v1 has exactly one field describing the observed world: `expansion_trigger_status`. It holds
`awaiting_observed_data` on all 120 rows, because when v1 was written there was no way to
observe anything.

Phase 4 built that way in. Once a utility can send a load study and a facility manager can
send a month of charger logs, the model produces information v1 has nowhere to put:

- the measured values behind a trigger decision, and the decision's own reasoning
- when and how a capacity value was confirmed, and whether two sources disagreed
- **why** a site's data confidence is what it is, not only what it is

Widening v1 in place was not an option - the whole point of a frozen contract is that
artifacts already quoting it keep meaning what they meant. So v2 is a superset, and v1 is
now immutable.

---

## What is different

### 1. `contract_version` is `2.0.0`

If you assert the major version (and the contract's own consumer rules say you should), you
will need to accept `2`. Assert on the major component, not the whole string.

### 2. `horizon_label` - `now` became `baseline` ⚠️

**This is the change that can break something.** If you filter, join, or switch on
`horizon_label == "now"`, that comparison silently matches nothing in v2 and your baseline
row quietly disappears. Nothing errors. You get an empty result or a chart missing its first
column.

```diff
- baseline = rows[rows.horizon_label == "now"]
+ baseline = rows[rows.horizon_label == "baseline"]
```

**Safer still:** filter on the year, which did not change and never will.

```python
baseline = rows[rows.horizon_year == 2026]
```

**Why bother changing it?** `now` is time-relative text frozen into a dated artifact. Read in
2036, a row labelled `now` is simply false - and "now" is the one horizon word this program
prohibits everywhere else. v1 keeps `now` forever, because v1 is frozen. That is exactly the
situation an immutable contract plus an additive successor exists to handle.

### 3. Twelve new columns

| Field | What it carries |
|---|---|
| `observed_months` | months of charger operating data behind the trigger decision |
| `observed_utilization` | measured average utilisation, 0–1 |
| `observed_uptime` | measured availability, 0–1 - the gate the policy checks first |
| `observed_p90_wait_min` | measured p90 wait, minutes |
| `observed_source_system` | which system reported it |
| `capacity_observed_date` | when the capacity value was confirmed |
| `capacity_method` | how it was established (utility record, panel schedule, walkthrough…) |
| `capacity_conflict` | text of any unresolved disagreement between sources |
| `data_confidence_reason` | **why** the confidence level is what it is |
| `trigger_outcome` | evaluated decision, with its policy status attached |
| `trigger_rule_trace` | the rules that produced that outcome, in order |
| `trigger_equity_override` | whether the equity override lowered the utilisation gate |

---

## The rule that matters most about those columns

> **An empty `observed_*` field means NOT OBSERVED. It never means zero.**

Do not `fillna(0)`. Do not default `observed_uptime` to `1.0` because "it was probably up".
A defaulted uptime of 1.0 walks straight past the reliability gate that exists to catch an
under-observed site, and a defaulted wait of 0 makes an unmeasured site look better than a
measured one.

In the CSV these are empty cells. In JSON they are `null`. In pandas they read back as
`NaN`. All three mean the same thing: nobody looked.

The contract enforces this rather than asking nicely. `validate_v2` refuses a table where a
row carries an observed value while reporting `awaiting_observed_data`, and refuses a
`verified_*` capacity basis with no `capacity_observed_date` - because verification with no
date is not verification.

---

## What is in v2 today

**Zero real observations.** Every `observed_*` field is empty. Every row reports
`awaiting_observed_data`. Capacity is `placeholder` at **all twelve sites**, exactly as
loudly as in v1.

That is the correct state, not an omission. The plumbing exists and is exercised by tests;
no facility manager or utility has sent anything yet. Nothing in v2 is more certain than
anything in v1 - it is the same numbers in a container that can hold more.

`model_version` in the v2 manifest is **`3.0.0`**, not `4.0.0`. The contract version and the
model version are separate facts: v2 is a container change, and the numbers inside it were
produced by the V3 model on rows that say `model_mode = milestone2_v3`. The model version
bumps when V4 is genuinely complete.

---

## Which version should I read?

| You are | Read |
|---|---|
| Quoting published Milestone 2 figures | **v1.** It is frozen; it will never move under you. |
| Building anything new | **v2.** Same numbers, room for the observed fields. |
| Consuming observed / trigger data | **v2.** v1 cannot express it. |
| MATLAB / Simulink harness | **v1** for now - the adapter still generates from v1. |

Both are tracked, both carry their own SHA-256 hash chain, and both are gated by
`scripts/verify.sh`.

---

## v1 is frozen - what that means in practice

`tests/test_contract_v2.py` pins the SHA-256 of `data/contract/v1/contract_manifest.json`.
Anything that regenerates or edits v1 fails that test.

If you hit it: **do not update the constant to match the new output.** That is precisely how
an immutable contract stops being immutable without anyone noticing. Either revert whatever
touched v1, or route the change into v2.

---

## Regenerating v2

```bash
python scripts/build_contract_v2.py           # write data/contract/v2/
python scripts/build_contract_v2.py --check   # verify the tracked copy is current
```

v2 is **derived from v1** by migration, and that is the design rather than a shortcut:
migration copies every v1 value across, so "additive" is guaranteed by construction - a v2
number drifting from its v1 counterpart is not something the code can express. The build
refuses to leave a non-additive v2 on disk, and `verify.sh` re-checks it on every run.

The single migration path lives in `src/fcf_m2/contract_v2.py`. `scripts/build_contract_v2.py`
and `fcf_m2.workflow` are both callers. Neither reimplements it.

---

## Validation

```bash
python -m fcf_m2.workflow validate-contract data/contract/v1
python -m fcf_m2.workflow validate-contract data/contract/v2
```

One command, version-aware. It reads the version from the artifact's manifest rather than a
flag, so a v2 directory cannot be checked under v1's weaker rules by getting an argument
wrong. v2 runs every v1 rule first and then its own.
