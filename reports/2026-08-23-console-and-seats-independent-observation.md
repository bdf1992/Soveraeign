# Console continuity and seat etiquette, observed from outside, 2026-08-23

Status: `OBSERVED INDEPENDENTLY · NOT WITNESSED · NOTHING RATIFIED`

Two builds landed in this working tree without an independent pass: the Console
Service continuity record path (`decisions/0036`) and the seat etiquette checker
(`decisions/0035`). Both carried the builder's own tests and nothing else.
`AGENTS.md` holds that a build cannot witness itself, so this session — which
wrote neither — took the other path and looked.

This report records what was observed. It proposes at most `BUILT -> WITNESSED`
and settles nothing. Only Bdo ratifies.

## What independence meant here

Independence is a claim that has to be specific, or it is decoration.

For the Console Service, the participant's own tests import
`soveraeign_console_service`, drive the Python API, and project records through
the service's own `contract.py`. `scripts/witness_console.py` does none of those
things. It reaches the service only as a subprocess through `cli.py`, so it never
imports it. It reconstructs the declared record by projecting the emitted payload
onto each schema file's own `properties` keys, so the projection under test is
rebuilt from the contract rather than borrowed from the code. And it joins each
post to its receipt by scanning the journal for a `COMMITTED` receipt naming that
entry, rather than asking the console who committed it.

For the seat etiquette, `scripts/tests/test_seat_etiquette.py` runs the fourteen
prepared defeating fixtures. That proves the checker catches what it was shown.
`scripts/witness_seats.py` asks the different question: does the checker read
`contracts/seat-etiquette.json`, or does it recognise its own fixtures? Every case
starts from a positive fixture the checker admits and breaks it in a way the table
forbids and no fixture covers.

One limit worth naming plainly: independence here is scoped to the actor and the
path, not the model. A sibling session of the same model built this code. The
repository's rule is actor-scoped and this session performed nothing on either
artifact, so the observation stands under the rule as written. Whether that rule
should also be model-scoped is not this report's to settle.

## Console Service continuity path

`python scripts/witness_console.py`, 20 of 20 observations held.

```text
an ungranted operator is refused                NO_LIVE_GRANT
a channel validates
a thread validates
a human session validates
a model session validates
the journal reconstructs outside the console    10 committed addresses
a human post validates
a human post has a committed receipt            entry_363b1e1a...
a model post validates
a model post has a committed receipt            entry_faf14bf1...
identical bodies differ only in attribution     stray=[]
both actor kinds reach one content address      sha256:0de0414c5b9f401ec
a model claim without a proposal is refused     CLAIM_WITHOUT_PROPOSAL
the same claim from a human is admitted
live grants are readable                        3 live
a revoked grant refuses the next post           NO_LIVE_GRANT
revocation does not unmake committed posts      3 posts remain
the read path declares itself a projection      record-service-journal
the projection is stable across rebuilds
session-context carries what landed while away
```

Three of these are worth calling out because they are the claims the charter
rests on rather than mechanics.

**Parity is structural, not promised.** A human turn and a model turn carrying
identical bytes were posted into one thread. Every field that differed was
attribution — the post id, journal entry, actor, session, binding, timestamp. The
set of unexplained differences was empty, and both reached one content address.
`PRD.md` PROD-I-3 asks that a human post and a model post be one crossing through
the same record; through the CLI, they are.

**Authority is checked at the operation, not held in a process.** An operator with
no grant was refused before any record existed. A grant was recorded, the
operation admitted, the grant revoked, and the next operation refused with
`NO_LIVE_GRANT`. The posts already committed under that grant survived the
revocation intact, which is the behaviour `AGENTS.md` requires: a counter-record
withdraws admission going forward and never unmakes what was already committed.

**The read path admits it is a projection.** `read-thread` returns
`authoritative: false` and `rebuilt_from: record-service-journal`, and the journal
reconstructs to the same records when read directly by the Record Service without
the console in the path.

## Seat etiquette checker

`python scripts/witness_seats.py`, 16 of 16 observations held. Every positive
fixture is admitted as written, and each of the following was caught with a defect
naming the rule:

- an orchestration seat speaking `ATTEST`, a work seat speaking `DISPATCH`, and
  the root seat speaking `ASK` — three acts absent from those seats' `may` lists,
  none of them covered by a fixture;
- an `AGGREGATE` claiming `PERFORMED` and a `HOLD` claiming `PERFORMED`, against
  the relation each act requires;
- an `ATTEST` proposing from `OPEN` and a `REPORT` proposing to `WITNESSED`,
  against the standing ceiling each act carries;
- a statement from an unregistered seat, and one addressed to an unregistered
  seat.

The carriage duty needed a different approach. Every positive fixture carries
`judgement_items` and `residuals`; none carries a `dissent` or a `stall`, so the
duty was declared over four kinds and exercised over two. Injecting both into the
originating `REPORT` and forwarding them showed the full conversation admitted,
and dropping either one at the orchestration hop or the control hop was caught by
item id. The duty holds over all four kinds. The corpus is what does not exercise
it.

## Residual

`contracts/fixtures/seat-message.fixtures.json` has no positive fixture in which a
dissent or a stall is carried through both aggregate hops to the root. The checker
handles both, as above, but that is now recorded here rather than in the corpus a
future change would be graded against. Two positive fixtures would close it. This
is a gap in coverage, not a defect in the checker.

## Repository checks, same working tree

Taken at 19:13 local, before the manifest change described below:

```text
python scripts/verify.py    PASS  18 checks, 282 tests in 1.2s against a 3.0s budget
python scripts/lint.py      PASS  405 text files, 119 Python modules, 0 named debt
python scripts/sov_kernel.py parity
                            PASS  7 correspondences, every participant refusal matches
python scripts/sov_capability.py check
                            PASS  57 capabilities, no defect, not stale
```

Re-run at 19:19, `python scripts/verify.py` **fails**, and the failure is not in
anything this report observed:

```text
FAIL: repository tooling tests   failures=2, errors=2
  test_capability_map.ReferenceMap  x4
  capability_map.py:161  TypeError: '<' not supported between instances of 'dict' and 'dict'
```

`scripts/sovkernel/capability_map.py` sorts `manifest["operations"]` as strings.
Service manifests were being changed to carry operation objects instead while these
checks ran — `services/record/contracts/service.json` and
`services/proofing/contracts/service.json` at 19:18, a new
`scripts/sovkernel/manifests.py` at 19:18, and
`contracts/fixtures/service-manifest.fixtures.json` at 19:19. That work is in
flight in another session and is not touched here. Both witness scripts above
still hold at 19:19; the console and seat observations do not read manifests.

The named module debt is gone: `services/asset/.../core.py` was split into
`store.py`, `authority.py`, `runs.py`, and `projections.py`, and
`KNOWN_MODULE_DEBT` in `scripts/lint.py` is now empty. The kernel parity check
drives the real Console Service against a temporary journal and matches its two
declared refusals, which is the same code path this report observed by hand.

## What this does not establish

- Nothing here reaches `WITNESSED`. That standing is proposed by an observation
  and settled by Bdo.
- Four of the five console surfaces in `services/console/CHARTER.md` — notifications,
  settings, dashboards, judgement requests — remain boundary with no implementation.
  Only the continuity path was built and only the continuity path was observed.
- No binding beyond the local CLI exists. `PRD.md` two-binding proof needs one
  human-facing binding and two materially different model bindings executing the
  same transitions; this observation covers one surface reached two ways.
- The seat etiquette itself is a proposal. The checker enforces the table; whether
  the table is right is `decisions/0035`, unruled.
- `OPEN-SEAMS.md` S17 stands: `INCOMPLETE_PROPOSAL` is declared in
  `contracts/kernel-transitions.json` and emitted by nothing.

## Note on the working tree

This observation was taken while another session was committing to the same
branch. `710f552` landed during the run, and files under `bindings/mcp/` and
`decisions/0039` were written while the checks were executing. The commands above
were run against the tree as it stood; a later tree may differ. Both witness
scripts are checked in and re-runnable, so the observation can be retaken rather
than trusted.
