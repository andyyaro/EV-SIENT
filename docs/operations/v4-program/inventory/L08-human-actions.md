# L08 - HUMAN ACTION PACKAGES (`repo/docs/human-actions/`)

**Lane:** L08-human-actions
**Root:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo/docs/human-actions/`
**Files assigned:** brief said 40; the directory actually contains **37** files
(README.md + ahj_fire_marshal 5 + client_meeting_2 10 + fellowship_confirmation 2 +
public_engagement 8 + team_alternatives_session 7 + utility_facility_data 4 = 37).
All 37 read end to end, no truncation, no skimming. Read-only - nothing modified.

**Global character of this tree:** every file is *authored prose/templates*. None are generated,
none are code, none are data-contract files. They are **instruments for human actions that have
not yet occurred**. Every capture field is deliberately blank. There are **no secrets, no absolute
local paths, no URLs, no AWS identifiers anywhere in the tree** (verified by grep for
`/Users/`, `/home/`, `AKIA`, `arn:aws`, `amazonaws`, `secret`, `token`, `api_key`, `password`,
12-digit account numbers, `http://`, `https://` - zero hits).

**Global cross-check results (done against `data/contract/v1/`):**
- Run id `milestone2_v3_20260719T052322Z` - **CONFIRMED** in `data/contract/v1/contract_manifest.json:4`.
- Contract horizons: `contract_manifest.json` `conventions.baseline_year = 2026`, `horizons = [2036, 2046, 2056]`.
  `scenario_table.csv` has 120 rows: `horizon_year` = 2026 (12) / 2036 (36) / 2046 (36) / 2056 (36);
  `horizon_label` = `now` (12) / `plus10` (36) / `plus20` (36) / `plus30` (36).
- `capacity_basis` = `placeholder` in **120/120** rows; `capacity_confidence` = `none` 120/120;
  `data_confidence` = `Low` 120/120; `service_capacity_kw` and `spare_capacity_kw` **empty in all 120 rows**.
- eGRID factor: `596.3 lb CO2e/MWh` in every scenario row and in `contract_manifest.json`
  `grid_factor.value_lb_per_mwh: 596.3`. **`590.2` appears NOWHERE in this lane** (grep clean).
  No file in this lane quotes an emissions factor at all.
- `battery_storage_flag = 0` for all 12 sites in `data/inputs/real_sites_v2.csv` - the
  COI note's claim is **true**.

---

## `README.md`

- **Role:** Index and integrity charter for the whole human-actions tree; declares that nothing in
  it has been sent, held, adopted, or answered.
- **Kind:** authored
- **Reads:** n/a (prose)
- **Written by / read by:** Referenced from `docs/operations/open-human-actions.md` (which lists the
  six packages as open rows 1–5 and 10). Sub-packages reference each other by relative path.
- **Key contents:**
  - Line 3: "**Prepared 2026-07-19.**" - every file in the tree carries this date.
  - Lines 7–12, "Integrity rule (governs every package)", four numbered rules. Rule 2: every outbound
    document carries `**"DRAFT - PREPARED 2026-07-19 - NOT SENT"**` and "Removing that header is part of
    the human act of sending, and only the team does that." Rule 4: "Provisional analytical content
    (the MCDA matrix, screening-class costs, placeholder capacity values) is labeled as such and is
    input *to* the human decision, never a substitute for it."
  - Lines 16–23 package index → criteria mapping:
    `client_meeting_2/` → A1, A2, A3, A4, G5;
    `team_alternatives_session/` → A5, A6, A7, A8, B7, F2;
    `ahj_fire_marshal/` → C7 validation path, G1 authority confirmation, post-M2 disconnect/access;
    `utility_facility_data/` → **D1; upgrade of `capacity_basis` from placeholder to verified**;
    `public_engagement/` → G3, G4 (engagement evidence), equity validation;
    `fellowship_confirmation/` → A1 classification; B3/B5/B6 convention; C-row scope.
  - Line 27: client contact **[client contact], Green Buildings Manager, PWC Office of Sustainability**;
    quoted verbatim: "either one, follow up meeting, or emails is fine."
    **"The interview date was *not recorded*"** - `[INTERVIEW DATE]` is a live blank everywhere.
  - Line 29: Milestone 2 presentation **Tuesday 2026-07-21**. Team: **Anna, Laylas, Andy, Adama, Paula**
    (Paula's presentation role unassigned).
  - Line 30: "All 12 candidate sites remain electrically unconfirmed (`capacity_basis = placeholder`,
    confidence Low). Package 4 is the closure path."
- **Notes:** Line 30 says confidence **Low**; the contract's `capacity_confidence` is literally `none`
  and `data_confidence` is `Low` - the README is conflating two columns, harmlessly but imprecisely.
  Line 7 cites "Report 02 §4" - see the dead-reference finding below.

---

# Package 4 - `utility_facility_data/` (CAPACITY-CONFIRMATION PATH - Phase 4 / Phase 5 critical)

## `utility_facility_data/01_DATA_REQUEST_DOMINION.md`

- **Role:** Draft formal letter to Dominion Energy Virginia requesting electrical service data for the
  three top-ranked sites.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** n/a
- **Written by / read by:** Tracked by `03_TRACKING_REGISTER.md` (Dominion-sourced rows);
  its received fields are consumed per `04_DATA_FLOW_INTO_MODEL.md`.
- **Key contents:**
  - Header line 1: `# DRAFT - PREPARED 2026-07-19 - NOT SENT`.
  - Line 5: routing note - "a **facility-owner authorization may be required** for account-level data";
    [client contact] may introduce. Recipient name/routing TBD by the team.
  - Sites and coordinates (lines 17–19), all three verified against `data/contract/v1/site_table.csv`:
    - **FFX002** City of Fairfax Regional Library - 38.847072, −77.30363 ✔
    - **FFX004** Fairfax County Government Center - 38.85404, −77.35706 ✔
    - **PWC006** Bull Run Library - 38.78694, −77.520529 ✔
  - **The seven requested items (lines 23–29), literal:**
    1. Electrical service rating (**voltage, amperage, service capacity in kW/kVA**) per account serving the site
    2. **Interval load data (15-minute or hourly) for the most recent 12+ months**
    3. Estimated **spare capacity on the existing service at current peak**
    4. **Serving transformer and feeder information** (size, loading, headroom, known constraints)
    5. **Distance from the existing service/transformer to the candidate charging area**
    6. Any **planned outages, upgrades, or capital projects** affecting these services
    7. Applicability/status of the **Dominion Level 2 Charging Program** (50% make-ready incentive;
       100% in designated disadvantaged communities), including eligibility steps and queue/timeline
  - Line 31: data-handling commitment - "use it only for capacity screening in this municipal planning effort."
- **Notes:** The 50% / 100%-disadvantaged-community figures **match** `docs/methodology/current-facts-source-register.md:13`
  (IM-07) and `reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md:22`. Consistent.
  **Consent language is present and correct**: this letter does not assume authorization -
  it explicitly says facility-owner authorization may be required.

## `utility_facility_data/02_DATA_REQUEST_FACILITY_MANAGERS.md` ⚑ FIELD-LIST SOURCE OF TRUTH

- **Role:** Draft formal letter to each of the three facility managers requesting facility electrical
  and usage data. **This is the definitive list of what a facility manager is asked for** - Phase 4
  ingestion schema and Phase 5 NFC capture form must match it.
- **Kind:** authored (outbound draft, unsent; three individually addressed copies intended)
- **Reads:** n/a
- **Written by / read by:** feeds `03_TRACKING_REGISTER.md` (Facility-sourced rows) and
  `04_DATA_FLOW_INTO_MODEL.md` (upgrade path).
- **Key contents - EVERY requested field, verbatim, with type/units as stated:**

  **Section "Electrical:" (items 1–5)**

  | # | Field as written | Expected type / units as stated |
  |---|---|---|
  | 1 | "Main service rating (**voltage, amperage**) and **switchgear/panel schedule** for the panel(s) that could serve the parking area" | numeric V + numeric A; plus a document (panel schedule) |
  | 2 | "**Spare breaker positions** and **spare panel capacity**" | count (positions); capacity (units unstated - implicitly A or kW) |
  | 3 | "Any recent **load studies**, or **utility bills covering 12+ months** (**kWh and peak demand kW by month**) if interval data is unavailable" | document; or monthly series: kWh/month + peak kW/month, ≥12 months |
  | 4 | "**Approximate distance** from the electrical room/service to the candidate parking rows" | distance (units unstated - ft/m) |
  | 5 | "Planned **electrical shutdowns, renovations, or capital projects in the next 24 months**" | free text + dates, 24-month window |

  **Section "Facility use:" (items 6–9)**

  | # | Field as written | Expected type / units as stated |
  |---|---|---|
  | 6 | "**Total parking count** and any **counts by lot/row**; **existing ADA space count and locations**" | integer counts; ADA count integer + locations (text/geometry) |
  | 7 | "**Facility activity data: visitor counts** (gate/door counts, program attendance) **by month**, and **typical daily/weekly patterns**" | monthly integer series + qualitative/temporal pattern |
  | 8 | "For any **government fleet vehicles** based at or serving the site: **number, type, and duty cycles (daily mileage, dwell windows)**" | integer count; categorical type; miles/day; dwell window (hours/time-of-day) |
  | 9 | "Any known **site constraints** (drainage, easements, planned repaving - repaving is an opportunity to lay conduit cheaply)" | free text |

  - Line 30: "A **walk-through with your building engineer** would be equally valuable if documents are
    hard to pull." - this is the sentence Phase 5 NFC field capture should anchor on.
  - Line 30: provenance commitment - "We will **label everything you provide with its source and date**,
    and use it only for this planning effort."
- **Notes:**
  - **Nine requested fields total (5 electrical + 4 facility-use).** Units are only fully specified for
    item 3 (kWh, kW) and item 8 (daily mileage). Items 2 and 4 have **no stated units** - Phase 4 must
    fix a unit convention and Phase 5's form must present it, because the source document does not.
  - Note the asymmetry with the Dominion letter: the facility letter asks for **panel/breaker-level**
    detail and **usage/parking/fleet** data; the Dominion letter asks for **service/transformer/feeder/
    interval** data. `04_DATA_FLOW_INTO_MODEL.md` maps them to different `capacity_basis` values.
  - **Consent posture:** the letter is a *request*, not a notification. It nowhere implies charger
    placement is approved. Phase 5 must preserve this - no NFC/field artifact may present placement
    as authorised.

## `utility_facility_data/03_TRACKING_REGISTER.md`

- **Role:** Per-site × per-field status register for the data requests. Blank by design.
- **Kind:** authored (blank fixture/register)
- **Reads:** n/a
- **Written by / read by:** Populated by hand as responses arrive; consumed by `04_DATA_FLOW_INTO_MODEL.md`
  ("Received datum (from register 03)").
