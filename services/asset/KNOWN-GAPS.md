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
| Derivation reconstruction | Derivative records identify run and input version but omit reader version, configuration digest, fidelity omissions, and direct source resolution | Full reconstruction path must resolve deterministically | C2; PROD-I-2 |
| Atomic commit | Blob writes and ledger commits are not one recoverable protocol | Partial-write recovery must distinguish committed from attempted state | SPEC fault model |
| Two bindings | Only a Python API/CLI participant exists | Human and model bindings must use the same transition contract | C1; PROD-I-3 |
| Attestation | Byte observation exists, but general claim attestation does not | `REPRODUCED`, `DISSENTED`, and `UNATTESTABLE` must be recorded | C5; PROD-I-8 |
| Judgement queue | Missing authority refuses synchronously | Judgement-dependent work must remain visible and non-blocking | PROD-I-6 |

These are participant defects or unimplemented requirements, not reasons to
relax the logical oracle.
