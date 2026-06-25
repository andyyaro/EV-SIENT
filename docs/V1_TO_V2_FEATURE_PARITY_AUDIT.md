# V1 to V2 Feature Parity Audit

## Purpose

V2 is a continuation of V1, not a separate replacement. The goal is:

```text
Every feature available in V1 should either exist in V2 or be intentionally replaced by an upgraded V2 version.
```

This audit separates three categories:

```text
1. Mirrored or upgraded in V2
2. Present in V1 but still missing or incomplete in V2
3. V2-only additions that go beyond V1
```

## V1 workflow reference

The V1 full workflow is controlled by:

```text
src/run_all.py
```

V1 workflow steps:

```text
Validate input data
Run readiness and right-sizing model
Add readiness-confidence action matrix
Create polished readiness score chart
Create data confidence chart
Run sensitivity analysis
Run scoring profile analysis
Create profile score heatmap
Create profile rank stability chart
Create readiness map
Generate Markdown run summary
Generate results interpretation
Check outputs and compare to V1 baseline
```

## V2 workflow reference

The V2 workflow is controlled by:

```text
src/run_v2.py
```

Current V2 workflow steps:

```text
Run V2 site-readiness model
Add V2 readiness-confidence action matrix
Validate V2 site input data
Run V2 sensitivity analysis
Run V2 scoring-profile analysis
Run V2 electrical-feasibility scenario analysis
Run V2 right-sizing scenario analysis
Generate V2 interpretation report
```

## Mirrored or upgraded in V2

| V1 feature | V2 status | Notes |
|---|---|---|
| Input validation | Mirrored | V2 runs validation against `real_sites_v2.csv`. |
| Readiness scoring model | Mirrored and expanded | V2 uses expanded candidate set and public-data upgrades. |
| Port recommendation | Upgraded | V2 still has model ports and now adds right-sizing scenarios. |
| Action matrix | Mirrored | V2 writes `v2_action_matrix.md`. |
| Sensitivity analysis | Mirrored | V2 writes V2-specific sensitivity outputs. |
| Scoring profile analysis | Mirrored | V2 writes V2-specific profile outputs. |
| Results interpretation | Mirrored | V2 writes `v2_results_interpretation.md`. |
| Output checker | Mirrored and expanded | V2 checker now also checks electrical and right-sizing outputs. |

## V1 features not yet fully mirrored in V2

These are the important parity gaps.

| V1 feature | V1 script | V2 gap | Recommended V2 action |
|---|---|---|---|
| Polished readiness score chart | `src/plot_readiness_score_chart.py` | Script exists and accepts custom paths, but V2 workflow does not call it yet. | Add V2 call and output `data/outputs/charts/v2_polished_readiness_score_chart.png`. |
| Data confidence chart | `src/plot_data_confidence_chart.py` | Script exists and accepts custom paths, but V2 workflow does not call it yet. | Add V2 call and output `data/outputs/charts/v2_data_confidence_chart.png`. |
| Profile score heatmap | `src/plot_profile_score_heatmap.py` | Script exists and accepts custom paths, but V2 workflow does not call it yet. | Add V2 call and output `data/outputs/charts/v2_profile_score_heatmap.png`. |
| Profile rank stability chart | `src/plot_profile_rank_stability.py` | Script exists and accepts custom paths, but V2 workflow does not call it yet. | Add V2 call and output `data/outputs/charts/v2_profile_rank_stability_chart.png`. |
| Readiness map | `src/plot_site_map.py` | Script exists and accepts custom paths, but may need V2 tuning because it was written around the original six-site layout. | Add V2 output after checking it handles 12 sites cleanly; adjust labels if needed. |
| Markdown run summary | `src/generate_run_summary.py` | V2 workflow does not currently produce a V2 run summary. | Add V2-compatible arguments or create `src/generate_run_summary_v2.py`. |
| Success marker / output manifest summary | `src/run_all.py` + output manifest | V2 has no V2 success marker or manifest-backed output summary. | Add `data/config/output_manifest_v2.json` and `data/outputs/v2_workflow_success.json`. |
| Baseline comparison | `src/check_outputs.py` / `src/compare_to_baseline.py` | V2 checker validates outputs but does not compare against a V2 baseline. | Create V2 baseline snapshot after parity is stable, then compare future runs against it. |
| Deliverable package | `src/build_deliverable_package.py` | Not part of current V2 workflow. | Decide whether V2 needs a deliverable package after parity is complete. |
| Demo mode / scalable visuals | `src/run_demo.py`, scalable chart scripts | These exist in repo but are not V2-specific yet. | Treat as optional after core parity. |

## V2-only additions beyond V1

These should remain in V2 because they improve the prototype beyond V1.

```text
Expanded candidate dataset
Public-data source extracts
AFDC EV supply counts
OSM amenities review
Draft parking review workflow
Electrical-feasibility scenario analysis
Right-sizing scenario analysis
Batch checkpoint documents
V2 technical workflow README
```

## Recommended implementation order

Do the parity work in this order to avoid breaking the workflow:

```text
1. Add V2 calls for the existing polished chart scripts.
2. Add V2 calls for profile heatmap and rank stability charts.
3. Add V2 map output, then check whether labels are readable with 12 sites.
4. Add V2 run summary.
5. Add V2 output manifest and success marker.
6. Add V2 baseline comparison only after the V2 outputs are stable.
```

## Important rule

If V1 has a feature and V2 has an upgraded version, do not duplicate it unnecessarily.

Example:

```text
V1 had recommended_ports_now / 2035 / 2050.
V2 has those plus right-sizing scenarios.
That counts as mirrored and upgraded, not missing.
```

## Current conclusion

V2 has already mirrored the core model-analysis features from V1, and it adds several stronger Phase 2 features. The main remaining parity work is visual/reporting/output-packaging fidelity: polished charts, map, run summary, manifest/success marker, and baseline comparison.
