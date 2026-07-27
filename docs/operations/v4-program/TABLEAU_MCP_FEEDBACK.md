# Feedback: `tableau-public-authoring` MCP server (v0.1, spec v0.1)

Written 2026-07-27 after building and publishing a real 7-sheet workbook with it, against
Tableau Public 2026.2.0 on macOS. Ordered by how much damage each issue caused.

**Context that makes this feedback worth something:** every issue below was found by
publishing and then *looking at the rendered result*, not by reading the generated XML.
Three of them produce a workbook the server reports as a clean success — `"ok": true`,
`"warnings": []` — that is visibly broken in public.

---

## 1. A tooltip MEASURE silently blanks the entire sheet — highest severity

**What happens.** A measure on `tooltips` with no aggregation compiles to
`derivation="None" type="quantitative"`. Tableau treats it as a level-of-detail field,
cannot resolve it, and **the whole worksheet renders as its title and subtitle with no chart
underneath.** The static render is 793×90 px instead of 793×681.

**Reproduction:**

```json
{"name": "Ports Across Horizons", "template": "line", "data_source": "horizons",
 "rows": [{"field": "ports_active", "aggregation": "Sum"}],
 "columns": ["horizon"], "color": "scenario_name",
 "tooltips": ["pathway_capacity", "model_mode"]}
```

`pathway_capacity` is numeric. The sheet builds, validates, publishes, and draws nothing.
Adding `{"field": "pathway_capacity", "aggregation": "Sum"}` fixes it completely.

**Why this one stings.** `AUTHORING_SPEC.md` already documents this exact failure mode for
the *dimension* case, and handles it:

> **Dimensions placed on `tooltips` are automatically promoted to `Attribute`.** With `None`
> they become level-of-detail fields, Tableau cannot resolve the reference, and the sheet
> renders blank with a red pill. This is applied for you.

Measures hit the identical failure and get neither the promotion nor a warning. The server
already knows this shape of bug is fatal and already knows how to detect it — the check just
does not cover the other half of the type space.

**Suggested fix, in order of preference:**
1. Reject a bare measure on `tooltips` in `validate_workbook_spec`, with the same message
   quality as the existing measure-on-`filters` rejection (which is excellent — it explains
   *why* and tells you what to do instead).
2. Or auto-promote to `Attribute`, symmetrically with dimensions.
3. At minimum, emit a `warning` in the build result rather than `"warnings": []`.

---

## 2. Nothing detects a worksheet that will draw nothing

**What happens.** Two separate causes produced a published, world-visible chart consisting
of axis labels and white space, and in both cases the build reported success with no
warnings:

- issue 1 above;
- a measure that is **constant across every row**. Our peak-waits sheet plotted `p50` and
  `p90`, which are genuinely `0.0` at all twelve sites. Valid data; empty chart.

**Suggested fix.** A cheap post-build check with a big payoff: for each worksheet, if the
plotted measure has ≤1 distinct value in the source CSV, warn. It cannot be an error — a
legitimately flat series exists — but the caller should be told before it goes public.

We ended up implementing both checks on our side
(`scripts/build_tableau_workbook.py::refuse_bare_tooltip_measures` and
`refuse_uninformative_measures`). They are ~15 lines each. They belong in the server, where
every caller benefits.

---

## 3. A digit-only string column silently becomes a measure

**What happens.** Type inference runs on the **CSV on disk**, so a column written as the
string `"2026"` is read back as an integer and becomes a measure. A measure on `columns`
gives a continuous axis: tick marks at 2028, 2030, 2032 between the only four horizons that
exist, and — combined with issue 1 — a sheet that drew nothing.

The caller has **no way to express "this is a category"**. We worked around it by making the
labels `"2026 baseline"`, `"2036 (+10y)"` … so they contain letters. That works, but it
means a year axis cannot be a clean `2026 2036 2046 2056` without a hack.

**Suggested fix.** An optional per-source type override, e.g.
`{"id": "horizons", "path": "...", "types": {"horizon": "string"}}`. The `datatype` key
already exists on `calculated_fields`, so the vocabulary is there.

---

## 4. No sort key, so a "ranking" chart is alphabetical

**What happens.** A bar chart draws its categories in the dimension's natural order. For a
site name that is alphabetical, so a sheet titled *"Site readiness ranking"* published with
sites in alphabetical order — a chart that misleads by omission, since a reader infers order
from left to right.

Worked around by embedding the rank in the label (`01 Fairfax County…`), which is arguably
better UX anyway, but it should not be the only option.

**Suggested fix.** `"sort": {"field": "readiness_score", "direction": "desc"}` on a
worksheet. This is probably the single most-requested thing a real workbook needs.

---

## 5. `series` on colour alone stacks; there is no way to ask for grouped

**What happens.** With one measure and a dimension on colour, Tableau stacks. Our
starter-vs-pathway chart published showing `3 + 8 = 11` ports — **a number that does not
exist**, because the two series are not additive.

Worked around by putting the series dimension on `rows` as a second level, which nests and
groups. That works and is discoverable *once you know*, but stacking-vs-grouping is a
semantic choice about whether the measures sum, and the default silently assumes they do.

**Suggested fix.** Document the rows-nesting idiom in `AUTHORING_SPEC.md` under `color`, or
add `"mark_stacking": "stacked" | "grouped"`.

---

## 6. `fit` does not affect dashboard rendering at all — and the docs imply it does

**This is the one that cost the most time, because the documentation reads as though `fit`
controls layout generally.** `AUTHORING_SPEC.md` says:

