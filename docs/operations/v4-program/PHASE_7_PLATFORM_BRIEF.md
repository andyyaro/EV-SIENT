<!-- Saved design output. Read the provenance note before treating anything here as done. -->
# Phase 7 - platform implementation brief (design output)

> **Provenance.** Produced 2026-07-27 by a 10-agent design panel (`wf_7244a2a1-9e4`): a
> grounding pass, four independent architectures written from different angles, an
> adversarial challenge pass over each, then synthesis. ~2.4 M subagent tokens.
>
> **It read the tree, not my prompt.** I told the panel "nothing is built"; it checked, found
> five Phase 7 commits already landed, and corrected me in its own opening section. That is
> the behaviour asked for, and it is worth noting that the correction came from the panel
> rather than from me.
>
> **Claims are marked.** `[V: path:line]` means verified by reading or measuring during that
> session; `[UNVERIFIED]` means it could not be checked. External prices were not fetched.
> Nothing marked UNVERIFIED may be acted on without checking it first.
>
> **Decisions taken from this brief get their own `DECISIONS.md` entries** - see DEC-015.

---

# PHASE 7 IMPLEMENTATION BRIEF
## The platform: one spine, one shell, two tiers

Prepared 2026-07-27. Research and design only - **no file in the repository was written or edited during this pass.** Every repo claim is marked `[V: path:line]` (verified by reading or measuring this session) or `[UNVERIFIED]`. External prices are marked and not fetched.

---

### Note on the instruction "nothing is built"

That instruction does not match the tree, and the project's first rule is that honesty beats convenience. `HEAD` is **`346015a` "Phase 7: one interface, two tiers - the tier is detected, not configured"**, four Phase-7 commits deep [V: `git log --oneline`]. `git status` is **clean** [V]. Verified present and gated **today**:

| Component | Measured |
|---|---|
| `src/fcf_m2/provenance.py` | 447 lines [V: `wc -l`] |
| `src/fcf_m2/operations.py` | 283 lines, 11 operations [V: read in full] |
| `src/fcf_m2/server.py` | 186 lines, stdlib-only loopback server [V: read in full] |
| `site/platform/{index.html, app.js, styles.css, operations.json, provenance_v1.json}` | 5 files, tracked, 466-line `app.js` [V: read in full] |
| `scripts/build_platform_web.py` | 86 lines, `--check` mode [V: read in full] |
| `tests/{test_provenance,test_operations,test_platform_web,test_server}.py` | 20 + 15 + 19 + 18 test functions [V: `grep '^def test'`] |
| `scripts/verify.sh` | **25 gates**, four of them `platform:` [V: `grep -c '^gate '`, lines 84-94] |

So this brief is written against a real spine, not a blank page. **What is not built** is everything in §7 below: the remaining surfaces (3D explorer, dashboards, MATLAB/Octave/Simulink panes, NFC, downloads), the four new gates, the deploy path, and any packaged desktop artifact. Nothing in §3–§11 should be read as describing existing behaviour unless it carries a `[V:]`.

---

## 1. The decision

**Build the platform as a Python-native local server - `python -m fcf_m2.server` - that serves the one static bundle `site/platform/` on loopback and adds `/api/*` for execution; deploy that same directory, byte-for-byte, to S3 + CloudFront for the web tier. No Rust, no Electron, no bundled Chromium, no second frontend, and no signed installer in Phase 7.**

The single most important reason: **it is the only architecture where "one shell, two tiers" is a property of the deployment rather than a promise maintained by a build flag.** The desktop tier and the web tier are literally the same five files; the tier is *detected* by asking whether `/api/operations` answers [V: app.js:366-378, server.py:94-100], not compiled in. Every other angle ends up with an extra layer - a Rust host, a Chromium runtime, an installer - whose only job is to open a window onto a page that already exists, and each of those layers introduces a place where the two tiers can drift, a package the project cannot debug, or a signing bill that consumes 82.5% of the entire cost ceiling.

---

## 2. Why the other three lost

**Tauri + Rust shell.** The strongest of the three on size (~9–12 MiB of shell versus 279 MiB of Chromium) and genuinely correct that an embedded `python-build-standalone` CPython 3.12.13 can run this model with no user Python at all - the adversarial pass on that angle proved it end to end, with all seven contract files byte-identical to the tracked v1. The real trade is that after the correction pass, **the Rust layer's entire remaining job is "spawn `fcf_m2.server` and open a WebView"** - the sidecar it spawns is the architecture chosen here. It adds ~180 MiB of embedded runtime, a language no contributor to this repo writes (`cargo` and `rustc` are not installed on this machine [UNVERIFIED this session - not re-checked]), a second cross-platform build matrix, and it collides head-on with §10's boundary problem: a publicly downloadable installer that can *run* the model must carry `data/inputs/real_sites_v2.csv`, which is facility-level electrical and occupancy data for twelve named public buildings in a repository that stays private. Tauri buys an icon and a double-click; it costs a language, a CI matrix, and a declassification decision that is not the platform's to make.

**Electron.** It wins exactly one argument, and it is a real one: the flagship 3D surface is CesiumJS WebGL2 with 12 GLB models, and Electron guarantees the desktop renderer is the *same* engine as the web tier's Chromium, where Tauri gives you WKWebView on macOS and WebView2 on Windows and no cross-browser harness exists in this repo to catch a divergence. The trade that kills it: ~279 MiB of bundled Chromium - about half the installed bundle - duplicating a browser the user already has, on a project whose entire tracked payload is **13.5 MiB / 405 files** [V: `git ls-files`, `stat`]. Worse, that browser cannot auto-update within budget (Squirrel.Mac refuses unsigned updates; signing is $8.25/month minimum), so a desktop user's Chromium ages indefinitely while the web tier's does not. Shipping a stale browser to make a planning study look like an app is a security trade this project should not make.

**Web-first progressive (public page probes a local companion).** Architecturally almost identical to the winner, and its instincts about the capability probe and the deploy allowlist are grafted below. It loses on one specific mechanism: it has the *public* `https://` page reach out to `http://127.0.0.1`. That is mixed content in every browser, it is the shape a port-scanning ad script has, it is exactly the pattern Private Network Access exists to restrict, and none of the three could be verified in a browser this session [UNVERIFIED]. Betting the desktop tier on a cross-origin loopback fetch surviving the next Chrome release is a bet with no upside - serving the identical files from the local server instead makes every request same-origin and costs nothing. The idea survives; the direction of the arrow is reversed.

---

## 3. Architecture

### 3.1 Components and where they run

