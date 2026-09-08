# Commissioning circuit, reconnaissance lap

Status: `IN PROGRESS · UNGRADED · CLAIMS NOTHING`

One bounded piece of real work carried around the Phase 1.5 commissioning
circuit by hand, to find out which stages have a mechanism and which do not.

This run grades nothing and earns nothing. `P15-X5` has no reader, and the
circuit it names is not declared anywhere a machine can read, so no verdict
about the clause could be honest. The deliverable is the trace: what each stage
cost, what carried it, and where it broke.

## Why by hand, and why before the reader

The `P15-X5` custody carries two tickets. The first is the circuit reader
`decisions/0102` named as this clause's first piece of work on the day the
phase opened. Writing that reader against the ASCII block in
`contracts/phase-1-5-phase-ii-horizon.md` would be a grader built from a
drawing, which is the shape of the last five days: four instruments landed,
none of them fed. Walking the circuit first produces a real trace to build the
reader against, and finds the stages that have no mechanism at all - which no
reader could have discovered, because a reader only checks the stages someone
already knew to declare.

## The payload

`concern:schematically/golden-rendered-text`, in the schematically repository.

Pull request #32 there states in its own body, under "Not in this PR": "A
golden-corpus check that compares rendered text, which would have caught the
caption regression at its own commit." That PR introduced a real regression at
`1f213c7` where typed component captions stopped rendering, repaired it at
`31bbe4e`, and recorded that no suite caught it.

Chosen because the work is small, is owed, is claimed by no open pull request,
and above all because its correctness is objectively checkable: the new check
must pass on `dev` and must fail at `1f213c7`. A payload whose result is a
matter of taste would have made the independent finding on the work unfalsifiable.

Deliberately not maintenance of this repository. The phase is named Participant
Delivery Substrate and nothing has been delivered through it.

## Trace

Stage names are the circuit's own, from `contracts/phase-1-5-phase-ii-horizon.md`.

### 1 · Definition - MECHANISM EXISTS

`python scripts/sov_lease.py take` requires `--definition`, `--closure` and
`--defeat` and refuses without them. The first stage of the circuit is the one
stage the machinery enforces on entry.

### 2 · Request - NO MECHANISM

`python scripts/sov_session.py console` reports:

```
Work console (projection; grants no authority)
  concern: concern:session/session-6352b5
  source session: (none)
  sources: (none)
  queues: (none)
```

Nothing can be requested into the node. Work reaches a session because a human
tells the session what to do, which is the oral history `P15-X1` forbids. The
console is built and correct; it projects an empty set because no producer
exists behind it.

### 3 · Agenda - NO MECHANISM

No agenda object exists. `scripts/sov_ticket.py` reads a ticket export produced
by the GitHub registrar under `adapters/github/`, so a request does have a
durable coordination form. Nothing projects those tickets into a session's
console as available work, so the two ends do not meet.

### 4 · Queue / Custody / Lease - PARTIAL, AND DISCONNECTED

The lease was taken and is live:

```
lease:concern-schematically-golden-rendered-text HELD
urn:soveraeign:principal:instance:session-6352b5 live 0%
```

Custody boards are built. Leases are built. They cannot see each other:

```
$ grep -c "lease" scripts/sovcustody/board.py scripts/sovcustody/model.py
scripts/sovcustody/board.py:0
scripts/sovcustody/model.py:0
```

and the lease record carries no custody identifier. So a live lease on a
concern is invisible to the board that holds the obligation, and the board
cannot answer who is carrying a member right now. The circuit names Queue,
Custody and Lease as one stage; the implementation has them as two systems with
no edge between them.

### 5 · Participant Context - PARTIAL, IDENTITY ASSERTED NOT ESTABLISHED

`python scripts/sov_session.py register` reports:

```
principal: unidentified - no registered principal named principal:session-6352b5
```

`sov_lease.py take` then minted `urn:soveraeign:principal:instance:session-6352b5`
and held the lease under it. A lease can be held by a principal the node does
not know. The identity axis is asserted at the lease, not established at the
registry, and nothing compares the two.

