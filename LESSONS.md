# Lessons

An inbox, not a rulebook. Every entry here is a `Proposal` under `SPEC.md`
(Information objects): it begins `RECORDED` and claims no authority. Nothing in
this file governs anything. A lesson that should govern leaves this file for the
document that owns the rule; a lesson that restates a rule an owning document
already holds is dropped with a link to that owner (`AGENTS.md`, Design System
of Record: do not duplicate a rule as a competing authority).

Proposed standing: `decisions/0029-lessons-loop.md`.

## How an entry moves

`RECORDED` when written here. `ADMITTED` when a fixture or check passes for it.
`RATIFIED` only by Bdo, through a decision record. `EFFECTIVE` when it actually
runs in `scripts/verify.py` or `scripts/lint.py`. The four do not collapse
(`SPEC.md`, Historical standing and current effectiveness).

A lesson awaiting Bdo is a PROD-I-6 pending-right record. It blocks nothing.

## Capture and drain

- **Capture trigger:** memory consolidation — when an interactive session merges
  or retires its memory files. Not host context compaction; wiring that is a
  later `update-config` operation.
- **Drain trigger:** seven entries standing `RECORDED`. At seven, each is drained
  into its landing or dropped. The rule is *drain*, not *review*: a file that only
  grows becomes policy by accident.
- **Landing:** `fixture` when the claim is mechanically checkable, `decision` when
  it is a judgement. Also `lint`, `known-gap`, `seam`, `drop`. The lesson declares
  its landing when written.

Standing now: **8 `RECORDED`**, threshold 7. L-0001, L-0008 and L-0009 are
`EFFECTIVE`. The drain is due and is recorded as debt rather than refused:
`decisions/0029` declined to fail a run on an eighth lesson, because that makes
capture costly at exactly the moment capture matters. `python
scripts/sov_lessons.py check` reads this page every run and refuses a standing
the tree does not support; the count it prints is a debt reading, not a gate.

Draining the eight is not one concern. L-0003, L-0005 and L-0006 each land in a
different service from the others, and `AGENTS.md` mints a separate concern when
work crosses a service boundary; four of the eight declare `decision` landings
that are Bdo's.

## Entries

### L-0001 · The orientation snapshot drifted from the record inside one day

`CLAUDE.md`'s repository snapshot claimed 26 commits and 17 decision records.
The record at the time of writing held 65 commits, 18 PRs, 51 issues, and
decision records through 0027. A snapshot that is stale within a day is worse
than no snapshot: it is read as current by every launched agent, which does not
carry the interactive session's context.

- Evidence: `lineage/SOURCES.lock`, all 65 `git-commit:*` and 18 `github-pr:*`
  sources; `CLAUDE.md` "Repository snapshot (informational)".
- Landing: `lint` — landed 2026-08-25 as `scripts/sov_snapshot.py`, run inside
  `scripts/verify.py` as `orientation snapshot`. It derives the verification
  check count, commits, decision records, declared operations and reports from
  the record and fails when the page diverges past a declared tolerance. Two
  further numbers are listed as NOT CHECKED rather than guessed at, after a draft
  that re-counted conformance cases got 9 against the suite's own 20. A witness
  then showed that a third, declared operations, had been wrongly listed as
  underivable when a gated projection already held it.
- Standing: `EFFECTIVE` — the check runs inside `scripts/verify.py`, which is
  what this file defines `EFFECTIVE` to mean. It was recorded `ADMITTED` until
  a witness pointed out that the four standings do not collapse and this one
  was under-claiming. `RATIFIED` remains Bdo's and nothing here asks for it.

### L-0002 · Six of twenty-five sessions are locked but never recorded

`SOURCES.lock` carries 25 `session-file` sources; `lineage/recordings/` holds 19
session recordings. The six without a recording are the six largest transcripts
on the host — the ones holding the most abandoned paths and corrections, which is
exactly the material a session source exists to preserve. No size cap in
`services/asset/scripts/` explains the gap; the cause is not established.

- Evidence: `session-file:0e5f4b24-fe64-4e61-8f83-b0957e4e7eae`,
  `session-file:0fde28fd-48b2-4b45-aa42-ad6bfc72a631`,
  `session-file:146efe7e-d200-42f2-bc46-03163e48b76d`,
  `session-file:8fcfa24b-4ac0-42ac-9c91-62f4f9c950c5`,
  `session-file:99dc7434-460a-4a54-846c-cf775a777acd`,
  `session-file:a4d1c9a7-4f15-42ec-ae79-685452d4eeda`.
