# Product Canon

Epoch: `EPOCH-1` · Revision: `CANON-3` · Rendering: `CANON-3.0` · Ground: `GROUND-1`
Status: `OWNER-ACCEPTED 2026-08-24 · SUPERSEDES CANON-2`

This document names the durable product-level things that requirements are for: who a
Soveraeign node is for, what those people and models are trying to accomplish, what
Soveraeign undertakes to make possible for them, and the principal journeys by which an
undertaking becomes something someone can actually use.

It sits between `GROUND.md` and `PRD.md`. `GROUND.md` says what product this is;
`CONTRACT.md` says what may never stop being true; `PRD.md` says what the product currently requires and how qualification is measured.
Between them there was nothing, so a requirement had no parent and an operation had no
reason. This is that layer and nothing more.

It is **not** a second PRD, not architecture, and not a plan. It states no requirement,
selects no stack, sequences no work, and grants nothing.

`contracts/product-canon.json` carries the identifiers and the joins in machine form.
This document owns the wording; that record owns the links. `python scripts/sov_canon.py
check` refuses if they disagree.

## What CANON-3 changed

Bdo accepted `CANON-2` with one promise struck (2026-08-24, `decisions/0052`). Striking a
promise is a change of meaning, so it minted this revision rather than a rendering.

**`PROMISE-14` — "a node of your own" — is retired.** Standing a node up is not a durable
product promise merely because a node has to come into existence somehow. `GROUND-016`
carries the durable claim: a node is whole at any size. Installation, establishment,
bootstrapping, first run, deployment and onboarding sit beneath it as product experiences,
and may become important journeys and requirements without becoming permanent canon
promises.

`JOURNEY-12` is **kept**. Someone still has to go from nothing to a node, `node.establish`
and `node.read-identity` are still `MISSING`, and a journey does not have to be eternal
product identity to be a real gap. It now serves `PROMISE-02`, custody, which is what
standing up your own node is for.

One consequence worth seeing: `GROUND-016` is now carried by `PROMISE-15` alone, which is
`LATER`. That is admissible — the check requires a ground claim to be carried, not carried
in this phase — and it means that inside the historical `PHASE_I` bucket, "a node is whole at any
size" is represented only by `JOURNEY-12`'s gap list.

## What CANON-2 changed

`CANON-1` was drafted on 2026-08-24 and never accepted. Three corrections, all of them
directed by Bdo the same day, produced this revision:

1. Product Ground was extracted. Sixteen claims in `GROUND.md` now say what product this
   is; every promise here derives from at least one of them, and the check refuses a
   promise that derives from none.
2. `PROMISE-12` stopped being canonical because it was built. An implementation is
   evidence about product intent and never authority for creating it. It is now grounded
   in `CONTRACT.md` C12 and `SYSTEM.md`, and `decisions/0036` is cited as evidence rather
   than as a reason.
3. `PROMISE-13` was retired and `PROMISE-16` minted. `PROMISE-13` said proofing.
   Soveraeign would still be Soveraeign without proofing, so that wording was domain
   altitude wearing canon clothes.

The `standing` field on a promise also became `source`. `standing` is a governed word for
the artifact and record lifecycles, and where a promise's wording came from is a different
dimension that must not borrow the name.

## Rendering, revision, epoch

Three levels, and conflating them is how attribution rots. `GROUND.md` owns the rule; the
canon follows it.

| Level | Changes when | This canon |
| --- | --- | --- |
| **Rendering** | the artifact is re-issued with no change of meaning | `CANON-2.0` |
| **Revision** | meaning changes: a promise or journey added, retired, or reworded to say something different | `CANON-2` |
| **Epoch** | what product is being made changes, which the ground sets, not this document | `EPOCH-1` |

A typo is a rendering. It does not mean Soveraeign entered a new product epoch, and a
rendering may never be used to change meaning.

An identifier whose meaning changes is **retired**, and a new identifier is minted for
the new meaning. Retired identifiers are never reused. This is the rule `STATUS.yaml`
already applies to the retired `O1`–`O22` docket identifiers: *"They are retired, not
reserved."*

