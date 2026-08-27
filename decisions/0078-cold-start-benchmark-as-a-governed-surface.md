# 0078 · The cold-start benchmark is a governed surface, not a script

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-26
Relates to: `decisions/0070-ai-native-assessment-grader.md` (the standard this surface is
graded against), `decisions/0075-grant-scope-excludes-what-bounds-it.md` (a finding this
benchmark surfaced), `AI-NATIVE.md` target bar 6.

## The problem this addresses

Every launched agent in this repository is oriented by `CLAUDE.md`, `AGENTS.md` and the
session hooks before it reads a single file. Those pages go stale silently. `LESSONS.md`
L-0001 records the snapshot being stale within a day of being written, and
`scripts/sov_snapshot.py` was built to catch the numbers on that page drifting.

`sov_snapshot.py` checks whether the page matches the repository. It cannot check the other
direction: what a fresh participant actually believes after reading it. Those are different
questions, and the second one is the one that decides whether a launched agent does the
right thing in its first ten minutes.

`conformance/assessments/self-hosted-concern-execution.json` recorded the gap plainly:
`cold_start_competence: UNPROVEN`, with the note "a fresh instance is oriented by CLAUDE.md
and a checked snapshot, and neither time to useful nor intervention count is measured".

## What is proposed

A cold-start benchmark as a first-class surface with a contract, defeating fixtures, a
verify-gate check, a daily agent path and a recorded history.

| Piece | Path |
| --- | --- |
| The operation | `scripts/sov_coldstart.py`, `scripts/sovcoldstart/` |
| The corpus | `scripts/sovcoldstart/corpus.json`, 175 questions in 4 tiers |
| The result contract | `contracts/coldstart-run.schema.json` |
| Its defeating cases | `conformance/fixtures/coldstart/run-cases.json`, 38 cases, 12 refusals |
| The gate path | `scripts/tests/test_coldstart_records.py`, via `run_tooling_tests.py` |
| The agent path | `.claude/workflows/sov-coldstart.js`, `.claude/skills/sov-coldstart/` |
| The cadence | `.claude/schedules/daily-coldstart.json`, disabled |
| The history | `reports/coldstart/` |
| The AI-native reading | `conformance/assessments/cold-start-benchmark.json` |

Three rulings hold it together.

**Ruling 1 — the corpus grades itself against the world, never against a maintained key.**
Each question carries a deterministic probe that recomputes its answer from the live
repository, host or GitHub. A benchmark whose answers are typed by hand is stale the day
after it is written, which is the failure it was built to detect.

**Ruling 2 — the gates are conjunctive and there is no weighted total.** Tier 0 admits no
failures, tier 1 needs 90%, tier 2 needs 80%, tier 3 is recorded and never scored. One
scalar over conjunctive gates is at best redundant and at worst anti-correlated: the same
98% reads NOT_ADMISSIBLE, DEGRADED or ADMISSIBLE depending only on which tier the missing
points came from, and a reader who sees 98% beside a failed invariant hears "it nearly
passed".

**Ruling 3 — the verdict is derived from the tier table and never written, and the table is
derived from the counts.** Every field in a run record except the counts is a conclusion,
and a participant that writes its own conclusion has removed the only part of the reading
anyone else was going to check. `VERDICT_NOT_DERIVED` refuses a record whose stated verdict
disagrees with its numbers, and `TIER_NOT_DERIVED` refuses a row whose stated gate or
result disagrees with them.

The second half of that ruling exists because the first half was defeated. An independent
witness read this contract, found that `defects` re-derived the verdict faithfully and took
the *threshold* from the record it was grading, and built an otherwise honest record
declaring `gate: 0.0` on tiers 1 and 2. Five of forty-six met its own bar. `records.write`
accepted it and wrote ADMISSIBLE to disk. The per-tier `result` string was readable the same
way. Both are now computed by `report.grade_row`, which both the printed card and the record
grader call, and `contracts/coldstart-run.schema.json` pins `gate` to the declared table so
the schema refuses an undeclared threshold even if the derivation is ever loosened. The case
is `D-012`, and the attack is kept verbatim as a unit test. A check that reads a declaration
where it could compute one is not a check.

