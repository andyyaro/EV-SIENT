<!-- Saved research output. Do not treat as an implementation record. -->
# Phase 6B - design brief (research output, nothing built)

> **Provenance of this document.** Produced 2026-07-27 by a 12-agent research fleet
> (`wf_d029c874-d32`): five parallel lanes - input schema, units/CRS, validation UX,
> completeness→confidence, fallbacks - each followed by an **adversarial challenge pass whose
> first duty was finding invented sources**, then a synthesis pass.
>
> **It is a design brief for work that has not started.** Every path it names under
> `data/intake/` and `src/fcf_m2/input_schema.py` does **not exist**. Read it as a proposal.
>
> **What has been independently confirmed by the lead, and what has not.** The brief's claims
> about *this repository's current code* were spot-checked where they were acted on - and
> three of them turned out to be real defects, reproduced by execution and recorded in
> **DEC-011** with one fixed and two pinned by
> [`tests/test_absence_is_not_favourable.py`](../../../tests/test_absence_is_not_favourable.py).
> The brief's claims about *external data sources* have **not** been checked by anyone: §6
> says so itself, in its own words - *"Read this section as a to-verify list, not a usable
> table. I did not open a single external publisher page in this session."* Nothing marked
> `[UNVERIFIED]` may ship, be cited, or be presented to the client until someone opens the
> publisher's page and confirms it exists.
>
> Recorded here so the reasoning survives the session that produced it. Decisions taken from
> it get their own `DECISIONS.md` entries.

---

# Phase 6B - Data Intake Layer: Design Brief

**Status:** design only. **Nothing in this brief has been built.** Every path under `data/intake/` and `src/fcf_m2/input_schema.py` named below does not exist - I checked (`ls data/intake` → No such file or directory; `ls data/input_schema` → No such file or directory).
**Date:** 2026-07-27 · **Implements:** DEC-000 · **Verification basis:** every `file:line` below was opened in this session, or executed in `./venv/bin/python`. Claims I could not check carry `[UNVERIFIED]` and say what to check.

---

## 1. What 6B is

Today the model reads five files whose names, columns, units and coordinate frame are hard-coded to Northern Virginia. `workflow._load_inputs` is five bare `pd.read_csv` calls with no existence check and no validation [VERIFIED: workflow.py:62-68]. `scoring.enrich_and_score` then indexes 27 columns as `df[col]` - 7 `YES_NO_FIELDS` and 20 `NUMERIC_FIELDS` [VERIFIED: scoring.py:83-95, :181-184] - so a file missing one column raises `KeyError: 'aadt_nearest'` [VERIFIED: executed]. Site IDs must match `^(FFX|PWC)[0-9]{3}$` and jurisdiction must be `fairfax` or `pwc` or the output contract refuses the run [VERIFIED: contract.py:83, :85]. There is no CRS handling anywhere: the only geospatial code is a lon/lat range check that drops a site with a warning [VERIFIED: src/fcf3d/build_sites.py:438-441] and a `CRS84` string stamped into emitted GeoJSON [VERIFIED: build_sites.py:664]. Units exist only as column-name suffixes; `grep -i units src/fcf_m2/` returns only `grid_factor_units`. This is what makes it a study rather than a product.

6B inserts one stage in front of the existing pipeline. A jurisdiction supplies a file in whatever shape it has; intake **proposes** a column mapping, a unit interpretation, a CRS and an ID assignment; a human sees the proposal and every finding **before** any run; on acceptance intake materialises a canonical frame, writes a transformation ledger, and emits typed provenance rows into the confidence system that already exists. What changes about the model: a missing column stops being a crash and becomes a scored, named absence; a substituted default stops being invisible and becomes a ledger line plus a confidence deduction; and `data_confidence_level_v3` starts meaning "how complete and how well-sourced is this jurisdiction's data" rather than "which of two fixed conditions did `build_field_provenance.py` evaluate". Nothing about the scoring formulas changes. The two frozen reproductions - `legacy_v2` bit-exact and `milestone2_v3` - must still hold.

**The hard constraint governs every decision below.** Cleaning must never silently improve data quality. Two specific traps this brief must not fall into, both verified: `site_capacity_cap` returns **6** when `parking_spaces <= 0`, which is *more permissive* than a real 40-space lot (cap 2) [VERIFIED: right_sizing.py:61-65 and `even_ceiling` at :44-50] - so an absent parking count currently *raises* the port ceiling; and `garage_enclosed` and `stormwater_risk` are in `INVERTED_DRIVERS` [VERIFIED: scoring.py:78-81], so `.fillna(0)` on an absent value yields `1 - 0 = 1`, the *best* safety term. Absence currently improves two numbers. 6B must close both or say plainly that it did not.

---

## 2. The input schema

**Location:** `src/fcf_m2/input_schema.py` (code), `data/input_schema/v1/{schema.json, fields.csv, README.md}` (versioned artifact), `data/intake/jurisdiction_registry.csv` (prefix authority). Per-jurisdiction intake state under `data/intake/<JUR>/`. **None of these exist.** Run *output* goes to `data/outputs/<run_id>/` because that is the only gitignored data path [VERIFIED: `.gitignore` line 11 is `data/outputs/` and nothing else under `data/`] - writing per-run artifacts under `data/intake/` means `git add -A` commits somebody's real facility data.

The entry point is `input_schema.materialise(raw_frame, manifest) -> (model_frame, provenance_rows, ledger_rows)`, called in front of `enrich_and_score`. It guarantees all 27 hard-required columns exist, so `KeyError` stops being the failure mode.

### 2.1 Absence classes

| Class | Behaviour | Confidence effect |
|---|---|---|
| `refuse` | The run does not start. Names the field and the 1-based file lines. | - |
| `neutral` | Column materialised with a **declared** neutral value. Ledger line written. Field's group loses coverage. | Feeds `build_confidence` through the existing rubric. |
| `carry` | Absent, no model effect, no demotion. | None. |

### 2.2 REQUIRED - `refuse` class (2 fields)

| Field | Type | Why absence refuses |
|---|---|---|
| `source_site_id` | string, 1–128 chars, non-blank, unique in file | It is the join key. There is nothing to substitute. |
| `site_type` | string, non-blank | `right_sizing` branches on `"garage" in site_type` twice [VERIFIED: right_sizing.py:90, :131]. An empty string switches off the garage/fire-review gate **and** satisfies the `"garage" not in site_type` floor-raising branch at :90 - anti-conservative in both directions. |

`site_name` is **not** in this class. Its rule is a substitution (`source_site_id` used as the display name), and calling a substitution a refusal is the category error the class table exists to prevent. It is `neutral`, with one caveat: the output contract enforces `"site_name": {"minLength": 3}` [VERIFIED: contract.py:84], so intake must range-check the substituted value at intake time and refuse *then*, naming the row, rather than letting it fail four layers later.

`public_access` is **not** in this class either. Its `0` neutral is already the most conservative outcome the model can produce: demand × 0.65, `access_adjustment` 0.35 [VERIFIED: scoring.py:186-187], all port targets capped at 2 and strategy forced to `do_not_advance_general_public_buildout` [VERIFIED: right_sizing.py:80-83, :125-127]. A blank cannot inflate any number. It degrades; it does not refuse.

### 2.3 REQUIRED-for-scoring - `neutral` class (27 fields)

**Flags** (7). `yesno_to_num` returns `float(value)` **unchanged for any int or float**, and only maps *strings* through `{1, y, yes, true, t}` [VERIFIED: scoring.py:104-110; executed: numeric `0.5` → `0.5`, string `'0.5'` → `0.0`]. Because pandas parses a `0/1/0.5` column as float, **fractional and out-of-range flag values survive into the safety subscore unclamped.** Intake must therefore range-check flags to exactly `{0, 1}`: a numeric flag outside that set refuses the value by row and value, because coercing it either direction invents a fact.

| Flag | Neutral | What the neutral costs |
|---|---|---|
| `public_access` | 0 | Highest-consequence neutral in the schema (§2.2). |
| `ada_layout_possible` | 0 | −5.25 readiness (0.15 × 0.35 × 100) [VERIFIED: scoring.py:35-40, :61-67] |
| `fire_access_ok` | 0 | −5.25 readiness |
| `emergency_disconnect_visible` | 0 | −1.5 readiness |
| `stormwater_risk` | **UNRESOLVED** | Inverted (0.15 × 0.05). `0` is the *favourable* value - absence improves the score. |
| `garage_enclosed` | **UNRESOLVED** | Inverted (0.15 × 0.15) and suppresses the "High-review candidate" tier. See below. |
| `battery_storage_flag` | 0 | No formula reads it. One non-formula read in a standards-register condition string [VERIFIED: standards.py:174]. |

**`garage_enclosed` and `stormwater_risk` are UNRESOLVED and must be decided before implementation.** Setting them to the pessimistic `1` manufactures an affirmative claim about a physical site, and for `garage_enclosed` that claim surfaces to users as a tier string, which carries no ledger. Two acceptable resolutions, pick one: **(a)** keep the `0` neutral and record the absence purely as coverage loss on `parking_and_layout` / `safety_review_fields`, accepting that readiness is silently 2.25 points optimistic and *saying so in the ledger line*; or **(b)** adopt the pessimistic `1` **and** replace the tier string with an explicit "garage status unknown - review required". Shipping (b) without the tier change ships a fabrication.

**Numerics** (20). Coercion is `pd.to_numeric(errors="coerce").fillna(0)`; a non-numeric string becomes `0` with no warning [VERIFIED: scoring.py:183-184]. Neutral is `0` except where stated.