- **Key contents:**
  - Line 3, **status vocabulary (5 values):** `not_requested` / `requested` / `received` / `partial` / `declined`.
    "All rows start `not_requested` because nothing has been sent. **Dates are real dates only.**"
  - **Columns (6):** `Field` | `Source (Dominion / Facility)` | `Status` | `Date requested` | `Date received` |
    `Received value / doc reference`. (The FFX002 table header reads `Source (Dominion / Facility)`;
    FFX004 and PWC006 headers read just `Source` - cosmetic inconsistency, lines 7 / 23 / 39.)
  - **Three site sections:** `## FFX002 - City of Fairfax Regional Library` (lines 5–19),
    `## FFX004 - Fairfax County Government Center` (21–35), `## PWC006 - Bull Run Library` (37–51).
  - **The 11 tracked field rows, identical in all three sections, with their source assignment:**
    1. Service rating (V/A/kVA) - Dominion + Facility
    2. Interval load data 12+ mo - Dominion
    3. Spare capacity at peak - Dominion
    4. Transformer/feeder info - Dominion
    5. Service distance to charging area - Dominion + Facility
    6. Panel details / spare positions - Facility
    7. Planned shutdowns/outages - Dominion + Facility
    8. Parking counts (incl. ADA) - Facility
    9. Visitor/activity counts - Facility
    10. Fleet duty cycles (if any) - Facility
    11. Planned capital projects - Facility
  - **Current state: 33 rows (11 × 3 sites), every one `not_requested`, every date and value cell empty.**
  - Line 53: "**Register owner:** [ASSIGN]  **Last updated:** 2026-07-19 (creation; no requests sent)".
- **Notes:** The register's 11 rows are a **condensation** of the two letters' fields, not a 1:1 map.
  Letter-02 item 9 ("site constraints - drainage, easements, planned repaving") has **no row here**;
  letter-02 item 5's "renovations" is folded into rows 7/11. Phase 4's schema should either add a
  `site_constraints` field or note the omission deliberately - the register as written cannot track it.

## `utility_facility_data/04_DATA_FLOW_INTO_MODEL.md` ⚑ PLACEHOLDER→VERIFIED CONTRACT

- **Role:** Defines exactly how received data upgrades the model - the closure mechanism for D1 and the
  "12/12 sites electrically unconfirmed" limitation.
- **Kind:** authored (data-contract-adjacent specification)
- **Reads:** references contract run `milestone2_v3_20260719T052322Z` and contract field names.
- **Written by / read by:** Consumes `03_TRACKING_REGISTER.md`; writes into `data/contract/v1/scenario_table.csv`
  field semantics; MATLAB consumer rule in `contract_manifest.json` depends on `capacity_basis`.
- **Key contents:**
  - **Current state block (lines 9–14) - every claim verified against the contract:**
    - `capacity_basis = placeholder` ✔ (120/120 rows)
    - `capacity_source = "legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)"`
      ✔ **exact string match, 120/120 rows**
    - `capacity_confidence = none` ✔
    - `service_capacity_kw` and `spare_capacity_kw` empty ✔
    - `data_confidence = Low` ✔
  - **Upgrade table (lines 17–25) - datum → contract field(s) → new `capacity_basis`:**
    | Received datum | Contract field(s) updated | New `capacity_basis` |
    |---|---|---|
    | Facility panel/service rating (facility mgr or walk-through) | `service_capacity_kw`; `capacity_source` = document/person + date; `capacity_confidence` | **`verified_facility`** |
    | Utility service rating / transformer / feeder headroom (Dominion) | `service_capacity_kw`, `spare_capacity_kw`; `capacity_source`; `capacity_confidence` | **`verified_utility`** |
    | Interval load data 12+ months | `base_load_kw` replaced (measured profile instead of modeled constant); enables `spare_capacity_kw = service_capacity_kw − observed peak × safety margin` | (whichever supplied the rating) |
    | Service distance / panel details | cost model (trenching/run length - McCoart escalation driver) + layout drawings | n/a (cost inputs) |
    | Parking counts, visitor/activity counts | demand-model calibration; replaces synthetic arrival assumptions; `data_confidence` Low → Medium/High per rubric | n/a |
    | Fleet duty cycles | honest re-scoring of MCDA alternative D | n/a |
    | Planned shutdowns / capital projects | scheduling constraints + conduit-opportunity flags in the staging plan | n/a |
  - **Five rules (lines 29–33), load-bearing for Phase 4/5:**
    1. **Precedence:** `verified_utility` > `verified_facility` > `placeholder`. On conflict, keep both in
       `capacity_source`, **use the more conservative for screening**, and flag for resolution.
    2. **"Every upgrade is re-run, not hand-edited"** - received values enter site inputs, the model re-runs,
       a **new `run_id` is generated**; "**scenario rows are never edited in place.**"
    3. **Provenance:** `capacity_source` must name the **document/person and date** for every non-placeholder
       value; `source_date` updates accordingly.
    4. **Confidence discipline:** `data_confidence` may rise only for sites whose specific fields were
       verified; partial receipt = partial upgrade; the "**0 High-confidence sites**" presentation statement
       changes only when the underlying rows do.
    5. **Ranking sensitivity:** after any capacity verification, re-check ranking + MCDA sensitivity notes;
       a site failing verified-capacity screening triggers documented fallback to the next-ranked site,
       logged in the decision log.
- **Notes:**
  - Rule 2 ("never edited in place, new run_id") is the **single most constraining requirement on Phase 4's
    "living planning system correctable by the field"** and on Phase 5's NFC write-back. A field correction
    cannot mutate `scenario_table.csv`; it must enter as an input and trigger a re-run.
  - `spare_capacity_kw` formula uses an undefined "safety margin" - no numeric value is given anywhere in
    this lane or in `assumptions.json`. Phase 4 must define it.
  - `capacity_basis` enum implied by this file: `placeholder` | `verified_facility` | `verified_utility`.
    `contract_manifest.json` consumer rule 2 names exactly `verified_utility`/`verified_facility`. Consistent.
  - "0 High-confidence sites" is corroborated at `docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:19`,
    `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:52` ("**0 of 12**"), and
    `docs/operations/v4-program/LEDGER.md:240`.

---

# Package 5 - `public_engagement/` (Phase 5 NFC + Phase 9 accessibility)

## `public_engagement/01_SURVEY.md`

- **Role:** The 8-question intercept/online survey for the three top sites. This is the existing survey
  Phase 5 may link to from an NFC tag.
- **Kind:** authored (instrument, undeployed)
- **Reads:** n/a
- **Written by / read by:** Its Q7 feeds `04_LANGUAGE_ACCESS_PLAN.md` ("Survey question 7 is the sensor");
  its responses feed `06_FEEDBACK_TO_DECISION_MATRIX.md`; `05_PRIVACY_NOTICE.md` is printed on the form.
- **Key contents:**
  - Line 1 header: `# DRAFT - PREPARED 2026-07-19 - NOT SENT / NOT DEPLOYED`.
  - Line 5: "Per toolkit §8: **8 questions max**"; deployment mode "**intercept cards + QR to an online
    form**"; "**Spanish version required before deployment**"; "**No PII is required**".
  - Intro text (line 7): "Nothing is decided. Your answers guide siting, layout, and payment design.
    **No name or contact information is needed.**"
  - **The 8 questions with their exact option sets:**
    1. Would you use Level 2 charging at this location? - Yes regularly / Yes occasionally / Not now but if I get an EV / No
    2. When you visit this site, how long do you typically stay? - Under 30 min / 30–60 min / 1–2 hours / 2+ hours
    3. How would you prefer to pay? (multi-select) - Tap credit/debit card (no app needed) / Mobile app /
       Membership-RFID card / Free-other:____ - with the note "*(A no-app option is a design requirement
       we are testing, not an afterthought.)*"
    4. Do you have any accessibility needs we should design for? (e.g. wheelchair access to the charger,
       extra door clearance, cable weight/reach, signage readability) - No / Yes:____
    5. Where in this parking lot would charging work best for you? - Near the entrance / Anywhere is fine /
       Away from the busiest rows / Other:____
    6. Any concerns about chargers here? (multi-select) - Losing regular parking spaces / Safety / Fees-cost /
       Blocked-occupied spaces / None / Other:____
    7. What language do you prefer for information about this project? - English / Español / Other:____
    8. **(Optional)** Your home ZIP code:____ "*(helps us check who the site serves; leave blank if you prefer)*"
  - Line 34: "**Deployment record (BLANK until deployed):** dates, sites, mode (intercept/online),
    responses collected, collector initials:" - empty.
- **Notes:** Q8 (ZIP) is the **only** quasi-identifier collected and it is explicitly optional. Q4 is a
  free-text accessibility field - Phase 5/9 must treat it as potentially sensitive even though the notice
  says no PII is required. Any Phase-5 NFC survey must keep the 8-question ceiling and the anonymity property.

## `public_engagement/02_ACCESSIBLE_USER_REVIEW.md` ⚑ Phase 9 accessibility commitments

- **Role:** Invitation + protocol for a layout review by actual accessible users.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** n/a
- **Written by / read by:** Comments route to `06_FEEDBACK_TO_DECISION_MATRIX.md` (line 29);
  PII posture defers to `05_PRIVACY_NOTICE.md` (line 31).
- **Key contents:**
  - Line 5 context: "ADA EV-space requirements are the documented local cost/schedule driver"; "**The US
    Access Board EVSE rule is still at NPRM stage (no final rule as of 2026-07-19)**, so review by actual
    accessible users against Access Board technical-assistance guidance is our strongest available design check."
    Recipient orgs are placeholders; **no invitation has been sent**.
  - Two offered activities (lines 18–19): (1) **Review layout drawings** - accessible route, space and aisle
    dimensions, charger reach ranges, cable management, bollard placement, signage - paper or video call,
    **30–45 min**; (2) **Join a site walk** at one or more of the three sites, **60 min**, "scheduled at your
    convenience; accessible meeting point at the main entrance."
  - **Commitments to participants (line 21), verbatim:** "Your comments will be recorded verbatim in our
    feedback register, mapped to specific design changes, and reported back to you with what changed and why.
    Participation involves **no obligation and no personal information beyond what you choose to share**."
  - **Protocol (lines 27–31), 5 steps:** materials = dimensioned layout drawing per site + Access Board
    TA-guidance checklist + camera for **(consented) photos** of pinch points; site-walk script = approach
    from parking **and from transit stop**, simulate charge connection at charger height, test door/ramp
    clearances, review **signage sightlines at day and dusk**; capture = one scribe, verbatim, each comment
    gets an ID into `06_FEEDBACK_TO_DECISION_MATRIX.md`; close the loop = written summary of resulting design
    changes to participants, "**disagreements recorded, not smoothed over**"; "**No PII beyond voluntary
    contact for the loop-closing summary.**"
  - Line 33: "**Review record (BLANK until review occurs):** date, site(s), participants (roles only unless
    consented), scribe:" - empty.
