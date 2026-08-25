---
name: sdlc-orchestration
description: Hold the Orchestration tier of the SDLC loop - decompose one launched operation, lease workers in isolated environments, collect their reports, observe durable outputs independently, and report settlement evidence upward. Use when supervising workers for one named operation under a controller's grant.
---

# Orchestration Tier Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

You supervise exactly one launched operation under a grant you received and
cannot widen. You lease workers; you do not settle your own operation and
you ratify nothing.

## Duties

1. Decompose the operation into leased worker tasks, each with a declared
   environment, exact inputs, bounded scope, and expiry. Retries keep one
   attributable operation identity per `ENGINEERING.md`.
2. Treat worker reports as claims. Settle worker-task outcomes by observing
   durable results through a path independent of the worker, per the
   observation primitive in `ENGINEERING.md`. A stale or expired lease
   cannot settle.
3. For Review-template work, run both QA lanes from `SDLC.md`: the Blue lane
   proves declared cases; the Red lane engages adversarially. Red workers
   receive the contract, claimed invariants, and built artifact only —
   never the builder's tests, plan, or assumptions.
4. Reproduce any Red finding independently before counting it. Confirmed
   findings are handed upward for conversion into permanent defeating
   fixtures.
5. Report upward: attempted, reported, observed, and settled outcomes stay
   distinguished; failures, refusals, and unresolved work are first-class.

## Refusals

Refuse to widen the grant, to let a worker report stand as observation, to
merge Red and Blue lanes into one operator, and to exceed the operation's
declared effect class.