- Landing: `fixture` — ingestion reconciles locked sources against produced
  recordings and refuses silently to skip one; a declared skip carries a reason.
- Standing: `RECORDED`.

### L-0003 · Two omission definitions overlap, and only one gets the credit

`history_reader.py` declares `sanitize-v1` (absolute host paths, oversized tool
results, secret shapes) and `pii-v1` (owner email, host username). All 18 lossy
recordings carry `pii-v1` only. Reading the code, an omission is recorded when it
removes something, and `pii-v1` consumes the host username inside a path before
`sanitize-v1` sees it as a path. No content leaked. But a `Recording` that
declares which definitions *fired* is a weaker claim than one declaring which
were *applied*, and `SPEC.md` (`Reader`) asks for omissions deterministically
recoverable from the definition — which reads as configuration, not effect.

- Evidence: `services/asset/scripts/history_reader.py` (`definition_record`,
  the `if removed:` guard); all 18 lossy manifests in `lineage/recordings/`.
- Landing: `decision` — which of declaration-by-configuration or
  declaration-by-effect the `Recording` contract means, and which definition owns
  host paths when both match.
- Standing: `RECORDED`.

### L-0004 · One session transcript is recorded `EXACT`

`rec-6437c0f22043d43e` records a `session-file` source with `fidelity: EXACT` and
`omissions: []`. Under `SPEC.md` (`Reader`), `EXACT` asserts the reader declares
no omissions at all. For a Claude Code transcript that assertion should be rare
and should be justified, not reached by a transform finding nothing to strip.

- Evidence: `lineage/recordings/rec-6437c0f22043d43e.json`.
- Landing: `fixture` — a `session-file` source recorded `EXACT` is refused unless
  the recording carries a declared justification.
- Standing: `RECORDED`.

### L-0005 · Putting the checks last meant the budget took out exactly the checks

Federation run `wf_a2d4eb5e-df2` dispatched five domains sequentially in
implementation order, verification fourth and governance fifth. It exhausted the
host account's monthly spend at agent 20 of 25. The five agents that died were
the three verification builders, the witness, and a governance scoping agent —
that is, every agent whose job was to check the work, plus the operation that
would have surfaced the result for judgement. The build survived; its verification
did not. Ordering checks after construction is correct for dependency and wrong
for budget exhaustion, because a budget runs out at the end.

- Evidence: run `wf_a2d4eb5e-df2` (25 agents, 20 done, 5 failed, 1,792,065
  subagent tokens, 555 tool uses, 5,013s); its journal at
  `subagents/workflows/wf_a2d4eb5e-df2/journal.jsonl`;
  `.claude/drafts/history-lineage-and-lessons-brief.md` operations 1-5.
- Landing: `decision` — whether a federation run reserves budget for its witness
  before dispatching builders, or interleaves verification per domain rather than
  running it as a terminal phase.
- Standing: `RECORDED`.

### L-0006 · A GitHub source's digest covers its title, not its content

`history_sources.py` says plainly that "digests for git and GitHub sources cover
the captured representation recorded here; session digests cover raw bytes". For
a commit that is sound — the payload is `<sha>\t<subject>\n`, and the sha is
itself a content address, so the commit cannot change without the address
changing. For a pull request or issue it is not: the payload is number, title,
and state, so a body can be rewritten entirely and the digest will not move.
PROD-I-2 asks that "a source rereads byte-identical by digest"; 69 of the 159
locked sources currently satisfy a weaker claim than that.

- Evidence: `services/asset/scripts/history_sources.py` (`build_lock`,
  `enumerate_github`); the 51 `github-issue:*` and 18 `github-pr:*` entries in
  `lineage/SOURCES.lock`. Found by witness check W3, which reproduced all 65
  git-commit digests independently and could not do the same for GitHub bodies.
- Landing: `decision` — whether a GitHub source's digest must cover its body,
  which makes the lock depend on an `EXTERNAL_WORLD` read to verify, or whether
  the lock declares metadata-only fidelity for those kinds and says so in
  `lineage/README.md`.
- Standing: `RECORDED`.

### L-0007 · A guard can be too narrow, or about the wrong thing, and hardening fixes only the first

Two participants spent 2026-08-25 hardening two unrelated guards against
independent witnesses. Ten refutations between them, seven on one side and three
on the other. In both, the loop broke the same way, and neither participant
reasoned their way out of it — one of them reasoned correctly.