Capability and authority were not resolved separately, because nothing required
either: no grant was named or checked to take a lease whose work lands in a
different repository. The lease accepted `--effect-ceiling RECORD_LOCAL` and
carries no field for which node or repository the effect reaches.

### 6 · Execution - IN PROGRESS

Carried by a participant launched with the definition, closure condition and
defeating condition only, and nothing from the session that holds the lease.
Whether a stranger can carry this work from the artifact alone is part of what
is being measured.

## Findings so far

| # | Stage | Finding |
| --- | --- | --- |
| F1 | Request | No producer feeds the work console. Work enters a session only as oral history. |
| F2 | Agenda | No agenda object. Tickets exist in the GitHub adapter and reach no session. |
| F3 | Custody / Lease | Custody boards and leases share no reference in either direction. A live lease is invisible to the board holding the obligation. |
| F4 | Participant Context | A lease mints and accepts a principal the session registry reports as unidentified. |
| F5 | Participant Context | No grant was required to lease work whose effect lands in another repository, and the lease records no node or repository for its effect. |
| F6 | Definition | Positive: the definition, closure and defeating condition are required at lease time and refused without. |

Findings are appended as the lap continues.

### 6 · Execution - CARRIED, WITH ENVIRONMENT FRICTION

A participant was launched holding the definition, the closure condition and
the defeating condition, and nothing from the session that holds the lease. It
carried the work from the artifact alone. For this payload the premise under
`P15-X1` held: a stranger did not need oral history.

It reported one environment obstacle: `playwright` was not importable although
the browser directory is populated, so it installed the pinned version from
`requirements-dev.txt`. Nothing in this node's orientation layer names that
step, and the next fresh participant meets it first.

### 7 · Operational Record and report - NO MECHANISM

The execution converged into no Record. What exists is a markdown report the
participant wrote to a path its launcher named. No service received it, no
event was emitted, and nothing addresses it.

The lease that holds the concern recorded nothing about the work done under it:

```
readings: []
pressure: 0.0
state: HELD
```

`python scripts/sov_lease.py draw` exists precisely to "record what a lease
consumed or produced" and nothing called it, because the participant doing the
work was never told a lease existed. Holding a concern and doing the work under
it are two disconnected acts.

### 8 · Independent perspective formation - IN PROGRESS

Two readings launched in parallel on different subjects: one on the work, one
on the participant's carrying of it. Neither built the change. Neither can see
the other.

### 9 · Frozen Findings - CONTRACT COMPLETE, NOTHING IMPLEMENTS IT

`contracts/finding.schema.json` specifies a Finding: subject, evaluator, scope,
record projection, claims, evidence and counterevidence addresses, input
findings, authority effect, settlement effect, supersedes - and it **requires**
`frozen_at`.

No Finding has ever been produced. Across the whole tree, `finding_schema`
appears in exactly two files:

```
./contracts/finding.schema.json
./conformance/fixtures/commissioning/evidence-contract-cases.json
```

The schema and one test fixture. No instance, and no code that constructs one.
The only writer of `frozen_at` anywhere is `scripts/sovland/candidates.py`,
which freezes repository candidates, a different object.

`conformance/commissioning.py` grades `P15-Q2.3` by reading
`projections_frozen_before_sharing` as a boolean out of an `observed` dict. The
freeze is therefore asserted to the oracle, never performed by a mechanism and
never recorded. This is the same shape as the observer-independence problem
`decisions/0104` describes: the property is declared by whoever is being graded.

The two readings in this lap are frozen only because they were launched in
parallel and their launcher refuses to relay between them. That is a discipline
of the launcher, not a property of the system. `P15-X2` requires readings that
freeze before comparison, and its custody reads two members at `VERTICAL_SLICE`.

## Findings, continued

| # | Stage | Finding |
| --- | --- | --- |
| F7 | Execution | Positive: a participant carried the work from the definition, closure and defeating condition alone, with nothing from the holding session. |
| F8 | Execution | `playwright` is not importable despite a populated browser directory; the orientation layer does not name the install step a fresh participant needs. |
| F9 | Record | The execution converged into no Record. The report exists only as a file at a path its launcher chose. |
| F10 | Record / Lease | The lease recorded nothing about the work done under it. `sov_lease.py draw` exists and nothing called it; the executing participant was never told the lease existed. |
| F11 | Frozen Findings | `contracts/finding.schema.json` is complete and requires `frozen_at`. No Finding instance exists anywhere in the tree and no code produces one; `finding_schema` appears only in the schema and one fixture. |
| F12 | Frozen Findings | The freeze `P15-X2` requires is asserted to the oracle as a boolean and performed by nothing. In this lap it is a discipline of the launcher, not a property of the system. |

