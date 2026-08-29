---
name: sdlc-qa
description: QA domain competence for the SDLC loop - both verification stances. The Blue lane continuously proves declared positive and defeating cases for each work unit; the Red lane is a separately queued milestone operation that adversarially seeks undeclared defeats under a scoped grant. Use when verifying, witnessing, or challenging built work.
---

# QA Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

`SDLC.md` owns the Red/Blue dyad and the release gate. One operator holds
one stance per engagement; the lanes must not merge. `decisions/0098-milestone-witnessing.md`
owns the cadence change: Blue is continuous, Red is queued at named milestones.

## Blue lane

Blue belongs to every consequential work unit. Deferring independent witness
never defers expected engineering verification.

1. Prove every consequential behavior with at least one positive case and
   one declared defeating case, per `AGENTS.md` testing rules.
2. Run unit tests beside the service, semantic cases in `conformance/`, and
   `python scripts/verify.py` from a clean root within its budget.
3. Distinguish attempted, reported, observed, and settled outcomes. A green
   run establishes `BUILT` evidence only.
4. Continue reachable engineering work after `BUILT` when the next transition
   does not consume independent observation. Unwitnessed standing is not by
   itself a block.

## Red lane

Red is dispatched as a `verification-engagement` against a named milestone. It
is not the default next operation after every Blue increment.

1. Pin the exact target bytes before attacking them. Under the current ticket
   contract the engagement names `target_pr` and `target_head`; the PR is a
   carrier for the immutable milestone target, not the milestone's semantic
   identity.
2. Operate only under a typed grant naming target surfaces, effect class
   (Phase I: `RECORD_LOCAL`, isolated environments, no authoritative
   writes), budget, and exit criterion.
3. Work from the contract, claimed invariants, and built artifact — never
   from the builder's tests, plan, or assumptions, and never importing the
   participant implementation.
4. Hunt undeclared defeats: refusal bypasses, authority escalation,
   stale-source use, provenance gaps, retraction that erases history,
   executor-only success.
5. File findings as proposals with exact reproduction inputs. A finding
   counts only after independent reproduction; confirmed findings become
   permanent defeating fixtures.
6. Stop at dry-run convergence: the declared number of consecutive rounds
   with no new confirmed finding.
7. Treat a failed witness as evidence against the named milestone and claims
   that depend on its defeated predicate. Do not convert it into a global stop
   on unrelated reachable work.

## Witness debt

A milestone that owes independent verification must have an address: a queued
`verification-engagement`, immutable target, and named claim or surface. “Later”
with no address is not a witness plan.

A target may keep moving in circuit stage, scope, and implementation state while
its standing stays `BUILT`. The witness becomes mandatory when the next requested
transition explicitly consumes it, including `BUILT -> WITNESSED`, a release or
acceptance gate that requires witnessed evidence, and `CAPABLE_NODE` admission.

## Refusals

Refuse to weaken a fixture to admit a participant, to witness work you built,
to fabricate or inflate findings, to exceed the engagement grant, to claim
`WITNESSED` because ordinary work continued, or to defer witness without an
address once a milestone requires it.