Five further rules decide a score. Each was an exploit before it was a rule, found by
adversarial readers asked to construct a participant that scores well and knows nothing:

1. Unmeasured is not passed. A skipped, errored or hand-graded tier 0 question makes the
   verdict `UNPROVEN`; otherwise `--fast` is a way to pass the gate rather than to run less
   of it.
2. An absent tier is not a passed tier. `--section host` selects no tier 0 question and
   used to print ADMISSIBLE and exit 0 on that basis.
3. A failed probe never falls back to the answer key. Breaking every tier 0 probe used to
   re-point each question at the key checked into this repository.
4. No fuzzy string credit in either direction. The bare word `wrong` used to score RIGHT on
   three of the ten defeating cases.
5. The participant does not grade its own prose. Hand-graded questions read `UNGRADED`
   until a verdict file written by another seat names them, and that file must name the
   answers file it grades.

## Why a gate check and not a gate

`scripts/verify.py` reaches `sov_coldstart.py selfcheck` through `run_tooling_tests.py`,
which grades the run-record contract against its declared cases and fails if any refusal has
no case firing it. It deliberately does **not** run the corpus against the world.

Not its own named check, and that is a compromise rather than a design. The table in
`scripts/sovverify/checks.py` is at exactly 300 lines, which is the module ceiling
`scripts/lint.py` enforces, and four other live sessions hold that file. One more entry
fails lint for everyone on this tree. The cost is a named row in the verify output;
splitting the check table is the verification domain's concern, not this one.

Drift is a daily reading, not a defect. Making drift fail the required gate would reward
rebasing a stale expectation to green, which is precisely the behaviour this benchmark
exists to detect in other pages.

## Defaults taken

- **The daily schedule ships disabled**, like every other schedule in the repository. It
  declares cadence, mode, effect class and limits; it fires nothing until someone enables
  it. Reversible.
- **`isolation: worktree`** for the daily run, because ten sessions write this tree at once
  (trap T6) and a benchmark that reads a racing tree measures the race.
- **Records are committed, not written to `.local/`.** A benchmark whose history is
  gitignored cannot show drift across days, which is the reading the cadence is for. One
  small JSON file per run.
- **`retraction` scored `NONE`** in the AI-native assessment rather than argued up to
  PARTIAL. Superseding a record by date is not counteraction.
- **The `earn_it` judgement is left `OPEN`** with a null reviewer. Whether this surface is
  substantive or bolted on is a human judgement with an attributable reviewer, and only the
  root seat holds it.

## What this does not fix

**The corpus ships its own answers.** `expected` sits beside each question inside the
repository the participant is being tested on. An agent that reads `corpus.json` scores
ADMISSIBLE while knowing nothing. The `paper` verb hands a launched participant the
questions with every answer stripped, so reading the key becomes something it has to decide
to do rather than the default. That is a reduction, not a fix. Closing it means holding the
key outside the tree, which is a change to where the corpus lives and is a separate
concern.

**Fifty-seven questions are prose.** They read `UNGRADED` until Bdo writes a verdict file,
so an unattended daily run will normally record `UNPROVEN`. That is the honest state and
not a fault, but it means the daily cadence measures the deterministic 118 and parks the
rest.

**Time to useful and intervention count are not measured.** `AI-NATIVE.md` target bar 6
asks for both alongside accuracy. This surface measures accuracy only, so
`cold_start_competence` stays `UNPROVEN` in the assessment rather than moving to `PASS`.

**The surface is not wired into the qualification table.**
`contracts/ai-native-qualifications.json` still evidences `cold_start_competence` with
`FOUND-009`, which is about Sov's bounded agency and measures neither time nor
intervention. Repointing it crosses into a contract owned by decision 0070 and is a
separate concern.

## What an independent witness found

The first witness pass defeated the central claim, refuted one sub-claim, and produced two
corrections. All four are repaired above or recorded below rather than argued with.

- **The gate was self-declared.** Ruling 3, above. Repaired, with two new defeating cases
  and the attack kept as a test.
- **`selfcheck` graded `expect` as a subset of what fired**, so a refusal could fire on a
  case that never meant to test it with nothing saying so. `D-005` was earning
  `RECORD_SHAPE` alongside the `STANDING_OVERCLAIMED` it declared. Grading is now exact.
