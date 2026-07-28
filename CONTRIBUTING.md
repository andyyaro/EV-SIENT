# Contributing

## Setup, test, verify

```bash
make setup            # venv + editable install with pinned [test] extras (Python 3.11+)
make test             # full suite incl. legacy golden tests; reports coverage (the 80% floor
                      #   is enforced by ./scripts/verify.sh and CI, not by this target)
make run-legacy       # reproduce the accepted V2 baseline (25 starter / 48 pathway)
make run-v3           # full V3 run into data/outputs/v3_run/
make validate         # validate the tracked contract at data/contract/v1
./scripts/verify.sh   # every repository gate — must pass before you open a PR
```

Full command reference: [docs/operations/reproduction-guide.md](docs/operations/reproduction-guide.md).

## Claims discipline (non-negotiable)

This project's value rests on labeled uncertainty. Contributions must not
erode it:

- **Never present placeholder capacity as verified.** `capacity_basis` is
  `placeholder` at all 12 sites; any output showing capacity must carry that
  label until utility/facility verification upgrades it.
- **Never fabricate client, AHJ, utility, or funding outcomes.** The
  human-action packages in `docs/human-actions/` are instruments for events
  that have not happened; blank fields stay blank until the real event is
  documented.
- **Keep the "0 of 12 sites High confidence" finding visible.** Do not bury,
  reword, or soften it in any README, report, visual, or caption.
- **Screening values are not budgets.** Costs are screening-class net present
  cost; never present them as budgets, bids, or forecasts.
- MATLAB has been executed on licensed MathWorks R2025b Update 5 (**49 passed / 0 failed**)
  against a **synthetic fixture only**. No MATLAB output describes a real facility, and the
  Simulink model was **built, never simulated** — do not claim more than
  `matlab/EXECUTION_STATUS.md` records.

## Golden-test rule

The legacy fixtures under `tests/` are **frozen**. They encode the accepted
V2 baseline (FFX002 58.8; 25/48 port totals). A golden-test failure means
the model changed — investigate it. **Do not regenerate goldens to silence a
failure.** A deliberate re-baselining requires a documented migration note
and reviewer sign-off, never a quiet fixture update.

## Pull requests

Use the checklist in
[.github/pull_request_template.md](.github/pull_request_template.md): state
the results impact of any change, confirm `make test`, `./scripts/verify.sh`,
and `make validate` pass, and check off the claims-discipline items. Data
updates must state source, date, and provenance class.