- **Notes:** "participants (roles only unless consented)" is a hard constraint for any Phase-9 published
  artifact. The Access Board NPRM date is given as `2024-09-03` in `04_CODE_EDITION_CONFIRMATION_CHECKLIST.md:14`
  and corroborated in `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md:46` (IM-02). Consistent.

## `public_engagement/03_LISTENING_SESSION_ONE_PAGER.md`

- **Role:** Public-facing handout/facilitation guide for a listening session.
- **Kind:** authored (public-facing draft, undeployed)
- **Reads:** n/a
- **Written by / read by:** Points to `05_PRIVACY_NOTICE.md` (printed on the back); links to the survey.
- **Key contents:**
  - Line 5: strategy - "**ride existing civic channels (library boards, district town halls) rather than
    creating new events. Session dates/venues to be arranged - none scheduled yet.**"
  - "### What's decided" → "**Nothing.** No chargers have been approved, funded, or sited. No fees have been
    set. This session happens *before* decisions, which is the point." (lines 13–15)
  - What's proposed (lines 19–22): "**2–3 Level 2 charging ports** at a few high-scoring public sites";
    expandable by design (extra conduit + electrical room in the first dig); "**Everyone can pay:**
    tap-to-pay without a smartphone app is a design requirement"; "**Accessible-first layouts**, reviewed
    with accessible users before construction."
  - Line 20 names both local failure modes: "chargers nobody used (and paid to shut off), and expansions that
    cost multiples because pathways weren't pre-built."
  - What feedback changes (lines 26–29): siting; layout; **fees - "no fee policy exists"**; expansion priorities
    including "areas where EV adoption is currently lower."
  - **Comment channels (lines 33–35):** comment cards (no name required) + open mic; "**[FORMAL MUNICIPAL
    COMMENT CHANNEL - TO BE CONFIRMED]** - formal comments go through accountable municipal channels,
    **not through our project website's assistant, which only explains the project**"; survey
    "(5 min, anonymous, English/Español): **[QR / LINK WHEN DEPLOYED]**".
  - Line 40 facilitator notes: "open with 'what's decided: nothing'; scribe captures comments verbatim…
    **do not promise outcomes; log every comment, including hostile ones.**"
  - Line 41: session record blank.
- **Notes:** The **QR/link slot is empty** - this is the natural hook for a Phase-5 NFC/QR landing page.
  The one-pager also promises the survey is available in **English/Español**, which the language plan says
  has not been produced yet - so deploying the one-pager without the Spanish survey would break its own promise.

## `public_engagement/04_LANGUAGE_ACCESS_PLAN.md` ⚑ Phase 5 multi-language landing pages

- **Role:** Commitments and production register for translated public-facing instruments.
- **Kind:** authored (policy + blank register)
- **Reads:** n/a
- **Written by / read by:** Governs instruments 01, 03, 05 and any posted study signage.
- **Key contents - the six commitments, load-bearing:**
  1. **"Spanish is the minimum, not the ceiling."** All public-facing instruments in the package - **survey (01),
     listening-session one-pager (03), privacy notice (05), and any posted signage about the study** - are
     produced in **English and Spanish before any PWC deployment** (Bull Run Library and any other PWC site),
     **and in Spanish for Fairfax City deployments as well**.
  2. **"Survey question 7 is the sensor."** If responses show meaningful demand for another language at a
     specific site, instruments for that site are translated **before the next engagement round**.
     **Candidate languages to watch: Korean, Vietnamese, Arabic, Urdu** - "driven by data, not assumption."
  3. **Translation quality:** human-reviewed (bilingual team member, municipal language-access staff, or
     professional service) - "**not raw machine output**." Reviewer name and date recorded.
  4. **Live sessions:** interpretation offered on request in session announcements with **[X] business days'
     notice** (the number is an unfilled placeholder); host venue's existing language-access services used
     where available.
  5. **Plain language first:** English source written in plain language; "no jargon ('Level 2 charger' is
     explained once, then used)."
  6. **Accessibility overlap:** **large-print versions of all handouts on request; survey online version
     screen-reader compatible.**
  - **Production register (lines 16–21) - columns:** Instrument | Language | Translated by | Reviewed by |
    Date | Deployed at. **Three pre-seeded rows** (Survey 01 / One-pager 03 / Privacy notice 05, all Spanish)
    plus one empty row. **All cells blank - no translation exists.**
- **Notes:** Languages committed **now: English + Spanish (2)**. Watch-list (not committed): Korean,
  Vietnamese, Arabic, Urdu. Phase 5 multi-language landing pages must ship **en + es** to honour commitment 1,
  and must not ship machine translation (commitment 3). Commitment 6 makes screen-reader compatibility a
  stated obligation for any online survey Phase 5 builds. The `[X] business days'` placeholder in commitment 4
  is an unresolved blank.

## `public_engagement/05_PRIVACY_NOTICE.md` ⚑ VERBATIM COMMITMENTS - Phase 5 NFC must honour

- **Role:** Public-facing privacy notice for the engagement instruments.
- **Kind:** authored (public-facing draft, **NOT PUBLISHED**)
- **Reads:** n/a
- **Written by / read by:** Printed on 01 (survey), on the back of 03 (one-pager), referenced by 02 (§5).
- **Key contents - quoted verbatim (Phase 5 must honour each):**
  - Line 1: `# DRAFT - PREPARED 2026-07-19 - NOT PUBLISHED`
  - Line 5: "*VCDPA-aware notice per toolkit §8 and Report 10. Printed on survey forms, on the
    listening-session handout, and posted on the project website. **Municipal counsel/IT review recommended
    before publication** (VCDPA applicability and municipal records rules - city counsel/IT and county
    counsel/DoIT per the jurisdictional map).*"
  - Line 11: "**No personal information is required to comment.** You can complete the survey, submit a
    comment card, or speak at a session without giving your name, address, email, or phone number. The only
    location question (home ZIP code) is optional and used solely to understand who each site serves."
  - Line 13: "**The website assistant explains - it does not collect.** Our project website's assistant exists
    to explain the study. It is not a channel for formal public comment, and you should not enter personal
    information into it. **Formal comments belong in accountable municipal channels** ([FORMAL CHANNEL(S) TO BE
    CONFIRMED with Fairfax City and Prince William County]), where public-record rules and accountability apply."
  - Line 15: "**What we keep and for how long (retention statement):** Anonymous survey responses and session
    notes are kept for the duration of the fellowship project and any resulting municipal planning use, then
    handled per the applicable municipal records-retention schedule. If you voluntarily give contact information
    (for example, to receive a summary of what changed), it is used only for that purpose, **never sold or shared
    for marketing**, and **deleted when that purpose is complete**. Comments made through official municipal
    channels are governed by those bodies' public-records rules, which may make them public records."
  - Line 17: "**Virginia Consumer Data Protection Act (VCDPA) awareness:** This study is designed to minimize
    data collection so that, for most participants, **no personal data is processed at all**. Where personal
    data is voluntarily provided, **we honor requests to access, correct, or delete it** - contact [PROJECT
    CONTACT CHANNEL TO BE CONFIRMED]."
  - Line 19: "**Photos:** No photographs of identifiable individuals are taken at site walks or sessions
    **without explicit consent**."
  - Line 22: "*Version: draft 2026-07-19. Counsel review: [PENDING - name/date]. Spanish version:
    [PENDING - see language access plan].*"
- **Notes / Phase-5 constraints derived:** (a) no required PII; (b) ZIP optional only; (c) assistant must not
  collect and must not accept formal comment; (d) voluntary contact data is single-purpose and must be deleted
  when that purpose completes; (e) access/correct/delete requests honoured; (f) photo consent explicit;
  (g) **two unfilled placeholders remain: the formal municipal channel(s) and the project contact channel** -
  an NFC tag cannot honour (e) until a real contact channel exists.
  Compare `docs/operations/website-patch-package/content/privacy_notice.md`, which is a **different, website-scoped
  notice** stating the assistant "**is restricted to approved, authenticated users (Cognito)**" and that assistant
  conversations "**may be logged for quality and security**". See finding on the two notices' divergence.

## `public_engagement/06_FEEDBACK_TO_DECISION_MATRIX.md`

- **Role:** Blank traceability matrix mapping every engagement input to a design response.
- **Kind:** authored (blank template)
- **Reads:** n/a
- **Written by / read by:** Fed by 01 (survey), 02 (accessibility review), 03 (session); checked by
  `07_EQUITY_REVIEW_PROTOCOL.md` checklist row 7. Described as "the public-engagement counterpart of the
  client what-changed register and the **G3/G4 traceability evidence**."
- **Key contents:**
  - **Nine columns (line 5):** `#` | `Date` | `Source (survey site / session / accessibility review / other)` |
    `Input (verbatim or aggregated theme, with n if aggregated)` | `Decision area (siting / layout / fees /
    payment / expansion / other)` | `Response (change made or "no change")` | `Reason` | `Where reflected
    (drawing/report/model field)` | `Reported back to participants? (how/when)`.
  - Five empty rows. **Zero data.**
  - Line 13 **aggregation rule:** themes with counts allowed (e.g. "concern: parking loss, n=14") but individual
    verbatim comments that drove a change are quoted. "**No fabricated or illustrative rows - ever.**"
- **Notes:** The `Decision area` enum (siting / layout / fees / payment / expansion / other) is a usable
  controlled vocabulary for a Phase-4/5 feedback ingestion schema.

## `public_engagement/07_EQUITY_REVIEW_PROTOCOL.md`

- **Role:** Protocol pairing the model equity index with real engagement evidence; governs expansion decisions.
- **Kind:** authored (policy + blank checklist)
- **Reads:** cites the contract `equity_indicator` values.
- **Written by / read by:** Depends on 02, 04, 06; feeds expansion-trigger policy.
- **Key contents:**
  - Line 3 **stated numbers:** "The model's equity index exists (**e.g., FFX002 0.66, PWC006 0.614,
    FFX004 0.203**) but reflects data only - no community input yet (G3)."
    **All three verified exactly** against `data/contract/v1/scenario_table.csv` `equity_indicator`:
    FFX002 = 0.66, PWC006 = 0.614, FFX004 = 0.203. ✔
  - **Six principles:**
    1. "**Equity index + engagement evidence, never index alone.**" Until engagement occurs, equity claims are
       labeled "**model-index only, community input pending**."
    2. "**Equity override on expansion triggers.**" At each review cycle **at least one expansion/seed decision
       may be justified on equity grounds even if utilization triggers have not fired**; "Every use - and every
       cycle where it is *not* used - is logged with reasons."
    3. "**Parking displacement is counted and said.**" Each port consumes a general space; site layouts state
       the count of displaced general and ADA spaces.
    4. "**Fees are an equity variable.**" No fee policy is adopted; any future fee proposal triggers a re-run of
       this review and is flagged as a client/board decision.
    5. "**Digital access:** no-app/tap-to-pay capability is a procurement requirement; any vendor exception
       triggers equity review."
    6. "**Language and disability access** per 04 and 02 are preconditions to calling an engagement round complete."
  - **Review checklist (lines 16–24) - 7 checks, columns `Check | Result | Evidence | Date | Reviewer`, all blank:**
    survey covered all top-3 sites incl. lower-index site(s); Spanish instruments deployed where required;
    accessibility review held; equity override considered this cycle (used / not used + reason); parking
    displacement counts stated; fee status re-confirmed; feedback matrix (06) updated and reported back.