| Field | Unit | Accepted range | Neutral | Effect of the neutral |
|---|---|---|---|---|
| `employees_day` | persons/day | 0–200000 | 0 | demand × 0.0006 [VERIFIED: config.py:81] |
| `visitors_day` | persons/day | 0–500000 | 0 | demand × 0.0015 [VERIFIED: config.py:80] |
| `fleet_vehicles` | count | ≥0 | 0 | Coerced; **no formula reads it** [VERIFIED: only reference in `src/`+`scripts/` is its own name in `NUMERIC_FIELDS`] |
| `parking_spaces` | count | 0–50000 | **refuse-the-column, cap at 2** | `<= 0` returns cap **6** [VERIFIED: right_sizing.py:61-65] - more permissive than any lot under ~100 spaces. Ledger: *"parking_spaces was absent, so the site's port ceiling was set to the schema minimum of 2."* |
| `hours_open` | hours/day | 0–24, clipped [VERIFIED: scoring.py:197] | 0 | Also the queueing denominator; `ports_for_sessions` separately defaults it to **8** via `row.get("hours_open", 8)` [VERIFIED: right_sizing.py:56] - two different defaults for one field, which intake must reconcile |
| `avg_dwell_min` | minutes | 0–1440 | 0 | `choose_ports` falls back to a 2 h service time |
| `nearby_households_1mi` | count | ≥0 | 0 | anchored lo 0 / hi 12000 |
| `nearby_jobs_1mi` | count | ≥0 | 0 | anchored lo 0 / hi 40000 |
| `aadt_nearest` | vehicles/day | ≥0 | 0 | anchored lo 0 / hi 60000, 0.45 × 0.13 |
| `amenities_count_0_5mi` | count | ≥0 | 0 | anchored lo 0 / hi 8 |
| `ev_share_local` | **fraction 0–1** | 0–1 | 0 | **Not min-max normalised** - `bounded_signal(s, 0.10)` = `(s/0.10).clip(0,1)` [VERIFIED: scoring.py:26, :121-123, :193]. A percent value of `8.2` clips to 1.0 and scores maximum, silently. |
| `existing_l2_ports_1mi` / `existing_dcfc_ports_3mi` | count | ≥0 | 0 | summed, anchored lo 0 / hi 130, inverted |
| `equity_gap_index` | index 0–1 | 0–1 | 0 | Whole equity subscore. A percent value clips at the anchor *and* fails the contract's `maximum: 1`. Both are loud. |
| `spare_capacity_kw` | kW | 0–5000 | 0 | anchored lo 0 / hi 200; largest single feasibility term (0.30 × 0.35) |
| `distance_to_service_ft` | feet | ≥0 | **anchor `hi` = 300** | Inverted, so `0` reads as *"the panel is right there"*. The anchor's own `hi` is 300 [VERIFIED: executed against `data/anchors/anchor_set_v1.json` - `{'lo': 0, 'hi': 300, 'note': 'cohort range 75-150'}`]. Ledger: *"distance_to_service_ft was absent, so the worst distance the model's anchor set allows for was used."* **Do not use a cohort-derived neutral** - it would break the V3 fixed-anchor invariant the module's own docstring promises: *"The same site receives the same score regardless of which other sites are in the run"* [VERIFIED: scoring.py:5-8]. |
| `trenching_ft` | feet | ≥0 | 0 | inverted (anchor hi 250); feeds `install_cost_est_usd` |
| `trench_cost_per_ft` | USD/ft | ≥0 | 0 | `install_cost_est_usd` only |
| `service_upgrade_cost_usd` | USD | ≥0 | 0 | `install_cost_est_usd`; also `economics.SiteCostInputs` |
| `elec_service_rating_amp` | amps | ≥0 | 0 | No scoring formula reads it, but `build_field_provenance.py:52-53` uses it to decide whether `electrical_service` is `unconfirmed` |

**Derived, never ingested** [VERIFIED: scoring.py:189-190]: `install_cost_est_usd = trenching_ft × trench_cost_per_ft + service_upgrade_cost_usd`; `existing_ports_total = existing_l2_ports_1mi + existing_dcfc_ports_3mi`. Intake **refuses** a file supplying either directly - a discrepancy between a supplied value and the derived one has no honest resolution.

**Anchor coverage:** 13 anchors, all 12 `NORMALIZE_COLS` anchored, plus an `ev_share_local` entry `normalize_fields` never reads [VERIFIED: executed]. So `anchor_fallback_fields` is empty in V3 mode and **a new jurisdiction is scored against Northern Virginia's anchors.** The manifest must carry `anchor_set_version` so the output states which yardstick was used. This is a portability limitation, not a bug - see §8.

### 2.4 Per-site operating profile

`legacy_matlab_site_meta.csv` is read whole and indexed `meta_idx.loc[sid]` - `KeyError` for any missing site [VERIFIED: workflow.py:66, :163, :213].

| Field | Unit | Range | Neutral |
|---|---|---|---|
| `arrival_start_hr` / `arrival_end_hr` | hour of day | 0–24, end ≥ start | `(0, hours_open)` so the window equals the operating day; `charging_window_hr` must land in [0,24] or RT-05 fails [VERIFIED: contract.py:206-207] |
| `base_load_mean_kw` | kW | 0–5000 | **`None`, not `0`** - `base_load_kw` is schema-nullable. Three call sites assume a number: `workflow.py:224`, `workflow.py:262`, `matlab_adapter.py:51`. All three need a null path. |
| `base_load_peak_kw` | kW | 0–5000 | `None`. Consumed at `matlab_adapter.py:52`. |

**Recommendation:** fold these four into the site file as optional columns and keep `legacy_matlab_site_meta.csv` as a v1-only compatibility reader for NoVA. DEC-000's gate is a *single* messy fixture running end to end [VERIFIED: DECISIONS.md:74]; a second mandatory file is a second refusal surface for no modelling benefit.

### 2.5 OPTIONAL

| Field | Class | Notes |
|---|---|---|
| `lat` / `lon` | `neutral` | Run proceeds - `scored.get("lat")` broadcasts a null column [VERIFIED: workflow.py:155]. But `gis_offline.build_site_map` does `s["lat"]` → KeyError, and `fcf3d.build_sites` range-checks and `continue`s with a warning [VERIFIED: build_sites.py:438-441]. Model runs, map silently loses the site. 6B makes that a counted degradation. |
| `address`, `city`, `state`, `zip` | `carry` | Read via `row.get(...)` - safe absence |
| `elec_service_voltage` | `carry` | **Zero references in `src/` or `scripts/`** [VERIFIED: grep]. Populated `480` at all 12 sites and consumed by nothing. |
| `ev_registrations_local` | `carry` | **Zero references** [VERIFIED: grep] |
| `battery_storage_kwh` | `carry` | **Zero references** [VERIFIED: grep] |
| `notes` | `carry` | Contract requires the field to exist but never parses it |
| `electrical_risk_level` | `neutral` → `"medium"` | `_merge_risk_defaults` accepts any string and comparisons lowercase [VERIFIED: right_sizing.py:75, :120, :274-284], so `"elevated"` silently reads as not-high and disables the `ports_now ≤ 2` cap. **An unrecognised value REFUSES the file**, naming the row, the value and the three permitted spellings - a typo is a one-edit fix for the supplier. A genuinely blank cell stays `neutral` → `"medium"`, ledgered (which is what happens today, silently). |

### 2.6 Observed-data files: referenced, not redefined

`CAPACITY_COLUMNS` (11) and `SESSION_COLUMNS` (13) already exist with all-or-nothing schema refusal [VERIFIED: observed.py:78-90, :223-225, :248-254]. The input schema imports them exactly as `contract_v2.observed_methods()` already imports `METHOD_TO_BASIS` rather than restating it [VERIFIED: contract_v2.py:148-155].

Two live gaps 6B inherits:

1. `_as_date` accepts only `%Y-%m-%d` and raises a bare `ValueError` [VERIFIED: observed.py:208-213]. `workflow._ingest_observations` catches only `observed.ObservationError`, so a file with `09/15/2026` produces a stack trace. Same for `_optional_float` on `"1,200"` or `"400 kW"` [VERIFIED: observed.py:201-205].
2. `engineering_estimate` and `planning_proxy` are `implied_basis` values absent from `SOURCE_CLASS_SCORES`, so `observation_provenance_rows` rewrites them to `official_source` = 90 [VERIFIED: observed.py:430-433 vs confidence.py:22-33]. A comparable-site proxy currently scores above `derived_public_data` (55). **6B must not build on that fallback.** Fixing it is a scoring-policy change with its own decision entry.

---

## 3. The adapter stage

**Nothing here is ever applied silently.** The adapter produces a `MappingProposal`, renders it, and applies nothing until `accepted_by` is set. DEC-000 names this a first-class platform surface: *"load data, see the proposed mapping, see what failed validation and why, see the resulting confidence before committing to a run"* [VERIFIED: DECISIONS.md:33-35].

### 3.1 The proposed-mapping data structure

The platform renders this. It is JSON-serialisable, entirely typed, and contains no composed prose except the `reason` fields, which are single sentences.

```python
@dataclass(frozen=True)
class ColumnProposal:
    source_column: str            # verbatim header from the file
    source_index: int             # 0-based position; survives duplicate names
    target_field: str | None      # canonical name, or None = "unmapped"
    confidence: str               # "exact" | "alias" | "fuzzy" | "none"
    evidence: str                 # "header matched alias table entry 'SVC_AMPS'"
    sample_values: list[str]      # first 3 non-blank, verbatim, repr'd, <=60 chars each
    proposed_unit: str | None     # from the closed vocabulary, or None
    unit_source: str              # "declared_by_user" | "canonical_default" | "unknown"
    conversion: Conversion | None  # None when no conversion is needed
    status: str                   # "proposed" | "accepted" | "rejected" | "auto"
    reason: str                   # ONE sentence, <=140 chars, names both units/columns

@dataclass(frozen=True)
class Conversion:
    from_unit: str; to_unit: str; factor: float
    exact: bool                   # True only for definitional factors
    explanation: str              # "converted from metres to feet"

@dataclass(frozen=True)
class IdProposal:
    source_site_id: str; source_line: int
    proposed_site_id: str         # f"{JUR}{NNN:03d}"
    basis: str                    # "crosswalk_existing" | "assigned_new"

@dataclass(frozen=True)
class CrsProposal:
    declared: str | None          # "EPSG:2283", from .prj / manifest / GeoJSON crs member
    declared_from: str            # "prj_file" | "manifest" | "geojson_crs_member" | "absent"
    target: str                   # always "OGC:CRS84" (lon, lat)
    operation_name: str | None    # pyproj's chosen operation, verbatim
    operation_accuracy_m: float | None
    unavailable_operations: list[str]
    status: str

@dataclass(frozen=True)
class MappingProposal:
    dataset: str; file: str; file_sha256: str
    delimiter: str; encoding: str; line_terminator: str
    input_schema_version: str; jurisdiction_code: str
    columns: list[ColumnProposal]
    unmapped_source_columns: list[str]
    unmatched_target_fields: list[str]   # canonical fields nothing mapped to
    ids: list[IdProposal]
    crs: CrsProposal | None
    findings: list[Finding]              # §4
    accepted_by: str | None              # None until a human or a mapping file accepts
    accepted_at: datetime | None
```

Every applied transformation writes a `Fix` record with `kind`, `status`, `accepted_by`, `before`, `after`, `reason`, `applied_by` - persisted to `data/outputs/<run_id>/transformation_ledger.csv`.

### 3.2 What may run without being asked

A transformation may be `accepted_by="auto:deterministic"` **only if it is byte-level and provably value-preserving.** Exhaustively, three:

- BOM stripped
- Leading/trailing whitespace and NBSP trimmed from `source_site_id`
- CRLF normalised **on write** (recorded, not applied to the source)

Everything else is `status="proposed"` and requires acceptance: delimiter change, any unit conversion, any date reinterpretation, any column mapping, any reprojection, any row drop. **There is no `--auto-fix-all` flag.** The batch path is `--accept-fixes-from intake_map.json`, diffable in review - DEC-000 rules that a mapping config is the automation fallback, never the primary path [VERIFIED: DECISIONS.md:60].

### 3.3 Units