### 8 · Independent perspective formation, partial - THE SUBJECTS COLLAPSED

The first of the two readings returned. Before its content is used, one
property of the stage itself is already visible and does not depend on what it
concluded.

The reading commissioned on the participant's *carrying* of the assignment
spent a substantial part of its effort reproducing the closure condition of the
*work*: it re-ran the suite, reproduced the failure at the regression commit,
and ran a counterfactual the builder had not run. That counterfactual was
valuable and independent. It is also the other reading's subject.

`P15-X2` requires that "work quality and participant conduct are judged as
different subjects". `contracts/finding.schema.json` has `subject` and `scope`
fields for exactly this. Nothing implements them, so nothing scoped either
reading to its subject, and the two collapsed toward the same one. A comparator
that receives two readings of the same subject cannot attribute a defect to
work rather than participant, which is the discrimination the clause exists to
make.

This is not a defect in the reading, which was asked an open question and
answered it well. It is the absence of the mechanism that would have held it to
its subject.

| # | Stage | Finding |
| --- | --- | --- |
| F13 | Independent perspective formation | Nothing scopes a reading to its subject. Commissioned on the participant, one reading spent much of its effort on the work. The `subject` and `scope` fields exist in the Finding contract and are unimplemented, so the discrimination `P15-X2` requires is left to the prompt. |

### 10 · Comparison, repair, decision - WORKED, BY DISCIPLINE

Both readings returned frozen, having been launched in parallel with nothing
relaying between them. They reached different subjects' verdicts - the work
`MET WITH QUALIFICATION`, the carrying `CARRIED WELL` - and produced defect
sets that barely overlap. They corroborated on the one thing both tested: each
independently ran the counterfactual of the nine pre-existing corpus documents
at the regression commit without the new anchor, and both got a pass, which is
what makes the corpus extension a build of the check rather than a rig of it.

That is the discrimination `P15-X2` exists to produce, and it was produced. By
arrangement, not by mechanism: the two subjects, the parallel launch and the
refusal to relay were the launcher's discipline and are recorded nowhere.

Attribution, which is the part a comparator owes:

| Defect | Attributed to | Reasoning |
| --- | --- | --- |
| A caption at `opacity: 0` passes the check | The **definition**, not the work | The closure condition said "compares rendered text" and the work does exactly that. The concern pull request #32 recorded was broader - a check that "would have caught the caption regression" - and an invisibility regression is a different class. The definition was written narrower than the concern and the work satisfied the definition. |
| The commit subject says "compared by what it draws" | The **work**, minor | What exists compares text, not what a viewer sees. Naming, disclosed in the report body and overstated in the subject line. |
| The anchor's load-bearing property was unguarded | The **work**, root cause in the **product** | `src/10-model.js` normalises `labelMode` on load, so any open-and-resave silently disarms the demonstration. |
| The report misstates reciprocity-mark coverage | The **participant**, minor | Reporting accuracy; the reading corrected it against the artifact. |
| Report file list, an eight-for-nine slip, residue in the repository root | The **participant**, minor | Reporting hygiene. |

**Decision.** Closure accepted with qualification. The anchor defect is
repaired in the payload repository at `e51b999`, proved by writing the
disarming value in, reading the refusal, and restoring. The opacity defect is
recorded as a residual and attributed to the definition rather than carried as
a repair, because widening from rendered text to rendered visibility is a
different concern with a different cost, and inventing that scope inside a
reconnaissance run would be the scope creep the contract names.

One defect was found in the repair while proving it, and removed before commit:
the first guard also refused an authored label, which fails the correct
document. Running the defeating case before trusting the change caught it.

### Three more findings, from carrying the repair