```
                    THE SPINE (unchanged, single producer)
   src/fcf_m2/{scoring,right_sizing,demand,economics,emissions,peak_wait,
               queueing,confidence,triggers,observed,contract,contract_v2}.py
                              │  writes
                              ▼
                    data/contract/v1  (FROZEN, tracked, 8 files, 316 KB [V: du])
                    data/contract/v2  (additive, tracked, 340 KB [V: du])
                              │
         ┌────────────────────┴────────────────────┐
         │ fcf_m2.provenance.export_all()          │ fcf_m2.operations.for_tier()
         ▼                                          ▼
   site/platform/provenance_v1.json          site/platform/operations.json
        1,201,250 B  [V: measured]                6,312 B  [V: ls -la]
        25,815 B gzip -9  [V: measured]
         └──────────────┬───────────────────────────┘
                        │  both written by scripts/build_platform_web.py [V: read]
                        ▼
        ┌──────── ONE BUNDLE: site/platform/ ────────┐
        │ index.html · app.js · styles.css           │
        │ provenance_v1.json · operations.json       │
        │ + (Phase 7 additions) explorer/, dash/,    │
        │   engines/, downloads/, field/             │
        └────────────────────────────────────────────┘
              │                              │
   python -m fcf_m2.server            aws s3 sync (allowlisted)
   127.0.0.1:<ephemeral>              S3 future-city-fellowship
   + /api/operations                  + CloudFront E1XZPHWHZV0OEO
   + /api/run/<id>                    https://futurecityfellowship.andyyaro.com
   + /api/provenance/<key>  (new)     [V: AWS_INVENTORY.md §2]
   DESKTOP TIER                       WEB TIER (primary distribution)
```

### 3.2 What runs where

| Capability | Web | Desktop | Mechanism |
|---|---|---|---|
| View every contract number + provenance | ✅ | ✅ | static `provenance_v1.json` |
| Validate contract v1 / v2 | ✅ (result of last run) | ✅ (live) | `validate-contract-v1/v2`, `TIER_BOTH` [V: operations.py:80-97] |
| Run the model (v3 / legacy) | ❌ stated | ✅ | `run-milestone2-v3`, `run-legacy-v2` [V: operations.py:100-128] |
| Regenerate contract v2, dashboards, Tableau data, NFC, docs | ❌ stated | ✅ | 5 declared operations [V: operations.py:148-204] |
| `ingest-observations` (V4 loop) | ❌ stated | ✅ | read-only by design [V: operations.py:131-145] |
| Run all 25 gates | ❌ stated | ✅ *conditionally* | `verify-all` → `bash scripts/verify.sh` [V: operations.py:218]; see §10.5 |
| 3D explorer | ✅ | ✅ | same files; desktop defaults to offline mode |
| MATLAB pane | archive viewer only | archive viewer only | never runs here (§5) |
| Octave pane | ❌ | ⚠️ only if probed AND registered | not an operation today (§10.4) |
| Simulink view | ✅ | ✅ | static SVG rendered at build time from the tracked `.slx` |

### 3.3 How one codebase serves both tiers

Three rules, two of which are already the shipped behaviour:

1. **The tier is detected, never configured.** `app.js` calls `/api/operations`; a 404 or a network failure *is* the web tier's answer, not an error [V: app.js:366-378 `detectTier`, and its gate `test_a_missing_api_means_web_tier_not_an_error` at test_platform_web.py:148]. One build, one artifact, no `#ifdef`.
2. **The capability list is generated from one registry.** `operations.for_tier(TIER_BOTH)` writes the static file; `for_tier(TIER_DESKTOP)` is what the server returns [V: build_platform_web.py:43, server.py:99]. `for_tier` returns the **whole** list to both tiers with `available:false` and a mandatory `unavailable_reason`, because "Hiding a capability is how a product quietly becomes less honest than its documentation" [V: operations.py:226-246; construction-time enforcement at :60-65]. Note: `for_tier` accepts only `"both"` and `"desktop"` - `"web"` raises [V: operations.py:232]. Do not "fix" that spelling; two gates depend on it.
3. **The frontend computes nothing.** Formatting only, never arithmetic [V: app.js:38-48, gated by `test_the_web_tier_does_no_arithmetic_on_displayed_values` at test_platform_web.py:72].

**Two changes required to the shipped shell, both small:**

- **Move the session token out of the URL.** `serve()` returns `…/index.html?token=<token>` [V: server.py:153] and `app.js` reads it from `location.search` and re-sends it as a query parameter [V: app.js:367, :370, :387]. The server already accepts `X-Platform-Token` [V: server.py:79]. A token in the URL lands in browser history and in the `Referer` of any outbound request - and the explorer, once added to this bundle, makes outbound requests. Recommendation: navigate to a token-free URL, hand the token to the page once (a one-shot `/api/session` bootstrap bound to the loopback socket, or `history.replaceState` immediately on read), and send it **header-only** thereafter.
- **Never let the tier badge claim desktop without a live API.** Today, opening `http://127.0.0.1:PORT/index.html` without the token silently renders as the web tier [V: app.js:368 returns `{tier:"both"}` when no token is present]. That is honest in the sense that it under-claims, but the banner should distinguish "web tier" from "local server present, not authorised" so a desktop user does not conclude their install is broken.

---

## 4. The provenance panel

This is the centrepiece and the section that must be buildable from the brief alone.

### 4.1 The data structure

Schema `fcf-provenance/1`, produced by `fcf_m2.provenance.export_all(contract_dir, out_path)` [V: provenance.py:338-408]. **Normalised, not flattened** - the naive one-record-per-cell form was 6.76 MB because it repeated caveat prose and run metadata 3,720 times [V: provenance.py:344-351].

```jsonc
{
  "schema": "fcf-provenance/1",
  "generated_from": "v1",
  "shared": {                                  // identical for every entry, hoisted
    "contract_version": "1.0.0",
    "model_version":    "3.0.0",
    "run_id":           "milestone2_v3_20260719T052322Z",
    "generated_utc":    "2026-07-19T05:23:22.507266+00:00",
    "table":            "scenario_table.csv",
    "table_sha256":     "a40358883265eb25649c0047b62ad6fad21eaf4936205a25a3814771f2e86aef",
    "engine":           "Python (fcf_m2)",
    "consumer_rules":   [ 4 strings ]
  },
  "engine_note":  "… GNU Octave is not MATLAB. No number here may be attributed to either.",
  "caveat_text":  { 8 keys → prose },
  "field_provenance": { "<site_id>|<field_group>": {8 typed fields} },   // 60 records
  "entries": {                                                          // 3,720 entries
    "<site_id>|<horizon_year>|<scenario_name>|<column>": {
      "v": <native JSON number|string|null>,   // never a stringified number
      "conf":  "<data_confidence>",
      "basis": "<capacity_basis>",
      "mode":  "<model_mode>",
      "cav":   ["<caveat_key>", …],            // keys into caveat_text
      "fp":    "<key into field_provenance>",  // "" when the column has no typed record
      "flag":  "<assumption_flag>"
    }
  }
}
```

