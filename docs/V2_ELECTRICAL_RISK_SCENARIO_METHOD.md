# V2 Electrical-Risk Scenario Method

## Why this exists

The V2 model still has unconfirmed electrical inputs for many candidate sites. Instead of pretending those fields are known, the prototype now uses a scenario-based electrical-risk screen.

This is a planning-support method only. It does not replace utility, engineering, AHJ, Fire Marshal, facilities, or permitting review.

## What the module does

The module reads the generated V2 results table and adds:

```text
electrical_risk_points
electrical_risk_level
electrical_risk_reason
electrical_data_needed_next
electrical_adjusted_score
electrical_adjusted_rank
```

It then tests three electrical cases:

```text
optimistic_electrical_case
expected_electrical_case
conservative_electrical_case
```

## Risk signals

The model assigns electrical-risk points for practical screening issues such as:

```text
unknown electrical service rating
unknown spare capacity
emergency disconnect visibility not confirmed
garage or enclosed-structure context
limited public access or special-use context
long distance-to-service assumption
long trenching assumption
high service-upgrade cost assumption
stormwater or runoff review risk
battery-storage review risk
public-safety facility context
```

## Risk levels

```text
0 to 3 points: low electrical risk
4 to 7 points: medium electrical risk
8 or more points: high electrical risk
```

## Scenario penalties

The scenario analysis subtracts a small planning penalty from the base readiness score.

```text
optimistic_electrical_case: low = 0, medium = 1, high = 2
expected_electrical_case: low = 0.5, medium = 3, high = 6
conservative_electrical_case: low = 2, medium = 6, high = 12
```

The goal is not to punish sites permanently. The goal is to show which rankings are sensitive to electrical uncertainty.

## Generated outputs

The V2 workflow now writes:

```text
data/outputs/v2_electrical_scenario_results.csv
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_electrical_feasibility_report.md
```

## How to interpret it

If a site stays high-ranked under the expected and conservative electrical cases, it is less sensitive to electrical uncertainty.

If a site drops sharply under the conservative case, it should receive earlier electrical review before advancement.

Do not remove a site only because of high electrical risk. Use the result to decide what needs confirmation next.
