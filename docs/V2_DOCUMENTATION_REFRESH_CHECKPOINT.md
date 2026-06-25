# V2 Documentation Refresh Checkpoint

## Status

The repo documentation has been refreshed so the current V2 workflow has one clear landing page and the main repo guides point to it.

## New file

```text
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

## Updated files

```text
START_HERE.md
README.md
REPRODUCIBILITY_CHECKLIST.md
docs/REPO_MAP.md
data/outputs/README.md
docs/PROJECT_STATUS.md
```

## Purpose

The documentation now reflects the active V2 workflow instead of only describing the older stable V1 workflow.

The updated docs explain:

```text
which branch to use
how to run V2
what the 20 V2 workflow steps do
where the deliverable package is written
which files to open first
what the checker validates
what the current V2 candidate set is
what assumptions still need confirmation
how V1 differs from V2
```

## Main V2 command

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

## Expected success sign

```text
V2 OUTPUT CHECK
Status: PASSED
All expected V2 outputs are present and all 12 V2 candidate sites are represented in the main output tables.
```

## Documentation reading path

```text
1. docs/V2_CURRENT_WORKFLOW_GUIDE.md
2. START_HERE.md
3. README.md
4. REPRODUCIBILITY_CHECKLIST.md
5. docs/REPO_MAP.md
6. docs/PROJECT_STATUS.md
```

## Notes

Generated V2 outputs are still local-only and ignored by Git. The documentation points to generated paths, but those files are created only after running the workflow locally.