Measured today [V]: `entries` **3,720** (= 120 rows × 31 exportable columns), `field_provenance` **60** (12 sites × 5 used field groups), `caveat_text` **8**, `consumer_rules` **4**, raw **1,201,250 B**, `gzip -9` **25,815 B** (46.5×). CloudFront already has `compress on` [V: AWS_INVENTORY.md:37], so the wire cost of the entire provenance corpus is ~26 KB. There is no case for lazy loading.

Two properties that must not be lost, both already enforced: values are converted by an explicit `_jsonable()` with **no `default=str` fallback** - a stringified `"2"` on the web side and an integer `2` on the desktop side would sort 6 after 10 [V: provenance.py:141-175]; and the file is written `allow_nan=False`, because a bare `NaN` literal is invalid JSON and would blank the whole page in front of a reader [V: provenance.py:407, gated at test_provenance.py:213].

### 4.2 How it is produced

`scripts/build_platform_web.py` writes both generated files from `data/contract/v1` [V: read in full], and `--check` rebuilds into a tempdir and fails on any textual difference [V: build_platform_web.py:57-75]. It is already wired into the gate at verify.sh:87-88. **Missing and required:** a `make platform` target, and a `build-platform-web` entry in `OPERATIONS` so the desktop tier can regenerate the web tier's data *through the same registry as everything else* - today it cannot [V: no such id among the 11 in operations.py:78-220].

### 4.3 How it resolves identically in both tiers

- Desktop path: `ContractIndex.load(dir)` → `resolve(index, site, year, case, column)` → a frozen `Provenance` dataclass [V: provenance.py:246-328].
- Web path: `entry_to_provenance(payload, key)` reassembles the same record from the normalised export [V: provenance.py:411-440]; `app.js`'s `resolve(key)` is the JavaScript mirror [V: app.js:53-76].
- Gate today: `test_the_web_tier_and_the_desktop_tier_say_the_same_thing` compares `resolve().to_dict()` against `entry_to_provenance()` field by field [V: test_provenance.py:174].

**The hole, stated plainly:** that gate pins **Python against Python**. The browser runs a *third* implementation - `app.js:53-76` - and nothing checks it. `entry_to_provenance`'s own docstring calls itself "the reference implementation of what the web tier's JavaScript does" [V: provenance.py:414-416]; a reference implementation with no conformance test is a promise. **Gate G-B in §6 closes it.**

**The refusal is load-bearing.** `resolve()` raises `ProvenanceError` on an unknown column or missing row [V: provenance.py:287-302], because "A provenance panel that renders 'unknown' for a number it cannot explain is worse than one that refuses - the first looks like an answer" [V: provenance.py:28-30]. The browser's equivalent renders a non-numeric muted span reading *"not available"* with the title *"This value has no resolvable provenance, so it is not shown"* [V: app.js:84-91], gated at test_platform_web.py:131. **Keep that behaviour; do not replace it with a throw** - a throw would blank an entire table because one cell was unmapped, and it would break a passing gate.

### 4.4 The DOM contract

Every number reaches the DOM through exactly one function, `numberCell(siteId, column, opts)`, which builds a `<button class="val" data-key="…">` with `textContent` (never interpolated HTML - the contract carries free text in `site_name`, `notes` and `assumption_flag`), an `aria-label`, and a click handler opening the panel [V: app.js:80-111]. **The attribute is `data-key`. There is no `data-prov` anywhere in this repo** - two of the four design angles invented it; a gate written against it would check nothing.

The panel renders five groups in this order [V: app.js:137-232]: *Which run produced it* · *Which file it came from* · *What backs it* · *How much to trust it* · *What you must know about this number* + *Rules for anyone consuming this contract*. When a column has no typed field-provenance record, the panel says so explicitly rather than borrowing a neighbour's credibility [V: app.js:178-186]. The open panel is addressable - `?number=FFX004|2036|base|ports_active` - so a reader can send someone the provenance rather than the claim, and a deep link to a nonexistent key refuses rather than opening an empty panel [V: app.js:228-231, :428-447].

### 4.5 Worked example - `ports_active` = 4, FFX004, horizon 2036, case `base`

Key: `FFX004|2036|base|ports_active`. Entry, read verbatim from the tracked export today [V]:

```json
{"v":4,"conf":"Low","basis":"placeholder","mode":"milestone2_v3",
 "cav":["screening_only"],"fp":"FFX004|parking_and_layout",
 "flag":"growth multipliers provisional; demand synthetic_uncalibrated; capacity placeholder; costs screening-class; emissions benchmark assumptions"}
```

Field-provenance record `FFX004|parking_and_layout` [V]:

```json
{"field_group":"parking_and_layout","source_class":"planning_assumption",
 "verification_status":"spot_checked","source_org":"imagery/site visit count",
 "source_date":"2026-06-24","reviewer":"team_v2_snapshot",
 "assumption_type":"unverified count","unresolved":false}
```

The panel therefore shows, with nothing computed client-side:

| Group | Field | Value | Where it comes from |
|---|---|---|---|
| **The number** | value | **4** | `entry.v` |
| | what | `ports_active · FFX004 · 2036 · base` | key split |
| **Which run produced it** | Engine | `Python (fcf_m2)` | `shared.engine` [V: provenance.py:138] |
| | Mode | `milestone2_v3` | `entry.mode` |
| | Model version | `3.0.0` | `shared.model_version` |
| | Run id | `milestone2_v3_20260719T052322Z` | `shared.run_id` |
| | Generated | `2026-07-19T05:23:22.507266+00:00` | `shared.generated_utc` |
| **Which file it came from** | Contract | `v1.0.0` | `shared.contract_version` |
| | Table | `scenario_table.csv` | `shared.table` |
| | SHA-256 | `a40358883265eb25649c0047b62ad6fad21eaf4936205a25a3814771f2e86aef` | `shared.table_sha256` |
| **What backs it** | Field group | `parking_and_layout` | `field_provenance` |
| | Source class | `planning_assumption` | " |
| | Verification | `spot_checked` | " |
| | Source | `imagery/site visit count` | " |
| | Source date | `2026-06-24` | " |
| | Reviewer | `team_v2_snapshot` | " |
| | Assumption | `unverified count` | " |
| | Unresolved | `no` | " |
| **How much to trust it** | Data confidence | `Low` | `entry.conf` |
| | Capacity basis | `placeholder` | `entry.basis` |
| | Assumption flag | the five-clause string above | `entry.flag` |
| **Caveats** | screening_only | *"A screening-class planning output for comparing sites. It cannot approve, permit or fund anything, and it is not an engineering design."* | `caveat_text` [V: provenance.py:116-118] |
| **Consumer rules** | 4 rules verbatim | incl. *"MATLAB refuses feasibility claims when capacity_basis is not verified_utility/verified_facility."* | `shared.consumer_rules` [V: measured] |

