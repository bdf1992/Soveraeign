# 0104 · Independence is context and perspective, not lineage

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

### 1. Independence has two axes and needs both

**Context** is what an observer was given. **Perspective** is what an observer
is. An observer is independent of a subject when it holds nothing the subject's
construction produced, and is not a version of an actor that produced it.

Neither axis substitutes for the other. Isolating context from an actor that
already holds the builder's frame produces a second run of the same reading,
and repetition has never been authority here. Changing the actor while handing
it the builder's reasoning produces a different reader agreeing with a
conclusion it was given.

### 2. Context: ends, not means

An observer may hold what the run was asked to do and what the run produced. It
may not hold how the run decided, what it concluded, or what it says about
itself.

The observer inherits the objective and the artifact, never the route between
them. A witness handed the route can only check that route against itself, and
it will agree, because agreement is what shared context manufactures.

Stated as the two readings a participant is handed: context about the work, not
about the worker. Context on what the controller chose, not on how the
orchestration reached it.

### 3. Perspective is carried by the actor and survives a fresh context

Bdo's ruling, 2026-09-07: the same actor is the same perspective. A session
holding none of the prior session's transcript is not a stranger to it. It is a
version of the prior actor — same profile, same role definition, same
dispositions, reading the artifact the way the builder read it.

Isolation removes what an observer *inherited*. It does not remove what an
observer *is*.

This is why the harness carries distinct role definitions rather than one agent
with a job flag. `sov-worker` and `sov-witness` are not two labels on one
participant; they are two frames. The rule ratifies what the harness already
does and says why it was never cosmetic.

### 4. Launch lineage is not a relation

Who launched the observer is not what makes it dependent. A witness launched by
the builder, handed the subject and not the builder's reasoning, and loading a
frame the builder did not load, reaches its answer along a path the builder
never walked.

The evidence is ordinary. Ask a participant the same question twice, under
different context and a different frame, and the answers differ when the second
holds neither the first's context nor its frame. Difference under a different
frame is the entire product of an observation. Identity of origin does not
suppress it; shared context and shared perspective do.

### 5. The subject's lifecycle is the scope, not the run

Standing moves `OPEN -> BUILT -> WITNESSED -> RATIFIED`, and a subject accretes
actors along the way. A relation inferred against one run's record cannot see an
actor that touched the same subject at an earlier arrow.

That gap is exploitable without anyone intending it: build the subject in run 1,
then observe run 2, which touches the same subject. Per-run inference finds no
edge to run 2 and admits the builder as its own witness one arrow later.

So the inference is scoped to the subject's standing lifecycle. Every arrow
needs an actor independent of every actor on every prior arrow, by both axes.

Read this way, three separate rules collapse into one. "A build report cannot
witness itself", "no seat settles its own output", and "only Bdo ratifies
judgement" are the same test applied at successive arrows, with a different tier
holding each. Ratification sits with the root seat because that seat is the only
actor guaranteed to be a version of nothing below it.

### 6. The edge set

Seven direct edges. One found is `OBSERVER_NOT_INDEPENDENT`.

| Edge | Holds when | Axis | Standing |
| --- | --- | --- | --- |
| `SAME_ACTOR_VERSION` | The candidate is an actor the record shows executing or reporting the run, **or** loads the same operating profile that actor loaded | perspective | widened from `SAME_ACTOR` |
| `PRIOR_STANDING_ACTOR` | The candidate, or a version of it, appears at any earlier standing arrow on the same subject | perspective | new |
| `HOLDS_RUN_LEASE` | The candidate holds the lease an attempt ran under | context | kept |
| `PRODUCED_THE_OUTPUT` | The candidate produced an output it proposes to observe | context | kept |
| `ONLY_EXECUTOR_REPORT` | The executor's report is the only thing available to read, including an observation the executor relayed rather than one the observer wrote | context | kept, widened |
| `CONSTRUCTION_CONTEXT_INHERITED` | The record shows the candidate was passed the run's reasoning, plan, transcript, or conclusion | context | new |
| `PREDICATES_SUPPLIED_BY_EXECUTOR` | The criteria the candidate graded against came from the executor rather than from a contract, a fixture, or the observer's own declaration | context | new |
| `GRANT_DESCENDS_FROM_RUN` | — | — | retired |

`GRANT_DESCENDS_FROM_RUN` is retired. Authority descent is an authority fact. It
was standing in for a real hazard — a builder that can bury a finding it does
not like — and that hazard is about the finding's path to the record, not the
observer's parentage. `ONLY_EXECUTOR_REPORT` names it directly: a finding that
reaches the record only through the builder is the builder's report wearing an
observer's name.

`PREDICATES_SUPPLIED_BY_EXECUTOR` is the quality predicate `decisions/0100`
asked for when it named the cosmetic rubber-stamp witness as its own defeater. A
witness graded against the builder's chosen criteria checks the builder's frame,
whoever launched it and whatever it read.

### 7. This is checkable, and refuses when it is not

`decisions/0041` names as its own defeater a definition the service cannot
check. This one is checkable on the terms the grant chain already was.

- **Context** — the launch is a recorded act whose payload declares what was
  passed.
