# Data Confidence Score

## Purpose

The model now keeps two ideas separate:

```text
readiness_score = how promising the site looks

data_confidence_score = how complete the current input data is
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

## Main idea

Use both scores together:

```text
High readiness + High confidence = strongest case
High readiness + Medium or Low confidence = promising but needs better data
Low readiness + High confidence = likely lower priority
Low readiness + Low confidence = weak result until data improves
```

## What affects the score

The score looks at simple project fields such as:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
distance_to_service_ft
trenching_ft
parking_spaces
hours_open
visitors_day
employees_day
public_access
garage_enclosed
notes
```

## Simple rule

Readiness says where to focus.

Confidence says how careful to be with that result.
