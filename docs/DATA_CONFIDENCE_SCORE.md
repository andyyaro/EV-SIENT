# Data Confidence Score

## Purpose

The model keeps two ideas separate:

```text
readiness_score = how promising the site looks

data_confidence_score = how complete and source-supported the current input data is
```

The confidence score does not change the ranking.

## Output columns

These columns are added to:

```text
data/outputs/site_results.csv
```

```text
data_confidence_score
data_confidence_level
data_confidence_reason
```

## Levels

```text
75 to 100 = High
50 to 74.9 = Medium
0 to 49.9 = Low
```

## Data confidence visual

The generated chart is:

```text
data/outputs/charts/data_confidence_chart.png
```

The committed preview used by GitHub Markdown should be synced from the generated chart to:

```text
docs/assets/charts/data_confidence_chart.png
```

![Data confidence chart](assets/charts/data_confidence_chart.png)

The chart is intentionally simple:

```text
one horizontal bar per candidate site
site order follows model rank
bar length = data confidence score
label = confidence score and confidence level
vertical guides = Medium and High thresholds
```

The purpose is not to re-rank sites. The purpose is to show how careful we should be with each model result.

## Main idea

Use both scores together:

```text
High readiness + High confidence = strongest case
High readiness + Medium or Low confidence = promising but needs better data
Low readiness + High confidence = likely lower priority
Low readiness + Low confidence = weak result until data improves
```

## What affects the score

The score looks at simple project fields such as parking, hours, public access, service distance, trenching distance, estimated activity, and electrical placeholders.

## Current source-confidence interpretation

```text
Official or official-derived values raise trust.
Reviewed open GIS / POI values are usable but should still be labeled as open-data support.
Manual estimates, planning estimates, planning proxies, placeholders, and unconfirmed notes lower confidence.
```

## How to improve confidence

```text
1. Record stakeholder or official-source answers in data/source_extracts/stakeholder_response_tracker.csv.
2. Update data/inputs/real_sites_v1.csv only when the answer has a source, date, and confidence level.
3. Update source extracts or notes when a value changes.
4. Re-run python src/run_all.py.
5. Review data/outputs/site_results.csv and data/outputs/action_matrix.md.
```

## Simple rule

Readiness says where to focus.

Confidence says how careful to be with that result.

A strong score with low confidence is not a build recommendation. It is a reason to verify the site first.
