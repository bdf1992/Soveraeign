# Registry Service Requirements Document

Status: `PROPOSED · SERVICE-SCOPED PROJECTION OF PRD.md`

This document applies the pattern `decisions/0093-service-srd-spec-ground.md`
authorizes: `PRD.md` at node scope, re-derived at Registry scope with the node
itself — its Gateway, its other services, its harness — named as the caller
instead of a human. It grants no standing. `CHARTER.md` remains the Registry's
authoritative role statement; this document only makes that role's obligations
countable the way `PRD.md` makes the node's obligations countable.

## Product outcome

Given a declared name, the Registry returns what it is, the document that
owns it, that document's own standing, and what it relates to — from one
freshly rebuilt index, or refuses rather than answer stale
(`CHARTER.md`, Role in Soveraeign).

## Callers

- **Gateway**, in a future routed profile — the Registry's own `CHARTER.md`
  names the in-process Gateway path as `resolve`'s only reachable route today.
- **Other services**, indirectly: eighteen open issues in `.claude/epic/tree.json`
  declare `requires: #14`, more than any other bit in the tree, naming Gateway,
  Relay, Workflow, Automation, the Capability Broker, Workers, Adapters,
  Proofing, and Phase-I Qualification as waiting behind this boundary
  (`CHARTER.md`, Role in Soveraeign).
- **Human operators**, through the `human-binding` port declared in
  `contracts/service.json`, for every operation; through the `model-binding`
  port for every operation except `declare-owner`, `supersede-owner`, and
  `retire-owner`, which `contracts/capability-offices.json` restricts to
  `HUMAN` actor kinds only.
- **`scripts/sov_owners.py`**, today, is not a caller of this service — it
  reads `contracts/domain-owners.json` directly, because `declare-owner` and
  `read-owner` are `PROPOSED`, not `BUILT`. This is stated rather than
  silently treated as the Registry already serving owner-record reads.

## Requirement lifecycle

```text
OPEN → BUILT → WITNESSED → RATIFIED
```

Same vocabulary as `PRD.md`: `BUILT` is an implementation claim this document
makes about the Registry's own code, not independent evidence. `WITNESSED`
requires a party that did not write this document or the code it describes.
`RATIFIED` requires the declared right. No requirement below may be advanced
past `BUILT` by this drafting pass.

## Requirements

### SVC-REGISTRY-1 · Resolve answers only from a fresh index

A declared name resolves to its entry, owning document address and digest,
office, required authority, and Kernel binding, or refuses `NAME_UNKNOWN`, and
never answers while any declared source has drifted from the digest the index
was built against. Serves `PROD-I-2` (Remember: a recording resolves its exact
source). Cites `sov://registry/resolve` in `contracts/service.json` and the
`_source_drift` check in `src/soveraeign_registry_service/core.py`.

Defeating case: a lookup returns an entry while a declared source's bytes no
longer match the digest the index was built from (`CHARTER.md`, Defeating
cases, first item).

Standing: `BUILT`. This is the one operation `contracts/service.json` marks
`BUILT` rather than `PROPOSED`.

### SVC-REGISTRY-2 · An entry always names a resolvable owner

`register-entry` and `supersede-entry` accept an entry only with a declared
kind, name, owning document address, and owning document digest that
resolves; an address that does not resolve is refused rather than stored.
Serves `PROD-I-2`. Cites `register-entry` and `supersede-entry` in
`contracts/service.json`.

Defeating case: an entry is stored without an owning document address, or
with one that does not resolve (`CHARTER.md`, Defeating cases).

Standing: `OPEN`. `register-entry` and `supersede-entry` are `PROPOSED` in
`contracts/service.json`; no code path exists yet.

### SVC-REGISTRY-3 · Two entries never both resolve the same name

`register-entry` refuses `NAME_COLLIDES` when the declared name already
resolves to a different entry, keeping resolution a function rather than a
choice among candidates. Serves `PROD-I-2`.

