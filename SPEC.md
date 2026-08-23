# Phase-I Logical Specification

Status: `PROPOSED · STACK-NEUTRAL · OWNER FREEZE PENDING`

This specification implements the Phase-I requirements in `PRD.md`. It fixes
logical objects, roles, states, transitions, predicates, receipts, and refusal
behavior. It does not select storage, encoding, language, transport, process,
container, graph, model provider, or repository layout.

## Operating profile

### Trust model

- The host provides execution and persistence mechanisms but does not receive
  ratification authority merely by running the system.
- Human and model operators are untrusted outside explicitly recorded grants.
- Model output is always a proposal, recording, report, or observation; its
  fluency never changes standing.
- Stored artifacts are trusted only to the degree that their addresses,
  digests, provenance, and required attestations verify.
- The runtime may attest reproduction. It may not ratify judgement.

### Local operation

Phase I must run from a clean local artifact without Claude, GitHub, an external
graph database, or another network service. Optional integrations either
operate through declared adapters or refuse as `UNCONFIGURED` with a receipt.

The first operating profile is a personally owned node. It uses the same
contracts as later team or enterprise profiles. Model computation may be local
or remote, but the authoritative record, authority, and continuity remain under
node ownership.

### Fault model

| Fault | Phase-I obligation |
| --- | --- |
| Process restart | committed records remain reconstructable |
| Partial write | no partially committed record becomes effective |
| Power loss | recovery distinguishes committed from attempted work |
| Corrupt payload | digest verification refuses the reading |
| Missing dependency | affected operation refuses or becomes `UNATTESTABLE` |
| Stale input or lease | settlement refuses and preserves the attempt |
| Concurrent author | precondition or fencing failure refuses stale settlement |
| External service loss | local custody, authority, and record operation continue |

Media durability beyond detectable corruption is an infrastructure concern and
is not claimed by the logical specification.

### Effects

Every consequential operation declares exactly one effect class:

- `RECORD_LOCAL` — changes only governed record state; countering is supported.
- `RESOURCE_CONSUMPTION` — consumes time, compute, storage, money, or another
  resource; the record can be countered but consumption is not reversed.
- `EXTERNAL_WORLD` — mutates a system outside the local record; refused in
  Phase I unless an isolated test double makes the observed effect record-local.

## Logical roles

The terms below follow `CLASSIFICATION.md`. A value may fill more than one role
only through a declared equivalence.

### Identity roles

`identity`, `address`, `digest`, `label`, `route`, and `handle` are distinct.
Coincidental equality never merges their semantics.

### Information objects

#### `Source`

Required fields:

```text
source_id, source_address, payload_digest, payload_size,
captured_at, captured_by
```

The bytes resolved by `source_address` must match `payload_digest` before a
reading begins.

#### `Reader`

```text
reader_id, reader_version, configuration_digest,
output_role, fidelity: EXACT | LOSSY,
omissions: [] | versioned_omission_definition
```

An `EXACT` reader declares no omissions. A `LOSSY` reader directly declares
omissions or resolves a versioned definition from which they are
deterministically recoverable.

#### `Recording`

```text
recording_id, source_id, source_digest, reader_id, reader_version,
configuration_digest, payload_address, payload_digest,
fidelity, omissions, produced_at, produced_by, standing
```

A recording never replaces or mutates its source.

#### `Proposal`

```text
proposal_id, actor_id, actor_kind: HUMAN | MODEL,
content_address, source_addresses, cost_record,
required_authority_type, scope, created_at, standing
```

A new proposal begins `RECORDED` and claims no authority.

#### `AuthorityGrant`

```text
grant_id, issuer_id, actor_id,
authority_type: VERIFICATION | JUDGEMENT,
capability, scope, budget, valid_from, valid_until,
revoked_at | null
```

An authority check evaluates type, capability, scope, budget, time, and
revocation at the attempted transition.

#### `ModelBinding`

```text
binding_id, adapter_id,
provider_id, provider_kind: LOCAL | REMOTE,
model_id, model_version,
runtime_id, runtime_version, host_id,
interface_contract_id, capabilities,
data_boundary: LOCAL_ONLY | REDACTED_REMOTE | REMOTE_ALLOWED,
input_projection_id, omissions,
usage_meter, cost_meter,
fallback_policy: NONE | EXPLICIT,
created_at
```

Model and provider identity are configuration, not authority. A binding grants
no capability by existing; every invocation still checks the actor's scoped
authority and operation plan. `EXPLICIT` fallback requires a new attributed
invocation and receipt naming the replacement binding.

#### `OperationPlan`

```text
operation_id, operation_type, requester_id, interface_id,
input_addresses, input_digests, readings, configuration_digest,
required_capabilities, preconditions, expected_observations,
effect_class, limits, refusal_behavior, created_at
```

No consequential run begins without a complete plan.

#### `EventEnvelope`

