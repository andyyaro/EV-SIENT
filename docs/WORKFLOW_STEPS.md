# V3 Workflow Steps (generated from fcf_m2.workflow.STEPS - do not edit by hand)

Step count: **11**

1. **load_inputs** - Load site table, electrical-risk fixture, provenance, anchors, MATLAB site meta
2. **score_sites** - Score readiness (legacy min-max or V3 fixed anchors) + Erlang-C port screen
3. **right_sizing** - Starter vs pathway right-sizing (legacy 2035/2050 or V3 2026/2036/2046/2056)
4. **confidence** - Structured field-level data confidence (V3) / legacy confidence passthrough
5. **peak_wait** - Peak-window Erlang and seeded discrete-event wait simulation (P10/P50/P90)
6. **economics** - Lifecycle NPC: staged vs overbuild vs defer at 2036/2046/2056, low/base/high
7. **emissions** - Net avoided CO2e with sourced grid factor + avoided-EVSE resource metric
8. **scenario_table** - Assemble canonical scenario rows (all required contract fields)
9. **contract** - Validate + write versioned hybrid CSV/JSON contract with manifest hashes
10. **matlab_adapter** - Generate MATLAB input CSV from the contract (capacity_basis on every row)
11. **summary** - Write run summary with headline totals and claims-discipline labels