- **Notes:** Principle 2 corresponds to `data/contract/v1/assumptions.json` `trigger_policy.equity_override`
  (`enabled: true`, `equity_index_percentile_min: 0.6`, `reduced_utilization_threshold: 0.25`,
  `budget_gate: human_approval_required`). The protocol states the *policy* but **quotes none of the numbers**,
  so there is no contradiction - but also no cross-reference. Phase 4/9 should link them.
  Note also `trigger_policy.policy_status = "proposed_default_pending_team_and_client_adoption"` - the protocol
  correctly does not claim adoption.

## `public_engagement/08_STAKEHOLDER_CONTACT_MAP.md`

- **Role:** Role→organization→named-contact map with an explicit Verified/Placeholder discipline.
- **Kind:** authored (register)
- **Reads:** n/a
- **Written by / read by:** Supplies routing for all outbound packages.
- **Key contents:**
  - Line 3: "Roles are filled only where verified by the evidence base; every unverified name/contact is a
    placeholder the team must fill through real outreach. **Do not guess names into this table.**"
  - **17 rows.** Only **two named individuals** in the entire tree:
    - **[client contact], Green Buildings Manager**, PWC Office of Sustainability - "Verified (interviewed;
      offered follow-up meeting or email)".
    - **[fire-service interviewee]** - "Fire-service perspective (Phase 1 evidence)", organization recorded as
      "[Local fire service - affiliation as recorded in Phase 1 interview]", "(interviewed: **no local EV fires
      yet; recognition/education gap**)", status "Verified as interviewee; **current role/contact to reconfirm
      before reuse**".
  - Rows verified as *offices* but with `[TO BE IDENTIFIED]` contacts: Fairfax City counterpart; Fairfax City
    Fire Marshal; PWC Fire Marshal's Office; Fairfax City Code Administration; PWC Building Development Division;
    Dominion Energy EV programs ("program verified: Level 2 Charging Program active"); **facility managers for
    FFX002, FFX004, PWC006 (all three Placeholder)**; Fairfax City Public Works (VSMP-delegated);
    PWC Environmental Services (VSMP-delegated); disability advocacy org(s); DiscoverE Future City Fellowship staff.
  - "Oversight / funding | PWC Board of County Supervisors; Fairfax City Council (via CIP) | n/a (bodies, not
    contacts) | **Verified as authorities**".
  - Line 24 **update rule:** "a row moves from Placeholder to Verified only with a real name obtained through
    real contact, plus date and source noted in this file."
- **Notes:** ⚑ **Directly Phase-5 relevant:** all three facility-manager rows are Placeholder. **No facility
  manager has been identified, let alone contacted, let alone granted permission.** Any Phase-5 artifact that
  implies a site owner has agreed to charger placement would contradict this file.
  [fire-service interviewee]'s affiliation is a bracketed placeholder even though he is listed as an interviewee - mildly
  awkward but honestly flagged.

---

# Package 3 - `ahj_fire_marshal/` (the walkthrough Phase 5 may support with tags)

## `ahj_fire_marshal/01_QUESTION_SET_FAIRFAX_CITY_FIRE_MARSHAL.md`

- **Role:** 12-question interview set for the Fairfax City Fire Marshal.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** n/a
- **Written by / read by:** companion to 03 (site packet) and 05 (proposed-standard feedback sheet).
- **Key contents:**
  - Line 5 scope: sites in this jurisdiction **FFX002 (rank 1), FFX004 (rank 2 - "confirm whether county
    facilities within city limits fall under city or county fire review"), FFX001 Fairfax City Hall**.
    "Answers are recorded verbatim with respondent name, title, and date; **interpretations by the AHJ govern
    over any code reading in our documents.**"
  - **Section A Code basis (Q1–Q2):** 2021 Virginia SFPC as adopted (2021 USBC effective 2024-01-18, 2020 NEC
    electrical basis); local amendments; 2024 code-development cycle "expected conclusion ≈2027".
  - **Section B Disconnect location, labeling, illumination (Q3–Q5):** for public L2 EVSE "**≤19.2 kW AC
    pedestal units**"; single remote disconnect for a bank; labeling (wording, size, reflectivity,
    photoluminescence); night visibility + acceptance test.
  - **Section C Apparatus access geometry (Q6–Q7):** clearances to fire lanes, hydrants, FDCs, building access
    paths; minimum aisle/turning geometry.
  - **Section D Stormwater / firewater runoff (Q8):** containment/drainage in a suppression event
    (coordination with City Public Works as VSMP authority).
  - **Section E EV-fire pre-planning (Q9–Q10)** - explicitly framed on the [fire-service interviewee] evidence: "no local EV
    fires have occurred yet and… the gap is **recognition/education** rather than incident history."
    Q9 asks whether site pre-plans (charger locations, disconnects, hazard notes) should be **filed with the office**;
    Q10 asks what **crew training/familiarization** is wanted before a public site opens.
  - **Section F Process (Q11–Q12):** review/permit workflow for a **2–3-port municipal pilot**; willingness to
    review the one-page proposed-standard concept (`05_PROPOSED_STANDARD_FEEDBACK_SHEET.md`).
  - Lines 40–42: response record blank (respondent name/title, date, medium, verbatim numbered answers).
- **Notes:** 19.2 kW matches `evse_power_kw = 19.2` in every contract row. ✔
  Q9/Q10 (pre-plans + crew familiarization + charger/disconnect locations) is the strongest hook in the whole
  tree for a **Phase-5 NFC tag at the disconnect** - but note the AHJ has not been asked yet.

## `ahj_fire_marshal/02_QUESTION_SET_PWC_FIRE_MARSHAL.md`

- **Role:** 13-question interview set for the PWC Fire Marshal's Office, with a garage-specific section.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** n/a
- **Written by / read by:** as 01.
- **Key contents:**
  - Line 5 scope: **PWC006 Bull Run Library** (top PWC candidate) and **PWC002 Neabsco-Potomac Commuter Garage**
    ("the county's existing enclosed-garage installation" - matches `site_table.csv` `garage_enclosed = 1.0`
    for PWC002, the only such site ✔).
  - Sections mirror 01 (A code basis; B disconnect; D apparatus access; E stormwater; F pre-planning;
    G process) **plus C Garage conditions (Q6–Q7)**, which states at line 20: "The county already operates
    **70 ports** at the Neabsco-Potomac garage; **17 stations were later taken offline**."
    Q6 asks about ventilation, ceiling-mounted detection/suppression above charging rows, separation from
    exits/stair towers, structural slab; Q7 asks about restrictions by level/proximity to ramps/egress and
    whether added ports at Neabsco would be treated differently from a greenfield surface site.
  - Q12 process: workflow for a 2–3-port county pilot, "interaction with **Building Development Division**".
  - Q11: "would you participate in a **walk-through**?"
  - Lines 46–48: response record blank.
- **Notes:** 70 ports / 17 offline is corroborated by `README.md:25` of the repo root
  ("a 70-port garage installation that ended with 17 stations…") and by
  `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md:13` ("Neabsco; 17 stations removed") and
  `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md:159`. **Consistent across the repo.**

## `ahj_fire_marshal/03_SITE_REVIEW_PACKET_TOP3.md`

- **Role:** Site-fact packet to accompany the question sets; the AHJ-facing statement of the three sites.
- **Kind:** authored (outbound draft, unsent) - but its content is **quoted from the data contract**
- **Reads:** `data/contract/v1/site_table.csv` and `scenario_table.csv` (via run `milestone2_v3_20260719T052322Z`).
- **Written by / read by:** accompanies 01 and 02.
- **Key contents - every value verified against the contract:**
  - Line 5: "Site facts below are from data contract v1 (run `milestone2_v3_20260719T052322Z`). All electrical
    values are model **placeholders pending utility/facility confirmation** - flagged so the AHJ is never shown
    screening values as verified data."
  | Site | Coordinates (doc) | Coordinates (contract) | Starter ports | Pathway | Contract check |
  |---|---|---|---|---|---|
  | FFX002 (rank 1) | 38.847072, −77.30363 | 38.847072, −77.30363 ✔ | 2 × L2 19.2 kW | 8 | `FFX002_2026_baseline` ports_active=2, pathway=8, 19.2 kW ✔ |
  | FFX004 (rank 2) | 38.85404, −77.35706 | 38.85404, −77.35706 ✔ | 3 × L2 19.2 kW | 8 | `FFX004_2026_baseline` ports_active=3, pathway=8, 19.2 kW ✔ |
  | PWC006 (top PWC) | 38.78694, −77.520529 | 38.78694, −77.520529 ✔ | 2 × L2 19.2 kW | 4 | `PWC006_2026_baseline` ports_active=2, pathway=4, 19.2 kW ✔ |
  - All three "Electrical capacity basis" rows read "**PLACEHOLDER - unconfirmed**", basis `contract capacity_basis`. ✔
  - Site types: FFX002 library/surface lot (not enclosed); FFX004 office/government center, surface lot;
    PWC006 library/surface lot - all match `site_table.csv` (`garage_enclosed = 0.0` for all three). ✔
  - Attachment checkboxes (unchecked, per site): site plan / proposed layout with ADA spaces / disconnect
    location sketch - "to be produced".
  - Review request (line 45): AHJ to mark up preferred disconnect location, required apparatus clearances,
    signage/labeling, site-specific conditions, whether a pre-plan filing is desired.
  - Lines 47–53: AHJ response record table blank (FFX002 / FFX004 / PWC006 rows).
- **Notes:** **This is the cleanest number-to-contract traceability in the lane** - every quoted value resolves.
  FFX004's jurisdiction cell is honestly ambiguous: "Fairfax (confirm city vs county fire review authority for
  this facility)". No layout drawings exist yet.

## `ahj_fire_marshal/04_CODE_EDITION_CONFIRMATION_CHECKLIST.md`

