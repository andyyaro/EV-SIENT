# V1 Demo Scalability Freeze Notes

## Purpose

These notes explain the final changes made after the original `v1-review-ready` checkpoint and before the planned `v1-demo-scalability-ready` checkpoint.

The original V1 reviewer-ready tag preserved the official six-site model package.

This later checkpoint keeps the same official V1 planning result, but adds better scalability testing, demo-mode documentation, and repo-quality cleanup.

## Relationship to the original V1 tag

```text
v1-review-ready
  Original six-site V1 reviewer-ready checkpoint.

v1-demo-scalability-ready
  Planned follow-up checkpoint with synthetic demo-mode scalability testing and audit fixes.
```

The new checkpoint should not replace the meaning of `v1-review-ready`. It is an improved development checkpoint that makes the repo easier to test, review, and extend.

## What changed after `v1-review-ready`

```text
Synthetic demo mode was added for larger candidate pools.
A deterministic demo-site generator was added.
The demo workflow now evaluates 25, 50, or 100 synthetic sites without changing the official V1 dataset.
Scalable visualizations were added for larger result sets.
A Top-N readiness chart was added for readable ranking review.
A Top-N data-confidence chart was added for readable confidence review.
A multi-panel scalable readiness map was added.
A Top-N profile heatmap was added.
A top-8 rank-stability chart was added to avoid crowded profile-line visuals.
Readiness score distribution and recommendation-tier count visuals were added.
Demo sensitivity analysis was added.
Demo scoring-profile analysis was added.
Demo mode was added to GitHub Actions CI.
Generated ZIP outputs were added to .gitignore.
Python version guidance was clarified.
New-site expansion guidance was clarified.
Utilization chart filenames were hardened by including site_id.
Project status, repo map, and decisions log were refreshed.
```

## What did not change

The official six-site V1 dataset remains the official project dataset.

```text
data/inputs/real_sites_v1.csv
```

The official workflow remains:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```

The official V1 ranking remains:

```text
1. FFX002 — City of Fairfax Regional Library
2. FFX001 — Fairfax City Hall or municipal building
3. PWC002 — Neabsco-Potomac Commuter Garage
4. PWC004 — Chinn Park Regional Library
5. PWC001 — PWC McCoart Government Center
6. PWC003 — Prince William County Public Safety Training Center
```

The model is still planning support only. It does not replace utility, engineering, ADA/accessibility, Fire Marshal/AHJ, permitting, procurement, or stakeholder review.

## Demo mode scope

Demo mode is synthetic.

It is for testing:

```text
scalability
ranking behavior
workflow robustness
chart readability
data-confidence behavior
sensitivity behavior
profile-priority behavior
```

Demo mode is not for real candidate-site recommendations.

Do not copy synthetic demo rows into the official V1 dataset.

## Main demo command

Use this command from the repository root:

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

This creates local-only files under:

```text
data/demo/
```

That folder is ignored by Git.

## Main files to review before freezing

After the final local QA run, review these official outputs:

```text
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/action_matrix.md
data/outputs/site_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/profile_rank_summary.csv
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/data_confidence_chart.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/site_readiness_map.png
data/outputs/deliverable_package/
```

Review these demo outputs:

```text
data/demo/outputs/demo_run_summary_50.md
data/demo/outputs/demo_sensitivity_summary_50.csv
data/demo/outputs/charts/scalable/readiness_top_15.png
data/demo/outputs/charts/scalable/data_confidence_top_15.png
data/demo/outputs/charts/scalable/readiness_map_top_15_labeled.png
data/demo/outputs/charts/scalable/profile_heatmap_top_15.png
data/demo/outputs/charts/scalable/profile_rank_stability_top_8.png
data/demo/outputs/charts/scalable/readiness_score_distribution.png
data/demo/outputs/charts/scalable/recommendation_tier_counts.png
```

## Final QA command before tag

Run this from the repository root before creating the freeze tag:

```bash
git pull --rebase origin main

python src/run_all.py
python src/build_deliverable_package.py
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean

git status --short
```

Expected result:

```text
Official workflow passes.
Deliverable package builds with Missing files: 0.
Demo mode completes.
No unexpected tracked files are modified.
```

## Planned freeze tag

If final QA passes, create the follow-up checkpoint with:

```bash
git tag -a v1-demo-scalability-ready -m "Freeze V1 repo with scalable demo mode and polished demo visuals"
git push origin v1-demo-scalability-ready
```

Do not move or overwrite the existing `v1-review-ready` tag.

## Final reminder

The strongest next project work after this freeze is not another code feature. It is stakeholder confirmation and selected site screening, starting with the strongest current candidates and replacing V1 assumptions with confirmed site, utility, parking, ADA/accessibility, Fire Marshal/AHJ, and facility data.
