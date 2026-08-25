# Product Ground

Epoch: `EPOCH-1` · Revision: `GROUND-1` · Rendering: `GROUND-1.1`
Status: `OWNER-ACCEPTED 2026-08-24`

This document holds the small number of claims that say **what product Soveraeign is**.
Sixteen of them. They are meant to change very rarely, and everything below them —
promises, journeys, requirements, operations, services, work, receipts — is meant to
change often.

## The test a claim has to pass

> If this statement became false, would we merely implement Soveraeign differently, or
> would we be building a materially different product?

Only the second belongs here. Every claim below carries its answer to that question in a
`what changing it would mean` line, and that line is the admission test rather than
decoration. A claim whose answer is "we would build it differently" belongs in
`CONTRACT.md`, `PRD.md`, `SPEC.md`, `ENGINEERING.md` or an implementation, not here.

Ground is not minted per service, feature, operation or requirement. Sixteen claims carry
102 declared operations. That ratio is the point.

## What Ground is and is not

Ground supplies the **meaning** of a fact about the node. It never asserts that the fact
is currently true. These are separate planes and collapsing them is the mistake this
layer exists to prevent:

| Plane | Holds | Owned by |
| --- | --- | --- |
| Product Ground | stable accepted meaning | `GROUND.md`, this document |
| Declared state | what currently claims to exist | service manifests, the capability map, `STATUS.yaml` |
| Observed evidence | what reality demonstrated | `reports/`, observations, conformance runs |
| Derived fact | a proposition read through Ground and supported by state and evidence | nothing yet; see `contracts/state-fact.schema.json` |

Worked through:

```text
GROUND-006   A participant can find out what it may do from the artifact alone.
STATE        console.discover-operations is declared and ACTIVE over IN_PROCESS.
EVIDENCE     a fresh model listed its legal operations without being told.
FACT         participant A could discover its legal operations on node N at revision R.
```

`GROUND-006` does not become false when the binding changes, when the node changes, when
the grant is revoked, or when that fact stops being true. That is the whole reason to
separate them.

Six distinctions this layer keeps apart, stated once so nothing below has to restate them:

```text
Product Ground   ≠ state fact.
Intent           ≠ existence.
Specification    ≠ implementation.
Implementation   ≠ success.
Declaration      ≠ observation.
Evidence         ≠ authority.
```

## Rendering, revision, epoch

Three levels, and conflating them is how attribution rots.

| Level | Changes when | Example |
| --- | --- | --- |
| **Rendering** `GROUND-1.1` | the artifact is re-issued with no change of meaning | a typo, a repaired citation, a reflowed table — and `GROUND-1.0` → `GROUND-1.1`, which recorded acceptance and changed no claim |
| **Revision** `GROUND-1` | meaning changes: a claim added, retired, or reworded to say something different | adding a seventeenth claim |
| **Epoch** `EPOCH-1` | what product is being made changes, which is what retiring or replacing a Ground claim means | dropping sovereign custody |

A rendering must never be used to change meaning, and a typo must never imply that
Soveraeign entered a new product epoch. Historical revisions stay addressable. An
identifier whose meaning changes is **retired**, and a new one is minted; retired
identifiers are never reused, because work already attributed under an identifier has to
keep meaning what it meant when the work was done. This is the rule `STATUS.yaml` already
applies to the retired `O1`–`O22` docket.

## The sixteen claims

### `GROUND-001` — custody stays with the enterprise

> An enterprise keeps custody of its memory, its authority, its operation and its
> continuity. Compute may be borrowed from anywhere; none of those four may quietly move
> with it.

Grounded in `SYSTEM.md` Scope and Ownership and model portability, `SPEC.md`.

*What changing it would mean.* Soveraeign would be a hosted platform that runs an
enterprise's work, rather than a node an enterprise owns. Every promise about swapping
providers, standing up your own node, or losing a provider without losing the enterprise
would go with it.

### `GROUND-002` — one governed world

> People and models are native operators of one governed world. They resolve to the same
> state, the same transitions, the same authority checks, the same evidence and the same
> history. Neither gets a private door.

Grounded in `CONTRACT.md` C1, `SYSTEM.md` Scope, `PRD.md`, `AI-NATIVE.md`.

*What changing it would mean.* Soveraeign would be an ordinary enterprise application
with a model integration beside it, or a model framework with a human dashboard. The
AI-native claim rests entirely here.

### `GROUND-003` — authority is granted, never acquired

