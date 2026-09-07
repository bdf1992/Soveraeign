# 0104 · Independence is a property of context, not of lineage

Status: `OWNER-DIRECTED · PROPOSED`

Directed by Bdo (seat:root) in session on 2026-09-07, opening the item
`decisions/0041-the-observation-service.md` left in his judgement queue: the
edge set that defines "direct". This narrows `decisions/0041` Ruling 2 and
supplies the quality predicate `decisions/0100-launch-your-own-witness.md`
named and did not have.

## The conflict this settles

Two accepted policies disagree about the same act.

`decisions/0100` requires a builder that can launch a witness to launch one and
receive its observation as its own step. `decisions/0041` Ruling 2 makes an
observer `DIRECT` when its grant descends from the run's grant chain — which is
what a builder-launched witness has, when the launch is recorded at all.

The inference was driven against both readings of that launch on 2026-09-07,
at `services/observation/src/soveraeign_observation_service/relation.py`:

| Recorded launch | `infer_relation` outcome |
| --- | --- |
| Witness holds a grant whose parent is the run's grant | `DIRECT`, edge `GRANT_DESCENDS_FROM_RUN` |
| Witness holds no recorded grant | `UNDETERMINED`, unanswerable `GRANT_DESCENDS_FROM_RUN` |

Neither reads `INDEPENDENT`. The step the loop requires cannot pass the check
the loop declares. Recording the launch more completely makes it worse, not
better, which is the sign that the edge is measuring the wrong thing.

## Decision

### 1. An observer is independent when it holds nothing the run's construction produced

It may hold what the run was asked to do and what the run produced. It may not
hold how the run decided, what the run concluded, or what the run says about
itself.

Ends, not means. The observer inherits the objective and the artifact; it does
not inherit the route between them. A witness handed the route can only check
that route against itself, and it will agree, because agreement is what shared
context produces.

Stated as the two readings a participant is given: context about the work, not
about the worker. Context on what the controller chose, not on how the
orchestration reached it.

### 2. Launch lineage is not a relation

Who launched the observer is not what makes it dependent. A subagent launched
by the builder, handed the subject and not the builder's reasoning, reaches its
answer along a path the builder never walked.

The evidence is ordinary and available to anyone: ask a participant the same
question twice, under different context and a different frame, and the answers
differ when the second does not hold the first. Difference under a different
frame is the whole product of an observation. Identity of origin is not what
suppresses it — shared context is.

### 3. The edge set

Six direct edges. One found is `OBSERVER_NOT_INDEPENDENT`.

| Edge | Holds when | Standing |
| --- | --- | --- |
| `SAME_ACTOR` | The candidate is an actor the record shows executing or reporting the run | kept |
| `HOLDS_RUN_LEASE` | The candidate holds the lease an attempt ran under | kept |
| `PRODUCED_THE_OUTPUT` | The candidate produced an output it proposes to observe | kept |
| `ONLY_EXECUTOR_REPORT` | The executor's report is the only thing available to read | kept |
| `CONSTRUCTION_CONTEXT_INHERITED` | The record shows the candidate was passed the run's reasoning, plan, transcript, or conclusion | new |
| `PREDICATES_SUPPLIED_BY_EXECUTOR` | The criteria the candidate graded against came from the executor rather than from a contract, a fixture, or the observer's own declaration | new |
| `GRANT_DESCENDS_FROM_RUN` | — | retired |

`GRANT_DESCENDS_FROM_RUN` is retired as an independence edge. Authority descent
is an authority fact. It was standing in for a real hazard — a builder that can
suppress a finding it does not like — and that hazard is named directly instead,
by `ONLY_EXECUTOR_REPORT` reading an observation the executor relayed rather
than one the observer wrote. A finding that reaches the record only through the
builder is the builder's report wearing an observer's name.

`PREDICATES_SUPPLIED_BY_EXECUTOR` is the quality predicate `decisions/0100`
asked for when it named the cosmetic rubber-stamp witness as its own defeater.
A witness graded against the builder's chosen criteria checks the builder's
frame, whoever launched it and whatever it read.

### 4. This is checkable, and refuses when it is not

`decisions/0041` names as its own defeater a definition the service cannot
check. This one is checkable on exactly the terms the grant chain already
was: the launch is a recorded act, and its payload declares what context was
passed.

