# Observation Service Charter

Standing is read from `STATUS.yaml`. Five of the eight declared operations are built and self-tested under `src/soveraeign_observation_service`: `request-observation`, `declare-predicates`, `infer-relation`, `observe-run`, and `read-observation`. `list-pending-observations`, `counter-observation`, and `attest-observation` are declared only. Three independent witness passes observed the built five through this surface (`witness/observation-service.md`); nothing is ratified.

## Role in Soveraeign

The Observation Service owns independent observation: evidence about a run gathered by
something that did not perform it.

`SPEC.md` already defines an `Observation` as a record carrying an observer, the addresses and
digests that observer looked at itself, the predicates that held, and an `observer_relation`
stating how it avoided relying solely on the executor's report. `settle_run` refuses with
`OBSERVATION_MISSING` when that record is absent. This boundary exists because `observe_run`
needs a service-owned path for independent observation. The charter defines that path;
`relation.py` and `observe.py` walk it, and `tests/test_kernel_parity.py` proves the
observation they emit is the one `scripts/sovkernel/transitions.py` accepts for `settle_run`.

## Independence is inferred, never declared

This is the ruling the service is built around (Bdo, 2026-08-23): an observer is independent
when no direct relation to the execution can be found in the record.

Nobody registers as an observer and nobody asserts their own independence. A declared relation
would be the observer vouching for itself, which is the substitution this contract refuses
everywhere else — it is the same shape as an executor's report standing in for an observation.

`decisions/0104-independence-is-context-and-perspective.md` (Bdo, 2026-09-07) says what
independence *is*, on two axes that do not substitute for one another.

**Context** is what the observer was given. It may hold what the run was asked to do and what
the run produced; it may not hold how the run decided, what it concluded, or what it says about
itself. Ends, not means. A witness handed the route can only check that route against itself,
and it will agree, because agreement is what shared context manufactures. This axis is
removable at launch, and the launcher — never the observer — declares what it passed.

**Perspective** is what the observer is. A session holding none of the prior session's
transcript is not a stranger to it: it is a version of the prior actor, loading the same
profile and reading the artifact the way the builder read it. Isolation removes what an
observer inherited, never what it is. This axis is read from the operating profile rather than
the actor id, because a rename defeats an id and does not defeat a frame.

The walk is scoped to the subject's standing lifecycle, not to one run. Standing moves
`OPEN -> BUILT -> WITNESSED -> RATIFIED` and a subject collects actors along the way, so a
per-run walk would admit a builder as its own witness one arrow later.

`infer-relation` looks for a direct edge on either axis:

- `SAME_ACTOR_VERSION` — the candidate is an actor that executed or reported the run, or loads
  the same operating profile one of them loaded;
- `PRIOR_STANDING_ACTOR` — the candidate, or a version of it, already moved this subject along
  an earlier standing arrow;
- `HOLDS_RUN_LEASE` — the candidate holds the lease, fence, or session the run executed under;
- `PRODUCED_THE_OUTPUT` — the candidate produced the output it proposes to observe;
- `ONLY_EXECUTOR_REPORT` — the only evidence available to the candidate is the executor's
  report, which includes an observation the executor relayed rather than one the observer
  wrote;
- `CONSTRUCTION_CONTEXT_INHERITED` — the launch handed the candidate the run's reasoning, plan,
  transcript, or conclusion;
- `PREDICATES_SUPPLIED_BY_EXECUTOR` — the criteria the candidate grades against were authored
  by an executor rather than by a contract, a fixture, or the observer itself. The launch
  declares the author's *kind* as well as its id, because an id this service does not
  recognise is as likely to be an alias of the executor as a contract address, and reading
  either one as "not the executor" is a denial the bytes cannot support.

Find one and the answer is `OBSERVER_NOT_INDEPENDENT`. Find none and the observer may observe.

The grant-descent edge is retired (`decisions/0104` names it exactly; this charter does not,
because an edge name written here is one the contract must enforce). Who launched an observer
is not what makes it dependent:
a witness launched by the builder, handed the subject and not the builder's reasoning, and
loading a frame the builder did not load, reaches its answer along a path the builder never
walked. The hazard that edge stood for — a builder that can bury a finding it dislikes — is
`ONLY_EXECUTOR_REPORT`, and `observe-run` refuses an observation an executor relays.

Those seven names are the vocabulary `relation-inference.schema.json` enforces, and
`services/observation/tests/test_contract_shapes.py` reads this list at check time to prove the
charter and the contract have not drifted apart about what direct means.

### The third outcome

Absence of a recorded direct edge is not the same as absence of a direct relation. A record too
thin to answer the question would otherwise read as independence, which would make the check
worthless exactly where it matters most — on runs that recorded too little.

So the inference has three outcomes, not two: `DIRECT`, `INDEPENDENT`, and `UNDETERMINED`.
`infer-relation` refuses `RELATION_UNDETERMINED` when the record cannot support the inference,
and `observe-run` refuses on it as well. Silence is not a pass.

This is what keeps the two new axes honest. Each of these leaves an edge unanswerable, so
under-declaring buys a refusal rather than a pass:

- a launch that declares no context, or no kind for the author of its criteria;
- any actor the comparison must place — an executor, a prior arrow's actor, a named author —
  whose operating profile the record does not carry, because a rename is exactly what the
  profile exists to defeat;
- a run that names no subject, or that names one while the record also shows the candidate
  moving another, since the subject is declared by the executor's own entry and a decoy that
  carries real arrows would otherwise walk the wrong lifecycle;
- a lease the record carries in a shape this service cannot read.

The first witness pass over this walk reached `INDEPENDENT` on five records the manifest
forbids, every one of them a place where a missing datum answered "no" instead of "cannot
say". `witness/independence-context-perspective.md` is that pass. The asymmetry it found is
the thing to watch for in any edge added later: one walk refused on a missing profile and
another read the same absence as a clean answer.

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

An admitted operator action lands in the journal. After the run is terminal, the observation loop is:

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

## Unresolved boundary seams

- The exact set of direct edges above is proposed, not settled. It is the whole enforcement
  surface, and a missing edge is a way past the check.
- Whether `observation-receipt` is this service's own record or a `terminal-receipt` in the
  Record Service journal. Four services now own a private receipt type and nothing says how
  they relate.
- What makes a run's record complete enough to infer from. `RELATION_UNDETERMINED` needs a
  definition, not just a name.
- Whether the repository's own `verify.py` run is an observation of this kind. The MCP surface
  already appends one; it observes the repository rather than a service run.