- **Role:** Converts the team's researched code basis into AHJ-confirmed fact, per jurisdiction.
- **Kind:** authored (blank checklist)
- **Reads:** cites `Current-Facts register IM-03`.
- **Written by / read by:** gates how code values may be labeled in artifacts.
- **Key contents:**
  - Line 3 working basis: "**2021 Virginia USBC effective 2024-01-18, 2020 NEC electrical basis, VCC §406.2.7
    EV provisions, 2021 SFPC for fire; permits solely under 2021 USBC since 2025-01-18; 2024 code-development
    cycle underway (expected ≈2027)**." **Verified against `docs/methodology/current-facts-source-register.md:9`
    (IM-03) - exact match**, including the 2025-01-18 permits-only date. ✔
  - Two identical tables (Fairfax City, Prince William County), columns `Item | Working assumption | Confirmed
    value | Confirmed by (name/title) | Date`. **7 rows each, all Confirmed cells empty:**
    Building/electrical code edition (2021 USBC, 2020 NEC basis); Fire code edition (2021 SFPC);
    EV provisions applied (VCC §406.2.7); Local amendments affecting EVSE (none known);
    EV-ready interpretation - Fairfax row adds "**'sufficient EV charging', AFDC listing 12646 ambiguity -
    confirmed by client**"; ADA/accessibility basis - "USBC ADA provisions now; **Access Board EVSE NPRM
    (2024-09-03) not final as of 2026-07-19**"; Anticipated 2024-cycle changes (none assumed).
  - Line 29 **rule:** "until a row is confirmed, artifacts must continue to label the value as
    '**researched, AHJ confirmation pending**'."
- **Notes:** The two jurisdiction tables differ only in the two noted cells (AFDC listing 12646 mention and
  "NPRM tracked" wording) - likely intentional. `AFDC listing 12646` is the only external identifier in the file.
  Line 29's rule is a hard labeling constraint for Phase 9 friendlier framing: the friendly text may not drop
  "AHJ confirmation pending".

## `ahj_fire_marshal/05_PROPOSED_STANDARD_FEEDBACK_SHEET.md`

- **Role:** One-page ask for AHJ practitioner reaction to the team's proposed municipal EV standard concept,
  focused on Module M1.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** points at `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` (**file exists** ✔).
- **Written by / read by:** referenced by 01 (Q12) and 02 (Q13); its answers "feed into **C7 test-parameter table**".
- **Key contents:**
  - Line 5: "This is a **student fellowship concept, not a code proposal before any body**."
  - Scope quoted: "public municipal charging sites (new and retrofit), **L1/L2 AC (DC annex reserved)**."
  - Three modules as presented to the AHJ:
    - **M1 - Emergency access & disconnect (flagship, most testable):** apparatus approach dimensions;
      disconnect location/labeling/illumination/operation time; responder signage.
    - **M2 - Expandability & right-sizing documentation:** pathway capacity declaration; utilization-monitoring
      capability; documented expansion triggers; **load-management fail-safe behavior on communications loss**.
    - **M3 - Accessibility & site conditions cross-references:** accessible route/space conformance by reference
      to Access Board guidance; impact protection; enclosure/garage conditions; stormwater/firewater planning note.
  - **Six questions**, notably Q2: "What **measurable pass/fail values** would you set for: maximum distance from
    apparatus position to disconnect; **disconnect operation time**; **signage legibility distance at night**?"
    and Q3: "Would an **M1-style commissioning test (witnessed disconnect operation + signage check before
    energization)** be practical within your current inspection workflow?"
  - Response record blank, including "Suggested parameter values (feed into C7 test-parameter table)".
- **Notes:** ⚑ **Module numbering does not match the concept document.** `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md`
  defines **seven** modules (1 Emergency access; 2 Expandability & right-sizing; 3 Accessibility & site-condition
  cross-references; 4 Monitoring and expansion triggers; 5 Managed-charging fail-safe; 6 Commissioning and evidence
  package; 7 Materials, take-back, end of life). The feedback sheet's "M2" bundles concept Modules 2 + 4 + 5, and
  its Q4 asks about "**M2's 'fail-safe on comms loss'**" - which in the concept is **Module 5**, not Module 2.
  See findings.

---

# Package 1 - `client_meeting_2/`

## `client_meeting_2/01_EMAIL_DRAFT_TO_CLIENT.md`

- **Role:** Ready-to-send request to [client contact] for a 30-minute follow-up (or email exchange) before M2.
- **Kind:** authored (outbound draft, unsent)
- **Key contents:** Header `DRAFT - PREPARED 2026-07-19 - NOT SENT`; blockquote instruction (line 3) - team must
  "confirm [client contact] is the designated client for CM2 purposes, insert the interview date, choose sender, and send.
  **Do not remove blanks before the facts exist.**" Quotes [client contact] verbatim: "either one, follow up meeting, or
  emails is fine." States the narrowed focus: "**12 public sites** across Fairfax City and Prince William County,
  with **three top candidates**, and we have developed and compared **seven distinct solution alternatives**."
  Requests **30 minutes** before **Tuesday, July 21**, with a 4-item time-boxed structure (3–10 / 10–18 / 18–25 /
  25–30 min) and the fleet-hub framing "**~35-station fleet hub track**". Offers the structured-email alternative
  (two-page pre-read + five questions). Pre-read sent ≥24 h ahead. Attachment noted: `02_CLIENT_PREREAD.md` as PDF.
  Live blanks: `[TEAM SENDER NAME]`, `[INTERVIEW DATE]` (×1), `[PROPOSED DATE/TIME OPTIONS]`.
- **Notes:** 12 sites ✔ (`site_table.csv` = 12 rows). Seven alternatives ✔ (A–G in 04 and in the MCDA).

## `client_meeting_2/02_CLIENT_PREREAD.md` ⚑ contains the headline numbers

- **Role:** Two-page pre-read: problem recap, narrowed focus with numbers, alternatives, the five questions.
- **Kind:** authored (outbound draft, unsent)
- **Reads:** quotes contract-derived NPV / ports values.
- **Key contents and their traceability:**
  - Line 9 problem recap - client evidence numbers: "**McCoart 10-port trenching**"; "**Neabsco garage: 70 ports,
    17 stations later taken offline at roughly $1,000/station/yr**"; "**12 public candidate sites**"; "models
    demand and capacity at **10/20/30-year horizons**"; "**seven** genuinely distinct deployment strategies."
  - Top-3 table (lines 15–19), column header "**10-yr cost screen (NPV)**":
    | Site | Rank | Starter ports (pathway) | doc NPV | contract value | verdict |
    |---|---|---|---|---|---|
    | FFX002 | 1 | 2 (8) | ≈ **$134k** | `FFX002_2036_*` `lifecycle_cost_npv_usd = 133641.0` | ✔ traces (plus10 / 2036) |
    | FFX004 | 2 | 3 (8) | ≈ **$166k** | `FFX004_2036_*` = 166275.0 | ✔ traces |
    | PWC006 | top PWC | 2 (4) | ≈ **$148k** | `PWC006_2036_*` = 147663.0 | ✔ traces |
    All three "Readiness / confidence" cells read "Electrical capacity **unconfirmed (placeholder)**;
    data confidence **Low**" ✔ (contract: `capacity_basis=placeholder`, `data_confidence=Low`).
  - Line 21: "**All cost and capacity figures are screening values** - synthetic-demand model outputs with
    placeholder electrical capacity and benchmark costs, suitable for ranking and sizing conversations,
    **not for budgeting**."
  - Alternatives condensation to 4 rows (staged pilots leader / hybrid close second / EV-ready first /
    centralized fleet hub as "the county's own **~35-station** in-design track").
  - **The five questions (lines 34–38):** (1) public vs fleet vs both for next 24 months; (2) does the in-design
    fleet hub change what you need from public sites; (3) **geographic equity of access vs utilization-proven
    expansion**; (4) budget envelope and funding route (CIP, Dominion program, grant) for a 2-port pilot;
    (5) what would make you say "no" to the top-ranked site.
  - Line 42: answers set (a) which alternative is finalized + fleet-hub framing; (b) top-3 priority order;
    (c) **the equity weighting** (Q3 "can change our ranking"); (d) funding pathway; (e) site-level veto conditions.
    "Every answer is logged in our decision log with the design change it caused - **feedback that changes
    nothing is recorded too, with the reason**."
- **Notes:** ⚑ The NPV numbers are correct but the **labels are legacy-relative**: "10/20/30-year horizons" (line 9)
  and "10-yr cost screen (NPV)" (line 15). The canonical convention is 2026/2036/2046/2056 and the underlying
  contract rows are `horizon_label = plus10` / `horizon_year = 2036`. See findings.

## `client_meeting_2/03_MEETING_AGENDA.md`

- **Role:** Minute-by-minute 30-minute agenda with the compliance criterion each block serves.
- **Kind:** authored (draft, unsent)
- **Key contents:** Blocks (Min | Item | Compliance purpose): `0–3` recap + what your feedback changed
  (trenching → pathway oversizing; Neabsco → staged triggers; Animal Services → EV-ready option) → **A4**;
  `3–10` narrowed focus, 12-site screening, top-3 FFX002/FFX004/PWC006, "screening-value caveats stated" → **A2**;
  `10–18` alternatives on one slide, the pivotal question "**which would you rule out, and why?**", client may add
  alternatives → **A3**; `18–25` structured feedback incl. "**what would you never approve?**" and priorities
  ranking (**cost / equity / speed / fleet-coordination / visibility**) → **A4, G5**; `25–30` asks →
  **D1 pipeline**. Roles to assign: Presenter (narrowed focus), Presenter (alternatives), Scribe (verbatim into
  form 05), Timekeeper - all `[NAME]`. Line 21: async substitution rule (pre-read + five questions replace
  items 3–25; verbatim replies into 05).
- **Notes:** The priorities enum (cost / equity / speed / fleet-coordination / visibility) recurs in 05 - a stable
  controlled vocabulary.

## `client_meeting_2/04_ALTERNATIVES_BRIEFING.md`

