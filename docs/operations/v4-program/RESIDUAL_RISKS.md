# RESIDUAL RISKS - what is still unverified, unfinished, or needs a person

**Recorded 2026-07-28.** For the four teammates who did not watch this work happen.

Nothing here is hidden elsewhere. Every item is either already stated on the surface it affects,
gated so it cannot be forgotten, or logged as a numbered human action. The point of collecting
them is that a reader should be able to learn the worst of it in one place, from us, rather than
discovering it later on their own.

---

## 1. The one that governs everything

**Nobody has confirmed the electrical capacity at any of the twelve sites.**

`capacity_basis = placeholder` on **120/120** contract rows. Every electrical field - service
rating, spare capacity, disconnect visibility - is unconfirmed everywhere. The fail-closed guard
therefore refuses to emit a feasibility claim, by design rather than by omission.

Consequences that follow directly from it, and cannot be fixed before it is:

- **35% of the feasibility sub-score is weighted on `spare_capacity_kw`, which is `0` at all
  twelve sites** - so that weight currently contributes nothing to any score. Correcting it
  would move every published readiness score and break the `legacy_v2` golden, which this
  repository treats as a permanent obligation. Disclosed, not corrected.
- **`base_load_kw` is the only populated electrical field** (120/120), which makes it the one a
  reader is most likely to mistake for a measurement. No building was metered; it is a
  hand-adapted planning proxy, and it carries its own caveat separate from the capacity one.
- **No expansion trigger has ever been evaluated against real data**, because no site has been
  observed in operation. The trigger policy is proposed configuration, not adopted policy.

**Needs a person:** human action 4 (utility and facility data requests) and 11 (facility-owner
consent before any real site data is published).

---

## 2. Two dormant model defects, deliberately not fixed

Pinned by `tests/test_absence_is_not_favourable.py`, which asserts them **as known defects** so
they cannot be forgotten and cannot silently change:

| Defect | Why it is dormant | Why it was not fixed |
|---|---|---|
| An **absent** parking count scores more permissively than a real 40-space lot (`site_capacity_cap` → 6 vs 2) | All twelve real sites supply positive parking | Fixing it moves scores and breaks the frozen golden |
| `garage_enclosed` / `stormwater_risk` are inverted, so an **absent** flag scores as the best possible case - an affirmative safety claim from no data | All twelve real sites carry strict 0/1 flags | Same |

`test_all_twelve_real_sites_have_complete_flags_so_the_two_defects_are_dormant` is the guard: if
a site ever arrives without those fields, that test fails and the defects stop being theoretical.
**The day real third-party data arrives, these must be fixed first.**

---

## 3. Four artifacts still carry `legacy_v2` ranks

All four are disclosed; none is silently wrong. Two are owner decisions.

| Artifact | State | Action |
|---|---|---|
| Superseded Tableau workbook, still public | `legacy_v2` ranks; that mode's own Medium/Low confidence labels | **8b** - only the account holder can remove it |
| `results.html` rotating gallery | **Re-baselined 2026-07-28** to `milestone2_v3`, generated from the fixture and gated | closed |
| `Public_EV_Charging_Planning_Report.pdf` | **Stamped 2026-07-28** with a superseded cover; 8 original pages unaltered | **8d** - kept as a dated artifact by decision |
| Dated Milestone 2 deck + speaker notes | Names no mode at all | Deliberately unedited: it records what was presented on 2026-07-21 |

**The residual risk:** the deck is the artifact most likely to be quoted by a person from
memory, and it says FFX002 leads at 58.8. Anyone presenting from it should know the canonical
answer is FFX004 at 53.4.

---

## 4. Surfaces this repository does not control

**Two Framer-hosted iframes** are embedded on the public site:

- `index.html` - the entire home-page body between our disclaimer and our footer
- `results.html` - the "Results Explorer"

Everything inside them is third-party-hosted: **outside version control, outside review, and
outside every gate this repository has.** The content can change without a commit and nothing here would notice.
The linking text no longer asserts anything about what those hosts serve.

This is a structural fact about what "the public site" means for this project, not a bug with a
fix. It is the owner's call whether to bring that content into the repository.

