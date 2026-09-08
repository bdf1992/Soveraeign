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