- **The claim "no new failing check" is literally true and partly dissented.** All six
  checks `verify.py` reports were already red. Two of them, documentation reader and diagram
  provenance, would be red anyway and this concern also contributes: four of its `.md` files
  are in the published corpus and absent from the built page, and its `STATUS.yaml` queue
  entries move a digest `diagrams/authority-typing.md` declares. The builder's flat "none
  involves a path of mine" was wrong, and `test_sov_docs` does touch a changed path.
- **`observer_relation` has two incompatible shapes.** Recorded as `OPEN-SEAMS.md` S26 and
  not settled here. The docstring in `scripts/sovkernel/authority.py` and the note in
  `conformance/fixtures/authority/grant-cases.json` both claimed the object shape was what
  `contracts/observation.schema.json` requires. It is not; that schema types the field as a
  required string on a different object, and the landing request's observation has no
  declared shape at all. Both claims are corrected.

One thing the witness could not do: write its observation. The `sov-witness` role under
`.claude/agents/` carries no `Write` tool, and it declined to reach for `Bash` to get around
that, which is the right call. So this concern has an independent reading and no independent
*record* of one, and the builder transcribing that prose into a file is precisely the seam
`_observation_verdict` names. Whether a witness should hold `Write`, or whether observations
should arrive through the Observation Service `decisions/0041` proposes, is a harness
question this decision does not settle.

## What a second witness found

The repair held against the attack that produced it and against nothing else. A second
independent witness, told what the first had found, took the same class further and refused
to support any standing at all. It was right to.

Every one of these was admitted by `records.defects` and written to disk by `records.write`:

- **The tier 0 row deleted entirely.** `derive` read a missing tier as a clean one and the
  check for an unasked tier inspected only rows that were present, so a record derived
  ADMISSIBLE with the hard-invariant gate simply absent from it.
- **Tier 0 duplicated with the clean copy last.** Which row decided the verdict was settled
  by ordering, so a record carrying a visible `result: "FAIL"` on tier 0 read DEGRADED.
- **`sections` never reconciled with `tiers`.** That block drives the entire drift reading,
  and a record could count the same run one way in the table and another in the block a
  reader compares day to day.
- **`corpus.selected` never reconciled with what was asked.**
- **`participant.answers_digest` never checked against the file it names**, so it identified
  nothing; a missing file was not refused either.
- **`SELF_GRADED` evaded by omitting `graded_by` entirely**, because the refusal read a
  number out of a block that need not exist.
- **`gate: true` admitted**, because `True == 1.0` in Python passes both the enum and the
  equality check.

Two more, outside the record contract:

- **A `contains` question whose probe drifted was still scored against the corpus key.** The
  run measured the key stale and then graded against it. Nine of the 49 tier 0 questions are
  `contains`-graded. `truth_for` now returns UNMEASURED on drift.
- **The verdict-file binding was optional and compared basenames.** Omitting
  `grades_answer_file` skipped the check, and any two files named `answers.json` graded each
  other. It is now a required digest.

Four new refusals, `TIER_SET_INVALID`, `COUNTS_DISAGREE`, `ANSWERS_UNVERIFIED` and a
strengthened `SELF_GRADED`, and eight new cases D-014 through D-021. Two docstrings were
also corrected: one described the exploit it had closed as though it were current
behaviour, and the other claimed a schema requirement that does not exist.

The lesson is the ruling above, arrived at twice: **a check that reads a declaration where
it could compute or look up the value is not a check.** Both passes found the same shape in
different fields, and the second found five instances after the first was repaired. The
class should be assumed alive until a pass finds none.

## What a third witness found

The class held a third time. A third pass, told what the first two had found, took it into
the places they had not looked and again supported no move above `BUILT`.

- **`owner_verdicts` was a path nobody opened.** `SELF_GRADED` refused a record whose
  verdict file was missing or empty and admitted one naming `nope/not-a-file.json`. The
  lookup it needed was already in the same function, seventeen lines above, checking the
  answers file. Worse: the positive fixture that existed to show a properly owner-graded
  competence run cited `scripts/sovcoldstart/verdicts/2026-08-26-owner.json`, a file that
  has never existed, and returned zero defects.