There is no unit metadata anywhere in the repo; units live only in column-name suffixes and no reader validates one. **Inferring a unit from a suffix is exactly the silent improvement DEC-000 forbids.** Units come from the mapping step, never from the header.

**Recommendation: a hand-rolled, frozen conversion table in `fcf_m2`. Reject `pint`.** I re-verified the reasoning against pint 0.25.3 by execution:

| Probe | Result | Consequence |
|---|---|---|
| `Q('1 kVA').to('kW')` | **1.0, no warning** | The most consequential electrical collision passes silently. Power factor erased. |
| `Q('1 ton').to('kg')` | **907.18474** (short ton) | "1 ton CO2" meaning tonnes is off by 10.23%. |
| `Q('1 therm').to('J')` | **1.055056e8** | The US therm is 105,480,400 J, carried only as `US_therm`. The obvious spelling is 0.024% wrong. |
| `Q('1 acre').to('m**2')` | **4046.8726** (US **survey** acre) | While `Q('1 foot**2')` = 0.09290304 (**international** foot). Two length bases in one registry, no signal. |

[All VERIFIED: executed against pint 0.25.3.] The collisions that hurt this dataset - kVA↔kW, short↔metric ton, ftUS↔ftIntl, fraction↔percent, Wh↔kWh - are same-dimension or dimensionless, and pint's dimensional algebra catches none of them. It catches exactly one thing (amps→kW raises `DimensionalityError`), which is one `if` statement. And `Q('1 KW')`, `Q('1 kw')`, `Q('1 MMBTU')` all raise `UndefinedUnitError` - you write the alias table regardless.

Declared conversions, all factors re-checked:

| Field | Canonical | Also accepted | Factor | Ledger sentence |
|---|---|---|---|---|
| `distance_to_service_ft`, `trenching_ft` | feet | metres | ×3.280839895 (**international** foot) | "converted from metres to feet" |
| `avg_dwell_min` | minutes | hours | ×60 | "converted from hours to minutes" |
| `spare_capacity_kw` | kW | MW / W | ×1000 / ÷1000 | "converted from megawatts to kilowatts" |
| `ev_share_local`, `equity_gap_index` | fraction 0–1 | percent 0–100 | ÷100 | "converted from percent to a 0–1 fraction" |
| `trench_cost_per_ft` | USD/ft | USD/m | ×0.3048 | "converted from USD per metre to USD per foot" |

