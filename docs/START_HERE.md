# Start here

This project studies where to put public EV chargers at twelve public buildings in **Fairfax
City**, **Fairfax County** and **Prince William County**, Virginia — and, more importantly,
*how many* to put there.

If you have five minutes, read this page. Everything it links to is optional.

---

## The problem, in one paragraph

A commuter garage in Prince William County has 70 charging ports. Seventeen were later taken
offline: not enough people used them, and they cost roughly $1,000 per station per year to
keep. At another county site, a ten-port install ran over budget on trenching. Overbuild and
you pay for chargers nobody uses; underbuild and expanding later means digging up ground you
already paid to close. This project is about finding the middle — **install 25 ports now, build
the underground pathway for 48, and energise the rest only when real usage data says to.**

## The one caveat that governs everything

**Nobody has confirmed the electrical capacity at any of these twelve sites.**

Not one. The capacity number the model uses is a labelled placeholder — a value it needs in
order to run that nobody has checked. So this study can compare sites, and it can argue for
staging, but it **cannot** tell you whether a site is electrically able to host chargers. The
software refuses to make that claim rather than quietly leaving it out.

Everything else on this page sits underneath that sentence.

---

## Find your way in

### I live here and just want to know what's happening

Nothing is being built yet. This is a study of where charging *could* go, and no approval,
permit, funding, or utility sign-off exists for any of it. Each site also has its own page,
reachable by a tap-to-open tag — though **no tag has actually been placed at any site yet**.

→ [What this can and can't tell you](WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md)

### I'm on a council or a board and have to decide something

Read the limits before the numbers, because the limits are the finding. The comparison
between sites is screening-class — good enough to decide what to study next, not what to build
— and the feasibility question is open at every site. No number here is a budget.

→ [What this can and can't tell you](WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md)
→ [Final Milestone 2 report](../reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md)
→ [Open human actions](operations/open-human-actions.md) — what still needs a person

### I manage one of these facilities

You are the person who can move this furthest. Confirming your building's electrical service
rating and spare capacity changes more than any other single input: it releases the feasibility
guard, activates a scoring weight that currently does nothing, and lifts the site off the
confidence floor.

→ [What this can and can't tell you](WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md#what-would-change-these-answers)
→ [Open human actions](operations/open-human-actions.md)

### I'm an engineer or a planner

Every number resolves to the run that produced it and the source behind it. Two model modes
exist, and every surface this repository builds names which one it used. Standards scope,
adopted code editions, and the [Authority Having Jurisdiction](GLOSSARY.md#ahj--authority-having-jurisdiction) (AHJ) boundary are stated explicitly. One caveat: an **older
Tableau workbook is still public** carrying superseded `legacy_v2` ranks and overstated
confidence — removing it needs the account holder, and it is tracked as an open action.

→ [Methodology](methodology/) · [Standards matrix](standards/FINAL_STANDARDS_APPLICATION_MATRIX.md)
→ [Migration from V2](migration-from-v2.md) — why two modes exist and what moved

### I want to run or read the code

→ [Repository README](../README.md) · [Reproduction guide](operations/reproduction-guide.md)
→ [Contributing](../CONTRIBUTING.md) · [Install guide](INSTALL.md)

---

## Honest FAQ

**Is anything being built?**
No. No construction, no permit, no funding award, no utility agreement, and no client
endorsement exists. This is a screening study.

**Are these the final sites?**
No. Twelve candidate sites were screened. The comparison between them is the output; it is not
a decision, and the ranking depends on weights that reasonable people can set differently.

**Can these sites actually support chargers?**
Unknown at all twelve, and that is the study's central limitation rather than an oversight. The
electrical fields — service rating, spare capacity, disconnect visibility — are unconfirmed
everywhere. See [capacity basis](GLOSSARY.md#capacity-basis).

**The costs look precise. Are they?**
No. They are screening-class estimates for comparing options against each other. They are not
budgets, quotes, bids, or engineering estimates, and they should not be used as any of those.

**Where does the demand number come from?**
A model, not a meter. The contract's own label for it is **synthetic and uncalibrated**: no
charging has been observed at any of these sites, so demand is modelled from benchmark
assumptions applied to site characteristics, and the growth multipliers are provisional
conventions rather than forecasts.

**Why does one site rank first in one place and second in another?**
Two model modes exist. `legacy_v2` reproduces an earlier accepted baseline exactly, and
`milestone2_v3` is the current canonical model. They disagree about the top site — FFX002 under
the old mode, FFX004 under the current one — so every surface built from this repository
**names the mode** wherever a rank appears. They are not interchangeable. The exception is the
superseded public workbook noted above, which carries `legacy_v2` ranks without saying so; that
is precisely why it is queued for removal.

**Why is the data confidence low everywhere?**
Because it is scored from where the data actually came from, not from how good the answer
looks. All twelve sites score 33.8, which is Low; none reaches Medium. That number is designed
to be uncomfortable while capacity is unverified.

**Is this an official Fairfax City, Fairfax County or Prince William County document?**
No. It is student work from a George Mason University Future City Fellowship team, produced in
consultation with Prince William County's Office of Sustainability and Fire & Rescue
interviewees. It carries no authority and asserts none.

**Does it say anything about power outages or backup?**
No. There is no battery storage in the plan and no resilience claim anywhere.

**Who decides what's actually allowed?**
The local Authority Having Jurisdiction — the building official, electrical inspector, or fire
marshal. Every permit, disconnect-placement, access, and code-edition determination rests with
them, not with this study.

**Something here is wrong. Can I correct it?**
Yes, and that is a designed-for case rather than a courtesy. Each site has a correction form
that feeds observations back into the model — reachable by tag once tags are placed, and by link
in the meantime — and there is a documented path for another jurisdiction to bring its own data
file.

---

*Terms are defined one honest sentence at a time in the [glossary](GLOSSARY.md).*
