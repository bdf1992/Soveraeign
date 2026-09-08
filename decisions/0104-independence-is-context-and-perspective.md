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

## What changed

Built on `claude/agent-independence-definition-z4crlv` at `BUILT` standing. The
decision stays `PROPOSED`: a participant may construct what it cannot ratify,
and nothing here reached `main`.

- `services/observation/contracts/relation-inference.schema.json`: the `edge`
  enum, `edges_examined` `minItems` from 5 to 7, and `subject_id`.
- `.../src/soveraeign_observation_service/record.py`: reads two more journal
  events, `LAUNCH` and `STANDING`, and widens from one run's slice to the
  subject's lifecycle slice. `profile_of` reads the frame an actor loaded.
- `.../relation.py`: `EDGES`, `_walk_grants` deleted, and three walks added —
  perspective, lifecycle, and context.
- `.../observe.py` and `service.py`: `observe_run` takes `submitted_by` and
  refuses `OBSERVER_NOT_INDEPENDENT` when an executor relays another actor's
  observation. This is where `ONLY_EXECUTOR_REPORT`'s widening landed. The edge
  itself is unchanged: an inference runs before an observation exists, so the
  relay cannot be seen from there.
- `tests/test_thin_slice.py`: seven cases added, one per new edge plus the
  lifecycle-shopping case, the relay refusal, and the case proving a grant
  descending from the run is no longer an edge. 55 tests pass.
- `contracts/fixtures/relation-inference.fixtures.json`: 12 entries carried onto
  the new vocabulary, 6 added — three positive edges and three defeating cases
  (a narrowed five-edge examination, a retired edge reported as a finding, and
  an undeclared context read as independence).
- `CHARTER.md`, `KNOWN-GAPS.md`, `STATUS.yaml`.
- `AGENTS.md` Closure ownership and `contracts/closure-ownership.json`
  `helper_policy.witness_rule`. Both said a helper that *read* the change is
  inside the build. That reason is wrong — a witness reads the change too — and
  read literally it disqualified every witness there is. The helper is inside
  the build because it shaped the thing or watched it being shaped.

### A gap the new fixtures found

`OBS-RELATION-SEM-UNDECLARED-CONTEXT-READS-INDEPENDENT` was written to be
invalid and validated clean. The schema's `INDEPENDENT` branch constrained
`edges_found` and `record_completeness` and said nothing about
`unanswerable_edges`, so a record could claim independence while naming edges
nobody could read — the silence-as-pass `decisions/0041` built its third outcome
to refuse. The implementation never emitted it; the contract permitted it, and a
different participant could.

Repaired by adding `unanswerable_edges: {maxItems: 0}` to that branch and to no
other. A `DIRECT` verdict may name an unanswered edge, because a found edge
already answers the question the inference asks. Independence may not.

### Standing moved

`observation_service_status` demoted from
`BUILT_THIN_SLICE_WITNESSED_REMAINDER_DECLARED` to
`BUILT_THIN_SLICE_REMAINDER_DECLARED_NOT_WITNESSED`. The three witness passes at
commit `3087714` observed the five-edge walk this decision replaced. They were
not wrong; they no longer cover what is there.

## The first witness pass dissented

`witness/independence-context-perspective.md`, 2026-09-07, over commit `7be1323`. It supported
no standing and reached `INDEPENDENT` on five records the manifest forbids. Every one was the
same shape: a datum the record did not carry, answered "no" instead of "cannot say".

The deepest one defeats Ruling 3 directly. `_walk_perspective` treated a missing operating
profile as unanswerable; `_walk_lifecycle` treated the same absence as a clean "different", so
`PRIOR_STANDING_ACTOR` degraded to id equality and a rename defeated it — a rename being the
exact thing the profile exists to defeat. Two walks in one module read one absence two ways.

Repaired. The perspective reading is three-valued (`SAME`, `DIFFERENT`, `UNKNOWN`) and lives
in `version.py`, because the pass also found the executor-relay refusal comparing ids while the walk compared
profiles: `infer_relation` called two actors the same and `observe_run` called them different,
on one record. The gate moved to `admission.py` and now reads the whole verdict — found edges,
unanswered edges, completeness, and whether the examination covered the closed set — after the
pass admitted an inference saying `INDEPENDENT` over an `INCOMPLETE` record, whose observation
then asserted the record was `COMPLETE` in the one field `SPEC.md` owns.

Two things the pass found are worth stating as ruling rather than repair.

**A source the record cannot place is not a source it can clear.** An id this service does not
recognise is as likely to be an alias of the executor as a contract address, so a launch now
declares the *kind* of the author of an observer's criteria, not only its id.

**A subject named by the executor is not a subject the walk can trust.** `subject_id` comes
from the executor's own `ATTEMPTED` payload, and a decoy carrying real arrows walked the wrong
lifecycle and passed. A record that also shows the candidate moving another subject is now
unanswerable rather than clear.