Defeating case: two entries claim the same name and both resolve
(`CHARTER.md`, Defeating cases).

Standing: `OPEN`. `register-entry` is `PROPOSED`.

### SVC-REGISTRY-4 · The index is rebuilt, never repaired in place

When `resolve` observes drift it refuses `INDEX_STALE` rather than patching
the disputed entry; `rebuild-index` is the only transition that may change
what the index answers, and it re-derives the whole index from its declared
sources. Serves `PROD-I-2`.

Defeating case: the index is repaired in place instead of rebuilt when it
disagrees with a source (`CHARTER.md`, Defeating cases). `resolve` already
meets the refusal half of this defeating case; `rebuild-index` meeting the
rebuild half remains `OPEN`.

Standing: `OPEN` for `rebuild-index` (`PROPOSED` in `contracts/service.json`);
the refusal half is exercised today as part of SVC-REGISTRY-1.

### SVC-REGISTRY-5 · An owner and its witness are never the same participant

`declare-owner` and `supersede-owner` refuse `WITNESS_NOT_INDEPENDENT` when
the declared witness matches the declared owner, and both require a budget
and a deadline or refuse `INCOMPLETE_PROPOSAL`. Serves `PROD-I-5` (Typed
authority) and the mandate in `contracts/domain-owners.json`, which names
`PROD-I-2` and `PROD-I-5` as what `owner-registry@1` was asked to answer.

Defeating cases: an owner record is declared with the same participant as
owner and witness; an owner record is declared with no budget or no deadline
(`CHARTER.md`, Defeating cases; `AGENTS.md`, Evidence and standing — "a build
report cannot witness itself").

Standing: `OPEN`. `declare-owner` and `supersede-owner` are `PROPOSED`, and
`contracts/capability-offices.json` restricts both to `HUMAN` actor kinds —
so even once built, a model operator cannot exercise this requirement
directly.

### SVC-REGISTRY-6 · Retiring an owner counters; it never erases

`retire-owner` emits a counter-record under `retract` semantics and preserves
the original owner record rather than deleting it. Serves `PROD-I-4` (Gate
and retract).

Defeating case: retiring an owner erases the earlier record instead of adding
a counter-record (`CHARTER.md`, Defeating cases).

Standing: `OPEN`. `retire-owner` is `PROPOSED` and, per
`contracts/capability-offices.json`, requires `ratify:judgement` — a
`JUDGEMENT`-typed authority, matching the `requires_authority_type:
JUDGEMENT` the `retract` kernel transition declares in
`contracts/kernel-transitions.json`.

### SVC-REGISTRY-7 · A resolution grants nothing

Every `resolve` receipt records `standing_effect: NONE`. Resolving an entry,
or reading an owner record, never advances that subject's own standing,
authority, or ratification. Serves `PROD-I-5` and `GROUND-003` (authority is
granted, never acquired).

Defeating case: a registry entry is treated as standing, authority, or
permission to act (`CHARTER.md`, Defeating cases).

Standing: `BUILT` for `resolve` (the field is set in
`src/soveraeign_registry_service/core.py`); `OPEN` for the same guarantee on
every other operation, none of which are built yet.

## Non-goals

- Defining a term, standing, or policy. Every entry's answer is "which
  document owns this," never a restatement of that document's content
  (`CHARTER.md`, What it is not).
- Cross-node or remote resolution, a query language, a UI projection, or any
  transport beyond in-process and CLI — explicitly deferred in `CHARTER.md`,
  Deferred.
- Reconciling the eight hand-maintained tables the Registry is meant to
  eventually replace. Nothing in this document claims that reconciliation is
  underway; see `JOURNEYS.md` for what currently goes unreconciled.
- Granting or ratifying authority. `owner-record` names an accountable
  participant; it does not hold authority itself (`CHARTER.md`, Owner
  records).
