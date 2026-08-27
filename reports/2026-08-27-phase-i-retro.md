# Phase I retro — what it was defined as, and where six days got it

Reading taken 2026-08-27 on `feat/federation-harness-and-hardening`, 49 commits
ahead of `main` and 41 behind. A report is not policy and settles nothing
(`AGENTS.md`, directory boundaries). Every number below comes from a command
named beside it, so a later reader can re-run the reading rather than trust it.

## The headline

Phase I is defined by `PRD.md` as nine requirements and an exit condition, and by
`ROADMAP.md` as seven phases F0 through F6. Six days of work produced 401
commits, 78 decision records, 60 contracts and 68,843 lines of Python.

`python scripts/sov_f2_gate.py` reads **0 of 44 normative predicates carrying
both a positive and a defeating fixture.** That is the F2 exit criterion, stated
verbatim. F2 is the second of seven phases.

Six days moved it from zero to zero.

That is not a productivity finding and reading it as one would be the wrong
lesson. The Record Service, the Asset Service, the acceptance gate, the
closure-ownership table, the product ground, the seat topology and the landing
loop are all real, all built, and several are genuinely good. The finding is
narrower and more useful: **nothing that was built was ever required to move the
one number that defines the phase.**

## What Phase I was defined as

`PRD.md` states the exit in five clauses:

1. every normative predicate has a positive and a defeating fixture;
2. the applicable fixtures run through one human-facing binding and two
   materially different model bindings;
3. independent observation can reconstruct the receipts;
4. open judgement calls are visible;
5. the owner ratifies Phase-I operational acceptance.

Clause 4 is served. Five acceptance packets sit in the queue with runnable
evidence, five have been accepted, and `sov_accept.py audit` fails the build if
anything waits without a reason or a packet. That machinery works.

Clauses 1, 2 and 3 are at or near zero, and clause 5 cannot begin until they
move.

## Where six days got it

Everything in this table comes from a command.

| Reading | Value | Command |
| --- | --- | --- |
| Commits | 401 | `git rev-list --count HEAD` |
| Decision records | 78 (33 open, 20 with a routed question) | `scripts/sov_docket.py` |
| Contracts | 60 | `ls contracts/*.json` |
| Reports | 27 | `ls reports/` |
| Python | 68,843 lines | `find . -name '*.py' \| xargs wc -l` |
| Service boundaries | 11 | `ls services/` |
| Declared operations | 140 | `scripts/sov_worklist.py derive` |
| Verification checks | 44, graded SILVER | `scripts/verify.py` |
| Conformance controls | 20, all passing | `conformance/run.py` |
| **F2 predicates covered** | **0 / 44** | `scripts/sov_f2_gate.py` |
| Epic issues | 52 open-ish, 2 ready, 21 unroutable | `scripts/sov_epic.py status` |
| Open seams | 25 of 27 | `OPEN-SEAMS.md` |
| Branches unmerged | 39, holding 207 commits | `scripts/sov_strand.py` |
| Commits on this disk only | 20, across 4 branches | `scripts/sov_strand.py` |
| Console operations declaring an authority and checking none | 9 | `STATUS.yaml` |
| Things ratified | 1 — `grant:standing-landing-loop` | `decisions/0065` |

Commits by day: 15 on the 22nd, 125 on the 23rd, 145 on the 24th, 73 on the
25th, 25 on the 26th, 18 on the 27th. By type over the whole window: 100 `feat`,
71 `docs`, 58 `fix`, 33 `test`, 25 `chore`.

## Six findings

### 1. The gate that measures the phase was never on the critical path

`verify.py` runs 44 checks and passes. The F2 gate is not one of them. Nothing in
the landing loop, the CI gate, or the orientation snapshot refuses when 0/44
stays 0/44. `CLAUDE.md` trap T2 already warns that a green `verify.py` means
"unchanged", not "correct" — but the trap is about the participant baseline, and
nobody extended the same suspicion to the phase gate itself.

**A number nothing refuses on is a number nothing moves.**

### 2. Coverage was produced at one granularity and read at another

The oracle holds 20 controls. They pass. Each declares
`"requirement": "PROD-I-1"`. The F2 gate reads predicates — `PRED-I-1.1`,
`PRED-I-1.2` — and credits a case only for predicates it declares in a
machine-readable `predicates` array. None of the 20 has one.

So real, passing, defeating-fixture-carrying coverage reads as zero. The gate is
not wrong to refuse credit for a claim nobody made. The defect is that joining
the two vocabularies was nobody's job, and each side looked complete from its own
end.

This is also the single highest-value hour of work available right now. The
requirement family is 25 of the 44 predicates. Reading each of the 20 controls
and declaring which predicates it actually exercises is bounded work over
artifacts that already exist. It will not reach 25 of 25 — some predicates
genuinely have no case — and it moves the transition (14) and parity (5)
families not at all. It is still the difference between a gate that reads zero
and a gate that reads the truth.

### 3. Governance outgrew the thing it governs

78 decision records against 0 covered predicates. 60 contracts against 20
conformance controls. Each individual record was defensible when it was written;
several were commissioned directly. The aggregate is a system that documents
faster than it demonstrates.

The clearest instance: `decisions/0041` charters the Observation Service because
the kernel's `observe_run` transition has no service behind it and
`AI-NATIVE.md` check 3 reads `UNATTESTABLE` on every service assessment. That
was recorded on 2026-08-23. Four days later `services/observation` is still a
charter with no implementation, and check 3 still reads `UNATTESTABLE`
everywhere. The record was correct and changed nothing, because a record is not
a holder.

### 4. Work was scoped by document, not by initiative

