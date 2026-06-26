# Checkpoint and History Index

This folder is the navigation home for project checkpoint and history notes.

The checkpoint files currently remain in `docs/` to avoid breaking many internal links in one large move. Use this index to understand which files are active documentation and which files are history/checkpoints.

## Active docs to read first

These are the active review and reproduction docs:

```text
README.md
START_HERE.md
REPRODUCIBILITY_CHECKLIST.md
docs/REVIEWER_GUIDE.md
docs/V2_CURRENT_WORKFLOW_GUIDE.md
docs/REPO_MAP.md
src/README.md
docs/MAINTENANCE_CHECKLIST.md
docs/DATA_DICTIONARY.md
docs/PROJECT_STATUS.md
```

## Checkpoint file patterns

Most checkpoint or history files follow these patterns:

```text
docs/V2_*_CHECKPOINT.md
docs/V2_*_RESULTS.md
docs/V2_*_PENDING.md
docs/V1_TO_V2_FEATURE_PARITY_AUDIT.md
```

These files are useful for auditability and project memory, but they are not the first files a reviewer needs to read.

## Main checkpoint themes

```text
workflow checkpoints
baseline and package checkpoints
executive-summary enhancement checkpoints
port-simulation and right-sizing checkpoints
port-sizing scenario checkpoints
GIS/map and visual-cleanup checkpoints
V1-to-V2 parity checkpoints
public-data upgrade and batch checkpoints
```

## Moving policy

Do not move all checkpoint files at once.

When physically moving checkpoint files into this folder, move a small group at a time and immediately run:

```bash
make links
```

Also update links in:

```text
README.md
START_HERE.md
docs/README.md
docs/REPO_MAP.md
docs/REVIEWER_GUIDE.md
```
