# Data Confidence Score

## Purpose

The model keeps two ideas separate:

```text
readiness_score = how promising the site looks

data_confidence_score = how complete and source-supported the current input data is
```

The confidence score does not change the ranking.

## Active V2 output columns

These columns are included in:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_executive_site_summary.csv
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

## Public visual layer

The main public-facing visual artifact is the Tableau workbook documented in:

```text
tableau/README.md
```

The workbook includes a data confidence and review issues view.

Static data-confidence charts remain support outputs for reproducibility and technical package review.

## Static support chart

The generated V2 chart is:

```text
data/outputs/charts/v2_data_confidence_chart.png
```

The chart is intentionally simple:

```text
one horizontal bar per candidate site
site order follows model rank
bar length = data confidence score
label = confidence score and confidence level
threshold guides = Medium and High confidence levels
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

The score looks at project fields such as parking, hours, public access, service distance, trenching distance, estimated activity, source notes, and electrical placeholders.

## Current source-confidence interpretation

```text
Official or official-derived values raise trust.
Reviewed open GIS / POI values are usable but should still be labeled as open-data support.
Manual estimates, planning estimates, planning proxies, placeholders, and unconfirmed notes lower confidence.
```

## How to improve confidence

```text
1. Record stakeholder or official-source answers in data/source_extracts/stakeholder_response_tracker.csv.
2. Update data/inputs/real_sites_v2.csv only when the answer has a source, date, and confidence level.
3. Update source extracts or notes when a value changes.
4. Re-run python src/run_v2.py.
5. Re-run python src/check_outputs_v2.py.
6. Re-run python src/build_tableau_exports.py if the Tableau workbook needs refreshed data.
7. Review data/outputs/v2_site_results.csv, data/outputs/v2_executive_site_summary.csv, and the Tableau workbook.
```

## Simple rule

Readiness says where to focus.

Confidence says how careful to be with that result.

A strong score with low confidence is not a build recommendation. It is a reason to verify the site first.
