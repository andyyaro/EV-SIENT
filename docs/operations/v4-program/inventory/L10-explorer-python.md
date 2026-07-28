# LANE L10 — The 3D Explorer: Python, Build, Tests

**Tree:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/incoming/explorer/fcf-3d`
(NOT in the repo; not a git working tree — `git rev-parse --is-inside-work-tree` returns
`fatal: not a git repository`, and there is no `.git` directory.)

**Repo under comparison:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo` (branch `v4-platform`).

All 12 assigned files were read end to end. Paths below are relative to the `fcf-3d` root
unless prefixed `repo/`.

---

## THE GOVERNING FINDING OF PHASE 3 — independent verification

**Verdict: the claim HOLDS, with one material qualification that Phase 3 must know.**

### The exact lines that choose the input source

`fcf3d/build_sites.py`, lines 46–58:

```python
46  REQUIRED = {
47      "results": "tests/fixture_legacy_v2_site_results.csv",
48      "right_sizing": "tests/fixture_legacy_v2_right_sizing.csv",
49  }
50  OPTIONAL = {
51      "peak_waits": "dashboard/tableau/patch_package/tbl_peak_waits.csv",
52      "avoided_evse": "dashboard/tableau/patch_package/tbl_avoided_evse.csv",
53      "scenarios": "data/contract/v1/scenario_table.csv",
54      "coord_sources": "data/provenance/site_coordinate_sources.csv",
55      "readiness_conf": "dashboard/tableau/patch_package/tbl_readiness_confidence.csv",
56  }
57  # electrical risk file is date-stamped
58  ELECTRICAL_GLOB = "data/inputs/legacy_v2_electrical_risk_summary_frozen_*.csv"
```

`resolve_sources()` (lines 65–80) hard-fails if either REQUIRED table is absent
(line 71: `raise SourceMissing(f"required table missing: {rel}")`) and silently skips
any missing OPTIONAL table (lines 73–76).

**Qualification (important):** the canonical contract IS read — but only as an *optional*
side table. Line 53 loads `data/contract/v1/scenario_table.csv` into `frames["scenarios"]`,
consumed by `build_scenarios()` (lines 278–303) and attached at line 513 as
`props["scenarios"]`. That block is fully canonical: I confirmed the generated
`web/data/sites.geojson` carries 10 scenarios per site with `horizon_year`
2026/2036/2046/2056 and `horizon_label` now/plus10/plus20/plus30.

So: **the spine (identity, rank, score, subscores, narrative, right-sizing, and the 3D
massing sizing) is legacy_v2 fixture; the `scenarios` sub-object is canonical
milestone2_v3.** One feature carries two incompatible horizon conventions side by side,
neither of them labelled.

### The exact lines that name the output fields

`fcf3d/build_sites.py`, lines 435–437 (top-level right-sizing):

```python
435            "ports_now": _clean(row.get("recommended_ports_now")),
436            "ports_2035": _clean(row.get("recommended_ports_2035")),
437            "ports_2050": _clean(row.get("recommended_ports_2050")),
```

`fcf3d/build_sites.py`, lines 461–471 (the `right_sizing` sub-object):

```python
461            props["right_sizing"] = {
462                "ports_now": _clean(rs_row.get("ports_now")),
463                "ports_2035_base": _clean(rs_row.get("ports_2035_base")),
464                "ports_2035_high": _clean(rs_row.get("ports_2035_high")),
465                "ports_2050_base": _clean(rs_row.get("ports_2050_base")),
466                "ports_2050_high": _clean(rs_row.get("ports_2050_high")),
467                "site_capacity_cap": _clean(rs_row.get("site_capacity_cap")),
468                "future_ready_capacity": _clean(rs_row.get("future_ready_capacity")),
469                "expansion_strategy": rs_row.get("expansion_strategy"),
470                "right_sizing_reason": rs_row.get("right_sizing_reason"),
471            }
```

Two downstream consumers also key off `ports_2050`:

- `fcf3d/build_models.py:43` — `ports_pathway=asset.get("pathway_ports", props.get("ports_2050") or 2),`
- `blender/build_assets.py:184` — `ports_pathway = int(asset.get("pathway_ports") or props.get("ports_2050") or ports_now)`

Nowhere in the Python, Makefile, or tests is the string `legacy_v2` used as a *mode label* on
output. The only appearances of "legacy_v2" are inside the input filenames themselves
(`build_sites.py:47,48,58`; `Makefile:77,80,92`). Nothing tells a downstream reader that
`ports_2035`/`ports_2050` are legacy_v2-mode numbers.

### Every output field the ETL emits, in order

**GeoJSON envelope** (`write()`, lines 543–549): `type`, `name`
(`"chargeready_nova_candidate_sites"`), `crs` (`urn:ogc:def:crs:OGC:1.3/CRS84`), `metadata`,
`features`.

**Feature** (lines 516–521): `type` (`"Feature"`), `id` (= site_id), `geometry`
(`{"type":"Point","coordinates":[lon,lat,0.0]}`), `properties`.

**`properties`, in emission order** (lines 395–513) — 47 top-level keys:

1. `site_id`
2. `site_name`
3. `site_type`
4. `address`
5. `city`
6. `state`
7. `zip` (coerced `str()`, line 403)
8. `jurisdiction` — derived: `"fairfax" if str(sid).startswith("FFX") else "prince_william"` (line 404)
9. `public_access` (bool)
10. `garage_enclosed` (bool)
11. `model_rank` (int)
12. `readiness_score`
13. `readiness_score_pct` — cohort-relative rescale to 0–100 across `score_min..score_max` (lines 410–415)
14. `recommendation_tier`
15. `tier_key` — via `TIER_RANK` (lines 176–189)
16. `readiness_band`
17. `confidence_band`
18. `action_label`
19. `action_detail`
20. `planning_recommendation`
21. `priority_reason`
22. `subscores` — dict of the four `*_subscore` values
23. `subscore_labels` — dict `{demand_subscore: "Demand", ...}`
24. `data_confidence_score`
25. `data_confidence_level`
26. `data_confidence_reason`
27. `data_needed_next` (list, semicolon-split)
28. `ports_now`  ← `recommended_ports_now`
29. **`ports_2035`** ← `recommended_ports_2035`
30. **`ports_2050`** ← `recommended_ports_2050`
31. `expected_sessions_day`
32. `estimated_utilization`
33. `mean_wait_min`
34. `install_cost_est_usd`
35. `parking_spaces`
36. `strengths` (list of driver dicts)
37. `constraints` (list of driver dicts; AHJ review reasons prepended, lines 375–379)
38. `driver_attribution` (full list)
39. `score_reconstructed`
40. `ahj_review_flag` (int)
41. `review_reasons` (list)
42. `asset` — `{model:"evse_canopy", heading_deg, offset_east_m, offset_north_m, clamp_to_ground}` plus `ports` and `pathway_ports` added at lines 472–478
43. `right_sizing` (conditional) — the 9 keys quoted above, incl. **`ports_2035_base/high`, `ports_2050_base/high`**
44. `electrical` (conditional) — `risk_level`, `risk_points`, `risk_reason`, `data_needed_next`, `rank_optimistic`, `rank_expected`, `rank_conservative`, `worst_case_rank_change`
45. `queueing` (conditional) — `ports`, `mean_wait_min`, `p90_wait_min`, `peak_p90_wait_min`, `peak_erlang_wait_min`, `sim_utilization`
46. `coordinate_provenance` (conditional) — `source_dataset`, `source_owner`, `source_quality`, `notes`
47. `avoided_overbuild` (conditional) — `avoided_active_evse_ports`, `avoided_network_fee_usd_yr`
48. `scenarios` — list of dicts with `scenario_id`, `horizon_year`, `horizon_label`, `scenario_name`, `ports_active`, `ports_pathway_capacity`, `evse_power_kw`, `sessions_per_day`, `energy_required_kwh_day`, `utilization`, `peak_wait_minutes`, `lifecycle_cost_npv_usd`, `avoided_overbuild_cost_usd`, `net_co2e_kg`

*(I verified against the generated `web/data/sites.geojson`: all 47 keys present, 12 features,
FFX002 first at rank 1 / 58.8, 10 scenarios per site.)*

