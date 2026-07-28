# `tests/` — verification suite

[← repository root](../README.md)

The suite is run by `make test`; CI enforces a coverage floor of 80%.
*(This line previously stated a fixed test count. It went stale, so it now describes the
suite rather than counting it — the count lives in `docs/operations/v4-program/VERIFICATION.md`,
where it is a dated measurement.)*

| File | Covers |
|---|---|
| `test_legacy_golden.py` | Bit-exact reproduction of the accepted V2 baseline against frozen fixtures (`fixture_legacy_v2_*.csv`) — scores, ranks, ports, strategies, 25/48 totals |
| `test_scoring_and_queueing.py` | Normalization/anchor properties, Erlang-C behavior, port chooser, **cohort invariance** (a site's V3 score never changes when other sites are added/removed) |
| `test_modules.py` | Demand-calibration refusal logic, discrete-event simulation determinism/percentiles, typed confidence (note-text invariance), economics orderings (staged < overbuild at every horizon), emissions vintage rules, trigger policy incl. equity override |
| `test_contract_and_integration.py` | Full-workflow integration, contract rule/schema/hash-chain validation incl. deliberate-corruption failures, cross-model reconciliation, offline GIS with network disabled, chart footer QA, doc-drift check |

Run: `make test` (root) or `python -m pytest tests/ -q`.
The golden fixtures are the frozen outputs of the accepted V2 baseline run
(2026-07-19); do not regenerate them to make a failure disappear — a legacy-golden
failure means the model changed.
