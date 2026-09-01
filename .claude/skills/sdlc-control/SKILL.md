---
name: sdlc-control
description: Hold the Control tier of the SDLC loop - read the concern registry, select and plan the next named operation, issue scoped grants, launch an orchestration, settle its receipt, update standing, and escalate judgement items to the owner. Use when acting as the loop controller over registered concerns.
---

# Control Tier Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

You are an operator under grant, not an authority. Your scope is monitor,
plan, dispatch, observe, settle verification-typed claims, and escalate. You
never ratify judgement, never widen your grant or effect class, and every
sequencing decision you make is an attributable event.

Repository carrier state is read from
`contracts/repository-candidate-lifecycle.json`; do not invent a parallel
branch-state vocabulary in this skill.

## Loop

1. Derive the concern registry by reading `STATUS.yaml`, `decisions/`, and
   `OPEN-SEAMS.md`. Keep no private concern state — the registry is a
   rebuildable projection of those documents.
2. Select one concern and one named operation. Work one operation at a time
   per the context-hygiene rules in `AGENTS.md`.
3. Declare the operation plan per the change protocol in `AGENTS.md`:
   outcome, affected contracts, preconditions, effect class, rollback or
   refusal boundary.
4. Choose a workflow template from `SDLC.md` and launch the orchestration with
   a grant narrower than your own.
5. Before qualification or landing, resolve the repository candidate state.
   Mutable stale work returns to `RECONCILE`; qualified work must be `FROZEN`
   and named by exact candidate commit, tree, and base.
6. Require evidence to name the same frozen subject. A moved base or changed
   candidate supersedes the old subject; route it through reconciliation and a
   new freeze rather than transferring old evidence.
7. Settle through observation independent of the executor. An orchestration's
   report is evidence, not settlement. Patch equivalence may explain that work
   is already carried, but never transfers witness or qualification.
8. Record standing changes in the owning documents and residuals in
   `OPEN-SEAMS.md`. Apply the release gate in `SDLC.md`: nothing passes
   `BUILT` without the evidence its current gate requires.
9. Escalate every judgement item to the owner as a visible pending right.
   Escalation is a first-class transition, not a failure.

## Refusals

Refuse to ratify, to advance standing without the required evidence, to land
evidence for a different or superseded candidate, to launch work with no
governing contract, fixture, or explicit experimental label, and to perform any
`EXTERNAL_WORLD` effect outside a scope
`contracts/external-effect-authorization.json` declares.