- **Perspective** — the record carries each actor's operating profile address
  and digest, at attempt and at observation.
- **Lifecycle** — the standing arrows on a subject are already record entries.

A record that cannot answer one of them is too thin, which is `UNDETERMINED`,
which refuses. Under-declaring buys nothing, because silence has never been a
pass here.

### 8. Independence is still inferred, never declared

Ruling 2 of `decisions/0041` is narrowed, not reversed. The observer still does
not vouch for itself. What changed is which party the record reads: the launcher
declares what it passed, and the launcher is not the observer.

That declaration is the builder's word, which is a real weakness and is
cross-checked rather than trusted. An observation cites the addresses and
digests it read. An observation whose citations exceed the context its launch
declared is evidence the declaration was false, readable by anyone holding both
records.

## What this changes

- `services/observation/contracts/relation-inference.schema.json`: the `edge`
  enum, `edges_examined` `minItems` from 5 to 7, and the subject scope alongside
  `run_id`.
- `services/observation/src/soveraeign_observation_service/relation.py`:
  `EDGES`, `_walk_grants` removed, walks added over the launch entry, the actor
  profile, and the subject's prior standing arrows.
- `services/observation/src/soveraeign_observation_service/record.py`: the
  record widens from one run's slice to the subject's lifecycle slice.
- `services/observation/CHARTER.md` and `KNOWN-GAPS.md`: the independence
  section and the recursion row.
- A defeating fixture per new edge, one proving a launch with no declared
  context reads `UNDETERMINED`, and one proving a builder admitted at
  `BUILT -> WITNESSED` on a later run is refused by `PRIOR_STANDING_ACTOR`.
- `AGENTS.md` Closure ownership and `contracts/closure-ownership.json`
  `helper_policy.witness_rule`. Both currently say a helper that *read* the
  change is inside the build. Under this definition that reason is wrong — a
  witness reads the change too. The helper is inside the build because it holds
  the construction context: it shaped the thing, or watched it being shaped. The
  current wording, read literally, disqualifies every witness there is.

None of it is done here. The edge set is the entire enforcement surface of a
built service, and one question in Bdo's queue is still open, so this record
states the delta precisely enough to be one step from landing and stops there.

## Defaults taken

- `GRANT_DESCENDS_FROM_RUN` retired rather than narrowed. Narrowing would have
  kept a lineage test alive beside a context test, and a participant would have
  had to satisfy both.
- Four edges rather than two. Inherited reasoning, supplied criteria, shared
  frame, and prior standing fail independently: a witness can hold neither the
  plan nor the transcript, be graded against a contract's own predicates, and
  still be a version of the actor that built the thing.
- Perspective read from the operating profile the actor loaded, not from actor
  identity alone. Identity alone is defeated by a rename; the profile is what
  carries the frame.

## Corrected in draft

An earlier draft of this record kept `SAME_ACTOR` as bookkeeping — the edge held
only because the record could not tell two sessions of one actor id apart, and
would dissolve once sessions carried distinct ids. Bdo rejected that reading on
2026-09-07. Distinct session ids dissolve nothing: the later session is a
version of the prior actor and carries its perspective. The edge is a first-class
axis, and it widened rather than narrowed.

## What would defeat this ruling

- A builder that declares a thin context and passes the rest out of band — a
  shared working tree, a file the record does not hold, a prompt written
  elsewhere. The check would then grade a declaration where it could have
  measured, which is the defect `.claude/agents/sov-witness.md` step 6a names.
- Measured agreement rates that do not move. If context-isolated observers and
  context-holding ones defeat claims at the same rate, context is not doing the
  work and lineage was the cheaper proxy.
- Two launches of one profile that reliably defeat each other's claims. That
  would show perspective is not carried by the profile, and
  `SAME_ACTOR_VERSION` is tighter than the evidence supports.
- A pattern of context-isolated witnesses reporting deliberate choices as
  defects often enough that builders stop launching them. The cost is real and
  accepted here — a witness that does not know why a choice was made asks the
  artifact, and the builder answers the finding — but a measured collapse in the
  step's use would mean the trade was wrong.

## Judgement queue for Bdo

1. ~~Does `SAME_ACTOR` survive?~~ Settled 2026-09-07: it survives and widens.
   Same actor is same perspective; a fresh session is a version of the prior
   actor, not a stranger to it.
2. Is retiring `GRANT_DESCENDS_FROM_RUN` right, or does a builder's power over
   the observer's authority stay an independence question in its own right,
   separately from its power over the finding?

## Residuals

- Not implemented. Schema, walks, record scope, fixtures, charter and the two
  closure-ownership wordings are named above and unchanged in the tree.
- `contracts/standing-grants.json` requires `requires_independent_observation`
  for `repository.land` without saying which definition it means. It resolves
  through `AGENTS.md` today and would resolve through this record on acceptance;
  the grant text is not edited here because the grant excludes its own registry.
- Lifecycle scope raises a cost this record does not price: an inference at
  `WITNESSED -> RATIFIED` reads every actor on every prior arrow, and long-lived
  subjects accumulate them. Whether that walk stays bounded is unmeasured.
- The recursion `services/observation/KNOWN-GAPS.md` records is untouched:
  whatever observes this service still cannot be this service.