The reason is attribution. If `PROMISE-03` could quietly come to mean something else,
every hour and every token already recorded against it would silently change what it had
been spent on. Work attributed under an identifier must keep meaning what it meant when
the work was done.

## Where a promise comes from

Every promise records how it got the right to be here. This is not standing and not
confidence; it is the direction the authority ran.

| `source` | Means |
| --- | --- |
| `OWNER_DIRECTED` | Bdo said it. Refined against evidence, never invented. |
| `GOVERNINGLY_GROUNDED` | The governing set already carries the language, close to verbatim. |
| `STRONGLY_DERIVED` | Read out of several governing sources that do not state it as one promise in one place. |
| `IMPLEMENTATION_DERIVED` | It exists because something was built that way. **Always a defect.** The value exists so the classification can be written down while it is being fixed; an implementation is evidence about product intent and never authority for creating it. |
| `OWNER_CONFIRMATION_REQUIRED` | It stays proposed until Bdo confirms it. |

`python scripts/sov_canon.py check` refuses any promise carrying
`IMPLEMENTATION_DERIVED`. The three admissible resolutions are: ground it independently,
mark it `OWNER_CONFIRMATION_REQUIRED`, or move it below canon altitude.

## Who this is for

Ten participants. Where the repository already names one — the cast in
`.claude/epic/offices.json` — the canon reuses that name rather than minting a second.
`actor_kind` is `SPEC.md`'s; `role` is `CLASSIFICATION.md`'s.

**Owner is deliberately not in this list.** Owner is not a role: it is the context that
sets which Binding and which Projection a person comes through, over whatever role they
are holding (`decisions/0020`). Bdo at the operator desk is a human operator.

| Participant | Kind / role | What they are trying to accomplish |
| --- | --- | --- |
| `human-operator` | `HUMAN` / operator | Do domain work without learning the node's internals first; see what happened while away; be told what concerns them; decide the things only a person can decide, where the answer becomes a record. |
| `model-operator` | `MODEL` / operator | Discover the legal operations from the artifact alone; act inside a live grant and be refused legibly outside one; hand off what it did without keeping private state. |
| `model-bringer` | `HUMAN` / operator | Keep custody of the record while changing which model runs; know what each model consumed; get a visible refusal rather than a silent substitution. |
| `agent` | `HUMAN` or `MODEL` / agent | Choose among reachable operations without widening its own authority; escalate what it does not hold without stalling everything else. |
| `worker` | `WORKER` / worker | One bounded task with an unambiguous input state, and a lease that fences it against a newer holder. |
| `witness` | `HUMAN` or `MODEL` / witness | Reach the durable output without relying on the executor's account of it; record a dissent that stays visible. |
| `domain-owner` | `HUMAN` or `MODEL` / operator | A mandate narrow enough to finish; a resource envelope they can spend inside and see the remainder of; a witness who is not themselves. |
| `node-owner` | `HUMAN` / operator | Stand a node up and know it is theirs; grow or federate without migrating authority elsewhere. |
| `external-system` | `SYSTEM` / operator | Be reached only through a declared crossing that leaves a receipt. It has no expectations of its own. |
| `peer-node` | `SYSTEM` / node | Cross into another node without either absorbing the other. |

Needs carry no identifier of their own. They are not a join in the chain from a promise
down to a run, and an unnamed need is cheaper to correct than a wrong one made canonical.
Recorded as a default taken; reversible.

## What Soveraeign undertakes

Fourteen promises. Each is said to a participant rather than about the system, each names
where in the governing set its language already lives, and each derives from at least one
claim in `GROUND.md`. A promise deriving from no ground claim would mean product intent
was invented above the layer that holds it, and the check refuses one.

`python scripts/sov_canon.py promises` prints the whole table: promise, phase, source,
reachability and ground claims. `python scripts/sov_canon.py ground` prints it the other
way up.

`PHASE_I` is the historical first-qualification bucket retained for traceability.
`LATER` means outside that first profile. Neither token names the active campaign;
`STATUS.yaml` and `contracts/phases.json` are the reading for that.