The console's authority check compares four strings: node, operator, capability,
scope. One round hardened the node id into a predicate that held — a witness
threw 297 spellings at it, Arabic-Indic digits through NUL, and 60 identities
across all 3600 ordered pairs, and could not break it. It is still true. It was
about the wrong noun. The credential was bound to a node and the *records* were
not, so a caller who could not take one office took their own and spent it
against the first one's data. Bound the records, and the *operator* was still
caller-typed, because three of the four strings the check compares had never been
examined. Every attack had varied the one already hardened.

The landing gate's path check ran the same course. Five rounds closed spellings
that reached an admitted prefix while naming an excluded file — traversal, dot
segments, doubled separators, eight globs, pathspec magic. Those were narrowness
and hardening was the right answer. Then a bare directory passed every one of
them, because it is a canonical literal path that selects a set. Then the gate
turned out to grade `--path` while `git merge` carried a different set entirely,
so an excluded path reached the target having never been shown to the evaluator
at all. Neither of the last two is a spelling.

The distinction that matters: a guard can be too narrow, or it can be about the
wrong thing. More rigour on the predicate finds the first and is invisible to the
second, because from inside the predicate the wrong-thing failure looks like
success. A participant who responds to being refuted by writing a broader
predicate will be refuted again.

Generalising correctly does not end the sequence either, and that is the harder
half. After the wrong-noun refutation the console round did not write a broader
predicate: it moved the fix from the call sites to the folds, one chokepoint every
lookup by id passes through and listings filtering rather than refusing, on the
stated reasoning that a call-site fix is a list and this needed a rule. That is
the right response, reached deliberately, and the next witness refuted it anyway
on an axis the new rule did not touch. So a correct generalisation at one level
does not protect the level above it, and the stopping condition cannot be "until
it is right". It has to be a budget and a seam.

What broke both loops was a witness changing the question rather than sharpening
it. One said it in a line: *I could not find an escape inside the string. The
escape is outside it.*

The operational move, and the only instruction here worth following: having
established that the guard holds, enumerate what it touches — the operands it
compares, the sets it names, the call sites that reach it — and mark which have
actually been varied by an attack rather than assumed covered. The console check
compares four operands and three were never varied. `--path` named one set and
the merge carried another. Both were answerable by listing and asking, which is
cheap, and neither participant did it until a witness did.

Over-applied, this is expensive: enumerating neighbours has no natural stopping
point, and a participant who applies it without a budget never lands. The counter
is that bounded rounds each producing a real refutation is the loop working,
while a further round chasing a class that cannot be closed inside the service is
the loop failing. Knowing which one you are in is a judgement this lesson cannot
make for anyone.

- Evidence: `reports/observations/2026-08-25-*` — twelve observations across the
  landing gate, seven of them dissents, with the bare-directory and merge-range
  findings at `...directory-and-containment...` and `...effect-path-drift...`.
  The console rounds are held on `feat/console-authority-enforced` and their
  three observations are **not in the tree**, so a reader cannot reach them.
  That is not an oversight by their author: `contracts/standing-grants.json`
  requires an independent observation and admits no path under `reports/`, so
  the loop cannot land the evidence its own precondition demands. Since the
  merge-range fix landed, committing one to a branch refuses the entire landing,
  because it is then carried whether or not `--path` names it. Both landings that
  did carry observations went by hand. Widening the grant by one prefix makes
  this citation reachable and the qualifier removable.
- Landing: `decision` — whether "enumerate what the guard touches and mark what
  has been varied" belongs in `AGENTS.md` alongside the evidence rules, or stays
  a practice note. It is a claim about how participants attack their own work,
  which is Bdo's to place.
- Standing: `RECORDED`.

### L-0008 · The number that defined the phase was never on the critical path

`python scripts/sov_f2_gate.py` read the distance between `SPEC.md` and the
conformance corpus for six days and returned non-zero the whole time. Nothing
ran it. It was in no check table, no landing gate, and no orientation page, so
the reading sat at 0 of 44 across 401 commits and refused nothing. The gate was
not wrong and was never consulted; the defect is that a number nothing refuses
on is a number nothing moves.

Registering the gate itself is the wrong repair and was rejected: it would
refuse every run until the phase exit is earned, which teaches a reader to
ignore a red check. What landed is a floor. A fall refuses, because a fall
needs an edit to the corpus or the specification and is attributable to it. A
stall prints its commit count and records debt, on the reasoning
`decisions/0081` used to take the wall clock out of the exit code.

