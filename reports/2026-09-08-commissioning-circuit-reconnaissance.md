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