### `PROMISE-01` — bring your own participant into a sovereign node · `PHASE_I`

> You can bring your own agent or model into a sovereign node you control or are
> authorized to use, discover what that participant can do under its actual authority,
> perform substantive governed work through the same operational world as a human, and
> inspect the resulting history, evidence and receipts without surrendering custody to
> the model or its provider.

Bdo's wording, 2026-08-24, given as approximate and to be refined against evidence
rather than adopted as final prose. It is compound on purpose, and it composes
`PROMISE-02`, `PROMISE-03`, `PROMISE-04`, `PROMISE-05` and `PROMISE-06` so that each
part is separately testable. This is the first promise the canon is meant to test.

### `PROMISE-02` — custody stays here · `PHASE_I`

> Custody of your record, your authority and your continuity stays with your node.
> Losing a provider costs you that provider, not your enterprise.

Grounded in `SYSTEM.md`, `BYOM.md`, `PRD.md` PROD-I-9, `AI-NATIVE.md` check 8.

### `PROMISE-03` — you can find out what can be asked · `PHASE_I`

> You can find out what can be asked of this node, by whom, and over what, without being
> told by a person who already knows.

`AI-NATIVE.md`'s reachability gate is this promise stated as a test.
`services/gateway/CHARTER.md` states the need in as many words and records that no single
place answers it.

### `PROMISE-04` — one world · `PHASE_I`

> People and models act through the same records, permissions, transitions, evidence and
> history. Neither gets a private door.

Grounded in `CONTRACT.md` C1, `SYSTEM.md`, `PRD.md`, `SPEC.md` Interface parity.

### `PROMISE-05` — you can find out why · `PHASE_I`

> You can find out why anything is what it is: its source, its version, who read it, what
> was left out, and what it cost.

The cost clause is the part the repository does not yet keep. `PRD.md` PROD-I-1 requires
a recorded cost and `services/asset/conformance/BASELINE.md` records it failing.

### `PROMISE-06` — the model is swappable · `PHASE_I`

> You can swap the model without changing your state, standing, authority, receipts or
> contracts. What changes is quality, latency and cost, and those are recorded rather
> than normalized away.

Grounded in `BYOM.md`, `PRD.md` PROD-I-9, `SPEC.md` `ModelBinding`.

### `PROMISE-07` — everything leaves a receipt · `PHASE_I`

> Every crossing returns a receipt, including the ones that refuse, fail, or leave a
> judgement unresolved.

Grounded in `CONTRACT.md` C8, `SPEC.md` `Receipt`.

### `PROMISE-08` — correction never erases · `PHASE_I`

> You can correct what the node did without pretending it never happened, and without a
> false claim that consumed resources came back.

Grounded in `CONTRACT.md` C9, `PRD.md` PROD-I-4, `AI-NATIVE.md` Retraction.

### `PROMISE-09` — your judgement is the scarce thing · `PHASE_I`

> Your judgement is treated as the scarce thing. Requests for it queue without stopping
> unrelated work, and where it was spent is visible.

Grounded in `PRD.md` PROD-I-6, `README.md`, `services/console/CHARTER.md`.

### `PROMISE-10` — useful from the artifact alone · `PHASE_I`

> A person or model arriving fresh can become safely useful from the artifact alone, and
> how long that took is measured rather than assumed.

Grounded in `CONTRACT.md` C12, `PRD.md` PROD-I-7, `AI-NATIVE.md` check 6.

### `PROMISE-11` — delegate and check · `PHASE_I`

> You can hand bounded work to someone or something else and check the result through a
> path they did not control.

Grounded in `CONTRACT.md` C7, `SDLC.md`, `SPEC.md` `observe_run`.

### `PROMISE-12` — work carries across a boundary · `PHASE_I`

> Work carries across a boundary where context is lost: a new session, a new operator, a
> new model, tomorrow.

Corrected in `CANON-2`. `CANON-1` said this promise arrived because continuity was
implemented, which had the direction of authority backwards. It stands on `CONTRACT.md`
C12, on `SYSTEM.md` giving Sov bounded agency over its own handoff, and on `AGENTS.md`
requiring a handoff that names standing, changes, observations, residuals and next
action. `decisions/0036` and the console continuity path are evidence that the promise is
keepable, not the reason it exists.