**Three additions this brief requires for this cell, none of which the export carries today.**

1. **The arithmetic behind `Low`.** `field_provenance` gives `planning_assumption` (base 35) + `spot_checked` (adj 0) − staleness 0 − unresolved 0 = **35.0** for this group [scores at confidence.py:22-42, per grounding; UNVERIFIED this session - not re-read]. The site rollup is **33.8 → Low**, and the same 33.8 already appears in `explorer/web/data/sites.geojson` as `data_confidence_score` [V: measured - FFX004 `data_confidence_score: 33.8`]. The panel should show the group score and the site score with their weights, so "Low" stops being an assertion. Requires adding two numbers per entry to the export.
2. **The derivation of 4.** Per the grounding pack, the binding constraint at 2036/base for a Tier-1 site is the **policy floor** `max(h1_base, 4)`, not the queueing screen [right_sizing.py:85-89 - UNVERIFIED this session]. A panel that implies "derived from Erlang-C" here would be wrong. Add a `deriv` key naming the binding constraint, emitted by the model.
3. **A truthful uniformity statement.** `data_confidence` is `Low` and `capacity_basis` is `placeholder` on **120/120 rows** [per grounding]. The panel must say *"This value is identical on all 120 contract rows - it is a study-wide condition, not a property of this site"* rather than let repetition read as per-site assessment.

### 4.6 The coverage gaps - "every number, every screen" is not true yet

| Gap | Status | Fix |
|---|---|---|
| **31 of 48 scenario columns are exported** [V: `EXPORTABLE_COLUMNS`, provenance.py:332-335] | 17 columns unresolvable | Most are run-constant metadata; hoist the ones that get displayed into `shared`. |
| **The grid emission factor is displayed and unresolvable.** `grid_factor_value` / `_units` / `_vintage` are among the 17, and are **not** in `shared` either [V: measured] | a published, test-pinned number with no lineage | Add `shared.grid_factor` + a `shared\|grid_factor` key. Cheapest of all the fixes. |
| **Portfolio aggregates have no entries.** `starter_total_2026`, `pathway_total`, `high_confidence_sites` live in `run_summary.json` [V: operations.py:112 declares it as `produces`] | not resolvable | Emit an `agg\|<name>` key class from `export_all` reading the model's own output. **Never sum in JavaScript** - that is a second source of truth, already forbidden by a passing gate. And note `data/outputs/` is gitignored and `run_summary.json` embeds absolute local paths, so it must never be copied into the bundle. |
| **The 3D explorer's numbers are not contract numbers.** `MODE_SOURCES` reads `tests/fixture_milestone2_v3_*.csv` [V: build_sites.py:61-71]. FFX004 shows `readiness_score 53.4, model_rank 1` in the geojson [V: measured] while right-sizing uses a legacy rank of 2 [per grounding] | the flagship surface is the one place the promise fails | Either repoint `build_sites` at the contract (correct, larger) or ship a second key namespace `site\|FFX004\|readiness_score` with its own field groups (achievable in Phase 7). **Until then the explorer must carry a visible label: "screening scores from the frozen fixture set, not the contract."** |
| **Numbers inside the 9 dashboard PNGs are pixels** [V: `dashboard/static` = 3,520 KB] | not clickable, ever | Chart-level provenance card beside each image + the existing footer stamp + a link to the table it was drawn from. |
| **The Tableau embed is a cross-origin iframe** | not instrumentable | A card that says so, plus the sheet caveats already gated at verify.sh:96-97. |

---

## 5. Engine distinguishability

**The rule, applied without exception: no surface renders engine output without exactly one engine chip, and the chip's text is read from a stamp file at build or request time - never typed into HTML.**

Four permanent identities, a closed set. `site/platform/styles.css` already defines `badge-python`, `badge-matlab`, `badge-octave`, `badge-simulink`, and `index.html:94-106` already renders all four with their distinctions in prose, gated by `test_the_page_names_all_four_engines_and_does_not_conflate_them` [V: read both]. Extend that vocabulary; do not create a fifth.

| Chip | Text (sourced) | Source of truth | Distinguished by |
|---|---|---|---|
| **PY** | `Python · fcf_m2 3.0.0 · contract v1.0.0 · run milestone2_v3_20260719T052322Z` | `shared.engine` + `PRODUCING_ENGINE` [V: provenance.py:138]; `manifest.producer = {"package":"fcf_m2","module":"fcf_m2.contract"}` | solid border, accent green |
| **ML** | `MathWorks MATLAB 25.2.0.3177638 (R2025b) Update 5 · ARCHIVED CI run 30296650057 · commit 343f1983 · SYNTHETIC input` | `matlab/outputs/run-30296650057/matlab_version.txt` and `run_provenance.txt`, both read verbatim [V: `engine: MathWorks MATLAB`, `repository: andyyaro/fcf-matlab-ci`, `input_sha256: ab1f6584…`, `note: the input is SYNTHETIC. No row corresponds to any real facility.`] | double rule, blue |
| **OCT** | `GNU Octave <probed version> - NOT MATLAB · transformed sources` | `octave --version` at probe time. **Never a literal.** If the version string is empty, the chip reads `version unavailable`, never blank | **dashed** border, amber |
| **SLX** | `Simulink structural view - rendered by the platform from the tracked .slx. Built, never simulated.` | the `.slx` SHA-256 + the MATLAB version string | dotted, grey |

Six enforcement rules:

1. **Colour is never the only signal.** Border style and text differ too; a monochrome print or a colour-blind reader still distinguishes four engines.
2. **The MATLAB chip always carries `SYNTHETIC`.** Real MATLAB has never seen the twelve sites and cannot - the public harness is gated against site-identifying data at verify.sh:163-164 [V].
3. **The Octave chip is the only dashed amber one**, because Octave is the one engine with a recorded *behavioural* divergence. The correct framing, from the repo's own record: under the **shipped Tier-2** (transformed sources + shim + `datatypes`), `guardproof.m` passes 16/16 with a negative control, and MATLAB_LIBERATION.md records HIGH confidence the fail-closed guard *does* fire. The bypass at `capacityGuard.m:53/:89` is a property of **Tier 1 - untransformed Octave - which is explicitly ruled out and forbidden to ship** [per grounding + the Electron angle's correction; UNVERIFIED this session - I did not re-read `guardproof.m`]. **`index.html:100-102` currently states the bypass as a live property of the Octave tier** [V: read] - that text needs reconciling against MATLAB_LIBERATION §3.5-3.6 before Phase 7 closes. Overstating a safety risk is the same class of failure as understating one.
4. **Cross-validation gets two columns, never a merged one.** 2,640 cells across 22 columns, zero numeric divergence, one behavioural divergence at `run_all_scenarios.m:135` classified **fatal_loud** - it lands after every number is computed and *cannot corrupt a value* [per grounding]. Render both engines side by side, both chips visible, no row suppressed, the two excluded columns (`run_id`, `placeholder_banner`) named on screen.
5. **The Simulink view needs no MATLAB.** `matlab/outputs/run-30296650057/simulink/site_grid_behavior_ev_charging_v3.slx` is an OPC zip whose `systems/system_root.xml` contains 11 `<Block>` and 8 `<Line>` elements [per grounding, independently confirmed by two angles; UNVERIFIED this session]. A build-time `zipfile` + `xml.etree` renderer produces a deterministic SVG, tracked, with its own re-render comparison test. It renders topology, not results - it does not compute, so it does not violate "`src/fcf_m2` is the only scorer" - but it is new generation logic and needs a gate or it becomes an unchecked second depiction of the model.
6. **Octave provenance is known-lossy.** `version("-release")` returns empty under Octave and a blank `matlab_release:` line is written silently - classified `fatal_silent` [per grounding]. Therefore: the Octave pane must refuse to run rather than emit an unstampable result, and `matlab/octave/transform.py` should write an `octave_provenance.txt` carrying `engine: GNU Octave`, the probed version, the pkg prefix, the input SHA-256, and the literal line *"GNU Octave is not MathWorks MATLAB."* No such file exists [per grounding; `octave` and `octave-cli` **are** on this machine at `/opt/homebrew/bin/` - V: `which`, which is exactly why it must be probed and not assumed].