**Per-driver dict** (lines 240–253): `driver`, `subscore`, `subscore_label`, `effective`,
`points_earned`, `points_possible`, `points_forgone`, `lower_is_better`, and conditionally
`raw` + `raw_display`.

**`manifest`** (lines 524–537): `schema_version` (`"fcf3d/1.0.0"`, line 40), `generated_at`,
`site_count`, `score_min`, `score_max`, `sources`, `disclaimer`, `warnings`.

### Corroborating repo evidence for the finding

- `repo/tests/fixture_legacy_v2_right_sizing.csv` is **byte-identical** (`diff` clean) to
  `repo/data/outputs/v3_run/right_sizing_legacy_2035_2050.csv`. The filename in the repo says
  plainly what it is: legacy 2035/2050.
- The canonical alternative exists and is not read:
  `repo/data/outputs/v3_run/right_sizing_v3_canonical.csv` (columns: `site_id, site_name,
  model_rank, horizon_year, case, ports_active, ports_pathway, site_capacity_cap,
  expansion_strategy, right_sizing_reason`).
- `repo/data/outputs/v3_run/site_results_milestone2_v3.csv` exists (72 columns) and is not read.
- `repo/data/contract/v1/scenario_table.csv`: 120 rows, 12 sites, `model_mode` =
  `milestone2_v3` on all 120 rows, `run_id` = `milestone2_v3_20260719T052322Z`,
  `contract_version` = `1.0.0`, horizons `2026`×12 / `2036`×36 / `2046`×36 / `2056`×36.

### The 15-column gap — Phase 3 cannot simply repoint the `--repo` path

`tests/fixture_legacy_v2_site_results.csv` has 83 columns. Both
`site_results_milestone2_v3.csv` and `site_results_legacy_v2.csv` in `data/outputs/v3_run/`
have 72. Columns present in the fixture but in **neither** pipeline output:

```
action_detail, action_label, ahj_review_flag, confidence_band,
data_confidence_level, data_confidence_reason, data_confidence_score,
data_needed_next, planning_recommendation, priority_reason,
readiness_band, readiness_confidence_cell,
recommended_ports_2035, recommended_ports_2050, review_reason
```

