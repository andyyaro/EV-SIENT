# Milestone 2 Final Presentation - Timing Runbook

**Presentation:** 2026-07-21 · **Hard target:** ≤ 13:00 · **Rehearsal target:** 12:15 (leaves ~45 s of real-world slack)
**Deck:** `Future_City_Fellowship_Milestone_2_Final.pptx` (17 slides) · **Backup:** `Future_City_Fellowship_Milestone_2_QA_Backup.pdf`

## Per-slide time budget (sums to exactly 13:00)

| # | Slide (beat) | Speaker | Budget | Running total |
|---|---|---|---|---|
| 1 | Title | Anna | 0:15 | 0:15 |
| 2 | Problem carried from Phase 1 (beat 1) | Anna | 0:45 | 1:00 |
| 3 | Client evidence - two quotes (beat 2) | Laylas | 0:55 | 1:55 |
| 4 | Client Meeting #2 honest status (beat 3) | Laylas | 0:40 | 2:35 |
| 5 | Seven alternatives table (beat 4) | Adama | 0:55 | 3:30 |
| 6 | Provisional weighted comparison (beat 5) | Adama | 0:50 | 4:20 |
| 7 | Staged workflow + gates (beat 6) | Andy | 0:55 | 5:15 |
| 8 | Readiness ranking + confidence (beat 7) | Andy | 0:50 | 6:05 |
| 9 | Map + 25/48 portfolio shape (beat 7) | Andy | 0:40 | 6:45 |
| 10 | Two aspects × three horizons table (beat 8) | Adama | 0:55 | 7:40 |
| 11 | Aspect visuals side by side (beat 8) | Adama | 0:35 | 8:15 |
| 12 | Standards package + proposed concept (beat 9) | Laylas | 0:55 | 9:10 |
| 13 | Integration + top-3 failure modes (beat 10) | Andy | 0:50 | 10:00 |
| 14 | Economic / environmental / stakeholder case (beat 11) | Anna | 0:55 | 10:55 |
| 15 | Limitations + human validation (beat 12) | Laylas | 0:50 | 11:45 |
| 16 | Peer question + immediate next actions (beat 13) | Anna | 0:50 | 12:35 |
| 17 | Closing / roster | Anna | 0:25 | **13:00** |

Checkpoint calls during the live run (timekeeper: whoever is not speaking - Paula if she takes the Q&A-lead role):
- **4:20** after slide 6 - if past 4:45, activate Cut Level 1.
- **8:15** after slide 11 - if past 8:45, activate Cut Level 2.
- **11:45** after slide 15 - if past 12:15, activate Cut Level 3.

## Fallback cuts if running long (in order; never cut slides 4, 15, or 16)

1. **Cut Level 1 (saves ~35 s):** Slide 11 becomes a 5-second flash - "same two aspects as pictures" - no narration.
2. **Cut Level 2 (saves ~40 s):** Slide 5 collapses to one sentence ("seven real options, from broad buildout to doing nothing - the table is in your handout") and goes straight to slide 6.
3. **Cut Level 3 (saves ~30 s):** Slide 9 narration drops to the caption line only; slide 13 drops the architecture walk-through and keeps only the three failure modes.
4. **Never cut:** slide 4 (CM2 honesty), slide 15 (limitations), slide 16 (peer question + asks) - these carry the integrity and the deliverable requirements.

## Rehearsal checkpoints

### Monday evening (2026-07-20, ~8:00 pm - full-dress run)

- [ ] Full timed run, all speakers, projector or largest available screen; record actual per-slide times next to the budget column.
- [ ] **Assign Paula's role** (slide 17 + speaker-notes table) and re-balance budgets if she takes a slide.
- [ ] Practice the three handoffs that cross topics (Laylas→Adama, Andy→Adama, Laylas→Anna).
- [ ] Anna reads the peer question aloud twice - pacing, not speed.
- [ ] Laylas rehearses slide 4 (CM2 status) until it sounds confident, not apologetic.
- [ ] Run the static-visual QA checklist (below) on the presentation machine.
- [ ] Dry-run one cut level end-to-end so the cuts are muscle memory.

### Tuesday pre-meeting (2026-07-21 - final check)

- [ ] One timed speed run (target ≤ 12:15).
- [ ] Re-run the offline-open test on the actual presentation machine **with Wi-Fi off**.
- [ ] Confirm Paula's row on slide 17 is edited (or her role stated verbally).
- [ ] Q&A backup PDF open in a second window; crib-card slide (last page) reviewed by all speakers.
- [ ] Confirm nobody's notes claim: client endorsement, a held CM2, confirmed capacity, budgets, or adopted MCDA.

## Static-visual QA checklist (offline-open test)

- [ ] Copy the whole `presentation/` folder to the presentation machine (not just the .pptx).
- [ ] **Turn networking off.** Open `Future_City_Fellowship_Milestone_2_Final.pdf` - all 17 pages render, every image visible (images are embedded; the PDF is the fail-safe).
- [ ] Open the .pptx offline - all 17 slides render identically; no font substitution warnings that change layout (deck uses Georgia + Arial only).
- [ ] Open all **9** files in `dashboard/static/` directly *(corrected 2026-07-28: this said 11 files in `static_visuals/`, a directory that does not exist in this repository)* - each PNG opens offline (no live map tiles; `09_site_map_offline.png` is the offline-rendered map).
- [ ] Stand 3 m from the screen: slide titles, table numbers, and chart headlines readable.
- [ ] Spot-check numbers against the deck's canonical set: 58.8 / 54.4 / 52.1 · 25/48 · 44→48 *(corrected 2026-07-28: this read 44→47 & 47→48; **47 is not a portfolio total at any horizon or scenario** - the active-port series across the contract is 25 → 35 → 44 → 48)* · $1.56M/$1.87M · $2.29M/$2.64M · $3.01M/$3.41M · $0.31M/$0.34M/$0.39M · ≈43 → ≈173–260 t/yr · 596.3 lb CO2e/MWh (eGRID2023 Rev 2, accessed 2026-07-19).
- [ ] Every data slide shows its source/vintage footer; every ports/capacity slide shows the placeholder caption.
- [ ] Backup: PDF copies on a USB stick **and** a second laptop.
