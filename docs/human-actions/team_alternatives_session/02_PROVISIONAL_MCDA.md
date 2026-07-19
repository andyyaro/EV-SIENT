# PROVISIONAL — TEAM MUST REVIEW/AMEND/ADOPT

# Provisional MCDA — Seven Alternatives × Six Criteria

*Source: the research-phase ranking `SOLUTION_ALTERNATIVES_MCDA.csv` (pre-V3 research archive, not tracked in this repository; researched scores, 0–5 anchored). These are research inputs to the team session, not the team's decision. The team may re-score any cell with a stated reason; the adopted matrix lives on the scoring sheet (03), not here.*

## Weights (audit-recommended defaults — adopt or amend via 04)

| Criterion | Weight |
|---|---|
| Safety / code readiness | 25 |
| Demand fit / service quality | 20 |
| Lifecycle cost / funding | 20 |
| Expandability / resilience | 15 |
| Equity / public value | 10 |
| Data confidence / implementation risk | 10 |

## Matrix (scores 0–5; weighted score /100)

| Alt | Alternative | Safety 25 | Demand 20 | Cost 20 | Expand 15 | Equity 10 | Confidence 10 | Weighted | Rank |
|---|---|---|---|---|---|---|---|---|---|
| A | Broad immediate distributed buildout | 2 | 2 | 1 | 3 | 4 | 1 | 41.0 | 6 |
| B | Distributed staged pilots + expandable pathways | 4 | 4 | 5 | 5 | 3 | 4 | **85.0** | **1** |
| C | EV-ready first, limited active EVSE | 4 | 2 | 4 | 5 | 2 | 4 | 71.0 | 4 |
| D | Centralized fleet hub + selective public | 3 | 3 | 3 | 3 | 2 | 3 | 58.0 | 5 |
| E | Managed-charging-first | 4 | 3 | 4 | 4 | 3 | 3 | 72.0 | 3 |
| F | Hybrid portfolio (B + C + E, coordinated with D) | 4 | 4 | 4 | 5 | 4 | 3 | 81.0 | 2 |
| G | Do nothing / defer (comparator) | 3 | 0 | 3 | 1 | 0 | 5 | 37.0 | 7 |

## Evidence notes (per row, from the researched CSV)

- **A:** Contradicted by the client's own Neabsco experience (70 ports, 17 stations later shut off, ~$1k/station/yr); 12/12 sites electrically unconfirmed; single-digit simulated utilization.
- **B:** Matches modeled low current utilization + growth scenarios; captures cheap expansion during civil work (client trenching-cost evidence); keeps AHJ/electrical gates; equity limited until expansion triggers fire.
- **C:** Mirrors the PWC Animal Services Center pattern (EV-ready conduit, no charger yet); minimal capex but little near-term service or visible value.
- **D:** PWC is already pursuing a ~35-station fleet hub — for the county this is complementary reality, not the team's public-site answer; ADA clustering cost issue reported by client and Dominion; fleet duty-cycle data absent.
- **E:** The MATLAB model already illustrates managed vs unmanaged load; defers service upgrades; requires networked EVSE + comms reliability with fail-safe design; not a siting strategy by itself.
- **F:** Combines B's evidence base with E's load control and D-awareness; more moving parts to explain and govern in a 12-minute presentation.
- **G:** Zero service/equity value; wastes the proactive planning window the fire-service evidence identified; lowest implementation risk only.

## Known sensitivities (read before adopting)

- **Equity crossover:** at roughly 2× the default equity weight (~20 vs 10), **F overtakes B**. See the disclosure in `04_WEIGHT_ADOPTION_PAGE.md`.
- Faster near-term adoption evidence improves F and A (A still cannot win while all 12 sites lack electrical confirmation).
- A client priority on fleet over public makes D the frame (a client question, not a scoring question).
- Budget collapse makes C the floor option.
