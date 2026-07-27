# NFC pilot plan

**Scope: two sites, indoors, for one season. Not twelve, not outdoors, not permanent.**

The point of a pilot is to find out whether the idea works before committing to it, so this
plan states in advance what would make it a failure. A pilot that cannot fail is a
deployment with better marketing.

## Why so small

Three constraints, each of which independently argues against a full outdoor rollout:

1. **The material will not survive outdoors.** These are PVC coins with adhesive backing —
   an indoor, short-term product. UV, freeze-thaw, and a Northern Virginia summer will
   degrade both the laminate and the adhesive. The listing says not for metal; it does not
   promise weatherproofing either.
2. **NFC detunes badly on metal.** Charging pedestals, bollards and equipment cabinets are
   metal. Without a ferrite isolation layer a coin stuck to any of them may read
   intermittently or not at all — and an intermittent tag is worse than none, because the
   person concludes the project is broken rather than that the sticker is.
3. **Placement needs permission we do not have.** Attaching anything to a public facility
   requires the facility manager's consent. **That consent has not been sought or given for
   any site.** Nothing in this plan should be presented as though it has.

## Sites

Two, chosen for indoor placement and existing contact:

| | Criteria |
|---|---|
| **Site A** | a Tier 1 candidate with an indoor public lobby and a facility contact already engaged through the utility/facility data request |
| **Site B** | a contrasting site type, so the result is not a single-context anecdote |

Specific sites are named **only after** their facility managers agree, and the agreement is
recorded in `docs/human-actions/utility_facility_data/03_TRACKING_REGISTER.md`.

## Placement

- **Indoors only.** A lobby noticeboard, a printed sign, or a display stand.
- **Not on metal**, unless a ferrite layer is fitted and the tag is re-verified in place —
  reading it on a desk proves nothing about reading it on a bollard.
- **Card beside every tag**, carrying the QR code and the URL in text. NFC is a convenience
  layer, never the only door.
- **At eye or hand height**, reachable without crouching or reaching over an obstacle.

## What is measured

Aggregate only. No individual-level tracking, no personal data, per
`docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md`.

| Measure | How | Why |
|---|---|---|
| Page reaches per site per week | server logs, aggregate | does anyone tap at all |
| Tap vs QR vs typed | distinct paths per entry route | is NFC pulling its weight over a QR code |
| Capture-form starts and completions | aggregate counts | does the tap lead anywhere useful |
| Physical condition | monthly visual check | is the material surviving |
| Tag still readable | monthly check with a phone | has it detuned, peeled, or been removed |

## What would make this a failure

Stated in advance, so the answer is not negotiated afterwards:

- **Fewer than 10 taps per site over the season.** The convenience layer is not being used
  and does not justify the placement, the permission, or the maintenance.
- **QR scans exceed NFC taps by more than 3:1.** The QR code is doing the work; NFC is
  ornament, and a printed sign would have been the honest answer.
- **Any tag unreadable, peeled or missing at a monthly check.** The material is not suited
  to the placement — which is a finding worth having cheaply.
- **A tag is found rewritten.** The locking procedure failed or was skipped. Pull every
  tag immediately; this is the failure mode with a real liability attached.
- **Zero capture-form completions.** The strongest use case does not survive contact with
  the actual walkthrough workflow, and the design needs rethinking rather than scaling.

## What would make it a success worth extending

- ≥ 30 taps per site over the season, **and**
- at least one capacity confirmation arriving through the capture form that would not
  otherwise have been collected, **and**
- all tags physically intact and readable at the final check.

The middle one is the one that matters. Taps are a vanity measure; a `capacity_basis`
moving off `placeholder` because someone tapped a coin during a walkthrough is the entire
justification for this layer existing.

## Exit

Whatever the result, the tags come down at the end of the season unless the facility manager
agrees to extend. Leaving them up by default is how a pilot silently becomes infrastructure
nobody has maintained.
