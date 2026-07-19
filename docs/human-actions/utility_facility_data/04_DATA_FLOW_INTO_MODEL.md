# How Received Data Flows Into the Model

*Explanation of the placeholder→verified upgrade path per data contract v1. This is the closure mechanism for D1 and for the "12/12 sites electrically unconfirmed" limitation. No data has been received; nothing below has been executed.*

## Current state (contract run `milestone2_v3_20260719T052322Z`)

Every scenario row carries:

- `capacity_basis = placeholder`
- `capacity_source = "legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)"`
- `capacity_confidence = none`
- `service_capacity_kw` and `spare_capacity_kw` empty
- `data_confidence = Low`

## Upgrade path per field

| Received datum (from register 03) | Contract field(s) updated | New `capacity_basis` value |
|---|---|---|
| Facility panel/service rating (from facility manager or walk-through) | `service_capacity_kw`; `capacity_source` = document/person + date; `capacity_confidence` | `verified_facility` |
| Utility service rating / transformer / feeder headroom (from Dominion) | `service_capacity_kw`, `spare_capacity_kw`; `capacity_source`; `capacity_confidence` | `verified_utility` |
| Interval load data 12+ months | `base_load_kw` replaced (measured profile instead of modeled constant); enables real spare-capacity calc: `spare_capacity_kw = service_capacity_kw − observed peak × safety margin` | (whichever of the above supplied the rating) |
| Service distance / panel details | feeds cost model (trenching/run length — the client's McCoart escalation driver) and layout drawings | n/a (cost inputs) |
| Parking counts, visitor/activity counts | demand-model calibration: replaces synthetic arrival assumptions; `data_confidence` upgrade Low → Medium/High per rubric | n/a |
| Fleet duty cycles | enables honest re-scoring of MCDA alternative D | n/a |
| Planned shutdowns / capital projects | scheduling constraints + conduit-opportunity flags in the staging plan | n/a |

## Rules

1. **Precedence:** `verified_utility` > `verified_facility` > `placeholder`. If facility and utility values conflict, keep both in `capacity_source`, use the more conservative for screening, and flag for resolution.
2. **Every upgrade is re-run, not hand-edited:** received values enter the site inputs, the model re-runs, and a new `run_id` is generated — scenario rows are never edited in place.
3. **Provenance:** `capacity_source` must name the document/person and date for every non-placeholder value; `source_date` updates accordingly.
4. **Confidence discipline:** `data_confidence` may rise only for sites whose specific fields were verified — partial receipt yields partial upgrades, and the "0 High-confidence sites" statement in the presentation changes only when the underlying rows do.
5. **Ranking sensitivity:** after any capacity verification, re-check the site ranking and the MCDA sensitivity notes; a site failing verified-capacity screening triggers the documented fallback to the next-ranked site (logged in the decision log).