A launch that does not declare its context is a record too thin to answer.
That is `UNDETERMINED`, and it refuses — the third outcome doing the job it was
built for. Under-declaring buys nothing, because silence has never been a pass
here.

### 5. Independence is still inferred, never declared

Ruling 2 of `decisions/0041` is narrowed, not reversed. The observer still does
not vouch for itself. What changed is which party the record reads: the
launcher declares what it passed, and the launcher is not the observer.

That declaration is the builder's word, which is a real weakness and is
cross-checkable rather than trusted. An observation cites the addresses and
digests it read. An observation whose citations exceed the context its launch
declared is evidence the declaration was false, and it is readable by anyone
holding both records.

## What this changes

- `services/observation/contracts/relation-inference.schema.json`: the `edge`
  enum, and `edges_examined` `minItems` from 5 to 6.
- `services/observation/src/soveraeign_observation_service/relation.py`:
  `EDGES`, `_walk_grants` removed, two walks added over the launch entry.
- `services/observation/CHARTER.md` and `KNOWN-GAPS.md`: the independence
  section and the recursion row.
- A defeating fixture per new edge, and one proving a launch with no declared
  context reads `UNDETERMINED` rather than `INDEPENDENT`.
- `AGENTS.md` Closure ownership and `contracts/closure-ownership.json`
  `helper_policy.witness_rule`. Both currently say a helper that *read* the
  change is inside the build. Under this definition that reason is wrong: a
  witness reads the change too. The helper is inside the build because it holds
  the construction context — it shaped the thing, or watched it being shaped.
  The current wording invites the reading that anyone who has seen the diff is
  disqualified, which would disqualify every witness there is.

None of it is done here. The edge set is the entire enforcement surface of a
built service and it is the open item in Bdo's queue, so this record states the
delta precisely enough to be one step from landing and stops there.

## Defaults taken

- `SAME_ACTOR` kept, for an attribution reason rather than a context one. A
  fresh session of the same actor, holding none of the prior context, is
  context-independent under Ruling 1 — but the record cannot tell two sessions
  of one actor id apart, so the edge holds until sessions carry distinct actor
  ids, at which point it dissolves on its own.
- `GRANT_DESCENDS_FROM_RUN` retired rather than narrowed. Narrowing it would
  have kept a lineage test alive next to a context test, and a participant
  would have had to satisfy both.
- Two new edges rather than one. Inherited reasoning and supplied criteria fail
  independently: a witness can hold neither the plan nor the transcript and
  still be graded against the builder's chosen predicates.

## What would defeat this ruling

- A builder that declares a thin context and passes the rest out of band — a
  shared working tree, a file the record does not hold, a prompt written
  elsewhere. The check would then grade a declaration where it could have
  measured, which is the defect `.claude/agents/sov-witness.md` step 6a names.
- Measured agreement rates that do not move. If context-isolated witnesses and
  context-holding ones defeat claims at the same rate, context is not doing the
  work and lineage was the cheaper proxy.
- A pattern of context-isolated witnesses reporting deliberate choices as
  defects often enough that builders stop launching them. The cost is real and
  accepted here — a witness that does not know why a choice was made is
  supposed to ask the artifact, and the builder answers the finding — but a
  measured collapse in the step's use would mean the trade was wrong.

## Judgement queue for Bdo

1. Does `SAME_ACTOR` survive? A fresh session of the same actor holding none of
   the prior context is independent under Ruling 1 and direct under the edge
   set. Kept above as a default; the reason is attribution, not taint.
2. Is retiring `GRANT_DESCENDS_FROM_RUN` right, or does a builder's power over
   the observer's authority stay an independence question in its own right,
   separately from its power over the finding?

## Residuals

- Not implemented. Schema, walk, fixtures, charter and the two closure-ownership
  wordings are named above and unchanged in the tree.
- `contracts/standing-grants.json` requires `requires_independent_observation`
  for `repository.land` without saying which definition it means. It resolves
  through `AGENTS.md` today and would resolve through this record on
  acceptance; the grant text is not edited here because the grant excludes its
  own registry.
- The recursion `services/observation/KNOWN-GAPS.md` records is untouched:
  whatever observes this service still cannot be this service.