- **`sections` was reconciled only in total.** One section could claim 95 hits out of 45
  scored, offset by another claiming none, and `moved` reads the individual numbers. An
  empty block skipped the check entirely.
- **`run_id` was never re-derived**, and `write` names the file from it, so a second record
  declaring the same id replaced the first. A `NOT_ADMISSIBLE` reading could be overwritten
  by an `ADMISSIBLE` one leaving no trace.
- **`corpus.digest` was never checked against `corpus.path`.**
- **`manual_graded` and `manual_asked` were never related**, so a record could grade 99 of
  nothing.
- **A malformed `participant` crashed the grader** instead of refusing the record, and
  `load_all` grades every file on disk, so one such record broke `history` for the whole
  directory.

And two in `rebase`, which writes the answer key and is the sharper operational risk:

- **No tier 0 guard.** Ruling 1 in this decision says a tier 0 expectation that moved is a
  rule that changed, and the verb that rewrites tier 0 expectations took no argument to stop
  it. It now holds every tier 0 question unless `--tier-zero-ruling` names an existing
  decision record. That sentence was policy in prose and is now policy in code.
- **It wrote the wrong field.** For the 23 questions carrying `probe_expected`, the probe is
  compared against that field and `rebase` wrote the probe value into `expected`. A drift
  about whether a protected boundary is still declared rewrote the answer to "a builder
  writes the observation that witnesses its own change - what happens?" as the integer 1.

Two further tightenings. `selfcheck` compared sets, so one declared `RECORD_SHAPE` stood for
eight distinct shape defects; it compares multisets now. And the probe-leak check had been
made too broad in the second repair: it now separates a *presence* probe, which has to name
the thing whose presence it asserts, from a probe whose pattern equals what it is graded
against, which can report text vanishing and never a rule changing.

## Three questions the witnesses raised that this decision settles

Recorded here rather than sent up, because `AGENTS.md` Closure ownership makes ordinary
reversible engineering choices the concern-holder's.

1. **Is a run record checked against the corpus that produced it?** Two different checks, on
   purpose. `defects` grades a record against itself, which is all a reader of an old record
   can do: re-digesting today's corpus would mark every past reading defective. `write`
   additionally checks the corpus digest and re-derives the run id, because at write time
   both are computable. Reversible: fold them together if a use appears for grading an old
   record against a corpus it never saw.
2. **May `rebase` rewrite a tier 0 expectation?** Only with a decision record named on the
   command line and present on disk. A tier 0 question states a rule; its expectation moving
   means the rule changed, and that is a thing to record rather than a number to update.
3. **`AGENTS.md` says a run past fifteen seconds fails; `decisions/0050` says a slipped grade
   is a reportable observation. Which governs?** Both, and they do not conflict.
   `decisions/0050` is about the grade band - `PLATINUM` slipping to `GOLD` to `SILVER` is
   reportable and not a failure. Past fifteen seconds nothing is earned and the run fails,
   which is what `AGENTS.md` says and what `verify.py` does. A run that hits 15.9s on a box
   with ten live sessions is a real failure of a real budget, not a contradiction.

## What a fourth and fifth witness found

The class held twice more. Sixteen findings on the fourth pass and ten on the fifth, and
neither supported a move above `BUILT`.

The blocking one was mine and recent: the fourth pass found that `cmd_grade` never computed
the `owner_verdicts_digest` the record required, so every owner-graded run raised out of
`main` rather than recording. The one positive fixture proving an owner-graded record
admissible hand-wrote a digest no code path produced - the defect this contract exists to
refuse, sitting inside the contract.

Three more mattered more than bookkeeping:

- **`pin()` did not freeze what it claimed to.** Four probe kinds called `git ls-files`,
  which reads the index rather than a commit, so one run could observe two trees. That is
  trap T6, which the pin exists to prevent. `tracked_paths()` reads the pinned commit now.
- **The replacement matcher was confidently wrong.** `_pinned_glob` delegated to
  `PurePosixPath.match`, which is not `:(glob)`: it treats `**` as a single non-crossing
  `*` and matches from the right rather than from the repository root. Question C07 asks how
  many files sit under `reports/` and the matcher answered 23 where git answers 47, so the
  question reported drift about the world in every run and a rebase would have written the
  matcher's error into the answer key. `scripts/tests/test_pinned_glob.py` now asks git the
  same question and compares, which is the only check that catches this.