**Independence held at the participant and broke at the environment.** The work
reading recorded that `playwright==1.57.0` was already installed in the
container by the builder. Both readings ran inside an environment the build had
mutated. Independence was arranged between participants and unmeasured between
contexts, which is exactly the axis `decisions/0104` names, and nothing checks
it.

**Repairing on a finding invalidates the finding, and nothing re-arms it.**
Both readings are frozen against the subject as it stood before the repair. The
repair moved the subject. Nothing marks a finding stale when its subject moves,
and no stage exists to re-form a reading after a repair. The circuit draws
Comparison to Repair to Settlement as forward motion with no edge back to
observation, so a repaired defect is settled against evidence that no longer
describes the thing being settled. This is the same hazard `OPEN-SEAMS.md` S30
records for repository candidates, met here at a different object.

**Cleanup and work share a namespace.** The payload suite writes its fixtures
into `tests/`, the directory holding its own source. Restoring the tree after a
run destroys the change under test. That is not a hypothetical: this session
ran `git checkout -- tests/` to clear run artifacts and silently reverted its
own repair, discovering it only because the commit reported nothing staged.

| # | Stage | Finding |
| --- | --- | --- |
| F13 | Independent perspective formation | *Refined.* The two subjects collapsed in **effort** - the participant reading spent much of itself reproducing the work's closure - but not in **verdict**: the two returned different subjects' conclusions and near-disjoint defect sets. Nothing scoped either reading; the separation held because the prompts named different subjects. |
| F14 | Independent perspective formation | Independence was arranged between participants and violated between contexts. Both readings ran in a container the build had mutated, and nothing measures the context axis `decisions/0104` names. |
| F15 | Comparison / repair | A repair invalidates the findings it answers, and the circuit has no edge back to observation. Nothing marks a finding stale when its subject moves. S30's hazard, met at a different object. |
| F16 | Cleanup | The payload's suite writes fixtures into the directory holding its source, so restoring the tree after a run destroys the change under test. Observed by doing it. |

Positives so far, kept explicit because a trace of only breakage is not a
reading: the definition stage is enforced, a stranger carried real work from the
artifact alone, and two readings on different subjects produced the
discrimination `P15-X2` asks for.

### 11 · Settlement - THE STRONGEST MECHANISM IN THE CIRCUIT

Closing the lease at `WITNESSED`, citing both readings by address, was refused:

```
REFUSED UNWITNESSED_STANDING_CLAIM:
lease:concern-schematically-golden-rendered-text claims WITNESSED with no
witness lease held by a principal other than
urn:soveraeign:principal:instance:session-6352b5
```

That refusal is correct and it is the best behaviour found anywhere in this
lap. It does not accept a citation, a name, or an evidence address as witness.
It requires a witness **lease**, held by a **different principal**. A claim
cannot be talked into standing.

It also exposes the gap that made the refusal unavoidable. Two genuine
independent readings existed, formed by participants that did not build the
change and could not see each other. Settlement could not see either of them,
because they were formed as launched participants and not under witness leases.
`python scripts/sov_lease.py helper` exists precisely to "recruit a helper or
witness under a lease" and nothing connected the readings to it - the same
disconnection as F10, met at the witness end instead of the execution end.

So a lap can produce exactly the evidence the clause asks for and still be
unable to settle above `BUILT`. The lease was closed at `BUILT`, which is what
the record can honestly carry.

### 12 · Cleanup and Receipt - CLEANUP UNASKED, RECEIPT UNPRODUCED

The close accepted `--receipt receipt:lap/golden-rendered-text` and four
`--evidence` addresses. The retained lease record is:

```
lease: lease:concern-schematically-golden-rendered-text
holder: urn:soveraeign:principal:instance:session-6352b5
state: COMPLETED
pressure: 0.0
readings: []
```

The closed lease is retained, which is right. What it retains is liveness: who
held it and that it completed. The receipt identifier, the four evidence
addresses and the standing are not in it. The lease is a record that work
happened, not a record of what the work produced or what supports it.

No receipt object was produced. `contracts/receipt.schema.json` requires
fifteen fields. Searching the tree for a top-level object carrying all fifteen
finds exactly one file, `bindings/mcp/observations/journey-02-receipt.json`, a
binding demonstration. No operation in this repository has ever emitted a
receipt, and settlement did not emit one here.