---

## 6. CLI / platform byte-equivalence

### 6.1 The structural guarantee, already in place

An operation is a **declared argv executed as a subprocess**, never an import-and-call: `subprocess.run(op.argv(python), cwd=root, capture_output=True, text=True, timeout=timeout)` [V: operations.py:274-275]. The server accepts an **operation id** and looks it up in `OPERATIONS_BY_ID`, rejecting anything else by name so a UI/registry drift is *visible* rather than silent [V: server.py:113-120]. There is no endpoint that accepts a command, a path, or a flag. `test_the_platform_never_reimplements_the_model` greps `operations.py` for model imports and refuses them [V: test_operations.py:138].

### 6.2 What is gated today, and what it does not cover

`test_running_an_operation_matches_running_the_cli_directly` runs `validate-contract-v1` through `operations.run()` and through a direct `subprocess.run(op.argv())` and asserts identical returncode and **stdout** [V: test_operations.py:120]. That is one read-only operation and zero produced files. **The operations that matter for byte-equivalence are the six that write.**

### 6.3 Gate G-C - the exact gate

**Layer 1 - make the model reproducible.** Exactly three wall-clock stamps drift, all confirmed by source this session:

- `workflow.py:97` - `run_id = f"{mode}_{datetime.now(timezone.utc)…}"` [V]
- `workflow.py:98` - `generated_at = datetime.now(timezone.utc).isoformat()` [V]
- `contract.py:294` - `"generated_utc": datetime.now(timezone.utc).isoformat()` [V]

There is **no `SOURCE_DATE_EPOCH`-style override anywhere** [V: grep over both files found no `environ`, no `FCF_RUN_ID`]. Measured consequence, per the grounding: a fresh `run --mode milestone2_v3` reproduces the tracked v1 scenario table in **46 of 48 columns on all 120 rows**; the two that differ are `run_id` and `generated_at`, and the manifest additionally differs in `generated_utc` and therefore in `tables["scenario_table.csv"]`.

Add `FCF_RUN_ID` and `FCF_GENERATED_AT` environment overrides at those three sites. **Three conditions on that change**, because the platform reaching into the scorer is exactly what this project forbids:

- it lands as a **model** commit with **model** tests, justified by reproducibility of the frozen contract - a standing defect on its own merits - not by "the platform gate needs it";
- the manifest records `"run_id_source": "environment" | "clock"`, or the override becomes a way to forge a run identity;
- `provenance_v1.json` surfaces that field, so a panel can never show an environment-pinned run_id as if it were a real run.

**Layer 2 - compare produced files, with a declared mask.** Per operation, the registry gains two fields beside `produces`:

```python
compared: list[str]   # exact repo-relative paths compared by SHA-256
excluded: dict[str, str]   # path or field -> the stated reason it is excluded
```

The gate: for each `produces`-bearing operation, run it twice into two temp roots with the stamps pinned, SHA-256 every path in `compared`, and **fail on any difference at all**. With Layer 1 in place the mask should be empty; if it is not, the reason is named in `excluded` and the gate asserts that the mask is *exactly* the declared set - nothing is silently forgiven.

This adopts the shape the repo already uses rather than inventing one: `scripts/build_contract_v2.py --check` compares a named list of five tables by SHA-256 and **excludes `contract_manifest.json` entirely**, because the manifest is where the wall clock lives [per grounding, build_contract_v2.py:163-171; UNVERIFIED this session - not re-read]. Known-nondeterministic artifacts stay out of `compared` with their reasons: `.twbx` (embedded Hyper extracts carry engine state; only the `.twb` is gated, at verify.sh:96-97 [V]) and `explorer/web/data/manifest.json` (`generated_at`).

### 6.4 The other four gates

**G-A - every rendered number resolves.** Runtime, not static. Serve `site/platform/`, drive it headless through the existing `webapp-testing` Playwright path, walk every screen and assert: (a) at least one `button.val[data-key]` was found - *a gate that finds nothing to check must not report success*, which is the failure `scripts/check_cdn_pins.py` was written to avoid; (b) every `data-key` is a key of `provenance_v1.json.entries`; (c) no element carrying the declared numeric display class (`class="num"` [V: index.html:68-69, app.js:267]) contains a digit without a resolvable `data-key` ancestor. **Scope (c) to the declared class** - a blanket "no digit outside a provenance wrapper" rule fires on the contract version, the year labels, "12 sites" and the SHA-256 itself, and a gate that needs a growing exclusion list gets deleted within a month, taking the real check with it. Mutation-test it: delete one key, confirm red.

**Expected initial result, stated in advance: G-A fails on the explorer**, because `readiness_score` and `model_rank` have no entries (§4.6). That is the correct outcome and the reason to build the gate before the surfaces.

**G-B - the JavaScript agrees with Python.** `node` v25.8.2 is present and `verify.sh:160-161` already runs `node --check` on the explorer's JS [V]. Walk all 3,720 keys through `app.js`'s `resolve()` under node, dump to JSON, diff field-by-field against a `entry_to_provenance` dump. This is the only thing standing between "both tiers say the same thing" and "both *Python* implementations say the same thing."

**G-D - engine chip coverage.** Extend `tests/test_platform_web.py`'s existing four-engine test into a DOM assertion: every container marked as engine output carries exactly one chip from the closed set of four, the chip text matches the corresponding stamp file, and `MATLAB` never appears inside a provenance panel.