- **The `contains` grader let the participant supply the container, twice.** Read as "the
  term appears in the answer", one 339-character blob of prose took three tier 0 questions.
  The repair narrowed it to a comma-separated list, which changed the haystack from prose to
  commas and raised the yield: 886 tokens harvested from `AGENTS.md` and `CLAUDE.md` alone
  took four tier 0 questions, and a list of the 21 expected values took 18 of 21. The answer
  is now the term, which is what the paper has told participants all along.

The daily path had four of its own on the fourth pass - it overwrote its own answers file
every day and so invalidated the previous day's record, hid its coverage from
`records.comparable`, returned the grading agent's transcription of its own result while the
contract-graded record sat unread, and threw away the contamination it collected - and one
on the fifth: the read-back agent read an address the graded agent chose, and nothing
compared its answer to the report it was checking.

The rest were the same class in new fields: `sections` reconciled only in total,
`corpus.selected` and `run_id` and `corpus.digest` never re-derived, `SELF_GRADED` switched
off by omitting `graded_by` or by declaring nothing hand-graded, `ANSWERS_UNVERIFIED`
switched off by omitting the path, digests verified against files outside the repository,
`gate: true` slipping through because `True == 1.0`, and `cost_of` deciding a command
reaches the network from a substring of its name - trap T3's shape, which graded
`highlight` as a network call.

## One question the fifth witness sent up, which this decision settles

It asked whether `SELF_GRADED` is meant to establish that a second party graded, or only
that two files agree. It was right that the refusal was named for the first and enforced the
second: a witness wrote both files, put the digest of its own answers in the verdict file,
named itself the grader and granted RIGHT to all 57 hand-graded questions.

That is not an open policy question. `decisions/0070` already ruled that the
substantive-operation judgement in an AI-native assessment is refused unless a registered
`HUMAN` principal made it, and `AGENTS.md` already says no seat settles its own output. The
same mechanism applies here for the same reason, and `_grader_defects` now resolves the
verdict file's `graded_by` against `contracts/principals.json`.

It is a floor rather than a proof, and the code says so: the registry is a projection that
grants nothing, so this stops a participant naming itself and does not stop anyone who can
write `contracts/principals.json` from adding an entry. `contracts/standing-grants.json`
excludes that file from the standing grant, which is why `decisions/0075` matters here.

## What a sixth witness found

Eleven more, and three of them were the contract failing at its stated job rather than
missing an edge.

- **A perfect competence score with no owner grading at all.** Declaring `manual_asked: 0`
  and `manual_graded: 0` returned before `SELF_GRADED` was considered, so a record could
  claim 175 of 175, `ADMISSIBLE`, with no verdict file anywhere - and `history` read it
  clean. The number was in the corpus the record digest-binds in the same object. It is
  counted from there now.
- **Trap T3, in the check written to catch a self-report.** The workflow compared the
  read-back agent's verdict to the grading agent's with `indexOf`, and
  `"NOT_ADMISSIBLE".indexOf("ADMISSIBLE")` is 4, so the two never disagreed in either
  direction. `CLAUDE.md` records that exact shape as a known trap and
  `scripts/sov_standing.py` is the worked example. Whole tokens now.
- **Two tier 0 FATAL probes enumerate their own answer set.** A04's probe searched
  `AGENTS.md` for `RECORD_LOCAL|RESOURCE_CONSUMPTION|EXTERNAL_WORLD`, which can report one
  of the three being deleted and can never report a fourth being added - the change that
  would matter most. The guard that refuses exactly this skipped any question whose
  `expected` is not a string, which was 90 of the 175. Four questions were in that blind
  spot; all four are repointed at a `region_tokens` probe that finds the list by its
  surroundings and takes whatever is inside.

Close behind: `records.write` was append-preserving only against a second call in the same
process. A witness ran twelve trials on two threads and got one silent replacement and two
half-written files, and `load_all` raised on the torn one for the whole directory. It is
create-exclusive now, `load_all` survives an unreadable file, and the run id includes the
participant, because it omitted one and the daily schedule collides two participants at one
instant by construction.