Every commit had a home — a decision, a contract, a service directory. None had a
holder carrying it to a named stage. `AGENTS.md` has required closure ownership
since `decisions/0055`, and participants have largely honoured it *within* a
session. What was missing is the layer above: something that survives the session
and says this initiative is still owed, by this seat, until it reaches this
stage.

The measurable consequence is the 21 unroutable epic issues. They are unroutable
because nothing about them says what would close them, which is exactly the
failure `contracts/work-item.schema.json` already names for a single item and
which nothing named for a collection.

### 5. A concern ended at a landed commit, not at a closed path

`adapters/ollama/invoke.py` executes a model against the local runtime and grades
its own output. It landed, it works, and its path does not close: the participant
that produced the result is also its only evidence. `GROUND-010` — a report is
not an observation — was accepted on 2026-08-24 and this is the shape it
forbids.

Same pattern, larger: nine BUILT console operations declare an authority and
check none, `console.grant` and `console.revoke` among them. Anyone reaching the
service can write themselves a grant. Each of those operations landed as done.
Discovery said they were guarded, the endpoint did not guard them, and neither
side alone looked wrong.

### 6. Product ground was accepted and then not used to route anything

Sixteen ground claims were accepted on 2026-08-24 (`decisions/0052`), fixing
revision GROUND-1 so later work could be attributed against them. Nothing since
has required a piece of work to name which claim it serves. The ground became a
document to cite rather than a key to route on.

`custody:phase-i/predicate-fixtures` naming GROUND-010 is not decoration — it is the
first time a unit of work has had to answer "which claim does this keep" before
it could be admitted.

## The terminal Bdo ruled

`phase_execution_status: CLOSED`, `phase_acceptance_status: NOT_EARNED`.

Two readings rather than one. The operating window is over; the exit was not
earned. The original definition stays historically intact and no partial
evidence is promoted into acceptance. `contracts/phases.json` records it and
pins `PRD.md`, `ROADMAP.md` and `SPEC.md` by digest, so a later reader can prove
the exit being checked is the exit the phase opened with.

Clause by clause: X1 predicate fixtures `NOT_EARNED`, X2 binding parity
`NOT_EARNED`, X3 receipt reconstruction `NOT_EARNED`, X4 judgement visibility
`SUBSTANTIALLY_EARNED`, X5 operational acceptance `NOT_REACHED`. Every unmet
clause names the exit custody that inherits it, because carried forward is not a
terminal.

## What changes

Built this session and described in `decisions/0085`:

- **`contracts/phases.json`** — the phase terminal, its pinned definition, and
  the five clauses with their verdicts. A phase reading `EARNED` while a clause
  does not is refused: that is how a campaign ends by narrowing its own
  definition.
- **Custody, hierarchical** (`contracts/custody.schema.json`,
  `contracts/custodies.json`) — five exit custodies mirroring the five clauses,
  eight delivery custodies beneath them, three marked explicitly outside the
  phase exit. An initiative that cannot name the exit custody it serves is not
  Phase-I work.
- **The work circuit** (`contracts/work-circuit.json`) — `ROOT_POINT` through
  `CAPABLE_NODE`, kept as a separate axis from standing and from work state.
  Every member card carries all three, so `CAPABLE_NODE` is never read as done.
- **Definition of ready and closed** (`contracts/concern-admission.json`) —
  twelve fields before a concern enters work, six layers before it leaves.
  Landed is not closed, and cleaned is not optional.
- **Estimation** (`contracts/estimation.json`) — thirteen dimensions including
  the coordination emissions, with maturity tied to circuit position so a
  delivery promise cannot be made at a point that has no extent.

Three readings the repository could not previously produce:

- `sov_custody.py reconcile` — the phase exit, clause by clause, against the
  custody holding each.
- `sov_custody.py orphans --kind ITEM` — **119 of 140 declared operations fall
  inside no custody.** Console 24, Asset 17, Projection 16, Host 15, Registry 13,
  Proofing 11, Gateway 9, Automation 7, Identity 7. Admissible, and newly
  visible.
- `sov_custody.py orphans --kind SEAM` — 22 of the 25 open seams are held by
  nobody.

## What "more boring work" now means concretely

Advance one member of one custody by one stage, against a declared admission
predicate, with a defeating case that says what would prove the stage was not
reached.

The five shortest such moves, in order of value per hour:

1. Declare predicates on the 20 oracle controls. `custody:oracle-predicate-join`,
   `VERTICAL_SLICE` to `HORIZONTAL_SURFACE`. Moves the F2 gate off zero and is
   where Bdo's close sequence starts.
2. Repair the broken journal chain at `entry_80767935e18c488fb45502df9d5c385e`.
   `custody:record-custody`. Every session start has reported it and no session
   has fixed it. This is also the nominated first thin slice of the successor
   campaign.
3. Add the authority check to `console.grant` and `console.revoke`.
   `custody:authority-enforcement`. Guarding them removes an ability from whoever
   can call them today, so it is presented rather than applied.
4. Land or retire the branches holding commits that reach no trunk.
   `custody:trunk-reconciliation`.
5. Attach the 22 unheld seams to a custody or close them with evidence.
   `custody:seam-drain`.

## What this retro does not claim

- It does not claim the custody set is correct. It is a decomposition, it is a
  reversible default, and rejecting one or naming another is Bdo's.
- It does not claim the estimates are accurate. Several are guesses, each
  declares itself one in its `basis` field, and the first measured actual landing
  outside its range is what overturns it.
- It does not witness anything. Every contract and reader named here is
  `BUILT_SELF_TESTED_NOT_WITNESSED`. The participant that built them cannot
  observe them.
- It does not read the working tree as landed. `STATUS.yaml` is owed four status
  fields and is deliberately not edited: live sessions held it while this was
  written.