Cleanup was discharged by hand: a scratch branch retired, worktrees pruned, run
artifacts restored. Nothing asked for it, nothing checked it, and the lease
closed without reference to it. `contracts/custody.schema.json` carries a
`cleanup_obligations` field for this and the settlement path does not read it.

| # | Stage | Finding |
| --- | --- | --- |
| F17 | Settlement | Positive, and the strongest mechanism in the circuit: `WITNESSED` is refused without a witness lease held by another principal. Citations, names and evidence addresses do not buy standing. |
| F18 | Settlement | Two genuine independent readings could not be seen by settlement, because nothing connects a launched reading to a witness lease. `sov_lease.py helper` exists and nothing routes to it. A lap can produce the evidence a clause requires and still be unable to settle above `BUILT`. |
| F19 | Receipt | Settlement accepts a receipt identifier and evidence addresses and retains neither. No operation in this repository has ever produced a receipt: one object in the tree satisfies `contracts/receipt.schema.json`, and it is a binding demonstration. |
| F20 | Cleanup | Cleanup obligations were discharged by hand, unasked and unchecked. `custody.schema.json` declares `cleanup_obligations` and the settlement path does not read it. |

### 13 · Discovery - FOUND, BY PROSE, AND NEARLY NOT AT ALL

A participant with no history was sent to this node and asked to find the most
recently settled work, reconstruct why it stands, reach the capability and use
it. It succeeded. The path it took is the finding.

Seventeen commands, four dead ends, two points where the trail nearly went
cold. The three obvious settlement stores each failed differently:

- `.local/acceptance/ledger.ndjson`, which `STATUS.yaml` line 88 names as the
  acceptance record, **does not exist**; `.local/` is gitignored.
- `.local/landing/ledger.ndjson` holds twelve rows shaped exactly like
  landings, all carrying `grant:test`, branch `work` and one timestamp. They
  are fixtures. Nothing marks them as fixtures. The participant caught it and
  recorded that reporting one would have been a false claim.
- `witness/` and `reports/observations/` top out before the work.

What actually carried the trail was a **prose report a participant wrote by
hand** - this file. `python scripts/sov_lease.py status` returns an empty set
for the very lease that is the answer, because it projects live leases only.
The real store was found in a source docstring.

That store is `.git/sov-sessions/leases.ndjson`. It is inside the git
directory: no clone carries it, no commit can contain it, and no reader outside
this container can reach it. `P15-X3` requires that a fresh participant
discover the accepted result "without builder-private state". The settlement
record **is** builder-private state, by construction. A participant working
from a fresh clone would find no settlement record at all, and the evidence
addresses point into a second repository a clone would not have.

### 14 · Use - REACHED AND USED, AND THIS IS THE SECOND STRONG RESULT

The participant reached the capability in the other repository and ran it:

- at head, `PASS golden rendered text QA (10 documents, 101 text nodes)`;
- the registered suite, `RC QA PASS: 37 suites + 17 JS syntax checks`;
- the defeating condition reproduced at the regression commit, exit 1, failing
  on exactly the three captions;
- the repair exercised by writing the disarming value in and reading the guard's
  refusal;
- the disclosed residual confirmed: `.component-label { opacity: 0 }` makes
  every caption invisible and the suite still passes.

Everything the record claimed was reproduced by a participant that built none
of it. Where the record was honest it held up, including about its own
weakness.

It also met `F8` head on. `CHROMIUM_PATH` appears in no document in either
repository, and its first run died on a browser-revision mismatch. It recovered
by reading `tests/browser_runtime.py`. The finding this lap recorded one stage
earlier was met, unfixed, by the next fresh participant one stage later. It
reproduced `F16` by accident as well.