Derives from `GROUND-015`.

### `PROMISE-15` — cross to another node · `LATER`

> You can cross to another authorized node without either node absorbing the other.

Named so the product world is whole. The first qualification profile treated
federation as a non-goal, and this canon does not promote it into the active work
queue. Derives from `GROUND-016`.

### `PROMISE-16` — decide against exact state · `PHASE_I`

> You can do consequential work over governed, versioned domain state: decide against an
> exact version rather than against the thing in general, have the decision attached to
> that version, and have someone who was not you inspect it or counter it.

Minted in `CANON-2`, replacing the retired `PROMISE-13`. Derives from `GROUND-005`,
`GROUND-009` and `GROUND-011`.

`PROMISE-13` said proofing: open a review session, annotate a version, ratify a decision.
Bdo's test on 2026-08-24 was whether Soveraeign would still be Soveraeign if it stopped
shipping proofing as a first-class domain while keeping its foundational promises. It
would. So the proofing wording was domain altitude wearing canon clothes, and this is the
durable claim underneath it. `JOURNEY-11` remains the first concrete workflow that
demonstrates it, and proofing remains the first substantive enterprise proving workflow —
which is a real claim and a lesser one than being part of the definition.

## Retired

| Identifier | Retired in | Because |
| --- | --- | --- |
| `PROMISE-13` | `CANON-2` | Named proofing specifically, which is one domain workflow rather than a product-level undertaking. Superseded by `PROMISE-16`. Retired rather than reworded so nothing attributed to `PROMISE-13` silently comes to mean something wider. |
| `PROMISE-14` | `CANON-3` | Struck by Bdo. Standing a node up is a product experience beneath `GROUND-016`, not a durable promise. Nothing supersedes it: `JOURNEY-12` keeps the gap and `PROMISE-02` keeps the meaning. |

`python scripts/sov_canon.py trace PROMISE-13` still answers, and says what happened to
it. A reader following an old attribution has to be able to find out.

## How a promise becomes usable

Fourteen journeys. A journey is one participant's complete intention, not a screen. Each
names the promises it serves, the declared capabilities it crosses, and — separately —
the crossings it needs that **no service declares at all**.

That last column is the one the capability map cannot hold. The map is total over the
operations that exist and silent about the ones that do not, so a journey is where a
missing operation becomes visible.

| Journey | Participant | Serves |
| --- | --- | --- |
| `JOURNEY-01` Bring my model and put it to work here | `model-bringer` | 01, 02, 06 |
| `JOURNEY-02` Find out what I can do here | `model-operator` | 01, 03, 04 |
| `JOURNEY-03` Pick up work I left in another session | `model-operator` | 12, 04 |
| `JOURNEY-04` Put something under governed custody | `human-operator` | 05, 07 |
| `JOURNEY-05` Hand off bounded work and check the result | `agent` | 11, 07 |
| `JOURNEY-06` Find out why something happened | `human-operator` | 05, 07 |
| `JOURNEY-07` Correct something without erasing it | `human-operator` | 08, 07 |
| `JOURNEY-08` Get a decision only a person can make | `human-operator` | 09, 07 |
| `JOURNEY-09` Establish that an operation actually succeeded | `witness` | 11, 10 |
| `JOURNEY-10` Find something the node already holds | `model-operator` | 05, 03 |
| `JOURNEY-11` Review a pinned version and land a decision | `human-operator` | 16, 04, 08 |
| `JOURNEY-12` Stand up a node of my own | `node-owner` | 02 |
| `JOURNEY-13` Cross to another authorized node | `peer-node` | 15 |
| `JOURNEY-14` Read this node from where I stand | `human-operator` | 10, 05 |

`python scripts/sov_canon.py trace JOURNEY-02` walks one of them down to its crossings
and says which are reachable today, which are declared and unreachable, and which are
missing. `python scripts/sov_canon.py promises` gives the same reading per promise.

## The join this exists to make possible

