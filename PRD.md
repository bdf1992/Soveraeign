# Product Requirements — Founding and Phase I

Status: `FREEZE CANDIDATE, NOT OWNER-RATIFIED IN THIS REPOSITORY`

## Product outcome

Create the smallest locally sovereign enterprise environment in which one human
and one model can use the same governed record to propose, remember, cross,
ratify, attest, act, inspect, and retract.

## Users

- The enterprise owner, who holds product and judgement authority.
- Human operators acting under typed scopes.
- Model operators acting under typed scopes and explicit host capabilities.
- Witnesses that independently verify declared outcomes.
- Later, maintainers and federated enterprise nodes.

## Requirement lifecycle

```text
OPEN → BUILT → WITNESSED → RATIFIED
```

`BUILT` is an implementation claim. `WITNESSED` requires independent evidence.
`RATIFIED` requires the declared right. No agent may advance a requirement on
its own report.

## Phase-I requirements

### PROD-I-1 · Propose

A fresh model session can submit a proposal at a recorded cost. The result is
an attributed, addressed, left-signed candidate that claims no authority.

Defeating case: a proposal missing author, cost, source, or proposal standing is
admitted.

### PROD-I-2 · Remember

The local store preserves addressed payloads and sufficient versioned
reconstruction authority to recover the exact source, reader, derivation,
configuration, provenance, and exact-or-lossy status of a derived recording.

Defeating case: a source rereads differently, or a recording cannot resolve its
source and reader.

### PROD-I-3 · Cross

One human and one model exchange through the same record. A fact deposited by
one is retrieved and used by the other with origin and projection visible, and
the crossing returns a receipt.

Defeating case: the crossing cannot name its authoritative source, reader,
version, or omissions.

### PROD-I-4 · Gate and retract

Every admission carries a mark and receipt. An acted record entry can be
countered while preserving the act and counter-record.

Defeating case: an unmarked entry is admitted, or retraction erases history or
claims external-world rollback.

### PROD-I-5 · Typed authority

Authority slots are typed, scoped, revocable, and recorded. Machine authority
may ratify verification-typed truth when delegated; judgement-typed truth
requires a human right.

Defeating case: a machine right ratifies judgement-typed truth.

### PROD-I-6 · Founder judgement budget

Judgement requests queue without blocking operation. The system reports where
human judgement was spent and which unresolved rights remain pending without
inventing a target quota.

Defeating case: an operation blocks indefinitely awaiting owner judgement or
hides the pending right.

### PROD-I-7 · Independent qualification

A fresh witness can verify Phase-I requirements from the artifact and addressed
evidence alone. The witness emits an attributable qualification record and
queues the owner's operational acceptance decision.

Defeating case: the witness needs undocumented oral explanation or trusts the
implementation's self-report.

### PROD-I-8 · Joint sign

An already-ratified executable claim receives a runtime attestation naming the
validator, version, inputs, run, and outcome: `reproduced`, `dissented`, or
`unattestable`. Dissent changes current effectiveness without changing the
historical ratification.

Defeating cases: changed inputs still reproduce falsely; attestation modifies
an authority sign; or an unattestable claim crosses to effective silently.

## Two-binding proof

At least one human-facing binding and one model-facing binding must execute the
same authoritative transitions and yield compatible receipts. A surface that
bypasses the kernel fails Phase I.

## Non-goals for Phase I

- Treating the selected name as proof of product maturity or public clearance.
- A graphical production interface.
- A universal ontology or frozen encoding.
- Automated external-world effects.
- World rollback.
- Distributed consensus or federation.
- Importing whole predecessor implementations.
- Optimizing performance before semantic conformance.
- Treating Gauge, Definition, Atlas, or another subsystem as the whole product.

## Phase-I exit

Phase I exits only when every normative predicate has a positive and defeating
fixture, the fixtures run against two bindings, independent observation can
reconstruct the receipts, open judgement calls are visible, and the owner
ratifies Phase-I operational acceptance.