| # | Stage | Finding |
| --- | --- | --- |
| F21 | Discovery | The only path to the settled result was hand-written prose. `sov_lease.py status` returns empty for the lease that is the answer; the store is named only in a source docstring. |
| F22 | Discovery | The settlement record lives in `.git/sov-sessions/leases.ndjson`, inside the git directory. No clone carries it. `P15-X3` requires discovery without builder-private state and the record is builder-private by construction. |
| F23 | Discovery | `STATUS.yaml` names an acceptance ledger that does not exist, and the landing ledger holds twelve fixture rows shaped like real landings with nothing marking them as fixtures. A reader nearly made a false claim from them. |
| F24 | Use | Positive, and the second strong result: a participant that built none of it reached the capability and reproduced every claim, including the disclosed residual. |
| F25 | The loop | `F8` was met by the next fresh participant one stage later, unfixed, and cost it its first run. Recording a finding changes nothing about the node. |

## 15 · Experience, and 16 · Synthesis

Twenty-five findings. The pattern under them is not that pieces are missing.
Most pieces are built, and several are good: the definition stage refuses work
without a closure and a defeating condition, settlement refuses a claim that
has no witness lease held by another principal, and a stranger both carried
real work and later found and used it from the artifact.

What is missing is that **the participant circuit and the Record are two
parallel worlds**. `services/` converges on the Record Service - Gateway,
Registry, Host, Console, Observation and Asset all use it, and parts of
`scripts/` do too. The spine of the circuit does not. `scripts/sovsession/store.py`
writes sessions and leases to `.git/sov-sessions/`, a location no clone carries
and no commit can contain.

Every finding in this trace is a symptom of that split:

- Nothing can be requested into the node because there is no committed queue
  object to request into (`F1`, `F2`).
- Custody cannot see a lease, and a lease cannot see its own execution or its
  witnesses, because there is no shared record the three write to (`F3`, `F10`,
  `F18`).
- No Finding and no receipt has ever been produced, though both contracts are
  complete, because there is nowhere for either to land (`F11`, `F19`).
- Discovery fails from a clone because the only durable trace is prose
  (`F21`, `F22`).

The horizon document says to ask what lower-level governed primitive is missing
from the composition, and to add the small primitive rather than the
institution. The answer this lap produces is not a circuit reader, an agenda
service or a judgement agent. It is that the circuit's spine should write to
the Record the rest of the node already shares.

## 17 · Candidate next Definition

**Unprivileged.** It gains no standing from having been generated by this run,
from the evidence behind it, or from the run having reached this stage. It is
input to a Proposal, refusable in full.

> Route the session and lease store to the Record Service, so that taking a
> lease, drawing on it, recruiting a witness under it, and closing it emit
> addressable records in the same append-preserving Record that `services/`
> already converges on, instead of to `.git/sov-sessions/`.

What it would change, each traceable to a finding above: settlement becomes
discoverable from a clone (`F21`, `F22`); the receipt the close already accepts
has somewhere to land (`F19`); a witness lease becomes visible to settlement, so
readings that exist can be seen (`F18`); custody can join to leases (`F3`); and
a queue projection has a substrate to project from, which is the precondition
for stages 2 and 3 existing at all (`F1`, `F2`).

What would defeat it: if the split is deliberate - if session and lease state is
meant to be host-local scratch and the durable record is meant to be written
separately by an explicit act - then this proposal is wrong and the missing
primitive is that explicit act instead. Nothing found in this lap settles which,
and the root seat owns that question.

Evidence basis, preserved: this report; `FINDING-WORK.md` and
`FINDING-PARTICIPANT.md` and `LAP-EXECUTION-REPORT.md` in the schematically
repository at `d406790`; `reports/2026-09-08-commissioning-circuit-discovery.md`; the payload
at `schematically@e51b999`.

## Closing count

Seventeen stages. Three have a working mechanism that did its job: Definition,
Settlement, and Use. Two more worked by the discipline of whoever set the run
up rather than by any mechanism: independent perspective formation, and
comparison. Three have no mechanism at all: Request, Agenda, and the
convergence of execution into a Record. Three have a complete contract that
nothing implements: Finding, freeze, and subject scoping. The rest are built
and disconnected.

No clause advanced. Nothing here is witnessed. `P15-X5` still carries two
tickets at `ROOT_POINT` and this run is not a member of it, because an ungraded
lap is not the witnessed circuit the clause requires. What this run produced is
the trace the reader was always going to need, and a candidate Definition that
nobody has to accept.
