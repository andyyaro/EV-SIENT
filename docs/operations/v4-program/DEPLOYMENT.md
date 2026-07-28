# DEPLOYMENT — pointer, not a copy

**The deployment record lives at [`/DEPLOYMENT.md`](../../../DEPLOYMENT.md) in the repository
root.** It carries everything this slot requires: what is live, every resource created and how
to remove each one, the measured cost table, how to deploy, the guard that makes the deploy
safe, deploying from CI, risks including the ones that already happened, what is verified and
what is not, and open items.

## Why this file is a pointer

The Phase 10 deliverable list asks for a `DEPLOYMENT.md` under `docs/operations/v4-program/`.
A second copy of a document that already exists is the drift mechanism this entire program has
been fighting: this session alone found a test count that was correct when written and stale in
three places, a MATLAB status that the README asserted twice in contradictory forms, and a
gallery that drifted from the model it was generated from and published the wrong top-ranked
site for months.

Two deployment documents would disagree the first time either one changed, and the one nobody
opened would be the one still claiming the old thing. So there is one, and this points at it.

The root location is the right canonical home because that is where a person deploying looks
first, it is linked from the README and the CI workflow, and it is not buried three directories
deep in a program record that will be historical the moment this program lands.

## What is specific to this program

The deployment work carried out under the V4 program — the two-bucket architecture, the
Lambda@Edge Cognito gate, the measured percent-encoding behaviour that made a structural
guarantee necessary rather than a behavioural one, and the cost figures — is recorded in
`/DEPLOYMENT.md` and in the dated rows of [`LEDGER.md`](LEDGER.md). What still needs a person is
in [`RESIDUAL_RISKS.md`](RESIDUAL_RISKS.md) §4 and §8, and what was actually observed working is
in [`VERIFICATION.md`](VERIFICATION.md) §5.