> Authority is granted, typed, scoped, revocable and recorded. Nothing acquires it by
> operating successfully, by being fluent, by being recent, by being the provider, or by
> being trusted.

Grounded in `CONTRACT.md` C3 and C11, `AGENTS.md` Authority, `SPEC.md`.

*What changing it would mean.* Soveraeign would be an automation environment in which
capability implies permission. Refusal, delegation, and the whole notion of a participant
that can build what it cannot ratify would lose their basis.

### `GROUND-004` — you act by crossing a declared operation

> A participant acts by crossing a declared operation, not by having access. The
> operation declares its inputs, its required authority, its preconditions, its expected
> observable result, its effect class and its refusal behaviour before it runs.

Grounded in `CONTRACT.md` C6, `SPEC.md`, `AGENTS.md` State and execution.

*What changing it would mean.* Soveraeign would be a permissions layer over arbitrary
action. There would be no unit to discover, to attribute effort to, or to refuse.

### `GROUND-005` — a consequential act binds to exact state

> What it read, at what version, with what digest, and what it produced, stay recoverable
> after the fact, and coincidence of value is never treated as identity.

Grounded in `CONTRACT.md` C2, C10 and C15, `SPEC.md`.

*What changing it would mean.* Soveraeign would record that something happened without
being able to say what it happened to. Evidence, reproduction, version-pinned decisions
and staleness refusal all rest here.

### `GROUND-006` — the node is discoverable from the artifact alone

> What may be asked of a node is discoverable from the artifact alone. A participant
> arriving with no briefing can determine what it may do, over what, under whose
> authority, and how success or failure will be observed.

Grounded in `CONTRACT.md` C12, `AI-NATIVE.md`, `PRD.md` PROD-I-7.

*What changing it would mean.* Soveraeign would require a person who already knows in
order to be usable. Model participation would degrade to whatever a human remembered to
explain, and the product would be normal enterprise software.

### `GROUND-007` — every crossing leaves a record

> Every crossing leaves a durable attributable record: who, what operation, on what,
> under what authority, with what effect class, and what came of it. Refusals, failures
> and unresolved judgements leave one too.

Grounded in `CONTRACT.md` C8 and C15, `SPEC.md`.

*What changing it would mean.* Soveraeign would be unable to answer why anything is what
it is. Attribution, audit, correction and independent observation would have nothing to
stand on.

### `GROUND-008` — refusal is an outcome

> A participant that may not do something is told so legibly, with a reason, and the
> refusal is as much a result as a success.

Grounded in `CONTRACT.md` C6 and C8, `SPEC.md` refusals, `AI-NATIVE.md`.

*What changing it would mean.* Soveraeign would be permissive by default with exceptions
bolted on. A model operator could not tell the difference between not allowed, not built,
and broken.

### `GROUND-009` — correction never erases occurrence

> A wrong record stops conditioning what happens next by being countered, and the counter
> never claims that consumed resources or external effects came back.

Grounded in `CONTRACT.md` C4 and C9, `PRD.md` PROD-I-4.

*What changing it would mean.* The record would be rewritable, and every historical
attribution would be provisional. Soveraeign would be a database with an undo button.

### `GROUND-010` — a report is not an observation

> Whether something actually happened is settled by a path the executor did not control,
> and a build never witnesses itself.

Grounded in `CONTRACT.md` C7 and C5, `SDLC.md`, `AGENTS.md` Evidence and standing.

*What changing it would mean.* Soveraeign would take an agent's word for its own work.
Delegation at any scale, and the entire claim to govern model work rather than merely run
it, would collapse.

### `GROUND-011` — standing does not collapse

> Proposed, recorded, admitted, ratified and effective are distinct, and nothing enters
> as authoritative merely by being written, being confident, or being agreed with.

Grounded in `CONTRACT.md` C4, C11 and C14, `CLASSIFICATION.md`.

*What changing it would mean.* Soveraeign would be a wiki with permissions. The
difference between a draft, an accepted rule and a currently applicable rule would stop
being machine-readable.

### `GROUND-012` — human judgement is reserved and scarce

> Some transitions require a person, that requirement is declared, and waiting on one
> does not stop unrelated work.

Grounded in `CONTRACT.md` C5, `PRD.md` PROD-I-6, `AGENTS.md` Authority, `decisions/0023`.

*What changing it would mean.* Soveraeign would be an autonomous agent runtime. The owner
would be an operator of last resort rather than the holder of a declared kind of
decision.