---

## 5. Verification that has not been done

| Gap | Why | Mitigation in place |
|---|---|---|
| **Real MATLAB has never seen the real sites** | The public harness must never carry facility data | 49/49 on a synthetic fixture; Octave↔MATLAB cross-validated at 2 640 cells / 0 divergences |
| **Simulink has never been simulated** | Model built only | The view states it on its face; no number derives from it |
| ~~**No true fresh-clone walkthrough**~~ | **CLOSED 2026-07-28.** Cloned to an empty directory and followed the README from zero: 40/40 gates on a tree never built in, and no documentation needed correcting | [`VERIFICATION.md`](VERIFICATION.md) §9 |
| **Windows install unexercised** | No Windows machine available. **The CI packaging job now runs** - it first executed 2026-07-28 and has been green on both platforms since 2026-08-02 - but nobody has ever *installed* the Windows artifact, because there is no Windows machine to install it on | Every published artifact is opened and inspected rather than trusted; four Windows-only defects were found that way and fixed. v3.0.0 is tagged **pre-release** for this reason. See [`VERIFICATION.md`](VERIFICATION.md) §10–§11 |
| **macOS Gatekeeper** | **Nothing is signed.** `spctl -a -t exec` rejects the artifact, exit 3, measured on macOS 26.5.1. The workflow used to ad-hoc sign the run script, but `zip` discards the extended attributes the signature lives in, so no build ever shipped one - the step has been removed and the guide corrected | Real click-path documented; disabling Gatekeeper explicitly refused; a test fails if a signing step returns without xattr-preserving archiving |
| **Editable dev install is not hash-verified** | pip cannot hash an editable requirement - measured, not assumed | `requirements-hashed.txt` covers the clean non-editable install and the packaging build |
| **Platform sub-surfaces unexercised by a human** | Only "it renders" was confirmed | Stated explicitly rather than folded into the sign-in confirmation |
| **NFC tags are not deployed** | Placement needs facility-manager consent, not sought | One bench tag written and read back through iOS background NFC |

---

## 6. Presentation features that could not be built

Four Tableau features remain unbuildable through the authoring path and are **named rather than
approximated**: bar-in-bar, two reference lines, dashboard filter scoping, and the 8-point
story. Each substitute is declared in its own sheet subtitle and asserted by test. See
`dashboard/tableau/CAPABILITY_GAP.md`.

One fix that did **not** work is recorded as a failure rather than a fix: `fit: fit_width`
changes nothing about dashboard rendering - proven by three cache-busted fetches after a
confirmed publish returning byte-identical images.

---

## 7. Process risks this program demonstrated

Recorded because they are more likely to recur than any single defect above.

1. **A gate suite only checks the tree it runs in.** Three separate failures. Gate 23 now
   catches the mechanical case; nothing catches a dependency read at runtime from a path no
   static scan can see.
2. **Insert-only patching.** Guarding an edit with "is a marker present?" rather than "is it
   current?" made three separate corrections reach the source and no page - twice while a full
   gate run passed.
3. **Text-versus-meaning.** At least eleven instances: prose that is accurate about something
   *other than* the thing it annotates. The wait caveat needed four revisions; its numbers are
   now machine-checked because prose demonstrably could not be.
4. **Fixing a claim in one file does not fix the file that repeats it.** Three of five findings
   in one review round were half-applied fixes.
5. **A local pass is not a production pass when the local tool is the more capable one.**
   Python's `http.server` generates directory listings; S3 does not. Five links 404'd in
   production while every local check passed.

---

## 8. Open human actions, in full

`docs/operations/open-human-actions.md` carries 15 rows (1–10 plus 8b, 8c, 8d, 8e). The ones that block something:

- **4** - utility and facility data requests. Unblocks §1 entirely.
- **8b** - remove the superseded Tableau workbook (account holder only).
- **11** - facility-owner consent before publishing real site data. Blocks declassification of
  `data/inputs/real_sites_v2.csv`, and therefore blocks any public installer that runs on real
  inputs rather than the synthetic set.

**Standing integrity rule, inherited and kept:** closing any row requires the real event and its
documentation. Retroactive relabelling is not closure.