- **Role:** Plain-language client-facing description of all seven alternatives A–G.
- **Kind:** authored (draft, unsent)
- **Key contents:**
  - Line 5 format contract: "name → one-sentence concept → what you'd see in year 1 → **10-yr cost order** →
    main risk → what evidence would change our mind. **No jargon.** The county's fleet hub is presented as
    '**your parallel track we coordinate with**,' never as a competing recommendation. All seven researched
    alternatives are shown here for completeness; **the client slide condenses to four rows**."
  - **A** Broad immediate distributed buildout - highest 10-yr cost of the public options; risk "Repeating
    Neabsco - paying to install, then paying (**~$1,000/station/yr scale**)".
  - **B** Staged distributed pilots with expandable pathways - "***our current leader***"; year 1 = "2–3 working
    ports at each of up to three sites"; risk = slower geographic reach.
  - **C** EV-ready first - "your Animal Services Center pattern"; risk "the **Animal Services conduit still has
    no charger**"; "**A budget collapse - this is the floor option.**"
  - **D** Centralized fleet hub + selective public - "***your parallel track we coordinate with***";
    "**~35-station fleet hub now in design**"; risk = ADA space-clustering redesign cost + absent fleet duty-cycle data.
  - **E** Managed-charging-first - "not a siting strategy by itself"; "this layers onto B/F as ports multiply."
  - **F** Hybrid portfolio - "***close second***" (B spine + C seeding + E operating layer, coordinated with D);
    "If **geographic equity outweighs utilization-proven expansion** in your priorities, this overtakes B."
  - **G** Do nothing / defer - "honest comparator", "**Zero direct cost; wasted proactive-planning window**
    (our fire-service interviewee's point)"; "it exists so the comparison is honest."
- **Notes:** ⚑ "**10-yr cost order**" appears **7 times** (lines 5, 11, 19, 27, 35, 43, 51, 59). Same legacy-relative
  labelling issue as the pre-read. All are *ordinal* statements ("highest", "lowest", "slightly above B") -
  no numbers - so the risk is convention drift in language, not wrong figures.
  F's "overtakes B" claim here is qualitative and consistent with 02_PROVISIONAL_MCDA / 04_WEIGHT_ADOPTION_PAGE,
  but see the crossover-arithmetic finding.

## `client_meeting_2/05_CLIENT_FEEDBACK_FORM.md`

- **Role:** Blank verbatim-capture form for the touchpoint.
- **Kind:** authored (blank template)
- **Key contents:** Line 3: "**Verbatim means verbatim - quote, do not paraphrase.** All fields intentionally
  blank until the touchpoint occurs." **Nine capture fields:** Date/attendees/duration/medium; Narrowed focus
  presented? (slide #, reaction verbatim); Alternative preferred / ruled out (verbatim + why); Objections raised;
  **Priorities (rank: cost / equity / speed / fleet-coordination / visibility)**; Approval boundaries ("would
  never approve…"); New information provided (data, contacts, constraints); **Explicit adoptability signal
  (verbatim quote)**; Design changes we will make because of this meeting. Plus "Scribe name / date completed:".
  **All empty.**
- **Notes:** "Explicit adoptability signal (verbatim quote)" is the G5 evidence field.

## `client_meeting_2/06_DECISION_LOG.md`

- **Role:** Blank feedback→decision traceability log.
- **Kind:** authored (blank template)
- **Key contents:** **Six columns:** `#` | `Date` | `Input (who/what)` | `Decision affected` |
  `Change made / rejected + reason` | `Owner`. Five empty rows. Line 3: "One row per input that affected
  (**or explicitly did not affect**) a decision. Rows are added only as real inputs occur."
- **Notes:** Distinct from 07 - 06 is any input, 07 is specifically client-feedback→design.

## `client_meeting_2/07_WHAT_CHANGED_REGISTER.md`

- **Role:** Blank register mapping client feedback to design change; "**this register is the A4 evidence artifact**".
- **Kind:** authored (blank template)
- **Key contents:** **Seven columns:** `#` | `Client feedback (verbatim or tightly quoted)` | `Date received` |
  `Design element affected` | `Change made (or "no change")` | `Reason` | `Where reflected (slide/report/model field)`.
  Five empty rows. "including 'no change, because…'".
- **Notes:** Structurally parallel to `public_engagement/06_FEEDBACK_TO_DECISION_MATRIX.md` (which explicitly calls
  itself "the public-engagement counterpart of the client what-changed register").

## `client_meeting_2/08_ATTENDANCE_RECORD.md`

- **Role:** Blank attendance record for the touchpoint.
- **Kind:** authored (blank template)
- **Key contents:** Header fields Date / Start-end time / Medium (in person / virtual / email exchange) /
  Location or platform. Table `Name | Role / affiliation | Present (Y/N)` **pre-seeded with six names**:
  [client contact] (Green Buildings Manager, PWC Office of Sustainability), Anna, Laylas, Andy, Adama, Paula
  (all "Team"), plus a spare blank row. **All Present cells empty.** Async fallback line: "thread subject line,
  date of question set sent, date(s) of replies received". "Recorded by / date:".
- **Notes:** The only place in the tree where all five team first names appear as a table. No surnames for the
  students - good privacy hygiene.

## `client_meeting_2/09_FOLLOWUP_EMAIL_DRAFT.md`

- **Role:** Post-meeting thank-you/summary template, to be filled only from real verbatim content.
- **Kind:** authored (draft, unsent)
- **Key contents:** Line 3: "Send **only after** the touchpoint actually occurs. Every [bracketed] slot must be
  filled with **verbatim** content from the completed feedback form (05) - no paraphrase, no invention.
  **If a slot has no real content, delete the sentence rather than fabricate.**" Bracketed slots:
  `[DATE]` (×2), `[meeting with / corresponding with]`, `[NARROWED FOCUS AS ACTUALLY PRESENTED]`,
  Preferred option "[VERBATIM]", Ruled out/objections "[VERBATIM]", Approval boundaries "[VERBATIM]",
  Priorities ranking `[AS CAPTURED]`, `[SPECIFIC DESIGN CHANGES FROM 07_WHAT_CHANGED_REGISTER - or state
  honestly that no changes resulted and why]`, `[DATA / CONTACT OFFERS AS ACTUALLY MADE]`, `[TEAM SENDER NAME]`.
  Line 26: "Our Milestone 2 presentation on July 21 will reflect this discussion, and we would welcome any
  corrections to this summary."
- **Notes:** Best example in the tree of the "delete rather than fabricate" discipline.

## `client_meeting_2/10_ACCEPTANCE_CHECKLIST.md`

- **Role:** Evidence checklist that closes CM2 (A1–A4, G5) - and the classification gate.
- **Kind:** authored (blank checklist)
- **Key contents:**
  - **Synchronous meeting record (8 unchecked items):** dated invite/email thread; pre-read as sent with
    sent date/time; attendee list (08 completed); completed feedback form (05, verbatim); decision-log entries (06);
    what-changed entries (07); follow-up email sent (09, with sent date); **"Slide/screenshot of exactly what was
    shown to the client"**.
  - **Asynchronous substitute rule (5 items):** the question set as sent (pre-read + five questions, dated);
    "**[client contact]'s verbatim replies (the thread itself, preserved unedited)**"; feedback form from those replies;
    decision-log + what-changed entries; follow-up summary email sent and corrections received.
  - **Classification gate (2 items):** team has confirmed with fellowship staff (`../fellowship_confirmation/`)
    whether this touchpoint completes CM2, and recorded the answer; "A1 status updated in the compliance tracking
    **only after** the above: **prior interview = strong client evidence; interview + this documented touchpoint =
    CM2 complete**."
  - Line 31 **integrity note:** "if the touchpoint does not occur before July 21, the presentation states honestly
    that CM2 completion is scheduled/requested and shows these instruments as process evidence - **it does not
    claim the meeting happened**."
- **Notes:** The `../fellowship_confirmation/` relative link resolves ✔.

---

# Package 6 - `fellowship_confirmation/`

## `fellowship_confirmation/01_EMAIL_DRAFT_FELLOWSHIP_STAFF.md` ⚑ horizon-year question lives here

- **Role:** Four clarification questions to DiscoverE / Future City Fellowship staff.
- **Kind:** authored (outbound draft, unsent)
- **Key contents:**
  - **Q1 CM2 classification:** the [client contact] interview covered county EV history, costs, code experience, "**However,
    that interview did not include presenting our narrowed focus or brainstorming our solution alternatives with
    him - the defined CM2 content.** Does the interview count as Client Meeting #2, or is a follow-up touchpoint
    required?"
  - **Q2 process evidence:** is a scheduled-but-not-held touchpoint plus documented instruments acceptable
    Phase 2 process evidence, with the outcome reported afterward?
  - **Q3 Horizon years (line 15), verbatim:** "The milestone documents ask for modeling '**in 10, 20, and 30-year
    timelines.**' **Are exact calendar years required (e.g., 2036/2046/2056), or only consistent 10/20/30-year
    intervals from a stated baseline?**"
  - **Q4 ULSE standards count:** challenge statement says "choosing at least two to highlight"; Phase 2 rubric rows
    say "at least one" (safety) and "at least one" (sustainability). Team is prepared to present two + one proposed.
  - Response record blank (date sent / date answered / respondent / verbatim numbered answers).
- **Notes:** **Q3 is the correct, properly-scoped legacy reference.** The "10, 20, and 30-year timelines" phrasing
  is explicitly quoted as *the fellowship's own wording being questioned*, and the canonical answer 2036/2046/2056
  is given in the same sentence. This is **not** a horizon-convention defect.

## `fellowship_confirmation/02_CONTINGENCY_SUMMARY.md`

- **Role:** What the team does under each possible answer to Q1–Q4; every branch has a conservative default.
- **Kind:** authored
- **Key contents:**
  - **Q1:** If YES → reclassify A1 toward HAVE, still hold the follow-up. If NO → execute `../client_meeting_2/`
    (email 01 → pre-read 02 → touchpoint → capture 05–08 → follow-up 09 → checklist 10) and present honestly:
    "strong client evidence; CM2 completion requested/scheduled." **Default: treat as NO** (Report 02 ruling 5).
  - **Q2:** If YES → present instruments + scheduled touchpoint, report outcomes in a post-meeting addendum and at
    Milestone 3. If NO → prioritize completing the touchpoint before July 21 via the email-exchange path.
    Default: pursue completion regardless.
  - **Q3 (lines 17–21) - the horizon convention branch:**
    "If intervals suffice: Keep the current consistent **2026 baseline + 2036/2046/2056 set** (already the cleanest
    compliance) and state the baseline convention; no rework."
    "If exact named years are required: … **the pipeline already produces 2036/2046/2056**, so relabeling/re-running
    to any named convention is model-arithmetic work (B3/B5/B6 path)."
    "**Until answered (default): Present 2026 + 2036/2046/2056 with the baseline convention stated explicitly** -
    defensible under both readings (Report 02 ruling 1)."
  - **Q4:** If TWO → **UL 2594 (safety, AC EVSE) + UL 3600 (sustainability, circular economy)** + the one proposed
    standard with tests. If ONE → present the same two anyway. Default: two.
- **Notes:** ✔ **Fully canon-compliant on horizons** - 2026 baseline + 2036/2046/2056, matching
  `contract_manifest.json` `conventions`. UL 2594 / UL 3600 match
  `docs/methodology/current-facts-source-register.md:10–11` (IM-04, IM-05) and
  `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md:14–15`. ✔
  This file is the strongest positive precedent in the lane for how a legacy interval reference *should* be handled.

---

# Package 2 - `team_alternatives_session/`

## `team_alternatives_session/01_FACILITATION_GUIDE.md`

- **Role:** 60–90-minute facilitation script for the team session that closes A5–A8, B7, F2.
- **Kind:** authored
- **Key contents:**
  - Line 3: "**This session has NOT been held.** Holding it - with all five members if possible, before July 21 -
    is the only honest way to close criteria A5, A6, A7, A8, B7, and F2. Per Report 04 §5.
    **A retroactive record without a real session is prohibited.**"
  - Participants Anna/Laylas/Andy/Adama/Paula; Facilitator `[ASSIGN]`, Scribe `[ASSIGN]`.
    Materials: this package, "the MCDA CSV", `../client_meeting_2/04_ALTERNATIVES_BRIEFING.md`.
  - **Block 1 - Free brainstorm (15 min) → A5.** "**every** idea is recorded, including bad, duplicate, and
    immediately discarded ones. Discarded ideas are marked 'discarded + reason', **never deleted**."
    "**Do not open the provisional MCDA before this block ends (avoid anchoring).**"
  - **Block 2 - Confirm/amend alternatives (15 min) → A6.** Are A–G genuinely distinct? merged/split/renamed/added?
  - **Block 3 - MCDA walk (30 min) → A7, B7.** MCDA presented "explicitly as **PROVISIONAL**". Adopt/amend weights
    first via 04, "including **reading aloud the equity-weighting crossover disclosure** before deciding".
    "**Any member may re-score any cell** by stating a reason." "**Dissent is recorded, not resolved away**…
    **Consensus is not required; documentation is.**" Recompute weighted totals before Block 4.
  - **Block 4 - Adopt winner + conditions (10 min) → A8, feeds G5, F2.** Winner "**which may or may not be the
    researched leader B**", adopted **with conditions**; signed/initialed. Confirm funding/budget framing
    (**F2 linkage: FY2027 adopted budgets, Dominion make-ready, NEVI-with-caveat**).
  - Required outputs: one slide (alternatives + adopted winner) for the July 21 deck; one backup table (full adopted
    matrix); completed dated attendee-named session record = 03 + 04 + 05 + 06 + 07.
  - Line 42: "60 minutes minimum (15+15+30 compressed +10); 90 minutes preferred."
- **Notes:** Block timings 15+15+30+10 = 70 min, so "60 minutes minimum" requires the stated compression.
  "the MCDA CSV" is `SOLUTION_ALTERNATIVES_MCDA.csv`, which 02 says is **not tracked in this repository** -
  confirmed absent (`find -iname "*MCDA*"` returns only `02_PROVISIONAL_MCDA.md` and
  `presentation/assets/10_mcda_provisional.png`). The material list therefore points at a file the team cannot
  open from the repo.

## `team_alternatives_session/02_PROVISIONAL_MCDA.md` ⚑ contains an arithmetic error

- **Role:** The provisional 7-alternative × 6-criterion MCDA matrix the team must review, amend, and adopt.
- **Kind:** authored, derived from an **untracked** research CSV
- **Reads:** "`SOLUTION_ALTERNATIVES_MCDA.csv` (**pre-V3 research archive, not tracked in this repository**;
  researched scores, 0–5 anchored)".
- **Written by / read by:** consumed by 03 (scoring sheet), 04 (weights), 07 (decision record);
  visualised at `presentation/assets/10_mcda_provisional.png`.
- **Key contents:**
  - Header line 1: `# PROVISIONAL - TEAM MUST REVIEW/AMEND/ADOPT`.
  - **Weights (sum 100):** Safety / code readiness **25**; Demand fit / service quality **20**;
    Lifecycle cost / funding **20**; Expandability / resilience **15**; Equity / public value **10**;
    Data confidence / implementation risk **10**.
  - **Matrix (scores 0–5, weighted /100):**
    | Alt | Alternative | Saf | Dem | Cost | Exp | Eq | Conf | Weighted (published) | Rank | Recomputed |
    |---|---|---|---|---|---|---|---|---|---|---|
    | A | Broad immediate distributed buildout | 2 | 2 | 1 | 3 | 4 | 1 | 41.0 | 6 | 41.0 ✔ |
    | B | Distributed staged pilots + expandable pathways | 4 | 4 | 5 | 5 | 3 | 4 | **85.0** | **1** | 85.0 ✔ |
    | C | EV-ready first, limited active EVSE | 4 | 2 | 4 | 5 | 2 | 4 | 71.0 | 4 | 71.0 ✔ |
    | D | Centralized fleet hub + selective public | 3 | 3 | 3 | 3 | 2 | 3 | 58.0 | 5 | 58.0 ✔ |
    | E | Managed-charging-first | 4 | 3 | 4 | 4 | 3 | 3 | 72.0 | 3 | 72.0 ✔ |
    | F | Hybrid portfolio (B + C + E, coordinated with D) | 4 | 4 | 4 | 5 | 4 | 3 | 81.0 | 2 | 81.0 ✔ |
    | G | Do nothing / defer (comparator) | 3 | 0 | 3 | 1 | 0 | 5 | **37.0** | 7 | **40.0 ✗** |
  - Evidence notes per row: A "Contradicted by the client's own Neabsco experience (70 ports, 17 stations later shut
    off, ~$1k/station/yr); **12/12 sites electrically unconfirmed**; single-digit simulated utilization";
    C "Mirrors the PWC Animal Services Center pattern (EV-ready conduit, no charger yet)";
    D "PWC is already pursuing a **~35-station fleet hub**… fleet duty-cycle data absent";
    E "The MATLAB model already illustrates managed vs unmanaged load";
    F "more moving parts to explain and govern in a **12-minute presentation**".
  - **Known sensitivities:** "**Equity crossover:** at roughly **2× the default equity weight (~20 vs 10)**,
    **F overtakes B**"; "Faster near-term adoption evidence improves F and A (A still cannot win while all 12 sites
    lack electrical confirmation)"; "A client priority on fleet over public makes D the frame"; "Budget collapse
    makes C the floor option."
