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
| Reader execution evidence | A declared recording verifies the exact reader artifact, configuration, source, and output, but not that the worker semantically executed that reader | Model binding and observation must attest execution without promoting worker self-report | C2, C7; PROD-I-2 |
| Atomic commit | Blob writes and ledger commits are not one recoverable protocol | Partial-write recovery must distinguish committed from attempted state | SPEC fault model |
| Two bindings | Only a Python API/CLI participant exists | Human and model bindings must use the same transition contract | C1; PROD-I-3 |
| Attestation | Byte observation exists, but general claim attestation does not | `REPRODUCED`, `DISSENTED`, and `UNATTESTABLE` must be recorded | C5; PROD-I-8 |
| Judgement queue | Missing authority refuses synchronously | Judgement-dependent work must remain visible and non-blocking | PROD-I-6 |
| Model portability | No Model Binding or Model Adapter participant exists | Two materially different models must use one kernel contract with exact identity, data-boundary, usage, cost, and provider-loss receipts | PROD-I-9; BYOM.md |
| Operational journal | Mutable lifecycle tables and partial receipts do not yet implement the complete append-preserving Event Envelope | Every consequential decision and state transition must remain reconstructable independently of current projections | C15; SPEC `EventEnvelope` |
| Collection type migration | A collection type cannot be redeclared: a second declaration is refused `STALE_STATE`, so a schema change under existing members has no path at all | A superseding type version, with every member re-judged against it and the earlier version preserved | ENGINEERING; `decisions/0057`, Defaults taken |
| Metadata field types | A required field accepts any JSON value; only a declared controlled vocabulary constrains one, and a field with no vocabulary is satisfied by an empty string | A declared value type per field, checked when a description is recorded rather than only when it is read back | `decisions/0057`, Ruling 1 |
| Search and graph projections | `CHARTER.md` names an SQLite FTS projection and lineage traversal; the build is a `LIKE` substring scan with no ranking and a one-hop `neighbors()` | Ranked text search, bounded multi-hop traversal, and per-hit source resolution belong to the chartered Asset Projection Service (`services/projection/`, `decisions/0021`); these two tables are a compatibility path | SPEC Projection rule; PROD-I-3; OPEN-SEAMS S14 |

These are participant defects or unimplemented requirements, not reasons to
relax the logical oracle.
