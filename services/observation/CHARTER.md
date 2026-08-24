# Observation Service Charter

Standing: `PROPOSED`. Chartered and contracted; nothing here is implemented.

## Role in Soveraeign

The Observation Service owns independent observation: evidence about a run gathered by
something that did not perform it.

That distinction is the whole service. `SPEC.md` already defines an `Observation` as a record
carrying `observer_id`, `observer_relation`, the addresses and digests the observer looked at
itself, and the predicates that held — and `observer_relation` must state how the observer
avoided relying solely on the executor's report. `settle_run` refuses with `OBSERVATION_MISSING`
when that record is absent. Today nothing owns the transition that produces it.

The gap is visible everywhere. Check 3 on the `AI-NATIVE.md` bar — independent observation —
reads `UNATTESTABLE` on every service assessment in the repository.
`scripts/witness_observe.py` is a loose script rather than a governed surface. `observe_run` is
one of fourteen kernel transitions and the only one with no service behind it.

## What this service is not

**It is not the log.** The append-preserving journal belongs to the Record Service, and an
operator's view over it belongs to the Console Service's `projection-view`. Adding a third
place that records what happened would be the competing authority the contract forbids. If you
want to know what occurred, read the journal. This service answers a narrower and harder
question: did somebody who wasn't the executor check, and did the declared predicates hold.

**It is not a witness in the governance sense.** An observation is evidence. It settles
nothing, ratifies nothing, and does not by itself move an artifact from `BUILT` to
`WITNESSED`. It is the input that makes such a move possible.

**It is not a validator.** `attest-observation` records a validator's outcome —
`REPRODUCED`, `DISSENTED`, or `UNATTESTABLE` — against declared inputs. `DISSENTED` and
`UNATTESTABLE` stay visible; neither changes an authority sign.

## The loop it closes

An operator pilots the node — today through the CLI, and through the MCP tool surface once it
is reseated on the Gateway Service. Acts land in the journal. Then:

1. `request-observation` — the executor, or the door on its behalf, asks for a terminal run to
   be observed. It cannot observe itself, so it asks. Refuses `RUN_NOT_TERMINAL` on a run still
   in flight.
2. `check-independence` — the proposed observer is compared against the run's executor.
   Refuses `OBSERVER_NOT_INDEPENDENT`, which is the refusal the whole service exists to make.
3. `declare-predicates` — what must hold, stated before the looking, and evaluable without
   reading the executor's report.
4. `observe-run` — the observer reads the durable outputs itself, records their addresses and
   digests, and evaluates the predicates.
5. `read-observation` — the result, alongside the predicates it was judged against and the
   independence check that admitted the observer.

`counter-observation` exists because an observation can later be shown wrong. It is countered,
never erased.

That sequence is the feedback path. Without it, the only evidence that anything worked is the
report of the thing that did it, which the contract has refused from the beginning.

## Authoritative versus derived

Observations, requests, registrations, predicate declarations, independence checks, and
attestation receipts are this service's authoritative records. Everything it says about the
run it observed is derived from that run's durable outputs, read directly.

It reads the Record Service journal. It never writes it.

## What it does not do

- It does not observe what it executed. An observer that ran the thing is refused by name.
- It does not settle. A satisfactory observation lets the kernel settle; it is not the
  settlement.
- It does not ratify. Judgement is Bdo's.
- It does not accept an executor's report as an observation. That substitution is the failure
  mode the service is built against.
- It does not record an observation with no declared relation. An observer that cannot say how
  it stayed independent has not observed anything.

## Proving operation

Drive a run to a terminal receipt through the Asset Service, then attempt to observe it with
the same actor that executed it, and prove the refusal is `OBSERVER_NOT_INDEPENDENT` with no
observation recorded. Then observe the same run with a registered independent observer,
proving the observation records digests the observer computed rather than any value the
executor reported, and that a predicate failure is recorded rather than dropped.

The refusal is the case that matters. A service that only ever produces observations proves
nothing about whether it can tell an observer from an executor.

## Gaps and standing

`KNOWN-GAPS.md` records every observed difference from this charter. The service is chartered
under `decisions/0041-the-observation-service.md`.

## Open before this can be built

- What makes an observer independent, concretely. Different process, different actor id,
  different grant chain, or something stronger. `SPEC.md` requires the relation to be stated
  and does not say what qualifies.
- Whether `observation-receipt` is this service's own record or a `terminal-receipt` in the
  Record Service journal. Four services now own a private receipt type and the Record Service
  owns `terminal-receipt`; nothing says how they relate.
- Whether the repository's own `verify.py` run is an observation of this kind. The MCP surface
  already appends one; it observes the repository rather than a service run.