- **Notes:** See findings - G's weighted total and the equity crossover both fail to reproduce.

## `team_alternatives_session/03_TEAM_SCORING_SHEET.md`

- **Role:** Blank sheet to record any cell the team re-scores, and the recomputed adopted totals.
- **Kind:** authored (blank template)
- **Key contents:** Session date + Attendees blanks. Score-changes table columns: `Alt` | `Criterion` |
  `Provisional score` | `Team score` | `Proposed by` | `Reason (required)` - **8 empty rows**.
  Line 20: "*(No rows filled = team adopted all provisional scores unchanged - state that explicitly below.)*"
  with checkbox "[ ] Team adopted all provisional scores unchanged (initials: ______)".
  **Line 26 states the formula: "Weighted score = Σ (score × weight) / 5, out of 100."**
  Recomputed-totals table rows A–G, all blank. "Computed by: ______  Checked by: ______".
- **Notes:** This file supplies the formula that proves 02's G row is wrong (Σ(score×weight)/5 = 200/5 = 40.0, not 37.0).

## `team_alternatives_session/04_WEIGHT_ADOPTION_PAGE.md` ⚑ mandatory disclosure

- **Role:** Weight adoption page with a disclosure the facilitator must read aloud before the vote.
- **Kind:** authored (blank template + policy)
- **Key contents:**
  - Line 7 **MANDATORY DISCLOSURE - equity-weighting crossover, verbatim:** "The default weights place equity at
    10/100. Sensitivity analysis (**Report 04 §2**) shows that at roughly **2× the default equity weight (~20/100)**,
    the **Hybrid portfolio (F) overtakes Staged pilots (B)** as the winner, because F carries broader geographic
    value via EV-ready seeds at lower-tier sites. In other words: **the choice of equity weight can decide the
    outcome.** The team must choose the weight deliberately, knowing this, and may revisit it after the client
    answers priority question Q3 (equity of access vs utilization-proven expansion)."
  - Default-weights table (Safety 25 / Demand 20 / Cost 20 / Expand 15 / Equity 10 / Confidence 10,
    **Total must = 100**) with `Adopted weight` / `Changed? (Y/N)` / `Reason if changed` columns - all blank.
  - "Disclosure read aloud before adoption: [ ] (facilitator initials: ______)"; "Adopted by (initials of all
    present)"; "Date"; dissents → `05_DISSENT_LOG.md`.
- **Notes:** See findings - the "2×" crossover does **not** reproduce from the published matrix.

## `team_alternatives_session/05_DISSENT_LOG.md`

- **Role:** Blank verbatim dissent log.
- **Kind:** authored (blank template)
- **Key contents:** Line 3: "**Dissent is recorded, not resolved away.** … **A recorded dissent does not block
  adoption - it makes the record honest.** Empty log after a real session = state 'no dissents recorded' with
  initials." Columns: `#` | `Member` | `Item dissented (weight / score cell / adoption)` | `Dissent (verbatim)` |
  `Alternative they would prefer` | `Acknowledged by facilitator (initials)` - 3 empty rows.
  Checkbox "[ ] No dissents were recorded in this session (scribe initials: ______)". Session date blank.
- **Notes:** Deliberately distinguishes "no session yet" (blank, unchecked) from "session held, no dissents"
  (checked with initials) - a genuinely careful design.

## `team_alternatives_session/06_COI_ASSUMPTION_NOTE.md`

- **Role:** Standing-assumption disclosure + per-member conflict-of-interest declarations.
- **Kind:** authored (policy + blank template)
- **Key contents:**
  - **Five standing assumptions the scoring inherits (from Report 04 §3):**
    1. "Scores assume **no battery storage (BESS)** in scope - true of the current candidate set
       (`battery_storage_flag=0` at all 12 sites). If BESS enters scope, safety scoring must be redone
       (**UL 9540/9540A, NFPA 855** become active)." - **verified: `battery_storage_flag = 0` for all 12 rows of
       `data/inputs/real_sites_v2.csv`** ✔
    2. "Cost scores use **client cost evidence + AFDC/NREL benchmarks, not site quotes** - screening-class only."
    3. "Equity scores reflect the **model equity index only**; no community input exists yet (G3 gap)."
    4. "Alternative D's score would change materially with **fleet duty-cycle data**, which is currently absent."
    5. "All demand figures are **synthetic/uncalibrated**; all electrical capacity is **placeholder**."
  - **Declarable-interest examples (line 15):** "authorship of a specific artifact being scored (e.g., **builder of
    the platform or MATLAB model may favor alternatives showcasing it**); prior public statement of a preferred
    option; presentation-role stakes."
  - Member declaration table (Anna / Laylas / Andy / Adama / Paula), columns `Declared interest / potential bias
    (or "none")` and `Effect on participation (none / abstain from cell X / noted only)` - **all blank**.