```text
GROUND-nnn  →  PROMISE-nn  →  JOURNEY-nn  →  capability_id  →  sov://service/operation
            →  PROD-I-n  →  SPEC.md transition  →  service  →  work item  →  run
            →  receipt  →  resource usage  →  observation
```

Everything to the right of `capability_id` already existed and was already checked. The
ground and the canon supply the three links to its left, so that a person can start at an
expenditure and walk up to what justified it, or start at a product intention and walk
down to what has been spent on it.

The chain is not yet whole. Two edges are still missing and neither is canon's to supply:

- a work item cannot name the capability it serves
  (`contracts/issue-metadata.schema.json` has no product referent);
- a receipt cannot record what its operation consumed
  (`contracts/receipt.schema.json` has no field for it).

Both are recorded in `reports/2026-08-24-product-canon-attribution-discovery.md` and both
are contract work, not canon work.

## What resource words mean here

The canon names these so they are not collapsed later. They are seven measurements, not
one, and a receipt being the record that happens to exist is not a reason to fold them
together.

| Word | Means |
| --- | --- |
| `BUDGET` | The resource envelope intended for a piece of work. Typed and multidimensional — wall clock, tokens, tool calls, money — never a synonym for money, and never converted between dimensions without a declared policy. |
| `USAGE` | What was actually consumed, per dimension. |
| `COST` | A valuation of usage. A local run can consume real wall clock and tokens at zero monetary charge; that zero is a valuation, not an absence of usage. |
| `WALLCLOCK` | Elapsed real time. Which spans of it count as work is an accounting rule and belongs to the accounting contract, not here. |
| `EFFORT` | Participant activity attributable to an objective. |
| `RESULT` | What changed. |
| `VALUE` | Whether a result moved an accepted product intention. Only the canon can supply the intention half. |

Usage is independent of effect class. A `RECORD_LOCAL` operation still spends wall clock,
tokens, tool calls and electricity, and its effect being record-local must not make that
consumption disappear (Bdo, Q2 redirect 2026-08-24).

### One expenditure, many true readings

A run serves one capability. That capability is crossed by journeys, those journeys serve
promises, some of those promises are composed by a compound promise, and all of them
derive from ground claims. Six true statements about one expenditure, and it is still one
expenditure.

So the canon keeps two relations apart, and needs only two:

| Relation | Means |
| --- | --- |
| `directly_serves` | What the work actually served: one capability. This is what was measured. |
| `rolls_up_to` | Every broader intention that contains it. A view, and views overlap. |

Measured usage is counted **once**, from the set of distinct units. It may be *viewed*
through every valid ancestor. Summing the promise views to get a total would count a run
once per promise it supports, which is how a node reports spending four times what it
spent. `scripts/sovkernel/attribution.py` computes the measured total without ever
summing a view, and `overlap()` reports how much a naive sum would have invented rather
than hiding it. The same rule applies to crossings: a promise's reachability counts each
crossing once, however many of its journeys cross it.

## What would defeat this canon

- A participant a node genuinely serves that none of the ten covers.
- A promise here that no governing document grounds, which would mean the canon invented
  product intent rather than naming it.
- A journey whose crossings cannot be expressed as declared operations plus named gaps.
- Evidence that a promise identifier has been re-pointed at a different meaning instead
  of being retired, which would break every attribution already made against it.
- The canon acquiring requirements, sequencing or architecture, at which point it has
  become a second `PRD.md` and should be struck.

## Standing

`OWNER-ACCEPTED` 2026-08-24 (`decisions/0052`, recorded in `STATUS.yaml`), superseding
`CANON-2` and the never-accepted `CANON-1`. Acceptance fixes what these fourteen promises
mean; it is not a claim that the node keeps any of them.

Previously: Drafted by Claude at Bdo's
direction (2026-08-24, Q1 `ACCEPT` with a narrow boundary) and corrected the same day at
his direction on the three points listed at the top. Nothing here is `WITNESSED` or
`RATIFIED`. `PRD.md` was not modified to accommodate it, as directed. `STATUS.yaml` is
not changed by this document; recording the canon's standing there is part of accepting
it.
