# 0046 · The product canon: who the node is for and what it undertakes

Status: `PROPOSED · DRAFTED AT OWNER DIRECTION · ACCEPTANCE PENDING`

Drafted at Bdo's direction, 2026-08-24, answering Q1 of
`reports/2026-08-24-product-canon-attribution-discovery.md` with `ACCEPT, with a narrow
boundary`.

## Decision

Establish a product-canon layer between `CONTRACT.md` and `PRD.md`. It names four things
and nothing else: participants, what they are trying to accomplish, the promises
Soveraeign undertakes to them, and the principal journeys by which a promise becomes
usable.

- `CANON.md` owns the wording. Revision `CANON-1`, fifteen promises, thirteen journeys,
  ten participants.
- `contracts/product-canon.json` owns the identifiers and the joins.
- `contracts/product-canon.schema.json` owns the record shape.
- `scripts/sovkernel/canon.py` owns the join rules a schema cannot express.
- `python scripts/sov_canon.py check | trace | promises` reads it;
  `scripts/verify.py` runs `check`.

`PRD.md` was not modified. No requirement was restated, renumbered, or reparented.

## Why the layer had to exist

Nine `PROD-I` requirements carry 102 declared operations, one of them 32. Above the
requirement there was nothing: the words *journey*, *user need* and *product promise*
appeared zero times outside `lineage/`. A requirement had no parent and an operation had
no reason, so the question "why did we spend this?" had no artifact to answer it and the
question "what has been spent on this?" had nothing to aggregate against.

The evidence is in `reports/2026-08-24-product-canon-attribution-discovery.md`: NEED was
`MISSING` in twelve of thirteen probed journeys, and the `needs` line was inference for
all ten actor classes.

## What the canon is not

It states no requirement, selects no stack, sequences no work, and grants nothing. If it
acquires requirements, sequencing or architecture, it has become a second `PRD.md` and
should be struck. That is recorded in `CANON.md` as a defeating condition rather than as
an intention.

## Rulings

**1. A revision is immutable; an identifier is retired, never redefined.** A correction
or a change of product intent mints the next revision. An identifier whose meaning
changes is retired and a new one minted, and retired identifiers are never reused. This
is the rule `STATUS.yaml` already applies to the `O1`–`O22` docket: *"They are retired,
not reserved."*

The reason is attribution, not tidiness. If `PROMISE-03` could quietly come to mean
something else, every hour and token already recorded against it would silently change
what it had been spent on.

**2. Needs are named and not identified.** A participant states what they are trying to
accomplish in plain words. Needs get no identifier because they are not a join in the
chain from a promise down to a run, and an unnamed need is cheaper to correct than a
wrong one made canonical. Recorded under Defaults taken; reversible.

**3. A promise must be grounded in the governing set.** Every promise cites addresses
where its language already lives, and the schema requires at least one. A promise
grounded in nothing would mean the canon invented product intent rather than naming it.
Fourteen of fifteen are `DERIVED` from existing text; `PROMISE-01` is `OWNER_DIRECTED`.

**4. The join is checked, not asserted.** Every capability a journey names must exist in
`contracts/fixtures/capability-map.reference.json`. Every promise must be reached by a
journey or composed by a promise that is. A crossing a journey needs that no service
declares goes in `missing_capabilities` with a stated reason, and recording a declared
capability there is itself a defect.

This is the difference between a canon and a taxonomy. Nine defeats are declared and each
has a case in `scripts/tests/test_product_canon.py`.

**5. The wording and the record are held together by a check.** Every identifier in
`contracts/product-canon.json` must appear in `CANON.md`. Two places holding one fact
drift unless something checks them, which is the shape `decisions/0037` settled for the
two ticket readers.

**6. `PROMISE-01` is compound and says so.** Bdo's wording bundles bringing a
participant, discovering what it may do, working in the same world, inspecting the
result, and keeping custody. It composes `PROMISE-02` through `PROMISE-06` so that each
part is separately testable, and a reading of `PROMISE-01` answers for its parts.

**7. Proofing is a journey, not the definition.** Bdo's Q3 redirect: proofing may be the
first proving enterprise workflow and is not the first product promise. `PROMISE-13` is
one promise among fifteen and `JOURNEY-11` is the concrete journey that demonstrates
`PROMISE-01` in domain work rather than in the node's own governance.

**8. The seven resource words are named and kept apart.** `BUDGET`, `USAGE`, `COST`,
`WALLCLOCK`, `EFFORT`, `RESULT`, `VALUE`. A budget is a typed multidimensional envelope
and never a synonym for money; no conversion between dimensions exists without a declared
policy; and usage is independent of effect class, because a `RECORD_LOCAL` operation
still spends wall clock, tokens and electricity (Bdo, Q2 and Q5 redirects 2026-08-24).

The canon names them so a later contract cannot collapse them because a receipt happened
to be the available record. It builds none of them; that is contract work.

## What the canon reads today

`python scripts/sov_canon.py promises`, at drafting:

| Promise | reachable | declared, unreachable | missing |
| --- | --- | --- | --- |
| `PROMISE-01` bring your own participant | 18 | 25 | 4 |
| `PROMISE-02` custody stays here | 2 | 4 | 4 |
| `PROMISE-03` find out what can be asked | 1 | 10 | 0 |
| `PROMISE-04` one world | 7 | 12 | 0 |
| `PROMISE-05` find out why | 9 | 9 | 0 |
| `PROMISE-06` the model is swappable | 2 | 2 | 2 |
| `PROMISE-07` everything leaves a receipt | 13 | 12 | 1 |
| `PROMISE-08` correction never erases | 4 | 9 | 0 |
| `PROMISE-09` your judgement is the scarce thing | 0 | 5 | 0 |
| `PROMISE-10` useful from the artifact alone | 0 | 5 | 0 |
| `PROMISE-11` delegate and check | 1 | 8 | 1 |
| `PROMISE-12` work carries across a boundary | **5** | **0** | **0** |
| `PROMISE-13` review pinned to a version | 1 | 8 | 0 |
| `PROMISE-14` a node of your own | 0 | 2 | 2 |
| `PROMISE-15` cross to another node | 2 | 0 | 1 |

`PROMISE-12` is the only promise every crossing of which is reachable, and it is the one
that arrived as an implementation choice rather than as stated intent
(`decisions/0036`). `PROMISE-09` and `PROMISE-10` have nothing reachable at all.

## Consequences

- The upward question is answerable for the first time in principle: a capability
  resolves to a journey and a promise. It is not yet answerable in practice, because a
  work item cannot name a capability and a receipt cannot record what it consumed.
- Those two edges are contract work and are named in the report, not here.
- `STATUS.yaml` is unchanged. Recording the canon's standing there is part of accepting
  it, and a participant does not record its own acceptance.
- Nothing in `PRD.md`, `SPEC.md`, `CONTRACT.md` or `CLASSIFICATION.md` moved.

## Defaults taken

- Named the document `CANON.md` at the repository root, beside the rest of the governing
  set. Bdo holds naming; this is the plain rendering of the words he used and is one
  rename to counter.
- Reserved decision number `0046` through `scripts/sov_session.py`, which is the
  mechanism `OPEN-SEAMS.md` S16 wanted and now exists.
- Reused the cast identifiers in `.claude/epic/offices.json` for participants rather than
  minting a second set of names for actors the repository already names.
- Gave needs no identifiers (Ruling 2).
- Included two `LATER`/weakly-grounded promises (`PROMISE-14`, `PROMISE-15`) so the
  product world is whole, rather than trimming the canon to Phase I and making it look
  like a phase plan.
- Wrote fifteen promises and thirteen journeys. The instruction was to keep it small; the
  test applied was whether removing any one of them would leave a declared operation with
  no reason.

These are proposals. Bdo may counter any of them.

## What would defeat this ruling

- A participant a node genuinely serves that none of the ten covers.
- A promise that no governing document grounds.
- A journey whose crossings cannot be expressed as declared operations plus named gaps.
- A promise identifier re-pointed at a different meaning instead of being retired, which
  would break every attribution already made against it.
- The canon acquiring requirements, sequencing or architecture.

## Residuals

- `PROMISE-14` is weakly grounded: no document treats standing a node up as an
  experience anyone has, and `JOURNEY-12` carries two missing capabilities as a result.
- `OPEN-SEAMS.md` S10, the product boundary, is not closed by this canon. The canon says
  what the node undertakes; S10 asks whether Soveraeign is a primary enterprise
  application or a constitutional runtime over existing ones, and `PROMISE-13` is the
  only promise aimed at ordinary enterprise work.
- Nothing reconciles the canon's journeys against `.claude/epic/offices.json` or against
  `conformance/scenarios.json`, both of which describe adjacent things in different words.

## Movement 2026-08-24 — superseded by CANON-2

This ruling stands: the layer, its boundary, and the eight rulings below are unchanged.
Two things in it are now wrong on their own terms, both recorded in `decisions/0051`.

**Ruling 3 was too weak, and this record proved it.** It required a promise to be grounded
in the governing set and classified `PROMISE-12` as `DERIVED` while its own note said the
promise "arrived as an implementation choice". That is `IMPLEMENTATION_DERIVED`, and the
schema had no value for it, so the record could not say what it was. `CANON-2` adds the
five-value `source` classification and refuses `IMPLEMENTATION_DERIVED` outright.
`PROMISE-12` is re-grounded on `CONTRACT.md` C12 and `SYSTEM.md`.

**The per-promise table above is arithmetically wrong.** `promise_reading` summed crossing
counts across a promise's journeys, so a capability crossed by two of them counted twice.
`PROMISE-01` reads 17 reachable, not 18. Read
`python scripts/sov_canon.py promises` rather than the table here.

Ruling 7 also moved. `PROMISE-13` was retired in `CANON-2` and `PROMISE-16` minted: the
ruling that proofing is not the definition was right, and the promise still said proofing.