**G-E - the deploy boundary.** An explicit allowlist file in the repo enumerating every path published to S3; the gate asserts the sync manifest is a subset of it, and runs `secret_scan.py`'s patterns over the **built bundle**, not just tracked files. `scripts/secret_scan.py` scans `git ls-files` output only [per grounding], so a bundle can contain what a tracked file does not. Also widen `scripts/check_cdn_pins.py`'s glob - it globs `explorer/web/*.html` only, so `site/platform/index.html` is unscanned; latent today (that file has no external URLs [V: read]), fatal the first time someone adds one.

**Gate count: 25 → 30** [V: 25 measured today].

---

## 7. Build order

Each step must leave `./scripts/verify.sh` green. The ordering principle: **make the promise checkable before making it broad.** A platform with three honest surfaces and a gate that proves it is worth more than nine surfaces and a slogan.

| # | Step | Leaves green because | New gates |
|---|---|---|---|
| **0** | **Reconcile the Octave text in `index.html:100-102`** against MATLAB_LIBERATION §3.5-3.6. Either the shipped tier's guard fires (Tier 2) or it does not; the page must not assert the Tier-1 failure as live. | text-only change; existing gate checks the four engine names, not this clause | - |
| **1** | **Token hygiene**: header-only `X-Platform-Token`, token-free navigation URL, tier badge distinguishes "web" from "unauthorised local". | `test_server.py`'s token tests already cover header auth [V: server.py:79] | - |
| **2** | **G-A (DOM audit) + G-B (JS↔Python conformance)**, against the current three-section page. Both will pass on today's surfaces. | nothing new rendered yet | +2 → 27 |
| **3** | **`FCF_RUN_ID`/`FCF_GENERATED_AT` + `run_id_source` in the manifest** (model commit, model tests), then **G-C** over the six writing operations. | contract v1 stays frozen; the override is opt-in and absent by default | +1 → 28 |
| **4** | **Close the cheap provenance gaps**: hoist `grid_factor` into `shared`; add `agg\|` entries emitted by `export_all`; add group/site confidence scores and a `deriv` field to entries. Regenerate, `--check` passes. | `build_platform_web.py --check` is already gated | - |
| **5** | **`make platform` + a `build-platform-web` operation** in the registry, so the desktop tier regenerates the web tier through the registry. | `test_operations.py` shape tests cover it automatically | - |
| **6** | **Engine surfaces**: the Simulink structural SVG (build-time, tracked, with a re-render test), the MATLAB archive viewer, the cross-validation two-column screen, all chipped. **G-D.** | each surface arrives already chipped and already audited by G-A | +1 → 29 |
| **7** | **The 3D explorer, absorbed**: `/explorer/` under the same URL space; boot into Flat (the `#tokenSkip` path already exists in the viewer [per grounding]); add an explicitly-labelled **"Offline (boundaries only)"** mode using the tracked TIGER/Line county geojson; make the desktop build **fail loudly** if `explorer/web/vendor/Cesium` is absent rather than falling back to `unpkg.com`. Label the explorer's scores as fixture-derived until step 8. | G-A must be told the explorer's numeric class is not yet provenance-backed, **with the exemption recorded in a tracked file and a stated deadline**, not silently | - |
| **8** | **Repoint `build_sites` at the contract** (or ship the `site\|` namespace). G-A's explorer exemption is deleted. | the explorer's own drift suite already gates that attribution reproduces the model score in both modes [V: verify.sh:114-115] | - |
| **9** | **Dashboards, downloads, NFC payloads, field-data screens** (§9). | all read-only static surfaces | - |
| **10** | **Deploy**: allowlist file, **G-E**, OIDC role for CI (`sts:AssumeRoleWithWebIdentity`, trust pinned to the branch), S3 lifecycle rule expiring noncurrent versions, dedupe the six identical PNGs. | - | +1 → 30 |

Packaging (PyInstaller / `python-build-standalone`) is deliberately **not** in this list. See §8 and §11.1.

---

## 8. Cost

Ceiling: all new recurring combined **≤ $10/month, at on-demand rates, no free tier, no credits.**

**Baseline.** Project-attributable AWS run rate today is **≈ $0.40/month**, essentially one Secrets Manager secret at ~$0.40/secret-month [V: AWS_INVENTORY.md:191-196]. That document explicitly warns it reflects free tier and credits and that Phase 8 must recompute without them [V: read]. I budget **$1.00** for the pre-existing stack at on-demand and flag it for a proper Phase 8 recompute.

**Unit rates - all [UNVERIFIED]; not fetched this session.** S3 Standard $0.023/GB-mo, PUT $0.005/1,000; CloudFront US/EU egress $0.085/GB, HTTPS requests $0.0100/10,000, invalidations first 1,000 paths/mo free then $0.005/path; Route 53 queries $0.40/million; GitHub Actions private-repo Linux $0.008/min. Close these with `aws pricing get-products` and the GitHub billing page before Phase 8.

**New bytes on the origin** (measured today with `du -sk` [V]):

```
site/ (incl. site/platform, 1.2 MB of which is provenance_v1.json)   1,468 KB
explorer/web/data + models                                             908 KB
dashboard/static (9 PNG + PDF)                                       3,520 KB
data/contract/v1 + v2                                                  656 KB
matlab/outputs (archive + Simulink SVG)                                488 KB
                                                                    ---------
                                                                    ≈ 7.0 MB
CesiumJS vendored - EXCLUDED, see below                            (20,324 KB)
```

**Decision: keep the pinned `unpkg.com/cesium@1.128` CDN for the web tier** and vendor Cesium only for local/offline use. It keeps 20 MB and ~377 objects off the origin, and `scripts/check_cdn_pins.py` already gates that the reference stays version-pinned [V: verify.sh:160-161]. Serving it from S3 instead costs roughly +$0.30/month at 500 first-visits and is a *policy* question (third-party CDN reachability), not a cost one - §11.4.

**Arithmetic.** Assume ~10× today's traffic (today: 2,132 requests / 323,172,829 B per 30 days [V: AWS_INVENTORY.md:69-70]), so 25,000 requests and - because per-visit bytes grow with the explorer - **5 GB/month egress**:

| Line | Quantity | Rate | $/month |
|---|---|---|---|
| S3 storage (7 MB × 2.5 for versioning growth) | 0.018 GB | $0.023/GB-mo | 0.0004 |
| S3 PUT (≈120 objects × 4 deploys) | 480 | $0.005/1,000 | 0.0024 |
| CloudFront egress | 5.0 GB | $0.085/GB | **0.4250** |
| CloudFront HTTPS requests | 25,000 | $0.0100/10,000 | 0.0250 |
| CloudFront invalidations (4 wildcard paths, no free tier assumed) | 4 | $0.005/path | 0.0200 |
| Route 53 queries (zone pre-exists and is shared [V: AWS_INVENTORY.md:32, :47-49] - no new zone) | 30,000 | $0.40/M | 0.0120 |
| ACM, Cognito, Lambda, DynamoDB | unchanged | - | 0.0000 |
| GitHub Actions, existing CI (private repo, ~200 min/mo Linux) | 200 min | $0.008/min | **1.6000** |
| **New recurring subtotal** | | | **$2.085** |
| Pre-existing stack at on-demand | | | 1.000 |
| **All-in** | | | **≈ $3.09 / month** |