**A closed `AMBIGUOUS_PAIRS` vocabulary that never converts and always asks:** kVA→kW, amps→kW, therms→kWh (a category error, not a unit problem: a facility's gas therms must not reach electrical capacity), short↔metric tons, nominal↔real USD (`ECON` carries no cost-year key [VERIFIED: config.py:114-135 - 15 keys, none naming a dollar-year]).

**Two rules, and the split between them matters.** (1) **Every** conversion - exact or not - emits a provenance record naming from-unit, to-unit, factor and reason. DEC-000 requires *recording*, not penalising [VERIFIED: DECISIONS.md:43-45]. (2) **Only an assumed** unit additionally sets `unresolved_flag=1`, which `score_field` already deducts 15 for [VERIFIED: confidence.py:82]. A declared unit converted by an exact factor is recorded at full confidence.

**The residual hole, stated plainly.** The out-of-range gate catches `ev_share_local = 8.2`. It does **not** catch a percent value that lands inside 0–1: a true share of 0.082% arriving as `0.082` is in range, undeclared, and reads as 8.2% - `bounded_signal(0.082, 0.10) = 0.82` [VERIFIED: computed], a near-maximum EV-share term, silently. The only defence is the declared-unit field. If this matters enough to close, the honest close is to make the supplied-unit declaration **mandatory for `ev_share_local` and `equity_gap_index` whenever they are supplied at all** - a refusal the user satisfies with one manifest line.

**Where the conversion record lands is an unmade decision that must be made before code.** The provenance frame has exactly nine columns [VERIFIED: confidence.py:55-56] and **none can hold "what transformation was applied"**. Either write it into `assumption_type`, or add a tenth column to `REQUIRED_COLUMNS`. **Inventing a separate transformation log is not an option** - `score_field` would never see it, and `observation_provenance_rows`' own docstring states the rule: *"Reusing the existing typed-provenance format rather than inventing a parallel one is the point."*

### 3.4 CRS

**Recommendation: take `pyproj` as a core dependency, scoped.** The refusals do the epistemic work; pyproj does the arithmetic. Full dependency assessment in §9.

- **Reproject only from a CRS the user *declared*** - read from a `.prj`, chosen in the mapping step, or taken from a legacy GeoJSON `crs` member. Never from a guess.
- **Three-tier acceptance, not a whitelist.** Vetted list (a controlled vocabulary in `config.py`, in the style of `CAPACITY_BASIS_VALUES`) → transform, record, no flag. Declared but unvetted, and pyproj can construct the transform offline → **transform, record the EPSG code and operation, set `unresolved_flag=1`**. Undeclared, or no transform constructible → refuse the coordinate columns. A hard whitelist would refuse a declared EPSG:2926 that pyproj handles correctly, which is DEC-000's rejected "honest but useless" alternative [VERIFIED: DECISIONS.md:59].
- **Target is `OGC:CRS84`, longitude-then-latitude, with `always_xy=True` stated explicitly.** Not "EPSG:4326" - CRS84 and EPSG:4326 are the same datum with opposite authority axis order, and `build_sites.py:664` already emits `urn:ogc:def:crs:OGC:1.3/CRS84`. Naming the target "EPSG:4326" reintroduces the axis ambiguity 6B exists to eliminate.
- **`accuracy == -1.0` is not a refusal trigger.** I executed `Transformer.from_crs("EPSG:4269","EPSG:4326").accuracy` → **exactly −1.0**, the sentinel for "no accuracy declared", on the single commonest conversion this system will perform. Consult `TransformerGroup(...).transformers[0].accuracy` for the declared figure and record it. `unavailable_operations` non-empty is a **degrade** - record the chosen operation and its accuracy, set `unresolved_flag=1`. Refuse only when no transform can be constructed, or the declared accuracy exceeds a threshold the team writes down once.
- **Coordinates present, CRS not declared → refuse the coordinate columns, not the run.** `lat`/`lon` dropped, `coordinates` group scores `missing` = 0 (weight 0.05 [VERIFIED: confidence.py:49]), map and 3D output suppressed with a stated reason, ledger: *"coordinates were supplied without a stated coordinate reference system, so they were not used."* **Never infer 4326 from the value range** - a geographic CRS on a different datum sits inside ±180/±90 and is undetectable by range check.
- **Bounding-box gate on the output**, keyed to a box the jurisdiction supplies. The existing lon/lat check passes a **lat/lon swap** for Northern Virginia: swapped, lat = −77.35 and lon = 38.68 are both in range, landing the site in the Indian Ocean [VERIFIED: build_sites.py:438-441 is the only coordinate check in the repo]. The gate must emit an `unresolved_flag=1` provenance row; `BuildResult.warnings` may echo it but must not be the only record, or it becomes a quality signal that never reaches the confidence score.

**Two verified facts that make the CRS case concrete.** PWC001 (lat 38.679705, lon −77.352905) in EPSG:2283 is `(11810368.334, 6932629.134)` **US survey feet** [VERIFIED: executed]. Reading those as international feet displaces the site by **7.1996 m east, 4.2261 m north - 8.3483 m planar** [VERIFIED: computed]. And `CRS.from_epsg(2283)` resolves to *"NAD83 / Virginia North (ftUS)"*, US survey foot, with an area of use naming both **Fairfax** and **Prince William** counties [VERIFIED: executed from the bundled PROJ 9.5.1 database, offline]. Magnitude alone cannot separate 3857 from 2283 (8.6e6 vs 1.18e7); sign can, in the western hemisphere. **2283 and 6593 produce byte-identical coordinates**, so the datum *realization* is never recoverable from the numbers - sniffing may propose a projection family, never decide a realization, and whatever it proposes must be labelled "inferred from coordinate magnitude" and carry `unresolved_flag=1`.

### 3.5 IDs

```
source_site_id   the jurisdiction's own key, verbatim, never modified   (required)
site_id          canonical, generated: f"{JUR}{NNN:03d}"                (derived, never ingested)
```

1. The prefix comes from the **manifest**, not the data: `jurisdiction_code` matches `^[A-Z]{3}$`, `jurisdiction_name` matches `^[a-z][a-z0-9_]{1,31}$`.
2. `data/intake/jurisdiction_registry.csv` owns prefixes, seeded from `config.JURISDICTIONS` [VERIFIED: config.py:163 - a constant referenced nowhere in `src/`, `scripts/` or `tests/`; `jurisdiction_for` re-hardcodes the same two prefixes as an if/elif at config.py:175-181].
3. Numbers assigned once, by stable sort of `source_site_id`, never reassigned. `site_id_crosswalk_v1.csv` is read first on every re-ingest.
4. `jurisdiction_for` becomes registry-driven; the `"unknown"` branch becomes a refusal rather than a value that fails contract validation four layers later.

| Collision | Answer |
|---|---|
| Prefix registered to another jurisdiction | **REFUSE**, naming the incumbent and its first-registered date. *Rejected:* auto-suffix `FFXB` - breaks the 3-letter/3-digit shape and produces an ID the user never chose. |
| Two rows share a `source_site_id` | **REFUSE the file**, naming both 1-indexed lines and the value. *Rejected:* keep-first, because `build_confidence` already silently keeps the first of duplicate `(site_id, field_group)` rows [VERIFIED: confidence.py:117-119] and that behaviour is what 6B exists to stop, not imitate. |
| >999 sites in one jurisdiction | **REFUSE at crosswalk-assignment time**, not at contract validation - otherwise a 1,000-site file gets 999 good IDs and one stack trace. |

*Rejected:* hashing `source_site_id` into the numeric slot. With 12 sites in a 1000-slot space the birthday probability of at least one collision is **6.4%** [VERIFIED: recomputed, `1 − Π(1−k/1000), k=0..11 = 0.0638`], and a hash collision merges two sites into one row silently.

**Widening the contract.** `site_id`'s pattern and `jurisdiction`'s enum are NoVA-only [VERIFIED: contract.py:83, :85]. They must be overridden in `build_schema_v2` - which already overrides `horizon_label` and `model_mode` the same way [VERIFIED: contract_v2.py:112-123] - and **never in `build_schema`**, because v1's manifest digest is pinned by `test_v1_manifest_digest_is_pinned` against the module constant `V1_MANIFEST_SHA256` [VERIFIED: tests/test_contract_v2.py:41, :61]. **Consequence: a third-party jurisdiction produces contract v2, never v1.**

---

## 4. The validation stage

**New module `src/fcf_m2/intake_validation.py`.** It imports vocabularies from `observed` and `confidence`; neither imports it. `observed` already imports `confidence` [VERIFIED: observed.py:52], so `intake_validation → observed → confidence` is acyclic.

*Rejected:* putting the checks inside `observed.py`'s readers - those are fail-fast by design (*"a half-ingested capacity file is how a site ends up described as verified on evidence nobody checked"* [VERIFIED: observed.py:219-220]), and fail-fast and accumulate-all are opposite contracts. *Rejected:* extending `confidence.validate_provenance` - `list[str]` cannot carry a line, severity, column or fix hint. *Rejected:* a separate intake pipeline - DEC-000 [VERIFIED: DECISIONS.md:57].

### 4.1 The result object

```python
SEVERITIES = ("blocks_run", "quarantines_row", "degrades_confidence", "noted")

@dataclass(frozen=True)
class Finding:
    code: str; severity: str; dataset: str; file: str
    line: int | None              # 1-BASED FILE LINE, header == 1 (the number Excel shows)
    column: str | None; site_id: str | None
    observed_value: str | None    # verbatim, repr'd, truncated to 120 chars
    what: str; where: str; fix: str
    field_group: str | None       # a key of confidence.FIELD_GROUP_WEIGHTS, or None
    confidence_effect: str | None

@dataclass
class ValidationReport:
    dataset: str; file: str; file_sha256: str
    delimiter: str; encoding: str; line_terminator: str
    rows_read: int; rows_accepted: int; rows_quarantined: int
    sites_seen: list[str]; findings: list[Finding]; fixes: list[Fix]
    checked_at: datetime          # UTC; pass checked_at.DATE() into build_confidence
    schema_version: str = "intake_report_v1"
```

`pandas.iterrows()` gives a 0-based index, so index 0 is file line 2 [VERIFIED: `read_capacity_observations` binds `index` at observed.py:228 and never uses it]. Prose is composed **exactly once**, in `to_text()` - not printed inside the checks, which is what `workflow._ingest_observations` does today.

`checked_at` is a `datetime`; `confidence._staleness_penalty` does `(today - d).days` where `d` is a `date` [VERIFIED: confidence.py:71-75], so passing a `datetime` raises `TypeError`. Pass `report.checked_at.date()`. The point behind it stands: `_staleness_penalty` defaults `today = today or date.today()` [VERIFIED: confidence.py:74] and `workflow` passes no `today` [VERIFIED: workflow.py:147], so **the same input file scores 10 points lower once its `source_date` crosses 730 days.** Intake must pass an explicit `today` and record it in the manifest, or two runs of the same file disagree.

### 4.2 The severity model, and the refuse-versus-degrade boundary

> **Block when the data's MEANING is unknowable. Degrade when the data's COVERAGE is incomplete.**

That is the whole boundary, and it is the one line in this brief that decides the most.

**`blocks_run`** - the value is ambiguous, or the file's shape is unknown. Picking one interpretation is a silent quality improvement, which DEC-000 forbids [VERIFIED: DECISIONS.md:41-45]. This is *not* the rejected "reject anything that does not match the schema exactly" [VERIFIED: DECISIONS.md:59], because **ambiguity is not incompleteness.** `05/04/2026` blocks because May 4 and April 5 are both real dates and the file does not say which. A missing safety column does not block, because "we don't know" is a fact the model can carry.

**`quarantines_row`** - the meaning is clear and clearly wrong. The row is excluded, listed by line, counted, and the exclusion lowers coverage. Escalation to `blocks_run` at `QUARANTINE_ESCALATION_SHARE = 0.20`, carrying `"policy_status": "proposed_default_pending_team_and_client_adoption"` exactly as `TRIGGER_POLICY` does [VERIFIED: config.py:139]. **The 0.20 is a judgment call with no external basis [UNVERIFIED] and must be labelled as a proposal with its own DECISIONS entry.**

**`degrades_confidence`** - absent or weak, not wrong. Missing optional column; no row for a field group; `source_date` older than 730 days; `verification_status = "unreviewed"`. This is DEC-000's *"80% of the fields should get a run and a lower confidence rating"* [VERIFIED: DECISIONS.md:59].

**`noted`** - recorded, zero score effect. CRLF vs LF; BOM; delimiter recorded after the user chose it.

**Two mechanisms move the number. No new score.** (1) **Omit** the provenance row for a group intake could not populate → `SOURCE_CLASS_SCORES["missing"] = 0` by the existing rule [VERIFIED: confidence.py:121-122]. (2) **Weaken** the emitted row (`source_class`, `unresolved_flag`, coverage). *Rejected:* a `validation_penalty` term in `score_field` - a parallel scoring system, which DEC-000 rules out [VERIFIED: DECISIONS.md:69].

### 4.3 Taxonomy and message templates

Message contract, enforced by test: **WHAT** (quotes the value verbatim), **WHERE** (file, Excel line, column), **FIX** (imperative, with a concrete good value). No exception class names, no `Traceback`, no `NaN`, no `dtype`.

**Structural.** `STR01` missing required column (`blocks_run` if required / `degrades_confidence` if optional) · `STR02` unrecognised column (`noted`) · `STR03` duplicate column name (`blocks_run`) · `STR04` duplicate key (`quarantines_row`) · `STR05` no data rows (`blocks_run`) · `STR06` ragged row (`quarantines_row`).

**Type.** `TYP01` text where a number is required (`quarantines_row`) · `TYP02` thousands separator (**proposal, see below**) · `TYP03` ambiguous date (`blocks_run`) · `TYP04` Excel serial date (`blocks_run`) · `TYP05` unit inside a number (`quarantines_row`) · `TYP06` yes/no column with unexpected text (`degrades_confidence`).

**Range.** `RNG01` ratio outside domain · `RNG02` negative where non-negative required · `RNG03` magnitude implausible for stated unit (`degrades_confidence`, and it says in its own message that it is a heuristic) · `RNG04` zero where positive required.

**Semantic.** `SEM01` observation dated in the future · `SEM02` capacity below known base load (`degrades_confidence`) · `SEM03` energy inconsistent with sessions (`degrades_confidence`) · `SEM04` observation older than the staleness threshold (`degrades_confidence`).

**Referential.** `REF01` unknown site_id (`quarantines_row`; the suggestion comes from `difflib.get_close_matches`, which is Ratcliff/Obershelp similarity, **not** an edit distance - saying "Levenshtein" would justify adding a package the stdlib makes unnecessary) · `REF02` site present but unobserved (`degrades_confidence`) · `REF03` site_id outside the ID convention (**see below**) · `REF04` reserved `SYN`/`EXAMPLE` prefix in a live run (`blocks_run`).

**Format.** `FMT01` delimiter is not a comma (`blocks_run`, offered as a proposed `Fix`) · `FMT02` BOM (`noted`, auto-stripped) · `FMT03` CRLF (`noted`) · `FMT04` mojibake (`degrades_confidence`) · `FMT05` not valid UTF-8 (`blocks_run` - guessing the encoding transforms every text value in the file) · `FMT06` invisible whitespace in a key (`noted`, auto-trimmed).

**Attribution.** `ATT01` unattributed observation (`quarantines_row`) · `ATT02` unknown method (`quarantines_row`).

#### Before / after - three real cases

**TYP01, from the current behaviour.** A capacity file with `service_capacity_kw = "N/A"` for PWC004 today produces:

> `PWC004: observation carries neither service_capacity_kw nor spare_capacity_kw, so there is nothing to confirm.`

The user's file **does** carry a capacity column with content in it. pandas maps `N/A` to NaN by default; `_optional_float` returns `None` [VERIFIED: observed.py:201-205]; the refusal at observed.py:131-134 then blames the wrong thing. After:

```
WHAT   service_capacity_kw reads "N/A" for PWC004. That is text, not a kW value, so the
       model cannot tell whether the capacity is unknown or zero.
WHERE  capacity_returns.csv, line 6, column service_capacity_kw.
FIX    Write a number if you have one: 400. If the service capacity is genuinely unknown,
       leave this cell empty AND put a number in spare_capacity_kw - an observation with
       both capacity columns empty is refused, because there is nothing in it to confirm.
```

The conditional in that FIX is load-bearing. An unconditional "leave it empty" produces the exact refusal the finding exists to prevent.

**FMT01, from the current behaviour.** A semicolon-delimited file: `pd.read_csv` returns one column named `'site_id;observed_date;...;notes'` and `read_capacity_observations` reports **all eleven** columns missing [VERIFIED: observed.py:222-225 is a bare `pd.read_csv(path)` followed by the presence check]. This is the identical failure the program already diagnosed once in MATLAB and prescribed a fix for - state the delimiter, the header line and the data-line range explicitly. **That prescription has never been applied to the Python side.** After: count candidate delimiters **on the header line only**, never on a data row; never treat whitespace as a candidate; reject `csv.Sniffer` because it cannot express "I am not sure"; offer the switch as a `Fix` with `status="proposed"`.

**SEM04, and the arithmetic that must be right.** A stale panel schedule:

```
WHAT   The panel schedule for FFX004 is dated 2023-02-11, which is 3.4 years old. The
       confidence rubric applies a 10-point staleness penalty beyond 2 years.
WHERE  capacity_returns.csv, line 7, column observed_date.
FIX    Nothing is wrong with this record and it is being used. If a newer panel schedule
       exists, submitting it raises this site's electrical_service score from 95 to 100
       (the raw 105 is capped) - that is 1.25 points of overall confidence.
```

Trace: `verified_facility` 100 + `reviewed` 5 − stale 10 = **95**; fresh gives 105, **capped to 100** at confidence.py:83. Realised gain is 5 group points × weight 0.25 = **1.25** overall. Multiplying the uncapped 10-point penalty by the weight gives 2.5 and promises the user twice the benefit that exists. Every number in every message template must be traced through the cap.

### 4.4 Two things this stage must resolve before code

**(a) One parse of the bytes, not two.** Intake reads with explicit `sep=`, `encoding="utf-8-sig"`, `keep_default_na=False, na_values=[]` so `"N/A"` arrives as the literal string it is. `observed.py`'s readers are bare `pd.read_csv(path)` with pandas' default NA list [VERIFIED: observed.py:222, :247]. **Two parses of the same bytes with different NA and delimiter semantics is precisely the divergence DEC-000 rejects.** Pick one: either `read_capacity_observations` / `read_session_observations` gain `sep`, `encoding` and NA parameters that intake feeds from the `ValidationReport`, or those functions become thin wrappers over intake. Until this is decided, any claim that the CLI's `except ObservationError` is unreachable is false.

**(b) `REF03` cannot ship as `blocks_run` in a portability phase.** The facts are right - `jurisdiction_for` returns `"unknown"` for any non-FFX/PWC prefix, and the contract pins the pattern and the enum. But as a `blocks_run` rule it refuses **every dataset from every jurisdiction 6B exists to accept.** It must ship paired, in the same ticket, with the registry-driven prefix source of §3.5.

### 4.5 Required extensions to `observed.py`

None of these changes a refusal.

1. Wrap `_optional_float` and `_as_date` so they raise `ObservationError` naming the column and row, not a bare `ValueError` that `workflow`'s narrower `except` cannot catch.
2. Add the row number to every constructor message - `read_capacity_observations` already binds `index` and discards it [VERIFIED: observed.py:228]; pass `line = index + 2`.
3. Split `SESSION_COLUMNS` into **8 required / 5 optional**. Five have defaults in the dataclass - `facility_visitors_day` (`None`), `sessions_delayed` (`0`), `wait_p90_min` (`None`), `observer` (`""`), `source_system` (`""`) - but the reader blocks on all 13 equally [VERIFIED: observed.py:157-169 vs :248-254]. The five defaulted ones belong in `missing_for_triggers`, not in a whole-file refusal.
4. Give both readers explicit `sep`, `encoding` and NA parameters (per 4.4a).
5. Fix `ATT01`'s message logic: the check is `if not source_document.strip() or not observer.strip()` - an **OR** [VERIFIED: observed.py:123] - but the message says "no source_document **and** observer", which sends a user with a document hunting for one they already supplied.

---

## 5. Completeness → confidence

**No parallel score.** DEC-000: *"Requirement 6B.4 routes completeness into this rather than inventing a parallel score"* [VERIFIED: DECISIONS.md:69]. Adding a new `field_group` is not an option: the seven weights are hard-coded, sum to exactly 1.00 with no runtime normalisation [VERIFIED: confidence.py:45-53; executed: `sum(...) == 1.0`], so an eighth group silently re-weights all 12 existing sites off the pinned 33.8 baseline, and `validate_provenance` refuses unknown group names outright [VERIFIED: confidence.py:95-97].

### 5.1 Field → group membership

This map **does not exist anywhere in the repo.** `build_field_provenance.py` picks a `source_class` per group by inspecting one or two representative columns - electrical is `unconfirmed` iff `elec_service_rating_amp <= 0 or spare_capacity_kw <= 0` [VERIFIED: build_field_provenance.py:52-56] - and hard-codes the other four classes [VERIFIED: :68-71]. That shortcut is the hole in §5.3.

| field_group (weight) | Members from the 40-column site file |
|---|---|
| `electrical_service` (0.25) | `elec_service_voltage`, `elec_service_rating_amp`, `spare_capacity_kw`, `distance_to_service_ft`, `trenching_ft`, `trench_cost_per_ft`, `service_upgrade_cost_usd`, `battery_storage_flag`, `battery_storage_kwh`, + new: `electrical_risk_level`, `base_load_mean_kw`, `base_load_peak_kw` |
| `site_use_and_demand` (0.20) | `employees_day`, `visitors_day`, `fleet_vehicles`, `hours_open`, `avg_dwell_min`, `aadt_nearest`, `ev_registrations_local`, `ev_share_local`, `existing_l2_ports_1mi`, `existing_dcfc_ports_3mi`, + new: `arrival_start_hr`, `arrival_end_hr` |
| `address_and_public_access` (0.10) | `address`, `city`, `state`, `zip`, `public_access` |
| `coordinates` (0.05) | `lat`, `lon` (+ the **manifest key** `coordinate_reference_system`, whose absence is what demotes this group - it is not a column) |
| `parking_and_layout` (0.15) | `parking_spaces`, `ada_layout_possible`, `garage_enclosed` |
| `safety_review_fields` (0.15) | `fire_access_ok`, `emergency_disconnect_visible`, `stormwater_risk` |
| `equity_and_context` (0.10) | `nearby_households_1mi`, `nearby_jobs_1mi`, `amenities_count_0_5mi`, `equity_gap_index` |

The site file has exactly 40 columns [VERIFIED: header read and enumerated]. Thirty-six carry a group; four (`site_id`, `site_name`, `site_type`, `notes`) are identity or free text. Five fields above are **new columns 6B proposes**, not part of the 40. **Every input field must declare a group** - a field with no home means its absence routes into nothing, which is the parallel-path failure in miniature.

The *assignment* of each column to a group is design judgment [UNVERIFIED as a correctness claim]; only `equity_gap_index`, `spare_capacity_kw`, `emergency_disconnect_visible`, `visitors_day` and `employees_day` have their group implied by existing code [VERIFIED: build_field_provenance.py:52-71]. Since a change to this map changes `data_confidence_level_v3` for an unchanged file, **every future change to it is a MAJOR input-schema bump.**

### 5.2 The four levers

1. **Group entirely unsupplied → emit no provenance row.** Existing behaviour scores it `missing` = 0 [VERIFIED: confidence.py:121-122]. **This is NOT zero code change.** The pipeline never reaches confidence: `scoring.enrich_and_score` raises `KeyError` on the missing column first [VERIFIED: executed]. A file omitting all three safety columns - the exact §5.3 demonstration - crashes before any confidence is computed. **That is a REFUSE where DEC-000 mandates a DEGRADE.** Closing it requires the `input_schema.materialise` reindex step of §2, which is 6B work, not free.
2. **`source_class` reflects what intake actually did**, not what the file claimed: derived at the site's own geography → `derived_public_data` (55); borrowed from a larger area or assumed → `planning_assumption` (35); substituted from a code default → `synthetic_model` (30). All three keys already exist [VERIFIED: confidence.py:28-30]. Zero code change.
3. **`unresolved_flag=1`** for any group containing a substituted default → −15 [VERIFIED: confidence.py:82]. Zero code change to `confidence.py`. Note the substitution inventory is **27 fields**, not one - every `NUMERIC_FIELDS` entry and every `YES_NO_FIELDS` entry gets a silent 0 [VERIFIED: scoring.py:181-184].
4. **NEW - a `field_coverage` column**, the fraction of a group's members the dataset actually supplied, applied multiplicatively inside `score_field`.

**Two rules the levers require, both currently unspecified.**

- **A field group takes the `source_class` of its weakest contributing source, and its `unresolved_flag` is 1 if any contributor is unresolved.** Without this, several defaulted columns inside one group collapse into a single provenance row by `.iloc[0]`, i.e. **by row order** - the defaults writer becomes non-deterministic and the gate test unpinnable.
- **`field_coverage` must travel with the *names* of the absent members**, not just the fraction. `0.778` plus a reason naming no field passes every check while recording nothing - a transformation applied without being surfaced.

**Ordering defect in lever 4, which blocks it.** Multiplying *after* subtracting `unresolved` scales the penalty down as coverage falls: `(95 − 15) × 0.8 = 64.00`, i.e. the −15 becomes an effective −12. A penalty that shrinks as the data gets sparser is backwards. The alternative `(base + adj − stale) × coverage − unresolved` gives `95 × 0.8 − 15 = 61.00` [VERIFIED: both computed]. **Do not ship lever 4 without picking one and writing down why.**

*Rejected:* an additive penalty `− K × (1 − coverage)` - with a constant `K`, a 40%-covered `verified_utility` group and a 40%-covered `planning_assumption` group lose the same absolute points, which mis-ranks them, and `K` becomes a tunable nobody can defend. Multiplicative needs no constant and has the correct limit: `coverage → 0` gives `score → 0`, identically `SOURCE_CLASS_SCORES["missing"]`.

**Two required changes to `confidence.py` beyond the multiply:**

- `field_coverage` is an **optional 10th column**, defaulting to 1.0. It must **not** join `REQUIRED_COLUMNS`, or all 84 existing provenance rows fail `validate_provenance` [VERIFIED: confidence.py:88-91].
- **`validate_provenance` must reject duplicate `(site_id, field_group)` pairs by name.** Today they are silently collapsed to the first [VERIFIED: confidence.py:117-119]. §3.5 condemns exactly that behaviour in the ID rules; the design cannot condemn it there and depend on it here. 6B is the first producer that could emit duplicates at scale.

**Backward compatibility:** with `field_coverage` absent the default is 1.0, all 84 existing rows produce byte-identical output, and all 12 sites still score 33.8 / Low with the identical breakdown [VERIFIED: executed with `today=date(2026,7,27)`].

### 5.3 The hole this closes, with numbers

A third-party file supplying **14 of 36 fields (38.9%)**, every supplied field `official_gis` + `reviewed` + fresh date:

| field_group | supplied/total | today | with coverage |
|---|---|---|---|
| electrical_service | 1/9 | 95.0 | 10.56 |
| site_use_and_demand | 3/10 | 95.0 | 28.50 |
| address_and_public_access | 5/5 | 95.0 | 95.00 |
| coordinates | 2/2 | 95.0 | 95.00 |
| parking_and_layout | 1/3 | 95.0 | 31.67 |
| safety_review_fields | 0/3 | 0.0 | 0.00 |
| equity_and_context | 2/4 | 95.0 | 47.50 |

**Today: 80.75 → High. With the coverage factor: 32.09 → Low.** [VERIFIED: both recomputed - `95 × 0.85 = 80.75`; `2.639 + 5.7 + 9.5 + 4.75 + 4.75 + 0 + 4.75 = 32.089`.] A 38.9%-complete dataset rates *High* today. That is the hole, and it is currently masked rather than absent: the shipped provenance builder writes `unconfirmed` for electrical on all 12 sites, so no real site sits near the boundary [VERIFIED: executed groupby].

### 5.4 Worked example - a well-sourced file with four gaps

Missing: `elec_service_voltage`, `battery_storage_kwh`, `ev_registrations_local` (all three genuinely optional - **zero references in `src/` or `scripts/`** [VERIFIED: grep]) and `hours_open`, which is required-but-substitutable (defaulted to 8 [VERIFIED: right_sizing.py:56]). A substituted default does **not** count toward coverage **and** sets `unresolved_flag=1`; a plain absence only reduces coverage. Substitution is strictly worse than absence, because a defaulted value flows into arithmetic while an absent one is visibly absent.

Per-group score `= (90 + 5 − 0 − unresolved) × coverage`:

| group | coverage | unresolved | score | weight | contribution |
|---|---|---|---|---|---|
| electrical_service | 7/9 = 0.778 | 0 | **73.89** | 0.25 | 18.472 |
| site_use_and_demand | 8/10 = 0.800 | 1 (−15) | **64.00** | 0.20 | 12.800 |
| address_and_public_access | 5/5 | 0 | 95.00 | 0.10 | 9.500 |
| coordinates | 2/2 | 0 | 95.00 | 0.05 | 4.750 |
| parking_and_layout | 3/3 | 0 | 95.00 | 0.15 | 14.250 |
| safety_review_fields | 3/3 | 0 | 95.00 | 0.15 | 14.250 |
| equity_and_context | 4/4 | 0 | 95.00 | 0.10 | 9.500 |

**Total = 83.52 → High** [VERIFIED: computed]. The same file under today's code scores **95.0 → High**. The mechanism grades rather than cliffs: an 89%-complete, well-sourced dataset gets a run and a *lower* rating, which is exactly what DEC-000 demands.

### 5.5 The reason strings

Composed per `(site_id, field_group)` into the existing `assumption_type` column, then joined per site with `"; "` into the `confidence_reasons` dict `migrate_v1_to_v2` already accepts [VERIFIED: contract_v2.py:160-161, :184-186]. Emit a clause for every group whose score was reduced; nothing for groups at full potential.

**Rule: name the field, name what happened to it, name what the model used instead.**

1. `"site_use_and_demand: hours_open was not supplied; provenance records the substituted default of 8 operating hours from right_sizing.ports_for_sessions, so this site's port count rests on an assumed operating day."`
2. `"electrical_service: no measured spare_capacity_kw or elec_service_rating_amp was supplied; provenance keeps capacity_basis at placeholder and no feasibility claim is emitted for this site."`
3. `"site_use_and_demand: ev_share_local was not supplied; provenance records that scoring coerced it to 0 at scoring.py:183-184, so this site's EV-uptake demand term contributes nothing rather than an estimate."`
4. `"safety_review_fields: the file supplied none of fire_access_ok, emergency_disconnect_visible, stormwater_risk, so provenance scores this group 0 as missing rather than passing a screening nobody performed."`
5. `"coordinates: lat/lon arrived as projected easting/northing and were reprojected to CRS84; the reprojection is exact but the source dataset declares no positional accuracy, so provenance keeps coordinates at public_web_reference."`

**Anti-example the design must reject:** `"some data missing"` - no field, no substitute, no consequence, and it satisfies `minLength: 20`. Length is not the guard.

**Two blocking constraints on these strings, both verified.**

- `tests/test_contract_v2.py:216-220` asserts every reason has `str.len().min() > 30` **and** `reasons.str.contains("provenance").all()`. **Every clause above therefore contains the literal word "provenance"** - that is why, and it is not stylistic. Either every emitted reason names the provenance basis literally, or that assertion is deliberately amended with a recorded rationale. This is a decision, not something to discover in CI.
- `validate_provenance` does not constrain `assumption_type` at all [VERIFIED: confidence.py:86-98]. **The only guard against the anti-example is a unit test asserting every emitted reason names at least one column from the membership map.** Write it.

**A second sink exists and 6B must state whether it fixes it.** `data_confidence_reason` also travels: fixture site_results → `src/fcf3d/build_sites.py:523` → `explorer/web/data/sites.geojson` → rendered at `explorer/web/app.js:740`, currently carrying the breakdown table recited verbatim (`"electrical_service=0.0; site_use_and_demand=55.0; ..."`). **That is the anti-example, already live in the product.** Fixing only `migrate_v1_to_v2` leaves the recitation on screen.

**Contract v2's two always-required added fields must be filled.** `data_confidence_reason` is `minLength: 20` and `trigger_outcome` is `minLength: 4`, both always required [VERIFIED: contract_v2.py:140-141]. Since §3.5 forces every intake jurisdiction onto v2, an intake run with no observations must emit `contract_v2.UNOBSERVED_STATUS` for `trigger_outcome` [VERIFIED: contract_v2.py:88] and a reason generated from the intake ledger. Without this, **every intake run fails JSON Schema validation on its first write.**

---

## 6. Documented fallbacks

**Read this section as a to-verify list, not a usable table.** I did not open a single external publisher page in this session. Everything below marked `[UNVERIFIED]` is prior knowledge or a prior lane's search summary, and **a search summary is not an opened page.** No source string in this section may be written into a `source_org` field, a provenance row, or a user-facing citation until someone opens the publisher's page and confirms the dataset name, edition, resolution, vintage and redistribution terms.

### 6.1 The shape every default must carry

Copy the naming shape the project already uses for its one properly-provenanced constant [VERIFIED: config.py:105-108 - `GRID_FACTOR_LB_PER_MWH` / `_SOURCE` / `_VINTAGE` / `_NEXT_REFRESH`, surfaced as five keys in `assumptions.json`], plus one addition:

`*_value`, `*_units`, `*_source`, `*_vintage` (human), **`*_vintage_iso_date` (`YYYY-MM-DD`)**, `*_next_refresh`, `*_status = "national_default_not_user_data"`.

The ISO date is not decoration. `_staleness_penalty` does `datetime.fromisoformat(str(source_date))` and returns the full 10-point penalty on any `ValueError` [VERIFIED: confidence.py:67-75], so a prose vintage like `"SVI 2022"` gets scored stale **by accident rather than by rule**.

**Write the block into the run's own `assumptions.json` under `data/outputs/<run_id>/`, never into `data/contract/v1/assumptions.json`.** v1's manifest digest is pinned [VERIFIED: tests/test_contract_v2.py:41, :61] and editing it fails the suite, which fails `scripts/verify.sh`.

### 6.2 The catalog

| Target field | Proposed default | Status | What must be checked before it can ship |
|---|---|---|---|
| `equity_gap_index` | CDC/ATSDR Social Vulnerability Index, `RPL_THEMES` | **[UNVERIFIED]** | Publisher, exact dataset name, current edition, geographic resolution, release date, redistribution licence. **The mechanical fit is VERIFIED**: `equity_gap_index` is documented "index is already 0-1 constructed" [VERIFIED: `data/anchors/anchor_set_v1.json`] and `equity_index_percentile_min = 0.60` is literally a percentile [VERIFIED: config.py:146] - so no rescale is needed *if* the source is what it is believed to be. |
| - | CEJST, EPA EJScreen | **REJECTED** | Rejected on reasoning that does not depend on unverified dates: a default whose canonical citation is a third-party mirror cannot be the source line printed next to a number. |
| Grid emissions | **Reuse `config.GRID_FACTOR_*`; do not replace** | **VERIFIED in-repo** [config.py:105-108] | The portability limitation is real: the subregion `SRVC` is hard-coded. A ZIP/coordinate→subregion crosswalk is **[UNVERIFIED]**. Honest coarser fallback: a state rate, labelled `resolution = "state"`. |
| `ev_share_local` | AFDC / FHWA registration counts | **[UNVERIFIED]** and **probably should not ship at all** | Two problems. (1) Redistribution terms unknown. **If they do not clearly permit redistributing derived counts, there is no default** - the field stays missing and confidence falls. Do not ship a fetch script instead: `scripts/verify.sh` runs pytest and local workflow commands with no network assumption [VERIFIED: read], so a fetch-at-need default is either a CI that needs network or a repo where the numbers are not reproducible from a clean checkout. (2) Even if terms permit it, a **state** broadcast is not an upgrade over the project's existing documented locality proxy - it is a lateral move with a better-sounding publisher. |
| `aadt_nearest` | **No default** | **VERIFIED as a decision** | Leave missing, let confidence fall. This is the catalog's best entry. |
| `nearby_households_1mi` | ACS **B11001** + TIGER centroid-in-buffer | Table number **VERIFIED in-repo** (the project's own site notes record this method); the Census-side table title is **[UNVERIFIED]** | Confirm the table's official title and current vintage. TIGER/Line 2024 is already cached in-repo with attribution [VERIFIED: `data/cache/boundaries/tl_2024_va_counties.geojson`, `gis_offline.py:29`], so the vendoring precedent is real. |
| `nearby_jobs_1mi` | LODES WAC | **[UNVERIFIED]** externally; **VERIFIED in-repo** that LODES already feeds this field [build_field_provenance.py:66] | Confirm current release, vintage, block geography. |
| Electricity price | EIA *Electric Power Monthly* | **[UNVERIFIED]** | Replaces a value the project itself labels a placeholder [VERIFIED: config.py:121 - `"tariff_usd_per_kwh": 0.11, # placeholder commercial energy rate; Dominion tariff TBV`]. Confirm table identity and update cadence. |
| Demand charge | **Stays 0.0, explicitly "not modeled"** | **VERIFIED in-repo** [config.py:122] | Nothing. This is a correct refusal and must not be "improved". |

### 6.3 The scoring rule for any default

**A default is `derived_public_data` (55) only if it was computed at the site's own geography. A value borrowed from any larger area is `planning_assumption` (35) with `unresolved_flag = 1`.** Consequences under `score_field`:

- site-geography default, fresh: `55 − 5 = 50`
- site-geography default, stale: `55 − 5 − 10 = 40`
- borrowed-geography default, fresh: `35 − 5 − 15 = 15`
- borrowed-geography default, stale: `35 − 5 − 10 − 15 = 5`

**A site whose every group is defaulted tops out at 50 - Medium at best, never High** [VERIFIED: `level_for` needs ≥75; weights sum to 1.00].

**Do not assert "a site with unverified electrical cannot reach High."** It is arithmetically false: the remaining 0.75 of weight maxes at 100 (capped at confidence.py:83), so `0.75 × 100 = 75.0` and `level_for(75.0)` returns **"High"** [VERIFIED: confidence.py:60-61]. Assert the numeric bound instead.

**One guard.** Scoring an intake site's `coordinates` at `official_gis` (90) puts it *above* the native cohort, which sits at `public_web_reference` (60) for every site [VERIFIED: executed - every breakdown reads `coordinates=60.0`]. Rating a bring-your-own-data site higher than the project's own on the strength of a reprojection is cleaning that improves quality. **`official_gis` only when the county's GIS is the stated publisher AND the EPSG is declared by that publisher. Any inferred EPSG → `planning_assumption` + `unresolved_flag=1`.**

---

## 7. Template and worked example

### 7.1 `intake_sites_template.csv` - the blank

Two files, both new, both tracked under `data/intake/`.

**Columns:** the 27 hard-required (`YES_NO_FIELDS` 7 + `NUMERIC_FIELDS` 20 [VERIFIED: counted at scoring.py:83-95]), plus `source_site_id`, `site_name`, `site_type`, the four operating-profile fields, `lat`, `lon`, `address`, `city`, `state`, `zip`, `electrical_risk_level`, `notes`.

**Excluded:** the two derived fields [VERIFIED: scoring.py:189-190], and the three dead-in-code fields `ev_registrations_local`, `elec_service_voltage`, `battery_storage_kwh` - **zero references in `src/` or `scripts/`** [VERIFIED: grep]. Note the exclusion is safe for a narrower reason than "unreferenced": all three appear as pass-through columns in the golden output fixtures, and `test_legacy_golden.py` compares named columns, not column sets [VERIFIED: read].

**One template row**, matching the existing convention exactly [VERIFIED: `data/observed/observed_capacity_template.csv` row 2 reads *"TEMPLATE ROW - illustrative only. Delete before entering real data. site_id EXAMPLE001 is not a project site."*, and `tests/test_observed.py:56-62` asserts exactly one row starting with `EXAMPLE`].

### 7.2 `intake_sites_template.dictionary.csv` - the sidecar

Columns: `column, canonical_unit, accepted_units, accepted_range, required_class, field_group, what_it_means, what_happens_if_missing`.

**It must carry the denominator, not just the unit.** Proof from the existing cohort: `hours_open` **already mixes two units inside the 12 published sites** - 24 for the PWC002 commuter garage versus 7.29–9.29 for libraries, where the library values are weekly-average daily hours. A dictionary that says "hours" and nothing else cannot express that.

`what_happens_if_missing` must state, in one sentence per column, that the scoring engine substitutes 0 and what that does to the score. **Intake fixes the provenance, not the arithmetic** (§8).

*Rejected:* `#` comment lines in the CSV (they break every naive reader). *Rejected:* JSON Schema as the user-facing artifact (a county facilities analyst opens a spreadsheet, not a schema).

### 7.3 The messy Gate 6B fixture

`data/intake/fixtures/ASHCROFT_COUNTY_MESSY.csv` - an invented county, 12 rows, with a sibling README.

**Marker string.** The existing test asserts **two** literals - `"SYNTHETIC"` and `"Not an observation of any real facility"` [VERIFIED: tests/test_observed.py:53-54]. The fixture's marker must satisfy both if the equivalent test is written the same way:

> `SYNTHETIC FIXTURE - fabricated for testing. Ashcroft County is not a real county. Not an observation of any real facility.`

**Key column.** The raw keys must themselves be `SYN`-prefixed (`SYN-1041`, …). The existing guardrail reads a column literally named `site_id` [VERIFIED: tests/test_observed.py:45], which the messy fixture does not have - so a copy-pasted guardrail would **pass by not looking**. The new test must key on the fixture's declared id column.

**The defects, and what each proves:**

| # | Defect | Expected behaviour |
|---|---|---|
| D1 | Headers are `FAC_NO, FACILITY, SVC_AMPS, X_COORD, Y_COORD, ANN_VISITS, HRS_WK, …` | Mapping proposed, shown, applied only on acceptance |
| D2 | Coordinates in a projected CRS, EPSG declared in a sidecar `.prj` | Reprojected to CRS84, ledger line per site, operation + accuracy recorded |
| D2b | **Second variant, `..._MESSY_NO_CRS.csv`:** same coordinates, no CRS anywhere | **Degrades, does not refuse.** 12 sites scored, `coordinates` = 0 by the existing missing-group rule, map and 3D output suppressed with a stated reason, non-zero exit. Refusing the whole file is DEC-000's explicitly rejected alternative, and coordinates are weight 0.05 and unused by scoring. |
| D3 | `SVC_AMPS` contains `"400A"` and `"1,200"` | Quarantined with the value quoted. Today both become `0.0` silently [VERIFIED: scoring.py:183-184] |
| D4 | Trench lengths in metres, declared | Converted ×3.280839895, ledger names both units and the factor and **which foot** |
| D5 | A transformer nameplate in **kVA** offered as `spare_capacity_kw` | **REFUSED as a mapping.** Power factor is not in the file. `CAPACITY_METHOD_PRECEDENCE` contains no nameplate method [VERIFIED: observed.py:58-65]. This is the fixture's best moment. |
| D6 | `SVC_AMPS <= 0` at three sites | Routes into the existing rule → `electrical_service` = `unconfirmed` + `unresolved_flag=1` [VERIFIED: build_field_provenance.py:52-56] |
| D7 | `ADA_OK` reads `"Pending survey"` | Degrades. Today `yesno_to_num` returns `0.0` silently [VERIFIED: scoring.py:104-110] |
| D9 | `HRS_WK = 168` | Confirmation required for the `/7` divisor. Today `.clip(upper=24)` makes it 24 silently [VERIFIED: scoring.py:197] |
| D10 | Equity column with inverted polarity | **REFUSED.** Polarity is not derivable from the file. |
| D11 | Two rows share `FAC_NO SYN-1041`, disagreeing on `ANN_VISITS` (48300 vs 51200) | **Keep the site with the conservative 48300**, record the conflict string, `unresolved_flag=1` on `site_use_and_demand`, **exit 3.** This mirrors `resolve_capacity`, which selects `min(...)`, appends `" | CONFLICT, unresolved: … | conservative value used for screening"` and returns the site [VERIFIED: observed.py:390-403] - it never excludes. |
| D12 | `ANN_VISITS / 365` to reach `visitors_day` | Confirmation required, same as D9. The file does not state operating days, and the cohort's `visitors_day` values are per-**open**-day, so `/365` silently redefines a column that is a regressor in the demand model [VERIFIED: demand.py `X_cols` includes `visitors_day`]. |
| D13 | A clean, correct column | **Negative control.** Must produce no finding. |
| D14 | A file the validator should accept unchanged | **Negative control.** Must produce an empty findings list. |

**The expected confidence.** Do **not** pin a scalar. Pin these properties and this ordering:

- The fixture's score is **strictly below 33.75**, the live NoVA cohort's score [VERIFIED: executed - all 12 sites 33.8, `33.75` before rounding].
- `electrical_service = 0.0` and `safety_review_fields = 0.0`, matching the two zeros in the live baseline for the same reason (`unconfirmed` + `unresolved_flag=1`) [VERIFIED: executed groupby].
- No group fed only by borrowed-geography defaults exceeds 15; no group fed only by site-geography defaults exceeds 50; a site whose `electrical_service` scores 0 cannot exceed **75.0**.
- Every group score decomposes in `confidence_breakdown` [VERIFIED: confidence.py:123, :129].

**The test must pass `today=date(2026, 7, 27)` explicitly.** `_staleness_penalty` defaults to `date.today()` [VERIFIED: confidence.py:74] and `workflow` passes nothing [VERIFIED: workflow.py:147], so an unpinned test changes its answer as the wall clock moves.

---

## 8. What this does NOT do

1. **Intake fixes the provenance, not the arithmetic.** A missing `SVC_AMPS` is recorded as missing and lowers confidence - and then `run_scoring` still does `.fillna(0)` on it [VERIFIED: scoring.py:183-184] and `yesno_to_num(NaN) → 0.0` on all seven flags [VERIFIED: scoring.py:104-106]. A missing `ada_layout_possible` still *scores* as "ADA not possible". Making missing ≠ zero in the arithmetic is a `scoring.py` change with its own decision entry, not part of 6B as scoped.
2. **Absence still improves two numbers.** `garage_enclosed` and `stormwater_risk` are inverted drivers, so `.fillna(0)` yields the *best* value [VERIFIED: scoring.py:78-81]. Coverage lowers confidence; it does nothing to stop `readiness_score` from rising. Unless §2.3's UNRESOLVED item is decided in favour of resolution (b), this brief ships a known silent improvement of up to 2.25 readiness points.
3. **A new jurisdiction is scored against Northern Virginia's anchors.** All 12 `NORMALIZE_COLS` are anchored, so `anchor_fallback_fields` is empty and nothing warns [VERIFIED: executed]. A jurisdiction whose trenching distances or households genuinely differ is normalised against NoVA's benchmark. 6B records `anchor_set_version` in the manifest so the output *says* which yardstick was used. It does not produce a portable anchor set.
4. **RT-04 will fail for every non-NoVA cohort.** `validate_scenario_table` hard-codes baseline starter `== 25` and pathway `== 48`, with `expect_legacy_totals: bool = True`, and both `contract.write_contract` and `contract_v2.validate_v2` call it with no kwargs [VERIFIED: contract.py:139-140, :193-201, :275; contract_v2.py:265]. This must be driven off an explicit run-level flag defaulting True only on the frozen v1 path. **Do not** drive it off "is the jurisdiction set exactly {FFX, PWC}" - that silently disables the check for a genuine NoVA run that gains a third jurisdiction.
5. **`workflow` has no V4 mode.** `choices=[MODE_LEGACY, MODE_V3]` [VERIFIED: workflow.py:435] despite `config.MODE_V4` existing [VERIFIED: config.py:38] and `build_schema_v2` already admitting it [VERIFIED: contract_v2.py:121-123]. Intake needs a mode and a `--input-manifest` argument.
6. **`validate_v2` has a production consumer.** It is called at `workflow.py:477` inside the shipped `validate-contract` command, and `migrate_v1_to_v2`, `apply_observations` and `write_contract_v2` are all called at `scripts/build_contract_v2.py:76, :78, :99` [VERIFIED: grep]. **`contract_v2` is fully wired.** Changing any of those signatures changes shipped behaviour. Any plan that assumed otherwise needs revisiting.
7. **Only `electrical_service` has a package-level provenance producer.** `observation_provenance_rows` hard-codes that group [VERIFIED: observed.py:422-447]. The other six - **75% of the confidence weight** - are produced only by `scripts/build_field_provenance.py`, which hard-codes this project's derivation rules and `SOURCE_DATE = "2026-06-24"`. **DEC-000's gate cannot be fully met until that script is promoted into a jurisdiction-agnostic package function.** That work must be in scope, or the gate is met for one group and the brief must say so.
8. **`engineering_estimate` and `planning_proxy` still score 90.** Neither is a key of `SOURCE_CLASS_SCORES`, so `observation_provenance_rows` rewrites both to `official_source` [VERIFIED: observed.py:430-433]. A comparable-site proxy outranks `derived_public_data` (55). Not 6B's to fix, but 6B must not build on it.
9. **The percent-inside-0-to-1 unit trap stays open** unless the declared-unit field is made mandatory for `ev_share_local` and `equity_gap_index` (§3.3).
10. **Two files in `data/` are CRLF, not one.** `field_provenance_v1.csv` (85 CRLF) and `legacy_matlab_site_meta.csv` (13) [VERIFIED: executed byte count over `data/**/*.csv`]. `build_field_provenance.py:74` opens with `newline=""` and hands `csv.DictWriter` no `lineterminator`, so it defaults to CRLF. Every file 6B writes must pin `lineterminator="\n"`, and that writer should be fixed in the same pass - a findings CSV digested into the run manifest would inherit the same defect.
11. **No external data source in §6 has been verified.** Nothing there is usable until someone opens the publisher's page.

---

## 9. Decisions and rejected alternatives

| ID | Decision | Rejected | Why the rejected option loses |
|---|---|---|---|
| **6B-D1** | Take **`pyproj` as a CORE dependency**, pinned in `requirements-lock.txt` alongside a `certifi` pin | An optional `intake` extra | The DEC-000 acceptance gate is a CI gate, and CI installs `-e .[test] -c requirements-lock.txt` [VERIFIED: .github/workflows/tests.yml:34]. **An extra CI does not install cannot gate anything.** A constraints file does not force installation, so both packages must be *added* to the lock, not merely constrained. |
| | | Depend on `geopandas` instead | It is an unlocked optional extra CI never installs [VERIFIED: pyproject.toml:18], its only use is plotting a boundary file with a pure-Python fallback already in place, and it drags fiona/shapely/GDAL along for a job `open()` + `CRS.from_wkt()` does offline. |
| | | Accept lat/lon 4326 only, refuse everything else | Attractive - zero dependencies, honest, house style. **It does not eliminate the transformation; it eliminates the record of it.** The user reprojects in QGIS and pastes numbers back, and 6B has no idea which datum, which foot, or which operation. It also fails the DEC-000 gate, which requires a "different CRS" fixture to *run and degrade*, not be refused [VERIFIED: DECISIONS.md:73-75]. If the dependency is vetoed, the honest fallback is: refuse, and emit the exact command the user should run, so the transformation is at least specified. |
| | | Hand-roll the Lambert Conformal Conic inverse | DEC-000 already rejected this in terms: a hand-rolled reprojection "would be a transformation that cannot be explained in one sentence" [VERIFIED: DECISIONS.md:79-82]. It would also only cover hard-coded zones, recreating the very problem 6B exists to solve. |
| **6B-D2** | **Hand-rolled frozen conversion table.** Reject `pint` | `pint` | The collisions that hurt this dataset are same-dimension. Verified by execution: `1 kVA → 1.0 kW` silently; `1 ton → 907.18 kg` (short); `therm` ≠ `US_therm` by 0.024%; `acre` is US-survey while `foot**2` is international, in one registry with no signal. pint fires on exactly one item - amps→kW - which is one `if`. And it does not know `KW`, `kw` or `MMBTU`, so you write the alias table anyway. Whole table is ~20 rows, reviewable in five minutes, diffable in git. **Honestly given up:** compound-unit algebra, automatic prefix parsing, a maintained alias corpus. The ~20 unit-bearing columns are each a single-unit scalar with no derived units, so nothing needed is lost today. Revisit if 6B ever needs runtime composition. |
| **6B-D3** | Widen `site_id` and `jurisdiction` in **`build_schema_v2` only** | Widen `contract.build_schema()` | v1's manifest digest is pinned to a module constant [VERIFIED: tests/test_contract_v2.py:41, :61], `schema.json` is a hashed table, and `build_schema_v2` starts from `build_schema()`. Editing v1 fails the suite. |
| **6B-D4** | Duplicate `source_site_id` → **REFUSE the file** | Keep-first | `build_confidence` already silently keeps the first of duplicate rows [VERIFIED: confidence.py:117-119], and that is the behaviour 6B exists to stop, not imitate. |
| **6B-D5** | Completeness enters through **coverage + source_class + omission**, all inside the existing rubric | A separate `completeness_score` column | DEC-000 routes 6B.4 into the existing system rather than inventing a parallel score [VERIFIED: DECISIONS.md:69]. |
| | | A new `field_group` called `completeness` | Weights are hard-coded and sum to 1.00 with no normalisation [VERIFIED: confidence.py:45-53]; an eighth group re-weights all 12 existing sites and moves the pinned 33.8 baseline. |
| | | A new `source_class` like `partially_missing` | Categorical - cannot distinguish 90% coverage from 40%, and still needs an arbitrary threshold. `validate_provenance` would also refuse it until added [VERIFIED: confidence.py:92-94]. |
| **6B-D6** | Per-group provenance rows, aggregated in the intake layer | Per-column provenance rows | `build_confidence` silently keeps only the first row per `(site_id, field_group)`. The fix is to **make that an error** (§5.2), not to emit rows it will silently drop. |
| **6B-D7** | The transformation record goes in `assumption_type` **or** a new tenth provenance column | A separate transformation log | `score_field` would never see it. `observation_provenance_rows`' docstring states the rule directly [VERIFIED: observed.py:423-427]. **Which of the two is UNDECIDED and must be decided before code.** |
| **6B-D8** | `distance_to_service_ft` neutral = the anchor's `hi` (300 ft) | Cohort max of supplied values | Breaks the V3 fixed-anchor invariant stated in `scoring.py`'s own docstring - a site's score would change when unrelated sites join the file, which is the legacy min-max behaviour V3 replaced. |
| **6B-D9** | Run artifacts under `data/outputs/<run_id>/` | `data/intake/<run_id>/` | Only `data/outputs/` is gitignored [VERIFIED: .gitignore:11]. Per-run artifacts under a tracked path get committed by `git add -A`, turning a run over real facility data into a repo record. |
| **6B-D10** | No `--auto-fix-all` flag; three auto-safe transformations only | An auto-fix flag | One keystroke back to "best-effort silent cleaning", "the failure this project exists to avoid" [VERIFIED: DECISIONS.md:58]. |

**Cost and licensing:** total new recurring cost **$0/month**, well inside the $10 ceiling. Every artifact is a committed file; CI is the existing pytest run. `pyproj` is **MIT** with **exactly one runtime dependency, `certifi`**, `requires_python >= 3.11`, and **network disabled by default** - all four re-verified this session by executing against an installed 3.7.2 / PROJ 9.5.1 and reading its distribution metadata. It installs into a bare venv with pip and needs no system PROJ. **No licensed software anywhere: no Alteryx, no MATLAB, no Tableau, no paid ETL.** [UNVERIFIED: I did not execute on a GitHub `ubuntu-latest` runner; I verified a pip-only install works on macOS arm64 and that manylinux wheels exist. Confirm on a runner before pinning.]

---

## 10. Open questions for the owner

Only the ones where different answers change the work.

1. **`garage_enclosed` and `stormwater_risk`: optimistic-and-logged, or pessimistic-and-retiered?** (§2.3.) Answer (a) ships a known 2.25-point optimistic bias with a ledger line. Answer (b) requires changing a user-facing tier string. This changes both `scoring.py`'s neutral table and the tier vocabulary. **It cannot be deferred to implementation.**
2. **Coverage penalty ordering: `(base+adj−stale−unresolved)×coverage` or `(base+adj−stale)×coverage−unresolved`?** (§5.2.) The first shrinks the unresolved penalty as data thins - `64.00` vs `61.00` on the worked example [VERIFIED: both computed]. This changes `score_field` and every pinned confidence number downstream.
3. **Where does the transformation record live - `assumption_type`, or a tenth provenance column?** (§3.3, 6B-D7.) A tenth column touches `REQUIRED_COLUMNS`, `validate_provenance`, `build_field_provenance.py`, `observation_provenance_rows` and the committed 84-row CSV. `assumption_type` touches nothing but overloads a field that already carries prose.
4. **Does `scripts/build_field_provenance.py` become a package function in 6B?** (§8.7.) If no, DEC-000's gate is met for one of seven field groups and the brief must say so in the gate criteria. If yes, that is a substantial addition to 6B's scope.
5. **Does 6B fix the explorer's `data_confidence_reason` sink, or only the contract's?** (§5.5.) The user-visible string today is the breakdown table recited - the anti-example, shipped. Fixing only `migrate_v1_to_v2` leaves it on screen.
6. **Is `TYP02` (a thousands separator) ever grounds for blocking a whole file?** A decimal-comma locale conventionally exports with `;` as the delimiter, so in a file that already parsed as comma-separated with the right column count, the "1.2 kW" reading is close to unreachable. A narrower rule - quarantine the row, escalate only when the delimiter is `;` or more than one such value appears - may be right. Needs a `policy_status` string and a DECISIONS entry either way.
7. **`QUARANTINE_ESCALATION_SHARE = 0.20` and `engineering_estimate: 45` / `planning_proxy: 35`** - all three are proposals with **no external basis** [UNVERIFIED]. Each needs adoption or replacement.
8. **What is the declared-accuracy threshold above which a reprojection refuses rather than degrades?** (§3.4.) The concrete case to argue about: a NAD27 source falls back to a 10.0 m operation when the grid file is unavailable, and pyproj emits a `UserWarning` rather than an exception [reported by the units-crs lane; I verified the mechanism exists - `TransformerGroup(...).transformers[0].accuracy` and `.unavailable_operations` are the hooks - but did not reproduce this specific NAD27 warning myself]. A warning in a pipeline is the silent quality change the constraint forbids.

---

## 11. Gate 6B verification plan

The gate is green when **all** of the following are observed. Anything short of all of them is not the gate.

**A. The fixture runs end to end and degrades correctly.**
1. `data/intake/fixtures/ASHCROFT_COUNTY_MESSY.csv` - wrong column names, mixed units, missing fields, projected CRS - produces a completed run: a scenario table, a site table, a confidence table.
2. Its confidence score is **strictly below 33.75** [VERIFIED baseline: executed], with `electrical_service = 0.0` and `safety_review_fields = 0.0`, and the breakdown decomposes to all seven groups.
3. The `..._MESSY_NO_CRS.csv` variant **also completes**: 12 sites scored, `coordinates = 0`, map and 3D output suppressed with a stated reason, non-zero exit. A refusal here fails the gate.
4. The two negative controls (D13, D14) produce **zero findings**.
5. The test passes `today=date(2026, 7, 27)` explicitly. A test whose answer moves with the wall clock does not gate anything.

**B. Every transformation is traceable.**
6. `transformation_ledger.csv` contains one row per imputation, inferred mapping, unit conversion, dropped row and default substitution - no exceptions, including exact conversions.
7. Automated check on ledger reasons: non-empty, ≤ 140 chars, exactly one terminal period, names both units or both column names and the factor. **The module docstring states that one-sentence explainability is a human review gate, not a test.** Do not claim CI enforces the constraint; a punctuation check is not an explainability check.
8. Every `applied_defaults.csv` row maps to a `(site_id, field_group)` provenance row that exists. No sidecar row without a provenance row.

**C. No stack trace reaches a user.**
9. `test_reader_never_raises_on_a_validated_file` - run the **actual** `observed.read_capacity_observations` / `read_session_observations` over the fixture as intake would hand it on, and fail on **any** exception, not only `ObservationError`. This is the assertion that makes "never a stack trace" a gate, and it is what forces the single-parse decision of §4.4a.
10. `test_intake_never_surprises_observed` - every record intake accepts constructs a `CapacityObservation` / `SessionObservation` without raising.
11. Every `ObservationError` the fixture can produce is predicted by at least one `Finding` code.

**D. Nothing existing moved.**
12. `legacy_v2` reproduces bit-exact; `milestone2_v3` reproduces; both golden fixtures unchanged.
13. All 12 NoVA sites still score **33.8 / Low** with the identical breakdown string [VERIFIED as the current value: executed].
14. `tests/test_contract_v2.py` passes unchanged - including `test_v1_manifest_digest_is_pinned` and `test_confidence_reason_is_populated_and_specific` (>30 chars **and** contains "provenance").
15. `scripts/verify.sh` passes. `requirements-lock.txt` contains `pyproj==<pinned>` and `certifi==<pinned>` if 6B-D1 is adopted, and CI installs them.

**E. Nothing invented leaked in.**
16. No file under `data/intake/` contains a site_id that is not `SYN`-prefixed [the guardrail must key on the fixture's **declared** id column, not the literal name `site_id`, or it passes by not looking].
17. Every fixture declares itself synthetic with **both** required literals.
18. **No source string anywhere in the shipped code or data cites a §6 external source that has not been opened and confirmed.** A grep for the §6 dataset names in `src/`, `scripts/` and `data/` returns nothing unless a `[VERIFIED]` marker with a checked publisher page accompanies it.

**F. The visual surface exists.**
19. `MappingProposal.to_json()` renders: every source column with its proposal, confidence and evidence; every unmapped source column; every unmatched canonical field; the CRS proposal with its operation and accuracy; the ID crosswalk; and every finding with its Excel line number.
20. `accepted_by` is `None` on that object until a human or an explicit mapping file sets it, and **no transformation outside the three auto-safe byte-level ones has been applied when it is `None`.**