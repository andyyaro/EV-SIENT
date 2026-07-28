# Synthetic site inputs — invented data, for public distribution

**No file here describes any real building.** No site id, name, address, postcode or
coordinate; no per-site measurement; no rank order, spacing or correlation structure;
no row-to-row correspondence with the real study. Every facility-scale number is drawn
from generic stated assumptions about what a public library or county office is like,
written down in `scripts/build_synthetic_inputs.py` where they can be argued with.

**What IS shared with the real files, deliberately, none of it distinguishing a
facility:** the schema vocabularies (the model cannot parse a file that uses others);
boolean and small-integer domains (0/1 flags, ranks 1..12 — arithmetic, not leakage);
the study's uniform conventions such as 480 V service and $150/ft trenching, which are
identical across all twelve real rows *because they are assumptions the study adopted*,
so each separates no site from any other; and the electrical placeholders
(`elec_service_rating_amp = 0`, `spare_capacity_kw = 0`), which must be preserved or
the fail-closed capacity guard would stop firing.

It exists because DEC-016 requires a public installer to ship synthetic inputs
rather than the twelve real facilities' data, and `workflow.py` cannot run without
*some* site table.

## What is NOT randomised, and why

- `elec_service_rating_amp = 0` and `spare_capacity_kw = 0` are kept as placeholders.
  They are what makes `capacity_basis` come out `placeholder` at every site. A
  fixture that invented electrical capacity would make the synthetic run **more
  confident** than the real one — the one direction a fixture must never move.
- The study's uniform conventions (480 V, $150/ft trenching, the safety-review
  flags) are the same for every real row because they are assumptions, not
  measurements.

## Honesty markers

Site ids are `SYN001`–`SYN012`. The county does not exist. The coordinate grid is
not Northern Virginia, so a site map drawn from this data cannot be mistaken for the
real candidates. Every field group is recorded with `source_class = synthetic`, so a
reader who follows any number to its provenance is told it was invented.

Regenerate with `python scripts/build_synthetic_inputs.py` (seeded, reproducible).
