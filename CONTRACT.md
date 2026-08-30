# Founding Contract

Status: `C1-C15 ACCEPTED · C16 PROPOSED UNDER DECISION 0066`

This document is normative.

These invariants constrain specifications and implementations. A change to one
requires a decision record and the authority declared in `STATUS.yaml`.

Uppercase `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` carry the
BCP 14 meanings of RFC 2119 and RFC 8174 only where a governing document states
that it is normative. Lowercase uses retain their ordinary meaning.

## C1 · Same world

Human and model surfaces resolve through the same authoritative transitions,
constraints, standings, and receipts. No interface may write authoritative
state around the kernel.

## C2 · Source survives reading

A reading never mutates its source. A derivation produces a new recording with
the source, reader, reader version, configuration, and exact-or-lossy status
recoverable.

## C3 · Evidence is not authority

Provenance, confidence, reproduction, consensus, model fluency, and quantity of
evidence do not grant authority. Authority must be explicitly typed, scoped,
revocable, and recorded.

## C4 · Standing does not collapse

Recorded, admitted, ratified, and effective are distinct. Admission does not
ratify. Ratification does not prove current applicability. Retraction does not
erase occurrence.

## C5 · Ratification and attestation differ

A right hand may ratify within its type. Runtime attestation reports
`reproduced`, `dissented`, or `unattestable`; it occupies no authority slot and
cannot alter a sign.

## C6 · Consequential operations are gated

Every consequential operation declares its inputs, required capabilities,
preconditions, expected observable result, effect class, and refusal behavior
before execution.

## C7 · Reports are not observations

An executor's success report is not evidence that the world changed. Settlement
uses an observer that can inspect the relevant world state without relying on
the executor's account.

## C8 · Every crossing returns a receipt

Admission, refusal, action, failure, unresolved judgement, attestation,
retraction, and counteraction produce attributable records with persistence
rules.

## C9 · Retraction preserves history

Record retraction counters effective record state and preserves both the act
and counter-record. It must not claim reversal of resource consumption or
external-world mutation.

## C10 · Identity roles are declared

Identity, address, digest, label, route, and handle may share a value only under
an intentional declared equivalence. Coincidence is not equivalence.

## C11 · No claim enters as authoritative

New claims enter as proposals or recordings. They become authoritative only
through witnessed evidence and typed ratification—not through a preloaded wise
model, universal ontology, inherited reputation, or confident assertion.

## C12 · Fresh operation is a test

Cold-start-to-competence is measured from the artifact alone. A fresh operator
or model instance must be able to determine what it can do, why, under whose
authority, and how success or failure will be observed.

## C13 · Lineage without inheritance

Previous repositories and documents are evidence and ancestors. Their ideas or
code become canonical only through an explicit carried obligation, fixture,
decision, or implementation adoption.

## C14 · Reality retains veto power

A persuasive synthesis does not close a seam. Contradictions, failed fixtures,
dissenting attestations, and unattestable claims remain visible until the
authorized process resolves them.

## C15 · State outlives execution

Execution does not own authoritative state. Every consequential human or model
decision leaves an attributable event with its actor, operation, reason, time,
exact inputs and outputs, authority, effect class, and outcome. Reports and
projections may be rebuilt or replaced; events, receipts, and counter-records
remain reconstructable.

## C16 · Precedent before invention

Before defining a consequential technical boundary, inspect applicable stable
standards and established ecosystem conventions, then deliberately adopt,
profile, defer, deviate, or monitor them. Precedent informs design but grants no
authority. A host language, runtime, library, provider, database, or operating
system MUST NOT silently define Soveraeign's persistent, cryptographic,
compatibility, interface, or authority semantics.
