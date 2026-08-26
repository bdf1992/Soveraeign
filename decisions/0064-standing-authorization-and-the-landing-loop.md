# 0064 · A standing authorization, and the loop that spends it

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

`SPEC.md` has declared the `AuthorityGrant` object since the founding spec and required an
authority check at every consequential transition (PROD-I-5). Nothing implemented it. Work
leases already carried a `grant_id` field pointing at an object no file held. The practical
consequence was that no run could ever finish: every workflow in the repository ends with an
uncommitted working tree and a queue pointed at Bdo, because the only way to move a change
onto `main` was to ask him for that change specifically.

Three things are decided.

First, the grant object exists. `contracts/authority-grant.schema.json` compiles the SPEC
object, and `scripts/sovkernel/authority.py` is the check SPEC requires: type, capability,
scope, budget, time, and revocation, evaluated at the attempted transition.

Second, one standing grant is issued. `grant:standing-landing-loop` in
`contracts/standing-grants.json` lets a change that is inside scope, on `main`, under budget,
green on `verify` and `lint`, and independently observed reach `main` without a fresh
conversation. Bdo settled its three terms on 2026-08-25: the loop's terminal is commit and
merge to `main`; its scope is code, contracts, tests, and scripts; its effect ceiling is
`RESOURCE_CONSUMPTION`.

Third, the loop that spends it exists. `.claude/workflows/sov-loop.js` runs one concern
through control, orchestration, work, an independent witness, and `scripts/sov_land.py`,
which is the only place in the repository that commits and merges.

## Why a standing grant is not a wider grant

A standing grant is the same typed, scoped, budgeted, expiring object as a task grant. What
changes is when it is decided, not how far it reaches. `decisions/0023` already settled that
Bdo's gate is acceptance over an evidenced result and never permission to begin; asking him
to authorize each merge individually was the pre-approval that decision refuses, arriving
under a different name.

Three separate mechanisms keep the grant away from standing, and each would have to fail
independently for the loop to settle anything:

- the excluded paths keep it out of `decisions/`, `lineage/`, `STATUS.yaml`, `.github/`, and
  every root governing document, and out of its own registry and schema, so an exercise of
  the grant cannot widen the grant it is being exercised under;
- the `VERIFICATION` authority type cannot ratify a `JUDGEMENT` claim (`SPEC.md`, PROD-I-5),
  so the grant could not be used to record standing even if a path slipped through;
- `requires_independent_observation` means a build still cannot close itself, which is the
  rule `AGENTS.md` has held since the founding contract.

A landed commit under this grant is `BUILT` plus an independent observation. It is not
`WITNESSED` in the sense the artifact lifecycle reserves for a settled observation, and it is
not `RATIFIED`. Landing removes a conversation about merging. It removes no gate.

## What the grant costs to keep

The grant expires on 2026-11-23. That is deliberate and it is the main ongoing cost: ninety
days from now somebody has to decide again, or the loop stops landing. A standing grant that
never has to be renewed has stopped being a decision and become a habit.

Its budget is sixty agent invocations per exercise, in the grant's own unit. `sov-loop`
counts its own invocations and declares them to the gate, so a run that sprawled past its
envelope is refused at the landing gate rather than nowhere.

## Refusal vocabulary

No new refusal code was minted. The gate reports the codes
`contracts/kernel-transitions.json` already declares:

| Code | Fires when |
| --- | --- |
| `AUTHORITY_REFUSED` | no live grant covers the request: unratified, revoked, expired, wrong actor, capability not carried, path out of scope, branch not admitted, budget exhausted, effect class above the ceiling |
| `EFFECT_CLASS_REFUSED` | the phase refuses the declared effect class outright, before any grant is consulted |
| `OBSERVATION_MISSING` | the grant requires an independent observation and none was offered, or it did not confirm |
| `OBSERVER_NOT_INDEPENDENT` | the observation came from a participant that contributed to the build |
| `MISSING_PRECONDITION` | a required check is absent from the evidence or did not pass |

An out-of-scope path and an expired grant are both `AUTHORITY_REFUSED`, distinguished by the
detail sentence rather than by a second vocabulary. That is a deliberate choice: the kernel's
refusal set is small on purpose, and a reader who needs the specific reason gets it in the
sentence.

## Evidence

`conformance/fixtures/authority/grant-cases.json` carries twenty-one cases: two prove a
live grant covers a request, nineteen prove a refusal, and every refusal code the evaluator
can report has at least one case proving it fires. `python scripts/sov_grant.py selfcheck` grades
them and also validates every issued grant against the schema, so a grant that no case could
exercise cannot sit in the registry looking authoritative. The check runs inside
`python scripts/verify.py` as `standing authority grants`.

## Defaults taken

- The grant's actor is the profile name `sov`, so one grant serves both a Bdo-driven session
  and a launched agent. A per-agent grant would have meant minting one per invocation, and
  nothing in `SPEC.md` requires the actor to be a single process.
- The budget unit is agent invocations per exercise rather than a cumulative ledger. A
  cumulative budget needs a store and a reconciliation path; per-exercise needs neither and
  still refuses the failure mode that matters, which is one run sprawling.
- `scripts/sov_land.py` refuses to stage anything it was not given by name. Sessions in this
  repository share one working directory, and a blanket stage would land another
  participant's uncommitted work under this one's evidence.
- The gate refuses to merge a branch that is behind its target, rather than rebasing on its
  own. `AGENTS.md` requires the update before merge; performing it silently inside a gate
  would hide a conflict resolution inside an authority check.

## What would defeat this ruling

- A landed commit that touches `decisions/` or `STATUS.yaml`. That would mean the scope
  exclusions do not hold and the loop can record its own standing.
- A landing that carries an observation from a participant that also built the change. That
  would mean `OBSERVER_NOT_INDEPENDENT` is decorative.
- A run that lands while `verify` or `lint` is red. `main` is the releasable design System of
  Record and the gate exists to keep it passing.
- Grant renewal becoming automatic. If the ninety-day expiry is extended without anyone
  deciding again, the grant has become the habit this record says it must not be.

## Residual

Both paragraphs below were true when this record was written and are superseded by
`decisions/0065-standing-grant-ratified.md`: Bdo ratified the grant on 2026-08-25, and the
branch was brought level with `main` the same day. They are kept as written rather than
edited, because a decision record states what was true when it was made.

The grant ships at `PROPOSED` standing and the evaluator refuses a grant that is not
`RATIFIED`, which means the loop is presently inert: it will run and the gate will refuse
every landing. Flipping `status` to `RATIFIED` in `contracts/standing-grants.json` is Bdo's
act and nothing in the loop may perform it for him. That is the acceptance gate of
`decisions/0023` doing its job, not an oversight.

One operational fact belongs next to that decision.
`feat/federation-harness-and-hardening` is currently ninety-five commits ahead of `main` and
thirty behind, so the first exercise of this grant would move far more than one concern and
would be refused for being behind before it got that far. Bringing the branch level with
`main` is a separate concern and is not attempted here.
