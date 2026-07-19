## Summary

<!-- What does this change do, in one or two sentences? -->

## Type of change

- [ ] Model/code change (may alter results — describe below)
- [ ] Data update (state source, date, and provenance class)
- [ ] Documentation
- [ ] CI / tooling

## Results impact

<!-- If any number a reviewer might quote changes, say which and why.
     Legacy baseline (25 starter / 48 pathway, FFX002 58.8) must remain
     reproducible in legacy_v2 mode unless a deliberate re-baselining is
     documented in a migration note. -->

## Verification

- [ ] `make test` passes locally
- [ ] `./scripts/verify.sh` passes locally
- [ ] Contract still validates (`make validate`) if data changed

## Claims discipline

- [ ] No placeholder capacity presented as verified
- [ ] No screening estimate presented as a budget/forecast
- [ ] No client/AHJ/utility approval implied that has not occurred
