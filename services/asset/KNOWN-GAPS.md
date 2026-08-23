# Asset Service Reference Gaps

Status: `OBSERVED AGAINST PROPOSED SPEC · NOT OWNER-RATIFIED`

The reference participant proves a useful local walk, but it does not yet pass
the full Phase-I logical contract.

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| Admission standing | Proposal ratification updates `RECORDED` directly to `RATIFIED` | Admission must be a visible separate transition | C4; SPEC `admit`/`ratify` |
| Effectiveness | A ratified relationship becomes effective immediately | Current effectiveness must follow the applicable attestation and policy gate | C4-C5; PROD-I-8 |
| Authority envelope | Grants carry actor, capability, and scope only | Type, issuer authority, budget, validity, and revocation must be enforced | C3; PROD-I-5 |
| Observer independence | Any named actor can call `observe`, including the worker | Observer relation must prevent executor-only settlement | C7; SPEC `Observation` |
| Receipt completeness | Receipts omit exact input state, authority grants, preconditions, effect class, and digest | Required receipt fields must be present for every terminal outcome | C6-C8 |
| Atomic commit | Blob writes and ledger commits are not one recoverable protocol | Partial-write recovery must distinguish committed from attempted state | SPEC fault model |
| Two bindings | Only a Python API/CLI participant exists | Human and model bindings must use the same transition contract | C1; PROD-I-3 |
| Attestation | Byte observation exists, but general claim attestation does not | `REPRODUCED`, `DISSENTED`, and `UNATTESTABLE` must be recorded | C5; PROD-I-8 |
| Judgement queue | Missing authority refuses synchronously | Judgement-dependent work must remain visible and non-blocking | PROD-I-6 |
| Model portability | No Model Binding or Model Adapter participant exists | Two materially different models must use one kernel contract with exact identity, data-boundary, usage, cost, and provider-loss receipts | PROD-I-9; BYOM.md |
| Operational journal | Mutable lifecycle tables and partial receipts do not yet implement the complete append-preserving Event Envelope | Every consequential decision and state transition must remain reconstructable independently of current projections | C15; SPEC `EventEnvelope` |

These are participant defects or unimplemented requirements, not reasons to
relax the logical oracle.

## Repairs at `BUILT` standing

The following prior defects now have self-tested implementation evidence. They
remain below `WITNESSED` until an independent engagement reproduces them.

**Derivation reconstruction.** Every derivative declares and persists its exact
source version and digest, CAS-addressed supplied reader artifact and replay
configuration, fidelity, recoverable omissions, output address, and recorded
standing. Source, reader, configuration, and output drift refuse. Settlement
reconstructs the full path instead of checking only the output bytes. Evidence:
`conformance/PROD-I-2-BUILD.md`, C2, and PROD-I-2.

**Module boundary.** Storage, authority/receipts, derivative execution,
observation, projections, reader declarations, and the Asset facade are
separate modules below 300 lines. Evidence: `scripts/lint.py` and ENGINEERING's
`Context and module budget` section.