The pass could not file its own record: `witness/*.md` is in the documentation corpus, so
writing one turns `verify.py` red and repairing that needs a file a witness may not edit. Its
words are filed by the builder, quoted, and the coupling is a row in `KNOWN-GAPS.md`. Custody
of a witness record filed by the party it grades is weaker than one the witness wrote, and
saying so is the honest form of it.

## The second pass dissented too, and falsified this record

`reports/2026-09-08-independence-repairs.md`, over commit `f28e43b`. It supported no standing
either, and its first finding was against the paragraph above: this record claimed one module
with one reading while `HOLDS_RUN_LEASE` and `PRODUCED_THE_OUTPUT` still compared raw ids. A
candidate that was a version of the lease holder, or of the actor that produced the very output
it proposed to observe, read `INDEPENDENT` over a `COMPLETE` record. Neither actor need be the
run's attempter, which is why `SAME_ACTOR_VERSION` did not cover them and why those two edges
exist at all. **A decision record stating a repair as complete when it is not is the same
defect as a check that grades a declaration, in the document that governs the check.**

Three more findings changed what this record rules rather than only what the code does.

**A closed vocabulary on both context fields, not one.** `PREDICATE_SOURCE_KINDS` was closed in
the repair above and refused an unrecognised kind. `context_passed` was not, so a launcher that
truthfully declared `FULL_BUILD_CONTEXT`, or wrote `transcript` in lower case, was read as
subject-side. The launcher said something real and the service could not read the word. Both
sets are closed now, and an unrecognised kind on either is a question.

**A gate reads the record, not a report about it.** `admission.py` graded a verdict and never
the record that verdict described, so the run's own executor observed its own run through the
exported `observe_run` on a hand-written dict. It now takes the record, re-derives the
`inference_id` from the material the walk hashes, and refuses an inference citing entries the
record does not carry.

**Corroborate the subject; do not charge the candidate.** The decoy repair above asked whether
the candidate had moved any other subject, and the pass showed that made admission *decrease*
as the record grew: one unrelated arrow by an unrelated party refused every candidate, and the
only route to admission was handing the walk a narrowed record — the thing
`record_completeness` exists to punish. The question is now asked of the subject instead. An
actor of this run must appear on the subject the run names. The decoy still refuses and an
observer with prior work elsewhere is admitted, and the two cases are pinned together, because
either alone can be satisfied by a rule that is wrong.

The pass's envelope was `UNATTESTABLE` for a contract-typed `Finding`: no `RecordProjection`
has been exercised on a real run, and minting an id to satisfy the schema would be inventing
evidence. It said plainly that the standing answer was no either way. It also declined to be
the next pass, on the ground that from that point its own probes are inside the repair loop.
That is the correct reading of this decision applied to the pass itself.

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

- Question 2 below is unanswered, and the retirement of grant-descent is built
  on the default this record takes rather than on a ruling. The first witness
  pass sharpened it: the control the retirement leans on was defeated by a
  second session of the executor, and though that is repaired, the pass is
  right that a builder's power over the observer's authority is a question the
  repair does not answer.
- The pass's own independence is imperfect on this subject and the record says
  so. The deliverable is partly a rationale, so the artifact under review is
  the builder's reasoning: the context axis cannot be clean on a
  rationale-shaped subject, and the perspective axis carried the pass. That is
  a limit of the definition, not of the launch.
- No second pass. The repairs are `BUILT` and self-tested; nothing here is
  witnessed, and the standing stays demoted.
- Both context edges read a launcher's declaration where they could not measure.
  The cross-check named in Ruling 8 — an observation citing more than its launch
  declared — is described and not computed by anything.
- `contracts/transition.schema.json` still carries `observer_relation` with
  `INDEPENDENT | SELF | DELEGATED`, declared by the observer and used nowhere
  else in the repository. `DELEGATED` is exactly the builder-launched witness
  this record admits, so the enum is now readable for the first time and is also
  the self-declaration `decisions/0041` Ruling 2 refuses. Left alone: `SPEC.md`
  owns it and it is outside this concern.
- `contracts/standing-grants.json` requires `requires_independent_observation`
  for `repository.land` without saying which definition it means. It resolves
  through `AGENTS.md` today and would resolve through this record on acceptance;
  the grant text is not edited here because the grant excludes its own registry.
- Lifecycle scope raises a cost this record does not price: an inference at
  `WITNESSED -> RATIFIED` reads every actor on every prior arrow, and long-lived
  subjects accumulate them. Whether that walk stays bounded is unmeasured, and
  it is a row in `KNOWN-GAPS.md`.
- The recursion `services/observation/KNOWN-GAPS.md` records is untouched:
  whatever observes this service still cannot be this service.
