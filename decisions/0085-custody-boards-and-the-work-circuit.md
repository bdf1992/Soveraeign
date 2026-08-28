# 0085 · Custody, the work circuit, and the Phase-I terminal

Status: `OWNER-DIRECTED · CONTRACT WORDING PROPOSED`

Bdo ruled on Phase I on 2026-08-27. This record implements that ruling and adds
the contracts it needs. The ruling itself is his; the sections below restate it
only where a later reader would otherwise have to go back to a conversation.

> Phase I produced substantial and useful system ground, but it did not earn the
> exit that `PRD.md` defines. The central lesson is not that too little was
> built. It is that the repository optimized the wrong unit of progress.

## The terminal

`phase_execution_status: CLOSED`, `phase_acceptance_status: NOT_EARNED`.

Two readings, not one. The window is over, and the exit was not earned. Nothing
here narrows the definition to fit the evidence and nothing promotes partial
evidence into acceptance. `contracts/phases.json` records it, pinning `PRD.md`,
`ROADMAP.md` and `SPEC.md` by digest so a later reader can prove the exit they
are checking is the exit the phase opened with.

| Clause | Verdict |
| --- | --- |
| `PHASE-I-X1` every normative predicate has a positive and defeating fixture | `NOT_EARNED` |
| `PHASE-I-X2` fixtures run through one human and two model bindings | `NOT_EARNED` |
| `PHASE-I-X3` independent observation can reconstruct the receipts | `NOT_EARNED` |
| `PHASE-I-X4` open judgement calls are visible | `SUBSTANTIALLY_EARNED` |
| `PHASE-I-X5` the owner ratifies operational acceptance | `NOT_REACHED` |

`SUBSTANTIALLY_EARNED` is never rounded up. X4 falls short of `EARNED` because
29 owner-routed questions name no hold reason from the seven
`contracts/acceptance-policy.json` declares exhaustive: the router and the policy
do not speak one vocabulary. `NOT_REACHED` is distinct from `NOT_EARNED` — X5
was never attempted and never refused, and recording it as unearned would suggest
otherwise.

Every unmet clause names the exit custody that inherits it. Carried forward is
not a terminal.

## What went wrong, in one sentence

The repository had requirements and commits and no durable object between them
saying: *this bounded initiative serves these exact exit predicates; this seat
carries it until this target is reached; this separate seat settles it; and this
evidence would defeat a false claim of closure.*

The measured shape of that absence: 401 commits, 78 decision records, 60
contracts, 68,843 lines of Python, and `python scripts/sov_f2_gate.py` reading
**0 of 44** credited predicate pairs for the whole phase. Nothing ever refused
because of that number.

## Decision

### 1. Custody, and it is hierarchical

`contracts/custody.schema.json`. `GROUND-001` already opens with "an enterprise
keeps custody of its memory, its authority, its operation and its continuity";
this is that word applied to work in progress. A custody is not a seat, which is
an authority position; not a work lease, which expires; not an office, which
groups capabilities.

An earlier draft of this record proposed ten flat peers. Bdo refused it, and
correctly: the ten mixed exit obligations, service work, coordination cleanup and
a future product capability as equals, which reproduces at a new layer the
failure the layer was built to fix.

| Object | Terminal |
| --- | --- |
| Phase | accepted, closed incomplete, or cancelled |
| Exit custody | one clause earned, or explicitly closed unmet |
| Delivery custody | target predicates evidenced and settled |
| Concern | landed or explicitly retired |
| Work lease | completed, failed, released, expired, superseded |
| Board | never independently stored or settled |

An `EXIT` custody holds exactly one phase exit clause and has no parent. A
`DELIVERY` custody names the exit custody it serves, or is marked explicitly
outside the phase exit with a reason. **If an initiative cannot name the exit
custody it serves, it is not Phase-I work.** Naming neither, or both, is refused
by `FLAT_CUSTODY`.

`contracts/custodies.json` now carries 5 exit custodies mirroring the five
clauses, 8 delivery custodies beneath them, and 3 marked explicitly outside:
`trunk-reconciliation` and `seam-drain` as coordination cleanup the close
sequence requires, and `session-as-node` as a future product capability.

### 2. Three axes, kept separate

The circuit — `ROOT_POINT → VERTICAL_SLICE → HORIZONTAL_SURFACE →
EXPLODED_SURFACE → CAPABLE_NODE` — says how much of the system object has been
drawn. Standing — `OPEN → BUILT → WITNESSED → RATIFIED` — says how well a claim
about it is evidenced. Work state — `CANDIDATE → READY → CLAIMED → IN_PROGRESS →
PRESENTED → LANDED → RETIRED` — says where it sits in the queue.

They must not become one ladder, and every member record carries all three, so
`CAPABLE_NODE` is never read as "done". Most initiatives should not target
`CAPABLE_NODE`: a contract mapping may honestly stop at `HORIZONTAL_SURFACE`, a
service boundary at `EXPLODED_SURFACE`. A session becomes a node only after
admission, typed authority, a parent relation, receipts and outside observation.
Registration alone makes it addressable host plumbing.

Each stage's defeating case is a defect that actually happened here:

| Stage | Defeat | The live instance |
| --- | --- | --- |
| `ROOT_POINT` | `ROOTLESS_POINT` | 21 unroutable epic issues |
| `VERTICAL_SLICE` | `OPEN_PATH` | `adapters/ollama/invoke.py` grades its own output |
| `HORIZONTAL_SURFACE` | `SURFACE_OVER_OPEN_PATHS` | — |
| `EXPLODED_SURFACE` | `ADVERTISED_NOT_ENFORCED` | 9 console operations declaring an authority and checking none |
| `CAPABLE_NODE` | `SELF_WITNESSED_NODE` | node identity inferred from a host session id |