- **Notes:** Assumptions 2 and 5 match `assumptions.json` (`demand_model.status = "synthetic_uncalibrated"`,
  `economics.provenance` "screening/planning benchmarks (AFDC/NREL cost classes + client operating evidence).
  None are quotes, budgets, or engineering estimates", `capacity` "service/spare capacity NULL with
  capacity_basis=placeholder at all 12 sites"). ✔ Fully consistent.

## `team_alternatives_session/07_DECISION_RECORD_TEMPLATE.md`

- **Role:** The signed adopted-decision record - "the **A8 evidence artifact** and the **F2 linkage record**",
  also carrying the A5/A6 session record.
- **Kind:** authored (blank template)
- **Key contents:** Session date / location-medium / duration / attendees / facilitator / scribe - all blank.
  **§1 Brainstorm record (A5)** - 4 empty bullets, "including discarded ones (verbatim; mark discarded ideas
  'discarded + reason')". **§2 Alternatives confirmation/amendment (A6)** - table `Alternative | Confirmed /
  amended / added / removed | Reason` with a pre-seeded row "A–G as researched". **§3 Adopted comparison (A7, B7)** three attachment checkboxes referencing 04, 03, 05. **§4 Adoption (A8)** - "Adopted leading solution:"
  (blank), "Conditions attached to the adoption", "**Client input that could change this adoption (feeds G5 -
  revisit after the CM2 follow-up)**", "Funding/budget framing confirmed for the presentation (F2)".
  **§5 Presentation outputs assigned** - alternatives+winner slide owner; backup full-matrix table owner;
  "**Paula's presentation role (assign here if still open)**". **Signatures/initials table** for all five members
  with Initials and Date columns - **all blank**.
- **Notes:** All three internal relative references (`04_WEIGHT_ADOPTION_PAGE.md`, `03_TEAM_SCORING_SHEET.md`,
  `05_DISSENT_LOG.md`) resolve ✔.

---

# FINDINGS SUMMARY (detail in the structured return)

1. **HIGH - Alternative G's weighted MCDA score is arithmetically wrong.**
   `02_PROVISIONAL_MCDA.md:28` publishes 37.0; the formula stated in `03_TEAM_SCORING_SHEET.md:26`
   (Σ(score × weight)/5) gives **40.0** for scores 3/0/3/1/0/5 against weights 25/20/20/15/10/10
   (Σ = 75+0+60+15+0+50 = 200; 200/5 = 40.0). All six other rows (A, B, C, D, E, F) reproduce exactly.
   Rank order is unaffected (G stays 7th behind A's 41.0), but the number is wrong in a matrix the team is
   instructed to adopt.

2. **HIGH - The "MANDATORY DISCLOSURE" equity crossover does not reproduce.**
   `04_WEIGHT_ADOPTION_PAGE.md:7` and `02_PROVISIONAL_MCDA.md:42` claim F overtakes B at ~2× equity weight
   (20/100). Recomputed at equity = 20 with the total held at 100: donor = Data-confidence → B 83.0, F 83.0 (**tie**);
   donor = Cost → B 81.0, F 81.0 (**tie**); donor = Expandability → B 81.0, F 79.0 (B wins); donor = Safety → 83.0 vs
   81.0 (B wins); donor = Demand → 83.0 vs 81.0 (B wins). **Under no allocation does F strictly overtake B at 2×.**
   F only wins at roughly 2.5× (equity 25, drawn from confidence + cost → B 81.0, F 83.0). The cited source
   (Report 04 §2) is not in the repository, so the claim cannot be reconciled.

3. **MEDIUM - Horizon-convention drift in the two client-facing documents.**
   `02_CLIENT_PREREAD.md:9` "models demand and capacity at **10/20/30-year horizons**"; `:15` column header
   "**10-yr cost screen (NPV)**"; `04_ALTERNATIVES_BRIEFING.md` uses "**10-yr cost order**" 8 times (lines 5, 11,
   19, 27, 35, 43, 51, 59). Canon is 2026/2036/2046/2056 (`contract_manifest.json` `conventions`). The *numbers*
   are correct and trace to the `plus10`/2036 rows, so this is labelling drift, not a wrong figure - and it is
   **not** marked as legacy_v2. Contrast the correct handling in `fellowship_confirmation/02_CONTINGENCY_SUMMARY.md:19–21`
   and the properly-quoted legacy reference in `01_EMAIL_DRAFT_FELLOWSHIP_STAFF.md:15`.

4. **MEDIUM - Dead references: the "Client and Public Engagement Toolkit" and the numbered Report series
   do not exist in the repository.** `toolkit §1/§3/§4/§5/§6/§7/§8` is cited in 03, 05, 06, 09, 10 of
   `client_meeting_2/` and in `public_engagement/01, 03, 05`; "Report 02 §4 / ruling 1, 2, 5", "Report 04 §2/§3/§5",
   "Report 10 §3/§4", "Report 11" are cited in `README.md`, `02_CONTINGENCY_SUMMARY.md`, `01_FACILITATION_GUIDE.md`,
   `06_COI_ASSUMPTION_NOTE.md`, `04_WEIGHT_ADOPTION_PAGE.md`, `03_LISTENING_SESSION_ONE_PAGER.md`,
   `04_LANGUAGE_ACCESS_PLAN.md`, `05_PRIVACY_NOTICE.md`, `07_EQUITY_REVIEW_PROTOCOL.md`.
   `find` for `*TOOLKIT*` returns nothing outside `venv/`; `reports/` contains only the Milestone-2 deliverables.
   Only the MCDA CSV is honestly flagged as "pre-V3 research archive, not tracked in this repository"
   (`02_PROVISIONAL_MCDA.md:5`); the toolkit and Reports carry no such disclaimer.

5. **MEDIUM - `05_PROPOSED_STANDARD_FEEDBACK_SHEET.md` module numbering contradicts the concept document.**
   The sheet presents M1/M2/M3; `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md:23–84` defines seven
   modules. The sheet's "M2" bundles concept Modules 2 + 4 + 5, and its Q4 asks about "**M2's 'fail-safe on comms
   loss'**" which the concept places in **Module 5** (`:59–65`). An AHJ handed both documents would be reading two
   different numbering schemes.

6. **MEDIUM (Phase 4/5) - The tracking register does not cover every requested field.**
   `02_DATA_REQUEST_FACILITY_MANAGERS.md:28` item 9 asks for "known site constraints (drainage, easements, planned
   repaving)"; `03_TRACKING_REGISTER.md` has **no row** for it (its 11 rows fold "renovations" into
   `Planned shutdowns/outages` and `Planned capital projects`). Two requested quantities also carry **no units**:
   "spare panel capacity" (item 2) and "approximate distance from the electrical room/service to the candidate
   parking rows" (item 4). Phase 4's schema and Phase 5's NFC form must resolve both gaps.

7. **MEDIUM (Phase 5) - No facility manager has been identified or contacted; nothing is authorised.**
   `08_STAKEHOLDER_CONTACT_MAP.md:15–17` lists all three facility-manager rows as `[TO BE IDENTIFIED]` /
   Placeholder. `03_TRACKING_REGISTER.md` shows 33/33 rows `not_requested`.
   `01_DATA_REQUEST_DOMINION.md:5` notes "a facility-owner authorization may be required".
   Any Phase-5 artifact implying site-owner consent to charger placement would contradict these three files.

8. **LOW - Two divergent privacy notices.** `public_engagement/05_PRIVACY_NOTICE.md:13` tells the public the
   project website's assistant "exists to explain the study" and that they "should not enter personal information
   into it" (an open explainer), and `03_LISTENING_SESSION_ONE_PAGER.md:34` likewise directs the public away from
   "our project website's assistant, which only explains the project". But
   `docs/operations/website-patch-package/content/privacy_notice.md` states the assistant "**is restricted to
   approved, authenticated users (Cognito)**" and that "assistant conversations **may be logged**". The public-facing
   notice does not mention authentication or logging. `docs/operations/v4-program/LEDGER.md:138` (FIND-AWS-02)
   records that the website patch **was never applied** (`privacy.html` 403s), so neither notice is live.

9. **LOW - Present-tense deployment language in undeployed instruments.**
   `05_PRIVACY_NOTICE.md:5` says the notice is "Printed on survey forms, on the listening-session handout, and
   **posted on the project website**" while the same file's line 1 header reads "NOT PUBLISHED" and LEDGER
   FIND-AWS-02 confirms nothing is live. Similarly `03_LISTENING_SESSION_ONE_PAGER.md:35` advertises the survey as
   available in "English/Español" when `04_LANGUAGE_ACCESS_PLAN.md`'s production register is entirely empty.

10. **INFO - Presentation-length inconsistency.** `02_PROVISIONAL_MCDA.md:37` refers to "a **12-minute**
    presentation"; the rest of the repo uses **≤13 minutes** (`docs/operations/open-human-actions.md:13`,
    `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:124, :145`,
    `reports/milestone-2/Milestone_2_Gap_Closure_Status.md:77` "10–15 minute structure … Timed run ≤13:00").

11. **INFO - `01_FACILITATION_GUIDE.md:6` lists "the MCDA CSV" as required session material**, but that file
    (`SOLUTION_ALTERNATIVES_MCDA.csv`) is not in the repository (`02_PROVISIONAL_MCDA.md:5` says so explicitly;
    `find -iname "*MCDA*"` confirms only the .md and `presentation/assets/10_mcda_provisional.png` exist).

12. **INFO - `README.md:30` says capacity "confidence Low"** where the contract's `capacity_confidence` is
    literally `none` and it is `data_confidence` that is `Low`. Two different columns conflated in one phrase.

13. **INFO - unfilled placeholder that blocks a stated commitment:** `04_LANGUAGE_ACCESS_PLAN.md:10` promises
    interpretation on request "with **[X] business days' notice**" - the number was never chosen.

## POSITIVE VERIFICATIONS (no defect - record so later phases do not re-litigate)

- **eGRID 596.3 / 590.2:** no emissions factor appears anywhere in this lane; **`590.2` has zero occurrences**.
- Every equity index quoted (`07_EQUITY_REVIEW_PROTOCOL.md:3`: FFX002 0.66, PWC006 0.614, FFX004 0.203)
  matches `scenario_table.csv` exactly.
- Every NPV quoted (`02_CLIENT_PREREAD.md`: ≈$134k / $166k / $148k) matches the 2036 rows (133641 / 166275 / 147663).
- Every coordinate, port count, pathway capacity and 19.2 kW rating in `03_SITE_REVIEW_PACKET_TOP3.md` and
  `01_DATA_REQUEST_DOMINION.md` matches `site_table.csv` / `scenario_table.csv`.
- The `capacity_source` string in `04_DATA_FLOW_INTO_MODEL.md:10` is an exact 120/120-row match.
- `battery_storage_flag = 0` at all 12 sites (`06_COI_ASSUMPTION_NOTE.md:7`) - true.
- Code basis in `04_CODE_EDITION_CONFIRMATION_CHECKLIST.md:3` is an exact match to IM-03.
- Dominion 50% / 100%-disadvantaged incentive (`01_DATA_REQUEST_DOMINION.md:29`) matches IM-07 and the funding brief.
- Neabsco 70 ports / 17 offline / ~$1,000/station/yr and the ~35-station fleet hub are used consistently
  across `02_CLIENT_PREREAD.md`, `04_ALTERNATIVES_BRIEFING.md`, `02_QUESTION_SET_PWC_FIRE_MARSHAL.md`,
  `02_PROVISIONAL_MCDA.md` and the repo root README / standards docs.
- UL 2594 + UL 3600 (`02_CONTINGENCY_SUMMARY.md:25`) match IM-04 / IM-05.
- All in-tree relative file references resolve; `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` exists.
- No secrets, tokens, keys, AWS identifiers, absolute local paths, or external URLs anywhere in the 37 files.
