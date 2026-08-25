# 0051 · Product Ground, and the corrections that produced CANON-2

Status: `PROPOSED · DRAFTED AT OWNER DIRECTION · ACCEPTANCE PENDING`

Drafted at Bdo's direction, 2026-08-24. He accepted the product-canon layer as the correct
place between `CONTRACT.md` and `PRD.md` and did not accept `CANON-1` as the final
semantic revision. This records the correction pass. The acceptance surface is
`reports/2026-08-24-product-ground-acceptance.md`; `decisions/0046` records the layer
itself and is not reopened.

## Decision

Split the canon's two altitudes. A **Product Ground** of sixteen stable claims says what
product Soveraeign is. The **Product Canon** says who it is for and what it undertakes, and
every promise in it derives from at least one ground claim.

- `GROUND.md` owns the ground wording. `EPOCH-1`, revision `GROUND-1`, rendering
  `GROUND-1.0`.
- `contracts/product-ground.json` and its schema own the identifiers and the eight-to-twenty
  ceiling.
- `CANON.md` and `contracts/product-canon.json` move to `CANON-2` / `CANON-2.0`, superseding
  the never-accepted `CANON-1`.
- `scripts/sovkernel/ground.py` owns the join rules; `scripts/sovkernel/attribution.py` owns
  the rollup; `python scripts/sov_canon.py check | trace | promises | ground | rollup` reads
  them, and `scripts/verify.py` runs `check`.

No governing document was modified. `PRD.md`, `SPEC.md`, `CONTRACT.md`, `CLASSIFICATION.md`
and `STATUS.yaml` are untouched.

## Rulings

**1. Ground is admitted by one test, and the answer is a required field.**

> If this statement became false, would we merely implement Soveraeign differently, or
> would we be building a materially different product?

Only the second belongs. Every claim carries an `if_false` line, the schema requires it,
and it is the admission test rather than commentary. Sixteen claims stand under 102 declared
operations and nine `PROD-I` requirements; the schema caps the set at twenty, because a
larger ground means claims are being minted per feature.

Proofing, the storage choices, offices and counters, leases and the resource vocabulary were
each considered and placed below this altitude, with the reason recorded in `GROUND.md`.

**2. An implementation is evidence about product intent, never authority for creating it.**

`CANON-1` said `PROMISE-12` "arrived as an implementation choice rather than a stated
intention" and named it anyway. That direction is now refused mechanically: a promise
carrying `IMPLEMENTATION_DERIVED` is a hard defect with three named exits — ground it
independently, mark it `OWNER_CONFIRMATION_REQUIRED`, or move it below canon.

`PROMISE-12` took the first exit. It stands on `CONTRACT.md` C12, on `SYSTEM.md` giving Sov
bounded agency over its own handoff, and on `AGENTS.md` requiring a handoff that names
standing, changes, observations, residuals and next action. `decisions/0036` is cited as
evidence that the promise is keepable.

`PROMISE-14` took the second. No governing document treats standing a node up as an
experience anyone has, so it stays proposed until Bdo confirms it or it moves below canon.

**3. Proofing is the first substantive enterprise proving workflow, not part of the
definition.**

Bdo's test: would Soveraeign still be Soveraeign if it stopped shipping proofing as a
first-class domain while keeping its foundational promises? It would. `PROMISE-13` said
proofing — open a session, annotate, ratify — which is domain altitude. It is **retired**
and `PROMISE-16` minted for the durable claim underneath: consequential work over governed,
versioned state, decided against an exact version and inspectable by someone who was not
you. `JOURNEY-11` still walks proofing and now serves `PROMISE-16`.

Retired rather than reworded, even though `CANON-1` was never accepted and nothing had been
attributed to `PROMISE-13`. The machinery is worth exercising once for real, and
`sov_canon.py trace PROMISE-13` still answers with what happened to it.

**4. Rendering, revision and epoch are three levels.**

| Level | Changes when |
| --- | --- |
| Rendering `GROUND-1.0` | the artifact is re-issued with no change of meaning |
| Revision `GROUND-1` | meaning changes: a claim added, retired, or reworded to say something different |
| Epoch `EPOCH-1` | what product is being made changes — a ground claim retired or replaced |

A rendering may not render a revision other than its own, and the check enforces it. A typo
must never imply that Soveraeign entered a new product epoch. `CANON-1`'s single
`epoch_rule` conflated all three.

**5. `standing` was the wrong word, twice.**