> **`fit`** is how the viz fills its canvas.

In the generated XML, `fit` is emitted as:

```xml
<window class="worksheet" name="Ports Across Horizons">
  ...
  <viewpoint><zoom type="fit-width"/></viewpoint>
</window>
```

That is the **worksheet window's own viewpoint** — how the sheet displays when you open its
tab in Desktop. It is **not** a property of the dashboard zone, so it has no effect
whatsoever on how the sheet renders inside a dashboard.

Consequence: a chart with few categories (our 4 horizons) renders as a narrow strip in a
full-width dashboard zone, and **there is no way to change that through the spec.** Changing
`entire_view` → `fit_width` produced a byte-identical dashboard render, verified by three
cache-busted fetches after a confirmed publish.

Compounding it: since Tableau Public publishes with `showTabs: false`, the worksheet tab view
that `fit` *does* control is the one view a reader can never reach. As emitted, `fit` is inert
for any published-to-Public workbook.

**Suggested fix:**
1. Say in the docs that `fit` sets the worksheet window viewpoint and does not affect
   dashboard zones — that one sentence would have saved a publish cycle.
2. Add a per-zone fit on `dashboards[].worksheets[]`, e.g.
   `{"worksheet": "Ports Across Horizons", "fit": "fit_width"}`, which is what actually
   governs the rendered output.

---

## 6b. No way to publish with sheet tabs visible

The generated `.twb` contains **no tab-visibility setting whatsoever** (grepped: no
`show-tabs`, no equivalent). Tableau Public therefore applies its default, `showTabs: false`,
and a reader who opens the published URL sees only the default view.

Every other worksheet is genuinely published and individually addressable, but there is **no
navigation to them from the viz**. A caller who builds seven sheets and one dashboard
reasonably expects seven reachable sheets, and gets one, silently.

Two URL forms exist and they are **not** interchangeable — the distinction is undocumented
and easy to get wrong:

| Purpose | Form |
|---|---|
| Share / embed (what the Share button gives) | `/views/<workbook>/<Sheet>?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link` |
| Profile page route | `/app/profile/<profile>/viz/<workbook>/<Sheet>` |

Both return HTTP 200 and both return the same ~1.4 KB JavaScript shell, so a status-code
check cannot tell them apart or confirm either renders.

This interacts badly with issue 6: a chart squeezed into a dashboard zone renders narrow and
cannot be fixed, while the same chart on its own tab renders full-size — but that tab is
exactly what the reader cannot reach.

**Suggested fix.** A workbook-level `"show_tabs": true` in the spec, or at minimum a line in
`PUBLISHING_WORKFLOW.md` saying that published workbooks hide tabs by default, plus **both**
per-sheet URL forms and which is which. Better still, have `publish_to_tableau_public` return
a `sheet_urls` map in its result — the server already resolves and verifies the workbook URL,
so it is well placed to emit the share form for every sheet it just published.

---

## 7. Title and subtitle render with no separation

Published output reads `Active ports by planning horizon48-port pathway ceiling is in the
tooltip…` — the subtitle butts directly against the title with no space or line break. Every
sheet is affected. Cosmetic but universal, and it makes an otherwise careful workbook look
unfinished.

---

## 8. `publish_to_tableau_public` — the save click misses

Of five publish attempts, **three needed the human to click Save manually**. The server
reports honestly (`"error": "the save dialog never closed; publication was not submitted"`,
`"published": false`), which is exactly right and much better than a false success. But the
click at a computed coordinate did not land, and the log line is confusing:

```
"save button: clicked at (1003,593) within dialog bounds 382x191"
```

(1003, 593) cannot be within a 382×191 region — those are screen coordinates being reported
against dialog-relative bounds. Whatever the cause, a coordinate click into an AppKit sheet
is fragile; hitting Return, or querying the button's accessibility element and pressing it,
would be sturdier.

**Also:** each publish takes >120 s and gets backgrounded by the client. Not the server's
fault, but a progress signal would help.

---

## What the server gets right, and should not lose

Worth saying plainly, because the list above is all complaints:

- **`publication_confirmed: false` with a real explanation** when a workbook of that name
  already existed — *"a reachable URL does not by itself prove this upload succeeded…
  Tableau's profile API exposes no publish timestamp"*. That is exactly the right epistemics.
  A lesser tool would have returned success because a URL returned 200.
- **The measure-on-`filters` rejection** explains why and what to do instead. It is the model
  the tooltip rule should follow.
- **`validate_workbook_spec` as a genuine dry run**, and the layered validation with a second
  independent pass over the *generated* file.
- **Honest determinism claim**: the docs say the `.twb` is byte-deterministic and the `.twbx`
  is not, because of Hyper state. We measured it — two builds from an identical spec gave an
  identical `.twb` and different `.twbx` digests. The documentation was exactly right, which
  let us gate on the `.twb` with confidence.
- **The capability boundary is stated up front and is accurate.** Everything
  `get_authoring_capabilities` said was unsupported really was, and nothing it claimed to
  support failed structurally. That made the gap assessment honest work rather than guesswork.

---

## The one-line summary

The server's *validation* is thoughtful and its *honesty* is excellent. The gap is that
nothing checks whether a successfully-built worksheet will actually **draw anything** — and
three of the issues above (1, 2, 3) converge on that same blind spot. A workbook that
compiles, validates, publishes and renders blank is the worst outcome available, because
every signal says it worked.