Then the same class again: `corpus.questions` reconciled with nothing, `participant.answers`
admitting any file in the repository that digests correctly, the grader check discarding the
namespace so `hostile-agent:bdo` resolved to the registered human, the cost table reading
`kind` and never `scope`, and `_glob_regex` still disagreeing with git on seven patterns -
one of which raised `re.error` out of the probe loop, because `re.error` is not a
`ValueError` and was not in the catch list.

One finding was the opposite: `set_eq` refused a good answer. `_flat` strips a trailing
period and reads an arrow as a separator, `_norm` did neither, so `OPEN, BUILT.` was graded
WRONG against `OPEN,BUILT` on nineteen questions, nine of them tier 0. A benchmark that
refuses a correct answer measures no better than one that accepts a wrong one.

## Two more questions the witness sent up, which this decision settles

1. **May a run record declare `manual_asked` at all?** No, and the witness was right that
   this is the same question Ruling 3 answered for `verdict`. The record binds a corpus by
   digest; the count is read from that corpus whenever it still matches, which is always at
   write time. It is left declared only for a historical record whose corpus has moved on,
   where nothing can check it and nothing pretends to.
2. **Is a floor that accepts `hostile-agent:bdo` still a floor?** No. That was a hole with a
   floor's name on it, and the comparison is whole-identifier now. What remains genuinely a
   floor is the registry itself: it grants nothing, so anyone who can write
   `contracts/principals.json` can add an entry, which is why `decisions/0075` keeps that
   file outside the standing grant.

The third, whether a witness should hold `Write`, stays Bdo's. It is now the sixth unwritten
observation.

## Ruling 4 — the referents are fixed by the system, not by the record

A seventh witness read the generator behind six passes of findings, and it is one thing:
**the record supplies its own referents.** Every check was "read field F from the record,
then check something about F". Each repair bound one more referent by digest -
`answers_digest`, `owner_verdicts_digest`, `corpus.digest` - and digest-binding proves a
file was not swapped, never that it is the right file. So each repair converted "field
unchecked" into "field checked against a target the record also chose", and the hole moved
one field over.

It demonstrated this by pointing `corpus.path` at a one-answer fixture with a true digest.
The hand-graded count read as zero, the sixth pass's headline repair returned early, and a
record claiming 175 of 175 `ADMISSIBLE` with no owner verdict anywhere was written and read
back clean.

`CANONICAL_CORPUS` in `scripts/sovcoldstart/refusals.py` is the referent being fixed. A run
record is a reading of that corpus and of nothing else; `CORPUS_NOT_CANONICAL` refuses the
rest, and every count derived from the corpus is now read from the pinned file rather than
from the one the record names.

## Ruling 5 — the oracle is graded on whether it reaches its own checks

The same witness instrumented the corpus checks and found they returned early on all
thirty-four cases: the base record's digest is sixty-four zeros, so nothing ever bound the
real corpus, and `selfcheck` printed "eleven refusals all proven" while a whole family of
checks was unreachable from it.

"Every refusal has a case that fires it" is necessary and not sufficient. A refusal can fire
from one branch while three others never run.

`scripts/tests/test_fixture_coverage.py` disables one check at a time and asserts the
declared corpus notices. Ten mutations, none surviving. It found one real gap on its first
run - no case reached `_answers_shape` on its own, because every case citing an answers file
also failed the digest check first - which is now `D-032`. `selfcheck` additionally fails if
no case binds the canonical corpus at all, so the specific blindness that hid Ruling 4's
defect cannot recur silently.

## Ruling 6 - a record may not pin bytes that exist only on the disk that wrote it

A peer session found four generated diagrams under `diagrams/` stamping a `source_digest`
for `STATUS.yaml` that matches none of the thirty-four committed versions of that file. The
cause was a builder run inside the shared working tree, where it captured whatever another
session had uncommitted at that moment. A run record has exactly that shape.

It had exactly that hole. `CORPUS_UNVERIFIED` compared the declared digest against the
working tree, which proves the writer read what it says it read and proves nothing about
whether anyone else can. Two records already under `reports/coldstart/` name commit
`cc95d85` and carry different corpus digests, which is only possible while the corpus is
uncommitted and moving underneath them.