### 3. Definition of ready, definition of closed

`contracts/concern-admission.json`. Twelve fields resolve before a concern leaves
`CANDIDATE` for `READY` — roots, custody, holder and settler, service boundary,
effect class and authority, entry and target stage, closure check, defeating
case, dependencies, estimate range and basis, isolation, cleanup obligations. An
item missing one stays visible inventory; it does not enter work in progress.

Six layers demonstrate closure: `BUILT`, `ATTACKED`, `OBSERVED`, `LANDED`,
`SETTLED`, `CLEANED`. **Landed is not closed and cleaned is not optional.** A
concern that emitted a branch, an issue and a worktree and retired none of them
has moved its cost onto whoever comes next.

Three roles, three different endings: a worker presents an evidenced tree; the
branch holder merges or retires it and clears its integration inventory; the
custody holder stays accountable until the target predicate and its settlement
evidence close.

### 4. Estimation, with maturity tied to circuit position

`contracts/estimation.json` declares thirteen dimensions across five kinds,
including the coordination emissions Bdo named — branches, pull requests and
issues opened — because a run that emits inventory without approaching closure
should become visibly pressured.

An estimate is only as firm as the stage of the thing it sizes.
`DISCOVERY_ENVELOPE` at a `ROOT_POINT`, `WIDE_RANGE` at a `VERTICAL_SLICE`,
`COMMITTED_RANGE` at `HORIZONTAL_SURFACE` and above. Committing early is refused
by `OVERCOMMITTED_ESTIMATE`. A wide range is not a worse estimate than a tight
one; it is a truer report of what is known.

Every graded dimension names where its measured actual is read from. `points`
declares itself ungraded and says why — nothing measures a story point after the
fact, so grading it would compare an estimate to itself. Dimensions stay
separate: one computed from others is refused by `SYNTHETIC_SCORE`, because
combining unlike units destroys the only reading the split was for.

### 5. A board is derived and is never a second System of Record

`python scripts/sov_custody.py board <id>` computes from the custody, the
circuit, and the live tree. Progress reads from the **least-drawn** member, not
the frontier: a custody is only as far along as its laggard.

## Defaults taken

- **The five exit custodies mirror the five clauses exactly**, one each. Two
  custodies on one clause is refused by `DUPLICATE_EXIT_CLAUSE`, because then
  neither is accountable.
- **`seat:session-control` holds all sixteen; `seat:root` settles all sixteen.**
  Overturned by a custody whose real holder is a seat that does not exist yet.
- **Estimates are ranges from named bases, several declared as guesses.**
  Overturned by the first measured actual landing outside its range.

## Consequences

- `python scripts/sov_custody.py reconcile` walks the phase exit clause by
  clause against the custody holding each, and refuses a phase whose pinned
  definition has moved.
- **119 of 140 derived work items fall inside no custody**
  (`orphans --kind ITEM`); **22 of 25 open seams are held by nobody**
  (`orphans --kind SEAM`). Both are admissible and both are newly visible.
- The phase gate is still not on the ordinary landing path. `scripts/sov_land.py`
  should recompute it before claiming phase progress, and this record does not
  make that change: two live sessions hold `scripts/sovverify/checks.py` with
  uncommitted work, and editing it would clobber theirs.
- `STATUS.yaml` is owed `phase_i_status`, `custody_status`, `work_circuit_status`
  and `estimation_status`. It is not edited here; three live sessions held it
  while this was written.

## Evidence

- `conformance/fixtures/custody/circuit-cases.json`: 44 cases across six judges
  (circuit, estimate, custody, collection, registry, phase). Every one of the 25
  declared refusals is reached by a case that fires it.
- `scripts/tests/test_custody_boards.py`: 58 tests over circuit order, path
  closure, surface composition, both directions of the discovery-enforcement
  divergence, node witness, the custody hierarchy, the phase terminal, estimate
  maturity, and board derivation.
- `python scripts/sov_custody.py selfcheck` runs the corpus by hand.
- Standing is `BUILT_SELF_TESTED_NOT_WITNESSED`.

## What still waits on Bdo

1. **Ratifying the terminal.** `CLOSED / NOT_EARNED` is recorded as his ruling
   and the record is `PROPOSED`. Settling it is the root seat's.
2. **The successor campaign's scope.** `succeeded_by` is deliberately null: the
   next phase is scoped after the residual custodies are attached, not before.
   His nomination is the Record path as one thin qualification slice.
3. **Ratifying the four contracts.** `STATUS.yaml` fields are owed once he rules.

## Source and authority

- Bdo's Phase-I retrospective and custody ruling, 2026-08-27 — the terminal, the
  hierarchy, the three axes, the definition of ready and closed, the estimate
  maturity table, the ten operating rules, and the close sequence
- `AGENTS.md` closure ownership, self-direction, change protocol, implementation
  order, directory boundaries
- `PRD.md`, `ROADMAP.md`, `SPEC.md` — the exit this record pins by digest
- `contracts/product-ground.json` — GROUND-001 custody, GROUND-003 typed
  authority, GROUND-010 a report is not an observation, GROUND-012 judgement is
  scarce, GROUND-014 effort resolves to intention, GROUND-016 a node is whole at
  any size
- `decisions/0055-closure-ownership.md`, `decisions/0056-participation-substrate-leases-and-budgets.md`,
  `decisions/0039-the-node-surface.md`, `decisions/0084-peer-network-and-cumulative-evidence.md`
