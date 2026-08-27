# 0070 · The AI-native standard gets an executable grader

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

## Context

`AI-NATIVE.md` has owned the definition of an AI-native surface since day one. It states
four scored axes, one human judgement, nine qualifications for the Soveraeign bar, and a
derived verdict. It states all of it in prose. Nothing in this repository read that
document, so every claim that a surface here is or is not AI-native has been an opinion
typed by whoever was writing at the time, and no such claim could be defeated by evidence.

That is the same failure the founding docket named elsewhere: a rule with no oracle is a
rule that reports whatever its reader wants. `conformance/founding-scenarios/` already
holds ten scenarios that map almost one to one onto the nine qualifications, and all ten
are `SEED` narratives that nothing executes.

## Decision

Three artifacts, at proposal standing:

- `contracts/ai-native-qualifications.json` compiles `AI-NATIVE.md` into the four axes,
  the nine qualifications with the founding scenario each rests on, the derivation rules,
  and eight refusals.
- `contracts/ai-native-assessment.schema.json` shapes one reading of one surface
  performing one named operation.
- `scripts/sov_ainative.py` with `scripts/sovainative/` derives the verdict, grades the
  declared corpus, and prints what each qualification still rests on.

`AI-NATIVE.md` remains the owning document. The table compiles it and does not compete
with it; a disagreement between them is a judgement item, not a licence to edit either.

## The four rulings this record asks for

**1. The verdict is derived and the record cannot state one.** The schema declares no
`verdict` property and refuses additional ones, so a record that states its own result
fails the shape rather than being argued with. This is `AI-NATIVE.md`'s own sentence -
"the verdict is derived from the recorded scores; it is never selected directly" - made
mechanical.

**2. The substantive-operation judgement is resolved against the principal registry.**
`AI-NATIVE.md` calls `earn_it` a human judgement with an attributable reviewer. The grader
resolves the named reviewer against `contracts/principals.json` and refuses a judgement
made by anything that is not a registered `HUMAN` principal.

The consequence is deliberate and is the point of the whole record: **no surface can ever
reach a verdict without Bdo.** A model can score every axis, gather every piece of
evidence, and drive every qualification to `PASS`, and the assessment still reads `OPEN`
until a human judges whether removing the AI path would remove a material capability. That
is the one input a swarm cannot manufacture for itself.

**3. A seed scenario evidences nothing.** A qualification may be claimed `PASS` only on
evidence that exists. A founding scenario at `SEED` standing is a narrative nothing
executes, so citing one is refused by `SCENARIO_NOT_EXECUTABLE`. Turning a seed into an
executable case is what moves its qualification off `UNPROVEN`, and
`python scripts/sov_ainative.py scenarios` reports that zero of ten can evidence anything
today.

**4. Reachability is the gate, so nothing above it may pass while it fails.** A record
scoring reachability `NONE` while claiming any of the nine qualifications `PASS` is refused
by `CONTRADICTORY_SCORE`. `AI-NATIVE.md` says an unreachable surface cannot be AI-native
regardless of every other score; the nine are layered above that minimum. This is a
reading, not a quotation, and it is the ruling most likely to be wrong.

## Residual: the fourth derived-verdict branch has no live case

`AI-NATIVE.md` lists four outcomes for a complete assessment. The fourth reads: "reachable
but substantive but below the supporting-axis threshold → `TRUTH_CAPABLE` when a
structural axis is present, otherwise `DECORATION`."

Under the natural reading - "present" means scored above `NONE` - that branch cannot fire.
Being below the supporting-axis threshold *is* having no structural axis above `NONE`, so
the condition and its exception are the same condition. The grader implements the list
literally and the branch is dead code, marked as such.

Either the document means something else by "present", or the clause is redundant and
should be collapsed. This needs a ruling from the seat that owns `AI-NATIVE.md`. It is
recorded here rather than repaired, because editing the standard to fit the first grader
written against it is exactly backwards.

## Defaults taken

- **The principal registry holds durable principals only.**
  `contracts/principals.json` now exists at the path
  `scripts/sovsession/principals.py` has always looked for, carrying Bdo, the two Claude
  models that have operated this node, and the two local models with declared bindings.
  Session-scoped instance principals are not committed: they change several times an hour
  in a tree several sessions share, and the live session registry already tracks them.
  Reversible - the schema admits `INSTANCE` principals and the registry can carry them the
  day something needs them committed.
- **Assessments live under `conformance/assessments/`.** They are witness inputs about a
  surface, which is what `conformance/` owns. No new top-level directory was created.
- **`FOUND-009` evidences cold-start competence and `FOUND-010` local sovereignty.** Those
  two mappings are the least obvious in the table and were chosen on the scenarios' own
  titles.

## Effect class and rollback

`RECORD_LOCAL`. Three new contract files, one new script package, one test module, one
assessment record and one registry instance. Nothing changes standing, no existing check
was weakened, and deleting the files restores the previous state exactly.

## What would defeat this

- A reviewer resolving as a registered human principal by a route a model can take. The
  registry is a projection and being registered grants nothing, so if a model can get a
  `HUMAN` entry written for itself, ruling 2 is decorative.
- A qualification that can reach `PASS` on evidence nobody can re-observe. The evidence
  shape requires an address and a reading; if either can be left vague, the grader grades
  prose again.
- A surface reaching `SOVERAEIGN_QUALIFIED` that an unpersuaded reader would not call
  AI-native. That would mean the table compiled the document wrongly, and the table is
  what should change.

## The first reading

`conformance/assessments/self-hosted-concern-execution.json` assesses the operation a
swarm would perform: take one bounded concern, work it, land the result. It reads `OPEN`,
held by the substantive-operation judgement. Two qualifications are recorded `FAIL` with
evidence - independent observation, because the grant decides independence from a boolean
the request writes about itself; and model substitutability, because the model performing
the work has no binding, no invocation receipt and no visible cost. The rest are
`UNPROVEN`.

It is a self-assessment by a participant that also builds on that surface. It establishes
`BUILT` evidence and witnesses nothing.