**Ceiling met. Headroom ≈ $6.91.** Stated break-even, so it can be watched: at $0.085/GB the headroom is exhausted at roughly **+81 GB/month of egress**, which at ~5 MB per full explorer session is about **16,000 sessions/month**. That is a comfortable margin *specifically because there is no installer to serve.*

**What is excluded, with the reason stated rather than hidden:**

- **Code signing and notarisation: OUT OF SCOPE for Phase 7.** Apple Developer Program is ~$99/year = **$8.25/month** [UNVERIFIED - price not fetched; a fee waiver exists for nonprofit/educational/government entities and a fellowship *might* qualify, which is an application, not an assumption]. Windows OV certificates are ~$200–400/year, or Azure Trusted Signing at ~$9.99/month [UNVERIFIED]. $8.25 alone consumes 82.5% of the ceiling and leaves $-1.34 against the $3.09 above once both platforms are signed. **This is the single largest reason the winning architecture wins: it needs no installer, so it needs no signature.**
- **Desktop installer egress.** The Electron/Tauri angles carried 90–230 MiB per download; at 50 downloads/month that is $0.44–$1.79, and it caps distribution at ~150–1,200 downloads/month. Not incurred here.
- **Cesium ion: $0 to this project.** The token is user-supplied and stored only in that user's browser [V: per grounding, `localStorage['fcf3d.ionToken']`]. But `photoreal` and `terrain` meter against **the user's own ion account**, and the page must say so.
- **MathWorks MATLAB** runs on a licence outside this budget, in `andyyaro/fcf-matlab-ci` [V: run_provenance.txt].

**Two hygiene items to fix regardless, both cheap and both structural:** S3 versioning is **ENABLED** with no recorded lifecycle rule [V: AWS_INVENTORY.md:44] - add a 30-day noncurrent-version expiry or storage grows without bound; and 7.77 MB of the current 8.19 MB origin is **six byte-identical duplicate PNGs sharing one ETag** [V: AWS_INVENTORY.md:69], which dominate today's transfer and are free to delete.

---

## 9. What ships EMPTY and labelled

This project has **no observed field data**, and the platform must make that state legible rather than look broken.

**What is true today, verified:** of the 12 fields contract v2 adds for the observed-data loop, only `data_confidence_reason` and `trigger_outcome` are populated; the other ten are empty on all 120 rows [per grounding]. `capacity_basis` is `placeholder` at 12/12 sites and `data_confidence` is `Low` on 120/120. The canonical run reports `high_confidence_sites: 0`.

**Day-one field-data screens:**

1. **The empty state is already written and gated** [V: index.html:109-121, gated by `test_the_field_data_section_says_it_is_empty_and_why` at test_platform_web.py:125]: *"No field observations have been received. The loop that ingests them is built and tested: a utility load study or a month of charger logs would upgrade a site's capacity from `placeholder` to `verified`, raise its data confidence, and make its expansion trigger evaluable. Until something arrives, this stays empty - which is the honest state, not an omission."* Keep that wording. It is the model for every other empty surface.
2. **A "what would change" preview, driven by the model, not by prose.** The `ingest-observations` operation is available in the desktop tier and is **deliberately read-only - it never writes** [V: operations.py:131-145, caveat *"No field observations have been received. Today this reports nothing to change, which is the correct answer."*]. Running it with no arguments exits 2 [per grounding]. The screen should offer it, run it, and show its actual output including that exit code - not a simulated preview.
3. **A per-site table of the ten empty v2 fields**, rendered as empty cells with the `not available` treatment (§4.3), each clickable to a provenance card explaining *why* it is empty: `observed_months`, `observed_utilization`, `observed_uptime`, `observed_p90_wait_min`, `observed_source_system`, `capacity_observed_date`, `capacity_method`, `capacity_conflict`, `trigger_rule_trace`, `trigger_equity_override`. An empty cell with a reason is a stronger claim than a hidden column.
4. **The expansion-trigger panel** shows `awaiting_observed_data (proposed policy, not adopted)` on every site, with the caveat text verbatim: *"The expansion-trigger policy is PROPOSED configuration, not adopted municipal policy, and every evaluation says so."* [V: provenance.py:125-127].
5. **The NFC/capture layer ships as artifacts, not as a service.** 12 landing pages, 12 capture forms, 12 QR SVGs and the tag payload CSV are downloadable. The capture forms **submit nowhere** - they assemble a CSV row in-browser for download or email [per grounding]. The platform must say that on the page: there is no backend, no endpoint, no database, and no credential - which is also why this layer costs $0.
6. **The confidence screen shows 0 of 12 high-confidence sites** and says the arithmetic that produces it, rather than an empty chart. `high_confidence_sites: 0` is the correct answer, not a loading failure.

**One thing that must not happen:** no screen may show a plausible-looking placeholder observation, a demo dataset, or a greyed-out chart implying data is coming. The empty state *is* the finding.

---

## 10. Risks and residual limitations

