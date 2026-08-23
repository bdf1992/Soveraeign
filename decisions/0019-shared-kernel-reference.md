# 0019 · Shared kernel reference boundary

Status: `PROPOSED · BUILT · SELF-TESTED · NOT WITNESSED`

Numbering note: decision 0018 is occupied on the concurrent federation-harness
branch. This decision uses 0019 so both histories can merge without address
collision.

## Decision

Give the shared kernel one executable reference under `/kernel`, separate from
`/contracts` (which owns the schemas) and from `/services/<domain>` (each of
which owns one lifecycle). The kernel is the cross-cutting foundation
`CLASSIFICATION.md` already names; it is not a service and does not become one
by having code.

The reference realizes ten of the fourteen `SPEC.md` transitions through one
`Attempt` path that checks the declared pre-state, evaluates typed authority at
the moment of the transition, and appends exactly one event envelope and one
receipt per attempt to an append-only journal whose `audit` exposes any write
that did not pass through it. The four remaining transitions are compositions a
service or adapter performs with these primitives; `invoke_model` waits on O12.

Its obligations are declared in `kernel/fixtures/transition-matrix.json` as
positive and defeating cases and executed by `kernel/tests/`, which also
validates every emitted record against the shared contracts through a validator
the kernel does not own.

## Why

Issue #6 asks the kernel to "govern legal transitions ... without turning those
primitives into independent services". Before this decision the transition
contract was realized only inside the Asset Service, with admission, attestation,
and effectiveness collapsed or absent (`services/asset/KNOWN-GAPS.md`). A
second service would have had to copy that private rule set. One reference the
services compose is the smallest change that makes "same kernel semantics" a
thing a witness can run.

## Consequences

- `AGENTS.md` Directory boundaries gains a `/kernel` row. The kernel owns
  transition semantics and the journal surface; it must not own a service
  lifecycle, provider types, or durable storage policy.
- `STATUS.yaml` gains `shared_kernel_status` and the proposed claim
  `shared_kernel_reference_transitions`. Standing is `BUILT` at most.
- Seven refusal reason codes beyond `SPEC.md`'s named set are proposals queued
  under O10 (`kernel/src/soveraeign_kernel/reasons.py`).
- The Asset Service is not rebound by this decision. Its private rules remain a
  named gap; rebinding is the held work behind #6 (issue #8 and siblings).
- Durable storage of the journal is issue #7, behind the same `append`,
  `entries`, `audit` surface.
- An attestation JSON Schema is still not authored (O4). The kernel records
  the `SPEC.md` field block and nothing more.

## Judgement queued for Bdo

1. Accept `/kernel` as the boundary, or fold the reference under `/contracts`.
2. Accept, rename, or strike the seven proposed reason codes at O10.
3. Whether the journal's chain digest is the mechanism #7 should persist, or
   only the exposure rule it must preserve.
