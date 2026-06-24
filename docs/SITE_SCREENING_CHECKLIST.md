# Site Screening Checklist

## Purpose

Use this checklist before adding a new candidate site to the model.

The goal is simple: avoid adding random locations that do not clearly fit the project.

Companion checklist table:

```text
data/source_extracts/site_screening_checklist.csv
```

Expansion guide:

```text
docs/ADDING_NEW_SITES_GUIDE.md
```

## Quick decision

A site is worth adding if it passes most of these checks:

```text
1. It has parking.
2. It is public or has a clear public-agency use case.
3. It is near people, jobs, roads, transit, or public destinations.
4. It has enough dwell time for Level 2 charging.
5. It has no obvious access problem.
6. It adds something useful to the candidate list.
```

## Simple scoring

Use this rough screen before doing full data collection:

```text
2 = yes / strong fit
1 = maybe / needs more information
0 = no / weak fit
```

Suggested interpretation:

```text
10 to 12 points = good candidate to add
7 to 9 points = maybe add if it fills a gap
0 to 6 points = do not add yet
```

This is not the final readiness score. It is only a quick pre-screen.

## Checklist questions

| Check | Question | Why it matters |
|---|---|---|
| Parking | Does the site have parking spaces? | Chargers need a place where vehicles can sit. |
| Public/use case | Can the public use the site, or is there a clear agency use case? | The project is focused on public or public-serving charging. |
| Demand nearby | Is the site near people, jobs, traffic, transit, or destinations? | Better demand makes chargers more useful. |
| Dwell time | Are people likely to stay long enough for Level 2 charging? | Level 2 charging works best when vehicles park for a while. |
| Site clarity | Can we clearly explain why this site is being considered? | Reviewers should understand why it belongs in the model. |
| Expansion value | Does this site add something new compared with current sites? | Avoid adding many sites that all tell the same story. |

## When to add the site

Add the site to the model when:

```text
- the screen looks good,
- the address and coordinates are known,
- the site type is clear,
- basic parking or access assumptions can be written down,
- notes can explain what is confirmed and what is estimated.
```

## When not to add the site yet

Do not add the site yet when:

```text
- it has no parking,
- public access is unclear and there is no agency use case,
- the location is hard to explain,
- too many basic fields are unknown,
- it duplicates another nearby candidate without adding value.
```

## Next step after screening

If a site passes the screen:

```text
1. Copy a row from data/inputs/new_sites_template.csv.
2. Assign a new site_id.
3. Fill the first-pass public data.
4. Add notes for assumptions.
5. Run python src/validate_site_data.py.
6. Run python src/run_all.py.
```

## Simple rule

Screen first. Add only sites that are easy to justify.