1. **The provenance panel is only as good as the contract, and the contract is uniform.** `data_confidence = Low` and `capacity_basis = placeholder` on 120/120 rows means every panel says the same thing about trust. Truthful, unsatisfying, and unfixable by any shell. The mitigation is the explicit "this is study-wide, not site-specific" line (§4.5) - not synthesised variation.
2. **"Every number, every screen" is false on the flagship surface until step 8.** The explorer's `readiness_score` and `model_rank` come from `tests/fixture_*` [V: build_sites.py:61-71], and G-A will fail on it by design. If step 8 slips, the exemption must be a tracked, dated file - never a quiet allowlist entry.
3. **Genuinely offline 3D does not exist today.** Even Flat mode fetches OSM raster tiles from `tile.openstreetmap.org`, because `baseLayer` is set at viewer construction in every mode [per grounding]. The tracked TIGER/Line county geojson (~172 KB) is the only fully offline map asset, and it is boundaries only. There is also a third-party-terms exposure: the OSMF usage policy restricts systematic application use. The desktop default must be the labelled boundaries-only mode.
4. **There is no Octave operation, so there is no honest Octave pane.** `OPERATIONS` has 11 entries and none runs Octave [V: read in full]; `scripts/octave_crossvalidate.py` *compares* two existing result sets. Under this design's own rule - a pane with no registry-declared argv cannot exist - the Octave runner is deferred until an `Operation` exists. And its precondition is not `which octave`: it needs Octave ≥ 11.1.0, the third-party `datatypes` package (~14 MB, 9 C++ sources, licence `NOASSERTION`), the 15-rule transform, the shim, and `guardproof.m` passing [per grounding]. A `which`-only check offers a button that fails.
5. **`verify-all` is the weakest operation in the registry.** Its command is `["bash", "scripts/verify.sh"]` with **no `{py}`** [V: operations.py:218], so the interpreter is never substituted; `verify.sh:7` resolves `${VENV_PY:-$REPO/venv/bin/python}` [V]. It also needs `pytest`/`pytest-cov`, and two gates shell out to `git grep` / `git ls-files` [V: verify.sh:108, :111]. In a repo clone with a venv it works; anywhere else it does not. **Never ship a green "ALL GATES PASSED" over gates that could not run** - either the operation reports a per-gate skip list with reasons, or it stays CLI-only. Note also that `Operation` has a `tier` axis and **no OS axis** [V: operations.py:60-67], so "macOS/Linux only" has nowhere to live without a registry change.
6. **A dated cliff in confidence.** `build_confidence` is called without a `today` argument, so `_staleness_penalty` falls back to `date.today()`; every provenance row carries `source_date = 2026-06-24` and the staleness threshold is 730 days [per grounding]. **From ~2028-06-24 every field group takes −10** and a live desktop run will disagree with the frozen web export by calendar date alone. G-C will catch it, and it will look like a platform bug. Consider pinning `today` from the contract's `source_date` in a model commit.
7. **Two rank systems coexist and both are correct.** Right-sizing uses legacy ranks (FFX004 = 2); display and the explorer use v3 fixed-anchor ranks (FFX004 = 1, score 53.4 [V: measured]). A panel that shows one rank without naming its mode is wrong half the time.
8. **`.twbx` can never be byte-equivalent** - embedded Hyper extracts carry non-deterministic engine state, and the repo already gates the `.twb` only, with the reason written down [V: verify.sh:96-97].
9. **The desktop tier is a browser tab.** No dock badge, no menu bar, no native file picker. That last one is a genuine crack in byte-equivalence: `ingest-observations --capacity <path>` in a browser means the user picks a file, the bytes are POSTed, and the command actually run is `--capacity /tmp/xyz.csv` - not what the user would have typed. Honest handling: echo the exact command run, temp path included, and keep user-path operations out of G-C's scope.
10. **A locked-down browser or an aggressive extension breaks the desktop tier with no useful error** [UNVERIFIED - not tested].
11. **The private/public boundary is a deploy-script property, not a gate today.** What crosses: `site/platform/*`, the contract tables, `sites.geojson` (12 real sites with coordinates, already public-shaped), the dashboards, the Simulink SVG. What must not: `data/inputs/` (facility-level electrical and occupancy data for twelve named public buildings), `data/outputs/` (gitignored, and `run_summary.json` embeds absolute local paths), `matlab/legacy_archive/`, `tests/`, `scripts/`, `docs/operations/`. An `aws s3 sync` of the wrong directory is how a private study's electrical survey becomes public, and `verify.sh` cannot catch a deploy it does not run. That is why G-E is not optional. **This architecture largely dodges the problem the installer angles hit head-on** - there is no bundle to leak into.
12. **`provenance_v1.json` publishes internal review metadata**: `source_org`, `reviewer` (a single value, `team_v2_snapshot`, across all 60 records [V: measured]), `assumption_type`, `verification_status`. Not secrets, but a deliberate publication decision, and `test_the_web_tier_carries_no_credentials` does not currently scan that file [V: test_platform_web.py:209 - check its file list before Phase 8].

---

## 11. Open questions for the owner

Only the ones where a different answer changes the build.

1. **Does the desktop tier need to be double-clickable by a non-technical user?**
 *If no* (the assumption in this brief): the desktop tier is `python -m fcf_m2.server` from a clone, cost stays at ~$3/month, and nothing is packaged. *If yes*: add PyInstaller `--onedir` (≈200–320 MB per platform, [UNVERIFIED] - no build was performed, and the repo contains no packaging config), plus the Gatekeeper problem - macOS Sequoia and later removed the Control-click override, so an unsigned download needs a System Settings detour [UNVERIFIED - Apple's statement quoted second-hand by one angle; this machine is Darwin 25.5.0 [V: env], past that threshold]. Signing puts the ceiling at ~$11.34 for macOS alone. **This is the biggest fork in the road.**

2. **May `data/inputs/` be declassified?** It is required by `workflow.py:_load_inputs()` on every run [per grounding], so any distributable that runs the model must carry it. Under this architecture the question is deferred, not answered - but it becomes load-bearing the moment question 1 is answered "yes." It is a program decision, not a packaging one.

3. **The explorer's spine: repoint `build_sites` at the contract, or ship a second provenance namespace?** Repointing is correct and larger (it changes the payload the whole 3D tier renders and touches a gated drift suite). A `site|` namespace is achievable inside Phase 7 and leaves two spines. The answer determines whether step 8 is a week or a day.

4. **May the web tier reach `unpkg.com` for CesiumJS?** Keeping the pinned CDN saves 20 MB and ~377 objects from the origin and is what `check_cdn_pins.py` already assumes. Self-hosting costs ~+$0.30/month and removes a third-party runtime dependency from a government-facing planning tool. Cost is not the deciding factor; policy is.

5. **Is `verify-all` in scope for the desktop tier at all?** It cannot honestly run outside a repo clone with a venv (§10.5). Shipping it degraded requires a per-gate skip list, which is real work; dropping it costs a button.

6. **Does the platform absorb the explorer and the dashboards into one URL space, or link out to them?** Absorbing gives one shell and one design language, and puts every surface under G-A. Linking out is faster and leaves two products. The Phase 7 requirement ("ONE SHELL") reads as absorb; confirm before step 7, because it determines whether the explorer's numbers must be provenance-backed or merely labelled.

---

**Files that carry the load** (all absolute, under `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo`):
`src/fcf_m2/provenance.py` · `src/fcf_m2/operations.py` · `src/fcf_m2/server.py` · `src/fcf_m2/workflow.py` · `src/fcf_m2/contract.py` · `src/fcf_m2/confidence.py` · `src/fcf3d/build_sites.py` · `site/platform/{index.html,app.js,styles.css,operations.json,provenance_v1.json}` · `scripts/build_platform_web.py` · `scripts/verify.sh` · `scripts/secret_scan.py` · `scripts/check_cdn_pins.py` · `tests/{test_provenance,test_operations,test_platform_web,test_server}.py` · `matlab/outputs/run-30296650057/{matlab_version.txt,run_provenance.txt,simulink/site_grid_behavior_ev_charging_v3.slx}` · `docs/operations/v4-program/{AWS_INVENTORY.md,MATLAB_LIBERATION.md}`.