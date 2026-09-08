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
- `services/observation/tests/test_thin_slice.py`: seven cases added, one per new edge plus the
  lifecycle-shopping case, the relay refusal, and the case proving a grant
  descending from the run is no longer an edge. 55 tests pass.
- `services/observation/contracts/fixtures/relation-inference.fixtures.json`: 12 carried onto
  the new vocabulary, 6 added — three positive edges and three defeating cases
  (a narrowed five-edge examination, a retired edge reported as a finding, and
  an undeclared context read as independence).
- `services/observation/CHARTER.md`, `services/observation/KNOWN-GAPS.md`,
  `STATUS.yaml`.
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
exported `observe_run` on a hand-written dict. It now takes the record. *(Pass 3 defeated the
first repair: re-deriving `inference_id` proved nothing, because that id hashes three fields
the caller supplies and is therefore identical for every verdict the walk could reach about one
subject. The gate now re-runs the walk and refuses unless the handed verdict is the one it
reaches, field by field. A verdict is a convenience for the caller and never a credential.)*

**Both guards, and the cost taken deliberately.** The decoy repair asked whether the candidate
had moved any other subject, and pass 2 showed that made admission *decrease* as the record
grew. Corroborating the subject instead — an actor of this run must appear on the subject the
run names — admitted the experienced observer, and pass 3 then defeated it: the executor writes
the name, so it corroborates any decoy it has itself moved, and the subject's own builder was
admitted as its independent observer with the candidate's arrow on the real subject sitting
unread in the same record.

So both, and pass 2's objection is accepted as a cost rather than answered. An observer the
record shows moving any other subject is refused. That makes an experienced observer
unattestable, which is real, disclosed in `KNOWN-GAPS.md`, and better than admitting a
subject's builder as its witness. A subject nobody can verify is not one the walk may guess at.

The pass's envelope was `UNATTESTABLE` for a contract-typed `Finding`: no `RecordProjection`
has been exercised on a real run, and minting an id to satisfy the schema would be inventing
evidence. It said plainly that the standing answer was no either way. It also declined to be
the next pass, on the ground that from that point its own probes are inside the repair loop.
That is the correct reading of this decision applied to the pass itself.

## The third pass found the axis itself is declarable

`reports/2026-09-08-independence-repairs.md`, over commit `3c24420`. It dissented too, defeated
the two repairs corrected above, and found the section they sit in stating them as complete two
paragraphs after the sentence naming that exact defect. That is this record repeating the thing
it names, twice now, and the second time it was pass 3 rather than the builder who noticed.

It also found this record citing a report that had never existed. The script that should have
written `reports/2026-09-08-independence-repairs.md` aborted, the retry re-ran only the other
half, and three artifacts — this one among them — cited it for a day. A governing decision
record citing a file in no commit is the same defect as a check that grades a declaration, made
by the same participant one layer up, and nothing in the repository resolves a path named in
prose. That is now a `KNOWN-GAPS` row.

**The finding that is not repaired.** Ruling 3 makes perspective the axis a declaration cannot
remove, read from the operating profile because a rename defeats an id and does not defeat a
frame. Its stated safeguard is that the launcher is not the observer.

`decisions/0100` has a builder launch its own witness. So the launcher *is* the executor, and
every field this walk reads to establish either axis — `context_passed`,
`predicates_source_kind`, `predicates_source_actor`, `subject_id`, `lease`, and the profile
digest — is written by the party being graded. `RunRecord.profile_of` resolves that digest
against nothing. A rename does not defeat the frame; the executor typing a different digest
does.

Ruling 3's safeguard names the wrong adversary. It stops the observer vouching for itself and
leaves the executor vouching for the observer. That is why three repairs failed in the same
shape: each moved where a declaration is read, not that one is read.

This is not repaired, because it is not repairable at that boundary. What changed instead is
what the repository claims: `CHARTER.md` now states the property the walk has — it detects
carelessly recorded dependence and does not detect declared independence — and `KNOWN-GAPS.md`
carries the perspective axis as declared, beside the context axis that was already disclosed.
Whether Ruling 3 and `decisions/0100` are a conflict to settle or a gap to carry is the owner's
and is judgement item 4.

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
3. May showing the walk more record ever reduce admission? Both answers change
   what `record_completeness` means, which is `SPEC.md`-adjacent rather than an
   engineering choice inside this concern. The walk currently refuses an
   observer the record shows working elsewhere, which is that shape.
4. Ruling 3 makes perspective the non-declarable axis; `decisions/0100` makes
   the executor the launcher that declares it. Conflict to settle, or a gap to
   carry disclosed as the context axis already is?
5. Does a witness record admit a builder's section at all, or must the
   builder's disposition live in a report that cites it? Two repairs put the
   prose below the certifying line and then above it before it left the file.
6. A governing decision record cited a report that existed in no commit, and
   every gate stayed green. Is a check that resolves cited repository paths in
   covered prose worth its cost, and is repairing a Record defect in a decision
   record the builder's to do?

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
