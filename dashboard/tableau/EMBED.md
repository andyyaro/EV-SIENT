# Embedding the published Tableau views

**Use the `/views/` share form. Never the `/app/profile/` page form.**

They look interchangeable and are not:

| Form | Use it for | Do NOT use it for |
|---|---|---|
| `https://public.tableau.com/views/<workbook>/<Sheet>` | **embedding**, sharing, the static-image endpoint | — |
| `https://public.tableau.com/app/profile/<profile>/viz/<workbook>/<Sheet>` | a human clicking through from the profile | **embedding** — it is the profile-app wrapper |

Both return HTTP 200 and both return the same ~1.4 KB JavaScript shell, because Tableau
Public is a single-page app. **A status-code check cannot tell them apart and cannot confirm
anything rendered.** To verify a view genuinely works, fetch its static image (below) and
check the dimensions: a healthy sheet here is ~792×681, and a broken one is ~792×90 — title
and subtitle with no chart under them. That is exactly how two blank charts were caught after
they had already been published.

---

## The views

Workbook: `EV_Charging_Site_Readiness_M2_Canonical`
Profile: `yiguedan.philippe.andy.yaro`

| View | Sheet segment |
|---|---|
| Site readiness ranking | `ReadinessbySite` |
| Starter vs pathway ports | `StartervsPathwayPorts` |
| Active ports by horizon | `PortsAcrossHorizons` |
| Queue wait, minutes | `PeakWaitsbySite` |
| Lifecycle cost NPV | `LifecycleCostbyHorizon` |
| Net CO2e per year | `NetCO2ebyHorizon` |
| Candidate sites map | `SiteMap` |
| **Dashboard** (all seven) | `Milestone2Overview` |

Sheet segments are the worksheet names with spaces removed. They were read out of the `.twb`
**downloaded from Tableau Public**, not from the local build, so they are Tableau's own names
for what is live.

---

## Share link

```
https://public.tableau.com/views/EV_Charging_Site_Readiness_M2_Canonical/<Sheet>?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link
```

## Embed code (iframe)

```html
<iframe
  title="EV charging site readiness — screening study, not an approval"
  src="https://public.tableau.com/views/EV_Charging_Site_Readiness_M2_Canonical/ReadinessbySite?:embed=y&:showVizHome=no&:display_count=n&:origin=viz_share_link&:toolbar=bottom"
  width="100%" height="720" frameborder="0" loading="lazy"
  style="border:0;max-width:100%"></iframe>
```

`:embed=y` and `:showVizHome=no` are what strip the Tableau Public site chrome. Swap the
sheet segment for any other view.

## Static image (for a PDF, a deck, or a verification check)

```
https://public.tableau.com/views/EV_Charging_Site_Readiness_M2_Canonical/<Sheet>.png?:display_static_image=y&:showVizHome=n
```

---

## Prefer individual sheets over the dashboard when presenting

Three of the seven — `PortsAcrossHorizons`, `LifecycleCostbyHorizon`, `NetCO2ebyHorizon` —
render as a **narrow strip inside the dashboard**, because they have only four horizon
categories and the authoring spec offers no control over dashboard zone sizing
(see [`CAPABILITY_GAP.md`](CAPABILITY_GAP.md), residual blocker 5).

On their own URLs they use the full canvas and look right. So for a deck, the website, or
anything where the chart is the point, **embed the sheet, not the dashboard**.

---

## What every embed must carry alongside it

The workbook states its own caveats in every title and subtitle, but an embed can be cropped,
screenshotted or scrolled past. Whatever page hosts one of these must also carry, in its own
text:

> Screening-class planning study. **Electrical capacity is a placeholder at all twelve sites**
> — not evidence of feasibility. Demand is modelled, not measured. Costs are screening
> estimates for comparison, never budgets or quotes. Nothing here is approved, funded or
> permitted.

This is the same rule the NFC landing pages follow, and for the same reason: a number that
travels away from its caveat stops being a screening estimate and starts being a claim.