### `GROUND-013` — the model is substitutable

> Changing which model runs changes quality, latency and cost, and changes nothing about
> state, standing, authority, receipts or contracts. A model that is unavailable is
> refused visibly, never substituted silently.

Grounded in `SYSTEM.md` Ownership and model portability, `BYOM.md`, `PRD.md` PROD-I-9,
`AGENTS.md` Secrets and local boundaries.

*What changing it would mean.* Soveraeign would be a wrapper around one provider.
Bring-your-own-model, the local-first posture and the custody argument would all be
marketing rather than structure.

### `GROUND-014` — effort resolves to intention

> Any meaningful expenditure of time, tokens, tools or money can be traced up to the
> product intention that justified it, and any product intention can be traced down to
> what has actually been spent realizing it.

Grounded in `CONTRACT.md` C15, `PRD.md` PROD-I-1, `AGENTS.md` Change protocol,
`reports/2026-08-24-product-canon-attribution-discovery.md`.

*What changing it would mean.* Soveraeign would record that resources were consumed
without being able to say what for. A node could run agents all night and produce a
ledger nobody could read as a decision about priorities.

### `GROUND-015` — work survives the loss of context

> A new session, a different operator, a different model or the next day does not lose
> what was under way, because what mattered was written down rather than held in
> someone's head.

Grounded in `CONTRACT.md` C12, `SYSTEM.md` Ownership and model portability, `AGENTS.md`
Context hygiene.

*What changing it would mean.* Soveraeign would be usable only within one continuous
conversation. Model participation would be capped at whatever fits in one context window,
which is the constraint the product exists to remove.

### `GROUND-016` — a node is whole at any size

> One person's node is a first-class node, not a reduced edition, and growing to more
> participants or federating with another node does not migrate its authority or its
> record somewhere else.

Grounded in `SYSTEM.md` Ownership and model portability, `CLASSIFICATION.md`,
`decisions/0039`.

*What changing it would mean.* Soveraeign would be enterprise software with a hobby tier,
and federation would be a migration path into someone else's system rather than a
crossing between two sovereign ones.

## What was deliberately kept out

Each of these was considered and rejected as belonging below this altitude. The reason is
the admission test, not that they are unimportant.

| Considered | Where it belongs | Because |
| --- | --- | --- |
| Proofing as a product domain | a journey and `PRD.md` | If Soveraeign never shipped proofing and still kept `GROUND-001` through `GROUND-016`, it would still be Soveraeign. Proofing is the first substantive enterprise workflow, which is a different and lesser claim. |
| SQLite, Python, the filesystem store | `ENGINEERING.md` | Changing all three changes the implementation and no promise. |
| The office and counter vocabulary | `CLASSIFICATION.md`, `decisions/0038` | A useful way to place an operation, not a claim about what the product is. |
| Bounded leases and fencing tokens | `SPEC.md` | The mechanism by which `GROUND-010` is kept, not a separate claim. |
| The seven resource words | the canon and the accounting contract | Vocabulary that keeps `GROUND-014` from being collapsed, not ground itself. |
| Federation | `GROUND-016` and `PROMISE-15` | Already carried: a node that is whole at any size is what makes crossing without absorption meaningful. |

## What would defeat this Ground

- A claim here whose `what changing it would mean` line, read honestly, describes a
  different implementation rather than a different product.
- A claim that no promise derives from, which would mean the Ground is carrying something
  the product does not undertake.
- A promise that derives from no claim here, which would mean the canon has product
  intent this Ground does not account for.
- A Ground identifier re-pointed at a different meaning instead of being retired.
- Ground growing past twenty claims, which is the signal that claims are being minted per
  feature.

## Standing

`OWNER-ACCEPTED`. Extracted from `CANON-1` and the governing set by Claude at Bdo's
direction and accepted by Bdo on 2026-08-24 (`decisions/0052`, recorded in
`STATUS.yaml`). Revision `GROUND-1` is now fixed: later work is attributed against these
sixteen claims meaning what they mean here.

Accepting the ground is **not** a claim that the node keeps any of it. Bdo said so in the
ruling: *"I am accepting the semantic ground, not asserting that the implementation
currently keeps every Ground claim."* `GROUND-010` in particular is a claim the node
cannot presently keep, and saying so is what the four planes are for.

No governing document was modified to accommodate this. `contracts/product-ground.json`
carries the identifiers; `python scripts/sov_canon.py check` refuses if the two disagree.
