# V2 Deliverable Package — Clean Rebuild Checkpoint

## Status

The V2 deliverable package builder now removes the old package folder before rebuilding it by default.

## Updated file

```text
src/build_v2_deliverable_package.py
```

## Why this fix was needed

Before this fix, the package builder copied files into:

```text
data/outputs/deliverable_package_v2/
```

without clearing old copied files first. If a packaged file was later removed, renamed, or moved, an outdated file could remain in the package folder and make the package look cleaner than it really was.

## New behavior

By default, the builder now performs a clean rebuild:

```text
1. Check whether the package folder exists.
2. Confirm the folder is inside the safe data/outputs area.
3. Delete the previous package folder.
4. Recreate the package folder.
5. Copy the current V2 outputs into a fresh package.
6. Write a new README.md and package_manifest.json.
```

## Safety guard

The script refuses to clean a custom output path outside:

```text
data/outputs/
```

unless the user disables cleaning.

## Optional no-clean mode

A user can still preserve the existing package folder by running:

```bash
python src/build_v2_deliverable_package.py --no-clean
```

## New manifest fields

The package manifest now records:

```text
clean_rebuild
previous_package_removed
```

## Validation command

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected package output includes:

```text
Clean rebuild: True
Previous package removed: True
```

or `Previous package removed: False` if the package folder did not exist before the first clean build.
