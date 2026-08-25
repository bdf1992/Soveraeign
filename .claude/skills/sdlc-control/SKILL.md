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

## Loop

1. Derive the concern registry by reading `STATUS.yaml`, `decisions/`, and
   `OPEN-SEAMS.md`. Keep no private concern state — the registry is a
   rebuildable projection of those documents.
2. Select one concern and one named operation. Work one operation at a time
   per the context-hygiene rules in `AGENTS.md`.
3. Declare the operation plan per the change protocol in `AGENTS.md`:
   outcome, affected contracts, preconditions, effect class, rollback or
   refusal boundary.
4. Choose a workflow template from `SDLC.md` (Report, Standup, Review, Demo,
   Design) and launch the orchestration with a grant narrower than your own.
5. Settle through observation independent of the executor. An orchestration's
   report is evidence, not settlement.
6. Record standing changes in the owning documents and residuals in
   `OPEN-SEAMS.md`. Apply the release gate in `SDLC.md`: nothing passes
   `BUILT` without a settled Red engagement receipt.
7. Escalate every judgement item to the owner as a visible pending right.
   Escalation is a first-class transition, not a failure.

## Refusals

Refuse to ratify, to advance standing without the required evidence, to
launch work with no governing contract, fixture, or explicit experimental
label, and to perform any `EXTERNAL_WORLD` effect outside a scope
`contracts/external-effect-authorization.json` declares.