`CORPUS_NOT_AT_REVISION` in `scripts/sovcoldstart/records.py` compares the digest against
the corpus blob at the commit the record names. Write time only, like `CORPUS_UNVERIFIED`: a
reader of an old record must not re-run it, because the commit may have been rebased away
and refusing a past reading on that ground is the same mistake as re-digesting a corpus that
has since moved on.

The immediate consequence is that no run can be recorded until this concern lands. That is
the correct statement rather than a regression: a benchmark record is a provenance claim,
and a provenance claim over bytes nobody else can fetch is not one. `sov_coldstart.py
--record run` now prints `REFUSED to record this run` and exits 1 instead of raising.

Two things fell out of building it, both true readings rather than incidents:

- `_blob_at` spawns its own `git cat-file` rather than reusing `_git`, which decodes stdout
  to text. A digest taken over decoded text is not the digest of the file, so a provenance
  check built on it would be checking its own round trip.
- The first byte-exactness test compared a blob against the working-tree copy of `AGENTS.md`
  and failed, because another session had that file modified. The test now grades against
  git's own object id, and the write-path cases stand their corpus on a tracked file chosen
  by measuring which ones are clean rather than by naming one. In a tree nine sessions
  write, any file named in a test is eventually one of the modified ones.

## Why the eighth pass is this instead

Seven adversarial passes on one bounded concern found 1, 7, 8, 16, 10, 11 and 16 defects.
Not one came back clean, and four of the seven found a defect the previous pass's repair
introduced. The seventh's own reading was that the count looks like decay and is not: what
matters is whether the central claim survives a pass, and it had not survived four of them,
because nothing about the shape of the artifact had changed.

That is a resource judgement, and under `AGENTS.md` Closure ownership it belongs to whoever
holds the concern. The ruling: **stop reading and change the shape.** Ruling 4 removes the
generator, Ruling 5 makes the oracle able to see itself, and both are finite where another
pass is not. An eighth pass is worth taking after those land, as a spot check over a gate
that can now see what it grades - not as the primary instrument.

The witness's third recommendation, moving the oracle out of the participant so that
`selfcheck` is not `oracle.py` grading a fixture it ships with, is **not** done and is the
largest thing still open here. `AGENTS.md` puts cross-participant cases in `conformance/`
with an oracle that does not import participant code; today the fixture is data under
`conformance/` and the grader is the thing graded. `test_fixture_coverage.py` narrows the
gap and does not close it.

## What would defeat this ruling

- A participant scoring ADMISSIBLE on a run whose answers came from reading `corpus.json`,
  landed as a change on that basis. The mitigation would then be shown insufficient rather
  than partial.
- A daily run whose drift is dominated by counts that move for reasons no reader cares
  about. The corpus would then be measuring repository churn rather than orientation
  accuracy, and tier 2 would need re-cutting.
- A reading taken by a genuinely fresh participant that scores well while that participant
  goes on to make an error the benchmark claims to cover. The corpus would then be
  measuring recall rather than competence.
- Evidence that the verify check costs enough wall time to move the graded budget band. It
  is pure file reads today; if that changes, the check moves out of the gate.
- An eighth reading finding another referent the record still chooses. Rulings 4 and 5 are a
  claim about the *generator*, not about a list of fields, and the way to defeat them is to
  find a check that still reads its target out of the thing it is grading.
- A mutation that survives `test_fixture_coverage.py` while `selfcheck` still reports every
  refusal proven. That would mean the coverage instrument has the same blindness it was
  built to remove.
- The count so far is 1, 7, 8, 16, 10, 11, 16 across seven passes - every finding an
  instance of one class, and four passes finding a defect the previous repair introduced.
  If the eighth pass reads like the seventh, the shape change did not work and the honest
  conclusion is that this contract is the wrong shape rather than insufficiently read. Three passes is the current
  evidence that a single adversarial reading of a contract like this is not enough, which is
  itself worth carrying to the next one.

## Residual

This decision cannot be landed by the standing loop: `decisions/` is excluded from
`grant:standing-landing-loop`, which is correct. Everything else in the concern is inside
the grant's scope and waits only on an independent observation.
