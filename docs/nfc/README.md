# The NFC field layer

**Status: built, tested, and walked end to end on real hardware.**

One physical tag (FFX002) has been written, read back through iOS background NFC with the
writing app closed, and confirmed to open the correct live page. It is deliberately left
**unlocked** as a bench tag. **No tag has been placed, and no permission to place one has
been sought.**

## The hardware, verified before designing

50 × NTAG215 coins, 25 mm, white PVC, adhesive, rewritable.

| Property | Value | What it decides |
|---|---|---|
| Standard | NFC Forum Type 2, ISO/IEC 14443 Type A | universally readable by modern phones |
| User memory | **~504 bytes** | enough for a URL, not a payload — **the tag is a pointer** |
| UID | 7-byte, read-only, unique | usable as an identifier, deliberately **not** used — see below |
| Protection | 32-bit password (PWD/PACK) **or** lock bytes | we lock; see the decision below |
| Locking | **permanent and irreversible** | verify-before-lock is a hard sequence, not advice |
| Metal | detunes badly without ferrite | pedestals, bollards and cabinets are all metal |
| Material | PVC + adhesive | indoor, short-term. UV and freeze-thaw will destroy it outdoors |

**iOS behaviour, which decides the whole experience:** iPhone XS and later read NDEF tags
**in the background with no app installed** — tap, a banner appears, tap it, Safari opens.
Older iPhones need the Control Center reader. The project phone is an **iPhone 17 Pro**, so
the design targets the tap-and-it-works path. A reader installs nothing; the writing app is
for the person programming the tags, once.

## The use case, and why it beat the alternatives

**Field data capture that closes the capacity gap.**

The project's largest limitation is that electrical capacity is a **placeholder at 12 of 12
sites**. A site visit is exactly where a placeholder becomes confirmed — and a walkthrough
is exactly when nobody wants to find a laptop. A tag at the site, tapped during the visit,
opens a capture form already scoped to that `site_id`, feeding the fields
`docs/human-actions/utility_facility_data/` already asks for into the V4 ingestion path.

It is a physical bridge from the project's biggest limitation to its resolution, which is
the only justification strong enough to put an object on someone else's property.

### Alternatives considered

| Alternative | Why it did not win |
|---|---|
| **Public engagement tags** — open the plain-language "what is being considered here" page | Genuinely useful, and **folded in** rather than rejected: the tag lands on a site page carrying both the public explanation and the staff capture route. One tag, both audiences. |
| **Deep links into the 3D explorer** | The explorer needs a real screen and a WebGL context. A phone in a car park is the wrong device, and a slow heavy page is a bad first impression. Linked from the site page instead. |
| **Presentation and demo tags** | Real value, zero deployment risk — but it does not need 12 site tags or any permission, so it is not what the hardware is *for*. Worth doing separately with two spare coins. |
| **AHJ site-review tags** for the fire marshal walkthrough | Attractive, and the same mechanism. Deferred because the AHJ packages are not yet through their own human-action gates; adding an untested channel to a regulatory conversation is a bad trade. |
| **Tag carries the data itself** | 504 bytes. Not possible, and not desirable — a tag that carries data is a tag that goes stale the moment the contract regenerates. |

## Security

The threat is specific and worth stating plainly: **an unlocked NDEF tag is rewritable by
anyone with a phone in about five seconds.** A tag on county property carries an implicit
endorsement. One rewritten to point at a phishing page — collecting credentials under the
apparent authority of a county EV programme — is a serious liability.

Controls, and where each is enforced:

| Control | Enforced by |
|---|---|
| Tags are **locked** before deployment | `TAG_WRITING_RUNBOOK.md` step 6, and the verification log's rule that a tag is never Placed before Locked |
| URLs point **only** at hosts we control | `src/fcf_m2/nfc.py` allowlist — **in code**, refusing at generation, not trusted to a runbook |
| **https only** | same, refused at generation |
| **No credential, identifier, or access grant** on any tag | `tests/test_nfc.py` asserts no payload contains token, auth, user, email, session or bearer strings |
| Payloads derived from the contract | `payloads_from_contract` — a tag can never point at a site id the contract does not contain |

### Decision: lock tags that are deployed, not tags that are tested

Locking defends against one thing: a stranger rewriting a tag that carries the project's
implicit endorsement. That threat exists only once a tag is somewhere a stranger can reach
it. A bench tag — used for a demo, a rehearsal, or verifying the pipeline — is not exposed
to it, and locking one throws away the ability to re-point it when a URL changes for no
security gain. With 50 coins and 12 sites, spares are free.

So: **lock at the point of deployment, not at the point of writing.** Written and verified
but deliberately unlocked is a complete, correct state for a bench tag, and the verification
log records which kind each tag is.

### Decision: lock, not password-protect

NTAG215 supports a 32-bit password (PWD/PACK). We **lock** instead.

A password shared across a team, printed in a runbook and carried into a car park is
security theatre — it protects against nobody who has physical access, which is the only
attacker that matters here. Locking achieves the actual goal, permanent read-only, with no
secret to leak, rotate, or forget. The cost is that a locked tag can never be corrected,
which is why verification precedes locking as a hard sequence.

### Decision: the tag UID is not used as an identifier

Every NTAG215 carries a unique read-only 7-byte UID, and it is tempting to use it to
recognise a specific tag. We do not. A UID is trivially cloneable, so it authenticates
nothing, and treating it as an identifier invites exactly the "the tag said so" reasoning
this design avoids. The UID is recorded in the verification log for *inventory* — knowing
which physical coin is where — and never consulted by any code path.

## Privacy

Per `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md`:

- **No personal data on any tag.** A lost tag discloses a site id and nothing else.
- **No individual-level tracking.** Analytics are aggregate and disclosed. There is no
  per-tag identifier in the URL, no query parameter, and no cookie set by tapping.
- **Every landing page states** what is collected, why, and for how long.
- **The capture form collects facility data, not personal data** — panel ratings and spare
  breaker positions, not names or contact details beyond an optional attribution for
  provenance, which the person chooses to give.

## Physical reality, stated rather than designed around

- **PVC with adhesive is indoor, short-term.** It will not survive a Northern Virginia
  summer outdoors, and no amount of engineering here changes that. The pilot is indoor.
- **Do not mount on metal without ferrite.** Charging pedestals, bollards and cabinets are
  metal, and a detuned tag reads intermittently — which reads to a visitor as a broken
  project rather than a bad sticker.
- **Placement requires the facility manager's consent, which has not been sought.** Nothing
  in this directory may be presented as though permission exists.

## Graceful degradation

**Every destination is reachable without NFC.** Each placement card carries the QR code and
the URL in text large enough to type. NFC is a convenience layer for people who have a
modern phone and are standing close enough — never the only door.

## Files

| File | What it is |
|---|---|
| `tag_payloads.csv` | one row per tag: URL, byte count, exact NDEF hex. **Generated** from the contract. |
| `qr/<SITE_ID>.svg` | the same URL as a QR code, high error correction |
| `PLACEMENT_CARDS.md` | printable card per site, to sit beside each tag |
| `TAG_WRITING_RUNBOOK.md` | phone-only procedure: write, verify, lock, log |
| `TAG_VERIFICATION_LOG.md` | one row per physical tag |
| `PILOT_PLAN.md` | two sites, indoors, one season — with the failure conditions stated in advance |

Regenerate with `make nfc`. Never hand-edit `tag_payloads.csv` or the QR codes.
