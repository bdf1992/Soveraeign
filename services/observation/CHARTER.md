# Observation Service Charter

Standing: `PROPOSED`. Chartered and contracted; nothing here is implemented.

## Role in Soveraeign

The Observation Service owns independent observation: evidence about a run gathered by
something that did not perform it.

`SPEC.md` already defines an `Observation` as a record carrying an observer, the addresses and
digests that observer looked at itself, the predicates that held, and an `observer_relation`
stating how it avoided relying solely on the executor's report. `settle_run` refuses with
`OBSERVATION_MISSING` when that record is absent. Before this charter, nothing owned the
transition that produces it — `observe_run` was one of fourteen kernel transitions and the only
one with no service behind it.

The gap shows everywhere else too. Check 3 on the `AI-NATIVE.md` bar — independent observation
— reads `UNATTESTABLE` on every service assessment in the repository.

## Independence is inferred, never declared

This is the ruling the service is built around (Bdo, 2026-08-23): an observer is independent
when no direct relation to the execution can be found in the run's own record.

Nobody registers as an observer and nobody asserts their own independence. A declared relation
would be the observer vouching for itself, which is the substitution this contract refuses
everywhere else — it is the same shape as an executor's report standing in for an observation.
Instead `infer-relation` walks the run's record and looks for a direct edge:

- `SAME_ACTOR` — the candidate observer is the actor that executed the run;
- `HOLDS_RUN_LEASE` — the candidate holds the lease, fence, or session the run executed under;
- `GRANT_DESCENDS_FROM_RUN` — the candidate's grant descends from the run's own grant chain;
- `PRODUCED_THE_OUTPUT` — the candidate produced the output it proposes to observe;
- `ONLY_EXECUTOR_REPORT` — the only evidence available to the candidate is the executor's report.

Find one and the answer is `OBSERVER_NOT_INDEPENDENT`. Find none and the observer may observe.

Those five names are the vocabulary `relation-inference.schema.json` enforces, and
`services/observation/tests/test_contract_shapes.py` reads this list at check time to prove the
charter and the contract have not drifted apart about what direct means.

### The third outcome

Absence of a recorded direct edge is not the same as absence of a direct relation. A record too
thin to answer the question would otherwise read as independence, which would make the check
worthless exactly where it matters most — on runs that recorded too little.

So the inference has three outcomes, not two: `DIRECT`, `INDEPENDENT`, and `UNDETERMINED`.
`infer-relation` refuses `RELATION_UNDETERMINED` when the run's record cannot support the
inference, and `observe-run` refuses on it as well. Silence is not a pass.

## What this service is not

**It is not the log.** The append-preserving journal belongs to the Record Service; an
operator's view over it belongs to the Console Service's `projection-view`. A third place
recording what happened would be the competing authority the contract forbids. The journal
answers *what occurred*. This service answers *whether something that did not perform it
checked, and whether the predicates declared beforehand held*.

**It is not a witness in the governance sense.** An observation is evidence. It settles nothing
and does not by itself move an artifact from `BUILT` to `WITNESSED`. It is the input that makes
such a move possible.

**It is not a validator.** `attest-observation` records a validator's outcome — `REPRODUCED`,
`DISSENTED`, or `UNATTESTABLE` — against declared inputs. `DISSENTED` and `UNATTESTABLE` stay
visible; neither changes an authority sign.

## The loop it closes

An operator pilots the node — today through the CLI, and through the MCP tool surface once it
is reseated on the Gateway Service. Acts land in the journal. Then:

1. `request-observation` — the executor, or the door on its behalf, asks for a terminal run to
   be observed. It cannot observe itself, so it asks. Refuses `RUN_NOT_TERMINAL` on a run still
   in flight.
2. `declare-predicates` — what must hold, stated before the looking, and evaluable without
   reading the executor's report.
3. `infer-relation` — the run's record is walked for a direct edge to the candidate observer.
4. `observe-run` — the observer reads the durable outputs itself, records their addresses and
   digests, and evaluates the predicates.
5. `read-observation` — the result, alongside the predicates it was judged against and the
   inference that admitted the observer.

`counter-observation` exists because an observation can later be shown wrong. It is countered,
never erased.

That sequence is the feedback path. Without it, the only evidence that anything worked is the
report of the thing that did it, which the contract has refused since founding.

## Authoritative versus derived

Observations, requests, predicate declarations, relation inferences, and attestation receipts
are this service's authoritative records. Everything it says about the run it observed is
derived from that run's durable outputs, read directly.

It reads the Record Service journal. It never writes it.

## What it does not do

- It does not observe what it executed.
- It does not accept a declared relation in place of an inferred one.
- It does not read an incomplete record as independence.
- It does not settle. A satisfactory observation lets the kernel settle; it is not the
  settlement.
- It does not ratify. Judgement is Bdo's.
- It does not accept an executor's report as an observation.

## Proving operation

Drive a run to a terminal receipt through the Asset Service, then propose the executing actor
as its observer, and prove `infer-relation` returns `DIRECT` and `observe-run` refuses
`OBSERVER_NOT_INDEPENDENT` with no observation recorded. Then strip the run's record of the
actor attribution and prove the answer is `RELATION_UNDETERMINED` rather than independence.
Only then observe the same run from an actor with no edge to it, proving the observation
records digests the observer computed rather than any value the executor reported, and that a
predicate failure is recorded rather than dropped.

Three cases, and the first two are the service. A service that only ever produces observations
proves nothing about whether it can tell an observer from an executor, and one that cannot say
"I don't know" will call every thin record independent.

## Gaps and standing

`KNOWN-GAPS.md` records every observed difference from this charter. Chartered under
`decisions/0041-the-observation-service.md`.

## Open before this can be built

- The exact set of direct edges above is proposed, not settled. It is the whole enforcement
  surface, and a missing edge is a way past the check.
- Whether `observation-receipt` is this service's own record or a `terminal-receipt` in the
  Record Service journal. Four services now own a private receipt type and nothing says how
  they relate.
- What makes a run's record complete enough to infer from. `RELATION_UNDETERMINED` needs a
  definition, not just a name.
- Whether the repository's own `verify.py` run is an observation of this kind. The MCP surface
  already appends one; it observes the repository rather than a service run.
