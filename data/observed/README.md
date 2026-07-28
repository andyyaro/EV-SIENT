# `data/observed/` — field observations

**This directory contains ZERO real observations, and that is the correct state.**

Nothing here describes any real facility. It holds two templates and, under
`fixtures/`, clearly-marked synthetic data used to exercise the ingestion path in tests.
Until a facility manager or the utility actually sends something, that is what belongs
here — the V4 work ships the *pipeline*, never invented data.

## Why this directory matters

The project's largest limitation is that electrical capacity is a **placeholder at 12 of
12 sites**, and **0 of 12 reach High data confidence**. Everything downstream inherits it.
This is the path that closes it: real observations enter here, the model **re-runs**, and
`capacity_basis` moves off `placeholder` with provenance attached.

## The two files

| File | What it records | Who fills it |
|---|---|---|
| `observed_capacity_template.csv` | one confirmation of a site's electrical service | facility manager, or the utility |
| `observed_sessions_template.csv` | one site-day of charger operation | the charging network's export |

Both templates carry a single `EXAMPLE001` row that is **illustrative only**. Delete it
before entering real data; `EXAMPLE001` is not a project site id.

## Why the session template has more columns than it used to

It shipped with six: site, date, sessions, energy, mean dwell, visitors. The expansion
trigger policy in `data/contract/v1/assumptions.json` gates on **average utilisation, p90
wait, uptime and equity percentile** — and `triggers.evaluate` checks **uptime first**,
refusing to trust utilisation until reliability clears.

Of those four, utilisation was only derivable by joining in port counts and open hours,
p90 wait needs per-session timing rather than a daily dwell mean, and **uptime had no
corresponding field at all**. The one metric the policy consults first was the one the
template could not supply, so the loop it exists to feed could not have been closed.

The added columns are all things a networked EVSE actually reports:

- `ports_in_service` — how many ports existed that day
- `port_hours_available` / `port_hours_possible` — availability, which gives **uptime**
- `sessions_delayed`, `wait_p90_min` — queueing, which gives **p90 wait**
- `observer`, `source_system` — provenance, because an unattributed number cannot upgrade anything

## Rules that are enforced, not merely stated

1. **Nothing is hand-edited into the contract.** Observations enter here, the model re-runs,
   and a new `run_id` is generated. Scenario rows are never edited in place.
2. **Provenance or nothing.** An observation with no `source_document` and no `observer` is
   *refused at ingestion*, because it could not establish the provenance a non-placeholder
   value requires.
3. **Evidence caps the claim.** A walkthrough can justify `verified_facility`; only a
   utility record justifies `verified_utility`. An assumed value can never upgrade
   provenance — it can only sit alongside unverified data.
4. **Conflicts are surfaced, not resolved.** Where facility and utility values disagree,
   both are kept in `capacity_source`, the **more conservative** value is used for
   screening, and the conflict is flagged for a human.
5. **Missing metrics stay missing.** Where a trigger input cannot be derived it is left
   `None` and named, never defaulted. A defaulted uptime of 1.0 would walk straight past
   the reliability gate that exists to catch exactly that.
6. **Partial receipt yields partial upgrade.** `data_confidence` may rise only for the
   specific fields verified. The "0 of 12 High confidence" statement changes only when the
   underlying rows do.

See `docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md` for the upgrade
path per field, and `src/fcf_m2/observed.py` for the implementation.