```text
event_id, operation_id,
event_phase: ATTEMPTED | REPORTED | OBSERVED | SETTLED | COUNTERED,
actor_id, actor_kind: HUMAN | MODEL | WORKER | SYSTEM,
reason, occurred_at,
inputs: [{address, digest}], outputs: [{address, digest}],
authority_grant_ids, effect_class,
outcome: ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED,
receipt_id | null
```

Every consequential human or model decision emits an event envelope. An attempt
may have a null `receipt_id` until it reaches a terminal outcome; settlement,
refusal, failure, unresolved work, and counteraction resolve a durable receipt.
The envelope does not replace the more specific domain record.

#### `Run`

```text
run_id, operation_id, actor_id, worker_id | null,
input_state_digest, lease_fence | null, lease_expires_at | null,
started_at, completed_at | null,
outcome: ATTEMPTED | COMMITTED | FAILED | REFUSED | UNRESOLVED,
emitted_record_addresses
```

Executor completion is a report, not settlement.

#### `Observation`

```text
observation_id, run_id, observer_id, observer_relation,
observed_state_addresses, observed_state_digests,
predicate_results, observed_at
```

`observer_relation` must state how the observer avoids relying solely on the
executor's report.

#### `Attestation`

```text
attestation_id, claim_id, validator_id, validator_version,
input_addresses, input_digests, run_id,
outcome: REPRODUCED | DISSENTED | UNATTESTABLE,
evidence_addresses, created_at
```

Attestation changes no authority sign. `DISSENTED` or `UNATTESTABLE` remains
visible when current effectiveness is evaluated.

#### `Receipt`

Every attempted crossing and every consequential operation eventually returns
one terminal receipt:

```text
receipt_id, event_id, event_type, actor_id, interface_id,
input_addresses, input_state_digest, authority_grant_ids,
precondition_results, effect_class,
outcome: COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED,
reason_code | null, emitted_record_addresses,
observed_evidence_addresses, prior_receipt_id | null,
created_at, receipt_digest
```

The receipt is attributable and addressable even when the outcome is refusal,
failure, unresolved judgement, dissent, or counteraction.

#### `Retraction`

```text
retraction_id, target_record_id, target_receipt_id,
actor_id, authority_grant_id, reason,
effect_class, counter_record_id, created_at
```

Retraction preserves the original record and receipt. For non-record-local
effects it states what remains consumed or changed and makes no rollback claim.

#### `QualificationRecord`

```text
qualification_id, artifact_revision, witness_id,
host_description, started_at, completed_at,
scenario_results, evidence_addresses,
time_to_safe_competence, interventions,
owner_acceptance: PENDING | ACCEPTED | STRUCK
```

The witness may deposit this record. Only the owner may change
`owner_acceptance` from `PENDING`.

## Historical standing and current effectiveness

Standing values are `RECORDED`, `ADMITTED`, `RATIFIED`, and `EFFECTIVE`.
They do not collapse:

1. `RECORDED` establishes attributable existence.
2. `ADMITTED` records that an admission gate passed.
3. `RATIFIED` records a typed authority decision.
4. `EFFECTIVE` means the ratified record currently conditions operation.

Historical ratification is never deleted. A dissenting attestation,
superseding record, expiration, or authorized retraction may stop a record from
conditioning current operation while preserving its history.

## Transition contract

Every transition checks the declared pre-state. Each attempted operation emits
exactly one terminal receipt; intermediate run transitions append attributable
events but do not create extra terminal outcomes. A stale pre-state cannot
settle.

| Transition | Preconditions | Commit | Refusal |
| --- | --- | --- | --- |
| `capture_source` | readable bytes; address and digest available | create immutable `Source` | `UNREADABLE` or `DIGEST_MISMATCH` |
| `read_source` | source digest verifies; reader fully declared | emit `Recording`; source unchanged | `SOURCE_CHANGED` or `READER_UNDECLARED` |
| `submit_proposal` | actor, cost, source, scope, and required authority declared | record proposal as `RECORDED` | `INCOMPLETE_PROPOSAL` |
| `admit` | admission predicates pass against exact proposal state | preserve `RECORDED`; add `ADMITTED` event | `ADMISSION_REFUSED` or `STALE_STATE` |
| `ratify` | proposal admitted; live matching authority grant | preserve history; add `RATIFIED` event | `AUTHORITY_REFUSED` or `STALE_STATE` |
| `attest` | ratified executable claim; declared validator and exact inputs | emit one attestation outcome | `VALIDATOR_UNDECLARED` |
| `make_effective` | ratified; required attestation policy satisfied; no current counter | add `EFFECTIVE` event | `DISSENTED`, `UNATTESTABLE`, or `POLICY_REFUSED` |
| `begin_run` | complete plan; capability, budget, input, and effect gates pass | emit `ATTEMPTED`; issue lease if delegated | reasoned refusal |
| `report_run` | current lease and fence; declared output records | store executor report; do not settle | `STALE_LEASE` |
| `observe_run` | independent observer relation; expected predicates declared | emit observation | `OBSERVER_NOT_INDEPENDENT` |
| `settle_run` | current input state; satisfactory observation | `COMMITTED`, `FAILED`, or `UNRESOLVED` receipt | `STALE_STATE` or `OBSERVATION_MISSING` |
| `retract` | live matching retraction authority; target and effect known | emit counter-record and `COUNTERED` receipt | `AUTHORITY_REFUSED` |
| `cross` | declared source, reader/projection, omissions, authority, destination | destination record and receipt | reasoned refusal |
| `invoke_model` | declared binding, operation plan, authority, input projection, data boundary, usage and cost meters | proposal, recording, report, or observation plus receipt | `MODEL_UNAVAILABLE`, `MODEL_INCOMPATIBLE`, `DATA_BOUNDARY_REFUSED`, or reasoned refusal |

