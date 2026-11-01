# `docs/` - documentation index

[← repository root](../README.md)

## Start here
- Root [README](../README.md) - the launch film, both live sites, quick start, limitations
- [Start here](START_HERE.md) - a five-minute orientation with a reader map and an honest FAQ
- [What this can and can't tell you](WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md) · [Glossary](GLOSSARY.md) · [Install](INSTALL.md)
- [Reproduction guide](operations/reproduction-guide.md) - every verified command
- [Migration from V2](migration-from-v2.md) - old vs new commands, paths, and results
- [Migration from contract v1 to v2](migration-from-v3.md) - additive; the one change that can break a consumer is `horizon_label`

## For model users
- [Running EV-SIENT on your own sites](INPUT_SCHEMA.md) - intake, the cohort directory, every input field, and a worked example
- [The planner](../platform/README.md) - app.futurecity.andyyaro.com: the model in the browser, on a visitor's own file
- [Flexible analysis](FLEXIBLE_ANALYSIS.md) - the column dictionary, Explore and Your Index for columns the model does not score
- [Accessibility Conformance Report](accessibility/ACR.md) - the planner against WCAG 2.1 and 2.2 A and AA, self-assessed
- [Workflow steps](WORKFLOW_STEPS.md) (generated - regenerate with `make docs`)
- [`src/` guide](../src/README.md) · [`data/` guide](../data/README.md) · [`tests/` guide](../tests/README.md)
- [Current-facts source register](methodology/current-facts-source-register.md) - primary-source verification of every time-sensitive fact (2026-07-19)
- [How firm are the ranks?](methodology/rank_stability.md) - score breakdown, weight sensitivity and rank stability: a planning-support check, not a probability

## For technical reviewers
- [Repository migration plan](repository-migration-plan.md) - what was retained/replaced/archived and why
- [Legacy baseline verification](operations/legacy-baseline/BASELINE_VERIFICATION.md) - the reproduced V2 baseline this repo is golden-tested against
- [Technical integration architecture](architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md) (+ [diagram](assets/architecture/integration_architecture.png))

## For standards / safety reviewers
- [Standards application matrix](standards/FINAL_STANDARDS_APPLICATION_MATRIX.md)
- [Proposed standard concept](standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md) - fellowship design exercise, not a UL/ULSE proposal
- [Risk register](../reports/milestone-2/RISK_REGISTER.md)

## For municipal stakeholders
- [Economic & funding brief](../reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md)
- [Environment & resilience](../reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md)
- [Regulatory & stakeholder map](../reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md)

## For human-action owners
- [Open human actions](operations/open-human-actions.md) - what software cannot close, and who has to
- [Human-action packages](human-actions/README.md) - client meeting #2, team session, AHJ, utility data, public engagement, fellowship clarification (all drafts, nothing sent)

## For maintainers
- [Website/assistant patch package](operations/website-patch-package/README.md) - the patch applied in Phase 8.3; `site/www/` is now the source
- [Deployment](../DEPLOYMENT.md) - what is live, what it costs and how to undo it; [decisions log](operations/v4-program/DECISIONS.md)
- [The study site](../site/redesign/README.md) · [the launch film](../media/launch-film/README.md)
- [`scripts/` guide](../scripts/README.md) · [CI workflows](../.github/workflows/)