The map's Overview / Risk-&-gaps panels are built almost entirely from those 15 fields
(properties #16–#21, #24–#27, #40–#41 above). Repointing `REQUIRED["results"]` at the V3
output would silently blank all of them (every one is fetched with `.get()`, so no error is
raised). Phase 3 needs either a V3 enrichment step that re-emits these columns, or a
documented join against `tbl_readiness_confidence.csv` + the confidence/triggers modules.

### Good news for Phase 3 — the massing does not need to change

`props["asset"]["pathway_ports"]` comes from the legacy `future_ready_capacity`
(line 473–475), **not** from `ports_2050`. I compared legacy `future_ready_capacity` against
the max `ports_pathway_capacity` in the canonical `scenario_table.csv` for all 12 sites:
they are **equal for every site** (FFX001 4/4, FFX002 8/8, FFX003 4/4, FFX004 8/8,
PWC001 3/3, PWC002 3/3, PWC003 2/2, PWC004 4/4, PWC005 2/2, PWC006 4/4, PWC007 4/4,
PWC008 2/2). So the GLB geometry is already numerically consistent with the canonical
contract. Only the *names and labels* are wrong, not the shapes.

---

## SUBSCORE_WEIGHTS / DRIVERS drift gate — line-by-line comparison

### The mirrored values, verbatim

`fcf3d/build_sites.py` lines 87–97:

```python
87  # --- Model weights, mirrored from fcf_m2.scoring.score_sites ------------------
88  # Kept in one place so the map's "why this rank" attribution is the model's own
89  # arithmetic, not a re-interpretation of it. test_build_sites.py asserts that
90  # reconstructing the score from these weights reproduces readiness_score.
91
92  SUBSCORE_WEIGHTS = {
93      "demand_subscore": 0.45,
94      "feasibility_subscore": 0.30,
95      "safety_subscore": 0.15,
96      "equity_subscore": 0.10,
97  }
```

`DRIVERS`, lines 134–174 (weight / subscore / invert, in file order):

| # | build_sites.py line | column | weight | subscore | invert |
|---|---|---|---|---|---|
| 1 | 136 | `nearby_households_1mi_n` | 0.18 | demand | no |
| 2 | 138 | `nearby_jobs_1mi_n` | 0.18 | demand | no |
| 3 | 140 | `aadt_nearest_n` | 0.13 | demand | no |
| 4 | 142 | `amenities_count_0_5mi_n` | 0.11 | demand | no |
| 5 | 144 | `parking_spaces_n` | 0.10 | demand | no |
| 6 | 146 | `hours_open_n` | 0.08 | demand | no |
| 7 | 148 | `avg_dwell_min_n` | 0.07 | demand | no |
| 8 | 150 | `ev_share_local_n` | 0.08 | demand | no |
| 9 | 152 | `existing_ports_total_n` | 0.07 | demand | **yes** |
| 10 | 155 | `spare_capacity_kw_n` | 0.35 | feasibility | no |
| 11 | 157 | `distance_to_service_ft_n` | 0.25 | feasibility | **yes** |
| 12 | 159 | `install_cost_est_usd_n` | 0.25 | feasibility | **yes** |
| 13 | 161 | `trenching_ft_n` | 0.15 | feasibility | **yes** |
| 14 | 164 | `ada_layout_possible` | 0.35 | safety | no |
| 15 | 165 | `fire_access_ok` | 0.35 | safety | no |
| 16 | 166 | `garage_enclosed` | 0.15 | safety | **yes** |
| 17 | 168 | `emergency_disconnect_visible` | 0.10 | safety | no |
| 18 | 170 | `stormwater_risk` | 0.05 | safety | **yes** |
| 19 | 172 | `equity_gap_index_n` | 1.00 | equity | no |

### `repo/src/fcf_m2/scoring.py` — the authority

```python
140  df["demand_subscore"] = 100 * (
141      0.18 * df["nearby_households_1mi_n"]
142      + 0.18 * df["nearby_jobs_1mi_n"]
143      + 0.13 * df["aadt_nearest_n"]
144      + 0.11 * df["amenities_count_0_5mi_n"]
145      + 0.10 * df["parking_spaces_n"]
146      + 0.08 * df["hours_open"].clip(lower=0, upper=24) / 24
147      + 0.07 * df["avg_dwell_min_n"]
148      + 0.08 * df["ev_share_local_n"]
149      + 0.07 * (1 - df["existing_ports_total_n"])
150  )
151  df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]
152
153  df["feasibility_subscore"] = 100 * (
154      0.35 * df["spare_capacity_kw_n"]
155      + 0.25 * (1 - df["distance_to_service_ft_n"])
156      + 0.25 * (1 - df["install_cost_est_usd_n"])
157      + 0.15 * (1 - df["trenching_ft_n"])
158  )
159
160  df["safety_subscore"] = 100 * (
161      0.35 * df["ada_layout_possible"]
162      + 0.35 * df["fire_access_ok"]
163      + 0.15 * (1 - df["garage_enclosed"])
164      + 0.10 * df["emergency_disconnect_visible"]
165      + 0.05 * (1 - df["stormwater_risk"])
166  )
167
168  df["equity_subscore"] = 100 * df["equity_gap_index_n"]
169
170  df["readiness_score"] = (
171      0.45 * df["demand_subscore"]
172      + 0.30 * df["feasibility_subscore"]
173      + 0.15 * df["safety_subscore"]
174      + 0.10 * df["equity_subscore"]
175  ).round(1)
```

### Verdict: NUMERICALLY IDENTICAL. Zero weight differences.

Every one of the 19 driver weights, all 6 inversions, all 4 subscore weights, and the
access-adjustment handling match exactly. The differences are structural only, and each is
correctly handled:

1. **`hours_open_n` does not exist as a persisted column.** scoring.py computes it inline
   (line 146). `build_sites.prepare()` lines 322–323 recreates it:
   `res["hours_open_n"] = res["hours_open"].clip(lower=0, upper=24) / 24.0` — an exact match.
   *(It does exist in the fixture CSV? No — I confirmed `hours_open_n` is NOT among the
   fixture's 83 columns; `prepare()` is doing real work, not a no-op.)*
2. **`readiness_access_adjustment`.** scoring.py:132 `np.where(public_access >= 1, 1.00, 0.65)`.
   build_sites `prepare()` lines 325–327 uses the same 1.00/0.65 split as a fallback; the
   fixture already carries the column so the fallback is dormant. `attribute_drivers()`
   line 237 applies it to demand drivers only — matching scoring.py:151, which multiplies
   only `demand_subscore`.
3. **`access_adjustment` (1.00/0.35, scoring.py:131) is deliberately NOT mirrored.** It does
   not feed `readiness_score`. Correct omission.
4. **`ev_share_local_n` is produced by `bounded_signal(x, EV_SHARE_HIGH_BENCHMARK=0.10)`**
   (scoring.py:26, 138) rather than min-max. build_sites reads the persisted column, so it
   inherits whichever regime produced the CSV. Mode-agnostic — correct.
5. **`.round(1)` on `readiness_score`** (scoring.py:175) vs. the map's per-driver
   `round(..., 2)` accumulation. This is why the gate is a ±0.15 tolerance, not equality.

### Independent numerical verification (I re-implemented the arithmetic in pure stdlib)

Script: `/private/tmp/.../scratchpad/verify_drift.py` (scratchpad only; nothing in the repo
or explorer tree was touched).

| source table | rows | worst |rebuilt − readiness_score| |
|---|---|---|
| `repo/tests/fixture_legacy_v2_site_results.csv` | 12 | **0.100** (PWC005: 37.0 vs 36.9) |
| `repo/data/outputs/v3_run/site_results_legacy_v2.csv` | 12 | 0.100 (PWC005) |
| `repo/data/outputs/v3_run/site_results_milestone2_v3.csv` | 12 | **0.100** (FFX001: 48.8 vs 48.7) |

**Two conclusions Phase 3 should bank:**
- The gate passes today, with 0.05 of headroom on a 0.15 tolerance. It is not comfortably green.
- **The same mirrored weights reproduce the milestone2_v3 scores exactly too.** This follows
  from scoring.py's own docstring (lines 10–12: *"Subscore weights ... are identical in both
  modes; only normalization differs"*). So `SUBSCORE_WEIGHTS`/`DRIVERS` are **not** a blocker
  for repointing the ETL at V3. The 15 missing narrative columns are the blocker.

### How to automate the drift gate

The honest gate is a direct read of the source of truth, not a re-listing. Suggested Phase 3
check: import `fcf_m2.scoring`, parse the four subscore coefficients out of
`enrich_and_score` (or better, refactor scoring.py to expose them as module constants and
have `build_sites` import them), and assert equality against `SUBSCORE_WEIGHTS`/`DRIVERS`.
Today nothing structurally prevents drift — `test_attribution_reproduces_model_score` only
compares against a *frozen CSV*, so if someone reweights `scoring.py` and does not re-freeze,
the test stays green and the map keeps telling the old story. **The guard is weaker than
CLAUDE.md non-negotiable #2 claims.**

---

## `test_attribution_reproduces_model_score` — full quote and what it proves

`tests/test_pipeline.py`, lines 88–102:

```python
 88  @needs_repo
 89  def test_subscore_weights_sum_to_one():
 90      assert sum(bs.SUBSCORE_WEIGHTS.values()) == pytest.approx(1.0)
 91
 92
 93  @needs_repo
 94  def test_attribution_reproduces_model_score(frames):
 95      """The whole point: our decomposition must rebuild the model's own score."""
 96      res = bs.prepare(frames["results"])
 97      for _, row in res.iterrows():
 98          rebuilt = bs.reconstruct_score(row)
 99          actual = round(float(row["readiness_score"]), 1)
100          assert abs(rebuilt - actual) <= 0.15, (
101              f"{row['site_id']}: attribution {rebuilt} vs model {actual}"
102          )
```

**What it actually proves:** for every row of whatever CSV `resolve_sources` picked as
`results`, the sum of the 19 `points_earned` values from `DRIVERS` lands within 0.15 of that
row's own `readiness_score` column.

**What it does NOT prove — and this matters:**
1. It **never imports `fcf_m2.scoring`.** It compares the map's weights to a *frozen CSV*,
   not to the live model code. If `scoring.py` is reweighted and the fixture is not
   re-frozen, this test still passes. CLAUDE.md line 53 (*"`test_attribution_reproduces_model_score`
   guards this"*) and README lines 82–84 (*"fails the build if anyone reweights the model
   without updating the map"*) both overstate what the test can do.
2. It is decorated `@needs_repo` (line 88), which is
   `pytest.mark.skipif(not os.path.isdir(REPO), ...)` where `REPO` defaults to
   `os.path.expanduser("~/fcf/Future-City-Fellowship--main-2")` (line 35). **On any machine
   without that exact directory and without `FCF_REPO` set, this test silently SKIPS.**
   15 of 31 test functions carry `@needs_repo`.
3. It runs against `bs.prepare()`, so it also exercises the `hours_open_n` reconstruction
   (lines 322–323) — a genuine part of the mirror.
4. It cannot catch a *label* error: swapping two driver `label` strings leaves the arithmetic
   intact and the test green, while the map would attribute points to the wrong thing.

Companion guards that partly close the gap:
- `test_driver_weights_sum_to_one_per_subscore` (lines 77–85) — each subscore's driver
  weights sum to 1.0.
- `test_subscore_weights_sum_to_one` (lines 88–90).
- `test_invert_flags_match_scoring_module` (lines 111–122) — pins the exact inverted set.
- `test_build_emits_no_drift_warnings` (lines 105–108) — asserts `build()` produced no
  warning containing `"attribution"` (the runtime version of the same check,
  build_sites.py lines 366–372).

---

## Per-file inventory

### `CLAUDE.md`
- **Role:** Project instructions for Claude Code working inside the explorer; the constitutional document for the 3D layer.
- **Kind:** authored (113 lines).
- **Reads:** n/a (prose).
- **Written by / read by:** read by any agent operating in `fcf-3d`. Cross-references `fcf3d/build_sites.py`, `fcf3d/geometry.py`, `fcf3d/glb.py`, `fcf3d/build_models.py`, `blender/build_assets.py`, `web/`, `tests/test_pipeline.py`, `fcf_m2/scoring.py`, `app.js::renderPanel()`, `COMPARE_ROWS`.
- **Key contents:** see the verbatim constraint list below.
- **Notes:** the "46 tests" claim (line 42) is **correct** — I counted 31 `def test_*`, of which three are parametrized (5 + 6 + 7 cases), giving 28 + 18 = 46. Line 74 gives a macOS-specific Blender path as an example (`/Applications/Blender.app/Contents/MacOS/Blender`), which is illustrative, not a hardcoded dependency.

#### EVERY architectural constraint in CLAUDE.md, verbatim and numbered

**C1 — the architecture rule (line 14):**
> **Blender authors. Cesium delivers. Python glues.**

**C2 — Blender is not the viewer (lines 28–30):**
> Blender is **never** the viewer. It is an offline asset factory that emits
> glTF. If a task starts with "make Blender show the map interactively," that is
> the wrong shape — redirect it into the Cesium layer.

**C3 — the layout table's role assignments (lines 36–42):**
> | `fcf3d/build_sites.py` | ETL. Joins model CSVs → GeoJSON. **Read-only on the source repo.** |
> | `fcf3d/geometry.py` | Parametric infrastructure massing. Single source of truth. |
> | `fcf3d/glb.py` | Dependency-free glTF 2.0 writer (the no-Blender path). |
> | `fcf3d/build_models.py` | CLI; routes to `glb.py` or Blender. |
> | `blender/build_assets.py` | Headless `bpy` asset builder. Only importable inside Blender. |
> | `web/` | CesiumJS app. Static — no build step, no bundler. |
> | `tests/test_pipeline.py` | 46 tests. Must stay green. |

**C4 — never re-run the model (non-negotiable 1, lines 46–48):**
> 1. **Never re-run or re-implement the scoring model here.** This repo is a
>    *projection* of frozen outputs. If a number looks wrong, fix it upstream in
>    `fcf_m2`, re-freeze, and re-run `make data`.

**C5 — the weight mirror (non-negotiable 2, lines 50–55):**
> 2. **`SUBSCORE_WEIGHTS` and `DRIVERS` in `build_sites.py` mirror
>    `fcf_m2/scoring.py`.** They exist so the map can explain *why* a site ranks
>    where it does using the model's own arithmetic.
>    `test_attribution_reproduces_model_score` guards this. If you change either
>    file, run the tests — a silent drift means the map tells planners a story
>    the model never told.

**C6 — geometry.py has zero dependencies (non-negotiable 3, lines 57–58):**
> 3. **`geometry.py` has zero dependencies and must stay that way.** Blender's
>    bundled Python imports it directly; anything exotic breaks the Blender path.

**C7 — the disclaimer (non-negotiable 4, lines 60–63):**
> 4. **Keep the disclaimer visible.** Every surface says screening-class
>    planning estimates, not engineering. Electrical service capacity is
>    unconfirmed for all 12 sites. Do not let UI polish imply more certainty
>    than the data supports.

**C8 — no secrets / the Cesium ion token (non-negotiable 5, lines 65–66):**
> 5. **No secrets in the repo.** The Cesium ion token is entered at runtime and
>    held in the browser only.

**C9 — the procedure for adding a field to the map (lines 85–89):**
> 1. Add it to the properties dict in `build_sites.py::build()`.
> 2. Add a key assertion to `test_all_expected_keys_present`.
> 3. Render it in `app.js::renderPanel()` and, if comparable, add a row to
>    `COMPARE_ROWS`.
> 4. `make data && make test`.

**C10 — geometry changes go in one place (lines 93–96):**
> Edit `fcf3d/geometry.py` only. Both output paths read from it, so they stay in
> sync automatically. Add a test to the geometry section — the existing ones
> check ADA stall provision, canopy clearance, pathway-stall translucency, and
> the ENU→glTF axis conversion.

**C11 — Blender MCP sandbox warning (lines 100–103):**
> - **Blender MCP** (`blender.org/lab/mcp-server`, official; Blender 5.1+) —
>   for interactive art direction of the assets. It executes generated Python
>   inside a live Blender session with no sandbox, so run it against a scratch
>   scene, not a file you care about.

**C12 — batch generation over MCP (lines 106–107):**
> For batch asset generation prefer `blender --background --python`, not MCP.
> It is deterministic, reviewable, and runs in CI.

**C13 — style (lines 111–113):**
> - Python: 3.11+, type hints, module docstrings that say *why*.
> - JS: plain ES modules, no framework, no bundler. Keep it that way.
> - Comments explain intent and constraints, not syntax.

**Attribution obligations** are stated in README.md, not CLAUDE.md — see below (A1/A2).

---

### `README.md`
- **Role:** Public-facing explainer: the Blender-vs-Cesium architectural argument, what's in the tree, setup, extension paths, honest limits, licences.
- **Kind:** authored (234 lines).
- **Reads:** n/a.
- **Written by / read by:** human-read. Duplicates and elaborates CLAUDE.md.
- **Key contents:**
  - Layer table (lines 31–37): CesiumJS (Apache-2.0) / Google Photorealistic 3D Tiles / Blender→glTF / Python / Claude Code.
  - "`build_sites.py` is read-only on the Fellowship repo. It joins **seven** frozen model tables on `site_id`" (lines 66–67).
  - The worked FFX002 example (lines 77–79) and "Those numbers sum back to 58.8 exactly, for all 12 sites" (line 81).
  - Setup: `make setup && make all FCF_REPO=... && make serve`; `make candidates`; `make doctor`; the `~/` expansion rationale (lines 122–143).
  - **A1 — Google attribution obligation (lines 154–156):** *"Google requires that its logo and the data attribution stay visible; the app leaves Cesium's credit widget in place, so don't remove it."*
  - **A2 — licence block (lines 231–234):** *"CesiumJS is Apache-2.0. Google Photorealistic 3D Tiles are governed by the Google Maps Platform Terms of Service and require visible brand and data attribution. OpenStreetMap imagery and building data are ODbL. Blender is GPL — that covers the application, not the glTF it exports."*
  - Cesium ion token guidance (lines 147–159): free token, pasted into an in-page gate, "stored in your browser only"; without a token the viewer falls back to *Flat* mode on OSM imagery.
  - "Honest limits" (lines 211–225): screening-class only; electrical capacity unconfirmed for all 12 sites; the massing is not a design; ADA provision is a rule of thumb — confirm against the AHJ; placement offsets are eyeballed; photorealistic tiles are a dated snapshot.
- **Notes:** I verified the FFX002 attribution numbers by recomputing them from the fixture — **+8.11 / +7.50 / +7.50 earned and −10.50 / −4.52 / −4.08 forgone reproduce exactly**. But those are *legacy_v2* numbers (see findings). Line 80 calls `distance_to_service_ft` "short service run" whereas the code's label (build_sites.py:157) is "Distance to electrical service" — prose/code label mismatch. Line 81's "exactly" is a slight overclaim (PWC005 is off by 0.1). Line 66 says "seven" tables; the code resolves eight.

---

### `Makefile`
- **Role:** The whole build/run/verify surface for the explorer.
- **Kind:** authored (123 lines).
- **Reads:** `requirements.txt`; `$(FCF)/tests/fixture_legacy_v2_site_results.csv` as its repo-validity probe; `web/data/sites.geojson`; `web/app.js`.
- **Written by / read by:** invokes `fcf3d.build_sites`, `fcf3d.build_models`, `pytest tests/`, `ruff`, `node --check`, `python -m http.server`.
- **Variables:** `VENV ?= venv`; `PY ?=` auto-selects `venv/bin/python` if executable else `python3` (line 15); `FCF_REPO ?= ../Future-City-Fellowship` (line 16); `FCF := $(patsubst ~/%,$(HOME)/%,$(FCF_REPO))` (line 20); `BLENDER ?=` (empty); `PORT ?= 8080`; `SHELL := /bin/bash` (line 25, needed for the `< <(...)` process substitution in `candidates`).

**Every target and what it runs:**

| target | line | what it does |
|---|---|---|
| `setup` | 30–36 | `python3 -m venv venv`; upgrade pip; `pip install -r requirements.txt`; prints next-step hint. |
| `all` | 38 | `data models` (no recipe of its own). |
| `data` | 41–42 | depends on `doctor`; runs `$(PY) -m fcf3d.build_sites --repo "$(FCF)" --out web/data`. |
| `models` | 45–46 | `$(PY) -m fcf3d.build_models --sites web/data/sites.geojson --out web/models`. **No `doctor` dependency and no dependency on `data`.** |
| `models-blender` | 49–52 | requires `BLENDER` to be non-empty (else `exit 1`); same as `models` plus `--blender "$(BLENDER)"`. |
| `serve` | 55–59 | depends on `all`; `cd web && $(PY) -m http.server $(PORT)`. |
| `test` | 62–63 | depends on `doctor`; `FCF_REPO="$(FCF)" $(PY) -m pytest tests/ -q`. |
| `doctor` | 66–82 | three gates: (a) `$(PY) -c "import pandas"`, else "Fix: make setup"; (b) `test -d "$(FCF)"`; (c) `test -f "$(FCF)/tests/fixture_legacy_v2_site_results.csv"`, else *"so it is not the model repo"*. Failures call `$(MAKE) -s candidates` then exit 1. |
| `candidates` | 85–112 | `find -L "$(HOME)" -maxdepth 5 -type d -name "Future-City-Fellowship*" -print0 \| sort -z`; marks each `OK` iff it contains `tests/fixture_legacy_v2_site_results.csv`. |
| `lint` | 114–116 | `$(PY) -m ruff check fcf3d tests` (soft-fails to a "(ruff not installed, skipping)" echo) then `node --check web/app.js`. |
| `clean` | 118–120 | `rm -rf web/data/sites.* web/data/manifest.json web/models/*.glb` plus `find . -name __pycache__ -type d -exec rm -rf {} +`. |
| `help` | 122–123 | `grep -E '^## ' $(MAKEFILE_LIST) \| sed 's/## /  /'`. |

- **Notes:** `doctor` and `candidates` both encode **"a directory is the model repo iff it contains `tests/fixture_legacy_v2_site_results.csv`"** (lines 77, 92). Phase 3 must change this probe, or a V3-only checkout will be rejected as "not the model repo." `.PHONY` (line 27) correctly lists all 12 targets. `ruff` and `node` are used but appear in no dependency file.

---

### `requirements.txt`
- **Role:** Python dependency list for the explorer's own venv.
- **Kind:** authored (9 lines).
- **Reads:** n/a. **Read by:** `Makefile:33`.
- **Key contents, verbatim:** `pandas>=2.1` (runtime, "the ETL only"); `pytest>=8.0` (dev); commented-out `# geopandas>=0.14` and `# py3dep>=0.16` labelled "Optional, only for the GIS extension path described in README.md".
- **Notes:** see the pyproject comparison section below.

---

### `.gitignore`
- **Role:** Excludes Python bytecode and every generated artifact.
- **Kind:** authored (9 lines).
- **Reads:** n/a.
- **Key contents — the file in full:**
```
1  __pycache__/
2  *.pyc
3  .pytest_cache/
4  web/data/sites.geojson
5  web/data/sites.json
6  web/data/sites.inline.js
7  web/data/manifest.json
8  web/models/*.glb
9  *.blend1
```
- **Answering the assigned question precisely:** it does **NOT** use a `web/data/*` glob — it
  enumerates the four generated files by name (lines 4–7). It **does** exclude
  `web/models/*.glb` (line 8, exact string). Any *new* file the ETL writes into `web/data/`
  would not be ignored.
- **Notes:** `venv/` is **not** ignored, even though `make setup` (Makefile:31) creates
  `venv/` in the tree. Also `*.blend` is not ignored — only `*.blend1` — while
  `blender/build_assets.py:192` writes `<sid>.blend` files when `--blend` is passed.
  Both are real gaps for Phase 3's `git add`.

---

### `fcf3d/__init__.py`
- **Role:** Marks `fcf3d` as a package so `python -m fcf3d.build_sites` works.
- **Kind:** authored. **0 bytes / 0 lines.**
- **Reads:** n/a. **Read by:** the Python import machinery.
- **Key contents:** none — the file is empty.
- **Notes:** no `__version__`. The GLB `asset.generator` string and `SCHEMA_VERSION` are the
  only version markers in the package.

---

### `fcf3d/build_sites.py`
- **Role:** The ETL. Joins the frozen model tables into one georeferenced record per site and writes four artifacts into `web/data/`.
- **Kind:** authored (597 lines). Generator of `sites.geojson`, `sites.json`, `manifest.json`, `sites.inline.js`.
- **Reads:** eight tables under `--repo` (lines 46–58, quoted above), of which two are required.
- **Written by / read by:** invoked by `Makefile:42`; its output is read by `fcf3d/build_models.py`, `blender/build_assets.py`, `web/app.js`, and `tests/test_pipeline.py`.
- **Key contents:**
  - `SCHEMA_VERSION = "fcf3d/1.0.0"` (line 40).
  - `REQUIRED` / `OPTIONAL` / `ELECTRICAL_GLOB` (46–58); `SourceMissing` (61–62); `resolve_sources()` (65–80) — takes `matches[-1]` of the sorted electrical glob, commented "newest freeze".
  - `SUBSCORE_WEIGHTS` (92–97), `SUBSCORES` (99–104), `Driver` dataclass (107–131), `DRIVERS` (134–174).
  - `TIER_RANK` (176–182): `{"Tier 1":1, "Tier 2":2, "Tier 3":3, "High-review":2, "Low public-priority":4}`; `tier_key()` prefix match, default **9** (185–189).
  - `_clean()` (192–204): NaN/inf → `None`, floats `round(..., 6)`.
  - `split_sentences()` (207–212): splits on `;`, strips `" .;"`, upper-cases the first letter.
  - `attribute_drivers()` (215–255): `possible = SUBSCORE_WEIGHTS[sub] * drv.weight * 100.0 * adj`; `earned = possible * eff`; `forgone = possible - earned`. Rounds `effective` to 4 dp and points to 2 dp.
  - `reconstruct_score()` (258–261).
  - `mine_strengths_constraints()` (264–275): **strength threshold `effective >= 0.60`** (line 270); **constraint threshold `points_forgone >= 0.20`** (line 273); `top_n=5` each.
  - `build_scenarios()` (278–303): the canonical-contract projection; sorts by `(horizon_year or 0, scenario_name)`.
  - `prepare()` (318–328); `load()` (331–335); `build()` (338–538); `write()` (541–574); `main()` (577–593).
  - Drift warning at runtime: `abs(rebuilt - actual) > 0.15` → warning string *"(fcf3d.build_sites DRIVERS may have drifted from fcf_m2.scoring)"* (lines 368–372).
  - Coordinate sanity gate: `-180 <= lon <= 180 and -90 <= lat <= 90`, else warn + `continue` (lines 359–361).
  - `sites.inline.js` header: `/* generated by fcf3d.build_sites — do not edit */` then `window.__FCF_SITES__ = <json>;` (lines 570–573). Rationale comment at 566–567: `fetch()` of a local JSON file is blocked by CORS on `file://`.
  - Manifest disclaimer, verbatim (531–535): *"Planning prototype only. Screening-class estimates; not an engineering, permitting, or procurement tool. Electrical service capacity is unconfirmed for all sites pending utility/facility review."*
- **Notes:**
  - `readiness_conf` (line 55) is resolved and `load()`ed into a DataFrame, but `build()`
    **never reads `frames["readiness_conf"]`**. It only inflates the manifest's `sources`
    block. Dead load.
  - Line 89 comment names `test_build_sites.py`; the actual test file is `tests/test_pipeline.py`.
  - Line 388 filters `avoided_evse` on `horizon_year == 2026` only and then takes
    `m.iloc[0]` with no filter on the table's `case` column. Today `tbl_avoided_evse.csv`
    has exactly 12 rows at 2026, all `case == 'baseline'`, so it is deterministic — but it
    is one contract change away from silently picking an arbitrary case.
  - `readiness_score_pct` (410–415) is a **cohort-relative** rescale over the 12 sites in the
    run. It is not the model's score and will move if the cohort changes.
  - The `jurisdiction` derivation (line 404) hardcodes the `FFX`-prefix convention; any
    third jurisdiction silently becomes `prince_william`.

---

### `fcf3d/build_models.py`
- **Role:** CLI that turns `sites.geojson` into one `.glb` per site, via either the pure-Python writer or a Blender subprocess.
- **Kind:** authored (81 lines).
- **Reads:** `--sites` (default `web/data/sites.geojson`); writes `--out` (default `web/models`).
- **Written by / read by:** invoked by `Makefile:46` and `Makefile:51`; imports `.geometry.build_site` and `.glb.write_glb` (lines 23–24); shells out to `blender/build_assets.py`.
- **Key contents:**
  - `load_sites()` (27–30) — accepts either a FeatureCollection or a bare list.
  - `run_pure_python()` (33–48) — `build_site(sid, ports_now=asset.get("ports", props.get("ports_now") or 2), ports_pathway=asset.get("pathway_ports", props.get("ports_2050") or 2))`.
  - `run_blender()` (51–58) — `[blender, "--background", "--factory-startup", "--python", script, "--", "--sites", sites_path, "--out", out_dir]`; script path resolved as `<pkg parent>/blender/build_assets.py`.
  - `main()` (61–77) — args `--sites`, `--out`, `--blender`; prints a per-site size table.
- **Notes:** line 43's `props.get("ports_2050")` fallback is a legacy-horizon reference. In
  practice it is dead for real runs, because `build_sites` always sets `asset.pathway_ports`
  (lines 474/478). `asset.get("ports", ...)` uses `dict.get` with a default rather than
  `or`, so an explicit `0` in `asset["ports"]` would pass through — but `build_site` clamps
  with `max(1, ...)` (geometry.py:136).

---

### `fcf3d/geometry.py`
- **Role:** The single parametric definition of a proposed site build, shared by the pure-Python and Blender asset paths.
- **Kind:** authored (268 lines).
- **Reads:** nothing — pure computation.
- **Written by / read by:** imported by `fcf3d/glb.py:20` (`MATERIALS, Box, SiteBuild`), `blender/build_assets.py:44` (`MATERIALS, build_site`), `fcf3d/build_models.py:23` (`build_site`), `tests/test_pipeline.py:26–32`.

#### C6 verified — EVERY import statement in `geometry.py`

```python
25  from __future__ import annotations
26
27  import math
28  from dataclasses import dataclass
```

That is the complete list — three statements, lines 25–28. `__future__`, `math`, and
`dataclasses` are all Python standard library. **Confirmed: zero third-party imports.**
The constraint holds.

- **Key contents (all metres):** `STALL_WIDTH = 2.75`, `STALL_LENGTH = 5.50`,
  `ADA_STALL_WIDTH = 4.90` (*"stall + access aisle, ADA van-accessible"*), `AISLE_CLEAR = 1.50`,
  `CANOPY_HEIGHT = 4.30`, `CANOPY_THICKNESS = 0.28`, `CANOPY_OVERHANG = 0.55`,
  `COLUMN_SIDE = 0.30`, `PEDESTAL = (0.50, 0.34, 1.45)`, `CABINET = (1.60, 0.90, 2.00)`,
  `TRANSFORMER = (2.10, 1.60, 1.80)`, `PAD_THICKNESS = 0.06` (lines 32–45).
  - `MATERIALS` (49–59), 9 entries `(RGBA, metallic, roughness)`. Only
    `stall_future` is translucent: `((0.784, 0.639, 0.243, 0.45), 0.00, 0.80)` — alpha 0.45.
    `pedestal` is commented "ChargeReady green" `(0.086, 0.478, 0.408, 1.00)`.
  - `Box` frozen dataclass (62–88): `center`, `size`, `material`, `yaw_deg=0.0`, `name="part"`;
    `corners_enu()` emits 8 corners in `(sx, sy, sz)` order with `sx` outermost;
    **`enu_to_gltf((x,y,z)) -> (x, z, -y)`** (lines 85–88).
  - `SiteBuild` frozen dataclass (91–105): `site_id`, `ports_now`, `ports_pathway`, `boxes`,
    `footprint_m`, `ada_stalls`, plus `part_count` property.
  - `ada_stall_count()` (113–119): `max(1, ceil(total/25))` for `total > 0`, else 0 —
    docstring explicitly calls it a *"screening rule of thumb ... Confirm against the AHJ's
    adopted accessibility code before using in design."*
  - `build_site()` (122–268): clamps `ports_now = max(1, int(...))` and
    `ports_pathway = max(ports_now, ...)`; first `n_ada` stalls get `ADA_STALL_WIDTH`;
    stall pads are `w - 0.12` wide; a `stripe_NN` wheel-stop per stall; one `dispenser_NN`
    per **two** stalls at `y = STALL_LENGTH/2 + 0.55`; canopy deck at
    `z = CANOPY_HEIGHT + CANOPY_THICKNESS/2` with four corner columns; **mid columns added
    only when `span > 16` m** (line 220); `power_cabinet` at `x = span/2 + 1.20`;
    `pad_transformer` + `transformer_pad` at `x = span/2 + 3.40`, both behind
    `equip_y = STALL_LENGTH/2 + AISLE_CLEAR + 1.20`; footprint
    `(span + 2*CANOPY_OVERHANG + 5.0, STALL_LENGTH + AISLE_CLEAR + 4.0)`.
- **Notes:** the module docstring (lines 20–22) is itself a disclaimer: *"Dimensions follow
  common US surface-lot practice for a screening-level massing study. They are illustrative
  geometry for siting discussions, NOT a design."* No third-party import has crept in; the
  `dataclass(frozen=True)` on `SiteBuild` holds a mutable `list` field, which is a soft spot
  (hashability), but nothing hashes it.

---

### `fcf3d/glb.py`
- **Role:** Dependency-free binary glTF 2.0 writer — the no-Blender output path.
- **Kind:** authored (222 lines). Generator of `web/models/*.glb`.
- **Reads:** `MATERIALS, Box, SiteBuild` from `.geometry` (line 20). Writes to a path given by the caller.
- **Written by / read by:** called by `fcf3d/build_models.py:24,46`; exercised by `tests/test_pipeline.py:299–364`; its output is loaded by `web/app.js` in Cesium.

#### How it writes glTF 2.0, and what it guarantees about well-formedness

**Structure.** `build_gltf()` (70–195) groups `site.boxes` by material (`defaultdict(list)`,
72–74), then emits **one primitive per material** into a single mesh in a single node in a
single scene (lines 176–184). Each box is tessellated by `_tessellate()` (50–63) into 6
quads → 12 triangles, with **its own 4 vertices per face** so every face gets a crisp flat
normal (24 positions per box). `FACES` (32–39) is an explicit index table into
`corners_enu()`'s documented ordering, with the ordering itself re-documented in a comment
at lines 30–31. Normals come from `_normal()` (42–47), a normalized cross product with a
`or 1.0` divide-by-zero guard.

**Binary layout.** `add_view()` (100–108) appends a payload, records
`{buffer:0, byteOffset, byteLength, target}`, then pads the *buffer* to a 4-byte boundary —
so every subsequent `byteOffset` is 4-aligned while `byteLength` stays exact. Three views
per material: POSITION (`ARRAY_BUFFER` 34962), NORMAL (34962), indices
(`ELEMENT_ARRAY_BUFFER` 34963). Component types: `FLOAT = 5126` for attributes,
`UNSIGNED_INT = 5125` for indices, `mode = TRIANGLES = 4`.

**Spec guarantees it makes:**
1. `asset.version == "2.0"` and a `generator` string (173–176): `"fcf3d.glb (Future City Fellowship / ChargeReady NOVA)"`.
2. **POSITION accessors carry `min`/`max`** (129–131, 138–139) — required by the glTF 2.0 spec for POSITION; normals and indices correctly omit them.
3. Coordinate system: every position goes through `Box.enu_to_gltf` (line 52) so the file is **Y-up**, as the spec requires.
4. Accessor `byteOffset` alignment is satisfied by the 4-byte buffer padding; all component types are 4 bytes.
5. `buffers[0].byteLength == len(buffer)` (line 184) — the test asserts this equality (test line 307).
6. **Alpha handling:** `alphaMode: "BLEND"` is set iff `colour[3] < 1.0` (91–92), so only `stall_future` is blended. `doubleSided: False` on every material.
7. **GLB container** (`write_glb`, 198–211): 12-byte header `struct.pack("<4sII", b"glTF", 2, total)`; JSON chunk padded with **spaces** (`_pad4(..., b" ")`, line 201) as the spec requires; BIN chunk padded with **zeros** (line 202); `total = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)` (line 204). Both chunk lengths are therefore multiples of 4 and the declared total equals the real file length.
8. `extras` (185–193) carries `site_id`, `ports_now`, `ports_pathway`, `ada_stalls`, `footprint_m`, `part_count`, and a `note`: *"Screening-level massing for siting discussion. Not a design."* — the disclaimer travels inside the binary asset.

**What it does not guarantee:** no `byteStride` (fine for tightly packed VEC3), no
`bufferView.name`, no UVs or tangents, no textures, no `KHR_materials_*` extensions, no
Draco compression. `UNSIGNED_INT` indices are legal in core glTF 2.0 but need
`OES_element_index_uint` on WebGL1-only renderers.

- **Also:** `to_data_uri()` (214–222) emits a base64 `model/gltf+json` data URI with the buffer inlined as a `data:application/octet-stream;base64,...` URI. It is **not referenced anywhere else in the tree** — dead but harmless.
- **Verified against the shipped artifacts:** all 12 `web/models/*.glb` begin with the magic
  `glTF`, and each file's `extras.ports_now` / `extras.ports_pathway` matches the
  corresponding `asset.ports` / `asset.pathway_ports` in `web/data/sites.geojson` exactly.
  **No generator/artifact drift.** Sizes 15,296–29,732 bytes; part counts 13–32.

---

### `blender/build_assets.py`
- **Role:** Headless `bpy` asset factory — the presentation-fidelity twin of `glb.py`.
- **Kind:** authored (198 lines). Only importable inside Blender's Python.
- **Reads:** `--sites` (default `web/data/sites.geojson`); writes `--out` (default `web/models`) and optionally `--blend <dir>`.
- **Written by / read by:** launched as a subprocess by `fcf3d/build_models.py:51–58`, i.e. by `make models-blender`. Imports `fcf3d.geometry` (line 44) after inserting the repo root into `sys.path` (lines 40–42).
- **Key contents:**
  - Imports `bpy` (line 36, `# noqa: F401  (only resolvable inside Blender)`) and `bmesh` (37).
  - `BEVEL_WIDTH = 0.015` (line 46).
  - `reset_scene()` (54–59) — `bpy.ops.wm.read_factory_settings(use_empty=True)` then explicitly purges meshes/materials/objects; comment: *"--factory-startup still ships a default cube."*
  - `get_material()` (62–79) — builds a Principled BSDF from the shared `MATERIALS` palette; sets `Alpha` and `blend_method = "BLEND"` when `colour[3] < 1.0`.
  - `make_box()` (82–111) — `bmesh.ops.create_cube(size=1.0)` → `scale(vec=box.size)` → bevel with `offset = min(BEVEL_WIDTH, min(box.size) * 0.2)`, `segments=2`, `profile=0.7`, `affect="EDGES"`, skipped if the result would be ≤ 1e-4. Sets `obj.location = box.center`, `rotation_euler = (0, 0, radians(yaw_deg))`, and forces `use_smooth = False` on every polygon.
  - `build_blender_site()` (114–130) — one root collection `<sid>_build` with sub-collections named from the part-name prefix (`stall`, `stripe`, `dispenser`, `canopy`, `column`, `power`, `pad`, `transformer`).
  - `export_glb()` (133–150) — `bpy.ops.export_scene.gltf(export_format="GLB", export_yup=True, export_apply=True, export_materials="EXPORT", export_cameras=False, export_lights=False, export_extras=True, use_selection=False)`.
  - `parse_args()` (158–169) — reads args after the bare `--`; keys `sites`, `out`, `blend`.
  - `main()` (172–194) — per feature: `ports_now = int(asset.get("ports") or props.get("ports_now") or 2)`, `ports_pathway = int(asset.get("pathway_ports") or props.get("ports_2050") or ports_now)`, reset scene, build, export, optionally `bpy.ops.wm.save_as_mainfile`.
- **Notes:**
  - Docstring lines 25–26 restate C2 verbatim in a second place: *"Blender is an AUTHORING tool here, not the viewer. It never ships to the browser — it produces glTF, and CesiumJS does the delivery."*
  - Line 184 is the second `ports_2050` reference outside `build_sites.py`.
  - `export_glb` passes `filepath=path` but `use_selection=False` and never selects — it exports the whole scene, which is correct because `reset_scene()` runs per site.
  - `bpy.ops.export_scene.gltf` keyword names (`export_yup`, `export_apply`, `export_materials`) are Blender-version-sensitive; CLAUDE.md line 100 targets Blender 5.1+ for MCP but nothing pins a version for this script. **Uncertain** whether these kwargs are valid on the reader's Blender — I could not execute Blender here.
  - There is **no test coverage of this file at all** (it cannot be imported outside Blender). The "cannot drift" guarantee in the docstring (line 23) rests entirely on both paths importing `fcf3d.geometry`, which is true, but the *rendering* of that geometry is untested.

---

### `tests/test_pipeline.py`
- **Role:** The explorer's whole test suite: source resolution, weight fidelity, output shape, utilities, geometry, GLB validity, end-to-end.
- **Kind:** authored (382 lines).
- **Reads:** `os.environ["FCF_REPO"]`, default `os.path.expanduser("~/fcf/Future-City-Fellowship--main-2")` (line 35). Inserts the repo root on `sys.path` (line 23).
- **Written by / read by:** run by `Makefile:63` as `FCF_REPO="$(FCF)" $(PY) -m pytest tests/ -q`.
- **Key contents — 31 `def test_*`, 46 collected cases:**
  - Fixtures `sources` / `frames` / `result`, all `scope="module"` (44–56).
  - `needs_repo = pytest.mark.skipif(not os.path.isdir(REPO), ...)` (36–38). **15 tests carry it.**
  - Source layer: `test_required_sources_resolve` (63), `test_missing_repo_raises` (69, no `@needs_repo` — the only source test that always runs).
  - Weight fidelity: `test_driver_weights_sum_to_one_per_subscore` (78), `test_subscore_weights_sum_to_one` (89), `test_attribution_reproduces_model_score` (94), `test_build_emits_no_drift_warnings` (106), `test_invert_flags_match_scoring_module` (112).
  - Output shape: `test_every_site_becomes_a_feature` (129), `test_ranks_are_dense_and_unique` (134), `test_coordinates_are_in_northern_virginia` (140) — **bbox `-78.5 < lon < -76.8`, `38.4 < lat < 39.2`**, `test_output_is_strict_json` (148) — asserts no `"NaN"`/`"Infinity"` substrings, `test_all_expected_keys_present` (159) — the 12-key required set, `test_asset_ports_are_sane` (171), `test_strengths_and_constraints_are_ordered` (179), `test_writes_inline_bundle` (189).
  - Utilities: `test_split_sentences` (5 params), `test_tier_key` (6 params, incl. the exact tier strings `"Tier 1 — advance to site screening"`, `"Tier 2 — promising candidate, refine data"`, `"Tier 3 — lower priority / monitor"`, `"High-review candidate"`, `"Low public-priority / special-use"` → 1/2/3/2/4, and `"something else"` → 9), `test_clean_strips_non_finite`.
  - Geometry: `test_ada_stall_count` (7 params: 0→0, 1→1, 8→1, 25→1, 26→2, 50→2, 51→3), `test_build_site_scales_with_ports`, `test_pathway_stalls_are_translucent`, `test_first_stall_is_ada_width` (asserts `ADA_STALL_WIDTH - 0.12`), `test_ports_pathway_never_below_ports_now`, `test_canopy_sits_above_every_dispenser`, `test_enu_to_gltf_conversion`, `test_box_corners_count_and_yaw`.
  - GLB: `test_gltf_structure_is_valid` (asserts `pos["count"] % 24 == 0`, i.e. 6 faces × 4 verts per box), `test_glb_header_is_well_formed` (magic/version/length/chunk alignment/`extras.site_id`), `test_translucent_material_gets_blend_mode`, `test_normals_are_unit_length`.
  - `test_end_to_end` (368–382) — writes via `bs.write`, then `run_pure_python`, asserts each GLB `> 1000` bytes and starts with `b"glTF"`.
- **Notes:**
  - The 12-key set in `test_all_expected_keys_present` (161–164) does **not** include `ports_2035`/`ports_2050`/`right_sizing`/`scenarios`, so removing or renaming those fields would not fail the suite. That is convenient for Phase 3's rename but means the suite provides no schema lock on the horizon fields.
  - `test_invert_flags_match_scoring_module`'s docstring says *"These four drivers are the ones fcf_m2.scoring wraps in (1 - x)"* (line 113) while the assertion lists **six** columns (115–122). Docstring/assert contradiction.
  - `test_missing_repo_raises` (69–71) asserts `SourceMissing` for `"/nonexistent/path/xyz"` — that path does not exist, so `os.path.isfile` fails on the first REQUIRED entry. Correct, but it only proves the required-table branch, not that a *V3-only* repo is rejected.
  - No test asserts the GeoJSON `crs`, the `schema_version`, or the manifest `disclaimer`.

---

## `requirements.txt` vs `repo/pyproject.toml` and `repo/requirements-lock.txt`

**`repo/pyproject.toml`** — `name = "fcf-m2"`, `version = "3.0.0"`, `requires-python = ">=3.11"`.
Core deps: `numpy>=1.26`, `pandas>=2.1`, `matplotlib>=3.8`, `jsonschema>=4.20`.
Extras: `gis = ["geopandas>=0.14", "contextily>=1.5", "xyzservices>=2024.0"]`,
`test = ["pytest>=8.0", "pytest-cov>=4.1"]`,
`presentation = ["pillow>=10.0", "reportlab>=4.0"]`.
`[tool.setuptools.packages.find] where = ["src"]`.
`[tool.pytest.ini_options] testpaths = ["tests"]`, `addopts = "-q"`.

**`repo/requirements-lock.txt`** — header: *"Lock generated 2026-07-19 from Python 3.14.6 arm64
venv used for all V3 verification runs"*. Relevant pins: `pandas==3.0.3`, `numpy==2.5.1`,
`pytest==9.1.1`, `pytest-cov==7.1.0`, `matplotlib==3.11.1`, `jsonschema==4.26.0`.

**Version conflicts: NONE.** `pandas>=2.1` is satisfied by `pandas==3.0.3`; `pytest>=8.0` by
`pytest==9.1.1`; `geopandas>=0.14` matches pyproject's `gis` extra exactly. Nothing in the
explorer's requirements is incompatible with a pinned lock.

**What would need to become an optional extra:**
- The explorer's *runtime* need is `pandas` only — already a **core** dependency of `fcf-m2`.
  So an `explorer` extra would add **zero new runtime packages**. Merging is cheap.
- `pytest` → already covered by the existing `test` extra.
- `py3dep>=0.16` (commented out, requirements.txt line 9) is the **one genuinely new**
  dependency; it is not in pyproject's `gis` extra. If Phase 3 keeps the GIS-extension path,
  extend `gis` to `["geopandas>=0.14", "contextily>=1.5", "xyzservices>=2024.0", "py3dep>=0.16"]`.
- `ruff` (used by `Makefile:115`) and `node` (used by `Makefile:116`) appear in **no**
  dependency file in either tree. If `lint` is to be enforced, `ruff` belongs in a `dev` extra.

**Packaging friction Phase 3 must plan for:**
1. `pyproject.toml` uses a **src layout** (`where = ["src"]`). The explorer's package sits at
   `fcf-3d/fcf3d/`, a flat layout. It must move to `repo/src/fcf3d/` to be discovered — and
   that changes `blender/build_assets.py:40–42`, which computes `_REPO` as
   `dirname(dirname(abspath(__file__)))` and inserts it on `sys.path`.
2. `[tool.pytest.ini_options] testpaths = ["tests"]` is repo-wide, so the explorer's tests
   would join the main run — meaning **`REPO`/`FCF_REPO` and the 15 `@needs_repo` skips
   become part of the repo's CI story.** Once in-tree, `FCF_REPO` should simply be the repo
   root and the skip should be deleted, or the skips will hide real failures.
3. Python floor: pyproject says `>=3.11`, the lock was built on 3.14.6, CLAUDE.md line 111
   says "Python: 3.11+". Consistent.

---

## Cross-cutting checks I ran

| check | result |
|---|---|
| `590.2` (the corrected-away eGRID factor) anywhere in the explorer tree | **not found** — clean |
| `596.3` anywhere in the explorer tree | **not found** — the explorer never surfaces the emissions factor at all, even though it copies `net_co2e_kg` out of the contract (`build_sites.py:299`). The contract's `grid_factor_value` is `596.3`, units `lb CO2e/MWh`, vintage `eGRID2023r2, accessed 2026-07-19` on all 120 rows. |
| absolute `/Users/...` paths in the Python, Makefile, or docs | **none** |
| secrets / tokens / AWS account IDs / `AKIA` | **none.** `web/index.html:102` contains `placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6..."`, which is only the generic JWT header prefix used as an input placeholder, not a credential. (That file is L11's lane; noted here as corroboration of constraint C8.) |
| generator vs artifact drift (`web/models/*.glb` vs `web/data/sites.geojson`) | **none** — all 12 match on `ports_now`/`ports_pathway` |
| `web/data/manifest.json` provenance | `schema_version: fcf3d/1.0.0`, `generated_at: 2026-07-26T04:27:14.192759+00:00`, `site_count: 12`, `score_min: 29.6`, `score_max: 58.8`, `warnings: []`, and an eight-entry `sources` block naming both `fixture_legacy_v2_*.csv` files. **The ETL demonstrably ran, cleanly, against the legacy fixture.** |
| test count claim ("46 tests", CLAUDE.md:42, README:61) | **correct** |

**Observation, not a defect:** `fcf3d/__pycache__/` exists with an mtime of today
(2026-07-27 11:50), later than the tree's copy time (10:57). Something imported the package
today. I did not import or execute anything inside either tree; my verification script is a
standalone re-implementation in the scratchpad.

---

## Findings summary (severity-ordered)

1. **HIGH — legacy_v2 spine, unlabelled.** `build_sites.py:47–48` requires
   `tests/fixture_legacy_v2_*.csv`; `:436–437` and `:463–466` emit `ports_2035`,
   `ports_2050`, `ports_2035_base/high`, `ports_2050_base/high`; `build_models.py:43` and
   `build_assets.py:184` consume `ports_2050`. Nothing labels any of it `legacy_v2`.
   Canonical is 2026/2036/2046/2056.
2. **HIGH — two horizon conventions in one Feature.** The same `properties` object carries
   `ports_2035`/`ports_2050` (legacy) and a `scenarios` list at 2026/2036/2046/2056
   (canonical, from `data/contract/v1/scenario_table.csv` via `build_sites.py:53,513`).
3. **HIGH — README.md:199** *"the 2026 → 2036 → 2050 horizons"*: mangled, neither convention.
   Should read 2026 → 2036 → 2046 → 2056.
4. **HIGH — README.md:77–81** headline numbers (FFX002 *"ranks #1 at 58.8"*) are legacy_v2.
   Under `milestone2_v3` the same site scores **51.8 at rank #2**, and **FFX004 is #1 at 53.4**
   (`repo/data/outputs/v3_run/site_results_milestone2_v3.csv`). The arithmetic reproduces
   exactly; the *regime* is unlabelled.
5. **HIGH — the drift guard is weaker than advertised.** `test_attribution_reproduces_model_score`
   never imports `fcf_m2.scoring`; it compares against a frozen CSV. CLAUDE.md:53 and
   README:82–84 claim it "fails the build if anyone reweights the model."
6. **HIGH — Phase 3 blocker: the 15-column gap.** The fixture carries 15 narrative/banding
   columns that neither `site_results_milestone2_v3.csv` nor `site_results_legacy_v2.csv`
   has. Every one is read with `.get()`, so repointing the ETL fails **silently**.
7. **MEDIUM — the Makefile defines "the model repo" as "contains
   `tests/fixture_legacy_v2_site_results.csv`"** (`Makefile:77,80,92`). A V3-only checkout is
   rejected with *"so it is not the model repo."*
8. **MEDIUM — 15 of 46 tests silently skip** unless `FCF_REPO` points at a real directory
   (`test_pipeline.py:35–38`), including the load-bearing attribution test. The default is a
   machine-specific `~/fcf/Future-City-Fellowship--main-2`.
9. **MEDIUM — `readiness_conf` is resolved and loaded but never used** (`build_sites.py:55`
   vs. `build()` 338–538). It inflates the manifest `sources` block, and is the likely origin
   of README:66's "seven tables" (the code resolves eight).
10. **LOW — `build_sites.py:89`** references `test_build_sites.py`; the file is
    `tests/test_pipeline.py`.
11. **LOW — `test_pipeline.py:113`** docstring says *"These four drivers"*; the assertion
    lists six columns.
12. **LOW — README.md:81** *"sum back to 58.8 exactly, for all 12 sites"* — PWC005 is off by
    0.1 (37.0 rebuilt vs 36.9 model). The gate is ±0.15, not exact.
13. **LOW — README.md:80** calls the driver *"short service run"*; the code label
    (`build_sites.py:157`) is *"Distance to electrical service"*.
14. **LOW — `.gitignore` does not exclude `venv/`** (created by `Makefile:31`) nor `*.blend`
    (written by `build_assets.py:192`); it ignores only `*.blend1`.
15. **LOW — `build_sites.py:388`** filters `tbl_avoided_evse.csv` on `horizon_year == 2026`
    but not on `case`, then takes `iloc[0]`. Deterministic today (12 rows, all `baseline`),
    fragile to a contract change.
16. **INFO — good news for Phase 3:** the mirrored weights reproduce **milestone2_v3** scores
    just as well as legacy_v2 (worst delta 0.100 on both), and the legacy
    `future_ready_capacity` equals the canonical max `ports_pathway_capacity` for all 12
    sites. Neither the weight table nor the GLB geometry needs to change.