No interface, adapter, worker, projection, or graph store may bypass these
transitions to change authoritative state.

## Requirement predicates

### PROD-I-1 · Propose

- Every accepted proposal has actor, actor kind, source, cost, scope, required
  authority, address, and `RECORDED` standing.
- Missing fields defeat admission.

### PROD-I-2 · Remember

- A source rereads byte-identical by digest.
- Every recording resolves its exact source, reader version, configuration,
  fidelity, and recoverable omissions.
- Reading never mutates source bytes.

### PROD-I-3 · Cross

- Human and model bindings resolve the same authoritative transition contract.
- A crossing identifies source, version, reader or projection, omissions,
  destination, and receipt.

### PROD-I-4 · Gate and retract

- Admission, refusal, action, failure, unresolved judgement, attestation,
  retraction, and counteraction are receipted.
- Retraction preserves the original occurrence and distinguishes effect class.

### PROD-I-5 · Typed authority

- Every consequential transition checks a live typed, scoped, budgeted grant.
- `VERIFICATION` authority cannot ratify a `JUDGEMENT` claim.
- Revoked, expired, out-of-scope, and over-budget grants refuse visibly.

### PROD-I-6 · Founder judgement budget

- Missing judgement produces a persistent pending-right record and
  `UNRESOLVED` receipt without blocking unrelated operation.
- Judgement use is reported from actual receipts; no quota is invented.

### PROD-I-7 · Independent qualification

- A fresh witness receives only the declared artifact and host assumptions.
- The witness can locate authority, run conformance, reconstruct evidence, and
  record time and interventions without oral explanation.
- Qualification remains pending until owner acceptance.

### PROD-I-8 · Joint sign

- A ratified executable claim has an attestation naming validator, version,
  exact inputs, run, outcome, and evidence.
- Changed inputs cannot inherit `REPRODUCED` from a historical run.
- Attestation never changes ratification authority.

### PROD-I-9 · Bring your own model

- Two materially different model bindings expose the same named operation and
  use the same kernel transitions, authority checks, and receipt contract.
- Each run records binding, adapter, provider, model, version, runtime, host,
  input projection, omissions, data boundary, usage, and cost.
- Changing models creates distinct attributed results; it does not silently
  merge outputs or change authoritative state.
- An unavailable model returns a reasoned receipt. Any fallback is a separately
  attributed explicit invocation.
- Provider loss cannot remove local record custody or non-model operation.

## Interface parity

Human and model bindings may present different projections, but they must:

- discover the same legal operations and required inputs;
- invoke the same transitions and authority checks;
- receive compatible receipts and reason codes;
- expose provenance and omissions appropriate to their projection;
- and lack direct authoritative storage writes.

Parity is tested by equivalent operations and reconciled receipts, not by
pixel or response-format identity.

## Projection rule

Search indexes, graph stores, caches, dashboards, and model context packages are
rebuildable projections. Each projected value resolves to authoritative source
records and declares omissions. Projection-originated edits return as proposals
through the transition contract.

## Conformance boundary

Every normative predicate above requires a positive and a defeating fixture.
Fixtures observe state, authority checks, receipts, and effects rather than
requiring a particular mechanism. Passing self-authored unit tests establishes
`BUILT`; an independent run is required for `WITNESSED`; Bdo's recorded decision
is required for `RATIFIED`.

## Traceability

| Specification area | Requirement | Source ground |
| --- | --- | --- |
| Proposal and standing | PROD-I-1, I-4 | SUBSTRATE R3; ANCHOR A2, A5 |
| Source and derivation | PROD-I-2 | SUBSTRATE R1, R2, R5 |
| Shared crossing | PROD-I-3 | SUBSTRATE V1, R5; ANCHOR A3 |
| Authority | PROD-I-5, I-6 | SUBSTRATE R4; ANCHOR A4, A10 |
| Observation and receipts | PROD-I-4, I-8 | SUBSTRATE R3, R6; ANCHOR A2 |
| Cold-start qualification | PROD-I-7 | SUBSTRATE V5, T1; ANCHOR A6 |
| Personal-local model portability | PROD-I-9 | SUBSTRATE V1-V3, R2-R5; ANCHOR A3, A8 |
| Node and federation boundary | later phase | ANCHOR A8; PRODUCT §5 |

Exact historical source addresses and digests remain in `lineage/` and are not
duplicated into this normative layer.
