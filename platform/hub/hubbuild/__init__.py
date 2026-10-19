"""Builds the EV-SIENT public data hub: per-county Parquet packs from pinned public vintages.

See platform/hub/README.md. Nothing here reads the planner's data or the reference study's
inputs (DEC-016): every input is a public file named in platform/hub/sources.json.
"""

#: Bumped when the pack layout or a method changes, so a build_id never names two different
#: computations of the same inputs.
BUILDER_VERSION = "1"