- Evidence: `reports/2026-08-27-phase-i-retro.md` finding 1;
  `contracts/phase-progress.json`; `scripts/sov_phase_progress.py`;
  `scripts/tests/test_phase_progress.py`.
- Landing: `fixture` — landed 2026-08-27 as `scripts/sov_phase_progress.py`,
  registered in `scripts/sovverify/checks.py` as "phase progress floor".
- Standing: `EFFECTIVE`.

### L-0009 · Coverage was produced at one granularity and read at another

The oracle held 20 controls, all passing, each declaring a `requirement`. The
gate reads *predicates*, one granularity below that, and credits a case only for
what it declares in a machine-readable `predicates` array. None of the 20 had
one, so real defeating-fixture-carrying coverage read as zero. Neither side was
wrong from its own end, and joining the two vocabularies was nobody's job.

The join itself was cheap — an afternoon reading controls already in the tree —
and took the reading from 0 to 36 of 44 without adding a single fixture. What
makes it stay true is that the eight remaining gaps are enumerated with reasons,
so covering one forces its own exclusion to be deleted, and a predicate id the
specification does not state now refuses instead of being silently uncounted.

- Evidence: `conformance/oracle-controls.json` `predicates` arrays;
  `contracts/phase-progress.json` `uncovered_on_purpose`; the `UNKNOWN_PREDICATE`
  and `UNDECLARED_UNCOVERED` refusals.
- Landing: `fixture` — landed 2026-08-27 in the same check as L-0008.
- Standing: `EFFECTIVE`.

### L-0010 · Governance outgrew the thing it governs

78 decision records against 0 covered predicates. 60 contracts against 20
conformance controls. Each record was defensible when written and several were
commissioned directly; the aggregate is a system that documents faster than it
demonstrates. The clearest instance is `decisions/0041`, which charters the
Observation Service because `observe_run` has no service behind it and
`AI-NATIVE.md` check 3 reads `UNATTESTABLE` everywhere. Four days later the
charter is still a charter and check 3 still reads `UNATTESTABLE`. The record was
correct and changed nothing, because a record is not a holder.

What this does not claim is that the records were wrong or that fewer should have
been written. The measurable thing is the ratio and its direction, and whether a
ratio is a defect at all is a judgement about proportion.

- Evidence: `reports/2026-08-27-phase-i-retro.md` finding 3;
  `decisions/0041`; `services/observation/`; `python scripts/sov_docket.py`.
- Landing: `decision` — whether a proportion between records and demonstrated
  coverage is a governed constraint at all, and if so what holds it. It is a
  claim about how much governance is too much, which is Bdo's to place.
- Standing: `RECORDED`.

### L-0011 · Product ground was accepted and then not used to route anything

Sixteen ground claims were accepted on 2026-08-24 (`decisions/0052`), fixing
revision GROUND-1 so later work could be attributed against them. Nothing since
has required a unit of work to name which claim it serves. `PRD.md`, `ROADMAP.md`
and `SPEC.md` contain zero occurrences of the string `GROUND-`, so the edge from
a requirement to the claim it keeps does not exist in either direction. The
ground became a document to cite rather than a key to route on.

The repair is small and is not built: nine requirements, each naming the ground
claim it serves, and a check that a requirement without one refuses. It is listed
here rather than done because it edits `PRD.md`, which is a governing document
this concern does not hold.

- Evidence: `grep -c "GROUND-" PRD.md ROADMAP.md SPEC.md` reads 0, 0, 0;
  `contracts/product-ground.json`; `decisions/0052`.
- Landing: `fixture` — a Phase-I requirement that names no ground claim refuses.
- Standing: `RECORDED`.

## Dropped

A dropped entry stays listed here with its reason and the owning document it
duplicated, so the same lesson is not relearned and re-proposed.

- **Work was scoped by document, not by initiative.**
  `reports/2026-08-27-phase-i-retro.md` finding 4. Dropped as a restatement:
  `contracts/custody.schema.json` and `contracts/custodies.json` own this rule,
  and `decisions/0085` records it. Recording it here as well would make the
  inbox a second authority on a rule an owning document already holds.
- **A concern ended at a landed commit, not at a closed path.**
  `reports/2026-08-27-phase-i-retro.md` finding 5. Dropped for the same reason:
  `contracts/work-circuit.json` owns it as the `OPEN_PATH` refusal, with
  `adapters/ollama/invoke.py` as the live instance.
