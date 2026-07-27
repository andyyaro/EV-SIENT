# Tag-writing runbook

**For a non-technical teammate with a phone and nothing else.** No computer, no card
reader, no prior NFC experience. Roughly 3 minutes per tag once you have the rhythm.

> ## Read this before you touch a tag
>
> **Locking a tag is permanent and irreversible.** There is no undo, no factory reset, no
> way to rewrite a locked NTAG215. A tag locked with the wrong URL is landfill.
>
> That is why step 5 (verify) comes before step 6 (lock), and why the verify step asks you
> to read the tag with a *different* mechanism than the one that wrote it. Do not lock a
> tag you have not read back. If you are unsure, stop and leave it unlocked — an unlocked
> tag can be fixed tomorrow; a wrongly locked one cannot be fixed at all.

---

## What you need

| | |
|---|---|
| **Phone** | iPhone XS or later, or a recent Android. Confirmed for this project: **iPhone 17 Pro**. |
| **App** | **NFC Tools** (free) — App Store or Play Store. Used only for *writing*. |
| **Tags** | NTAG215 coins, 25 mm, white PVC, adhesive. 50 on hand. |
| **The list** | `docs/nfc/tag_payloads.csv` — one row per site, with the exact URL. Print it or open it on a laptop. |

**People reading the tags need none of this.** An iPhone XS or later reads a tag in the
background with no app at all: tap, a banner drops down, tap the banner, Safari opens. That
is the whole experience for a resident or a facility manager. The app is for you, once.

---

## Before the first tag: turn off automatic actions

NFC Tools has an "auto-write" convenience that writes on contact without confirmation. It is
a good way to write the wrong URL to the wrong tag.

1. Open NFC Tools → **Other** tab.
2. Confirm **Auto-write** is **off**.
3. In the **Write** tab, confirm the queue is **empty** before every tag.

---

## Writing one tag

### 1. Find the row

Open `docs/nfc/tag_payloads.csv` and find the site you are tagging. You need two things:
the **site id** (e.g. `FFX002`) and the **URL**.

Write the site id on the back of the coin, or on the card that will sit beside it, *before*
you write the tag. Once several tags are written they are physically indistinguishable.

### 2. Queue the record

1. NFC Tools → **Write** tab → **Add a record**.
2. Choose **URL/URI**.
3. Type the URL from the CSV **exactly**, including `https://`.
4. Tap **OK**. The queue should now show **1 record**.

Check the size NFC Tools reports: it should be around **50 bytes**. If it says something
very different, you have typed the URL wrong.

### 3. Write

1. Tap **Write / Save**.
2. Hold the coin flat against the **top third of the back of the phone**, where the NFC
   antenna sits. On an iPhone this is near the camera bump.
3. Hold still for two seconds. NFC Tools will say **Write successful**.

If it fails: reposition and try again. PVC coins are thin and the antenna sweet spot is
small. Repeated failure on one coin, when others work, means a dead tag — set it aside and
label it dead rather than fighting it.

### 4. Close the app

Genuinely close it — swipe it away. The next step must not be done by the app that just
wrote the tag, or you are checking your own homework.

### 5. Verify — the step that protects you

1. With NFC Tools **closed**, tap the coin on the back of your phone.
2. A notification banner appears at the top of the screen showing the URL.
3. **Read the URL on the banner, character by character**, against the CSV. Check the site
   id especially: `FFX002` and `FFX004` differ by one character.
4. Tap the banner. Safari opens. Confirm the page is the **right site**.

This is a real read through the operating system, not a readback through the app that just
wrote it. If it does not match, rewrite it. **Do not proceed to lock.**

### 6. Lock — irreversible, and only for tags that are going out

**Locking is not always the right answer. Decide which kind of tag this is first.**

| This tag is... | Lock it? |
|---|---|
| **Going out** — placed at a site, in public, where strangers can reach it | **Yes.** This is the whole reason locking exists. |
| **A bench tag** — testing, a demo, a walkthrough rehearsal, something that lives in a drawer | **No.** Leave it writable. |

The threat locking defends against is a stranger rewriting a tag that carries the project's
implicit endorsement — redirecting it to a phishing page under apparent county authority.
That threat only exists once a tag is somewhere a stranger can reach it. A tag on your desk
is not exposed to it, and locking one costs you the ability to re-point it when a URL
changes. There are 50 coins and 12 sites; spares are free, so there is no reason to lock one
you might want to reuse.

**If this is a bench tag, stop here.** Skip to step 7 and log it as verified but not locked —
that is a complete, correct outcome, not a job half done.

**If this tag is going out**, and only after step 5 has passed on this specific coin:

1. Reopen NFC Tools → **Other** tab → **Lock tag**.
2. Read the warning it shows you. It is telling the truth.
3. Hold the coin to the phone until it confirms.

The tag is now permanently read-only. It can never be rewritten by us or by anyone else,
which is the entire point.

> **Why lock at all?** An unlocked NDEF tag can be rewritten by anyone with a phone in a few
> seconds. A tag on county property carries an implicit endorsement; one rewritten to point
> at a phishing page is a serious liability. Locking is the only mitigation that survives
> contact with a public car park.

### 7. Log it

Add a row to `docs/nfc/TAG_VERIFICATION_LOG.md`: site id, date, who wrote it, verified yes,
locked yes, and the last 4 characters of the tag's UID if NFC Tools shows it.

An unlogged tag is an unknown tag.

---

## If something goes wrong

| What happened | What to do |
|---|---|
| Wrote the wrong URL, **not yet locked** | Just write again. Writing overwrites; there is nothing to undo. |
| Need to change the URL on a **locked** tag | Not possible. That is the trade locking makes. Use a fresh coin — which is why bench tags stay unlocked. |
| Wrote the wrong URL, **already locked** | The tag is unusable. Mark it, bin it, use a new one. Do not deploy it. |
| Tag will not write, others do | Dead tag. Label it and set it aside. |
| Banner does not appear on tap | NFC background reading is off, or the phone is in Low Power Mode, or it is not an iPhone XS or later. Check Low Power Mode first. |
| Banner shows a URL you do not recognise | **Stop.** Do not tap it. That tag is not one of ours, or it has been rewritten. |

---

## Doing all twelve

Write, verify and (for tags going out) lock **one tag completely** before starting the next. Batching the writes
and verifying later is how a mislabelled tag gets locked — and one mislabelled locked tag
means one site's visitors get another site's information, which is worse than no tag.

Expect around 40 minutes for twelve tags including logging.

---

## What is deliberately *not* here

- **No instruction to disable any phone security setting.** Nothing in this process needs it.
- **No password protection.** NTAG215 supports a 32-bit password, but a password shared
  across a team on printed paper is security theatre, and locking achieves the actual goal
  — permanent read-only — without a secret to leak. Recorded as a decision, not an oversight.
- **No tag carries anything except a URL.** No name, no credential, no identifier for any
  person. Nothing on a tag is secret, so a lost tag discloses nothing.