The promise field `standing` becomes `source`, and the state-fact field is
`evidential_status`. `standing` already means the artifact lifecycle
(`OPEN`/`BUILT`/`WITNESSED`/`RATIFIED`) and the record lifecycle
(`RECORDED`/`ADMITTED`/`RATIFIED`/`EFFECTIVE`). `AGENTS.md` forbids a synonym for an
existing standing term, and a third meaning on the same word would have been
`OPEN-SEAMS.md` S18's defect, self-inflicted.

**6. Measured usage is counted once and viewed many times.**

Two relations, and no more: `directly_serves` names the one capability a unit of work
served, and `rolls_up_to` names every broader intention that contains it. The measured total
is computed from the set of distinct units and never by summing views;
`attribution.overlap()` reports how much a naive sum would have invented rather than hiding
it.

This was not only a future concern. `canon.promise_reading` was summing crossing counts
across a promise's journeys, so a capability crossed by two of them counted twice. Fixed;
`PROMISE-01` now reads 17 reachable where `decisions/0046` published 18, and 18 was wrong.

No conversion between dimensions exists. Usage carries `wallclock_seconds`, `tokens`,
`tool_calls` and `usd` and an unknown dimension is refused, so `COST` and `EFFORT` cannot
enter a usage record because a receipt happened to be the available shape.

**7. Ground supplies meaning; it never asserts a fact is true.**

Four planes stay separate: Product Ground, declared state, observed evidence, derived fact.
`contracts/state-fact.schema.json` is the shape where they meet, with two worked examples —
one `DECLARED`, one `REFUTED`. A fact pins the state it was read from, so it can go `STALE`
when that state moves, while the ground, promise and journey references stay exactly as they
were.

**8. The perspectival read is recorded as missing, not invented.**

`projection.read-perspective` — take a perspective and a purpose, return a bounded reading
with its source ground, state references, evidence references, declared omissions and
perspective attribution — belongs in the Projection Service beside `package-context`. It
does not exist. `JOURNEY-14` carries it in `missing_capabilities`, which is the canon's own
mechanism for a crossing nothing declares. No service manifest was modified.

The five readings in the acceptance report were written by hand, which is the evidence that
this crossing is missing rather than a demonstration that it is not needed.

## Consequences

- A new product promise now has to be argued at the ground layer first.
- A promise may never become canonical because something was built that way.
- An identifier's meaning is fixed for good; changing it retires the identifier.
- `decisions/0046` remains the record of the layer. Its per-promise table is superseded by
  `python scripts/sov_canon.py promises`, and its `PROMISE-01` row was arithmetically wrong.
- `STATUS.yaml` is unchanged. Recording the layer's standing there is part of accepting it.

## Defaults taken

- Ground lives in `GROUND.md` at the root with its own revision line, rather than as a
  section of `CANON.md`.
- `IMPLEMENTATION_DERIVED` is a hard defect rather than a warning.
- `scripts/sovkernel/jsonschema.py` learned the `maxItems` keyword so the eight-to-twenty
  ceiling could be a contract rather than a convention. The validator refuses unknown
  keywords by design, so adding one is the only way to use it.
- `contracts/state-fact.schema.json` and its fixtures are proposed and wired to nothing but
  their own cases.

## What would defeat this ruling

- A ground claim whose `if_false` line describes a different implementation rather than a
  different product.
- A promise that derives from no ground claim, or a ground claim no promise carries.
- A ground or promise identifier re-pointed at a different meaning instead of retired.
- Ground growing past twenty claims.
- A total reached by summing attribution views.
- A perspectival reading treated as a correction to the ground rather than as dissent.

## Residuals

- `PROMISE-14` unconfirmed. If it goes, `GROUND-016` is left carried by a `LATER` promise
  alone.
- `GROUND-014` carries the most product weight and the least implementation; `PRD.md`
  PROD-I-1 requires a recorded cost that `services/asset/conformance/BASELINE.md` records
  failing.
- `bindings/mcp` withholding `record.read-entry` sits awkwardly under `GROUND-002`. Open
  since `decisions/0038` Movement 2026-08-24 and unchanged here.
- `OPEN-SEAMS.md` S10 is not closed. All sixteen claims are true whether Soveraeign is a
  primary enterprise application or a constitutional runtime over existing ones.
- Two senses of `Requirement`, in `#41`/`#48` against `PROD-I-n`. Naming is Bdo's; nothing
  was renamed.
- Nothing reconciles the fourteen journeys against `.claude/epic/offices.json` or
  `conformance/scenarios.json`.
